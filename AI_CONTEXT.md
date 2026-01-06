# AI CONTEXT - PROYECTO: TradeOlympo (Paper Trading)
> **SISTEMA:** Google Antigravity IDE
> **FECHA:** Enero 2026

## 1. Directrices de Modelos (Antigravity Rules)
- **Para Lógica Compleja/Arquitectura:** Usar **Gemini 3 Pro (High)**. Necesitamos razonamiento profundo para la estrategia "Rompeolas" y la gestión de riesgo.
- **Para Código Rutinario/Refactor:** Usar **Gemini Flash 2.5**. Priorizar velocidad en funciones simples de `pandas` o ajustes de UI en Streamlit.

## 2. Visión del Proyecto
Bot de trading algorítmico en Python para Swing Trading de Opciones.
- **Objetivo:** Paper Trading (Simulación) para validar estrategia.
- **Plataforma:** Alpaca Markets (Paper API).
- **Capital Simulado:** $1,000 USD (Hard Limit).

## 3. Reglas Críticas (Hard Constraints)
1.  **Paper Only:** Base URL debe ser SIEMPRE `https://paper-api.alpaca.markets`.
2.  **Dependencias 2026:**
    - `alpaca-py` (SDK oficial).
    - `pandas` 2.x+.
    - `streamlit` (Dashboard).
3.  **Prohibido:** No usar `yfinance` para datos en vivo (retraso), usar datos de Alpaca Historical.

## 4. Estado del Agente (Current State)
- El bot tiene estructura básica.
- Foco actual: Implementación de señales de entrada basadas en RSI + Volumen.
- Próximo paso: Validación de órdenes de venta (Stop Loss).
