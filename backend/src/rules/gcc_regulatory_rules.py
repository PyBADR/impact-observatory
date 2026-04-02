"""GCC regulatory rules — cross-sector compliance framework.

Central registry of regulatory bodies and their jurisdiction thresholds.
Used by decision_service.py to assess regulatory_risk per action.
"""

from __future__ import annotations

# GCC Central Banks and Regulators
REGULATORS = {
    "SAMA": {
        "name_en": "Saudi Arabian Monetary Authority",
        "name_ar": "مؤسسة النقد العربي السعودي",
        "country": "SA",
        "jurisdiction": ["banking", "insurance", "fintech"],
        "car_requirement_pct": 12.0,
        "lcr_requirement_pct": 100.0,
    },
    "CBUAE": {
        "name_en": "Central Bank of UAE",
        "name_ar": "مصرف الإمارات المركزي",
        "country": "AE",
        "jurisdiction": ["banking", "insurance", "fintech"],
        "car_requirement_pct": 13.0,
        "lcr_requirement_pct": 100.0,
    },
    "QCB": {
        "name_en": "Qatar Central Bank",
        "name_ar": "مصرف قطر المركزي",
        "country": "QA",
        "jurisdiction": ["banking", "insurance"],
        "car_requirement_pct": 12.5,
        "lcr_requirement_pct": 100.0,
    },
    "CBK": {
        "name_en": "Central Bank of Kuwait",
        "name_ar": "بنك الكويت المركزي",
        "country": "KW",
        "jurisdiction": ["banking", "insurance"],
        "car_requirement_pct": 13.0,
        "lcr_requirement_pct": 100.0,
    },
    "CBB": {
        "name_en": "Central Bank of Bahrain",
        "name_ar": "مصرف البحرين المركزي",
        "country": "BH",
        "jurisdiction": ["banking", "insurance", "fintech"],
        "car_requirement_pct": 12.5,
        "lcr_requirement_pct": 100.0,
    },
    "CBO": {
        "name_en": "Central Bank of Oman",
        "name_ar": "البنك المركزي العماني",
        "country": "OM",
        "jurisdiction": ["banking", "insurance"],
        "car_requirement_pct": 12.0,
        "lcr_requirement_pct": 100.0,
    },
    "CMA_SA": {
        "name_en": "Capital Market Authority (Saudi)",
        "name_ar": "هيئة السوق المالية",
        "country": "SA",
        "jurisdiction": ["capital_markets"],
    },
    "SCA_AE": {
        "name_en": "Securities and Commodities Authority (UAE)",
        "name_ar": "هيئة الأوراق المالية والسلع",
        "country": "AE",
        "jurisdiction": ["capital_markets"],
    },
}

# Regulatory risk scoring: what happens if a decision is NOT taken
REGULATORY_RISK_WEIGHTS = {
    "banking": {
        "car_breach": 0.9,          # Regulator will intervene
        "lcr_breach": 0.8,          # Liquidity crisis triggers central bank action
        "interbank_contagion": 0.7,  # Systemic risk attracts regulatory scrutiny
    },
    "insurance": {
        "solvency_breach": 0.85,     # Insurance authority intervention
        "ifrs17_misstatement": 0.75, # Audit and compliance failure
        "reinsurance_failure": 0.70, # Market confidence collapse
    },
    "fintech": {
        "payment_system_failure": 0.80,  # Central bank mandates DR activation
        "cross_border_disruption": 0.65, # SWIFT/correspondent banking regulatory risk
        "data_breach": 0.70,             # Data protection regulatory action
    },
}

# Notification obligations (hours to report to regulator)
NOTIFICATION_DEADLINES_HOURS = {
    "material_loss": 24,        # Material loss > threshold must be reported in 24h
    "capital_breach": 4,        # CAR breach: immediate (within 4h)
    "cyber_incident": 2,        # Cyber: within 2h (GCC mandates)
    "payment_disruption": 6,    # Payment system: within 6h
    "reinsurance_trigger": 48,  # Reinsurance activation: within 48h
}
