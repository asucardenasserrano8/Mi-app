import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import google.generativeai as genai

def mostrar(datos_accion):
    """
    Sección de Análisis de Riesgo Avanzado - Adaptada para recibir datos_accion
    """
    # Extraer información de datos_accion
    stonk = datos_accion['ticker']
    info = datos_accion['info']
    nombre = datos_accion['nombre']
    
    st.header(f"⚠️ Análisis de Riesgo Avanzado De {nombre}")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 20px; border-radius: 10px; margin: 15px 0;'>
    <h4 style='color: white;'>🔍 EVALUACIÓN COMPLETA DE RIESGOS</h4>
    <p>Análisis profesional de los diferentes tipos de riesgo que afectan a esta inversión</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener métricas de riesgo
    with st.spinner('Calculando métricas avanzadas de riesgo...'):
        metricas_riesgo = calcular_metricas_riesgo_avanzadas(stonk, periodo_años=5)
    
    if metricas_riesgo:
        # =============================================
        # 1. RESUMEN EJECUTIVO DE RIESGO
        # =============================================
        st.subheader("📊 Resumen Ejecutivo de Riesgo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Clasificación de riesgo general
            score_riesgo = 0
            if metricas_riesgo['Drawdown Máximo'] > 0.4:
                score_riesgo += 3
            elif metricas_riesgo['Drawdown Máximo'] > 0.25:
                score_riesgo += 2
            elif metricas_riesgo['Drawdown Máximo'] > 0.15:
                score_riesgo += 1
                
            if metricas_riesgo['Volatilidad Anual'] > 0.5:
                score_riesgo += 3
            elif metricas_riesgo['Volatilidad Anual'] > 0.3:
                score_riesgo += 2
            elif metricas_riesgo['Volatilidad Anual'] > 0.2:
                score_riesgo += 1
                
            if metricas_riesgo['Beta'] > 1.5:
                score_riesgo += 2
            elif metricas_riesgo['Beta'] > 1.2:
                score_riesgo += 1
            
            if score_riesgo >= 5:
                riesgo_color = "red"
                riesgo_texto = "ALTO RIESGO"
                riesgo_icono = "🔴"
            elif score_riesgo >= 3:
                riesgo_color = "orange"
                riesgo_texto = "RIESGO MODERADO-ALTO"
                riesgo_icono = "🟡"
            elif score_riesgo >= 1:
                riesgo_color = "blue"
                riesgo_texto = "RIESGO MODERADO"
                riesgo_icono = "🔵"
            else:
                riesgo_color = "green"
                riesgo_texto = "BAJO RIESGO"
                riesgo_icono = "🟢"
                
            st.metric("Nivel de Riesgo General", f"{riesgo_icono} {riesgo_texto}")
        
        with col2:
            st.metric("Drawdown Máximo Histórico", f"{metricas_riesgo['Drawdown Máximo']:.1%}")
        
        with col3:
            st.metric("Volatilidad Anual", f"{metricas_riesgo['Volatilidad Anual']:.1%}")
        
        with col4:
            st.metric("Beta vs Mercado", f"{metricas_riesgo['Beta']:.2f}")
        
        # =============================================
        # 2. MÉTRICAS CUANTITATIVAS DE RIESGO
        # =============================================
        st.subheader("📈 Métricas Cuantitativas de Riesgo")

        # Pre-procesar valores para display
        sortino_val = metricas_riesgo.get('Sortino Ratio', 0)
        sortino_display = f"{sortino_val:.2f}" if abs(sortino_val) > 0.01 else f"{sortino_val:.4f}"

        var_val = metricas_riesgo.get('VaR 95% Anual', 0)
        var_display = f"{abs(var_val):.1%}" if abs(var_val) > 0.001 else "< 0.1%"

        skewness_val = metricas_riesgo.get('Skewness', 0)
        skewness_display = f"{skewness_val:.2f}" if abs(skewness_val) > 0.01 else f"{skewness_val:.4f}"

        max_perdida_val = metricas_riesgo.get('Máxima Pérdida Consecutiva', 0)
        max_perdida_display = f"{max_perdida_val} días" if max_perdida_val > 0 else "0 días"

        # Primera fila de métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Sharpe Ratio", f"{metricas_riesgo['Sharpe Ratio']:.2f}",
                    help="Rendimiento por unidad de riesgo total")

        with col2:
            st.metric("Sortino Ratio", sortino_display,
                    help="Rendimiento por unidad de riesgo bajista")

        with col3:
            st.metric("VaR 95% (Anual)", var_display,
                    help="Pérdida máxima esperada en condiciones normales")

        with col4:
            st.metric("Alpha", f"{metricas_riesgo['Alpha']:.2%}",
                    help="Rendimiento excedente sobre el esperado")

        # Segunda fila de métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Correlación S&P500", f"{metricas_riesgo['Correlación S&P500']:.2f}",
                    help="Grado de relación con el mercado")

        with col2:
            st.metric("Probabilidad Pérdida", f"{metricas_riesgo['Probabilidad de Pérdida (%)']:.1f}%",
                    help="% de días con rendimientos negativos")

        with col3:
            st.metric("Máxima Pérdida Consecutiva", max_perdida_display,
                    help="Racha máxima de días negativos")

        with col4:
            st.metric("Skewness", skewness_display,
                    help="Asimetría de la distribución de retornos")
        
        # =============================================
        # 3. ANÁLISIS GRÁFICO DE RIESGO
        # =============================================
        st.subheader("📊 Visualización de Riesgos")
        
        col_grafica1, col_grafica2 = st.columns(2)
        
        with col_grafica1:
            # Gráfica de Drawdown
            st.markdown("**📉 Análisis de Drawdown**")
            grafica_drawdown = crear_grafica_drawdown_mejorada(stonk)
            if grafica_drawdown:
                st.plotly_chart(grafica_drawdown, use_container_width=True)
                st.caption("Evolución histórica de las caídas desde máximos. Áreas rojas indican períodos de pérdidas.")
        
        with col_grafica2:
            # Gráfica de Distribución
            st.markdown("**📊 Distribución de Retornos**")
            grafica_distribucion = crear_grafica_distribucion_retornos(stonk)
            if grafica_distribucion:
                st.plotly_chart(grafica_distribucion, use_container_width=True)
                st.caption("Distribución de ganancias/pérdidas diarias. Línea roja = distribución normal teórica.")
        

        # =============================================
        # 4. COMPARATIVA CON EL MERCADO
        # =============================================
        st.subheader("📈 Comparativa de Riesgo vs Mercado")
        
        col_comp1, col_comp2, col_comp3 = st.columns(3)
        
        with col_comp1:
            vol_vs_mercado = (metricas_riesgo['Volatilidad Anual'] - 0.15) * 100  # 15% volatilidad promedio mercado
            st.metric("Volatilidad vs Mercado", 
                     f"{metricas_riesgo['Volatilidad Anual']:.1%}",
                     f"{vol_vs_mercado:+.1f}%")
        
        with col_comp2:
            beta_interpretacion = "Más volátil" if metricas_riesgo['Beta'] > 1 else "Menos volátil"
            st.metric("Beta vs Mercado", 
                     f"{metricas_riesgo['Beta']:.2f}",
                     beta_interpretacion)
        
        with col_comp3:
            sharpe_mercado = 0.6  # Sharpe promedio mercado
            sharpe_diff = metricas_riesgo['Sharpe Ratio'] - sharpe_mercado
            st.metric("Sharpe vs Mercado", 
                     f"{metricas_riesgo['Sharpe Ratio']:.2f}",
                     f"{sharpe_diff:+.2f}")
        
        # =============================================
        # 5. ALERTAS Y SEÑALES DE RIESGO
        # =============================================
        st.subheader("🚨 Alertas de Riesgo Activas")
        
        alertas = []
        
        # Verificar condiciones de riesgo
        if metricas_riesgo['Drawdown Máximo'] < -0.25:
            alertas.append("🔴 **ALTA ALERTA**: Drawdown histórico > 25%")
        elif metricas_riesgo['Drawdown Máximo'] < -0.15:
            alertas.append("🟡 **ALERTA MODERADA**: Drawdown histórico > 15%")
            
        if metricas_riesgo['Volatilidad Anual'] > 0.40:
            alertas.append("🔴 **ALTA VOLATILIDAD**: > 40% anual")
        elif metricas_riesgo['Volatilidad Anual'] > 0.25:
            alertas.append("🟡 **VOLATILIDAD ELEVADA**: > 25% anual")
            
        if metricas_riesgo['Probabilidad de Pérdida (%)'] > 55:
            alertas.append("🔴 **ALTA FRECUENCIA PÉRDIDAS**: > 55% de días negativos")
        elif metricas_riesgo['Probabilidad de Pérdida (%)'] > 50:
            alertas.append("🟡 **FRECUENCIA PÉRDIDAS ELEVADA**: > 50% de días negativos")
            
        if metricas_riesgo.get('VaR 95% Anual', 0) < -0.30:
            alertas.append("🔴 **VAR EXTREMO**: Pérdida esperada > 30%")
            
        if metricas_riesgo['Beta'] > 1.5:
            alertas.append("🟡 **BETA ALTO**: > 1.5 - Muy sensible al mercado")
        
        if alertas:
            for alerta in alertas:
                st.warning(alerta)
        else:
            st.success("✅ **SIN ALERTAS CRÍTICAS**: Perfil de riesgo dentro de parámetros normales")
        
        # =============================================
        # 6. HISTORIAL DE ESTRESES
        # =============================================
        st.subheader("📅 Historial de Eventos de Estrés")
        
        # Simulación de eventos de estrés (en una app real esto vendría de datos históricos)
        eventos_estres = [
            {"fecha": "2020-03", "evento": "COVID-19", "impacto": "Mercado global -40%"},
            {"fecha": "2022-01", "evento": "Subida tasas Fed", "impacto": "Tech -30%"},
            {"fecha": "2023-03", "evento": "Crisis bancaria", "impacto": "Bancos -25%"}
        ]
        
        for evento in eventos_estres:
            col_fecha, col_evento, col_impacto = st.columns([1, 2, 2])
            with col_fecha:
                st.write(f"**{evento['fecha']}**")
            with col_evento:
                st.write(evento['evento'])
            with col_impacto:
                st.write(evento['impacto'])

        # =============================================
        # 7. ANÁLISIS CUALITATIVO CON IA
        # =============================================
        st.subheader("🤖 Análisis Cualitativo de Riesgo")
        
        with st.spinner('Generando análisis cualitativo con IA...'):
            analisis_ia = generar_analisis_riesgo_ia(stonk, metricas_riesgo, nombre)
            
            if analisis_ia:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px;'>
                <h4 style='color: white;'>ANÁLISIS DE RIESGO POR IA</h4>
                """, unsafe_allow_html=True)
                st.write(analisis_ia)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("""
                **Análisis Cualitativo de Riesgos:**
                
                Basado en las métricas calculadas, aquí tienes un análisis de los riesgos:
                
                **🔴 Riesgos Principales Identificados:**
                - **Drawdown del {:.1f}%**: Indica que históricamente ha tenido caídas significativas
                - **Volatilidad del {:.1f}%**: Sugiere movimientos de precio considerables
                - **Beta de {:.2f}**: {} volatilidad que el mercado
                
                **🟡 Factores a Considerar:**
                - Sharpe Ratio de {:.2f}: {}
                - Probabilidad de pérdida: {:.1f}% de los días
                - Correlación con mercado: {:.2f}
                """.format(
                    metricas_riesgo['Drawdown Máximo'] * 100,
                    metricas_riesgo['Volatilidad Anual'] * 100,
                    metricas_riesgo['Beta'],
                    "Mayor" if metricas_riesgo['Beta'] > 1 else "Menor",
                    metricas_riesgo['Sharpe Ratio'],
                    "Rendimiento ajustado al riesgo positivo" if metricas_riesgo['Sharpe Ratio'] > 0 else "Rendimiento ajustado al riesgo negativo",
                    metricas_riesgo['Probabilidad de Pérdida (%)'],
                    metricas_riesgo['Correlación S&P500']
                ))
        
        # =============================================
        # 8. TIPOS DE RIESGO DETALLADOS
        # =============================================
        st.subheader("🎯 Tipos de Riesgo Específicos")
        
        # Crear pestañas para diferentes tipos de riesgo
        tab1, tab2, tab3, tab4 = st.tabs(["📉 Riesgo de Mercado", "🏦 Riesgo Financiero", "📊 Riesgo Operativo", "🌍 Riesgo Sectorial"])
        
        with tab1:
            st.markdown("""
            **📉 RIESGO DE MERCADO (Sistemático)**
            
            *No diversificable - Afecta a todo el mercado*
            
            **Métricas clave para {}:**
            - **Beta: {:.2f}** - {} sensibilidad a movimientos del mercado
            - **Volatilidad: {:.1f}%** - Nivel de fluctuación de precios
            - **Correlación S&P500: {:.2f}** - Grado de sincronización con el mercado
            - **VaR 95%: {:.1f}%** - Pérdida máxima esperada en condiciones normales
            
            **🔍 Impacto:** {}
            """.format(
                stonk,
                metricas_riesgo['Beta'],
                "Alta" if metricas_riesgo['Beta'] > 1.2 else "Moderada" if metricas_riesgo['Beta'] > 0.8 else "Baja",
                metricas_riesgo['Volatilidad Anual'] * 100,
                metricas_riesgo['Correlación S&P500'],
                metricas_riesgo.get('VaR 95% Anual', 0) * 100,
                "Alta exposición a riesgos de mercado" if metricas_riesgo['Beta'] > 1.2 else "Exposición moderada" if metricas_riesgo['Beta'] > 0.8 else "Baja exposición"
            ))
            
        with tab2:
            # Obtener información financiera para riesgo financiero
            deuda_equity = info.get('debtToEquity', 0)
            current_ratio = info.get('currentRatio', 0)
            interest_coverage = info.get('earningsBeforeInterestAndTaxes', 0) / max(info.get('interestExpense', 1), 1)
            
            st.markdown("""
            **🏦 RIESGO FINANCIERO**
            
            *Relacionado con la estructura de capital y solvencia*
            
            **Métricas clave:**
            - **Deuda/Equity: {:.2f}** - {}
            - **Current Ratio: {:.2f}** - {}
            - **Cobertura de Intereses: {:.1f}x** - {}
            
            **🔍 Evaluación:** {}
            """.format(
                deuda_equity,
                "Alto apalancamiento" if deuda_equity > 2 else "Apalancamiento moderado" if deuda_equity > 1 else "Bajo apalancamiento",
                current_ratio,
                "Buena liquidez" if current_ratio > 1.5 else "Liquidez adecuada" if current_ratio > 1 else "Posibles problemas de liquidez",
                interest_coverage,
                "Cobertura sólida" if interest_coverage > 5 else "Cobertura adecuada" if interest_coverage > 2 else "Cobertura insuficiente",
                "Perfil financiero conservador" if deuda_equity < 1 and current_ratio > 1.5 else "Perfil financiero moderado" if deuda_equity < 2 and current_ratio > 1 else "Perfil financiero agresivo"
            ))
            
        with tab3:
            st.markdown("""
            **📊 RIESGO OPERATIVO**
            
            *Relacionado con las operaciones del negocio*
            
            **Indicadores clave:**
            - **Margen Operativo: {}** - Eficiencia operativa
            - **ROE: {}** - Rentabilidad sobre el capital
            - **Crecimiento Ingresos: {}** - Dinamismo del negocio
            
            **🔍 Factores a monitorear:**
            • Gestión de costos y eficiencia operativa
            • Capacidad de generación de flujo de caja
            • Inversiones en investigación y desarrollo
            • Eficiencia del management
            """.format(
                f"{info.get('operatingMargins', 0)*100:.1f}%" if info.get('operatingMargins') else "N/A",
                f"{info.get('returnOnEquity', 0)*100:.1f}%" if info.get('returnOnEquity') else "N/A",
                f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A"
            ))
            
        with tab4:
            sector = info.get('sector', 'N/A')
            industria = info.get('industry', 'N/A')
            
            st.markdown("""
            **🌍 RIESGO SECTORIAL**
            
            *Riesgos específicos del sector industrial*
            
            **Contexto sectorial:**
            - **Sector:** {}
            - **Industria:** {}
            
            **🔍 Riesgos sectoriales típicos:**
            • Cambios regulatorios del sector
            • Ciclos económicos específicos
            • Disrupción tecnológica
            • Competencia intensiva
            • Dependencia de materias primas
            """.format(sector, industria))
        
        # =============================================
        # 9. RECOMENDACIONES DE GESTIÓN DE RIESGO
        # =============================================
        st.subheader("🛡️ Estrategias de Mitigación de Riesgo")
        
        col_rec1, col_rec2 = st.columns(2)
        
        with col_rec1:
            st.markdown("""
            **✅ PARA RIESGO MODERADO-BAJO:**
            
            • **Diversificación básica**: 15-20 acciones diferentes
            • **Horizonte medio**: 3-5 años de inversión
            • **Monitoreo trimestral**: Revisión periódica
            • **Stop-loss del 15%**: Protección básica
            """)
            
        with col_rec2:
            st.markdown("""
            **⚠️ PARA RIESGO MODERADO-ALTO:**
            
            • **Diversificación amplia**: 25+ acciones
            • **Stop-loss del 10%**: Protección más estricta
            • **Posicionamiento reducido**: Menor exposición
            • **Monitoreo mensual**: Seguimiento cercano
            • **Hedging consideración**: Opciones de protección
            """)
    
        # =============================================
        # 10. PANEL DE CONTROL DE RIESGO
        # =============================================
        st.markdown("---")
        col_ctrl1, col_ctrl2 = st.columns(2)
        
        with col_ctrl1:
            if st.button("🔄 Recalcular Métricas", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
                
        with col_ctrl2:
            # Exportar datos de riesgo
            csv_riesgo = pd.DataFrame([metricas_riesgo]).to_csv(index=False)
            st.download_button(
                label="📥 Exportar Reporte Riesgo",
                data=csv_riesgo,
                file_name=f"riesgo_{stonk}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    else:
        st.error("""
        ❌ No se pudieron calcular las métricas de riesgo para esta acción.
        
        **Posibles causas:**
        • Datos históricos insuficientes
        • Símbolo no válido o no cotizado
        • Problemas de conexión con las fuentes de datos
        
        **Sugerencias:**
        • Verifica que el símbolo sea correcto
        • Intenta con una acción más líquida y conocida
        • Espera unos minutos e intenta nuevamente
        """)
        
        if st.button("🔄 Intentar nuevamente", use_container_width=True):
            st.rerun()

    # =============================================
    # INFORMACIÓN EDUCATIVA SOBRE RIESGOS
    # =============================================
    with st.expander("📚 Guía Educativa: Entendiendo los Riesgos de Inversión", expanded=False):
        st.markdown("""
        ## 🎓 Guía Completa de Análisis de Riesgo
        
        ### 📉 ¿Qué es el Riesgo en Inversiones?
        
        El riesgo es la **posibilidad de perder dinero** en una inversión. Todas las inversiones conllevan algún nivel de riesgo, y generalmente:
        - **Mayor riesgo potencial = Mayor rendimiento potencial**
        - **Menor riesgo potencial = Menor rendimiento potencial**
        
        ### 🎯 Tipos Principales de Riesgo
        
        **1. Riesgo de Mercado (Sistemático)**
        - Afecta a TODO el mercado
        - No se puede eliminar con diversificación
        - Ejemplos: Recesiones, crisis geopolíticas, pandemias
        
        **2. Riesgo Específico (No Sistemático)**
        - Afecta a UNA empresa o sector específico
        - SÍ se puede reducir con diversificación
        - Ejemplos: Mala gestión, problemas legales, huelgas
        
        **3. Riesgo de Liquidez**
        - No poder vender rápidamente sin afectar el precio
        - Común en acciones de baja capitalización
        
        **4. Riesgo de Tasa de Interés**
        - Las subidas de tasas afectan negativamente a las acciones
        
        ### 📊 Métricas Clave Explicadas
        
        **• Volatilidad:** Mide cuánto fluctúa el precio
        - Alta volatilidad = Precio muy variable
        - Baja volatilidad = Precio más estable
        
        **• Drawdown Máximo:** Mayor caída histórica desde un pico
        - Drawdown 25% = Cayó 25% desde su máximo histórico
        - Importante para entender el "peor escenario"
        
        **• Beta:** Sensibilidad vs mercado
        - Beta 1.0 = Se mueve igual que el mercado
        - Beta 1.5 = 50% más volátil que el mercado
        - Beta 0.8 = 20% menos volátil que el mercado
        
        **• Sharpe Ratio:** Rendimiento por unidad de riesgo
        - >1.0 = Buen rendimiento ajustado al riesgo
        - <0 = Mal rendimiento ajustado al riesgo
        
        **• Value at Risk (VaR):** Pérdida máxima esperada
        - VaR 95% = 5% probabilidad de perder más de X%
        - Ayuda a dimensionar posibles pérdidas
        
        ### 🛡️ Estrategias de Gestión de Riesgo
        
        1. **Diversificación:** No poner todos los huevos en una canasta
        2. **Asset Allocation:** Distribuir entre diferentes tipos de activos
        3. **Stop-Loss:** Límites automáticos de pérdida
        4. **Hedging:** Usar instrumentos de protección
        5. **Dollar-Cost Averaging:** Invertir cantidades fijas periódicamente
        
        ### 💡 Consejos Prácticos
        
        - **Conoce tu tolerancia al riesgo** antes de invertir
        - **Diversifica siempre**, incluso en buenas oportunidades
        - **Establece límites de pérdida** antes de comprar
        - **Mantén perspectiva a largo plazo**
        - **Revisa periódicamente** tu exposición al riesgo
        """)

# FUNCIONES DE APOYO (MANTENIDAS DEL CÓDIGO ORIGINAL)
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
    Crea gráfica de drawdown con datos reales
    """
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=periodo_años * 365)
        
        stock_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval='1d')
        if stock_data.empty:
            return None
        
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_close = stock_data[('Close', ticker_symbol)]
        else:
            stock_close = stock_data['Close']
        
        returns = stock_close.pct_change().dropna()
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown * 100,
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.3)',
            line=dict(color='red', width=2),
            name='Drawdown'
        ))
        
        fig.update_layout(
            title=f'Drawdown Real - {ticker_symbol}',
            xaxis_title='Fecha',
            yaxis_title='Drawdown (%)',
            height=500
        )
        
        return fig
        
    except Exception as e:
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

def generar_analisis_riesgo_ia(simbolo, datos_riesgo, nombre_empresa):
    """
    Genera análisis de riesgo COMPLETO usando IA de Google Gemini
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Crear prompt detallado y estructurado
        prompt = f"""
        Eres un analista de riesgo financiero senior en un fondo de inversión global. 
        Analiza DETALLADAMENTE estos datos de riesgo para {nombre_empresa} ({simbolo}):

        📊 DATOS DE RIESGO COMPLETOS:
        
        • Drawdown Máximo Histórico: {datos_riesgo.get('Drawdown Máximo', 0)*100:.1f}%
        • Volatilidad Anualizada: {datos_riesgo.get('Volatilidad Anual', 0)*100:.1f}%
        • Sharpe Ratio: {datos_riesgo.get('Sharpe Ratio', 0):.3f}
        • Sortino Ratio: {datos_riesgo.get('Sortino Ratio', 0):.3f}
        • Beta vs Mercado: {datos_riesgo.get('Beta', 0):.2f}
        • Alpha: {datos_riesgo.get('Alpha', 0)*100:.2f}%
        • Value at Risk (VaR 95%): {datos_riesgo.get('VaR 95% Anual', 0)*100:.1f}%
        • Expected Shortfall (CVaR): {datos_riesgo.get('Expected Shortfall 95%', 0)*100:.1f}%
        • Correlación S&P500: {datos_riesgo.get('Correlación S&P500', 0):.3f}
        • Probabilidad de Pérdida Diaria: {datos_riesgo.get('Probabilidad de Pérdida (%)', 0):.1f}%
        • Máxima Pérdida Consecutiva: {datos_riesgo.get('Máxima Pérdida Consecutiva', 0)} días
        • Skewness: {datos_riesgo.get('Skewness', 0):.3f}
        • Kurtosis: {datos_riesgo.get('Kurtosis', 0):.3f}

        Proporciona un análisis PROFESIONAL que incluya:

        1. 🎯 EVALUACIÓN GLOBAL DEL RIESGO (1-10 escala)
        2. 📈 PRINCIPALES FUENTES DE RIESGO identificadas
        3. ⚖️ COMPARACIÓN con benchmarks del mercado
        4. 🛡️ RECOMENDACIONES ESPECÍFICAS de gestión
        5. 👤 PERFIL DE INVERSOR ADECUADO
        6. ⚠️ SEÑALES DE ALERTA principales
        7. 💡 ESTRATEGIAS DE MITIGACIÓN

        Sé técnico pero claro. Usa terminología profesional.
        Máximo 300 palabras. Basado estrictamente en los datos proporcionados.
        Incluye métricas específicas en tu análisis.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # Análisis de respaldo COMPLETO si falla la IA
        drawdown = datos_riesgo.get('Drawdown Máximo', 0) * 100
        volatilidad = datos_riesgo.get('Volatilidad Anual', 0) * 100
        sharpe = datos_riesgo.get('Sharpe Ratio', 0)
        beta = datos_riesgo.get('Beta', 0)
        var = datos_riesgo.get('VaR 95% Anual', 0) * 100
        
        # Evaluación automática
        riesgo_score = 0
        if drawdown > 40: riesgo_score += 3
        elif drawdown > 25: riesgo_score += 2
        elif drawdown > 15: riesgo_score += 1
        
        if volatilidad > 50: riesgo_score += 3
        elif volatilidad > 30: riesgo_score += 2
        elif volatilidad > 20: riesgo_score += 1
        
        if beta > 1.5: riesgo_score += 2
        elif beta > 1.2: riesgo_score += 1
        
        nivel_riesgo = "ALTO" if riesgo_score >= 5 else "MODERADO-ALTO" if riesgo_score >= 3 else "MODERADO" if riesgo_score >= 1 else "BAJO"
        
        return f"""
        **🔍 ANÁLISIS DE RIESGO AVANZADO - {nombre_empresa}**

        **📊 EVALUACIÓN GLOBAL: {nivel_riesgo}**
        - Puntuación de riesgo: {riesgo_score}/8
        - Drawdown histórico: {drawdown:.1f}% ({'CRÍTICO' if drawdown > 40 else 'ALTO' if drawdown > 25 else 'MODERADO' if drawdown > 15 else 'BAJO'})
        - Volatilidad anual: {volatilidad:.1f}%

        **📈 MÉTRICAS CLAVE:**
        • Sharpe Ratio: {sharpe:.3f} ({'BUENO' if sharpe > 1.0 else 'ACEPTABLE' if sharpe > 0.5 else 'DEFICIENTE'})
        • Beta: {beta:.2f} ({'ALTA' if beta > 1.2 else 'MODERADA' if beta > 0.8 else 'BAJA'} sensibilidad al mercado)
        • VaR 95%: {var:.1f}% (Pérdida máxima esperada)
        • Prob. pérdida: {datos_riesgo.get('Probabilidad de Pérdida (%)', 0):.1f}% de días

        **🛡️ RECOMENDACIONES:**
        1. Stop-loss: {max(10, abs(drawdown * 0.6)):.0f}% (basado en drawdown histórico)
        2. Posicionamiento: {'REDUCIDO' if riesgo_score >= 4 else 'MODERADO' if riesgo_score >= 2 else 'NORMAL'}
        3. Diversificación: {'ALTA' if beta > 1.2 else 'MODERADA'} recomendada
        4. Monitoreo: {'SEMANAL' if volatilidad > 40 else 'MENSUAL'}

        **👤 PERFIL ADECUADO:** {'INVERSOR EXPERIMENTADO' if riesgo_score >= 4 else 'INVERSOR MODERADO' if riesgo_score >= 2 else 'INVERSOR CONSERVADOR'}
        """