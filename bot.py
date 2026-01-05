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

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT')

# TUS ACCIONES FAVORITAS (TECH WATCHLIST)
WATCHLIST = ['NVDA', 'TSLA', 'AAPL', 'AMZN', 'MSFT', 'AMD']

# --- HERRAMIENTAS DE ANÁLISIS ---
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
    print(f"--- 🧠 INICIANDO ANÁLISIS (VERSIÓN DIARIA CORREGIDA): {datetime.now()} ---")
    
    if not API_KEY or not SECRET_KEY:
        print("ERROR: Credenciales no encontradas.")
        return

    api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')
    
    # Verificar Mercado
    try:
        clock = api.get_clock()
        print(f"🕐 Mercado Abierto: {clock.is_open}")
    except Exception as e:
        print(f"Nota: No se pudo verificar horario (Error: {e}). Continuando igual...")
    
    # BUCLE PRINCIPAL
    for symbol in WATCHLIST:
        try:
            print(f"\n🔍 Analizando: {symbol}...")
            
            # --- EL FIX MAESTRO: PEDIR DÍAS (Day), NO HORAS ---
            # Pedimos 300 días de historia para asegurar que la SMA 200 funcione
            bars = api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=300).df
            
            if len(bars) < 200:
                print(f"   ⚠️ Datos insuficientes para {symbol} ({len(bars)} velas). Saltando.")
                continue
                
            # Limpieza de datos
            closes = bars['close']
            current_price = closes.iloc[-1]
            
            # Calcular Indicadores
            rsi = calcular_rsi(closes).iloc[-1]
            sma_200 = calcular_sma(closes, 200).iloc[-1]
            sma_20 = calcular_sma(closes, 20).iloc[-1]
            
            print(f"   📊 Precio: ${current_price:.2f} | RSI: {rsi:.2f} | SMA200: {sma_200:.2f} | SMA20: {sma_20:.2f}")
            
            # --- EL TRIBUNAL (3 JUECES) ---
            juez_tendencia = current_price > sma_200      # Juez 1: Tendencia Alcista
            juez_oportunidad = rsi < 70                   # Juez 2: No está caro
            juez_momentum = current_price > sma_20        # Juez 3: Fuerza corto plazo
            
            # Veredicto
            if juez_tendencia and juez_oportunidad and juez_momentum:
                print(f"   ✅ VEREDICTO: COMPRAR {symbol} (3/3 Jueces Aprobado)")
                
                # Verificar si ya tenemos la acción
                try:
                    pos = api.get_position(symbol)
                    if int(pos.qty) > 0:
                        print(f"   ✋ Ya tienes {symbol}. Mantenemos posición.")
                        continue
                except:
                    pass # No hay posición
                
                # EJECUTAR COMPRA
                print(f"   🚀 ENVIANDO ORDEN DE COMPRA POR {symbol}...")
                api.submit_order(
                    symbol=symbol,
                    qty=1,
                    side='buy',
                    type='market',
                    time_in_force='gtc' # Good till cancelled
                )
                
            else:
                fallos = []
                if not juez_tendencia: fallos.append("Tendencia Bajista (Debajo SMA200)")
                if not juez_oportunidad: fallos.append(f"RSI Alto ({rsi:.0f})")
                if not juez_momentum: fallos.append("Sin Momentum (Debajo SMA20)")
                print(f"   ❌ DESCARTADO. Razones: {', '.join(fallos)}")
                
        except Exception as e:
            print(f"   Error analizando {symbol}: {e}")

    print("\n--- 🏁 ANÁLISIS FINALIZADO ---")

if __name__ == "__main__":
    run_bot()
