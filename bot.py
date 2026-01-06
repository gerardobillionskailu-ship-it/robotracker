"""
TradeOlympo - Bot de Trading Autónomo (Arquitectura Modular v2.0)

ESTRATEGIAS IMPLEMENTADAS:
1. Estrategia Élite: Reversión a la media para Tech stocks (RSI < 30)
2. Estrategia Rompeolas: Breakout de energía (Resistencia 20d + RSI > 50 + Volumen alto)

Ejecuta COMPRA solo si la estrategia correspondiente aprueba y no hay posición abierta.
"""
import os
import json
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import pandas_ta as ta

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT')

# --- FUNCIONES DE CONFIGURACIÓN ---

def load_watchlist():
    """Lee la watchlist desde watchlist.json (sincronización con web)"""
    try:
        with open('watchlist.json', 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"⚠️ No se pudo leer watchlist.json: {e}")
        # Fallback a valores por defecto
        return {
            "strategy_elite": {
                "name": "Estrategia Élite",
                "symbols": ["NVDA", "TSLA", "AMD"],
                "enabled": True
            },
            "strategy_rompeolas": {
                "name": "Estrategia Rompeolas",
                "symbols": ["XLE", "OXY", "CVX"],
                "enabled": True
            },
            "account_settings": {
                "account_size": 1000,
                "max_contract_cost": 200,
                "target_delta": 0.60,
                "option_days_to_expiry_min": 45,
                "option_days_to_expiry_max": 60
            }
        }

def log_message(message):
    """Escribe mensaje en consola y en archivo bot_logs.txt"""
    print(message)
    try:
        with open('bot_logs.txt', 'a', encoding='utf-8') as f:
            timestamp = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S ET')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"⚠️ No se pudo escribir log: {e}")

# --- INDICADORES TÉCNICOS ---

def calcular_rsi(series, period=14):
    """Calcula RSI usando pandas-ta"""
    rsi = ta.rsi(series, length=period)
    return rsi

def calcular_sma(series, window):
    """Calcula SMA simple"""
    return series.rolling(window=window).mean()

def calcular_maximos_20d(df):
    """Calcula máximo de 20 días (resistencia)"""
    return df['high'].rolling(window=20).max()

def calcular_volumen_promedio(df, window=20):
    """Calcula volumen promedio de N días"""
    return df['volume'].rolling(window=window).mean()

# --- ESTRATEGIAS DE TRADING ---

def analizar_estrategia_elite(df, ticker):
    """
    ESTRATEGIA ÉLITE (Reversión a la Media - Tech Stocks)

    Lógica:
    - RSI < 30 (sobreventa)
    - Precio > SMA 200 (tendencia alcista general)
    - Volumen > 1M (liquidez)

    Returns:
        dict: {'aprobado': bool, 'razon': str, 'precio': float}
    """
    closes = df['close']
    current_price = closes.iloc[-1]

    # Indicadores
    rsi = calcular_rsi(closes).iloc[-1]
    sma_200 = calcular_sma(closes, 200).iloc[-1]

    # Filtro de volumen
    volumes = df['volume']
    avg_volume_30d = volumes.tail(30).mean()
    MIN_VOLUME_THRESHOLD = 1_000_000

    if avg_volume_30d < MIN_VOLUME_THRESHOLD:
        return {
            'aprobado': False,
            'razon': f'Volumen bajo: {avg_volume_30d:,.0f} < 1M',
            'precio': current_price
        }

    # Reglas de Estrategia Élite
    rsi_sobreventa = rsi < 30
    tendencia_alcista = current_price > sma_200

    aprobado = rsi_sobreventa and tendencia_alcista

    if aprobado:
        razon = f"✅ RSI sobreventa ({rsi:.1f}) + Tendencia alcista (${current_price:.2f} > ${sma_200:.2f})"
    else:
        razones = []
        if not rsi_sobreventa:
            razones.append(f"RSI no sobreventa ({rsi:.1f})")
        if not tendencia_alcista:
            razones.append(f"Sin tendencia alcista (${current_price:.2f} <= ${sma_200:.2f})")
        razon = " | ".join(razones)

    return {
        'aprobado': aprobado,
        'razon': razon,
        'precio': current_price,
        'rsi': rsi,
        'sma_200': sma_200
    }

def analizar_estrategia_rompeolas(df, ticker):
    """
    ESTRATEGIA ROMPEOLAS (Breakout - Energía)

    Lógica:
    - Precio > Máximo de 20 días (breakout de resistencia)
    - RSI > 50 (momentum alcista)
    - Volumen > 150% del promedio de 20 días (confirmación de fuerza)

    Returns:
        dict: {'aprobado': bool, 'razon': str, 'precio': float}
    """
    closes = df['close']
    highs = df['high']
    volumes = df['volume']

    current_price = closes.iloc[-1]
    current_volume = volumes.iloc[-1]

    # Indicadores
    rsi = calcular_rsi(closes).iloc[-1]
    resistencia_20d = calcular_maximos_20d(df).iloc[-2]  # Día anterior (no incluye hoy)
    volumen_promedio_20d = calcular_volumen_promedio(df).iloc[-1]

    # Reglas de Estrategia Rompeolas
    breakout_resistencia = current_price > resistencia_20d
    momentum_alcista = rsi > 50
    volumen_alto = current_volume > (volumen_promedio_20d * 1.5)

    aprobado = breakout_resistencia and momentum_alcista and volumen_alto

    if aprobado:
        razon = f"✅ Breakout (${current_price:.2f} > ${resistencia_20d:.2f}) + RSI ({rsi:.1f}) + Volumen ({current_volume:,.0f} > {volumen_promedio_20d * 1.5:,.0f})"
    else:
        razones = []
        if not breakout_resistencia:
            razones.append(f"Sin breakout (${current_price:.2f} <= ${resistencia_20d:.2f})")
        if not momentum_alcista:
            razones.append(f"RSI débil ({rsi:.1f})")
        if not volumen_alto:
            razones.append(f"Volumen insuficiente ({current_volume:,.0f})")
        razon = " | ".join(razones)

    return {
        'aprobado': aprobado,
        'razon': razon,
        'precio': current_price,
        'rsi': rsi,
        'resistencia_20d': resistencia_20d,
        'volumen_actual': current_volume,
        'volumen_promedio': volumen_promedio_20d
    }

# --- GESTIÓN DE RIESGO (OPCIONES) ---

def sugerir_contrato_opciones(precio_actual, account_settings):
    """
    Sugiere contrato de opciones para cuenta pequeña

    Args:
        precio_actual: Precio actual de la acción
        account_settings: Configuración de cuenta desde watchlist.json

    Returns:
        dict: Sugerencia de strike, vencimiento, costo estimado
    """
    max_cost = account_settings.get('max_contract_cost', 200)
    target_delta = account_settings.get('target_delta', 0.60)
    days_min = account_settings.get('option_days_to_expiry_min', 45)
    days_max = account_settings.get('option_days_to_expiry_max', 60)

    # Calcular strike ITM (Delta ~0.60)
    # Aproximación: Strike = Precio actual * (1 - 0.03) para Delta ~0.60
    strike_itm = round(precio_actual * 0.97, 2)

    # Estimar costo de contrato (5-8% del precio de la acción para ITM 45-60 días)
    costo_estimado = precio_actual * 0.06  # 6% promedio
    costo_contrato = round(costo_estimado * 100, 2)  # Multiplicador de 100

    # Calcular fecha de vencimiento (60 días desde hoy, buscar viernes)
    fecha_objetivo = datetime.now() + timedelta(days=60)
    # Ajustar a viernes más cercano
    days_until_friday = (4 - fecha_objetivo.weekday()) % 7
    fecha_vencimiento = fecha_objetivo + timedelta(days=days_until_friday)

    # Validar si el contrato cabe en el presupuesto
    dentro_presupuesto = costo_contrato <= max_cost

    return {
        'strike': strike_itm,
        'vencimiento': fecha_vencimiento.strftime('%Y-%m-%d'),
        'costo_estimado': costo_contrato,
        'dentro_presupuesto': dentro_presupuesto,
        'delta_objetivo': target_delta,
        'tipo': 'CALL ITM'
    }

# --- CEREBRO DEL BOT ---

def run_bot():
    """Función principal del bot con arquitectura modular"""
    log_message(f"\n{'='*60}")
    log_message(f"🚀 INICIANDO BOT TRADOLYMPO v2.0 - {datetime.now()}")
    log_message(f"{'='*60}")

    if not API_KEY or not SECRET_KEY:
        log_message("❌ ERROR: No hay API KEYS de Alpaca configuradas.")
        return

    # Cargar configuración de watchlist
    config = load_watchlist()
    account_settings = config.get('account_settings', {})

    log_message(f"💰 Cuenta: ${account_settings.get('account_size', 1000)}")
    log_message(f"💵 Máximo por contrato: ${account_settings.get('max_contract_cost', 200)}\n")

    api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')

    # Fecha de inicio para datos históricos
    fecha_inicio = (datetime.now() - timedelta(days=700)).strftime('%Y-%m-%d')

    # ========== ESTRATEGIA ÉLITE ==========
    if config.get('strategy_elite', {}).get('enabled', False):
        elite_symbols = config.get('strategy_elite', {}).get('symbols', [])
        log_message(f"\n📊 ESTRATEGIA ÉLITE (Reversión a la Media)")
        log_message(f"Tickers: {', '.join(elite_symbols)}")
        log_message("-" * 60)

        for symbol in elite_symbols:
            try:
                log_message(f"\n🔍 Analizando {symbol} (Élite)...")

                bars = api.get_bars(
                    symbol,
                    tradeapi.TimeFrame.Day,
                    start=fecha_inicio,
                    limit=300,
                    feed='iex'
                ).df

                if len(bars) < 200:
                    log_message(f"   ⚠️ Historial insuficiente ({len(bars)} días). Saltando.")
                    continue

                # Analizar con Estrategia Élite
                resultado = analizar_estrategia_elite(bars, symbol)

                log_message(f"   {resultado['razon']}")

                if resultado['aprobado']:
                    # Verificar posición existente
                    try:
                        pos = api.get_position(symbol)
                        if int(pos.qty) > 0:
                            log_message("   ✋ Ya tenemos posición. Mantener.")
                            continue
                    except:
                        pass

                    # Sugerir contrato de opciones
                    opcion = sugerir_contrato_opciones(resultado['precio'], account_settings)

                    log_message(f"\n   💡 SUGERENCIA DE OPCIONES:")
                    log_message(f"      - Strike: ${opcion['strike']} CALL (ITM)")
                    log_message(f"      - Vencimiento: {opcion['vencimiento']}")
                    log_message(f"      - Costo estimado: ${opcion['costo_estimado']:.2f}")
                    log_message(f"      - Estado: {'✅ Dentro de presupuesto' if opcion['dentro_presupuesto'] else '❌ Fuera de presupuesto'}")

                    # Ejecutar orden de acción (1 acción)
                    api.submit_order(
                        symbol=symbol,
                        qty=1,
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )
                    log_message(f"\n   🚀 ORDEN EJECUTADA: Compra de 1 acción de {symbol}")

            except Exception as e:
                log_message(f"   ❌ Error en {symbol}: {e}")

    # ========== ESTRATEGIA ROMPEOLAS ==========
    if config.get('strategy_rompeolas', {}).get('enabled', False):
        rompeolas_symbols = config.get('strategy_rompeolas', {}).get('symbols', [])
        log_message(f"\n\n⚡ ESTRATEGIA ROMPEOLAS (Breakout Energía)")
        log_message(f"Tickers: {', '.join(rompeolas_symbols)}")
        log_message("-" * 60)

        for symbol in rompeolas_symbols:
            try:
                log_message(f"\n🔍 Analizando {symbol} (Rompeolas)...")

                bars = api.get_bars(
                    symbol,
                    tradeapi.TimeFrame.Day,
                    start=fecha_inicio,
                    limit=300,
                    feed='iex'
                ).df

                if len(bars) < 200:
                    log_message(f"   ⚠️ Historial insuficiente ({len(bars)} días). Saltando.")
                    continue

                # Analizar con Estrategia Rompeolas
                resultado = analizar_estrategia_rompeolas(bars, symbol)

                log_message(f"   {resultado['razon']}")

                if resultado['aprobado']:
                    # Verificar posición existente
                    try:
                        pos = api.get_position(symbol)
                        if int(pos.qty) > 0:
                            log_message("   ✋ Ya tenemos posición. Mantener.")
                            continue
                    except:
                        pass

                    # Sugerir contrato de opciones
                    opcion = sugerir_contrato_opciones(resultado['precio'], account_settings)

                    log_message(f"\n   💡 SUGERENCIA DE OPCIONES:")
                    log_message(f"      - Strike: ${opcion['strike']} CALL (ITM)")
                    log_message(f"      - Vencimiento: {opcion['vencimiento']}")
                    log_message(f"      - Costo estimado: ${opcion['costo_estimado']:.2f}")
                    log_message(f"      - Estado: {'✅ Dentro de presupuesto' if opcion['dentro_presupuesto'] else '❌ Fuera de presupuesto'}")

                    # Ejecutar orden de acción (1 acción)
                    api.submit_order(
                        symbol=symbol,
                        qty=1,
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )
                    log_message(f"\n   🚀 ORDEN EJECUTADA: Compra de 1 acción de {symbol}")

            except Exception as e:
                log_message(f"   ❌ Error en {symbol}: {e}")

    log_message(f"\n{'='*60}")
    log_message(f"✅ FIN DEL ANÁLISIS - {datetime.now()}")
    log_message(f"{'='*60}\n")

if __name__ == "__main__":
    run_bot()
