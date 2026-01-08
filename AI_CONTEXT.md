# TradeOlympo

## Hard Constraints
- Requiere claves API para datos y trading: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_ENDPOINT`.
- Requiere claves API opcionales para sincronización GitHub: `GITHUB_TOKEN`, `GITHUB_REPO`.
- Flujo local esperado: `pip install -r requirements.txt` y `streamlit run app.py`.
- Python 3.9+ requerido (GitHub Actions usa Python 3.9).
- Sin linter/format oficial documentado en el repo.
- Prohibido usar pandas-ta (incompatible con Python 3.9).

## Project State Summary
TradeOlympo v6.0 (Zen Mode + Charts) es una terminal web profesional (Streamlit, dark-mode) con **6 estrategias de trading** y **visualización avanzada de gráficos**. Diseño "Zen Mode" que prioriza datos sobre configuración. Arquitectura de doble propósito con (1) **Panel de Control del Bot** (colapsado por defecto) que configura misión automática en `user_config.json` sincronizada vía GitHub/PyGithub, y (2) **Radar de Monitoreo Panorámico** con vista simultánea de todos los jueces + **Gráficos TradingView integrados**.

**Modo Centinela (🛡️)**: Estrategia de máxima eficiencia que ejecuta **4 estrategias de trading simultáneamente** (Élite, Rompeolas, The Wheel, ORB). Si cualquier juez da señal CALL → Ejecuta compra inmediata. Registra en `trade_history.json` qué estrategia específica disparó (ej: "centinela → rompeolas"). Prioridad de disparo: Rompeolas > Élite > Wheel > ORB.

**Zen Mode UX**: Sidebar colapsado por defecto (initial_sidebar_state="collapsed"). Panel de Control del Bot dentro de expander cerrado. Usuario ve directamente: Radar Panorámico → Consenso de Jueces → Selector de Análisis → Detalles del Contrato → **Gráfico TradingView**. Mensajes informativos compactados (st.caption en lugar de st.info). Disclaimer en expander colapsable.

**Integración TradingView**: Widget oficial de TradingView embebido con st.components.v1.html. Gráfico de 600px de altura, tema dark, timezone NY. Símbolo dinámico vinculado a st.session_state (ej: NASDAQ:AAPL). Exchange automático según ticker (NASDAQ/NYSE/AMEX). Estudios preconfigurados: SMA y RSI. Preparado para personalización futura con user_id y chart_id para gráficos guardados.

Ejecuta cada **15 minutos** durante market hours (9:30am-4pm ET) vía GitHub Actions (cron: `*/15 13-21 * * 1-5` UTC). Todas las operaciones se registran en **`trade_history.json`** con timestamp en New York Time (America/New_York). Bot opera con **10 acciones** por señal en Paper Trading. Interfaz incluye pestaña "📜 Historial Oficial" que muestra bitácora de operaciones con métricas de resumen.

**Sectores estratégicos curados**: (1) Venezuela Recovery & Oil Services (10 tickers: CVX, SLB, HAL, VLO, WFRD, XOM, COP, MPC, OXY, PBR), (2) Big Tech & AI (8 tickers), (3) Crypto Proxies (6 tickers), (4) Defensa & Aero (6 tickers). **Radar Panorámico**: Tabla muestra todos los jueces simultáneamente con iconos visuales (🟢 CALL, 🔴 SELL, 🟡 WATCH, ⚪ NEUTRAL). Stack técnico: Python 3.9+, Streamlit, Alpaca API, PyGithub, TradingView Widgets, pandas nativo (sin pandas-ta). Estado: **PRODUCCIÓN v6.0** - Zen Mode activado, gráficos integrados.

## Recent Session Logs
| Fecha | Evento |
| --- | --- |
| 2026-01-08 (v6.0 Zen Mode + Charts) | **Rediseño Zen + Gráficos Avanzados**: (1) **Zen Mode** - Sidebar colapsado por defecto. Panel de Control del Bot en expander cerrado. Mensajes informativos compactados (st.caption). Disclaimer en expander. Usuario ve directamente Radar → Análisis. (2) **Integración TradingView** - Widget oficial embebido con st.components.v1.html. Gráfico de 600px, tema dark, timezone NY. Símbolo dinámico vinculado a ticker seleccionado. Exchange automático (NASDAQ/NYSE/AMEX). Estudios: SMA + RSI preconfigurados. Preparado para personalización futura (user_id, chart_id). (3) **Optimización de Espacio** - Eliminados mensajes redundantes. Más espacio vertical para tabla y gráfico. Layout optimizado para laptops. |
| 2026-01-07 (v5.1 Eficiencia Integral) | **Actualización Integral de Eficiencia**: (1) **Modo Centinela expandido** - Ejecuta 4 estrategias simultáneamente (Elite, Rompeolas, Wheel, ORB) con prioridad de disparo y registro específico de trigger. (2) **Radar Panorámico completo** - Tabla muestra todas las columnas de jueces simultáneamente con iconos visuales. (3) **UX Mejorado** - Avisos de recomendación técnica. Botón "Cargar Tickers por Defecto". (4) **Tesis Venezuela integrada** - Sector venezuela_recovery disponible. |
| 2026-01-07 (v5.0 PROD) | **Producción Lista**: Nuevas estrategias: The Wheel (opciones CSP/CC) y ORB (day trading). Componentes educativos UX con `st.expander()`. Sincronización horaria completa a NY Time. Test mode removido. Bot opera con **qty=10 acciones**. Bitácora persistente en **`trade_history.json`**. Cron actualizado a **cada 15 minutos**. Pestaña "📜 Historial Oficial" con métricas. |

## 🤖 PROTOCOLO DE MANTENIMIENTO (Instrucciones para la IA)
Regla de Oro: Este archivo debe ser ligero.
1. Si "Recent Session Logs" tiene >3 entradas: Mueve las antiguas a `AI_ARCHIVE.md`.
2. Actualiza el "Project State Summary" con los cambios realizados.
3. Mantén este archivo por debajo de 15,000 tokens.
4. Respeta la estructura original: Hard Constraints, Project State Summary, Recent Session Logs, Protocolo.
5. Recent Session Logs debe ser una tabla markdown con columnas: Fecha | Evento.
