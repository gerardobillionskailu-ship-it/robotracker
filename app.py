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
    from views.guide import render_guide
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
    Renderiza el sidebar con navegación y configuraciones.
    """
    with st.sidebar:
        st.title("⚙️ TradeOlympo")
        st.markdown("---")

        # NAVEGACIÓN PRINCIPAL
        page = st.radio(
            "📍 Navegación:",
            options=["📈 Dashboard", "📘 Guía de Uso"],
            index=0,
            help="Cambia entre el dashboard de trading y la guía de uso"
        )

        st.markdown("---")

        # Mostrar configuraciones solo si estamos en Dashboard
        if page == "📈 Dashboard":
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

            # Modo Simulación
            simulation_mode = st.toggle(
                "🎮 Modo Simulación",
                value=False,
                help="""
                Genera datos sintéticos alcistas simulando un rally por cambio de régimen en Venezuela.
                Útil cuando Alpha Vantage API está saturada o para demos.
                """
            )

            if simulation_mode:
                st.warning("⚡ Modo Simulación Activo: Usando datos sintéticos")

            st.markdown("---")

            # Watchlist Editable
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
                help="Muestra alertas sobre Maduro y análisis petrolero venezolano"
            )

            st.markdown("---")

            # Información de cuenta
            st.subheader("💼 Tipo de Cuenta")
            st.info("**Cuenta Cash** (por defecto)")
            st.caption("Solo se sugerirán estrategias de compra directa (Long Calls o Acciones).")

        else:
            # Si está en Guía, solo mostrar info básica
            strategy_mode = "Larry Williams"
            custom_ticker = ""
            simulation_mode = False
            watchlist_symbols = ["CVX", "SLB", "HAL", "XLE"]
            geopolitical_mode = True

        st.markdown("---")

        # Información adicional (siempre visible)
        with st.expander("ℹ️ Acerca de"):
            st.markdown("""
            **TradeOlympo v1.0**

            Aplicación de análisis financiero que combina:
            - Indicadores técnicos avanzados
            - Análisis de volumen Wyckoff
            - Noticias en tiempo real
            - Sugerencias de estrategias Cash

            **Stack Tecnológico:**
            - Streamlit
            - Alpha Vantage (API de datos reales)
            - Plotly
            - Pandas & NumPy
            """)

        st.markdown("---")

        # Footer
        st.caption(f"© 2024 TradeOlympo | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return page, strategy_mode, custom_ticker, simulation_mode, watchlist_symbols, geopolitical_mode


# ========== FUNCIÓN PRINCIPAL ==========

def main():
    """
    Función principal de la aplicación.
    Maneja el flujo y renderizado de componentes.
    """
    try:
        # Renderizar sidebar y obtener configuración
        page, strategy_mode, custom_ticker, simulation_mode, watchlist_symbols, geopolitical_mode = render_sidebar()

        # Renderizar página según selección
        if page == "📘 Guía de Uso":
            # Mostrar guía de uso
            render_guide()

        else:  # Dashboard
            # Header principal
            st.title("📈 TradeOlympo - Análisis Financiero Avanzado")
            st.markdown("*Estrategias inteligentes para cuentas Cash*")

            # Mensaje de bienvenida (solo primera vez)
            if 'first_load' not in st.session_state:
                st.session_state['first_load'] = True
                mode_text = "🎮 Simulación" if simulation_mode else strategy_mode
                ticker_text = f" analizando **{custom_ticker}**" if custom_ticker else ""
                st.info(f"""
                ¡Bienvenido a TradeOlympo!

                Modo: **{mode_text}**{ticker_text}
                Selecciona un símbolo en el Watchlist para comenzar el análisis.
                """)

            st.markdown("---")

            # Renderizar dashboard principal
            render_dashboard(strategy_mode, custom_ticker, simulation_mode, watchlist_symbols, geopolitical_mode)

    except Exception as e:
        # Manejo elegante de errores
        st.error("❌ Ocurrió un error inesperado")

        with st.expander("🔍 Ver detalles del error"):
            st.code(traceback.format_exc())

        st.warning("""
        **Posibles soluciones:**
        - Verifica tu conexión a Internet
        - Intenta seleccionar otro símbolo
        - Recarga la página (F5)
        - Revisa que los paquetes estén instalados correctamente
        """)

        # Botón para recargar
        if st.button("🔄 Recargar Aplicación"):
            st.rerun()


# ========== PUNTO DE ENTRADA ==========

if __name__ == "__main__":
    main()
