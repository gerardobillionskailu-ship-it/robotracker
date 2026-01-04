"""
Módulo de Indicadores Técnicos para TradeOlympo
Implementa estrategias de análisis técnico para identificar oportunidades de trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import yfinance as yf


# ========== FUNCIONES DE DESCARGA ROBUSTA ==========

def generate_synthetic_data(symbol: str, days: int = 500) -> pd.DataFrame:
    """
    Genera datos sintéticos alcistas simulando el 'Rally por cambio de régimen en Venezuela'.

    Args:
        symbol: Símbolo del ticker (para referencia)
        days: Número de días de datos a generar

    Returns:
        DataFrame con datos OHLCV sintéticos con tendencia alcista
    """
    from datetime import datetime, timedelta

    # Precio base según símbolo
    base_prices = {
        'CVX': 150,
        'SLB': 50,
        'HAL': 35,
        'XLE': 80
    }
    base_price = base_prices.get(symbol, 100)

    # Generar fechas
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=days, freq='D')

    # Generar tendencia alcista con volatilidad
    np.random.seed(42)  # Para reproducibilidad

    # Tendencia alcista: +50% en el período
    trend = np.linspace(0, 0.5, days)

    # Volatilidad diaria (2-5%)
    volatility = np.random.randn(days) * 0.025

    # Precio de cierre con tendencia + volatilidad
    close_prices = base_price * (1 + trend + volatility.cumsum() * 0.1)

    # Generar OHLC a partir del cierre
    data = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        # High/Low dentro de ±2% del cierre
        daily_range = close * 0.02
        high = close + np.random.uniform(0, daily_range)
        low = close - np.random.uniform(0, daily_range)

        # Open cercano al cierre anterior
        if i == 0:
            open_price = close * 0.99
        else:
            open_price = close_prices[i-1] * (1 + np.random.uniform(-0.01, 0.01))

        # Volumen con picos ocasionales (simulando acumulación Wyckoff)
        base_volume = 5_000_000
        volume_spike = 1 if np.random.random() > 0.85 else 0  # 15% de probabilidad
        volume = base_volume * (1 + volume_spike * 2) * (1 + np.random.uniform(-0.3, 0.5))

        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': int(volume)
        })

    df = pd.DataFrame(data, index=dates)
    df.index.name = 'Date'

    # Simular últimas velas con fortaleza alcista (para Wyckoff)
    for i in range(-10, 0):
        df.iloc[i, df.columns.get_loc('Close')] = df.iloc[i, df.columns.get_loc('High')] * 0.95  # Cierre cerca del máximo
        df.iloc[i, df.columns.get_loc('Volume')] *= 1.8  # Volumen alto

    return df


def fetch_stock_data(symbol: str, period: str = "2y", _retry_count: int = 0) -> pd.DataFrame:
    """
    Descarga datos de acciones de forma robusta usando yfinance.

    Implementa User-Agent, requests-cache y fallback automático para evitar bloqueos.

    Args:
        symbol: Símbolo del ticker (ej: 'CVX', 'SLB', 'AAPL')
        period: Período de datos ('1y', '2y', '6mo', etc.)
        _retry_count: Contador interno de reintentos (no usar manualmente)

    Returns:
        DataFrame con datos OHLCV o DataFrame vacío si hay error
    """
    try:
        # Configurar requests-cache para evitar bloqueos de IP
        import requests
        import requests_cache

        # Crear sesión con caché (válida por 1 hora)
        session = requests_cache.CachedSession(
            'yfinance_cache',
            backend='memory',
            expire_after=3600  # 1 hora
        )

        # Configurar headers para evitar bloqueos (User-Agent de Chrome)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://finance.yahoo.com/'
        })

        # Crear objeto Ticker con sesión cacheada
        ticker = yf.Ticker(symbol, session=session)

        # Descargar datos históricos
        df = ticker.history(period=period)

        # Validar que el DataFrame no esté vacío
        if df.empty:
            # Intentar fallback a variantes internacionales si es el primer intento
            if _retry_count == 0:
                # Intentar con .MX (México)
                df_mx = fetch_stock_data(symbol + ".MX", period, _retry_count=1)
                if not df_mx.empty:
                    return df_mx

                # Intentar con .SA (Brasil)
                df_sa = fetch_stock_data(symbol + ".SA", period, _retry_count=1)
                if not df_sa.empty:
                    return df_sa

            # Intentar con período más corto
            if period == "2y":
                return fetch_stock_data(symbol, "1y", _retry_count)
            elif period == "1y":
                return fetch_stock_data(symbol, "6mo", _retry_count)
            elif period == "6mo":
                return fetch_stock_data(symbol, "3mo", _retry_count)
            else:
                return pd.DataFrame()

        return df

    except Exception as e:
        # En caso de error, retornar DataFrame vacío
        # El error será manejado en la capa de UI
        return pd.DataFrame()


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

        # Medias Móviles
        self.df['sma_20'] = self.df['Close'].rolling(window=20).mean()
        self.df['sma_50'] = self.df['Close'].rolling(window=50).mean()
        self.df['sma_200'] = self.df['Close'].rolling(window=200).mean()

        # Cruces de Medias (Golden Cross / Death Cross)
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


# PRÓXIMAS FUNCIONES A IMPLEMENTAR:
# - calculate_rsi(): Índice de Fuerza Relativa
# - calculate_macd(): MACD y señal
# - calculate_bollinger_bands(): Bandas de Bollinger
# - detect_chart_patterns(): Detección de patrones (cabeza y hombros, triángulos, etc.)
# - calculate_fibonacci_levels(): Niveles de retroceso de Fibonacci
# - volume_profile(): Perfil de volumen por precio
