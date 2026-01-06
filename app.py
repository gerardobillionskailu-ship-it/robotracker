"""
TradeOlympo - Plataforma Profesional de Análisis Financiero
Interfaz Dark Mode con persistencia de configuración
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
        font-size: 2rem;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #B0B0B0;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tablas */
    .dataframe {
        background-color: #1A1D24 !important;
        border-radius: 8px;
    }

    /* Headers */
    h1 {
        color: #1E88E5;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 1rem;
    }

    h2 {
        color: #60A5FA;
        font-weight: 700;
        margin-top: 1.5rem;
    }

    h3 {
        color: #93C5FD;
        font-weight: 600;
    }

    /* Success/Error boxes */
    .stSuccess {
        background-color: #065F46;
        color: #D1FAE5;
        border-left: 4px solid #10B981;
    }

    .stError {
        background-color: #7F1D1D;
        color: #FEE2E2;
        border-left: 4px solid #EF4444;
    }

    .stInfo {
        background-color: #1E3A8A;
        color: #DBEAFE;
        border-left: 4px solid #3B82F6;
    }

    /* Input fields */
    .stTextInput>div>div>input {
        background-color: #1A1D24;
        color: #FAFAFA;
        border: 1px solid #2D3748;
        border-radius: 8px;
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

                # Obtener datos históricos (60 días para calcular indicadores)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)

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

                # RSI
                delta = closes.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 0

                # SMAs
                sma_20 = closes.rolling(window=20).mean().iloc[-1]
                sma_200 = closes.rolling(window=200).mean().iloc[-1] if len(closes) >= 200 else closes.rolling(window=20).mean().iloc[-1]

                # Volumen promedio
                avg_volume = volumes.tail(30).mean()

                # Resistencia (para Rompeolas)
                resistencia_20d = bars['high'].rolling(20).max().shift(1).iloc[-1]

                results.append({
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': rsi_val,
                    'sma_20': sma_20,
                    'sma_200': sma_200,
                    'volume': volumes.iloc[-1],
                    'avg_volume': avg_volume,
                    'resistencia_20d': resistencia_20d
                })

            except Exception as e:
                st.warning(f"Error obteniendo datos de {symbol}: {str(e)}")
                continue

        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Error conectando a Alpaca API: {str(e)}")
        return pd.DataFrame()

def generate_signals(df, strategy):
    """
    Genera señales de trading basadas en la estrategia

    Args:
        df: DataFrame con datos de mercado
        strategy: 'elite' o 'rompeolas'

    Returns:
        DataFrame con columna 'signal' y 'reason'
    """
    signals = []

    for idx, row in df.iterrows():
        signal = "NEUTRAL"
        reason = ""

        if strategy == 'elite':
            # ESTRATEGIA ÉLITE: RSI < 30 + Precio > SMA 200
            if row['rsi'] < 30:
                if row['price'] > row['sma_200']:
                    signal = "CALL"
                    reason = f"Sobrevendido (RSI {row['rsi']:.1f}) en tendencia alcista"
                else:
                    signal = "WATCH"
                    reason = f"RSI bajo ({row['rsi']:.1f}) pero sin tendencia"
            elif row['price'] > row['sma_20'] and 40 < row['rsi'] < 55:
                signal = "WATCH"
                reason = f"Pullback sano (RSI {row['rsi']:.1f})"
            else:
                reason = f"RSI {row['rsi']:.1f} | Precio vs SMA200: {((row['price']/row['sma_200']-1)*100):.1f}%"

        elif strategy == 'rompeolas':
            # ESTRATEGIA ROMPEOLAS: Breakout + RSI > 50 + Volumen > 150%
            breakout = row['price'] > row['resistencia_20d'] if pd.notna(row['resistencia_20d']) else False
            volumen_alto = row['volume'] > (row['avg_volume'] * 1.5)
            fuerza = row['rsi'] > 50

            if breakout and fuerza:
                if volumen_alto:
                    signal = "CALL"
                    reason = f"Breakout confirmado (RSI {row['rsi']:.1f}, Vol +{((row['volume']/row['avg_volume']-1)*100):.0f}%)"
                else:
                    signal = "WATCH"
                    reason = f"Breakout sin volumen (RSI {row['rsi']:.1f})"
            else:
                if breakout:
                    reason = f"Breakout pero RSI {row['rsi']:.1f} < 50"
                else:
                    reason = f"Precio ${row['price']:.2f} < Resistencia ${row['resistencia_20d']:.2f}"

        signals.append({'signal': signal, 'reason': reason})

    signals_df = pd.DataFrame(signals)
    return pd.concat([df, signals_df], axis=1)

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
                "last_updated": datetime.now().isoformat()
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
            message = f"Update config: {config_data['active_strategy']} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            repo.update_file(
                path="user_config.json",
                message=message,
                content=json.dumps(config_data, indent=2),
                sha=sha,
                branch="main"
            )
            return True, "✅ Configuración guardada exitosamente en GitHub"

        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path="user_config.json",
                    message="Create user_config.json",
                    content=json.dumps(config_data, indent=2),
                    branch="main"
                )
                return True, "✅ Archivo de configuración creado en GitHub"
            else:
                raise e

    except Exception as e:
        return False, f"❌ Error guardando en GitHub: {str(e)}"

# ========== PANEL DE ESTADO DEL BOT ==========

def render_bot_status():
    """Muestra el estado actual del bot desde user_config.json"""
    st.markdown("## 🤖 Estado Actual del Bot")

    config = load_user_config()

    if config:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Estrategia Activa",
                config.get('active_strategy', 'N/A').upper(),
                delta=None
            )

        with col2:
            watchlist = config.get('watchlist', [])
            st.metric(
                "Tickers en Vigilancia",
                len(watchlist),
                delta=None
            )

        with col3:
            last_update = config.get('last_updated', 'Nunca')
            if last_update != 'Nunca':
                try:
                    dt = datetime.fromisoformat(last_update)
                    last_update = dt.strftime('%d/%m %H:%M')
                except:
                    pass
            st.metric(
                "Última Actualización",
                last_update,
                delta=None
            )

        # Mostrar watchlist
        st.markdown("### 📋 Watchlist Activa")
        if watchlist:
            cols = st.columns(4)
            for idx, ticker in enumerate(watchlist):
                with cols[idx % 4]:
                    st.code(ticker, language=None)
        else:
            st.warning("⚠️ No hay tickers en la watchlist")
    else:
        st.error("❌ No se pudo cargar la configuración del bot")

# ========== PANEL DE CONFIGURACIÓN ==========

def render_config_panel():
    """Panel para cambiar la configuración del bot"""
    st.markdown("## ⚙️ Configurar Bot")

    config = load_user_config()

    if not config:
        st.error("Error cargando configuración")
        return

    st.markdown("### 🎯 Seleccionar Estrategia")

    strategies = config.get('strategies', {})

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🏆 Estrategia Élite", use_container_width=True):
            st.session_state['selected_strategy'] = 'elite'
        st.markdown("""
        **Reversión a la Media**
        - Tech stocks (NVDA, TSLA, AMD)
        - RSI < 30 (sobreventa)
        - Tendencia alcista (SMA 200)
        """)

    with col2:
        if st.button("🌊 Estrategia Rompeolas", use_container_width=True):
            st.session_state['selected_strategy'] = 'rompeolas'
        st.markdown("""
        **Breakout de Energía**
        - Sector energía (XLE, OXY, CVX)
        - RSI > 50 (fuerza)
        - Volumen > 150% promedio
        """)

    if 'selected_strategy' not in st.session_state:
        st.session_state['selected_strategy'] = config.get('active_strategy', 'rompeolas')

    current_strategy = st.session_state['selected_strategy']

    st.info(f"🎯 Estrategia seleccionada: **{current_strategy.upper()}**")

    st.markdown("### 📝 Editar Watchlist")

    default_tickers = strategies.get(current_strategy, {}).get('default_tickers', [])
    current_watchlist = config.get('watchlist', default_tickers)

    if st.button("📥 Cargar Tickers por Defecto", use_container_width=True):
        st.session_state['watchlist_text'] = ", ".join(default_tickers)
        st.rerun()

    if 'watchlist_text' not in st.session_state:
        st.session_state['watchlist_text'] = ", ".join(current_watchlist)

    watchlist_input = st.text_area(
        "Tickers (separados por comas)",
        value=st.session_state['watchlist_text'],
        height=100,
        help="Ingresa los tickers separados por comas. Ej: NVDA, TSLA, AAPL"
    )

    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 💾 Guardar y Sincronizar")
        st.markdown("Al guardar, el Bot en GitHub Actions usará esta configuración.")

    with col2:
        if st.button("💾 GUARDAR", type="primary", use_container_width=True):
            new_watchlist = [x.strip().upper() for x in watchlist_input.split(',') if x.strip()]

            new_config = config.copy()
            new_config['active_strategy'] = current_strategy
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
                    st.success("✅ Configuración guardada localmente")
                    st.info("💡 Configura GITHUB_TOKEN y GITHUB_REPO en secrets para sincronización automática")

                st.session_state['watchlist_text'] = ", ".join(new_watchlist)

            except Exception as e:
                st.error(f"❌ Error guardando: {e}")

# ========== VISTA DE ANÁLISIS EN TIEMPO REAL ==========

def render_analysis_view():
    """Vista de análisis de mercado con datos en tiempo real"""
    st.markdown("## 📊 Análisis de Mercado en Tiempo Real")

    config = load_user_config()

    if not config:
        st.error("No se pudo cargar la configuración")
        return

    watchlist = config.get('watchlist', [])
    strategy = config.get('active_strategy', 'rompeolas')

    if not watchlist:
        st.warning("⚠️ No hay tickers en la watchlist. Configura tu lista en el panel izquierdo.")
        return

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

    # Botón de refresh
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Obtener datos
    with st.spinner('Obteniendo datos de mercado...'):
        df = fetch_market_data(watchlist, api_key, secret_key, endpoint)

    if df.empty:
        st.error("No se pudieron obtener datos de mercado")
        return

    # Generar señales
    df_with_signals = generate_signals(df, strategy)

    # Mostrar tabla profesional
    st.markdown("### 📈 Tabla de Trading")

    # Formatear DataFrame para mostrar
    display_df = df_with_signals[['symbol', 'price', 'rsi', 'signal', 'volume', 'avg_volume', 'reason']].copy()
    display_df.columns = ['Ticker', 'Precio', 'RSI', 'Señal', 'Volumen Actual', 'Volumen Prom', 'Análisis']

    # Formatear números
    display_df['Precio'] = display_df['Precio'].apply(lambda x: f"${x:.2f}")
    display_df['RSI'] = display_df['RSI'].apply(lambda x: f"{x:.1f}")
    display_df['Volumen Actual'] = display_df['Volumen Actual'].apply(lambda x: f"{int(x):,}")
    display_df['Volumen Prom'] = display_df['Volumen Prom'].apply(lambda x: f"{int(x):,}")

    # Aplicar colores a las señales
    def color_signal(val):
        if val == 'CALL':
            return 'background-color: #10B981; color: white; font-weight: bold;'
        elif val == 'SELL':
            return 'background-color: #EF4444; color: white; font-weight: bold;'
        elif val == 'WATCH':
            return 'background-color: #F59E0B; color: white; font-weight: bold;'
        else:
            return 'background-color: #6B7280; color: white;'

    # Mostrar tabla estilizada
    styled_df = display_df.style.applymap(color_signal, subset=['Señal'])
    st.dataframe(styled_df, use_container_width=True, height=400)

    # Resumen de señales
    st.markdown("### 🎯 Resumen de Señales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        calls = len(df_with_signals[df_with_signals['signal'] == 'CALL'])
        st.metric("📈 CALL", calls, delta=None)

    with col2:
        sells = len(df_with_signals[df_with_signals['signal'] == 'SELL'])
        st.metric("📉 SELL", sells, delta=None)

    with col3:
        watches = len(df_with_signals[df_with_signals['signal'] == 'WATCH'])
        st.metric("👀 WATCH", watches, delta=None)

    with col4:
        neutrals = len(df_with_signals[df_with_signals['signal'] == 'NEUTRAL'])
        st.metric("⚪ NEUTRAL", neutrals, delta=None)

    # Destacar señales CALL
    calls_df = df_with_signals[df_with_signals['signal'] == 'CALL']
    if not calls_df.empty:
        st.markdown("### 🚀 Señales de Compra Activas")
        for idx, row in calls_df.iterrows():
            st.success(f"""
            **{row['symbol']}** @ ${row['price']:.2f}

            {row['reason']}

            RSI: {row['rsi']:.1f} | Volumen: {int(row['volume']):,}
            """)

# ========== MAIN ==========

def main():
    st.markdown("# 📊 TradeOlympo")
    st.markdown("**Trading Terminal Profesional** | Dark Mode Edition")
    st.markdown("---")

    render_bot_status()

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        render_config_panel()

    with col2:
        render_analysis_view()

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6B7280; font-size: 0.85rem;'>
        TradeOlympo v3.0 | Arquitectura Modular con Persistencia<br>
        Bot Status: 🟢 Online | Data: Alpaca API (IEX Feed)
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
