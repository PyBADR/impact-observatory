"""
Decision Effectiveness Engine — Phase 4 Engine 3

Classifies each decision's performance as SUCCESS / NEUTRAL / FAILURE
based on expected vs actual and value attribution.

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


# Thresholds for classification
_SUCCESS_DELTA_RATIO: float = -0.10   # delta/expected < this → SUCCESS (beat expectations)
_FAILURE_DELTA_RATIO: float = -0.50   # delta/expected < this → FAILURE (far below)
_NEUTRAL_BAND: float = 0.15           # |variance_ratio| < this → NEUTRAL


def compute_effectiveness(
    expected_actual: dict,
    value_attribution: dict,
) -> dict:
    """Classify decision effectiveness.

    The score is a 0–1 measure of how well the decision performed:
      1.0 = exceeded expectations significantly
      0.5 = met expectations
      0.0 = total failure

    Returns:
        {decision_id, score, classification}
    """
    decision_id = _ss(expected_actual.get("decision_id"), "eff_unknown")
    expected = _sn(expected_actual.get("expected_outcome"))
    actual = _sn(expected_actual.get("actual_outcome"))
    delta = _sn(expected_actual.get("delta"))
    variance_ratio = _sn(expected_actual.get("variance_ratio"))
    value_created = _sn(value_attribution.get("value_created"))
    attr_conf = _sn(value_attribution.get("attribution_confidence"), 0.50)

    # ── Score computation ──
    # Based on how actual compares to expected
    if expected > 0:
        # Performance ratio: actual / expected
        # 1.0 = met expectations, >1.0 = exceeded, <1.0 = underperformed
        perf_ratio = actual / expected
    else:
        # No expected value → score based on whether any value was created
        perf_ratio = 1.0 if value_created > 0 else 0.5

    # Map performance ratio to 0–1 score
    # 0.0 → 0.0, 0.5 → 0.25, 1.0 → 0.50, 1.5 → 0.75, 2.0+ → 1.0
    raw_score = min(1.0, max(0.0, perf_ratio * 0.5))

    # Adjust for attribution confidence: low confidence dampens extreme scores
    # This prevents claiming SUCCESS when we're not sure the value is real
    if attr_conf < 0.50:
        raw_score = 0.5 + (raw_score - 0.5) * attr_conf

    score = round(raw_score, 4)

    # ── Classification ──
    if score >= 0.45 and value_created > 0:
        classification = "SUCCESS"
    elif score < 0.25 or (delta < 0 and variance_ratio > 0.40):
        classification = "FAILURE"
    else:
        classification = "NEUTRAL"

    return {
        "decision_id": decision_id,
        "score": score,
        "classification": classification,
    }


def compute_all_effectiveness(
    expected_actuals: list[dict],
    value_attributions: list[dict],
) -> list[dict]:
    """Classify effectiveness for all decisions."""
    results = []
    for i, ea in enumerate(expected_actuals):
        va = value_attributions[i] if i < len(value_attributions) else {}
        eff = compute_effectiveness(ea, va)
        results.append(eff)
    return results
