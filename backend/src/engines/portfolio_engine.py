"""
Portfolio Value Aggregator — Phase 4 Engine 4

Aggregates value, effectiveness, and ROI across all decisions
in a scenario run for CFO-grade reporting.

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


def aggregate_portfolio(
    expected_actuals: list[dict],
    value_attributions: list[dict],
    effectiveness_results: list[dict],
) -> dict:
    """Aggregate portfolio-level metrics.

    Returns:
        {
            total_decisions, total_value_created, total_expected,
            total_actual, net_delta, success_rate, failure_count,
            success_count, neutral_count, avg_effectiveness_score,
            avg_attribution_confidence, best_decision_id, worst_decision_id,
            roi_ratio,
        }
    """
    total_decisions = len(expected_actuals)
    if total_decisions == 0:
        return {
            "total_decisions": 0,
            "total_value_created": 0.0,
            "total_expected": 0.0,
            "total_actual": 0.0,
            "net_delta": 0.0,
            "success_rate": 0.0,
            "failure_count": 0,
            "success_count": 0,
            "neutral_count": 0,
            "avg_effectiveness_score": 0.0,
            "avg_attribution_confidence": 0.0,
            "best_decision_id": None,
            "worst_decision_id": None,
            "roi_ratio": 0.0,
        }

    total_expected = sum(_sn(ea.get("expected_outcome")) for ea in expected_actuals)
    total_actual = sum(_sn(ea.get("actual_outcome")) for ea in expected_actuals)
    net_delta = round(total_actual - total_expected, 2)

    total_value_created = sum(
        _sn(va.get("value_created")) for va in value_attributions
    )

    # Classification counts
    success_count = 0
    failure_count = 0
    neutral_count = 0
    for eff in effectiveness_results:
        cls = eff.get("classification", "NEUTRAL")
        if cls == "SUCCESS":
            success_count += 1
        elif cls == "FAILURE":
            failure_count += 1
        else:
            neutral_count += 1

    success_rate = round(success_count / total_decisions, 4) if total_decisions > 0 else 0.0

    # Average scores
    scores = [_sn(eff.get("score")) for eff in effectiveness_results]
    avg_effectiveness_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    confs = [_sn(va.get("attribution_confidence")) for va in value_attributions]
    avg_attribution_confidence = round(sum(confs) / len(confs), 4) if confs else 0.0

    # Best / worst by value created
    best_decision_id = None
    worst_decision_id = None
    if value_attributions:
        sorted_va = sorted(value_attributions, key=lambda x: _sn(x.get("value_created")), reverse=True)
        best_decision_id = sorted_va[0].get("decision_id")
        worst_decision_id = sorted_va[-1].get("decision_id")

    # ROI ratio: total value created vs total expected investment
    roi_ratio = 0.0
    if total_expected > 0:
        roi_ratio = round(total_value_created / total_expected, 4)

    return {
        "total_decisions": total_decisions,
        "total_value_created": round(total_value_created, 2),
        "total_expected": round(total_expected, 2),
        "total_actual": round(total_actual, 2),
        "net_delta": net_delta,
        "success_rate": success_rate,
        "failure_count": failure_count,
        "success_count": success_count,
        "neutral_count": neutral_count,
        "avg_effectiveness_score": avg_effectiveness_score,
        "avg_attribution_confidence": avg_attribution_confidence,
        "best_decision_id": best_decision_id,
        "worst_decision_id": worst_decision_id,
        "roi_ratio": roi_ratio,
    }
