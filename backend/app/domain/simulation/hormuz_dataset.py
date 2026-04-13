"""
Impact Observatory | مرصد الأثر — Phase 1 Hormuz Dataset
Real GCC macro-financial parameters for Strait of Hormuz disruption.

Sources (calibrated to public IMF/GCC central-bank data):
  - Oil dependency: IMF Article IV consultations + OPEC Bulletin
  - Banking liquidity: GCC central bank annual reports
  - Insurance penetration: SAMA, CBUAE, CBK annual reports
  - GDP composition: World Bank WDI + national statistics offices

All weights are deterministic. No randomness, no ML inference.
Shock vectors are initialized from empirical GCC exposure ratios.
"""
from __future__ import annotations

from app.domain.simulation.graph_types import Edge, NodeId

# ═══════════════════════════════════════════════════════════════════════════════
# Country Metadata
# ═══════════════════════════════════════════════════════════════════════════════

COUNTRY_META: dict[str, dict] = {
    "KWT": {
        "name": "Kuwait",
        "name_ar": "الكويت",
        "gdp_usd": 184.0e9,
        "oil_gdp_share": 0.52,
        "hormuz_dependency": 0.95,   # virtually all exports via Hormuz
        "banking_assets_usd": 290.0e9,
        "insurance_penetration": 0.011,
        "fintech_maturity": 0.35,
        "real_estate_share": 0.07,
    },
    "SAU": {
        "name": "Saudi Arabia",
        "name_ar": "المملكة العربية السعودية",
        "gdp_usd": 1069.0e9,
        "oil_gdp_share": 0.42,
        "hormuz_dependency": 0.15,   # East–West pipeline alternative
        "banking_assets_usd": 960.0e9,
        "insurance_penetration": 0.018,
        "fintech_maturity": 0.55,
        "real_estate_share": 0.08,
    },
    "UAE": {
        "name": "United Arab Emirates",
        "name_ar": "الإمارات العربية المتحدة",
        "gdp_usd": 507.0e9,
        "oil_gdp_share": 0.30,
        "hormuz_dependency": 0.60,   # Fujairah bypass partially mitigates
        "banking_assets_usd": 880.0e9,
        "insurance_penetration": 0.029,
        "fintech_maturity": 0.65,
        "real_estate_share": 0.14,
    },
    "QAT": {
        "name": "Qatar",
        "name_ar": "قطر",
        "gdp_usd": 236.0e9,
        "oil_gdp_share": 0.38,      # gas-heavy, but LNG via Hormuz
        "hormuz_dependency": 0.92,
        "banking_assets_usd": 490.0e9,
        "insurance_penetration": 0.015,
        "fintech_maturity": 0.40,
        "real_estate_share": 0.09,
    },
    "BHR": {
        "name": "Bahrain",
        "name_ar": "البحرين",
        "gdp_usd": 44.0e9,
        "oil_gdp_share": 0.18,
        "hormuz_dependency": 0.85,
        "banking_assets_usd": 220.0e9,  # OFC-heavy (offshore banking center)
        "insurance_penetration": 0.022,
        "fintech_maturity": 0.50,
        "real_estate_share": 0.06,
    },
    "OMN": {
        "name": "Oman",
        "name_ar": "عُمان",
        "gdp_usd": 105.0e9,
        "oil_gdp_share": 0.34,
        "hormuz_dependency": 0.88,
        "banking_assets_usd": 95.0e9,
        "insurance_penetration": 0.013,
        "fintech_maturity": 0.30,
        "real_estate_share": 0.05,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Sector Metadata
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_META: dict[str, dict] = {
    "oil_gas": {
        "label": "Oil & Gas",
        "label_ar": "النفط والغاز",
        "base_sensitivity": 0.90,    # direct Hormuz exposure
        "recovery_lag_hours": 336,
    },
    "banking": {
        "label": "Banking & Finance",
        "label_ar": "الخدمات المصرفية",
        "base_sensitivity": 0.55,
        "recovery_lag_hours": 168,
    },
    "insurance": {
        "label": "Insurance & Takaful",
        "label_ar": "التأمين والتكافل",
        "base_sensitivity": 0.45,
        "recovery_lag_hours": 240,
    },
    "fintech": {
        "label": "Fintech & Digital",
        "label_ar": "التقنية المالية",
        "base_sensitivity": 0.25,
        "recovery_lag_hours": 72,
    },
    "real_estate": {
        "label": "Real Estate & Construction",
        "label_ar": "العقارات والبناء",
        "base_sensitivity": 0.30,
        "recovery_lag_hours": 504,
    },
    "government": {
        "label": "Government & Fiscal",
        "label_ar": "الحكومة والمالية العامة",
        "base_sensitivity": 0.40,
        "recovery_lag_hours": 168,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Shock Vector — initial exogenous stress per (country, sector)
# ═══════════════════════════════════════════════════════════════════════════════

def build_initial_shock_vector(
    severity: float,
    transit_reduction_pct: float,
) -> dict[tuple[str, str], float]:
    """Compute deterministic initial shock for every (country, sector) pair.

    Formula per node:
      shock = severity
            * transit_reduction_pct
            * country.hormuz_dependency
            * sector.base_sensitivity
            * (1 + country.oil_gdp_share)   # amplifier for oil-heavy economies

    Returns dict mapping (country_code, sector_code) -> shock in [0, 1].
    """
    shocks: dict[tuple[str, str], float] = {}
    for cc, cm in COUNTRY_META.items():
        for sc, sm in SECTOR_META.items():
            raw = (
                severity
                * transit_reduction_pct
                * cm["hormuz_dependency"]
                * sm["base_sensitivity"]
                * (1.0 + cm["oil_gdp_share"])
            )
            shocks[(cc, sc)] = min(raw, 1.0)  # cap at 1.0
    return shocks


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Template — cross-sector and cross-country transmission channels
# ═══════════════════════════════════════════════════════════════════════════════

# Intra-country sector-to-sector transmission weights.
# Read as: stress in source_sector transmits to target_sector at weight.
INTRA_COUNTRY_EDGES: list[tuple[str, str, float, str]] = [
    # (source_sector, target_sector, weight, channel_label)
    ("oil_gas",      "banking",      0.70, "Revenue shock → credit tightening"),
    ("oil_gas",      "insurance",    0.55, "Energy price → marine/cargo claims surge"),
    ("oil_gas",      "government",   0.65, "Fiscal revenue collapse"),
    ("oil_gas",      "real_estate",  0.35, "Construction cost escalation"),
    ("oil_gas",      "fintech",      0.20, "Payment volume decline"),
    ("banking",      "insurance",    0.45, "Liquidity stress → counterparty exposure"),
    ("banking",      "real_estate",  0.50, "Credit freeze → project finance halt"),
    ("banking",      "fintech",      0.40, "Interbank rate spike → fintech funding cost"),
    ("banking",      "government",   0.30, "Sovereign debt repricing"),
    ("insurance",    "banking",      0.25, "Claims payouts → deposit drawdown"),
    ("insurance",    "real_estate",  0.20, "Construction insurance repricing"),
    ("government",   "banking",      0.35, "Fiscal stimulus withdrawal"),
    ("government",   "real_estate",  0.30, "Infrastructure spending freeze"),
    ("real_estate",  "banking",      0.30, "NPL contagion from developer defaults"),
    ("fintech",      "banking",      0.15, "Digital channel disruption"),
]

# Cross-country transmission weights (major corridors only).
# Format: (source_country, target_country, weight, channel_label)
CROSS_COUNTRY_EDGES: list[tuple[str, str, float, str]] = [
    ("SAU", "BHR", 0.55, "Saudi–Bahrain banking corridor (OFC dependency)"),
    ("SAU", "KWT", 0.35, "GCC interbank market linkage"),
    ("SAU", "UAE", 0.40, "Trade finance & re-export channel"),
    ("UAE", "OMN", 0.45, "Logistics & port re-routing"),
    ("UAE", "QAT", 0.30, "Financial center contagion"),
    ("QAT", "KWT", 0.25, "LNG revenue → sovereign wealth linkage"),
    ("KWT", "BHR", 0.30, "Investment corridor (Bahrain OFC)"),
    ("OMN", "UAE", 0.35, "Port substitution pressure"),
    ("QAT", "UAE", 0.35, "LNG processing & shipping overlap"),
    ("BHR", "SAU", 0.20, "Causeway trade & labor flow"),
]


def build_edges(
    shock_vector: dict[tuple[str, str], float],
) -> list[Edge]:
    """Build the full propagation graph edge list.

    1. Intra-country: for each country, connect sectors via INTRA_COUNTRY_EDGES.
    2. Cross-country: for each corridor, connect the dominant sector pair
       (oil_gas → oil_gas initially, then banking → banking for financial contagion).
    """
    edges: list[Edge] = []

    # Intra-country edges (6 countries x 15 sector pairs = 90 edges)
    for cc in COUNTRY_META:
        for src_s, tgt_s, w, ch in INTRA_COUNTRY_EDGES:
            edges.append(Edge(
                source=NodeId(cc, src_s),
                target=NodeId(cc, tgt_s),
                weight=w,
                channel=ch,
                delay_hours=4.0,
            ))

    # Cross-country edges (oil_gas and banking corridors)
    for src_c, tgt_c, w, ch in CROSS_COUNTRY_EDGES:
        # Energy corridor
        edges.append(Edge(
            source=NodeId(src_c, "oil_gas"),
            target=NodeId(tgt_c, "oil_gas"),
            weight=w * 0.8,
            channel=f"Energy: {ch}",
            delay_hours=12.0,
        ))
        # Banking corridor
        edges.append(Edge(
            source=NodeId(src_c, "banking"),
            target=NodeId(tgt_c, "banking"),
            weight=w * 0.6,
            channel=f"Banking: {ch}",
            delay_hours=8.0,
        ))
        # Insurance corridor (lower coupling)
        edges.append(Edge(
            source=NodeId(src_c, "insurance"),
            target=NodeId(tgt_c, "insurance"),
            weight=w * 0.3,
            channel=f"Insurance: {ch}",
            delay_hours=24.0,
        ))

    return edges
