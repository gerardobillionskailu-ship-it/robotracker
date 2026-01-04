# 📈 TradeOlympo

**Análisis Financiero Avanzado para Traders**

TradeOlympo es una aplicación web interactiva que combina análisis técnico tradicional con metodologías avanzadas para identificar oportunidades de trading en el mercado de acciones.

## ✨ Características

- **Múltiples Estrategias de Análisis**
  - Larry Williams: Williams %R y cruces de medias móviles
  - Wyckoff: Análisis de volumen y detección de acumulación/distribución

- **Watchlist Personalizado**
  - Monitoreo de CVX, SLB, HAL, XLE
  - Métricas en tiempo real
  - Noticias relevantes

- **Visualizaciones Interactivas**
  - Gráficos de velas con Plotly
  - Indicadores superpuestos
  - Análisis de volumen

- **Sugerencias de Estrategias Cash**
  - Recomendaciones para cuentas Cash
  - Enfoque en Long Calls y compra de acciones
  - Sin estrategias de margen

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd robotracker
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv

   # En Windows:
   venv\Scripts\activate

   # En Mac/Linux:
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   streamlit run app.py
   ```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📖 Guía de Uso

### Seleccionar Estrategia

En el **sidebar izquierdo**, elige entre:
- **Larry Williams**: Ideal para detectar momentum y tendencias
- **Wyckoff**: Perfecto para análisis de volumen y acumulación/distribución

### Analizar Símbolos

1. En la columna **Watchlist**, haz clic en el símbolo que deseas analizar
2. La **Tarjeta de Estrategia** (columna central) mostrará:
   - Señal de trading (BUY/SELL/HOLD)
   - Confianza de la señal (0-100%)
   - Razones del análisis
   - Estrategia recomendada

3. El **gráfico interactivo** muestra:
   - Precios históricos
   - Indicadores técnicos
   - Volumen (en modo Wyckoff, con colores especiales)

4. La columna de **Noticias** muestra artículos recientes del símbolo

### Interpretar Señales

- 🟢 **BUY**: Oportunidad de compra identificada
- 🔴 **SELL**: Considerar venta o evitar nuevas posiciones
- 🟡 **HOLD**: Sin señal clara, esperar

## 🎯 Estrategias Implementadas

### Larry Williams

**Indicadores:**
- Williams %R (período 14)
- SMA 20, 50, 200
- Golden Cross / Death Cross

**Señales:**
- Williams %R < -80: Sobreventa (posible compra)
- Williams %R > -20: Sobrecompra (precaución)
- Golden Cross: SMA 50 cruza por encima de SMA 200 (alcista)
- Death Cross: SMA 50 cruza por debajo de SMA 200 (bajista)

### Wyckoff

**Métricas:**
- Volumen relativo vs promedio 20 períodos
- Posición del cierre en la vela (0-100%)
- Detección de acumulación/distribución
- Análisis esfuerzo vs resultado

**Señales:**
- Volumen > 150% + cierre alto: Fortaleza alcista
- Volumen > 150% + cierre bajo: Debilidad bajista
- Patrones de acumulación: 3+ velas con fortaleza
- Patrones de distribución: 3+ velas con debilidad

## 📊 Estructura del Proyecto

```
robotracker/
├── app.py                 # Punto de entrada principal
├── requirements.txt       # Dependencias del proyecto
├── utils/
│   ├── __init__.py
│   └── indicators.py      # Cálculo de indicadores técnicos
├── views/
│   ├── __init__.py
│   └── dashboard.py       # UI y visualizaciones
├── .gitignore
└── README.md
```

## 🛠️ Tecnologías Utilizadas

- **Streamlit**: Framework web interactivo
- **yfinance**: Datos de mercado en tiempo real
- **Plotly**: Gráficos interactivos
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos
- **TA-Lib**: Indicadores técnicos

## ⚙️ Configuración

### Personalizar Watchlist

Edita `views/dashboard.py`:

```python
WATCHLIST_SYMBOLS = ['CVX', 'SLB', 'HAL', 'XLE', 'TU_SIMBOLO']
```

### Ajustar Períodos de Indicadores

Edita `utils/indicators.py` y modifica los parámetros en las funciones de cálculo.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Próximas Funcionalidades

- [ ] RSI (Relative Strength Index)
- [ ] MACD (Moving Average Convergence Divergence)
- [ ] Bandas de Bollinger
- [ ] Fibonacci Retracements
- [ ] Detección automática de patrones de velas
- [ ] Backtesting de estrategias
- [ ] Alertas por email/SMS
- [ ] Exportación de reportes PDF

## ⚠️ Disclaimer

Esta aplicación es solo para fines educativos e informativos. No constituye asesoramiento financiero. Siempre realiza tu propia investigación antes de tomar decisiones de inversión.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👨‍💻 Autor

Desarrollado con ❤️ para la comunidad de traders

---

**¿Preguntas o problemas?** Abre un issue en el repositorio.
