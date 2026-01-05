"""
Dashboard View para TradeOlympo
Gestiona la interfaz visual de 3 columnas: Watchlist, Estrategia, Noticias
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from utils.indicators import TechnicalIndicators, get_support_resistance, fetch_stock_data, generate_synthetic_data


# ========== CONFIGURACIÓN ==========

DEFAULT_WATCHLIST = ['CVX', 'SLB', 'HAL', 'XLE']
FALLBACK_SYMBOL = "AAPL"  # Símbolo por defecto si no hay selección


# ========== COLUMNA 1: WATCHLIST ==========

def render_watchlist(symbols=None):
    """
    Renderiza la columna de Watchlist con selección de símbolos.
    Los precios se muestran en la Tarjeta de Estrategia (Alpha Vantage).
    """
    if not symbols:
        symbols = DEFAULT_WATCHLIST

    st.header("📊 Watchlist")

    selected_symbol = st.session_state.get('selected_symbol', symbols[0] if symbols else 'CVX')

    # Mostrar cada símbolo como botón seleccionable
    for symbol in symbols:
        if st.button(
            symbol,
            key=f"btn_{symbol}",
            use_container_width=True,
            type="primary" if symbol == selected_symbol else "secondary"
        ):
            st.session_state['selected_symbol'] = symbol
            st.rerun()

    st.divider()

    # Información del símbolo seleccionado
    if selected_symbol:
        st.subheader(f"📍 Seleccionado: {selected_symbol}")
        st.info("💡 Los precios y métricas se muestran en la **Tarjeta de Estrategia** con datos de Alpha Vantage.")


# ========== COLUMNA 2: TARJETA DE ESTRATEGIA DINÁMICA ==========

def render_strategy_card(strategy_mode: str, custom_ticker: str = "", simulation_mode: bool = False):
    """
    Renderiza la tarjeta de estrategia que cambia dinámicamente
    según el indicador seleccionado.

    Args:
        strategy_mode: 'Larry Williams' o 'Wyckoff'
        custom_ticker: Ticker personalizado ingresado por el usuario
        simulation_mode: Si True, usa datos sintéticos en lugar de yfinance
    """
    st.header("🎯 Estrategia de Trading")

    # Usar ticker personalizado si está presente, sino usar del watchlist
    if custom_ticker and custom_ticker.strip():
        selected_symbol = custom_ticker.strip().upper()
        st.info(f"📊 Analizando ticker personalizado: **{selected_symbol}**")
    else:
        selected_symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    try:
        # Obtener datos: sintéticos o reales
        if simulation_mode:
            st.success("🎮 Usando datos sintéticos - Rally por cambio de régimen en Venezuela")
            df = generate_synthetic_data(selected_symbol, days=500)
        else:
            # Obtener datos históricos usando función robusta con User-Agent
            df = fetch_stock_data(selected_symbol, period="2y")

        # Validar que el DataFrame no esté vacío y tenga suficientes datos
        if df is None or df.empty or len(df) < 20:
            st.error(f"❌ No se pudieron obtener suficientes datos para {selected_symbol}")
            st.info("""
            **Posibles causas:**
            - El símbolo no existe o está mal escrito
            - Problemas de conexión con Yahoo Finance
            - El símbolo no tiene datos históricos disponibles

            **Sugerencias:**
            - Intenta con otro símbolo del watchlist
            - Recarga la página
            - Verifica tu conexión a Internet
            """)
            return

        # Validar que tenemos las columnas necesarias
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"❌ Faltan columnas en los datos: {', '.join(missing_columns)}")
            return

        # Validar que no haya valores nulos en columnas críticas
        if df[required_columns].isnull().any().any():
            st.warning("⚠️ Algunos datos contienen valores nulos. Rellenando...")
            df = df.ffill().bfill()

        # Verificar nuevamente que tengamos datos válidos
        if df.empty or len(df) < 20:
            st.error("❌ Datos insuficientes después de validación")
            return

        # Calcular indicadores
        indicators = TechnicalIndicators(df)
        df_with_indicators = indicators.calculate_all_indicators()

        # Validar que los indicadores se calcularon correctamente
        if df_with_indicators.empty:
            st.error("❌ Error al calcular indicadores técnicos")
            return

        # Obtener señal según estrategia
        if strategy_mode == 'Larry Williams':
            signal_data = indicators.get_larry_williams_signal()
            render_larry_williams_card(selected_symbol, signal_data, df_with_indicators)
        else:  # Wyckoff
            signal_data = indicators.get_wyckoff_signal()
            render_wyckoff_card(selected_symbol, signal_data, df_with_indicators)

        # Gráfico interactivo
        render_chart(selected_symbol, df_with_indicators, strategy_mode)

    except Exception as e:
        st.error(f"❌ Error al generar estrategia: {str(e)}")

        with st.expander("🔍 Ver detalles técnicos"):
            st.code(str(e))

        st.info("""
        **¿Qué hacer?**
        - Intenta seleccionar otro símbolo
        - Recarga la página (F5)
        - Verifica que tienes conexión a Internet
        """)


def render_larry_williams_card(symbol: str, signal_data: dict, df: pd.DataFrame):
    """Renderiza la tarjeta específica para Larry Williams con UI mejorada"""

    # Señal principal
    signal = signal_data['signal']
    strength = signal_data['strength']
    current_price = df['Close'].iloc[-1]
    latest = df.iloc[-1]

    # Calcular target (precio objetivo) based on signal
    if signal == 'BUY':
        target_price = current_price * 1.10  # +10% target
    elif signal == 'SELL':
        target_price = current_price * 0.90  # -10% target
    else:
        target_price = current_price

    # MÉTRICAS PRINCIPALES (Precio, Target, Confianza)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="💰 Precio Actual",
            value=f"${current_price:.2f}",
            delta=None
        )

    with col2:
        delta_target = ((target_price - current_price) / current_price) * 100
        st.metric(
            label="🎯 Target",
            value=f"${target_price:.2f}",
            delta=f"{delta_target:+.1f}%"
        )

    with col3:
        st.metric(
            label="📊 Confianza",
            value=f"{strength}%",
            delta=None
        )

    st.markdown("---")

    # ALERTA DE ACCIÓN CLARA
    if signal == 'BUY':
        strike_5pct = current_price * 1.05
        st.success(f"""
        ### 🟢 ACCIÓN: COMPRAR CALL STRIKE ${strike_5pct:.2f}
        **Estrategia:** Long Call (Cuenta Cash)
        **Razón:** {signal_data['suggested_strategy']}
        """)

        # Strikes recomendados
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📞 Strike Conservador (+5%)", f"${strike_5pct:.2f}")
        with col2:
            st.metric("📞 Strike Agresivo (+10%)", f"${current_price * 1.10:.2f}")

    elif signal == 'SELL':
        st.warning(f"""
        ### 🔴 ACCIÓN: NO COMPRAR / CONSIDERAR VENTA
        **Razón:** {signal_data['suggested_strategy']}
        """)

    else:
        st.info(f"""
        ### 🟡 ACCIÓN: ESPERAR MEJOR PUNTO DE ENTRADA
        **Razón:** {signal_data['suggested_strategy']}
        """)

    st.markdown("---")

    # CALCULADORA DE GESTIÓN DE RIESGO (Regla 2-10%)
    if signal == 'BUY':
        st.subheader("💰 Gestión de Riesgo (Capital: $1,000)")

        # Estimación de prima (aproximadamente 3-5% del precio de la acción para ATM)
        strike_price = current_price * 1.05  # Strike conservador +5%
        prima_estimada = current_price * 0.04  # 4% del precio de la acción
        costo_contrato = prima_estimada * 100  # 1 contrato = 100 acciones

        # Validación de riesgo
        MAX_PRIMA = 150  # 15% del capital de $1,000

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Costo Estimado (1 contrato)",
                f"${costo_contrato:.2f}",
                help=f"Prima estimada ~${prima_estimada:.2f}/acción × 100"
            )

        with col2:
            stop_loss = costo_contrato * 0.75  # Vender si pierde 25%
            st.metric(
                "Stop Loss (-25%)",
                f"${stop_loss:.2f}",
                delta=f"-${costo_contrato - stop_loss:.2f}",
                delta_color="inverse",
                help="Salir si la opción pierde 25% de su valor"
            )

        with col3:
            take_profit = costo_contrato * 1.50  # Vender si gana 50%
            st.metric(
                "Take Profit (+50%)",
                f"${take_profit:.2f}",
                delta=f"+${take_profit - costo_contrato:.2f}",
                help="Salir si la opción gana 50% de valor"
            )

        # Advertencia de riesgo
        if costo_contrato > MAX_PRIMA:
            st.error(f"""
            ⚠️ **RIESGO ALTO**: El costo estimado (${costo_contrato:.2f}) supera el límite recomendado de ${MAX_PRIMA} (15% del capital).

            **Recomendación**: Considera esperar una mejor oportunidad o usar un strike más alejado (OTM) con prima menor.
            """)
        else:
            st.success(f"""
            ✅ **RIESGO CONTROLADO**: El costo estimado (${costo_contrato:.2f}) está dentro del límite de ${MAX_PRIMA} (15% del capital).

            **Capital restante**: ${1000 - costo_contrato:.2f} disponible para diversificación.
            """)

        st.markdown("---")

    # Explicación del indicador
    with st.expander("📚 ¿Qué es Larry Williams %R?"):
        st.markdown("""
        **Williams %R** mide el momentum del precio en una escala de -100 a 0.

        - **< -80 (Sobreventa)**: El precio está muy bajo, posible rebote alcista 📈
        - **> -20 (Sobrecompra)**: El precio está muy alto, posible corrección bajista 📉

        Las **Medias Móviles** (SMA) muestran la tendencia: cuando el precio cruza sobre las medias, es señal alcista.
        """)

    # Razones del análisis
    st.subheader("📋 Análisis Detallado")
    for reason in signal_data['reasons']:
        st.write(f"• {reason}")

    # Métricas técnicas
    st.subheader("📊 Indicadores Técnicos")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Williams %R",
            f"{signal_data['williams_r']:.2f}",
            help="< -80 = Sobreventa, > -20 = Sobrecompra"
        )

    with col2:
        st.metric(
            "SMA 20",
            f"${latest['sma_20']:.2f}"
        )

    with col3:
        st.metric(
            "SMA 50",
            f"${latest['sma_50']:.2f}"
        )


def render_wyckoff_card(symbol: str, signal_data: dict, df: pd.DataFrame):
    """Renderiza la tarjeta específica para Wyckoff con UI mejorada"""

    signal = signal_data['signal']
    strength = signal_data['strength']
    current_price = df['Close'].iloc[-1]
    latest = df.iloc[-1]

    # Calcular target based on signal
    if signal == 'BUY':
        target_price = current_price * 1.10  # +10% target
    elif signal == 'SELL':
        target_price = current_price * 0.90  # -10% target
    else:
        target_price = current_price

    # MÉTRICAS PRINCIPALES (Precio, Target, Confianza)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="💰 Precio Actual",
            value=f"${current_price:.2f}",
            delta=None
        )

    with col2:
        delta_target = ((target_price - current_price) / current_price) * 100
        st.metric(
            label="🎯 Target",
            value=f"${target_price:.2f}",
            delta=f"{delta_target:+.1f}%"
        )

    with col3:
        st.metric(
            label="📊 Confianza",
            value=f"{strength}%",
            delta=None
        )

    st.markdown("---")

    # ALERTA DE ACCIÓN CLARA
    if signal == 'BUY':
        strike_5pct = current_price * 1.05
        st.success(f"""
        ### 🟢 ACCIÓN: COMPRAR CALL STRIKE ${strike_5pct:.2f}
        **Estrategia:** Long Call (Cuenta Cash)
        **Razón:** {signal_data['suggested_strategy']}
        """)

        # Strikes recomendados
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📞 Strike Conservador (+5%)", f"${strike_5pct:.2f}")
        with col2:
            st.metric("📞 Strike Agresivo (+10%)", f"${current_price * 1.10:.2f}")

    elif signal == 'SELL':
        st.warning(f"""
        ### 🔴 ACCIÓN: NO COMPRAR / CONSIDERAR VENTA
        **Razón:** {signal_data['suggested_strategy']}
        """)

    else:
        st.info(f"""
        ### 🟡 ACCIÓN: ESPERAR MEJOR PUNTO DE ENTRADA
        **Razón:** {signal_data['suggested_strategy']}
        """)

    st.markdown("---")

    # CALCULADORA DE GESTIÓN DE RIESGO (Regla 2-10%)
    if signal == 'BUY':
        st.subheader("💰 Gestión de Riesgo (Capital: $1,000)")

        # Estimación de prima (aproximadamente 3-5% del precio de la acción para ATM)
        strike_price = current_price * 1.05  # Strike conservador +5%
        prima_estimada = current_price * 0.04  # 4% del precio de la acción
        costo_contrato = prima_estimada * 100  # 1 contrato = 100 acciones

        # Validación de riesgo
        MAX_PRIMA = 150  # 15% del capital de $1,000

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Costo Estimado (1 contrato)",
                f"${costo_contrato:.2f}",
                help=f"Prima estimada ~${prima_estimada:.2f}/acción × 100"
            )

        with col2:
            stop_loss = costo_contrato * 0.75  # Vender si pierde 25%
            st.metric(
                "Stop Loss (-25%)",
                f"${stop_loss:.2f}",
                delta=f"-${costo_contrato - stop_loss:.2f}",
                delta_color="inverse",
                help="Salir si la opción pierde 25% de su valor"
            )

        with col3:
            take_profit = costo_contrato * 1.50  # Vender si gana 50%
            st.metric(
                "Take Profit (+50%)",
                f"${take_profit:.2f}",
                delta=f"+${take_profit - costo_contrato:.2f}",
                help="Salir si la opción gana 50% de valor"
            )

        # Advertencia de riesgo
        if costo_contrato > MAX_PRIMA:
            st.error(f"""
            ⚠️ **RIESGO ALTO**: El costo estimado (${costo_contrato:.2f}) supera el límite recomendado de ${MAX_PRIMA} (15% del capital).

            **Recomendación**: Considera esperar una mejor oportunidad o usar un strike más alejado (OTM) con prima menor.
            """)
        else:
            st.success(f"""
            ✅ **RIESGO CONTROLADO**: El costo estimado (${costo_contrato:.2f}) está dentro del límite de ${MAX_PRIMA} (15% del capital).

            **Capital restante**: ${1000 - costo_contrato:.2f} disponible para diversificación.
            """)

        st.markdown("---")

    # Explicación del indicador
    with st.expander("📚 ¿Qué es el Método Wyckoff?"):
        st.markdown("""
        **Wyckoff** analiza el volumen y la posición del cierre para identificar acumulación o distribución.

        - **Alto volumen + cierre arriba (>70%)**: Instituciones acumulando (COMPRA) 🐋📈
        - **Alto volumen + cierre abajo (<30%)**: Instituciones distribuyendo (VENTA) 🐋📉

        Cuando el "dinero inteligente" acumula, el precio tiende a subir. Cuando distribuye, tiende a bajar.
        """)

    # Razones del análisis
    st.subheader("📋 Análisis Detallado")
    for reason in signal_data['reasons']:
        st.write(f"• {reason}")

    # Métricas técnicas
    st.subheader("📊 Métricas Wyckoff")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Volumen Relativo",
            f"{signal_data['volume_relative']:.0f}%",
            help="> 150% = Volumen alto"
        )

    with col2:
        st.metric(
            "Posición Cierre",
            f"{signal_data['close_position']:.0f}%",
            help="> 75% = Zona alta, < 25% = Zona baja"
        )

    # Niveles de soporte/resistencia
    support, resistance = get_support_resistance(df)
    col1, col2 = st.columns(2)

    with col1:
        st.metric("📍 Soporte", f"${support:.2f}")

    with col2:
        st.metric("📍 Resistencia", f"${resistance:.2f}")


def render_chart(symbol: str, df: pd.DataFrame, strategy_mode: str):
    """
    Renderiza gráfico interactivo según estrategia.

    Args:
        symbol: Símbolo del ticker
        df: DataFrame con datos e indicadores
        strategy_mode: 'Larry Williams' o 'Wyckoff'
    """
    st.subheader("📈 Gráfico de Análisis")

    # Crear subplots
    if strategy_mode == 'Larry Williams':
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{symbol} - Precio y Medias Móviles', 'Williams %R')
        )

        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Precio'
            ),
            row=1, col=1
        )

        # Medias móviles
        fig.add_trace(
            go.Scatter(x=df.index, y=df['sma_20'], name='SMA 20', line=dict(color='blue', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['sma_50'], name='SMA 50', line=dict(color='orange', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['sma_200'], name='SMA 200', line=dict(color='red', width=1)),
            row=1, col=1
        )

        # Williams %R
        fig.add_trace(
            go.Scatter(x=df.index, y=df['williams_r'], name='Williams %R', line=dict(color='purple')),
            row=2, col=1
        )

        # Líneas de referencia Williams %R
        fig.add_hline(y=-20, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=-80, line_dash="dash", line_color="green", row=2, col=1)

    else:  # Wyckoff
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{symbol} - Análisis Wyckoff', 'Volumen')
        )

        # Candlestick con colores especiales para volumen alto
        colors = []
        for idx, row in df.iterrows():
            if row.get('high_volume', False):
                if row.get('bullish_strength', False):
                    colors.append('darkgreen')  # Fortaleza alcista
                elif row.get('bearish_weakness', False):
                    colors.append('darkred')  # Debilidad bajista
                else:
                    colors.append('orange')  # Volumen alto sin definición
            else:
                colors.append('lightgray')

        # Velas
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Precio'
            ),
            row=1, col=1
        )

        # Volumen con colores destacados
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volumen',
                marker_color=colors,
                showlegend=True
            ),
            row=2, col=1
        )

        # Línea de volumen promedio
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['volume_avg'],
                name='Vol Promedio',
                line=dict(color='blue', dash='dash')
            ),
            row=2, col=1
        )

        # Línea de 150% volumen
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['volume_avg'] * 1.5,
                name='150% Vol',
                line=dict(color='red', dash='dot')
            ),
            row=2, col=1
        )

    # Layout con tema oscuro y diseño profesional
    fig.update_layout(
        template='plotly_dark',  # Tema oscuro
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        paper_bgcolor='#0E1117',  # Fondo oscuro de Streamlit
        plot_bgcolor='#262730',   # Fondo del gráfico
        font=dict(color='white', size=12),
        title=dict(
            text=f"<b>{symbol}</b> - Análisis {strategy_mode}",
            font=dict(size=20, color='white'),
            x=0.5,
            xanchor='center'
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        # Configurar colores de velas
        xaxis=dict(
            gridcolor='#3E3E3E',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='#3E3E3E',
            showgrid=True
        )
    )

    # Configurar colores de velas (verde/rojo vibrantes)
    fig.update_traces(
        increasing_line_color='#00FF41',  # Verde neón
        decreasing_line_color='#FF073A',  # Rojo vibrante
        increasing_fillcolor='#00FF41',
        decreasing_fillcolor='#FF073A',
        selector=dict(type='candlestick')
    )

    st.plotly_chart(fig, use_container_width=True)


# ========== COLUMNA 3: NOTICIAS ==========

def render_news(geopolitical_mode=True):
    """
    Renderiza la columna de noticias.
    Si geopolitical_mode=True, muestra alertas sobre Venezuela.
    Si geopolitical_mode=False, muestra mensaje de contexto de mercado.
    """
    st.header("📰 Noticias")

    selected_symbol = st.session_state.get('selected_symbol', DEFAULT_WATCHLIST[0])

    # Noticias fallback sobre Venezuela (solo si modo geopolítico activado)
    if geopolitical_mode:
        st.warning("""
        ⚠️ **Alerta Geopolítica**: La captura de Nicolás Maduro genera alta volatilidad.
        Se recomienda monitorear contratos de servicios petroleros (SLB/HAL).
        """)

        fallback_news = [
            {
                'title': '🔴 URGENTE: Captura de Nicolás Maduro sacude mercados energéticos globales',
                'publisher': 'TradeOlympo Alert',
                'time_str': 'Hace 1 hora'
            },
            {
                'title': 'SLB y HAL: Contratos petroleros venezolanos bajo revisión ante cambio político',
                'publisher': 'Energy Markets Today',
                'time_str': 'Hace 3 horas'
            },
            {
                'title': 'Volatilidad extrema en sector energético tras eventos en Venezuela',
                'publisher': 'Bloomberg Energy',
                'time_str': 'Hace 5 horas'
            },
            {
                'title': 'CVX evalúa reapertura de operaciones en Venezuela post-Maduro',
                'publisher': 'Reuters',
                'time_str': 'Hace 8 horas'
            },
            {
                'title': 'Analistas proyectan impacto en precios del crudo ante transición venezolana',
                'publisher': 'Financial Times',
                'time_str': 'Hace 12 horas'
            }
        ]

        st.info("📡 Alertas de mercado:")

        for article in fallback_news:
            with st.container():
                st.markdown(f"**{article['title']}**")
                st.caption(f"📅 {article['time_str']} | 📰 {article['publisher']}")
                st.divider()
    else:
        # Modo universal: mostrar mensaje genérico
        st.info(f"""
        📊 **Analizando**: {selected_symbol}

        Para obtener noticias en tiempo real, activa el **Modo Geopolítico** en el sidebar
        o utiliza fuentes externas como Bloomberg, Reuters o Yahoo Finance.
        """)


# ========== FUNCIÓN PRINCIPAL DEL DASHBOARD ==========

def render_dashboard(strategy_mode: str, custom_ticker: str = "", simulation_mode: bool = False, watchlist_symbols=None, geopolitical_mode=True):
    """
    Renderiza el dashboard completo con las 3 columnas.

    Args:
        strategy_mode: 'Larry Williams' o 'Wyckoff'
        custom_ticker: Ticker personalizado ingresado por el usuario
        simulation_mode: Si True, usa datos sintéticos
        watchlist_symbols: Lista de símbolos para el watchlist
        geopolitical_mode: Si True, muestra alertas sobre Venezuela
    """
    # Inicializar símbolo seleccionado
    if not watchlist_symbols:
        watchlist_symbols = DEFAULT_WATCHLIST

    if 'selected_symbol' not in st.session_state:
        st.session_state['selected_symbol'] = watchlist_symbols[0] if watchlist_symbols else 'CVX'

    # Layout de 3 columnas
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        render_watchlist(watchlist_symbols)

    with col2:
        render_strategy_card(strategy_mode, custom_ticker, simulation_mode)

    with col3:
        render_news(geopolitical_mode)
