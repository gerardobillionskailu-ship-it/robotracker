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
                st.success("✅ API Key cargada desde Secrets - Datos reales activos")
            else:
                st.error("❌ API Key no configurada en Secrets")
                st.info("""
                **Para configurar tu API Key:**

                1. Ve a tu dashboard de Streamlit Cloud
                2. Abre "Settings" → "Secrets"
                3. Añade: `ALPHAVANTAGE_API_KEY = "tu_clave_aquí"`
                4. Obtén tu clave gratis en: https://www.alphavantage.co/support/#api-key

                Mientras tanto, usa el Modo Simulación.
                """)
        except Exception as e:
            # Si no hay secrets configurados (desarrollo local)
            st.warning("⚠️ Secrets no disponibles - Usando Modo Simulación")
            api_key = ""

        # Opción manual para desarrollo/override
        manual_key = st.text_input(
            "API Key Manual (opcional)",
            type="password",
            placeholder="Solo para desarrollo local",
            help="Sobrescribe la API Key de Secrets si es necesario"
        )

        if manual_key:
            api_key = manual_key
            st.info("🔧 Usando API Key manual")

        # Modo Simulación (automático si no hay API key)
        simulation_mode = st.toggle(
            "🎮 Modo Simulación",
            value=(not bool(api_key)),  # Activado si no hay API key
            help="""
            Genera datos sintéticos alcistas simulando un rally por cambio de régimen en Venezuela.
            Se activa automáticamente si no hay API Key.
            """
        )

        if simulation_mode:
            st.warning("⚡ Modo Simulación Activo: Usando datos sintéticos")

        st.markdown("---")

        # Información de cuenta
        st.subheader("💼 Tipo de Cuenta")
        st.info("**Cuenta Cash** (por defecto)")
        st.caption("Solo se sugerirán estrategias de compra directa (Long Calls o Acciones).")

        st.markdown("---")

        # Watchlist info
        st.subheader("📊 Símbolos Monitoreados")
        symbols = ["CVX", "SLB", "HAL", "XLE"]
        for symbol in symbols:
            st.markdown(f"• **{symbol}**")

        st.markdown("---")

        # Información adicional
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
            - yfinance
            - Plotly
            - Pandas & NumPy
            """)

        with st.expander("📖 Guía de Uso"):
            st.markdown("""
            **Cómo usar TradeOlympo:**

            1. **Selecciona tu estrategia** en el sidebar
            2. **Elige un símbolo** en el Watchlist
            3. **Revisa la señal** en la tarjeta central
            4. **Analiza el gráfico** interactivo
            5. **Lee las noticias** relacionadas

            **Interpretación de Señales:**
            - 🟢 **BUY**: Oportunidad de compra
            - 🔴 **SELL**: Considerar venta o esperar
            - 🟡 **HOLD**: Sin señal clara

            **Estrategias Cash:**
            - Long Call: Compra de opciones Call
            - Compra de Acciones: Compra directa
            """)

        st.markdown("---")

        # Footer
        st.caption(f"© 2024 TradeOlympo | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return strategy_mode, custom_ticker, simulation_mode, api_key


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

        # Renderizar sidebar y obtener configuración
        strategy_mode, custom_ticker, simulation_mode, api_key = render_sidebar()

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
        render_dashboard(strategy_mode, custom_ticker, simulation_mode, api_key)

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


# ========== MANEJO DE ERRORES DE DATOS ==========

def check_data_availability():
    """
    Verifica que se puedan obtener datos de yfinance.
    Útil para debugging y validación inicial.
    """
    import yfinance as yf

    try:
        test_ticker = yf.Ticker("CVX")
        test_data = test_ticker.history(period="1d")

        if test_data.empty:
            return False, "No se pudieron obtener datos de prueba"

        return True, "Conexión exitosa"

    except Exception as e:
        return False, f"Error de conexión: {str(e)}"


# ========== PUNTO DE ENTRADA ==========

if __name__ == "__main__":
    # Validación inicial (opcional, puede comentarse en producción)
    # success, message = check_data_availability()
    # if not success:
    #     st.error(f"Error de inicialización: {message}")
    #     st.stop()

    # Ejecutar aplicación
    main()
