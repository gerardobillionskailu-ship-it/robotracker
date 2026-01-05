"""
Dashboard View para TradeOlympo
Mobile-First UI con fix de nesting columns usando HTML
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from utils.indicators import TechnicalIndicators, get_support_resistance, fetch_stock_data, fetch_stock_data_alphavantage, generate_synthetic_data

# ========== CONFIGURACIÓN ==========

DEFAULT_WATCHLIST = ['CVX', 'SLB', 'HAL', 'XLE']
FALLBACK_SYMBOL = "AAPL"

# ========== COMPONENTES UI (HTML/CSS) ==========

def render_metric_html(label, value, delta=None, color="white"):
    """Renderiza una métrica usando HTML para evitar nesting de columnas."""
    delta_html = ""
    if delta:
        delta_color = "#00FF88" if "+" in delta else "#FF073A"
        delta_html = f"<span style='color: {delta_color}; font-size: 0.8em; margin-left: 5px;'>{delta}</span>"

    return f"""
    <div style="background-color: #262730; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 3px solid {color};">
        <div style="color: #AAAAAA; font-size: 0.8em;">{label}</div>
        <div style="color: white; font-size: 1.1em; font-weight: bold;">{value} {delta_html}</div>
    </div>
    """

# ========== COLUMNA 1: WATCHLIST ==========

def render_watchlist(symbols=None):
    """Renderiza watchlist compacta"""
    if not symbols:
        symbols = DEFAULT_WATCHLIST

    st.subheader("📊 Watchlist")
    current = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    for symbol in symbols:
        if st.button(symbol, key=f"btn_{symbol}", use_container_width=True,
                    type="primary" if symbol == current else "secondary"):
            st.session_state['selected_symbol'] = symbol
            st.rerun()

# ========== TARJETAS INTERNAS (SIN ST.COLUMNS - USA HTML) ==========

def render_larry_card_content(symbol, signal_data, df):
    """Renderiza el contenido de Larry Williams sin usar st.columns (evita nesting)"""
    latest = df.iloc[-1]

    # 1. Señal Visual
    color = "#00FF88" if signal_data['signal'] == 'BUY' else "#FF073A" if signal_data['signal'] == 'SELL' else "#FFA500"
    st.markdown(f"""
    <div style="text-align: center; background: {color}20; padding: 10px; border-radius: 10px; border: 1px solid {color}; margin-bottom: 10px;">
        <h3 style="margin:0; color: {color};">{signal_data['signal']} ({signal_data['strength']}%)</h3>
        <p style="margin:0; font-size: 0.8em; color: #ddd;">Larry Williams</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Métricas (HTML stack - NO st.columns)
    st.markdown(render_metric_html("💰 Precio", f"${latest['Close']:.2f}", color=color), unsafe_allow_html=True)
    st.markdown(render_metric_html("Williams %R", f"{signal_data['williams_r']:.1f}", color="purple"), unsafe_allow_html=True)
    st.markdown(render_metric_html("SMA 50", f"${latest['sma_50']:.2f}", color="orange"), unsafe_allow_html=True)

    # 3. Razón principal
    st.caption(f"**Razón**: {signal_data['suggested_strategy'][:100]}...")

def render_wyckoff_card_content(symbol, signal_data, df):
    """Renderiza el contenido de Wyckoff sin usar st.columns (evita nesting)"""
    latest = df.iloc[-1]

    # 1. Señal Visual
    color = "#00FF88" if signal_data['signal'] == 'BUY' else "#FF073A" if signal_data['signal'] == 'SELL' else "#FFA500"
    st.markdown(f"""
    <div style="text-align: center; background: {color}20; padding: 10px; border-radius: 10px; border: 1px solid {color}; margin-bottom: 10px;">
        <h3 style="margin:0; color: {color};">{signal_data['signal']} ({signal_data['strength']}%)</h3>
        <p style="margin:0; font-size: 0.8em; color: #ddd;">Wyckoff (Volumen)</p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Métricas (HTML stack - NO st.columns)
    st.markdown(render_metric_html("💰 Precio", f"${latest['Close']:.2f}", color=color), unsafe_allow_html=True)
    st.markdown(render_metric_html("Vol. Relativo", f"{signal_data['volume_relative']:.0f}%", color="blue"), unsafe_allow_html=True)
    st.markdown(render_metric_html("Pos. Cierre", f"{signal_data['close_position']:.0f}%", color="yellow"), unsafe_allow_html=True)

    # 3. Razón principal
    st.caption(f"**Razón**: {signal_data['suggested_strategy'][:100]}...")

# ========== STRIKE CALCULATOR ==========

def calculate_optimal_strike(current_price: float) -> float:
    """Calcula el strike ideal para un Call (ATM +5%) con redondeo inteligente"""
    strike = current_price * 1.05

    if strike < 10:
        return round(strike, 2)
    elif strike < 100:
        return round(strike * 2) / 2  # Múltiplos de $0.50
    else:
        return round(strike)

# ========== ESTRATEGIA PRINCIPAL (MOBILE-FIRST) ==========

def render_dual_strategy_card(custom_ticker: str = "", simulation_mode: bool = False, api_key: str = ""):
    """
    Renderiza VISIÓN DOBLE con Mobile-First UI.
    TARJETA PROMINENTE arriba, detalles en expander.
    """
    st.header("🎯 Panel de Control Unificado")

    # Determinar símbolo
    if custom_ticker and custom_ticker.strip():
        selected_symbol = custom_ticker.strip().upper()
        st.info(f"📊 Analizando: **{selected_symbol}**")
        st.session_state['selected_symbol'] = selected_symbol
    else:
        selected_symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    try:
        # Obtención de datos (manejo seguro de api_key)
        if simulation_mode:
            st.success("🎮 Usando datos sintéticos")
            df = generate_synthetic_data(selected_symbol, days=500)
        elif api_key and api_key.strip():
            df = fetch_stock_data_alphavantage(selected_symbol, api_key)
        else:
            df = fetch_stock_data(selected_symbol, period="2y")

        # Validaciones
        if df is None or df.empty or len(df) < 20:
            st.error(f"❌ Datos insuficientes para {selected_symbol}")
            st.info("💡 Activa 'Modo Simulación' o espera 1 minuto (límite de API)")
            return

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            st.error("❌ Datos incompletos de la API")
            return

        # Calcular indicadores
        indicators = TechnicalIndicators(df)
        df_with_indicators = indicators.calculate_all_indicators()

        if df_with_indicators.empty:
            st.error("❌ Error al calcular indicadores")
            return

        # Obtener señales de AMBAS estrategias
        larry_signal = indicators.get_larry_williams_signal()
        wyckoff_signal = indicators.get_wyckoff_signal()

        current_price = df_with_indicators['Close'].iloc[-1]
        strike_ideal = calculate_optimal_strike(current_price)

        # ========== TARJETA PROMINENTE (MOBILE-FIRST) ==========

        show_buy_signal = (
            (larry_signal['signal'] == 'BUY' and larry_signal['strength'] >= 50) or
            (wyckoff_signal['signal'] == 'BUY' and wyckoff_signal['strength'] >= 50)
        )

        if show_buy_signal:
            # ✅ TARJETA VERDE: COMPRA
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #00FF88 0%, #00D975 100%);
                        padding: 30px;
                        border-radius: 15px;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 8px 25px rgba(0,255,136,0.5);
                        border: 3px solid #00FF88;">
                <h1 style="margin:0; color: #000; font-size: 32px; font-weight: bold;">
                    🎯 STRIKE SUGERIDO: Call ${strike_ideal:.2f}
                </h1>
                <p style="margin: 15px 0 0 0; color: #1A1D24; font-size: 18px; font-weight: 600;">
                    📅 Vencimiento: 30-45 días | 💰 Precio actual: ${current_price:.2f}
                </p>
                <p style="margin: 10px 0 0 0; color: #000; font-size: 16px;">
                    💪 Confianza: Larry {larry_signal['strength']}% | Wyckoff {wyckoff_signal['strength']}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        else:
            # ⚠️ TARJETA AMARILLA: ESPERAR
            if larry_signal['strength'] > wyckoff_signal['strength']:
                main_reason = larry_signal['suggested_strategy']
                confidence = larry_signal['strength']
            else:
                main_reason = wyckoff_signal['suggested_strategy']
                confidence = wyckoff_signal['strength']

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%);
                        padding: 25px;
                        border-radius: 15px;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 6px 20px rgba(255,165,0,0.4);
                        border: 2px solid #FFA500;">
                <h2 style="margin:0; color: #000; font-size: 28px; font-weight: bold;">
                    🟡 ESTADO: ESPERAR / HOLD
                </h2>
                <p style="margin: 15px 0 0 0; color: #1A1D24; font-size: 16px; font-weight: 600;">
                    💰 Precio actual: ${current_price:.2f}
                </p>
                <p style="margin: 10px 0 0 0; color: #000; font-size: 14px; max-width: 600px; margin-left: auto; margin-right: auto;">
                    {main_reason[:120]}...
                </p>
                <p style="margin: 10px 0 0 0; color: #000; font-size: 14px;">
                    📊 Confianza máxima: {confidence}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ========== DETALLES TÉCNICOS (EXPANDER - OCULTO) ==========
        with st.expander("🔍 Ver Detalles Técnicos y Gráficos", expanded=False):
            st.markdown("### 📊 Análisis Dual: Larry Williams vs Wyckoff")

            # VISIÓN DOBLE (usando st.columns aquí es SEGURO porque estamos en nivel 2)
            col_larry, col_wyckoff = st.columns(2)

            with col_larry:
                st.subheader("📊 Larry Williams")
                render_larry_card_content(selected_symbol, larry_signal, df_with_indicators)

            with col_wyckoff:
                st.subheader("🐋 Wyckoff")
                render_wyckoff_card_content(selected_symbol, wyckoff_signal, df_with_indicators)

            st.markdown("---")

            # Gráfico
            st.markdown("### 📈 Gráfico de Análisis Técnico")
            render_chart(selected_symbol, df_with_indicators)

    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        with st.expander("🔍 Ver detalles"):
            import traceback
            st.code(traceback.format_exc())

# ========== GRÁFICO ==========

def render_chart(symbol, df):
    """Renderiza gráfico compacto con tema oscuro"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} - Precio', 'Volumen')
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

    # SMAs
    fig.add_trace(go.Scatter(x=df.index, y=df['sma_20'], name='SMA 20', line=dict(color='#00D9FF', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['sma_50'], name='SMA 50', line=dict(color='#FFB800', width=1)), row=1, col=1)

    # Volumen
    colors = ['#00FF88' if row['Close'] >= row['Open'] else '#FF073A' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color=colors), row=2, col=1)

    # Layout tema oscuro
    fig.update_layout(
        template='plotly_dark',
        height=600,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#1A1D24',
        font=dict(family='Courier New, monospace', size=12, color='#E0E0E0'),
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_rangeslider_visible=False,
        showlegend=True
    )

    # Colores de velas
    fig.update_traces(
        increasing_line_color='#00FF41',
        decreasing_line_color='#FF073A',
        increasing_fillcolor='#00FF41',
        decreasing_fillcolor='#FF073A',
        selector=dict(type='candlestick')
    )

    st.plotly_chart(fig, use_container_width=True)

# ========== NOTICIAS ==========

def render_news(geopolitical_mode=True):
    """Renderiza columna de noticias"""
    st.header("📰 Noticias")

    selected_symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    if geopolitical_mode:
        st.warning(f"⚠️ **Modo Geopolítico**: Monitoreando {selected_symbol} y sector energético")
        st.info("📡 **Alertas de Mercado (Venezuela/Energía):**")

        news_items = [
            ("🔴 URGENTE: Volatilidad en sector energético", "Hace 1 hora"),
            ("SLB/HAL: Contratos bajo revisión", "Hace 3 horas"),
            ("CVX evalúa reapertura total", "Hace 5 horas")
        ]

        for title, time in news_items:
            st.markdown(f"**{title}**")
            st.caption(f"📅 {time}")
            st.divider()
    else:
        st.info(f"📊 **Noticias Corporativas: {selected_symbol}**")
        st.caption("Modo Geopolítico desactivado.")

        st.markdown(f"**Resultados Trimestrales de {selected_symbol}**")
        st.caption("Hace 2 días | Finance Daily")
        st.divider()
        st.markdown(f"**Análisis Técnico: {selected_symbol} rompe resistencia**")
        st.caption("Hace 4 horas | Market Watch")

# ========== DASHBOARD PRINCIPAL ==========

def render_dashboard(strategy_mode: str, custom_ticker: str = "", simulation_mode: bool = False,
                     api_key: str = "", watchlist_symbols=None, geopolitical_mode=True):
    """
    Orquestador principal del dashboard.
    NOTA: strategy_mode ignorado - siempre mostramos VISIÓN DOBLE.
    """

    if not watchlist_symbols:
        watchlist_symbols = DEFAULT_WATCHLIST

    # Layout 3 columnas (NIVEL 1 - PERMITIDO)
    # Dentro de columna central usaremos st.columns (NIVEL 2 - PERMITIDO)
    # Pero NO usaremos st.columns dentro de las tarjetas (NIVEL 3 - PROHIBIDO -> por eso usamos HTML)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        render_watchlist(watchlist_symbols)

    with col2:
        # VISIÓN DOBLE con Mobile-First
        api_key_safe = api_key if api_key else ""
        render_dual_strategy_card(custom_ticker, simulation_mode, api_key_safe)

    with col3:
        render_news(geopolitical_mode)
