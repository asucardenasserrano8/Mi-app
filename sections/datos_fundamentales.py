# sections/datos_fundamentales.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Gemini
GOOGLE_KEY = os.getenv("AP")
if GOOGLE_KEY:
    genai.configure(api_key=GOOGLE_KEY)

# FUNCIONES ORIGINALES SIN MODIFICAR (copiadas exactamente de tu código)

def extraer_tabla_finviz(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer TODOS los datos de la tabla snapshot de Finviz
            tabla_snapshot = soup.find('table', class_='snapshot-table2')
            
            if tabla_snapshot:
                datos = {}
                
                # Extraer en el formato exacto de Finviz (pares clave-valor)
                filas = tabla_snapshot.find_all('tr')
                
                for fila in filas:
                    celdas = fila.find_all('td')
                    for i in range(0, len(celdas) - 1, 2):
                        if i + 1 < len(celdas):
                            clave = celdas[i].get_text(strip=True)
                            valor = celdas[i + 1].get_text(strip=True)
                            if clave and valor:
                                datos[clave] = valor
                
                return datos
            else:
                return {}
        else:
            return {}
            
    except Exception as e:
        return {}

def calcular_skewness_kurtosis(returns):
    """
    Calcula skewness y kurtosis de una serie de retornos
    """
    try:
        n = len(returns)
        if n < 4:
            return 0, 0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0, 0
        
        # Skewness
        skew = np.sum((returns - mean) ** 3) / (n * std ** 3)
        
        # Kurtosis (Fisher's definition, excess kurtosis)
        kurt = np.sum((returns - mean) ** 4) / (n * std ** 4) - 3
        
        return skew, kurt
        
    except Exception as e:
        return 0, 0

def calcular_metricas_riesgo_avanzadas(ticker_symbol, periodo_años=5):
    """
    Calcula métricas avanzadas de riesgo MEJORADAS para una acción
    """
    try:
        # Descargar datos históricos
        end_date = datetime.today()
        start_date = end_date - timedelta(days=periodo_años * 365)
        
        # Datos de la acción
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
        if stock_data.empty or len(stock_data) == 0:
            return None
            
        # Datos del mercado (S&P500 como benchmark)
        market_data = yf.download('^GSPC', start=start_date, end=end_date, interval='1d')
        if market_data.empty or len(market_data) == 0:
            return None
        
        # Asegurarnos de que tenemos columnas de cierre
        if 'Close' not in stock_data.columns or 'Close' not in market_data.columns:
            return None
        
        # Calcular rendimientos diarios - manejar MultiIndex
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_close = stock_data[('Close', ticker_symbol)]
        else:
            stock_close = stock_data['Close']
            
        if isinstance(market_data.columns, pd.MultiIndex):
            market_close = market_data[('Close', '^GSPC')]
        else:
            market_close = market_data['Close']
        
        stock_returns = stock_close.pct_change().dropna()
        market_returns = market_close.pct_change().dropna()
        
        # Alinear las fechas
        common_dates = stock_returns.index.intersection(market_returns.index)
        if len(common_dates) == 0:
            return None
            
        stock_returns = stock_returns.loc[common_dates]
        market_returns = market_returns.loc[common_dates]
        
        if len(stock_returns) < 30:  # Mínimo de datos
            return None
        
        # Convertir a arrays numpy para evitar problemas con Series
        stock_returns_array = stock_returns.values
        market_returns_array = market_returns.values
        
        # 1. CALCULAR BETA
        covariance = np.cov(stock_returns_array, market_returns_array)[0, 1]
        market_variance = np.var(market_returns_array)
        beta = covariance / market_variance if market_variance != 0 else 0
        
        # 2. CALCULAR ALPHA
        stock_total_return = (stock_close.iloc[-1] / stock_close.iloc[0] - 1)
        market_total_return = (market_close.iloc[-1] / market_close.iloc[0] - 1)
        alpha = stock_total_return - (beta * market_total_return)
        
        # 3. CALCULAR SHARPE RATIO
        risk_free_rate = 0.02 / 252  # Tasa diaria
        excess_returns = stock_returns_array - risk_free_rate
        sharpe_ratio = (np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) 
                      if np.std(excess_returns) != 0 else 0)
        
        # 4. CALCULAR SORTINO RATIO
        downside_returns = stock_returns_array[stock_returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino_ratio = (np.mean(excess_returns) / downside_std * np.sqrt(252) 
                       if downside_std != 0 else 0)
        
        # 5. CALCULAR TREYNOR RATIO
        treynor_ratio = (stock_total_return - 0.02) / beta if beta != 0 else 0
        
        # 6. CALCULAR INFORMATION RATIO
        active_returns = stock_returns_array - market_returns_array
        tracking_error = np.std(active_returns) * np.sqrt(252) if len(active_returns) > 0 else 0
        information_ratio = (stock_total_return - market_total_return) / tracking_error if tracking_error != 0 else 0
        
        # 7. CALCULAR VALUE AT RISK (VaR)
        var_95 = np.percentile(stock_returns_array, 5)
        var_95_annual = var_95 * np.sqrt(252)
        var_99 = np.percentile(stock_returns_array, 1)
        var_99_annual = var_99 * np.sqrt(252)
        
        # 8. CALCULAR EXPECTED SHORTFALL (CVaR)
        cvar_95 = stock_returns_array[stock_returns_array <= var_95].mean()
        cvar_95_annual = cvar_95 * np.sqrt(252) if not np.isnan(cvar_95) else 0
        
        # 9. CALCULAR DRAWDOWN MÁXIMO
        cumulative_returns = (1 + stock_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Calcular duración del drawdown máximo
        max_dd_idx = drawdown.idxmin()
        max_dd_start = drawdown[drawdown == 0].last_valid_index()
        if max_dd_start is not None:
            max_dd_duration = (max_dd_idx - max_dd_start).days
        else:
            max_dd_duration = 0
        
        # 10. CALCULAR VOLATILIDAD ANUALIZADA
        volatility_annual = np.std(stock_returns_array) * np.sqrt(252)
        
        # 11. CALCULAR CORRELACIONES CON MÚLTIPLES ÍNDICES 
        correlation_sp500 = np.corrcoef(stock_returns_array, market_returns_array)[0, 1]
        
        # 12. CALCULAR MÁXIMO GANANCIA/PÉRDIDA CONSECUTIVA 
        positive_streak = 0
        negative_streak = 0
        max_positive_streak = 0
        max_negative_streak = 0
        
        for ret in stock_returns_array:
            if ret > 0:
                positive_streak += 1
                negative_streak = 0
                max_positive_streak = max(max_positive_streak, positive_streak)
            elif ret < 0:
                negative_streak += 1
                positive_streak = 0
                max_negative_streak = max(max_negative_streak, negative_streak)
        
        # 13. CALCULAR SKEWNESS Y KURTOSIS
        skewness, kurtosis = calcular_skewness_kurtosis(stock_returns_array)
        
        # 14. CALCULAR PROBABILIDAD DE PÉRDIDA
        prob_loss = np.mean(stock_returns_array < 0) * 100
        
        return {
            # Métricas básicas
            'Beta': round(beta, 4),
            'Alpha': round(alpha, 4),
            'Sharpe Ratio': round(sharpe_ratio, 4),
            'Sortino Ratio': round(sortino_ratio, 4),
            'Treynor Ratio': round(treynor_ratio, 4),
            'Information Ratio': round(information_ratio, 4),
            
            # Métricas de riesgo
            'VaR 95% Diario': round(var_95, 4),
            'VaR 95% Anual': round(var_95_annual, 4),
            'VaR 99% Diario': round(var_99, 4),
            'VaR 99% Anual': round(var_99_annual, 4),
            'Expected Shortfall 95%': round(cvar_95_annual, 4),
            'Drawdown Máximo': round(max_drawdown, 4),
            'Duración Drawdown (días)': max_dd_duration,
            'Volatilidad Anual': round(volatility_annual, 4),
            
            # Correlaciones
            'Correlación S&P500': round(correlation_sp500, 4),
            
            # Estadísticas avanzadas
            'Máxima Ganancia Consecutiva': max_positive_streak,
            'Máxima Pérdida Consecutiva': max_negative_streak,
            'Skewness': round(skewness, 4),
            'Kurtosis': round(kurtosis, 4),
            'Probabilidad de Pérdida (%)': round(prob_loss, 2),
            
            # Rendimientos
            'Rendimiento Total': round(stock_total_return, 4),
            'Rendimiento Mercado': round(market_total_return, 4),
            'Días Analizados': len(stock_returns),
            'Período': f"{periodo_años} años"
        }
        
    except Exception as e:
        st.error(f"Error calculando métricas de riesgo: {str(e)}")
        return None

def crear_grafica_drawdown_mejorada(ticker_symbol, periodo_años=5):
    """
    Crea gráfica de drawdown MEJORADA para visualizar pérdidas máximas
    """
    try:
        # Descargar datos
        end_date = datetime.today()
        start_date = end_date - timedelta(days=periodo_años * 365)
        
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
        if stock_data.empty:
            return None
        
        # Manejar MultiIndex columns
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_close = stock_data[('Close', ticker_symbol)]
        else:
            stock_close = stock_data['Close']
        
        # Calcular drawdown
        returns = stock_close.pct_change().dropna()
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        # Crear gráfica
        fig = go.Figure()
        
        # Área de drawdown
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown * 100,
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.3)',
            line=dict(color='red', width=2),
            name='Drawdown',
            hovertemplate='<b>Drawdown</b><br>Fecha: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
        ))
        
        # Línea de máximo anterior
        fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="Máximo Anterior")
        
        # Encontrar los 3 mayores drawdowns
        drawdown_sorted = drawdown.sort_values()
        top_drawdowns = drawdown_sorted.head(3)
        
        # Anotar los mayores drawdowns
        for i, (fecha, valor) in enumerate(top_drawdowns.items()):
            fig.add_annotation(
                x=fecha,
                y=valor * 100,
                text=f"DD {i+1}: {valor*100:.1f}%",
                showarrow=True,
                arrowhead=2,
                bgcolor="red",
                font=dict(color="white", size=10),
                yshift=10 if i == 0 else (-20 if i == 1 else 30)
            )
        
        fig.update_layout(
            title=f'Análisis de Drawdown - {ticker_symbol}',
            xaxis_title='Fecha',
            yaxis_title='Drawdown (%)',
            height=500,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creando gráfica de drawdown: {str(e)}")
        return None

def crear_grafica_distribucion_retornos(ticker_symbol, periodo_años=5):
    """
    Crea gráfica de distribución de retornos
    """
    try:
        # Descargar datos
        end_date = datetime.today()
        start_date = end_date - timedelta(days=periodo_años * 365)
        
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
        if stock_data.empty:
            return None
        
        # Manejar MultiIndex columns
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_close = stock_data[('Close', ticker_symbol)]
        else:
            stock_close = stock_data['Close']
        
        # Calcular retornos
        returns = stock_close.pct_change().dropna() * 100  # En porcentaje
        
        # Crear histograma con curva normal
        fig = go.Figure()
        
        # Histograma
        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name='Frecuencia',
            opacity=0.7,
            marker_color='lightblue'
        ))
        
        # Calcular distribución normal (aproximación)
        if len(returns) > 0:
            x_norm = np.linspace(returns.min(), returns.max(), 100)
            # Aproximación manual de distribución normal
            mean = np.mean(returns)
            std = np.std(returns)
            if std > 0:
                y_norm = (1/(std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean)/std) ** 2)
                y_norm = y_norm * len(returns) * (returns.max() - returns.min()) / 50  # Escalar
                
                # Curva normal
                fig.add_trace(go.Scatter(
                    x=x_norm,
                    y=y_norm,
                    mode='lines',
                    name='Distribución Normal',
                    line=dict(color='red', width=2)
                ))
        
        # Línea en cero
        fig.add_vline(x=0, line_dash="dash", line_color="green")
        
        fig.update_layout(
            title=f'Distribución de Retornos Diarios - {ticker_symbol}',
            xaxis_title='Retorno Diario (%)',
            yaxis_title='Frecuencia',
            height=400,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creando gráfica de distribución: {str(e)}")
        return None

# FUNCIÓN PRINCIPAL DE LA SECCIÓN (EXACTAMENTE COMO EN TU CÓDIGO ORIGINAL)
def mostrar(datos_accion):
    stonk = datos_accion['ticker']
    nombre = datos_accion['nombre']
    info = datos_accion['info']
    """
    Función principal que muestra la sección de datos fundamentales
    """
    st.header(f"💰 Datos Fundamentales Completos De {nombre}")
    
    # Pestañas para Fundamentales
    tab1, tab2 = st.tabs(["📊 Análisis Fundamental", "🎓 Educación Financiera"])

    with tab1:
        # Mostrar spinner mientras se cargan los datos
        with st.spinner('Cargando datos fundamentales y calculando métricas de riesgo avanzadas...'):
            datos_finviz = extraer_tabla_finviz(stonk)
            metricas_riesgo = calcular_metricas_riesgo_avanzadas(stonk)
            
            if datos_finviz:
                st.success(f"✅ Se cargaron {len(datos_finviz)} métricas fundamentales")
                
                # FUNCIÓN INTELIGENTE PARA BUSCAR MÉTRICAS
                def buscar_metrica(datos, posibles_claves):
                    for clave in posibles_claves:
                        if clave in datos:
                            return datos[clave]
                    return "N/A"
                
                # DEFINIR LAS MÉTRICAS QUE QUEREMOS MOSTRAR
                metricas_principales = {
                    # Valoración y Mercado
                    "Market Cap": ["Market Cap", "Mkt Cap"],
                    "P/E": ["P/E", "PE", "P/E Ratio"],
                    "Forward P/E": ["Forward P/E", "Fwd P/E", "Forward PE"],
                    "PEG": ["PEG", "PEG Ratio"],
                    "P/FCF": ["P/FCF", "Price/FCF"],
                    "EV/EBITDA": ["EV/EBITDA", "Enterprise Value/EBITDA"],
                    "EV/SALES": ["EV/Sales", "Enterprise Value/Sales", "EV/S"],
                    
                    # Ingresos y Rentabilidad
                    "Income": ["Income", "Net Income"],
                    "Sales": ["Sales", "Revenue", "Sales Q/Q"],
                    "Gross Margin": ["Gross Margin", "Gross Mgn"],
                    "Oper. Margin": ["Oper. Margin", "Operating Margin", "Oper Mgn"],
                    "Profit Margin": ["Profit Margin", "Profit Mgn", "Net Margin"],
                    
                    # Efectivo y Deuda
                    "Cash/Share": ["Cash/sh", "Cash/Share", "Cash per Share"],
                    "Debt/Eq": ["Debt/Eq", "Debt/Equity", "Total Debt/Equity"],
                    "LT Debt/Eq": ["LT Debt/Eq", "Long Term Debt/Equity"],
                    
                    # Rentabilidad (MANTENEMOS ROIC)
                    "ROA": ["ROA", "Return on Assets"],
                    "ROE": ["ROE", "Return on Equity"],
                    "ROIC": ["ROI", "ROIC", "Return on Investment", "Return on Capital"],
                    
                    # Indicadores Técnicos
                    "Volatility": ["Volatility", "Volatility W", "Volatility M"],
                    "RSI": ["RSI (14)", "RSI", "Relative Strength Index"],
                    "Beta": ["Beta", "Beta"],
                    "Volume": ["Volume", "Avg Volume", "Volume Today"]
                }
                
                # =============================================
                # 1. MÉTRICAS FUNDAMENTALES PRINCIPALES
                # =============================================
                st.subheader("🏢 Métricas Fundamentales Principales")
                
                # Valoración y Mercado
                st.write("#### 💰 Valoración y Mercado")
                cols = st.columns(4)
                valoracion_keys = ["Market Cap", "P/E", "Forward P/E", "PEG", "P/FCF", "EV/EBITDA", "EV/SALES"]
                for i, key in enumerate(valoracion_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Ingresos y Rentabilidad
                st.write("#### 📈 Ingresos y Rentabilidad")
                cols = st.columns(4)
                ingresos_keys = ["Income", "Sales", "Gross Margin", "Oper. Margin", "Profit Margin"]
                for i, key in enumerate(ingresos_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Deuda y Efectivo
                st.write("#### 🏦 Deuda y Efectivo")
                cols = st.columns(4)
                deuda_keys = ["Cash/Share", "Debt/Eq", "LT Debt/Eq"]
                for i, key in enumerate(deuda_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Rentabilidad (CON ROIC)
                st.write("#### 📊 Rentabilidad")
                cols = st.columns(4)
                rentabilidad_keys = ["ROA", "ROE", "ROIC"]
                for i, key in enumerate(rentabilidad_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                # Indicadores Técnicos
                st.write("#### 📈 Indicadores Técnicos")
                cols = st.columns(4)
                tecnicos_keys = ["Volatility", "RSI", "Beta", "Volume"]
                for i, key in enumerate(tecnicos_keys):
                    with cols[i % 4]:
                        valor = buscar_metrica(datos_finviz, metricas_principales[key])
                        st.metric(key, valor)
                
                st.markdown("---")
                
                # =============================================
                # 2. MÉTRICAS AVANZADAS DE RIESGO Y RENDIMIENTO
                # =============================================
                if metricas_riesgo:
                    st.subheader("🎯 Métricas Avanzadas de Riesgo y Rendimiento")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Beta con interpretación 
                        beta = metricas_riesgo['Beta']
                        if beta < 0.8:
                            interpretacion = "Defensivo"
                            color = "green"
                        elif beta < 1.2:
                            interpretacion = "Neutro"
                            color = "orange"
                        else:
                            interpretacion = "Agresivo"
                            color = "red"
                        
                        st.metric("📊 Beta (Riesgo Sistemático)", f"{beta:.4f}")
                        st.caption(f"*Interpretación: {interpretacion}*")
                        
                        # Alpha 
                        alpha = metricas_riesgo['Alpha']
                        st.metric("α Alpha", f"{alpha:.2%}")
                        st.caption("*Rendimiento vs esperado*")
                    
                    with col2:
                        # Sharpe Ratio 
                        sharpe = metricas_riesgo['Sharpe Ratio']
                        if sharpe > 1.0:
                            color_sharpe = "green"
                        elif sharpe > 0.5:
                            color_sharpe = "orange"
                        else:
                            color_sharpe = "red"
                        
                        st.metric("⚡ Sharpe Ratio", f"{sharpe:.4f}")
                        st.caption("*Rendimiento/riesgo total*")
                        
                        # Sortino Ratio 
                        sortino = metricas_riesgo['Sortino Ratio']
                        st.metric("🎯 Sortino Ratio", f"{sortino:.4f}")
                        st.caption("*Rendimiento/riesgo bajista*")
                    
                    with col3:
                        # Nuevos ratios
                        treynor = metricas_riesgo['Treynor Ratio']
                        st.metric("📈 Treynor Ratio", f"{treynor:.4f}")
                        st.caption("*Rendimiento/riesgo sistemático*")
                        
                        information = metricas_riesgo['Information Ratio']
                        st.metric("ℹ️ Information Ratio", f"{information:.4f}")
                        st.caption("*Rendimiento activo*")
                    
                    with col4:
                        # Rendimiento vs Mercado 
                        rend_stock = metricas_riesgo['Rendimiento Total']
                        rend_mercado = metricas_riesgo['Rendimiento Mercado']
                        diferencia = rend_stock - rend_mercado
                        
                        st.metric("📊 Vs S&P500", f"{diferencia:.2%}")
                        st.caption("*Exceso vs mercado*")
                        
                        # Probabilidad de pérdida
                        prob_loss = metricas_riesgo['Probabilidad de Pérdida (%)']
                        st.metric("📉 Prob. Pérdida", f"{prob_loss:.1f}%")
                        st.caption("*Frecuencia días negativos*")
                    
                    st.markdown("---")
                    
                    # =============================================
                    # 3. MÉTRICAS DE RENDIMIENTO AJUSTADO AL RIESGO
                    # =============================================
                    st.subheader("📈 Métricas de Rendimiento Ajustado al Riesgo")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # VaR 
                        var_95 = metricas_riesgo['VaR 95% Anual']
                        var_99 = metricas_riesgo['VaR 99% Anual']
                        
                        st.metric("📉 VaR 95% Anual", f"{var_95:.2%}")
                        st.caption("*Pérdida máxima esperada*")
                        st.metric("📉 VaR 99% Anual", f"{var_99:.2%}")
                        st.caption("*Pérdida extrema esperada*")
                    
                    with col2:
                        # Drawdown 
                        max_dd = metricas_riesgo['Drawdown Máximo']
                        dd_duration = metricas_riesgo['Duración Drawdown (días)']
                        
                        st.metric("🔻 Drawdown Máximo", f"{max_dd:.2%}")
                        st.caption("*Peor pérdida histórica*")
                        st.metric("⏱️ Duración DD", f"{dd_duration} días")
                        st.caption("*Tiempo recuperación*")
                    
                    with col3:
                        # Volatilidad y Correlación
                        volatilidad = metricas_riesgo['Volatilidad Anual']
                        correlacion = metricas_riesgo['Correlación S&P500']
                        
                        st.metric("📈 Volatilidad Anual", f"{volatilidad:.2%}")
                        st.caption("*Riesgo total anualizado*")
                        st.metric("🔗 Correlación S&P500", f"{correlacion:.2%}")
                        st.caption("*Movimiento vs mercado*")
                    
                    with col4:
                        # Estadísticas avanzadas
                        cvar = metricas_riesgo['Expected Shortfall 95%']
                        skew = metricas_riesgo['Skewness']
                        
                        st.metric("💀 Expected Shortfall", f"{cvar:.2%}")
                        st.caption("*Pérdida promedio en colas*")
                        st.metric("📊 Skewness", f"{skew:.4f}")
                        st.caption("*Asimetría distribución*")
                    
                    st.markdown("---")
                    
                    # =============================================
                    # 4. ALERTAS DE RIESGO
                    # =============================================
                    st.subheader("🚨 Alertas de Riesgo")
                    
                    alertas = []
                    
                    # Verificar condiciones de riesgo
                    if metricas_riesgo['Drawdown Máximo'] < -0.20:
                        alertas.append("🔴 ALTO RIESGO: Drawdown máximo > 20%")
                    elif metricas_riesgo['Drawdown Máximo'] < -0.10:
                        alertas.append("🟡 RIESGO MODERADO: Drawdown máximo > 10%")
                    
                    if metricas_riesgo['VaR 95% Anual'] < -0.25:
                        alertas.append("🔴 ALTO RIESGO: VaR anual > 25%")
                    
                    if metricas_riesgo['Volatilidad Anual'] > 0.40:
                        alertas.append("🟡 VOLATILIDAD ALTA: > 40% anual")
                    
                    if metricas_riesgo['Probabilidad de Pérdida (%)'] > 50:
                        alertas.append("🔴 ALTA PROBABILIDAD DE PÉRDIDA: > 50%")
                    
                    if alertas:
                        for alerta in alertas:
                            st.warning(alerta)
                    else:
                        st.success("✅ Perfil de riesgo dentro de parámetros normales")
                    
                    st.markdown("---")
                    
                    # =============================================
                    # 5. ANÁLISIS GRÁFICO DE RIESGO
                    # =============================================
                    st.subheader("📈 Análisis Gráfico de Riesgo")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Gráfica de drawdown 
                        st.markdown("**📉 Drawdown - Pérdidas Máximas Históricas**")
                        
                        grafica_drawdown = crear_grafica_drawdown_mejorada(stonk)
                        if grafica_drawdown:
                            st.plotly_chart(grafica_drawdown, use_container_width=True)
                            st.caption("*Visualiza las mayores caídas desde máximos históricos. Áreas rojas indican períodos de pérdidas.*")
                        else:
                            st.warning("No se pudo generar la gráfica de drawdown")

                    with col2:
                        # Gráfica de distribución de retornos
                        st.markdown("**📊 Distribución de Retornos Diarios**")
                        
                        grafica_distribucion = crear_grafica_distribucion_retornos(stonk)
                        if grafica_distribucion:
                            st.plotly_chart(grafica_distribucion, use_container_width=True)
                            st.caption("*Muestra la frecuencia y distribución de ganancias/pérdidas diarias. Línea roja = distribución normal teórica.*")
                        else:
                            st.warning("No se pudo generar la gráfica de distribución")

                    st.markdown("---")

                # =============================================
                # 6. MODELO CAPM - COSTO DE CAPITAL
                # =============================================
                st.subheader("📊 Modelo CAPM - Costo de Capital")

                # Configuración de parámetros CAPM
                col_params1, col_params2, col_params3 = st.columns(3)

                with col_params1:
                    tasa_libre_riesgo = st.number_input(
                        "Tasa Libre de Riesgo (%)", 
                        min_value=0.0, 
                        max_value=10.0, 
                        value=2.0, 
                        step=0.1,
                        help="Rendimiento de bonos gubernamentales (10 años)"
                    ) / 100

                with col_params2:
                    prima_riesgo_mercado = st.number_input(
                        "Prima de Riesgo de Mercado (%)", 
                        min_value=0.0, 
                        max_value=15.0, 
                        value=6.0, 
                        step=0.1,
                        help="Rendimiento esperado del mercado sobre tasa libre de riesgo"
                    ) / 100

                with col_params3:
                    # Obtener Beta de Yahoo Finance o usar valor por defecto
                    beta_actual = info.get('beta', 1.0)
                    beta = st.number_input(
                        "Beta (β) de la Acción", 
                        min_value=0.0, 
                        max_value=5.0, 
                        value=float(beta_actual), 
                        step=0.1,
                        help="Riesgo sistemático vs mercado"
                    )

                # Calcular CAPM
                costo_capital = tasa_libre_riesgo + beta * prima_riesgo_mercado

                # Mostrar métricas CAPM
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Tasa Libre Riesgo", 
                        f"{tasa_libre_riesgo*100:.1f}%",
                        "Rf"
                    )

                with col2:
                    st.metric(
                        "Beta (β)", 
                        f"{beta:.2f}",
                        "Riesgo Sistemático"
                    )

                with col3:
                    st.metric(
                        "Prima Riesgo Mercado", 
                        f"{prima_riesgo_mercado*100:.1f}%",
                        "E(Rm) - Rf"
                    )

                with col4:
                    st.metric(
                        "**Costo Capital (CAPM)**", 
                        f"**{costo_capital*100:.1f}%**",
                        "**E(R) = Rf + β×(Rm-Rf)**",
                        delta_color="off"
                    )

                # Gráfica del CAPM - Scatter Plot con datos históricos
                st.subheader("📈 Análisis CAPM - Datos Históricos")

                # SELECTOR DE PERÍODO PARA DATOS HISTÓRICOS
                st.markdown("**🕐 Selecciona el período de análisis:**")

                col_periodo, col_frecuencia = st.columns(2)

                with col_periodo:
                    periodo_capm = st.selectbox(
                        "Período de datos:",
                        options=["1 mes", "3 meses", "6 meses", "1 año", "2 años", "3 años", "5 años", "10 años"],
                        index=3,  # 1 año por defecto
                        key="periodo_capm"
                    )

                with col_frecuencia:
                    frecuencia_capm = st.selectbox(
                        "Frecuencia de datos:",
                        options=["Diario", "Semanal", "Mensual"],
                        index=0,  # Diario por defecto para períodos cortos
                        key="frecuencia_capm"
                    )

                # Mapear selecciones a parámetros
                periodo_map = {
                    "1 mes": 30,
                    "3 meses": 90,
                    "6 meses": 180,
                    "1 año": 365,
                    "2 años": 730,
                    "3 años": 1095,
                    "5 años": 1825,
                    "10 años": 3650
                }

                frecuencia_map = {
                    "Diario": "1d",
                    "Semanal": "1wk", 
                    "Mensual": "1mo"
                }

                dias_periodo = periodo_map[periodo_capm]
                intervalo = frecuencia_map[frecuencia_capm]

                # Ajustar frecuencia automáticamente para períodos muy cortos
                if dias_periodo <= 90 and frecuencia_capm == "Mensual":  # 3 meses o menos
                    st.warning("⚠️ Para períodos cortos (≤ 3 meses) se recomienda frecuencia Diaria o Semanal para mejor análisis")
                    intervalo = "1d"  # Forzar diario para períodos cortos

                st.info(f"**📊 Configuración:** {periodo_capm} | {frecuencia_capm} | {stonk} vs S&P500")

                # Obtener datos históricos según la selección
                try:
                    start_date = datetime.today() - timedelta(days=dias_periodo)
                    end_date = datetime.today()
                    
                    # Descargar datos
                    with st.spinner(f'Cargando datos {frecuencia_capm.lower()} para {periodo_capm}...'):
                        stock_data = yf.download(stonk, start=start_date, end=end_date, interval=intervalo)
                        market_data = yf.download('^GSPC', start=start_date, end=end_date, interval=intervalo)
                    
                    if not stock_data.empty and not market_data.empty:
                        # Obtener precios de cierre
                        if isinstance(stock_data.columns, pd.MultiIndex):
                            stock_close = stock_data[('Close', stonk)]
                        else:
                            stock_close = stock_data['Close']
                            
                        if isinstance(market_data.columns, pd.MultiIndex):
                            market_close = market_data[('Close', '^GSPC')]
                        else:
                            market_close = market_data['Close']
                        
                        # Calcular rendimientos
                        stock_returns = stock_close.pct_change().dropna()
                        market_returns = market_close.pct_change().dropna()
                        
                        # Alinear fechas
                        common_dates = stock_returns.index.intersection(market_returns.index)
                        stock_returns = stock_returns.loc[common_dates]
                        market_returns = market_returns.loc[common_dates]
                        
                        if len(stock_returns) > 5:  # Mínimo reducido para períodos cortos
                            # Crear scatter plot
                            fig_capm = go.Figure()
                            
                            # Determinar color de los puntos basado en la tendencia reciente
                            color_points = 'blue'
                            if len(stock_returns) > 10:
                                # Calcular tendencia reciente para colorear puntos
                                tendencia_reciente = stock_returns.tail(min(10, len(stock_returns))).mean()
                                if tendencia_reciente > 0:
                                    color_points = 'green'
                                else:
                                    color_points = 'red'
                            
                            # Puntos de datos históricos
                            fig_capm.add_trace(go.Scatter(
                                x=market_returns * 100,
                                y=stock_returns * 100,
                                mode='markers',
                                name=f'Datos {frecuencia_capm} ({len(stock_returns)} puntos)',
                                marker=dict(
                                    size=8,
                                    color=color_points,
                                    opacity=0.7,
                                    line=dict(width=1, color='darkgray')
                                ),
                                hovertemplate=(
                                    'Fecha: %{text}<br>' +
                                    'Rendimiento Mercado: %{x:.2f}%<br>' +
                                    'Rendimiento Acción: %{y:.2f}%<br>' +
                                    '<extra></extra>'
                                ),
                                text=[date.strftime('%d/%m/%Y') for date in common_dates]
                            ))
                            
                            # Calcular línea de regresión (Beta histórico)
                            if len(market_returns) > 1:
                                beta_real, intercepto = np.polyfit(market_returns, stock_returns, 1)
                                r_squared = np.corrcoef(market_returns, stock_returns)[0, 1] ** 2
                                
                                # Línea de regresión
                                x_line = np.linspace(market_returns.min(), market_returns.max(), 50)
                                y_line = intercepto + beta_real * x_line
                                
                                fig_capm.add_trace(go.Scatter(
                                    x=x_line * 100,
                                    y=y_line * 100,
                                    mode='lines',
                                    name=f'Beta Histórico = {beta_real:.2f}',
                                    line=dict(color='red', width=3, dash='dash'),
                                    hovertemplate='Beta histórico: {:.2f}<extra></extra>'.format(beta_real)
                                ))
                            
                            # Línea CAPM teórica
                            # Ajustar tasa libre de riesgo según frecuencia
                            if frecuencia_capm == "Diario":
                                rf_ajustado = tasa_libre_riesgo / 252
                            elif frecuencia_capm == "Semanal":
                                rf_ajustado = tasa_libre_riesgo / 52
                            else:  # Mensual
                                rf_ajustado = tasa_libre_riesgo / 12
                                
                            x_capm = np.linspace(market_returns.min(), market_returns.max(), 50)
                            y_capm = rf_ajustado + beta * (x_capm - rf_ajustado)
                            
                            fig_capm.add_trace(go.Scatter(
                                x=x_capm * 100,
                                y=y_capm * 100,
                                mode='lines',
                                name=f'CAPM Teórico (β = {beta:.2f})',
                                line=dict(color='blue', width=3),
                                hovertemplate='CAPM teórico<extra></extra>'
                            ))
                            
                            # Punto de rendimiento esperado actual
                            fig_capm.add_trace(go.Scatter(
                                x=[0],  # Centrado en el origen para mejor visualización
                                y=[costo_capital * 100],
                                mode='markers+text',
                                name='Rendimiento Esperado Anual',
                                marker=dict(size=12, color='orange', symbol='star', line=dict(width=2, color='darkorange')),
                                text=['ESPERADO'],
                                textposition="top center",
                                hovertemplate=f'Rendimiento esperado anual: {costo_capital*100:.1f}%<extra></extra>'
                            ))
                            
                            fig_capm.update_layout(
                                title=f'CAPM - {stonk} vs S&P500 ({periodo_capm}, {frecuencia_capm})',
                                xaxis_title='Rendimiento del Mercado (S&P500) (%)',
                                yaxis_title=f'Rendimiento de {stonk} (%)',
                                height=600,
                                showlegend=True,
                                hovermode='closest',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                ),
                                xaxis=dict(
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='lightgray',
                                    zeroline=True,
                                    zerolinewidth=2,
                                    zerolinecolor='black'
                                ),
                                yaxis=dict(
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='lightgray',
                                    zeroline=True,
                                    zerolinewidth=2,
                                    zerolinecolor='black'
                                )
                            )
                            
                            st.plotly_chart(fig_capm, use_container_width=True)
                            
                            # Análisis de la regresión
                            st.subheader("📊 Análisis de Regresión")
                            
                            col_reg1, col_reg2, col_reg3, col_reg4 = st.columns(4)
                            
                            with col_reg1:
                                st.metric("Beta Histórico", f"{beta_real:.2f}")
                                st.caption(f"Calculado con {len(stock_returns)} puntos")
                                
                            with col_reg2:
                                st.metric("Beta Teórico", f"{beta:.2f}")
                                st.caption("Valor de Yahoo Finance")
                                
                            with col_reg3:
                                diferencia_beta = beta_real - beta
                                st.metric(
                                    "Diferencia Beta", 
                                    f"{diferencia_beta:.2f}",
                                    f"{'↑' if beta_real > beta else '↓'} histórico vs teórico"
                                )
                                st.caption("Consistencia del beta")
                                
                            with col_reg4:
                                st.metric("R² (Coef. Determinación)", f"{r_squared:.3f}")
                                st.caption("Ajuste del modelo")
                            
                            # Interpretación específica por período
                            st.markdown("---")
                            st.subheader("💡 Interpretación por Período")
                            
                            col_interp1, col_interp2 = st.columns(2)
                            
                            with col_interp1:
                                st.markdown(f"""
                                **📈 Análisis del Período {periodo_capm}:**
                                
                                • **Beta histórico**: **{beta_real:.2f}**
                                • **Puntos analizados**: **{len(stock_returns)}**
                                • **Período**: {periodo_capm}
                                • **Frecuencia**: {frecuencia_capm}
                                
                                **🎯 Significado del Beta:**
                                - **Beta > 1**: Más volátil que el mercado
                                - **Beta = 1**: Misma volatilidad  
                                - **Beta < 1**: Menos volátil
                                """)
                            
                            with col_interp2:
                                # Interpretación específica del período
                                if "mes" in periodo_capm:
                                    interpretacion_periodo = "**🔄 Análisis de Corto Plazo** - Muestra el comportamiento reciente y puede ser más volátil"
                                elif periodo_capm == "1 año":
                                    interpretacion_periodo = "**📊 Análisis de Mediano Plazo** - Balance entre estabilidad y actualidad"
                                else:
                                    interpretacion_periodo = "**📈 Análisis de Largo Plazo** - Muestra tendencias estables y comportamiento histórico"
                                
                                st.markdown(f"""
                                **🔍 Contexto del Período:**
                                
                                {interpretacion_periodo}
                                
                                **📋 Recomendaciones:**
                                - Períodos cortos: Útiles para trading
                                - Períodos largos: Mejores para inversión
                                - Combine períodos para análisis completo
                                """)
                            
                            # Recomendaciones específicas basadas en el período
                            st.markdown("---")
                            st.subheader("🎯 Recomendaciones Específicas")
                            
                            if "mes" in periodo_capm:
                                if r_squared > 0.6:
                                    st.success("""
                                    **✅ BUEN AJUSTE EN CORTO PLAZO - Para Trading:**
                                    - Relación mercado-acción consistente recientemente
                                    - Estrategias de momentum pueden ser efectivas
                                    - Monitorea cambios diarios en la relación
                                    """)
                                else:
                                    st.warning("""
                                    **🟡 AJUSTE VARIABLE EN CORTO PLAZO - Precauciones:**
                                    - La acción tiene comportamiento independiente reciente
                                    - Considera noticias y eventos específicos de la empresa
                                    - Usa stops más ajustados
                                    """)
                            else:
                                if r_squared > 0.7:
                                    st.success("""
                                    **✅ ALTO AJUSTE - Para Inversión:**
                                    - Comportamiento predecible vs mercado
                                    - Estrategias basadas en Beta son confiables
                                    - Buena para diversificación de cartera
                                    """)
                                elif r_squared > 0.4:
                                    st.info("""
                                    **🟡 AJUSTE MODERADO - Enfoque Balanceado:**
                                    - Combine análisis CAPM con otros métodos
                                    - Considere factores específicos de la empresa
                                    - Monitoree cambios en la relación
                                    """)
                                else:
                                    st.warning("""
                                    **🔴 BAJO AJUSTE - Análisis Cauteloso:**
                                    - La acción se mueve independientemente del mercado
                                    - Enfóquese en análisis fundamental y técnico
                                    - El Beta puede no ser indicador confiable
                                    """)
                        
                        else:
                            st.warning(f"⚠️ No hay suficientes datos {frecuencia_capm.lower()} para {periodo_capm}. Intenta con una frecuencia diferente.")
                            
                    else:
                        st.warning("❌ No se pudieron cargar los datos para el análisis CAPM")
                        
                except Exception as e:
                    st.error(f"Error en el análisis CAPM: {str(e)}")

                # Consejos para usar diferentes períodos
                st.markdown("---")
                st.subheader("💡 Consejos para Usar Diferentes Períodos")

                consejos_periodos = [
                    "**📅 1-3 meses**: Ideal para traders - muestra comportamiento reciente",
                    "**📊 6 meses - 1 año**: Balanceado - buen para swing trading",
                    "**📈 2-3 años**: Estabilidad media - recomendado para mayoría de inversores", 
                    "**🏛️ 5-10 años**: Largo plazo - muestra tendencias estables",
                    "**🔄 Combine períodos**: Use corto + largo plazo para análisis completo",
                    "**📉 Períodos cortos**: Más volátiles pero más actualizados",
                    "**📈 Períodos largos**: Más estables pero pueden omitir cambios recientes"
                ]

                for consejo in consejos_periodos:
                    st.write(f"• {consejo}")

                st.markdown("---")

                # =============================================
                # 7. SNAPSHOT FINANCIERO COMPLETO
                # =============================================
                st.subheader(f"📊 Snapshot Financiero Completo - {stonk}")
                
                # Crear una tabla de 2 columnas replicando Finviz
                num_datos = len(datos_finviz)
                mitad = (num_datos + 1) // 2
                
                # Dividir los datos en dos columnas
                items = list(datos_finviz.items())
                col1_items = items[:mitad]
                col2_items = items[mitad:]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    for clave, valor in col1_items:
                        st.markdown(f"""
                        <div style="border-bottom: 1px solid #444; padding: 10px 0;">
                            <div style="font-weight: bold; color: white; font-size: 14px; margin-bottom: 2px;">{clave}</div>
                            <div style="color: #f0f0f0; font-size: 14px; text-align: right; font-weight: 500;">{valor}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    for clave, valor in col2_items:
                        st.markdown(f"""
                        <div style="border-bottom: 1px solid #444; padding: 10px 0;">
                            <div style="font-weight: bold; color: white; font-size: 14px; margin-bottom: 2px;">{clave}</div>
                            <div style="color: #f0f0f0; font-size: 14px; text-align: right; font-weight: 500;">{valor}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # BOTÓN DE DESCARGA
                st.markdown("---")
                st.subheader("💾 Exportar Datos")
                
                # Crear DataFrame combinado con todas las métricas
                df_completo = pd.DataFrame(list(datos_finviz.items()), columns=['Métrica', 'Valor'])
                
                # Agregar métricas de riesgo si están disponibles
                if metricas_riesgo:
                    df_riesgo = pd.DataFrame(list(metricas_riesgo.items()), columns=['Métrica', 'Valor'])
                    df_completo = pd.concat([df_completo, df_riesgo], ignore_index=True)
                
                csv = df_completo.to_csv(index=False)
                
                st.download_button(
                    label="📥 Descargar datos fundamentales y de riesgo como CSV",
                    data=csv,
                    file_name=f"{stonk}_datos_completos.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                    
            else:
                st.error("""
                ❌ No se pudieron cargar los datos fundamentales. Posibles causas:
                
                • **Problemas de conexión** con Finviz
                • **Bloqueo temporal** por demasiadas solicitudes
                • **El símbolo no existe** o no está disponible
                
                💡 **Sugerencias:**
                • Verifica el símbolo (ej: AAPL, MSFT, TSLA, GOOGL)
                • Espera 1-2 minutos e intenta nuevamente  
                • Verifica directamente en [Finviz](https://finviz.com/quote.ashx?t={stonk})
                """)
                
                if st.button("🔄 Intentar nuevamente", use_container_width=True, key="reintentar_fundamentales"):
                    st.rerun()
    #
    with tab2:
        st.header("🎓 Educación Financiera - Guía Completa de 82 Métricas")
        st.write("**Explicación DETALLADA de cada métrica: qué es, para qué sirve, ventajas y desventajas**")
        
        # Selector de categoría
        categorias = [
            "💰 VALORACIÓN Y MERCADO (18 métricas)",
            "📈 RENTABILIDAD Y MÁRGENES (16 métricas)", 
            "🏦 DEUDA Y LIQUIDEZ (12 métricas)",
            "📊 EFICIENCIA OPERATIVA (10 métricas)",
            "📈 CRECIMIENTO (8 métricas)",
            "📊 INDICADORES TÉCNICOS (10 métricas)",
            "🏢 DATOS CORPORATIVOS (8 métricas)",
            "⚡ MÉTRICAS AVANZADAS DE RIESGO",
            "💡 CONSEJOS PRÁCTICOS DE INVERSIÓN"
        ]
        
        categoria = st.selectbox("Selecciona la categoría:", categorias)
        
        st.markdown("---")
        
        if categoria == "💰 VALORACIÓN Y MERCADO (18 métricas)":
            st.subheader("💰 VALORACIÓN Y MERCADO - 18 Métricas")
            
            metricas = {
                "Market Cap": {
                    "definicion": "**Capitalización de mercado** - Valor total de la empresa en bolsa",
                    "calculacion": "Precio actual de la acción × Número total de acciones en circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Large Cap (>$10B)**: Empresas establecidas, menos volátiles, dividendos consistentes
                    - **Mid Cap ($2B-$10B)**: Empresas en crecimiento, balance riesgo/recompensa
                    - **Small Cap (<$2B)**: Empresas pequeñas, alto crecimiento potencial, más riesgo
                    - **Mega Cap (>$200B)**: Gigantes globales como Apple, Microsoft
                    
                    **Ventajas:**
                    - Fácil de calcular y entender
                    - Buen indicador del tamaño relativo
                    - Útil para comparar empresas del mismo sector
                    
                    **Desventajas:**
                    - No considera la deuda de la empresa
                    - Puede ser engañoso si hay muchas acciones en circulación
                    - No refleja el valor intrínseco real
                    
                    **¿Para qué sirve?**
                    - Determinar el tamaño y estabilidad de la empresa
                    - Clasificar empresas por capitalización
                    - Evaluar el riesgo relativo (generalmente empresas más grandes = menos riesgo)
                    """,
                    "ejemplo": "Apple: 16,300 millones de acciones × $150 = $2.45 billones de Market Cap"
                },
                
                "P/E (Price-to-Earnings)": {
                    "definicion": "**Ratio Precio-Beneficio** - Cuánto pagan los inversores por cada dólar de ganancias",
                    "calculacion": "Precio de la acción ÷ Ganancias por acción (EPS)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **P/E bajo (<15)**: Posiblemente subvalorada, pero investiga por qué
                    - **P/E medio (15-25)**: Rango típico para muchas empresas
                    - **P/E alto (>25)**: Altas expectativas de crecimiento o posible sobrevaloración
                    
                    **Ventajas:**
                    - Fácil de calcular y entender
                    - Ampliamente utilizado y aceptado
                    - Buen punto de partida para valoración
                    
                    **Desventajas:**
                    - No útil para empresas sin ganancias
                    - Las ganancias pueden ser manipuladas contablemente
                    - No considera el crecimiento futuro
                    - Varía mucho entre sectores
                    
                    **Sectores típicos:**
                    - Tecnología: 20-30 (alto crecimiento esperado)
                    - Utilities: 12-18 (bajo crecimiento, estables)
                    - Bancos: 8-12 (regulados, crecimiento estable)
                    - Biotech: 30+ (potencial alto crecimiento)
                    
                    **¿Para qué sirve?**
                    - Comparar empresas dentro del mismo sector
                    - Identificar posibles oportunidades de valor
                    - Evaluar si el precio está justificado por las ganancias
                    """,
                    "ejemplo": "Empresa precio $100, EPS $5 → P/E = 20 (pagas $20 por cada $1 de ganancias)"
                },
                
                "Forward P/E": {
                    "definicion": "**P/E Forward** - Ratio P/E basado en ganancias estimadas futuras",
                    "calculacion": "Precio actual ÷ EPS estimado para el próximo año",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Forward P/E < Current P/E**: Se espera crecimiento de ganancias
                    - **Forward P/E > Current P/E**: Se espera disminución de ganancias
                    - Diferencia significativa puede indicar cambios en el negocio
                    
                    **Ventajas:**
                    - Más forward-looking que el P/E tradicional
                    - Mejor para empresas en crecimiento rápido
                    - Considera las expectativas del mercado
                    
                    **Desventajas:**
                    - Depende de estimaciones (pueden ser erróneas)
                    - Sensible a revisiones de analistas
                    - Las estimaciones pueden ser demasiado optimistas o pesimistas
                    
                    **¿Para qué sirve?**
                    - Evaluar valoración basada en expectativas futuras
                    - Identificar empresas donde el crecimiento no está reflejado en el precio
                    - Comparar con el P/E histórico para ver tendencias
                    """,
                    "ejemplo": "Precio $50, EPS estimado próximo año $2.50 → Forward P/E = 20"
                },
                
                "PEG Ratio": {
                    "definicion": "**Ratio P/E sobre Crecimiento** - Relaciona el P/E con la tasa de crecimiento",
                    "calculacion": "P/E Ratio ÷ Tasa de crecimiento anual de EPS (%)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **PEG < 1**: Posiblemente subvalorada (crecimiento > P/E)
                    - **PEG = 1**: Valoración justa
                    - **PEG > 1**: Posiblemente sobrevalorada (P/E > crecimiento)
                    
                    **Ventajas:**
                    - Considera el crecimiento futuro
                    - Mejor que solo mirar P/E para empresas growth
                    - Útil para comparar empresas con diferentes tasas de crecimiento
                    
                    **Desventajas:**
                    - Depende de estimaciones de crecimiento (inciertas)
                    - No considera el riesgo
                    - Las tasas de crecimiento pueden no ser sostenibles
                    
                    **Interpretación por sectores:**
                    - Tech growth: PEG 1.0-1.5 puede ser aceptable
                    - Value stocks: Buscar PEG < 0.8
                    - Empresas maduras: PEG cercano a 1.0
                    
                    **¿Para qué sirve?**
                    - Identificar empresas growth a precios razonables
                    - Evaluar si el premium de P/E está justificado por el crecimiento
                    - Comparar empresas con diferentes perfiles de crecimiento
                    """,
                    "ejemplo": "P/E 20, crecimiento EPS 25% anual → PEG = 0.8 (atractivo)"
                },
                
                "P/S (Price-to-Sales)": {
                    "definicion": "**Ratio Precio-Ventas** - Valoración respecto a los ingresos por ventas",
                    "calculacion": "Market Cap ÷ Ventas anuales totales",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **P/S < 1**: Considerado bajo (posible oportunidad)
                    - **P/S 1-3**: Rango típico para muchas empresas
                    - **P/S > 3**: Considerado alto (mucho crecimiento esperado)
                    
                    **Ventajas:**
                    - Útil para empresas sin ganancias o con ganancias volátiles
                    - Las ventas son más difíciles de manipular que las ganancias
                    - Bueno para startups y empresas en crecimiento
                    
                    **Desventajas:**
                    - No considera la rentabilidad
                    - Empresas con márgenes bajos pueden tener P/S engañosos
                    - No diferencia entre ventas de calidad y ventas sin profit
                    
                    **Sectores típicos:**
                    - Software: P/S 5-15 (márgenes altos esperados)
                    - Retail: P/S 0.5-1.5 (márgenes bajos)
                    - Manufacturing: P/S 1-2
                    
                    **¿Para qué sirve?**
                    - Evaluar empresas que aún no son rentables
                    - Comparar empresas dentro del mismo sector
                    - Identificar empresas con ventas crecientes pero P/S bajo
                    """,
                    "ejemplo": "Market Cap $500M, Ventas $250M → P/S = 2.0"
                },
                
                "P/B (Price-to-Book)": {
                    "definicion": "**Ratio Precio-Valor Contable** - Compara precio de mercado con valor en libros",
                    "calculacion": "Precio de la acción ÷ Valor contable por acción",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **P/B < 1**: Cotiza bajo valor contable (posible oportunidad value)
                    - **P/B = 1**: Precio igual al valor contable
                    - **P/B > 1**: Prima sobre valor contable (normal para empresas rentables)
                    
                    **Ventajas:**
                    - Bueno para empresas con muchos activos tangibles
                    - El valor contable es relativamente estable
                    - Útil para bancos y empresas financieras
                    
                    **Desventajas:**
                    - No útil para empresas de servicios o tecnología
                    - No considera activos intangibles (marca, patentes)
                    - El valor contable puede estar desactualizado
                    
                    **Sectores típicos:**
                    - Bancos: P/B 0.8-1.5
                    - Seguros: P/B 1.0-1.8
                    - Tecnología: P/B 3.0+ (muchos intangibles)
                    
                    **¿Para qué sirve?**
                    - Encontrar empresas potencialmente subvaloradas
                    - Evaluar empresas con muchos activos físicos
                    - Análisis de bancos y instituciones financieras
                    """,
                    "ejemplo": "Precio $50, Valor contable por acción $40 → P/B = 1.25"
                },
                
                "P/FCF": {
                    "definicion": "**Precio/Flujo de Caja Libre** - Valoración respecto al flujo de caja generado",
                    "calculacion": "Market Cap ÷ Flujo de Caja Libre anual",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **P/FCF < 15**: Generalmente considerado atractivo
                    - **P/FCF 15-25**: Rango razonable
                    - **P/FCF > 25**: Posiblemente sobrevalorado
                    
                    **Ventajas:**
                    - El flujo de caja es más difícil de manipular que las ganancias
                    - Mide la capacidad real de generar efectivo
                    - Buen indicador de salud financiera
                    
                    **Desventajas:**
                    - El FCF puede ser volátil entre años
                    - No considera inversiones de capital futuras
                    - Puede ser negativo en empresas en crecimiento
                    
                    **¿Para qué sirve?**
                    - Evaluar la capacidad de generar efectivo real
                    - Comparar empresas dentro del mismo sector
                    - Identificar empresas con fuerte generación de caja
                    """,
                    "ejemplo": "Market Cap $1B, FCF $100M → P/FCF = 10"
                },
                
                "P/C": {
                    "definicion": "**Precio/Efectivo** - Valoración respecto al efectivo en balance",
                    "calculacion": "Precio de la acción ÷ Efectivo por acción",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **P/C bajo**: Mucho efectivo relativo al precio (posible oportunidad)
                    - **P/C alto**: Poca reserva de efectivo relativa al precio
                    - **P/C < 5**: Generalmente considerado atractivo
                    - **P/C > 10**: Puede indicar sobrevaloración
                    
                    **Ventajas:**
                    - Mide el colchón de seguridad en efectivo
                    - Útil para identificar empresas con fuerte posición de caja
                    - El efectivo es el activo más líquido y seguro
                    - Bueno para evaluar valoración en situaciones de crisis
                    
                    **Desventajas:**
                    - No considera cómo se usa el efectivo
                    - El efectivo puede estar destinado a obligaciones específicas
                    - Puede ser temporal (venta de activos, emisión de deuda)
                    - No diferencia entre efectivo operativo y no operativo
                    
                    **Interpretación por sectores:**
                    - **Tecnología**: P/C 5-15 (normal por alto crecimiento)
                    - **Manufactura**: P/C 3-8 (menos efectivo intensivo)
                    - **Financieras**: P/C 1-3 (mucha regulación de capital)
                    - **Biotech**: P/C 10-20 (queman efectivo en desarrollo)
                    
                    **¿Para qué sirve?**
                    - Evaluar la solidez financiera a corto plazo
                    - Identificar empresas con exceso de efectivo
                    - Analizar oportunidades de recompra de acciones o dividendos
                    - Valoración en adquisiciones (empresas con mucho cash)
                    
                    **Señales de alerta:**
                    - P/C muy alto con poco crecimiento
                    - Efectivo decreciente con P/C constante
                    - Empresas que queman cash rápidamente
                    """,
                    "ejemplo": "Precio $100, Efectivo por acción $25 → P/C = 4 (atractivo)\nPrecio $50, Efectivo por acción $3 → P/C = 16.7 (elevado)"
                },

                "EV/EBITDA": {
                    "definicion": "**Enterprise Value/EBITDA** - Valor empresa completa sobre ganancias operativas",
                    "calculacion": "Enterprise Value ÷ EBITDA",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EV/EBITDA < 8**: Posiblemente subvalorada
                    - **EV/EBITDA 8-12**: Rango típico
                    - **EV/EBITDA > 12**: Posiblemente sobrevalorada
                    
                    **Ventajas:**
                    - Considera la deuda y efectivo (mejor que P/E)
                    - Útil para comparar empresas con diferente apalancamiento
                    - Muy usado en fusiones y adquisiciones
                    
                    **Desventajas:**
                    - No considera gastos por intereses e impuestos
                    - El EBITDA puede ser engañoso en algunos casos
                    - No es GAAP (puede calcularse de diferentes formas)
                    
                    **Sectores típicos:**
                    - Telecom: 6-9
                    - Healthcare: 10-14
                    - Tech: 12-18
                    
                    **¿Para qué sirve?**
                    - Comparar empresas con diferentes estructuras de capital
                    - Análisis de M&A (fusiones y adquisiciones)
                    - Evaluar el valor operativo del negocio
                    """,
                    "ejemplo": "EV $500M, EBITDA $50M → EV/EBITDA = 10"
                },
                
                "EV/Sales": {
                    "definicion": "**Enterprise Value/Ventas** - Valor empresa completa sobre ventas",
                    "calculacion": "Enterprise Value ÷ Ventas anuales",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EV/Sales < 1**: Bajo relativo a ventas
                    - **EV/Sales 1-3**: Rango típico
                    - **EV/Sales > 3**: Alto relativo a ventas
                    
                    **Ventajas:**
                    - Considera la estructura completa de capital
                    - Mejor que P/S para empresas con mucha deuda
                    - Útil para empresas sin ganancias
                    
                    **Desventajas:**
                    - No considera rentabilidad
                    - Las ventas no garantizan ganancias
                    - Puede variar mucho entre sectores
                    
                    **¿Para qué sirve?**
                    - Evaluar empresas en crecimiento sin ganancias
                    - Comparar empresas con diferentes niveles de deuda
                    - Análisis de startups y empresas high-growth
                    """,
                    "ejemplo": "EV $600M, Ventas $200M → EV/Sales = 3.0"
                },
                
                "EV/FCF": {
                    "definicion": "**Enterprise Value/Flujo de Caja Libre** - Valor empresa completa sobre FCF",
                    "calculacion": "Enterprise Value ÷ Flujo de Caja Libre",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EV/FCF < 10**: Muy atractivo
                    - **EV/FCF 10-20**: Razonable
                    - **EV/FCF > 20**: Posiblemente caro
                    
                    **Ventajas:**
                    - Considera toda la estructura de capital
                    - Basado en flujo de caja real (no ganancias contables)
                    - Bueno para evaluar capacidad de pago de deuda
                    
                    **Desventajas:**
                    - El FCF puede ser volátil
                    - No considera necesidades futuras de inversión
                    - Puede ser negativo
                    
                    **¿Para qué sirve?**
                    - Evaluar el retorno sobre la inversión total
                    - Análisis de empresas con mucha deuda
                    - Comparar oportunidades de inversión
                    """,
                    "ejemplo": "EV $800M, FCF $80M → EV/FCF = 10"
                },
                
                "EPS (ttm)": {
                    "definicion": "**Ganancias por Acción últimos 12 meses** - Beneficio neto por acción",
                    "calculacion": "Beneficio Neto últimos 12 meses ÷ Acciones en circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EPS creciente**: Empresa en crecimiento
                    - **EPS estable**: Empresa madura
                    - **EPS decreciente**: Posibles problemas
                    
                    **Ventajas:**
                    - Fácil de entender
                    - Directamente relacionado con el precio (P/E)
                    - Buen indicador de salud financiera
                    
                    **Desventajas:**
                    - Puede ser manipulado contablemente
                    - No considera el flujo de caja
                    - Puede variar por eventos extraordinarios
                    
                    **¿Para qué sirve?**
                    - Calcular el P/E ratio
                    - Evaluar la rentabilidad por acción
                    - Seguir la trayectoria de ganancias
                    """,
                    "ejemplo": "Beneficio $100M, 10M acciones → EPS = $10"
                },
                
                "EPS next Y": {
                    "definicion": "**EPS Próximo Año** - Estimación de ganancias para el próximo año",
                    "calculacion": "Estimación de Beneficio Neto próximo año ÷ Acciones estimadas",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EPS next Y > EPS actual**: Crecimiento esperado
                    - **EPS next Y < EPS actual**: Decrecimiento esperado
                    - **Gran diferencia**: Cambios significativos en el negocio
                    
                    **Ventajas:**
                    - Proporciona visión futura
                    - Útil para calcular Forward P/E
                    - Refleja expectativas del mercado
                    
                    **Desventajas:**
                    - Basado en estimaciones (inciertas)
                    - Puede ser demasiado optimista/pesimista
                    - Sensible a revisiones
                    
                    **¿Para qué sirve?**
                    - Evaluar expectativas de crecimiento
                    - Identificar posibles sorpresas de ganancias
                    - Planificar estrategias de inversión
                    """,
                    "ejemplo": "EPS actual $5, EPS next Y estimado $6 → 20% crecimiento esperado"
                },
                
                "EPS next Q": {
                    "definicion": "**EPS Próximo Trimestre** - Estimación para el próximo trimestre",
                    "calculacion": "Estimación Beneficio Neto próximo trimestre ÷ Acciones",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Beat estimates**: Supera estimaciones (positivo)
                    - **Miss estimates**: No alcanza estimaciones (negativo)
                    - **Guide higher**: Aumenta guidance (muy positivo)
                    
                    **Ventajas:**
                    - Proporciona visión a corto plazo
                    - Útil para trading alrededor de earnings
                    - Indica momentum operativo
                    
                    **Desventajas:**
                    - Muy volátil entre trimestres
                    - Sensible a estacionalidad
                    - Las estimaciones pueden ser erróneas
                    
                    **¿Para qué sirve?**
                    - Anticipar resultados trimestrales
                    - Evaluar momentum del negocio
                    - Timing de entrada/salida de posiciones
                    """,
                    "ejemplo": "Estimación Q1: $1.25 por acción"
                },
                
                "EPS this Y": {
                    "definicion": "**EPS Este Año** - Ganancias actuales vs año anterior",
                    "calculacion": "EPS año actual ÷ EPS año anterior - 1",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo**: Crecimiento interanual
                    - **Negativo**: Decrecimiento interanual
                    - **Alto**: Fuerte crecimiento
                    
                    **Ventajas:**
                    - Muestra tendencia anual
                    - Menos volátil que trimestral
                    - Buen indicador de dirección
                    
                    **Desventajas:**
                    - Puede estar influido por eventos únicos
                    - No considera factores estacionales
                    - Puede enmascarar problemas trimestrales
                    
                    **¿Para qué sirve?**
                    - Evaluar performance anual
                    - Comparar con guidance de la empresa
                    - Análisis de tendencias a medio plazo
                    """,
                    "ejemplo": "EPS 2023: $4.50, EPS 2024: $5.00 → Crecimiento 11%"
                },
                
                "EPS next 5Y": {
                    "definicion": "**Crecimiento EPS Próximos 5 Años** - Tasa crecimiento anual estimada",
                    "calculacion": "Estimación crecimiento anual compuesto próximo 5 años",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<5%**: Crecimiento lento (empresa madura)
                    - **5-15%**: Crecimiento moderado
                    - **>15%**: Crecimiento rápido (empresa growth)
                    
                    **Ventajas:**
                    - Proporciona perspectiva a largo plazo
                    - Útil para modelos de descuento de flujos
                    - Refleja expectativas de crecimiento sostenido
                    
                    **Desventajas:**
                    - Muy especulativo a 5 años vista
                    - Las estimaciones suelen ser optimistas
                    - Difícil de predecir con precisión
                    
                    **¿Para qué sirve?**
                    - Calcular PEG ratio
                    - Evaluar potencial de crecimiento a largo plazo
                    - Comparar empresas dentro del mismo sector
                    """,
                    "ejemplo": "Crecimiento EPS estimado 12% anual próximos 5 años"
                },
                
                "EPS past 5Y": {
                    "definicion": "**Crecimiento EPS 5 Años** - Tasa crecimiento histórico anual",
                    "calculacion": "Tasa crecimiento anual compuesto últimos 5 años",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Consistente**: Crecimiento estable (buena gestión)
                    - **Volátil**: Resultados irregulares (riesgo)
                    - **Decreciente**: Posible madurez/saturación
                    
                    **Ventajas:**
                    - Basado en datos reales (no estimaciones)
                    - Muestra capacidad histórica de crecimiento
                    - Buen indicador de calidad de gestión
                    
                    **Desventajas:**
                    - El pasado no garantiza futuro
                    - Puede estar influido por ciclos económicos
                    - No considera cambios recientes en el negocio
                    
                    **¿Para qué sirve?**
                    - Evaluar track record de la empresa
                    - Comparar con estimaciones futuras
                    - Análisis de consistencia en resultados
                    """,
                    "ejemplo": "EPS creció de $2 a $4 en 5 años → 15% crecimiento anual"
                },
                
                "Book Value/Share": {
                    "definicion": "**Valor Contable por Acción** - Valor patrimonial por acción",
                    "calculacion": "Patrimonio Neto ÷ Acciones en circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Creciente**: Empresa acumulando valor
                    - **Decreciente**: Pérdidas o recompras de acciones
                    - **Estable**: Empresa madura
                    
                    **Ventajas:**
                    - Representa el valor en libros
                    - Relativamente estable
                    - Bueno para empresas con activos tangibles
                    
                    **Desventajas:**
                    - No refleja valor de mercado
                    - Puede no incluir activos intangibles
                    - Puede estar desactualizado
                    
                    **¿Para qué sirve?**
                    - Calcular P/B ratio
                    - Evaluar valoración relativa
                    - Análisis de empresas value
                    """,
                    "ejemplo": "Patrimonio $400M, 10M acciones → Book Value/Share = $40"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")
        
        elif categoria == "📈 RENTABILIDAD Y MÁRGENES (16 métricas)":
            st.subheader("📈 RENTABILIDAD Y MÁRGENES - 16 Métricas")
            
            metricas = {
                "ROA (Return on Assets)": {
                    "definicion": "**Retorno sobre Activos** - Eficiencia en el uso de todos los recursos",
                    "calculacion": "Beneficio Neto ÷ Activos Totales × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **ROA < 5%**: Baja eficiencia
                    - **ROA 5-10%**: Adecuado
                    - **ROA > 10%**: Alta eficiencia
                    
                    **Ventajas:**
                    - Considera todos los recursos (no solo el capital)
                    - Menos susceptible a manipulación por apalancamiento
                    - Bueno para comparar empresas con diferentes estructuras de capital
                    
                    **Desventajas:**
                    - Los activos pueden estar valorados incorrectamente
                    - No considera el costo de capital
                    - Puede penalizar empresas con muchos activos
                    
                    **Comparativa por sectores:**
                    - Tecnología: 8-15% (pocos activos, altos retornos)
                    - Manufactura: 4-8% (activos intensivos)
                    - Retail: 3-6% (márgenes bajos, alta rotación)
                    
                    **¿Para qué sirve?**
                    - Medir la eficiencia operativa general
                    - Comparar empresas con diferentes niveles de deuda
                    - Evaluar la calidad de la gestión
                    """,
                    "ejemplo": "Beneficio $500k, Activos $10M → ROA = 5%"
                },
                
                "ROE (Return on Equity)": {
                    "definicion": "**Retorno sobre el Patrimonio** - Rentabilidad generada con el capital de los accionistas",
                    "calculacion": "Beneficio Neto ÷ Patrimonio Neto × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **ROE < 8%**: Bajo - podría no compensar el riesgo
                    - **ROE 8-15%**: Adecuado
                    - **ROE 15-20%**: Bueno
                    - **ROE > 20%**: Excelente
                    
                    **Ventajas:**
                    - Fácil de calcular y entender
                    - Buen indicador de eficiencia del capital
                    - Ampliamente utilizado
                    
                    **Desventajas:**
                    - Puede ser inflado por mucho apalancamiento (deuda)
                    - No considera el riesgo asumido
                    - Puede variar significativamente entre sectores
                    
                    **Análisis DuPont (descomposición del ROE):**
                    ROE = (Margen Neto) × (Rotación Activos) × (Apalancamiento)
                    - **Margen Neto**: Eficiencia en control de costos
                    - **Rotación**: Eficiencia uso de activos  
                    - **Apalancamiento**: Uso de deuda vs capital
                    
                    **¿Para qué sirve?**
                    - Medir la eficiencia en el uso del capital de accionistas
                    - Comparar empresas dentro del mismo sector
                    - Identificar empresas con ventajas competitivas sostenibles
                    """,
                    "ejemplo": "Beneficio $1M, Patrimonio $10M → ROE = 10%"
                },
                
                "ROI (Return on Investment)": {
                    "definicion": "**Retorno sobre la Inversión** - Eficiencia de las inversiones realizadas",
                    "calculacion": "Beneficio de la inversión ÷ Costo de la inversión × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **ROI > costo de capital**: Crea valor
                    - **ROI < costo de capital**: Destruye valor
                    - **ROI alto**: Inversiones eficientes
                    
                    **Ventajas:**
                    - Mide la eficiencia de las decisiones de inversión
                    - Útil para evaluar proyectos específicos
                    - Fácil de entender
                    
                    **Desventajas:**
                    - Puede ser difícil de calcular para inversiones complejas
                    - No considera el valor temporal del dinero
                    - Puede variar según el período medido
                    
                    **¿Para qué sirve?**
                    - Evaluar la eficiencia del capital invertido
                    - Comparar diferentes oportunidades de inversión
                    - Tomar decisiones de asignación de capital
                    """,
                    "ejemplo": "Inversión $1M, Beneficio $150k anual → ROI = 15%"
                },
                
                "Gross Margin": {
                    "definicion": "**Margen Bruto** - Porcentaje que queda después de costos directos",
                    "calculacion": "(Ventas - Costo de Bienes Vendidos) ÷ Ventas × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Margen alto**: Fuertes ventajas competitivas, poder de precios
                    - **Margen bajo**: Competencia intensa, commoditización
                    - **Margen creciente**: Mejora en eficiencia o poder de precios
                    
                    **Ventajas:**
                    - Buen indicador de ventajas competitivas
                    - Relativamente estable en el tiempo
                    - Difícil de manipular contablemente
                    
                    **Desventajas:**
                    - No considera gastos operativos
                    - Puede variar significativamente por estacionalidad
                    - Depende de la clasificación de costos
                    
                    **Rangos por industria:**
                    - Software: 80-90%
                    - Farmacéutica: 70-80%
                    - Bienes de consumo: 40-60%
                    - Retail: 20-40%
                    - Airlines: 10-20%
                    
                    **¿Para qué sirve?**
                    - Evaluar el poder de fijación de precios
                    - Medir ventajas competitivas en costos
                    - Identificar tendencias en la rentabilidad del core business
                    """,
                    "ejemplo": "Ventas $1M, Costo bienes $600k → Margen Bruto = 40%"
                },
                
                "Operating Margin": {
                    "definicion": "**Margen Operativo** - Rentabilidad del negocio principal antes de intereses e impuestos",
                    "calculacion": "Beneficio Operativo ÷ Ventas × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Margen alto**: Eficiencia operativa, control de gastos
                    - **Margen bajo**: Altos gastos operativos, ineficiencia
                    - **Margen creciente**: Mejora en gestión operativa
                    
                    **Ventajas:**
                    - Mide la eficiencia del negocio principal
                    - Excluye efectos financieros y fiscales
                    - Bueno para comparar empresas con diferente apalancamiento
                    
                    **Desventajas:**
                    - No considera la estructura de capital
                    - Puede variar por decisiones contables
                    - No refleja el beneficio final para accionistas
                    
                    **Componentes que afectan el margen operativo:**
                    - Eficiencia en producción
                    - Control de gastos generales
                    - Precios vs costos
                    - Economías de escala
                    
                    **¿Para qué sirve?**
                    - Evaluar la eficiencia operativa del negocio core
                    - Comparar empresas con diferentes estructuras financieras
                    - Identificar mejoras en gestión operativa
                    """,
                    "ejemplo": "Ventas $1M, Beneficio operativo $150k → Margen Operativo = 15%"
                },
                
                "Profit Margin": {
                    "definicion": "**Margen de Beneficio Neto** - Porcentaje final que queda para accionistas",
                    "calculacion": "Beneficio Neto ÷ Ventas × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Margen alto**: Empresa muy eficiente o con fuertes ventajas
                    - **Margen bajo**: Competencia intensa o ineficiencias
                    - **Margen creciente**: Mejoras en eficiencia o mix de productos
                    
                    **Ventajas:**
                    - Representa el resultado final para accionistas
                    - Incluye todos los costos y gastos
                    - Fácil de comparar entre empresas
                    
                    **Desventajas:**
                    - Puede ser afectado por eventos extraordinarios
                    - No diferencia entre ganancias operativas y no operativas
                    - Puede variar por decisiones fiscales
                    
                    **Rangos típicos:**
                    - Software: 20-30%
                    - Bancos: 15-25%
                    - Retail: 2-5%
                    - Airlines: 2-8%
                    
                    **¿Para qué sirve?**
                    - Evaluar la rentabilidad final del negocio
                    - Comparar eficiencia entre competidores
                    - Identificar tendencias en rentabilidad
                    """,
                    "ejemplo": "Ventas $1M, Beneficio neto $80k → Profit Margin = 8%"
                },
                
                "EBITDA": {
                    "definicion": "**Ganancias antes de Intereses, Impuestos, Depreciación y Amortización**",
                    "calculacion": "Beneficio Operativo + Depreciación + Amortización",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EBITDA alto**: Fuerte generación operativa de caja
                    - **EBITDA creciente**: Mejora en performance operativa
                    - **EBITDA/Intereses alto**: Buena capacidad de cubrir deuda
                    
                    **Ventajas:**
                    - Elimina efectos de decisiones financieras y fiscales
                    - Buen proxy para flujo de caja operativo
                    - Útil para comparar empresas con diferentes estructuras
                    
                    **Desventajas:**
                    - No es GAAP (puede calcularse de diferentes formas)
                    - Ignora necesidades de reinversión en activos
                    - Puede ser engañoso en empresas con alta depreciación
                    
                    **¿Para qué sirve?**
                    - Evaluar performance operativa pura
                    - Calcular ratios de cobertura de deuda
                    - Análisis de empresas con diferentes políticas de depreciación
                    """,
                    "ejemplo": "Beneficio operativo $200k, Depreciación $50k → EBITDA = $250k"
                },
                
                "EBIT": {
                    "definicion": "**Ganancias antes de Intereses e Impuestos** - Resultado operativo",
                    "calculacion": "Ventas - Todos los gastos operativos (excluyendo intereses e impuestos)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **EBIT alto**: Negocio central rentable
                    - **EBIT creciente**: Mejora en eficiencia operativa
                    - **EBIT estable**: Empresa madura y predecible
                    
                    **Ventajas:**
                    - Mide la rentabilidad del negocio principal
                    - Excluye efectos financieros y fiscales
                    - Bueno para comparar eficiencia operativa
                    
                    **Desventajas:**
                    - No considera necesidades de inversión en activos
                    - Puede variar por métodos contables
                    - No refleja el costo del capital
                    
                    **¿Para qué sirve?**
                    - Evaluar la rentabilidad operativa core
                    - Comparar empresas con diferente apalancamiento
                    - Análisis de eficiencia operativa por segmentos
                    """,
                    "ejemplo": "Ventas $1M, Gastos operativos $800k → EBIT = $200k"
                },
                
                "Net Income": {
                    "definicion": "**Beneficio Neto** - Ganancias finales después de todos los gastos",
                    "calculacion": "Ingresos Totales - Gastos Totales (incluyendo intereses e impuestos)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo y creciente**: Empresa saludable y en crecimiento
                    - **Volátil**: Resultados inconsistentes (riesgo)
                    - **Negativo**: Pérdidas (señal de alerta)
                    
                    **Ventajas:**
                    - Representa el resultado final para accionistas
                    - Incluye todos los aspectos del negocio
                    - Base para cálculo de EPS
                    
                    **Desventajas:**
                    - Puede incluir partidas extraordinarias
                    - Sensible a decisiones contables
                    - No diferencia entre ganancias recurrentes y no recurrentes
                    
                    **¿Para qué sirve?**
                    - Evaluar la rentabilidad general
                    - Calcular ratios de rentabilidad (ROE, ROA)
                    - Seguir la trayectoria de ganancias
                    """,
                    "ejemplo": "Ingresos $1.2M, Gastos $1.1M → Net Income = $100k"
                },
                
                "Income Tax": {
                    "definicion": "**Impuesto sobre la Renta** - Monto pagado en impuestos",
                    "calculacion": "Base imponible × Tasa impositiva",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Tasa efectiva baja**: Posibles beneficios fiscales o ubicación favorable
                    - **Tasa efectiva alta**: Pocos beneficios fiscales
                    - **Cambios significativos**: Cambios en legislación o estructura
                    
                    **Ventajas:**
                    - Indica la carga fiscal real
                    - Puede mostrar ventajas competitivas fiscales
                    - Útil para proyecciones futuras
                    
                    **Desventajas:**
                    - Puede ser temporal (créditos fiscales, pérdidas arrastradas)
                    - Complejo de analizar en empresas multinacionales
                    - Sensible a cambios legislativos
                    
                    **¿Para qué sirve?**
                    - Evaluar la carga fiscal efectiva
                    - Identificar ventajas fiscales sostenibles
                    - Proyectar ganancias futuras netas
                    """,
                    "ejemplo": "Beneficio antes impuestos $500k, Impuestos $100k → Tasa 20%"
                },
                
                "Dividend": {
                    "definicion": "**Dividendo** - Pago periódico a accionistas",
                    "calculacion": "Monto total distribuido ÷ Acciones en circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Dividendo creciente**: Empresa con exceso de caja y confianza
                    - **Dividendo estable**: Empresa madura y predecible
                    - **Recorte de dividendo**: Posibles problemas financieros
                    
                    **Ventajas:**
                    - Proporciona income a inversores
                    - Señal de confianza del management
                    - Atractivo para inversores conservadores
                    
                    **Desventajas:**
                    - Dinero que no se reinvierte en el negocio
                    - Puede crear expectativas difíciles de mantener
                    - Empresas pueden endeudarse para pagarlos
                    
                    **¿Para qué sirve?**
                    - Evaluar política de distribución a accionistas
                    - Calcular yield y retorno total
                    - Identificar empresas income-oriented
                    """,
                    "ejemplo": "Dividendo trimestral $0.25 por acción → $1.00 anual"
                },
                
                "Dividend %": {
                    "definicion": "**Rendimiento por Dividendo** - Retorno por dividendo relativo al precio",
                    "calculacion": "Dividendo anual por acción ÷ Precio de la acción × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Yield bajo (1-3%)**: Empresas growth, poco income
                    - **Yield medio (3-6%)**: Empresas value, balance growth/income
                    - **Yield alto (>6%)**: Empresas income, posible riesgo
                    
                    **Ventajas:**
                    - Fácil de calcular y comparar
                    - Componente importante del retorno total
                    - Atractivo para inversores que buscan income
                    
                    **Desventajas:**
                    - Yield alto puede indicar problemas (precio bajo)
                    - No garantizado (puede ser recortado)
                    - Empresas pueden tener yield alto pero poco crecimiento
                    
                    **Sectores típicos:**
                    - Utilities: 3-5%
                    - REITs: 4-8%
                    - Tech: 0-2%
                    - Consumer Staples: 2-4%
                    
                    **¿Para qué sirve?**
                    - Evaluar atractivo para inversores income
                    - Comparar con alternativas de renta fija
                    - Calcular retorno total esperado
                    """,
                    "ejemplo": "Precio $100, Dividendo anual $4 → Yield = 4%"
                },
                
                "Payout Ratio": {
                    "definicion": "**Ratio de Pago** - Porcentaje de ganancias pagado como dividendo",
                    "calculacion": "Dividendo por acción ÷ EPS × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Payout bajo (<30%)**: Empresa retiene ganancias para crecimiento
                    - **Payout medio (30-60%)**: Balance entre dividendos y crecimiento
                    - **Payout alto (>60%)**: Empresa madura, poco crecimiento
                    - **Payout >100%**: Pagando más de lo que gana (insostenible)
                    
                    **Ventajas:**
                    - Indica sostenibilidad del dividendo
                    - Muestra la política de distribución vs reinversión
                    - Útil para evaluar crecimiento futuro
                    
                    **Desventajas:**
                    - Basado en ganancias que pueden ser volátiles
                    - No considera flujo de caja
                    - Puede variar significativamente entre años
                    
                    **¿Para qué sirve?**
                    - Evaluar sostenibilidad del dividendo
                    - Identificar empresas con potencial de aumento de dividendo
                    - Analizar el balance entre income y crecimiento
                    """,
                    "ejemplo": "EPS $5, Dividendo $2 → Payout Ratio = 40%"
                },
                
                "EPS Q/Q": {
                    "definicion": "**Crecimiento EPS Trimestral** - Cambio vs trimestre anterior",
                    "calculacion": "(EPS trimestre actual - EPS trimestre anterior) ÷ EPS trimestre anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo**: Mejora trimestral
                    - **Negativo**: Empeoramiento trimestral
                    - **Alto**: Fuerte momentum
                    - **Consistente positivo**: Trayectoria sólida
                    
                    **Ventajas:**
                    - Muestra momentum a corto plazo
                    - Útil para identificar tendencias emergentes
                    - Reacciona rápido a cambios en el negocio
                    
                    **Desventajas:**
                    - Muy volátil entre trimestres
                    - Sensible a estacionalidad
                    - Puede estar afectado por eventos únicos
                    
                    **¿Para qué sirve?**
                    - Evaluar performance trimestral
                    - Identificar cambios en momentum
                    - Timing de decisiones de inversión
                    """,
                    "ejemplo": "EPS Q1: $1.20, EPS Q2: $1.35 → Crecimiento 12.5%"
                },
                
                "Sales Q/Q": {
                    "definicion": "**Crecimiento Ventas Trimestral** - Cambio en ventas vs trimestre anterior",
                    "calculacion": "(Ventas trimestre actual - Ventas trimestre anterior) ÷ Ventas trimestre anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo**: Crecimiento orgánico o por adquisiciones
                    - **Negativo**: Contracción del negocio
                    - **Aceleración**: Crecimiento cada vez más rápido
                    - **Desaceleración**: Crecimiento perdiendo momentum
                    
                    **Ventajas:**
                    - Indica salud del top line
                    - Menos manipulable que las ganancias
                    - Buen indicador de demanda del producto/servicio
                    
                    **Desventajas:**
                    - No considera rentabilidad
                    - Puede estar inflado por adquisiciones
                    - Sensible a estacionalidad
                    
                    **¿Para qué sirve?**
                    - Evaluar crecimiento del negocio principal
                    - Identificar tendencias en demanda
                    - Comparar con expectativas del mercado
                    """,
                    "ejemplo": "Ventas Q1: $250M, Ventas Q2: $275M → Crecimiento 10%"
                },
                
                "Earnings Date": {
                    "definicion": "**Fecha de Resultados** - Próxima publicación de resultados trimestrales",
                    "calculacion": "Fecha calendario anunciada por la empresa",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Antes del opening/after closing**: Normal para minimizar impacto
                    - **Desviación del patrón habitual**: Posible sorpresa
                    - **Retraso inusual**: Posibles problemas
                    
                    **Ventajas:**
                    - Permite prepararse para la volatilidad
                    - Útil para estrategias de trading alrededor de earnings
                    - Indica transparencia del management
                    
                    **Desventajas:**
                    - Las fechas pueden cambiar
                    - No indica la calidad de los resultados
                    - Puede generar expectativas irreales
                    
                    **¿Para qué sirve?**
                    - Planificar timing de inversiones
                    - Gestionar riesgo alrededor de eventos
                    - Evaluar consistencia en comunicación
                    """,
                    "ejemplo": "Próximo earnings: 25 de Octubre, después del cierre"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")

        elif categoria == "🏦 DEUDA Y LIQUIDEZ (12 métricas)":
            st.subheader("🏦 DEUDA Y LIQUIDEZ - 12 Métricas")
            
            metricas = {
                "Total Debt": {
                    "definicion": "**Deuda Total** - Suma de deuda a corto y largo plazo",
                    "calculacion": "Deuda Corto Plazo + Deuda Largo Plazo",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Deuda creciente**: Posible expansión agresiva o problemas de caja
                    - **Deuda decreciente**: Desapalancamiento, mejora financiera
                    - **Sin deuda**: Empresa conservadora (puede perder oportunidades)
                    
                    **Ventajas:**
                    - Muestra la carga total de deuda
                    - Fácil de entender
                    - Base para otros ratios de deuda
                    
                    **Desventajas:**
                    - No considera la capacidad de pago
                    - No diferencia entre tipos de deuda
                    - Puede variar por ciclos empresariales
                    
                    **¿Para qué sirve?**
                    - Evaluar el apalancamiento total
                    - Comparar con patrimonio y activos
                    - Analizar tendencias de financiación
                    """,
                    "ejemplo": "Deuda corto plazo $50M + Deuda largo plazo $150M = Total Debt $200M"
                },
                
                "Debt/Eq": {
                    "definicion": "**Ratio Deuda/Patrimonio** - Relación entre deuda total y capital propio",
                    "calculacion": "Deuda Total ÷ Patrimonio Neto",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<0.5**: Conservador
                    - **0.5-1.0**: Moderado
                    - **>1.0**: Agresivo
                    - **>2.0**: Muy riesgoso
                    
                    **Ventajas:**
                    - Muestra estructura de capital
                    - Útil para comparar empresas del mismo sector
                    - Indica política financiera
                    
                    **Desventajas:**
                    - No considera el costo de la deuda
                    - Puede variar por valoración de patrimonio
                    - Sectores intensivos en capital pueden tener ratios altos normales
                    
                    **Sectores típicos:**
                    - Utilities: 1.0-1.5
                    - Telecom: 1.5-2.0
                    - Tech: 0.2-0.8
                    - Bancos: 3.0+ (estructura diferente)
                    
                    **¿Para qué sirve?**
                    - Evaluar riesgo financiero
                    - Comparar políticas de financiación
                    - Identificar posibles problemas de solvencia
                    """,
                    "ejemplo": "Deuda $200M, Patrimonio $250M → Debt/Eq = 0.8"
                },
                
                "LT Debt/Eq": {
                    "definicion": "**Deuda Largo Plazo/Patrimonio** - Deuda a largo plazo vs capital",
                    "calculacion": "Deuda Largo Plazo ÷ Patrimonio Neto",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Financiación estable a largo plazo
                    - **Bajo**: Poca deuda estructural
                    - **Creciente**: Más financiación vía deuda
                    
                    **Ventajas:**
                    - Enfocado en deuda estructural
                    - Menos volátil que deuda total
                    - Mejor para análisis de largo plazo
                    
                    **Desventajas:**
                    - Ignora deuda a corto plazo
                    - No considera vencimientos
                    - Puede enmascarar problemas de liquidez
                    
                    **¿Para qué sirve?**
                    - Evaluar estructura de capital permanente
                    - Analizar financiación de proyectos largos
                    - Comparar estabilidad financiera
                    """,
                    "ejemplo": "Deuda LP $150M, Patrimonio $250M → LT Debt/Eq = 0.6"
                },
                
                "Current Ratio": {
                    "definicion": "**Ratio Corriente** - Capacidad para pagar obligaciones a corto plazo",
                    "calculacion": "Activos Corrientes ÷ Pasivos Corrientes",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<1.0**: Posibles problemas de liquidez
                    - **1.0-1.5**: Aceptable
                    - **1.5-2.0**: Bueno
                    - **>2.0**: Excelente (pero puede indicar activos ociosos)
                    
                    **Ventajas:**
                    - Simple y ampliamente usado
                    - Buen indicador de salud a corto plazo
                    - Fácil de calcular
                    
                    **Desventajas:**
                    - No considera calidad de activos corrientes
                    - El inventario puede no ser líquido
                    - Puede variar estacionalmente
                    
                    **¿Para qué sirve?**
                    - Evaluar liquidez inmediata
                    - Detectar posibles problemas de pago
                    - Comparar con competidores del sector
                    """,
                    "ejemplo": "Activos corrientes $500k, Pasivos corrientes $300k → Current Ratio = 1.67"
                },
                
                "Quick Ratio": {
                    "definicion": "**Ratio Rápido** - Liquidez inmediata excluyendo inventario",
                    "calculacion": "(Activos Corrientes - Inventario) ÷ Pasivos Corrientes",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<0.5**: Muy bajo
                    - **0.5-1.0**: Aceptable
                    - **>1.0**: Bueno
                    - **>1.5**: Excelente
                    
                    **Ventajas:**
                    - Más conservador que Current Ratio
                    - Excluye inventario (menos líquido)
                    - Mejor indicador de liquidez real
                    
                    **Desventajas:**
                    - Puede ser demasiado conservador
                    - No considera rotación de inventario
                    - Algunas empresas dependen del inventario
                    
                    **¿Para qué sirve?**
                    - Evaluar capacidad de pago inmediata
                    - Análisis más realista de liquidez
                    - Detectar dependencia del inventario
                    """,
                    "ejemplo": "Activos corrientes $500k, Inventario $200k, Pasivos $300k → Quick Ratio = 1.0"
                },
                
                "Cash/Share": {
                    "definicion": "**Efectivo por Acción** - Reservas de efectivo por cada acción",
                    "calculacion": "Efectivo y Equivalentes ÷ Acciones en Circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Fuertes reservas, posibles dividendos especiales o recompras
                    - **Bajo**: Poco colchón de seguridad
                    - **Creciente**: Acumulación de caja
                    
                    **Ventajas:**
                    - Muestra colchón de seguridad por acción
                    - Útil para valoración
                    - Indica capacidad para oportunidades
                    
                    **Desventajas:**
                    - No considera deuda
                    - El efectivo puede estar destinado a obligaciones
                    - Demasiado efectivo puede indicar falta de oportunidades de inversión
                    
                    **¿Para qué sirve?**
                    - Evaluar margen de seguridad
                    - Identificar posibles recompras o dividendos
                    - Valoración en adquisiciones
                    """,
                    "ejemplo": "Efectivo $100M, 10M acciones → Cash/Share = $10"
                },
                
                "Cash Flow/Share": {
                    "definicion": "**Flujo de Caja por Acción** - Flujo operativo generado por acción",
                    "calculacion": "Flujo de Caja Operativo ÷ Acciones en Circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Fuerte generación de caja por acción
                    - **Creciente**: Mejora en eficiencia operativa
                    - **> EPS**: Calidad de ganancias alta
                    
                    **Ventajas:**
                    - Basado en caja real (no ganancias contables)
                    - Mejor indicador de salud financiera
                    - Difícil de manipular
                    
                    **Desventajas:**
                    - Puede ser volátil
                    - No considera inversiones de capital
                    - Sensible a cambios en capital de trabajo
                    
                    **¿Para qué sirve?**
                    - Evaluar calidad de ganancias
                    - Calcular capacidad de pago de dividendos
                    - Comparar con EPS
                    """,
                    "ejemplo": "FCF Operativo $80M, 10M acciones → Cash Flow/Share = $8"
                },
                
                "Total Cash": {
                    "definicion": "**Efectivo Total** - Dinero disponible en caja y equivalentes",
                    "calculacion": "Efectivo + Equivalentes de Efectivo",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Fuertes reservas líquidas
                    - **Bajo**: Dependencia de financiación externa
                    - **Óptimo**: Suficiente para operar + colchón de seguridad
                    
                    **Ventajas:**
                    - Muestra liquidez absoluta
                    - Fácil de entender
                    - Base para otros cálculos
                    
                    **Desventajas:**
                    - No considera obligaciones
                    - Puede estar en el extranjero con restricciones
                    - Demasiado efectivo puede ser ineficiente
                    
                    **¿Para qué sirve?**
                    - Evaluar solvencia a corto plazo
                    - Analizar capacidad para oportunidades
                    - Preparación para crisis
                    """,
                    "ejemplo": "Efectivo $50M + Equivalentes $30M = Total Cash $80M"
                },
                
                "Total Cash/Share": {
                    "definicion": "**Efectivo Total por Acción** - Similar a Cash/Share pero incluye equivalentes",
                    "calculacion": "Total Cash ÷ Acciones en Circulación",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Comparación con precio**: Si Cash/Share es alto vs precio, posible oportunidad
                    - **Tendencia**: Creciente es positivo
                    - **Sector**: Tech suele tener más cash que industriales
                    
                    **Ventajas:**
                    - Visión completa de liquidez por acción
                    - Útil para valoración
                    - Bueno para análisis comparativo
                    
                    **Desventajas:**
                    - No considera uso del efectivo
                    - Puede incluir efectivo restringido
                    - No diferencia entre efectivo operativo y no operativo
                    
                    **¿Para qué sirve?**
                    - Valoración relativa
                    - Identificar empresas con exceso de caja
                    - Evaluar potencial de recompra de acciones
                    """,
                    "ejemplo": "Total Cash $80M, 10M acciones → Total Cash/Share = $8"
                },
                
                "Working Capital": {
                    "definicion": "**Capital de Trabajo** - Recursos disponibles para operaciones diarias",
                    "calculacion": "Activos Corrientes - Pasivos Corrientes",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo**: Capacidad para operar sin problemas
                    - **Negativo**: Posibles problemas de liquidez
                    - **Creciente**: Mejora en gestión operativa
                    
                    **Ventajas:**
                    - Muestra salud operativa a corto plazo
                    - Indica eficiencia en gestión de capital de trabajo
                    - Buen predictor de problemas financieros
                    
                    **Desventajas:**
                    - No considera calidad de activos
                    - Puede ser manipulado con timing de pagos/cobros
                    - Varía por estacionalidad
                    
                    **¿Para qué sirve?**
                    - Evaluar salud operativa a corto plazo
                    - Detectar posibles problemas de liquidez
                    - Analizar eficiencia en gestión de capital
                    """,
                    "ejemplo": "Activos corrientes $500k, Pasivos corrientes $300k → Working Capital = $200k"
                },
                
                "Interest Coverage": {
                    "definicion": "**Cobertura de Intereses** - Capacidad para pagar intereses de la deuda",
                    "calculacion": "EBIT ÷ Gastos por Intereses",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<1.0**: No cubre intereses (muy peligroso)
                    - **1.0-1.5**: Muy justo
                    - **1.5-3.0**: Aceptable
                    - **>3.0**: Bueno
                    - **>5.0**: Excelente
                    
                    **Ventajas:**
                    - Mide capacidad de servicio de deuda
                    - Buen predictor de problemas financieros
                    - Fácil de calcular
                    
                    **Desventajas:**
                    - No considera amortización de principal
                    - Basado en EBIT (no cash flow)
                    - Puede variar con tipos de interés
                    
                    **¿Para qué sirve?**
                    - Evaluar riesgo de impago
                    - Comparar capacidad de endeudamiento
                    - Análisis de solvencia
                    """,
                    "ejemplo": "EBIT $50M, Intereses $10M → Interest Coverage = 5.0"
                },
                
                "Total Debt/EBITDA": {
                    "definicion": "**Deuda Total/EBITDA** - Años necesarios para pagar deuda con EBITDA",
                    "calculacion": "Deuda Total ÷ EBITDA",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<3.0**: Conservador
                    - **3.0-5.0**: Moderado
                    - **5.0-7.0**: Alto
                    - **>7.0**: Muy riesgoso
                    
                    **Ventajas:**
                    - Muy usado por agencias de rating
                    - Considera capacidad operativa de generar caja
                    - Bueno para comparar entre sectores
                    
                    **Desventajas:**
                    - El EBITDA no es flujo de caja
                    - No considera inversiones de capital
                    - Puede variar con ciclo económico
                    
                    **¿Para qué sirve?**
                    - Evaluar sostenibilidad de la deuda
                    - Comparar políticas de endeudamiento
                    - Análisis de riesgo crediticio
                    """,
                    "ejemplo": "Deuda Total $200M, EBITDA $50M → Debt/EBITDA = 4.0"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")

        elif categoria == "📊 EFICIENCIA OPERATIVA (10 métricas)":
            st.subheader("📊 EFICIENCIA OPERATIVA - 10 Métricas")
            
            metricas = {
                "Asset Turnover": {
                    "definicion": "**Rotación de Activos** - Eficiencia en uso de activos para generar ventas",
                    "calculacion": "Ventas ÷ Activos Totales Promedio",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Eficiente uso de activos
                    - **Bajo**: Activos subutilizados
                    - **Creciente**: Mejora en eficiencia
                    
                    **Ventajas:**
                    - Mide eficiencia operativa general
                    - Bueno para comparar empresas del mismo sector
                    - Refleja calidad de gestión
                    
                    **Desventajas:**
                    - Varía mucho entre sectores
                    - Puede estar influido por valoración de activos
                    - No considera rentabilidad
                    
                    **Sectores típicos:**
                    - Retail: 2.0-3.0 (alta rotación)
                    - Manufacturing: 0.8-1.2
                    - Utilities: 0.3-0.5 (activos intensivos)
                    
                    **¿Para qué sirve?**
                    - Evaluar eficiencia operativa
                    - Comparar gestión entre competidores
                    - Identificar mejoras en utilización de activos
                    """,
                    "ejemplo": "Ventas $1B, Activos promedio $500M → Asset Turnover = 2.0"
                },
                
                "Inventory Turnover": {
                    "definicion": "**Rotación de Inventario** - Veces que se renueva el inventario anual",
                    "calculacion": "Costo de Ventas ÷ Inventario Promedio",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Gestión eficiente de inventario
                    - **Bajo**: Exceso de inventario o ventas lentas
                    - **Óptimo**: Balance entre disponibilidad y costos
                    
                    **Ventajas:**
                    - Mide eficiencia en gestión de inventario
                    - Buen predictor de problemas operativos
                    - Sensible a cambios en demanda
                    
                    **Desventajas:**
                    - Varía por estacionalidad
                    - Depende del tipo de negocio
                    - Puede ser manipulado con valoración de inventario
                    
                    **Sectores típicos:**
                    - Grocery: 10-15
                    - Retail: 4-8
                    - Manufacturing: 2-4
                    
                    **¿Para qué sirve?**
                    - Evaluar eficiencia operativa
                    - Detectar problemas de ventas
                    - Optimizar niveles de inventario
                    """,
                    "ejemplo": "Costo ventas $600M, Inventario promedio $100M → Inventory Turnover = 6.0"
                },
                
                "Receivables Turnover": {
                    "definicion": "**Rotación de Cuentas por Cobrar** - Eficiencia en cobro a clientes",
                    "calculacion": "Ventas a Crédito ÷ Cuentas por Cobrar Promedio",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Cobros rápidos (eficiente)
                    - **Bajo**: Cobros lentos (posibles problemas)
                    - **Decreciente**: Posible deterioro de calidad de clientes
                    
                    **Ventajas:**
                    - Mide eficiencia en gestión de crédito
                    - Indicador de calidad de cartera
                    - Sensible a cambios en políticas de crédito
                    
                    **Desventajas:**
                    - Necesita datos de ventas a crédito (no siempre disponibles)
                    - Puede variar por estacionalidad
                    - No considera morosidad
                    
                    **¿Para qué sirve?**
                    - Evaluar políticas de crédito
                    - Detectar problemas de cobranza
                    - Comparar con términos de pago ofrecidos
                    """,
                    "ejemplo": "Ventas crédito $400M, Cuentas cobrar promedio $50M → Receivables Turnover = 8.0"
                },
                
                "Days Inventory": {
                    "definicion": "**Días de Inventario** - Días promedio que permanece el inventario",
                    "calculacion": "365 ÷ Inventory Turnover",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Bajo**: Inventario que se mueve rápido
                    - **Alto**: Inventario lento o excesivo
                    - **Óptimo**: Balance entre disponibilidad y costos
                    
                    **Ventajas:**
                    - Más intuitivo que turnover
                    - Fácil de comparar con términos de pago
                    - Bueno para gestión operativa
                    
                    **Desventajas:**
                    - Mismo que Inventory Turnover
                    - Sensible a estacionalidad
                    - Puede variar por mix de productos
                    
                    **Sectores típicos:**
                    - Fast food: 2-5 días
                    - Retail: 30-60 días
                    - Manufacturing: 60-90 días
                    
                    **¿Para qué sirve?**
                    - Gestión de niveles de inventario
                    - Evaluar eficiencia operativa
                    - Detectar productos obsoletos
                    """,
                    "ejemplo": "Inventory Turnover 6 → Days Inventory = 61 días"
                },
                
                "Days Sales Outstanding": {
                    "definicion": "**Días de Ventas Pendientes** - Días promedio para cobrar ventas",
                    "calculacion": "365 ÷ Receivables Turnover",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Bajo**: Cobros rápidos (bueno)
                    - **Alto**: Cobros lentos (malo)
                    - **Comparar con términos**: Si DSO > términos, problemas de cobro
                    
                    **Ventajas:**
                    - Fácil de entender y gestionar
                    - Bueno para seguimiento operativo
                    - Sensible a cambios en políticas
                    
                    **Desventajas:**
                    - Puede variar por mix de clientes
                    - Sensible a estacionalidad
                    - No considera morosidad
                    
                    **¿Para qué sirve?**
                    - Evaluar eficiencia de cobranza
                    - Gestionar capital de trabajo
                    - Detectar problemas con clientes
                    """,
                    "ejemplo": "Receivables Turnover 8 → DSO = 46 días"
                },
                
                "Payables Period": {
                    "definicion": "**Período de Pago a Proveedores** - Días promedio para pagar proveedores",
                    "calculacion": "365 ÷ (Compras ÷ Cuentas por Pagar Promedio)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Paga lentamente (usa proveedores como financiación)
                    - **Bajo**: Paga rápidamente (puede perder descuentos)
                    - **Óptimo**: Balance entre relaciones y costos
                    
                    **Ventajas:**
                    - Mide gestión de proveedores
                    - Indica poder de negociación
                    - Afecta capital de trabajo
                    
                    **Desventajas:**
                    - Datos de compras no siempre disponibles
                    - Puede variar por relaciones estratégicas
                    - No considera descuentos por pronto pago
                    
                    **¿Para qué sirve?**
                    - Optimizar capital de trabajo
                    - Evaluar relaciones con proveedores
                    - Comparar con términos de pago
                    """,
                    "ejemplo": "Compras $300M, Cuentas pagar $50M → Payables Period = 61 días"
                },
                
                "Cash Conversion Cycle": {
                    "definicion": "**Ciclo de Conversión de Efectivo** - Días desde pago a proveedores hasta cobro de clientes",
                    "calculacion": "Days Inventory + DSO - Payables Period",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo**: Necesita financiar operaciones
                    - **Negativo**: Proveedores financian operaciones (ideal)
                    - **Bajo**: Eficiente gestión de capital de trabajo
                    
                    **Ventajas:**
                    - Mide eficiencia global de capital de trabajo
                    - Buen predictor de necesidades de financiación
                    - Refleja calidad de gestión operativa
                    
                    **Desventajas:**
                    - Complejo de calcular
                    - Requiere múltiples datos
                    - Puede variar estacionalmente
                    
                    **¿Para qué sirve?**
                    - Evaluar eficiencia operativa global
                    - Gestionar necesidades de financiación
                    - Comparar con competidores
                    """,
                    "ejemplo": "DI 61 + DSO 46 - PP 61 = CCC 46 días"
                },
                
                "Fixed Asset Turnover": {
                    "definicion": "**Rotación de Activos Fijos** - Eficiencia en uso de activos fijos",
                    "calculacion": "Ventas ÷ Activos Fijos Netos Promedio",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Uso intensivo de activos fijos
                    - **Bajo**: Activos fijos subutilizados
                    - **Creciente**: Mejora en utilización
                    
                    **Ventajas:**
                    - Enfocado en activos productivos
                    - Bueno para empresas intensivas en capital
                    - Refleja decisiones de inversión
                    
                    **Desventajas:**
                    - Sensible a métodos de depreciación
                    - Varía por antigüedad de activos
                    - No considera mantenimiento
                    
                    **Sectores típicos:**
                    - Retail: 3-5
                    - Manufacturing: 1-2
                    - Utilities: 0.3-0.6
                    
                    **¿Para qué sirve?**
                    - Evaluar eficiencia de inversiones en activos fijos
                    - Comparar utilización de capacidad
                    - Análisis de decisiones de capex
                    """,
                    "ejemplo": "Ventas $1B, Activos fijos promedio $400M → Fixed Asset Turnover = 2.5"
                },
                
                "R&D/Sales": {
                    "definicion": "**Gastos I+D/Ventas** - Porcentaje de ventas invertido en investigación",
                    "calculacion": "Gastos de I+D ÷ Ventas × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Empresa innovadora, orientada al futuro
                    - **Bajo**: Empresa madura, poco innovación
                    - **Óptimo**: Balance entre innovación y rentabilidad
                    
                    **Ventajas:**
                    - Mide compromiso con innovación
                    - Bueno para empresas growth
                    - Indicador de ventajas competitivas futuras
                    
                    **Desventajas:**
                    - No garantiza resultados
                    - Puede ser gasto ineficiente
                    - Dificil de comparar entre sectores
                    
                    **Sectores típicos:**
                    - Biotech: 15-25%
                    - Software: 10-20%
                    - Pharma: 12-18%
                    - Industrial: 2-5%
                    
                    **¿Para qué sirve?**
                    - Evaluar estrategia de innovación
                    - Comparar con competidores
                    - Analizar sostenibilidad de ventajas competitivas
                    """,
                    "ejemplo": "I+D $50M, Ventas $500M → R&D/Sales = 10%"
                },
                
                "SG&A/Sales": {
                    "definicion": "**Gastos Generales/Ventas** - Eficiencia en gastos operativos",
                    "calculacion": "Gastos de Venta, Generales y Administrativos ÷ Ventas × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Estructura costosa, posible ineficiencia
                    - **Bajo**: Estructura lean, eficiente
                    - **Decreciente**: Mejora en eficiencia operativa
                    
                    **Ventajas:**
                    - Mide eficiencia en gastos operativos
                    - Bueno para detectar burocracia
                    - Sensible a economías de escala
                    
                    **Desventajas:**
                    - Puede incluir gastos estratégicos
                    - Varía por modelo de negocio
                    - Reducciones excesivas pueden dañar crecimiento
                    
                    **Sectores típicos:**
                    - Software: 20-30%
                    - Retail: 15-25%
                    - Manufacturing: 10-15%
                    
                    **¿Para qué sirve?**
                    - Evaluar eficiencia operativa
                    - Identificar oportunidades de mejora
                    - Comparar estructura de costos
                    """,
                    "ejemplo": "SG&A $120M, Ventas $500M → SG&A/Sales = 24%"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")

        elif categoria == "📈 CRECIMIENTO (8 métricas)":
            st.subheader("📈 CRECIMIENTO - 8 Métricas")
            
            metricas = {
                "Sales Growth 5Y": {
                    "definicion": "**Crecimiento de Ventas 5 Años** - Tasa crecimiento anual compuesto",
                    "calculacion": "(Ventas año actual ÷ Ventas año base)^(1/5) - 1",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<5%**: Crecimiento lento (madurez)
                    - **5-15%**: Crecimiento moderado
                    - **>15%**: Crecimiento rápido
                    - **Negativo**: Contracción
                    
                    **Ventajas:**
                    - Muestra tendencia de largo plazo
                    - Menos volátil que anual
                    - Buen indicador de momentum
                    
                    **Desventajas:**
                    - Puede enmascarar cambios recientes
                    - Sensible al año base elegido
                    - No considera adquisiciones orgánicas vs inorgánicas
                    
                    **¿Para qué sirve?**
                    - Evaluar trayectoria histórica
                    - Comparar con expectativas futuras
                    - Análisis de madurez del negocio
                    """,
                    "ejemplo": "Ventas crecieron de $200M a $400M en 5 años → 15% CAGR"
                },
                
                "EPS Growth 5Y": {
                    "definicion": "**Crecimiento EPS 5 Años** - Tasa crecimiento ganancias por acción",
                    "calculacion": "(EPS año actual ÷ EPS año base)^(1/5) - 1",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Consistente >10%**: Empresa growth de calidad
                    - **Volátil**: Resultados inconsistentes
                    - **Decreciente**: Posible saturación o problemas
                    
                    **Ventajas:**
                    - Enfocado en valor por acción
                    - Considera efecto de recompras
                    - Mejor que crecimiento de beneficio neto
                    
                    **Desventajas:**
                    - Puede ser afectado por eventos extraordinarios
                    - Sensible a cambios en número de acciones
                    - No considera calidad de ganancias
                    
                    **¿Para qué sirve?**
                    - Evaluar creación de valor histórico
                    - Calcular PEG ratio
                    - Proyectar crecimiento futuro
                    """,
                    "ejemplo": "EPS creció de $2 a $4 en 5 años → 15% CAGR"
                },
                
                "Sales Growth Q/Q": {
                    "definicion": "**Crecimiento Ventas Trimestral** - Cambio vs trimestre anterior",
                    "calculacion": "(Ventas Q actual - Ventas Q anterior) ÷ Ventas Q anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Positivo**: Momentum positivo
                    - **Negativo**: Desaceleración
                    - **Aceleración**: Crecimiento cada vez más rápido
                    - **Desaceleración**: Pérdida de momentum
                    
                    **Ventajas:**
                    - Muestra momentum reciente
                    - Sensible a cambios en el negocio
                    - Útil para trading
                    
                    **Desventajas:**
                    - Muy volátil
                    - Sensible a estacionalidad
                    - Puede estar distorsionado por eventos únicos
                    
                    **¿Para qué sirve?**
                    - Evaluar performance reciente
                    - Identificar cambios en tendencia
                    - Timing de decisiones de inversión
                    """,
                    "ejemplo": "Ventas Q1 $250M, Q2 $275M → Crecimiento 10%"
                },
                
                "EPS Growth Q/Q": {
                    "definicion": "**Crecimiento EPS Trimestral** - Cambio ganancias vs trimestre anterior",
                    "calculacion": "(EPS Q actual - EPS Q anterior) ÷ EPS Q anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Beat estimates**: Supera expectativas (positivo)
                    - **Miss estimates**: No alcanza expectativas (negativo)
                    - **Guide higher**: Aumenta guidance (muy positivo)
                    
                    **Ventajas:**
                    - Muestra momentum reciente de ganancias
                    - Muy seguido por el mercado
                    - Bueno para estrategias de earnings
                    
                    **Desventajas:**
                    - Extremadamente volátil
                    - Sensible a estacionalidad
                    - Las estimaciones pueden ser erróneas
                    
                    **¿Para qué sirve?**
                    - Evaluar resultados trimestrales
                    - Identificar sorpresas de ganancias
                    - Trading alrededor de earnings
                    """,
                    "ejemplo": "EPS Q1 $1.20, Q2 $1.35 → Crecimiento 12.5%"
                },
                
                "Sales Growth Y/Y": {
                    "definicion": "**Crecimiento Ventas Interanual** - Cambio vs mismo periodo año anterior",
                    "calculacion": "(Ventas periodo actual - Ventas mismo periodo año anterior) ÷ Ventas año anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Elimina estacionalidad**: Mejor comparación que Q/Q
                    - **Tendencia real**: Muestra crecimiento subyacente
                    - **Comparable**: Mismo periodo estacional
                    
                    **Ventajas:**
                    - Elimina efecto estacional
                    - Mejor indicador de tendencia
                    - Ampliamente utilizado
                    
                    **Desventajas:**
                    - Puede enmascarar cambios recientes
                    - Menos frecuente que Q/Q
                    - Sensible a eventos únicos anuales
                    
                    **¿Para qué sirve?**
                    - Evaluar crecimiento real
                    - Comparar performance anual
                    - Análisis de tendencias fundamentales
                    """,
                    "ejemplo": "Ventas Q2 2024 $300M, Q2 2023 $250M → Crecimiento 20%"
                },
                
                "EPS Growth Y/Y": {
                    "definicion": "**Crecimiento EPS Interanual** - Cambio ganancias vs mismo periodo año anterior",
                    "calculacion": "(EPS periodo actual - EPS mismo periodo año anterior) ÷ EPS año anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Crecimiento orgánico**: Mejora en operaciones
                    - **Decrecimiento**: Problemas operativos o comparación difícil
                    - **Consistencia**: Crecimiento sostenido es positivo
                    
                    **Ventajas:**
                    - Elimina estacionalidad
                    - Mejor indicador de tendencia de ganancias
                    - Menos volátil que Q/Q
                    
                    **Desventajas:**
                    - Puede estar afectado por eventos únicos
                    - No considera cambios recientes
                    - Sensible a base de comparación
                    
                    **¿Para qué sirve?**
                    - Evaluar crecimiento real de ganancias
                    - Comparar con expectativas
                    - Análisis de calidad de crecimiento
                    """,
                    "ejemplo": "EPS Q2 2024 $1.50, Q2 2023 $1.25 → Crecimiento 20%"
                },
                
                "Revenue Growth (ttm)": {
                    "definicion": "**Crecimiento de Ingresos últimos 12 meses** - Cambio vs mismo periodo anterior",
                    "calculacion": "(Ventas ttm - Ventas ttm año anterior) ÷ Ventas ttm año anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Muestra tendencia**: Crecimiento en los últimos 12 meses
                    - **Menos volátil**: Que trimestral
                    - **Visión actualizada**: Pero con perspectiva
                    
                    **Ventajas:**
                    - Combina actualidad con estabilidad
                    - Menos volátil que trimestral
                    - Bueno para análisis fundamental
                    
                    **Desventajas:**
                    - Puede enmascarar cambios recientes
                    - Menos frecuente que trimestral
                    - Sensible a eventos pasados
                    
                    **¿Para qué sirve?**
                    - Evaluar crecimiento reciente con perspectiva
                    - Comparar con competidores
                    - Análisis de momentum fundamental
                    """,
                    "ejemplo": "Ventas ttm $1.2B, ttm año anterior $1.0B → Crecimiento 20%"
                },
                
                "EPS Growth (ttm)": {
                    "definicion": "**Crecimiento EPS últimos 12 meses** - Cambio ganancias vs mismo periodo anterior",
                    "calculacion": "(EPS ttm - EPS ttm año anterior) ÷ EPS ttm año anterior × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Crecimiento sostenido**: Positivo para valoración
                    - **Volátil**: Resultados inconsistentes
                    - **Decreciente**: Posibles problemas
                    
                    **Ventajas:**
                    - Visión actualizada con perspectiva
                    - Menos volátil que trimestral
                    - Bueno para análisis de valoración
                    
                    **Desventajas:**
                    - Puede estar afectado por eventos pasados
                    - Menos frecuente que trimestral
                    - Sensible a base de comparación
                    
                    **¿Para qué sirve?**
                    - Evaluar crecimiento reciente de ganancias
                    - Calcular ratios de crecimiento
                    - Análisis fundamental para inversión
                    """,
                    "ejemplo": "EPS ttm $5.00, ttm año anterior $4.00 → Crecimiento 25%"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")

        elif categoria == "📊 INDICADORES TÉCNICOS (10 métricas)":
            st.subheader("📊 INDICADORES TÉCNICOS - 10 Métricas")
            
            metricas = {
                "Beta": {
                    "definicion": "**Volatilidad vs Mercado** - Sensibilidad de la acción vs benchmark",
                    "calculacion": "Covarianza(Acción, Mercado) ÷ Varianza(Mercado)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<0.8**: Defensivo (menos volátil que mercado)
                    - **0.8-1.2**: Neutral (similar volatilidad)
                    - **>1.2**: Agresivo (más volátil que mercado)
                    - **Negativo**: Se mueve en dirección opuesta (raro)
                    
                    **Ventajas:**
                    - Mide riesgo sistemático
                    - Útil para construcción de carteras
                    - Base para modelo CAPM
                    
                    **Desventajas:**
                    - Basado en datos históricos
                    - Asume distribuciones normales
                    - Puede cambiar con el tiempo
                    
                    **¿Para qué sirve?**
                    - Evaluar riesgo vs recompensa esperada
                    - Construcción de carteras diversificadas
                    - Cálculo de costo de capital
                    """,
                    "ejemplo": "Beta 1.5: si mercado ±10%, acción ±15% en promedio"
                },
                
                "RSI (14)": {
                    "definicion": "**Índice de Fuerza Relativa** - Oscilador de momentum",
                    "calculacion": "100 - (100 ÷ (1 + (Ganancia promedio ÷ Pérdida promedio)))",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **>70**: Sobrecomprado (posible corrección)
                    - **<30**: Sobrevendido (posible rebote)
                    - **50**: Neutral
                    - **Divergencias**: Señales fuertes
                    
                    **Ventajas:**
                    - Identifica condiciones extremas
                    - Fácil de interpretar
                    - Ampliamente seguido
                    
                    **Desventajas:**
                    - Puede dar señales prematuras en tendencias fuertes
                    - Menos efectivo en mercados laterales
                    - Parámetro dependiente (14 períodos típico)
                    
                    **¿Para qué sirve?**
                    - Identificar puntos de entrada/salida
                    - Confirmar momentum
                    - Detectar posibles reversiones
                    """,
                    "ejemplo": "RSI 75 → condición sobrecomprada, posible corrección"
                },
                
                "Volatility": {
                    "definicion": "**Volatilidad** - Desviación estándar de rendimientos",
                    "calculacion": "Desviación estándar(rendimientos diarios) × √252",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<20%**: Baja volatilidad (estable)
                    - **20-40%**: Volatilidad media
                    - **>40%**: Alta volatilidad (riesgosa)
                    - **>80%**: Extremadamente volátil
                    
                    **Ventajas:**
                    - Mide riesgo total
                    - Base para muchos modelos
                    - Fácil de comparar
                    
                    **Desventajas:**
                    - Asume distribuciones normales
                    - No diferencia entre riesgo arriba/abajo
                    - Basado en histórico
                    
                    **¿Para qué sirve?**
                    - Evaluar riesgo de la inversión
                    - Dimensionar posiciones
                    - Comparar con rendimiento esperado
                    """,
                    "ejemplo": "Volatilidad 30% → movimientos típicos de ±30% anuales"
                },
                
                "ATR": {
                    "definicion": "**Average True Range** - Volatilidad basada en rangos de trading",
                    "calculacion": "Media móvil de True Range (máx(alto-bajo, |alto-cierre anterior|, |bajo-cierre anterior|))",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto**: Alta volatilidad intradía
                    - **Bajo**: Baja volatilidad intradía
                    - **Creciente**: Aumento volatilidad
                    - **Decreciente**: Disminución volatilidad
                    
                    **Ventajas:**
                    - Considera gaps de precios
                    - Mejor que volatilidad basada solo en cierres
                    - Útil para stops y targets
                    
                    **Desventajas:**
                    - No direccional
                    - Depende del período elegido
                    - Menos conocido que volatilidad estándar
                    
                    **¿Para qué sirve?**
                    - Colocar stops loss dinámicos
                    - Evaluar condiciones de trading
                    - Gestión de riesgo intradía
                    """,
                    "ejemplo": "ATR $2.50 → movimiento intradía típico de $2.50"
                },
                
                "SMA 20": {
                    "definicion": "**Media Móvil Simple 20 días** - Tendencia corto plazo",
                    "calculacion": "Suma últimos 20 cierres ÷ 20",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Precio > SMA**: Tendencia alcista
                    - **Precio < SMA**: Tendencia bajista
                    - **Cruces**: Posibles cambios de tendencia
                    - **Soporte/Resistencia**: Niveles importantes
                    
                    **Ventajas:**
                    - Suaviza el ruido
                    - Fácil de calcular e interpretar
                    - Ampliamente usado
                    
                    **Desventajas:**
                    - Retraso (lagging indicator)
                    - Menos efectivo en mercados laterales
                    - Parámetro dependiente
                    
                    **¿Para qué sirve?**
                    - Identificar tendencias
                    - Señales de compra/venta
                    - Niveles de soporte/resistencia
                    """,
                    "ejemplo": "Precio $105, SMA20 $100 → tendencia alcista corto plazo"
                },
                
                "SMA 50": {
                    "definicion": "**Media Móvil Simple 50 días** - Tendencia medio plazo",
                    "calculacion": "Suma últimos 50 cierres ÷ 50",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Tendencia intermedia**: Más suave que SMA20
                    - **Cruces con SMA20**: Señales de momentum
                    - **Soporte/Resistencia**: Niveles más fuertes
                    
                    **Ventajas:**
                    - Menos ruido que SMA20
                    - Mejor para tendencias intermedias
                    - Menos señales falsas
                    
                    **Desventajas:**
                    - Más retraso que SMA20
                    - Puede perder movimientos rápidos
                    - Parámetro fijo
                    
                    **¿Para qué sirve?**
                    - Confirmar tendencias
                    - Filtrar señales de corto plazo
                    - Análisis de momentum intermedio
                    """,
                    "ejemplo": "SMA20 > SMA50 → momentum alcista confirmado"
                },
                
                "SMA 200": {
                    "definicion": "**Media Móvil Simple 200 días** - Tendencia largo plazo",
                    "calculacion": "Suma últimos 200 cierres ÷ 200",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Tendencia principal**: Bull market vs Bear market
                    - **Soporte/Resistencia mayor**: Nivel muy importante
                    - **Golden Cross/Death Cross**: Señales mayores
                    
                    **Ventajas:**
                    - Define tendencia principal
                    - Muy seguido por instituciones
                    - Señales fuertes y confiables
                    
                    **Desventajas:**
                    - Mucho retraso
                    - Puede perder grandes movimientos
                    - Menos útil para trading corto
                    
                    **¿Para qué sirve?**
                    - Determinar tendencia principal
                    - Señales de inversión (no trading)
                    - Análisis de largo plazo
                    """,
                    "ejemplo": "Precio > SMA200 → tendencia alcista principal"
                },
                
                "Volume": {
                    "definicion": "**Volumen** - Acciones negociadas en el período",
                    "calculacion": "Número total de acciones negociadas",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto volumen**: Confirmación de movimiento
                    - **Bajo volumen**: Falta de convicción
                    - **Volume spikes**: Eventos importantes
                    - **Divergencias**: Señales de debilidad
                    
                    **Ventajas:**
                    - Confirma price action
                    - Indica interés institucional
                    - Detecta acumulación/distribución
                    
                    **Desventajas:**
                    - No da señales por sí solo
                    - Puede ser manipulado en acciones pequeñas
                    - Varía por liquidez de la acción
                    
                    **¿Para qué sirve?**
                    - Confirmar rupturas de soporte/resistencia
                    - Detectar interés institucional
                    - Identificar posibles reversiones
                    """,
                    "ejemplo": "Ruptura con alto volumen → señal más confiable"
                },
                
                "Avg Volume": {
                    "definicion": "**Volumen Promedio** - Volumen medio histórico",
                    "calculacion": "Media volumen últimos 20-30 días",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Volume > Avg**: Interés inusual
                    - **Volume < Avg**: Poco interés
                    - **Cambios en avg volume**: Cambio en liquidez/perfil
                    
                    **Ventajas:**
                    - Proporciona contexto
                    - Detecta anomalías
                    - Útil para screening
                    
                    **Desventajas:**
                    - Basado en histórico
                    - Puede cambiar estructuralmente
                    - No considera eventos conocidos
                    
                    **¿Para qué sirve?**
                    - Evaluar liquidez relativa
                    - Detectar interés inusual
                    - Filtrar acciones por liquidez
                    """,
                    "ejemplo": "Volume actual 2M, Avg Volume 1M → interés inusual"
                },
                
                "Rel Volume": {
                    "definicion": "**Volumen Relativo** - Volumen actual vs promedio",
                    "calculacion": "Volume actual ÷ Avg Volume",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<0.5**: Muy bajo volumen
                    - **0.5-1.5**: Volumen normal
                    - **1.5-3.0**: Alto volumen
                    - **>3.0**: Volumen muy alto
                    
                    **Ventajas:**
                    - Normalizado y comparable
                    - Fácil de interpretar
                    - Bueno para screening
                    
                    **Desventajas:**
                    - Depende del período de avg volume
                    - Puede dar falsas señales en eventos conocidos
                    - No considera dirección del movimiento
                    
                    **¿Para qué sirve?**
                    - Identificar acciones con volumen inusual
                    - Detectar acumulación/distribución
                    - Screening para oportunidades
                    """,
                    "ejemplo": "Rel Volume 2.5 → volumen 2.5x el normal, interés inusual"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")

        elif categoria == "🏢 DATOS CORPORATIVOS (8 métricas)":
            st.subheader("🏢 DATOS CORPORATIVOS - 8 Métricas")
            
            metricas = {
                "Shares Out": {
                    "definicion": "**Acciones en Circulación** - Número total de acciones emitidas",
                    "calculacion": "Acciones comunes emitidas - Acciones en tesorería",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Creciente**: Dilución (emisiones)
                    - **Decreciente**: Recompra de acciones
                    - **Estable**: Política conservadora
                    
                    **Ventajas:**
                    - Base para cálculo por acción
                    - Muestra política de capital
                    - Afecta valoración
                    
                    **Desventajas:**
                    - No considera clases diferentes
                    - Puede incluir acciones restringidas
                    - No muestra float real
                    
                    **¿Para qué sirve?**
                    - Calcular market cap
                    - Evaluar políticas de capital
                    - Analizar dilución/recompra
                    """,
                    "ejemplo": "10 millones de acciones en circulación"
                },
                
                "Float": {
                    "definicion": "**Acciones Flotantes** - Acciones disponibles para trading público",
                    "calculacion": "Shares Out - Acciones restringidas (insiders, control)",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Float pequeño**: Alta volatilidad posible
                    - **Float grande**: Más liquidez
                    - **Float vs Shares Out**: Grado de control insider
                    
                    **Ventajas:**
                    - Mejor indicador de liquidez real
                    - Muestra concentración de propiedad
                    - Útil para análisis técnico
                    
                    **Desventajas:**
                    - Los datos pueden ser estimados
                    - Puede cambiar con el tiempo
                    - No considera bloqueos regulatorios
                    
                    **¿Para qué sirve?**
                    - Evaluar liquidez real
                    - Analizar riesgo de manipulación
                    - Gestión de tamaño de posición
                    """,
                    "ejemplo": "Shares Out 10M, Float 8M → 80% disponible para trading"
                },
                
                "Insider Own": {
                    "definicion": "**Propiedad Insider** - % acciones poseídas por directivos y consejo",
                    "calculacion": "Acciones de insiders ÷ Shares Out × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto (>10%)**: Alineación con accionistas
                    - **Bajo (<5%)**: Posible falta de alineación
                    - **Muy alto (>30%)**: Control concentrado
                    
                    **Ventajas:**
                    - Mide alineación de intereses
                    - Buen predictor de performance
                    - Refleja confianza del management
                    
                    **Desventajas:**
                    - No considera tipos de acciones
                    - Puede incluir holdings pasivos
                    - Datos con retraso
                    
                    **¿Para qué sirve?**
                    - Evaluar gobierno corporativo
                    - Analizar alineación de intereses
                    - Detectar posibles conflictos
                    """,
                    "ejemplo": "Insiders poseen 15% de las acciones → buena alineación"
                },
                
                "Insider Trans": {
                    "definicion": "**Transacciones Insider** - Compras y ventas de directivos",
                    "calculacion": "Net buying/selling de insiders en período",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Net buying**: Confianza en el futuro
                    - **Net selling**: Puede ser normal (diversificación) o preocupante
                    - **Patrones**: Compras consistentes son muy positivas
                    
                    **Ventajas:**
                    - Información privilegiada (legal)
                    - Muy seguido por el mercado
                    - Buen predictor de performance
                    
                    **Desventajas:**
                    - Las ventas pueden ser por razones personales
                    - Datos con retraso (form 4)
                    - Puede ser manipulado con timing
                    
                    **¿Para qué sirve?**
                    - Confirmar tesis de inversión
                    - Detectar posibles problemas
                    - Señales de confianza del management
                    """,
                    "ejemplo": "CEO compró 50,000 acciones → señal muy positiva"
                },
                
                "Inst Own": {
                    "definicion": "**Propiedad Institucional** - % acciones poseídas por fondos e instituciones",
                    "calculacion": "Acciones de instituciones ÷ Shares Out × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Alto (>60%)**: Aprobación institucional
                    - **Bajo (<30%)**: Poco seguimiento institucional
                    - **Creciente**: Mayor interés profesional
                    
                    **Ventajas:**
                    - Mapeo de interés profesional
                    - Indica calidad de la empresa
                    - Refleja liquidez institucional
                    
                    **Desventajas:**
                    - Instituciones pueden ser wrong
                    - Datos trimestrales con retraso
                    - No diferencia entre tipos de instituciones
                    
                    **¿Para qué sirve?**
                    - Evaluar calidad de la empresa
                    - Analizar seguimiento profesional
                    - Detectar cambios en percepción
                    """,
                    "ejemplo": "70% propiedad institucional → buena aprobación profesional"
                },
                
                "Inst Trans": {
                    "definicion": "**Transacciones Institucionales** - Compras/ventas de fondos",
                    "calculacion": "Net buying/selling de instituciones en período",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Net buying**: Aprobación profesional
                    - **Net selling**: Preocupación profesional
                    - **Cambios bruscos**: Señales fuertes
                    - **Calidad instituciones**: Importa quién compra/vende
                    
                    **Ventajas:**
                    - Muestra sentiment profesional
                    - Datos de gestores sofisticados
                    - Puede anticipar movimientos
                    
                    **Desventajas:**
                    - Datos con retraso (13F trimestral)
                    - Agregado, no detalle por institución
                    - Puede ser momentum following
                    
                    **¿Para qué sirve?**
                    - Confirmar tesis de inversión
                    - Seguir smart money
                    - Detectar cambios en percepción profesional
                    """,
                    "ejemplo": "Fondos value reconocidos comprando → señal positiva"
                },
                
                "Short Float": {
                    "definicion": "**Short Interest** - % acciones vendidas en corto",
                    "calculacion": "Acciones vendidas en corto ÷ Float × 100",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **Bajo (<5%)**: Poco pesimismo
                    - **Moderado (5-10%)**: Escepticismo normal
                    - **Alto (10-20%)**: Significativo pesimismo
                    - **Muy alto (>20%)**: Posible short squeeze
                    
                    **Ventajas:**
                    - Mapeo de sentiment negativo
                    - Identifica posibles squeezes
                    - Refleja controversia
                    
                    **Desventajas:**
                    - Los shorts pueden tener razón
                    - Datos con retraso (semanal/biweekly)
                    - No considera timing de shorts
                    
                    **¿Para qué sirve?**
                    - Evaluar controversia sobre la acción
                    - Identificar oportunidades de squeeze
                    - Analizar riesgo de covering rallies
                    """,
                    "ejemplo": "Short Float 25% → alto pesimismo, posible squeeze"
                },
                
                "Short Ratio": {
                    "definicion": "**Días para Cubrir** - Tiempo para cubrir posiciones cortas",
                    "calculacion": "Acciones vendidas en corto ÷ Volumen promedio diario",
                    "interpretacion": """
                    **¿Qué significa?**
                    - **<3 días**: Bajo riesgo de squeeze
                    - **3-7 días**: Riesgo moderado
                    - **>7 días**: Alto riesgo de squeeze
                    - **>10 días**: Riesgo muy alto
                    
                    **Ventajas:**
                    - Mejor que Short Float solo
                    - Considera liquidez
                    - Buen predictor de squeeze potential
                    
                    **Desventajas:**
                    - Basado en volumen histórico
                    - Puede cambiar rápidamente
                    - No considera convicción de shorts
                    
                    **¿Para qué sirve?**
                    - Evaluar riesgo de short squeeze
                    - Analizar dinámica de covering
                    - Gestión de riesgo en posiciones cortas
                    """,
                    "ejemplo": "Short Ratio 12 días → alto riesgo de squeeze"
                }
            }
            
            for metrica, detalles in metricas.items():
                with st.expander(f"**{metrica}**"):
                    st.write(f"**📖 DEFINICIÓN:** {detalles['definicion']}")
                    st.write(f"**🧮 CÁLCULO:** {detalles['calculacion']}")
                    st.markdown("**📊 INTERPRETACIÓN DETALLADA:**")
                    st.write(detalles['interpretacion'])
                    if 'ejemplo' in detalles:
                        st.info(f"**🔢 EJEMPLO:** {detalles['ejemplo']}")

        elif categoria == "⚡ MÉTRICAS AVANZADAS DE RIESGO":
            st.subheader("⚡ Métricas Avanzadas de Riesgo y Rendimiento")
            st.write("**Métricas sofisticadas para análisis profesional**")
            
            metricas_avanzadas = {
                "Beta (Riesgo Sistemático)": {
                    "definicion": "Mide la volatilidad de una acción en relación con el mercado completo.",
                    "formula": "Covarianza(Acción, Mercado) / Varianza(Mercado)",
                    "interpretacion": "**<0.8**: Defensivo | **0.8-1.2**: Neutral | **>1.2**: Agresivo",
                    "uso": "Para determinar qué tan sensible es una acción a los movimientos del mercado."
                },
                "Alpha": {
                    "definicion": "Rendimiento excedente sobre lo esperado dado su nivel de riesgo (Beta).",
                    "formula": "Rendimiento Real - (Beta × Rendimiento Mercado)",
                    "interpretacion": "**Alpha > 0**: Supera expectativas | **Alpha < 0**: No alcanza expectativas",
                    "uso": "Medir la habilidad del gestor o el desempeño anormal."
                },
                "Sharpe Ratio": {
                    "definicion": "Rendimiento excedente por unidad de riesgo total.",
                    "formula": "(Rendimiento - Tasa Libre Riesgo) / Volatilidad",
                    "interpretacion": "**>1.0**: Excelente | **0.5-1.0**: Bueno | **<0.5**: Pobre",
                    "uso": "Comparar fondos o estrategias ajustando por riesgo total."
                },
                "Sortino Ratio": {
                    "definicion": "Similar a Sharpe pero solo considera riesgo bajista (desviación negativa).",
                    "formula": "(Rendimiento - Tasa Libre Riesgo) / Volatilidad Bajista",
                    "interpretacion": "**>2.0**: Excelente | **1.0-2.0**: Bueno | **<1.0**: Mejorable",
                    "uso": "Mejor métrica cuando preocupa más las pérdidas que la volatilidad general."
                },
                "Treynor Ratio": {
                    "definicion": "Rendimiento excedente por unidad de riesgo sistemático (Beta).",
                    "formula": "(Rendimiento - Tasa Libre Riesgo) / Beta",
                    "interpretacion": "Cuanto mayor mejor. Comparar con benchmark del sector.",
                    "uso": "Para carteras diversificadas donde el riesgo no sistemático es mínimo."
                },
                "Information Ratio": {
                    "definicion": "Rendimiento activo por unidad de riesgo activo (tracking error).",
                    "formula": "(Rendimiento Cartera - Rendimiento Benchmark) / Tracking Error",
                    "interpretacion": "**>0.5**: Buen gestor activo | **>0.75**: Excelente gestor",
                    "uso": "Evaluar gestión activa vs benchmark."
                }
            }
            
            for metrica, detalles in metricas_avanzadas.items():
                st.markdown(f"### {metrica}")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write(f"**📖 Definición**: {detalles['definicion']}")
                    st.write(f"**🧮 Fórmula**: {detalles['formula']}")
                
                with col2:
                    st.write(f"**📊 Interpretación**: {detalles['interpretacion']}")
                    st.write(f"**🎯 Uso Práctico**: {detalles['uso']}")
                
                # Ejemplos prácticos
                if "Beta" in metrica:
                    st.info("**Ejemplo**: Una acción con Beta 1.5 subirá 15% si el mercado sube 10%, pero caerá 15% si el mercado cae 10%")
                elif "Sharpe" in metrica:
                    st.info("**Ejemplo**: Sharpe 1.2 significa que por cada 1% de riesgo, genera 1.2% de rendimiento excedente")
                elif "Alpha" in metrica:
                    st.info("**Ejemplo**: Alpha 0.05 significa que superó en 5% al rendimiento esperado dado su riesgo")
                
                st.markdown("---")

        else:  # Consejos Prácticos de Inversión
            st.subheader("💡 Consejos Prácticos de Inversión")
            st.write("**Sabiduría probada para tomar mejores decisiones**")
            
            # Consejos organizados por categoría
            categorias_consejos = {
                "🔍 Investigación y Análisis": [
                    "**Conoce el negocio**: Invierte solo en empresas que entiendas completamente",
                    "**Análisis competitivo**: Evalúa ventajas competitivas duraderas (moats)",
                    "**Sector y tendencias**: Invierte en sectores con tailwinds, no headwinds",
                    "**Calidad management**: Investiga el track record del equipo directivo",
                    "**Múltiples métricas**: Nunca bases decisiones en una sola métrica"
                ],
                "📈 Gestión de Riesgo": [
                    "**Diversificación inteligente**: No sobre-diversifiques, pero tampoco pongas todos los huevos en una canasta",
                    "**Tamaño de posición**: Nunca arriesgues más del 5% de tu cartera en una sola idea",
                    "**Stop losses mentales**: Define tu precio de venta antes de comprar",
                    "**Riesgo asimétrico**: Busca oportunidades con upside potencial > downside risk",
                    "**Liquidez**: Considera siempre cuán fácil puedes salir de la inversión"
                ],
                "⏳ Psicología y Disciplina": [
                    "**Paciencia**: El tiempo en el mercado > timing del mercado",
                    "**Control emocional**: El miedo y la codicia son tus peores enemigos",
                    "**Independencia**: Piensa por ti mismo, no sigas la manada",
                    "**Humildad**: Reconoce cuando te equivocas y ajusta",
                    "**Consistencia**: Sigue tu proceso invariablemente"
                ],
                "💰 Valoración y Timing": [
                    "**Margen de seguridad**: Compra con descuento al valor intrínseco",
                    "**Ciclos de mercado**: Entiende en qué fase del ciclo estás",
                    "**Valoración relativa**: Compara siempre con alternativas",
                    "**Catalizadores**: Identifica eventos que puedan mover el precio",
                    "**Patience**: Mejor oportunidad perdida que mala inversión"
                ],
                "📚 Educación Continua": [
                    "**Aprendizaje constante**: Los mercados evolucionan, tú también debes hacerlo",
                    "**Historia financiera**: Estudia burbujas y cracks pasados",
                    "**Mentes brillantes**: Lee a Buffett, Munger, Lynch, Graham",
                    "**Pensamiento crítico**: Cuestiona todo, especialmente tus propias ideas",
                    "**Red de conocimiento**: Rodéate de personas más inteligentes que tú"
                ]
            }
            
            for categoria, consejos in categorias_consejos.items():
                st.markdown(f"### {categoria}")
                for consejo in consejos:
                    st.write(f"• {consejo}")
                st.markdown("---")
            
            # Frases célebres de inversión
            st.markdown("### 💬 Sabiduría de los Grandes Inversores")
            frases = [
                "**Warren Buffett**: 'Sé temeroso cuando otros son codiciosos, y codicioso cuando otros son temerosos.'",
                "**Charlie Munger**: 'La inversión no es fácil. Cualquiera que crea que es fácil es un tonto.'",
                "**Peter Lynch**: 'Detrás de cada acción hay una empresa. Descubre qué está haciendo esa empresa.'",
                "**Benjamin Graham**: 'En el corto plazo, el mercado es una máquina de votación. En el largo plazo, es una máquina de ponderación.'",
                "**Philip Fisher**: 'El stock market está lleno de individuos que saben el precio de todo, pero el valor de nada.'",
                "**John Bogle**: 'No busques la aguja en el pajar. Simplemente compra el pajar.'"
            ]
            
            for frase in frases:
                st.success(frase)

        # Sección de libros recomendados
        st.markdown("---")
        st.subheader("📚 Libros Recomendados para Aprender Más")
        
        libros = {
            "Para Principiantes": [
                "**El Inversor Inteligente** - Benjamin Graham (la biblia de la inversión value)",
                "**Un paseo aleatorio por Wall Street** - Burton Malkiel (sobre eficiencia de mercados)",
                "**Los ensayos de Warren Buffett** - Lawrence Cunningham (sabiduría de Buffett)",
                "**The Little Book of Common Sense Investing** - John Bogle (inversión indexada)"
            ],
            "Para Nivel Intermedio": [
                "**Security Analysis** - Benjamin Graham & David Dodd (análisis profundo)",
                "**Common Stocks and Uncommon Profits** - Philip Fisher (inversión en crecimiento)", 
                "**The Little Book of Valuation** - Aswath Damodaran (valoración)",
                "**The Most Important Thing** - Howard Marks (gestión de riesgo)"
            ],
            "Para Avanzados": [
                "**Value Investing: From Graham to Buffett and Beyond** - Bruce Greenwald",
                "**Expected Returns** - Antti Ilmanen (teoría moderna de portafolios)",
                "**The Black Swan** - Nassim Taleb (eventos extremos)",
                "**Principles** - Ray Dalio (modelos mentales para inversión)"
            ],
            "Análisis Fundamental Específico": [
                "**Financial Statement Analysis** - Martin Fridson (análisis de estados financieros)",
                "**The Essays of Warren Buffett** - Lawrence Cunningham (filosofía de inversión)",
                "**Investment Valuation** - Aswath Damodaran (valoración avanzada)",
                "**The Intelligent Asset Allocator** - William Bernstein (asignación de activos)"
            ]
        }
        
        for nivel, lista_libros in libros.items():
            st.write(f"**{nivel}:**")
            for libro in lista_libros:
                st.write(f"• {libro}")

        # Consejos finales mejorados
        st.markdown("---")
        st.subheader("💡 Consejos para Dominar el Análisis Fundamental")
        
        consejos = [
            "**Comienza con lo básico**: Domina primero las 10-15 métricas más importantes de cada sector",
            "**Contexto es clave**: Una métrica por sí sola no te dice mucho. Siempre compara con el sector, historial y competidores",
            "**Tendencias > Niveles absolutos**: Una métrica mejorando consistentemente es más importante que su nivel actual", 
            "**Calidad de ganancias**: Analiza si las ganancias vienen del negocio principal o de eventos extraordinarios",
            "**Flujo de caja vs Ganancias**: Las ganancias son una opinión, el flujo de caja es un hecho",
            "**Apalancamiento prudente**: Un poco de deuda puede ser bueno, demasiada puede ser peligrosa",
            "**Ventajas competitivas**: Busca empresas con márgenes estables/crecientes - indican 'moats' económicos",
            "**Management calidad**: Métricas consistentes suelen indicar buena gestión",
            "**Paciencia**: El análisis fundamental es para inversores, no para traders. Think long-term",
            "**Humildad**: Ninguna métrica es perfecta. Usa múltiples herramientas y mantén escepticismo saludable"
        ]
        
        for i, consejo in enumerate(consejos, 1):
            st.write(f"**{i}.** {consejo}")

        # Resumen final de las 82 métricas
        st.markdown("---")
        st.subheader("📋 Resumen Completo: Las 82 Métricas Fundamentales")
        
        st.write("""
        **💰 VALORACIÓN Y MERCADO (18 métricas)**
        - Market Cap, P/E, Forward P/E, PEG, P/S, P/B, P/FCF
        - EV/EBITDA, EV/Sales, EV/FCF, EPS (ttm), EPS next Y, EPS next Q
        - EPS this Y, EPS next 5Y, EPS past 5Y, Book Value/Share
        
        **📈 RENTABILIDAD Y MÁRGENES (16 métricas)**
        - ROA, ROE, ROI, Gross Margin, Oper. Margin, Profit Margin
        - EBITDA, EBIT, Net Income, Income Tax, Dividend, Dividend %
        - Payout Ratio, EPS Q/Q, Sales Q/Q, Earnings Date
        
        **🏦 DEUDA Y LIQUIDEZ (12 métricas)**
        - Total Debt, Debt/Eq, LT Debt/Eq, Total Debt/EBITDA
        - Current Ratio, Quick Ratio, Cash/Share, Cash Flow/Share
        - Total Cash, Total Cash/Share, Working Capital, Interest Coverage
        
        **📊 EFICIENCIA OPERATIVA (10 métricas)**
        - Asset Turnover, Inventory Turnover, Receivables Turnover
        - Days Inventory, Days Sales Outstanding, Payables Period
        - Cash Conversion Cycle, Fixed Asset Turnover, R&D/Sales, SG&A/Sales
        
        **📈 CRECIMIENTO (8 métricas)**
        - Sales Growth 5Y, EPS Growth 5Y, Sales Growth Q/Q, EPS Growth Q/Q
        - Sales Growth Y/Y, EPS Growth Y/Y, Revenue Growth (ttm), EPS Growth (ttm)
        
        **📊 INDICADORES TÉCNICOS (10 métricas)**
        - Beta, RSI (14), Volatility W, Volatility M, ATR
        - SMA 20, SMA 50, SMA 200, Volume, Avg Volume, Rel Volume
        
        **🏢 DATOS CORPORATIVOS (8 métricas)**
        - Shares Out, Float, Insider Own, Insider Trans
        - Inst Own, Inst Trans, Short Float, Short Ratio
        """)
        
        st.success("**🎯 TOTAL: 82 MÉTRICAS FUNDAMENTALES COMPLETAMENTE EXPLICADAS**")