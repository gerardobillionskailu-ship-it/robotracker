"""
Dashboard View para TradeOlympo - Mobile-First Premium UI
Diseño tipo App Financiera de Alta Gama
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

# ========== SELECTOR DE TICKER COMPACTO ==========

def render_ticker_selector(symbols):
    """Renderiza selector de ticker horizontal tipo pills"""
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    current = st.session_state.get('selected_symbol', symbols[0] if symbols else FALLBACK_SYMBOL)

    # Pills horizontales
    cols = st.columns(len(symbols))
    for idx, symbol in enumerate(symbols):
        with cols[idx]:
            is_selected = (symbol == current)
            btn_type = "primary" if is_selected else "secondary"

            if st.button(
                symbol,
                key=f"ticker_pill_{symbol}",
                type=btn_type,
                use_container_width=True
            ):
                st.session_state['selected_symbol'] = symbol
                st.rerun()

    return current

# ========== HEADER HERO ==========

def render_hero_header(symbol: str, current_price: float, prev_close: float):
    """Renderiza header gigante tipo app financiera"""

    price_change = current_price - prev_close
    price_change_pct = (price_change / prev_close) * 100 if prev_close > 0 else 0

    # Color según cambio
    color = "#00FF88" if price_change >= 0 else "#FF073A"
    arrow = "▲" if price_change >= 0 else "▼"

    # Formatear valores
    price_str = f"${current_price:.2f}"
    change_str = f"{arrow} ${abs(price_change):.2f} ({price_change_pct:+.2f}%)"

    # HTML sin indentación para evitar problemas de rendering
    html_content = f"""<div style='background: linear-gradient(135deg, #1A1D24 0%, #262730 100%); padding: 30px 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'><div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;'><div style='flex: 1; min-width: 120px;'><h1 style='margin: 0; font-size: 48px; font-weight: 900; color: #FFFFFF; letter-spacing: 2px;'>{symbol}</h1><p style='margin: 5px 0 0 0; font-size: 14px; color: #888; font-weight: 500;'>Stock Price</p></div><div style='text-align: right; min-width: 150px;'><div style='font-size: 36px; font-weight: 700; color: #FFFFFF; margin-bottom: 5px;'>{price_str}</div><div style='font-size: 18px; font-weight: 600; color: {color};'>{change_str}</div></div></div></div>"""

    st.markdown(html_content, unsafe_allow_html=True)

# ========== PANEL SEMÁFORO (3 JUECES) ==========

def render_semaphore_panel(larry_signal, wyckoff_signal, elite_signal):
    """Panel horizontal compacto con estado de 3 jueces"""

    def get_judge_color(signal, strength):
        if signal == 'BUY' and strength >= 50:
            return "#00FF88", "🟢"
        elif signal == 'SELL':
            return "#FF073A", "🔴"
        else:
            return "#FFA500", "🟡"

    larry_color, larry_icon = get_judge_color(larry_signal['signal'], larry_signal['strength'])
    wyckoff_color, wyckoff_icon = get_judge_color(wyckoff_signal['signal'], wyckoff_signal['strength'])
    elite_color, elite_icon = get_judge_color(elite_signal['signal'], elite_signal['strength'])

    st.markdown("""
    <div style="background: #1A1D24;
                padding: 15px;
                border-radius: 12px;
                margin-bottom: 20px;">
        <h3 style="margin: 0 0 15px 0;
                   font-size: 16px;
                   color: #888;
                   font-weight: 600;">
            📊 PANEL DE JUECES
        </h3>
    """, unsafe_allow_html=True)

    # Barra de estado horizontal
    cols = st.columns(3)

    judges = [
        ("Larry Williams", larry_icon, larry_color, larry_signal),
        ("Wyckoff", wyckoff_icon, wyckoff_color, wyckoff_signal),
        ("Élite", elite_icon, elite_color, elite_signal)
    ]

    for idx, (name, icon, color, signal) in enumerate(judges):
        with cols[idx]:
            st.markdown(f"""
            <div style="background: {color}20;
                        border: 2px solid {color};
                        border-radius: 8px;
                        padding: 12px 8px;
                        text-align: center;">
                <div style="font-size: 24px; margin-bottom: 5px;">
                    {icon}
                </div>
                <div style="font-size: 12px;
                            font-weight: 700;
                            color: #FFF;
                            margin-bottom: 3px;">
                    {name}
                </div>
                <div style="font-size: 14px;
                            font-weight: 600;
                            color: {color};">
                    {signal['signal']} {signal['strength']}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ========== TARJETA DE EJECUCIÓN ==========

def render_action_card(strike: float, current_price: float, elite_buy: bool = False):
    """Tarjeta de ejecución con Strike, Stop Loss y Take Profit"""

    # Cálculos para opciones
    option_premium_estimate = strike * 0.05  # Estimado 5% del strike
    stop_loss_price = option_premium_estimate * 0.75  # -25%
    take_profit_price = option_premium_estimate * 1.40  # +40%

    banner_color = "#FFD700" if elite_buy else "#00FF88"
    gradient = f"linear-gradient(135deg, {banner_color} 0%, {'#FFA500' if elite_buy else '#00D975'} 100%)"
    title = "🏆 SEÑAL ÉLITE DETECTADA" if elite_buy else "🎯 SEÑAL DE COMPRA"

    st.markdown(f"""
    <div style="background: {gradient};
                padding: 25px 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 6px 20px rgba({'255,215,0' if elite_buy else '0,255,136'},0.4);">

        <h2 style="margin: 0 0 20px 0;
                   font-size: 24px;
                   font-weight: 800;
                   color: #000;
                   text-align: center;">
            {title}
        </h2>

        <!-- Entrada -->
        <div style="background: rgba(0,0,0,0.15);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 12px;">
            <div style="font-size: 13px;
                        font-weight: 600;
                        color: #000;
                        opacity: 0.8;
                        margin-bottom: 5px;">
                🎯 ENTRADA
            </div>
            <div style="font-size: 28px;
                        font-weight: 900;
                        color: #000;">
                Call ${strike:.2f}
            </div>
            <div style="font-size: 12px;
                        color: #000;
                        opacity: 0.7;
                        margin-top: 3px;">
                Vencimiento: 30-45 días | Precio actual: ${current_price:.2f}
            </div>
        </div>

        <!-- Stop Loss y Take Profit -->
        <div style="display: flex;
                    gap: 10px;
                    flex-wrap: wrap;">

            <!-- Stop Loss -->
            <div style="flex: 1;
                        min-width: 140px;
                        background: rgba(255,7,58,0.2);
                        border: 2px solid #FF073A;
                        padding: 12px;
                        border-radius: 8px;">
                <div style="font-size: 11px;
                            font-weight: 700;
                            color: #000;
                            margin-bottom: 5px;">
                    🛑 STOP LOSS
                </div>
                <div style="font-size: 20px;
                            font-weight: 800;
                            color: #FF073A;">
                    ${stop_loss_price:.2f}
                </div>
                <div style="font-size: 10px;
                            color: #000;
                            opacity: 0.7;">
                    -25% del premium
                </div>
            </div>

            <!-- Take Profit -->
            <div style="flex: 1;
                        min-width: 140px;
                        background: rgba(0,255,136,0.2);
                        border: 2px solid #00FF88;
                        padding: 12px;
                        border-radius: 8px;">
                <div style="font-size: 11px;
                            font-weight: 700;
                            color: #000;
                            margin-bottom: 5px;">
                    💰 TAKE PROFIT
                </div>
                <div style="font-size: 20px;
                            font-weight: 800;
                            color: #00D975;">
                    ${take_profit_price:.2f}
                </div>
                <div style="font-size: 10px;
                            color: #000;
                            opacity: 0.7;">
                    +40% del premium
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

# ========== DETALLES TÉCNICOS (EXPANDER) ==========

def render_technical_details(symbol, larry_signal, wyckoff_signal, elite_signal, df):
    """Expander con análisis detallado de las 3 estrategias"""

    with st.expander("🔍 Ver Análisis Detallado y Gráficos", expanded=False):
        st.markdown("### 📊 Análisis de las 3 Estrategias")

        # Tabs para cada estrategia
        tab1, tab2, tab3 = st.tabs(["📊 Larry Williams", "🐋 Wyckoff", "🏆 Estrategia Élite"])

        with tab1:
            st.subheader("Larry Williams")
            latest = df.iloc[-1]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Williams %R", f"{larry_signal['williams_r']:.1f}")
            with col2:
                st.metric("SMA 50", f"${latest['sma_50']:.2f}")
            with col3:
                st.metric("Fuerza", f"{larry_signal['strength']}%")

            st.caption(f"**Estrategia**: {larry_signal['suggested_strategy']}")

            if larry_signal['reasons']:
                st.markdown("**Razones:**")
                for reason in larry_signal['reasons']:
                    st.markdown(f"- {reason}")

        with tab2:
            st.subheader("Wyckoff (Análisis de Volumen)")
            latest = df.iloc[-1]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vol. Relativo", f"{wyckoff_signal['volume_relative']:.0f}%")
            with col2:
                st.metric("Pos. Cierre", f"{wyckoff_signal['close_position']:.0f}%")
            with col3:
                st.metric("Fuerza", f"{wyckoff_signal['strength']}%")

            st.caption(f"**Estrategia**: {wyckoff_signal['suggested_strategy']}")

            if wyckoff_signal['reasons']:
                st.markdown("**Razones:**")
                for reason in wyckoff_signal['reasons']:
                    st.markdown(f"- {reason}")

        with tab3:
            st.subheader("🏆 Estrategia Élite (Squeeze + VWAP + RSI)")
            latest = df.iloc[-1]

            col1, col2, col3 = st.columns(3)
            with col1:
                squeeze_status = "🔥 Firing" if elite_signal['squeeze_on'] else "💤 Quiet"
                st.metric("TTM Squeeze", squeeze_status)
            with col2:
                vwap_diff = ((latest['Close'] - elite_signal['vwap_val']) / elite_signal['vwap_val']) * 100
                st.metric("vs VWAP", f"{vwap_diff:+.2f}%")
            with col3:
                st.metric("RSI", f"{elite_signal['rsi_val']:.1f}")

            st.metric("Fuerza Total", f"{elite_signal['strength']}%")

            st.caption(f"**Estrategia**: {elite_signal['suggested_strategy']}")

            if elite_signal['reasons']:
                st.markdown("**Razones:**")
                for reason in elite_signal['reasons']:
                    st.markdown(f"- {reason}")

            if elite_signal.get('squeeze_release', False):
                st.success("🚀 **SQUEEZE RELEASE DETECTADO** - Breakout en progreso!")

        st.markdown("---")

        # Gráfico
        st.markdown("### 📈 Gráfico de Análisis Técnico")
        render_chart(symbol, df)

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

    # VWAP si existe
    if 'vwap' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='#FFD700', width=2, dash='dash')), row=1, col=1)

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

# ========== DASHBOARD PRINCIPAL (MOBILE-FIRST) ==========

def render_dashboard(strategy_mode: str, custom_ticker: str = "", simulation_mode: bool = False,
                     api_key: str = "", watchlist_symbols=None, geopolitical_mode=True):
    """
    Dashboard Mobile-First tipo App Financiera Premium.
    Layout: Header Hero → Selector Ticker → Semáforo → Action Card → Detalles
    """

    if not watchlist_symbols or len(watchlist_symbols) == 0:
        watchlist_symbols = DEFAULT_WATCHLIST

    # ========== CSS MOBILE-FIRST ==========
    st.markdown("""
    <style>
    /* Eliminar padding extra en mobile */
    .main {
        padding-top: 0 !important;
    }

    /* Optimización para botones */
    .stButton > button {
        font-weight: 600;
    }

    /* Tabs más compactos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        font-weight: 600;
    }

    /* Fix Plotly */
    .js-plotly-plot, .plotly {
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ========== 1. SELECTOR DE TICKER ==========
    selected_symbol = render_ticker_selector(watchlist_symbols)

    # Si hay custom ticker, usarlo
    if custom_ticker and custom_ticker.strip():
        selected_symbol = custom_ticker.strip().upper()
        st.info(f"📊 Analizando ticker manual: **{selected_symbol}**")

    st.session_state['selected_symbol'] = selected_symbol

    # ========== 2. OBTENER DATOS ==========
    try:
        # Obtención de datos
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
            st.info("💡 Activa 'Modo Simulación' en el sidebar o espera 1 minuto (límite de API)")
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

        # Obtener señales de LAS TRES estrategias
        larry_signal = indicators.get_larry_williams_signal()
        wyckoff_signal = indicators.get_wyckoff_signal()
        elite_signal = indicators.get_elite_signal()

        current_price = df_with_indicators['Close'].iloc[-1]
        prev_close = df_with_indicators['Close'].iloc[-2] if len(df_with_indicators) > 1 else current_price
        strike_ideal = calculate_optimal_strike(current_price)

        # ========== 3. HEADER HERO ==========
        render_hero_header(selected_symbol, current_price, prev_close)

        # ========== 4. PANEL SEMÁFORO ==========
        render_semaphore_panel(larry_signal, wyckoff_signal, elite_signal)

        # ========== 5. TARJETA DE EJECUCIÓN (solo si hay señal de compra) ==========
        show_buy_signal = (
            (larry_signal['signal'] == 'BUY' and larry_signal['strength'] >= 50) or
            (wyckoff_signal['signal'] == 'BUY' and wyckoff_signal['strength'] >= 50) or
            (elite_signal['signal'] == 'BUY' and elite_signal['strength'] >= 50)
        )

        elite_buy = (elite_signal['signal'] == 'BUY' and elite_signal['strength'] >= 50)

        if show_buy_signal:
            render_action_card(strike_ideal, current_price, elite_buy)
        else:
            # Tarjeta HOLD
            max_strength = max(larry_signal['strength'], wyckoff_signal['strength'], elite_signal['strength'])

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%);
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        margin-bottom: 20px;">
                <h2 style="margin: 0;
                           font-size: 24px;
                           font-weight: 800;
                           color: #000;">
                    🟡 ESPERAR / HOLD
                </h2>
                <p style="margin: 10px 0 0 0;
                          font-size: 16px;
                          color: #000;
                          opacity: 0.8;">
                    Sin confluencia de señales de compra
                </p>
                <p style="margin: 5px 0 0 0;
                          font-size: 14px;
                          color: #000;">
                    Confianza máxima: {max_strength}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        # ========== 6. DETALLES TÉCNICOS ==========
        render_technical_details(selected_symbol, larry_signal, wyckoff_signal, elite_signal, df_with_indicators)

    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        with st.expander("🔍 Ver detalles"):
            import traceback
            st.code(traceback.format_exc())
