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

    # ========== GESTIÓN DE RIESGO INTERACTIVA ==========
    st.header("💰 Gestión de Riesgo (Regla del 15%)")

    st.markdown("""
    TradeOlympo incluye una **Calculadora de Gestión de Riesgo** automática que aparece
    cuando hay señal de **BUY**.

    ### 📐 Regla del 15%

    **NUNCA** debes arriesgar más del **15%** de tu capital en una sola operación de opciones.

    **¿Por qué?**
    - Las opciones pueden expirar sin valor (pérdida del 100% de la prima)
    - Diversificación: Con 15% por operación, puedes tener hasta 6 posiciones diferentes
    - Protección de capital: Si pierdes 3 operaciones seguidas, aún conservas 55% del capital
    """)

    st.markdown("---")

    # ========== CALCULADORA INTERACTIVA ==========
    st.subheader("🧮 Calculadora Interactiva de Riesgo")
    st.markdown("*Prueba con tu propio capital para entender la regla del 15%*")

    col1, col2 = st.columns(2)

    with col1:
        capital_usuario = st.number_input(
            "💵 Tu Capital Actual ($)",
            min_value=100,
            max_value=100000,
            value=1000,
            step=100,
            help="Capital total disponible para trading"
        )

    with col2:
        precio_accion = st.number_input(
            "📊 Precio de la Acción ($)",
            min_value=1.0,
            max_value=1000.0,
            value=150.0,
            step=5.0,
            help="Precio actual del ticker que quieres analizar"
        )

    # Cálculos dinámicos
    max_riesgo = capital_usuario * 0.15  # 15% del capital
    prima_estimada = precio_accion * 0.04  # 4% del precio (estimación conservadora)
    costo_contrato = prima_estimada * 100
    stop_loss = costo_contrato * 0.75  # -25%
    take_profit = costo_contrato * 1.50  # +50%

    # Mostrar resultados
    st.markdown("### 📊 Resultados Calculados:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🎯 Riesgo Máximo (15%)",
            f"${max_riesgo:.2f}",
            help="Nunca arriesgues más de esta cantidad en una operación"
        )

    with col2:
        st.metric(
            "💰 Costo Estimado (1 Call)",
            f"${costo_contrato:.2f}",
            help=f"Prima ~${prima_estimada:.2f}/acción × 100"
        )

    with col3:
        posiciones_posibles = int(capital_usuario / costo_contrato)
        st.metric(
            "📈 Posiciones Posibles",
            f"{posiciones_posibles}",
            help="Cantidad de contratos que podrías comprar con tu capital"
        )

    # Validación visual
    if costo_contrato <= max_riesgo:
        st.success(f"""
        ✅ **RIESGO CONTROLADO**: El costo (${costo_contrato:.2f}) está dentro de tu límite de ${max_riesgo:.2f}.

        **Stop Loss**: Vende si baja a ${stop_loss:.2f} (-25%)
        **Take Profit**: Vende si sube a ${take_profit:.2f} (+50%)

        **Capital restante**: ${capital_usuario - costo_contrato:.2f} para diversificar en otras oportunidades.
        """)
    else:
        st.error(f"""
        ⚠️ **RIESGO ALTO**: El costo (${costo_contrato:.2f}) supera tu límite de ${max_riesgo:.2f}.

        **Recomendaciones:**
        1. Busca un ticker más barato
        2. Usa un strike más alejado (OTM) con prima menor
        3. Aumenta tu capital base antes de operar
        4. NO operes hasta tener el capital adecuado
        """)

    st.warning("""
    ⚠️ **IMPORTANTE**: Esta calculadora usa precios **estimados**. Antes de operar,
    verifica el precio real de la opción en tu broker (ej: Robinhood, TD Ameritrade, Interactive Brokers).
    """)

    st.markdown("---")

    # ========== CHECKLIST DE DISCIPLINA ==========
    st.header("✅ Checklist de Disciplina (Antes de Operar)")
    st.markdown("*Marca todos los checks antes de ejecutar cualquier operación*")

    check1 = st.checkbox("📈 **¿Vi la tendencia?** - Revisé el gráfico y entiendo la dirección del precio", value=False)
    check2 = st.checkbox("💰 **¿Calculé el riesgo?** - Sé exactamente cuánto puedo perder (Stop Loss)", value=False)
    check3 = st.checkbox("🧘 **¿Estoy tranquilo?** - No estoy operando por FOMO o desesperación", value=False)
    check4 = st.checkbox("💔 **¿Acepto perder?** - Entiendo que puedo perder el 100% de la prima y lo acepto", value=False)

    all_checks = check1 and check2 and check3 and check4

    if all_checks:
        st.success("""
        🎉 **¡Listo para operar!**

        Has completado el checklist de disciplina. Recuerda:
        - Respeta tu Stop Loss sin excepciones
        - Toma ganancias en tu Take Profit (no seas codicioso)
        - Una pérdida es parte del juego, 6 de cada 10 operaciones ganadoras es EXCELENTE
        """)
    else:
        st.warning("""
        ⚠️ **No estás listo aún**

        Completa todos los checks antes de operar. La disciplina es la diferencia entre
        traders ganadores y perdedores. No te saltes este paso.
        """)

    st.markdown("---")

    # ========== QUIZ RÁPIDO ==========
    st.header("🎓 Quiz Rápido de Trading")
    st.markdown("*Refuerza tu conocimiento con esta pregunta:*")

    quiz_respuesta = st.radio(
        "**¿Qué haces si el precio toca tu Stop Loss?**",
        options=[
            "A) Espero un poco más, puede recuperarse",
            "B) Vendo inmediatamente sin dudarlo",
            "C) Compro más para promediar el precio",
            "D) Muevo el Stop Loss más abajo para darle espacio"
        ],
        index=None,
        help="Selecciona la respuesta correcta según las reglas de gestión de riesgo"
    )

    if quiz_respuesta:
        if quiz_respuesta.startswith("B)"):
            st.success("""
            ✅ **¡CORRECTO!**

            Cuando el precio toca tu Stop Loss, **VENDES INMEDIATAMENTE**.

            El Stop Loss existe para proteger tu capital. No hay "esperar un poco más" ni "darle espacio".
            Las mejores traders siguen sus reglas religiosamente.

            **Recuerda**: Es mejor salir con -25% y vivir para operar otro día, que quedarte esperando
            y perder -100%.
            """)
        else:
            st.error(f"""
            ❌ **Incorrecto**

            Respuesta correcta: **B) Vendo inmediatamente sin dudarlo**

            **¿Por qué las otras opciones son malas?**

            - **A) Esperar**: El mercado no te debe nada. Si tocó el Stop Loss, tu análisis falló. Sal.
            - **C) Promediar**: Esto es "añadir a una posición perdedora". Nunca lo hagas.
            - **D) Mover el Stop Loss**: Esto es trampa a ti mismo. Perderás más dinero.

            El Stop Loss es tu red de seguridad. Respétalo SIEMPRE.
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
