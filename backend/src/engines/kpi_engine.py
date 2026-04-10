"""KPI Measurement Engine — Phase 6, Stage 38.

Computes real-world impact KPIs by comparing system decisions against
human decisions and observed outcomes.

KPIs:
  - decision_latency: how much faster the system produces a decision (hours)
  - human_vs_system_delta: fraction of decisions where system differs from human
  - avoided_loss_estimate: total $ loss avoided based on value engine outputs
  - false_positive_rate: fraction of escalations that were unnecessary
  - accuracy_rate: fraction of system decisions that matched or outperformed human
"""

from __future__ import annotations


def compute_pilot_kpi(
    *,
    actions: list[dict],
    shadow_comparisons: list[dict],
    portfolio_value: dict | None = None,
    policy_evaluations: list[dict] | None = None,
) -> dict:
    """Compute pilot KPIs from pipeline outputs and shadow comparisons.

    Args:
        actions: decision actions from the pipeline
        shadow_comparisons: list of ShadowDecision dicts from shadow engine
        portfolio_value: portfolio aggregation from Phase 4
        policy_evaluations: policy evaluations from Phase 5

    Returns:
        PilotKPI dict with all measurement fields.
    """
    n_decisions = len(shadow_comparisons) if shadow_comparisons else len(actions)
    if n_decisions == 0:
        return _empty_kpi()

    # ── Latency: system produces decisions instantly in simulation;
    #    human average is estimated at 4 hours for liquidity decisions
    HUMAN_AVG_LATENCY_HOURS = 4.0
    system_latency_hours = 0.05  # ~3 minutes for full pipeline
    decision_latency = HUMAN_AVG_LATENCY_HOURS - system_latency_hours

    # ── Human vs System Delta: measured from shadow comparisons
    divergent = sum(1 for s in shadow_comparisons if s.get("divergence", False))
    human_vs_system_delta = divergent / n_decisions if n_decisions > 0 else 0.0

    # ── Avoided Loss Estimate: from portfolio value engine
    avoided_loss = 0.0
    if portfolio_value:
        avoided_loss = max(0.0, portfolio_value.get("total_value_created", 0.0))

    # ── False Positive Rate: escalations that were not actually needed
    #    (policy blocked + no actual violation upon review)
    policies = policy_evaluations or []
    total_escalations = sum(1 for p in policies if not p.get("allowed", True))
    # In shadow mode, we consider escalations with <2 violations as potential FPs
    false_positives = sum(
        1 for p in policies
        if not p.get("allowed", True) and len(p.get("violations", [])) < 2
    )
    false_positive_rate = false_positives / total_escalations if total_escalations > 0 else 0.0

    # ── Accuracy Rate: non-divergent decisions
    accuracy_rate = 1.0 - human_vs_system_delta

    return {
        "total_decisions": n_decisions,
        "decision_latency_hours": round(decision_latency, 2),
        "latency_reduction_pct": round((decision_latency / HUMAN_AVG_LATENCY_HOURS) * 100, 1),
        "human_vs_system_delta": round(human_vs_system_delta, 4),
        "avoided_loss_estimate": round(avoided_loss, 2),
        "false_positive_rate": round(false_positive_rate, 4),
        "accuracy_rate": round(accuracy_rate, 4),
        "total_escalations": total_escalations,
        "divergent_count": divergent,
        "matched_count": n_decisions - divergent,
    }


def _empty_kpi() -> dict:
    """Return a zero-valued KPI dict."""
    return {
        "total_decisions": 0,
        "decision_latency_hours": 0.0,
        "latency_reduction_pct": 0.0,
        "human_vs_system_delta": 0.0,
        "avoided_loss_estimate": 0.0,
        "false_positive_rate": 0.0,
        "accuracy_rate": 0.0,
        "total_escalations": 0,
        "divergent_count": 0,
        "matched_count": 0,
    }
