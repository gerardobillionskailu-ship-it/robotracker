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
import requests

# ========== CONFIGURACIÓN ==========

API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')

# 🔒 MODO FORZADO: PAPER TRADING (Hardcoded para bypass variables de entorno)
ENDPOINT = "https://paper-api.alpaca.markets"

# 📱 TELEGRAM CONFIGURATION
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ⏰ REPORTE EJECUTIVO (Tracking global)
last_report_time = None
tickers_scanned_count = 0

# 💬 TELEGRAM COMMAND LISTENER (Tracking last update)
last_update_id = None

# 🔬 MODO FLASH TEST: Umbrales 20% más sensibles
FLASH_TEST_MODE = True  # Cambiar a False para desactivar
SENSITIVITY_MULTIPLIER = 0.8 if FLASH_TEST_MODE else 1.0  # 20% más sensible

# Watchlist por defecto
DEFAULT_WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "XLE", "OXY", "APA", "CVX"]
SECTOR_ENERGIA = ['XLE', 'OXY', 'APA', 'CVX', 'VLO', 'HAL', 'COP', 'SLB', 'BKR']

# 📋 PRESET WATCHLISTS (Para comando /radar interactivo)
PRESET_WATCHLISTS = {
    "energia": {
        "name": "🛢️ Sector Energía",
        "tickers": ['XLE', 'OXY', 'APA', 'CVX', 'VLO', 'HAL', 'COP', 'SLB', 'BKR']
    },
    "tech": {
        "name": "💻 Tech Giants",
        "tickers": ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "GOOGL", "META", "AMZN"]
    },
    "cripto": {
        "name": "🌙 Cripto 24/7",
        "tickers": ["BTC/USD", "ETH/USD"]
    },
    "mixta": {
        "name": "🎯 Mixta (Default)",
        "tickers": DEFAULT_WATCHLIST
    },
    "actual": {
        "name": "📋 Misión Actual",
        "tickers": None  # Se carga desde user_config.json
    }
}

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

def send_telegram_msg(message):
    """
    Envía un mensaje a Telegram de forma robusta

    Args:
        message: Texto del mensaje a enviar

    Returns:
        bool: True si se envió correctamente, False si falló
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        # Si no hay credenciales, no hacer nada (sin fallar el bot)
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            log_message(f"   📱 Telegram: Mensaje enviado")
            return True
        else:
            log_message(f"   ⚠️ Telegram: Error HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        log_message(f"   ⚠️ Telegram: Timeout (red lenta)")
        return False
    except requests.exceptions.ConnectionError:
        log_message(f"   ⚠️ Telegram: Error de conexión (sin internet)")
        return False
    except Exception as e:
        log_message(f"   ⚠️ Telegram: Error inesperado: {e}")
        return False

def send_telegram_msg_with_buttons(message, buttons):
    """
    Envía un mensaje a Telegram con botones InlineKeyboard

    Args:
        message: Texto del mensaje a enviar
        buttons: Lista de listas de botones [[{text, callback_data}]]

    Returns:
        bool: True si se envió correctamente, False si falló
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        # Construir InlineKeyboardMarkup
        inline_keyboard = []
        for row in buttons:
            keyboard_row = []
            for btn in row:
                keyboard_row.append({
                    "text": btn["text"],
                    "callback_data": btn["callback_data"]
                })
            inline_keyboard.append(keyboard_row)

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            log_message(f"   📱 Telegram: Mensaje con botones enviado")
            return True
        else:
            log_message(f"   ⚠️ Telegram: Error HTTP {response.status_code}")
            return False

    except Exception as e:
        log_message(f"   ⚠️ Telegram: Error enviando botones: {e}")
        return False

def answer_callback_query(callback_query_id, text=None):
    """
    Responde a un callback query (confirmación de botón presionado)

    Args:
        callback_query_id: ID del callback query
        text: Texto opcional para mostrar al usuario

    Returns:
        bool: True si se respondió correctamente
    """
    if not TELEGRAM_TOKEN:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id
        }

        if text:
            payload["text"] = text
            payload["show_alert"] = False

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200

    except Exception as e:
        log_message(f"   ⚠️ Error respondiendo callback: {e}")
        return False

def get_account_equity(api):
    """
    Obtiene el equity actual de la cuenta de Alpaca

    Args:
        api: Instancia de tradeapi.REST

    Returns:
        float: Equity actual en USD, o 0 si falla
    """
    try:
        account = api.get_account()
        return float(account.equity)
    except Exception as e:
        log_message(f"   ⚠️ Error obteniendo equity: {e}")
        return 0.0

def send_executive_report(api, watchlist):
    """
    Envía reporte ejecutivo a Telegram con resumen de misión

    Args:
        api: Instancia de tradeapi.REST
        watchlist: Lista de tickers analizados
    """
    global tickers_scanned_count

    equity = get_account_equity(api)
    ny_tz = pytz.timezone('America/New_York')
    current_time = datetime.now(ny_tz).strftime('%H:%M:%S ET')

    report_msg = (
        f"📊 <b>REPORTE EJECUTIVO</b>\n\n"
        f"🕐 Hora: {current_time}\n"
        f"✅ Tickers escaneados (periodo): <b>{tickers_scanned_count}</b>\n"
        f"💰 Equity actual: <b>${equity:,.2f}</b>\n"
        f"📋 Watchlist activa: <code>{', '.join(watchlist[:5])}</code>\n"
        f"🔬 Modo: <b>{'Flash Test (20% más sensible)' if FLASH_TEST_MODE else 'Normal'}</b>\n\n"
        f"⏰ Próximo análisis en 60 segundos\n"
        f"📈 Próximo reporte en 90 minutos"
    )

    send_telegram_msg(report_msg)

    # Reset contador
    tickers_scanned_count = 0

def should_send_report():
    """
    Verifica si deben pasar 90 minutos desde el último reporte

    Returns:
        bool: True si debe enviar reporte, False otherwise
    """
    global last_report_time

    if last_report_time is None:
        last_report_time = datetime.now()
        return True

    elapsed = (datetime.now() - last_report_time).total_seconds() / 60  # minutos
    if elapsed >= 90:
        last_report_time = datetime.now()
        return True

    return False


# ========== MÓDULO: TELEGRAM COMMAND LISTENER ==========

def get_telegram_updates():
    """
    Obtiene actualizaciones de Telegram usando getUpdates API

    Returns:
        list: Lista de updates (mensajes) o [] si falla
    """
    global last_update_id

    if not TELEGRAM_TOKEN:
        return []

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {
            "timeout": 10,
            "allowed_updates": ["message", "callback_query"]
        }

        # Si ya procesamos mensajes antes, pedir solo los nuevos
        if last_update_id is not None:
            params["offset"] = last_update_id + 1

        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])

        return []

    except Exception as e:
        log_message(f"   ⚠️ Error obteniendo updates de Telegram: {e}")
        return []

def handle_radar_command():
    """
    Maneja el comando /radar: Muestra botones para seleccionar watchlist

    Returns:
        None (envía mensaje con botones directamente)
    """
    try:
        ny_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(ny_tz).strftime('%H:%M:%S ET')

        message = (
            f"🔭 <b>RADAR TÉCNICO</b>\n\n"
            f"🕐 {current_time}\n"
            f"📋 Selecciona qué watchlist analizar:\n"
        )

        # Construir botones desde PRESET_WATCHLISTS
        buttons = []
        for key, preset in PRESET_WATCHLISTS.items():
            buttons.append([{
                "text": preset["name"],
                "callback_data": f"radar:{key}"
            }])

        send_telegram_msg_with_buttons(message, buttons)

    except Exception as e:
        log_message(f"   ⚠️ Error en /radar: {e}")
        send_telegram_msg("❌ Error mostrando opciones de radar")

def handle_radar_analysis(api, watchlist_key):
    """
    Ejecuta análisis técnico de una watchlist específica

    Args:
        api: Instancia de tradeapi.REST
        watchlist_key: Clave de PRESET_WATCHLISTS ("energia", "tech", etc.)

    Returns:
        str: Mensaje formateado con resultados
    """
    try:
        # Obtener watchlist según la clave
        if watchlist_key == "actual":
            config = load_user_config()
            watchlist = config.get('watchlist', DEFAULT_WATCHLIST)[:10]
            watchlist_name = "📋 Misión Actual"
        else:
            preset = PRESET_WATCHLISTS.get(watchlist_key)
            if not preset:
                return "❌ Watchlist no encontrada"
            watchlist = preset["tickers"][:10]
            watchlist_name = preset["name"]

        ny_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(ny_tz).strftime('%H:%M:%S ET')

        radar_lines = [
            f"🔭 <b>ANÁLISIS: {watchlist_name}</b>\n",
            f"🕐 {current_time}\n",
            f"📊 Analizando {len(watchlist)} tickers...\n"
        ]

        fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')

        for symbol in watchlist:
            try:
                # Detectar si es cripto
                if is_crypto_symbol(symbol):
                    # Cripto: usar velas de 5 minutos
                    end_time = datetime.now()
                    start_time = end_time - timedelta(hours=8)
                    bars = api.get_bars(
                        symbol,
                        tradeapi.TimeFrame(5, tradeapi.TimeFrameUnit.Minute),
                        start=start_time.isoformat(),
                        end=end_time.isoformat(),
                        feed='iex'
                    ).df

                    if not bars.empty and len(bars) >= 20:
                        closes = bars['close']
                        rsi = calcular_rsi(closes, period=14).iloc[-1]
                        price = float(closes.iloc[-1])

                        status = "🟢 COMPRA" if rsi < 40 else "⚪ NEUTRAL"
                        radar_lines.append(
                            f"\n<b>{symbol}</b>: ${price:.2f} | RSI: {rsi:.1f} {status}"
                        )
                else:
                    # Acciones: usar velas diarias
                    bars = api.get_bars(
                        symbol,
                        tradeapi.TimeFrame.Day,
                        start=fecha_inicio,
                        limit=300,
                        feed='iex'
                    ).df

                    if not bars.empty and len(bars) >= 200:
                        closes = bars['close']
                        rsi = calcular_rsi(closes, period=14).iloc[-1]
                        sma_20 = calcular_sma(closes, 20).iloc[-1]
                        price = float(closes.iloc[-1])

                        # Señal simplificada
                        if rsi < 30:
                            status = "🟢 SOBREVENTA"
                        elif rsi > 70:
                            status = "🔴 SOBRECOMPRA"
                        elif price > sma_20:
                            status = "⚪ ALCISTA"
                        else:
                            status = "⚪ BAJISTA"

                        radar_lines.append(
                            f"\n<b>{symbol}</b>: ${price:.2f} | RSI: {rsi:.1f} {status}"
                        )

            except Exception as e:
                radar_lines.append(f"\n<b>{symbol}</b>: ⚠️ Error")

        radar_lines.append(f"\n\n✅ Análisis completado")
        return "".join(radar_lines)

    except Exception as e:
        log_message(f"   ⚠️ Error en análisis radar: {e}")
        return "❌ Error ejecutando análisis"

def handle_status_command(api):
    """
    Maneja el comando /status: Balance, posiciones y estrategia activa

    Args:
        api: Instancia de tradeapi.REST

    Returns:
        str: Mensaje formateado para Telegram
    """
    try:
        # Obtener datos de cuenta
        account = api.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        buying_power = float(account.buying_power)

        # Obtener posiciones abiertas
        positions = api.list_positions()

        # Cargar estrategia activa
        config = load_user_config()
        active_strategy = config.get('active_strategy', 'centinela')
        watchlist = config.get('watchlist', DEFAULT_WATCHLIST)

        strategy_names = {
            'centinela': '🛡️ Centinela',
            'rompeolas': '🌊 Rompeolas',
            'elite': '🏆 Élite',
            'wheel': '🔄 The Wheel',
            'orb': '⚡ ORB',
            'flash_test': '⚡ Flash Test'
        }

        ny_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(ny_tz).strftime('%H:%M:%S ET')

        status_msg = [
            f"📊 <b>STATUS DE CUENTA</b>\n",
            f"🕐 {current_time}\n",
            f"\n💰 <b>Balance:</b>",
            f"\n  • Equity: <b>${equity:,.2f}</b>",
            f"\n  • Cash: ${cash:,.2f}",
            f"\n  • Buying Power: ${buying_power:,.2f}\n",
            f"\n📈 <b>Posiciones Abiertas:</b> {len(positions)}"
        ]

        if len(positions) > 0:
            for pos in positions[:10]:  # Máximo 10 posiciones
                qty = float(pos.qty)
                current_price = float(pos.current_price)
                cost_basis = float(pos.avg_entry_price)
                market_value = float(pos.market_value)
                unrealized_pl = float(pos.unrealized_pl)
                unrealized_plpc = float(pos.unrealized_plpc) * 100

                pl_emoji = "🟢" if unrealized_pl >= 0 else "🔴"

                status_msg.append(
                    f"\n  {pl_emoji} <b>{pos.symbol}</b>: {int(qty)} @ ${current_price:.2f} "
                    f"({unrealized_plpc:+.1f}%)"
                )
        else:
            status_msg.append("\n  • Sin posiciones abiertas")

        status_msg.append(
            f"\n\n⚡ <b>Estrategia Activa:</b> {strategy_names.get(active_strategy, active_strategy.upper())}"
        )
        status_msg.append(
            f"\n📋 <b>Watchlist:</b> {', '.join(watchlist[:5])}"
        )
        status_msg.append(f"\n\n✅ Sistema operativo")

        return "".join(status_msg)

    except Exception as e:
        log_message(f"   ⚠️ Error en /status: {e}")
        import traceback
        traceback.print_exc()
        return "❌ Error ejecutando /status. Intenta de nuevo."

def handle_config_command():
    """
    Maneja el comando /config: Muestra botones para cambiar estrategia

    Returns:
        None (envía mensaje con botones directamente)
    """
    try:
        # Cargar estrategia actual
        config = load_user_config()
        active_strategy = config.get('active_strategy', 'centinela')

        strategy_names = {
            'centinela': '🛡️ Centinela (Todas)',
            'rompeolas': '🌊 Rompeolas',
            'elite': '🏆 Élite',
            'wheel': '🔄 The Wheel',
            'orb': '⚡ ORB',
            'flash_test': '⚡ Flash Test'
        }

        ny_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(ny_tz).strftime('%H:%M:%S ET')

        message = (
            f"⚙️ <b>CONTROL REMOTO</b>\n\n"
            f"🕐 {current_time}\n"
            f"📊 Estrategia actual: <b>{strategy_names.get(active_strategy, active_strategy.upper())}</b>\n\n"
            f"Selecciona la nueva estrategia:"
        )

        # Construir botones de estrategias
        buttons = []
        for key, name in strategy_names.items():
            emoji = "✅ " if key == active_strategy else ""
            buttons.append([{
                "text": f"{emoji}{name}",
                "callback_data": f"config:{key}"
            }])

        send_telegram_msg_with_buttons(message, buttons)

    except Exception as e:
        log_message(f"   ⚠️ Error en /config: {e}")
        send_telegram_msg("❌ Error mostrando opciones de configuración")

def handle_config_change(strategy_key):
    """
    Cambia la estrategia activa en user_config.json

    Args:
        strategy_key: Clave de la estrategia ("centinela", "rompeolas", etc.)

    Returns:
        str: Mensaje de confirmación
    """
    try:
        strategy_names = {
            'centinela': '🛡️ Centinela',
            'rompeolas': '🌊 Rompeolas',
            'elite': '🏆 Élite',
            'wheel': '🔄 The Wheel',
            'orb': '⚡ ORB',
            'flash_test': '⚡ Flash Test'
        }

        # Cargar configuración actual
        config = load_user_config()
        old_strategy = config.get('active_strategy', 'centinela')

        # Actualizar estrategia
        config['active_strategy'] = strategy_key
        config['last_updated'] = datetime.now().isoformat()

        # Guardar en user_config.json
        with open('user_config.json', 'w') as f:
            json.dump(config, f, indent=2)

        log_message(f"   ⚙️ Estrategia cambiada: {old_strategy} → {strategy_key}")

        return (
            f"✅ <b>ESTRATEGIA ACTUALIZADA</b>\n\n"
            f"Anterior: {strategy_names.get(old_strategy, old_strategy.upper())}\n"
            f"Nueva: <b>{strategy_names.get(strategy_key, strategy_key.upper())}</b>\n\n"
            f"⏳ El cambio se aplicará en el próximo análisis (60s)"
        )

    except Exception as e:
        log_message(f"   ⚠️ Error cambiando estrategia: {e}")
        return "❌ Error actualizando estrategia"

def process_telegram_commands(api):
    """
    Procesa comandos y callbacks entrantes de Telegram

    Args:
        api: Instancia de tradeapi.REST
    """
    global last_update_id

    updates = get_telegram_updates()

    for update in updates:
        # Actualizar offset para no procesar el mismo mensaje dos veces
        update_id = update.get("update_id")
        if update_id:
            last_update_id = update_id

        # ========== PROCESAR MENSAJES DE TEXTO (COMANDOS) ==========
        if "message" in update:
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            # Verificar que el mensaje venga del chat correcto
            if str(chat_id) != str(TELEGRAM_CHAT_ID):
                continue

            # Procesar comandos
            if text.startswith("/radar"):
                log_message(f"\n💬 Comando recibido: /radar")
                handle_radar_command()  # Ahora solo muestra botones

            elif text.startswith("/status"):
                log_message(f"\n💬 Comando recibido: /status")
                response = handle_status_command(api)
                send_telegram_msg(response)

            elif text.startswith("/config"):
                log_message(f"\n💬 Comando recibido: /config")
                handle_config_command()  # Muestra botones de estrategias

            elif text.startswith("/"):
                # Comando desconocido
                send_telegram_msg(
                    f"❓ Comando desconocido: {text}\n\n"
                    f"<b>Comandos disponibles:</b>\n"
                    f"  /radar - Análisis técnico interactivo\n"
                    f"  /status - Balance y posiciones\n"
                    f"  /config - Cambiar estrategia"
                )

        # ========== PROCESAR CALLBACK QUERIES (BOTONES) ==========
        elif "callback_query" in update:
            callback = update.get("callback_query", {})
            callback_id = callback.get("id")
            callback_data = callback.get("data", "")
            from_user = callback.get("from", {})
            user_id = from_user.get("id")

            # Verificar que venga del usuario correcto
            if str(user_id) != str(TELEGRAM_CHAT_ID):
                continue

            log_message(f"\n🔘 Callback recibido: {callback_data}")

            # Parsear callback_data (formato: "comando:parametro")
            if ":" in callback_data:
                command, param = callback_data.split(":", 1)

                # ========== CALLBACK: RADAR ANALYSIS ==========
                if command == "radar":
                    answer_callback_query(callback_id, "🔍 Analizando...")
                    response = handle_radar_analysis(api, param)
                    send_telegram_msg(response)

                # ========== CALLBACK: CONFIG CHANGE ==========
                elif command == "config":
                    answer_callback_query(callback_id, "⚙️ Actualizando...")
                    response = handle_config_change(param)
                    send_telegram_msg(response)

                else:
                    answer_callback_query(callback_id, "❌ Callback no reconocido")

            else:
                answer_callback_query(callback_id, "❌ Formato de callback inválido")


def is_crypto_symbol(symbol):
    """
    Detecta si un símbolo es criptomoneda

    Args:
        symbol: Ticker del activo

    Returns:
        bool: True si es cripto, False si es acción
    """
    crypto_symbols = ['BTC/USD', 'BTCUSD', 'ETH/USD', 'ETHUSD']
    return symbol.upper() in crypto_symbols

def is_market_open(watchlist=None):
    """
    Verifica si el mercado de NY está abierto
    Horario: 9:30 AM - 4:00 PM ET, Lunes a Viernes

    BYPASS PARA CRIPTO: Si hay criptomonedas en la watchlist, retorna True (24/7)

    Args:
        watchlist: Lista de tickers a analizar (opcional)

    Returns:
        bool: True si mercado abierto o hay cripto, False otherwise
    """
    # BYPASS: Si hay criptomonedas, mercado "siempre abierto" (24/7)
    if watchlist:
        for symbol in watchlist:
            if is_crypto_symbol(symbol):
                return True  # Cripto opera 24/7

    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz)

    # Verificar si es fin de semana
    if now.weekday() >= 5:  # 5 = Sábado, 6 = Domingo
        return False

    # Verificar horario (9:30 AM - 4:00 PM)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now <= market_close

def calculate_dynamic_quantity(price, budget=1000, symbol=None):
    """
    Calcula cantidad de acciones/cripto a comprar basada en presupuesto máximo

    CRIPTO: Usa $100 budget para pruebas seguras (BTC/USD, ETH/USD)
    ACCIONES: Usa $1000 budget para operaciones normales

    Args:
        price: Precio actual del activo
        budget: Presupuesto máximo por operación (default: $1000)
        symbol: Símbolo del activo (para detectar si es cripto)

    Returns:
        tuple: (cantidad, es_cripto, notional_value)
            - cantidad: float para cripto, int para acciones
            - es_cripto: bool
            - notional_value: USD para cripto
    """
    if price <= 0:
        return 0, False, 0

    # CRIPTO: $100 budget, cantidad fraccionaria
    if symbol and is_crypto_symbol(symbol):
        test_budget = 100  # Prueba segura con $100
        qty_fractional = test_budget / price
        return qty_fractional, True, test_budget

    # ACCIONES: $1000 budget, cantidad entera
    qty = int(budget / price)

    # Mínimo 1 acción, máximo 100
    qty = max(1, min(qty, 100))

    return qty, False, qty * price

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
    - RSI < 30 (sobreventa extrema) [🔬 Flash Test: < 36]
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

    # 🔬 UMBRALES AJUSTADOS POR FLASH TEST (20% más sensible)
    rsi_oversold_threshold = 30 * (1 / SENSITIVITY_MULTIPLIER)  # 36 si Flash Test activo
    rsi_neutral_low = 40 * SENSITIVITY_MULTIPLIER  # 32 si Flash Test activo
    rsi_neutral_high = 55 * (1 / SENSITIVITY_MULTIPLIER)  # 66 si Flash Test activo

    signal = None
    reason = ""

    # Lógica de Entrada
    if pd.notna(rsi) and rsi < rsi_oversold_threshold:
        if current_price > sma_200_val:
            signal = "CALL (Rebote Técnico)"
            mode_indicator = "🔬 Flash Test" if FLASH_TEST_MODE else ""
            reason = f"Elite: Activo sobrevendido (RSI {rsi:.2f}) en tendencia alcista. Posible rebote a la media. {mode_indicator}"
        else:
            signal = "WATCHLIST (RSI Bajo en Downtrend)"
            reason = f"Elite: RSI {rsi:.2f} bajo pero precio < SMA200. Esperar confirmación."

    elif pd.notna(rsi) and current_price > sma_20_val and rsi_neutral_low < rsi < rsi_neutral_high:
        signal = "WATCHLIST (Pullback Sano)"
        reason = f"Elite: Precio sobre SMA20, RSI {rsi:.2f} en zona neutral. Monitorear."
    else:
        # 📱 Razón de NO COMPRA
        if pd.notna(rsi):
            reason = f"Neutral (RSI: {rsi:.2f} / SMA20: ${sma_20_val:.2f})"

    return signal, reason

# ========== MÓDULO 2: ESTRATEGIA ROMPEOLAS (Energía / Momentum) ==========

def analizar_estrategia_rompeolas(bars, ticker):
    """
    ESTRATEGIA ROMPEOLAS (Breakout con Volumen)
    Enfoque: Momentum / Breakout con confirmación institucional.
    Ideal para: XLE, OXY, APA (Crisis energética/política).

    Lógica:
    - Precio > Máximo de 20 días (breakout de resistencia)
    - RSI > 50 (fuerza alcista, no rebote) [🔬 Flash Test: > 40]
    - Volumen > 150% del promedio (confirmación institucional) [🔬 Flash Test: > 120%]
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

    # 🔬 UMBRALES AJUSTADOS POR FLASH TEST (20% más sensible)
    rsi_strength_threshold = 50 * SENSITIVITY_MULTIPLIER  # 40 si Flash Test activo
    volume_multiplier = 1.5 * SENSITIVITY_MULTIPLIER  # 1.2 si Flash Test activo

    signal = None
    reason = ""

    # Validar que tenemos datos
    if pd.isna(rsi) or pd.isna(resistencia) or pd.isna(vol_sma_val):
        return signal, reason

    # --- Lógica de Disparo (Trigger) ---
    breakout = current_price > resistencia
    volumen_institucional = current_volume > (vol_sma_val * volume_multiplier)
    fuerza = rsi > rsi_strength_threshold

    if breakout and fuerza:
        if volumen_institucional:
            signal = "CALL (ROMPEOLAS CONFIRMADO)"
            contrato = sugerir_contrato_opciones(current_price)
            mode_indicator = "🔬 Flash Test" if FLASH_TEST_MODE else ""

            reason = (
                f"🌊 BREAKOUT CON VOLUMEN EN {ticker}\n"
                f"   - Precio: ${current_price:.2f} rompió resistencia de ${resistencia:.2f}\n"
                f"   - Volumen: {int(current_volume):,} (>{int(volume_multiplier*100)}% del promedio)\n"
                f"   - RSI: {rsi:.2f} (Tendencia fuerte) {mode_indicator}"
                f"{contrato}"
            )
        else:
            signal = "WATCHLIST (Breakout sin Volumen)"
            reason = f"Rompeolas: Breakout de ${resistencia:.2f} pero volumen insuficiente. Monitorear."
    else:
        # 📱 Razón de NO COMPRA
        if pd.notna(rsi):
            reason = f"Neutral (RSI: {rsi:.2f} / Resistencia: ${resistencia:.2f})"

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

# ========== MÓDULO 5: ESTRATEGIA FLASH TEST (CRYPTO SCALPING) ==========

def analizar_estrategia_flash_test(api, symbol):
    """
    ESTRATEGIA FLASH TEST (Crypto Scalping - BTC/USD)
    Enfoque: Scalping rápido en criptomonedas 24/7
    Ideal para: BTC/USD, ETH/USD (prueba nocturna)

    Lógica:
    - Usa velas de 5 minutos (o 1 min si disponible)
    - COMPRA si RSI(14) < 40 (sobreventa leve)
    - Take Profit: +0.5% (salida rápida)
    - Stop Loss: -0.5% (riesgo controlado)

    Objetivo: Ver una operación abrirse y cerrarse rápido (prueba funcional)
    """
    try:
        # Obtener datos de 5 minutos (últimas 100 velas = ~8 horas)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=8)

        bars_5min = api.get_bars(
            symbol,
            tradeapi.TimeFrame(5, tradeapi.TimeFrameUnit.Minute),
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            feed='iex'
        ).df

        if bars_5min.empty or len(bars_5min) < 20:
            log_message(f"   ⚠️ Datos insuficientes para {symbol} (necesita al menos 20 velas de 5min)")
            return None, ""

        # Calcular RSI(14) en velas de 5 minutos
        closes = bars_5min['close']
        rsi_series = calcular_rsi(closes, period=14)
        current_rsi = rsi_series.iloc[-1]
        current_price = float(closes.iloc[-1])

        # Calcular niveles de salida
        take_profit_price = current_price * 1.005  # +0.5%
        stop_loss_price = current_price * 0.995    # -0.5%

        # 🔬 UMBRALES AJUSTADOS POR FLASH TEST (20% más sensible)
        rsi_crypto_threshold = 40 * (1 / SENSITIVITY_MULTIPLIER)  # 48 si Flash Test activo

        signal = None
        reason = ""

        # LÓGICA DE COMPRA: RSI < 40 (sobreventa leve) [🔬 Flash Test: < 48]
        if pd.notna(current_rsi) and current_rsi < rsi_crypto_threshold:
            signal = "CALL (Flash Test Scalping)"
            mode_indicator = f"🔬 ({rsi_crypto_threshold:.0f} threshold)" if FLASH_TEST_MODE else ""
            reason = (
                f"⚡ FLASH TEST - SCALPING BTC/USD {mode_indicator}\n"
                f"   Precio: ${current_price:.2f}\n"
                f"   RSI(14) 5min: {current_rsi:.2f} (sobreventa leve)\n"
                f"   📈 Take Profit: ${take_profit_price:.2f} (+0.5%)\n"
                f"   🛑 Stop Loss: ${stop_loss_price:.2f} (-0.5%)\n"
                f"   ⏱️ Timeframe: 5 minutos\n"
                f"   🎯 Objetivo: Operación rápida de prueba\n"
                f"   💰 Budget: $100 USD (prueba segura)"
            )
        else:
            reason = f"Neutral (RSI: {current_rsi:.2f} / Esperando < {rsi_crypto_threshold:.0f})"

        return signal, reason

    except Exception as e:
        log_message(f"⚠️ Error en estrategia Flash Test para {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None, ""

# ========== FUNCIÓN PRINCIPAL (ORQUESTADOR) ==========

def run_bot():
    """Función principal del bot con arquitectura modular"""
    config = load_user_config()  # ✅ Usar user_config.json para misiones dinámicas

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

    # ========== CONFIRMACIÓN DE MODO PAPER TRADING ==========
    log_message("\n" + "=" * 60)
    log_message("🔒 MODO FORZADO: PAPER TRADING ACTIVO")
    log_message(f"📡 Endpoint: {ENDPOINT}")
    log_message(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-4:] if API_KEY else 'N/A'}")
    log_message("=" * 60 + "\n")

    # 💬 PROCESAR COMANDOS DE TELEGRAM (Si hay mensajes pendientes)
    try:
        process_telegram_commands(api)
    except Exception as cmd_error:
        log_message(f"   ⚠️ Error procesando comandos: {cmd_error}")

    # Calcular fecha de inicio (Hace 700 días para asegurar datos de sobra)
    fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')
    log_message(f"📅 Solicitando datos desde: {fecha_inicio}")

    # Cargar Watchlist
    watchlist = load_watchlist()
    log_message(f"📊 Watchlist: {', '.join(watchlist)}\n")

    resultados = []

    # 📊 REPORTE EJECUTIVO (Cada 90 minutos)
    if should_send_report():
        log_message("\n📊 Generando Reporte Ejecutivo...")
        send_executive_report(api, watchlist)

    # BUCLE DE ANÁLISIS
    for symbol in watchlist:
        global tickers_scanned_count
        tickers_scanned_count += 1  # Incrementar contador

        try:
            log_message(f"\n🔍 Analizando: {symbol}...")

            # ========== BYPASS PARA CRIPTO: FLASH TEST 24/7 ==========
            if is_crypto_symbol(symbol):
                log_message(f"   🌙 DETECTADO: Criptomoneda {symbol} → Aplicando Flash Test (24/7)")
                signal, reason = analizar_estrategia_flash_test(api, symbol)
                triggered_strategy = 'flash_test'

                # Si hay señal, procesar inmediatamente (skip lógica de acciones)
                if signal and "CALL" in signal:
                    log_message(f"\n   🚀 SEÑAL ENCONTRADA: {symbol}")
                    log_message(f"      Tipo: {signal}")
                    log_message(f"      {reason}")

                    # Obtener precio actual de velas de 5 minutos
                    end_time = datetime.now()
                    start_time = end_time - timedelta(hours=1)
                    bars_5min = api.get_bars(
                        symbol,
                        tradeapi.TimeFrame(5, tradeapi.TimeFrameUnit.Minute),
                        start=start_time.isoformat(),
                        end=end_time.isoformat(),
                        feed='iex'
                    ).df

                    current_price = float(bars_5min['close'].iloc[-1])

                    # 📱 ALERTA 1: RADAR DETECTADO (Telegram)
                    telegram_radar = (
                        f"🔭 <b>RADAR DETECTADO</b>\n\n"
                        f"🎯 Ticker: <b>{symbol}</b>\n"
                        f"⚡ Estrategia: <b>Flash Test (Cripto 24/7)</b>\n"
                        f"📊 Precio: <b>${current_price:.2f}</b>\n"
                        f"📈 RSI 5min: <code>{reason.split('RSI(14) 5min: ')[1].split(' ')[0] if 'RSI(14) 5min:' in reason else 'N/A'}</code>\n\n"
                        f"⏳ Analizando viabilidad de compra..."
                    )
                    send_telegram_msg(telegram_radar)

                    # EJECUCIÓN CRIPTO: Usar notional ($100) en lugar de qty
                    try:
                        qty, es_cripto, notional_value = calculate_dynamic_quantity(current_price, symbol=symbol)

                        log_message(f"\n   📈 EJECUTANDO ORDEN DE COMPRA (CRIPTO):")
                        log_message(f"      Ticker: {symbol}")
                        log_message(f"      Notional: ${notional_value:.2f} USD")
                        log_message(f"      Cantidad estimada: {qty:.6f} {symbol.split('/')[0]}")
                        log_message(f"      Tipo: Market Order")
                        log_message(f"      Precio aproximado: ${current_price:.2f}")

                        # Alpaca Crypto usa 'notional' en lugar de 'qty'
                        order = api.submit_order(
                            symbol=symbol.replace('/', ''),  # BTC/USD → BTCUSD
                            notional=notional_value,  # $100 USD
                            side='buy',
                            type='market',
                            time_in_force='gtc'  # Good 'til cancelled (cripto 24/7)
                        )

                        log_message(f"   ✅ ORDEN EJECUTADA EXITOSAMENTE")
                        log_message(f"      Order ID: {order.id}")
                        log_message(f"      Status: {order.status}")

                        # 📱 ALERTA 2: ORDEN ENVIADA (Telegram)
                        telegram_exec = (
                            f"🟢 <b>ORDEN ENVIADA</b> ✅\n\n"
                            f"💼 Se compraron <b>{qty:.6f} {symbol.split('/')[0]}</b>\n"
                            f"🎯 Ticker: <b>{symbol}</b>\n"
                            f"💰 Notional: <b>${notional_value:.2f} USD</b>\n"
                            f"📊 Precio: <b>${current_price:.2f}</b>\n"
                            f"🆔 Order ID: <code>{order.id}</code>\n"
                            f"📈 Status: <b>{order.status.upper()}</b>\n\n"
                            f"⚡ Estrategia: Flash Test (Cripto)"
                        )
                        send_telegram_msg(telegram_exec)

                        # Timestamp en New York Time
                        ny_time = datetime.now(pytz.timezone('America/New_York'))

                        resultados.append({
                            "ticker": symbol,
                            "signal": signal,
                            "reason": reason,
                            "price": current_price,
                            "order_id": order.id,
                            "order_status": order.status,
                            "quantity": qty,
                            "notional": notional_value,
                            "timestamp": ny_time.isoformat(),
                            "strategy": "flash_test"
                        })

                        # Guardar en bitácora persistente
                        save_to_trade_history({
                            "date": ny_time.strftime('%Y-%m-%d %H:%M:%S ET'),
                            "ticker": symbol,
                            "action": "BUY",
                            "strategy": "flash_test",
                            "quantity": qty,
                            "notional": notional_value,
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

                else:
                    log_message(f"   💤 {symbol}: {reason if reason else 'Sin señal clara'}")
                    # Modo silencioso: No enviar notificaciones de "Neutral"

                # Skip al siguiente símbolo (no aplicar lógica de acciones)
                continue

            # ========== LÓGICA PARA ACCIONES (NO CRIPTO) ==========

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
            triggered_strategy = None

            # Obtener estrategia activa desde configuración
            active_strategy = config.get('active_strategy', 'rompeolas')

            # ========== MODO CENTINELA: Ejecutar TODAS las estrategias de trading ==========
            if active_strategy == 'centinela':
                log_message(f"   🛡️ Aplicando Modo Centinela (Vigilancia Total)")
                log_message(f"      Ejecutando análisis con 4 jueces de trading...")
                
                # Probar Elite
                signal_elite, reason_elite = analizar_estrategia_elite(bars, symbol)
                log_message(f"      🏆 Elite: {signal_elite or 'Sin señal'}")
                
                # Probar Rompeolas
                signal_rompeolas, reason_rompeolas = analizar_estrategia_rompeolas(bars, symbol)
                log_message(f"      🌊 Rompeolas: {signal_rompeolas or 'Sin señal'}")
                
                # Probar The Wheel
                signal_wheel, reason_wheel = analizar_estrategia_wheel(api, symbol)
                log_message(f"      🔄 The Wheel: {signal_wheel or 'Sin señal'}")
                
                # Probar ORB
                signal_orb, reason_orb = analizar_estrategia_orb(api, symbol)
                log_message(f"      ⚡ ORB: {signal_orb or 'Sin señal'}")
                
                # Prioridad de disparo: Rompeolas > Elite > Wheel > ORB
                # Si alguna da CALL, se dispara
                if signal_rompeolas and "CALL" in signal_rompeolas:
                    signal = signal_rompeolas
                    reason = reason_rompeolas
                    triggered_strategy = 'centinela → rompeolas'
                    log_message(f"      ✅ TRIGGER ACTIVADO por ROMPEOLAS")
                elif signal_elite and "CALL" in signal_elite:
                    signal = signal_elite
                    reason = reason_elite
                    triggered_strategy = 'centinela → elite'
                    log_message(f"      ✅ TRIGGER ACTIVADO por ÉLITE")
                elif signal_wheel and "CALL" in signal_wheel:
                    signal = signal_wheel
                    reason = reason_wheel
                    triggered_strategy = 'centinela → wheel'
                    log_message(f"      ✅ TRIGGER ACTIVADO por THE WHEEL")
                elif signal_orb and "CALL" in signal_orb:
                    signal = signal_orb
                    reason = reason_orb
                    triggered_strategy = 'centinela → orb'
                    log_message(f"      ✅ TRIGGER ACTIVADO por ORB")
                else:
                    triggered_strategy = 'centinela'

            # ========== MODOS INDIVIDUALES ==========
            elif active_strategy == 'wheel':
                log_message(f"   🔄 Aplicando Estrategia The Wheel (Opciones)")
                signal, reason = analizar_estrategia_wheel(api, symbol)
                triggered_strategy = 'wheel'

            elif active_strategy == 'orb':
                log_message(f"   ⚡ Aplicando Estrategia ORB (Day Trading)")
                signal, reason = analizar_estrategia_orb(api, symbol)
                triggered_strategy = 'orb'

            elif active_strategy == 'rompeolas' or symbol in SECTOR_ENERGIA:
                log_message(f"   🌊 Aplicando Estrategia Rompeolas (Energía)")
                signal, reason = analizar_estrategia_rompeolas(bars, symbol)
                triggered_strategy = 'rompeolas'

            else:  # elite (default)
                log_message(f"   🏆 Aplicando Estrategia Élite (Tech)")
                signal, reason = analizar_estrategia_elite(bars, symbol)
                triggered_strategy = 'elite'

            # --- PROCESAR RESULTADOS ---
            if signal and "CALL" in signal:
                log_message(f"\n   🚀 SEÑAL ENCONTRADA: {symbol}")
                log_message(f"      Tipo: {signal}")
                log_message(f"      {reason}")

                current_price = float(bars.iloc[-1]['close'])

                # 📱 ALERTA 1: RADAR DETECTADO (Telegram)
                strategy_name_map = {
                    'rompeolas': '🌊 Rompeolas',
                    'elite': '🏆 Élite',
                    'wheel': '🔄 The Wheel',
                    'orb': '⚡ ORB',
                    'centinela': '🛡️ Centinela'
                }
                strategy_display = strategy_name_map.get(triggered_strategy, triggered_strategy.upper())

                telegram_radar = (
                    f"🔭 <b>RADAR DETECTADO</b>\n\n"
                    f"🎯 Ticker: <b>{symbol}</b>\n"
                    f"⚡ Estrategia: <b>{strategy_display}</b>\n"
                    f"📊 Precio: <b>${current_price:.2f}</b>\n\n"
                    f"⏳ Analizando viabilidad de compra..."
                )
                send_telegram_msg(telegram_radar)

                # EJECUCIÓN REAL: Compra dinámica basada en $1000 budget
                try:
                    qty, es_cripto, total_cost = calculate_dynamic_quantity(current_price, budget=1000, symbol=symbol)

                    log_message(f"\n   📈 EJECUTANDO ORDEN DE COMPRA:")
                    log_message(f"      Ticker: {symbol}")
                    log_message(f"      Cantidad: {qty} acciones")
                    log_message(f"      Costo total: ${total_cost:.2f}")
                    log_message(f"      Tipo: Market Order")
                    log_message(f"      Precio aproximado: ${current_price:.2f}")

                    order = api.submit_order(
                        symbol=symbol,
                        qty=qty,  # DINÁMICO: Basado en budget de $1000
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )

                    log_message(f"   ✅ ORDEN EJECUTADA EXITOSAMENTE")
                    log_message(f"      Order ID: {order.id}")
                    log_message(f"      Status: {order.status}")

                    # 📱 ALERTA 2: ORDEN ENVIADA (Telegram)
                    telegram_exec = (
                        f"🟢 <b>ORDEN ENVIADA</b> ✅\n\n"
                        f"💼 Se compraron <b>{qty} acciones</b> de <b>{symbol}</b>\n"
                        f"💰 Costo total: <b>${total_cost:.2f}</b>\n"
                        f"📊 Precio: <b>${current_price:.2f}</b>\n"
                        f"🆔 Order ID: <code>{order.id}</code>\n"
                        f"📈 Status: <b>{order.status.upper()}</b>\n\n"
                        f"⚡ Estrategia: {strategy_display}"
                    )
                    send_telegram_msg(telegram_exec)

                    # Timestamp en New York Time
                    ny_time = datetime.now(pytz.timezone('America/New_York'))

                    resultados.append({
                        "ticker": symbol,
                        "signal": signal,
                        "reason": reason,
                        "price": current_price,
                        "order_id": order.id,
                        "order_status": order.status,
                        "quantity": qty,
                        "timestamp": ny_time.isoformat(),
                        "strategy": active_strategy
                    })

                    # Guardar en bitácora persistente
                    strategy_label = f"{active_strategy} → {triggered_strategy}" if active_strategy == 'centinela' else triggered_strategy
                    save_to_trade_history({
                        "date": ny_time.strftime('%Y-%m-%d %H:%M:%S ET'),
                        "ticker": symbol,
                        "action": "BUY",
                        "strategy": strategy_label,
                        "quantity": qty,
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
                # Modo silencioso: No enviar notificaciones de "Watchlist"
            else:
                log_message(f"   💤 Sin señal clara")
                # Modo silencioso: No enviar notificaciones de "Neutral"

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
    log_message("=" * 60)
    log_message("🚀 TRADEOLYMPO v6.0 - WORKER CONTINUO (RAILWAY ALWAYS-ON)")
    log_message("=" * 60)
    log_message("🔒 MODO FORZADO: PAPER TRADING ACTIVO")
    log_message(f"📡 Endpoint: {ENDPOINT}")
    if FLASH_TEST_MODE:
        log_message("🔬 FLASH TEST MODE: Umbrales 20% más sensibles")
    log_message("=" * 60)
    log_message("📡 Modo: Always-On Worker")
    log_message("⏰ Análisis cada 60s durante market hours")
    log_message("💤 Análisis cada 15min fuera de horario")
    log_message("💰 Gestión de capital: $1000 acciones / $100 cripto")
    log_message("🌙 Cripto: Opera 24/7 (BTC/USD, ETH/USD)")
    log_message("📊 Reporte ejecutivo cada 90 minutos")
    log_message("🤫 Silent Mode: Solo notifica señales y órdenes")
    log_message("💬 Comandos: /radar, /status, /config")
    log_message("🔘 Controles interactivos: Botones InlineKeyboard")
    log_message("=" * 60)

    # 📱 NOTIFICACIÓN DE INICIO (Telegram)
    flash_test_indicator = "🔬 Flash Test (20% más sensible)\n" if FLASH_TEST_MODE else ""
    startup_msg = (
        f"🚀 <b>TradeOlympo Online</b>\n\n"
        f"🛡️ Modo Centinela Activo\n"
        f"🔒 Paper Trading\n"
        f"{flash_test_indicator}"
        f"⏰ Análisis cada 60s (market hours)\n"
        f"💤 Análisis cada 15min (fuera de horario)\n"
        f"📊 Reporte ejecutivo cada 90 minutos\n"
        f"🤫 Silent Mode: Solo notifica señales y órdenes\n\n"
        f"💬 <b>Comandos disponibles:</b>\n"
        f"  /radar - Análisis técnico interactivo\n"
        f"  /status - Balance y posiciones\n"
        f"  /config - Cambiar estrategia\n\n"
        f"✅ Listo para detectar oportunidades"
    )
    send_telegram_msg(startup_msg)

    import time

    # Estado de mercado anterior (para detectar cambios)
    previous_market_state = None

    while True:
        try:
            # Cargar watchlist para detectar cripto
            from bot import load_watchlist
            watchlist = load_watchlist()

            # Verificar si el mercado está abierto (o si hay cripto en watchlist)
            market_is_open = is_market_open(watchlist)
            ny_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(ny_tz).strftime('%H:%M:%S ET')

            # Detectar si hay cripto en watchlist
            has_crypto = any(is_crypto_symbol(s) for s in watchlist)

            # 📱 NOTIFICACIÓN DE CAMBIO DE ESTADO (Telegram)
            if previous_market_state is not None and previous_market_state != market_is_open:
                if not market_is_open and not has_crypto:
                    # Mercado acaba de cerrar
                    close_msg = (
                        f"🔴 <b>Mercado Cerrado</b>\n\n"
                        f"🕐 Hora: {current_time}\n"
                        f"💤 Modo ahorro de recursos activado\n"
                        f"⏰ Próxima verificación en 15 minutos\n\n"
                        f"📊 Esperando próxima apertura..."
                    )
                    send_telegram_msg(close_msg)

            previous_market_state = market_is_open

            if market_is_open:
                if has_crypto:
                    log_message(f"\n🌙 CRIPTO DETECTADO - Operando 24/7 - {current_time}")
                else:
                    log_message(f"\n🟢 Mercado ABIERTO - {current_time}")
                log_message("   Ejecutando análisis...")
                run_bot()

                # Dormir 60 segundos
                log_message("   ⏱️ Próximo análisis en 60 segundos...")
                time.sleep(60)

            else:
                log_message(f"\n🔴 Mercado CERRADO - {current_time}")
                log_message("   💤 Modo ahorro de recursos activado")
                log_message("   ⏱️ Próxima verificación en 15 minutos...")

                # Dormir 15 minutos (900 segundos)
                time.sleep(900)
        
        except KeyboardInterrupt:
            log_message("\n\n⚠️ WORKER DETENIDO POR USUARIO")
            break
        
        except Exception as e:
            log_message(f"\n❌ ERROR EN WORKER: {e}")
            log_message("   ⏱️ Reintentando en 5 minutos...")
            import traceback
            traceback.print_exc()
            time.sleep(300)  # 5 minutos antes de reintentar
