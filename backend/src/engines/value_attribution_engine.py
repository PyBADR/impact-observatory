"""
Value Attribution Engine — Phase 4 Engine 2

Determines how much value each decision created and how confidently
that value can be attributed to the decision.

Pure function. Never throws. Returns safe defaults.
"""
from __future__ import annotations


def _sn(v, fb: float = 0.0) -> float:
    if v is None:
        return fb
    try:
        n = float(v)
        return n if n == n and abs(n) != float("inf") else fb
    except (TypeError, ValueError):
        return fb


def _ss(v, fb: str = "") -> str:
    if v is None:
        return fb
    s = str(v).strip()
    return s if s else fb


def compute_value_attribution(
    expected_actual: dict,
    *,
    action: dict | None = None,
    trust_confidence: float = 0.85,
    total_actions: int = 1,
    data_completeness: float = 0.70,
    scenario_id: str = "",
) -> dict:
    """Attribute value to a single decision.

    Args:
        expected_actual: Output from expected_actual_engine.
        action: Original action dict (for sector/urgency context).
        trust_confidence: Action-level confidence from Phase 2.
        total_actions: Total actions in the scenario (for overlap detection).
        data_completeness: Model dependency data completeness.

    Returns:
        {decision_id, value_created, attribution_confidence, attribution_type}
    """
    decision_id = _ss(expected_actual.get("decision_id"), "va_unknown")
    actual = _sn(expected_actual.get("actual_outcome"))
    expected = _sn(expected_actual.get("expected_outcome"))
    delta = _sn(expected_actual.get("delta"))

    # ── Value created ──
    # Positive actual_outcome = value captured
    value_created = round(actual, 2)

    # ── Attribution confidence ──
    # Blend of: trust confidence, data completeness, variance ratio
    variance_ratio = _sn(expected_actual.get("variance_ratio"))

    # Base confidence from trust system
    base_conf = _sn(trust_confidence, 0.70)

    # Penalize high variance (prediction was far off → less confident in attribution)
    variance_penalty = min(variance_ratio * 0.3, 0.30)

    # Penalize low data completeness
    data_penalty = max(0.0, (0.70 - _sn(data_completeness, 0.70)) * 0.5)

    attribution_confidence = max(0.10, min(1.0, round(
        base_conf - variance_penalty - data_penalty, 4
    )))

    # ── Attribution type ──
    if total_actions <= 1:
        # Single action → direct attribution
        attribution_type = "DIRECT"
    elif total_actions <= 3 and attribution_confidence >= 0.60:
        # Few actions with good confidence → still direct
        attribution_type = "DIRECT"
    elif attribution_confidence < 0.45 or _sn(data_completeness) < 0.50:
        # Weak data → low confidence attribution
        attribution_type = "LOW_CONFIDENCE"
    else:
        # Multiple overlapping actions → partial
        attribution_type = "PARTIAL"

    return {
        "decision_id": decision_id,
        "value_created": value_created,
        "attribution_confidence": attribution_confidence,
        "attribution_type": attribution_type,
        "scenario_id": scenario_id,
    }


def compute_all_attributions(
    expected_actuals: list[dict],
    *,
    actions: list[dict] | None = None,
    action_confidences: list[dict] | None = None,
    data_completeness: float = 0.70,
    scenario_id: str = "",
) -> list[dict]:
    """Compute value attribution for all decisions."""
    act_list = actions or []
    conf_list = action_confidences or []
    total_actions = len(expected_actuals)
    results = []

    for i, ea in enumerate(expected_actuals):
        action = act_list[i] if i < len(act_list) else None
        conf = 0.70
        if i < len(conf_list) and isinstance(conf_list[i], dict):
            conf = _sn(conf_list[i].get("confidence_score"), 0.70)

        va = compute_value_attribution(
            ea,
            action=action,
            trust_confidence=conf,
            total_actions=total_actions,
            data_completeness=data_completeness,
            scenario_id=scenario_id,
        )
        results.append(va)
    return results
