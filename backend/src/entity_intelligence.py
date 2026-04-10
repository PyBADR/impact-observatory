"""
Impact Observatory | مرصد الأثر
Entity Intelligence Engine — deterministic entity-level generation for
banking affected_institutions, insurance affected_lines, fintech affected_platforms.

DESIGN PRINCIPLES
─────────────────
• Fully deterministic: identical inputs → identical outputs
• Zero randomness: no random(), no faker, no static per-scenario lists
• Registry-driven: each sector has a real-world entity registry
• Score-driven inclusion: entities enter output only if impact_score > INCLUSION_THRESHOLD
• Scenario-sensitive: weights shift based on which shock_nodes are active

SCORING FORMULA (per sector)
─────────────────────────────
banking impact_score =
    0.30 * sector_exposure_weight       # how hard banking is hit this run
  + 0.25 * aggregate_sector_stress      # liquidity_stress aggregate
  + 0.20 * event_severity               # amplifies all exposures
  + 0.15 * entity_scenario_sensitivity  # entity-specific fit to scenario type
  + 0.10 * contagion_factor             # network spread from aggregate_stress

insurance impact_score =
    0.30 * sector_exposure_weight       # insurance sector exposure fraction
  + 0.25 * aggregate_sector_stress      # insurance_stress severity_index
  + 0.20 * event_severity
  + 0.15 * line_scenario_sensitivity
  + 0.10 * claims_contagion

fintech impact_score =
    0.30 * sector_exposure_weight       # fintech sector exposure fraction
  + 0.25 * aggregate_sector_stress      # liquidity_stress * 0.75
  + 0.20 * event_severity
  + 0.15 * platform_scenario_sensitivity
  + 0.10 * cross_border_factor
"""
from __future__ import annotations

import math
from typing import Literal

# ── Thresholds ────────────────────────────────────────────────────────────────

INCLUSION_THRESHOLD = 0.06   # entities below this score are excluded from output
MAX_ENTITIES_PER_SECTOR = 8  # cap output length

# ── Scenario type tags ────────────────────────────────────────────────────────

_MARITIME_NODES  = frozenset({"hormuz", "shipping_lanes", "salalah_port",
                               "dubai_port", "abu_dhabi_port", "dammam_port",
                               "kuwait_port"})
_ENERGY_NODES    = frozenset({"saudi_aramco", "qatar_lng", "adnoc",
                               "kuwait_oil", "gcc_pipeline", "oman_oil"})
_FINTECH_NODES   = frozenset({"swift_gcc", "uae_payment_rail",
                               "saudi_payment_rail", "gcc_fintech", "difc"})
_BANKING_NODES   = frozenset({"uae_banking", "saudi_banking", "qatar_banking",
                               "riyadh_financial", "bahrain_banking",
                               "kuwait_banking", "gcc_fsb"})


def _detect_scenario_type(shock_nodes: list[str]) -> str:
    """
    Return a single scenario type string based on which shock_nodes are active.
    Priority: cyber_fintech > liquidity > energy > maritime_trade > port > cross_sector
    """
    node_set = set(shock_nodes)
    if node_set & _FINTECH_NODES:
        return "cyber_fintech"
    if node_set & _BANKING_NODES:
        return "liquidity"
    if node_set & _ENERGY_NODES:
        return "energy"
    if node_set & _MARITIME_NODES:
        # Distinguish port-only (no shipping lanes) from full maritime
        if node_set & {"shipping_lanes", "hormuz"}:
            return "maritime_trade"
        return "port"
    return "cross_sector"


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _classify(score: float) -> str:
    if score >= 0.70: return "CRITICAL"
    if score >= 0.50: return "ELEVATED"
    if score >= 0.30: return "MODERATE"
    if score >= 0.10: return "LOW"
    return "NOMINAL"


# ═══════════════════════════════════════════════════════════════════════════════
# BANKING
# ═══════════════════════════════════════════════════════════════════════════════

# Each bank record:
#   assets_usd          — total balance sheet (USD)
#   base_car_pct        — capital adequacy ratio at baseline
#   trade_sensitivity   — sensitivity to maritime/trade disruption [0-1]
#   energy_sensitivity  — sensitivity to oil price / energy shocks [0-1]
#   digital_sensitivity — sensitivity to cyber/fintech disruption [0-1]
#   interbank_sensitivity — sensitivity to liquidity / interbank events [0-1]
#
# Sensitivity axes reflect each institution's business mix and geography.
# Higher = more affected when that scenario type fires.

_BANKING_REGISTRY: list[dict] = [
    {
        "id": "snb",
        "name": "Saudi National Bank",
        "name_ar": "البنك الأهلي السعودي",
        "country": "SA",
        "assets_usd": 280_000_000_000,
        "base_car_pct": 19.5,
        "trade_sensitivity":    0.60,   # large trade finance book
        "energy_sensitivity":   0.85,   # heavy hydrocarbon corporate lending
        "digital_sensitivity":  0.55,   # significant digital banking ops
        "interbank_sensitivity":0.70,   # largest SA bank — high interbank exposure
    },
    {
        "id": "al_rajhi",
        "name": "Al Rajhi Bank",
        "name_ar": "مصرف الراجحي",
        "country": "SA",
        "assets_usd": 195_000_000_000,
        "base_car_pct": 20.1,
        "trade_sensitivity":    0.45,   # retail-heavy, lower trade book
        "energy_sensitivity":   0.55,
        "digital_sensitivity":  0.72,   # major retail digital banking platform
        "interbank_sensitivity":0.50,
    },
    {
        "id": "fab",
        "name": "First Abu Dhabi Bank",
        "name_ar": "بنك أبوظبي الأول",
        "country": "AE",
        "assets_usd": 310_000_000_000,
        "base_car_pct": 16.8,
        "trade_sensitivity":    0.80,   # dominant UAE trade finance
        "energy_sensitivity":   0.75,
        "digital_sensitivity":  0.65,
        "interbank_sensitivity":0.78,   # major GCC interbank lender
    },
    {
        "id": "emirates_nbd",
        "name": "Emirates NBD",
        "name_ar": "الإمارات دبي الوطني",
        "country": "AE",
        "assets_usd": 210_000_000_000,
        "base_car_pct": 17.2,
        "trade_sensitivity":    0.75,
        "energy_sensitivity":   0.60,
        "digital_sensitivity":  0.80,   # Liv. digital bank, high payment exposure
        "interbank_sensitivity":0.65,
    },
    {
        "id": "qnb",
        "name": "Qatar National Bank",
        "name_ar": "بنك قطر الوطني",
        "country": "QA",
        "assets_usd": 340_000_000_000,
        "base_car_pct": 18.5,
        "trade_sensitivity":    0.65,
        "energy_sensitivity":   0.90,   # deep LNG / hydrocarbon exposure
        "digital_sensitivity":  0.50,
        "interbank_sensitivity":0.72,
    },
    {
        "id": "nbk",
        "name": "National Bank of Kuwait",
        "name_ar": "بنك الكويت الوطني",
        "country": "KW",
        "assets_usd": 120_000_000_000,
        "base_car_pct": 17.8,
        "trade_sensitivity":    0.55,
        "energy_sensitivity":   0.80,   # Kuwait oil / sovereign linked
        "digital_sensitivity":  0.45,
        "interbank_sensitivity":0.60,
    },
    {
        "id": "riyad_bank",
        "name": "Riyad Bank",
        "name_ar": "بنك الرياض",
        "country": "SA",
        "assets_usd": 105_000_000_000,
        "base_car_pct": 18.9,
        "trade_sensitivity":    0.50,
        "energy_sensitivity":   0.70,
        "digital_sensitivity":  0.60,
        "interbank_sensitivity":0.55,
    },
    {
        "id": "bank_muscat",
        "name": "Bank Muscat",
        "name_ar": "بنك مسقط",
        "country": "OM",
        "assets_usd": 45_000_000_000,
        "base_car_pct": 17.1,
        "trade_sensitivity":    0.70,   # Oman port / Salalah corridor exposure
        "energy_sensitivity":   0.65,
        "digital_sensitivity":  0.40,
        "interbank_sensitivity":0.45,
    },
]

_TOTAL_BANKING_ASSETS_USD: float = sum(b["assets_usd"] for b in _BANKING_REGISTRY)

# Maps scenario_type → which sensitivity axis drives banking entity score
_BANKING_SCENARIO_AXIS: dict[str, str] = {
    "maritime_trade": "trade_sensitivity",
    "port":           "trade_sensitivity",
    "energy":         "energy_sensitivity",
    "cyber_fintech":  "digital_sensitivity",
    "liquidity":      "interbank_sensitivity",
    "cross_sector":   "trade_sensitivity",   # balanced — use trade as default
}


def generate_banking_entities(
    shock_nodes: list[str],
    severity: float,
    sector_exposure: dict[str, float],
    liquidity_stress: dict,
    total_loss_usd: float,
) -> list[dict]:
    """
    Generate deterministic affected_institutions list.

    Returns list of institution dicts sorted by impact_score descending.
    Only entities with impact_score > INCLUSION_THRESHOLD are included.
    """
    scenario_type = _detect_scenario_type(shock_nodes)
    sensitivity_axis = _BANKING_SCENARIO_AXIS.get(scenario_type, "trade_sensitivity")

    # Aggregate banking sector inputs
    banking_exposure_weight = _clamp(sector_exposure.get("banking", 0.0))
    agg_banking_stress = _clamp(float(liquidity_stress.get("aggregate_stress", 0.0)))
    contagion_factor = _clamp(agg_banking_stress * 0.70)

    # Total loss attributed to banking sector
    total_banking_loss = total_loss_usd * max(sector_exposure.get("banking", 0.30), 0.05)

    results: list[dict] = []
    for bank in _BANKING_REGISTRY:
        entity_sensitivity = float(bank[sensitivity_axis])

        # ── Impact Score ──────────────────────────────────────────────
        # impact = 0.30*sector_exp + 0.25*agg_stress + 0.20*severity
        #        + 0.15*entity_sens + 0.10*contagion
        raw_score = (
            0.30 * banking_exposure_weight
            + 0.25 * agg_banking_stress
            + 0.20 * severity
            + 0.15 * entity_sensitivity
            + 0.10 * contagion_factor
        )
        # Scale by institution's relative size (larger institutions amplify systemic effect)
        size_weight = bank["assets_usd"] / _TOTAL_BANKING_ASSETS_USD
        impact_score = _clamp(raw_score * (1.0 + size_weight * 0.5))

        if impact_score < INCLUSION_THRESHOLD:
            continue

        # ── Derived metrics ────────────────────────────────────────────
        institution_exposure_usd = round(total_banking_loss * size_weight, 2)

        # Stress sub-components derived from aggregate + scenario type
        liq_stress_factor  = float(liquidity_stress.get("liquidity_stress", agg_banking_stress))
        credit_stress_factor = float(liquidity_stress.get("aggregate_stress", agg_banking_stress)) * 0.85

        inst_liquidity = _clamp(impact_score * liq_stress_factor / max(agg_banking_stress, 0.01)
                                if agg_banking_stress > 0 else impact_score * 0.80)
        inst_credit    = _clamp(impact_score * 0.75)
        inst_fx        = _clamp(impact_score * 0.60)
        inst_contagion = _clamp(impact_score * 0.55)

        # CAR impact: each 1% aggregate stress → proportional CAR pressure
        car_impact_pp = round(bank["base_car_pct"] * credit_stress_factor * severity * 0.15, 2)
        projected_car = max(round(bank["base_car_pct"] - car_impact_pp, 2), 0.0)

        results.append({
            "id":               bank["id"],
            "name":             bank["name"],
            "name_ar":          bank["name_ar"],
            "country":          bank["country"],
            "exposure_usd":     institution_exposure_usd,
            "stress":           round(impact_score, 4),
            "liquidity_stress": round(inst_liquidity, 4),
            "credit_stress":    round(inst_credit, 4),
            "fx_stress":        round(inst_fx, 4),
            "interbank_contagion": round(inst_contagion, 4),
            "projected_car_pct": projected_car,
            "car_impact_pp":    car_impact_pp,
            "classification":   _classify(impact_score),
            "_score":           impact_score,  # internal sorting key
        })

    # Sort descending by score; strip internal key; cap
    results.sort(key=lambda x: -x["_score"])
    for r in results:
        del r["_score"]
    return results[:MAX_ENTITIES_PER_SECTOR]


# ═══════════════════════════════════════════════════════════════════════════════
# INSURANCE
# ═══════════════════════════════════════════════════════════════════════════════

# Each line record:
#   market_share_pct     — fraction of GCC insurance market [0-1]
#   base_combined_ratio  — pre-shock combined ratio
#   maritime_sensitivity — hull / marine cargo / P&I
#   energy_sensitivity   — upstream / downstream / property energy
#   cyber_sensitivity    — cyber, technology E&O
#   bi_sensitivity       — business interruption across sector
#   credit_sensitivity   — trade credit, political risk, surety
#   port_sensitivity     — logistics, cargo, storage

_INSURANCE_REGISTRY: list[dict] = [
    {
        "id": "marine_cargo",
        "name": "Marine Cargo",
        "name_ar": "الشحن البحري",
        "market_share_pct": 0.14,
        "base_combined_ratio": 0.95,
        "maritime_sensitivity": 0.95,
        "energy_sensitivity":   0.50,
        "cyber_sensitivity":    0.25,
        "bi_sensitivity":       0.60,
        "credit_sensitivity":   0.55,
        "port_sensitivity":     0.85,
    },
    {
        "id": "energy_upstream",
        "name": "Energy Upstream",
        "name_ar": "تأمين الطاقة (المنبع)",
        "market_share_pct": 0.18,
        "base_combined_ratio": 0.92,
        "maritime_sensitivity": 0.60,
        "energy_sensitivity":   0.98,
        "cyber_sensitivity":    0.45,
        "bi_sensitivity":       0.75,
        "credit_sensitivity":   0.45,
        "port_sensitivity":     0.40,
    },
    {
        "id": "business_interruption",
        "name": "Business Interruption",
        "name_ar": "تأمين انقطاع الأعمال",
        "market_share_pct": 0.12,
        "base_combined_ratio": 1.02,
        "maritime_sensitivity": 0.75,
        "energy_sensitivity":   0.70,
        "cyber_sensitivity":    0.80,
        "bi_sensitivity":       0.95,
        "credit_sensitivity":   0.65,
        "port_sensitivity":     0.70,
    },
    {
        "id": "credit_political_risk",
        "name": "Credit & Political Risk",
        "name_ar": "المخاطر الائتمانية والسياسية",
        "market_share_pct": 0.09,
        "base_combined_ratio": 0.97,
        "maritime_sensitivity": 0.65,
        "energy_sensitivity":   0.60,
        "cyber_sensitivity":    0.50,
        "bi_sensitivity":       0.70,
        "credit_sensitivity":   0.95,
        "port_sensitivity":     0.60,
    },
    {
        "id": "property_catastrophe",
        "name": "Property Catastrophe",
        "name_ar": "تأمين الكوارث العقارية",
        "market_share_pct": 0.16,
        "base_combined_ratio": 0.88,
        "maritime_sensitivity": 0.40,
        "energy_sensitivity":   0.65,
        "cyber_sensitivity":    0.30,
        "bi_sensitivity":       0.50,
        "credit_sensitivity":   0.35,
        "port_sensitivity":     0.45,
    },
    {
        "id": "aviation",
        "name": "Aviation",
        "name_ar": "تأمين الطيران",
        "market_share_pct": 0.07,
        "base_combined_ratio": 0.94,
        "maritime_sensitivity": 0.70,   # air cargo disrupted by maritime rerouting
        "energy_sensitivity":   0.45,
        "cyber_sensitivity":    0.60,
        "bi_sensitivity":       0.65,
        "credit_sensitivity":   0.40,
        "port_sensitivity":     0.55,
    },
    {
        "id": "cyber_tech",
        "name": "Cyber & Technology E&O",
        "name_ar": "تأمين الإلكتروني وتقنية المعلومات",
        "market_share_pct": 0.06,
        "base_combined_ratio": 1.05,
        "maritime_sensitivity": 0.20,
        "energy_sensitivity":   0.35,
        "cyber_sensitivity":    0.98,
        "bi_sensitivity":       0.80,
        "credit_sensitivity":   0.40,
        "port_sensitivity":     0.20,
    },
    {
        "id": "life_health",
        "name": "Life & Health",
        "name_ar": "تأمين الحياة والصحة",
        "market_share_pct": 0.18,
        "base_combined_ratio": 0.90,
        "maritime_sensitivity": 0.20,
        "energy_sensitivity":   0.25,
        "cyber_sensitivity":    0.35,
        "bi_sensitivity":       0.40,
        "credit_sensitivity":   0.30,
        "port_sensitivity":     0.20,
    },
]

_INSURANCE_SCENARIO_AXIS: dict[str, str] = {
    "maritime_trade": "maritime_sensitivity",
    "port":           "port_sensitivity",
    "energy":         "energy_sensitivity",
    "cyber_fintech":  "cyber_sensitivity",
    "liquidity":      "credit_sensitivity",
    "cross_sector":   "bi_sensitivity",
}

# Scenario-specific claims surge multipliers applied on top of base
_CLAIMS_SURGE_BY_SCENARIO: dict[str, float] = {
    "maritime_trade": 2.80,
    "port":           2.20,
    "energy":         2.50,
    "cyber_fintech":  3.10,
    "liquidity":      1.80,
    "cross_sector":   2.00,
}


def generate_insurance_entities(
    shock_nodes: list[str],
    severity: float,
    sector_exposure: dict[str, float],
    insurance_stress: dict,
    total_loss_usd: float,
) -> list[dict]:
    """
    Generate deterministic affected_lines list.

    Each line's claims_surge is derived from:
      base_surge = scenario_type_max_surge (e.g. 2.8x for maritime)
      line_surge = 1.0 + (base_surge - 1.0) * line_sensitivity * impact_score
    """
    scenario_type = _detect_scenario_type(shock_nodes)
    sensitivity_axis = _INSURANCE_SCENARIO_AXIS.get(scenario_type, "bi_sensitivity")

    ins_exposure_weight = _clamp(sector_exposure.get("insurance", 0.0))
    agg_ins_stress = _clamp(float(insurance_stress.get("severity_index", 0.0)))
    claims_contagion = _clamp(agg_ins_stress * 0.60)
    max_surge = _CLAIMS_SURGE_BY_SCENARIO.get(scenario_type, 2.0)

    total_ins_loss = total_loss_usd * max(sector_exposure.get("insurance", 0.15), 0.03)

    results: list[dict] = []
    for line in _INSURANCE_REGISTRY:
        line_sensitivity = float(line[sensitivity_axis])

        # ── Impact Score ──────────────────────────────────────────────
        # impact = 0.30*ins_exp + 0.25*agg_ins_stress + 0.20*severity
        #        + 0.15*line_sens + 0.10*claims_contagion
        raw_score = (
            0.30 * ins_exposure_weight
            + 0.25 * agg_ins_stress
            + 0.20 * severity
            + 0.15 * line_sensitivity
            + 0.10 * claims_contagion
        )
        # Line market share scales impact (larger lines = more systemic)
        impact_score = _clamp(raw_score * (1.0 + line["market_share_pct"] * 0.40))

        if impact_score < INCLUSION_THRESHOLD:
            continue

        # ── Derived metrics ────────────────────────────────────────────
        line_exposure_usd = round(total_ins_loss * line["market_share_pct"], 2)

        # Claims surge: interpolate between 1.0 (no event) and max_surge (worst case)
        # driven by line_sensitivity and impact_score
        claims_surge = round(
            1.0 + (max_surge - 1.0) * line_sensitivity * impact_score, 3
        )
        claims_surge = max(1.0, claims_surge)

        # Combined ratio impact: +delta on top of base
        combined_ratio = round(
            line["base_combined_ratio"] + impact_score * 0.25 * line_sensitivity, 4
        )

        # Reserve stress: fraction of line exposure at risk
        reserve_stress = round(_clamp(impact_score * 0.60 * line_sensitivity), 4)

        stress = round(impact_score, 4)

        results.append({
            "id":                    line["id"],
            "name":                  line["name"],
            "name_ar":               line["name_ar"],
            "exposure_usd":          line_exposure_usd,
            "claims_surge":          claims_surge,
            "combined_ratio":        combined_ratio,
            "reserve_stress":        reserve_stress,
            "reinsurance_trigger":   impact_score >= 0.50,
            "stress":                stress,
            "classification":        _classify(impact_score),
            "_score":                impact_score,
        })

    results.sort(key=lambda x: -x["_score"])
    for r in results:
        del r["_score"]
    return results[:MAX_ENTITIES_PER_SECTOR]


# ═══════════════════════════════════════════════════════════════════════════════
# FINTECH
# ═══════════════════════════════════════════════════════════════════════════════

# Each platform record:
#   daily_txn_volume_usd  — approximate daily settlement volume (USD)
#   service_type          — RTGS / PAYMENT_RAIL / DIGITAL_BANK / CROSS_BORDER / CRYPTO
#   cross_border_weight   — fraction of volume that crosses borders [0-1]
#   cyber_sensitivity     — exposure to cyber attack vectors [0-1]
#   liquidity_sensitivity — dependence on interbank liquidity [0-1]
#   volume_sensitivity    — overall payment volume exposure [0-1]
#   trade_sensitivity     — sensitivity to trade/maritime disruption [0-1]

_FINTECH_REGISTRY: list[dict] = [
    {
        "id": "uae_payment_rail",
        "name": "UAE AANI Payment Rail",
        "name_ar": "شبكة آني للمدفوعات الإماراتية",
        "country": "AE",
        "service_type": "RTGS",
        "daily_txn_volume_usd": 18_000_000_000,
        "cross_border_weight":  0.45,
        "cyber_sensitivity":    0.75,
        "liquidity_sensitivity":0.70,
        "volume_sensitivity":   0.85,
        "trade_sensitivity":    0.60,
    },
    {
        "id": "saudi_mada",
        "name": "Saudi mada Payment Network",
        "name_ar": "شبكة مدى للمدفوعات السعودية",
        "country": "SA",
        "service_type": "PAYMENT_RAIL",
        "daily_txn_volume_usd": 22_000_000_000,
        "cross_border_weight":  0.25,
        "cyber_sensitivity":    0.70,
        "liquidity_sensitivity":0.65,
        "volume_sensitivity":   0.90,
        "trade_sensitivity":    0.50,
    },
    {
        "id": "swift_gcc_node",
        "name": "SWIFT GCC Node",
        "name_ar": "عقدة SWIFT الخليجية",
        "country": "AE",
        "service_type": "CROSS_BORDER",
        "daily_txn_volume_usd": 35_000_000_000,
        "cross_border_weight":  0.92,
        "cyber_sensitivity":    0.88,
        "liquidity_sensitivity":0.75,
        "volume_sensitivity":   0.80,
        "trade_sensitivity":    0.85,
    },
    {
        "id": "stc_pay",
        "name": "STC Pay",
        "name_ar": "اس تي سي باي",
        "country": "SA",
        "service_type": "DIGITAL_BANK",
        "daily_txn_volume_usd": 4_000_000_000,
        "cross_border_weight":  0.30,
        "cyber_sensitivity":    0.72,
        "liquidity_sensitivity":0.50,
        "volume_sensitivity":   0.75,
        "trade_sensitivity":    0.40,
    },
    {
        "id": "qatar_npss",
        "name": "Qatar NPSS Payment Hub",
        "name_ar": "مركز دفع NPSS القطري",
        "country": "QA",
        "service_type": "RTGS",
        "daily_txn_volume_usd": 8_000_000_000,
        "cross_border_weight":  0.55,
        "cyber_sensitivity":    0.65,
        "liquidity_sensitivity":0.72,
        "volume_sensitivity":   0.70,
        "trade_sensitivity":    0.65,
    },
    {
        "id": "bahrain_fintech_hub",
        "name": "Bahrain FinTech Bay",
        "name_ar": "خليج البحرين للتقنية المالية",
        "country": "BH",
        "service_type": "DIGITAL_BANK",
        "daily_txn_volume_usd": 1_500_000_000,
        "cross_border_weight":  0.60,
        "cyber_sensitivity":    0.60,
        "liquidity_sensitivity":0.65,
        "volume_sensitivity":   0.55,
        "trade_sensitivity":    0.50,
    },
    {
        "id": "ripple_gcc",
        "name": "RippleNet GCC Corridor",
        "name_ar": "ممر ريبل نت الخليجي",
        "country": "AE",
        "service_type": "CROSS_BORDER",
        "daily_txn_volume_usd": 3_000_000_000,
        "cross_border_weight":  0.96,
        "cyber_sensitivity":    0.68,
        "liquidity_sensitivity":0.60,
        "volume_sensitivity":   0.65,
        "trade_sensitivity":    0.80,
    },
    {
        "id": "tabby_bnpl",
        "name": "Tabby / Tamara BNPL",
        "name_ar": "تابي وتمارا للشراء الآجل",
        "country": "AE",
        "service_type": "CONSUMER",
        "daily_txn_volume_usd": 800_000_000,
        "cross_border_weight":  0.15,
        "cyber_sensitivity":    0.45,
        "liquidity_sensitivity":0.55,
        "volume_sensitivity":   0.60,
        "trade_sensitivity":    0.30,
    },
]

_FINTECH_SCENARIO_AXIS: dict[str, str] = {
    "maritime_trade": "trade_sensitivity",
    "port":           "trade_sensitivity",
    "energy":         "liquidity_sensitivity",
    "cyber_fintech":  "cyber_sensitivity",
    "liquidity":      "liquidity_sensitivity",
    "cross_sector":   "volume_sensitivity",
}

_TOTAL_FINTECH_DAILY_VOLUME: float = sum(
    p["daily_txn_volume_usd"] for p in _FINTECH_REGISTRY
)


def generate_fintech_entities(
    shock_nodes: list[str],
    severity: float,
    sector_exposure: dict[str, float],
    liquidity_stress: dict,
    total_loss_usd: float,
) -> list[dict]:
    """
    Generate deterministic affected_platforms list.

    volume_impact_pct = impact_score * 100 * platform.volume_sensitivity
    api_availability  = (1 - impact_score * 0.40) * 100
    cross_border_stress = impact_score * platform.cross_border_weight
    """
    scenario_type = _detect_scenario_type(shock_nodes)
    sensitivity_axis = _FINTECH_SCENARIO_AXIS.get(scenario_type, "volume_sensitivity")

    ft_exposure_weight = _clamp(sector_exposure.get("fintech", 0.0))
    agg_ft_stress = _clamp(
        float(liquidity_stress.get("aggregate_stress", 0.0)) * 0.75
    )
    cb_factor = _clamp(ft_exposure_weight * 0.80)

    results: list[dict] = []
    for platform in _FINTECH_REGISTRY:
        plat_sensitivity = float(platform[sensitivity_axis])

        # ── Impact Score ──────────────────────────────────────────────
        # impact = 0.30*ft_exp + 0.25*agg_ft_stress + 0.20*severity
        #        + 0.15*plat_sens + 0.10*cb_factor
        raw_score = (
            0.30 * ft_exposure_weight
            + 0.25 * agg_ft_stress
            + 0.20 * severity
            + 0.15 * plat_sensitivity
            + 0.10 * cb_factor
        )
        # Scale by daily volume share (higher-volume platforms → more systemic)
        vol_share = platform["daily_txn_volume_usd"] / _TOTAL_FINTECH_DAILY_VOLUME
        impact_score = _clamp(raw_score * (1.0 + vol_share * 0.8))

        if impact_score < INCLUSION_THRESHOLD:
            continue

        # ── Derived metrics ────────────────────────────────────────────
        volume_impact_pct = round(
            _clamp(impact_score * platform["volume_sensitivity"] * 100, 0.0, 100.0), 2
        )
        api_availability_pct = round(
            _clamp(100.0 - impact_score * 0.40 * 100.0, 50.0, 100.0), 2
        )
        cross_border_stress = round(
            _clamp(impact_score * platform["cross_border_weight"]), 4
        )
        settlement_delay_h = round(
            impact_score * platform["liquidity_sensitivity"] * 12.0, 2
        )   # max ~12 hours settlement delay at peak stress

        fraud_risk_uplift = round(_clamp(impact_score * 0.30), 4)

        # Nominal exposure: lost transaction volume (daily volume * disruption days)
        disruption_days = severity * 3.0  # severity 1.0 → up to 3 days disruption
        exposure_usd = round(
            platform["daily_txn_volume_usd"] * (volume_impact_pct / 100.0) * disruption_days, 2
        )

        results.append({
            "id":                    platform["id"],
            "name":                  platform["name"],
            "name_ar":               platform["name_ar"],
            "country":               platform["country"],
            "service_type":          platform["service_type"],
            "volume_impact_pct":     volume_impact_pct,
            "api_availability":      api_availability_pct,
            "api_availability_pct":  api_availability_pct,
            "settlement_delay_hours":settlement_delay_h,
            "cross_border_stress":   cross_border_stress,
            "fraud_risk_uplift":     fraud_risk_uplift,
            "stress":                round(impact_score, 4),
            "exposure_usd":          exposure_usd,
            "classification":        _classify(impact_score),
            "_score":                impact_score,
        })

    results.sort(key=lambda x: -x["_score"])
    for r in results:
        del r["_score"]
    return results[:MAX_ENTITIES_PER_SECTOR]
