"""
TradeOlympo - Bot de Trading Autónomo
Ejecuta estrategias de trading automáticamente usando Alpaca Markets API
"""

import os
import alpaca_trade_api as tradeapi
from datetime import datetime
import pytz

# Configuración
API_KEY = os.environ.get('ALPACA_API_KEY')
SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
ENDPOINT = os.environ.get('ALPACA_ENDPOINT', 'https://paper-api.alpaca.markets')

def run_bot():
    """
    Función principal del bot autónomo.
    Ejecuta lógica de trading basada en las estrategias de TradeOlympo.
    """
    print(f"--- Iniciando Bot Autónomo: {datetime.now(pytz.UTC)} ---")

    if not API_KEY or not SECRET_KEY:
        print("ERROR: Faltan las API KEYS en las variables de entorno.")
        print("Asegúrate de configurar ALPACA_API_KEY y ALPACA_SECRET_KEY en GitHub Secrets.")
        return

    try:
        # Conexión a Alpaca
        api = tradeapi.REST(API_KEY, SECRET_KEY, ENDPOINT, api_version='v2')

        # Verificar estado del mercado
        clock = api.get_clock()
        print(f"Mercado Abierto: {clock.is_open}")
        print(f"Próxima apertura: {clock.next_open}")
        print(f"Próximo cierre: {clock.next_close}")

        if not clock.is_open:
            print("Mercado cerrado. No se ejecutarán operaciones.")
            return

        # --- LÓGICA DE PRUEBA (NO MODIFICAR LÓGICA CORE AÚN) ---
        # Comprobación simple para validar que el pipeline funciona
        symbol = 'SPY'

        # Obtener información de la cuenta
        account = api.get_account()
        print(f"Poder de compra: ${float(account.buying_power):.2f}")
        print(f"Cash disponible: ${float(account.cash):.2f}")

        try:
            position = api.get_position(symbol)
            qty = int(position.qty)
            print(f"Posición actual en {symbol}: {qty} acciones. No se requiere acción.")
        except:
            print(f"No hay posición en {symbol}. Iniciando compra de prueba...")

            # Validar que tenemos suficiente capital
            quote = api.get_latest_trade(symbol)
            price = float(quote.price)

            if float(account.cash) >= price:
                api.submit_order(
                    symbol=symbol,
                    qty=1,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print(f"✅ Orden de compra enviada exitosamente: 1 acción de {symbol} @ ~${price:.2f}")
            else:
                print(f"❌ Capital insuficiente. Necesitas ${price:.2f} pero solo tienes ${float(account.cash):.2f}")

    except Exception as e:
        print(f"❌ Error crítico en ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_bot()
