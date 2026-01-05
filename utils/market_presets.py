"""
TradeOlympo - Market Presets
Listas pre-configuradas de acciones de alta calidad por sector

Criterios de selección:
- Blue Chips con capitalización > $10B
- Volumen diario promedio > 1M acciones
- Liquidez suficiente para opciones
- Empresas reconocidas con historia comprobada
"""

# ========== PRESETS DE MERCADO ==========

PRESETS = {
    "🛢️ Energía & Petróleo": [
        "XOM",    # ExxonMobil - Súper Major
        "CVX",    # Chevron - Súper Major
        "COP",    # ConocoPhillips - E&P líder
        "SLB",    # Schlumberger - Servicios petroleros
        "HAL",    # Halliburton - Servicios petroleros
        "VLO",    # Valero - Refinación
        "OXY",    # Occidental - E&P diversificado
        "MPC",    # Marathon Petroleum - Refinación
        "PSX",    # Phillips 66 - Downstream
        "BKR"     # Baker Hughes - Equipos y servicios
    ],

    "💻 Big Tech & AI": [
        "NVDA",   # NVIDIA - GPUs y AI chips
        "MSFT",   # Microsoft - Cloud + AI
        "AAPL",   # Apple - Consumer tech
        "GOOGL",  # Alphabet - Search + Cloud + AI
        "META",   # Meta - Social media + VR
        "AMZN",   # Amazon - E-commerce + AWS
        "TSLA",   # Tesla - EVs + Energy + AI
        "AMD",    # AMD - Semiconductores
        "AVGO",   # Broadcom - Semiconductores
        "ORCL"    # Oracle - Database + Cloud
    ],

    "₿ Crypto Proxies": [
        "MSTR",   # MicroStrategy - Bitcoin treasury
        "COIN",   # Coinbase - Crypto exchange
        "MARA",   # Marathon Digital - Bitcoin mining
        "RIOT",   # Riot Platforms - Bitcoin mining
        "IBIT",   # BlackRock Bitcoin ETF
        "CLSK",   # CleanSpark - Bitcoin mining
        "HUT"     # Hut 8 Mining - Bitcoin mining
    ],

    "🏦 Finanzas & Bancos": [
        "JPM",    # JPMorgan Chase - Banco universal #1
        "BAC",    # Bank of America - Retail banking
        "WFC",    # Wells Fargo - Retail banking
        "GS",     # Goldman Sachs - Investment banking
        "MS",     # Morgan Stanley - Wealth management
        "C",      # Citigroup - Banco global
        "V",      # Visa - Payment networks
        "MA",     # Mastercard - Payment networks
        "AXP",    # American Express - Tarjetas
        "BLK"     # BlackRock - Asset management
    ],

    "🛡️ Defensa & Aero": [
        "LMT",    # Lockheed Martin - Defensa #1
        "RTX",    # Raytheon Technologies - Defensa
        "GD",     # General Dynamics - Defensa
        "NOC",    # Northrop Grumman - Defensa
        "BA",     # Boeing - Aeroespacial comercial
        "HWM",    # Howmet Aerospace - Componentes
        "TDG",    # TransDigm - Componentes aeroespaciales
        "LHX"     # L3Harris - Defensa electrónica
    ],

    "💊 Pharma & Healthcare": [
        "JNJ",    # Johnson & Johnson - Healthcare diversificado
        "UNH",    # UnitedHealth - Seguros de salud
        "PFE",    # Pfizer - Farmacéutica
        "ABBV",   # AbbVie - Biofarmacéutica
        "MRK",    # Merck - Farmacéutica
        "LLY",    # Eli Lilly - Diabetes + Oncología
        "TMO",    # Thermo Fisher - Instrumentación
        "ABT",    # Abbott Labs - Dispositivos médicos
        "AMGN",   # Amgen - Biotecnología
        "BMY"     # Bristol Myers Squibb - Oncología
    ],

    "🏭 Industriales & Manufactura": [
        "CAT",    # Caterpillar - Maquinaria pesada
        "DE",     # Deere - Equipos agrícolas
        "GE",     # General Electric - Conglomerado
        "HON",    # Honeywell - Tecnología industrial
        "MMM",    # 3M - Productos industriales
        "EMR",    # Emerson Electric - Automatización
        "ETN",    # Eaton - Gestión de energía
        "ITW",    # Illinois Tool Works - Fabricación
        "CMI",    # Cummins - Motores diesel
        "PH"      # Parker-Hannifin - Motion control
    ],

    "🛒 Retail & Consumer": [
        "WMT",    # Walmart - Retail masivo
        "COST",   # Costco - Retail por membresía
        "HD",     # Home Depot - Mejoras del hogar
        "TGT",    # Target - Retail diversificado
        "LOW",    # Lowe's - Mejoras del hogar
        "MCD",    # McDonald's - Fast food
        "SBUX",   # Starbucks - Café
        "NKE",    # Nike - Ropa deportiva
        "KO",     # Coca-Cola - Bebidas
        "PEP"     # PepsiCo - Alimentos y bebidas
    ],

    "🇻🇪 Venezuela Recovery": [
        "CVX",    # Chevron - Licencia para operar en Venezuela
        "SLB",    # Schlumberger - Servicios en LATAM
        "HAL",    # Halliburton - Servicios en LATAM
        "BKR",    # Baker Hughes - Equipos
        "COP",    # ConocoPhillips - E&P global
        "VLO",    # Valero - Refinación de crudo pesado
        "WFRD",   # Weatherford - Servicios petroleros
        "XLE"     # Energy Select Sector ETF
    ],

    "🚀 Growth & Momentum": [
        "NVDA",   # NVIDIA - AI líder
        "META",   # Meta - Turnaround story
        "TSLA",   # Tesla - EV líder
        "AMD",    # AMD - Semiconductores
        "AVGO",   # Broadcom - Semiconductores
        "COIN",   # Coinbase - Crypto exposure
        "PLTR",   # Palantir - AI software
        "SHOP",   # Shopify - E-commerce platform
        "SQ",     # Block - Fintech
        "CRWD"    # CrowdStrike - Cybersecurity
    ]
}

# ========== FUNCIONES DE UTILIDAD ==========

def get_preset_names():
    """Retorna lista de nombres de presets disponibles"""
    return list(PRESETS.keys())

def get_preset_tickers(preset_name):
    """Retorna lista de tickers para un preset específico"""
    return PRESETS.get(preset_name, [])

def get_all_unique_tickers():
    """Retorna set de todos los tickers únicos en todos los presets"""
    all_tickers = set()
    for tickers in PRESETS.values():
        all_tickers.update(tickers)
    return sorted(list(all_tickers))

def get_preset_count():
    """Retorna número total de presets disponibles"""
    return len(PRESETS)

def validate_preset(preset_name):
    """Verifica si un preset existe"""
    return preset_name in PRESETS

# ========== METADATA ==========

PRESET_METADATA = {
    "total_presets": len(PRESETS),
    "total_unique_tickers": len(get_all_unique_tickers()),
    "categories": [
        "Energía",
        "Tecnología",
        "Criptomonedas",
        "Finanzas",
        "Defensa",
        "Healthcare",
        "Industriales",
        "Retail",
        "Temáticas"
    ]
}
