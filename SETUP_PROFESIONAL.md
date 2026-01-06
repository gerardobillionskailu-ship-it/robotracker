# 🚀 TradeOlympo v3.0 - Guía de Configuración Profesional

## 📋 Resumen de Cambios

✅ **Frontend Rediseñado**: Dark Mode profesional sin "Jueces"
✅ **Persistencia**: Configuración guardada en `user_config.json`
✅ **Sincronización**: La web guarda directamente en GitHub via PyGithub
✅ **Sin pandas-ta**: Bot usa funciones nativas (evita errores de dependencias)

---

## 🔧 Paso 1: Configurar GitHub Token

Para que la web pueda guardar la configuración en GitHub, necesitas un **Personal Access Token**.

### 1.1 Crear Token en GitHub

1. Ve a: https://github.com/settings/tokens
2. Click en **"Generate new token"** → **"Generate new token (classic)"**
3. Nombre: `TradeOlympo-WebSync`
4. Scopes necesarios:
   - ✅ `repo` (acceso completo al repositorio)
5. Click **"Generate token"**
6. **¡COPIA EL TOKEN!** (solo se muestra una vez)

### 1.2 Configurar en Streamlit Cloud

1. Ve a tu app en Streamlit Cloud
2. Click en **Settings** (⚙️)
3. Click en **Secrets**
4. Pega esto (reemplaza con tus valores):

```toml
GITHUB_TOKEN = "ghp_TU_TOKEN_AQUI"
GITHUB_REPO = "tu-usuario/robotracker"
```

5. Click **Save**

---

## 📁 Paso 2: Verificar Archivos

### Archivos Nuevos Creados:

```
user_config.json              ← Configuración centralizada
app.py                        ← Frontend rediseñado (Dark Mode)
requirements.txt              ← Actualizado (con PyGithub, SIN pandas-ta)
.streamlit/secrets.toml       ← Template de secrets
SETUP_PROFESIONAL.md          ← Este archivo
```

### Estructura de `user_config.json`:

```json
{
  "active_strategy": "rompeolas",
  "watchlist": ["XLE", "OXY", "APA", "CVX"],
  "last_updated": "2026-01-06T00:00:00",
  "strategies": {
    "elite": {
      "name": "Estrategia Élite",
      "default_tickers": ["NVDA", "TSLA", "AMD"]
    },
    "rompeolas": {
      "name": "Estrategia Rompeolas",
      "default_tickers": ["XLE", "OXY", "CVX"]
    }
  }
}
```

---

## 🎨 Paso 3: Usar la Nueva Interfaz

### Panel Superior: Estado del Bot
- **Estrategia Activa**: Muestra qué estrategia está ejecutando el bot
- **Tickers en Vigilancia**: Cantidad de stocks monitoreados
- **Última Actualización**: Timestamp del último cambio

### Panel Izquierdo: Configurar Bot
1. **Seleccionar Estrategia**:
   - 🏆 **Élite**: Reversión a la media (Tech stocks)
   - 🌊 **Rompeolas**: Breakout de energía

2. **Editar Watchlist**:
   - Escribe tickers separados por comas: `NVDA, TSLA, AAPL`
   - O click en **"Cargar Tickers por Defecto"**

3. **Guardar**:
   - Click en **💾 GUARDAR**
   - Si GitHub Token está configurado: se sincroniza automáticamente
   - Si no: se guarda localmente (debes commitear manual)

### Panel Derecho: Análisis
- Muestra las últimas señales del bot (`last_run_results.json`)
- **Verde**: Señales de CALL (compra)
- **Rojo**: Señales de SELL (venta)
- **Gris**: Señales neutrales

---

## 🤖 Paso 4: Flujo de Trabajo

### Desde la Web:
1. Entra a `https://tu-app.streamlit.app`
2. Selecciona estrategia y tickers
3. Click **💾 GUARDAR**
4. ✅ Se guarda en GitHub automáticamente

### En GitHub Actions:
1. El bot ejecuta (cada hora de 9am-4pm EST)
2. Lee `user_config.json` del repo
3. Aplica la estrategia y watchlist configurada
4. Guarda resultados en `last_run_results.json`

### Volver a la Web:
1. Refresca la página
2. El panel **"Últimas Señales del Bot"** muestra los resultados

---

## 🔍 Paso 5: Verificación

### Test Manual del Bot:

```bash
# En tu máquina local
python bot.py
```

**Salida esperada:**
```
==================================================
🤖 INICIANDO TRADEOLYMPO AUTO-BOT (Modular)
📅 Fecha: 2026-01-06 09:00:00 ET
📋 Estrategia activa: rompeolas
==================================================
✅ Configuración cargada desde user_config.json
   Estrategia activa: rompeolas
   Última actualización: 2026-01-06T00:00:00

📋 Tickers a analizar (8): XLE, OXY, APA, CVX, COP, SLB, HAL, VLO
...
```

### Test de la Web (Local):

```bash
streamlit run app.py
```

Deberías ver:
- ✅ Panel superior con métricas
- ✅ Botones de estrategia funcionando
- ✅ Editor de watchlist
- ✅ Botón GUARDAR (muestra warning si no hay GitHub Token local)

---

## ⚠️ IMPORTANTE: Dependencias

### ✅ Lo que SÍ está incluido:

```txt
PyGithub==2.1.1               ← Sincronización con GitHub
alpaca-trade-api==3.0.2       ← Datos de mercado
streamlit==1.31.0             ← Framework web
```

### ❌ Lo que NO está (y por qué):

- **pandas-ta**: Causa `ModuleNotFoundError` en Python 3.9
- **yfinance**: No se usa, datos vienen de Alpaca API

### Cálculo de Indicadores:

El bot usa **funciones nativas** en `bot.py`:

```python
def calcular_rsi(series, period=14):
    """Calcula RSI usando pandas nativo (sin pandas-ta)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_sma(series, window):
    """Calcula SMA usando pandas nativo (sin pandas-ta)"""
    return series.rolling(window=window).mean()
```

**✅ Estas funciones funcionan perfectamente sin dependencias adicionales.**

---

## 🚨 Solución de Problemas

### Problema: "Error guardando en GitHub"

**Causa**: Token no configurado o sin permisos

**Solución**:
1. Verifica que el token tenga scope `repo`
2. Verifica el formato en secrets: `GITHUB_TOKEN` y `GITHUB_REPO`
3. El repo name debe ser: `usuario/nombre-repo` (sin .git)

### Problema: "ModuleNotFoundError: pandas_ta"

**Causa**: Alguien agregó pandas_ta a requirements.txt

**Solución**:
```bash
# Elimina esta línea de requirements.txt:
# pandas-ta==0.3.14b0

# El bot ya tiene funciones nativas, no necesita pandas_ta
```

### Problema: "Watchlist vacía después de refrescar"

**Causa**: No se guardó en GitHub, solo localmente

**Solución**:
- Configura GitHub Token en Streamlit Secrets
- O commitea manualmente `user_config.json`

---

## 📊 Comparación: Antes vs Ahora

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **UI** | Tarjetas de colores neón con "Jueces" | Dark Mode profesional con métricas |
| **Persistencia** | Ninguna (perdías cambios) | `user_config.json` sincronizado con GitHub |
| **Configuración** | Hardcodeada en bot.py | Editable desde la web |
| **Dependencias** | Intentaba usar pandas-ta (fallaba) | Funciones nativas (funciona) |
| **Sincronización** | Manual (editar código) | Automática (PyGithub) |

---

## ✅ Checklist Final

- [ ] GitHub Token creado
- [ ] Token configurado en Streamlit Secrets
- [ ] `user_config.json` committeado al repo
- [ ] Bot ejecuta sin errores: `python bot.py`
- [ ] Web carga correctamente: `streamlit run app.py`
- [ ] Botón GUARDAR funciona y sincroniza
- [ ] GitHub Actions ejecuta sin errores

---

## 🎯 Próximos Pasos

Ahora que el sistema está configurado:

1. **Prueba cambiar estrategias** desde la web
2. **Monitorea los logs** del bot en GitHub Actions
3. **Revisa las señales** en el panel de Análisis
4. **Ajusta la watchlist** según tus preferencias

**¡Tu sistema está listo para trading profesional! 🚀**

---

## 📞 Soporte

Si algo no funciona:
1. Revisa los logs del bot: `bot_logs.txt`
2. Revisa los logs de GitHub Actions
3. Verifica que `user_config.json` se haya actualizado en el repo

**Recuerda**: El bot NO usa pandas-ta. Usa funciones nativas. Si ves errores de pandas-ta, alguien lo agregó incorrectamente.
