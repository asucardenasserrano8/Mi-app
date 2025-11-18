import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar API keys
GOOGLE_KEY = os.getenv("AP")
FMP = os.getenv("AP2")  # Financial Modeling Prep
currencyapi = os.getenv("AP1")
AlphaVantage = os.getenv("AP3")

if GOOGLE_KEY:
    genai.configure(api_key=GOOGLE_KEY)

# CONFIGURACIÓN COMPLETA DE LAS 4 APIS
API_KEYS = {
    "google_gemini": GOOGLE_KEY,
    "financial_modeling_prep": FMP,
    "currency_api": currencyapi,
    "alpha_vantage": AlphaVantage
}

@st.cache_data(ttl=300)
def obtener_datos_indices():
    """Obtiene índices bursátiles de múltiples fuentes"""
    indices_data = {}
    
    # ✅ FUENTE 1: Financial Modeling Prep (PRINCIPAL)
    if API_KEYS["financial_modeling_prep"]:
        try:
            # MÁS ÍNDICES - 17 ÍNDICES GLOBALES
            indices_fmp = {
                "S&P 500": "^GSPC",
                "NASDAQ": "^IXIC", 
                "Dow Jones": "^DJI",
                "Russell 2000": "^RUT",
                "NYSE Composite": "^NYA",
                "FTSE 100": "^FTSE",
                "DAX": "^GDAXI",
                "CAC 40": "^FCHI",
                "Euro Stoxx 50": "^STOXX50E",
                "IBEX 35": "^IBEX",
                "Nikkei 225": "^N225",
                "Hang Seng": "^HSI",
                "Shanghai Composite": "000001.SS",
                "S&P/TSX Composite": "^GSPTSE",
                "ASX 200": "^AXJO",
                "Bovespa": "^BVSP",
                "SMI Switzerland": "^SSMI"
            }
            
            for nombre, simbolo in indices_fmp.items():
                url = f"https://financialmodelingprep.com/api/v3/quote/{simbolo}?apikey={API_KEYS['financial_modeling_prep']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        quote = data[0]
                        precio_actual = quote.get('price', 0)
                        cambio_porcentaje = quote.get('changesPercentage', 0)
                        
                        # Formatear precio
                        if precio_actual > 1000:
                            precio_str = f"${precio_actual:,.0f}"
                        else:
                            precio_str = f"${precio_actual:.2f}"
                        
                        indices_data[nombre] = {
                            "precio": precio_str,
                            "cambio": f"{cambio_porcentaje:+.2f}%",
                            "valor": precio_actual,
                            "fuente": "Financial Modeling Prep"
                        }
                        
        except Exception as e:
            st.warning(f"FMP no disponible: {str(e)}")
    
    # ✅ FUENTE 2: Alpha Vantage (ALTERNATIVA)
    if not indices_data and API_KEYS["alpha_vantage"]:
        try:
            indices_av = {
                "S&P 500": ".INX",
                "NASDAQ": ".IXIC",
                "Dow Jones": ".DJI",
                "FTSE 100": ".FTSE",
                "DAX": ".GDAXI"
            }
            
            for nombre, simbolo in indices_av.items():
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={simbolo}&apikey={API_KEYS['alpha_vantage']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        precio_actual = float(quote.get('05. price', 0))
                        cambio_porcentaje = float(quote.get('10. change percent', '0%').replace('%', ''))
                        
                        if precio_actual > 0:
                            if precio_actual > 1000:
                                precio_str = f"${precio_actual:,.0f}"
                            else:
                                precio_str = f"${precio_actual:.2f}"
                            
                            indices_data[nombre] = {
                                "precio": precio_str,
                                "cambio": f"{cambio_porcentaje:+.2f}%",
                                "valor": precio_actual,
                                "fuente": "Alpha Vantage"
                            }
                            
        except Exception as e:
            st.warning(f"Alpha Vantage no disponible: {str(e)}")
    
    # ✅ FUENTE 3: Yahoo Finance (FALLBACK)
    if not indices_data:
        yf_indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC", 
            "Dow Jones": "^DJI",
            "Russell 2000": "^RUT",
            "NYSE Composite": "^NYA",
            "FTSE 100": "^FTSE",
            "DAX": "^GDAXI",
            "CAC 40": "^FCHI",
            "Euro Stoxx 50": "^STOXX50E",
            "IBEX 35": "^IBEX",
            "Nikkei 225": "^N225",
            "Hang Seng": "^HSI",
            "Shanghai Composite": "000001.SS",
            "S&P/TSX Composite": "^GSPTSE",
            "ASX 200": "^AXJO",
            "Bovespa": "^BVSP",
            "SMI Switzerland": "^SSMI"
        }
        
        for nombre, ticker in yf_indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    indices_data[nombre] = {
                        "precio": f"${current:,.0f}" if current > 1000 else f"${current:.2f}",
                        "cambio": f"{change:+.2f}%",
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
    
    return indices_data

@st.cache_data(ttl=300)
def obtener_datos_forex():
    """Obtiene datos de divisas de múltiples fuentes"""
    forex_data = {}
    
    # ✅ FUENTE 1: CurrencyAPI (ESPECIALIZADA EN FOREX)
    if API_KEYS["currency_api"]:
        try:
            url = f"https://api.currencyapi.com/v3/latest?apikey={API_KEYS['currency_api']}&base_currency=USD"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    # MÁS PARES DE DIVISAS - 17 PARES
                    divisas_objetivo = {
                        "EUR": "EUR/USD",
                        "JPY": "USD/JPY", 
                        "GBP": "GBP/USD",
                        "CHF": "USD/CHF",
                        "CAD": "USD/CAD",
                        "AUD": "AUD/USD",
                        "NZD": "NZD/USD",
                        "CNY": "USD/CNY",
                        "HKD": "USD/HKD",
                        "SGD": "USD/SGD",
                        "SEK": "USD/SEK",
                        "NOK": "USD/NOK",
                        "MXN": "USD/MXN",
                        "INR": "USD/INR",
                        "BRL": "USD/BRL",
                        "ZAR": "USD/ZAR",
                        "RUB": "USD/RUB"
                    }
                    
                    for currency_code, par_nombre in divisas_objetivo.items():
                        if currency_code in data["data"]:
                            rate_data = data["data"][currency_code]
                            rate = rate_data["value"]
                            
                            if currency_code in ["EUR", "GBP", "AUD", "NZD"]:
                                precio_formateado = f"{1/rate:.4f}" if rate != 0 else "0.0000"
                                forex_data[par_nombre] = {
                                    "precio": precio_formateado,
                                    "cambio": "0.00%",  # CurrencyAPI no proporciona cambios
                                    "valor": 1/rate if rate != 0 else 0,
                                    "fuente": "CurrencyAPI"
                                }
                            else:
                                precio_formateado = f"{rate:.4f}"
                                forex_data[par_nombre] = {
                                    "precio": precio_formateado,
                                    "cambio": "0.00%",
                                    "valor": rate,
                                    "fuente": "CurrencyAPI"
                                }
        except Exception as e:
            st.warning(f"CurrencyAPI no disponible: {str(e)}")
    
    # ✅ FUENTE 2: Financial Modeling Prep
    if not forex_data and API_KEYS["financial_modeling_prep"]:
        try:
            # MÁS PARES FOREX
            pares_forex = [
                "EURUSD", "USDJPY", "GBPUSD", "USDCHF", "USDCAD", 
                "AUDUSD", "NZDUSD", "USDCNY", "USDHKD", "USDSGD",
                "USDSEK", "USDNOK", "USDMXN", "USDINR", "USDBRL",
                "USDZAR", "USDRUB"
            ]
            nombres_pares = {
                "EURUSD": "EUR/USD",
                "USDJPY": "USD/JPY",
                "GBPUSD": "GBP/USD", 
                "USDCHF": "USD/CHF",
                "USDCAD": "USD/CAD",
                "AUDUSD": "AUD/USD",
                "NZDUSD": "NZD/USD",
                "USDCNY": "USD/CNY",
                "USDHKD": "USD/HKD",
                "USDSGD": "USD/SGD",
                "USDSEK": "USD/SEK",
                "USDNOK": "USD/NOK",
                "USDMXN": "USD/MXN",
                "USDINR": "USD/INR",
                "USDBRL": "USD/BRL",
                "USDZAR": "USD/ZAR",
                "USDRUB": "USD/RUB"
            }
            
            for par in pares_forex:
                url = f"https://financialmodelingprep.com/api/v3/quote/{par}?apikey={API_KEYS['financial_modeling_prep']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        quote = data[0]
                        precio = quote.get('price', 0)
                        cambio_porcentaje = quote.get('changesPercentage', 0)
                        
                        nombre_par = nombres_pares.get(par, par)
                        forex_data[nombre_par] = {
                            "precio": f"{precio:.4f}",
                            "cambio": f"{cambio_porcentaje:+.2f}%",
                            "valor": precio,
                            "fuente": "Financial Modeling Prep"
                        }
        except Exception as e:
            st.warning(f"FMP Forex no disponible: {str(e)}")
    
    # ✅ FUENTE 3: Alpha Vantage
    if not forex_data and API_KEYS["alpha_vantage"]:
        try:
            pares_av = {
                "EUR/USD": "EURUSD",
                "USD/JPY": "USDJPY", 
                "GBP/USD": "GBPUSD",
                "USD/CHF": "USDCHF",
                "AUD/USD": "AUDUSD"
            }
            
            for par_nombre, simbolo in pares_av.items():
                url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={simbolo[:3]}&to_currency={simbolo[3:]}&apikey={API_KEYS['alpha_vantage']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "Realtime Currency Exchange Rate" in data:
                        rate_data = data["Realtime Currency Exchange Rate"]
                        precio = float(rate_data.get('5. Exchange Rate', 0))
                        
                        forex_data[par_nombre] = {
                            "precio": f"{precio:.4f}",
                            "cambio": "0.00%",  # Alpha Vantage no da cambios en esta API
                            "valor": precio,
                            "fuente": "Alpha Vantage"
                        }
        except Exception as e:
            st.warning(f"Alpha Vantage Forex no disponible: {str(e)}")
    
    # ✅ FUENTE 4: Yahoo Finance (ÚLTIMO RECURSO)
    if not forex_data:
        yf_forex = {
            "EUR/USD": "EURUSD=X",
            "USD/JPY": "JPY=X",
            "GBP/USD": "GBPUSD=X",
            "USD/CHF": "CHF=X",
            "USD/CAD": "CAD=X",
            "AUD/USD": "AUDUSD=X",
            "NZD/USD": "NZDUSD=X",
            "USD/CNY": "CNY=X",
            "USD/HKD": "HKD=X",
            "USD/SGD": "SGD=X",
            "USD/SEK": "SEK=X",
            "USD/NOK": "NOK=X",
            "USD/MXN": "MXN=X",
            "USD/INR": "INR=X",
            "USD/BRL": "BRL=X",
            "USD/ZAR": "ZAR=X",
            "USD/RUB": "RUB=X"
        }
        
        for par, ticker in yf_forex.items():
            try:
                fx = yf.Ticker(ticker)
                hist = fx.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    forex_data[par] = {
                        "precio": f"{current:.4f}",
                        "cambio": f"{change:+.2f}%",
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
    
    return forex_data

@st.cache_data(ttl=300)
def obtener_datos_cripto():
    """Obtiene datos de criptomonedas de múltiples fuentes"""
    crypto_data = {}
    
    # ✅ FUENTE 1: Financial Modeling Prep
    if API_KEYS["financial_modeling_prep"]:
        try:
            # MÁS CRIPTOMONEDAS - 17 CRIPTOS
            criptos_fmp = {
                "Bitcoin": "BTCUSD",
                "Ethereum": "ETHUSD",
                "BNB": "BNBUSD",
                "XRP": "XRPUSD",
                "Cardano": "ADAUSD",
                "Solana": "SOLUSD",
                "Dogecoin": "DOGEUSD",
                "Polkadot": "DOTUSD",
                "Litecoin": "LTCUSD",
                "Chainlink": "LINKUSD",
                "Bitcoin Cash": "BCHUSD",
                "Avalanche": "AVAXUSD",
                "Polygon": "MATICUSD",
                "Stellar": "XLMUSD",
                "Uniswap": "UNIUSD",
                "Shiba Inu": "SHIBUSD",
                "Tron": "TRXUSD"
            }
            
            for nombre, simbolo in criptos_fmp.items():
                url = f"https://financialmodelingprep.com/api/v3/quote/{simbolo}?apikey={API_KEYS['financial_modeling_prep']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        quote = data[0]
                        precio = quote.get('price', 0)
                        cambio_porcentaje = quote.get('changesPercentage', 0)
                        
                        crypto_data[nombre] = {
                            "precio": f"${precio:,.2f}",
                            "cambio": f"{cambio_porcentaje:+.2f}%",
                            "valor": precio,
                            "fuente": "Financial Modeling Prep"
                        }
        except Exception as e:
            st.warning(f"FMP Crypto no disponible: {str(e)}")
    
    # ✅ FUENTE 2: Alpha Vantage
    if not crypto_data and API_KEYS["alpha_vantage"]:
        try:
            criptos_av = {
                "Bitcoin": "BTC",
                "Ethereum": "ETH",
                "Litecoin": "LTC",
                "Ripple": "XRP",
                "Cardano": "ADA"
            }
            
            for nombre, simbolo in criptos_av.items():
                url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={simbolo}&to_currency=USD&apikey={API_KEYS['alpha_vantage']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "Realtime Currency Exchange Rate" in data:
                        rate_data = data["Realtime Currency Exchange Rate"]
                        precio = float(rate_data.get('5. Exchange Rate', 0))
                        
                        crypto_data[nombre] = {
                            "precio": f"${precio:,.2f}",
                            "cambio": "0.00%",
                            "valor": precio,
                            "fuente": "Alpha Vantage"
                        }
        except Exception as e:
            st.warning(f"Alpha Vantage Crypto no disponible: {str(e)}")
    
    # ✅ FUENTE 3: Yahoo Finance
    if not crypto_data:
        yf_crypto = {
            "Bitcoin": "BTC-USD",
            "Ethereum": "ETH-USD",
            "BNB": "BNB-USD",
            "XRP": "XRP-USD",
            "Cardano": "ADA-USD",
            "Solana": "SOL-USD",
            "Dogecoin": "DOGE-USD",
            "Polkadot": "DOT-USD",
            "Litecoin": "LTC-USD",
            "Chainlink": "LINK-USD",
            "Bitcoin Cash": "BCH-USD",
            "Avalanche": "AVAX-USD",
            "Polygon": "MATIC-USD",
            "Stellar": "XLM-USD",
            "Uniswap": "UNI-USD",
            "Shiba Inu": "SHIB-USD",
            "Tron": "TRX-USD"
        }
        
        for nombre, ticker in yf_crypto.items():
            try:
                crypto = yf.Ticker(ticker)
                hist = crypto.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    crypto_data[nombre] = {
                        "precio": f"${current:,.2f}",
                        "cambio": f"{change:+.2f}%",
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
    
    return crypto_data

@st.cache_data(ttl=300)
def obtener_datos_commodities():
    """Obtiene datos de materias primas de múltiples fuentes"""
    commodities_data = {}
    
    # ✅ FUENTE 1: Financial Modeling Prep (PRINCIPAL)
    if API_KEYS["financial_modeling_prep"]:
        try:
            # MÁS COMMODITIES - 17 PRODUCTOS
            commodities_fmp = {
                "Petróleo WTI": "CLUSD",
                "Petróleo Brent": "BZUSD", 
                "Oro": "GCUSD",
                "Plata": "SIUSD",
                "Cobre": "HGUSD",
                "Gas Natural": "NGUSD",
                "Platino": "PLUSD",
                "Paladio": "PAUSD",
                "Aluminio": "ALIUSD",
                "Trigo": "ZWUSD",
                "Maíz": "ZCUSD",
                "Soja": "ZSUSD",
                "Azúcar": "SBUSD",
                "Café": "KCUSD",
                "Cacao": "CCUSD",
                "Algodón": "CTUSD",
                "Ganado": "LEUSD"
            }
            
            for nombre, simbolo in commodities_fmp.items():
                url = f"https://financialmodelingprep.com/api/v3/quote/{simbolo}?apikey={API_KEYS['financial_modeling_prep']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        quote = data[0]
                        precio = quote.get('price', 0)
                        cambio_porcentaje = quote.get('changesPercentage', 0)
                        
                        if nombre in ["Oro", "Plata", "Platino", "Paladio"]:
                            precio_str = f"${precio:,.2f}"
                        elif nombre in ["Petróleo WTI", "Petróleo Brent", "Gas Natural"]:
                            precio_str = f"${precio:.2f}"
                        elif nombre in ["Trigo", "Maíz", "Soja", "Azúcar", "Café", "Cacao", "Algodón"]:
                            precio_str = f"${precio:.2f}"  # Commodities agrícolas
                        else:
                            precio_str = f"${precio:.2f}"
                        
                        commodities_data[nombre] = {
                            "precio": precio_str,
                            "cambio": f"{cambio_porcentaje:+.2f}%",
                            "valor": precio,
                            "fuente": "Financial Modeling Prep"
                        }
        except Exception as e:
            st.warning(f"FMP Commodities no disponible: {str(e)}")
    
    # ✅ FUENTE 2: Alpha Vantage
    if not commodities_data and API_KEYS["alpha_vantage"]:
        try:
            commodities_av = {
                "Oro": "GCUSD",
                "Petróleo WTI": "CLUSD",
                "Plata": "SIUSD",
                "Cobre": "HGUSD"
            }
            
            for nombre, simbolo in commodities_av.items():
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={simbolo}&apikey={API_KEYS['alpha_vantage']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        precio_actual = float(quote.get('05. price', 0))
                        cambio_porcentaje = float(quote.get('10. change percent', '0%').replace('%', ''))
                        
                        if precio_actual > 0:
                            if nombre in ["Oro", "Plata"]:
                                precio_str = f"${precio_actual:,.2f}"
                            else:
                                precio_str = f"${precio_actual:.2f}"
                            
                            commodities_data[nombre] = {
                                "precio": precio_str,
                                "cambio": f"{cambio_porcentaje:+.2f}%",
                                "valor": precio_actual,
                                "fuente": "Alpha Vantage"
                            }
        except Exception as e:
            st.warning(f"Alpha Vantage Commodities no disponible: {str(e)}")
    
    # ✅ FUENTE 3: Yahoo Finance (FALLBACK)
    if not commodities_data:
        yf_commodities = {
            "Petróleo WTI": "CL=F",
            "Petróleo Brent": "BZ=F", 
            "Oro": "GC=F",
            "Plata": "SI=F",
            "Cobre": "HG=F",
            "Gas Natural": "NG=F",
            "Platino": "PL=F",
            "Paladio": "PA=F",
            "Aluminio": "ALI=F",
            "Trigo": "ZW=F",
            "Maíz": "ZC=F",
            "Soja": "ZS=F",
            "Azúcar": "SB=F",
            "Café": "KC=F",
            "Cacao": "CC=F",
            "Algodón": "CT=F",
            "Ganado": "LE=F"
        }
        
        for nombre, ticker in yf_commodities.items():
            try:
                comm = yf.Ticker(ticker)
                hist = comm.history(period="2d")
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = ((current - previous) / previous) * 100
                    
                    if nombre in ["Oro", "Plata", "Platino", "Paladio"]:
                        precio_str = f"${current:,.2f}"
                    elif nombre in ["Petróleo WTI", "Petróleo Brent", "Gas Natural"]:
                        precio_str = f"${current:.2f}"
                    elif nombre in ["Trigo", "Maíz", "Soja", "Azúcar", "Café", "Cacao", "Algodón"]:
                        precio_str = f"${current:.2f}"
                    else:
                        precio_str = f"${current:.2f}"
                    
                    commodities_data[nombre] = {
                        "precio": precio_str,
                        "cambio": f"{change:+.2f}%",
                        "valor": current,
                        "fuente": "Yahoo Finance"
                    }
            except Exception as e:
                continue
    
    return commodities_data

@st.cache_data(ttl=3600)
def obtener_datos_tasas_reales():
    """Obtiene tasas de interés REALES de múltiples fuentes"""
    tasas_data = {}
    
    try:
        # ✅ FUENTE PRINCIPAL: FMP para tasas del Tesoro
        if API_KEYS["financial_modeling_prep"]:
            try:
                # Obtener tasas del Tesoro de FMP
                url = f"https://financialmodelingprep.com/api/v4/treasury?apikey={API_KEYS['financial_modeling_prep']}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        # Tomar la entrada más reciente
                        latest = data[0]
                        date = latest.get('date', '')
                        
                        # MÁS TASAS - 13 PLAZOS DIFERENTES
                        tasas_mapping = {
                            'month1': 'Tesoro USA 1 mes',
                            'month2': 'Tesoro USA 2 meses', 
                            'month3': 'Tesoro USA 3 meses',
                            'month6': 'Tesoro USA 6 meses',
                            'year1': 'Tesoro USA 1 año',
                            'year2': 'Tesoro USA 2 años',
                            'year3': 'Tesoro USA 3 años',
                            'year5': 'Tesoro USA 5 años',
                            'year7': 'Tesoro USA 7 años',
                            'year10': 'Tesoro USA 10 años',
                            'year20': 'Tesoro USA 20 años',
                            'year30': 'Tesoro USA 30 años'
                        }
                        
                        for key, nombre in tasas_mapping.items():
                            tasa = latest.get(key, 0)
                            if tasa and tasa > 0:
                                tasas_data[nombre] = {
                                    "valor": f"{tasa:.2f}%",
                                    "fuente": "Financial Modeling Prep",
                                    "categoria": "tesoro"
                                }
            except Exception as e:
                st.warning(f"FMP Tasas no disponible: {str(e)}")

        # ✅ FUENTE 2: Alpha Vantage para tasas
        if not tasas_data and API_KEYS["alpha_vantage"]:
            try:
                # Alpha Vantage para datos macroeconómicos
                tasas_av = {
                    "Tesoro USA 10 años": "10year",
                    "Tesoro USA 5 años": "5year", 
                    "Tesoro USA 2 años": "2year"
                }
                
                for nombre, plazo in tasas_av.items():
                    url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity={plazo}&apikey={API_KEYS['alpha_vantage']}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and len(data["data"]) > 0:
                            latest_yield = data["data"][0]
                            tasa = float(latest_yield.get('value', 0))
                            
                            if tasa > 0:
                                tasas_data[nombre] = {
                                    "valor": f"{tasa:.2f}%",
                                    "fuente": "Alpha Vantage",
                                    "categoria": "tesoro"
                                }
            except Exception as e:
                st.warning(f"Alpha Vantage Tasas no disponible: {str(e)}")

        # ✅ FUENTE 3: Yahoo Finance para bonos gubernamentales (fallback)
        bonos_yahoo = {
            "USA 2 años": "^IRX",
            "USA 10 años": "^TNX", 
            "USA 30 años": "^TYX",
            "USA 5 años": "^FVX",
            "USA 13 semanas": "^IRX"
        }
        
        for nombre, ticker in bonos_yahoo.items():
            try:
                bono = yf.Ticker(ticker)
                hist = bono.history(period="2d")
                if not hist.empty:
                    yield_val = hist['Close'].iloc[-1]
                    if 0.1 < yield_val < 20:
                        tasas_data[nombre] = {
                            "valor": f"{yield_val:.2f}%",
                            "fuente": "Yahoo Finance",
                            "categoria": "bonos"
                        }
            except Exception as e:
                continue

        # ✅ FUENTE 4: CoinGecko para métricas cripto
        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    market_data = data["data"]
                    total_volume = market_data.get("total_volume", {})
                    market_cap = market_data.get("total_market_cap", {})
                    market_cap_change = market_data.get("market_cap_change_percentage_24h_usd", 0)
                    
                    if "usd" in total_volume:
                        vol_str = f"${total_volume['usd']:,.0f}"
                        tasas_data["Vol Cripto 24h"] = {
                            "valor": vol_str,
                            "fuente": "CoinGecko", 
                            "categoria": "cripto"
                        }
                    
                    if "usd" in market_cap:
                        cap_str = f"${market_cap['usd']:,.0f}"
                        tasas_data["Market Cap Cripto"] = {
                            "valor": cap_str,
                            "fuente": "CoinGecko",
                            "categoria": "cripto"
                        }
                    
                    tasas_data["Cambio MC Cripto 24h"] = {
                        "valor": f"{market_cap_change:+.2f}%",
                        "fuente": "CoinGecko",
                        "categoria": "cripto"
                    }
        except Exception as e:
            pass

    except Exception as e:
        st.error(f"Error obteniendo tasas: {str(e)}")
    
    return tasas_data

# FUNCIÓN DE ANÁLISIS CON GEMINI (TU API GOOGLE)
@st.cache_data(ttl=1800)
def obtener_analisis_completo(indices, forex, crypto, commodities, tasas):
    """Genera análisis con todos los datos disponibles usando Gemini"""
    try:
        # Contar datos disponibles
        stats = {
            "indices": len(indices),
            "forex": len(forex),
            "crypto": len(crypto),
            "commodities": len(commodities),
            "tasas": len(tasas)
        }
        
        total_datos = sum(stats.values())
        
        if total_datos == 0:
            return "🔍 **Estado del Sistema:** Conectando a fuentes de datos...\n\nLos datos se cargarán automáticamente en unos segundos."
        
        # Crear resumen para el prompt
        resumen_datos = {
            "indices": {k: f"{v['precio']} ({v['cambio']})" for k, v in indices.items()},
            "forex": {k: f"{v['precio']} ({v['cambio']})" for k, v in forex.items()},
            "crypto": {k: f"{v['precio']} ({v['cambio']})" for k, v in crypto.items()},
            "commodities": {k: f"{v['precio']} ({v['cambio']})" for k, v in commodities.items()},
            "tasas": {k: v["valor"] for k, v in tasas.items()}
        }

        prompt = f"""
        Analiza los siguientes datos financieros en tiempo real:

        ÍNDICES BURSÁTILES ({stats['indices']} índices):
        {resumen_datos['indices']}

        DIVISAS ({stats['forex']} pares):
        {resumen_datos['forex']}

        CRIPTOMONEDAS ({stats['crypto']} activos):
        {resumen_datos['crypto']}

        MATERIAS PRIMAS ({stats['commodities']} commodities):
        {resumen_datos['commodities']}

        TASAS DE INTERÉS ({stats['tasas']} tasas):
        {resumen_datos['tasas']}

        Proporciona un análisis profesional que incluya:
        1. Tendencias principales del mercado
        2. Movimientos significativos en activos clave
        3. Perspectiva de riesgo y oportunidades
        4. Contexto macroeconómico relevante

        Máximo 200 palabras. Enfoque en insights accionables.
        Basado únicamente en los datos proporcionados.
        """

        # USANDO TU API DE GOOGLE GEMINI
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"📊 **Datos Cargados:** {total_datos} activos | Análisis disponible en próxima actualización"

def mostrar(datos_accion):
    """Función principal para mostrar la sección de mercados globales - INTERFAZ PARA APP.PY"""
    
    st.header("📈 Mercados Globales en Tiempo Real")
    
    # OBTENER TODOS LOS DATOS
    with st.spinner('🔄 Conectando con fuentes de datos globales...'):
        indices = obtener_datos_indices()
        forex = obtener_datos_forex()
        crypto = obtener_datos_cripto()
        commodities = obtener_datos_commodities()
        tasas = obtener_datos_tasas_reales()
        analisis = obtener_analisis_completo(indices, forex, crypto, commodities, tasas)

    # DISEÑO DE LA INTERFAZ
    st.markdown("### 🤖 Análisis de Mercados en Tiempo Real")
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; margin: 15px 0;'>
        <h4 style='color: white; margin-bottom: 15px;'>ANÁLISIS GLOBAL</h4>
        """, unsafe_allow_html=True)
        st.write(analisis)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ESTADÍSTICAS DE DATOS
    total_activos = len(indices) + len(forex) + len(crypto) + len(commodities)
    st.markdown(f"### 📊 Indicadores del Mercado Global ({total_activos} activos cargados)")

    # INDICADORES PRINCIPALES
    st.markdown("#### 🎯 Indicadores Clave")
    col1, col2, col3, col4 = st.columns(4)
    
    indicadores_principales = [
        ("S&P 500", indices.get("S&P 500")),
        ("EUR/USD", forex.get("EUR/USD")),
        ("Bitcoin", crypto.get("Bitcoin")),
        ("Oro", commodities.get("Oro"))
    ]
    
    for i, (nombre, datos) in enumerate(indicadores_principales):
        with [col1, col2, col3, col4][i]:
            if datos:
                st.metric(
                    label=nombre,
                    value=datos["precio"],
                    delta=datos["cambio"]
                )
                st.caption(f"Fuente: {datos.get('fuente', 'Directo')}")
            else:
                st.metric(label=nombre, value="Cargando...")
                st.caption("Conectando...")

    st.markdown("---")

    # SECCIÓN DE ÍNDICES
    if indices:
        st.markdown("#### 📈 Índices Bursátiles Globales")
        # Usar más columnas para mostrar más índices
        cols = st.columns(4)
        indices_items = list(indices.items())
        
        for i, (nombre, datos) in enumerate(indices_items):
            with cols[i % 4]:
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: #1E1E1E; padding: 15px; border-radius: 10px; 
                                border-left: 4px solid #2E86AB; margin: 5px 0; border: 1px solid #444;'>
                    <div style='font-weight: bold; color: white; font-size: 14px;'>{nombre}</div>
                    <div style='font-size: 1.1em; color: white; margin: 8px 0;'>{datos['precio']}</div>
                    <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-weight: bold; font-size: 13px;'>
                        {datos['cambio']}
                    </div>
                    <div style='font-size: 0.7em; color: #CCCCCC; margin-top: 5px;'>
                        {datos.get('fuente', 'Directo')}
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # SECCIÓN DE DIVISAS Y CRIPTO
    col_divisas, col_cripto = st.columns(2)
    
    with col_divisas:
        if forex:
            st.markdown("#### 💵 Divisas Principales")
            # Mostrar más pares de divisas
            for par, datos in list(forex.items())[:10]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; 
                            border: 1px solid #444; margin: 6px 0;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-weight: bold; color: white; font-size: 13px;'>{par}</div>
                    <div style='display: flex; flex-direction: column; align-items: end;'>
                        <div style='color: white; font-weight: bold; font-size: 13px;'>{datos['precio']}</div>
                        <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-size: 11px;'>
                            {datos['cambio']}
                        </div>
                    </div>
                </div>
                <div style='font-size: 10px; color: #CCCCCC; margin-top: 4px;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("#### 💵 Divisas")
            st.info("Cargando datos de divisas...")
    
    with col_cripto:
        if crypto:
            st.markdown("#### ₿ Criptomonedas")
            # Mostrar más criptomonedas
            for moneda, datos in list(crypto.items())[:10]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; 
                            border: 1px solid #444; margin: 6px 0;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-weight: bold; color: white; font-size: 13px;'>{moneda}</div>
                    <div style='display: flex; flex-direction: column; align-items: end;'>
                        <div style='color: white; font-weight: bold; font-size: 13px;'>{datos['precio']}</div>
                        <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-size: 11px;'>
                            {datos['cambio']}
                        </div>
                    </div>
                </div>
                <div style='font-size: 10px; color: #CCCCCC; margin-top: 4px;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("#### ₿ Criptomonedas")
            st.info("Cargando datos cripto...")

    st.markdown("---")

    # SECCIÓN DE COMMODITIES
    if commodities:
        st.markdown("#### 🛢️ Materias Primas")
        # Usar más columnas para commodities
        cols = st.columns(4)
        commodities_items = list(commodities.items())
        
        for i, (producto, datos) in enumerate(commodities_items):
            with cols[i % 4]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; 
                            border: 1px solid #444; margin: 6px 0; text-align: center;'>
                <div style='font-weight: bold; color: white; font-size: 12px; margin-bottom: 6px;'>{producto}</div>
                <div style='color: white; font-size: 14px; font-weight: bold; margin-bottom: 4px;'>{datos['precio']}</div>
                <div style='color: {'#4CAF50' if '+' in datos['cambio'] else '#F44336'}; font-size: 11px; font-weight: bold;'>
                    {datos['cambio']}
                </div>
                <div style='font-size: 9px; color: #CCCCCC; margin-top: 4px;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # SECCIÓN DE TASAS
    if tasas:
        st.markdown("#### 🏦 Tasas de Interés y Bonos")
        
        # Organizar en más columnas para mostrar más tasas
        cols = st.columns(4)
        tasas_items = list(tasas.items())
        
        for i, (nombre, datos) in enumerate(tasas_items):
            with cols[i % 4]:
                st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 12px; border-radius: 8px; 
                            border: 1px solid #444; margin: 6px 0; text-align: center;'>
                <div style='font-weight: bold; color: white; font-size: 11px; margin-bottom: 8px; 
                            height: 35px; display: flex; align-items: center; justify-content: center;'>
                    {nombre}
                </div>
                <div style='color: white; font-size: 14px; font-weight: bold; margin-bottom: 6px;'>
                    {datos['valor']}
                </div>
                <div style='font-size: 9px; color: #CCCCCC;'>
                    {datos.get('fuente', 'Directo')}
                </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🏦 Cargando datos de tasas y bonos...")

    # PANEL DE CONTROL MEJORADO
    st.markdown("---")
    
    col_stats, col_control = st.columns([2, 1])
    
    with col_stats:
        total_activos = len(indices) + len(forex) + len(crypto) + len(commodities)
        st.markdown(f"""
        **🚀 Cobertura Expandida del Mercado:**
        - **Activos cargados:** {total_activos}
        - **📈 17 Índices Globales:** América, Europa, Asia
        - **💵 17 Pares de Divisas:** Principales y emergentes  
        - **₿ 17 Criptomonedas:** Grandes cap y altcoins
        - **🛢️ 17 Commodities:** Energía, metales, agrícolas
        - **🏦 Tasas Completas:** Tesoro USA múltiples plazos
        - **Análisis IA:** Google Gemini
        - **Última actualización:** {datetime.now().strftime('%H:%M:%S')}
        """)
    
    with col_control:
        if st.button("🔄 Actualizar Toda La Información", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

# Función para ejecutar la sección
def run():
    mostrar(datos_accion=None)

if __name__ == "__main__":
    run()