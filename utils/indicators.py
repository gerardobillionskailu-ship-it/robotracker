"""
Módulo de Indicadores Técnicos para TradeOlympo
Implementa estrategias de análisis técnico para identificar oportunidades de trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import streamlit as st


class TechnicalIndicators:
    """
    Clase base para calcular indicadores técnicos.
    Soporta múltiples estrategias de análisis.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Inicializa el analizador de indicadores.

        Args:
            df: DataFrame con datos OHLCV (Open, High, Low, Close, Volume)
        """
        self.df = df.copy()

    def calculate_all_indicators(self) -> pd.DataFrame:
        """
        Calcula todos los indicadores disponibles.

        Returns:
            DataFrame con indicadores calculados
        """
        self.calculate_larry_williams()
        self.calculate_wyckoff_metrics()
        # PRÓXIMOS INDICADORES:
        # - RSI (Relative Strength Index)
        # - MACD (Moving Average Convergence Divergence)
        # - Bandas de Bollinger
        # - Fibonacci Retracements

        return self.df

    # ========== LARRY WILLIAMS STRATEGY ==========

    def calculate_larry_williams(self) -> pd.DataFrame:
        """
        Implementa la estrategia de Larry Williams.

        Componentes:
        1. Williams %R: Indicador de momentum (-100 a 0)
           - Sobrecompra: %R > -20
           - Sobreventa: %R < -80
        2. Medias Móviles: Detección de tendencias

        Returns:
            DataFrame con indicadores Williams calculados
        """
        # Williams %R (período 14)
        period = 14
        highest_high = self.df['High'].rolling(window=period).max()
        lowest_low = self.df['Low'].rolling(window=period).min()

        self.df['williams_r'] = -100 * (
            (highest_high - self.df['Close']) / (highest_high - lowest_low)
        )

        # Señales de Williams %R
        self.df['williams_oversold'] = self.df['williams_r'] < -80
        self.df['williams_overbought'] = self.df['williams_r'] > -20

        # Medias Móviles (Larry Williams setup clásico)
        self.df['sma_20'] = self.df['Close'].rolling(window=20).mean()      # ~1 mes
        self.df['sma_50'] = self.df['Close'].rolling(window=50).mean()      # ~10 semanas / 2.5 meses
        self.df['sma_65'] = self.df['Close'].rolling(window=65).mean()      # 13 semanas (trimestral)
        self.df['sma_200'] = self.df['Close'].rolling(window=200).mean()    # ~40 semanas / 10 meses
        self.df['sma_250'] = self.df['Close'].rolling(window=250).mean()    # 50 semanas (~1 año)

        # Cruces de Medias (Golden Cross / Death Cross) - usando 50 y 200
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
        """
        Genera señal de trading basada en Larry Williams.

        Returns:
            Dict con:
                - signal: 'BUY', 'SELL', 'HOLD'
                - strength: 0-100 (confianza de la señal)
                - reasons: Lista de razones
                - suggested_strategy: Estrategia recomendada para cuenta Cash
        """
        latest = self.df.iloc[-1]
        reasons = []
        strength = 50  # Neutral
        signal = 'HOLD'

        # Análisis Williams %R
        if latest['williams_oversold']:
            reasons.append("Williams %R en sobreventa (oportunidad de compra)")
            strength += 20
            signal = 'BUY'
        elif latest['williams_overbought']:
            reasons.append("Williams %R en sobrecompra (considerar venta)")
            strength -= 20
            signal = 'SELL'

        # Análisis de Medias Móviles
        if latest['Close'] > latest['sma_20'] > latest['sma_50']:
            reasons.append("Precio sobre SMA 20 y 50 (tendencia alcista)")
            strength += 15
            if signal != 'SELL':
                signal = 'BUY'
        elif latest['Close'] < latest['sma_20'] < latest['sma_50']:
            reasons.append("Precio bajo SMA 20 y 50 (tendencia bajista)")
            strength -= 15

        # Golden/Death Cross
        if latest['golden_cross']:
            reasons.append("¡Golden Cross detectado! (SMA 50 cruzó SMA 200)")
            strength += 25
            signal = 'BUY'
        elif latest['death_cross']:
            reasons.append("Death Cross detectado (SMA 50 bajó de SMA 200)")
            strength -= 25
            signal = 'SELL'

        # Estrategia para cuenta Cash
        if signal == 'BUY':
            suggested_strategy = "Long Call (compra directa de opciones Call) o compra de acciones"
        elif signal == 'SELL':
            suggested_strategy = "Mantenerse en efectivo o considerar salir de posiciones existentes"
        else:
            suggested_strategy = "Esperar mejor punto de entrada"

        return {
            'signal': signal,
            'strength': max(0, min(100, strength)),
            'reasons': reasons,
            'suggested_strategy': suggested_strategy,
            'williams_r': latest['williams_r']
        }

    # ========== WYCKOFF LITE STRATEGY ==========

    def calculate_wyckoff_metrics(self) -> pd.DataFrame:
        """
        Implementa métricas básicas del método Wyckoff.

        Enfoque en:
        1. Análisis de Volumen (oferta/demanda)
        2. Posición del cierre en la vela (fuerza/debilidad)
        3. Detección de acumulación/distribución

        Returns:
            DataFrame con métricas Wyckoff calculadas
        """
        # Volumen promedio (20 períodos)
        self.df['volume_avg'] = self.df['Volume'].rolling(window=20).mean()

        # Volumen relativo (actual vs promedio)
        self.df['volume_relative'] = (
            self.df['Volume'] / self.df['volume_avg']
        ) * 100

        # Volumen alto (> 150% del promedio)
        self.df['high_volume'] = self.df['volume_relative'] > 150

        # Posición del cierre en la vela (0-100%)
        # 100% = cierre en máximo, 0% = cierre en mínimo
        range_hl = self.df['High'] - self.df['Low']
        range_hl = range_hl.replace(0, np.nan)  # Evitar división por 0

        self.df['close_position'] = (
            (self.df['Close'] - self.df['Low']) / range_hl
        ) * 100

        # Fortaleza de la vela
        # Volumen alto + cierre en la parte alta = Fortaleza (acumulación)
        # Volumen alto + cierre en la parte baja = Debilidad (distribución)
        self.df['bullish_strength'] = (
            (self.df['high_volume']) &
            (self.df['close_position'] > 70)
        )
        self.df['bearish_weakness'] = (
            (self.df['high_volume']) &
            (self.df['close_position'] < 30)
        )

        # Spread (rango de la vela)
        self.df['spread'] = self.df['High'] - self.df['Low']
        self.df['spread_avg'] = self.df['spread'].rolling(window=20).mean()

        # Esfuerzo vs Resultado (principio Wyckoff)
        # Volumen alto con spread pequeño = posible reversión
        self.df['effort_result_anomaly'] = (
            (self.df['volume_relative'] > 150) &
            (self.df['spread'] < self.df['spread_avg'] * 0.7)
        )

        return self.df

    def get_wyckoff_signal(self) -> Dict[str, any]:
        """
        Genera señal de trading basada en Wyckoff.

        Returns:
            Dict con señal, fuerza, razones y estrategia
        """
        latest = self.df.iloc[-1]
        recent = self.df.tail(5)  # Últimas 5 velas

        reasons = []
        strength = 50
        signal = 'HOLD'

        # Análisis de volumen
        if latest['high_volume']:
            reasons.append(f"Volumen alto detectado ({latest['volume_relative']:.0f}% del promedio)")

        # Análisis de fortaleza/debilidad
        if latest['bullish_strength']:
            reasons.append("Fortaleza alcista: Volumen alto + cierre en máximos")
            strength += 25
            signal = 'BUY'
        elif latest['bearish_weakness']:
            reasons.append("Debilidad bajista: Volumen alto + cierre en mínimos")
            strength -= 25
            signal = 'SELL'

        # Posición del cierre
        if latest['close_position'] > 75:
            reasons.append(f"Cierre en zona alta de la vela ({latest['close_position']:.0f}%)")
            strength += 10
            if signal != 'SELL':
                signal = 'BUY'
        elif latest['close_position'] < 25:
            reasons.append(f"Cierre en zona baja de la vela ({latest['close_position']:.0f}%)")
            strength -= 10

        # Anomalía esfuerzo-resultado
        if latest['effort_result_anomaly']:
            reasons.append("Anomalía Wyckoff: Alto volumen con poco movimiento (posible reversión)")
            strength += 15

        # Patrones de acumulación (múltiples velas con fortaleza)
        if recent['bullish_strength'].sum() >= 3:
            reasons.append("Patrón de acumulación detectado (3+ velas con fortaleza)")
            strength += 20
            signal = 'BUY'
        elif recent['bearish_weakness'].sum() >= 3:
            reasons.append("Patrón de distribución detectado (3+ velas con debilidad)")
            strength -= 20
            signal = 'SELL'

        # Estrategia para cuenta Cash
        if signal == 'BUY':
            suggested_strategy = "Long Call o compra de acciones (detectada posible acumulación)"
        elif signal == 'SELL':
            suggested_strategy = "Mantenerse líquido (posible distribución en curso)"
        else:
            suggested_strategy = "Esperar confirmación de acumulación/distribución"

        return {
            'signal': signal,
            'strength': max(0, min(100, strength)),
            'reasons': reasons,
            'suggested_strategy': suggested_strategy,
            'volume_relative': latest['volume_relative'],
            'close_position': latest['close_position']
        }


# ========== FUNCIONES AUXILIARES ==========

def get_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
    """
    Calcula niveles de soporte y resistencia básicos.

    Args:
        df: DataFrame con datos OHLCV
        window: Ventana para cálculo de niveles

    Returns:
        Tuple (soporte, resistencia)
    """
    recent_data = df.tail(window)
    support = recent_data['Low'].min()
    resistance = recent_data['High'].max()

    return support, resistance


@st.cache_data(ttl=3600)  # Cache por 1 hora
def fetch_stock_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    """
    Descarga datos de acciones usando yfinance con headers robustos.
    Implementa retry automático con periodos decrecientes.

    Args:
        symbol: Símbolo del ticker (ej: 'CVX', 'SLB')
        period: Periodo de datos ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')

    Returns:
        DataFrame con datos OHLCV o DataFrame vacío si falla
    """
    import yfinance as yf
    import requests_cache

    # Configurar caché para evitar hits repetidos a Yahoo Finance
    session = requests_cache.CachedSession('yfinance.cache', expire_after=3600)
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    # Intentar con diferentes periodos si falla
    periods_to_try = [period, "1y", "6mo", "3mo"]

    for attempt_period in periods_to_try:
        try:
            ticker = yf.Ticker(symbol, session=session)
            df = ticker.history(period=attempt_period)

            if not df.empty and len(df) >= 20:
                # Asegurar que tenemos las columnas necesarias
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                if all(col in df.columns for col in required_columns):
                    # Rellenar valores nulos si existen
                    df = df.ffill().bfill()
                    return df
        except Exception:
            continue

    # Si falla con el símbolo base, intentar variantes mexicanas y brasileñas
    for variant in [f"{symbol}.MX", f"{symbol}.SA"]:
        try:
            ticker = yf.Ticker(variant, session=session)
            df = ticker.history(period="1y")

            if not df.empty and len(df) >= 20:
                df = df.ffill().bfill()
                return df
        except Exception:
            continue

    # Si todo falla, retornar DataFrame vacío
    return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache por 1 hora para no saturar Alpha Vantage (5 calls/min free tier)
def fetch_stock_data_alphavantage(symbol: str, api_key: str) -> pd.DataFrame:
    """
    Descarga datos de acciones usando Alpha Vantage API.
    Alternativa a yfinance cuando hay bloqueos de IP.

    Args:
        symbol: Símbolo del ticker (ej: 'CVX', 'SLB')
        api_key: Alpha Vantage API Key

    Returns:
        DataFrame con datos OHLCV o DataFrame vacío si falla
    """
    try:
        from alpha_vantage.timeseries import TimeSeries

        ts = TimeSeries(key=api_key, output_format='pandas')
        data, meta_data = ts.get_daily(symbol=symbol, outputsize='full')

        # Renombrar columnas para que coincidan con yfinance
        df = data.rename(columns={
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. volume': 'Volume'
        })

        # Ordenar por fecha (más antiguo primero)
        df = df.sort_index()

        # Tomar últimos 500 días (~2 años de trading)
        df = df.tail(500)

        # Asegurar tipos numéricos
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Rellenar valores nulos
        df = df.ffill().bfill()

        return df

    except Exception as e:
        # Retornar DataFrame vacío si falla
        return pd.DataFrame()


def generate_synthetic_data(symbol: str, days: int = 500) -> pd.DataFrame:
    """
    Genera datos sintéticos alcistas para demostración.
    Simula un rally por cambio de régimen en Venezuela.

    Args:
        symbol: Símbolo del ticker (para naming)
        days: Cantidad de días de datos

    Returns:
        DataFrame con datos OHLCV sintéticos alcistas
    """
    from datetime import datetime, timedelta

    # Generar fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # Precio base según símbolo
    base_prices = {
        'CVX': 150,
        'SLB': 50,
        'HAL': 35,
        'XLE': 80
    }
    base_price = base_prices.get(symbol, 100)

    # Generar tendencia alcista con volatilidad
    np.random.seed(42)
    trend = np.linspace(base_price, base_price * 1.5, len(dates))
    volatility = np.random.normal(0, base_price * 0.02, len(dates))
    close_prices = trend + volatility

    # Generar OHLC basado en Close
    df = pd.DataFrame(index=dates)
    df['Close'] = close_prices
    df['Open'] = df['Close'].shift(1).fillna(df['Close'].iloc[0])
    df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + np.random.uniform(0, 0.02, len(df)))
    df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - np.random.uniform(0, 0.02, len(df)))
    df['Volume'] = np.random.randint(1000000, 5000000, len(df))

    # Asegurar tipos numéricos
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


# PRÓXIMAS FUNCIONES A IMPLEMENTAR:
# - calculate_rsi(): Índice de Fuerza Relativa
# - calculate_macd(): MACD y señal
# - calculate_bollinger_bands(): Bandas de Bollinger
# - detect_chart_patterns(): Detección de patrones (cabeza y hombros, triángulos, etc.)
# - calculate_fibonacci_levels(): Niveles de retroceso de Fibonacci
# - volume_profile(): Perfil de volumen por precio
