# utils/technical_analysis.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def calcular_indicadores_tecnicos(data):
    """
    Calcula indicadores técnicos para los datos proporcionados
    """
    if data.empty:
        return data
    
    # Crear una copia para no modificar el original
    data_tech = data.copy()
    
    # Asegurarnos de que tenemos la columna Close
    if 'Close' not in data_tech.columns:
        st.error("No se encuentra la columna 'Close' en los datos")
        return data_tech
    
    try:
        # RSI (Relative Strength Index)
        data_tech = _calcular_rsi(data_tech)
        
        # MACD (Moving Average Convergence Divergence)
        data_tech = _calcular_macd(data_tech)
        
        # Bandas de Bollinger
        data_tech = _calcular_bandas_bollinger(data_tech)
        
        # Medias Móviles
        data_tech = _calcular_medias_moviles(data_tech)
        
        return data_tech
        
    except Exception as e:
        st.error(f"Error calculando indicadores técnicos: {str(e)}")
        return data_tech

def _calcular_rsi(data, window=14):
    """
    Calcula el RSI (Relative Strength Index)
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    delta = data[close_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    return data

def _calcular_macd(data, fast=12, slow=26, signal=9):
    """
    Calcula el MACD (Moving Average Convergence Divergence)
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    exp_fast = data[close_col].ewm(span=fast, adjust=False).mean()
    exp_slow = data[close_col].ewm(span=slow, adjust=False).mean()
    
    data['MACD'] = exp_fast - exp_slow
    data['MACD_Signal'] = data['MACD'].ewm(span=signal, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
    
    return data

def _calcular_bandas_bollinger(data, window=20, num_std=2):
    """
    Calcula las Bandas de Bollinger
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    data['BB_Middle'] = data[close_col].rolling(window=window).mean()
    bb_std = data[close_col].rolling(window=window).std()
    data['BB_Upper'] = data['BB_Middle'] + (bb_std * num_std)
    data['BB_Lower'] = data['BB_Middle'] - (bb_std * num_std)
    data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']
    
    return data

def _calcular_medias_moviles(data):
    """
    Calcula varias medias móviles
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    # Medias móviles simples
    data['SMA_20'] = data[close_col].rolling(window=20).mean()
    data['SMA_50'] = data[close_col].rolling(window=50).mean()
    data['SMA_200'] = data[close_col].rolling(window=200).mean()
    
    # Medias móviles exponenciales
    data['EMA_12'] = data[close_col].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data[close_col].ewm(span=26, adjust=False).mean()
    
    return data

def analizar_tendencias(data):
    """
    Analiza la tendencia del precio basado en múltiples indicadores
    """
    if data.empty or 'Close' not in data.columns:
        return {"tendencia": "No disponible", "confianza": 0, "detalles": {}}
    
    try:
        # Calcular medias móviles si no existen
        if 'SMA_20' not in data.columns:
            data = _calcular_medias_moviles(data)
        
        if 'RSI' not in data.columns:
            data = _calcular_rsi(data)
        
        # Obtener últimos valores
        precio_actual = data['Close'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1] if 'SMA_20' in data.columns else precio_actual
        sma_50 = data['SMA_50'].iloc[-1] if 'SMA_50' in data.columns else precio_actual
        sma_200 = data['SMA_200'].iloc[-1] if 'SMA_200' in data.columns else precio_actual
        rsi_actual = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
        
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
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
            
        if precio_actual > sma_50:
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
            
        if precio_actual > sma_200:
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
        
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

def _obtener_nombre_columna(data, prefix):
    """
    Obtiene el nombre de columna que coincide con el prefijo
    """
    for col in data.columns:
        if col.startswith(prefix):
            return col
    return None

def generar_senales_tecnicas(data):
    """
    Genera señales técnicas basadas en múltiples indicadores
    """
    if data.empty or 'Close' not in data.columns:
        return {"senales": [], "resumen": "No hay datos suficientes"}
    
    try:
        # Calcular todos los indicadores
        data = calcular_indicadores_tecnicos(data)
        
        senales = []
        
        # Señal RSI
        if 'RSI' in data.columns:
            rsi_actual = data['RSI'].iloc[-1]
            if rsi_actual < 30:
                senales.append({"indicador": "RSI", "senal": "COMPRA", "fuerza": "FUERTE", 
                              "descripcion": f"RSI en {rsi_actual:.1f} - Zona de sobreventa"})
            elif rsi_actual > 70:
                senales.append({"indicador": "RSI", "senal": "VENTA", "fuerza": "FUERTE",
                              "descripcion": f"RSI en {rsi_actual:.1f} - Zona de sobrecompra"})
        
        # Señal MACD
        if all(col in data.columns for col in ['MACD', 'MACD_Signal']):
            macd_actual = data['MACD'].iloc[-1]
            signal_actual = data['MACD_Signal'].iloc[-1]
            macd_anterior = data['MACD'].iloc[-2] if len(data) > 1 else macd_actual
            
            if macd_actual > signal_actual and macd_anterior <= signal_actual:
                senales.append({"indicador": "MACD", "senal": "COMPRA", "fuerza": "MEDIA",
                              "descripcion": "MACD cruza por encima de la línea de señal"})
            elif macd_actual < signal_actual and macd_anterior >= signal_actual:
                senales.append({"indicador": "MACD", "senal": "VENTA", "fuerza": "MEDIA",
                              "descripcion": "MACD cruza por debajo de la línea de señal"})
        
        # Señal Bandas de Bollinger
        if all(col in data.columns for col in ['Close', 'BB_Upper', 'BB_Lower']):
            precio_actual = data['Close'].iloc[-1]
            bb_upper = data['BB_Upper'].iloc[-1]
            bb_lower = data['BB_Lower'].iloc[-1]
            
            if precio_actual <= bb_lower:
                senales.append({"indicador": "Bollinger", "senal": "COMPRA", "fuerza": "MEDIA",
                              "descripcion": "Precio toca banda inferior - Posible rebote"})
            elif precio_actual >= bb_upper:
                senales.append({"indicador": "Bollinger", "senal": "VENTA", "fuerza": "MEDIA",
                              "descripcion": "Precio toca banda superior - Posible corrección"})
        
        # Resumen de señales
        compras = sum(1 for s in senales if s['senal'] == 'COMPRA')
        ventas = sum(1 for s in senales if s['senal'] == 'VENTA')
        
        if compras > ventas:
            resumen = "TENDENCIA ALCISTA"
        elif ventas > compras:
            resumen = "TENDENCIA BAJISTA"
        else:
            resumen = "TENDENCIA NEUTRAL"
        
        return {
            "senales": senales,
            "resumen": resumen,
            "total_compras": compras,
            "total_ventas": ventas
        }
        
    except Exception as e:
        return {"senales": [], "resumen": f"Error: {str(e)}"}

# Función para testing
if __name__ == "__main__":
    # Probar las funciones
    import yfinance as yf
    from datetime import datetime, timedelta
    
    st.title("🔍 Prueba - Análisis Técnico")
    
    # Descargar datos de prueba
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    data = yf.download("AAPL", start=start_date, end=end_date)
    data = data.reset_index()
    
    st.subheader("Datos Originales")
    st.write(data.head())
    
    st.subheader("Indicadores Técnicos")
    data_tech = calcular_indicadores_tecnicos(data)
    st.write(data_tech.tail())
    
    st.subheader("Análisis de Tendencia")
    tendencia = analizar_tendencias(data_tech)
    st.write(tendencia)
    
    st.subheader("Señales Técnicas")
    senales = generar_senales_tecnicas(data_tech)
    st.write(senales)

# utils/technical_analysis.py
import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def calcular_indicadores_tecnicos(data):
    """
    Calcula indicadores técnicos para los datos proporcionados
    """
    if data.empty:
        return data
    
    # Crear una copia para no modificar el original
    data_tech = data.copy()
    
    # Asegurarnos de que tenemos la columna Close
    if 'Close' not in data_tech.columns:
        st.error("No se encuentra la columna 'Close' en los datos")
        return data_tech
    
    try:
        # RSI (Relative Strength Index)
        data_tech = _calcular_rsi(data_tech)
        
        # MACD (Moving Average Convergence Divergence)
        data_tech = _calcular_macd(data_tech)
        
        # Bandas de Bollinger
        data_tech = _calcular_bandas_bollinger(data_tech)
        
        # Medias Móviles
        data_tech = _calcular_medias_moviles(data_tech)
        
        return data_tech
        
    except Exception as e:
        st.error(f"Error calculando indicadores técnicos: {str(e)}")
        return data_tech

def _calcular_rsi(data, window=14):
    """
    Calcula el RSI (Relative Strength Index)
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    delta = data[close_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    return data

def _calcular_macd(data, fast=12, slow=26, signal=9):
    """
    Calcula el MACD (Moving Average Convergence Divergence)
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    exp_fast = data[close_col].ewm(span=fast, adjust=False).mean()
    exp_slow = data[close_col].ewm(span=slow, adjust=False).mean()
    
    data['MACD'] = exp_fast - exp_slow
    data['MACD_Signal'] = data['MACD'].ewm(span=signal, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
    
    return data

def _calcular_bandas_bollinger(data, window=20, num_std=2):
    """
    Calcula las Bandas de Bollinger
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    data['BB_Middle'] = data[close_col].rolling(window=window).mean()
    bb_std = data[close_col].rolling(window=window).std()
    data['BB_Upper'] = data['BB_Middle'] + (bb_std * num_std)
    data['BB_Lower'] = data['BB_Middle'] - (bb_std * num_std)
    data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']
    
    return data

def _calcular_medias_moviles(data):
    """
    Calcula varias medias móviles
    """
    close_col = _obtener_nombre_columna(data, 'Close')
    if close_col is None:
        return data
    
    # Medias móviles simples
    data['SMA_20'] = data[close_col].rolling(window=20).mean()
    data['SMA_50'] = data[close_col].rolling(window=50).mean()
    data['SMA_200'] = data[close_col].rolling(window=200).mean()
    
    # Medias móviles exponenciales
    data['EMA_12'] = data[close_col].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data[close_col].ewm(span=26, adjust=False).mean()
    
    return data

def analizar_tendencias(data):
    """
    Analiza la tendencia del precio basado en múltiples indicadores
    """
    if data.empty or 'Close' not in data.columns:
        return {"tendencia": "No disponible", "confianza": 0, "detalles": {}}
    
    try:
        # Calcular medias móviles si no existen
        if 'SMA_20' not in data.columns:
            data = _calcular_medias_moviles(data)
        
        if 'RSI' not in data.columns:
            data = _calcular_rsi(data)
        
        # Obtener últimos valores
        precio_actual = data['Close'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1] if 'SMA_20' in data.columns else precio_actual
        sma_50 = data['SMA_50'].iloc[-1] if 'SMA_50' in data.columns else precio_actual
        sma_200 = data['SMA_200'].iloc[-1] if 'SMA_200' in data.columns else precio_actual
        rsi_actual = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
        
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
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
            
        if precio_actual > sma_50:
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
            
        if precio_actual > sma_200:
            tendencia_alcista += 10
        else:
            tendencia_bajista += 10
        
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

def _obtener_nombre_columna(data, prefix):
    """
    Obtiene el nombre de columna que coincide con el prefijo
    """
    for col in data.columns:
        if col.startswith(prefix):
            return col
    return None

def generar_senales_tecnicas(data):
    """
    Genera señales técnicas basadas en múltiples indicadores
    """
    if data.empty or 'Close' not in data.columns:
        return {"senales": [], "resumen": "No hay datos suficientes"}
    
    try:
        # Calcular todos los indicadores
        data = calcular_indicadores_tecnicos(data)
        
        senales = []
        
        # Señal RSI
        if 'RSI' in data.columns:
            rsi_actual = data['RSI'].iloc[-1]
            if rsi_actual < 30:
                senales.append({"indicador": "RSI", "senal": "COMPRA", "fuerza": "FUERTE", 
                              "descripcion": f"RSI en {rsi_actual:.1f} - Zona de sobreventa"})
            elif rsi_actual > 70:
                senales.append({"indicador": "RSI", "senal": "VENTA", "fuerza": "FUERTE",
                              "descripcion": f"RSI en {rsi_actual:.1f} - Zona de sobrecompra"})
        
        # Señal MACD
        if all(col in data.columns for col in ['MACD', 'MACD_Signal']):
            macd_actual = data['MACD'].iloc[-1]
            signal_actual = data['MACD_Signal'].iloc[-1]
            macd_anterior = data['MACD'].iloc[-2] if len(data) > 1 else macd_actual
            
            if macd_actual > signal_actual and macd_anterior <= signal_actual:
                senales.append({"indicador": "MACD", "senal": "COMPRA", "fuerza": "MEDIA",
                              "descripcion": "MACD cruza por encima de la línea de señal"})
            elif macd_actual < signal_actual and macd_anterior >= signal_actual:
                senales.append({"indicador": "MACD", "senal": "VENTA", "fuerza": "MEDIA",
                              "descripcion": "MACD cruza por debajo de la línea de señal"})
        
        # Señal Bandas de Bollinger
        if all(col in data.columns for col in ['Close', 'BB_Upper', 'BB_Lower']):
            precio_actual = data['Close'].iloc[-1]
            bb_upper = data['BB_Upper'].iloc[-1]
            bb_lower = data['BB_Lower'].iloc[-1]
            
            if precio_actual <= bb_lower:
                senales.append({"indicador": "Bollinger", "senal": "COMPRA", "fuerza": "MEDIA",
                              "descripcion": "Precio toca banda inferior - Posible rebote"})
            elif precio_actual >= bb_upper:
                senales.append({"indicador": "Bollinger", "senal": "VENTA", "fuerza": "MEDIA",
                              "descripcion": "Precio toca banda superior - Posible corrección"})
        
        # Resumen de señales
        compras = sum(1 for s in senales if s['senal'] == 'COMPRA')
        ventas = sum(1 for s in senales if s['senal'] == 'VENTA')
        
        if compras > ventas:
            resumen = "TENDENCIA ALCISTA"
        elif ventas > compras:
            resumen = "TENDENCIA BAJISTA"
        else:
            resumen = "TENDENCIA NEUTRAL"
        
        return {
            "senales": senales,
            "resumen": resumen,
            "total_compras": compras,
            "total_ventas": ventas
        }
        
    except Exception as e:
        return {"senales": [], "resumen": f"Error: {str(e)}"}

# Función para testing
if __name__ == "__main__":
    # Probar las funciones
    import yfinance as yf
    from datetime import datetime, timedelta
    
    st.title("🔍 Prueba - Análisis Técnico")
    
    # Descargar datos de prueba
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    data = yf.download("AAPL", start=start_date, end=end_date)
    data = data.reset_index()
    
    st.subheader("Datos Originales")
    st.write(data.head())
    
    st.subheader("Indicadores Técnicos")
    data_tech = calcular_indicadores_tecnicos(data)
    st.write(data_tech.tail())
    
    st.subheader("Análisis de Tendencia")
    tendencia = analizar_tendencias(data_tech)
    st.write(tendencia)
    
    st.subheader("Señales Técnicas")
    senales = generar_senales_tecnicas(data_tech)
    st.write(senales)

# utils/technical_analysis.py
import pandas as pd
import numpy as np

def calcular_indicadores_tecnicos(data):
    """
    Calcula todos los indicadores técnicos para los datos proporcionados
    """
    if data.empty:
        return data
    
    # Crear una copia para no modificar el original
    data_tech = data.copy()
    
    # Asegurarnos de que tenemos la columna Close
    if 'Close' not in data_tech.columns:
        return data_tech
    
    try:
        # RSI
        delta = data_tech['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data_tech['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = data_tech['Close'].ewm(span=12, adjust=False).mean()
        exp26 = data_tech['Close'].ewm(span=26, adjust=False).mean()
        data_tech['MACD'] = exp12 - exp26
        data_tech['MACD_Signal'] = data_tech['MACD'].ewm(span=9, adjust=False).mean()
        data_tech['MACD_Histogram'] = data_tech['MACD'] - data_tech['MACD_Signal']
        
        # Bandas de Bollinger
        data_tech['BB_Middle'] = data_tech['Close'].rolling(window=20).mean()
        bb_std = data_tech['Close'].rolling(window=20).std()
        data_tech['BB_Upper'] = data_tech['BB_Middle'] + (bb_std * 2)
        data_tech['BB_Lower'] = data_tech['BB_Middle'] - (bb_std * 2)
        
        # Medias Móviles
        data_tech['SMA_20'] = data_tech['Close'].rolling(window=20).mean()
        data_tech['SMA_50'] = data_tech['Close'].rolling(window=50).mean()
        data_tech['SMA_200'] = data_tech['Close'].rolling(window=200).mean()
        
        return data_tech
        
    except Exception as e:
        print(f"Error calculando indicadores: {str(e)}")
        return data_tech