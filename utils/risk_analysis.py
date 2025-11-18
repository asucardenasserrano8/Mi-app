# utils/risk_analysis.py
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import streamlit as st

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
        
        st.info(f"📊 Calculando métricas de riesgo para {ticker_symbol}...")
        
        # Datos de la acción
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d', progress=False)
        if stock_data.empty or len(stock_data) < 100:
            st.warning(f"Datos insuficientes para {ticker_symbol}")
            return None
            
        # Datos del mercado (S&P500 como benchmark)
        market_data = yf.download('^GSPC', start=start_date, end=end_date, interval='1d', progress=False)
        if market_data.empty:
            st.warning("No se pudieron obtener datos del mercado")
            return None
        
        # Obtener precios de cierre
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_close = stock_data[('Close', ticker_symbol)]
        else:
            stock_close = stock_data['Close']
            
        if isinstance(market_data.columns, pd.MultiIndex):
            market_close = market_data[('Close', '^GSPC')]
        else:
            market_close = market_data['Close']
        
        # Limpiar datos NaN
        stock_close = stock_close.dropna()
        market_close = market_close.dropna()
        
        if len(stock_close) < 100 or len(market_close) < 100:
            st.warning("Datos insuficientes después de limpieza")
            return None
        
        # Calcular rendimientos
        stock_returns = stock_close.pct_change().dropna()
        market_returns = market_close.pct_change().dropna()
        
        # Alinear fechas
        common_dates = stock_returns.index.intersection(market_returns.index)
        if len(common_dates) < 50:
            st.warning("No hay suficientes fechas comunes con el mercado")
            return None
            
        stock_returns = stock_returns.loc[common_dates]
        market_returns = market_returns.loc[common_dates]
        
        if len(stock_returns) < 50:
            st.warning("Rendimientos insuficientes para análisis")
            return None
        
        # Convertir a arrays numpy
        stock_returns_array = stock_returns.values
        market_returns_array = market_returns.values
        
        # 1. CALCULAR BETA Y ALPHA
        try:
            covariance = np.cov(stock_returns_array, market_returns_array)[0, 1]
            market_variance = np.var(market_returns_array)
            beta = covariance / market_variance if market_variance != 0 else 1.0
            
            # Calcular rendimientos totales para Alpha
            stock_total_return = (stock_close.iloc[-1] / stock_close.iloc[0] - 1)
            market_total_return = (market_close.iloc[-1] / market_close.iloc[0] - 1)
            alpha = stock_total_return - (beta * market_total_return)
        except:
            beta = 1.0
            alpha = 0
        
        # 2. CALCULAR SHARPE RATIO
        try:
            risk_free_rate = 0.02 / 252  # Tasa libre de riesgo diaria (2% anual)
            excess_returns = stock_returns_array - risk_free_rate
            sharpe_ratio = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252) if np.std(excess_returns) != 0 else 0
        except:
            sharpe_ratio = 0
        
        # 3. CALCULAR SORTINO RATIO (CORREGIDO)
        try:
            # Solo considerar rendimientos negativos para el denominador
            negative_returns = stock_returns_array[stock_returns_array < 0]
            downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0.001
            
            # Usar el mismo excess_returns que para Sharpe
            sortino_ratio = (np.mean(excess_returns) / downside_std) * np.sqrt(252) if downside_std != 0 else 0
        except:
            sortino_ratio = 0
        
        # 4. CALCULAR VALUE AT RISK (VaR) - CORREGIDO
        try:
            # VaR histórico (no paramétrico)
            var_95 = np.percentile(stock_returns_array, 5)  # 5% peores rendimientos
            var_95_annual = var_95 * np.sqrt(252)  # Anualizar
            
            # VaR 99%
            var_99 = np.percentile(stock_returns_array, 1)
            var_99_annual = var_99 * np.sqrt(252)
        except:
            var_95 = 0
            var_95_annual = 0
            var_99 = 0
            var_99_annual = 0
        
        # 5. CALCULAR EXPECTED SHORTFALL (CVaR) - CORREGIDO
        try:
            # Promedio de los peores 5% rendimientos
            cvar_95 = stock_returns_array[stock_returns_array <= var_95].mean()
            cvar_95_annual = cvar_95 * np.sqrt(252) if not np.isnan(cvar_95) else 0
        except:
            cvar_95_annual = 0
        
        # 6. CALCULAR DRAWDOWN MÁXIMO - CORREGIDO
        try:
            # Calcular retornos acumulados
            cumulative_returns = (1 + stock_returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Calcular duración del drawdown máximo
            max_dd_idx = drawdown.idxmin()
            # Encontrar el inicio del drawdown (último máximo antes del mínimo)
            drawdown_period = drawdown[:max_dd_idx]
            max_dd_start = drawdown_period[drawdown_period == 0].last_valid_index()
            
            if max_dd_start is not None:
                max_dd_duration = (max_dd_idx - max_dd_start).days
            else:
                max_dd_duration = 0
        except:
            max_drawdown = 0
            max_dd_duration = 0
        
        # 7. CALCULAR VOLATILIDAD ANUALIZADA
        try:
            volatility_annual = np.std(stock_returns_array) * np.sqrt(252)
        except:
            volatility_annual = 0
        
        # 8. CALCULAR CORRELACIÓN CON S&P500
        try:
            correlation_sp500 = np.corrcoef(stock_returns_array, market_returns_array)[0, 1]
            if np.isnan(correlation_sp500):
                correlation_sp500 = 0
        except:
            correlation_sp500 = 0
        
        # 9. CALCULAR MÁXIMO GANANCIA/PÉRDIDA CONSECUTIVA - CORREGIDO
        try:
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
        except:
            max_positive_streak = 0
            max_negative_streak = 0
        
        # 10. CALCULAR SKEWNESS Y KURTOSIS - CORREGIDO
        try:
            if len(stock_returns_array) >= 4:
                skewness = float(pd.Series(stock_returns_array).skew())
                kurtosis = float(pd.Series(stock_returns_array).kurtosis())
            else:
                skewness = 0
                kurtosis = 0
        except:
            skewness = 0
            kurtosis = 0
        
        # 11. CALCULAR PROBABILIDAD DE PÉRDIDA - CORREGIDO
        try:
            prob_loss = (np.sum(stock_returns_array < 0) / len(stock_returns_array)) * 100
        except:
            prob_loss = 50
        
        # 12. CALCULAR TREYNOR RATIO
        try:
            treynor_ratio = (stock_total_return - 0.02) / beta if beta != 0 else 0
        except:
            treynor_ratio = 0
        
        # 13. CALCULAR INFORMATION RATIO
        try:
            active_returns = stock_returns_array - market_returns_array
            tracking_error = np.std(active_returns) * np.sqrt(252) if len(active_returns) > 0 else 0
            information_ratio = (stock_total_return - market_total_return) / tracking_error if tracking_error != 0 else 0
        except:
            information_ratio = 0
        
        st.success(f"✅ Métricas calculadas: {len(stock_returns)} días analizados")
        
        return {
            # Métricas básicas
            'Beta': beta,
            'Alpha': alpha,
            'Sharpe Ratio': sharpe_ratio,
            'Sortino Ratio': sortino_ratio,
            'Treynor Ratio': treynor_ratio,
            'Information Ratio': information_ratio,
            
            # Métricas de riesgo
            'VaR 95% Diario': var_95,
            'VaR 95% Anual': var_95_annual,
            'VaR 99% Diario': var_99,
            'VaR 99% Anual': var_99_annual,
            'Expected Shortfall 95%': cvar_95_annual,
            'Drawdown Máximo': max_drawdown,
            'Duración Drawdown (días)': max_dd_duration,
            'Volatilidad Anual': volatility_annual,
            
            # Correlaciones
            'Correlación S&P500': correlation_sp500,
            
            # Estadísticas avanzadas
            'Máxima Ganancia Consecutiva': max_positive_streak,
            'Máxima Pérdida Consecutiva': max_negative_streak,
            'Skewness': skewness,
            'Kurtosis': kurtosis,
            'Probabilidad de Pérdida (%)': prob_loss,
            
            # Rendimientos
            'Rendimiento Total': stock_total_return,
            'Rendimiento Mercado': market_total_return,
            'Días Analizados': len(stock_returns),
            'Período': f"{periodo_años} años"
        }
        
    except Exception as e:
        st.error(f"❌ Error calculando métricas de riesgo: {str(e)}")
        st.error(f"Tipo de error: {type(e).__name__}")
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
    Crea gráfica de distribución de retornos diarios COMPLETA con estadísticas avanzadas
    """
    try:
        # Descargar datos históricos
        end_date = datetime.today()
        start_date = end_date - timedelta(days=periodo_años * 365)
        
        st.info(f"📊 Calculando distribución de retornos para {ticker_symbol} ({periodo_años} años)...")
        
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d', progress=False)
        if stock_data.empty:
            st.warning(f"No se pudieron obtener datos para {ticker_symbol}")
            return None
        
        # Manejar MultiIndex columns
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_close = stock_data[('Close', ticker_symbol)]
        else:
            stock_close = stock_data['Close']
        
        # Calcular retornos diarios en porcentaje
        returns = stock_close.pct_change().dropna() * 100
        
        if len(returns) < 30:
            st.warning(f"Datos insuficientes para análisis: solo {len(returns)} días de trading")
            return None
        
        # Calcular estadísticas avanzadas
        mean_return = returns.mean()
        std_return = returns.std()
        median_return = returns.median()
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # Calcular percentiles
        percentiles = {
            '1%': returns.quantile(0.01),
            '5%': returns.quantile(0.05),
            '25%': returns.quantile(0.25),
            '75%': returns.quantile(0.75),
            '95%': returns.quantile(0.95),
            '99%': returns.quantile(0.99)
        }
        
        # Crear figura principal
        fig = go.Figure()
        
        # HISTOGRAMA PRINCIPAL
        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name='Frecuencia de Retornos',
            opacity=0.75,
            marker_color='#1f77b4',
            marker_line_color='#0d47a1',
            marker_line_width=1,
            hovertemplate=(
                '<b>Rango de Retorno:</b> %{x:.2f}%<br>' +
                '<b>Frecuencia:</b> %{y} días<br>' +
                '<b>Probabilidad:</b> %{y}' + f'/{len(returns)} días<br>' +
                '<extra></extra>'
            )
        ))
        
        # CALCULAR Y AGREGAR DISTRIBUCIÓN NORMAL TEÓRICA
        x_norm = np.linspace(returns.min() * 1.1, returns.max() * 1.1, 200)
        pdf_norm = (1/(std_return * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_return)/std_return) ** 2)
        pdf_norm = pdf_norm * len(returns) * (returns.max() - returns.min()) / 50  # Escalar
        
        fig.add_trace(go.Scatter(
            x=x_norm,
            y=pdf_norm,
            mode='lines',
            name='Distribución Normal Teórica',
            line=dict(color='red', width=3, dash='dash'),
            hovertemplate='<b>Distribución Normal</b><br>Retorno: %{x:.2f}%<br>Densidad: %{y:.2f}<extra></extra>'
        ))
        
        # LÍNEAS DE REFERENCIA PRINCIPALES
        # Línea en CERO
        fig.add_vline(x=0, line_dash="solid", line_color="green", line_width=2,
                     annotation_text="Cero", annotation_position="top right",
                     annotation_font_color="green")
        
        # Línea de MEDIA
        fig.add_vline(x=mean_return, line_dash="dot", line_color="orange", line_width=2,
                     annotation_text=f"Media: {mean_return:.2f}%", 
                     annotation_position="top left",
                     annotation_font_color="orange")
        
        # Líneas de DESVIACIÓN ESTÁNDAR
        colors_sigma = ['#ff6b6b', '#ffa726', '#66bb6a']
        for i, std_mult in enumerate([1, 2, 3], 1):
            color = colors_sigma[i-1]
            # +Sigma
            fig.add_vline(x=mean_return + std_mult * std_return, 
                         line_dash="dot", line_color=color, line_width=1,
                         annotation_text=f"+{std_mult}σ" if std_mult <= 2 else "",
                         annotation_position="top")
            # -Sigma
            fig.add_vline(x=mean_return - std_mult * std_return, 
                         line_dash="dot", line_color=color, line_width=1,
                         annotation_text=f"-{std_mult}σ" if std_mult <= 2 else "",
                         annotation_position="top")
        
        # PERCENTILES IMPORTANTES
        # Percentil 5% (VaR aproximado)
        fig.add_vline(x=percentiles['5%'], line_dash="dash", line_color="purple", line_width=2,
                     annotation_text=f"5%: {percentiles['5%']:.2f}%",
                     annotation_position="bottom right")
        
        # Percentil 95%
        fig.add_vline(x=percentiles['95%'], line_dash="dash", line_color="purple", line_width=2,
                     annotation_text=f"95%: {percentiles['95%']:.2f}%",
                     annotation_position="bottom right")
        
        # CONFIGURACIÓN DEL LAYOUT
        fig.update_layout(
            title=dict(
                text=f'Distribución de Retornos Diarios - {ticker_symbol}',
                x=0.5,
                xanchor='center',
                font=dict(size=16, color='white')
            ),
            xaxis_title=dict(text='Retorno Diario (%)', font=dict(size=14)),
            yaxis_title=dict(text='Frecuencia (Días)', font=dict(size=14)),
            height=600,
            showlegend=True,
            bargap=0.02,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='white'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        # PANEL DE ESTADÍSTICAS DETALLADO
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text=(
                f"<b>📊 ESTADÍSTICAS AVANZADAS</b><br>"
                f"<b>Retorno Promedio:</b> {mean_return:.3f}%<br>"
                f"<b>Volatilidad (σ):</b> {std_return:.3f}%<br>"
                f"<b>Mediana:</b> {median_return:.3f}%<br>"
                f"<b>Asimetría (Skew):</b> {skewness:.3f}<br>"
                f"<b>Curtosis:</b> {kurtosis:.3f}<br>"
                f"<b>Días Analizados:</b> {len(returns):,}<br>"
                f"<b>Período:</b> {periodo_años} años"
            ),
            showarrow=False,
            bgcolor="rgba(30, 30, 30, 0.9)",
            bordercolor="white",
            borderwidth=1,
            borderpad=10,
            font=dict(size=11, color='white'),
            align="left"
        )
        
        # INTERPRETACIÓN DE SKEWNESS Y KURTOSIS
        skew_interpretation = (
            "Sesgo positivo (colas derechas)" if skewness > 0.5 else
            "Sesgo negativo (colas izquierdas)" if skewness < -0.5 else
            "Distribución simétrica"
        )
        
        kurt_interpretation = (
            "Colas pesadas (Leptocúrtica)" if kurtosis > 3 else
            "Colas livianas (Platicúrtica)" if kurtosis < 3 else
            "Colas normales (Mesocúrtica)"
        )
        
        fig.add_annotation(
            x=0.98, y=0.98,
            xref="paper", yref="paper",
            text=(
                f"<b>🔍 INTERPRETACIÓN</b><br>"
                f"<b>Asimetría:</b> {skew_interpretation}<br>"
                f"<b>Curtosis:</b> {kurt_interpretation}<br>"
                f"<b>Normalidad:</b> {'No normal' if abs(skewness) > 1 or abs(kurtosis) > 3 else 'Cercana a normal'}"
            ),
            showarrow=False,
            bgcolor="rgba(30, 30, 30, 0.9)",
            bordercolor="white",
            borderwidth=1,
            borderpad=10,
            font=dict(size=11, color='white'),
            align="right"
        )
        
        # MEJORAS EN LOS EJES
        fig.update_xaxes(
            gridcolor='rgba(128, 128, 128, 0.3)',
            zerolinecolor='rgba(128, 128, 128, 0.5)',
            zerolinewidth=2
        )
        
        fig.update_yaxes(
            gridcolor='rgba(128, 128, 128, 0.3)'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Error creando gráfica de distribución: {str(e)}")
        # Debug information
        st.error(f"Tipo de error: {type(e).__name__}")
        return None

def analizar_tendencias(data):
    """
    Analiza tendencias del precio usando múltiples indicadores
    """
    if data.empty or 'Close' not in data.columns:
        return {"tendencia": "No disponible", "confianza": 0, "detalles": {}}
    
    try:
        # Calcular medias móviles
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # Obtener últimos valores
        precio_actual = data['Close'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        sma_200 = data['SMA_200'].iloc[-1]
        
        # Calcular RSI para momentum
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_actual = rsi.iloc[-1]
        
        # Análisis de tendencia
        tendencia_alcista = 0
        tendencia_bajista = 0
        
        # 1. Análisis de medias móviles (40%)
        if precio_actual > sma_20 > sma_50 > sma_200:
            tendencia_alcista += 40
        elif precio_actual < sma_20 < sma_50 < sma_200:
            tendencia_bajista += 40
        
        # 2. Posición respecto a medias (30%)
        if precio_actual > sma_20:
            tendencia_alcista += 15
        else:
            tendencia_bajista += 15
            
        if precio_actual > sma_50:
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
            
        if precio_actual > sma_200:
            tendencia_alcista += 5
        else:
            tendencia_bajista += 5
        
        # 3. Momentum RSI (30%)
        if rsi_actual > 50:
            tendencia_alcista += 30
        else:
            tendencia_bajista += 30
        
        # Determinar tendencia principal
        if tendencia_alcista > tendencia_bajista:
            tendencia = "ALCISTA"
            confianza = min(100, tendencia_alcista)
        elif tendencia_bajista > tendencia_alcista:
            tendencia = "BAJISTA"
            confianza = min(100, tendencia_bajista)
        else:
            tendencia = "LATERAL"
            confianza = 50
        
        detalles = {
            "precio_actual": precio_actual,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "rsi": rsi_actual,
            "puntos_alcista": tendencia_alcista,
            "puntos_bajista": tendencia_bajista
        }
        
        return {
            "tendencia": tendencia,
            "confianza": confianza,
            "detalles": detalles
        }
        
    except Exception as e:
        return {"tendencia": "Error en análisis", "confianza": 0, "detalles": {}}

def calcular_scoring_fundamental(info):
    """
    Calcula scoring fundamental basado en múltiples métricas
    """
    score = 0
    max_score = 100
    metricas = {}
    
    # P/E Ratio (15 puntos)
    pe = info.get('trailingPE', 0)
    if pe and pe > 0:
        if pe < 15:
            score += 15
            metricas['P/E'] = '🟢 Excelente'
        elif pe < 25:
            score += 10
            metricas['P/E'] = '🟡 Bueno'
        else:
            score += 5
            metricas['P/E'] = '🔴 Alto'
    
    # ROE (15 puntos)
    roe = info.get('returnOnEquity', 0)
    if roe and roe > 0:
        if roe > 0.15:
            score += 15
            metricas['ROE'] = '🟢 Excelente'
        elif roe > 0.08:
            score += 10
            metricas['ROE'] = '🟡 Bueno'
        else:
            score += 5
            metricas['ROE'] = '🔴 Bajo'
    
    # Deuda/Equity (15 puntos)
    deuda_eq = info.get('debtToEquity', 0)
    if deuda_eq and deuda_eq > 0:
        if deuda_eq < 0.5:
            score += 15
            metricas['Deuda/Equity'] = '🟢 Excelente'
        elif deuda_eq < 1.0:
            score += 10
            metricas['Deuda/Equity'] = '🟡 Bueno'
        else:
            score += 5
            metricas['Deuda/Equity'] = '🔴 Alto'
    
    # Margen Beneficio (15 puntos)
    margen = info.get('profitMargins', 0)
    if margen and margen > 0:
        if margen > 0.2:
            score += 15
            metricas['Margen Beneficio'] = '🟢 Excelente'
        elif margen > 0.1:
            score += 10
            metricas['Margen Beneficio'] = '🟡 Bueno'
        else:
            score += 5
            metricas['Margen Beneficio'] = '🔴 Bajo'
    
    # Crecimiento Ingresos (20 puntos)
    crecimiento = info.get('revenueGrowth', 0)
    if crecimiento and crecimiento > 0:
        if crecimiento > 0.15:
            score += 20
            metricas['Crecimiento Ingresos'] = '🟢 Excelente'
        elif crecimiento > 0.08:
            score += 15
            metricas['Crecimiento Ingresos'] = '🟡 Bueno'
        else:
            score += 8
            metricas['Crecimiento Ingresos'] = '🔴 Bajo'
    
    # Rating Analistas (20 puntos)
    rating_mean = info.get('recommendationMean', 3)
    if rating_mean and rating_mean > 0:
        if rating_mean < 2:
            score += 20
            metricas['Rating Analistas'] = '🟢 Fuerte Compra'
        elif rating_mean < 3:
            score += 15
            metricas['Rating Analistas'] = '🟡 Compra'
        else:
            score += 8
            metricas['Rating Analistas'] = '🔴 Neutral/Venta'
    
    return min(score, max_score), metricas