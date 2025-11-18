# sections/informacion.py
import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
from utils.data_fetcher import obtener_info_wikipedia, obtener_rating_analistas

def mostrar_seccion_informacion(datos_accion):
    """
    Muestra la sección de información completa de la acción
    Versión modificada para aceptar el diccionario datos_accion de app.py
    """
    # Extraer los datos del diccionario
    stonk = datos_accion['ticker']
    info = datos_accion['info']
    ticker = yf.Ticker(stonk)  # Crear objeto ticker si es necesario
    
    st.header(f"🏢 Información de {info.get('longName', stonk)}")
    
    # Rating de analistas
    ratings = obtener_rating_analistas(stonk)
    if ratings:
        st.subheader("🎯 Rating de Analistas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            reco_key = ratings.get('recommendationKey', 'N/A')
            if isinstance(reco_key, str):
                reco_display = reco_key.upper().replace("_", " ")
            else:
                reco_display = "N/A"
            
            st.metric("Recomendación", reco_display)
        
        with col2:
            target_price = ratings.get('targetMeanPrice', 'N/A')
            current_price = info.get('currentPrice', 0)
            if target_price != 'N/A' and current_price and target_price > current_price:
                st.metric("Target Price", f"${target_price:.2f}", f"+{((target_price/current_price)-1)*100:.1f}%")
            elif target_price != 'N/A':
                st.metric("Target Price", f"${target_price:.2f}")
            else:
                st.metric("Target Price", "N/A")
        
        with col3:
            st.metric("Rating Medio", f"{ratings.get('recommendationMean', 'N/A')}/5")
        
        with col4:
            st.metric("# Analistas", ratings.get('numberOfAnalystOpinions', 'N/A'))
    
    # Descripción traducida
    descripcion = info.get("longBusinessSummary", "No hay datos disponibles.")
    texto_traducido = _traducir_descripcion_empresa(descripcion)
    
    st.subheader("📋 Descripción de la Empresa")
    st.write(texto_traducido)
    
    # Información adicional básica
    _mostrar_informacion_basica(info)
    
    # Línea separadora
    st.markdown("---")

    # INFORMACIÓN DE WIKIPEDIA
    st.subheader("📚 Información Corporativa")

    # Obtener información de Wikipedia
    with st.spinner('Buscando información en Wikipedia...'):
        info_wikipedia = obtener_info_wikipedia(stonk, info.get('longName', stonk))

        if info_wikipedia.get('encontrado', False):
            # MOSTRAR DIRECTAMENTE CON MARKDOWN SIN EL CUADRO HTML
            st.markdown(info_wikipedia['contenido'])
            
            # Mostrar fuente
            st.caption(f"📖 Fuente: {info_wikipedia['fuente']} - [Enlace a Wikipedia]({info_wikipedia['url']})")
            
        else:
            st.info("""
            ℹ️ **Información no disponible**
                
            No se pudo encontrar información específica de esta empresa. 
            Esto puede deberse a:
            - La empresa es muy nueva o poco conocida
            - El nombre no coincide con entradas de Wikipedia
            - Limitaciones temporales de la API
            """)

def _traducir_descripcion_empresa(descripcion):
    """
    Traduce la descripción de la empresa usando Gemini
    """
    prompt = f"""
    Te voy a dar la descripción en inglés de una empresa que cotiza en bolsa, necesito que traduzcas la descripción a español financiero formal,
    quiero que la traducción sea lo más apegado posible a la descripción original y que me entregues el texto en exactamente 500 caracteres, te paso la
    descripción de la empresa: {descripcion}
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        texto_traducido = response.text
        return texto_traducido

    except Exception as e:
        return "Traducción no disponible por el momento."

def _mostrar_informacion_basica(info):
    """
    Muestra la información básica de la empresa en formato de métricas
    """
    st.subheader("📊 Información Básica")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sector = info.get("sector", "N/A")
        st.metric("Sector", sector)
        employees = info.get("fullTimeEmployees", "N/A")
        if employees != "N/A":
            st.metric("Empleados", f"{employees:,}")
        else:
            st.metric("Empleados", "N/A")
    
    with col2:
        industry = info.get("industry", "N/A")
        st.metric("Industria", industry)
        country = info.get("country", "N/A")
        st.metric("País", country)
    
    with col3:
        market_cap = info.get("marketCap", "N/A")
        if market_cap != "N/A":
            st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
        else:
            st.metric("Market Cap", "N/A")
        
        currency = info.get("currency", "N/A")
        st.metric("Moneda", currency)
    
    with col4:
        pe_ratio = info.get("trailingPE", "N/A")
        if pe_ratio != "N/A":
            st.metric("P/E Ratio", f"{pe_ratio:.2f}")
        else:
            st.metric("P/E Ratio", "N/A")
        
        dividend_yield = info.get("dividendYield", "N/A")
        if dividend_yield and dividend_yield != "N/A":
            st.metric("Dividend Yield", f"{dividend_yield*100:.2f}%")
        else:
            st.metric("Dividend Yield", "N/A")

def _mostrar_datos_financieros(info):
    """
    Muestra datos financieros adicionales (opcional)
    """
    st.subheader("💰 Datos Financieros Adicionales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # EBITDA
        ebitda = info.get("ebitda", "N/A")
        if ebitda != "N/A":
            st.metric("EBITDA", f"${ebitda/1e9:.2f}B")
        else:
            st.metric("EBITDA", "N/A")
    
    with col2:
        # Revenue
        revenue = info.get("totalRevenue", "N/A")
        if revenue != "N/A":
            st.metric("Ingresos Totales", f"${revenue/1e9:.2f}B")
        else:
            st.metric("Ingresos Totales", "N/A")
    
    with col3:
        # Gross Profits
        gross_profits = info.get("grossProfits", "N/A")
        if gross_profits != "N/A":
            st.metric("Beneficios Brutos", f"${gross_profits/1e9:.2f}B")
        else:
            st.metric("Beneficios Brutos", "N/A")
    
    with col4:
        # Operating Margin
        operating_margin = info.get("operatingMargins", "N/A")
        if operating_margin != "N/A":
            st.metric("Margen Operativo", f"{operating_margin*100:.2f}%")
        else:
            st.metric("Margen Operativo", "N/A")

# Alias para compatibilidad con App.py
mostrar = mostrar_seccion_informacion

# Función principal para testing
if __name__ == "__main__":
    # Para probar esta sección individualmente
    st.title("🔍 Prueba - Sección Información")
    
    # Ejemplo de prueba
    ticker_symbol = "MSFT"
    ticker_obj = yf.Ticker(ticker_symbol)
    info_data = ticker_obj.info
    
    # Crear el diccionario datos_accion como lo hace app.py
    datos_accion = {
        'ticker': ticker_symbol,
        'info': info_data,
        'datos': yf.download(ticker_symbol, period="1mo", progress=False),
        'nombre': info_data.get("longName", "Empresa no encontrada"),
        'descripcion': info_data.get("longBusinessSummary", "No hay descripción disponible")
    }
    
    mostrar_seccion_informacion(datos_accion)

  
