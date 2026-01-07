"""
TradeOlympo - Plataforma Profesional de Análisis Financiero v4.0
Arquitectura de Doble Propósito: Misión del Bot vs Radar de Monitoreo
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from github import Github, GithubException
import pandas as pd
import numpy as np

# ========== CONFIGURACIÓN DE PÁGINA (DARK MODE) ==========

st.set_page_config(
    page_title="TradeOlympo | Trading Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ESTILOS DARK MODE PROFESIONAL ==========

st.markdown("""
<style>
    /* Tema Dark Mode Principal */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    /* Botones */
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background-color: #1565C0;
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
    }

    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #1E88E5;
        font-size: 2rem;
        font-weight: 700;
    }

    /* Mensajes de éxito */
    .stSuccess {
        background-color: #065F46;
        color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 8px;
    }

    /* Mensajes de info */
    .stInfo {
        background-color: #1E3A8A;
        color: #DBEAFE;
        border-left: 4px solid #3B82F6;
        padding: 1rem;
        border-radius: 8px;
    }

    /* Mensajes de warning */
    .stWarning {
        background-color: #78350F;
        color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 8px;
    }

    /* Tablas */
    [data-testid="stDataFrame"] {
        background-color: #1F2937;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    /* Headers */
    h1, h2, h3 {
        color: #F9FAFB;
    }

    /* Inputs */
    .stTextArea textarea {
        background-color: #1F2937;
        color: #F9FAFB;
        border: 1px solid #374151;
    }

    /* Indicador de Sincronización */
    .sync-indicator {
        background: linear-gradient(135deg, #1E3A8A 0%, #065F46 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #3B82F6;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .sync-indicator h3 {
        margin: 0;
        color: #FFFFFF;
        font-size: 1.1rem;
    }

    .sync-indicator p {
        margin: 0.5rem 0 0 0;
        color: #D1FAE5;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNCIONES DE DATOS (ALPACA) ==========

@st.cache_data(ttl=60)  # Cache por 1 minuto
def fetch_market_data(symbols, api_key, secret_key, endpoint):
    """
    Obtiene datos de mercado en tiempo real desde Alpaca API

    Returns:
        DataFrame con: symbol, price, volume, rsi, sma_20, sma_200, signal
    """
    try:
        import alpaca_trade_api as tradeapi

        api = tradeapi.REST(api_key, secret_key, endpoint, api_version='v2')

        results = []

        for symbol in symbols:
            try:
                # Obtener precio actual
                latest_trade = api.get_latest_trade(symbol)
                current_price = float(latest_trade.price)

                # Obtener datos históricos (250 días para calcular indicadores Larry Williams)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=250)

                bars = api.get_bars(
                    symbol,
                    tradeapi.TimeFrame.Day,
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    feed='iex'
                ).df

                if bars.empty or len(bars) < 20:
                    continue

                # Calcular indicadores
                closes = bars['close']
                volumes = bars['volume']
                highs = bars['high']
                lows = bars['low']

                # RSI
                delta = closes.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 0

                # SMAs
                sma_20 = closes.rolling(window=20).mean().iloc[-1]
                sma_50 = closes.rolling(window=50).mean().iloc[-1] if len(closes) >= 50 else sma_20
                sma_200 = closes.rolling(window=200).mean().iloc[-1] if len(closes) >= 200 else sma_20

                # Williams %R
                highest_high_14 = highs.rolling(window=14).max().iloc[-1]
                lowest_low_14 = lows.rolling(window=14).min().iloc[-1]
                williams_r = -100 * ((highest_high_14 - current_price) / (highest_high_14 - lowest_low_14)) if highest_high_14 != lowest_low_14 else 0

                # Volumen promedio
                avg_volume = volumes.tail(30).mean()

                # Resistencia (para Rompeolas)
                resistencia_20d = highs.rolling(20).max().shift(1).iloc[-1]

                # Wyckoff: Posición de la vela
                candle_range = highs.iloc[-1] - lows.iloc[-1]
                close_position = ((current_price - lows.iloc[-1]) / candle_range * 100) if candle_range > 0 else 50

                results.append({
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': rsi_val,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'sma_200': sma_200,
                    'williams_r': williams_r,
                    'volume': volumes.iloc[-1],
                    'avg_volume': avg_volume,
                    'resistencia_20d': resistencia_20d,
                    'close_position': close_position,
                    'high': highs.iloc[-1],
                    'low': lows.iloc[-1]
                })

            except Exception as e:
                st.warning(f"Error obteniendo datos de {symbol}: {str(e)}")
                continue

        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Error conectando a Alpaca API: {str(e)}")
        return pd.DataFrame()

# ========== GENERACIÓN DE SEÑALES (TODOS LOS JUECES) ==========

def generate_all_judges_signals(df):
    """
    Genera señales de TODOS los jueces para cada ticker

    Returns:
        DataFrame con columnas adicionales: larry_signal, wyckoff_signal, elite_signal, rompeolas_signal
    """
    results = []

    for idx, row in df.iterrows():
        signals = {
            'symbol': row['symbol'],
            'price': row['price'],
            'rsi': row['rsi'],
            'volume': row['volume'],
            'avg_volume': row['avg_volume']
        }

        # ========== JUEZ 1: LARRY WILLIAMS ==========
        larry_signal = "NEUTRAL"
        larry_reason = ""

        # Williams %R + SMA Cross
        if row['williams_r'] < -80:  # Sobreventa extrema
            if row['sma_50'] > row['sma_200']:  # Golden Cross
                larry_signal = "CALL"
                larry_reason = f"Williams %R {row['williams_r']:.1f} (sobreventa) + Golden Cross"
            else:
                larry_signal = "WATCH"
                larry_reason = f"Williams %R {row['williams_r']:.1f} pero sin Golden Cross"
        elif row['williams_r'] > -20:  # Sobrecompra
            larry_signal = "SELL"
            larry_reason = f"Williams %R {row['williams_r']:.1f} (sobrecompra)"
        else:
            larry_reason = f"Williams %R {row['williams_r']:.1f} (neutral)"

        signals['larry_signal'] = larry_signal
        signals['larry_reason'] = larry_reason

        # ========== JUEZ 2: WYCKOFF ==========
        wyckoff_signal = "NEUTRAL"
        wyckoff_reason = ""

        # Volumen alto + Posición de cierre
        volumen_alto = row['volume'] > (row['avg_volume'] * 1.5)
        close_in_upper = row['close_position'] > 70
        close_in_lower = row['close_position'] < 30

        if volumen_alto and close_in_upper:
            wyckoff_signal = "CALL"
            wyckoff_reason = f"Volumen alto + Cierre en top {row['close_position']:.0f}% (acumulación)"
        elif volumen_alto and close_in_lower:
            wyckoff_signal = "SELL"
            wyckoff_reason = f"Volumen alto + Cierre en low {row['close_position']:.0f}% (distribución)"
        elif volumen_alto:
            wyckoff_signal = "WATCH"
            wyckoff_reason = f"Volumen alto pero cierre en {row['close_position']:.0f}%"
        else:
            wyckoff_reason = f"Volumen normal | Cierre en {row['close_position']:.0f}%"

        signals['wyckoff_signal'] = wyckoff_signal
        signals['wyckoff_reason'] = wyckoff_reason

        # ========== JUEZ 3: ÉLITE (Tech / Reversión) ==========
        elite_signal = "NEUTRAL"
        elite_reason = ""

        if row['rsi'] < 30:
            if row['price'] > row['sma_200']:
                elite_signal = "CALL"
                elite_reason = f"RSI {row['rsi']:.1f} sobrevendido + tendencia alcista"
            else:
                elite_signal = "WATCH"
                elite_reason = f"RSI {row['rsi']:.1f} bajo pero sin tendencia"
        elif row['price'] > row['sma_20'] and 40 < row['rsi'] < 55:
            elite_signal = "WATCH"
            elite_reason = f"Pullback sano (RSI {row['rsi']:.1f})"
        else:
            elite_reason = f"RSI {row['rsi']:.1f} | vs SMA200: {((row['price']/row['sma_200']-1)*100):.1f}%"

        signals['elite_signal'] = elite_signal
        signals['elite_reason'] = elite_reason

        # ========== JUEZ 4: ROMPEOLAS (Energía / Momentum) ==========
        rompeolas_signal = "NEUTRAL"
        rompeolas_reason = ""

        breakout = row['price'] > row['resistencia_20d'] if pd.notna(row['resistencia_20d']) else False
        volumen_alto = row['volume'] > (row['avg_volume'] * 1.5)
        fuerza = row['rsi'] > 50

        if breakout and fuerza:
            if volumen_alto:
                rompeolas_signal = "CALL"
                rompeolas_reason = f"Breakout confirmado (RSI {row['rsi']:.1f}, Vol +{((row['volume']/row['avg_volume']-1)*100):.0f}%)"
            else:
                rompeolas_signal = "WATCH"
                rompeolas_reason = f"Breakout sin volumen (RSI {row['rsi']:.1f})"
        else:
            if breakout:
                rompeolas_reason = f"Breakout pero RSI {row['rsi']:.1f} < 50"
            else:
                rompeolas_reason = f"Precio ${row['price']:.2f} < Resistencia ${row['resistencia_20d']:.2f}"

        signals['rompeolas_signal'] = rompeolas_signal
        signals['rompeolas_reason'] = rompeolas_reason

        results.append(signals)

    return pd.DataFrame(results)

# ========== FUNCIONES DE CONFIGURACIÓN ==========

def load_user_config():
    """Carga la configuración del usuario desde user_config.json"""
    try:
        if os.path.exists('user_config.json'):
            with open('user_config.json', 'r') as f:
                return json.load(f)
        else:
            return {
                "active_strategy": "rompeolas",
                "watchlist": ["XLE", "OXY", "APA", "CVX"],
                "last_updated": datetime.now().isoformat(),
                "strategies": {
                    "elite": {
                        "name": "Estrategia Élite (Reversión)",
                        "default_tickers": ["NVDA", "TSLA", "AMD", "AAPL", "MSFT", "META", "COIN"]
                    },
                    "rompeolas": {
                        "name": "Estrategia Rompeolas (Breakout)",
                        "default_tickers": ["XLE", "OXY", "APA", "CVX", "COP", "SLB", "HAL", "VLO"]
                    },
                    "larry": {
                        "name": "Larry Williams (Contrarian)",
                        "default_tickers": ["SPY", "QQQ", "IWM", "XLE", "XLF"]
                    },
                    "wyckoff": {
                        "name": "Wyckoff (Volume)",
                        "default_tickers": ["SPY", "NVDA", "TSLA", "XLE"]
                    }
                }
            }
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        return None

def save_config_to_github(config_data, github_token, repo_name):
    """Guarda la configuración en GitHub usando PyGithub"""
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        try:
            file = repo.get_contents("user_config.json")
            sha = file.sha
            message = f"🤖 Bot Mission Update: {config_data['active_strategy']} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            repo.update_file(
                path="user_config.json",
                message=message,
                content=json.dumps(config_data, indent=2),
                sha=sha,
                branch="main"
            )
            return True, "✅ Misión del Bot guardada exitosamente en GitHub"

        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path="user_config.json",
                    message="🤖 Create bot mission config",
                    content=json.dumps(config_data, indent=2),
                    branch="main"
                )
                return True, "✅ Archivo de configuración del bot creado en GitHub"
            else:
                raise e

    except Exception as e:
        return False, f"❌ Error guardando en GitHub: {str(e)}"

# ========== INDICADOR DE SINCRONIZACIÓN ==========

def render_sync_indicator(bot_strategy, view_strategy):
    """Muestra el estado de sincronización entre Bot y Vista"""
    st.markdown(f"""
    <div class="sync-indicator">
        <h3>🎯 Estado de Sincronización</h3>
        <p>
            <strong>👁️ Vista Actual:</strong> {view_strategy.upper()} (solo afecta tabla) |
            <strong>🤖 Bot Operando:</strong> {bot_strategy.upper()} (ejecuta en GitHub)
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== PANEL DE CONTROL DEL BOT (MISIÓN) ==========

def render_bot_mission_panel():
    """Panel de Control del Bot - Configura la Misión Automática"""
    st.markdown("## 🤖 Misión del Bot (Piloto Automático)")
    st.markdown("*Configura qué estrategia y tickers ejecutará el bot automáticamente en GitHub Actions*")

    config = load_user_config()

    if not config:
        st.error("Error cargando configuración")
        return None, None

    strategies = config.get('strategies', {})

    # Selector de estrategia del bot
    st.markdown("### 🎯 Estrategia que Ejecutará el Bot")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🏆 Élite (Reversión)", use_container_width=True, key="bot_elite"):
            st.session_state['bot_strategy'] = 'elite'
        st.markdown("""
        **Reversión a la Media**
        - Tech stocks (NVDA, TSLA, AMD)
        - RSI < 30 (sobreventa)
        - Tendencia alcista (SMA 200)
        """)

    with col2:
        if st.button("🌊 Rompeolas (Breakout)", use_container_width=True, key="bot_rompeolas"):
            st.session_state['bot_strategy'] = 'rompeolas'
        st.markdown("""
        **Breakout de Energía**
        - Sector energía (XLE, OXY, CVX)
        - RSI > 50 (fuerza)
        - Volumen > 150% promedio
        """)

    if 'bot_strategy' not in st.session_state:
        st.session_state['bot_strategy'] = config.get('active_strategy', 'rompeolas')

    bot_strategy = st.session_state['bot_strategy']

    st.info(f"🤖 **Bot ejecutará:** {bot_strategy.upper()}")

    # Watchlist del bot
    st.markdown("### 📝 Watchlist del Bot")

    default_tickers = strategies.get(bot_strategy, {}).get('default_tickers', [])
    current_watchlist = config.get('watchlist', default_tickers)

    if st.button("📥 Cargar Tickers por Defecto", use_container_width=True):
        st.session_state['bot_watchlist_text'] = ", ".join(default_tickers)
        st.rerun()

    if 'bot_watchlist_text' not in st.session_state:
        st.session_state['bot_watchlist_text'] = ", ".join(current_watchlist)

    watchlist_input = st.text_area(
        "Tickers que el Bot Monitoreará (separados por comas)",
        value=st.session_state['bot_watchlist_text'],
        height=100,
        help="Ingresa los tickers separados por comas. Ej: NVDA, TSLA, AAPL"
    )

    st.markdown("---")

    # Botón de guardar misión
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 💾 Guardar Misión del Bot")
        st.markdown("*Al guardar, el Bot en GitHub Actions ejecutará esta estrategia automáticamente*")

    with col2:
        if st.button("💾 GUARDAR MISIÓN", type="primary", use_container_width=True):
            new_watchlist = [x.strip().upper() for x in watchlist_input.split(',') if x.strip()]

            new_config = config.copy()
            new_config['active_strategy'] = bot_strategy
            new_config['watchlist'] = new_watchlist
            new_config['last_updated'] = datetime.now().isoformat()

            try:
                with open('user_config.json', 'w') as f:
                    json.dump(new_config, f, indent=2)

                github_token = st.secrets.get("GITHUB_TOKEN", None)
                repo_name = st.secrets.get("GITHUB_REPO", None)

                if github_token and repo_name:
                    success, message = save_config_to_github(new_config, github_token, repo_name)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.warning(f"{message}\n\n⚠️ Guardado localmente, pero no sincronizado con GitHub.")
                else:
                    st.success("✅ Misión guardada localmente")
                    st.info("💡 Configura GITHUB_TOKEN y GITHUB_REPO en secrets para sincronización automática")

                st.session_state['bot_watchlist_text'] = ", ".join(new_watchlist)

            except Exception as e:
                st.error(f"❌ Error guardando: {e}")

    return bot_strategy, current_watchlist

# ========== RADAR DE MONITOREO INDEPENDIENTE ==========

def render_independent_monitoring_radar():
    """Radar de Monitoreo - Vista Visual Independiente del Bot"""
    st.markdown("## 📊 Radar de Monitoreo en Tiempo Real")
    st.markdown("*Selecciona qué estrategia quieres visualizar (independiente de la misión del bot)*")

    # Selector de estrategia VISUAL (solo afecta tabla)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🏆 Ver Élite", use_container_width=True, key="view_elite"):
            st.session_state['view_strategy'] = 'elite'

    with col2:
        if st.button("🌊 Ver Rompeolas", use_container_width=True, key="view_rompeolas"):
            st.session_state['view_strategy'] = 'rompeolas'

    with col3:
        if st.button("📈 Ver Larry Williams", use_container_width=True, key="view_larry"):
            st.session_state['view_strategy'] = 'larry'

    with col4:
        if st.button("📊 Ver Wyckoff", use_container_width=True, key="view_wyckoff"):
            st.session_state['view_strategy'] = 'wyckoff'

    if 'view_strategy' not in st.session_state:
        st.session_state['view_strategy'] = 'elite'

    view_strategy = st.session_state['view_strategy']

    st.info(f"👁️ **Visualizando:** {view_strategy.upper()} (esto NO afecta al bot)")

    return view_strategy

def render_trading_table_with_judges(df_signals, view_strategy):
    """Tabla de Trading con Opiniones de TODOS los Jueces"""
    st.markdown("### 📈 Tabla de Trading con Análisis Multi-Juez")

    # Preparar datos para mostrar
    display_data = []

    for idx, row in df_signals.iterrows():
        # Construir análisis de cada juez
        larry_opinion = f"{row['larry_signal']} | {row['larry_reason']}"
        wyckoff_opinion = f"{row['wyckoff_signal']} | {row['wyckoff_reason']}"
        elite_opinion = f"{row['elite_signal']} | {row['elite_reason']}"
        rompeolas_opinion = f"{row['rompeolas_signal']} | {row['rompeolas_reason']}"

        # Determinar señal principal según estrategia visualizada
        if view_strategy == 'larry':
            main_signal = row['larry_signal']
            main_reason = row['larry_reason']
        elif view_strategy == 'wyckoff':
            main_signal = row['wyckoff_signal']
            main_reason = row['wyckoff_reason']
        elif view_strategy == 'elite':
            main_signal = row['elite_signal']
            main_reason = row['elite_reason']
        else:  # rompeolas
            main_signal = row['rompeolas_signal']
            main_reason = row['rompeolas_reason']

        display_data.append({
            'Ticker': row['symbol'],
            'Precio': f"${row['price']:.2f}",
            'RSI': f"{row['rsi']:.1f}",
            'Señal Principal': main_signal,
            'Análisis': main_reason,
            'Larry Williams': larry_opinion,
            'Wyckoff': wyckoff_opinion,
            'Élite': elite_opinion,
            'Rompeolas': rompeolas_opinion
        })

    display_df = pd.DataFrame(display_data)

    # Aplicar colores a señal principal
    def color_signal(val):
        if 'CALL' in val:
            return 'background-color: #10B981; color: white; font-weight: bold;'
        elif 'SELL' in val:
            return 'background-color: #EF4444; color: white; font-weight: bold;'
        elif 'WATCH' in val:
            return 'background-color: #F59E0B; color: white; font-weight: bold;'
        else:
            return 'background-color: #6B7280; color: white;'

    # Mostrar tabla estilizada
    styled_df = display_df.style.applymap(color_signal, subset=['Señal Principal'])
    st.dataframe(styled_df, use_container_width=True, height=500)

    # Resumen de señales
    st.markdown("### 🎯 Resumen de Señales según Vista Actual")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        calls = display_df['Señal Principal'].str.contains('CALL').sum()
        st.metric("📈 CALL", calls)

    with col2:
        sells = display_df['Señal Principal'].str.contains('SELL').sum()
        st.metric("📉 SELL", sells)

    with col3:
        watches = display_df['Señal Principal'].str.contains('WATCH').sum()
        st.metric("👀 WATCH", watches)

    with col4:
        neutrals = display_df['Señal Principal'].str.contains('NEUTRAL').sum()
        st.metric("⚪ NEUTRAL", neutrals)

# ========== MAIN ==========

def main():
    st.markdown("# 📊 TradeOlympo v4.0")
    st.markdown("**Trading Terminal Profesional** | Arquitectura de Doble Propósito")
    st.markdown("---")

    # PANEL 1: Panel de Control del Bot (Misión)
    with st.expander("🤖 PANEL DE CONTROL DEL BOT (MISIÓN)", expanded=True):
        bot_strategy, bot_watchlist = render_bot_mission_panel()

    st.markdown("---")

    # PANEL 2: Radar de Monitoreo Independiente
    view_strategy = render_independent_monitoring_radar()

    # Indicador de Sincronización
    if bot_strategy and view_strategy:
        render_sync_indicator(bot_strategy, view_strategy)

    # Obtener credenciales de Alpaca
    api_key = st.secrets.get("ALPACA_API_KEY", os.environ.get('ALPACA_API_KEY'))
    secret_key = st.secrets.get("ALPACA_SECRET_KEY", os.environ.get('ALPACA_SECRET_KEY'))
    endpoint = st.secrets.get("ALPACA_ENDPOINT", os.environ.get('ALPACA_ENDPOINT', 'https://paper-api.alpaca.markets'))

    if not api_key or not secret_key:
        st.error("""
        ❌ **Credenciales de Alpaca no configuradas**

        Para ver datos en tiempo real, configura en Streamlit Secrets:
        ```toml
        ALPACA_API_KEY = "tu_key"
        ALPACA_SECRET_KEY = "tu_secret"
        ALPACA_ENDPOINT = "https://paper-api.alpaca.markets"
        ```
        """)
        return

    if not bot_watchlist:
        st.warning("⚠️ Configura la watchlist del bot en el Panel de Control")
        return

    # Botón de refresh
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Obtener datos de mercado
    with st.spinner('Obteniendo datos de mercado y consultando a todos los jueces...'):
        df = fetch_market_data(bot_watchlist, api_key, secret_key, endpoint)

    if df.empty:
        st.error("No se pudieron obtener datos de mercado")
        return

    # Generar señales de TODOS los jueces
    df_signals = generate_all_judges_signals(df)

    # Mostrar tabla con todos los jueces
    render_trading_table_with_judges(df_signals, view_strategy)

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6B7280; font-size: 0.85rem;'>
        TradeOlympo v4.0 | Arquitectura de Doble Propósito<br>
        Bot Mission: Piloto Automático | Monitoring Radar: Vista Independiente
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
