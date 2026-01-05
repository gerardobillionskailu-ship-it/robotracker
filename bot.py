"""
TradeOlympo - Bot de Trading Autónomo
Estrategia de los 3 Jueces (Tech Stocks Edition)

Lógica de Trading:
- Juez 1 (Tendencia): Precio > SMA 200
- Juez 2 (Oportunidad): RSI < 70 (no sobrecomprado)
- Juez 3 (Momentum): Precio > SMA 20

Ejecuta COMPRA solo si los 3 jueces aprueban y no hay posición abierta.
Tercera modificacion manual por Gemini
"""
import os
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT')

# WATCHLIST (Tech Giants)
WATCHLIST = ['NVDA', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'AMD']

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
    print(f"--- 🚀 INICIANDO VERSIÓN FINAL (DÍAS) - {datetime.now()} ---")
    
    if not API_KEY or not SECRET_KEY:
        print("❌ ERROR: No hay API KEYS.")
        return

    api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')
    
    # Verificar Mercado
    try:
        clock = api.get_clock()
        print(f"🕐 Mercado Abierto: {clock.is_open}")
    except:
        print("⚠️ No se pudo verificar horario. Continuando...")

    # BUCLE DE ANÁLISIS
    for symbol in WATCHLIST:
        try:
            print(f"\n🔍 Analizando: {symbol}...")
            
            # --- SOLICITUD DE DATOS DIARIOS (Day) ---
            # Pedimos 365 días para asegurar SMA 200
            bars = api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=365).df
            
            # Debug: Mostrar cuántos datos llegaron
            print(f"   📥 Datos descargados: {len(bars)} días.")

            if len(bars) < 200:
                print(f"   ⚠️ Aún con TimeFrame.Day, hay pocos datos ({len(bars)}). Saltando.")
                continue
                
            # Datos listos
            closes = bars['close']
            current_price = closes.iloc[-1]
            
            # Indicadores
            rsi = calcular_rsi(closes).iloc[-1]
            sma_200 = calcular_sma(closes, 200).iloc[-1]
            sma_20 = calcular_sma(closes, 20).iloc[-1]
            
            print(f"   📊 Precio: ${current_price:.2f} | RSI: {rsi:.2f} | SMA200: {sma_200:.2f} | SMA20: {sma_20:.2f}")
            
            # --- LOS 3 JUECES ---
            juez_tendencia = current_price > sma_200
            juez_oportunidad = rsi < 70
            juez_momentum = current_price > sma_20
            
            if juez_tendencia and juez_oportunidad and juez_momentum:
                print(f"   ✅ COMPRAR {symbol} (Aprobado)")
                
                # Verificar posición
                try:
                    pos = api.get_position(symbol)
                    if int(pos.qty) > 0:
                        print("   ✋ Ya tenemos posición. Nada que hacer.")
                        continue
                except:
                    pass 
                
                # Ejecutar
                api.submit_order(symbol=symbol, qty=1, side='buy', type='market', time_in_force='gtc')
                print("   🚀 ORDEN ENVIADA.")
                
            else:
                print(f"   ❌ DESCARTADO (Tendencia:{juez_tendencia}, RSI:{juez_oportunidad}, Mom:{juez_momentum})")
                
        except Exception as e:
            print(f"   Error en {symbol}: {e}")

    print("\n--- FIN DEL ANÁLISIS ---")

if __name__ == "__main__":
    run_bot()
