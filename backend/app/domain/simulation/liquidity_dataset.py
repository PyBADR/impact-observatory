"""
Impact Observatory | مرصد الأثر — Phase 2 Liquidity Stress Dataset
GCC regional liquidity stress scenario: banking-first shock propagation.

Scenario narrative:
  A simultaneous deposit flight across GCC banking systems triggers an
  interbank market freeze. Correspondent banking channels seize, FX swap
  lines tighten, and sovereign CDS spreads widen. Unlike Hormuz (energy-first),
  this scenario originates in the banking sector and transmits outward
  to insurance, government, real estate, and fintech.

Sources:
  - Interbank dependency: BIS locational banking statistics
  - Deposit concentration: GCC central bank financial stability reports
  - Correspondent banking: SWIFT gpi corridor data (public summaries)
  - CDS spread history: Markit/IHS sovereign CDS indices

All weights are deterministic. Same contract as hormuz_dataset.py.
"""
from __future__ import annotations

from app.domain.simulation.graph_types import Edge, NodeId


# ═══════════════════════════════════════════════════════════════════════════════
# Country Metadata — liquidity-specific exposure parameters
# ═══════════════════════════════════════════════════════════════════════════════

COUNTRY_META: dict[str, dict] = {
    "KWT": {
        "name": "Kuwait",
        "name_ar": "الكويت",
        "gdp_usd": 184.0e9,
        "oil_gdp_share": 0.52,
        "banking_system_depth": 0.72,     # banking assets / GDP
        "interbank_exposure": 0.55,       # share of funding from interbank
        "deposit_concentration": 0.68,    # top-10 depositor share
        "fx_reserve_months": 14.0,
        "sovereign_cds_bps": 48,
    },
    "SAU": {
        "name": "Saudi Arabia",
        "name_ar": "المملكة العربية السعودية",
        "gdp_usd": 1069.0e9,
        "oil_gdp_share": 0.42,
        "banking_system_depth": 0.85,
        "interbank_exposure": 0.40,
        "deposit_concentration": 0.52,
        "fx_reserve_months": 22.0,
        "sovereign_cds_bps": 62,
    },
    "UAE": {
        "name": "United Arab Emirates",
        "name_ar": "الإمارات العربية المتحدة",
        "gdp_usd": 507.0e9,
        "oil_gdp_share": 0.30,
        "banking_system_depth": 1.35,     # major financial center
        "interbank_exposure": 0.62,
        "deposit_concentration": 0.45,
        "fx_reserve_months": 8.0,         # lower relative to banking size
        "sovereign_cds_bps": 55,
    },
    "QAT": {
        "name": "Qatar",
        "name_ar": "قطر",
        "gdp_usd": 236.0e9,
        "oil_gdp_share": 0.38,
        "banking_system_depth": 1.10,
        "interbank_exposure": 0.58,
        "deposit_concentration": 0.60,
        "fx_reserve_months": 10.0,
        "sovereign_cds_bps": 50,
    },
    "BHR": {
        "name": "Bahrain",
        "name_ar": "البحرين",
        "gdp_usd": 44.0e9,
        "oil_gdp_share": 0.18,
        "banking_system_depth": 5.20,     # OFC — banking assets >> GDP
        "interbank_exposure": 0.75,
        "deposit_concentration": 0.72,
        "fx_reserve_months": 3.0,         # thinnest buffer
        "sovereign_cds_bps": 185,
    },
    "OMN": {
        "name": "Oman",
        "name_ar": "عُمان",
        "gdp_usd": 105.0e9,
        "oil_gdp_share": 0.34,
        "banking_system_depth": 0.78,
        "interbank_exposure": 0.48,
        "deposit_concentration": 0.58,
        "fx_reserve_months": 6.0,
        "sovereign_cds_bps": 145,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Sector Metadata — liquidity-scenario sensitivities
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_META: dict[str, dict] = {
    "oil_gas": {
        "label": "Oil & Gas",
        "label_ar": "النفط والغاز",
        "base_sensitivity": 0.25,    # indirect — trade finance disruption
        "recovery_lag_hours": 168,
    },
    "banking": {
        "label": "Banking & Finance",
        "label_ar": "الخدمات المصرفية",
        "base_sensitivity": 0.95,    # epicenter of this scenario
        "recovery_lag_hours": 504,
    },
    "insurance": {
        "label": "Insurance & Takaful",
        "label_ar": "التأمين والتكافل",
        "base_sensitivity": 0.60,    # counterparty + investment portfolio
        "recovery_lag_hours": 336,
    },
    "fintech": {
        "label": "Fintech & Digital",
        "label_ar": "التقنية المالية",
        "base_sensitivity": 0.50,    # payment rails + funding dependency
        "recovery_lag_hours": 120,
    },
    "real_estate": {
        "label": "Real Estate & Construction",
        "label_ar": "العقارات والبناء",
        "base_sensitivity": 0.55,    # project finance freeze
        "recovery_lag_hours": 720,
    },
    "government": {
        "label": "Government & Fiscal",
        "label_ar": "الحكومة والمالية العامة",
        "base_sensitivity": 0.45,    # sovereign borrowing cost spike
        "recovery_lag_hours": 240,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Shock Vector
# ═══════════════════════════════════════════════════════════════════════════════

def build_initial_shock_vector(
    severity: float,
    interbank_freeze_pct: float = 0.45,
) -> dict[tuple[str, str], float]:
    """Compute initial liquidity shock for every (country, sector) pair.

    Formula per node:
      shock = severity
            * interbank_freeze_pct
            * country.interbank_exposure
            * sector.base_sensitivity
            * (1 + country.deposit_concentration)   # amplifier for concentrated systems
            * (1 / max(country.fx_reserve_months, 1)) ^ 0.3  # thin reserves amplify

    The banking sector hits hardest, then insurance/fintech, then others.
    """
    shocks: dict[tuple[str, str], float] = {}
    for cc, cm in COUNTRY_META.items():
        reserve_factor = (1.0 / max(cm["fx_reserve_months"], 1.0)) ** 0.3
        for sc, sm in SECTOR_META.items():
            raw = (
                severity
                * interbank_freeze_pct
                * cm["interbank_exposure"]
                * sm["base_sensitivity"]
                * (1.0 + cm["deposit_concentration"])
                * reserve_factor
            )
            shocks[(cc, sc)] = min(raw, 1.0)
    return shocks


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Template — liquidity-specific transmission channels
# ═══════════════════════════════════════════════════════════════════════════════

# Intra-country: banking-first outward transmission
INTRA_COUNTRY_EDGES: list[tuple[str, str, float, str]] = [
    # Banking is the epicenter — radiates outward
    ("banking",      "insurance",    0.65, "Counterparty exposure + investment portfolio stress"),
    ("banking",      "real_estate",  0.70, "Project finance freeze + developer credit withdrawal"),
    ("banking",      "fintech",      0.55, "Settlement disruption + funding line revocation"),
    ("banking",      "government",   0.50, "Sovereign debt repricing + fiscal deposit drawdown"),
    ("banking",      "oil_gas",      0.30, "Trade finance contraction for energy exports"),
    # Insurance feedback
    ("insurance",    "banking",      0.35, "Claims payouts deplete bank deposits"),
    ("insurance",    "real_estate",  0.25, "Construction insurance repricing halts permits"),
    # Real estate feedback
    ("real_estate",  "banking",      0.45, "Developer NPLs cascade into banking system"),
    ("real_estate",  "government",   0.20, "Property tax revenue decline"),
    # Government fiscal
    ("government",   "banking",      0.40, "Delayed sovereign deposits + subsidy withdrawal"),
    ("government",   "real_estate",  0.30, "Infrastructure spending freeze"),
    # Fintech second-order
    ("fintech",      "banking",      0.25, "Digital bank run amplifies withdrawal pressure"),
    ("fintech",      "insurance",    0.15, "Insurtech claims acceleration"),
    # Oil sector indirect
    ("oil_gas",      "banking",      0.30, "Revenue decline reduces banking system deposits"),
    ("oil_gas",      "government",   0.45, "Fiscal revenue drop from lower oil proceeds"),
]

# Cross-country: correspondent banking and FX swap corridors
CROSS_COUNTRY_EDGES: list[tuple[str, str, float, str]] = [
    ("UAE", "BHR", 0.65, "DIFC → Bahrain OFC correspondent banking corridor"),
    ("UAE", "OMN", 0.45, "Abu Dhabi → Muscat interbank lending"),
    ("UAE", "QAT", 0.40, "Dubai → Doha FX swap and trade finance"),
    ("SAU", "BHR", 0.60, "SAMA → CBB liquidity support dependency"),
    ("SAU", "KWT", 0.40, "Saudi–Kuwait bilateral swap line"),
    ("SAU", "UAE", 0.35, "Cross-listing and mutual fund contagion"),
    ("QAT", "KWT", 0.30, "Sovereign wealth reallocation pressure"),
    ("BHR", "SAU", 0.35, "Bahrain OFC deposit flight to Saudi"),
    ("KWT", "UAE", 0.30, "Investment fund redemption pressure"),
    ("OMN", "SAU", 0.25, "Omani bank subsidiary exposure in Saudi"),
]


def build_edges(
    shock_vector: dict[tuple[str, str], float],
) -> list[Edge]:
    """Build the full liquidity-stress propagation edge list."""
    edges: list[Edge] = []

    # Intra-country edges (6 countries x 15 sector pairs = 90 edges)
    for cc in COUNTRY_META:
        for src_s, tgt_s, w, ch in INTRA_COUNTRY_EDGES:
            edges.append(Edge(
                source=NodeId(cc, src_s),
                target=NodeId(cc, tgt_s),
                weight=w,
                channel=ch,
                delay_hours=2.0,  # liquidity transmits faster than energy
            ))

    # Cross-country edges (banking + insurance + fintech corridors)
    for src_c, tgt_c, w, ch in CROSS_COUNTRY_EDGES:
        # Banking corridor (primary)
        edges.append(Edge(
            source=NodeId(src_c, "banking"),
            target=NodeId(tgt_c, "banking"),
            weight=w * 0.85,
            channel=f"Banking: {ch}",
            delay_hours=4.0,
        ))
        # Insurance corridor (secondary)
        edges.append(Edge(
            source=NodeId(src_c, "insurance"),
            target=NodeId(tgt_c, "insurance"),
            weight=w * 0.40,
            channel=f"Insurance: {ch}",
            delay_hours=12.0,
        ))
        # Fintech corridor (fast but lower magnitude)
        edges.append(Edge(
            source=NodeId(src_c, "fintech"),
            target=NodeId(tgt_c, "fintech"),
            weight=w * 0.35,
            channel=f"Fintech: {ch}",
            delay_hours=2.0,
        ))

    return edges
