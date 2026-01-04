"""
Dashboard View para TradeOlympo
Gestiona la interfaz visual de 3 columnas: Watchlist, Estrategia, Noticias
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from utils.indicators import TechnicalIndicators, get_support_resistance


# ========== CONFIGURACIÓN ==========

WATCHLIST_SYMBOLS = ['CVX', 'SLB', 'HAL', 'XLE']


# ========== COLUMNA 1: WATCHLIST ==========

def render_watchlist():
    """
    Renderiza la columna de Watchlist con resumen de símbolos.
    Muestra precio actual, cambio % y selección de símbolo.
    """
    st.header("📊 Watchlist")

    selected_symbol = st.session_state.get('selected_symbol', WATCHLIST_SYMBOLS[0])

    # Mostrar cada símbolo con métricas básicas
    for symbol in WATCHLIST_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', current_price)

            if prev_close and prev_close != 0:
                change_pct = ((current_price - prev_close) / prev_close) * 100
            else:
                change_pct = 0

            # Botón seleccionable para cada símbolo
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                if st.button(
                    symbol,
                    key=f"btn_{symbol}",
                    use_container_width=True,
                    type="primary" if symbol == selected_symbol else "secondary"
                ):
                    st.session_state['selected_symbol'] = symbol
                    st.rerun()

            with col2:
                st.metric(
                    label="",
                    value=f"${current_price:.2f}",
                    delta=f"{change_pct:+.2f}%"
                )

        except Exception as e:
            st.error(f"Error cargando {symbol}: {str(e)}")

    st.divider()

    # Información adicional del símbolo seleccionado
    if selected_symbol:
        st.subheader(f"Detalles: {selected_symbol}")
        try:
            ticker = yf.Ticker(selected_symbol)
            info = ticker.info

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Volumen", f"{info.get('volume', 0):,}")
                st.metric("Market Cap", f"${info.get('marketCap', 0):,.0f}")

            with col2:
                st.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
                st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")

        except Exception as e:
            st.warning(f"No se pudo cargar información adicional: {str(e)}")


# ========== COLUMNA 2: TARJETA DE ESTRATEGIA DINÁMICA ==========

def render_strategy_card(strategy_mode: str):
    """
    Renderiza la tarjeta de estrategia que cambia dinámicamente
    según el indicador seleccionado.

    Args:
        strategy_mode: 'Larry Williams' o 'Wyckoff'
    """
    st.header("🎯 Estrategia de Trading")

    selected_symbol = st.session_state.get('selected_symbol', WATCHLIST_SYMBOLS[0])

    try:
        # Obtener datos históricos
        ticker = yf.Ticker(selected_symbol)
        df = ticker.history(period='1y')

        if df.empty:
            st.error(f"No se pudieron obtener datos para {selected_symbol}")
            return

        # Calcular indicadores
        indicators = TechnicalIndicators(df)
        df_with_indicators = indicators.calculate_all_indicators()

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
        st.error(f"Error al generar estrategia: {str(e)}")
        st.exception(e)


def render_larry_williams_card(symbol: str, signal_data: dict, df: pd.DataFrame):
    """Renderiza la tarjeta específica para Larry Williams"""

    # Señal principal
    signal = signal_data['signal']
    strength = signal_data['strength']

    # Color según señal
    if signal == 'BUY':
        signal_color = '🟢'
        bg_color = '#d4edda'
    elif signal == 'SELL':
        signal_color = '🔴'
        bg_color = '#f8d7da'
    else:
        signal_color = '🟡'
        bg_color = '#fff3cd'

    st.markdown(f"""
    <div style='background-color: {bg_color}; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h2 style='text-align: center;'>{signal_color} {signal}</h2>
        <p style='text-align: center; font-size: 18px;'>Confianza: {strength}%</p>
    </div>
    """, unsafe_allow_html=True)

    # Estrategia recomendada
    st.subheader("💡 Estrategia Recomendada (Cuenta Cash)")
    st.info(signal_data['suggested_strategy'])

    # Razones
    st.subheader("📋 Análisis")
    for reason in signal_data['reasons']:
        st.write(f"• {reason}")

    # Métricas clave
    st.subheader("📊 Métricas Larry Williams")
    col1, col2, col3 = st.columns(3)

    latest = df.iloc[-1]

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
    """Renderiza la tarjeta específica para Wyckoff"""

    signal = signal_data['signal']
    strength = signal_data['strength']

    # Color según señal
    if signal == 'BUY':
        signal_color = '🟢'
        bg_color = '#d4edda'
    elif signal == 'SELL':
        signal_color = '🔴'
        bg_color = '#f8d7da'
    else:
        signal_color = '🟡'
        bg_color = '#fff3cd'

    st.markdown(f"""
    <div style='background-color: {bg_color}; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h2 style='text-align: center;'>{signal_color} {signal}</h2>
        <p style='text-align: center; font-size: 18px;'>Confianza: {strength}%</p>
    </div>
    """, unsafe_allow_html=True)

    # Estrategia recomendada
    st.subheader("💡 Estrategia Recomendada (Cuenta Cash)")
    st.info(signal_data['suggested_strategy'])

    # Razones
    st.subheader("📋 Análisis Wyckoff")
    for reason in signal_data['reasons']:
        st.write(f"• {reason}")

    # Métricas clave
    st.subheader("📊 Métricas Wyckoff")
    col1, col2 = st.columns(2)

    latest = df.iloc[-1]

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
        st.metric("Soporte", f"${support:.2f}")

    with col2:
        st.metric("Resistencia", f"${resistance:.2f}")


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

    # Layout
    fig.update_layout(
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)


# ========== COLUMNA 3: NOTICIAS ==========

def render_news():
    """
    Renderiza la columna de noticias.
    Muestra noticias recientes del símbolo seleccionado.
    """
    st.header("📰 Noticias")

    selected_symbol = st.session_state.get('selected_symbol', WATCHLIST_SYMBOLS[0])

    try:
        ticker = yf.Ticker(selected_symbol)
        news = ticker.news

        if not news:
            st.info("No hay noticias recientes disponibles.")
            return

        # Mostrar hasta 5 noticias
        for article in news[:5]:
            title = article.get('title', 'Sin título')
            publisher = article.get('publisher', 'Desconocido')
            link = article.get('link', '#')
            publish_time = article.get('providerPublishTime', 0)

            # Convertir timestamp
            if publish_time:
                pub_date = datetime.fromtimestamp(publish_time)
                time_ago = datetime.now() - pub_date
                if time_ago.days > 0:
                    time_str = f"Hace {time_ago.days} día(s)"
                else:
                    hours = time_ago.seconds // 3600
                    time_str = f"Hace {hours} hora(s)"
            else:
                time_str = "Fecha desconocida"

            # Renderizar noticia
            with st.container():
                st.markdown(f"**[{title}]({link})**")
                st.caption(f"📅 {time_str} | 📰 {publisher}")
                st.divider()

    except Exception as e:
        st.error(f"Error cargando noticias: {str(e)}")


# ========== FUNCIÓN PRINCIPAL DEL DASHBOARD ==========

def render_dashboard(strategy_mode: str):
    """
    Renderiza el dashboard completo con las 3 columnas.

    Args:
        strategy_mode: 'Larry Williams' o 'Wyckoff'
    """
    # Inicializar símbolo seleccionado
    if 'selected_symbol' not in st.session_state:
        st.session_state['selected_symbol'] = WATCHLIST_SYMBOLS[0]

    # Layout de 3 columnas
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        render_watchlist()

    with col2:
        render_strategy_card(strategy_mode)

    with col3:
        render_news()
