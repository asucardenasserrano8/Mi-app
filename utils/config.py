"""
Configuración centralizada para la aplicación de análisis de acciones
Contiene todas las variables de entorno, configuraciones y constantes
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# =============================================
# CONFIGURACIÓN DE APIS
# =============================================

# Claves de APIs externas
GOOGLE_KEY = os.getenv("AP")
currencyapi = os.getenv("AP1")
FMP = os.getenv("AP2")  # Financial Modeling Prep
AlphaVantage = os.getenv("AP3")

# Configuración de Google Gemini
GEMINI_MODEL = "gemini-2.5-flash"

# =============================================
# CONFIGURACIÓN DE YAHOO FINANCE
# =============================================

# Períodos de datos
PERIODOS_DISponibles = {
    "1 Mes": 30,
    "3 Meses": 90, 
    "6 Meses": 180,
    "1 Año": 365,
    "3 Años": 3 * 365,
    "5 Años": 5 * 365,
    "Máximo": None
}

# Intervalos de datos
INTERVALOS_DISPONIBLES = {
    "Diario": "1d",
    "Semanal": "1wk",
    "Mensual": "1mo"
}

# =============================================
# CONFIGURACIÓN DE CACHÉ
# =============================================

# Tiempos de caché (en segundos)
CACHE_CONFIG = {
    "datos_precios": 1800,        # 30 minutos
    "datos_fundamentales": 3600,  # 1 hora
    "datos_sp500": 86400,         # 24 horas
    "datos_macro": 10800,         # 3 horas
    "analisis_ia": 1800,          # 30 minutos
    "noticias": 900,              # 15 minutos
    "datos_worldbank": 43200      # 12 horas
}

# Límites de caché
CACHE_LIMITS = {
    "max_entries_precios": 200,
    "max_entries_fundamentales": 100,
    "max_entries_sp500": 50,
    "max_entries_analisis": 30
}

# =============================================
# CONFIGURACIÓN DE RIESGO
# =============================================

# Parámetros para cálculo de métricas de riesgo
PARAMETROS_RIESGO = {
    "periodo_analisis_años": 5,
    "tasa_libre_riesgo_default": 0.02,  # 2%
    "prima_riesgo_mercado_default": 0.06,  # 6%
    "nivel_confianza_var": 0.95,
    "ventana_volatilidad": 252  # días trading anual
}

# Umbrales de alerta de riesgo
UMBRALES_RIESGO = {
    "drawdown_critico": 0.25,    # 25%
    "drawdown_alto": 0.15,       # 15%
    "volatilidad_alta": 0.40,    # 40%
    "volatilidad_elevada": 0.25, # 25%
    "prob_perdida_alta": 55,     # 55%
    "beta_alto": 1.5,
    "var_extremo": 0.30          # 30%
}

# =============================================
# CONFIGURACIÓN DE SCORING
# =============================================

# Ponderaciones para scoring fundamental
PONDERACIONES_SCORING = {
    "pe_ratio": 20,
    "roe": 20,
    "margen_beneficio": 15,
    "deuda_equity": 15,
    "crecimiento_ingresos": 20,
    "beta": 10
}

# Rangos para scoring
RANGOS_SCORING = {
    "pe_ratio": {
        "excelente": 15,
        "bueno": 25,
        "regular": 35
    },
    "roe": {
        "excelente": 0.20,
        "bueno": 0.15,
        "regular": 0.10,
        "minimo": 0.05
    },
    "margen_beneficio": {
        "excelente": 0.20,
        "bueno": 0.15,
        "regular": 0.10,
        "minimo": 0.05
    },
    "deuda_equity": {
        "excelente": 0.5,
        "bueno": 1.0,
        "regular": 1.5,
        "maximo": 2.0
    }
}

# =============================================
# CONFIGURACIÓN DE S&P 500
# =============================================

# Componentes principales del S&P 500 (lista reducida para demo)
SP500_COMPONENTES = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "AVGO", "TSLA", "ADBE",
    "CRM", "CSCO", "ACN", "ORCL", "IBM", "INTC", "AMD", "QCOM", "TXN", "NOW",
    
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "LLY", "DHR", "ABT", "BMY",
    
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "SCHW", "BLK", "AXP", "V", "MA",
    
    # Consumer
    "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "TGT", "BKNG", "ORLY", "AZO",
    
    # Industrials & Others
    "XOM", "CVX", "BRK-B", "WMT", "PG", "KO", "PEP", "COST", "UPS", "CAT"
]

# Sectores del S&P 500
SECTORES_SP500 = {
    "TECHNOLOGY": "Tecnología",
    "HEALTHCARE": "Salud", 
    "FINANCIALS": "Financieros",
    "CONSUMER_DISCRETIONARY": "Consumo Discrecional",
    "CONSUMER_STAPLES": "Consumo Básico",
    "INDUSTRIALS": "Industriales",
    "ENERGY": "Energía",
    "MATERIALS": "Materiales",
    "UTILITIES": "Servicios Públicos",
    "REAL_ESTATE": "Bienes Raíces",
    "COMMUNICATION": "Comunicaciones"
}

# =============================================
# CONFIGURACIÓN DE INDICADORES TÉCNICOS
# =============================================

# Parámetros para indicadores técnicos
PARAMETROS_TECNICOS = {
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "sma_short": 20,
    "sma_medium": 50,
    "sma_long": 200
}

# Umbrales para señales técnicas
UMBRALES_TECNICOS = {
    "rsi_sobrecompra": 70,
    "rsi_sobreventa": 30,
    "rsi_neutral": 50
}

# =============================================
# CONFIGURACIÓN DE INTERFAZ
# =============================================

# Configuración de Streamlit
STREAMLIT_CONFIG = {
    "page_title": "Análisis de Acciones",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# Colores para la interfaz
COLORES_UI = {
    "positivo": "#4CAF50",
    "negativo": "#F44336", 
    "neutral": "#FFC107",
    "primario": "#2196F3",
    "secundario": "#FF9800",
    "fondo_oscuro": "#1E1E1E",
    "fondo_tarjeta": "#2D2D2D",
    "texto_primario": "#FFFFFF",
    "texto_secundario": "#CCCCCC"
}

# Estilos CSS personalizados
CSS_ESTILOS = """
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
"""

# =============================================
# CONFIGURACIÓN DE APIS EXTERNAS
# =============================================

# URLs de APIs
API_URLS = {
    "financial_modeling_prep": "https://financialmodelingprep.com/api/v3/",
    "alpha_vantage": "https://www.alphavantage.co/query",
    "currency_api": "https://api.currencyapi.com/v3/",
    "world_bank": "http://api.worldbank.org/v2/",
    "finviz": "https://finviz.com/quote.ashx",
    "google_news": "https://news.google.com/rss"
}

# Headers para requests
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Timeouts para requests
REQUEST_TIMEOUTS = {
    "short": 5,
    "medium": 10,
    "long": 15
}

# =============================================
# CONFIGURACIÓN DE VALIDACIÓN
# =============================================

# Símbolos válidos para búsqueda
SIMBOLOS_VALIDOS = set(SP500_COMPONENTES)  # Se puede expandir

# Parámetros de validación
VALIDACION_CONFIG = {
    "max_ticker_length": 10,
    "min_ticker_length": 1,
    "allowed_chars": set("ABCDEFGHIJKLMNOPQRSTUVWXYZ.-")
}

# =============================================
# FUNCIONES DE CONFIGURACIÓN
# =============================================

def verificar_configuracion():
    """
    Verifica que todas las configuraciones necesarias estén presentes
    Retorna: (bool, str) - (éxito, mensaje)
    """
    problemas = []
    
    # Verificar APIs
    if not GOOGLE_KEY:
        problemas.append("API de Google Gemini no configurada")
    
    if not FMP and not AlphaVantage:
        problemas.append("No hay APIs de datos financieros configuradas")
    
    # Verificar configuraciones críticas
    if not SP500_COMPONENTES:
        problemas.append("Lista de componentes S&P 500 vacía")
    
    if not any([period for period in PERIODOS_DISponibles.values() if period]):
        problemas.append("Configuración de períodos inválida")
    
    if problemas:
        return False, " | ".join(problemas)
    
    return True, "Configuración OK"

def obtener_configuracion_completa():
    """
    Retorna un diccionario con toda la configuración
    Útil para debugging
    """
    return {
        "apis_configuradas": {
            "google_gemini": bool(GOOGLE_KEY),
            "financial_modeling_prep": bool(FMP),
            "alpha_vantage": bool(AlphaVantage),
            "currency_api": bool(currencyapi)
        },
        "cache_config": CACHE_CONFIG,
        "sp500_componentes": len(SP500_COMPONENTES),
        "parametros_riesgo": PARAMETROS_RIESGO,
        "periodos_disponibles": list(PERIODOS_DISponibles.keys())
    }

# =============================================
# INICIALIZACIÓN
# =============================================

# Verificar configuración al importar
config_ok, mensaje_config = verificar_configuracion()
if not config_ok:
    print(f"⚠️ Advertencia de configuración: {mensaje_config}")
else:
    print("✅ Configuración cargada correctamente")