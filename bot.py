"""
TradeOlympo - Bot de Trading Autónomo v5.0

ESTRATEGIAS IMPLEMENTADAS:
1. Swing - Élite: Reversión a la media para Tech stocks (RSI < 30 + SMA 200)
2. Swing - Rompeolas: Breakout de energía (Resistencia 20d + RSI > 50 + Volumen > 150%)
3. Income - The Wheel: Venta de primas con Cash-Secured Puts y Covered Calls
4. Day Trading - ORB: Opening Range Breakout (9:30-10:00 AM)

Fuente de Datos: Alpaca API con feed IEX (gratuito)
Ejecución: Según estrategia configurada en user_config.json
Filtro de Volumen: 100,000 acciones/día promedio
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

# Filtro de calidad: Solo analizar acciones con volumen promedio > 100K
MIN_VOLUME_THRESHOLD = 100_000

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

def save_to_trade_history(trade_record):
    """
    Guarda un registro de operación en trade_history.json

    Args:
        trade_record: Dict con {date, ticker, action, strategy, quantity, price, order_id, signal}
    """
    try:
        # Leer historial existente o crear nuevo
        if os.path.exists('trade_history.json'):
            with open('trade_history.json', 'r') as f:
                history = json.load(f)
        else:
            history = []

        # Agregar nuevo registro
        history.append(trade_record)

        # Guardar actualizado
        with open('trade_history.json', 'w') as f:
            json.dump(history, f, indent=2)

        log_message(f"   📜 Operación guardada en trade_history.json")

    except Exception as e:
        log_message(f"   ⚠️ Error guardando en trade_history.json: {e}")

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

def load_user_config():
    """
    Lee la configuración desde user_config.json (nuevo archivo centralizado)
    Este archivo es modificado por la interfaz web y sincronizado con GitHub.
    """
    try:
        # Prioridad 1: user_config.json (nuevo sistema)
        if os.path.exists('user_config.json'):
            with open('user_config.json', 'r') as f:
                config = json.load(f)
                log_message(f"✅ Configuración cargada desde user_config.json")
                log_message(f"   Estrategia activa: {config.get('active_strategy', 'N/A')}")
                log_message(f"   Última actualización: {config.get('last_updated', 'N/A')}")
                return config

        # Fallback: watchlist.json (sistema antiguo)
        if os.path.exists('watchlist.json'):
            with open('watchlist.json', 'r') as f:
                content = f.read()
                if content.strip():
                    config_data = json.loads(content)

                    if isinstance(config_data, list):
                        return {
                            'active_strategy': 'modular',
                            'watchlist': [x.strip().upper() for x in config_data if x.strip()]
                        }
                    elif isinstance(config_data, dict):
                        tickers = []
                        if 'strategy_elite' in config_data:
                            tickers.extend(config_data['strategy_elite'].get('symbols', []))
                        if 'strategy_rompeolas' in config_data:
                            tickers.extend(config_data['strategy_rompeolas'].get('symbols', []))
                        return {
                            'active_strategy': 'modular',
                            'watchlist': list(set([x.strip().upper() for x in tickers if x.strip()]))
                        }

        # Fallback final: trading_config.json
        return load_config()

    except Exception as e:
        log_message(f"⚠️ Error cargando user_config.json: {e}")
        return load_config()

def load_watchlist():
    """
    Extrae la watchlist desde la configuración del usuario
    """
    try:
        config = load_user_config()
        watchlist = config.get('watchlist', DEFAULT_WATCHLIST)

        if not watchlist:
            log_message("⚠️ Watchlist vacía, usando default")
            return DEFAULT_WATCHLIST

        return [x.strip().upper() for x in watchlist if x.strip()]
    except Exception as e:
        log_message(f"⚠️ Error extrayendo watchlist: {e}. Usando defecto.")
        return DEFAULT_WATCHLIST

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
    vol_sma = calcular_sma(volumes, 30)  # Sincronizado con app.py (30 días)
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

# ========== MÓDULO 3: ESTRATEGIA THE WHEEL (Opciones / Income) ==========

def analizar_estrategia_wheel(api, ticker):
    """
    ESTRATEGIA THE WHEEL (Opciones - Generación de Ingresos)
    Enfoque: Venta de primas (theta decay) con Cash-Secured Puts y Covered Calls.
    Ideal para: AAPL, MSFT, SPY, QQQ (alta liquidez en opciones).

    Lógica del Estado de Inventario:
    - Estado A (Cash disponible, NO tengo acciones): Vender Cash-Secured Put (CSP)
    - Estado B (Tengo 100+ acciones asignadas): Vender Covered Call (CC)

    Requisitos:
    - Margin Account con Options Tier 2
    - Colateral: $10,000+ por contrato
    - Delta objetivo: ~0.30 (70% probabilidad de expirar OTM)
    - DTE: 30-45 días
    """
    try:
        # Verificar posición actual (inventario)
        positions = api.list_positions()
        current_position = None

        for pos in positions:
            if pos.symbol == ticker:
                current_position = pos
                break

        shares_owned = int(current_position.qty) if current_position else 0

        signal = None
        reason = ""

        # ========== ESTADO A: CASH-SECURED PUT ==========
        if shares_owned == 0:
            signal = "WHEEL_CSP (Vender PUT)"
            reason = (
                f"🔄 THE WHEEL - FASE 1: Cash-Secured Put\n"
                f"   Ticker: {ticker}\n"
                f"   Estado: Sin acciones en inventario\n"
                f"   Acción recomendada: Vender 1 PUT con Delta ~0.30\n"
                f"   DTE objetivo: 30-45 días\n"
                f"   Nota: El bot necesita API de opciones configurada en Alpaca\n"
                f"   (Esta versión solo detecta oportunidad, ejecución manual)"
            )

        # ========== ESTADO B: COVERED CALL ==========
        elif shares_owned >= 100:
            # Verificar cost basis (precio promedio de compra)
            cost_basis = float(current_position.avg_entry_price)

            signal = "WHEEL_CC (Vender CALL)"
            reason = (
                f"🔄 THE WHEEL - FASE 2: Covered Call\n"
                f"   Ticker: {ticker}\n"
                f"   Acciones en inventario: {shares_owned}\n"
                f"   Cost Basis: ${cost_basis:.2f}\n"
                f"   Acción recomendada: Vender 1 CALL con strike > ${cost_basis:.2f}\n"
                f"   DTE objetivo: 30-45 días\n"
                f"   Nota: Asegura ganancia vendiendo por encima del coste"
            )

        else:
            # Caso: Tengo acciones pero menos de 100 (no se puede hacer CC)
            signal = "WATCHLIST (Acciones insuficientes para CC)"
            reason = f"The Wheel: Tienes {shares_owned} acciones. Necesitas 100 para vender Covered Call."

        return signal, reason

    except Exception as e:
        log_message(f"⚠️ Error en estrategia The Wheel para {ticker}: {e}")
        return None, ""

# ========== MÓDULO 4: ESTRATEGIA ORB (Day Trading) ==========

def analizar_estrategia_orb(api, ticker):
    """
    ESTRATEGIA ORB (Opening Range Breakout - Day Trading)
    Enfoque: Aprovechar la volatilidad de la apertura del mercado.
    Ideal para: SPY, QQQ, TSLA, NVDA (alta liquidez y volatilidad).

    Lógica:
    - FASE 1 (9:30-10:00 AM ET): Observación, registrar máximo y mínimo
    - FASE 2 (10:00 AM-3:55 PM ET): Ejecutar breakout si precio > máximo + volumen alto
    - FASE 3 (3:55 PM ET): Cerrar TODAS las posiciones (no overnight)

    Requisitos:
    - Margin Account con $25,000+ (PDT rule)
    - Datos en tiempo real (barras de 5 minutos)
    """
    try:
        now_et = datetime.now(pytz.timezone('America/New_York'))
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        range_end = now_et.replace(hour=10, minute=0, second=0, microsecond=0)
        market_close = now_et.replace(hour=15, minute=55, second=0, microsecond=0)

        signal = None
        reason = ""

        # ========== FASE 1: OBSERVACIÓN (9:30-10:00 AM) ==========
        if market_open <= now_et < range_end:
            signal = "ORB_OBSERVING (Fase 1: Observando Rango)"
            reason = (
                f"⚡ ORB - FASE 1: Observación del Rango de Apertura\n"
                f"   Hora actual: {now_et.strftime('%H:%M:%S ET')}\n"
                f"   Estado: Registrando máximo y mínimo (9:30-10:00 AM)\n"
                f"   Acción: NO operar aún, esperar hasta las 10:00 AM"
            )

        # ========== FASE 2: EJECUCIÓN (10:00 AM - 3:55 PM) ==========
        elif range_end <= now_et < market_close:
            # Obtener datos de 5 minutos del rango de apertura
            bars_5min = api.get_bars(
                ticker,
                tradeapi.TimeFrame.Minute,
                start=market_open.strftime('%Y-%m-%d %H:%M:%S'),
                end=range_end.strftime('%Y-%m-%d %H:%M:%S'),
                feed='iex'
            ).df

            if not bars_5min.empty and len(bars_5min) >= 6:
                opening_range_high = bars_5min['high'].max()
                opening_range_low = bars_5min['low'].min()

                # Obtener precio actual
                latest_trade = api.get_latest_trade(ticker)
                current_price = float(latest_trade.price)

                # Obtener volumen actual
                current_bar = api.get_bars(
                    ticker,
                    tradeapi.TimeFrame.Minute,
                    limit=1,
                    feed='iex'
                ).df

                current_volume = current_bar['volume'].iloc[-1] if not current_bar.empty else 0

                # Calcular volumen promedio
                avg_volume = bars_5min['volume'].mean()

                # ========== DETECTAR BREAKOUT ==========
                if current_price > opening_range_high and current_volume > (avg_volume * 1.5):
                    signal = "ORB_LONG (Comprar Breakout Alcista)"
                    reason = (
                        f"⚡ ORB - FASE 2: Breakout Alcista Detectado\n"
                        f"   Precio actual: ${current_price:.2f}\n"
                        f"   Rango apertura: ${opening_range_low:.2f} - ${opening_range_high:.2f}\n"
                        f"   Breakout: Precio > Máximo del rango\n"
                        f"   Volumen confirmado: {int(current_volume):,} > {int(avg_volume * 1.5):,}\n"
                        f"   ⚠️ RECORDATORIO: Cerrar posición antes de 3:55 PM ET"
                    )
                else:
                    signal = "ORB_WAITING (Esperando Breakout)"
                    reason = (
                        f"⚡ ORB - FASE 2: Esperando Breakout\n"
                        f"   Precio actual: ${current_price:.2f}\n"
                        f"   Rango apertura: ${opening_range_low:.2f} - ${opening_range_high:.2f}\n"
                        f"   Condición: Precio debe romper ${opening_range_high:.2f} con volumen alto"
                    )
            else:
                signal = "ORB_NO_DATA (Datos insuficientes)"
                reason = "ORB: No hay suficientes datos del rango de apertura."

        # ========== FASE 3: CIERRE DE POSICIONES (3:55 PM+) ==========
        else:
            signal = "ORB_CLOSE_ALL (Cerrar todas las posiciones)"
            reason = (
                f"⚡ ORB - FASE 3: Cierre de Mercado\n"
                f"   Hora actual: {now_et.strftime('%H:%M:%S ET')}\n"
                f"   Acción: Cerrar TODAS las posiciones ORB\n"
                f"   Nota: Estrategia NO deja posiciones overnight"
            )

        return signal, reason

    except Exception as e:
        log_message(f"⚠️ Error en estrategia ORB para {ticker}: {e}")
        return None, ""

# ========== FUNCIÓN PRINCIPAL (ORQUESTADOR) ==========

def run_bot():
    """Función principal del bot con arquitectura modular"""
    config = load_config()

    log_message("=" * 60)
    log_message(f"🤖 INICIANDO TRADEOLYMPO v5.0 AUTO-BOT")
    log_message(f"📅 Fecha: {datetime.now(pytz.timezone('America/New_York'))}")
    log_message(f"📋 Estrategia activa: {config.get('active_strategy', 'rompeolas')}")
    log_message(f"📊 Estrategias disponibles: elite, rompeolas, wheel, orb")
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

            # Obtener estrategia activa desde configuración
            active_strategy = config.get('active_strategy', 'rompeolas')

            if active_strategy == 'wheel':
                log_message(f"   🔄 Aplicando Estrategia The Wheel (Opciones)")
                signal, reason = analizar_estrategia_wheel(api, symbol)

            elif active_strategy == 'orb':
                log_message(f"   ⚡ Aplicando Estrategia ORB (Day Trading)")
                signal, reason = analizar_estrategia_orb(api, symbol)

            elif active_strategy == 'rompeolas' or symbol in SECTOR_ENERGIA:
                log_message(f"   🌊 Aplicando Estrategia Rompeolas (Energía)")
                signal, reason = analizar_estrategia_rompeolas(bars, symbol)

            else:  # elite (default)
                log_message(f"   🏆 Aplicando Estrategia Élite (Tech)")
                signal, reason = analizar_estrategia_elite(bars, symbol)

            # --- PROCESAR RESULTADOS ---
            if signal and "CALL" in signal:
                log_message(f"\n   🚀 SEÑAL ENCONTRADA: {symbol}")
                log_message(f"      Tipo: {signal}")
                log_message(f"      {reason}")

                current_price = float(bars.iloc[-1]['close'])

                # EJECUCIÓN REAL: Comprar 10 acciones (PRODUCCIÓN)
                try:
                    log_message(f"\n   📈 EJECUTANDO ORDEN DE COMPRA:")
                    log_message(f"      Ticker: {symbol}")
                    log_message(f"      Cantidad: 10 acciones")
                    log_message(f"      Tipo: Market Order")
                    log_message(f"      Precio aproximado: ${current_price:.2f}")

                    order = api.submit_order(
                        symbol=symbol,
                        qty=10,  # PRODUCCIÓN: 10 acciones
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )

                    log_message(f"   ✅ ORDEN EJECUTADA EXITOSAMENTE")
                    log_message(f"      Order ID: {order.id}")
                    log_message(f"      Status: {order.status}")

                    # Timestamp en New York Time
                    ny_time = datetime.now(pytz.timezone('America/New_York'))

                    resultados.append({
                        "ticker": symbol,
                        "signal": signal,
                        "reason": reason,
                        "price": current_price,
                        "order_id": order.id,
                        "order_status": order.status,
                        "quantity": 10,
                        "timestamp": ny_time.isoformat(),
                        "strategy": active_strategy
                    })

                    # Guardar en bitácora persistente
                    save_to_trade_history({
                        "date": ny_time.strftime('%Y-%m-%d %H:%M:%S ET'),
                        "ticker": symbol,
                        "action": "BUY",
                        "strategy": active_strategy,
                        "quantity": 10,
                        "price": current_price,
                        "order_id": order.id,
                        "signal": signal
                    })

                except Exception as order_error:
                    log_message(f"   ❌ ERROR AL EJECUTAR ORDEN: {order_error}")
                    ny_time = datetime.now(pytz.timezone('America/New_York'))
                    resultados.append({
                        "ticker": symbol,
                        "signal": signal,
                        "reason": reason,
                        "price": current_price,
                        "error": str(order_error),
                        "timestamp": ny_time.isoformat()
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
