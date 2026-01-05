"""
Dashboard View para TradeOlympo
Gestiona la interfaz visual de 3 columnas: Watchlist, Estrategia, Noticias
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from utils.indicators import TechnicalIndicators, get_support_resistance, fetch_stock_data, fetch_stock_data_alphavantage, generate_synthetic_data


# ========== CONFIGURACIÓN ==========

DEFAULT_WATCHLIST = ['CVX', 'SLB', 'HAL', 'XLE']
FALLBACK_SYMBOL = "AAPL"  # Símbolo por defecto si no hay selección


# ========== COLUMNA 1: WATCHLIST ==========

def render_watchlist(symbols=None):
    """
    Renderiza la columna de Watchlist con selección de símbolos.
    """
    if not symbols:
        symbols = DEFAULT_WATCHLIST

    st.header("📊 Watchlist")

    # Obtener símbolo actual o usar fallback
    current_symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)
    
    # Validar que el símbolo actual esté en la lista, si no, mantenerlo pero marcarlo
    if current_symbol not in symbols and current_symbol != FALLBACK_SYMBOL:
        pass # Permitir símbolos custom fuera de la lista

    # Mostrar cada símbolo como botón seleccionable
    for symbol in symbols:
        if st.button(
            symbol,
            key=f"btn_{symbol}",
            use_container_width=True,
            type="primary" if symbol == current_symbol else "secondary"
        ):
            st.session_state['selected_symbol'] = symbol
            st.rerun()

    st.divider()

    # Información del símbolo seleccionado
    st.subheader(f"📍 Seleccionado: {current_symbol}")
    st.info("💡 Los precios y métricas se muestran en la **Tarjeta de Estrategia** con datos de Alpha Vantage.")


# ========== COLUMNA 2: TARJETA DE ESTRATEGIA DINÁMICA ==========

def calculate_optimal_strike(current_price: float) -> float:
    """
    Calcula el strike ideal para un Call (ATM +5%).
    Redondea a decimales lógicos según el precio.
    """
    strike = current_price * 1.05

    # Redondeo lógico según magnitud del precio
    if strike < 10:
        return round(strike, 2)  # Ej: $9.47 → $9.47
    elif strike < 100:
        return round(strike * 2) / 2  # Ej: $47.3 → $47.50 (múltiplos de $0.50)
    else:
        return round(strike)  # Ej: $147.8 → $148


def render_dual_strategy_card(custom_ticker: str = "", simulation_mode: bool = False, api_key: str = ""):
    """
    Renderiza VISIÓN DOBLE: Larry Williams y Wyckoff simultáneamente.
    Incluye cálculo de Strike Ideal con tarjeta prominente.
    """
    st.header("🎯 Panel de Control Unificado")

    # Determinar símbolo
    if custom_ticker and custom_ticker.strip():
        selected_symbol = custom_ticker.strip().upper()
        st.info(f"📊 Analizando ticker personalizado: **{selected_symbol}**")
        st.session_state['selected_symbol'] = selected_symbol
    else:
        selected_symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    try:
        # Obtención de datos (manejo seguro de api_key None)
        if simulation_mode:
            st.success("🎮 Usando datos sintéticos - Rally por cambio de régimen")
            df = generate_synthetic_data(selected_symbol, days=500)
        elif api_key and api_key.strip():  # Verificar que api_key no sea None o vacío
            df = fetch_stock_data_alphavantage(selected_symbol, api_key)
        else:
            # Fallback a secrets
            df = fetch_stock_data(selected_symbol, period="2y")

        # Validaciones
        if df is None or df.empty or len(df) < 20:
            st.error(f"❌ No se pudieron obtener suficientes datos para {selected_symbol}")
            st.info("""
            **Posibles causas:**
            - El símbolo no existe o está mal escrito
            - Límite de API Alpha Vantage alcanzado (espera 1 min)
            - Problemas de conexión

            **Sugerencia:** Activa el 'Modo Simulación' en el sidebar para probar.
            """)
            return

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            st.error("❌ Datos incompletos recibidos de la API")
            return

        # Calcular indicadores
        indicators = TechnicalIndicators(df)
        df_with_indicators = indicators.calculate_all_indicators()

        if df_with_indicators.empty:
            st.error("❌ Error al calcular indicadores técnicos")
            return

        # Obtener señales de AMBAS estrategias
        larry_signal = indicators.get_larry_williams_signal()
        wyckoff_signal = indicators.get_wyckoff_signal()

        current_price = df_with_indicators['Close'].iloc[-1]

        # ========== STRIKE IDEAL (Tarjeta prominente) ==========
        strike_ideal = calculate_optimal_strike(current_price)

        # Determinar si mostrar strike (si AL MENOS una estrategia dice BUY con >50% confianza)
        show_strike = (
            (larry_signal['signal'] == 'BUY' and larry_signal['strength'] >= 50) or
            (wyckoff_signal['signal'] == 'BUY' and wyckoff_signal['strength'] >= 50)
        )

        if show_strike:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #00FF88 0%, #00D975 100%);
                        padding: 25px;
                        border-radius: 12px;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 6px 20px rgba(0,255,136,0.4);
                        border: 2px solid #00FF88;">
                <h2 style="margin:0; color: #000; font-size: 28px; font-weight: bold;">
                    🎯 STRIKE SUGERIDO: Call ${strike_ideal:.2f}
                </h2>
                <p style="margin: 10px 0 0 0; color: #1A1D24; font-size: 16px; font-weight: 600;">
                    📅 Vencimiento recomendado: 30-45 días | 💰 Precio actual: ${current_price:.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ========== VISIÓN DOBLE: Dos columnas ==========
        col_larry, col_wyckoff = st.columns(2)

        with col_larry:
            st.subheader("📊 Larry Williams")
            render_larry_williams_mini(selected_symbol, larry_signal, df_with_indicators)

        with col_wyckoff:
            st.subheader("🐋 Wyckoff")
            render_wyckoff_mini(selected_symbol, wyckoff_signal, df_with_indicators)

        st.markdown("---")

        # ========== GRÁFICO UNIFICADO ==========
        render_chart(selected_symbol, df_with_indicators, "Larry Williams")  # Mostrar Larry por defecto

    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        with st.expander("🔍 Ver detalles técnicos"):
            import traceback
            st.code(traceback.format_exc())


def render_larry_williams_mini(symbol: str, signal_data: dict, df: pd.DataFrame):
    """Versión compacta de Larry Williams para visión doble"""
    signal = signal_data['signal']
    strength = signal_data['strength']
    current_price = df['Close'].iloc[-1]

    # Señal visual
    if signal == 'BUY':
        st.success(f"### 🟢 BUY ({strength}%)")
    elif signal == 'SELL':
        st.error(f"### 🔴 SELL ({strength}%)")
    else:
        st.info(f"### 🟡 HOLD ({strength}%)")

    # Métricas compactas
    col1, col2 = st.columns(2)
    col1.metric("💰 Precio", f"${current_price:.2f}")
    col2.metric("Williams %R", f"{signal_data['williams_r']:.1f}")

    # Razón principal
    st.caption(f"**Razón**: {signal_data['suggested_strategy'][:80]}...")


def render_wyckoff_mini(symbol: str, signal_data: dict, df: pd.DataFrame):
    """Versión compacta de Wyckoff para visión doble"""
    signal = signal_data['signal']
    strength = signal_data['strength']
    current_price = df['Close'].iloc[-1]

    # Señal visual
    if signal == 'BUY':
        st.success(f"### 🐋 ACUMULACIÓN ({strength}%)")
    elif signal == 'SELL':
        st.error(f"### 🐋 DISTRIBUCIÓN ({strength}%)")
    else:
        st.info(f"### 🟡 NEUTRAL ({strength}%)")

    # Métricas compactas
    col1, col2 = st.columns(2)
    col1.metric("💰 Precio", f"${current_price:.2f}")
    col2.metric("Vol. Rel.", f"{signal_data['volume_relative']:.0f}%")

    # Razón principal
    st.caption(f"**Razón**: {signal_data['suggested_strategy'][:80]}...")


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

    # MÉTRICAS PRINCIPALES
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Precio Actual", f"${current_price:.2f}")
    with col2:
        delta_target = ((target_price - current_price) / current_price) * 100
        st.metric("🎯 Target", f"${target_price:.2f}", f"{delta_target:+.1f}%")
    with col3:
        st.metric("📊 Confianza", f"{strength}%")

    st.markdown("---")

    # ALERTA DE ACCIÓN
    if signal == 'BUY':
        strike_5pct = current_price * 1.05
        st.success(f"### 🟢 ACCIÓN: COMPRAR CALL STRIKE ${strike_5pct:.2f}\n**Razón:** {signal_data['suggested_strategy']}")
    elif signal == 'SELL':
        st.warning(f"### 🔴 ACCIÓN: CONSIDERAR VENTA\n**Razón:** {signal_data['suggested_strategy']}")
    else:
        st.info(f"### 🟡 ACCIÓN: ESPERAR\n**Razón:** {signal_data['suggested_strategy']}")

    st.markdown("---")

    # CALCULADORA DE GESTIÓN DE RIESGO (Solo si es BUY)
    if signal == 'BUY':
        st.subheader("💰 Gestión de Riesgo (Capital: $1,000)")
        
        # Cálculos
        prima_estimada = current_price * 0.04  # Est. 4% del precio
        costo_contrato = prima_estimada * 100
        MAX_PRIMA = 150 # 15% del capital

        c1, c2, c3 = st.columns(3)
        c1.metric("Costo (1 contrato)", f"${costo_contrato:.2f}")
        
        stop_loss = costo_contrato * 0.75
        c2.metric("Stop Loss (-25%)", f"${stop_loss:.2f}", f"-${costo_contrato - stop_loss:.2f}", delta_color="inverse")
        
        take_profit = costo_contrato * 1.50
        c3.metric("Take Profit (+50%)", f"${take_profit:.2f}", f"+${take_profit - costo_contrato:.2f}")

        if costo_contrato > MAX_PRIMA:
            st.error(f"⚠️ **RIESGO ALTO**: ${costo_contrato:.2f} supera el 15% sugerido.")
        else:
            st.success(f"✅ **RIESGO CONTROLADO**: ${costo_contrato:.2f} es seguro para tu cuenta.")

    st.markdown("---")
    
    # Métricas Técnicas
    st.subheader("📊 Indicadores Técnicos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Williams %R", f"{signal_data['williams_r']:.2f}")
    c2.metric("SMA 20", f"${latest['sma_20']:.2f}")
    c3.metric("SMA 50", f"${latest['sma_50']:.2f}")
    
    st.caption("Razones: " + ", ".join(signal_data['reasons']))


def render_wyckoff_card(symbol: str, signal_data: dict, df: pd.DataFrame):
    """Renderiza la tarjeta específica para Wyckoff"""
    
    signal = signal_data['signal']
    strength = signal_data['strength']
    current_price = df['Close'].iloc[-1]

    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Precio", f"${current_price:.2f}")
    c2.metric("📊 Confianza", f"{strength}%")
    c3.metric("📈 Volumen Rel.", f"{signal_data['volume_relative']:.0f}%")

    st.markdown("---")

    if signal == 'BUY':
        st.success(f"### 🟢 ACUMULACIÓN DETECTADA (BUY)\n{signal_data['suggested_strategy']}")
    elif signal == 'SELL':
        st.warning(f"### 🔴 DISTRIBUCIÓN DETECTADA (SELL)\n{signal_data['suggested_strategy']}")
    else:
        st.info("### 🟡 RANGO/NEUTRAL")

    st.caption("Razones: " + ", ".join(signal_data['reasons']))


def render_chart(symbol: str, df: pd.DataFrame, strategy_mode: str):
    """Renderiza gráfico interactivo con tema oscuro profesional"""
    
    st.subheader("📈 Gráfico de Análisis")

    if strategy_mode == 'Larry Williams':
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3],
                            subplot_titles=(f'{symbol} - Precio', 'Williams %R'))
        
        # Precio
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
        
        # SMAs
        fig.add_trace(go.Scatter(x=df.index, y=df['sma_20'], name='SMA 20', line=dict(color='#00D9FF', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['sma_50'], name='SMA 50', line=dict(color='#FFB800', width=1)), row=1, col=1)
        
        # Williams %R
        fig.add_trace(go.Scatter(x=df.index, y=df['williams_r'], name='Williams %R', line=dict(color='purple')), row=2, col=1)
        fig.add_hline(y=-20, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=-80, line_dash="dash", line_color="green", row=2, col=1)

    else: # Wyckoff
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3],
                            subplot_titles=(f'{symbol} - Wyckoff', 'Volumen'))
        
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
        
        # Color volumen
        colors = ['#00FF88' if row['Close'] >= row['Open'] else '#FF073A' for index, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color=colors), row=2, col=1)

    # Configuración Tema Oscuro (Terminal)
    fig.update_layout(
        template='plotly_dark',
        height=600,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#1A1D24',
        font=dict(family='Courier New, monospace', size=12, color='#E0E0E0'),
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


# ========== COLUMNA 3: NOTICIAS ==========

def render_news(geopolitical_mode=True):
    """
    Renderiza noticias. Si geopolitical_mode es False, muestra noticias del ticker seleccionado.
    """
    st.header("📰 Noticias")

    selected_symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    if geopolitical_mode:
        st.warning(f"⚠️ **Modo Geopolítico**: Monitoreando impacto en {selected_symbol} y sector energético.")
        st.info("📡 **Alertas de Mercado (Venezuela/Energía):**")
        
        # Noticias estáticas de ejemplo (en producción se conectarían a una API de noticias real)
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
        st.caption("Modo Geopolítico desactivado. Mostrando noticias del ticker.")
        
        # Simulación de noticias corporativas genéricas
        st.markdown(f"**Resultados Trimestrales de {selected_symbol}**")
        st.caption("Hace 2 días | Finance Daily")
        st.divider()
        st.markdown(f"**Análisis Técnico: {selected_symbol} rompe resistencia**")
        st.caption("Hace 4 horas | Market Watch")


# ========== SECCIÓN DE ACCIÓN RÁPIDA (MOBILE FIRST) ==========

def render_quick_action(strategy_mode: str, custom_ticker: str = "", simulation_mode: bool = False, api_key: str = ""):
    """
    Renderiza banner de acción rápida si hay señal fuerte.
    """
    # Determinar símbolo
    if custom_ticker:
        symbol = custom_ticker
    else:
        symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)
        
    # Obtener datos (lógica simplificada para banner)
    try:
        if simulation_mode:
            df = generate_synthetic_data(symbol)
        elif api_key:
            df = fetch_stock_data_alphavantage(symbol, api_key)
        else:
            df = fetch_stock_data(symbol)
            
        if df is None or df.empty or len(df) < 20: return

        indicators = TechnicalIndicators(df)
        df = indicators.calculate_all_indicators()
        
        if strategy_mode == 'Larry Williams':
            signal_data = indicators.get_larry_williams_signal()
        else:
            signal_data = indicators.get_wyckoff_signal()
            
        # Mostrar solo si es COMPRA FUERTE (>60%)
        if signal_data['signal'] == 'BUY' and signal_data['strength'] >= 60:
            st.markdown(f"""
            <div style="background: linear-gradient(45deg, #00FF88, #00D975); padding: 20px; border-radius: 10px; color: black; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,255,136,0.3);">
                <h2 style="margin:0; font-size: 24px;">🚀 SEÑAL: COMPRA FUERTE ({symbol})</h2>
                <p style="margin:5px; font-weight: bold;">Confianza: {signal_data['strength']}% | Estrategia: {strategy_mode}</p>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception:
        pass


# ========== FUNCIÓN PRINCIPAL DEL DASHBOARD ==========

def render_dashboard(strategy_mode: str, custom_ticker: str = "", simulation_mode: bool = False, api_key: str = "", watchlist_symbols=None, geopolitical_mode=True):
    """
    Orquestador principal del dashboard. Recibe TODOS los parámetros de app.py.
    NOTA: strategy_mode se ignora ahora - siempre mostramos VISIÓN DOBLE.
    """

    # Sincronizar watchlist
    if not watchlist_symbols:
        watchlist_symbols = DEFAULT_WATCHLIST

    # Acción Rápida (Mobile) - manejo seguro de api_key None
    api_key_safe = api_key if api_key else ""
    render_quick_action(strategy_mode, custom_ticker, simulation_mode, api_key_safe)

    # Layout de 3 columnas
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        render_watchlist(watchlist_symbols)

    with col2:
        # VISIÓN DOBLE: Siempre mostramos Larry Williams y Wyckoff juntos
        render_dual_strategy_card(custom_ticker, simulation_mode, api_key_safe)

    with col3:
        render_news(geopolitical_mode)