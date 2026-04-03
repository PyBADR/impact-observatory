"""
Impact Observatory | مرصد الأثر
Risk Models — pure mathematical functions, no side-effects, no I/O.

All models are deterministic given the same inputs. Equations documented
inline and in METHODOLOGY.md.
"""
from __future__ import annotations

import math
from typing import Literal

import numpy as np

from src.utils import clamp, classify_stress, weighted_average

# ---------------------------------------------------------------------------
# Risk threshold table (single source of truth)
# ---------------------------------------------------------------------------

RISK_THRESHOLDS: dict[str, tuple[float, float]] = {
    "NOMINAL":  (0.00, 0.20),
    "LOW":      (0.20, 0.35),
    "GUARDED":  (0.35, 0.50),
    "ELEVATED": (0.50, 0.65),
    "HIGH":     (0.65, 0.80),
    "SEVERE":   (0.80, 1.01),
}

# Sector sensitivity weights (fraction of GDP exposure per sector)
_SECTOR_WEIGHTS: dict[str, float] = {
    "energy":         0.28,
    "maritime":       0.18,
    "banking":        0.20,
    "insurance":      0.08,
    "fintech":        0.06,
    "logistics":      0.10,
    "infrastructure": 0.05,
    "government":     0.03,
    "healthcare":     0.02,
}

# Cross-sector dependency matrix (source_sector → [dependent_sectors])
_CROSS_SECTOR_DEPS: dict[str, list[str]] = {
    "energy":         ["banking", "maritime", "logistics", "fintech"],
    "maritime":       ["energy", "logistics", "banking"],
    "banking":        ["fintech", "insurance", "government"],
    "insurance":      ["banking", "fintech"],
    "fintech":        ["banking", "insurance"],
    "logistics":      ["maritime", "energy"],
    "infrastructure": ["energy", "banking"],
    "government":     ["banking", "fintech"],
    "healthcare":     ["banking", "logistics"],
}


# ---------------------------------------------------------------------------
# 1. Event Severity Model
# ---------------------------------------------------------------------------

def compute_event_severity(
    base_severity: float,
    n_shock_nodes: int,
    cross_sector: bool,
) -> float:
    """
    S = base_severity * cascade_multiplier * (1 + regional_amplification)

    cascade_multiplier  = 1 + 0.15*n_shock_nodes + 0.10*cross_sector_factor
    regional_amplification = base_severity * 0.15  (GCC systemic interconnect)

    Returns float in [0, 1].
    """
    base_severity = clamp(base_severity, 0.0, 1.0)
    cross_sector_factor = 1.0 if cross_sector else 0.0

    cascade_multiplier = 1.0 + 0.15 * n_shock_nodes + 0.10 * cross_sector_factor
    regional_amplification = base_severity * 0.15

    severity = base_severity * cascade_multiplier * (1.0 + regional_amplification)
    return clamp(severity, 0.0, 1.0)


# ---------------------------------------------------------------------------
# 2. Sector Exposure Model
# ---------------------------------------------------------------------------

def compute_sector_exposure(
    shock_nodes: list[str],
    severity: float,
    node_sectors: dict[str, str],
) -> dict[str, float]:
    """
    E_i = sum_k( w_k * dependency_ik * proximity_i )

    proximity_i is computed from hop distance to nearest shock node.
    dependency_ik  = cross-sector dependency weight (0.1–1.0).
    Returns {sector: exposure_score} for all known sectors.
    """
    severity = clamp(severity, 0.0, 1.0)

    # Determine directly-shocked sectors
    shocked_sectors: set[str] = {node_sectors.get(n, "infrastructure") for n in shock_nodes}

    exposures: dict[str, float] = {}
    for sector, weight in _SECTOR_WEIGHTS.items():
        if sector in shocked_sectors:
            # Direct exposure: full weight * severity
            proximity_factor = 1.0
        else:
            # Indirect: check cross-sector dependency paths
            dep_score = 0.0
            for shocked in shocked_sectors:
                deps = _CROSS_SECTOR_DEPS.get(shocked, [])
                if sector in deps:
                    dep_score = max(dep_score, 0.70)
                else:
                    # Second-hop
                    for d in deps:
                        if sector in _CROSS_SECTOR_DEPS.get(d, []):
                            dep_score = max(dep_score, 0.35)
            proximity_factor = dep_score if dep_score > 0 else 0.10

        exposure = weight * proximity_factor * severity
        exposures[sector] = clamp(exposure, 0.0, 1.0)

    return exposures


# ---------------------------------------------------------------------------
# 3. Propagation Model
# ---------------------------------------------------------------------------

def compute_propagation(
    shock_nodes: list[str],
    severity: float,
    adjacency: dict[str, list[str]],
    horizon_days: int,
) -> list[dict]:
    """
    Discrete-time propagation:
      P_i(t) = P_i(0) * e^(-lambda*t) + sum_j( A_ij * P_j(t-1) )
      lambda = 0.05  (decay rate)

    Simulates up to horizon_days steps or until all P < 0.01.
    Returns list of dicts, one per (step, entity) pair where impact > 0.001.
    """
    severity = clamp(severity, 0.0, 1.0)
    LAMBDA = 0.05
    all_nodes = list(adjacency.keys())

    if not all_nodes:
        return []

    # Map node_id → index
    node_index = {n: i for i, n in enumerate(all_nodes)}
    n = len(all_nodes)

    # Build adjacency matrix with weights (1/degree normalised)
    A = np.zeros((n, n), dtype=np.float64)
    for node, neighbors in adjacency.items():
        if node not in node_index:
            continue
        i = node_index[node]
        for nb in neighbors:
            if nb in node_index:
                j = node_index[nb]
                A[i, j] = 1.0

    # Normalise rows (out-degree)
    row_sums = A.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    A = A / row_sums

    # Initial state: shock nodes at full severity
    P = np.zeros(n, dtype=np.float64)
    for sn in shock_nodes:
        if sn in node_index:
            P[node_index[sn]] = severity

    MECHANISMS = [
        "Direct shock absorption",
        "Counter-party credit exposure",
        "Liquidity contagion",
        "Supply chain disruption",
        "Market sentiment spillover",
        "Operational dependency failure",
        "Regulatory capital stress",
        "Cross-collateral trigger",
        "Currency pressure amplification",
        "Network centrality amplification",
    ]

    results: list[dict] = []
    cumulative = P.copy()

    for t in range(1, horizon_days + 1):
        P_new = P * math.exp(-LAMBDA * t) + A @ P
        P_new = np.clip(P_new, 0.0, 1.0)

        for i, node in enumerate(all_nodes):
            impact = float(P_new[i])
            if impact > 0.001:
                mechanism_idx = (i + t) % len(MECHANISMS)
                results.append({
                    "step": t,
                    "entity_id": node,
                    "entity_label": node.replace("_", " ").title(),
                    "impact": round(impact, 4),
                    "propagation_score": round(float(cumulative[i]), 4),
                    "mechanism": MECHANISMS[mechanism_idx],
                })

        cumulative = np.maximum(cumulative, P_new)
        P = P_new

        # Early exit if propagation has attenuated
        if P.max() < 0.005:
            break

    # Sort by impact descending, cap at 20 rows
    results.sort(key=lambda x: (-x["impact"], x["step"]))
    return results[:20]


# ---------------------------------------------------------------------------
# 4. Liquidity Stress Index
# ---------------------------------------------------------------------------

def compute_liquidity_stress(
    severity: float,
    sector_exposure: dict[str, float],
) -> dict:
    """
    Liquidity Stress Index (Basel III informed):

    L = (outflow_rate * severity) / (buffer * CAR_ratio)

    outflow_rate      = 0.25 + 0.50 * banking_exposure
    buffer            = 0.85  (GCC sovereign buffer factor)
    CAR_ratio         = 0.105 + clamp(0.05 - severity * 0.04, 0, 0.05)
    LCR_ratio         = 1.0 - severity * 0.65

    time_to_breach_hours = (buffer / outflow_rate) * 24
    """
    severity = clamp(severity, 0.0, 1.0)
    banking_exp = sector_exposure.get("banking", 0.2)
    fintech_exp = sector_exposure.get("fintech", 0.1)

    outflow_rate = clamp(0.25 + 0.50 * banking_exp + 0.15 * fintech_exp, 0.0, 1.0)
    buffer = 0.85
    car_ratio = clamp(0.105 + max(0.0, 0.05 - severity * 0.04), 0.085, 0.20)
    lcr_ratio = clamp(1.0 - severity * 0.65, 0.0, 2.0)

    aggregate_stress = clamp(
        (outflow_rate * severity) / (buffer * car_ratio),
        0.0, 1.0,
    )
    liquidity_stress = clamp(aggregate_stress * 1.10, 0.0, 1.0)

    # Time to LCR breach (hours)
    daily_drain = outflow_rate * severity
    if daily_drain > 0:
        time_to_breach_hours = round((buffer * car_ratio / daily_drain) * 24, 1)
    else:
        time_to_breach_hours = 9999.0

    classification = classify_stress(aggregate_stress)

    return {
        "aggregate_stress": round(aggregate_stress, 4),
        "liquidity_stress": round(liquidity_stress, 4),
        "car_ratio": round(car_ratio, 4),
        "lcr_ratio": round(lcr_ratio, 4),
        "outflow_rate": round(outflow_rate, 4),
        "time_to_breach_hours": time_to_breach_hours,
        "classification": classification,
    }


# ---------------------------------------------------------------------------
# 5. Insurance Stress Index
# ---------------------------------------------------------------------------

def compute_insurance_stress(
    severity: float,
    sector_exposure: dict[str, float],
) -> dict:
    """
    Insurance Stress Index (IFRS-17 informed):

    IS = (claims_surge * tiv_exposure) / (reserve_ratio * reinsurance_coverage)

    claims_surge_multiplier = 1.0 + severity * 2.5
    tiv_exposure            = insurance_exposure (% of TIV at risk)
    reserve_ratio           = 0.18 (industry min)
    reinsurance_coverage    = 0.60 (GCC average retention)
    combined_ratio          = loss_ratio + expense_ratio
    """
    severity = clamp(severity, 0.0, 1.0)
    insurance_exp = sector_exposure.get("insurance", 0.15)
    energy_exp = sector_exposure.get("energy", 0.2)

    claims_surge_multiplier = 1.0 + severity * 2.5
    tiv_exposure = clamp(insurance_exp + energy_exp * 0.3, 0.0, 1.0)
    reserve_ratio = 0.18
    reinsurance_coverage = 0.60

    severity_index = clamp(
        (claims_surge_multiplier * tiv_exposure) / (reserve_ratio * reinsurance_coverage),
        0.0, 1.0,
    )

    # IFRS-17 combined ratio: loss ratio + expense ratio
    loss_ratio = clamp(0.55 + severity * 0.35, 0.0, 1.5)
    expense_ratio = 0.28
    combined_ratio = round(loss_ratio + expense_ratio, 4)

    # Reserve adequacy: 1.0 = fully adequate, <1 = deficient
    reserve_adequacy = clamp(
        reserve_ratio / (tiv_exposure * severity + 0.01),
        0.0, 2.0,
    )
    classification = classify_stress(severity_index)

    return {
        "severity_index": round(severity_index, 4),
        "claims_surge_multiplier": round(claims_surge_multiplier, 4),
        "combined_ratio": combined_ratio,
        "reserve_adequacy": round(reserve_adequacy, 4),
        "tiv_exposure": round(tiv_exposure, 4),
        "loss_ratio": round(loss_ratio, 4),
        "classification": classification,
    }


# ---------------------------------------------------------------------------
# 6. Financial Loss Model
# ---------------------------------------------------------------------------

# Sector-level base loss allocation (fraction of total scenario base loss)
_SECTOR_LOSS_ALLOCATION: dict[str, float] = {
    "energy":         0.30,
    "maritime":       0.20,
    "banking":        0.18,
    "insurance":      0.10,
    "logistics":      0.08,
    "fintech":        0.06,
    "infrastructure": 0.05,
    "government":     0.02,
    "healthcare":     0.01,
}


def compute_financial_losses(
    severity: float,
    scenario_base_loss: float,
    propagation: list[dict],
    sector_exposure: dict[str, float],
) -> list[dict]:
    """
    Loss_i = base_loss * severity^2 * sector_weight_i * propagation_factor_i

    Direct loss:   loss * 0.60
    Indirect loss: loss * 0.28
    Systemic:      loss * 0.12

    Returns top-20 entities sorted by loss_usd descending.
    """
    severity = clamp(severity, 0.0, 1.0)
    CLASSIFICATIONS = ["NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"]

    # Aggregate propagation factors per entity
    prop_by_entity: dict[str, float] = {}
    for row in propagation:
        eid = row["entity_id"]
        prop_by_entity[eid] = max(prop_by_entity.get(eid, 0.0), row["impact"])

    results: list[dict] = []

    # Build synthetic entity list from propagation results
    entities_seen: set[str] = set()
    for row in propagation:
        eid = row["entity_id"]
        if eid in entities_seen:
            continue
        entities_seen.add(eid)

        # Infer sector from entity id
        sector = _infer_sector(eid)
        sector_weight = _SECTOR_LOSS_ALLOCATION.get(sector, 0.03)
        exposure = sector_exposure.get(sector, 0.1)
        prop_factor = prop_by_entity.get(eid, 0.05)

        raw_loss = scenario_base_loss * (severity ** 2) * sector_weight * prop_factor * (1 + exposure)

        direct = raw_loss * 0.60
        indirect = raw_loss * 0.28
        systemic = raw_loss * 0.12
        total_loss = direct + indirect + systemic

        stress_score = clamp(prop_factor * severity * (1 + exposure), 0.0, 1.0)
        classification = classify_stress(stress_score)

        # Estimate peak day from step in propagation
        steps = [r["step"] for r in propagation if r["entity_id"] == eid]
        peak_day = min(steps) if steps else 3

        results.append({
            "entity_id": eid,
            "entity_label": eid.replace("_", " ").title(),
            "loss_usd": round(total_loss, 2),
            "direct_loss_usd": round(direct, 2),
            "indirect_loss_usd": round(indirect, 2),
            "systemic_loss_usd": round(systemic, 2),
            "stress_score": round(stress_score, 4),
            "classification": classification,
            "peak_day": peak_day,
            "sector": sector,
            "propagation_factor": round(prop_factor, 4),
        })

    results.sort(key=lambda x: -x["loss_usd"])
    return results[:20]


def _infer_sector(entity_id: str) -> str:
    """Heuristically infer sector from node id."""
    eid = entity_id.lower()
    if any(k in eid for k in ("bank", "financial", "credit", "monetary")):
        return "banking"
    if any(k in eid for k in ("oil", "gas", "lng", "energy", "petro", "opec")):
        return "energy"
    if any(k in eid for k in ("port", "ship", "maritime", "hormuz", "lane")):
        return "maritime"
    if any(k in eid for k in ("insur", "takaful", "reinsur")):
        return "insurance"
    if any(k in eid for k in ("fintech", "payment", "swift", "digital")):
        return "fintech"
    if any(k in eid for k in ("logistic", "supply", "cargo", "freight")):
        return "logistics"
    if any(k in eid for k in ("infra", "telecom", "power", "water", "grid")):
        return "infrastructure"
    if any(k in eid for k in ("gov", "ministry", "central", "regul")):
        return "government"
    return "infrastructure"


# ---------------------------------------------------------------------------
# 7. Confidence Score
# ---------------------------------------------------------------------------

def compute_confidence_score(
    n_shock_nodes: int,
    severity: float,
    scenario_id: str,
) -> float:
    """
    C = w1*data_quality + w2*model_coverage + w3*scenario_precedent + w4*node_completeness

    Weights: [0.30, 0.25, 0.25, 0.20]
    """
    W = [0.30, 0.25, 0.25, 0.20]

    # data_quality: degrades slightly at extreme severities
    data_quality = clamp(1.0 - abs(severity - 0.5) * 0.4, 0.50, 0.98)

    # model_coverage: GCC-calibrated scenarios get higher coverage
    well_known_scenarios = {
        "hormuz_chokepoint_disruption",
        "uae_banking_crisis",
        "gcc_cyber_attack",
        "saudi_oil_shock",
        "qatar_lng_disruption",
        "bahrain_sovereign_stress",
        "kuwait_fiscal_shock",
        "oman_port_closure",
    }
    model_coverage = 0.92 if scenario_id in well_known_scenarios else 0.72

    # scenario_precedent: known scenarios have historical precedent
    scenario_precedent = 0.88 if scenario_id in well_known_scenarios else 0.65

    # node_completeness: more shock nodes = slightly lower per-node confidence
    node_completeness = clamp(1.0 - (n_shock_nodes - 1) * 0.04, 0.55, 0.97)

    score = weighted_average(
        [data_quality, model_coverage, scenario_precedent, node_completeness],
        W,
    )
    return round(clamp(score, 0.0, 1.0), 4)


# ---------------------------------------------------------------------------
# 8. Unified Risk Score
# ---------------------------------------------------------------------------

def compute_unified_risk_score(
    severity: float,
    propagation_score: float,
    liquidity_stress: float,
    insurance_stress: float,
    sector_exposure: dict[str, float],
) -> dict:
    """
    R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U

    G = geopolitical   (severity proxy)
    P = propagation    (attenuated to keep score proportional to input severity)
    N = network_centrality (avg sector exposure)
    L = liquidity stress   (attenuated)
    T = threat_field   (insurance * severity)
    U = utilization    (max sector exposure, attenuated)

    Calibrated weights ensure score spreads across [0,1] proportionally to
    input severity so that:
      sev=0.2 → NOMINAL/LOW, sev=0.5 → GUARDED/ELEVATED, sev=0.8 → HIGH/SEVERE.
    """
    severity = clamp(severity, 0.0, 1.0)
    W = [0.30, 0.25, 0.10, 0.15, 0.10, 0.10]

    G = severity
    # Attenuate propagation score: it tends to be high even at low severity
    P = clamp(propagation_score * severity, 0.0, 1.0)
    exposures = list(sector_exposure.values()) or [0.0]
    # Attenuate network: sector exposure is already scaled by severity internally
    N = clamp(float(np.mean(exposures)), 0.0, 1.0)
    # Attenuate liquidity stress similarly
    L = clamp(liquidity_stress * severity, 0.0, 1.0)
    T = clamp(insurance_stress * severity * 0.5, 0.0, 1.0)
    U = clamp(float(np.max(exposures)) * 0.8, 0.0, 1.0)

    components = {"G": G, "P": P, "N": N, "L": L, "T": T, "U": U}
    score = clamp(
        W[0] * G + W[1] * P + W[2] * N + W[3] * L + W[4] * T + W[5] * U,
        0.0, 1.0,
    )
    risk_level = classify_risk(score)

    return {
        "score": round(score, 4),
        "components": {k: round(v, 4) for k, v in components.items()},
        "risk_level": risk_level,
        "classification": risk_level,
    }


# ---------------------------------------------------------------------------
# 9. Risk classification helper (alias)
# ---------------------------------------------------------------------------

def classify_risk(score: float) -> str:
    """Map a 0-1 risk score to a classification label."""
    return classify_stress(score)
