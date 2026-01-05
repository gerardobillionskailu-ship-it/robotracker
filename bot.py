"""
TradeOlympo - Bot de Trading Autónomo
Estrategia de los 3 Jueces (Tech Stocks Edition)

Lógica de Trading:
- Juez 1 (Tendencia): Precio > SMA 200
- Juez 2 (Oportunidad): RSI < 70 (no sobrecomprado)
- Juez 3 (Momentum): Precio > SMA 20

Ejecuta COMPRA solo si los 3 jueces aprueban y no hay posición abierta.
Cuarta modificacion manual por Gemini
"""
import os
import json
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT')

# Cargar configuración desde JSON
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
            "active_strategy": "elite",
            "watchlist": ['NVDA', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'AMD'],
            "status": "active"
        }

# Función para escribir logs
def log_message(message):
    """Escribe mensaje en consola y en archivo bot_logs.txt"""
    print(message)
    try:
        with open('bot_logs.txt', 'a', encoding='utf-8') as f:
            timestamp = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S ET')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"⚠️ No se pudo escribir log: {e}")

# WATCHLIST (se carga dinámicamente desde JSON)
config = load_config()
WATCHLIST = config.get('watchlist', ['NVDA', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'AMD'])

# --- INDICADORES ---
def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_sma(series, window):
    return series.rolling(window=window).mean()

# --- CEREBRO DEL BOT ---
def run_bot():
    log_message(f"--- 🚀 INICIANDO VERSIÓN 'MIRADA PROFUNDA' - {datetime.now()} ---")
    log_message(f"📋 Estrategia activa: {config.get('active_strategy', 'N/A')}")
    log_message(f"📊 Watchlist: {', '.join(WATCHLIST)}")

    if not API_KEY or not SECRET_KEY:
        log_message("❌ ERROR: No hay API KEYS.")
        return

    api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')

    # Calcular fecha de inicio (Hace 700 días para asegurar datos de sobra)
    fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')
    log_message(f"📅 Solicitando datos desde: {fecha_inicio}")

    # BUCLE DE ANÁLISIS
    for symbol in WATCHLIST:
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

            if len(bars) < 200:
                log_message(f"   ⚠️ Insuficiente historial ({len(bars)}). Saltando.")
                continue

            # ========== FILTRO DE CALIDAD: VOLUMEN ==========
            # Calcular volumen promedio de los últimos 30 días
            volumes = bars['volume']
            avg_volume_30d = volumes.tail(30).mean()

            # Umbral: 1 millón de acciones diarias
            MIN_VOLUME_THRESHOLD = 1_000_000

            if avg_volume_30d < MIN_VOLUME_THRESHOLD:
                log_message(f"   ⏭️ VOLUMEN BAJO: Promedio {avg_volume_30d:,.0f} < {MIN_VOLUME_THRESHOLD:,}. Saltando.")
                continue

            # Datos listos
            closes = bars['close']
            current_price = closes.iloc[-1]

            log_message(f"   ✅ Volumen OK: Promedio {avg_volume_30d:,.0f} acciones/día")

            # Indicadores
            rsi = calcular_rsi(closes).iloc[-1]
            sma_200 = calcular_sma(closes, 200).iloc[-1]
            sma_20 = calcular_sma(closes, 20).iloc[-1]

            log_message(f"   📊 Precio: ${current_price:.2f} | RSI: {rsi:.2f} | SMA200: {sma_200:.2f} | SMA20: {sma_20:.2f}")

            # --- LOS 3 JUECES ---
            juez_tendencia = current_price > sma_200
            juez_oportunidad = rsi < 70
            juez_momentum = current_price > sma_20

            if juez_tendencia and juez_oportunidad and juez_momentum:
                log_message(f"   ✅ APROBADO: {symbol}")

                # Verificar posición
                try:
                    pos = api.get_position(symbol)
                    if int(pos.qty) > 0:
                        log_message("   ✋ Ya tenemos posición. Mantener.")
                        continue
                except:
                    pass

                # Ejecutar
                api.submit_order(symbol=symbol, qty=1, side='buy', type='market', time_in_force='day')
                log_message("   🚀 ORDEN ENVIADA.")

            else:
                # Mostrar por qué falló
                razones = []
                if not juez_tendencia: razones.append(f"Tendencia Bajista (Precio < {sma_200:.2f})")
                if not juez_oportunidad: razones.append(f"RSI Alto ({rsi:.2f})")
                if not juez_momentum: razones.append(f"Sin Momentum (Precio < {sma_20:.2f})")
                log_message(f"   ❌ DESCARTADO: {', '.join(razones)}")

        except Exception as e:
            log_message(f"   Error en {symbol}: {e}")

    log_message("\n--- FIN DEL ANÁLISIS ---")

if __name__ == "__main__":
    run_bot()
