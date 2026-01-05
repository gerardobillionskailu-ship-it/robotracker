"""
TradeOlympo - Bot de Trading Autónomo
Estrategia de los 3 Jueces (Tech Stocks Edition)

Lógica de Trading:
- Juez 1 (Tendencia): Precio > SMA 200
- Juez 2 (Oportunidad): RSI < 70 (no sobrecomprado)
- Juez 3 (Momentum): Precio > SMA 20

Ejecuta COMPRA solo si los 3 jueces aprueban y no hay posición abierta.
"""

import os
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# ========== CONFIGURACIÓN ==========

API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT', 'https://paper-api.alpaca.markets')

# TUS ACCIONES FAVORITAS (TECH WATCHLIST)
WATCHLIST = ['NVDA', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'AMD']

# ========== HERRAMIENTAS DE ANÁLISIS (INDICADORES) ==========

def calcular_rsi(series, period=14):
    """
    Calcula el RSI (Relative Strength Index).
    Retorna valores entre 0 y 100.
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calcular_sma(series, window):
    """
    Calcula la SMA (Simple Moving Average).
    """
    return series.rolling(window=window).mean()

# ========== CEREBRO DEL BOT ==========

def run_bot():
    """
    Función principal que ejecuta el análisis de los 3 Jueces
    sobre la watchlist de Tech Stocks.
    """
    print(f"--- 🧠 INICIANDO ANÁLISIS 3 JUECES: {datetime.now(pytz.UTC)} ---")
    print(f"📂 Watchlist: {', '.join(WATCHLIST)}")

    # Validar credenciales
    if not API_KEY or not SECRET_KEY:
        print("❌ ERROR: Credenciales no encontradas.")
        print("Configura ALPACA_API_KEY y ALPACA_SECRET_KEY en GitHub Secrets.")
        return

    # Conexión a Alpaca
    try:
        api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')
    except Exception as e:
        print(f"❌ Error conectando a Alpaca: {e}")
        return

    # Verificar estado del mercado
    try:
        clock = api.get_clock()
        print(f"🕐 Mercado Abierto: {clock.is_open}")

        if not clock.is_open:
            print("⚠️ El mercado está CERRADO. Se realizará análisis simulado (sin ejecutar órdenes).")
    except Exception as e:
        print(f"⚠️ No se pudo verificar el estado del mercado: {e}")

    # BUCLE PRINCIPAL: Analizar cada acción de la lista
    for symbol in WATCHLIST:
        try:
            print(f"\n🔍 Analizando: {symbol}...")

            # 1. Obtener Datos (Velas Diarias de los últimos 300 periodos)
            try:
                bars = api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=300).df
            except Exception as e:
                print(f"   ❌ Error obteniendo datos para {symbol}: {e}")
                continue

            if bars.empty or len(bars) < 200:
                print(f"   ⚠️ Datos insuficientes para {symbol} (se necesitan 200+ velas). Saltando.")
                continue

            # Limpieza básica de datos
            closes = bars['close']
            current_price = closes.iloc[-1]

            # 2. Calcular Indicadores (Los Jueces)
            rsi = calcular_rsi(closes, period=14).iloc[-1]
            sma_200 = calcular_sma(closes, window=200).iloc[-1]
            sma_20 = calcular_sma(closes, window=20).iloc[-1]

            # Validar que los indicadores se calcularon correctamente
            if pd.isna(rsi) or pd.isna(sma_200) or pd.isna(sma_20):
                print(f"   ⚠️ Indicadores inválidos para {symbol}. Saltando.")
                continue

            print(f"   📊 Precio: ${current_price:.2f} | RSI: {rsi:.2f} | SMA200: ${sma_200:.2f} | SMA20: ${sma_20:.2f}")

            # 3. EL TRIBUNAL (Lógica de Decisión de los 3 Jueces)
            juez_tendencia = current_price > sma_200      # ¿Estamos en subida a largo plazo?
            juez_oportunidad = rsi < 70                   # ¿No está muy caro? (RSI < 70)
            juez_momentum = current_price > sma_20        # ¿Tiene fuerza ahora?

            # Veredicto
            if juez_tendencia and juez_oportunidad and juez_momentum:
                print(f"   ✅ VEREDICTO: COMPRAR {symbol} (3/3 Jueces Aprobaron)")

                # 4. Verificar si ya tenemos la acción
                try:
                    pos = api.get_position(symbol)
                    qty = int(pos.qty)
                    if qty > 0:
                        print(f"   ✋ Ya tienes {qty} acciones de {symbol} en cartera. No duplicamos.")
                        continue
                except:
                    # No tenemos posición, procedemos
                    pass

                # 5. EJECUTAR COMPRA (Solo si el mercado está abierto)
                if clock.is_open:
                    try:
                        # Comprar 1 acción (puedes ajustar la cantidad según tu estrategia)
                        api.submit_order(
                            symbol=symbol,
                            qty=1,
                            side='buy',
                            type='market',
                            time_in_force='day'
                        )
                        print(f"   🚀 ORDEN ENVIADA: Compra de 1 acción de {symbol} @ ~${current_price:.2f}")
                    except Exception as e:
                        print(f"   ❌ Error enviando orden para {symbol}: {e}")
                else:
                    print(f"   💤 Mercado cerrado. Orden simulada: Compraría 1 {symbol} @ ${current_price:.2f}")

            else:
                # Mostrar razones del rechazo
                fallos = []
                if not juez_tendencia:
                    fallos.append(f"Tendencia Bajista (Precio ${current_price:.2f} < SMA200 ${sma_200:.2f})")
                if not juez_oportunidad:
                    fallos.append(f"RSI Alto ({rsi:.1f}/70)")
                if not juez_momentum:
                    fallos.append(f"Sin Momentum (Precio ${current_price:.2f} < SMA20 ${sma_20:.2f})")

                print(f"   ❌ DESCARTADO. Razones: {' | '.join(fallos)}")

        except Exception as e:
            print(f"   ❌ Error analizando {symbol}: {e}")
            import traceback
            traceback.print_exc()

    print("\n--- 🏁 ANÁLISIS FINALIZADO ---")
    print(f"Timestamp: {datetime.now(pytz.UTC)}")

if __name__ == "__main__":
    run_bot()
