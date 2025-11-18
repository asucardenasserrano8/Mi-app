# sections/analisis_tecnico.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_fetcher import obtener_datos_accion
from utils.technical_analysis import calcular_indicadores_tecnicos

def mostrar(datos_accion):
    """
    Función principal que muestra la sección de análisis técnico
    Compatible con la estructura de app.py
    """
    stonk = datos_accion['ticker']
    nombre = datos_accion['nombre']
    
    mostrar_analisis_tecnico(stonk, nombre)

def mostrar_analisis_tecnico(stonk, nombre):
    """
    Muestra la sección completa de análisis técnico
    """
    st.header(f"📈 Análisis Técnico - {nombre}")
    
    try:
        # Obtener datos
        data = obtener_datos_accion(stonk, periodo="1y")
        
        if data.empty:
            st.warning("No se encontraron datos para análisis técnico")
            return
        
        # Verificar la estructura de los datos
        st.write(f"📊 Estructura de datos: {data.shape[0]} filas, {data.shape[1]} columnas")
        
        # Si los datos tienen MultiIndex, simplificarlos
        if isinstance(data.columns, pd.MultiIndex):
            simple_data = pd.DataFrame()
            for col_type in ['Open', 'High', 'Low', 'Close', 'Volume']:
                cols = [col for col in data.columns if col_type in col]
                if cols:
                    simple_data[col_type] = data[cols[0]]
            data = simple_data
        
        # Calcular indicadores técnicos
        data_tech = calcular_indicadores_tecnicos(data)
        
        if data_tech.empty:
            st.error("No se pudieron calcular los indicadores técnicos")
            return
        
        # Selector de indicadores
        st.subheader("🔧 Indicadores Técnicos")
        indicadores = st.multiselect(
            "Selecciona los indicadores a mostrar:",
            ["RSI", "MACD", "Bandas Bollinger", "Medias Móviles"],
            default=["RSI", "MACD"]
        )
        
        # Crear gráfica principal
        fig = crear_grafica_principal(data_tech, indicadores, stonk)
        st.plotly_chart(fig, use_container_width=True)
        
        # REDUCIR ESPACIO ENTRE GRÁFICA Y SEÑALES
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Mostrar señales técnicas
        mostrar_senales_tecnicas(data_tech)
        
        # PEQUEÑO ESPACIO ANTES DEL RESUMEN
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Mostrar resumen de indicadores
        mostrar_resumen_indicadores(data_tech)
        
        # PEQUEÑO ESPACIO ANTES DE LA SECCIÓN EDUCATIVA
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Mostrar sección educativa
        mostrar_seccion_educativa()
        
        # Mostrar consejos prácticos
        mostrar_consejos_practicos()
        
        # Opción para descargar datos
        mostrar_descarga_datos(data_tech, stonk)
        
    except Exception as e:
        st.error(f"Error en análisis técnico: {str(e)}")
        st.write("Detalles del error:", str(e))

def crear_grafica_principal(data_tech, indicadores, stonk):
    """
    Crea la gráfica principal con todos los indicadores seleccionados
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Precio e Indicadores', 'RSI y MACD'),
        row_heights=[0.6, 0.4]
    )
    
    # Gráfica de velas (fila 1)
    fig.add_trace(go.Candlestick(
        x=data_tech.index,
        open=data_tech['Open'],
        high=data_tech['High'],
        low=data_tech['Low'],
        close=data_tech['Close'],
        name='Precio'
    ), row=1, col=1)
    
    # Bandas de Bollinger
    if "Bandas Bollinger" in indicadores and all(col in data_tech.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
        fig.add_trace(go.Scatter(
            x=data_tech.index, y=data_tech['BB_Upper'],
            line=dict(color='rgba(255,0,0,0.5)', width=1),
            name='BB Superior',
            legendgroup="bollinger"
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=data_tech.index, y=data_tech['BB_Middle'],
            line=dict(color='rgba(0,255,0,0.5)', width=1),
            name='BB Media',
            legendgroup="bollinger"
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=data_tech.index, y=data_tech['BB_Lower'],
            line=dict(color='rgba(0,0,255,0.5)', width=1),
            name='BB Inferior',
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.1)',
            legendgroup="bollinger"
        ), row=1, col=1)
    
    # Medias Móviles
    if "Medias Móviles" in indicadores:
        if 'SMA_20' in data_tech.columns:
            fig.add_trace(go.Scatter(
                x=data_tech.index, y=data_tech['SMA_20'],
                line=dict(color='orange', width=2),
                name='SMA 20'
            ), row=1, col=1)
        
        if 'SMA_50' in data_tech.columns:
            fig.add_trace(go.Scatter(
                x=data_tech.index, y=data_tech['SMA_50'],
                line=dict(color='red', width=2),
                name='SMA 50'
            ), row=1, col=1)
        
        if 'SMA_200' in data_tech.columns:
            fig.add_trace(go.Scatter(
                x=data_tech.index, y=data_tech['SMA_200'],
                line=dict(color='purple', width=2),
                name='SMA 200'
            ), row=1, col=1)
    
    # RSI (fila 2)
    if "RSI" in indicadores and 'RSI' in data_tech.columns:
        fig.add_trace(go.Scatter(
            x=data_tech.index, y=data_tech['RSI'],
            line=dict(color='blue', width=2),
            name='RSI'
        ), row=2, col=1)
        
        # Líneas de sobrecompra/sobreventa
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
    
    # MACD (fila 2, segundo eje Y)
    if "MACD" in indicadores and all(col in data_tech.columns for col in ['MACD', 'MACD_Signal']):
        fig.add_trace(go.Scatter(
            x=data_tech.index, y=data_tech['MACD'],
            line=dict(color='red', width=2),
            name='MACD',
            yaxis='y2'
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=data_tech.index, y=data_tech['MACD_Signal'],
            line=dict(color='blue', width=2),
            name='Señal MACD',
            yaxis='y2'
        ), row=2, col=1)
        
        # Configurar segundo eje Y para MACD
        fig.update_layout(
            yaxis2=dict(
                title='MACD',
                overlaying='y',
                side='right'
            )
        )
    
    fig.update_layout(
        height=800, 
        showlegend=True, 
        xaxis_rangeslider_visible=False,
        title=f"Análisis Técnico de {stonk}"
    )
    
    return fig

def mostrar_senales_tecnicas(data_tech):
    """
    Muestra las señales técnicas actuales
    """
    st.subheader("📊 Señales Técnicas Actuales")
    
    if not data_tech.empty:
        # Obtener el último dato
        ultimo = data_tech.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'RSI' in data_tech.columns:
                rsi_actual = ultimo['RSI']
                st.metric("RSI", f"{rsi_actual:.2f}")
                if rsi_actual > 70:
                    st.error("SOBRECOMPRA 🔴")
                elif rsi_actual < 30:
                    st.success("SOBREVENTA 🟢")
                else:
                    st.info("NEUTRAL 🟡")
        
        with col2:
            if all(col in data_tech.columns for col in ['MACD', 'MACD_Signal']):
                macd_actual = ultimo['MACD']
                signal_actual = ultimo['MACD_Signal']
                st.metric("MACD", f"{macd_actual:.4f}")
                if macd_actual > signal_actual:
                    st.success("ALCISTA 🟢")
                else:
                    st.error("BAJISTA 🔴")
        
        with col3:
            if 'Close' in data_tech.columns and 'SMA_50' in data_tech.columns:
                precio_actual = ultimo['Close']
                sma_50 = ultimo['SMA_50']
                st.metric("Precio vs SMA50", f"${precio_actual:.2f}")
                if precio_actual > sma_50:
                    st.success("POR ENCIMA 🟢")
                else:
                    st.error("POR DEBAJO 🔴")
        
        with col4:
            if all(col in data_tech.columns for col in ['BB_Upper', 'BB_Lower', 'Close']):
                precio_actual = ultimo['Close']
                bb_upper = ultimo['BB_Upper']
                bb_lower = ultimo['BB_Lower']
                st.metric("Bandas Bollinger", f"${precio_actual:.2f}")
                if precio_actual > bb_upper:
                    st.error("SOBRE SUPERIOR 🔴")
                elif precio_actual < bb_lower:
                    st.success("BAJO INFERIOR 🟢")
                else:
                    st.info("DENTRO BANDAS 🟡")

def mostrar_resumen_indicadores(data_tech):
    """
    Muestra un resumen tabular de todos los indicadores
    """
    st.subheader("📈 Resumen de Indicadores")
    
    # Crear DataFrame resumen
    resumen_data = []
    
    if 'RSI' in data_tech.columns:
        rsi_actual = data_tech['RSI'].iloc[-1]
        rsi_señal = "SOBRECOMPRA" if rsi_actual > 70 else "SOBREVENTA" if rsi_actual < 30 else "NEUTRAL"
        resumen_data.append({'Indicador': 'RSI', 'Valor': f"{rsi_actual:.2f}", 'Señal': rsi_señal})
    
    if all(col in data_tech.columns for col in ['MACD', 'MACD_Signal']):
        macd_actual = data_tech['MACD'].iloc[-1]
        signal_actual = data_tech['MACD_Signal'].iloc[-1]
        macd_señal = "ALCISTA" if macd_actual > signal_actual else "BAJISTA"
        resumen_data.append({'Indicador': 'MACD', 'Valor': f"{macd_actual:.4f}", 'Señal': macd_señal})
    
    if all(col in data_tech.columns for col in ['Close', 'SMA_20', 'SMA_50', 'SMA_200']):
        precio_actual = data_tech['Close'].iloc[-1]
        sma_20 = data_tech['SMA_20'].iloc[-1]
        sma_50 = data_tech['SMA_50'].iloc[-1]
        sma_200 = data_tech['SMA_200'].iloc[-1]
        
        # Señal de tendencia basada en medias
        if precio_actual > sma_20 > sma_50 > sma_200:
            tendencia = "FUERTE ALCISTA 🟢"
        elif precio_actual < sma_20 < sma_50 < sma_200:
            tendencia = "FUERTE BAJISTA 🔴"
        else:
            tendencia = "LATERAL 🟡"
        
        resumen_data.append({'Indicador': 'Tendencia Medias', 'Valor': f"${precio_actual:.2f}", 'Señal': tendencia})
    
    if all(col in data_tech.columns for col in ['BB_Upper', 'BB_Lower', 'Close']):
        precio_actual = data_tech['Close'].iloc[-1]
        bb_upper = data_tech['BB_Upper'].iloc[-1]
        bb_lower = data_tech['BB_Lower'].iloc[-1]
        
        if precio_actual > bb_upper:
            bb_señal = "SOBRE SUPERIOR 🔴"
        elif precio_actual < bb_lower:
            bb_señal = "BAJO INFERIOR 🟢"
        else:
            bb_señal = "DENTRO BANDAS 🟡"
        
        resumen_data.append({'Indicador': 'Bandas Bollinger', 'Valor': f"${precio_actual:.2f}", 'Señal': bb_señal})
    
    if resumen_data:
        df_resumen = pd.DataFrame(resumen_data)
        st.dataframe(df_resumen, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar el resumen")

def mostrar_seccion_educativa():
    """
    Muestra la sección educativa sobre indicadores técnicos
    """
    st.subheader("📚 ¿Qué son los Indicadores Técnicos?")
    
    st.markdown("""
    Los **indicadores técnicos** son herramientas matemáticas que se aplican a los precios y volúmenes 
    históricos de un activo para analizar tendencias, identificar posibles puntos de entrada y salida, 
    y predecir movimientos futuros del precio. Se dividen principalmente en:
    
    - **Indicadores de tendencia**: Ayudan a identificar la dirección del mercado
    - **Indicadores de momentum**: Miden la velocidad de los movimientos de precios
    - **Indicadores de volatilidad**: Miden la magnitud de las fluctuaciones del precio
    - **Indicadores de volumen**: Analizan la fuerza detrás de los movimientos de precios
    """)
    
    # EXPANDERS PARA CADA INDICADOR
    st.subheader("🔍 Explicación de Cada Indicador")
    
    with st.expander("📊 RSI (Relative Strength Index)", expanded=False):
        st.markdown("""
        **¿Qué es?**
        - El RSI es un oscilador de momentum que mide la velocidad y el cambio de los movimientos de precios
        - Oscila entre 0 y 100
        
        **¿Para qué sirve?**
        - Identificar condiciones de **sobrecompra** (RSI > 70) y **sobreventa** (RSI < 30)
        - Detectar divergencias que pueden indicar cambios de tendencia
        - Confirmar la fuerza de una tendencia
        
        **Interpretación:**
        - **RSI > 70**: Posible sobrecompra - considerar venta
        - **RSI < 30**: Posible sobreventa - considerar compra
        - **RSI = 50**: Punto de equilibrio
        """)
    
    with st.expander("📈 MACD (Moving Average Convergence Divergence)", expanded=False):
        st.markdown("""
        **¿Qué es?**
        - Indicador de tendencia que muestra la relación entre dos medias móviles exponenciales
        - Se compone de:
          - **Línea MACD**: Diferencia entre EMA 12 y EMA 26
          - **Línea de Señal**: EMA 9 del MACD
          - **Histograma**: Diferencia entre MACD y su línea de señal
        
        **¿Para qué sirve?**
        - Identificar cambios en la dirección y fuerza de la tendencia
        - Generar señales de compra y venta
        - Detectar momentum alcista o bajista
        
        **Señales principales:**
        - **Cruce alcista**: MACD cruza por encima de la línea de señal → COMPRA
        - **Cruce bajista**: MACD cruza por debajo de la línea de señal → VENTA
        - **Divergencias**: Cuando el precio y el MACD no coinciden
        """)
    
    with st.expander("📉 Bandas de Bollinger", expanded=False):
        st.markdown("""
        **¿Qué es?**
        - Indicador de volatilidad que consiste en tres líneas:
          - **Banda media**: SMA 20 (Media Móvil Simple de 20 periodos)
          - **Banda superior**: SMA 20 + (2 × Desviación Estándar)
          - **Banda inferior**: SMA 20 - (2 × Desviación Estándar)
        
        **¿Para qué sirve?**
        - Medir la volatilidad del mercado
        - Identificar niveles de soporte y resistencia dinámicos
        - Detectar condiciones de mercado extremas
        
        **Interpretación:**
        - **Bandas estrechas**: Baja volatilidad (posible breakout próximo)
        - **Bandas anchas**: Alta volatilidad
        - **Precio toca banda superior**: Posible resistencia
        - **Precio toca banda inferior**: Posible soporte
        - **Walk the band**: El precio se mantiene en una banda indicando tendencia fuerte
        """)
    
    with st.expander("📊 Medias Móviles", expanded=False):
        st.markdown("""
        **¿Qué es?**
        - Indicadores que suavizan los datos de precio para identificar la dirección de la tendencia
        - Tipos principales:
          - **SMA (Simple Moving Average)**: Media aritmética simple
          - **EMA (Exponential Moving Average)**: Da más peso a los precios recientes
        
        **¿Para qué sirve?**
        - Identificar la dirección de la tendencia
        - Generar señales de compra y venta mediante cruces
        - Actuar como niveles de soporte y resistencia dinámicos
        
        **Configuraciones comunes:**
        - **SMA 20**: Tendencia a corto plazo
        - **SMA 50**: Tendencia a medio plazo
        - **SMA 200**: Tendencia a largo plazo (tendencia principal)
        
        **Señales importantes:**
        - **Cruce dorado**: SMA 50 cruza por encima de SMA 200 → FUERTE ALCISTA
        - **Cruce de la muerte**: SMA 50 cruza por debajo de SMA 200 → FUERTE BAJISTA
        - **Precio sobre medias**: Tendencia alcista
        - **Precio bajo medias**: Tendencia bajista
        """)

def mostrar_consejos_practicos():
    """
    Muestra consejos prácticos para el uso de indicadores
    """
    st.info("""
    **💡 Consejos Prácticos:**
    - Nunca uses un solo indicador para tomar decisiones
    - Combina múltiples indicadores para confirmar señales
    - Considera el contexto del mercado y las noticias relevantes
    - Los indicadores son herramientas, no garantías de éxito
    - Backtestea tus estrategias antes de implementarlas
    - Considera el timeframe adecuado para tu estilo de trading
    """)

def mostrar_descarga_datos(data_tech, stonk):
    """
    Muestra la opción para descargar los datos técnicos
    """
    st.subheader("💾 Exportar Datos Técnicos")
    
    # Preparar datos para descarga
    columnas_descarga = ['Open', 'High', 'Low', 'Close', 'Volume']
    if 'RSI' in data_tech.columns:
        columnas_descarga.append('RSI')
    if 'MACD' in data_tech.columns:
        columnas_descarga.extend(['MACD', 'MACD_Signal', 'MACD_Histogram'])
    if 'BB_Middle' in data_tech.columns:
        columnas_descarga.extend(['BB_Upper', 'BB_Middle', 'BB_Lower'])
    if 'SMA_20' in data_tech.columns:
        columnas_descarga.extend(['SMA_20', 'SMA_50', 'SMA_200'])
    
    # Filtrar solo las columnas que existen
    columnas_existentes = [col for col in columnas_descarga if col in data_tech.columns]
    datos_descarga = data_tech[columnas_existentes].copy()
    datos_descarga = datos_descarga.reset_index()
    
    csv = datos_descarga.to_csv(index=False)
    
    st.download_button(
        label="📥 Descargar datos técnicos como CSV",
        data=csv,
        file_name=f"{stonk}_datos_tecnicos.csv",
        mime="text/csv",
        use_container_width=True
    )