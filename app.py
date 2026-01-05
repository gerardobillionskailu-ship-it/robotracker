"""
TradeOlympo - Aplicación de Análisis Financiero
Monitorea acciones y sugiere estrategias de opciones para cuentas Cash
"""

import streamlit as st
import sys
import traceback
from datetime import datetime

# Importar módulos personalizados
try:
    from views.dashboard import render_dashboard
    from utils.indicators import TechnicalIndicators
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.stop()


# ========== CONFIGURACIÓN DE LA PÁGINA ==========

st.set_page_config(
    page_title="TradeOlympo - Análisis Financiero",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== ESTILOS PERSONALIZADOS ==========

st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
        border-bottom: 2px solid #1f77b4;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)


# ========== SIDEBAR - CONFIGURACIÓN ==========

def render_sidebar():
    """
    Renderiza el sidebar con configuraciones de estrategia.
    """
    with st.sidebar:
        st.title("⚙️ TradeOlympo")
        st.markdown("---")

        # Selección de estrategia
        st.subheader("🎯 Modo de Estrategia")

        strategy_mode = st.radio(
            "Selecciona tu estrategia de análisis:",
            options=["Larry Williams", "Wyckoff"],
            index=0,
            help="""
            **Larry Williams**: Utiliza Williams %R y medias móviles para detectar momentum.

            **Wyckoff**: Analiza volumen y posición del cierre para identificar acumulación/distribución.
            """
        )

        st.markdown("---")

        # Ticker personalizado
        st.subheader("🔧 Configuración Avanzada")

        custom_ticker = st.text_input(
            "Ticker Manual (opcional)",
            placeholder="Ej: XOM, CVX.MX, AAPL",
            help="Ingresa un ticker personalizado para analizar. Deja vacío para usar watchlist."
        )

        # Alpha Vantage API Key - Usando Streamlit Secrets (Seguro)
        st.subheader("🔑 API de Datos Reales")

        # Intentar cargar API Key desde secrets
        try:
            api_key = st.secrets.get("ALPHAVANTAGE_API_KEY", "")
            if api_key:
                st.success("✅ API Key cargada")
            else:
                st.warning("⚠️ Sin API Key (Usando Simulación)")
        except Exception:
            # Si no hay secrets configurados (desarrollo local)
            api_key = ""

        # Modo Simulación (automático si no hay API key)
        simulation_mode = st.toggle(
            "🎮 Modo Simulación",
            value=(not bool(api_key)),  # Activado si no hay API key
            help="Genera datos sintéticos si no hay conexión API."
        )

        st.markdown("---")

        # Watchlist Editable (Universal)
        st.subheader("📊 Watchlist Personalizada")
        watchlist_symbols = st.multiselect(
            "Edita tus símbolos:",
            options=["CVX", "SLB", "HAL", "XLE", "AAPL", "MSFT", "GOOGL", "TSLA", "SPY", "QQQ"],
            default=["CVX", "SLB", "HAL", "XLE"],
            help="Selecciona los tickers que quieres monitorear"
        )

        # Modo Geopolítico (Venezuela)
        geopolitical_mode = st.toggle(
            "🌎 Modo Geopolítico (Venezuela)",
            value=True,
            help="Muestra alertas sobre Maduro y análisis petrolero venezolano. Apagar para ver solo técnico."
        )

        st.markdown("---")

        # Información de cuenta
        st.subheader("💼 Tipo de Cuenta")
        st.info("**Cuenta Cash** (por defecto)")
        st.caption("Solo se sugerirán estrategias de compra directa (Long Calls o Acciones).")

        st.markdown("---")

        # Información adicional
        with st.expander("ℹ️ Acerca de"):
            st.markdown("""
            **TradeOlympo v1.0**
            Stack: Streamlit | Alpha Vantage | Plotly
            """)

        # Footer
        st.caption(f"© 2024 TradeOlympo | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Retornamos TODAS las variables necesarias
    return strategy_mode, custom_ticker, simulation_mode, api_key, watchlist_symbols, geopolitical_mode


# ========== FUNCIÓN PRINCIPAL ==========

def main():
    """
    Función principal de la aplicación.
    Maneja el flujo y renderizado de componentes.
    """
    try:
        # Header principal
        st.title("📈 TradeOlympo - Análisis Financiero Avanzado")
        st.markdown("*Estrategias inteligentes para cuentas Cash*")

        # Renderizar sidebar y obtener TODAS las configuraciones
        strategy_mode, custom_ticker, simulation_mode, api_key, watchlist_symbols, geopolitical_mode = render_sidebar()

        # Mensaje de bienvenida (solo primera vez)
        if 'first_load' not in st.session_state:
            st.session_state['first_load'] = True
            mode_text = "🎮 Simulación" if simulation_mode else strategy_mode
            ticker_text = f" analizando **{custom_ticker}**" if custom_ticker else ""
            st.info(f"Bienvenido a TradeOlympo! Modo: **{mode_text}**{ticker_text}")

        st.markdown("---")

        # Renderizar dashboard principal pasando TODOS los argumentos
        # IMPORTANTE: render_dashboard en views/dashboard.py debe aceptar estos argumentos
        render_dashboard(
            strategy_mode, 
            custom_ticker, 
            simulation_mode, 
            api_key, 
            watchlist_symbols, 
            geopolitical_mode
        )

    except Exception as e:
        # Manejo elegante de errores
        st.error("❌ Ocurrió un error inesperado")
        with st.expander("🔍 Ver detalles del error"):
            st.code(traceback.format_exc())
        
        if st.button("🔄 Recargar Aplicación"):
            st.rerun()


# ========== PUNTO DE ENTRADA ==========

if __name__ == "__main__":
    main()