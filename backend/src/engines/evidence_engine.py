"""
Phase 5 — Decision Evidence Pack Engine

Assembles a complete "defense file" for each decision by referencing
actual stored data from all prior pipeline stages. No recomputation.

Layer ownership: Evidence Layer (Stage 33)
Data flow: All prior stages → immutable evidence snapshot
"""
from __future__ import annotations

from datetime import datetime, timezone


def _safe_get(d: dict | None, key: str, default=None):
    """Safe dict get — handles None dicts."""
    if d is None:
        return default
    return d.get(key, default)


def _find_by_id(items: list[dict], key: str, value: str) -> dict | None:
    """Find first dict in list where dict[key] == value."""
    for item in items:
        if isinstance(item, dict) and item.get(key) == value:
            return item
    return None


def build_decision_evidence(
    decision: dict,
    *,
    transmission_chain: dict | None = None,
    counterfactual: dict | None = None,
    trust: dict | None = None,
    ownership: dict | None = None,
    workflow: dict | None = None,
    execution_trigger: dict | None = None,
    lifecycle: dict | None = None,
    expected_actual: dict | None = None,
    value_attribution: dict | None = None,
    effectiveness: dict | None = None,
    scenario_id: str = "",
    severity: float = 0.5,
    run_id: str = "",
) -> dict:
    """Build a complete evidence pack for a single decision.

    References actual stored data from all layers — no recomputation.
    Evidence is immutable once assembled.
    """
    decision_id = decision.get("id", decision.get("action_id", ""))

    return {
        "decision_id": decision_id,
        "run_id": run_id,
        "assembled_at": datetime.now(timezone.utc).isoformat(),

        # Layer 1: Signal snapshot
        "signal_snapshot": {
            "scenario_id": scenario_id,
            "severity": severity,
            "decision_label": decision.get("label", decision.get("action", decision.get("action_en", ""))),
            "sector": decision.get("sector", ""),
            "urgency": decision.get("urgency", 0),
            "loss_avoided_usd": decision.get("loss_avoided_usd", 0),
            "cost_usd": decision.get("cost_usd", 0),
        },

        # Layer 2: Transmission evidence
        "transmission_evidence": {
            "chain_length": _safe_get(transmission_chain, "chain_length", 0),
            "total_delay": _safe_get(transmission_chain, "total_delay", 0),
            "max_severity": _safe_get(transmission_chain, "max_severity", 0),
            "breakable_points_count": len(_safe_get(transmission_chain, "breakable_points", [])),
            "summary": _safe_get(transmission_chain, "summary", ""),
        },

        # Layer 3: Counterfactual basis
        "counterfactual_basis": {
            "baseline_loss": _safe_get(_safe_get(counterfactual, "baseline"), "projected_loss_usd", 0),
            "recommended_loss": _safe_get(_safe_get(counterfactual, "recommended"), "projected_loss_usd", 0),
            "loss_reduction_pct": _safe_get(_safe_get(counterfactual, "delta"), "loss_reduction_pct", 0),
            "consistency_flag": _safe_get(counterfactual, "consistency_flag", "UNKNOWN"),
            "confidence_score": _safe_get(counterfactual, "confidence_score", 0),
        },

        # Layer 4: Trust basis
        "trust_basis": {
            "confidence": _find_by_id(
                _safe_get(trust, "action_confidence", []),
                "action_id", decision_id,
            ) or {"confidence_score": 0, "confidence_label": "LOW"},
            "model_dependency": _safe_get(trust, "model_dependency", {}),
            "validation": _safe_get(trust, "validation", {}),
        },

        # Layer 5: Execution evidence
        "execution_evidence": {
            "ownership": ownership or {},
            "workflow": workflow or {},
            "execution_trigger": execution_trigger or {},
            "lifecycle": lifecycle or {},
        },

        # Layer 6: Outcome evidence
        "outcome_evidence": {
            "expected_actual": expected_actual or {},
            "value_attribution": value_attribution or {},
            "effectiveness": effectiveness or {},
        },

        # Completeness flags (for audit verification)
        "completeness": {
            "has_signal": True,
            "has_transmission": transmission_chain is not None,
            "has_counterfactual": counterfactual is not None,
            "has_trust": trust is not None,
            "has_execution": any([ownership, workflow, execution_trigger, lifecycle]),
            "has_outcome": any([expected_actual, value_attribution, effectiveness]),
            "complete": all([
                transmission_chain is not None,
                counterfactual is not None,
                trust is not None,
                ownership is not None or workflow is not None,
                expected_actual is not None,
            ]),
        },
    }


def build_all_evidence(
    actions: list[dict],
    *,
    transmission_chain: dict | None = None,
    counterfactual: dict | None = None,
    trust: dict | None = None,
    ownerships: list[dict] | None = None,
    workflows: list[dict] | None = None,
    execution_triggers: list[dict] | None = None,
    lifecycles: list[dict] | None = None,
    expected_actuals: list[dict] | None = None,
    value_attributions: list[dict] | None = None,
    effectiveness_results: list[dict] | None = None,
    scenario_id: str = "",
    severity: float = 0.5,
    run_id: str = "",
) -> list[dict]:
    """Build evidence packs for all decisions in the run."""
    results = []
    _ownerships = ownerships or []
    _workflows = workflows or []
    _triggers = execution_triggers or []
    _lifecycles = lifecycles or []
    _eas = expected_actuals or []
    _vas = value_attributions or []
    _effs = effectiveness_results or []

    for action in actions:
        did = action.get("id", action.get("action_id", ""))
        results.append(build_decision_evidence(
            action,
            transmission_chain=transmission_chain,
            counterfactual=counterfactual,
            trust=trust,
            ownership=_find_by_id(_ownerships, "decision_id", did),
            workflow=_find_by_id(_workflows, "decision_id", did),
            execution_trigger=_find_by_id(_triggers, "action_id", did),
            lifecycle=_find_by_id(_lifecycles, "decision_id", did),
            expected_actual=_find_by_id(_eas, "decision_id", did),
            value_attribution=_find_by_id(_vas, "decision_id", did),
            effectiveness=_find_by_id(_effs, "decision_id", did),
            scenario_id=scenario_id,
            severity=severity,
            run_id=run_id,
        ))

    return results
