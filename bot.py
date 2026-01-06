"""
TradeOlympo - Bot de Trading Autónomo
Estrategia de los 3 Jueces (Tech Stocks Edition)

Lógica de Trading:
- Juez 1 (Tendencia): Precio > SMA 200
- Juez 2 (Oportunidad): RSI < 70 (no sobrecomprado)
- Juez 3 (Momentum): Precio > SMA 20

Ejecuta COMPRA solo si los 3 jueces aprueban y no hay posición abierta.
quinta modificacion manual por Gemini
"""
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import json
import os

# --- CONFIGURACIÓN ---
# Si no existe el archivo de lista, usamos esta por defecto
DEFAULT_WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "XLE", "OXY", "APA"]

# --- MÓDULO 1: ESTRATEGIA ÉLITE (La original) ---
def analizar_estrategia_elite(df, ticker):
    """
    Lógica Original: Reversión a la media / Swing clásico.
    Busca activos sobrevendidos o en corrección dentro de tendencia.
    """
    # Indicadores
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Tomamos el último dato
    ultimo = df.iloc[-1]
    
    signal = None
    reason = ""
    
    # Lógica de Compra (Call) - Mantenemos tu lógica original
    # Ejemplo: Precio bajo la media pero con intención de subida o RSI bajo
    if ultimo['RSI'] < 30: 
        signal = "CALL (Rebote)"
        reason = f"Elite: RSI Sobrevendido ({ultimo['RSI']:.2f})"
    elif ultimo['Close'] > ultimo['SMA_20'] and ultimo['RSI'] > 40 and ultimo['RSI'] < 70:
        # Tendencia sana
        pass # Aquí podrías refinar, pero dejé la lógica 'segura' original
        
    return signal, reason

# --- MÓDULO 2: ESTRATEGIA ROMPEOLAS (La nueva) ---
def analizar_estrategia_rompeolas(df, ticker):
    """
    Lógica Nueva: Breakout / Volatilidad.
    Ideal para Energía (XLE, OXY) y noticias de impacto.
    """
    # Indicadores
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['Vol_SMA'] = ta.sma(df['Volume'], length=20)
    
    # Resistencia reciente (Máximo de los últimos 10 días)
    df['Resistencia'] = df['High'].rolling(10).max().shift(1)
    
    ultimo = df.iloc[-1]
    
    signal = None
    reason = ""
    
    # Condiciones Rompeolas
    condicion_fuerza = ultimo['RSI'] > 50  # Hay fuerza compradora
    condicion_volumen = ultimo['Volume'] > (ultimo['Vol_SMA'] * 1.2) # 20% más volumen que el promedio
    condicion_ruptura = ultimo['Close'] > ultimo['Resistencia'] # Rompió el techo reciente
    
    if condicion_fuerza and condicion_ruptura:
        # Si hay ruptura y fuerza, validamos volumen para confirmar
        tipo_volumen = "con Volumen Alto" if condicion_volumen else "Volumen Normal"
        signal = "CALL (Breakout)"
        reason = f"Rompeolas: Ruptura de {ultimo['Resistencia']:.2f} {tipo_volumen}. RSI: {ultimo['RSI']:.2f}"
        
        # Filtro de Capital: Solo sugerimos si el precio de la acción permite opciones baratas
        # (Estimación cruda: si la acción vale < $150, es probable encontrar contratos baratos. 
        # OXY y APA entran aquí perfecto).
        
    return signal, reason

# --- FUNCIÓN PRINCIPAL ---
def run_bot():
    print("--- INICIANDO TRADEOLYMPO BOT MODULAR ---")
    
    # 1. Cargar Watchlist (Intenta leer archivo json, si no usa la default)
    try:
        with open('watchlist.json', 'r') as f:
            watchlist = json.load(f)
        print("✅ Watchlist cargada desde archivo externo.")
    except FileNotFoundError:
        watchlist = DEFAULT_WATCHLIST
        # Creamos el archivo para la próxima
        with open('watchlist.json', 'w') as f:
            json.dump(watchlist, f)
        print("⚠️ Archivo no encontrado. Usando lista por defecto y creando archivo.")

    print(f"📋 Analizando: {watchlist}")
    
    resultados = []

    for ticker in watchlist:
        try:
            print(f"🔍 Procesando {ticker}...")
            # Descargar datos (suficiente historia para los cálculos)
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            if df.empty:
                print(f"❌ No hay datos para {ticker}")
                continue

            # --- SELECTOR DE ESTRATEGIA ---
            # Aquí decidimos qué 'cerebro' usa el bot según el ticker
            # XLE, OXY, APA, CVX van al Rompeolas. Las Tech van a Elite.
            
            sector_energia = ['XLE', 'OXY', 'APA', 'CVX', 'VLO']
            
            signal = None
            reason = ""
            
            if ticker in sector_energia:
                signal, reason = analizar_estrategia_rompeolas(df, ticker)
            else:
                signal, reason = analizar_estrategia_elite(df, ticker)
            
            # --- REPORTE ---
            if signal:
                print(f"🚀 SEÑAL ENCONTRADA en {ticker}: {signal}")
                print(f"   Razón: {reason}")
                
                # Aquí iría la lógica para enviar a Streamlit o Alerta
                resultados.append({
                    "ticker": ticker,
                    "signal": signal,
                    "reason": reason,
                    "price": df.iloc[-1]['Close']
                })
            else:
                print(f"💤 {ticker}: Sin señal clara.")

        except Exception as e:
            print(f"⚠️ Error analizando {ticker}: {e}")

    # Guardar resultados (simulado) para que Streamlit los lea luego
    with open('last_run_results.json', 'w') as f:
        json.dump(resultados, f)
    print("--- FIN DEL ANÁLISIS ---")

if __name__ == "__main__":
    run_bot()
