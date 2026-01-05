"""
Data Loader Module - Real-time Market Data
Handles real-time price fetching and company logos
"""

import streamlit as st
import requests
from typing import Dict, Optional, Tuple

# ========== REAL-TIME PRICE FETCHING ==========

@st.cache_data(ttl=5)  # Cache por 5 segundos (precio real-time)
def get_realtime_price(symbol: str, api_key: str = None, use_alpaca: bool = True) -> Dict[str, any]:
    """
    Obtiene el precio real-time de Alpaca o fallback a datos históricos.

    Returns:
        Dict con:
        - price: float (precio actual)
        - prev_close: float (cierre anterior)
        - change: float (cambio absoluto)
        - change_pct: float (cambio porcentual)
        - is_live: bool (True si es dato real-time)
        - timestamp: str (hora del dato)
    """

    if use_alpaca and api_key:
        try:
            import alpaca_trade_api as tradeapi
            from datetime import datetime
            import pytz

            # Obtener secrets de Alpaca
            api_key_alpaca = st.secrets.get("ALPACA_API_KEY", "")
            secret_key = st.secrets.get("ALPACA_SECRET_KEY", "")
            endpoint = st.secrets.get("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets")

            if api_key_alpaca and secret_key:
                api = tradeapi.REST(api_key_alpaca, secret_key, endpoint, api_version='v2')

                # Obtener último trade (precio real-time)
                latest_trade = api.get_latest_trade(symbol)
                current_price = float(latest_trade.price)

                # Obtener cierre del día anterior
                bars = api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=2).df
                if not bars.empty and len(bars) >= 2:
                    prev_close = float(bars['close'].iloc[-2])
                else:
                    prev_close = current_price * 0.99  # Fallback estimado

                change = current_price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

                return {
                    'price': current_price,
                    'prev_close': prev_close,
                    'change': change,
                    'change_pct': change_pct,
                    'is_live': True,
                    'timestamp': datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M:%S ET')
                }
        except Exception as e:
            print(f"Error obteniendo precio real-time de Alpaca: {e}")

    # Fallback: retornar None para usar datos históricos
    return None


# ========== COMPANY LOGO FETCHING ==========

@st.cache_data(ttl=86400)  # Cache por 24 horas
def get_company_logo(symbol: str) -> Optional[str]:
    """
    Obtiene la URL del logo de la empresa.

    Prioridad:
    1. Parqet CDN (más rápido y confiable)
    2. yfinance (fallback)

    Returns:
        URL del logo o None si no se encuentra
    """

    # Opción 1: Parqet CDN (público, rápido, sin API key)
    parqet_url = f"https://assets.parqet.com/logos/symbol/{symbol}?format=png"

    try:
        # Verificar que la URL existe (HEAD request)
        response = requests.head(parqet_url, timeout=2)
        if response.status_code == 200:
            return parqet_url
    except:
        pass

    # Opción 2: yfinance como fallback
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if 'logo_url' in info and info['logo_url']:
            return info['logo_url']
    except:
        pass

    # Si ninguno funciona, retornar None
    return None


# ========== COMPANY INFO ==========

@st.cache_data(ttl=86400)  # Cache por 24 horas
def get_company_name(symbol: str) -> str:
    """
    Obtiene el nombre completo de la empresa.

    Returns:
        Nombre de la empresa o el símbolo si no se encuentra
    """

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if 'longName' in info and info['longName']:
            return info['longName']
        elif 'shortName' in info and info['shortName']:
            return info['shortName']
    except:
        pass

    # Fallback: diccionario manual de nombres comunes
    common_names = {
        'NVDA': 'NVIDIA Corporation',
        'TSLA': 'Tesla, Inc.',
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com Inc.',
        'GOOGL': 'Alphabet Inc.',
        'META': 'Meta Platforms Inc.',
        'AMD': 'Advanced Micro Devices',
        'CVX': 'Chevron Corporation',
        'SLB': 'Schlumberger Limited',
        'HAL': 'Halliburton Company',
        'XLE': 'Energy Select Sector SPDR Fund',
        'BKR': 'Baker Hughes Company',
        'WFRD': 'Weatherford International',
        'COP': 'ConocoPhillips',
        'VLO': 'Valero Energy Corporation',
        'COIN': 'Coinbase Global, Inc.'
    }

    return common_names.get(symbol, symbol)
