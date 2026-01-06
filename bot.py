"""
TradeOlympo - Bot de Trading Autónomo
Estrategia de los 3 Jueces (Tech Stocks Edition)

Lógica de Trading:
- Juez 1 (Tendencia): Precio > SMA 200
- Juez 2 (Oportunidad): RSI < 70 (no sobrecomprado)
- Juez 3 (Momentum): Precio > SMA 20

Ejecuta COMPRA solo si los 3 jueces aprueban y no hay posición abierta.
sexta modificacion manual por Gemini
"""
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import json
import os
from datetime import datetime, timedelta

# --- CONFIGURACIÓN INICIAL ---
# Lista por defecto por si no existe el archivo JSON aún.
# Incluye Tech (Elite) y Energía (Rompeolas)
DEFAULT_WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "XLE", "OXY", "APA", "CVX"]

# Definimos qué tickers pertenecen al sector Energía para activar la estrategia Rompeolas
SECTOR_ENERGIA = ['XLE', 'OXY', 'APA', 'CVX', 'VLO', 'HAL']

# --- FUNCIONES AUXILIARES ---

def sugerir_contrato_opciones(precio_actual):
    """
    Calcula el contrato ideal para la Estrategia Rompeolas bajo gestión de riesgo estricta.
    - Capital: Cuenta pequeña ($1,000) -> Max costo por contrato $200.
    - Vencimiento: 45-60 días (Swing).
    - Strike: ITM (In The Money) para Delta ~0.60.
    """
    hoy = datetime.now()
    fecha_minima = hoy + timedelta(days=45)
    fecha_maxima = hoy + timedelta(days=60)
    
    # Formato de fecha para lectura humana
    rango_fechas = f"{fecha_minima.strftime('%d/%m')} al {fecha_maxima.strftime('%d/%m/%Y')}"
    
    # Strike ITM: Buscamos un strike aprox 3% debajo del precio actual (Delta ~0.60 conservador)
    strike_objetivo = round(precio_actual * 0.97, 1)
    
    sugerencia = (
        f"\n   🎯 PLAN DE EJECUCIÓN (Gestión $1,000):\n"
        f"      - Vencimiento Objetivo: {rango_fechas}\n"
        f"      - Strike Sugerido: CALL ${strike_objetivo} (ITM)\n"
        f"      - Límite de Compra: NO pagar más de $2.00 ($200) por contrato.\n"
    )
    return sugerencia

# --- MÓDULO 1: ESTRATEGIA ÉLITE (Tech / Reversión) ---
def analizar_estrategia_elite(df, ticker):
    """
    ESTRATEGIA ORIGINAL (NO MODIFICADA)
    Enfoque: Swing Trading Clásico / Reversión a la Media.
    Ideal para: NVDA, TSLA, AAPL en días normales.
    """
    # Indicadores
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    ultimo = df.iloc[-1]
    signal = None
    reason = ""
    
    # Lógica de Entrada Original
    # 1. Rebote por sobreventa extrema
    if ultimo['RSI'] < 30:
        signal = "CALL (Rebote Técnico)"
        reason = f"Elite: Activo sobrevendido (RSI {ultimo['RSI']:.2f}). Posible rebote a la media."
    
    # 2. Continuación de tendencia (Pullback sano)
    elif ultimo['Close'] > ultimo['SMA_20'] and 40 < ultimo['RSI'] < 55:
        # Nota: Lógica conservadora, busca entradas cuando el RSI no está caliente
        pass 
        
    return signal, reason

# --- MÓDULO 2: ESTRATEGIA ROMPEOLAS (Energía / Momentum) ---
def analizar_estrategia_rompeolas(df, ticker):
    """
    NUEVA ESTRATEGIA (Volatilidad / Noticias)
    Enfoque: Breakout con confirmación de Volumen.
    Ideal para: XLE, OXY, APA (Crisis energética/política).
    """
    # Indicadores
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['Vol_SMA'] = ta.sma(df['Volume'], length=20)
    # Resistencia: Máximo de los últimos 20 días (sin incluir hoy, por eso shift)
    df['Resistencia_20d'] = df['High'].rolling(20).max().shift(1)
    
    ultimo = df.iloc[-1]
    signal = None
    reason = ""
    
    # --- Lógica de Disparo (Trigger) ---
    
    # 1. Ruptura (Breakout): Precio cierra por encima del techo de 20 días
    breakout = ultimo['Close'] > ultimo['Resistencia_20d']
    
    # 2. Pico de Volumen Institucional: Volumen hoy > 150% del promedio
    volumen_institucional = ultimo['Volume'] > (ultimo['Vol_SMA'] * 1.5)
    
    # 3. Fuerza: RSI > 50 (No queremos rebotes, queremos fuerza)
    fuerza = ultimo['RSI'] > 50
    
    if breakout and fuerza:
        if volumen_institucional:
            signal = "CALL (ROMPEOLAS CONFIRMADO)"
            # Generamos la sugerencia del contrato específico
            contrato = sugerir_contrato_opciones(ultimo['Close'])
            
            reason = (
                f"🌊 BREAKOUT CON VOLUMEN EN {ticker}\n"
                f"   - Precio: ${ultimo['Close']:.2f} rompió resistencia de ${ultimo['Resistencia_20d']:.2f}\n"
                f"   - Volumen: {int(ultimo['Volume'])} (>150% del promedio)\n"
                f"   - RSI: {ultimo['RSI']:.2f} (Tendencia fuerte)"
                f"{contrato}"
            )
        else:
            # Si rompe pero sin volumen, lo marcamos como observación
            # signal = "WATCHLIST (Breakout sin Volumen)" # Descomentar si quieres alertas suaves
            pass

    return signal, reason

# --- FUNCIÓN PRINCIPAL (ORQUESTADOR) ---
def run_bot():
    print("--- 🤖 INICIANDO TRADEOLYMPO AUTO-BOT ---")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. Cargar Watchlist (Sistema de sincronización)
    # Intenta leer watchlist.json, si no existe, lo crea con los defaults.
    watchlist = []
    try:
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                content = f.read()
                if content:
                    watchlist = json.loads(content)
                    print("✅ Watchlist cargada desde archivo externo.")
                else:
                    watchlist = DEFAULT_WATCHLIST
        else:
            watchlist = DEFAULT_WATCHLIST
            with open('watchlist.json', 'w') as f:
                json.dump(watchlist, f)
            print("⚠️ Archivo json creado con lista por defecto.")
    except Exception as e:
        print(f"⚠️ Error cargando watchlist: {e}. Usando defecto.")
        watchlist = DEFAULT_WATCHLIST

    # Limpiar duplicados y formatear
    watchlist = list(set([x.strip().upper() for x in watchlist if x.strip()]))
    print(f"📋 Tickers a analizar: {watchlist}")
    
    resultados = []

    # 2. Bucle de Análisis
    for ticker in watchlist:
        try:
            # Descargar datos (60 días es suficiente para medias de 20 y RSI)
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            if df.empty or len(df) < 20:
                print(f"❌ {ticker}: Datos insuficientes.")
                continue

            # --- SELECTOR DE MÓDULO (CEREBRO) ---
            signal = None
            reason = ""
            
            if ticker in SECTOR_ENERGIA:
                # Usa Estrategia Rompeolas
                signal, reason = analizar_estrategia_rompeolas(df, ticker)
            else:
                # Usa Estrategia Élite (Tech/General)
                signal, reason = analizar_estrategia_elite(df, ticker)
            
            # --- PROCESAR RESULTADOS ---
            if signal:
                print(f"\n🚀 SEÑAL ENCONTRADA: {ticker}")
                print(f"   Tipo: {signal}")
                print(f"   Detalle: {reason}")
                
                resultados.append({
                    "ticker": ticker,
                    "signal": signal,
                    "reason": reason,
                    "price": float(df.iloc[-1]['Close']),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Log simple para no ensuciar la consola
                print(f"💤 {ticker}: Sin señal clara.")

        except Exception as e:
            print(f"⚠️ Error procesando {ticker}: {e}")

    # 3. Guardar Resultados
    # Esto permite que Streamlit (la web) lea lo que encontró el bot
    try:
        with open('last_run_results.json', 'w') as f:
            json.dump(resultados, f, indent=4)
        print("\n💾 Resultados guardados en 'last_run_results.json'")
    except Exception as e:
        print(f"❌ Error guardando resultados: {e}")

    print("--- FIN DEL ANÁLISIS ---")

if __name__ == "__main__":
    run_bot()
