# TradeOlympo

## Hard Constraints
- Requiere claves API para datos y trading: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_ENDPOINT`.
- Requiere claves API opcionales para sincronización GitHub: `GITHUB_TOKEN`, `GITHUB_REPO`.
- Flujo local esperado: `pip install -r requirements.txt` y `streamlit run app.py`.
- Python 3.9+ requerido (GitHub Actions usa Python 3.9).
- Sin linter/format oficial documentado en el repo.
- Prohibido usar pandas-ta (incompatible con Python 3.9).

## Project State Summary
TradeOlympo v4.0 es una terminal web profesional (Streamlit, dark-mode) con **arquitectura de doble propósito** que separa la configuración del bot automático de la visualización del usuario. La aplicación está unificada en `app.py` con dos interfaces independientes: (1) **Panel de Control del Bot** que configura la misión automática guardada en `user_config.json` y sincronizada vía GitHub/PyGithub, y (2) **Radar de Monitoreo** que permite visualizar cualquier estrategia sin afectar el bot.

Implementa 4 estrategias de trading simultáneas ("jueces"): Larry Williams (Williams %R + Golden Cross), Wyckoff (volumen + posición de vela), Élite (RSI + reversión), y Rompeolas (breakout + momentum). La tabla muestra la opinión de TODOS los jueces en columnas separadas, permitiendo al usuario explorar diferentes enfoques mientras el bot ejecuta automáticamente la estrategia configurada.

Stack técnico: Python 3.9+, Streamlit, Alpaca API (market data + ejecución), PyGithub (sincronización), pandas nativo (sin pandas-ta). Bot ejecuta en GitHub Actions leyendo `user_config.json`. Estado actual: ejecución automática activada con `api.submit_order()`, test mode temporal en OXY (pendiente revertir), sin tests automatizados documentados.

## Recent Session Logs
| Fecha | Evento |
| --- | --- |
| 2026-01-07 | **v4.0 - Arquitectura de Doble Propósito**: Refactorización completa de `app.py` (720 líneas). Implementado Panel de Control del Bot (Misión) separado de Radar de Monitoreo (Vista). Restauración de jueces Larry Williams y Wyckoff. Tabla multi-juez con opiniones simultáneas. Indicador de sincronización CSS. Usuario puede explorar estrategias sin interrumpir bot automático. Commits: `e690f39` (v4.0), `7f80188` (ejecución automática), `c704fcd` (test mode OXY). |
| 2026-01-06 | v3.1: Activada ejecución automática con `api.submit_order()`. Volumen mínimo reducido 1M→100K. Test mode forzado en OXY (1 acción). v3.0: Dark Mode completo, `user_config.json` como fuente única, sincronización GitHub vía PyGithub, tabla de análisis en tiempo real. Eliminación temporal de metáfora "Jueces" (restaurada en v4.0). |
| 2026-01-05/06 | v2.x: Arquitectura modular con funciones nativas `calcular_rsi()` y `calcular_sma()`. Eliminación de pandas-ta por incompatibilidad Python 3.9. Merge conflicts resueltos (Alpaca vs yfinance). Estrategias Élite y Rompeolas modularizadas. |

## 🤖 PROTOCOLO DE MANTENIMIENTO (Instrucciones para la IA)
Regla de Oro: Este archivo debe ser ligero.
1. Si "Recent Session Logs" tiene >3 entradas: Mueve las antiguas a `AI_ARCHIVE.md`.
2. Actualiza el "Project State Summary" con los cambios realizados.
3. Mantén este archivo por debajo de 15,000 tokens.
4. Respeta la estructura original: Hard Constraints, Project State Summary, Recent Session Logs, Protocolo.
5. Recent Session Logs debe ser una tabla markdown con columnas: Fecha | Evento.
