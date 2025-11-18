import streamlit as st
import google.generativeai as genai
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

def mostrar(datos_accion):
    """
    Sección de Análisis IA MEJORADA - Análisis más detallado y profesional
    """
    # Extraer información de datos_accion
    stonk = datos_accion['ticker']
    info = datos_accion['info']
    datos_historicos = datos_accion['datos']
    nombre = datos_accion['nombre']
    
    st.header(f"🤖 Análisis IA Avanzado - {nombre}")
    
    # Obtener datos MÁS COMPLETOS para el análisis
    try:
        # DATOS FUNDAMENTALES
        current_price = info.get('currentPrice', 0)
        previous_close = info.get('previousClose', 0)
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 0)
        forward_pe = info.get('forwardPE', 0)
        peg_ratio = info.get('pegRatio', 0)
        revenue_growth = info.get('revenueGrowth', 0)
        earnings_growth = info.get('earningsGrowth', 0)
        profit_margins = info.get('profitMargins', 0)
        operating_margins = info.get('operatingMargins', 0)
        return_on_equity = info.get('returnOnEquity', 0)
        return_on_assets = info.get('returnOnAssets', 0)
        debt_to_equity = info.get('debtToEquity', 0)
        current_ratio = info.get('currentRatio', 0)
        free_cash_flow = info.get('freeCashflow', 0)
        operating_cash_flow = info.get('operatingCashflow', 0)
        
        # DATOS TÉCNICOS
        beta = info.get('beta', 1.0)
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
        dividend_yield = info.get('dividendYield', 0)
        payout_ratio = info.get('payoutRatio', 0)
        
        # RATING DE ANALISTAS
        analyst_recommendation = info.get('recommendationKey', 'hold')
        target_mean_price = info.get('targetMeanPrice', 0)
        number_of_analysts = info.get('numberOfAnalystOpinions', 0)
        
        # DATOS HISTÓRICOS PARA ANÁLISIS TÉCNICO
        if not datos_historicos.empty:
            # CORRECCIÓN: Extraer valores numéricos correctamente
            if 'Close' in datos_historicos.columns:
                precio_actual = float(datos_historicos['Close'].iloc[-1])
                precio_max_52s = float(datos_historicos['Close'].max())
                precio_min_52s = float(datos_historicos['Close'].min())
                
                # Calcular métricas técnicas básicas
                if len(datos_historicos) > 20:
                    sma_20 = float(datos_historicos['Close'].rolling(window=20).mean().iloc[-1])
                    sma_50 = float(datos_historicos['Close'].rolling(window=50).mean().iloc[-1]) if len(datos_historicos) > 50 else float(precio_actual)
                else:
                    sma_20 = float(precio_actual)
                    sma_50 = float(precio_actual)
            else:
                precio_actual = float(current_price)
                precio_max_52s = float(fifty_two_week_high)
                precio_min_52s = float(fifty_two_week_low)
                sma_20 = float(current_price)
                sma_50 = float(current_price)
        else:
            precio_actual = float(current_price)
            precio_max_52s = float(fifty_two_week_high)
            precio_min_52s = float(fifty_two_week_low)
            sma_20 = float(current_price)
            sma_50 = float(current_price)
        
        # CORRECCIÓN: Asegurar que todos los valores sean numéricos
        current_price = float(current_price) if current_price else 0.0
        previous_close = float(previous_close) if previous_close else 0.0
        market_cap = float(market_cap) if market_cap else 0.0
        pe_ratio = float(pe_ratio) if pe_ratio else 0.0
        forward_pe = float(forward_pe) if forward_pe else 0.0
        peg_ratio = float(peg_ratio) if peg_ratio else 0.0
        revenue_growth = float(revenue_growth) if revenue_growth else 0.0
        earnings_growth = float(earnings_growth) if earnings_growth else 0.0
        profit_margins = float(profit_margins) if profit_margins else 0.0
        operating_margins = float(operating_margins) if operating_margins else 0.0
        return_on_equity = float(return_on_equity) if return_on_equity else 0.0
        return_on_assets = float(return_on_assets) if return_on_assets else 0.0
        debt_to_equity = float(debt_to_equity) if debt_to_equity else 0.0
        current_ratio = float(current_ratio) if current_ratio else 0.0
        free_cash_flow = float(free_cash_flow) if free_cash_flow else 0.0
        operating_cash_flow = float(operating_cash_flow) if operating_cash_flow else 0.0
        beta = float(beta) if beta else 1.0
        fifty_two_week_high = float(fifty_two_week_high) if fifty_two_week_high else 0.0
        fifty_two_week_low = float(fifty_two_week_low) if fifty_two_week_low else 0.0
        dividend_yield = float(dividend_yield) if dividend_yield else 0.0
        payout_ratio = float(payout_ratio) if payout_ratio else 0.0
        target_mean_price = float(target_mean_price) if target_mean_price else 0.0
        number_of_analysts = int(number_of_analysts) if number_of_analysts else 0
        
        # PANEL DE MÉTRICAS RÁPIDAS
        st.subheader("📊 Panel de Métricas Clave")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cambio_porcentaje = ((precio_actual - previous_close) / previous_close * 100) if previous_close else 0
            st.metric(
                "Precio Actual", 
                f"${precio_actual:.2f}", 
                f"{cambio_porcentaje:+.2f}%"
            )
        
        with col2:
            st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
        
        with col3:
            st.metric("P/E Ratio", f"{pe_ratio:.1f}" if pe_ratio else "N/A")
        
        with col4:
            st.metric("Beta", f"{beta:.2f}")
        
        # ANÁLISIS IA MEJORADO
        st.subheader("🧠 Análisis Fundamental Avanzado por IA")
        
        # Prompt MEJORADO y MÁS DETALLADO
        prompt_analisis_detallado = f"""
        Eres un analista financiero senior con 20 años de experiencia en Wall Street. 
        Analiza DETALLADAMENTE la acción {stonk} ({nombre}) y proporciona un informe completo.

        INFORMACIÓN FINANCIERA COMPLETA:

        💰 DATOS DE PRECIO:
        • Precio Actual: ${precio_actual:.2f}
        • Precio Anterior: ${previous_close:.2f}
        • Cambio: {cambio_porcentaje:+.2f}%
        • Máximo 52 semanas: ${precio_max_52s:.2f}
        • Mínimo 52 semanas: ${precio_min_52s:.2f}
        • Media Móvil 20 días: ${sma_20:.2f}
        • Media Móvil 50 días: ${sma_50:.2f}

        📈 VALUACIÓN:
        • Market Cap: ${market_cap/1e9:.2f}B
        • P/E Ratio: {pe_ratio:.1f}
        • Forward P/E: {forward_pe:.1f}
        • PEG Ratio: {peg_ratio:.2f}
        • Precio/Objetivo Analistas: ${target_mean_price:.2f}

        📊 CRECIMIENTO Y RENTABILIDAD:
        • Crecimiento Ingresos: {revenue_growth*100:.1f}% 
        • Crecimiento Beneficios: {earnings_growth*100 if earnings_growth else 0:.1f}%
        • Margen Beneficio: {profit_margins*100:.1f}%
        • Margen Operativo: {operating_margins*100:.1f}%
        • ROE: {return_on_equity*100:.1f}%
        • ROA: {return_on_assets*100:.1f}%

        🏛️ SOLVENCIA:
        • Deuda/Equity: {debt_to_equity:.2f}
        • Current Ratio: {current_ratio:.2f}
        • Free Cash Flow: ${free_cash_flow/1e6:.0f}M
        • Operating Cash Flow: ${operating_cash_flow/1e6:.0f}M

        📋 DATOS TÉCNICOS:
        • Beta: {beta:.2f}
        • Dividend Yield: {dividend_yield*100:.2f}%
        • Payout Ratio: {payout_ratio*100:.1f}%
        • Recomendación Analistas: {analyst_recommendation.upper()}
        • Número de Analistas: {number_of_analysts}

        Proporciona un análisis PROFESIONAL que incluya:

        1. 🎯 VALORACIÓN INTEGRAL (Sobrevalorada/Subvalorada/Justa)
        2. 📊 ANÁLISIS FUNDAMENTAL DETALLADO
        3. 💪 FORTALEZAS PRINCIPALES (mínimo 3)
        4. ⚠️ RIESGOS IDENTIFICADOS (mínimo 3)
        5. 📈 PERSPECTIVA TÉCNICA
        6. 🏆 RECOMENDACIÓN ESPECÍFICA (COMPRAR/MANTENER/REDUCIR/VENDER)
        7. 🎯 PRECIO OBJETIVO (basado en fundamentales)
        8. ⏰ HORIZONTE TEMPORAL RECOMENDADO
        9. 🔄 CATALIZADORES CLAVE a monitorear
        10. 💡 ESTRATEGIA DE INVERSIÓN específica

        Incluye métricas específicas en tu análisis.
        Sé técnico pero claro. Usa terminología profesional.
        Máximo 600 palabras. Basado estrictamente en los datos proporcionados.
        Proporciona porcentajes y números concretos.
        """

        with st.spinner("🧠 Realizando análisis fundamental avanzado..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response_ia = model.generate_content(prompt_analisis_detallado)
                
                st.success("✅ Análisis fundamental completado")
                
                # Mostrar el análisis con mejor formato
                st.markdown("### 📋 Informe de Análisis Fundamental")
                st.markdown("---")
                st.markdown(response_ia.text)
                
            except Exception as e:
                st.error(f"❌ Error en análisis IA: {str(e)}")
                # Análisis de respaldo MÁS DETALLADO
                mostrar_analisis_respaldo(info, precio_actual, market_cap, pe_ratio, revenue_growth)
        
        # ANÁLISIS DE SENTIMIENTO MEJORADO
        st.subheader("😊 Análisis de Sentimiento y Scoring")
        
        # Scoring fundamental mejorado
        scoring, metricas_scoring, analisis_scoring = calcular_scoring_fundamental_mejorado(info)
        
        col_sent1, col_sent2, col_sent3, col_sent4 = st.columns(4)
        
        with col_sent1:
            # Sentimiento del mercado
            sentimiento = analizar_sentimiento_avanzado(info, datos_historicos)
            color_sentimiento = "🟢" if sentimiento == "MUY POSITIVO" else "🟡" if sentimiento == "POSITIVO" else "🟠" if sentimiento == "NEUTRAL" else "🔴"
            st.metric("Sentimiento Mercado", f"{color_sentimiento} {sentimiento}")
        
        with col_sent2:
            # Scoring fundamental
            color_score = "🟢" if scoring >= 75 else "🟡" if scoring >= 60 else "🟠" if scoring >= 45 else "🔴"
            st.metric("Scoring Fundamental", f"{color_score} {scoring}/100")
        
        with col_sent3:
            # Recomendación IA
            recomendacion = generar_recomendacion_automatica(scoring, sentimiento, pe_ratio, revenue_growth)
            st.metric("Recomendación", recomendacion)
        
        with col_sent4:
            # Horizonte temporal
            horizonte = determinar_horizonte_inversion(scoring, beta, sentimiento)
            st.metric("Horizonte Recomendado", horizonte)
        
        # ANÁLISIS DETALLADO DEL SCORING
        st.subheader("📈 Desglose del Scoring Fundamental")
        
        # Mostrar métricas de scoring con barras de progreso
        for metrica, valor in metricas_scoring.items():
            col_met1, col_met2 = st.columns([1, 3])
            with col_met1:
                st.write(f"**{metrica}**")
            with col_met2:
                # Extraer valor numérico y texto
                if "Excelente" in valor:
                    progreso = 100
                    color = "green"
                elif "Bueno" in valor:
                    progreso = 75
                    color = "lightgreen" 
                elif "Moderado" in valor:
                    progreso = 50
                    color = "orange"
                else:
                    progreso = 25
                    color = "red"
                
                st.progress(progreso/100, text=valor)
        
        # ANÁLISIS ADICIONAL
        st.subheader("🔍 Análisis Adicional")
        
        tab1, tab2, tab3 = st.tabs(["📋 Resumen Ejecutivo", "⚖️ Comparativa Sector", "🎯 Estrategia"])
        
        with tab1:
            st.markdown(analisis_scoring.get('resumen_ejecutivo', 'Análisis no disponible'))
        
        with tab2:
            st.markdown(analisis_scoring.get('comparativa_sector', 'Comparativa no disponible'))
        
        with tab3:
            st.markdown(analisis_scoring.get('estrategia', 'Estrategia no disponible'))
            
    except Exception as e:
        st.error(f"Error en análisis IA: {str(e)}")
        st.info("💡 Intenta recargar la página o verificar tu conexión a internet.")

# FUNCIONES AUXILIARES MEJORADAS
def calcular_scoring_fundamental_mejorado(info):
    """
    Scoring fundamental MEJORADO con más métricas y análisis
    """
    score = 0
    max_score = 100
    metricas = {}
    analisis = {}
    
    # CORRECCIÓN: Asegurar que todos los valores sean numéricos
    pe = float(info.get('trailingPE', 0)) if info.get('trailingPE') else 0
    revenue_growth = float(info.get('revenueGrowth', 0)) if info.get('revenueGrowth') else 0
    roe = float(info.get('returnOnEquity', 0)) if info.get('returnOnEquity') else 0
    debt_to_equity = float(info.get('debtToEquity', 0)) if info.get('debtToEquity') else 0
    profit_margins = float(info.get('profitMargins', 0)) if info.get('profitMargins') else 0
    current_ratio = float(info.get('currentRatio', 0)) if info.get('currentRatio') else 0
    
    # 1. VALUACIÓN (25 puntos)
    if pe and pe > 0:
        if pe < 12:
            score += 25
            metricas['P/E Ratio'] = '🟢 Excelente (Muy Barato)'
        elif pe < 18:
            score += 20
            metricas['P/E Ratio'] = '🟡 Bueno (Razonable)'
        elif pe < 25:
            score += 15
            metricas['P/E Ratio'] = '🟠 Moderado (Justo)'
        else:
            score += 5
            metricas['P/E Ratio'] = '🔴 Alto (Caro)'
    else:
        metricas['P/E Ratio'] = '⚪ No disponible'
    
    # 2. CRECIMIENTO (20 puntos)
    if revenue_growth and revenue_growth > 0:
        if revenue_growth > 0.20:
            score += 20
            metricas['Crecimiento Ingresos'] = '🟢 Excelente (>20%)'
        elif revenue_growth > 0.10:
            score += 15
            metricas['Crecimiento Ingresos'] = '🟡 Bueno (10-20%)'
        elif revenue_growth > 0.05:
            score += 10
            metricas['Crecimiento Ingresos'] = '🟠 Moderado (5-10%)'
        else:
            score += 5
            metricas['Crecimiento Ingresos'] = '🔴 Bajo (<5%)'
    else:
        metricas['Crecimiento Ingresos'] = '🔴 Negativo'
    
    # 3. RENTABILIDAD (20 puntos)
    if roe and roe > 0:
        if roe > 0.20:
            score += 20
            metricas['ROE'] = '🟢 Excelente (>20%)'
        elif roe > 0.15:
            score += 15
            metricas['ROE'] = '🟡 Bueno (15-20%)'
        elif roe > 0.08:
            score += 10
            metricas['ROE'] = '🟠 Moderado (8-15%)'
        else:
            score += 5
            metricas['ROE'] = '🔴 Bajo (<8%)'
    else:
        metricas['ROE'] = '🔴 Negativo'
    
    # 4. SOLVENCIA (15 puntos)
    if debt_to_equity and debt_to_equity > 0:
        if debt_to_equity < 0.5:
            score += 15
            metricas['Deuda/Equity'] = '🟢 Excelente (<0.5)'
        elif debt_to_equity < 1.0:
            score += 12
            metricas['Deuda/Equity'] = '🟡 Bueno (0.5-1.0)'
        elif debt_to_equity < 2.0:
            score += 8
            metricas['Deuda/Equity'] = '🟠 Moderado (1.0-2.0)'
        else:
            score += 3
            metricas['Deuda/Equity'] = '🔴 Alto (>2.0)'
    else:
        metricas['Deuda/Equity'] = '🟢 Sin deuda'
    
    # 5. MÁRGENES (10 puntos)
    if profit_margins and profit_margins > 0:
        if profit_margins > 0.20:
            score += 10
            metricas['Margen Beneficio'] = '🟢 Excelente (>20%)'
        elif profit_margins > 0.10:
            score += 8
            metricas['Margen Beneficio'] = '🟡 Bueno (10-20%)'
        elif profit_margins > 0.05:
            score += 5
            metricas['Margen Beneficio'] = '🟠 Moderado (5-10%)'
        else:
            score += 2
            metricas['Margen Beneficio'] = '🔴 Bajo (<5%)'
    else:
        metricas['Margen Beneficio'] = '🔴 Sin beneficio'
    
    # 6. EFICIENCIA (10 puntos)
    if current_ratio and current_ratio > 0:
        if current_ratio > 2.0:
            score += 10
            metricas['Liquidez'] = '🟢 Excelente (>2.0)'
        elif current_ratio > 1.5:
            score += 8
            metricas['Liquidez'] = '🟡 Bueno (1.5-2.0)'
        elif current_ratio > 1.0:
            score += 5
            metricas['Liquidez'] = '🟠 Moderado (1.0-1.5)'
        else:
            score += 2
            metricas['Liquidez'] = '🔴 Bajo (<1.0)'
    else:
        metricas['Liquidez'] = '⚪ No disponible'
    
    # Análisis adicional
    analisis['resumen_ejecutivo'] = generar_resumen_ejecutivo(score, metricas)
    analisis['comparativa_sector'] = generar_comparativa_sector(info)
    analisis['estrategia'] = generar_estrategia_recomendada(score, info)
    
    return min(score, max_score), metricas, analisis

def analizar_sentimiento_avanzado(info, datos_historicos):
    """Análisis de sentimiento MEJORADO"""
    puntos = 0
    
    # Precio vs medias móviles
    if not datos_historicos.empty and len(datos_historicos) > 50:
        try:
            precio_actual = float(datos_historicos['Close'].iloc[-1])
            sma_20 = float(datos_historicos['Close'].rolling(window=20).mean().iloc[-1])
            sma_50 = float(datos_historicos['Close'].rolling(window=50).mean().iloc[-1])
            
            if precio_actual > sma_20 > sma_50:
                puntos += 2
            elif precio_actual > sma_20:
                puntos += 1
        except:
            pass
    
    # Fundamentales
    revenue_growth = float(info.get('revenueGrowth', 0)) if info.get('revenueGrowth') else 0
    profit_margins = float(info.get('profitMargins', 0)) if info.get('profitMargins') else 0
    debt_to_equity = float(info.get('debtToEquity', 0)) if info.get('debtToEquity') else 0
    
    if revenue_growth > 0.1:
        puntos += 1
    if profit_margins > 0.15:
        puntos += 1
    if debt_to_equity < 1.0:
        puntos += 1
    
    # Determinar sentimiento
    if puntos >= 4:
        return "MUY POSITIVO"
    elif puntos >= 3:
        return "POSITIVO"
    elif puntos >= 2:
        return "NEUTRAL"
    else:
        return "NEGATIVO"

def generar_recomendacion_automatica(scoring, sentimiento, pe_ratio, revenue_growth):
    """Genera recomendación automática MEJORADA"""
    if scoring >= 80 and sentimiento in ["MUY POSITIVO", "POSITIVO"]:
        return "🎯 COMPRAR FUERTE"
    elif scoring >= 65 and sentimiento in ["MUY POSITIVO", "POSITIVO"]:
        return "✅ COMPRAR"
    elif scoring >= 50:
        return "⚖️ MANTENER"
    elif scoring >= 35:
        return "⚠️ REDUCIR"
    else:
        return "🔴 VENDER"

def determinar_horizonte_inversion(scoring, beta, sentimiento):
    """Determina horizonte de inversión recomendado"""
    if scoring >= 75 and beta < 1.2:
        return "LARGO PLAZO (3+ años)"
    elif scoring >= 60:
        return "MEDIO PLAZO (1-3 años)"
    elif scoring >= 45:
        return "CORTO PLAZO (6-12 meses)"
    else:
        return "TRADING (<6 meses)"

def generar_resumen_ejecutivo(score, metricas):
    """Genera resumen ejecutivo del scoring"""
    if score >= 75:
        return "**🟢 EXCELENTE** - Empresa sólida con fundamentales fuertes. Alta calidad de inversión."
    elif score >= 60:
        return "**🟡 BUENA** - Empresa con buenos fundamentales. Oportunidad de inversión atractiva."
    elif score >= 45:
        return "**🟠 MODERADA** - Empresa con fundamentales aceptables. Requiere monitoreo cuidadoso."
    else:
        return "**🔴 DEFICIENTE** - Fundamentales débiles. Alto riesgo de inversión."

def generar_comparativa_sector(info):
    """Genera análisis comparativo con el sector"""
    pe = float(info.get('trailingPE', 0)) if info.get('trailingPE') else 0
    if pe < 15:
        return "📊 **VALUACIÓN**: Por debajo del promedio del sector (oportunidad)"
    elif pe < 25:
        return "📊 **VALUACIÓN**: En línea con el sector (justa)"
    else:
        return "📊 **VALUACIÓN**: Por encima del sector (sobrevalorada)"

def generar_estrategia_recomendada(score, info):
    """Genera estrategia de inversión recomendada"""
    if score >= 70:
        return "🎯 **ESTRATEGIA**: Inversión de valor a largo plazo. Acumular en correcciones."
    elif score >= 50:
        return "🎯 **ESTRATEGIA**: Inversión moderada. Diversificar y monitorear trimestralmente."
    else:
        return "🎯 **ESTRATEGIA**: Evitar o considerar solo para trading de momentum."

def mostrar_analisis_respaldo(info, precio_actual, market_cap, pe_ratio, revenue_growth):
    """Análisis de respaldo MEJORADO - CORREGIDO"""
    # CORRECCIÓN: Asegurar que todos los valores sean numéricos
    precio_actual = float(precio_actual) if precio_actual else 0.0
    market_cap = float(market_cap) if market_cap else 0.0
    pe_ratio = float(pe_ratio) if pe_ratio else 0.0
    revenue_growth = float(revenue_growth) if revenue_growth else 0.0
    
    # Obtener otros valores numéricos necesarios
    roe = float(info.get('returnOnEquity', 0)) if info.get('returnOnEquity') else 0.0
    profit_margins = float(info.get('profitMargins', 0)) if info.get('profitMargins') else 0.0
    debt_to_equity = float(info.get('debtToEquity', 0)) if info.get('debtToEquity') else 0.0
    current_ratio = float(info.get('currentRatio', 0)) if info.get('currentRatio') else 0.0
    beta = float(info.get('beta', 1)) if info.get('beta') else 1.0
    
    # Calcular scoring para el análisis de respaldo
    scoring, _, _ = calcular_scoring_fundamental_mejorado(info)
    sentimiento = analizar_sentimiento_avanzado(info, pd.DataFrame())
    horizonte = determinar_horizonte_inversion(scoring, beta, sentimiento)
    
    st.info(f"""
    **📊 ANÁLISIS FUNDAMENTAL AVANZADO (Respaldo)**
    
    **💰 VALUACIÓN:**
    - Precio: ${precio_actual:.2f}
    - Market Cap: ${market_cap/1e9:.2f}B
    - P/E Ratio: {pe_ratio:.1f}
    - Crecimiento: {revenue_growth*100:.1f}%
    
    **📈 ANÁLISIS DETALLADO:**
    
    **1. VALORACIÓN:**
    - P/E Ratio: {pe_ratio:.1f}
    - Comparativa: {"BARATA" if pe_ratio and pe_ratio < 15 else "JUSTA" if pe_ratio and pe_ratio < 25 else "CARA"}
    
    **2. CRECIMIENTO:**
    - Tasa crecimiento: {revenue_growth*100:.1f}%
    - Perspectiva: {"FUERTE" if revenue_growth and revenue_growth > 0.15 else "MODERADO" if revenue_growth and revenue_growth > 0.08 else "DÉBIL"}
    
    **3. RENTABILIDAD:**
    - ROE: {roe*100:.1f}%
    - Margen beneficio: {profit_margins*100:.1f}%
    
    **4. SOLVENCIA:**
    - Deuda/Equity: {debt_to_equity:.2f}
    - Liquidez: {current_ratio:.2f}
    
    **🎯 RECOMENDACIÓN:**
    - Scoring: {scoring}/100
    - Sentimiento: {sentimiento}
    - Horizonte: {horizonte}
    """)