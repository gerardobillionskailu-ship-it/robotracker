"""
TradeOlympo - Bot de Trading Autónomo (Arquitectura Modular v3.0)

ESTRATEGIAS IMPLEMENTADAS:
1. Estrategia Élite: Reversión a la media para Tech stocks (RSI < 30 + SMA 200)
2. Estrategia Rompeolas: Breakout de energía (Resistencia 20d + RSI > 50 + Volumen > 150%)

Modo: ANÁLISIS Y RECOMENDACIONES
Fuente de Datos: Alpaca API con feed IEX (gratuito)
Séptima modificación: Arquitectura modular SIN pandas-ta (usa funciones nativas)
"""
import os
import json
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# ========== CONFIGURACIÓN ==========

API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT')

# Watchlist por defecto
DEFAULT_WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "XLE", "OXY", "APA", "CVX"]
SECTOR_ENERGIA = ['XLE', 'OXY', 'APA', 'CVX', 'VLO', 'HAL', 'COP', 'SLB', 'BKR']

# Filtro de calidad: Solo analizar acciones con volumen promedio > 1M
MIN_VOLUME_THRESHOLD = 1_000_000

# ========== FUNCIONES DE CONFIGURACIÓN ==========

def load_config():
    """Lee la configuración desde trading_config.json"""
    try:
        with open('trading_config.json', 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"⚠️ No se pudo leer trading_config.json: {e}")
        return {
            "active_strategy": "modular",
            "watchlist": DEFAULT_WATCHLIST,
            "status": "active"
        }

def load_watchlist():
    """
    Lee la watchlist desde watchlist.json o trading_config.json
    Soporta formatos: lista simple o estructurado
    """
    try:
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                content = f.read()
                if not content.strip():
                    return load_config().get('watchlist', DEFAULT_WATCHLIST)

                config_data = json.loads(content)

                if isinstance(config_data, list):
                    return [x.strip().upper() for x in config_data if x.strip()]
                elif isinstance(config_data, dict):
                    tickers = []
                    if 'strategy_elite' in config_data and config_data['strategy_elite'].get('enabled', True):
                        tickers.extend(config_data['strategy_elite'].get('symbols', []))
                    if 'strategy_rompeolas' in config_data and config_data['strategy_rompeolas'].get('enabled', True):
                        tickers.extend(config_data['strategy_rompeolas'].get('symbols', []))
                    return list(set([x.strip().upper() for x in tickers if x.strip()])) or DEFAULT_WATCHLIST

        config = load_config()
        return config.get('watchlist', DEFAULT_WATCHLIST)

    except Exception as e:
        print(f"⚠️ Error cargando watchlist: {e}. Usando defecto.")
        return DEFAULT_WATCHLIST

# ========== FUNCIONES AUXILIARES ==========

def log_message(message):
    """Escribe mensaje en consola y en archivo bot_logs.txt"""
    print(message)
    try:
        with open('bot_logs.txt', 'a', encoding='utf-8') as f:
            timestamp = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S ET')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"⚠️ No se pudo escribir log: {e}")

def sugerir_contrato_opciones(precio_actual):
    """
    Calcula el contrato ideal bajo gestión de riesgo estricta.
    - Capital: Cuenta pequeña ($1,000) -> Max costo por contrato $200.
    - Vencimiento: 45-60 días (Swing).
    - Strike: ITM (In The Money) para Delta ~0.60.
    """
    hoy = datetime.now()
    fecha_minima = hoy + timedelta(days=45)
    fecha_maxima = hoy + timedelta(days=60)
    rango_fechas = f"{fecha_minima.strftime('%d/%m')} al {fecha_maxima.strftime('%d/%m/%Y')}"
    strike_objetivo = round(precio_actual * 0.97, 1)

    sugerencia = (
        f"\n   🎯 PLAN DE EJECUCIÓN (Gestión $1,000):\n"
        f"      - Vencimiento Objetivo: {rango_fechas}\n"
        f"      - Strike Sugerido: CALL ${strike_objetivo} (ITM)\n"
        f"      - Límite de Compra: NO pagar más de $2.00 ($200) por contrato.\n"
    )
    return sugerencia

# ========== INDICADORES (VERSIÓN ESTABLE) ==========

def calcular_rsi(series, period=14):
    """Calcula RSI usando pandas nativo (sin pandas-ta)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_sma(series, window):
    """Calcula SMA usando pandas nativo (sin pandas-ta)"""
    return series.rolling(window=window).mean()

# ========== MÓDULO 1: ESTRATEGIA ÉLITE (Tech / Reversión) ==========

def analizar_estrategia_elite(bars, ticker):
    """
    ESTRATEGIA ÉLITE (Reversión a la Media)
    Enfoque: Swing Trading Clásico / Reversión a la Media.
    Ideal para: NVDA, TSLA, AAPL en días normales.

    Lógica:
    - RSI < 30 (sobreventa extrema)
    - Precio > SMA 200 (tendencia alcista de fondo)
    """
    closes = bars['close']

    # Indicadores usando funciones nativas
    rsi_series = calcular_rsi(closes, period=14)
    sma_20 = calcular_sma(closes, 20)
    sma_200 = calcular_sma(closes, 200) if len(closes) >= 200 else calcular_sma(closes, 20)

    # Valores actuales
    current_price = closes.iloc[-1]
    rsi = rsi_series.iloc[-1]
    sma_200_val = sma_200.iloc[-1]
    sma_20_val = sma_20.iloc[-1]

    signal = None
    reason = ""

    # Lógica de Entrada
    if pd.notna(rsi) and rsi < 30:
        if current_price > sma_200_val:
            signal = "CALL (Rebote Técnico)"
            reason = f"Elite: Activo sobrevendido (RSI {rsi:.2f}) en tendencia alcista. Posible rebote a la media."
        else:
            signal = "WATCHLIST (RSI Bajo en Downtrend)"
            reason = f"Elite: RSI {rsi:.2f} bajo pero precio < SMA200. Esperar confirmación."

    elif pd.notna(rsi) and current_price > sma_20_val and 40 < rsi < 55:
        signal = "WATCHLIST (Pullback Sano)"
        reason = f"Elite: Precio sobre SMA20, RSI {rsi:.2f} en zona neutral. Monitorear."

    return signal, reason

# ========== MÓDULO 2: ESTRATEGIA ROMPEOLAS (Energía / Momentum) ==========

def analizar_estrategia_rompeolas(bars, ticker):
    """
    ESTRATEGIA ROMPEOLAS (Breakout con Volumen)
    Enfoque: Momentum / Breakout con confirmación institucional.
    Ideal para: XLE, OXY, APA (Crisis energética/política).

    Lógica:
    - Precio > Máximo de 20 días (breakout de resistencia)
    - RSI > 50 (fuerza alcista, no rebote)
    - Volumen > 150% del promedio (confirmación institucional)
    """
    closes = bars['close']
    volumes = bars['volume']
    highs = bars['high']

    # Indicadores usando funciones nativas
    rsi_series = calcular_rsi(closes, period=14)
    vol_sma = calcular_sma(volumes, 20)
    resistencia_20d = highs.rolling(20).max().shift(1)

    # Valores actuales
    current_price = closes.iloc[-1]
    current_volume = volumes.iloc[-1]
    rsi = rsi_series.iloc[-1]
    vol_sma_val = vol_sma.iloc[-1]
    resistencia = resistencia_20d.iloc[-1]

    signal = None
    reason = ""

    # Validar que tenemos datos
    if pd.isna(rsi) or pd.isna(resistencia) or pd.isna(vol_sma_val):
        return signal, reason

    # --- Lógica de Disparo (Trigger) ---
    breakout = current_price > resistencia
    volumen_institucional = current_volume > (vol_sma_val * 1.5)
    fuerza = rsi > 50

    if breakout and fuerza:
        if volumen_institucional:
            signal = "CALL (ROMPEOLAS CONFIRMADO)"
            contrato = sugerir_contrato_opciones(current_price)

            reason = (
                f"🌊 BREAKOUT CON VOLUMEN EN {ticker}\n"
                f"   - Precio: ${current_price:.2f} rompió resistencia de ${resistencia:.2f}\n"
                f"   - Volumen: {int(current_volume):,} (>150% del promedio)\n"
                f"   - RSI: {rsi:.2f} (Tendencia fuerte)"
                f"{contrato}"
            )
        else:
            signal = "WATCHLIST (Breakout sin Volumen)"
            reason = f"Rompeolas: Breakout de ${resistencia:.2f} pero volumen insuficiente. Monitorear."

    return signal, reason

# ========== FUNCIÓN PRINCIPAL (ORQUESTADOR) ==========

def run_bot():
    """Función principal del bot con arquitectura modular"""
    config = load_config()

    log_message("=" * 60)
    log_message(f"🤖 INICIANDO TRADEOLYMPO AUTO-BOT (Modular)")
    log_message(f"📅 Fecha: {datetime.now(pytz.timezone('America/New_York'))}")
    log_message(f"📋 Estrategia activa: {config.get('active_strategy', 'modular')}")
    log_message("=" * 60)

    if not API_KEY or not SECRET_KEY:
        log_message("❌ ERROR: No hay API KEYS.")
        return

    api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')

    # Calcular fecha de inicio (Hace 700 días para asegurar datos de sobra)
    fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')
    log_message(f"📅 Solicitando datos desde: {fecha_inicio}")

    # Cargar Watchlist
    watchlist = load_watchlist()
    log_message(f"📊 Watchlist: {', '.join(watchlist)}\n")

    resultados = []

    # BUCLE DE ANÁLISIS
    for symbol in watchlist:
        try:
            log_message(f"\n🔍 Analizando: {symbol}...")

            # --- FIX: SOLICITUD EXPLÍCITA CON FECHA DE INICIO Y FEED IEX ---
            bars = api.get_bars(
                symbol,
                tradeapi.TimeFrame.Day,
                start=fecha_inicio,
                limit=300,
                feed='iex'
            ).df

            log_message(f"   📥 Datos descargados: {len(bars)} días.")

            if bars.empty or len(bars) < 200:
                log_message(f"   ⚠️ Insuficiente historial ({len(bars)}). Saltando.")
                continue

            # ========== FILTRO DE CALIDAD: VOLUMEN ==========
            volumes = bars['volume']
            avg_volume_30d = volumes.tail(30).mean()

            if avg_volume_30d < MIN_VOLUME_THRESHOLD:
                log_message(f"   ⏭️ VOLUMEN BAJO: Promedio {avg_volume_30d:,.0f} < {MIN_VOLUME_THRESHOLD:,}. Saltando.")
                continue

            log_message(f"   ✅ Volumen OK: Promedio {avg_volume_30d:,.0f} acciones/día")

            # --- SELECTOR DE MÓDULO (CEREBRO) ---
            signal = None
            reason = ""

            if symbol in SECTOR_ENERGIA:
                log_message(f"   🌊 Aplicando Estrategia Rompeolas (Energía)")
                signal, reason = analizar_estrategia_rompeolas(bars, symbol)
            else:
                log_message(f"   🏆 Aplicando Estrategia Élite (Tech)")
                signal, reason = analizar_estrategia_elite(bars, symbol)

            # --- PROCESAR RESULTADOS ---
            if signal and "CALL" in signal:
                log_message(f"\n   🚀 SEÑAL ENCONTRADA: {symbol}")
                log_message(f"      Tipo: {signal}")
                log_message(f"      {reason}")

                resultados.append({
                    "ticker": symbol,
                    "signal": signal,
                    "reason": reason,
                    "price": float(bars.iloc[-1]['close']),
                    "timestamp": datetime.now().isoformat()
                })
            elif signal:
                log_message(f"   💤 {symbol}: {signal}")
            else:
                log_message(f"   💤 Sin señal clara")

        except Exception as e:
            log_message(f"   ⚠️ Error procesando {symbol}: {e}")
            import traceback
            traceback.print_exc()

    # Guardar Resultados
    try:
        with open('last_run_results.json', 'w') as f:
            json.dump(resultados, f, indent=4)
        log_message(f"\n💾 Resultados guardados en 'last_run_results.json'")
        log_message(f"   Total de señales: {len(resultados)}")
    except Exception as e:
        log_message(f"❌ Error guardando resultados: {e}")

    log_message("\n" + "=" * 60)
    log_message("✅ FIN DEL ANÁLISIS")
    log_message("=" * 60 + "\n")

if __name__ == "__main__":
    run_bot()
