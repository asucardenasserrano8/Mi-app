# app.py - ARCHIVO PRINCIPAL REDUCIDO
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Importar todas las secciones
from sections import (
    inicio, informacion, variacion_precio, datos_fundamentales,
    analisis_tecnico, analisis_ia, analisis_riesgo, comparacion,
    noticias, screener, macroeconomia, mercados_globales
)

# Cargar variables de entorno
load_dotenv()

# Configuración de la página (debe ser lo primero)
st.set_page_config(
    page_title="Análisis de Acciones", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de APIs
GOOGLE_KEY = os.getenv("AP")
if GOOGLE_KEY:
    genai.configure(api_key=GOOGLE_KEY)

# CSS personalizado mejorado
st.markdown("""
<style>
    /* Estilos para botones seleccionados */
    .stButton > button {
        border: 2px solid #cccccc;
        background-color: white;
        color: black;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        border-color: #adb5bd;
        background-color: #f8f9fa;
    }
    
    /* Botón seleccionado */
    .stButton > button.selected {
        border: 3px solid #28a745 !important;
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
    }
    
    /* Indicadores de métricas */
    .metric-positive {
        color: #28a745;
        font-weight: bold;
    }
    
    .metric-negative {
        color: #dc3545;
        font-weight: bold;
    }
    
    .metric-neutral {
        color: #ffc107;
        font-weight: bold;
    }
    
    /* Tarjetas de información */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    
    /* Estilos para educación financiera */
    .concept-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        border-left: 5px solid #ff6b6b;
    }
    
    .macro-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 5px 0;
    }
    
    /* Estilos para análisis de IA */
    .ia-analysis {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        border-left: 5px solid #28a745;
    }
    
    .ia-recommendation {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin: 8px 0;
        border-left: 4px solid #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de session_state
def inicializar_session_state():
    """Inicializa todas las variables de session_state"""
    if 'seccion_actual' not in st.session_state:
        st.session_state.seccion_actual = "inicio"
    
    if 'favoritas' not in st.session_state:
        st.session_state.favoritas = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    if 'portafolio' not in st.session_state:
        st.session_state.portafolio = {}
    
    if 'historial_busquedas' not in st.session_state:
        st.session_state.historial_busquedas = []
    
    if 'cache_lock' not in st.session_state:
        st.session_state.cache_lock = st.empty()

# Función para obtener datos básicos de la acción
@st.cache_data(ttl=300, show_spinner=False)
def obtener_datos_basicos(ticker):
    """Obtiene datos básicos de la acción"""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        datos = yf.download(ticker, period="1mo", progress=False)
        
        return {
            'ticker': ticker,
            'info': info,
            'datos': datos,
            'nombre': info.get("longName", "Empresa no encontrada"),
            'descripcion': info.get("longBusinessSummary", "No hay descripción disponible")
        }
    except Exception as e:
        st.error(f"Error al cargar datos de {ticker}: {str(e)}")
        return None

# Función principal de la aplicación
def main():
    """Función principal de la aplicación"""
    inicializar_session_state()
    
    # Sidebar para búsqueda y controles
    with st.sidebar:
        st.header("🔍 Búsqueda de Acciones")
        
        # Input para buscar acción
        stonk = st.text_input(
            "Ingrese el símbolo de la acción", 
            value="MSFT",
            help="Ejemplos: AAPL, MSFT, TSLA, GOOGL, AMZN"
        )
        
        # Agregar a historial de búsquedas
        if stonk and stonk not in st.session_state.historial_busquedas:
            st.session_state.historial_busquedas.append(stonk)
            if len(st.session_state.historial_busquedas) > 10:
                st.session_state.historial_busquedas.pop(0)
        
        # Favoritos rápidos
        st.markdown("---")
        st.subheader("⭐ Favoritos")
        cols_fav = st.columns(2)
        for i, favorita in enumerate(st.session_state.favoritas):
            with cols_fav[i % 2]:
                if st.button(favorita, use_container_width=True, key=f"fav_sidebar_{favorita}"):
                    st.session_state.seccion_actual = "informacion"
                    st.rerun()
        
        # Historial de búsquedas
        if st.session_state.historial_busquedas:
            st.markdown("---")
            st.subheader("📚 Historial")
            for busqueda in reversed(st.session_state.historial_busquedas[-5:]):
                if st.button(busqueda, use_container_width=True, key=f"hist_sidebar_{busqueda}"):
                    st.session_state.seccion_actual = "informacion"
                    st.rerun()
        
        # Información del sistema
        st.markdown("---")
        st.markdown("""
        **ℹ️ Acerca de:**
        - Análisis técnico y fundamental
        - Datos en tiempo real
        - Comparación de acciones
        - Screener S&P 500
        - Mercados globales
        """)
    
    # Obtener datos básicos de la acción
    datos_accion = obtener_datos_basicos(stonk)
    
    # Header principal
    if datos_accion:
        st.header(f"📊 Análisis de {datos_accion['nombre']} ({stonk})")
    else:
        st.header("📊 Análisis de Acciones")
        st.warning("No se pudieron cargar los datos de la acción. Verifica el símbolo.")
        return
    
    # BARRA DE NAVEGACIÓN MEJORADA
    st.markdown("### 🧭 Navegación Rápida")
    
    # Primera fila: 5 botones principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🏠 Inicio", use_container_width=True, 
                    type="primary" if st.session_state.seccion_actual == "inicio" else "secondary"):
            st.session_state.seccion_actual = "inicio"
            st.rerun()

    with col2:
        if st.button("🏢 Información", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "informacion" else "secondary"):
            st.session_state.seccion_actual = "informacion"
            st.rerun()

    with col3:    
        if st.button("📈 Variación Precio", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "variacion" else "secondary"):
            st.session_state.seccion_actual = "variacion"
            st.rerun()

    with col4:
        if st.button("💰 Fundamentales", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "fundamentales" else "secondary"):
            st.session_state.seccion_actual = "fundamentales"
            st.rerun()

    with col5:
        if st.button("📊 Análisis Técnico", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "tecnico" else "secondary"):
            st.session_state.seccion_actual = "tecnico"
            st.rerun()

    # Segunda fila: 4 botones
    col6, col7, col8, col9 = st.columns(4)

    with col6:
        if st.button("🤖 Análisis IA", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "ia" else "secondary"):
            st.session_state.seccion_actual = "ia"
            st.rerun()

    with col7:
        if st.button("⚠️ Análisis Riesgo", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "riesgo" else "secondary"):
            st.session_state.seccion_actual = "riesgo"
            st.rerun()

    with col8:
        if st.button("📊 Comparación", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "comparacion" else "secondary"):
            st.session_state.seccion_actual = "comparacion"
            st.rerun()

    with col9:
        if st.button("📰 Noticias", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "noticias" else "secondary"):
            st.session_state.seccion_actual = "noticias"
            st.rerun()

    # Tercera fila: 3 botones
    col10, col11, col12 = st.columns(3)

    with col10:
        if st.button("🔍 Buscador", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "screener" else "secondary"):
            st.session_state.seccion_actual = "screener"
            st.rerun()

    with col11:
        if st.button("🌍 Macroeconomía", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "macro" else "secondary"):
            st.session_state.seccion_actual = "macro"
            st.rerun()

    with col12:
        if st.button("📈 Mercados Globales", use_container_width=True,
                    type="primary" if st.session_state.seccion_actual == "global" else "secondary"):
            st.session_state.seccion_actual = "global"
            st.rerun()

    # Línea separadora
    st.markdown("---")
    
    # RUTEO A SECCIONES
    if datos_accion:
        if st.session_state.seccion_actual == "inicio":
            inicio.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "informacion":
            informacion.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "variacion":
            variacion_precio.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "fundamentales":
            datos_fundamentales.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "tecnico":
            analisis_tecnico.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "ia":
            analisis_ia.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "riesgo":
            analisis_riesgo.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "comparacion":
            comparacion.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "noticias":
            noticias.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "screener":
            screener.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "macro":
            macroeconomia.mostrar(datos_accion)
            
        elif st.session_state.seccion_actual == "global":
            mercados_globales.mostrar(datos_accion)
    
    # FOOTER Y CONTROLES ADICIONALES
    st.markdown("---")
    
    # Botones de utilidad en el footer
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if st.button("🔄 Limpiar Caché", use_container_width=True, type="secondary"):
            st.cache_data.clear()
            st.success("✅ Caché limpiado correctamente")
            st.rerun()
    
    with col_f2:
        if st.button("📄 Generar Reporte", use_container_width=True, type="secondary"):
            st.info("📋 Función de reporte disponible en cada sección")
    
    with col_f3:
        if st.button("ℹ️ Ayuda", use_container_width=True, type="secondary"):
            st.info("""
            **Guía rápida:**
            - **🏠 Inicio**: Vista general del mercado
            - **🏢 Información**: Datos básicos de la empresa
            - **📈 Variación**: Gráficas de precios históricos
            - **💰 Fundamentales**: Métricas financieras
            - **📊 Técnico**: Indicadores técnicos
            - **🤖 IA**: Análisis con inteligencia artificial
            - **⚠️ Riesgo**: Métricas de riesgo avanzadas
            - **📊 Comparación**: Comparar múltiples acciones
            - **📰 Noticias**: Noticias relevantes
            - **🔍 Buscador**: Filtrar acciones del S&P 500
            - **🌍 Macroeconomía**: Datos económicos por país
            - **📈 Globales**: Mercados internacionales
            """)
    
    # Disclaimer final
    st.markdown("""
    ---
    <p style='text-align: center; font-size: 13px; color: gray;'>
    © 2025 Todos los derechos reservados. Desarrollado por <strong>Jesús Alberto Cárdenas Serrano.</strong>
    <br><em>Esta aplicación es con fines educativos. No constituye asesoramiento financiero.</em>
    </p>
    """, unsafe_allow_html=True)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()