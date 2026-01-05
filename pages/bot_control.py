"""
TradeOlympo - Sala de Control del Bot
Panel de administración para controlar el bot de trading
"""
import streamlit as st
import json
import os
from datetime import datetime
from utils.market_presets import PRESETS, get_preset_names, get_preset_tickers

st.set_page_config(
    page_title="🤖 Control Room",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== FUNCIONES DE CONFIGURACIÓN ==========

def load_config():
    """Lee la configuración desde trading_config.json"""
    try:
        with open('trading_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Error al leer configuración: {e}")
        return {
            "active_strategy": "elite",
            "watchlist": ["NVDA", "TSLA", "AAPL", "AMD", "MSFT"],
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

def save_config(config):
    """Guarda la configuración en trading_config.json"""
    try:
        config['last_updated'] = datetime.now().isoformat()
        with open('trading_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar configuración: {e}")
        return False

def read_logs(num_lines=50):
    """Lee las últimas N líneas del archivo de logs"""
    try:
        if not os.path.exists('bot_logs.txt'):
            return "📝 No hay logs disponibles aún. El bot creará el archivo cuando se ejecute."

        with open('bot_logs.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Obtener últimas N líneas
            recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines
            return ''.join(recent_lines)
    except Exception as e:
        return f"❌ Error al leer logs: {e}"

# ========== HEADER ==========

st.markdown("""<div style="background: linear-gradient(135deg, #1A1D24 0%, #262730 100%); padding: 30px 20px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);"><h1 style="margin: 0; font-size: 42px; font-weight: 900; color: #FFFFFF; text-align: center;">🤖 SALA DE CONTROL DEL BOT</h1><p style="margin: 10px 0 0 0; font-size: 16px; color: #888; text-align: center; font-weight: 500;">Panel de administración y monitoreo</p></div>""", unsafe_allow_html=True)

# Cargar configuración actual
config = load_config()

# ========== SECCIÓN 1: ESTADO DEL BOT ==========

st.markdown("### 📊 Estado del Bot")

col1, col2, col3 = st.columns(3)

with col1:
    status = config.get('status', 'active')
    status_color = "#00FF88" if status == "active" else "#FF073A"
    status_text = "🟢 ACTIVO" if status == "active" else "🔴 INACTIVO"
    st.markdown(f"""<div style="background: linear-gradient(135deg, #1A1D24 0%, #262730 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid {status_color};"><div style="font-size: 14px; color: #888; margin-bottom: 8px;">Estado</div><div style="font-size: 24px; font-weight: 700; color: {status_color};">{status_text}</div></div>""", unsafe_allow_html=True)

with col2:
    strategy_display = {
        "elite": "🏆 Estrategia Élite",
        "larry": "📊 Larry Williams",
        "wyckoff": "🐋 Wyckoff"
    }
    current_strategy = config.get('active_strategy', 'elite')
    st.markdown(f"""<div style="background: linear-gradient(135deg, #1A1D24 0%, #262730 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #FFD700;"><div style="font-size: 14px; color: #888; margin-bottom: 8px;">Estrategia Activa</div><div style="font-size: 20px; font-weight: 700; color: #FFD700;">{strategy_display.get(current_strategy, current_strategy)}</div></div>""", unsafe_allow_html=True)

with col3:
    watchlist_count = len(config.get('watchlist', []))
    st.markdown(f"""<div style="background: linear-gradient(135deg, #1A1D24 0%, #262730 100%); padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #00BFFF;"><div style="font-size: 14px; color: #888; margin-bottom: 8px;">Acciones en Watchlist</div><div style="font-size: 28px; font-weight: 700; color: #00BFFF;">{watchlist_count}</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# ========== SECCIÓN 2: CONTROLES ==========

st.markdown("### ⚙️ Configuración del Bot")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### 🎯 Selector de Estrategia")

    strategy_options = {
        "🏆 Estrategia Élite": "elite",
        "📊 Larry Williams": "larry",
        "🐋 Wyckoff": "wyckoff"
    }

    # Encontrar la opción actual
    current_strategy_display = None
    for display, value in strategy_options.items():
        if value == config.get('active_strategy', 'elite'):
            current_strategy_display = display
            break

    selected_strategy_display = st.selectbox(
        "Selecciona la estrategia de trading:",
        options=list(strategy_options.keys()),
        index=list(strategy_options.keys()).index(current_strategy_display) if current_strategy_display else 0
    )

    selected_strategy = strategy_options[selected_strategy_display]

    if st.button("💾 Guardar Estrategia", key="save_strategy"):
        config['active_strategy'] = selected_strategy
        if save_config(config):
            st.success(f"✅ Estrategia actualizada a: {selected_strategy_display}")
            st.rerun()
        else:
            st.error("❌ Error al guardar")

with col_right:
    st.markdown("#### 📋 Editor de Watchlist")

    # ========== SELECTOR DE MISIÓN (PRESETS) ==========
    st.markdown("**🎯 Cargar Misión Pre-configurada:**")

    mission_options = ["-- Manual --"] + get_preset_names()
    selected_mission = st.selectbox(
        "Selecciona un sector o misión:",
        options=mission_options,
        help="Carga automáticamente una lista de tickers por sector"
    )

    # Botón para cargar misión
    if selected_mission != "-- Manual --":
        if st.button("🚀 Cargar Misión", key="load_mission", use_container_width=True):
            mission_tickers = get_preset_tickers(selected_mission)
            if mission_tickers:
                st.session_state['loaded_watchlist'] = ", ".join(mission_tickers)
                st.success(f"✅ Misión cargada: {len(mission_tickers)} tickers de {selected_mission}")
                st.rerun()

    st.markdown("---")

    # ========== EDITOR MANUAL DE WATCHLIST ==========
    current_watchlist = config.get('watchlist', [])

    # Si hay una misión cargada en session_state, usarla
    if 'loaded_watchlist' in st.session_state:
        watchlist_text = st.session_state['loaded_watchlist']
        # Limpiar después de cargar
        del st.session_state['loaded_watchlist']
    else:
        watchlist_text = ", ".join(current_watchlist)

    new_watchlist_text = st.text_area(
        "Ingresa los tickers separados por comas:",
        value=watchlist_text,
        height=120,
        help="Puedes modificar manualmente los tickers cargados o escribir los tuyos"
    )

    col_btn1, col_btn2 = st.columns([2, 1])

    with col_btn1:
        if st.button("💾 Guardar Watchlist", key="save_watchlist", use_container_width=True):
            # Parsear y limpiar
            new_watchlist = [ticker.strip().upper() for ticker in new_watchlist_text.split(',') if ticker.strip()]

            if len(new_watchlist) == 0:
                st.error("❌ La watchlist no puede estar vacía")
            elif len(new_watchlist) > 20:
                st.error("❌ Máximo 20 tickers permitidos")
            else:
                config['watchlist'] = new_watchlist
                if save_config(config):
                    st.success(f"✅ Watchlist actualizada: {len(new_watchlist)} tickers guardados")
                    st.rerun()
                else:
                    st.error("❌ Error al guardar")

    with col_btn2:
        if st.button("🗑️ Limpiar", key="clear_watchlist", use_container_width=True):
            st.session_state['loaded_watchlist'] = ""
            st.rerun()

st.markdown("---")

# ========== SECCIÓN 3: CONTROL DE ESTADO ==========

st.markdown("### 🔧 Control de Estado")

col_toggle1, col_toggle2 = st.columns(2)

with col_toggle1:
    if config.get('status') == 'active':
        if st.button("⏸️ Pausar Bot", type="secondary", use_container_width=True):
            config['status'] = 'paused'
            if save_config(config):
                st.success("✅ Bot pausado")
                st.rerun()
    else:
        if st.button("▶️ Activar Bot", type="primary", use_container_width=True):
            config['status'] = 'active'
            if save_config(config):
                st.success("✅ Bot activado")
                st.rerun()

with col_toggle2:
    last_updated = config.get('last_updated', 'N/A')
    st.info(f"⏰ Última actualización: {last_updated}")

st.markdown("---")

# ========== SECCIÓN 4: VISOR DE LOGS ==========

st.markdown("### 📜 Visor de Logs del Bot")

col_log1, col_log2 = st.columns([3, 1])

with col_log1:
    st.markdown("**Últimas 50 líneas del log:**")

with col_log2:
    num_lines = st.number_input("Líneas a mostrar:", min_value=10, max_value=500, value=50, step=10)

# Botón de actualización manual
if st.button("🔄 Actualizar Logs", use_container_width=True):
    st.rerun()

# Mostrar logs
logs_content = read_logs(num_lines)

st.code(logs_content, language='text', line_numbers=False)

# Auto-refresh cada 30 segundos (opcional)
st.markdown("---")
st.caption("💡 **Tip**: Los logs se actualizan automáticamente cada vez que el bot se ejecuta via GitHub Actions")

# ========== FOOTER ==========

st.markdown("---")
st.markdown("""<div style="text-align: center; color: #888; font-size: 12px; padding: 20px 0;">
<p><strong>TradeOlympo Control Room</strong> | Monitoreo y configuración del bot de trading</p>
<p>⚠️ Los cambios en la configuración se aplicarán en la próxima ejecución del bot</p>
</div>""", unsafe_allow_html=True)
