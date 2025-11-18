import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def mostrar(datos_accion):
    """
    Sección completa de noticias - Adaptada para recibir datos_accion
    """
    # Extraer stonk y nombre de datos_accion
    stonk = datos_accion['ticker']
    nombre = datos_accion['nombre']
    
    st.header("📰 Centro de Noticias")
    
    # Crear pestañas para las dos subsecciones
    tab1, tab2 = st.tabs([
        f"📈 Noticias de {nombre}", 
        "🌍 Noticias Globales"
    ])
    
    with tab1:
        # TU CÓDIGO ORIGINAL EXACTO
        st.header(f"📰 Noticias de {nombre}")
        
        # Función para obtener noticias de Finviz
        def obtener_noticias_finviz(ticker):
            url = f"https://finviz.com/quote.ashx?t={ticker}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Buscar la tabla de noticias
                    news_table = soup.find('table', {'class': 'fullview-news-outer'})
                    
                    if news_table:
                        noticias = []
                        rows = news_table.find_all('tr')
                        
                        for row in rows:
                            try:
                                # Extraer fecha/hora
                                fecha_td = row.find('td', {'align': 'right', 'width': '130'})
                                fecha = fecha_td.get_text(strip=True) if fecha_td else "Fecha no disponible"
                                
                                # Extraer enlace y título
                                link_container = row.find('div', {'class': 'news-link-left'})
                                if link_container:
                                    link = link_container.find('a')
                                    if link:
                                        titulo = link.get_text(strip=True)
                                        href = link.get('href', '')
                                        
                                        # Si el enlace es relativo, convertirlo a absoluto
                                        if href.startswith('/'):
                                            href = f"https://finviz.com{href}"
                                        
                                        # Extraer fuente
                                        fuente_container = row.find('div', {'class': 'news-link-right'})
                                        fuente = fuente_container.get_text(strip=True).strip('()') if fuente_container else "Fuente no disponible"
                                        
                                        noticias.append({
                                            'fecha': fecha,
                                            'titulo': titulo,
                                            'enlace': href,
                                            'fuente': fuente
                                        })
                            except Exception as e:
                                continue
                        
                        return noticias
                    else:
                        st.error("No se pudo encontrar la tabla de noticias en Finviz")
                        return []
                else:
                    st.error(f"Error al acceder a Finviz: {response.status_code}")
                    return []
                    
            except Exception as e:
                st.error(f"Error al obtener noticias: {str(e)}")
                return []

        # Obtener y mostrar noticias
        with st.spinner('Cargando noticias recientes...'):
            noticias = obtener_noticias_finviz(stonk)
            
            if noticias:
                st.success(f"✅ Se encontraron {len(noticias)} noticias recientes")
                
                # Mostrar estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Noticias", len(noticias))
                with col2:
                    fuentes_unicas = len(set(noticia['fuente'] for noticia in noticias))
                    st.metric("Fuentes Diferentes", fuentes_unicas)
                with col3:
                    st.metric("Última Actualización", datetime.now().strftime("%H:%M"))
                
                st.markdown("---")
                
                # Mostrar noticias
                st.subheader("📋 Noticias Recientes")
                
                for i, noticia in enumerate(noticias[:100], 1):
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.write(f"**{noticia['fecha']}**")
                            st.write(f"*{noticia['fuente']}*")
                        
                        with col2:
                            # Crear un enlace clickeable
                            st.markdown(f"**[{noticia['titulo']}]({noticia['enlace']})**")
                        
                        # Separador entre noticias (excepto la última)
                        if i < min(100, len(noticias)):
                            st.markdown("---")
                
                # Información adicional si hay más noticias
                if len(noticias) > 100:
                    st.info(f"💡 Mostrando las 100 noticias más recientes de {len(noticias)} totales")
                    
            else:
                st.warning("No se pudieron cargar las noticias. Esto puede deberse a:")
                st.write("• Problemas de conexión con Finviz")
                st.write("• Cambios en la estructura del sitio web")
                st.write("• Restricciones de acceso temporales")
                
                # Sugerencia alternativa
                st.info("💡 **Alternativa:** Puedes visitar directamente [Finviz](https://finviz.com) para ver las noticias más recientes")
    
    with tab2:
        # NUEVA SECCIÓN: NOTICIAS GLOBALES CON CONTROLES
        st.header("🌍 Noticias Globales")
        
        # CONTROLES PARA NOTICIAS GLOBALES - CORREGIDO
        col_controls1 = st.columns(1)
        
        # CORRECCIÓN: Acceder al primer elemento de la lista
        with col_controls1[0]:
            categoria_global = st.selectbox(
                "📂 Categoría:",
                ["general", "negocios", "tecnologia", "ciencia", "salud", "politica", "finanzas"],
                format_func=lambda x: {
                    "general": "🌍 General",
                    "negocios": "💼 Negocios", 
                    "tecnologia": "🔬 Tecnología",
                    "ciencia": "🧪 Ciencia",
                    "salud": "🏥 Salud", 
                    "politica": "⚖️ Política",
                    "finanzas": "💰 Finanzas"
                }[x]
            )

        # Botón para cargar noticias globales
        if st.button("🔄 Cargar Noticias Globales", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # Función para obtener noticias globales
        def obtener_noticias_globales(categoria, pais="us"):
            try:
                # Mapeo de categorías a Google News
                categorias_google = {
                    "general": "https://news.google.com/rss?hl=es-419&gl=US&ceid=US:es-419",
                    "negocios": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=es-419&gl=US&ceid=US:es-419",
                    "tecnologia": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=es-419&gl=US&ceid=US:es-419",
                    "ciencia": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=es-419&gl=US&ceid=US:es-419",
                    "salud": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=es-419&gl=US&ceid=US:es-419",
                    "politica": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=es-419&gl=US&ceid=US:es-419",
                    "finanzas": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=es-419&gl=US&ceid=US:es-419"
                }
                
                url = categorias_google.get(categoria, categorias_google["general"])
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    items = soup.find_all('item')
                    noticias = []
                    
                    for item in items:
                        try:
                            # Extraer título
                            titulo = item.find('title')
                            titulo_text = titulo.text if titulo else "Sin título"
                            
                            # Extraer enlace
                            enlace = item.find('link')
                            enlace_text = enlace.text if enlace else "#"
                            
                            # Extraer fecha
                            fecha = item.find('pubdate')
                            if not fecha:
                                fecha = item.find('pubDate')
                            fecha_text = fecha.text if fecha else "Fecha no disponible"
                            
                            # Extraer fuente del título
                            fuente = "Google News"
                            if ' - ' in titulo_text:
                                partes = titulo_text.split(' - ')
                                if len(partes) > 1:
                                    fuente = partes[-1].strip()
                                    titulo_text = ' - '.join(partes[:-1]).strip()
                            
                            # Limpiar HTML del título
                            titulo_text = BeautifulSoup(titulo_text, 'html.parser').get_text()
                            
                            noticias.append({
                                'fecha': fecha_text,
                                'titulo': titulo_text,
                                'enlace': enlace_text,
                                'fuente': fuente,
                                'categoria': categoria,
                                'pais': pais
                            })
                        except Exception as e:
                            continue
                    
                    return noticias
                else:
                    return []
                    
            except Exception as e:
                return []

        # Obtener y mostrar noticias globales (MISMO FORMATO QUE EL ORIGINAL)
        with st.spinner('Cargando noticias globales...'):
            noticias_globales = obtener_noticias_globales(categoria_global)
            
            if noticias_globales:
                st.success(f"✅ Se encontraron {len(noticias_globales)} noticias globales")
                
                # Mostrar estadísticas (MISMO FORMATO)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Noticias", len(noticias_globales))
                with col2:
                    fuentes_unicas = len(set(noticia['fuente'] for noticia in noticias_globales))
                    st.metric("Fuentes Diferentes", fuentes_unicas)
                with col3:
                    st.metric("Última Actualización", datetime.now().strftime("%H:%M"))
                
                st.markdown("---")
                
                # Mostrar noticias (MISMO FORMATO EXACTO)
                st.subheader("📋 Noticias Globales Recientes")
                
                for i, noticia in enumerate(noticias_globales, 1):
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.write(f"**{noticia['fecha']}**")
                            st.write(f"*{noticia['fuente']}*")
                        
                        with col2:
                            # Crear un enlace clickeable (MISMO FORMATO)
                            if noticia['enlace'] != "#":
                                st.markdown(f"**[{noticia['titulo']}]({noticia['enlace']})**")
                            else:
                                st.markdown(f"**{noticia['titulo']}**")
                                st.write("🔒 Enlace no disponible")
                        
                        # Separador entre noticias (MISMO FORMATO)
                        if i < len(noticias_globales):
                            st.markdown("---")
                
                # Información adicional (MISMO FORMATO)
                st.info(f"💡 Mostrando {len(noticias_globales)} noticias de {categoria_global}")
                    
            else:
                # Mensaje de error (MISMO FORMATO)
                st.warning("No se pudieron cargar las noticias globales. Esto puede deberse a:")
                st.write("• Problemas de conexión a internet")
                st.write("• Cambios en la estructura del sitio web")
                st.write("• Restricciones de acceso temporales")
                
                # Sugerencia alternativa (MISMO FORMATO)
                st.info("💡 **Alternativa:** Puedes visitar directamente [Google News](https://news.google.com) para ver las noticias más recientes")