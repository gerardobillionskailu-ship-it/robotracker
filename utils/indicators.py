"""
Módulo de Indicadores Técnicos para TradeOlympo
Implementa estrategias de análisis técnico para identificar oportunidades de trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import streamlit as st
from datetime import datetime, timedelta

# ========== FUNCIONES DE DESCARGA ROBUSTA ==========

@st.cache_data(ttl=3600)  # Cache por 1 hora
def generate_synthetic_data(symbol: str, days: int = 500) -> pd.DataFrame:
    """Genera datos sintéticos alcistas simulando el 'Rally por cambio de régimen en Venezuela'."""
    
    base_prices = {'CVX': 150, 'SLB': 50, 'HAL': 35, 'XLE': 80}
    base_price = base_prices.get(symbol, 100)
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')

    np.random.seed(42)
    trend = np.linspace(0, 0.5, days)
    volatility = np.random.randn(days) * 0.025
    close_prices = base_price * (1 + trend + volatility.cumsum() * 0.1)

    data = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        daily_range = close * 0.02
        high = close + np.random.uniform(0, daily_range)
        low = close - np.random.uniform(0, daily_range)
        open_price = close * 0.99 if i == 0 else close_prices[i-1] * (1 + np.random.uniform(-0.01, 0.01))
        
        base_volume = 5_000_000
        volume_spike = 1 if np.random.random() > 0.85 else 0
        volume = base_volume * (1 + volume_spike * 2) * (1 + np.random.uniform(-0.3, 0.5))
        
        data.append({'Open': open_price, 'High': high, 'Low': low, 'Close': close, 'Volume': int(volume)})

    df = pd.DataFrame(data, index=dates)
    df.index.name = 'Date'
    
    # Simular patrones de Wyckoff
    for i in range(-10, 0):
        df.iloc[i, df.columns.get_loc('Close')] = df.iloc[i, df.columns.get_loc('High')] * 0.95
        df.iloc[i, df.columns.get_loc('Volume')] *= 1.8

    return df


@st.cache_data(ttl=3600)  # Cache 1h para no saturar Alpha Vantage
def fetch_stock_data_alphavantage(symbol: str, api_key: str) -> pd.DataFrame:
    """
    Descarga datos reales usando SOLO Alpha Vantage.
    Usa outputsize='compact' (100 días) para compatibilidad con FREE TIER.
    """
    try:
        from alpha_vantage.timeseries import TimeSeries

        ts = TimeSeries(key=api_key, output_format='pandas')
        
        # CAMBIO CRÍTICO: 'compact' es gratis (100 datos), 'full' es premium.
        data, meta_data = ts.get_daily(symbol=symbol, outputsize='compact')

        if data is None or data.empty:
            st.error(f"⚠️ Alpha Vantage devolvió datos vacíos para {symbol}")
            return pd.DataFrame()

        # Mapeo de columnas
        df = data.rename(columns={
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. volume': 'Volume'
        })

        df = df.sort_index()
        # No necesitamos tail() porque compact ya trae solo los últimos 100

        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.ffill().bfill()
        
        return df

    except Exception as e:
        # Mensaje amigable si falla por límites de API
        if "premium" in str(e).lower() or "call frequency" in str(e).lower():
            st.warning(f"⚠️ Límite de API Alpha Vantage alcanzado para {symbol}. Espera 1 minuto.")
        else:
            st.error(f"❌ Error en Alpha Vantage: {str(e)}")
        return pd.DataFrame()


def fetch_stock_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    """Wrapper principal. Intenta usar Alpha Vantage desde secrets."""
    try:
        api_key = st.secrets.get("ALPHAVANTAGE_API_KEY", "")
        if api_key:
            return fetch_stock_data_alphavantage(symbol, api_key)
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


class TechnicalIndicators:
    """Clase base para calcular indicadores técnicos."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def calculate_all_indicators(self) -> pd.DataFrame:
        self.calculate_larry_williams()
        self.calculate_wyckoff_metrics()
        return self.df

    # ========== LARRY WILLIAMS STRATEGY ==========

    def calculate_larry_williams(self) -> pd.DataFrame:
        """Implementa la estrategia de Larry Williams."""
        period = 14
        highest_high = self.df['High'].rolling(window=period).max()
        lowest_low = self.df['Low'].rolling(window=period).min()

        self.df['williams_r'] = -100 * (
            (highest_high - self.df['Close']) / (highest_high - lowest_low)
        )

        self.df['williams_oversold'] = self.df['williams_r'] < -80
        self.df['williams_overbought'] = self.df['williams_r'] > -20

        # Medias Móviles
        # NOTA: SMA 200 y 250 serán NaN con Free Tier (solo 100 datos)
        self.df['sma_20'] = self.df['Close'].rolling(window=20).mean()
        self.df['sma_50'] = self.df['Close'].rolling(window=50).mean()
        self.df['sma_65'] = self.df['Close'].rolling(window=65).mean()
        self.df['sma_200'] = self.df['Close'].rolling(window=200).mean()
        self.df['sma_250'] = self.df['Close'].rolling(window=250).mean()

        # Cruces (manejo de errores si SMA 200 es NaN)
        self.df['golden_cross'] = False
        self.df['death_cross'] = False
        
        if len(self.df) >= 200:
             self.df['golden_cross'] = (
                (self.df['sma_50'] > self.df['sma_200']) &
                (self.df['sma_50'].shift(1) <= self.df['sma_200'].shift(1))
            )
             self.df['death_cross'] = (
                (self.df['sma_50'] < self.df['sma_200']) &
                (self.df['sma_50'].shift(1) >= self.df['sma_200'].shift(1))
            )

        return self.df

    def get_larry_williams_signal(self) -> Dict[str, any]:
        if self.df.empty:
            return {'signal': 'HOLD', 'strength': 0, 'reasons': ['Datos insuficientes'], 'suggested_strategy': 'Esperar'}

        latest = self.df.iloc[-1]
        reasons = []
        strength = 50
        signal = 'HOLD'

        # Análisis Williams %R
        if latest['williams_oversold']:
            reasons.append("Williams %R en sobreventa (posible rebote)")
            strength += 20
            signal = 'BUY'
        elif latest['williams_overbought']:
            reasons.append("Williams %R en sobrecompra")
            strength -= 20
            signal = 'SELL'

        # Análisis de Medias (Solo si existen datos)
        if pd.notna(latest['sma_20']) and pd.notna(latest['sma_50']):
            if latest['Close'] > latest['sma_20'] > latest['sma_50']:
                reasons.append("Tendencia alcista corto plazo (Precio > SMA20 > SMA50)")
                strength += 15
                if signal != 'SELL': signal = 'BUY'
            elif latest['Close'] < latest['sma_20'] < latest['sma_50']:
                reasons.append("Tendencia bajista corto plazo")
                strength -= 15

        # Golden Cross (Solo si SMA 200 existe)
        if latest.get('golden_cross', False):
            reasons.append("Golden Cross (SMA 50 > SMA 200)")
            strength += 25
            signal = 'BUY'

        if signal == 'BUY':
            suggested_strategy = "Long Call (Momentum alcista detectado)"
        elif signal == 'SELL':
            suggested_strategy = "Cerrar posiciones / Cash"
        else:
            suggested_strategy = "Esperar confirmación"

        return {
            'signal': signal,
            'strength': max(0, min(100, strength)),
            'reasons': reasons,
            'suggested_strategy': suggested_strategy,
            'williams_r': latest.get('williams_r', 0)
        }

    # ========== WYCKOFF LITE STRATEGY ==========

    def calculate_wyckoff_metrics(self) -> pd.DataFrame:
        self.df['volume_avg'] = self.df['Volume'].rolling(window=20).mean()
        self.df['volume_relative'] = (self.df['Volume'] / self.df['volume_avg']) * 100
        self.df['high_volume'] = self.df['volume_relative'] > 150

        range_hl = self.df['High'] - self.df['Low']
        range_hl = range_hl.replace(0, np.nan) 

        self.df['close_position'] = ((self.df['Close'] - self.df['Low']) / range_hl) * 100

        self.df['bullish_strength'] = (self.df['high_volume']) & (self.df['close_position'] > 70)
        self.df['bearish_weakness'] = (self.df['high_volume']) & (self.df['close_position'] < 30)

        self.df['spread'] = self.df['High'] - self.df['Low']
        self.df['spread_avg'] = self.df['spread'].rolling(window=20).mean()

        self.df['effort_result_anomaly'] = (
            (self.df['volume_relative'] > 150) &
            (self.df['spread'] < self.df['spread_avg'] * 0.7)
        )

        return self.df

    def get_wyckoff_signal(self) -> Dict[str, any]:
        if self.df.empty:
            return {'signal': 'HOLD', 'strength': 0, 'reasons': [], 'suggested_strategy': ''}
            
        latest = self.df.iloc[-1]
        reasons = []
        strength = 50
        signal = 'HOLD'

        if latest['high_volume']:
            reasons.append(f"Volumen alto ({latest['volume_relative']:.0f}% del promedio)")

        if latest['bullish_strength']:
            reasons.append("Fortaleza (Volumen alto + Cierre alto)")
            strength += 25
            signal = 'BUY'
        elif latest['bearish_weakness']:
            reasons.append("Debilidad (Volumen alto + Cierre bajo)")
            strength -= 25
            signal = 'SELL'

        if latest['effort_result_anomaly']:
            reasons.append("Anomalía Wyckoff (Mucho volumen, poco movimiento)")
            strength += 15

        if signal == 'BUY':
            suggested_strategy = "Acumulación detectada -> Long Call"
        elif signal == 'SELL':
            suggested_strategy = "Distribución detectada -> Cash"
        else:
            suggested_strategy = "Esperar definición"

        return {
            'signal': signal,
            'strength': max(0, min(100, strength)),
            'reasons': reasons,
            'suggested_strategy': suggested_strategy,
            'volume_relative': latest.get('volume_relative', 0),
            'close_position': latest.get('close_position', 50)
        }

# ========== FUNCIONES AUXILIARES ==========

def get_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
    recent_data = df.tail(window)
    support = recent_data['Low'].min()
    resistance = recent_data['High'].max()
    return support, resistance
