"""
TradeOlympo - Bot de Trading Autónomo (Arquitectura Modular v3.0)

ESTRATEGIAS IMPLEMENTADAS:
1. Estrategia Élite: Reversión a la media para Tech stocks (RSI < 30 + SMA 200)
2. Estrategia Rompeolas: Breakout de energía (Resistencia 20d + RSI > 50 + Volumen > 150%)

Modo: ANÁLISIS Y RECOMENDACIONES
Fuente de Datos: Alpaca API con feed IEX (gratuito)
Sexta modificación: Arquitectura modular con pandas_ta
"""
import os
import json
import alpaca_trade_api as tradeapi
import pandas as pd
import pandas_ta as ta
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
        # Fallback a valores por defecto
        return {
            "active_strategy": "modular",
            "watchlist": DEFAULT_WATCHLIST,
            "status": "active"
        }

def load_watchlist():
    """
    Lee la watchlist desde watchlist.json con soporte para múltiples formatos:
    - Formato simple: ["NVDA", "TSLA", ...]
    - Formato estructurado: {"strategy_elite": {...}, "strategy_rompeolas": {...}}

    Si no existe, intenta leer desde trading_config.json
    """
    try:
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                content = f.read()
                if not content.strip():
                    return load_config().get('watchlist', DEFAULT_WATCHLIST)

                config_data = json.loads(content)

                # Detectar formato
                if isinstance(config_data, list):
                    # Formato simple
                    return [x.strip().upper() for x in config_data if x.strip()]
                elif isinstance(config_data, dict):
                    # Formato estructurado - extraer todos los tickers
                    tickers = []
                    if 'strategy_elite' in config_data and config_data['strategy_elite'].get('enabled', True):
                        tickers.extend(config_data['strategy_elite'].get('symbols', []))
                    if 'strategy_rompeolas' in config_data and config_data['strategy_rompeolas'].get('enabled', True):
                        tickers.extend(config_data['strategy_rompeolas'].get('symbols', []))
                    return list(set([x.strip().upper() for x in tickers if x.strip()])) or DEFAULT_WATCHLIST

        # Si no existe watchlist.json, leer desde trading_config.json
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

    # Formato de fecha para lectura humana
    rango_fechas = f"{fecha_minima.strftime('%d/%m')} al {fecha_maxima.strftime('%d/%m/%Y')}"

    # Strike ITM: Buscamos un strike aprox 3% debajo del precio actual (Delta ~0.60)
    strike_objetivo = round(precio_actual * 0.97, 1)

    sugerencia = (
        f"\n   🎯 PLAN DE EJECUCIÓN (Gestión $1,000):\n"
        f"      - Vencimiento Objetivo: {rango_fechas}\n"
        f"      - Strike Sugerido: CALL ${strike_objetivo} (ITM)\n"
        f"      - Límite de Compra: NO pagar más de $2.00 ($200) por contrato.\n"
    )
    return sugerencia

# ========== MÓDULO 1: ESTRATEGIA ÉLITE (Tech / Reversión) ==========

def analizar_estrategia_elite(df, ticker):
    """
    ESTRATEGIA ÉLITE (Reversión a la Media)
    Enfoque: Swing Trading Clásico / Reversión a la Media.
    Ideal para: NVDA, TSLA, AAPL en días normales.

    Lógica:
    - RSI < 30 (sobreventa extrema)
    - Precio > SMA 200 (tendencia alcista de fondo)
    """
    # Indicadores usando pandas_ta
    df['SMA_20'] = ta.sma(df['close'], length=20)
    df['SMA_200'] = ta.sma(df['close'], length=200) if len(df) >= 200 else ta.sma(df['close'], length=20)
    df['RSI'] = ta.rsi(df['close'], length=14)

    ultimo = df.iloc[-1]
    signal = None
    reason = ""

    # Lógica de Entrada
    # 1. Rebote por sobreventa extrema
    if ultimo['RSI'] < 30:
        # Verificar tendencia de fondo
        if ultimo['close'] > ultimo['SMA_200']:
            signal = "CALL (Rebote Técnico)"
            reason = f"Elite: Activo sobrevendido (RSI {ultimo['RSI']:.2f}) en tendencia alcista. Posible rebote a la media."
        else:
            signal = "WATCHLIST (RSI Bajo en Downtrend)"
            reason = f"Elite: RSI {ultimo['RSI']:.2f} bajo pero precio < SMA200. Esperar confirmación."

    # 2. Continuación de tendencia (Pullback sano)
    elif ultimo['close'] > ultimo['SMA_20'] and 40 < ultimo['RSI'] < 55:
        # Lógica conservadora, busca entradas cuando el RSI no está caliente
        signal = "WATCHLIST (Pullback Sano)"
        reason = f"Elite: Precio sobre SMA20, RSI {ultimo['RSI']:.2f} en zona neutral. Monitorear."

    return signal, reason

# ========== MÓDULO 2: ESTRATEGIA ROMPEOLAS (Energía / Momentum) ==========

def analizar_estrategia_rompeolas(df, ticker):
    """
    ESTRATEGIA ROMPEOLAS (Breakout con Volumen)
    Enfoque: Momentum / Breakout con confirmación institucional.
    Ideal para: XLE, OXY, APA (Crisis energética/política).

    Lógica:
    - Precio > Máximo de 20 días (breakout de resistencia)
    - RSI > 50 (fuerza alcista, no rebote)
    - Volumen > 150% del promedio (confirmación institucional)
    """
    # Indicadores usando pandas_ta
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['Vol_SMA'] = ta.sma(df['volume'], length=20)
    # Resistencia: Máximo de los últimos 20 días (sin incluir hoy)
    df['Resistencia_20d'] = df['high'].rolling(20).max().shift(1)

    ultimo = df.iloc[-1]
    signal = None
    reason = ""

    # --- Lógica de Disparo (Trigger) ---

    # 1. Ruptura (Breakout): Precio cierra por encima del techo de 20 días
    breakout = ultimo['close'] > ultimo['Resistencia_20d']

    # 2. Pico de Volumen Institucional: Volumen hoy > 150% del promedio
    volumen_institucional = ultimo['volume'] > (ultimo['Vol_SMA'] * 1.5)

    # 3. Fuerza: RSI > 50 (No queremos rebotes, queremos fuerza)
    fuerza = ultimo['RSI'] > 50

    if breakout and fuerza:
        if volumen_institucional:
            signal = "CALL (ROMPEOLAS CONFIRMADO)"
            # Generamos la sugerencia del contrato específico
            contrato = sugerir_contrato_opciones(ultimo['close'])

            reason = (
                f"🌊 BREAKOUT CON VOLUMEN EN {ticker}\n"
                f"   - Precio: ${ultimo['close']:.2f} rompió resistencia de ${ultimo['Resistencia_20d']:.2f}\n"
                f"   - Volumen: {int(ultimo['volume']):,} (>150% del promedio)\n"
                f"   - RSI: {ultimo['RSI']:.2f} (Tendencia fuerte)"
                f"{contrato}"
            )
        else:
            # Si rompe pero sin volumen, alerta suave
            signal = "WATCHLIST (Breakout sin Volumen)"
            reason = f"Rompeolas: Breakout de ${ultimo['Resistencia_20d']:.2f} pero volumen insuficiente. Monitorear."

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

    # Validar credenciales
    if not API_KEY or not SECRET_KEY:
        log_message("❌ ERROR: No hay API KEYS.")
        return

    # Conexión a Alpaca
    try:
        api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')
        log_message("✅ Conexión establecida con Alpaca API")
    except Exception as e:
        log_message(f"❌ Error conectando a Alpaca: {e}")
        return

    # Calcular fecha de inicio (Hace 700 días para asegurar datos de sobra)
    fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')
    log_message(f"📅 Solicitando datos desde: {fecha_inicio}")

    # Cargar Watchlist (compatible con múltiples formatos)
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
                start=fecha_inicio,  # OBLIGATORIO: Fecha de inicio
                limit=300,
                feed='iex'           # OBLIGATORIO: Feed gratuito (IEX)
            ).df

            log_message(f"   📥 Datos descargados: {len(bars)} días.")

            if bars.empty or len(bars) < 200:
                log_message(f"   ⚠️ Insuficiente historial ({len(bars)}). Saltando.")
                continue

            # ========== FILTRO DE CALIDAD: VOLUMEN ==========
            # Calcular volumen promedio de los últimos 30 días
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
                # Usa Estrategia Rompeolas
                log_message(f"   🌊 Aplicando Estrategia Rompeolas (Energía)")
                signal, reason = analizar_estrategia_rompeolas(bars, symbol)
            else:
                # Usa Estrategia Élite (Tech/General)
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
    # Esto permite que Streamlit (la web) lea lo que encontró el bot
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
