"""
GCC Knowledge Graph Constants
Definitions matching frontend/lib/gcc-constants.ts exactly.
"""

# Economic base values in billions USD
BASES = {
    "oilRevenue": 540,
    "tourismRevenue": 85,
    "airportPax": 350,
    "portTEU": 45,
    "shippingCost": 12,
    "insurancePremium": 28,
    "aviationFuel": 42,
    "baseTicket": 320,
    "bankingAssets": 2800,
    "cbReserves": 780,
    "swfAssets": 3500,
    "gccGDP": 2100,
    "powerCapacity": 180,
    "desalCapacity": 22,
    "foodImports": 48,
    "hajjRevenue": 12,
    "fdiInflows": 35,
    "vision2030Budget": 1300,
}

# Sector GDP base values in billions USD
# - Geography: 0 (spatial layer, no direct GDP)
# - Infrastructure: $210B (ports, airports, utilities, telecom — ~10% GDP)
# - Economy: $950B (oil $540B + non-oil $410B — ~45% GDP)
# - Finance: $380B (banking, insurance, capital markets — ~18% GDP)
# - Society: $160B (consumer services, tourism demand, employment — ~8% GDP)
SECTOR_GDP_BASE = {
    "geography": 0,
    "infrastructure": 210,
    "economy": 950,
    "finance": 380,
    "society": 160,
}

# Hormuz Strait shock multipliers
HORMUZ_MULTIPLIERS = {
    "oilDrop": 0.85,
    "shipSpike": 1.2,
    "insSpike": 1.5,
    "avFuel": 0.6,
    "tourDrop": 0.45,
    "gdpMultiplier": 0.65,
}

# Disruption Propagation Score (DPS) weights
DPS_WEIGHTS = {
    "systemEnergy": 0.25,
    "propagationDepth": 0.15,
    "sectorSpread": 0.20,
    "exposureScore": 0.25,
    "stabilityRisk": 0.15,
}

# DPS normalization denominators
DPS_NORMALIZATION = {
    "energy": 15,
    "depth": 8,
    "spread": 5,
    "exposure": 80,
    "stability": 1,
}

# Adaptive Propagation Strategy (APS) cost multiplier by spread level
APS_COST_MULTIPLIER = {
    "low": 1.0,
    "medium": 0.7,
    "high": 0.4,
}

# Decision validation limits
DECISION_LIMITS = {
    "maxMarginalEffectiveness": 0.85,
    "minDataReliability": 0.3,
    "minScenarioCoherence": 0.4,
}

# Physics constants for system dynamics
PHYSICS = {
    "mu1": 0.35,
    "rho": 0.72,
    "alpha": 0.58,
    "beta": 0.92,
}

# Asset class weights for each infrastructure type (across 6 GCC states)
GCC_ASSET_WEIGHTS = {
    "airports": [0.27, 0.16, 0.19, 0.17, 0.11, 0.10],
    "seaports": [0.24, 0.14, 0.22, 0.23, 0.09, 0.08],
    "oilgas": [0.30, 0.12, 0.18, 0.15, 0.13, 0.12],
    "power": [0.20, 0.18, 0.22, 0.15, 0.12, 0.13],
    "telecom": [0.15, 0.20, 0.25, 0.12, 0.14, 0.14],
    "finance": [0.18, 0.15, 0.20, 0.22, 0.15, 0.10],
    "tourism": [0.25, 0.18, 0.15, 0.12, 0.18, 0.12],
}

# Monte Carlo simulation parameters
MONTE_CARLO = {
    "defaultRuns": 500,
    "weightNoise": 0.1,
    "severityMin": 0.7,
    "severityMax": 1.3,
}

# Layer metadata
LAYER_LABELS = {
    "geography": {"en": "Geography", "ar": "الجغرافيا"},
    "infrastructure": {"en": "Infrastructure", "ar": "البنية التحتية"},
    "economy": {"en": "Economy", "ar": "الاقتصاد"},
    "finance": {"en": "Finance", "ar": "المالية"},
    "society": {"en": "Society", "ar": "المجتمع"},
}

LAYER_COLORS = {
    "geography": "#2DD4A0",
    "infrastructure": "#F5A623",
    "economy": "#5B7BF8",
    "finance": "#A78BFA",
    "society": "#EF5454",
}

# Spread level translations
SPREAD_LABELS = {
    "low": "منخفض",
    "medium": "متوسط",
    "high": "مرتفع",
    "critical": "حرج",
}
