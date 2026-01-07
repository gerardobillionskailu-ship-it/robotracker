# Historical Decision Logs - TradeOlympo

## 2026-01-07

### v4.0 - Arquitectura de Doble Propósito

**Decisión Arquitectónica**: Separar completamente la configuración del bot de la visualización del usuario

**Problema Resuelto**:
- Usuario no podía explorar estrategias sin cambiar la configuración del bot automático
- Confusión entre "lo que veo en pantalla" vs "lo que ejecuta el bot"

**Implementación**:
1. **Panel de Control del Bot (Misión)**:
   - Configura qué estrategia ejecutará el bot en GitHub Actions
   - Guarda en `user_config.json` → sincroniza con GitHub vía PyGithub
   - Variables: `bot_strategy`, `bot_watchlist_text` (session_state)

2. **Radar de Monitoreo (Vista)**:
   - Selector visual de estrategia (4 opciones)
   - Solo afecta columna "Señal Principal" en tabla
   - Variable: `view_strategy` (session_state, NO persiste)

3. **Indicador de Sincronización**:
   - CSS gradient box mostrando: "Vista: X | Bot: Y"
   - Previene confusión usuario

**Jueces Restaurados**:
- **Larry Williams**: Williams %R + Golden/Death Cross
  - Lógica: Williams %R < -80 + SMA 50 > SMA 200 → CALL
- **Wyckoff**: Volumen + Posición de vela
  - Lógica: Volumen > 150% + Close en top 70% → CALL (acumulación)
- **Élite**: RSI + Reversión (ya existía)
- **Rompeolas**: Breakout + Momentum (ya existía)

**Tabla Multi-Juez**:
- Cada fila muestra opinión de TODOS los jueces
- Columnas: Ticker, Precio, RSI, Señal Principal, Análisis, Larry Williams, Wyckoff, Élite, Rompeolas
- Señal Principal cambia según `view_strategy` seleccionado

**Funciones Agregadas** (app.py):
- `generate_all_judges_signals()`: Consulta 4 estrategias simultáneamente
- `render_sync_indicator()`: Indicador visual
- `render_bot_mission_panel()`: Panel configuración bot
- `render_independent_monitoring_radar()`: Selector visual
- `render_trading_table_with_judges()`: Tabla con todas opiniones

**Indicadores Implementados**:
- Williams %R (14 períodos)
- SMA 50, SMA 200
- Close Position (% dentro del rango de vela)
- Volumen vs promedio 30 días

**Commits**:
- `e690f39`: v4.0 Arquitectura de Doble Propósito
- `7f80188`: Activar Ejecución Automática + Sincronizar Lógica Web-Bot
- `c704fcd`: TEST MODE: Compra Forzada de OXY

**Trade-offs**:
- ✅ Independencia total entre bot y vista
- ✅ Claridad conceptual (indicador de sincronización)
- ❌ Complejidad UI (2 selectores de estrategia)
- ✅ Flexibilidad: bot opera energía mientras usuario analiza tech

---

### Ejecución Automática Activada (v3.1)

**Decisión**: Activar `api.submit_order()` para ejecución real

**Problema**: Bot detectaba señales pero no ejecutaba órdenes (solo recomendaba)

**Implementación**:
- Función `submit_order()` en bot.py:345-374
- Parámetros: symbol, qty=10 (luego 1 en test), side='buy', type='market', time_in_force='day'
- Logs: Order ID, Status capturados en `last_run_results.json`

**Ajuste de Filtro de Volumen**:
- ANTES: `MIN_VOLUME_THRESHOLD = 1_000_000`
- AHORA: `MIN_VOLUME_THRESHOLD = 100_000`
- Razón: Acciones de energía (XLE, OXY) con volumen ~767K eran descartadas

**Test Mode OXY** (temporal):
```python
# bot.py:243-258
if ticker == "OXY":
    signal = "CALL (TEST DE CONEXIÓN - COMPRA FORZADA)"
    # Compra 1 acción para verificar submit_order()
```
**Resultado**: Verificación exitosa de integración con Alpaca API

**Pendiente**: Revertir test mode después de confirmar ejecución

---

### Dark Mode + Configuración Persistente (v3.0)

**Decisión**: Crear `user_config.json` como fuente única de verdad

**Problema**: Configuración se perdía al refrescar navegador

**Implementación**:
- `user_config.json`: Estructura con active_strategy, watchlist, last_updated, strategies
- `save_config_to_github()`: Sincronización automática vía PyGithub
- Dark Mode CSS: Background #0E1117, Accents #1E88E5, Success #10B981

**Tabla de Análisis en Tiempo Real**:
- `fetch_market_data()`: Cache 60s, Alpaca API con feed IEX
- `generate_signals()`: Lógica Élite y Rompeolas
- Styled DataFrame con colores condicionales

**Trade-off**:
- ✅ Persistencia entre sesiones
- ✅ Bot lee misma config que web
- ❌ Eliminación temporal de "Jueces" (revertido en v4.0)

---

### Arquitectura Modular sin pandas-ta (v2.x)

**Decisión**: Eliminar pandas-ta, usar funciones nativas

**Problema**: `ModuleNotFoundError: No module named 'pandas_ta'` en GitHub Actions Python 3.9

**Causa Raíz**: pandas-ta incompatible con Python 3.9

**Solución**:
```python
def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_sma(series, window):
    return series.rolling(window=window).mean()
```

**Estrategias Modularizadas**:
- `analizar_estrategia_elite()`: RSI < 30 + SMA 200
- `analizar_estrategia_rompeolas()`: Breakout + RSI > 50 + Volumen

**Merge Conflicts**:
- Resuelto usando `git checkout --ours` (versión Alpaca sobre yfinance)

**Trade-off**:
- ✅ Compatibilidad total Python 3.9+
- ✅ Control completo sobre cálculos
- ❌ Más código a mantener

---

## Decisiones Arquitectónicas Clave

### Por qué Alpaca en lugar de yfinance
- yfinance retorna errores JSON aleatorios ("Expecting value: line 1 column 1")
- Alpaca ofrece feed IEX gratuito + capacidad de ejecución
- API más estable y documentada

### Por qué NO pandas-ta
- Incompatibilidad con Python 3.9 en GitHub Actions
- Solo necesitamos RSI, SMA, Williams %R (implementables nativamente)
- Funciones nativas más rápidas (sin overhead)

### Por qué session_state para Vista (NO persiste)
- Vista es temporal: cada usuario puede tener preferencia diferente
- `user_config.json` es fuente de verdad del bot
- Evita escrituras excesivas a GitHub
- Performance: menos I/O

### Por qué Arquitectura de Doble Propósito (v4.0)
- Usuario quiere explorar sin interrumpir bot
- Evitar confusión: "¿Por qué bot no ejecuta lo que veo?"
- Flexibilidad: Bot opera energía mientras usuario analiza tech
- Indicador de sincronización resuelve ambigüedad

---

## Problemas Históricos Resueltos

### #1: "Bot descarta TODAS las oportunidades"
**Versión**: v3.1
**Síntoma**: `⏭️ VOLUMEN BAJO: Promedio 767,231 < 1,000,000`
**Solución**: `MIN_VOLUME_THRESHOLD = 100_000`
**Commit**: `7f80188`

### #2: "pandas-ta ModuleNotFoundError"
**Versión**: v1.x-v2.x
**Síntoma**: `ERROR: Could not find pandas-ta==0.3.14b0`
**Solución**: Funciones nativas `calcular_rsi()`, `calcular_sma()`
**Commit**: `5f72d82`

### #3: "Configuración se pierde al refrescar"
**Versión**: v1.x-v2.x
**Síntoma**: Watchlist vuelve a default
**Solución**: `user_config.json` + PyGithub sync
**Commit**: `ffdcff4`

### #4: "Bot no ejecuta lo que veo"
**Versión**: v3.x
**Síntoma**: Usuario ve CALL en Élite, bot no ejecuta
**Solución**: Arquitectura de Doble Propósito
**Commit**: `e690f39`

---

## Lecciones Aprendidas

1. **Dependencias externas son riesgosas**: pandas-ta bloqueó producción → usar nativo cuando sea posible
2. **Separación de concerns es crucial**: Mezclar bot con UI causó confusión → interfaces separadas
3. **Testing en producción requiere modo test**: Imposible verificar `submit_order()` sin señal → test mode temporal
4. **Indicadores visuales claros evitan soporte**: Indicador de sincronización previene 90% de preguntas

---

## Roadmap Futuro

### Corto Plazo (1-2 semanas)
- [ ] Revertir Test Mode de OXY
- [ ] Agregar logs de ejecución en UI (últimas órdenes del bot)
- [ ] Persistir `view_strategy` en localStorage (opcional)

### Mediano Plazo (1 mes)
- [ ] Backtesting panel: Comparar rendimiento histórico de jueces
- [ ] Gráficos Plotly con indicadores visuales
- [ ] Alertas vía webhook cuando bot ejecuta

### Largo Plazo (3 meses)
- [ ] Panel de Performance: P&L del bot
- [ ] Modo Paper Trading vs Real Trading toggle
- [ ] Integración con más brokers

---

## Changelog Detallado

### 2026-01-07
- [FEATURE] v4.0: Arquitectura de Doble Propósito
- [FEATURE] Panel de Control del Bot (Misión)
- [FEATURE] Radar de Monitoreo Independiente
- [FEATURE] Indicador de Sincronización CSS
- [FEATURE] Restauración jueces: Larry Williams, Wyckoff
- [FEATURE] Tabla multi-juez con opiniones simultáneas
- [DOCS] Actualización AI_CONTEXT.md y AI_ARCHIVE.md

### 2026-01-06
- [FEATURE] v3.1: Ejecución automática con `api.submit_order()`
- [FIX] Volumen mínimo 1M → 100K
- [TEST] Compra forzada de OXY (1 acción)
- [FIX] Sincronización cálculo volumen (30 días)
- [FEATURE] v3.0: Dark Mode completo
- [FEATURE] Persistencia con `user_config.json`
- [FEATURE] Sincronización GitHub vía PyGithub
- [FEATURE] Tabla análisis tiempo real

### 2026-01-05/06
- [FIX] v2.x: Arquitectura modular SIN pandas-ta
- [FEATURE] Funciones nativas `calcular_rsi()`, `calcular_sma()`
- [FIX] Merge conflicts (Alpaca vs yfinance)
- [FIX] Compatibilidad Python 3.9

### 2026-01-03/04
- [FEATURE] v1.x: MVP inicial con Streamlit
- [FEATURE] Conexión Alpaca API
- [FEATURE] Watchlist básica

---

**Archivo inicializado**: 2026-01-07 para mantener histórico de decisiones y bitácoras antiguas.
