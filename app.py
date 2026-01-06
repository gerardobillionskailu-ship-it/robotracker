"""
TradeOlympo - Plataforma Profesional de Análisis Financiero
Interfaz Dark Mode con persistencia de configuración
"""

import streamlit as st
import json
import os
from datetime import datetime
from github import Github, GithubException

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

    /* Señales de Trading */
    .signal-buy {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        font-weight: 700;
        text-align: center;
        margin: 0.5rem 0;
    }

    .signal-sell {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        font-weight: 700;
        text-align: center;
        margin: 0.5rem 0;
    }

    .signal-neutral {
        background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        font-weight: 700;
        text-align: center;
        margin: 0.5rem 0;
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

    /* Sidebar */
    .css-1d391kg {
        background-color: #161B22;
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

    /* Cards */
    .status-card {
        background-color: #1A1D24;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Input fields */
    .stTextInput>div>div>input {
        background-color: #1A1D24;
        color: #FAFAFA;
        border: 1px solid #2D3748;
        border-radius: 8px;
    }

    .stSelectbox>div>div>select {
        background-color: #1A1D24;
        color: #FAFAFA;
        border: 1px solid #2D3748;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNCIONES DE CONFIGURACIÓN ==========

def load_user_config():
    """Carga la configuración del usuario desde user_config.json"""
    try:
        if os.path.exists('user_config.json'):
            with open('user_config.json', 'r') as f:
                return json.load(f)
        else:
            # Config por defecto
            return {
                "active_strategy": "rompeolas",
                "watchlist": ["XLE", "OXY", "APA", "CVX"],
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        return None

def save_config_to_github(config_data, github_token, repo_name):
    """
    Guarda la configuración en GitHub usando PyGithub

    Args:
        config_data: Dict con la configuración
        github_token: Token de acceso personal de GitHub
        repo_name: Nombre del repo (ej: "usuario/robotracker")

    Returns:
        (success: bool, message: str)
    """
    try:
        # Conectar a GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        # Obtener el archivo actual
        try:
            file = repo.get_contents("user_config.json")
            sha = file.sha
            message = f"Update config: {config_data['active_strategy']} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # Actualizar archivo
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
                # El archivo no existe, crearlo
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
            # Mostrar en 4 columnas
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

    # Selector de estrategia
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

    # Mostrar estrategia seleccionada
    if 'selected_strategy' not in st.session_state:
        st.session_state['selected_strategy'] = config.get('active_strategy', 'rompeolas')

    current_strategy = st.session_state['selected_strategy']

    st.info(f"🎯 Estrategia seleccionada: **{current_strategy.upper()}**")

    # Editor de watchlist
    st.markdown("### 📝 Editar Watchlist")

    # Obtener default tickers de la estrategia
    default_tickers = strategies.get(current_strategy, {}).get('default_tickers', [])
    current_watchlist = config.get('watchlist', default_tickers)

    # Botón para cargar defaults
    if st.button("📥 Cargar Tickers por Defecto", use_container_width=True):
        st.session_state['watchlist_text'] = ", ".join(default_tickers)
        st.rerun()

    # Editor de texto
    if 'watchlist_text' not in st.session_state:
        st.session_state['watchlist_text'] = ", ".join(current_watchlist)

    watchlist_input = st.text_area(
        "Tickers (separados por comas)",
        value=st.session_state['watchlist_text'],
        height=100,
        help="Ingresa los tickers separados por comas. Ej: NVDA, TSLA, AAPL"
    )

    # Guardar configuración
    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 💾 Guardar y Sincronizar")
        st.markdown("Al guardar, el Bot en GitHub Actions usará esta configuración en la próxima ejecución.")

    with col2:
        if st.button("💾 GUARDAR", type="primary", use_container_width=True):
            # Preparar nueva config
            new_watchlist = [x.strip().upper() for x in watchlist_input.split(',') if x.strip()]

            new_config = config.copy()
            new_config['active_strategy'] = current_strategy
            new_config['watchlist'] = new_watchlist
            new_config['last_updated'] = datetime.now().isoformat()

            # Guardar localmente
            try:
                with open('user_config.json', 'w') as f:
                    json.dump(new_config, f, indent=2)

                # Intentar guardar en GitHub
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

                # Actualizar session state
                st.session_state['watchlist_text'] = ", ".join(new_watchlist)

            except Exception as e:
                st.error(f"❌ Error guardando: {e}")

# ========== VISTA DE ANÁLISIS (SIMPLIFICADA) ==========

def render_analysis_view():
    """Vista de análisis de mercado (placeholder para integración futura)"""
    st.markdown("## 📊 Análisis de Mercado")

    st.info("""
    **Panel de Análisis en Desarrollo**

    Esta sección mostrará:
    - Gráficos de precios en tiempo real
    - Indicadores técnicos (RSI, SMA)
    - Señales de compra/venta
    - Recomendaciones de contratos de opciones

    Por ahora, enfócate en configurar el bot usando el panel de la izquierda.
    """)

    # Mostrar últimas señales del bot (si existen)
    if os.path.exists('last_run_results.json'):
        st.markdown("### 🎯 Últimas Señales del Bot")

        try:
            with open('last_run_results.json', 'r') as f:
                results = json.load(f)

            if results:
                for result in results[:5]:  # Mostrar las últimas 5
                    ticker = result.get('ticker', 'N/A')
                    signal = result.get('signal', 'N/A')
                    price = result.get('price', 0)

                    # Determinar color de señal
                    if 'CALL' in signal.upper():
                        signal_class = 'signal-buy'
                    elif 'SELL' in signal.upper() or 'PUT' in signal.upper():
                        signal_class = 'signal-sell'
                    else:
                        signal_class = 'signal-neutral'

                    st.markdown(f"""
                    <div class="{signal_class}">
                        <strong>{ticker}</strong> | {signal} | ${price:.2f}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No hay señales recientes")

        except Exception as e:
            st.warning(f"No se pudieron cargar las últimas señales: {e}")

# ========== MAIN ==========

def main():
    # Logo y título
    st.markdown("# 📊 TradeOlympo")
    st.markdown("**Trading Terminal Profesional** | Dark Mode Edition")
    st.markdown("---")

    # Panel superior: Estado del Bot
    render_bot_status()

    st.markdown("---")

    # Layout de 2 columnas
    col1, col2 = st.columns([1, 2])

    with col1:
        render_config_panel()

    with col2:
        render_analysis_view()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6B7280; font-size: 0.85rem;'>
        TradeOlympo v3.0 | Arquitectura Modular con Persistencia<br>
        Bot Status: 🟢 Online | Data: Alpaca API (IEX Feed)
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
