# RESEARCH.md - Frameworks Investigados

Este documento resume los frameworks de trading investigados para TradeOlympo y las decisiones de arquitectura tomadas.

---

## 🔍 Frameworks Investigados

### 1. **OpenBB (Dark Pools & Advanced Analytics)**

**Propósito**: Análisis de Dark Pools, flujo institucional, y datos alternativos.

**Características**:
- Acceso a datos de Dark Pools y transacciones institucionales
- Integración con múltiples proveedores de datos (Bloomberg Terminal-like)
- Análisis fundamental avanzado (ratios, earnings, insider trading)
- Visualizaciones profesionales con matplotlib/plotly

**Decisión**: **NO IMPLEMENTADO**

**Razones**:
- **Complejidad**: OpenBB requiere configuración extensa y múltiples API keys
- **Overhead**: Librerías pesadas (500+ MB) para funcionalidad que no usamos
- **Scope creep**: TradeOlympo se enfoca en volumen y tendencia, no en flujos institucionales complejos
- **Alternativa**: Alpha Vantage provee datos OHLCV suficientes para análisis Wyckoff

---

### 2. **VectorBT (Backtesting Rápido)**

**Propósito**: Backtesting vectorizado ultra-rápido de estrategias de trading.

**Características**:
- Backtesting 100-1000x más rápido que frameworks tradicionales
- Optimización de parámetros con búsqueda exhaustiva
- Visualizaciones interactivas de resultados
- Soporte para múltiples instrumentos y timeframes

**Decisión**: **NO IMPLEMENTADO (aún)**

**Razones para NO incluir ahora**:
- **Scope**: TradeOlympo v1.0 es un **scanner de señales**, no un backtester
- **Complejidad**: VectorBT tiene curva de aprendizaje pronunciada
- **Performance**: Streamlit no es ideal para backtests intensivos (mejor Jupyter)

**Consideración futura**:
- **v2.0**: Añadir módulo de backtesting para validar Larry Williams y Wyckoff
- **Implementación**: Crear notebook separado (.ipynb) para backtests offline
- **Métricas objetivo**: Sharpe Ratio, Max Drawdown, Win Rate de señales

---

### 3. **Pandas-TA (Robustez de Indicadores)**

**Propósito**: Librería de ~130 indicadores técnicos pre-construidos y optimizados.

**Características**:
- Williams %R, Wyckoff Volume, MACD, RSI, Bollinger Bands
- Cálculos vectorizados (más rápidos que implementación manual)
- API consistente para todos los indicadores
- Validación automática de datos (manejo de NaN)

**Decisión**: **NO IMPLEMENTADO (evaluando)**

**Razones para implementación custom**:
- **Control total**: Nuestra implementación de Williams y Wyckoff es transparente
- **Personalización**: Podemos ajustar exactamente cómo calculamos cada indicador
- **Educación**: Código explícito ayuda a entender la lógica de trading
- **Zero dependencies**: Menos dependencias = menos riesgo de breaking changes

**Razones para considerar Pandas-TA**:
- **Robustez**: Código battle-tested usado por miles de traders
- **Mantenimiento**: Actualizaciones automáticas cuando hay bugs
- **Expansión**: Fácil añadir nuevos indicadores (RSI, MACD, etc.) sin código manual

**Recomendación**: **Mantener implementación custom por ahora, migrar a Pandas-TA en v2.0 si escalamos a +10 indicadores**.

---

## 🎯 Filosofía de Diseño: Minimalista & Enfocado

### Principio Core
**"Mantener la app minimalista: solo volumen y tendencia"**

### Qué NO hacer:
- ❌ No añadir 50 indicadores técnicos (confunde al usuario)
- ❌ No implementar ML/AI sin backtesting riguroso
- ❌ No integrar Dark Pools hasta tener estrategia clara para usarlos
- ❌ No crear backtester en Streamlit (usar Jupyter separado)

### Qué SÍ hacer:
- ✅ **Volumen Wyckoff**: Detectar acumulación/distribución institucional
- ✅ **Tendencia Williams**: Momentum con medias móviles
- ✅ **Gestión de Riesgo**: Stop Loss, Take Profit, límite de capital
- ✅ **UX Simple**: Mobile-first, 1 señal clara, 3 segundos para decidir

---

## 📊 Stack Tecnológico Final (v1.0)

```python
# Core
streamlit==1.31.0          # UI framework
alpha-vantage==2.3.1       # Data real (5 calls/min gratis)
plotly==5.18.0             # Gráficos interactivos oscuros

# Data processing
pandas==2.2.0              # DataFrames
numpy==1.26.3              # Cálculos numéricos

# Indicadores
# Custom implementation    # Williams %R, Wyckoff Volume (control total)

# Cache
requests-cache==1.1.1      # Evita rate limits
@st.cache_data(ttl=3600)   # Cache Streamlit 1h
```

---

## 🔮 Roadmap Futuro (v2.0+)

### Prioridades
1. **Backtesting con VectorBT** (notebook separado)
   - Validar señales Larry Williams last 10 years
   - Optimizar parámetros Williams %R (14 días vs 21 días)
   - Sharpe Ratio objetivo: >1.5

2. **Migración a Pandas-TA** (si > 10 indicadores)
   - Añadir RSI, MACD, Bollinger Bands
   - Comparar performance custom vs Pandas-TA

3. **Integración OpenBB** (solo si necesitamos Dark Pools)
   - Requiere justificación: ¿mejora win rate en +10%?
   - Análisis costo/beneficio de múltiples APIs

---

## 📚 Referencias

- **OpenBB**: https://github.com/OpenBB-finance/OpenBBTerminal
- **VectorBT**: https://github.com/polakowo/vectorbt
- **Pandas-TA**: https://github.com/twopirllc/pandas-ta
- **Alpha Vantage**: https://www.alphavantage.co/documentation/
- **Larry Williams**: "Long-Term Secrets to Short-Term Trading" (libro)
- **Wyckoff Method**: https://school.stockcharts.com/doku.php?id=market_analysis:the_wyckoff_method

---

**Última actualización**: 2026-01-04
**Decisión Core**: Minimalismo > Complejidad. Volumen y Tendencia antes que ML y Dark Pools.
