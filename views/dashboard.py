"""
Dashboard View para TradeOlympo (FIXED)
Soluciona el error de anidamiento de columnas usando HTML para métricas internas.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from utils.indicators import TechnicalIndicators, fetch_stock_data, fetch_stock_data_alphavantage, generate_synthetic_data

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
    if not symbols: symbols = DEFAULT_WATCHLIST
    st.subheader("📊 Watchlist")
    
    current = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)
    
    for symbol in symbols:
        if st.button(symbol, key=f"btn_{symbol}", use_container_width=True, type="primary" if symbol == current else "secondary"):
            st.session_state['selected_symbol'] = symbol
            st.rerun()

# ========== TARJETAS INTERNAS (SIN COLUMNAS) ==========

def render_larry_card_content(symbol, signal_data, df):
    """Renderiza el contenido de Larry Williams sin usar st.columns"""
    latest = df.iloc[-1]
    
    # 1. Señal Visual
    color = "#00FF88" if signal_data['signal'] == 'BUY' else "#FF073A"
    st.markdown(f"""
    <div style="text-align: center; background: {color}20; padding: 10px; border-radius: 10px; border: 1px solid {color}; margin-bottom: 10px;">
        <h3 style="margin:0; color: {color};">{signal_data['signal']} ({signal_data['strength']}%)</h3>
        <p style="margin:0; font-size: 0.8em; color: #ddd;">Larry Williams</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Métricas (HTML stack)
    st.markdown(render_metric_html("Precio", f"${latest['Close']:.2f}", color=color), unsafe_allow_html=True)
    st.markdown(render_metric_html("Williams %R", f"{signal_data['williams_r']:.1f}", color="purple"), unsafe_allow_html=True)
    st.markdown(render_metric_html("Tendencia (SMA)", f"${latest['sma_50']:.2f}", color="orange"), unsafe_allow_html=True)

def render_wyckoff_card_content(symbol, signal_data, df):
    """Renderiza el contenido de Wyckoff sin usar st.columns"""
    latest = df.iloc[-1]
    
    # 1. Señal Visual
    color = "#00FF88" if signal_data['signal'] == 'BUY' else "#FF073A"
    st.markdown(f"""
    <div style="text-align: center; background: {color}20; padding: 10px; border-radius: 10px; border: 1px solid {color}; margin-bottom: 10px;">
        <h3 style="margin:0; color: {color};">{signal_data['signal']} ({signal_data['strength']}%)</h3>
        <p style="margin:0; font-size: 0.8em; color: #ddd;">Wyckoff (Volumen)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Métricas (HTML stack)
    st.markdown(render_metric_html("Volumen Relativo", f"{signal_data['volume_relative']:.0f}%", color=color), unsafe_allow_html=True)
    st.markdown(render_metric_html("Posición Cierre", f"{signal_data['close_position']:.0f}%", color="blue"), unsafe_allow_html=True)
    st.markdown(render_metric_html("Esfuerzo/Res", "Anomalía" if latest['effort_result_anomaly'] else "Normal", color="yellow"), unsafe_allow_html=True)

# ========== ESTRATEGIA PRINCIPAL (VISIÓN DOBLE) ==========

def render_strategy_section(custom_ticker, simulation_mode, api_key):
    # Determinar símbolo
    if custom_ticker:
        symbol = custom_ticker.upper()
        st.session_state['selected_symbol'] = symbol
    else:
        symbol = st.session_state.get('selected_symbol', FALLBACK_SYMBOL)

    st.header(f"🔭 Análisis: {symbol}")

    # Obtener Datos
    try:
        if simulation_mode:
            df = generate_synthetic_data(symbol)
        elif api_key:
            df = fetch_stock_data_alphavantage(symbol, api_key)
        else:
            df = fetch_stock_data(symbol)
            
        if df is None or df.empty or len(df) < 20:
            st.error("❌ Datos insuficientes o error de API")
            return

        # Cálculos
        indicators = TechnicalIndicators(df)
        df = indicators.calculate_all_indicators()
        
        lw_data = indicators.get_larry_williams_signal()
        wy_data = indicators.get_wyckoff_signal()
        
        # --- TARJETA DE STRIKE (CALL TO ACTION) ---
        # Solo si al menos una es BUY fuerte
        is_buy = (lw_data['signal'] == 'BUY' and lw_data['strength'] > 50) or \
                 (wy_data['signal'] == 'BUY' and wy_data['strength'] > 50)
                 
        if is_buy:
            price = df['Close'].iloc[-1]
            strike_raw = price * 1.05
            # Redondeo inteligente para opciones
            if strike_raw < 10: strike = round(strike_raw, 1)
            elif strike_raw < 100: strike = round(strike_raw * 2) / 2
            else: strike = round(strike_raw)
            
            st.markdown(f"""
            <div style="background: linear-gradient(45deg, #006400, #00FF88); padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,255,136,0.2);">
                <h2 style="margin:0; color: white; text-align: center;">🎯 STRIKE SUGERIDO: Call ${strike}</h2>
                <p style="margin:0; color: #e0e0e0; text-align: center;">Vencimiento: 30-45 días | Precio Actual: ${price:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        # --- VISIÓN DOBLE (AQUÍ USAMOS COLUMNAS NIVEL 2 PERMITIDAS) ---
        c_larry, c_wyckoff = st.columns(2)
        
        with c_larry:
            st.subheader("📊 Larry Williams")
            render_larry_card_content(symbol, lw_data, df)
            
        with c_wyckoff:
            st.subheader("🐋 Wyckoff")
            render_wyckoff_card_content(symbol, wy_data, df)

        st.markdown("---")
        
        # Gráfico Unificado
        render_chart(symbol, df)

    except Exception as e:
        st.error(f"Error en análisis: {str(e)}")

def render_chart(symbol, df):
    # Gráfico simple para no saturar
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#303030'), row=2, col=1)
    
    fig.update_layout(template='plotly_dark', height=500, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ========== NOTICIAS ==========

def render_news(geopolitical_mode):
    st.subheader("📰 Noticias")
    if geopolitical_mode:
        st.warning("🇻🇪 Modo Crisis Venezuela Activo")
        st.markdown("**Alertas:**\n- Monitoreo de sanciones\n- Volatilidad en Petróleo (XLE)")
    else:
        st.info("🌐 Modo Universal")
        st.markdown("- Noticias corporativas\n- Reportes de ganancias")

# ========== DASHBOARD PRINCIPAL ==========

def render_dashboard(strategy_mode, custom_ticker, simulation_mode, api_key, watchlist_symbols=None, geopolitical_mode=True):
    # Layout Principal: Watchlist (Sidebar es mejor, pero mantendremos columna pequeña) | Estrategia (Ancha) | Noticias
    
    # TRUCO PARA EVITAR ERROR:
    # No usaremos columnas para TODO el dashboard, porque anidaremos columnas dentro de la estrategia.
    # Usaremos un layout 2 columnas: Estrategia (Grande) | Noticias (Pequeña). 
    # La Watchlist la dejamos solo visualmente compacta o confiamos en el sidebar.
    
    # Si quieres mantener 3 columnas visuales:
    c_list, c_main, c_news = st.columns([1, 3, 1])
    
    with c_list:
        render_watchlist(watchlist_symbols)
        
    with c_main:
        # Aquí dentro crearemos columnas para Larry/Wyckoff.
        # Streamlit permite: Main -> Columna -> Columna.
        # NO permite: Main -> Columna -> Columna -> Columna.
        # Como render_larry_card_content YA NO USA columnas, estamos a salvo.
        render_strategy_section(custom_ticker, simulation_mode, api_key)
        
    with c_news:
        render_news(geopolitical_mode)
