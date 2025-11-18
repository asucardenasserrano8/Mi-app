# sections/variacion_precio.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.technical_analysis import analizar_tendencias, calcular_indicadores_tecnicos

def mostrar_seccion_variacion_precio(datos_accion):
    """
    Muestra la sección de variación del precio y gráficas
    Versión modificada para aceptar el diccionario datos_accion de app.py
    """
    # Extraer los datos del diccionario
    stonk = datos_accion['ticker']
    info = datos_accion['info']
    nombre = info.get("longName", stonk)
    
    st.header(f"📊 Variación del Precio y Gráfica de Velas de {nombre}")
    
    # Configuración de fechas
    end_date = datetime.today()
    start_date_default = end_date - timedelta(days=5 * 365)
    
    try:
        # Descargar datos iniciales
        data = _descargar_datos_accion(stonk, start_date_default, end_date)
        
        if data.empty:
            st.warning("No se encontraron datos para este símbolo")
            return
        
        # Mostrar métricas de precio
        _mostrar_metricas_precio(data, stonk)
        
        # Selector de período
        periodo_seleccionado, data_periodo = _mostrar_selector_periodo(stonk, end_date)
        
        if not data_periodo.empty:
            # Mostrar gráfica de velas
            _mostrar_grafica_velas(data_periodo, stonk, periodo_seleccionado)
            
            # Mostrar detector de tendencias
            _mostrar_detector_tendencias(data_periodo)
            
            # Mostrar tabla de datos históricos
            _mostrar_tabla_datos(data_periodo, periodo_seleccionado)
            
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")

def _descargar_datos_accion(ticker, start_date, end_date):
    """
    Descarga datos de la acción y limpia las columnas
    """
    try:
        data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), 
                          end=end_date.strftime('%Y-%m-%d'), interval='1d')
        
        if data.empty:
            return pd.DataFrame()
        
        # Limpiar nombres de columnas
        data = data.reset_index()
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col 
                           for col in data.columns.values]
        
        data.columns = [col.replace(f'_{ticker}', '') for col in data.columns]
        
        return data
        
    except Exception as e:
        st.error(f"Error descargando datos: {str(e)}")
        return pd.DataFrame()

def _mostrar_metricas_precio(data, ticker):
    """
    Muestra las métricas principales de precio
    """
    st.subheader(f"📊 Métricas de Precio - Período Actual")
    
    if 'Close' not in data.columns:
        st.warning("No se encontraron datos de precio válidos")
        return
    
    # Calcular métricas
    precio_actual = data['Close'].iloc[-1]
    precio_inicial = data['Close'].iloc[0]
    variacion_total = ((precio_actual - precio_inicial) / precio_inicial) * 100
    
    # Calcular variación del último día
    if len(data) > 1:
        precio_anterior = data['Close'].iloc[-2]
        variacion_diaria = ((precio_actual - precio_anterior) / precio_anterior) * 100
    else:
        variacion_diaria = 0
    
    # Calcular máximo y mínimo del período
    precio_maximo = data['Close'].max()
    precio_minimo = data['Close'].min()
    
    # Calcular volatilidad (desviación estándar de los retornos diarios)
    retornos_diarios = data['Close'].pct_change().dropna()
    volatilidad = retornos_diarios.std() * 100  # En porcentaje
    
    # Mostrar métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Precio Inicial", f"${precio_inicial:.2f}")
        st.metric("Precio Mínimo", f"${precio_minimo:.2f}")
    
    with col2:
        st.metric("Precio Actual", f"${precio_actual:.2f}", f"{variacion_diaria:.2f}%")
        st.metric("Precio Máximo", f"${precio_maximo:.2f}")
    
    with col3:
        st.metric("Variación Total", f"{variacion_total:.2f}%")
        st.metric("Volatilidad Anual", f"{volatilidad:.2f}%")
    
    with col4:
        st.metric("Período", "5 Años")
        st.metric("Días Analizados", len(data))

def _mostrar_selector_periodo(ticker, end_date):
    """
    Muestra el selector de período y descarga los datos correspondientes
    """
    st.subheader("📅 Selecciona el período de análisis")
    
    periodo_opciones = {
        "1 Mes": 30,
        "3 Meses": 90,
        "6 Meses": 180,
        "1 Año": 365,
        "3 Años": 3 * 365,
        "5 Años": 5 * 365,
        "Máximo": None  # Para datos máximos disponibles
    }
    
    periodo_seleccionado = st.selectbox(
        "Período:",
        options=list(periodo_opciones.keys()),
        index=5,  # 5 Años por defecto
        key="selector_periodo_variacion"
    )
    
    # Calcular fecha de inicio según el período seleccionado
    if periodo_opciones[periodo_seleccionado] is None:
        # Para período máximo, usar una fecha muy antigua
        start_date = datetime(2000, 1, 1)
        periodo_texto = "Máximo"
    else:
        start_date = end_date - timedelta(days=periodo_opciones[periodo_seleccionado])
        periodo_texto = periodo_seleccionado
    
    # Descargar datos del período seleccionado
    data_periodo = _descargar_datos_accion(ticker, start_date, end_date)
    
    return periodo_texto, data_periodo

def _mostrar_grafica_velas(data, ticker, periodo):
    """
    Muestra la gráfica de velas para el período seleccionado
    """
    st.markdown("---")
    st.subheader(f"📈 Gráfica de Velas - Período: {periodo}")
    
    # Obtener nombres de columnas
    open_col = _obtener_nombre_columna(data, 'Open')
    high_col = _obtener_nombre_columna(data, 'High') 
    low_col = _obtener_nombre_columna(data, 'Low')
    close_col = _obtener_nombre_columna(data, 'Close')
    date_col = _obtener_nombre_columna(data, 'Date')
    
    # Verificar que tenemos todas las columnas necesarias
    if not all(col is not None for col in [open_col, high_col, low_col, close_col, date_col]):
        st.warning("No se pudieron cargar los datos necesarios para la gráfica de velas")
        return
    
    # Crear gráfica de velas
    fig = go.Figure(data=[go.Candlestick(
        x=data[date_col],
        open=data[open_col],
        high=data[high_col],
        low=data[low_col],
        close=data[close_col],
        increasing_line_color='#26a69a',  # Verde para velas alcistas
        decreasing_line_color='#ef5350',  # Rojo para velas bajistas
        increasing_fillcolor='#26a69a',
        decreasing_fillcolor='#ef5350',
        name=ticker,
        hoverinfo='x+y+name'
    )])
    
    # Personalizar el layout
    fig.update_layout(
        title=dict(
            text=f'Gráfica de Velas - {ticker} ({periodo})',
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='white')
        ),
        xaxis_title='Fecha',
        yaxis_title='Precio (USD)',
        xaxis_rangeslider_visible=False,
        height=600,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.3)',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.3)',
            showgrid=True
        )
    )
    
    # Configuraciones adicionales del eje x
    fig.update_xaxes(
        tickformat='%b %Y',
        tickangle=45,
        nticks=12
    )
    
    st.plotly_chart(fig, use_container_width=True)

def _obtener_nombre_columna(data, prefix):
    """
    Obtiene el nombre de columna que coincide con el prefijo
    """
    for col in data.columns:
        if col.startswith(prefix):
            return col
    return None

def _mostrar_detector_tendencias(data):
    """
    Muestra el análisis de tendencias
    """
    st.markdown("---")
    st.subheader("🔍 Detector de Tendencias")
    
    # Analizar tendencias
    analisis_tendencia = analizar_tendencias(data)
    
    # Mostrar resultados en columnas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Indicador de tendencia con color
        tendencia = analisis_tendencia["tendencia"]
        confianza = analisis_tendencia["confianza"]
        
        if tendencia == "ALCISTA":
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #00b09b, #96c93d); '
                f'padding: 20px; border-radius: 10px; text-align: center; color: white;">'
                f'<h3>📈 {tendencia}</h3>'
                f'<p>Confianza: {confianza}%</p>'
                f'</div>', 
                unsafe_allow_html=True
            )
        elif tendencia == "BAJISTA":
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #ff416c, #ff4b2b); '
                f'padding: 20px; border-radius: 10px; text-align: center; color: white;">'
                f'<h3>📉 {tendencia}</h3>'
                f'<p>Confianza: {confianza}%</p>'
                f'</div>', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #ffb347, #ffcc33); '
                f'padding: 20px; border-radius: 10px; text-align: center; color: white;">'
                f'<h3>➡️ {tendencia}</h3>'
                f'<p>Confianza: {confianza}%</p>'
                f'</div>', 
                unsafe_allow_html=True
            )
    
    with col2:
        # Métricas de precio y RSI
        if 'detalles' in analisis_tendencia:
            detalles = analisis_tendencia['detalles']
            
            if 'precio_actual' in detalles:
                st.metric("Precio Actual", f"${detalles['precio_actual']:.2f}")
            
            if 'rsi' in detalles:
                rsi_valor = detalles['rsi']
                rsi_color = "#26a69a" if rsi_valor < 30 else "#ef5350" if rsi_valor > 70 else "#ffa726"
                rsi_estado = "Sobreventa" if rsi_valor < 30 else "Sobrecompra" if rsi_valor > 70 else "Neutral"
                
                st.metric(
                    "RSI (14)", 
                    f"{rsi_valor:.1f}",
                    delta=rsi_estado,
                    delta_color="off" if rsi_estado == "Neutral" else "inverse"
                )
    
    with col3:
        # Medias móviles
        if 'detalles' in analisis_tendencia:
            detalles = analisis_tendencia['detalles']
            
            if all(key in detalles for key in ['sma_20', 'sma_50', 'sma_200']):
                st.write("**📊 Medias Móviles:**")
                
                precio_actual = detalles.get('precio_actual', 0)
                
                # SMA 20
                sma_20 = detalles['sma_20']
                sma_20_color = "#26a69a" if precio_actual > sma_20 else "#ef5350"
                st.write(f"<span style='color: {sma_20_color}'>• SMA 20: ${sma_20:.2f}</span>", 
                        unsafe_allow_html=True)
                
                # SMA 50
                sma_50 = detalles['sma_50']
                sma_50_color = "#26a69a" if precio_actual > sma_50 else "#ef5350"
                st.write(f"<span style='color: {sma_50_color}'>• SMA 50: ${sma_50:.2f}</span>", 
                        unsafe_allow_html=True)
                
                # SMA 200
                sma_200 = detalles['sma_200']
                sma_200_color = "#26a69a" if precio_actual > sma_200 else "#ef5350"
                st.write(f"<span style='color: {sma_200_color}'>• SMA 200: ${sma_200:.2f}</span>", 
                        unsafe_allow_html=True)
    
    # Explicación de la tendencia
    with st.expander("📖 Explicación del Análisis de Tendencia"):
        st.markdown("""
        **🔍 Cómo se determina la tendencia:**
        
        - **📈 Medias Móviles (40%):** Analiza la posición del precio respecto a las medias de 20, 50 y 200 días
        - **⚖️ Posición Precio/Medias (30%):** Evalúa si el precio está por encima o debajo de las medias clave
        - **💪 Momentum RSI (30%):** Considera si el RSI indica fuerza compradora o vendedora
        
        **🎯 Interpretación:**
        
        - 🟢 **ALCISTA:** Precio por encima de medias, RSI >50, medias alineadas ascendente
        - 🔴 **BAJISTA:** Precio por debajo de medias, RSI <50, medias alineadas descendente  
        - 🟡 **LATERAL:** Señales mixtas o sin dirección clara
        
        **📊 Niveles RSI:**
        - **< 30:** Sobreventa (posible rebote alcista)
        - **30-70:** Zona neutral
        - **> 70:** Sobrecompra (posible corrección)
        """)

def _mostrar_tabla_datos(data, periodo):
    """
    Muestra la tabla de datos históricos
    """
    st.markdown("---")
    st.subheader(f"📋 Datos Históricos - Período: {periodo}")
    
    # Obtener columna de fecha
    date_col = _obtener_nombre_columna(data, 'Date')
    
    # Mostrar información resumida
    st.write(f"**Total de registros:** {len(data)} días")
    
    if date_col and len(data) > 0:
        fecha_inicio = data[date_col].iloc[0]
        fecha_fin = data[date_col].iloc[-1]
        
        if hasattr(fecha_inicio, 'strftime'):
            fecha_inicio_str = fecha_inicio.strftime('%d/%m/%Y')
            fecha_fin_str = fecha_fin.strftime('%d/%m/%Y')
            st.write(f"**Período:** {fecha_inicio_str} - {fecha_fin_str}")
    
    # Preparar datos para mostrar
    datos_mostrar = data.copy()
    
    # Formatear columnas numéricas
    columnas_numericas = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    for col in columnas_numericas:
        col_name = _obtener_nombre_columna(data, col)
        if col_name and col_name in datos_mostrar.columns:
            if col == 'Volume':
                # Formatear volumen con separadores de miles
                datos_mostrar[col_name] = datos_mostrar[col_name].apply(
                    lambda x: f"{x:,.0f}" if pd.notnull(x) else ""
                )
            else:
                # Formatear precios con 2 decimales
                datos_mostrar[col_name] = datos_mostrar[col_name].apply(
                    lambda x: f"${x:.2f}" if pd.notnull(x) else ""
                )
    
    # Ordenar por fecha descendente (más reciente primero)
    if date_col and date_col in datos_mostrar.columns:
        datos_mostrar = datos_mostrar.sort_values(date_col, ascending=False)
    
    # Mostrar tabla con configuración
    st.dataframe(
        datos_mostrar,
        use_container_width=True,
        height=400
    )
    
    # Botones de exportación
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Descargar CSV", use_container_width=True):
            _descargar_csv(data, periodo)
    
    with col2:
        if st.button("📊 Descargar Excel", use_container_width=True):
            _descargar_excel(data, periodo)

def _descargar_csv(data, periodo):
    """
    Genera y descarga los datos en formato CSV
    """
    try:
        csv = data.to_csv(index=False)
        st.download_button(
            label="⬇️ Descargar CSV",
            data=csv,
            file_name=f"datos_historicos_{periodo.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generando CSV: {str(e)}")

def _descargar_excel(data, periodo):
    """
    Genera y descarga los datos en formato Excel
    """
    try:
        # Usar BytesIO para crear el archivo en memoria
        output = data.to_excel(index=False, engine='openpyxl')
        st.download_button(
            label="⬇️ Descargar Excel",
            data=output,
            file_name=f"datos_historicos_{periodo.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generando Excel: {str(e)}")

# Alias para compatibilidad con App.py
mostrar = mostrar_seccion_variacion_precio

# Función principal para testing
if __name__ == "__main__":
    st.title("🔍 Prueba - Sección Variación de Precio")
    
    # Ejemplo de prueba - crear el diccionario como lo hace app.py
    ticker_symbol = "MSFT"
    ticker_obj = yf.Ticker(ticker_symbol)
    info_data = ticker_obj.info
    
    datos_accion = {
        'ticker': ticker_symbol,
        'info': info_data,
        'datos': yf.download(ticker_symbol, period="1mo", progress=False),
        'nombre': info_data.get("longName", "Empresa no encontrada"),
        'descripcion': info_data.get("longBusinessSummary", "No hay descripción disponible")
    }
    
    mostrar_seccion_variacion_precio(datos_accion)