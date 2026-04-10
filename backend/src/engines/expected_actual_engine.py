"""
Expected vs Actual Engine — Phase 4 Engine 1

Compares what the system predicted (counterfactual recommended outcome)
against what actually happened (execution outcome from lifecycle).

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


def compute_expected_vs_actual(
    decision: dict,
    *,
    counterfactual: dict | None = None,
    lifecycle: dict | None = None,
    total_loss_usd: float = 0.0,
    severity: float = 0.5,
    scenario_id: str = "",
) -> dict:
    """Compare expected outcome against actual outcome for a single decision.

    Expected outcome = counterfactual recommended projected loss reduction
    Actual outcome = derived from lifecycle status + execution effectiveness

    Returns:
        {decision_id, expected_outcome, actual_outcome, delta, variance_ratio, scenario_id}
    """
    decision_id = _ss(
        decision.get("id") or decision.get("action_id") or decision.get("rank"),
        f"ea_{id(decision)}",
    )

    loss_avoided = _sn(decision.get("loss_avoided_usd"))
    cost = _sn(decision.get("cost_usd"))

    # ── Expected outcome ──
    # From counterfactual: the recommended path's projected loss reduction
    # minus the cost of the action = expected net benefit
    if counterfactual and isinstance(counterfactual, dict):
        delta_block = counterfactual.get("delta", {})
        cf_reduction = _sn(delta_block.get("loss_reduction_usd"))
        if cf_reduction > 0:
            # Proportion this decision's loss_avoided relative to total
            total_loss = _sn(total_loss_usd, 1.0)
            share = loss_avoided / total_loss if total_loss > 0 else 0.5
            expected_outcome = cf_reduction * min(share, 1.0)
        else:
            expected_outcome = loss_avoided - cost
    else:
        expected_outcome = loss_avoided - cost

    # Clamp: expected outcome should be positive (net benefit)
    expected_outcome = max(0.0, round(expected_outcome, 2))

    # ── Actual outcome ──
    # Derived from lifecycle status + execution effectiveness
    # Real systems would feed back actual loss data; here we derive from
    # lifecycle state and severity-based realization factors.
    lc_status = "ISSUED"
    if lifecycle and isinstance(lifecycle, dict):
        lc_status = _ss(lifecycle.get("status"), "ISSUED")

    # Realization factor: how much of expected value was actually captured
    if lc_status == "EXECUTED":
        # Executed: full realization with severity-based variance
        # Higher severity = more variance from expectation
        realization = 1.0 - (severity * 0.15)  # 85-100% realization
        actual_outcome = round(expected_outcome * realization, 2)
    elif lc_status == "APPROVED":
        # Approved but not yet executed: partial value (approval alone prevents some loss)
        realization = 0.60 - (severity * 0.10)
        actual_outcome = round(expected_outcome * max(0.3, realization), 2)
    elif lc_status == "COMPLETED":
        # Completed: exceeded expectations slightly (operational learning)
        realization = 1.05 + (0.10 * (1.0 - severity))
        actual_outcome = round(expected_outcome * realization, 2)
    else:
        # ISSUED only: minimal value (signal value only)
        realization = 0.15
        actual_outcome = round(expected_outcome * realization, 2)

    # ── Delta ──
    delta = round(actual_outcome - expected_outcome, 2)

    # ── Variance ratio ──
    if expected_outcome > 0:
        variance_ratio = round(abs(delta) / expected_outcome, 4)
    else:
        variance_ratio = 0.0

    return {
        "decision_id": decision_id,
        "expected_outcome": expected_outcome,
        "actual_outcome": actual_outcome,
        "delta": delta,
        "variance_ratio": variance_ratio,
        "scenario_id": scenario_id,
    }


def compute_all_expected_actual(
    actions: list[dict],
    *,
    counterfactual: dict | None = None,
    lifecycles: list[dict] | None = None,
    total_loss_usd: float = 0.0,
    severity: float = 0.5,
    scenario_id: str = "",
) -> list[dict]:
    """Compute expected vs actual for all actions."""
    lc_list = lifecycles or []
    results = []
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        lc = lc_list[i] if i < len(lc_list) else None
        ea = compute_expected_vs_actual(
            action,
            counterfactual=counterfactual,
            lifecycle=lc,
            total_loss_usd=total_loss_usd,
            severity=severity,
            scenario_id=scenario_id,
        )
        results.append(ea)
    return results
