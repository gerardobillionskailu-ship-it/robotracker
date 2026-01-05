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
            # NOTA: Removido selector de estrategia - ahora mostramos VISIÓN DOBLE siempre
            st.info("💡 **Visión Doble**: Viendo Larry Williams y Wyckoff simultáneamente")

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

            # Botón de Forzar Actualización
            if st.button("🔄 Forzar Actualización", use_container_width=True, help="Limpia el caché y recarga los precios en tiempo real"):
                st.cache_data.clear()
                st.success("✅ Caché limpiado. Actualizando precios...")
                st.rerun()

            st.markdown("---")

            # Sistema de Listas Temáticas
            st.subheader("📂 Listas Temáticas")

            # Inicializar lista personal en session_state
            if 'personal_watchlist' not in st.session_state:
                st.session_state['personal_watchlist'] = ["AAPL", "MSFT"]

            # Selectbox para elegir tema
            theme_choice = st.selectbox(
                "Selecciona un Tema:",
                options=[
                    "🇻🇪 Venezuela Recovery",
                    "🚀 Tech & Growth",
                    "⭐ Mi Lista Personal"
                ],
                index=0,
                help="Elige una lista temática pre-configurada o crea tu propia lista"
            )

            # Asignar símbolos según el tema elegido
            if theme_choice == "🇻🇪 Venezuela Recovery":
                watchlist_symbols = ["BKR", "WFRD", "COP", "VLO", "CVX", "SLB"]
            elif theme_choice == "🚀 Tech & Growth":
                watchlist_symbols = ["NVDA", "META", "TSLA", "AMD", "COIN"]
            else:  # Mi Lista Personal
                watchlist_symbols = st.session_state['personal_watchlist']

                # Mostrar input para agregar tickers solo en lista personal
                st.caption("🎯 Gestiona tu lista personal:")
                col_input, col_btn = st.columns([3, 1])

                with col_input:
                    new_ticker = st.text_input(
                        "Agregar ticker:",
                        placeholder="Ej: NVDA",
                        label_visibility="collapsed",
                        key="add_ticker_input"
                    )

                with col_btn:
                    if st.button("➕", key="add_ticker_btn", use_container_width=True):
                        if new_ticker and new_ticker.strip().upper() not in st.session_state['personal_watchlist']:
                            st.session_state['personal_watchlist'].append(new_ticker.strip().upper())
                            st.rerun()

                # Mostrar lista actual con opción de eliminar
                if st.session_state['personal_watchlist']:
                    st.caption("📋 Tickers actuales:")
                    for ticker in st.session_state['personal_watchlist']:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.text(f"• {ticker}")
                        with col2:
                            if st.button("🗑️", key=f"remove_{ticker}", use_container_width=True):
                                st.session_state['personal_watchlist'].remove(ticker)
                                st.rerun()

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
            custom_ticker = ""
            simulation_mode = False
            watchlist_symbols = ["CVX", "SLB", "HAL", "XLE"]
            geopolitical_mode = True

        # strategy_mode siempre es "Dual" ahora (no se usa pero lo retornamos por compatibilidad)
        strategy_mode = "Dual"

        st.markdown("---")

        # Información adicional (siempre visible)
        with st.expander("ℹ️ Acerca de"):
            st.markdown("""
            **TradeOlympo v1.0**

            Aplicación de análisis financiero que combina:
            - **Visión Doble**: Larry Williams + Wyckoff simultáneamente
            - Cálculo automático de Strike Ideal
            - Gestión de riesgo con regla del 15%
            - Noticias contextuales

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
            # Obtener API key de secrets de forma segura
            try:
                api_key = st.secrets.get("ALPHAVANTAGE_API_KEY", "")
            except Exception:
                api_key = ""

            # Renderizar dashboard principal con api_key
            render_dashboard(strategy_mode, custom_ticker, simulation_mode, api_key, watchlist_symbols, geopolitical_mode)

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
