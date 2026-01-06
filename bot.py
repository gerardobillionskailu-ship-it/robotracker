"""
TradeOlympo - Bot de Trading Autónomo (Arquitectura Modular v2.0)

ESTRATEGIAS IMPLEMENTADAS:
1. Estrategia Élite: Reversión a la media para Tech stocks (RSI < 30)
2. Estrategia Rompeolas: Breakout de energía (Resistencia 20d + RSI > 50 + Volumen > 150%)

Modo: ANÁLISIS Y RECOMENDACIONES
Fuente de Datos: Alpaca API (via variables de entorno)
"""
import pandas as pd
import pandas_ta as ta
import json
import os
from datetime import datetime, timedelta

# --- CONFIGURACIÓN INICIAL ---
DEFAULT_WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "XLE", "OXY", "APA", "CVX"]
SECTOR_ENERGIA = ['XLE', 'OXY', 'APA', 'CVX', 'VLO', 'HAL', 'COP', 'SLB', 'BKR']

# Filtro de calidad: Solo analizar acciones con volumen promedio > 1M
MIN_VOLUME_THRESHOLD = 1_000_000

# --- FUNCIONES DE CONFIGURACIÓN ---

def load_watchlist():
    """
    Lee la watchlist desde watchlist.json con soporte para múltiples formatos:
    - Formato simple: ["NVDA", "TSLA", ...]
    - Formato estructurado: {"strategy_elite": {...}, "strategy_rompeolas": {...}}
    """
    try:
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                content = f.read()
                if not content.strip():
                    return DEFAULT_WATCHLIST

                config = json.loads(content)

                # Detectar formato
                if isinstance(config, list):
                    # Formato simple
                    return [x.strip().upper() for x in config if x.strip()]
                elif isinstance(config, dict):
                    # Formato estructurado - extraer todos los tickers
                    tickers = []
                    if 'strategy_elite' in config and config['strategy_elite'].get('enabled', True):
                        tickers.extend(config['strategy_elite'].get('symbols', []))
                    if 'strategy_rompeolas' in config and config['strategy_rompeolas'].get('enabled', True):
                        tickers.extend(config['strategy_rompeolas'].get('symbols', []))
                    return list(set([x.strip().upper() for x in tickers if x.strip()])) or DEFAULT_WATCHLIST

        # Si no existe, crear con formato simple
        with open('watchlist.json', 'w') as f:
            json.dump(DEFAULT_WATCHLIST, f, indent=2)
        return DEFAULT_WATCHLIST

    except Exception as e:
        print(f"⚠️ Error cargando watchlist: {e}. Usando defecto.")
        return DEFAULT_WATCHLIST

# --- FUNCIONES DE DATOS (ALPACA API) ---

def fetch_data_alpaca(symbol, days=60):
    """
    Descarga datos históricos usando Alpaca API.
    Lee credenciales desde variables de entorno.

    Returns:
        pd.DataFrame con columnas: Open, High, Low, Close, Volume
    """
    try:
        import alpaca_trade_api as tradeapi

        # Leer variables de entorno (configuradas en GitHub Actions)
        api_key = os.environ.get('ALPACA_API_KEY', '')
        secret_key = os.environ.get('ALPACA_SECRET_KEY', '')
        endpoint = os.environ.get('ALPACA_ENDPOINT', 'https://paper-api.alpaca.markets')

        if not api_key or not secret_key:
            print(f"⚠️ Credenciales de Alpaca no configuradas en variables de entorno")
            return pd.DataFrame()

        # Conectar a Alpaca API
        api = tradeapi.REST(api_key, secret_key, endpoint, api_version='v2')

        # Calcular fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Descargar datos
        bars = api.get_bars(
            symbol,
            tradeapi.TimeFrame.Day,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        ).df

        if bars.empty:
            return pd.DataFrame()

        # Renombrar columnas para consistencia
        df = bars.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })

        # Resetear índice para tener fecha como columna
        df = df.reset_index()
        df = df.rename(columns={'timestamp': 'Date'})
        df = df.set_index('Date')

        return df

    except Exception as e:
        print(f"❌ Error descargando datos de {symbol}: {e}")
        return pd.DataFrame()

# --- FUNCIONES AUXILIARES ---

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

def log_message(message):
    """Escribe mensaje en consola y en archivo bot_logs.txt"""
    print(message)
    try:
        with open('bot_logs.txt', 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"⚠️ No se pudo escribir log: {e}")

# --- MÓDULO 1: ESTRATEGIA ÉLITE (Tech / Reversión) ---

def analizar_estrategia_elite(df, ticker):
    """
    ESTRATEGIA ÉLITE (Reversión a la Media)
    Enfoque: Swing Trading Clásico / Reversión a la Media.
    Ideal para: NVDA, TSLA, AAPL en días normales.

    Lógica:
    - RSI < 30 (sobreventa extrema)
    - Precio > SMA 200 (tendencia alcista de fondo)
    """
    # Indicadores
    df['SMA_20'] = ta.sma(df['Close'], length=20)
    df['SMA_200'] = ta.sma(df['Close'], length=200) if len(df) >= 200 else ta.sma(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)

    ultimo = df.iloc[-1]
    signal = None
    reason = ""

    # Lógica de Entrada
    # 1. Rebote por sobreventa extrema
    if ultimo['RSI'] < 30:
        # Verificar tendencia de fondo
        if ultimo['Close'] > ultimo['SMA_200']:
            signal = "CALL (Rebote Técnico)"
            reason = f"Elite: Activo sobrevendido (RSI {ultimo['RSI']:.2f}) en tendencia alcista. Posible rebote a la media."
        else:
            signal = "WATCHLIST (RSI Bajo en Downtrend)"
            reason = f"Elite: RSI {ultimo['RSI']:.2f} bajo pero precio < SMA200. Esperar confirmación."

    # 2. Continuación de tendencia (Pullback sano)
    elif ultimo['Close'] > ultimo['SMA_20'] and 40 < ultimo['RSI'] < 55:
        # Lógica conservadora, busca entradas cuando el RSI no está caliente
        signal = "WATCHLIST (Pullback Sano)"
        reason = f"Elite: Precio sobre SMA20, RSI {ultimo['RSI']:.2f} en zona neutral. Monitorear."

    return signal, reason

# --- MÓDULO 2: ESTRATEGIA ROMPEOLAS (Energía / Momentum) ---

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
    # Indicadores
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['Vol_SMA'] = ta.sma(df['Volume'], length=20)
    # Resistencia: Máximo de los últimos 20 días (sin incluir hoy)
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
                f"   - Volumen: {int(ultimo['Volume']):,} (>150% del promedio)\n"
                f"   - RSI: {ultimo['RSI']:.2f} (Tendencia fuerte)"
                f"{contrato}"
            )
        else:
            # Si rompe pero sin volumen, alerta suave
            signal = "WATCHLIST (Breakout sin Volumen)"
            reason = f"Rompeolas: Breakout de ${ultimo['Resistencia_20d']:.2f} pero volumen insuficiente. Monitorear."

    return signal, reason

# --- FUNCIÓN PRINCIPAL (ORQUESTADOR) ---

def run_bot():
    """Función principal del bot con arquitectura híbrida"""
    log_message("=" * 60)
    log_message(f"🤖 INICIANDO TRADEOLYMPO AUTO-BOT")
    log_message(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log_message("=" * 60)

    # 1. Cargar Watchlist (compatible con múltiples formatos)
    watchlist = load_watchlist()
    log_message(f"📋 Tickers a analizar ({len(watchlist)}): {', '.join(watchlist)}\n")

    resultados = []

    # 2. Bucle de Análisis
    for ticker in watchlist:
        try:
            log_message(f"\n🔍 Analizando {ticker}...")

            # Descargar datos usando Alpaca API (60 días)
            df = fetch_data_alpaca(ticker, days=60)

            if df.empty or len(df) < 20:
                log_message(f"   ❌ Datos insuficientes ({len(df)} días)")
                continue

            # --- FILTRO DE CALIDAD: Volumen promedio ---
            avg_volume = df['Volume'].mean()
            if avg_volume < MIN_VOLUME_THRESHOLD:
                log_message(f"   ⏭️ VOLUMEN BAJO: {int(avg_volume):,} < {MIN_VOLUME_THRESHOLD:,} (Skipping)")
                continue

            # --- SELECTOR DE MÓDULO (CEREBRO) ---
            signal = None
            reason = ""

            if ticker in SECTOR_ENERGIA:
                # Usa Estrategia Rompeolas
                log_message(f"   🌊 Aplicando Estrategia Rompeolas (Energía)")
                signal, reason = analizar_estrategia_rompeolas(df, ticker)
            else:
                # Usa Estrategia Élite (Tech/General)
                log_message(f"   🏆 Aplicando Estrategia Élite (Tech)")
                signal, reason = analizar_estrategia_elite(df, ticker)

            # --- PROCESAR RESULTADOS ---
            if signal and "CALL" in signal:
                log_message(f"\n   🚀 SEÑAL ENCONTRADA: {ticker}")
                log_message(f"      Tipo: {signal}")
                log_message(f"      {reason}")

                resultados.append({
                    "ticker": ticker,
                    "signal": signal,
                    "reason": reason,
                    "price": float(df.iloc[-1]['Close']),
                    "timestamp": datetime.now().isoformat()
                })
            elif signal:
                log_message(f"   💤 {ticker}: {signal}")
            else:
                log_message(f"   💤 Sin señal clara")

        except Exception as e:
            log_message(f"   ⚠️ Error procesando {ticker}: {e}")

    # 3. Guardar Resultados
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
