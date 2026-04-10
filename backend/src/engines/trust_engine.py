"""
Decision Trust System — Phase 2 Engines

Five trust computation modules:
  1. Action-Level Confidence Engine  → per-action confidence scores
  2. Model Dependency Engine         → data completeness, signal reliability, sensitivity
  3. Validation Requirement Engine   → whether human/regulatory validation is needed
  4. Confidence Breakdown Layer      → human-readable drivers explaining confidence
  5. Decision Risk Envelope          → downside, reversibility, time sensitivity

All engines are pure functions. They never throw. They return safe defaults
for missing or malformed input. Constants come from config.py.
"""

from __future__ import annotations

from src import config

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _sn(v, fb: float = 0.0) -> float:
    """Safe number: coerce to float, return fallback for None/non-finite."""
    if v is None:
        return fb
    try:
        n = float(v)
        return n if n == n and abs(n) != float("inf") else fb  # NaN / Inf guard
    except (TypeError, ValueError):
        return fb


def _ss(v, fb: str = "") -> str:
    """Safe string."""
    if v is None:
        return fb
    s = str(v).strip()
    return s if s else fb


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _label(score: float) -> str:
    """Confidence label: HIGH / MEDIUM / LOW."""
    if score >= config.TRUST_HIGH_THRESHOLD:
        return "HIGH"
    if score < config.TRUST_LOW_THRESHOLD:
        return "LOW"
    return "MEDIUM"


def _sensitivity_label(severity: float, sectors_count: int) -> str:
    """Assumption sensitivity based on scenario severity and sector breadth."""
    if severity >= 0.75 or sectors_count >= 5:
        return "HIGH"
    if severity >= 0.40 or sectors_count >= 3:
        return "MEDIUM"
    return "LOW"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Action-Level Confidence Engine
# ═══════════════════════════════════════════════════════════════════════════════

def compute_action_confidence(
    actions: list[dict],
    *,
    global_confidence: float = 0.85,
    propagation_score: float = 0.0,
    counterfactual_consistency: str = "CONSISTENT",
    data_completeness: float = 0.70,
    severity: float = 0.5,
) -> list[dict]:
    """Compute per-action confidence scores.

    Returns list of:
      {action_id, confidence_score, confidence_label}

    Confidence per action =
      W_SIG * signal_strength +
      W_DATA * data_completeness +
      W_PROP * propagation_confidence +
      W_CF * counterfactual_stability
    """
    results = []
    # Counterfactual stability: CONSISTENT → 0.95, CORRECTED_COSTLY → 0.70, else 0.50
    cf_map = {"CONSISTENT": 0.95, "CORRECTED_COSTLY": 0.70, "CORRECTED_INCONSISTENCY": 0.50}
    cf_stability = cf_map.get(counterfactual_consistency, 0.70)

    # Propagation confidence: normalise propagation_score (0–1)
    prop_conf = _clamp(_sn(propagation_score))

    for action in actions:
        if not isinstance(action, dict):
            continue

        action_id = _ss(action.get("id") or action.get("action_id"), f"action_{len(results)}")

        # Signal strength: derived from action's urgency & confidence
        action_urgency = _clamp(_sn(action.get("urgency")))
        action_confidence = _clamp(_sn(action.get("confidence"), 0.80))
        signal_strength = (action_confidence * 0.6 + action_urgency * 0.2 + _clamp(_sn(global_confidence)) * 0.2)

        # Data completeness: sector-specific
        sector = _ss(action.get("sector"), "cross-sector").lower()
        sector_data = config.TRUST_SECTOR_DATA_COMPLETENESS.get(sector, data_completeness)

        # Per-action confidence formula
        raw = (
            config.TRUST_W_SIGNAL * _clamp(signal_strength)
            + config.TRUST_W_DATA * _clamp(sector_data)
            + config.TRUST_W_PROPAGATION * _clamp(prop_conf)
            + config.TRUST_W_COUNTERFACTUAL * _clamp(cf_stability)
        )

        # Severity penalty: extreme scenarios reduce confidence
        if severity >= 0.85:
            raw *= 0.90
        elif severity >= 0.70:
            raw *= 0.95

        score = _clamp(round(raw, 4))
        results.append({
            "action_id": action_id,
            "confidence_score": score,
            "confidence_label": _label(score),
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Model Dependency Engine
# ═══════════════════════════════════════════════════════════════════════════════

def compute_model_dependency(
    *,
    sectors_affected: list[str] | None = None,
    severity: float = 0.5,
    propagation_score: float = 0.0,
    global_confidence: float = 0.85,
) -> dict:
    """Compute model dependency metrics.

    Returns:
      {data_completeness, signal_reliability, assumption_sensitivity}
    """
    sectors = sectors_affected or []

    # Data completeness: weighted average across affected sectors
    if sectors:
        sector_scores = [
            config.TRUST_SECTOR_DATA_COMPLETENESS.get(s.lower(), 0.60)
            for s in sectors
        ]
        data_completeness = round(sum(sector_scores) / len(sector_scores), 4)
    else:
        data_completeness = 0.60

    # Severity degrades data completeness (extreme events have more unknowns)
    if severity >= 0.80:
        data_completeness *= 0.85
    elif severity >= 0.60:
        data_completeness *= 0.92
    data_completeness = _clamp(round(data_completeness, 4))

    # Signal reliability: blend of global confidence and propagation clarity
    prop = _clamp(_sn(propagation_score))
    conf = _clamp(_sn(global_confidence))
    signal_reliability = _clamp(round(conf * 0.6 + prop * 0.4, 4))

    # Assumption sensitivity
    sensitivity = _sensitivity_label(severity, len(sectors))

    return {
        "data_completeness": data_completeness,
        "signal_reliability": signal_reliability,
        "assumption_sensitivity": sensitivity,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Validation Requirement Engine
# ═══════════════════════════════════════════════════════════════════════════════

def compute_validation(
    *,
    global_confidence: float = 0.85,
    total_loss_usd: float = 0.0,
    data_completeness: float = 0.70,
    risk_level: str = "MODERATE",
    severity: float = 0.5,
    immediate_action_count: int = 0,
) -> dict:
    """Determine whether human/regulatory validation is required.

    Returns:
      {required, reason, validation_type}
    """
    reasons = []
    vtype = "NONE"

    # Rule 1: Low confidence
    if _sn(global_confidence) < config.TRUST_VALIDATION_CONFIDENCE_FLOOR:
        reasons.append(f"Global confidence ({global_confidence:.0%}) below threshold")
        vtype = "RISK"

    # Rule 2: High financial exposure
    loss = _sn(total_loss_usd)
    if loss >= config.TRUST_VALIDATION_LOSS_THRESHOLD_USD:
        reasons.append(f"Financial exposure (${loss/1e6:.0f}M) exceeds validation threshold")
        vtype = "OPERATIONAL" if vtype == "NONE" else vtype

    # Rule 3: Regulatory-sensitive scenario
    if risk_level in ("HIGH", "SEVERE"):
        reasons.append(f"Risk level {risk_level} triggers regulatory review")
        vtype = "REGULATORY"

    # Rule 4: Low data completeness
    if _sn(data_completeness) < config.TRUST_VALIDATION_DATA_FLOOR:
        reasons.append(f"Data completeness ({data_completeness:.0%}) below acceptable floor")
        if vtype == "NONE":
            vtype = "RISK"

    # Rule 5: Extreme severity
    if severity >= 0.85:
        reasons.append("Extreme severity scenario requires board-level validation")
        vtype = "REGULATORY"

    required = len(reasons) > 0
    reason = "; ".join(reasons) if reasons else "All metrics within acceptable bounds"

    return {
        "required": required,
        "reason": reason,
        "validation_type": vtype,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Confidence Breakdown Layer
# ═══════════════════════════════════════════════════════════════════════════════

def build_confidence_breakdown(
    *,
    global_confidence: float = 0.85,
    data_completeness: float = 0.70,
    signal_reliability: float = 0.80,
    propagation_score: float = 0.0,
    counterfactual_consistency: str = "CONSISTENT",
    severity: float = 0.5,
    sectors_affected: list[str] | None = None,
    risk_level: str = "MODERATE",
) -> dict:
    """Build human-readable confidence drivers.

    Returns:
      {drivers: [...]}  — minimum 2 drivers, reflecting real context.
    """
    drivers: list[str] = []
    sectors = sectors_affected or []

    # Signal strength
    if _sn(global_confidence) >= 0.80:
        drivers.append("strong macro signal from well-calibrated scenario")
    elif _sn(global_confidence) >= 0.60:
        drivers.append("moderate macro signal — some calibration uncertainty")
    else:
        drivers.append("weak macro signal — limited scenario calibration data")

    # Data completeness
    dc = _sn(data_completeness)
    if dc >= 0.80:
        drivers.append("high data coverage across affected sectors")
    elif dc >= 0.60:
        weak_sectors = [
            s for s in sectors
            if config.TRUST_SECTOR_DATA_COMPLETENESS.get(s.lower(), 0.60) < 0.65
        ]
        if weak_sectors:
            drivers.append(f"limited data in {', '.join(weak_sectors)} sector(s)")
        else:
            drivers.append("moderate data coverage with some sector gaps")
    else:
        drivers.append("low data completeness — significant observation gaps")

    # Propagation clarity
    prop = _sn(propagation_score)
    if prop >= 0.80:
        drivers.append("high propagation certainty — clear causal chain")
    elif prop >= 0.50:
        drivers.append("moderate propagation clarity — some transmission uncertainty")
    else:
        drivers.append("low propagation clarity — causal pathways poorly defined")

    # Counterfactual stability
    if counterfactual_consistency == "CONSISTENT":
        drivers.append("counterfactual analysis internally consistent")
    elif counterfactual_consistency == "CORRECTED_COSTLY":
        drivers.append("counterfactual required correction — recommended path is costly")
    else:
        drivers.append("counterfactual inconsistency detected and auto-corrected")

    # Severity context
    if severity >= 0.80:
        drivers.append("extreme scenario severity increases model uncertainty")
    elif severity >= 0.60:
        drivers.append("elevated severity amplifies tail-risk assumptions")

    # Risk level context
    if risk_level in ("HIGH", "SEVERE"):
        drivers.append(f"{risk_level.lower()} systemic risk level compounds exposure estimates")

    # Guarantee minimum 2
    if len(drivers) < 2:
        drivers.append("baseline model assumptions applied")

    return {"drivers": drivers}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Decision Risk Envelope
# ═══════════════════════════════════════════════════════════════════════════════

def compute_risk_envelope(
    *,
    total_loss_usd: float = 0.0,
    actions: list[dict] | None = None,
    severity: float = 0.5,
    total_delay_hours: float = 24.0,
    risk_level: str = "MODERATE",
) -> dict:
    """Compute the decision risk envelope.

    Returns:
      {downside_if_wrong, reversibility, time_sensitivity}
    """
    loss = _sn(total_loss_usd)
    act_list = actions or []

    # Downside
    if loss >= config.TRUST_DOWNSIDE_HIGH_LOSS_USD or risk_level in ("HIGH", "SEVERE"):
        downside = "HIGH"
    elif loss >= config.TRUST_DOWNSIDE_MEDIUM_LOSS_USD:
        downside = "MEDIUM"
    else:
        downside = "LOW"

    # Reversibility: check actions for irreversible indicators
    low_rev_count = 0
    for a in act_list:
        if not isinstance(a, dict):
            continue
        rev = _ss(a.get("reversibility"), "MEDIUM").upper()
        if rev == "LOW":
            low_rev_count += 1
        # Also check keywords
        label = _ss(a.get("label") or a.get("action"), "").lower()
        if any(kw in label for kw in ("suspend", "terminate", "force majeure", "liquidat", "halt")):
            low_rev_count += 1

    if low_rev_count >= 2 or (low_rev_count >= 1 and severity >= 0.70):
        reversibility = "LOW"
    elif low_rev_count == 0 and severity < 0.50:
        reversibility = "HIGH"
    else:
        reversibility = "MEDIUM"

    # Time sensitivity: based on propagation delay and severity
    delay = _sn(total_delay_hours, 24.0)
    if delay <= config.TRUST_TIME_CRITICAL_HOURS or severity >= 0.85:
        time_sensitivity = "CRITICAL"
    elif delay <= 48.0 or severity >= 0.60:
        time_sensitivity = "MEDIUM"
    else:
        time_sensitivity = "LOW"

    return {
        "downside_if_wrong": downside,
        "reversibility": reversibility,
        "time_sensitivity": time_sensitivity,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Unified Trust Computation — orchestrates all 5 engines
# ═══════════════════════════════════════════════════════════════════════════════

def compute_decision_trust(
    *,
    actions: list[dict],
    scenario_id: str = "",
    severity: float = 0.5,
    total_loss_usd: float = 0.0,
    global_confidence: float = 0.85,
    propagation_score: float = 0.0,
    risk_level: str = "MODERATE",
    sectors_affected: list[str] | None = None,
    counterfactual_consistency: str = "CONSISTENT",
    transmission_total_delay: float = 24.0,
    action_pathways: dict | None = None,
) -> dict:
    """Orchestrate all 5 trust engines into a single trust payload.

    Returns:
      {
        action_confidence: [...],
        model_dependency: {...},
        validation: {...},
        confidence_breakdown: {...},
        risk_profile: {...},
      }
    """
    # 2. Model dependency first (needed by other engines)
    model_dep = compute_model_dependency(
        sectors_affected=sectors_affected,
        severity=severity,
        propagation_score=propagation_score,
        global_confidence=global_confidence,
    )

    # 1. Action-level confidence
    action_conf = compute_action_confidence(
        actions=actions,
        global_confidence=global_confidence,
        propagation_score=propagation_score,
        counterfactual_consistency=counterfactual_consistency,
        data_completeness=model_dep["data_completeness"],
        severity=severity,
    )

    # Merge classified actions from pathways for richer envelope computation
    all_actions_for_envelope = list(actions)
    if action_pathways and isinstance(action_pathways, dict):
        for key in ("immediate", "conditional", "strategic"):
            for a in (action_pathways.get(key) or []):
                if isinstance(a, dict):
                    all_actions_for_envelope.append(a)

    # 3. Validation
    imm_count = 0
    if action_pathways and isinstance(action_pathways, dict):
        imm_count = len(action_pathways.get("immediate") or [])

    validation = compute_validation(
        global_confidence=global_confidence,
        total_loss_usd=total_loss_usd,
        data_completeness=model_dep["data_completeness"],
        risk_level=risk_level,
        severity=severity,
        immediate_action_count=imm_count,
    )

    # 4. Confidence breakdown
    breakdown = build_confidence_breakdown(
        global_confidence=global_confidence,
        data_completeness=model_dep["data_completeness"],
        signal_reliability=model_dep["signal_reliability"],
        propagation_score=propagation_score,
        counterfactual_consistency=counterfactual_consistency,
        severity=severity,
        sectors_affected=sectors_affected,
        risk_level=risk_level,
    )

    # 5. Risk envelope
    risk_profile = compute_risk_envelope(
        total_loss_usd=total_loss_usd,
        actions=all_actions_for_envelope,
        severity=severity,
        total_delay_hours=transmission_total_delay,
        risk_level=risk_level,
    )

    return {
        "action_confidence": action_conf,
        "model_dependency": model_dep,
        "validation": validation,
        "confidence_breakdown": breakdown,
        "risk_profile": risk_profile,
    }
