# sections/inicio.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import requests
import google.generativeai as genai
from utils.data_fetcher import obtener_datos_accion, obtener_info_completa

def mostrar_seccion_inicio():
    """
    Muestra la sección de inicio con el dashboard del S&P 500
    """
    st.header("🏠 Análisis de las 20 Acciones de cada sector del S&P 500 en Tiempo Real")
    
    # Precalcular datos del mercado
    datos_mercado = _precalcular_datos_mercado()
    
    # Mostrar métricas del S&P 500
    _mostrar_metricas_sp500(datos_mercado)
    
    # Mostrar componentes del S&P 500 por sector
    _mostrar_componentes_sp500(datos_mercado)
    
    # Mostrar estadísticas del mercado
    _mostrar_estadisticas_mercado(datos_mercado)

def _precalcular_datos_mercado():
    """
    Precalcula todos los datos del mercado para máxima velocidad
    """
    if 'datos_mercado_precalculados' in st.session_state:
        return st.session_state.datos_mercado_precalculados
    
    # Inicializar estructura de datos
    datos_precalculados = {
        'sp500_data': {},
        'market_data': {},
        'empresa_info': {},
        'sectores': _obtener_componentes_sp500()
    }
    
    # Precalcular datos del S&P 500
    with st.spinner('🔄 Precalculando datos del mercado...'):
        try:
            sp500_data = obtener_datos_accion("^GSPC")
            datos_precalculados['sp500_data'] = sp500_data
        except:
            datos_precalculados['sp500_data'] = pd.DataFrame()
        
        # Precalcular información de empresas
        todos_los_tickers = []
        for sector, stocks in datos_precalculados['sectores'].items():
            for stock in stocks:
                todos_los_tickers.append(stock["ticker"])
        
        # Limitar a 100 tickers para demo
        tickers_rapidos = todos_los_tickers[:160]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers_rapidos):
            try:
                # Precalcular datos de precio
                stock_data = obtener_datos_accion(ticker)
                if not stock_data.empty and len(stock_data) >= 2:
                    datos_precalculados['market_data'][ticker] = stock_data
                
                # Precalcular info de empresa
                company_info = obtener_info_completa(ticker)
                datos_precalculados['empresa_info'][ticker] = company_info
                
                # Actualizar progreso
                if i % 10 == 0:
                    progress_percent = (i + 1) / len(tickers_rapidos)
                    progress_bar.progress(progress_percent)
                    status_text.text(f"Precalculando: {i+1}/{len(tickers_rapidos)} acciones")
                    
            except Exception as e:
                continue
        
        progress_bar.empty()
        status_text.empty()
    
    st.session_state.datos_mercado_precalculados = datos_precalculados
    return datos_precalculados

def _obtener_componentes_sp500():
    """
    Retorna la lista completa de componentes del S&P 500 por sector
    """
    return {
        "TECHNOLOGY": [
            {"ticker": "AAPL", "name": "Apple Inc.", "weight": 7.2},
            {"ticker": "MSFT", "name": "Microsoft Corp", "weight": 6.8},
            {"ticker": "NVDA", "name": "NVIDIA Corporation", "weight": 2.9},
            {"ticker": "AVGO", "name": "Broadcom Inc.", "weight": 1.2},
            {"ticker": "CRM", "name": "Salesforce Inc.", "weight": 0.8},
            {"ticker": "ADBE", "name": "Adobe Inc.", "weight": 0.7},
            {"ticker": "CSCO", "name": "Cisco Systems", "weight": 0.6},
            {"ticker": "ACN", "name": "Accenture PLC", "weight": 0.6},
            {"ticker": "ORCL", "name": "Oracle Corp", "weight": 0.5},
            {"ticker": "IBM", "name": "IBM Corporation", "weight": 0.4},
            {"ticker": "INTC", "name": "Intel Corp", "weight": 0.4},
            {"ticker": "AMD", "name": "Advanced Micro Devices", "weight": 0.4},
            {"ticker": "QCOM", "name": "Qualcomm Inc.", "weight": 0.3},
            {"ticker": "TXN", "name": "Texas Instruments", "weight": 0.3},
            {"ticker": "NOW", "name": "ServiceNow Inc.", "weight": 0.3},
            {"ticker": "AMAT", "name": "Applied Materials", "weight": 0.3},
            {"ticker": "LRCX", "name": "Lam Research", "weight": 0.3},
            {"ticker": "KLAC", "name": "KLA Corporation", "weight": 0.2},
            {"ticker": "INTU", "name": "Intuit Inc.", "weight": 0.2},
            {"ticker": "ADI", "name": "Analog Devices", "weight": 0.2}
        ],
        "HEALTHCARE": [
            {"ticker": "LLY", "name": "Eli Lilly & Co", "weight": 1.4},
            {"ticker": "UNH", "name": "UnitedHealth Group", "weight": 1.3},
            {"ticker": "JNJ", "name": "Johnson & Johnson", "weight": 1.1},
            {"ticker": "MRK", "name": "Merck & Co.", "weight": 0.6},
            {"ticker": "ABBV", "name": "AbbVie Inc.", "weight": 0.6},
            {"ticker": "TMO", "name": "Thermo Fisher Scientific", "weight": 0.5},
            {"ticker": "PFE", "name": "Pfizer Inc.", "weight": 0.4},
            {"ticker": "ABT", "name": "Abbott Laboratories", "weight": 0.4},
            {"ticker": "DHR", "name": "Danaher Corp", "weight": 0.4},
            {"ticker": "CVS", "name": "CVS Health Corp", "weight": 0.3},
            {"ticker": "MDT", "name": "Medtronic PLC", "weight": 0.3},
            {"ticker": "AMGN", "name": "Amgen Inc.", "weight": 0.3},
            {"ticker": "BMY", "name": "Bristol-Myers Squibb", "weight": 0.3},
            {"ticker": "CI", "name": "Cigna Corporation", "weight": 0.2},
            {"ticker": "HUM", "name": "Humana Inc.", "weight": 0.2},
            {"ticker": "ELV", "name": "Elevance Health", "weight": 0.2},
            {"ticker": "GILD", "name": "Gilead Sciences", "weight": 0.2},
            {"ticker": "VRTX", "name": "Vertex Pharmaceuticals", "weight": 0.2},
            {"ticker": "REGN", "name": "Regeneron Pharmaceuticals", "weight": 0.2},
            {"ticker": "ISRG", "name": "Intuitive Surgical", "weight": 0.2}
        ],
        "FINANCIALS": [
            {"ticker": "BRK-B", "name": "Berkshire Hathaway", "weight": 1.7},
            {"ticker": "JPM", "name": "JPMorgan Chase", "weight": 1.1},
            {"ticker": "V", "name": "Visa Inc.", "weight": 1.0},
            {"ticker": "MA", "name": "Mastercard Inc.", "weight": 0.7},
            {"ticker": "BAC", "name": "Bank of America", "weight": 0.6},
            {"ticker": "WFC", "name": "Wells Fargo", "weight": 0.4},
            {"ticker": "GS", "name": "Goldman Sachs", "weight": 0.4},
            {"ticker": "MS", "name": "Morgan Stanley", "weight": 0.3},
            {"ticker": "BLK", "name": "BlackRock Inc.", "weight": 0.3},
            {"ticker": "AXP", "name": "American Express", "weight": 0.3},
            {"ticker": "SCHW", "name": "Charles Schwab", "weight": 0.3},
            {"ticker": "C", "name": "Citigroup Inc.", "weight": 0.2},
            {"ticker": "PYPL", "name": "PayPal Holdings", "weight": 0.2},
            {"ticker": "SPGI", "name": "S&P Global Inc.", "weight": 0.2},
            {"ticker": "MCO", "name": "Moody's Corporation", "weight": 0.2},
            {"ticker": "ICE", "name": "Intercontinental Exchange", "weight": 0.2},
            {"ticker": "CME", "name": "CME Group Inc.", "weight": 0.2},
            {"ticker": "TFC", "name": "Truist Financial", "weight": 0.1},
            {"ticker": "PNC", "name": "PNC Financial", "weight": 0.1},
            {"ticker": "USB", "name": "U.S. Bancorp", "weight": 0.1}
        ],
        "CONSUMER & INDUSTRIAL": [
            {"ticker": "AMZN", "name": "Amazon.com Inc.", "weight": 3.5},
            {"ticker": "TSLA", "name": "Tesla Inc.", "weight": 1.6},
            {"ticker": "HD", "name": "Home Depot", "weight": 0.6},
            {"ticker": "PG", "name": "Procter & Gamble", "weight": 0.6},
            {"ticker": "MCD", "name": "McDonald's Corp", "weight": 0.5},
            {"ticker": "COST", "name": "Costco Wholesale", "weight": 0.5},
            {"ticker": "KO", "name": "Coca-Cola Company", "weight": 0.4},
            {"ticker": "PEP", "name": "PepsiCo Inc.", "weight": 0.4},
            {"ticker": "WMT", "name": "Walmart Inc.", "weight": 0.4},
            {"ticker": "NKE", "name": "Nike Inc.", "weight": 0.4},
            {"ticker": "LOW", "name": "Lowe's Companies", "weight": 0.3},
            {"ticker": "SBUX", "name": "Starbucks Corp", "weight": 0.3},
            {"ticker": "PM", "name": "Philip Morris Int", "weight": 0.3},
            {"ticker": "TJX", "name": "TJX Companies", "weight": 0.2},
            {"ticker": "TGT", "name": "Target Corp", "weight": 0.2},
            {"ticker": "BKNG", "name": "Booking Holdings", "weight": 0.2},
            {"ticker": "ORLY", "name": "O'Reilly Automotive", "weight": 0.2},
            {"ticker": "MO", "name": "Altria Group", "weight": 0.2},
            {"ticker": "MDLZ", "name": "Mondelez Intl", "weight": 0.2},
            {"ticker": "CL", "name": "Colgate-Palmolive", "weight": 0.2}
        ],
        "ENERGY & UTILITIES": [
            {"ticker": "XOM", "name": "Exxon Mobil", "weight": 0.8},
            {"ticker": "CVX", "name": "Chevron Corp", "weight": 0.6},
            {"ticker": "NEE", "name": "NextEra Energy", "weight": 0.3},
            {"ticker": "COP", "name": "ConocoPhillips", "weight": 0.3},
            {"ticker": "DUK", "name": "Duke Energy", "weight": 0.2},
            {"ticker": "SO", "name": "Southern Company", "weight": 0.2},
            {"ticker": "SLB", "name": "Schlumberger", "weight": 0.2},
            {"ticker": "EOG", "name": "EOG Resources", "weight": 0.2},
            {"ticker": "PSX", "name": "Phillips 66", "weight": 0.1},
            {"ticker": "MPC", "name": "Marathon Petroleum", "weight": 0.1},
            {"ticker": "VLO", "name": "Valero Energy", "weight": 0.1},
            {"ticker": "OXY", "name": "Occidental Petroleum", "weight": 0.1},
            {"ticker": "KMI", "name": "Kinder Morgan", "weight": 0.1},
            {"ticker": "WMB", "name": "Williams Companies", "weight": 0.1},
            {"ticker": "HES", "name": "Hess Corporation", "weight": 0.1},
            {"ticker": "OKE", "name": "ONEOK Inc.", "weight": 0.1},
            {"ticker": "DVN", "name": "Devon Energy", "weight": 0.1},
            {"ticker": "PXD", "name": "Pioneer Natural Resources", "weight": 0.1},
            {"ticker": "FANG", "name": "Diamondback Energy", "weight": 0.1},
            {"ticker": "ETR", "name": "Entergy Corporation", "weight": 0.1}
        ],
        "COMMUNICATION SERVICES": [
            {"ticker": "GOOGL", "name": "Alphabet Inc.", "weight": 2.1},
            {"ticker": "GOOG", "name": "Alphabet Inc. C", "weight": 1.9},
            {"ticker": "META", "name": "Meta Platforms", "weight": 2.0},
            {"ticker": "NFLX", "name": "Netflix Inc.", "weight": 0.3},
            {"ticker": "DIS", "name": "Walt Disney Company", "weight": 0.4},
            {"ticker": "CMCSA", "name": "Comcast Corporation", "weight": 0.3},
            {"ticker": "T", "name": "AT&T Inc.", "weight": 0.3},
            {"ticker": "VZ", "name": "Verizon Communications", "weight": 0.3},
            {"ticker": "TMUS", "name": "T-Mobile US", "weight": 0.2},
            {"ticker": "CHTR", "name": "Charter Communications", "weight": 0.1},
            {"ticker": "EA", "name": "Electronic Arts", "weight": 0.1},
            {"ticker": "TTWO", "name": "Take-Two Interactive", "weight": 0.1},
            {"ticker": "ATVI", "name": "Activision Blizzard", "weight": 0.1},
            {"ticker": "LYV", "name": "Live Nation Entertainment", "weight": 0.1},
            {"ticker": "OMC", "name": "Omnicom Group", "weight": 0.1},
            {"ticker": "IPG", "name": "Interpublic Group", "weight": 0.1},
            {"ticker": "FOXA", "name": "Fox Corporation", "weight": 0.1},
            {"ticker": "FOX", "name": "Fox Corporation", "weight": 0.1},
            {"ticker": "PARA", "name": "Paramount Global", "weight": 0.1},
            {"ticker": "WBD", "name": "Warner Bros Discovery", "weight": 0.1}
        ]
    }

def _mostrar_metricas_sp500(datos_mercado):
    """
    Muestra las métricas principales del S&P 500
    """
    st.markdown("### 📊 S&P 500 INDEX OVERVIEW")
    
    # Obtener datos del S&P 500
    sp500_data = datos_mercado.get('sp500_data', pd.DataFrame())
    
    if not sp500_data.empty and len(sp500_data) >= 2:
        current_sp500 = float(sp500_data['Close'].iloc[-1])
        previous_sp500 = float(sp500_data['Close'].iloc[-2])
        sp500_change = ((current_sp500 - previous_sp500) / previous_sp500) * 100
        sp500_change_abs = current_sp500 - previous_sp500
    else:
        # Datos de respaldo
        current_sp500 = 4780.94
        previous_sp500 = 4750.79
        sp500_change = 0.63
        sp500_change_abs = 30.15
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="S&P 500 INDEX",
            value=f"{current_sp500:,.2f}",
            delta=f"{sp500_change_abs:+.2f} ({sp500_change:+.2f}%)",
            delta_color="normal"
        )
    
    with col2:
        # Calcular YTD
        try:
            current_year = datetime.now().year
            start_of_year = pd.Timestamp(f'{current_year}-01-01')
            
            ytd_prices = sp500_data[sp500_data.index >= start_of_year]
            if len(ytd_prices) > 0:
                ytd_start_price = float(ytd_prices['Close'].iloc[0])
                ytd_return = ((current_sp500 - ytd_start_price) / ytd_start_price) * 100
                st.metric(
                    label="YTD PERFORMANCE",
                    value=f"{ytd_return:+.1f}%",
                    delta_color="normal"
                )
            else:
                st.metric(label="YTD PERFORMANCE", value="N/A")
        except:
            st.metric(label="YTD PERFORMANCE", value="N/A")
    
    with col3:
        # Calcular P/E ratio promedio
        pe_ratio = _calcular_pe_promedio(datos_mercado)
        st.metric(
            label="P/E RATIO",
            value=f"{pe_ratio:.1f}",
            delta_color="off"
        )

    with col4:
        # Calcular dividend yield promedio
        dividend_yield = _calcular_dividend_yield_promedio(datos_mercado)
        st.metric(
            label="DIVIDEND YIELD",
            value=f"{dividend_yield:.2f}%",
            delta_color="off"
        )
    
    with col5:
        # Market Cap total estimado
        market_cap = _calcular_market_cap_estimado(datos_mercado)
        st.metric(
            label="EST. MARKET CAP",
            value=f"${market_cap/1e12:.1f}T",
            delta_color="off"
        )

def _calcular_pe_promedio(datos_mercado):
    """Calcula el P/E ratio promedio ponderado"""
    try:
        total_pe = 0
        total_weight_pe = 0
        
        for sector, stocks in datos_mercado['sectores'].items():
            for stock in stocks:
                ticker = stock["ticker"]
                if (ticker in datos_mercado['empresa_info'] and 
                    datos_mercado['empresa_info'][ticker].get('trailingPE') not in [None, 'N/A']):
                    try:
                        pe = float(datos_mercado['empresa_info'][ticker]['trailingPE'])
                        if 0 < pe < 100:
                            weight = stock.get('weight', 0.1)
                            total_pe += pe * weight
                            total_weight_pe += weight
                    except:
                        continue
        
        return total_pe / total_weight_pe if total_weight_pe > 0 else 22.5
    except:
        return 22.5

def _calcular_dividend_yield_promedio(datos_mercado):
    """Calcula el dividend yield promedio ponderado"""
    try:
        total_dy = 0
        total_weight_dy = 0
        
        for sector, stocks in datos_mercado['sectores'].items():
            for stock in stocks:
                ticker = stock["ticker"]
                if (ticker in datos_mercado['empresa_info'] and 
                    datos_mercado['empresa_info'][ticker].get('dividendYield') not in [None, 'N/A']):
                    try:
                        dy = float(datos_mercado['empresa_info'][ticker]['dividendYield'])
                        if 0 <= dy < 0.1:
                            weight = stock.get('weight', 0.1)
                            total_dy += dy * weight
                            total_weight_dy += weight
                    except:
                        continue
        
        return (total_dy / total_weight_dy * 100) if total_weight_dy > 0 else 1.42
    except:
        return 1.42

def _calcular_market_cap_estimado(datos_mercado):
    """Calcula el market cap total estimado"""
    try:
        total_market_cap = 0
        count = 0
        for sector, stocks in datos_mercado['sectores'].items():
            for stock in stocks:
                ticker = stock["ticker"]
                if (ticker in datos_mercado['empresa_info'] and 
                    datos_mercado['empresa_info'][ticker].get('marketCap') not in [None, 'N/A']):
                    try:
                        market_cap = float(datos_mercado['empresa_info'][ticker]['marketCap'])
                        total_market_cap += market_cap
                        count += 1
                    except:
                        continue
        
        if count > 0:
            avg_market_cap = total_market_cap / count
            total_stocks = sum(len(stocks) for stocks in datos_mercado['sectores'].values())
            return avg_market_cap * total_stocks
        else:
            return 40e12  # Valor por defecto
    except:
        return 40e12

def _mostrar_componentes_sp500(datos_mercado):
    """
    Muestra los componentes del S&P 500 organizados por sector
    """
    st.markdown("### 🏢 COMPONENTES DEL S&P 500 - DATOS EN TIEMPO REAL")
    
    # Procesar datos de mercado
    market_data = _procesar_datos_mercado(datos_mercado)
    
    # Mostrar sectores con tabs
    tabs = st.tabs(list(market_data.keys()))
    
    for tab_idx, (sector, stocks) in enumerate(market_data.items()):
        with tabs[tab_idx]:
            if not stocks:
                st.warning(f"No hay datos disponibles para {sector}")
                continue
                
            st.markdown(f"#### 📈 {sector} - {len(stocks)} Acciones")
            
            # Búsqueda y filtrado
            search_col, filter_col = st.columns([2, 1])
            with search_col:
                search_term = st.text_input(f"🔍 Buscar en {sector}", key=f"search_{sector}")
            
            with filter_col:
                filter_option = st.selectbox(
                    "Filtrar por:",
                    ["Todos", "Alza (+)", "Baja (-)", "Top 10 por Peso"],
                    key=f"filter_{sector}"
                )
            
            # Aplicar filtros
            filtered_stocks = stocks
            if search_term:
                filtered_stocks = [s for s in filtered_stocks 
                                 if search_term.upper() in s["ticker"] or 
                                 search_term.lower() in s["name"].lower()]
            
            if filter_option == "Alza (+)":
                filtered_stocks = [s for s in filtered_stocks if s["change"] > 0]
            elif filter_option == "Baja (-)":
                filtered_stocks = [s for s in filtered_stocks if s["change"] < 0]
            elif filter_option == "Top 10 por Peso":
                filtered_stocks = sorted(filtered_stocks, key=lambda x: x["weight"], reverse=True)[:10]
            
            if not filtered_stocks:
                st.warning("No hay acciones que coincidan con los filtros aplicados")
                continue
            
            # Mostrar acciones en filas de 5
            for i in range(0, len(filtered_stocks), 5):
                row_stocks = filtered_stocks[i:i+5]
                cols = st.columns(5)
                
                for idx, stock in enumerate(row_stocks):
                    with cols[idx]:
                        _mostrar_tarjeta_accion(stock, i, idx)

def _procesar_datos_mercado(datos_mercado):
    """
    Procesa los datos del mercado para mostrar en la interfaz
    """
    market_data = {}
    
    for sector, stocks in datos_mercado['sectores'].items():
        market_data[sector] = []
        for stock in stocks:
            ticker = stock["ticker"]
            
            # Obtener datos del stock
            if ticker in datos_mercado['market_data']:
                stock_data = datos_mercado['market_data'][ticker]
                if not stock_data.empty and len(stock_data) >= 2:
                    try:
                        current_price = float(stock_data['Close'].iloc[-1])
                        previous_price = float(stock_data['Close'].iloc[-2])
                        change = ((current_price - previous_price) / previous_price) * 100
                        
                        market_data[sector].append({
                            **stock,
                            "current_price": current_price,
                            "change": change,
                            "volume": float(stock_data['Volume'].iloc[-1]) if 'Volume' in stock_data.columns else 0,
                            "market_cap": datos_mercado['empresa_info'].get(ticker, {}).get('marketCap', 'N/A'),
                            "sector": sector,
                            "fuente": "real"
                        })
                        continue
                    except:
                        pass
            
            # Datos simulados como fallback
            precio_simulado = 50 + (hash(ticker) % 200)
            cambio_simulado = (hash(ticker) % 40 - 20) / 10
            
            market_data[sector].append({
                **stock,
                "current_price": precio_simulado,
                "change": cambio_simulado,
                "volume": 1000000,
                "market_cap": 'N/A',
                "sector": sector,
                "fuente": "simulado"
            })
    
    return market_data

def _mostrar_tarjeta_accion(stock, row_idx, col_idx):
    """
    Muestra una tarjeta individual de acción
    """
    change_color = "#4CAF50" if stock["change"] >= 0 else "#F44336"
    change_icon = "📈" if stock["change"] >= 0 else "📉"
    
    st.markdown(f"""
    <div style='background: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #374151; 
                text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: space-between;'>
        <div>
            <div style='font-weight: bold; color: white; font-size: 14px; margin-bottom: 5px;'>{stock["ticker"]}</div>
            <div style='color: #9ca3af; font-size: 11px; margin-bottom: 8px; line-height: 1.2;'>
                {stock["name"][:25]}{'...' if len(stock["name"]) > 25 else ''}
            </div>
        </div>
        <div>
            <div style='color: white; font-weight: bold; font-size: 13px; margin-bottom: 4px;'>
                ${stock["current_price"]:,.2f}
            </div>
            <div style='color: {change_color}; font-size: 12px; font-weight: bold;'>
                {change_icon} {stock["change"]:+.2f}%
            </div>
            <div style='color: #6b7280; font-size: 10px; margin-top: 4px;'>
                Weight: {stock["weight"]}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón para análisis IA
    if st.button(f"🤖 Analizar {stock['ticker']}", 
               key=f"ia_{stock['ticker']}_{row_idx}_{col_idx}",
               use_container_width=True,
               type="primary"):
        _generar_analisis_ia(stock)

def _generar_analisis_ia(stock):
    """
    Genera análisis IA para una acción
    """
    with st.spinner(f'Generando análisis IA para {stock["ticker"]}...'):
        try:
            prompt = f"""
            Proporciona un análisis conciso de {stock["name"]} ({stock["ticker"]}) basado en:
            - Precio actual: ${stock["current_price"]:.2f}
            - Cambio del día: {stock["change"]:+.2f}%
            - Sector: {stock["sector"]}
            - Peso en S&P 500: {stock["weight"]}%
            
            Incluye en máximo 100 palabras:
            1. Evaluación rápida del movimiento
            2. Contexto del sector
            3. Recomendación breve (Observar/Considerar/Monitorear)
            
            Sé profesional pero conciso.
            """
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            st.session_state.analisis_actual = {
                "ticker": stock["ticker"],
                "nombre": stock["name"],
                "analisis": response.text,
                "precio": stock["current_price"],
                "cambio": stock["change"]
            }
            st.rerun()
            
        except Exception as e:
            st.error(f"Error en análisis IA: {str(e)}")

def _mostrar_estadisticas_mercado(datos_mercado):
    """
    Muestra estadísticas generales del mercado
    """
    st.markdown("### 📈 ESTADÍSTICAS DEL MERCADO")
    
    # Calcular estadísticas
    todos_los_cambios = []
    for sector, stocks in datos_mercado['sectores'].items():
        for stock in stocks:
            # Buscar datos reales o usar simulados
            if stock["ticker"] in datos_mercado['market_data']:
                stock_data = datos_mercado['market_data'][stock["ticker"]]
                if not stock_data.empty and len(stock_data) >= 2:
                    try:
                        current_price = float(stock_data['Close'].iloc[-1])
                        previous_price = float(stock_data['Close'].iloc[-2])
                        change = ((current_price - previous_price) / previous_price) * 100
                        todos_los_cambios.append(change)
                        continue
                    except:
                        pass
            
            # Usar cambio simulado
            cambio_simulado = (hash(stock["ticker"]) % 40 - 20) / 10
            todos_los_cambios.append(cambio_simulado)
    
    if todos_los_cambios:
        promedio_cambios = sum(todos_los_cambios) / len(todos_los_cambios)
        acciones_alcistas = sum(1 for cambio in todos_los_cambios if cambio > 0)
        porcentaje_alcistas = (acciones_alcistas / len(todos_los_cambios)) * 100
    else:
        promedio_cambios = 0
        porcentaje_alcistas = 0
    
    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <div style='font-size: 24px; font-weight: bold;'>{porcentaje_alcistas:.1f}%</div>
            <div style='font-size: 12px;'>ACCIONES EN ALZA</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat2:
        cambio_color = "#4CAF50" if promedio_cambios >= 0 else "#F44336"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <div style='font-size: 24px; font-weight: bold; color: {cambio_color};'>{promedio_cambios:+.2f}%</div>
            <div style='font-size: 12px;'>CAMBIO PROMEDIO</div>
        </div>
        """, unsafe_allow_html=True)

    # Mostrar análisis actual si existe
    if 'analisis_actual' in st.session_state and st.session_state.analisis_actual:
        _mostrar_analisis_actual()

def _mostrar_analisis_actual():
    """
    Muestra el análisis IA actual
    """
    st.markdown("---")
    st.markdown("### 🧠 ANÁLISIS IA - " + st.session_state.analisis_actual["ticker"])
    
    analisis = st.session_state.analisis_actual
    cambio = analisis["cambio"]
    color_borde = "#4CAF50" if cambio >= 0 else "#F44336"
    
    st.markdown(f"""
    <div style='background: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 6px solid {color_borde}; 
                border: 1px solid #374151; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;'>
            <div>
                <h4 style='color: white; margin: 0 0 5px 0;'>{analisis["nombre"]}</h4>
                <div style='color: #9ca3af; font-size: 14px;'>{analisis["ticker"]}</div>
            </div>
            <div style='text-align: right;'>
                <div style='color: white; font-size: 18px; font-weight: bold;'>
                    ${analisis["precio"]:,.2f}
                </div>
                <div style='color: {color_borde}; font-size: 14px; font-weight: bold;'>
                    {cambio:+.2f}%
                </div>
            </div>
        </div>
        <div style='color: #e5e7eb; font-size: 14px; line-height: 1.5; background: #2d3748; padding: 15px; border-radius: 6px;'>
            {analisis["analisis"]}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón para limpiar análisis
    if st.button("🗑️ Cerrar Análisis", use_container_width=True):
        del st.session_state.analisis_actual
        st.rerun()

# Función para limpiar caché
def limpiar_cache_mercado():
    """Limpia el caché del mercado"""
    if 'datos_mercado_precalculados' in st.session_state:
        del st.session_state.datos_mercado_precalculados
    if 'analisis_actual' in st.session_state:
        del st.session_state.analisis_actual

# ---------------------------------------------------------
# >>> AÑADIDO DE COMPATIBILIDAD (NO TOCA NADA DE TU LÓGICA)
# ---------------------------------------------------------
# Este pequeño wrapper mantiene **exactamente** toda tu implementación original
# y expone la función `mostrar(datos_accion)` que App.py espera.
def mostrar(datos_accion=None):
    """
    Wrapper de compatibilidad: App.py llama a inicio.mostrar(datos_accion)
    Esta función recibe (opcionalmente) los datos que envía App.py y los guarda
    en session_state para que puedas accederlos desde aquí si lo deseas.
    Luego llama a la función real que renderiza la sección.
    """
    # Guardar los datos recibidos (si vienen) para su uso dentro de la sección
    if datos_accion is not None:
        st.session_state['datos_accion_inicio'] = datos_accion

    # Llamar a la función principal de tu módulo (sin modificarla)
    mostrar_seccion_inicio()

# Función principal para testing
if __name__ == "__main__":
    st.title("🔍 Prueba - Sección Inicio")
    mostrar_seccion_inicio()
    
    # Botón para limpiar caché
    if st.button("🗑️ Limpiar Caché de Mercado", type="secondary"):
        limpiar_cache_mercado()
        st.success("✅ Caché limpiado. Los datos se recargarán.")
        st.rerun()