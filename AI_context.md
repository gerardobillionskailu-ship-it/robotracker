# AI Context - TradeOlympo v4.0

## Arquitectura de Doble Propósito

TradeOlympo v4.0 implementa una arquitectura única que separa completamente la **configuración del bot** de la **visualización del usuario**.

### Conceptos Clave

1. **Misión del Bot (Piloto Automático)**
   - Configura qué estrategia ejecutará el bot en GitHub Actions
   - Se guarda en `user_config.json`
   - Sincroniza automáticamente con GitHub vía PyGithub
   - **NO afecta** la visualización de la tabla

2. **Radar de Monitoreo (Vista Independiente)**
   - Selector visual que permite explorar cualquier estrategia
   - Solo afecta qué columna se muestra como "Señal Principal"
   - **NO afecta** la operación del bot
   - Permite escanear el mercado sin interrumpir el piloto automático

3. **Indicador de Sincronización**
   - Muestra claramente: "Vista: X | Bot: Y"
   - Evita confusión entre lo que ve el usuario vs lo que ejecuta el bot

---

## Estructura de Archivos

### `app.py` (Interfaz Web Unificada)

**Responsabilidad**: Única interfaz que integra control del bot y monitoreo visual

**Funciones Principales**:

#### Panel de Control del Bot
- `render_bot_mission_panel()`: Configura estrategia y watchlist del bot
- `save_config_to_github()`: Sincroniza `user_config.json` con GitHub
- Guarda en session_state: `bot_strategy`, `bot_watchlist_text`

#### Radar de Monitoreo
- `render_independent_monitoring_radar()`: Selector visual de estrategia
- `render_trading_table_with_judges()`: Tabla con TODAS las opiniones
- Guarda en session_state: `view_strategy`

#### Generación de Señales
- `generate_all_judges_signals(df)`: Consulta a 4 jueces simultáneamente
  - **Larry Williams**: Williams %R + Golden Cross
  - **Wyckoff**: Volumen + Posición de cierre de vela
  - **Élite**: RSI < 30 + Tendencia alcista
  - **Rompeolas**: Breakout + RSI > 50 + Volumen alto

#### Indicador de Estado
- `render_sync_indicator(bot_strategy, view_strategy)`: CSS gradient box

---

### `bot.py` (Ejecución Automática)

**Responsabilidad**: Lee `user_config.json` y ejecuta la estrategia configurada

**Flujo de Ejecución**:
1. `load_user_config()` → Lee `active_strategy` y `watchlist`
2. `fetch_stock_data()` → Descarga datos desde Alpaca API
3. `analizar_estrategia_elite()` o `analizar_estrategia_rompeolas()`
4. `api.submit_order()` → Ejecuta compra si hay señal CALL

**Importante**: El bot **ignora** el estado visual de la web. Solo lee `user_config.json`.

---

### `user_config.json` (Configuración Centralizada)

**Responsabilidad**: Contrato entre interfaz web y bot automático

```json
{
  "active_strategy": "rompeolas",
  "watchlist": ["XLE", "OXY", "APA", "CVX"],
  "last_updated": "2026-01-07T00:00:00",
  "strategies": {
    "elite": {
      "name": "Estrategia Élite (Reversión)",
      "default_tickers": ["NVDA", "TSLA", "AMD", "AAPL", "MSFT", "META", "COIN"]
    },
    "rompeolas": {
      "name": "Estrategia Rompeolas (Breakout)",
      "default_tickers": ["XLE", "OXY", "APA", "CVX", "COP", "SLB", "HAL", "VLO"]
    },
    "larry": {
      "name": "Larry Williams (Contrarian)",
      "default_tickers": ["SPY", "QQQ", "IWM", "XLE", "XLF"]
    },
    "wyckoff": {
      "name": "Wyckoff (Volume)",
      "default_tickers": ["SPY", "NVDA", "TSLA", "XLE"]
    }
  }
}
```

---

## Estrategias Implementadas

### 1. Larry Williams (Contrarian)

**Filosofía**: Trading contrarian con Williams %R

**Indicadores**:
- Williams %R (14 períodos)
- SMA 50 y SMA 200 (Golden/Death Cross)

**Lógica de Entrada**:
```python
if williams_r < -80:  # Sobreventa extrema
    if sma_50 > sma_200:  # Golden Cross
        → CALL
```

**Señales**:
- CALL: Williams %R < -80 + Golden Cross
- SELL: Williams %R > -20 (sobrecompra)
- WATCH: Sobreventa sin Golden Cross
- NEUTRAL: Zona intermedia (-80 a -20)

---

### 2. Wyckoff (Volume Analysis)

**Filosofía**: Análisis de volumen y posición de cierre de vela

**Indicadores**:
- Volumen vs promedio 30 días
- Posición de cierre dentro del rango de la vela

**Lógica de Entrada**:
```python
volumen_alto = volume > (avg_volume * 1.5)
close_in_upper = close_position > 70%

if volumen_alto and close_in_upper:
    → CALL (Acumulación institucional)
```

**Señales**:
- CALL: Volumen alto + Cierre en top 70% (acumulación)
- SELL: Volumen alto + Cierre en low 30% (distribución)
- WATCH: Volumen alto sin dirección clara
- NEUTRAL: Volumen normal

---

### 3. Élite (Tech / Reversión)

**Filosofía**: Swing trading clásico, reversión a la media

**Indicadores**:
- RSI (14 períodos)
- SMA 20 y SMA 200

**Lógica de Entrada**:
```python
if rsi < 30:
    if price > sma_200:
        → CALL (Sobrevendido en tendencia alcista)
```

**Señales**:
- CALL: RSI < 30 + Precio > SMA 200
- WATCH: RSI bajo sin tendencia, o pullback sano
- NEUTRAL: RSI en zona normal

---

### 4. Rompeolas (Energía / Breakout)

**Filosofía**: Breakout con confirmación de volumen

**Indicadores**:
- Resistencia 20 días
- RSI > 50 (fuerza, no rebote)
- Volumen vs promedio 30 días

**Lógica de Entrada**:
```python
breakout = price > resistencia_20d
fuerza = rsi > 50
volumen_institucional = volume > (avg_volume * 1.5)

if breakout and fuerza and volumen_institucional:
    → CALL
```

**Señales**:
- CALL: Breakout + RSI > 50 + Volumen > 150%
- WATCH: Breakout sin volumen
- NEUTRAL: Sin breakout o RSI < 50

---

## Flujo de Uso

### Escenario 1: Usuario quiere operar manualmente Tech mientras el bot opera Energía

1. En **Panel de Control del Bot**, seleccionar:
   - Estrategia: Rompeolas
   - Watchlist: XLE, OXY, APA
   - → GUARDAR MISIÓN

2. En **Radar de Monitoreo**, seleccionar:
   - Ver Élite

3. **Indicador de Sincronización** mostrará:
   - `Vista: ÉLITE | Bot: ROMPEOLAS`

4. **Tabla** mostrará:
   - Señal Principal: Opinión de Élite
   - Columnas de jueces: Larry, Wyckoff, Élite, Rompeolas

5. **Bot en GitHub** ejecutará:
   - Estrategia Rompeolas en XLE, OXY, APA
   - Ignorará lo que ve la tabla web

---

### Escenario 2: Usuario quiere explorar todas las estrategias sin cambiar bot

1. Mantener bot configurado en Rompeolas
2. Cambiar vista entre: Élite → Larry → Wyckoff → Rompeolas
3. Tabla actualiza "Señal Principal" sin tocar `user_config.json`
4. Bot sigue ejecutando Rompeolas

---

## Variables de Session State

### Bot (Persistente en user_config.json)
- `bot_strategy`: Estrategia que ejecutará el bot
- `bot_watchlist_text`: Tickers del bot (separados por coma)

### Vista (Solo UI, NO persiste)
- `view_strategy`: Estrategia visible en tabla

---

## Dependencias Críticas

### Python Packages
- `streamlit==1.31.0`: Web framework
- `alpaca-trade-api==3.0.2`: Market data
- `PyGithub==2.1.1`: Sincronización GitHub
- `pandas==2.2.0`: Data processing
- `plotly==5.18.0`: Charts (si se agregan en futuro)

### Secrets de Streamlit
```toml
ALPACA_API_KEY = "..."
ALPACA_SECRET_KEY = "..."
ALPACA_ENDPOINT = "https://paper-api.alpaca.markets"
GITHUB_TOKEN = "ghp_..."
GITHUB_REPO = "usuario/robotracker"
```

---

## Patrón de Diseño

**Separation of Concerns (SoC)**:
- **Presentación** (app.py): UI y visualización
- **Lógica de Negocio** (app.py + bot.py): Generación de señales
- **Ejecución** (bot.py): Órdenes a broker
- **Configuración** (user_config.json): Contrato entre componentes

**State Management**:
- Session State: Temporal, solo para UI
- user_config.json: Persistente, fuente de verdad del bot

**Independencia**:
- Bot NO lee session_state
- Vista NO afecta user_config.json (hasta presionar GUARDAR MISIÓN)

---

## Troubleshooting

### Problema: "El bot no ejecuta la estrategia que veo en pantalla"

**Diagnóstico**: Confusión entre Vista y Misión del Bot

**Solución**: Verificar indicador de sincronización. Si dice `Vista: ÉLITE | Bot: ROMPEOLAS`, es correcto que el bot ignore Élite.

---

### Problema: "La tabla no muestra datos"

**Checklist**:
1. ¿Credenciales de Alpaca configuradas en Secrets?
2. ¿Watchlist del bot tiene tickers válidos?
3. ¿Mercado está abierto o usando datos IEX?

---

### Problema: "Al guardar misión, no se sincroniza con GitHub"

**Checklist**:
1. ¿GITHUB_TOKEN configurado en Secrets?
2. ¿GITHUB_REPO tiene formato "usuario/repo"?
3. ¿Token tiene permisos de escritura (scope: repo)?

---

## Futuras Mejoras

### Fase 1: Gráficos Interactivos
- Agregar Plotly charts con indicadores visuales
- Mostrar entrada/salida histórica del bot

### Fase 2: Backtesting
- Panel de backtesting de estrategias
- Comparación de rendimiento Larry vs Wyckoff vs Élite

### Fase 3: Alertas
- Notificaciones cuando bot ejecuta orden
- Webhook a Discord/Telegram

---

## Convenciones de Código

### Nombres de Funciones
- `render_*()`: Funciones que muestran UI
- `generate_*()`: Funciones que calculan señales
- `load_*()` / `save_*()`: Funciones de persistencia

### Colores de Señales
- CALL: `#10B981` (Verde Emerald)
- SELL: `#EF4444` (Rojo Crimson)
- WATCH: `#F59E0B` (Naranja Ámbar)
- NEUTRAL: `#6B7280` (Gris Neutro)

### Emojis Estándar
- 🤖 Bot / Automatización
- 👁️ Vista / Visualización
- 🎯 Estrategia / Objetivo
- 📊 Datos / Análisis
- 💾 Guardar / Persistencia
- 🔄 Actualizar / Refresh
