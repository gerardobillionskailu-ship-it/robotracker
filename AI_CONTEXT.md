# TradeOlympo

## Hard Constraints
- Requiere claves API para datos y trading: `ALPHAVANTAGE_API_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_ENDPOINT`.
- Flujo local esperado: `pip install -r requirements.txt` y `streamlit run app.py`.
- Sin linter/format oficial documentado en el repo.

## Project State Summary
TradeOlympo es una terminal web en español (Streamlit, dark-mode) para análisis de acciones y simulación de estrategias. La base está organizada con `app.py` como entrada principal, páginas en `pages/`, componentes en `views/` y utilidades en `utils/`. El stack principal es Python 3.8+ con Streamlit, Plotly y pandas; integra datos vía Alpha Vantage y Alpaca. Estado actual: sin pruebas automatizadas documentadas, dependiente de claves API para validar flujos, y con necesidad futura de alinear la estrategia de datos entre fuentes.

## Recent Session Logs
| Fecha | Evento |
| --- | --- |
| N/A | Auditoría inicial del proyecto y creación del archivo de contexto consolidado. `AI_CONTEXT.md` fue modificado. No se ejecutaron pruebas ni se lanzó Streamlit. Próximo paso: ejecutar `streamlit run app.py` con claves válidas y documentar resultados. |

## 🤖 PROTOCOLO DE MANTENIMIENTO (Instrucciones para la IA)
Regla de Oro: Este archivo debe ser ligero.
1. Si "Recent Session Logs" tiene >3 entradas: Mueve las antiguas a `AI_ARCHIVE.md`.
2. Actualiza el "Project State Summary" con los cambios realizados.
3. Mantén este archivo por debajo de 15,000 tokens.
