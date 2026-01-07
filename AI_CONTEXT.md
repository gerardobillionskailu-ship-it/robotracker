# TradeOlympo

## Hard Constraints
- Requiere claves API para datos y trading: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_ENDPOINT`.
- Requiere claves API opcionales para sincronización GitHub: `GITHUB_TOKEN`, `GITHUB_REPO`.
- Flujo local esperado: `pip install -r requirements.txt` y `streamlit run app.py`.
- Python 3.9+ requerido (GitHub Actions usa Python 3.9).
- Sin linter/format oficial documentado en el repo.
- Prohibido usar pandas-ta (incompatible con Python 3.9).

## Project State Summary
TradeOlympo v5.0 (Producción) es una terminal web profesional (Streamlit, dark-mode) con **6 estrategias de trading**: 2 Swing (Élite, Rompeolas), 2 análisis (Larry Williams, Wyckoff), 1 Opciones (The Wheel), 1 Day Trading (ORB). Arquitectura de doble propósito con (1) **Panel de Control del Bot** que configura misión automática en `user_config.json` sincronizada vía GitHub/PyGithub, y (2) **Radar de Monitoreo** con flujo "Seleccionar → Inyectar → Editar → Analizar" usando sectores estratégicos pre-cargados pero editables.

Ejecuta cada **15 minutos** durante market hours (9:30am-4pm ET) vía GitHub Actions (cron: `*/15 13-21 * * 1-5` UTC). Todas las operaciones se registran en **`trade_history.json`** con timestamp en New York Time (America/New_York). Bot opera con **10 acciones** por señal en Paper Trading. Interfaz incluye pestaña "📜 Historial Oficial" que muestra bitácora de operaciones con métricas de resumen.

**Sectores estratégicos curados**: (1) Venezuela Recovery & Oil Services (10 tickers: CVX, SLB, HAL, VLO, WFRD, XOM, COP, MPC, OXY, PBR), (2) Big Tech & AI (8 tickers), (3) Crypto Proxies (6 tickers), (4) Defensa & Aero (6 tickers). Stack técnico: Python 3.9+, Streamlit, Alpaca API, PyGithub, pandas nativo (sin pandas-ta). Estado: **PRODUCCIÓN** - Test mode removido, qty=10 acciones, sincronización horaria NY completa.

## Recent Session Logs
| Fecha | Evento |
| --- | --- |
| 2026-01-07 (v5.0 PROD) | **Producción Lista**: Nuevas estrategias: The Wheel (opciones CSP/CC) y ORB (day trading). Componentes educativos UX con `st.expander()`. Sincronización horaria completa a NY Time (`America/New_York`). Test mode removido. Bot opera con **qty=10 acciones**. Bitácora persistente en **`trade_history.json`**. Cron actualizado a **cada 15 minutos** (market hours). Pestaña "📜 Historial Oficial" con métricas. GitHub Actions auto-commit de `trade_history.json`. |
| 2026-01-07 (v4.1) | **UX Mejorado + Tesis Venezuela**: Flujo "Seleccionar → Inyectar → Editar → Analizar" en Radar de Monitoreo. 4 sectores estratégicos curados con Venezuela Recovery (10 tickers). Selectbox con callback automático. |
| 2026-01-07 (v4.0) | **Arquitectura de Doble Propósito**: Panel de Control del Bot separado de Radar de Monitoreo. Tabla multi-juez con 4 estrategias simultáneas (Larry Williams, Wyckoff, Élite, Rompeolas). Indicador de sincronización CSS. |

## 🤖 PROTOCOLO DE MANTENIMIENTO (Instrucciones para la IA)
Regla de Oro: Este archivo debe ser ligero.
1. Si "Recent Session Logs" tiene >3 entradas: Mueve las antiguas a `AI_ARCHIVE.md`.
2. Actualiza el "Project State Summary" con los cambios realizados.
3. Mantén este archivo por debajo de 15,000 tokens.
4. Respeta la estructura original: Hard Constraints, Project State Summary, Recent Session Logs, Protocolo.
5. Recent Session Logs debe ser una tabla markdown con columnas: Fecha | Evento.
