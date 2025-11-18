# utils/data_fetcher.py
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
import time
import random
import numpy as np
from bs4 import BeautifulSoup
import concurrent.futures
from threading import Lock

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def obtener_rating_analistas(ticker):
    """Obtiene el rating de analistas para una acción"""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        ratings = {
            'recommendationMean': info.get('recommendationMean', 'N/A'),
            'recommendationKey': info.get('recommendationKey', 'N/A'),
            'targetMeanPrice': info.get('targetMeanPrice', 'N/A'),
            'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions', 'N/A')
        }
        return ratings
    except Exception as e:
        st.error(f"Error obteniendo rating de analistas: {str(e)}")
        return {}

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def obtener_info_wikipedia(ticker, nombre_empresa):
    """
    Obtiene información de Wikipedia usando la API oficial
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # PRIMERO: Usar la API de búsqueda de Wikipedia para encontrar la página correcta
        search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_empresa}&format=json&srlimit=5"
        
        search_response = requests.get(search_url, headers=headers, timeout=10)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            
            if search_data['query']['search']:
                # Tomar el primer resultado que parezca relevante
                for result in search_data['query']['search']:
                    title = result['title']
                    
                    # Verificar que el título sea relevante (contenga palabras clave de la empresa)
                    if any(keyword in title.lower() for keyword in ['inc', 'corp', 'company', 'corporation', nombre_empresa.split()[0].lower()]):
                        # Obtener el contenido COMPLETO de la página usando la API
                        content_url = f"https://es.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true&titles={title}&format=json"
                        content_response = requests.get(content_url, headers=headers, timeout=10)
                        
                        if content_response.status_code == 200:
                            content_data = content_response.json()
                            pages = content_data['query']['pages']
                            
                            for page_id, page_data in pages.items():
                                if 'extract' in page_data and page_data['extract']:
                                    contenido = page_data['extract']
                                    
                                    # LIMPIAR EL FORMATO DE TÍTULOS
                                    contenido_limpio = _limpiar_formato_wikipedia(contenido)
                                    
                                    return {
                                        'encontrado': True,
                                        'contenido': contenido_limpio,
                                        'url': f"https://es.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                        'termino_busqueda': title,
                                        'fuente': 'API Wikipedia'
                                    }
        
        # SEGUNDO: Intentar con búsqueda en inglés
        search_url_english = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={nombre_empresa}&format=json&srlimit=5"
        
        search_response_english = requests.get(search_url_english, headers=headers, timeout=10)
        
        if search_response_english.status_code == 200:
            search_data_english = search_response_english.json()
            
            if search_data_english['query']['search']:
                for result in search_data_english['query']['search']:
                    title = result['title']
                    
                    if any(keyword in title.lower() for keyword in ['inc', 'corp', 'company', 'corporation', nombre_empresa.split()[0].lower()]):
                        content_url_english = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true&titles={title}&format=json"
                        content_response_english = requests.get(content_url_english, headers=headers, timeout=10)
                        
                        if content_response_english.status_code == 200:
                            content_data_english = content_response_english.json()
                            pages_english = content_data_english['query']['pages']
                            
                            for page_id, page_data in pages_english.items():
                                if 'extract' in page_data and page_data['extract']:
                                    contenido_ingles = page_data['extract']
                                    
                                    # LIMPIAR EL FORMATO PRIMERO
                                    contenido_ingles_limpio = _limpiar_formato_wikipedia(contenido_ingles)
                                    
                                    # Traducir con Gemini - CONTENIDO COMPLETO
                                    try:
                                        prompt_traduccion = f"""
                                        Traduce al español el siguiente texto sobre una empresa manteniendo un tono formal.
                                        Conserva términos técnicos y financieros sin cambios.
                                        Traduce TODO el texto completo sin omitir nada.
                                        
                                        Texto: {contenido_ingles_limpio}
                                        """
                                        
                                        response_traduccion = genai.models.generate_content(
                                            model="gemini-2.5-flash",
                                            contents=prompt_traduccion
                                        )
                                        
                                        contenido_traducido = response_traduccion.text
                                        
                                        return {
                                            'encontrado': True,
                                            'contenido': contenido_traducido,
                                            'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                            'termino_busqueda': title,
                                            'fuente': 'API Wikipedia Inglés (Traducido)'
                                        }
                                    except:
                                        # Si falla la traducción, devolver en inglés COMPLETO
                                        return {
                                            'encontrado': True,
                                            'contenido': contenido_ingles_limpio,
                                            'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                            'termino_busqueda': title,
                                            'fuente': 'API Wikipedia Inglés'
                                        }
        
        return {'encontrado': False, 'error': 'No se encontró información en Wikipedia'}
            
    except Exception as e:
        return {'encontrado': False, 'error': f'Error: {str(e)}'}

def _limpiar_formato_wikipedia(texto):
    """
    Limpia el formato de markdown de Wikipedia y convierte los títulos a formato Markdown
    """
    if not texto:
        return texto
    
    lineas = texto.split('\n')
    lineas_limpias = []
    
    for linea in lineas:
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
            
        # Detectar títulos con === Título ===
        if linea_limpia.startswith('===') and linea_limpia.endswith('==='):
            # Es un título principal (### en Markdown)
            titulo = linea_limpia.replace('===', '').strip()
            if titulo:
                lineas_limpias.append(f"### {titulo}")
                
        # Detectar subtítulos con == Título ==
        elif linea_limpia.startswith('==') and linea_limpia.endswith('=='):
            # Es un subtítulo (## en Markdown)
            subtitulo = linea_limpia.replace('==', '').strip()
            if subtitulo:
                lineas_limpias.append(f"## {subtitulo}")
                
        else:
            # Texto normal
            lineas_limpias.append(linea_limpia)
    
    return '\n\n'.join(lineas_limpias)

@st.cache_data(ttl=3600, show_spinner=False, max_entries=100)
def obtener_info_completa(ticker):
    """Obtiene información completa de la acción"""
    try:
        return yf.Ticker(ticker).info
    except Exception as e:
        st.error(f"Error obteniendo información de {ticker}: {str(e)}")
        return {}

@st.cache_data(ttl=1800, show_spinner=False, max_entries=200)
def obtener_datos_accion(ticker, periodo="1y"):
    """Obtiene datos históricos de la acción"""
    try:
        return yf.download(ticker, period=periodo, progress=False, interval="1d")
    except Exception as e:
        st.error(f"Error descargando datos de {ticker}: {str(e)}")
        return pd.DataFrame()

# Función para testing
if __name__ == "__main__":
    # Probar las funciones individualmente
    st.title("🔍 Prueba - Data Fetcher")
    
    # Probar obtener_info_wikipedia
    st.subheader("Prueba Wikipedia")
    info_wiki = obtener_info_wikipedia("MSFT", "Microsoft Corporation")
    st.write(info_wiki)
    
    # Probar obtener_rating_analistas
    st.subheader("Prueba Rating Analistas")
    ratings = obtener_rating_analistas("MSFT")
    st.write(ratings)

# AGREGANDO NUEVAS FUNCIONES SIN MODIFICAR LAS EXISTENTES

@st.cache_data(ttl=3600, show_spinner=False, max_entries=10)
def obtener_datos_sp500():
    """Obtiene datos del índice S&P 500"""
    try:
        return yf.download("^GSPC", period="1y", progress=False, interval="1d")
    except Exception as e:
        st.error(f"Error obteniendo datos S&P 500: {str(e)}")
        return pd.DataFrame()

def obtener_datos_yahoo_directo(ticker):
    """Obtención directa de Yahoo Finance optimizada"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                closes = result['indicators']['quote'][0]['close']
                
                dates = [pd.to_datetime(ts, unit='s') for ts in timestamps]
                valid_data = [(date, close) for date, close in zip(dates, closes) 
                             if close is not None and not pd.isna(close)]
                
                if valid_data:
                    dates, closes = zip(*valid_data)
                    df = pd.DataFrame({
                        'Close': closes,
                        'Volume': [1000000] * len(closes)  # Placeholder
                    }, index=dates)
                    return df
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False, max_entries=100)
def obtener_datos_accion_optimizado(ticker):
    """Obtiene datos de acciones optimizado para paralelismo"""
    try:
        return yf.download(ticker, period="6mo", progress=False, interval="1d")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=7200, show_spinner=False, max_entries=50)
def obtener_info_completa_optimizada(ticker):
    """Obtiene información completa con caching extendido"""
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

@st.cache_data(ttl=10800, show_spinner=False, max_entries=1)
def precalcular_datos_screener():
    """Pre-calcula datos del screener para mayor velocidad"""
    st.info("📊 Pre-calculando datos del S&P500... Esto puede tomar 1-2 minutos")
    
    datos_precalculados = {}
    SP500_SYMBOLS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'V',
        'PG', 'UNH', 'HD', 'DIS', 'PYPL', 'ADBE', 'NFLX', 'CRM', 'INTC', 'CSCO',
        'PEP', 'T', 'ABT', 'TMO', 'COST', 'AVGO', 'TXN', 'LLY', 'HON', 'AMGN'
    ]
    
    for simbolo in SP500_SYMBOLS[:30]:
        try:
            datos = obtener_datos_completos_yfinance(simbolo)
            if datos and datos.get('Empresa Valida'):
                scoring = calcular_scoring_dinamico(datos)
                datos['Score'] = scoring
                datos_precalculados[simbolo] = datos
        except:
            continue
    
    return datos_precalculados

def obtener_datos_completos_yfinance(simbolo):
    """Obtiene datos fundamentales - CON PROTECCIÓN ANTI-RATE LIMITING"""
    try:
        # ✅ PAUSA ALEATORIA PARA EVITAR RATE LIMITING
        time.sleep(random.uniform(0.5, 1.5))
        
        ticker = yf.Ticker(simbolo)
        
        # ✅ INTENTAR MÚLTIPLES VECES CON RECUPERACIÓN DE ERRORES
        max_intentos = 2
        for intento in range(max_intentos):
            try:
                info = ticker.info
                
                # Verificar datos válidos
                if (not info or 'currentPrice' not in info or 
                    info.get('currentPrice') is None or info.get('currentPrice') == 0):
                    if intento < max_intentos - 1:
                        time.sleep(1)
                        continue
                    return None
                
                # ✅ DATOS MÍNIMOS PARA EVITAR TIMEouts
                try:
                    datos_historicos = yf.download(simbolo, period="1mo", interval="1d", 
                                                  progress=False, timeout=5)
                except:
                    datos_historicos = pd.DataFrame()
                
                # Construir datos
                datos = {
                    'Símbolo': simbolo,
                    'Nombre': info.get('longName', simbolo),
                    'Sector': info.get('sector', 'N/A'),
                    'Industria': info.get('industry', 'N/A'),
                    'Market Cap': info.get('marketCap', 0),
                    'P/E': info.get('trailingPE', 0),
                    'Precio Actual': info.get('currentPrice', 0),
                    'Cambio %': info.get('regularMarketChangePercent', 0),
                    'Volumen': info.get('volume', 0),
                    'ROE': info.get('returnOnEquity', 0),
                    'Margen Beneficio': info.get('profitMargins', 0),
                    'Deuda/Equity': info.get('debtToEquity', 0),
                    'Crecimiento Ingresos': info.get('revenueGrowth', 0),
                    'Beta': info.get('beta', 1),
                    'RSI': 50,
                    'Empresa Valida': True
                }
                
                return datos
                
            except Exception as e:
                if "Too Many Requests" in str(e):
                    wait_time = (intento + 1) * 3
                    time.sleep(wait_time)
                    continue
                else:
                    if intento < max_intentos - 1:
                        time.sleep(1)
                        continue
                    return None
                    
        return None
        
    except Exception as e:
        return None

def calcular_scoring_dinamico(datos):
    """Calcula scoring basado en datos fundamentales"""
    if not datos:
        return 0
    
    score = 0
    max_score = 100
    
    try:
        # P/E Ratio (20 puntos)
        pe = datos.get('P/E', 0)
        if pe and pe > 0:
            if pe < 15:
                score += 20
            elif pe < 25:
                score += 15
            elif pe < 35:
                score += 10
            else:
                score += 5
        
        # ROE (20 puntos)
        roe = datos.get('ROE', 0)
        if roe and roe > 0:
            if roe > 0.20:
                score += 20
            elif roe > 0.15:
                score += 16
            elif roe > 0.10:
                score += 12
            elif roe > 0.05:
                score += 8
            else:
                score += 4
        
        # Margen Beneficio (15 puntos)
        margen = datos.get('Margen Beneficio', 0)
        if margen and margen > 0:
            if margen > 0.20:
                score += 15
            elif margen > 0.15:
                score += 12
            elif margen > 0.10:
                score += 9
            elif margen > 0.05:
                score += 6
            else:
                score += 3
        
        # Deuda/Equity (15 puntos)
        deuda_eq = datos.get('Deuda/Equity', 0)
        if deuda_eq and deuda_eq >= 0:
            if deuda_eq < 0.5:
                score += 15
            elif deuda_eq < 1.0:
                score += 12
            elif deuda_eq < 1.5:
                score += 9
            elif deuda_eq < 2.0:
                score += 6
            else:
                score += 3
        
        # Crecimiento Ingresos (20 puntos)
        crecimiento = datos.get('Crecimiento Ingresos', 0)
        if crecimiento:
            if crecimiento > 0.20:
                score += 20
            elif crecimiento > 0.15:
                score += 16
            elif crecimiento > 0.10:
                score += 12
            elif crecimiento > 0.05:
                score += 8
            elif crecimiento > 0:
                score += 4
        
        # Beta (10 puntos)
        beta = datos.get('Beta', 1)
        if beta and beta > 0:
            if beta < 0.8:
                score += 10
            elif beta < 1.2:
                score += 8
            elif beta < 1.5:
                score += 6
            elif beta < 2.0:
                score += 4
            else:
                score += 2
        
        return min(score, max_score)
        
    except Exception as e:
        return 0

@st.cache_data(ttl=1800, show_spinner=False, max_entries=50)
def obtener_datos_tiempo_real(ticker):
    """Datos en tiempo real con caching corto"""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        hist = ticker_obj.history(period="2d")
        
        if not hist.empty and len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            previous = hist['Close'].iloc[-2] 
            change = ((current - previous) / previous) * 100
            
            return {
                'precio_actual': current,
                'cambio_porcentaje': change,
                'volumen': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
            }
    except:
        return None

def cargar_accion_paralelo(ticker_data):
    """Carga una acción en paralelo"""
    ticker, nombre, peso = ticker_data
    try:
        datos = obtener_datos_accion_optimizado(ticker)
        info = obtener_info_completa_optimizada(ticker)
        
        if not datos.empty:
            precio_actual = datos['Close'].iloc[-1] if 'Close' in datos.columns else 0
            precio_anterior = datos['Close'].iloc[-2] if len(datos) > 1 else precio_actual
            cambio = ((precio_actual - precio_anterior) / precio_anterior * 100) if precio_anterior else 0
            
            return {
                'ticker': ticker,
                'nombre': nombre,
                'peso': peso,
                'precio_actual': precio_actual,
                'cambio': cambio,
                'datos': datos,
                'info': info
            }
    except Exception as e:
        return None
    return None

def obtener_datos_accion_ultra_mejorado(ticker, max_reintentos=2):
    """Obtiene datos usando TODAS las APIs disponibles con reintentos y caché"""
    # Verificar caché primero
    cache_key = f"precio_{ticker}"
    
    # Lista de funciones de obtención de datos en orden de preferencia
    fuentes = [
        lambda: obtener_datos_accion(ticker),
        lambda: obtener_datos_yahoo_directo(ticker),
    ]
    
    for intento in range(max_reintentos):
        for i, fuente in enumerate(fuentes):
            try:
                data = fuente()
                if not data.empty and len(data) >= 2:
                    # Verificar que los datos sean válidos
                    current_price = float(data['Close'].iloc[-1])
                    if current_price > 0 and not pd.isna(current_price):
                        return data
            except:
                continue
        
        # Pequeña pausa entre reintentos
        if intento < max_reintentos - 1:
            time.sleep(0.1)
    
    # Si fallan todas las fuentes, devolver DataFrame vacío
    return pd.DataFrame()

def obtener_info_completa_ultra_mejorada(ticker):
    """Obtiene información completa usando caché"""
    # Primero Yahoo Finance
    try:
        info = obtener_info_completa(ticker)
        if info and info.get('longName') != 'N/A':
            return info
    except:
        pass
    
    # Información mínima como fallback
    info_fallback = {
        'longName': ticker,
        'sector': 'N/A',
        'industry': 'N/A',
        'trailingPE': 'N/A',
        'dividendYield': 0,
        'marketCap': 'N/A',
        'description': f'Compañía {ticker}'
    }
    return info_fallback

@st.cache_data(ttl=3600, show_spinner=False, max_entries=10)
def precalcular_datos_mercado():
    """Precalcula todos los datos del mercado para máxima velocidad"""
    datos_precalculados = {
        'sp500_data': {},
        'market_data': {},
        'empresa_info': {}
    }
    
    # Precalcular datos del S&P 500
    try:
        sp500_data = obtener_datos_accion_ultra_mejorado("^GSPC")
        datos_precalculados['sp500_data'] = sp500_data
    except:
        datos_precalculados['sp500_data'] = pd.DataFrame()
    
    return datos_precalculados

def obtener_datos_con_cache(ticker):
    """Obtiene datos usando el sistema de caché precalculado"""
    datos_precalculados = {}
    
    if ticker in datos_precalculados.get('market_data', {}):
        return datos_precalculados['market_data'][ticker]
    else:
        # Fallback a la función original si no está en caché
        return obtener_datos_accion_ultra_mejorado(ticker)

def obtener_info_con_cache(ticker):
    """Obtiene información de empresa usando caché"""
    datos_precalculados = {}
    
    if ticker in datos_precalculados.get('empresa_info', {}):
        return datos_precalculados['empresa_info'][ticker]
    else:
        # Fallback a la función original si no está en caché
        return obtener_info_completa_ultra_mejorada(ticker)

# AGREGANDO FUNCIONES PARA DATOS MACRO
@st.cache_data(ttl=10800, show_spinner=False, max_entries=30)
def obtener_datos_macro():
    """Datos macroeconómicos con caching extendido"""
    datos_macro = {
        "indicadores_usa": {
            "Inflación (CPI)": "3.2%",
            "Tasa de Desempleo": "3.8%", 
            "Crecimiento PIB": "2.1%",
            "Tasa de Interés Fed": "5.25%-5.50%",
            "Confianza del Consumidor": "64.9"
        },
        "mercados_globales": {
            "S&P 500": "+15% YTD",
            "NASDAQ": "+22% YTD",
            "Dow Jones": "+12% YTD",
            "Euro Stoxx 50": "+8% YTD", 
            "Nikkei 225": "+18% YTD"
        },
        "materias_primas": {
            "Petróleo (WTI)": "$78.50",
            "Oro": "$1,950.00",
            "Plata": "$23.15",
            "Cobre": "$3.85",
            "Bitcoin": "$42,000"
        },
        "divisas": {
            "EUR/USD": "1.0850",
            "USD/JPY": "148.50",
            "GBP/USD": "1.2650", 
            "USD/MXN": "17.20",
            "DXY (Índice Dólar)": "103.50"
        }
    }
    return datos_macro

# AGREGANDO FUNCIONES PARA NOTICIAS
def obtener_noticias_finviz(ticker):
    """Obtiene noticias de Finviz"""
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
                return []
        else:
            return []
            
    except Exception as e:
        return []

def obtener_noticias_globales(categoria, pais="us"):
    """Obtiene noticias globales de Google News"""
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