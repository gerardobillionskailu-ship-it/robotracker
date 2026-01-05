# TradeOlympo - Configuración de Secrets

Este documento explica cómo configurar correctamente los secrets para el proyecto TradeOlympo.

## 🔐 Resumen de Secrets

TradeOlympo usa **DOS conjuntos separados** de secrets para funciones diferentes:

---

## 1️⃣ GitHub Secrets (Para Bot de Trading Automático)

**Ubicación**: GitHub Repository → Settings → Secrets and variables → Actions

**Propósito**: Permitir que el bot de trading automático (`bot.py`) ejecute operaciones en Alpaca Markets.

### Secrets Requeridos:

| Secret Name | Descripción | Ejemplo |
|------------|-------------|---------|
| `ALPACA_API_KEY` | API Key de Alpaca Paper Trading | `PK...` |
| `ALPACA_SECRET_KEY` | Secret Key de Alpaca | `...` |
| `ALPACA_ENDPOINT` | Endpoint de Alpaca | `https://paper-api.alpaca.markets` |

### Cómo Configurar:

1. Ve a tu repositorio en GitHub
2. Click en **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Agrega cada uno de los 3 secrets arriba

### Cómo Obtener las Keys de Alpaca:

1. Regístrate en [Alpaca Markets](https://alpaca.markets/)
2. Ve a **Paper Trading** (cuenta demo)
3. Genera tus API keys
4. Copia `API Key ID` y `Secret Key`

---

## 2️⃣ Streamlit Secrets (Para App Web de Análisis)

**Ubicación**: Streamlit Cloud → App Settings → Secrets

**Propósito**: Permitir que la app web de TradeOlympo obtenga datos de mercado de Alpha Vantage.

### Secrets Requeridos:

```toml
ALPHAVANTAGE_API_KEY = "tu_api_key_aqui"
```

### Cómo Configurar:

1. Ve a [Streamlit Cloud](https://share.streamlit.io/)
2. Selecciona tu app **TradeOlympo**
3. Click en **⚙️ Settings** → **Secrets**
4. Pega el contenido arriba (formato TOML)

### Cómo Obtener Alpha Vantage API Key:

1. Regístrate en [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Copia tu API key gratuita
3. Pégala en los secrets de Streamlit

---

## ❓ Preguntas Frecuentes

### ¿Por qué dos conjuntos de secrets?

- **Alpaca** = Trading automático (bot ejecuta operaciones reales)
- **Alpha Vantage** = Análisis de mercado (app web muestra datos y estrategias)

Son servicios diferentes para propósitos diferentes.

### ¿Puedo usar Alpaca en la app web?

No es necesario. La app web de Streamlit solo analiza y sugiere estrategias. El bot automático es quien ejecuta las operaciones.

### ¿Los secrets de GitHub afectan a Streamlit?

No. Los secrets de GitHub Actions solo están disponibles para el bot que corre en GitHub. La app de Streamlit Cloud tiene su propio sistema de secrets separado.

### ¿Es seguro?

Sí. Los secrets nunca se exponen en el código fuente ni en los logs públicos. GitHub y Streamlit los encriptan.

---

## 🚀 Verificación

### Para verificar GitHub Secrets (Bot):

1. Ve a **Actions** en GitHub
2. Click en **TradeOlympo Auto-Bot**
3. Click **Run workflow** → **Run workflow**
4. Verifica que no haya errores de autenticación

### Para verificar Streamlit Secrets (App Web):

1. Abre tu app en Streamlit Cloud
2. Selecciona un ticker
3. Verifica que los datos se carguen correctamente (sin error de API)

---

## 📝 Notas Importantes

- **Nunca** compartas tus API keys públicamente
- Usa **Paper Trading** de Alpaca para pruebas (no dinero real)
- Alpha Vantage Free Tier: 5 requests por minuto, 500 por día
- El bot solo opera durante horarios de mercado (9:30am-4pm EST)

---

## 🛠️ Troubleshooting

### Error: "ALPACA_API_KEY not found"
→ Verifica que configuraste los 3 secrets en GitHub Actions (no en Streamlit)

### Error: "Alpha Vantage API limit reached"
→ Activa el "Modo Simulación" en el sidebar de la app

### Bot no ejecuta operaciones
→ Verifica que el mercado esté abierto (Lun-Vie, 9:30am-4pm EST)

---

Última actualización: 2026-01-05
