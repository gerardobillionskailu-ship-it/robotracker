"""
Guía de Uso para TradeOlympo
Página de ayuda interactiva para nuevos usuarios
"""

import streamlit as st


def render_guide():
    """
    Renderiza la guía completa de uso de TradeOlympo.
    Incluye explicaciones paso a paso, tabla de señales y reglas de gestión de riesgo.
    """
    st.title("📘 Guía de Uso - TradeOlympo")
    st.markdown("*Aprende a usar TradeOlympo en 5 minutos*")

    st.markdown("---")

    # ========== INTRODUCCIÓN ==========
    st.header("🎯 ¿Qué es TradeOlympo?")
    st.markdown("""
    **TradeOlympo** es una aplicación de análisis financiero que te ayuda a identificar
    oportunidades de compra de opciones Call y acciones para cuentas Cash.

    **Características principales:**
    - 📊 Análisis técnico con 2 estrategias probadas (Larry Williams y Wyckoff)
    - 💰 Calculadora de gestión de riesgo automática
    - 📈 Gráficos interactivos con indicadores visuales
    - 📰 Contexto de mercado y noticias
    """)

    st.markdown("---")

    # ========== CÓMO USAR LA APP ==========
    st.header("🚀 Cómo Usar la App (Paso a Paso)")

    st.subheader("**Paso 1: Selecciona tu Estrategia**")
    st.markdown("""
    En el **sidebar izquierdo**, elige tu estrategia de análisis:

    - **Larry Williams**: Analiza momentum usando Williams %R y medias móviles
      - ✅ Mejor para detectar tendencias y reversiones
      - ✅ Señales claras de sobrecompra/sobreventa

    - **Wyckoff**: Analiza volumen institucional y acumulación/distribución
      - ✅ Mejor para detectar movimientos de "dinero inteligente"
      - ✅ Identifica zonas de acumulación antes del rally
    """)

    st.subheader("**Paso 2: Elige un Símbolo del Watchlist**")
    st.markdown("""
    En la **columna izquierda (Watchlist)**, selecciona el ticker que quieres analizar:

    - Haz clic en el botón del símbolo (ej: CVX, SLB, HAL, XLE)
    - El símbolo seleccionado se resaltará en **azul**
    - También puedes editar tu Watchlist desde el sidebar
    """)

    st.subheader("**Paso 3: Revisa la Señal en la Tarjeta Central**")
    st.markdown("""
    La **columna central (Estrategia de Trading)** muestra:

    1. **Precio Actual**: Última cotización del ticker
    2. **Target**: Precio objetivo según la señal (+10% si BUY, -10% si SELL)
    3. **Confianza**: Porcentaje de confianza en la señal (0-100%)
    4. **Acción Recomendada**: Verde (BUY), Rojo (SELL), Amarillo (HOLD)
    """)

    st.subheader("**Paso 4: Analiza el Gráfico Interactivo**")
    st.markdown("""
    Debajo de la señal encontrarás un **gráfico interactivo** que muestra:

    - **Larry Williams**: Velas + Medias Móviles (SMA 20, 50, 200) + Williams %R
    - **Wyckoff**: Velas + Volumen con colores (Verde oscuro = acumulación, Rojo oscuro = distribución)

    **Tips del gráfico:**
    - 🖱️ Haz zoom con el mouse
    - 📊 Pasa el cursor sobre las velas para ver detalles
    - 📱 El gráfico es responsive (funciona en móviles)
    """)

    st.subheader("**Paso 5: Lee las Noticias de Contexto**")
    st.markdown("""
    La **columna derecha (Noticias)** muestra:

    - Alertas de mercado relacionadas con el símbolo
    - Si el **Modo Geopolítico** está activado, verás noticias sobre Venezuela
    - Úsalo para entender el contexto macro que afecta tus inversiones
    """)

    st.markdown("---")

    # ========== TABLA DE SEÑALES ==========
    st.header("🚦 Tabla de Señales")
    st.markdown("Aprende a interpretar las señales de TradeOlympo:")

    # Crear tabla con HTML para mejor formato
    st.markdown("""
    | Señal | Color | Significado | Acción Recomendada |
    |-------|-------|-------------|-------------------|
    | **🟢 BUY** | Verde | Oportunidad de compra detectada | Comprar Call o Acciones |
    | **🔴 SELL** | Rojo | Debilidad en el precio | No comprar / Considerar venta |
    | **🟡 HOLD** | Amarillo | Sin señal clara | Esperar mejor punto de entrada |

    **Niveles de Confianza:**
    - 🔥 **70-100%**: Señal muy fuerte (alta confianza)
    - 🟠 **60-69%**: Señal moderada (confianza media)
    - ⚪ **0-59%**: Señal débil (baja confianza)
    """)

    st.info("""
    💡 **Tip Profesional**: No operes solo por una señal. Combina la señal de TradeOlympo
    con tu propio análisis fundamental y contexto de mercado.
    """)

    st.markdown("---")

    # ========== GESTIÓN DE RIESGO ==========
    st.header("💰 Gestión de Riesgo (Regla del 15%)")

    st.markdown("""
    TradeOlympo incluye una **Calculadora de Gestión de Riesgo** automática que aparece
    cuando hay señal de **BUY**.

    ### 📐 Regla del 15%

    Si tienes un capital de **$1,000**, **NUNCA** debes arriesgar más del **15%** ($150)
    en una sola operación de opciones.

    **¿Por qué?**
    - Las opciones pueden expirar sin valor (pérdida del 100% de la prima)
    - Diversificación: Con 15% por operación, puedes tener hasta 6 posiciones diferentes
    - Protección de capital: Si pierdes 3 operaciones seguidas, aún tienes $550 (55% del capital)

    ### 🧮 Cómo Funciona la Calculadora

    Cuando ves una señal **BUY**, la app te muestra:

    1. **Costo Estimado (1 contrato)**: Prima estimada × 100 acciones
       - Ejemplo: Si AAPL está en $150, la prima de un Call +5% puede costar ~$600

    2. **Stop Loss (-25%)**: Precio al que debes salir si la opción pierde valor
       - Límita tu pérdida al 25% de la prima pagada
       - Ejemplo: Si pagaste $150, sal cuando baje a $112.50

    3. **Take Profit (+50%)**: Precio al que debes tomar ganancias
       - Asegura tu ganancia al 50% de la prima pagada
       - Ejemplo: Si pagaste $150, vende cuando suba a $225

    ### ✅ Validación Automática

    La app te dirá:

    - **✅ RIESGO CONTROLADO**: Si el costo está dentro del límite de $150
    - **⚠️ RIESGO ALTO**: Si el costo supera $150 (NO operes, espera otra oportunidad)
    """)

    st.warning("""
    ⚠️ **IMPORTANTE**: Esta calculadora usa precios **estimados**. Antes de operar,
    verifica el precio real de la opción en tu broker (ej: Robinhood, TD Ameritrade, Interactive Brokers).
    """)

    st.markdown("---")

    # ========== CONFIGURACIÓN AVANZADA ==========
    st.header("🔧 Configuración Avanzada")

    st.subheader("**🎮 Modo Simulación**")
    st.markdown("""
    Activa el **Modo Simulación** en el sidebar para:
    - Practicar con datos sintéticos sin gastar llamadas a la API
    - Aprender a usar la app sin riesgo
    - Simular un rally alcista (útil para demos)

    **Cuándo usarlo:**
    - Cuando estás aprendiendo a usar TradeOlympo
    - Si alcanzaste el límite de la API de Alpha Vantage (5 calls/min)
    - Para hacer pruebas sin afectar tus datos reales
    """)

    st.subheader("**🌎 Modo Geopolítico (Venezuela)**")
    st.markdown("""
    El **Modo Geopolítico** muestra alertas sobre Venezuela y su impacto en el sector energético.

    - **ON**: Muestra noticias sobre Maduro, CVX, SLB, HAL (útil si operas energía)
    - **OFF**: Oculta alertas geopolíticas, muestra mensaje genérico de mercado

    **Tip**: Si NO operas acciones de petróleo, desactívalo para reducir el ruido.
    """)

    st.subheader("**📊 Watchlist Personalizada**")
    st.markdown("""
    Edita tu Watchlist desde el sidebar:

    1. Click en el **multiselect de símbolos**
    2. Añade o quita tickers (ej: AAPL, MSFT, GOOGL, TSLA, SPY, QQQ)
    3. La app guarda tu selección durante la sesión

    **Símbolos disponibles:**
    - **Energía**: CVX, SLB, HAL, XLE
    - **Tech**: AAPL, MSFT, GOOGL, TSLA
    - **ETFs**: SPY (S&P 500), QQQ (Nasdaq 100)
    """)

    st.markdown("---")

    # ========== SOLUCIÓN DE PROBLEMAS ==========
    st.header("🛠️ Solución de Problemas")

    with st.expander("❌ No se cargan datos para el símbolo"):
        st.markdown("""
        **Posibles causas:**
        1. API Key de Alpha Vantage no configurada
           - **Solución**: Ve a Settings → Secrets y añade `ALPHAVANTAGE_API_KEY`

        2. Límite de API alcanzado (5 calls/min, 500 calls/día)
           - **Solución**: Espera 1 minuto o activa **Modo Simulación**

        3. Símbolo inválido o mal escrito
           - **Solución**: Verifica que el ticker sea correcto (ej: AAPL, no Apple)

        4. Conexión a Internet interrumpida
           - **Solución**: Verifica tu conexión y recarga la página
        """)

    with st.expander("📊 El gráfico no se ve bien en móvil"):
        st.markdown("""
        **Soluciones:**
        1. Rota tu dispositivo a modo horizontal
        2. Usa el zoom con dos dedos para acercar el gráfico
        3. Si usas Chrome, activa "Desktop Site" para mejor visualización

        **Nota**: La app está optimizada para desktop. En móviles, la experiencia
        puede ser limitada por el tamaño de pantalla.
        """)

    with st.expander("🔄 La app se recarga sola constantemente"):
        st.markdown("""
        **Causa**: Streamlit recarga cuando detecta cambios en el código o sesión.

        **Soluciones:**
        1. Verifica que no haya errores en la consola del navegador
        2. Limpia el caché del navegador (Ctrl+Shift+Delete)
        3. Cierra otras pestañas de TradeOlympo (solo debes tener 1 sesión abierta)
        """)

    with st.expander("⚠️ Aparece 'RIESGO ALTO' en la calculadora"):
        st.markdown("""
        **Significado**: El costo estimado del contrato supera el 15% de tu capital ($150).

        **¿Qué hacer?**
        1. **NO OPERES** con ese strike (es demasiado caro)
        2. Busca un strike más alejado (Out of the Money) con prima menor
        3. Espera otra oportunidad con un símbolo más barato
        4. Aumenta tu capital base (si $1,000 es muy poco, considera $2,000+)

        **Ejemplo:**
        - Si TSLA Call cuesta $800 → RIESGO ALTO (80% del capital)
        - Si AAPL Call cuesta $120 → RIESGO CONTROLADO (12% del capital) ✅
        """)

    st.markdown("---")

    # ========== RECURSOS ADICIONALES ==========
    st.header("📚 Recursos para Aprender Más")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📖 Estrategias")
        st.markdown("""
        **Larry Williams:**
        - Libro: *"Long-Term Secrets to Short-Term Trading"*
        - YouTube: Busca "Larry Williams %R strategy"

        **Wyckoff:**
        - Guía: [StockCharts - Wyckoff Method](https://school.stockcharts.com/doku.php?id=market_analysis:the_wyckoff_method)
        - YouTube: Busca "Wyckoff accumulation phases"
        """)

    with col2:
        st.subheader("🔗 Herramientas Externas")
        st.markdown("""
        **Datos de mercado:**
        - [Alpha Vantage](https://www.alphavantage.co) (API usada por TradeOlympo)
        - [Yahoo Finance](https://finance.yahoo.com) (noticias y fundamentales)

        **Brokers para opciones:**
        - Robinhood (comisión $0, interfaz simple)
        - TD Ameritrade (ThinkorSwim, avanzado)
        - Interactive Brokers (bajas comisiones)
        """)

    st.markdown("---")

    # ========== FOOTER ==========
    st.success("""
    🎉 **¡Listo para empezar!**

    Ve al **📈 Dashboard** en el sidebar y comienza a analizar tus primeros símbolos.
    Recuerda: practica primero en **Modo Simulación** antes de operar con dinero real.
    """)

    st.caption("TradeOlympo v1.0 | Documentación actualizada: 2026-01-04")
