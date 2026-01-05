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
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
    print(f"--- 🚀 INICIANDO VERSIÓN 'MIRADA PROFUNDA' - {datetime.now()} ---")
    
    if not API_KEY or not SECRET_KEY:
        print("❌ ERROR: No hay API KEYS.")
        return

    api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')
    
    # Calcular fecha de inicio (Hace 700 días para asegurar datos de sobra)
    fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')
    print(f"📅 Solicitando datos desde: {fecha_inicio}")

    # BUCLE DE ANÁLISIS
    for symbol in WATCHLIST:
        try:
            print(f"\n🔍 Analizando: {symbol}...")
            
            # --- FIX: SOLICITUD EXPLÍCITA CON FECHA DE INICIO Y FEED IEX ---
            bars = api.get_bars(
                symbol, 
                tradeapi.TimeFrame.Day, 
                start=fecha_inicio,  # OBLIGATORIO: Fecha de inicio
                limit=300,
                feed='iex'           # OBLIGATORIO: Feed gratuito (IEX)
            ).df
            
            print(f"   📥 Datos descargados: {len(bars)} días.")

            if len(bars) < 200:
                print(f"   ⚠️ Insuficiente historial ({len(bars)}). Saltando.")
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
                print(f"   ✅ APROBADO: {symbol}")
                
                # Verificar posición
                try:
                    pos = api.get_position(symbol)
                    if int(pos.qty) > 0:
                        print("   ✋ Ya tenemos posición. Mantener.")
                        continue
                except:
                    pass 
                
                # Ejecutar
                api.submit_order(symbol=symbol, qty=1, side='buy', type='market', time_in_force='day')
                print("   🚀 ORDEN ENVIADA.")
                
            else:
                # Mostrar por qué falló
                razones = []
                if not juez_tendencia: razones.append(f"Tendencia Bajista (Precio < {sma_200:.2f})")
                if not juez_oportunidad: razones.append(f"RSI Alto ({rsi:.2f})")
                if not juez_momentum: razones.append(f"Sin Momentum (Precio < {sma_20:.2f})")
                print(f"   ❌ DESCARTADO: {', '.join(razones)}")
                
        except Exception as e:
            print(f"   Error en {symbol}: {e}")

    print("\n--- FIN DEL ANÁLISIS ---")

if __name__ == "__main__":
    run_bot()
