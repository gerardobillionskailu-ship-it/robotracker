# AI_CONTEXT

## 1. **Project Identity:**
- **Nombre:** TradeOlympo (Paper Trading/Análisis)
- **Visión corta:** Terminal web en español para analizar acciones y simular estrategias de trading con estilo profesional dark-mode.
- **Objetivo final:** Proveer un dashboard Streamlit conectado a datos de mercado (Alpha Vantage/Alpaca) y utilidades de bot para validar señales en paper trading.

## 2. **Tech Stack Definition:**
- **Lenguaje principal:** Python 3.8+
- **Framework/UI:** Streamlit 1.31.0
- **Visualización:** Plotly 5.18.0
- **Datos y cálculos:** pandas 2.2.0, numpy 1.26.3, ta 0.11.0
- **APIs de mercado:** alpha-vantage 2.3.1 (datos), alpaca-trade-api 3.0.2 (trading/bars)
- **Utilidades adicionales:** requests-cache 1.1.1, pytz 2024.1, PyGithub 2.1.1

## 3. **Architecture Map:**
- **app.py:** Entrada principal de Streamlit con UI dark-mode, carga de datos vía Alpaca y generación de señales.
- **pages/**: Páginas secundarias de Streamlit (p.ej., `bot_control.py`).
- **views/**: Componentes de presentación (dashboard principal, guías de uso).
- **utils/**: Lógica de soporte (`indicators.py`, `data_loader.py`, presets de mercado).
- **configs/archivos raíz:** `trading_config.json`, `user_config.json`, `watchlist.json` y `runtime.txt` mantienen configuraciones predeterminadas; `requirements.txt` define dependencias.

## 4. **Environment & Rules:**
- **Instalación:** `pip install -r requirements.txt`
- **Ejecución local:** `streamlit run app.py`
- **Variables/Secrets requeridas:**
  - `ALPHAVANTAGE_API_KEY` (para datos en Streamlit; se define en secrets de Streamlit Cloud).
  - `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_ENDPOINT` (para funciones de bot y datos Alpaca; previstos en GitHub Actions/entorno local).
- **Linter/format:** No se documenta un linter específico en el repo actual.

## 5. **Status & Known Issues:**
- La app depende de claves API; sin ellas fallarán las llamadas a datos de mercado.
- No se encontraron pruebas automatizadas o CI documentados; el estado de compilación/test es desconocido.
- La documentación mezcla fuentes de datos (Alpha Vantage vs. Alpaca) y requiere alineación futura de estrategia de datos.

## 6. **🔄 SESIÓN ACTUAL (Bitácora de Relevo):**
- **Última Tarea:** Auditoría inicial del proyecto y creación del archivo de contexto consolidado.
- **Archivos Modificados:** `AI_CONTEXT.md`.
- **Estado del Código:** No se ejecutaron pruebas ni se lanzó Streamlit en esta sesión.
- **Siguiente Paso:** Ejecutar `streamlit run app.py` con claves de API válidas para verificar carga de datos y flujos de UI; documentar o agregar pruebas según resultados.
