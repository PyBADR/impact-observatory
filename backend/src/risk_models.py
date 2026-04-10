"""
Impact Observatory | مرصد الأثر
Risk Models — pure mathematical functions, no side-effects, no I/O.

All weights imported from src.config. All models are deterministic
given the same inputs. Equations documented inline and in METHODOLOGY.md.

PROHIBITED: Do not import from physics_intelligence_layer, decision_layer,
            explainability, flow_models, or main.
OWNED BY:   This module owns all financial/sector/risk mathematics.
"""
from __future__ import annotations

import math
from typing import Literal

import numpy as np

from src.utils import clamp, classify_stress, weighted_average
from src.config import (
    # Event severity
    ES_W1, ES_W2, ES_W3, ES_W4, ES_MAX_SHOCK_NODES,
    # Sector exposure
    SECTOR_ALPHA, EXPOSURE_V_DIRECT, EXPOSURE_V_INDIRECT,
    EXPOSURE_V_SECOND_HOP, EXPOSURE_V_DEFAULT,
    # Propagation
    PROP_BETA, PROP_LAMBDA, PROP_CUTOFF,
    # Liquidity stress
    LSI_L1, LSI_L2, LSI_L3, LSI_L4,
    LSI_BASE_OUTFLOW_RATE, LSI_BANKING_OUTFLOW_COEFF, LSI_FINTECH_OUTFLOW_COEFF,
    LSI_SOVEREIGN_BUFFER, LSI_CAR_BASE, LSI_LCR_SEVERITY_COEFF,
    LSI_GCC_FOREIGN_DEPENDENCY,
    # Insurance stress
    ISI_M1, ISI_M2, ISI_M3, ISI_M4,
    ISI_CLAIMS_SURGE_COEFF, ISI_BASE_LOSS_RATIO, ISI_SEVERITY_LR_COEFF,
    ISI_EXPENSE_RATIO, ISI_RESERVE_RATIO, ISI_REINSURANCE_COVERAGE,
    ISI_MAX_CLAIMS_SURGE,
    # Financial loss
    SECTOR_THETA, SECTOR_LOSS_ALLOCATION,
    # Confidence
    CONF_R1, CONF_R2, CONF_R3, CONF_R4,
    CONF_WELL_KNOWN_SCENARIOS, CONF_DQ_EXTREME_PENALTY,
    CONF_MC_WELL_KNOWN, CONF_MC_UNKNOWN, CONF_HS_WELL_KNOWN, CONF_HS_UNKNOWN,
    CONF_ST_NODE_PENALTY, CONF_ST_MIN, CONF_ST_MAX,
    # Unified risk score
    URS_G1, URS_G2, URS_G3, URS_G4, URS_G5,
    # Risk thresholds
    RISK_THRESHOLDS,
)

# Cross-sector dependency map (source → dependents)
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


# ──────────────────────────────────────────────────────────────────────────────
# 1. Event Severity
#    Es = w1*I + w2*D + w3*U + w4*G
# ──────────────────────────────────────────────────────────────────────────────

def compute_event_severity(
    base_severity: float,
    n_shock_nodes: int,
    cross_sector: bool,
) -> float:
    """
    Es = w1*I + w2*D + w3*U + w4*G

    I = infrastructure_impact  = n_shock_nodes / ES_MAX_SHOCK_NODES
    D = disruption_scale       = base_severity
    U = utilization_stress     = 1.0 if cross_sector else 0.25
    G = geopolitical_factor    = base_severity * (1 + 0.15*n_shock_nodes/ES_MAX_SHOCK_NODES)

    Returns float in [0, 1].
    """
    base_severity = clamp(base_severity, 0.0, 1.0)

    I = clamp(n_shock_nodes / ES_MAX_SHOCK_NODES, 0.0, 1.0)
    D = base_severity
    U = 1.0 if cross_sector else 0.25
    G = clamp(base_severity * (1.0 + 0.15 * n_shock_nodes / ES_MAX_SHOCK_NODES), 0.0, 1.0)

    es = ES_W1 * I + ES_W2 * D + ES_W3 * U + ES_W4 * G
    return round(clamp(es, 0.0, 1.0), 6)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Sector Exposure
#    Exposure_j = alpha_j * Es * V_j * C_j
# ──────────────────────────────────────────────────────────────────────────────

def compute_sector_exposure(
    shock_nodes: list[str],
    severity: float,
    node_sectors: dict[str, str],
) -> dict[str, float]:
    """
    Exposure_j = alpha_j * Es * V_j * C_j

    alpha_j = SECTOR_ALPHA[j]  (sensitivity coefficient)
    Es      = event_severity (computed from severity + shock count)
    V_j     = vulnerability: 1.0 direct, 0.70 first-hop, 0.35 second-hop, 0.10 default
    C_j     = connectivity = 1 + 0.10 * (shocked_sectors_count - 1), capped at 1.5

    Returns {sector: exposure_score (0-1)} for all known sectors.
    """
    severity = clamp(severity, 0.0, 1.0)

    # severity is already the event severity Es from Stage 3 — use it directly
    # Formula: Exposure_j = alpha_j * Es * V_j * C_j
    es = severity  # passed from simulation_engine after compute_event_severity

    shocked_sectors: set[str] = {node_sectors.get(sn, "infrastructure") for sn in shock_nodes}
    connectivity = clamp(1.0 + 0.10 * (len(shocked_sectors) - 1), 1.0, 1.5)

    exposures: dict[str, float] = {}
    for sector, alpha in SECTOR_ALPHA.items():
        if sector in shocked_sectors:
            V = EXPOSURE_V_DIRECT
        else:
            # Check first-hop and second-hop cross-sector dependency
            V = EXPOSURE_V_DEFAULT
            for shocked in shocked_sectors:
                deps = _CROSS_SECTOR_DEPS.get(shocked, [])
                if sector in deps:
                    V = max(V, EXPOSURE_V_INDIRECT)
                else:
                    for d in deps:
                        if sector in _CROSS_SECTOR_DEPS.get(d, []):
                            V = max(V, EXPOSURE_V_SECOND_HOP)

        exposure = alpha * es * V * connectivity
        exposures[sector] = round(clamp(exposure, 0.0, 1.0), 6)

    return exposures


# ──────────────────────────────────────────────────────────────────────────────
# 3. Propagation Model
#    X_(t+1) = beta * P * X_t + (1 - beta) * X_t + S_t
# ──────────────────────────────────────────────────────────────────────────────

def compute_propagation(
    shock_nodes: list[str],
    severity: float,
    adjacency: dict[str, list[str]],
    horizon_days: int,
) -> list[dict]:
    """
    X_(t+1) = beta * P * X_t + (1 - beta) * X_t + S_t

    beta   = PROP_BETA (0.65)  — propagation coupling
    P      = row-normalised adjacency matrix
    X_t    = state vector at time t
    S_t    = e^(-PROP_LAMBDA * t) * severity  (shock decays over time)

    Returns list of dicts, one per (step, entity) pair where impact > 0.001.
    """
    severity = clamp(severity, 0.0, 1.0)
    all_nodes = list(adjacency.keys())
    if not all_nodes:
        return []

    node_index = {node: i for i, node in enumerate(all_nodes)}
    n = len(all_nodes)

    # Build row-normalised adjacency matrix P
    A = np.zeros((n, n), dtype=np.float64)
    for node, neighbors in adjacency.items():
        if node not in node_index:
            continue
        i = node_index[node]
        for nb in neighbors:
            if nb in node_index:
                A[i, node_index[nb]] = 1.0
    row_sums = A.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    P_mat = A / row_sums

    # Initial state X_0: shock nodes at full severity
    X = np.zeros(n, dtype=np.float64)
    for sn in shock_nodes:
        if sn in node_index:
            X[node_index[sn]] = severity

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
    cumulative = X.copy()

    # Shock node indices for S_t injection
    shock_indices = [node_index[sn] for sn in shock_nodes if sn in node_index]

    for t in range(1, horizon_days + 1):
        # X_(t+1) = beta * P * X_t + (1 - beta) * X_t + S_t
        # S_t is a sparse vector — only shock nodes receive sustained injection
        S_t_vec = np.zeros(n, dtype=np.float64)
        s_val = math.exp(-PROP_LAMBDA * t) * severity
        for idx in shock_indices:
            S_t_vec[idx] = s_val

        X_new = PROP_BETA * (P_mat @ X) + (1.0 - PROP_BETA) * X + S_t_vec
        X_new = np.clip(X_new, 0.0, 1.0)

        for i, node in enumerate(all_nodes):
            impact = float(X_new[i])
            if impact > 0.001:
                mechanism_idx = (i + t) % len(MECHANISMS)
                results.append({
                    "step": t,
                    "entity_id": node,
                    "entity_label": node.replace("_", " ").title(),
                    "impact": round(impact, 4),
                    "propagation_score": round(float(cumulative[i]), 4),
                    "mechanism": MECHANISMS[mechanism_idx],
                    "mechanism_en": MECHANISMS[mechanism_idx],
                })

        cumulative = np.maximum(cumulative, X_new)
        X = X_new

        if X.max() < PROP_CUTOFF:
            break

    results.sort(key=lambda x: (-x["impact"], x["step"]))
    return results[:20]


# ──────────────────────────────────────────────────────────────────────────────
# 4. Liquidity Stress Index
#    LSI = l1*W + l2*F + l3*M + l4*C
# ──────────────────────────────────────────────────────────────────────────────

def compute_liquidity_stress(
    severity: float,
    sector_exposure: dict[str, float],
) -> dict:
    """
    LSI = l1*W + l2*F + l3*M + l4*C

    W = withdrawal_pressure = clamp(outflow_rate * severity, 0, 1)
        outflow_rate = LSI_BASE_OUTFLOW_RATE
                     + LSI_BANKING_OUTFLOW_COEFF * banking_exp
                     + LSI_FINTECH_OUTFLOW_COEFF * fintech_exp
    F = foreign_exposure    = severity * LSI_GCC_FOREIGN_DEPENDENCY
    M = market_stress       = (banking_exp + fintech_exp) / 2
    C = collateral_stress   = severity * max(0, 1 - CAR_ratio / LSI_CAR_BASE)

    Also computes: LCR ratio, CAR ratio, aggregate_stress, time_to_breach.
    """
    severity = clamp(severity, 0.0, 1.0)
    banking_exp = sector_exposure.get("banking", 0.20)
    fintech_exp = sector_exposure.get("fintech", 0.10)

    outflow_rate = clamp(
        LSI_BASE_OUTFLOW_RATE
        + LSI_BANKING_OUTFLOW_COEFF * banking_exp
        + LSI_FINTECH_OUTFLOW_COEFF * fintech_exp,
        0.0, 1.0,
    )
    car_ratio = clamp(LSI_CAR_BASE + max(0.0, 0.05 - severity * 0.04), 0.085, 0.20)
    lcr_ratio = clamp(1.0 - severity * LSI_LCR_SEVERITY_COEFF, 0.0, 2.0)

    W = clamp(outflow_rate * severity, 0.0, 1.0)
    F = clamp(severity * LSI_GCC_FOREIGN_DEPENDENCY, 0.0, 1.0)
    M = clamp((banking_exp + fintech_exp) / 2.0, 0.0, 1.0)
    C = clamp(severity * max(0.0, 1.0 - car_ratio / LSI_CAR_BASE), 0.0, 1.0)

    lsi = clamp(LSI_L1 * W + LSI_L2 * F + LSI_L3 * M + LSI_L4 * C, 0.0, 1.0)

    # Legacy alias fields (backward compat)
    aggregate_stress = lsi
    liquidity_stress = clamp(lsi * 1.10, 0.0, 1.0)

    daily_drain = outflow_rate * severity
    if daily_drain > 0:
        time_to_breach_hours = round(
            (LSI_SOVEREIGN_BUFFER * car_ratio / daily_drain) * 24, 1
        )
    else:
        time_to_breach_hours = 9999.0

    classification = classify_stress(lsi)

    return {
        "lsi": round(lsi, 4),
        "aggregate_stress": round(aggregate_stress, 4),
        "liquidity_stress": round(liquidity_stress, 4),
        "components": {"W": round(W, 4), "F": round(F, 4), "M": round(M, 4), "C": round(C, 4)},
        "car_ratio": round(car_ratio, 4),
        "lcr_ratio": round(lcr_ratio, 4),
        "outflow_rate": round(outflow_rate, 4),
        "time_to_breach_hours": time_to_breach_hours,
        "classification": classification,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 5. Insurance Stress Index
#    ISI = m1*Cf + m2*LR + m3*Re + m4*Od
# ──────────────────────────────────────────────────────────────────────────────

def compute_insurance_stress(
    severity: float,
    sector_exposure: dict[str, float],
) -> dict:
    """
    ISI = m1*Cf + m2*LR + m3*Re + m4*Od

    Cf = claims_frequency_index  = (claims_surge_multiplier - 1) / ISI_MAX_CLAIMS_SURGE
    LR = loss_ratio               = ISI_BASE_LOSS_RATIO + severity * ISI_SEVERITY_LR_COEFF
    Re = reserve_erosion          = severity * (1 - reserve_adequacy_ratio)
    Od = operational_disruption   = severity * insurance_exposure

    Also computes: combined_ratio (IFRS-17), reserve_adequacy, tiv_exposure.
    """
    severity = clamp(severity, 0.0, 1.0)
    insurance_exp = sector_exposure.get("insurance", 0.15)
    energy_exp = sector_exposure.get("energy", 0.20)

    claims_surge_multiplier = 1.0 + severity * ISI_CLAIMS_SURGE_COEFF
    tiv_exposure = clamp(insurance_exp + energy_exp * 0.30, 0.0, 1.0)
    reserve_adequacy = clamp(
        ISI_RESERVE_RATIO / (tiv_exposure * severity + 0.01),
        0.0, 2.0,
    )

    Cf = clamp((claims_surge_multiplier - 1.0) / ISI_MAX_CLAIMS_SURGE, 0.0, 1.0)
    LR = clamp(ISI_BASE_LOSS_RATIO + severity * ISI_SEVERITY_LR_COEFF, 0.0, 1.5)
    Re = clamp(severity * max(0.0, 1.0 - reserve_adequacy), 0.0, 1.0)
    Od = clamp(severity * insurance_exp, 0.0, 1.0)

    isi = clamp(ISI_M1 * Cf + ISI_M2 * LR + ISI_M3 * Re + ISI_M4 * Od, 0.0, 1.0)

    loss_ratio_val = LR
    combined_ratio = round(loss_ratio_val + ISI_EXPENSE_RATIO, 4)
    classification = classify_stress(isi)

    return {
        "isi": round(isi, 4),
        "severity_index": round(isi, 4),
        "components": {
            "Cf": round(Cf, 4),
            "LR": round(LR, 4),
            "Re": round(Re, 4),
            "Od": round(Od, 4),
        },
        "claims_surge_multiplier": round(claims_surge_multiplier, 4),
        "combined_ratio": combined_ratio,
        "reserve_adequacy": round(reserve_adequacy, 4),
        "tiv_exposure": round(tiv_exposure, 4),
        "loss_ratio": round(loss_ratio_val, 4),
        "classification": classification,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 6. Financial Loss Model
#    NormalizedLoss_j = Exposure_j * ImpactFactor_(j,t) * AssetBase_j * theta_j
# ──────────────────────────────────────────────────────────────────────────────

def compute_financial_losses(
    severity: float,
    scenario_base_loss: float,
    propagation: list[dict],
    sector_exposure: dict[str, float],
) -> list[dict]:
    """
    NormalizedLoss_j = Exposure_j * ImpactFactor_(j,t) * AssetBase_j * theta_j

    ImpactFactor_(j,t) = severity² * propagation_factor_j
    AssetBase_j        = scenario_base_loss * SECTOR_LOSS_ALLOCATION[sector_j]
    theta_j            = SECTOR_THETA[sector_j]

    Loss split: direct 60%, indirect 28%, systemic 12%.
    Returns top-20 entities sorted by loss_usd descending.
    """
    severity = clamp(severity, 0.0, 1.0)

    # Aggregate peak propagation factor per entity
    prop_by_entity: dict[str, float] = {}
    for row in propagation:
        eid = row["entity_id"]
        prop_by_entity[eid] = max(prop_by_entity.get(eid, 0.0), row["impact"])

    results: list[dict] = []
    entities_seen: set[str] = set()

    for row in propagation:
        eid = row["entity_id"]
        if eid in entities_seen:
            continue
        entities_seen.add(eid)

        sector = _infer_sector(eid)
        exposure = sector_exposure.get(sector, 0.10)
        prop_factor = prop_by_entity.get(eid, 0.05)
        asset_base = scenario_base_loss * SECTOR_LOSS_ALLOCATION.get(sector, 0.03)
        theta = SECTOR_THETA.get(sector, 1.00)
        impact_factor = (severity ** 2) * prop_factor

        total_loss = exposure * impact_factor * asset_base * theta

        direct = total_loss * 0.60
        indirect = total_loss * 0.28
        systemic = total_loss * 0.12

        stress_score = clamp(prop_factor * severity * (1.0 + exposure), 0.0, 1.0)
        classification = classify_stress(stress_score)

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
            "theta": theta,
        })

    results.sort(key=lambda x: -x["loss_usd"])
    return results[:20]


def _infer_sector(entity_id: str) -> str:
    """Heuristically infer sector from node id."""
    eid = entity_id.lower()
    if any(k in eid for k in ("bank", "financial", "credit", "monetary")):
        return "banking"
    if any(k in eid for k in ("oil", "gas", "lng", "energy", "petro", "opec", "aramco", "adnoc")):
        return "energy"
    if any(k in eid for k in ("port", "ship", "maritime", "hormuz", "lane", "salalah", "dammam")):
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


# ──────────────────────────────────────────────────────────────────────────────
# 7. Confidence Score
#    Conf = r1*DQ + r2*MC + r3*HS + r4*ST
# ──────────────────────────────────────────────────────────────────────────────

def compute_confidence_score(
    n_shock_nodes: int,
    severity: float,
    scenario_id: str,
) -> float:
    """
    Conf = r1*DQ + r2*MC + r3*HS + r4*ST

    DQ = data_quality          — degrades at extreme severities (< 0.2 or > 0.8)
    MC = model_coverage        — 0.92 for well-known GCC scenarios, 0.72 otherwise
    HS = historical_similarity — 0.88 for scenarios with precedent, 0.65 otherwise
    ST = scenario_tractability — degrades by CONF_ST_NODE_PENALTY per additional shock node
    """
    severity = clamp(severity, 0.0, 1.0)

    DQ = clamp(1.0 - abs(severity - 0.5) * CONF_DQ_EXTREME_PENALTY, 0.50, 0.98)
    MC = CONF_MC_WELL_KNOWN if scenario_id in CONF_WELL_KNOWN_SCENARIOS else CONF_MC_UNKNOWN
    HS = CONF_HS_WELL_KNOWN if scenario_id in CONF_WELL_KNOWN_SCENARIOS else CONF_HS_UNKNOWN
    ST = clamp(
        1.0 - (n_shock_nodes - 1) * CONF_ST_NODE_PENALTY,
        CONF_ST_MIN, CONF_ST_MAX,
    )

    conf = weighted_average([DQ, MC, HS, ST], [CONF_R1, CONF_R2, CONF_R3, CONF_R4])
    return round(clamp(conf, 0.0, 1.0), 4)


# ──────────────────────────────────────────────────────────────────────────────
# 8. Unified Risk Score
#    URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropagationScore + g5*LossNorm
# ──────────────────────────────────────────────────────────────────────────────

def compute_unified_risk_score(
    severity: float,
    propagation_score: float,
    liquidity_stress: float,
    insurance_stress: float,
    sector_exposure: dict[str, float],
    event_severity: float | None = None,
) -> dict:
    """
    URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropagationScore + g5*LossNorm

    Es              = event_severity (if provided) else computed from severity
    AvgExposure     = mean of all sector_exposure values
    AvgStress       = (liquidity_stress + insurance_stress) / 2
    PropagationScore = propagation_score (capped at 1.0)
    LossNorm        = severity² (normalised loss proxy)

    Returns dict with score, components, risk_level, classification.
    """
    severity = clamp(severity, 0.0, 1.0)

    Es = event_severity if event_severity is not None else severity
    Es = clamp(Es, 0.0, 1.0)

    # Peak sector exposure (max across all sectors — captures worst-hit sector)
    exposures = list(sector_exposure.values()) if sector_exposure else [0.0]
    peak_exposure = clamp(float(np.max(exposures)), 0.0, 1.0)

    # Peak stress (max of LSI and ISI — captures which stress axis dominates)
    peak_stress = clamp(max(liquidity_stress, insurance_stress), 0.0, 1.0)

    # Scale propagation score by sqrt(severity) so low-severity scenarios
    # don't over-represent sustained shock injection as risk
    prop_score = clamp(propagation_score * math.sqrt(severity), 0.0, 1.0)
    loss_norm = severity ** 2

    score = clamp(
        URS_G1 * Es
        + URS_G2 * peak_exposure
        + URS_G3 * peak_stress
        + URS_G4 * prop_score
        + URS_G5 * loss_norm,
        0.0, 1.0,
    )
    risk_level = classify_risk(score)

    return {
        "score": round(score, 4),
        "components": {
            "Es": round(Es, 4),
            "PeakExposure": round(peak_exposure, 4),
            "PeakStress": round(peak_stress, 4),
            "PropagationScore": round(prop_score, 4),
            "LossNorm": round(loss_norm, 4),
        },
        "risk_level": risk_level,
        "classification": risk_level,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 9. Risk Classification Helper
# ──────────────────────────────────────────────────────────────────────────────

def classify_risk(score: float) -> str:
    """Map a 0–1 risk score to a classification label using RISK_THRESHOLDS."""
    return classify_stress(score)
