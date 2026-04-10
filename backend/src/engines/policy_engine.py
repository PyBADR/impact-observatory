"""
Phase 5 — Policy Engine

Enforces governance rules before decision execution.
Evaluates each decision against configurable policy rules
and returns allow/block with violation explanations.

Layer ownership: Governance Layer (Stage 34)
Data flow: Decision + Trust + Ownership → Policy Evaluation
"""
from __future__ import annotations


# ── Policy Rules Configuration ────────────────────────────────────────
# Each rule is: (name, condition_fn, violation_message, required_approvals)
# condition_fn returns True if the rule is VIOLATED

def _is_regulatory_scenario(scenario_id: str) -> bool:
    """Scenarios that require regulator approval."""
    regulatory_ids = {
        "bahrain_sovereign_stress",
        "uae_banking_crisis",
        "regional_liquidity_stress_event",
        "financial_infrastructure_cyber_disruption",
    }
    return scenario_id in regulatory_ids


def _is_high_risk_low_confidence(trust: dict, risk_level: str) -> bool:
    """High risk combined with low model confidence."""
    risk_high = risk_level in ("HIGH", "SEVERE", "CRITICAL")
    model_dep = trust.get("model_dependency", {})
    confidence_low = model_dep.get("data_completeness", 1.0) < 0.50
    return risk_high and confidence_low


def _is_irreversible_action(action: dict) -> bool:
    """Action with LOW reversibility."""
    return action.get("reversibility", "MEDIUM") == "LOW"


def _is_auto_blocked(action: dict, trust: dict) -> bool:
    """Auto-execution blocked when confidence is too low or downside too high."""
    # Find action confidence
    action_id = action.get("id", action.get("action_id", ""))
    action_confs = trust.get("action_confidence", [])
    conf = 0.5
    for ac in action_confs:
        if ac.get("action_id") == action_id:
            conf = ac.get("confidence_score", 0.5)
            break

    risk_profile = trust.get("risk_profile", {})
    downside = risk_profile.get("downside_if_wrong", "MEDIUM")

    return conf < 0.60 and downside == "HIGH"


def _exceeds_cost_threshold(action: dict, threshold: float = 100_000_000) -> bool:
    """Action cost exceeds governance threshold requiring CFO approval."""
    return action.get("cost_usd", 0) > threshold


def evaluate_policy(
    decision: dict,
    *,
    trust: dict | None = None,
    ownership: dict | None = None,
    scenario_id: str = "",
    risk_level: str = "MODERATE",
    severity: float = 0.5,
) -> dict:
    """Evaluate governance policy for a single decision.

    Returns:
        {
            "decision_id": str,
            "allowed": bool,
            "violations": list[str],
            "required_approvals": list[str],
            "rules_evaluated": int,
            "rules_passed": int,
        }
    """
    decision_id = decision.get("id", decision.get("action_id", ""))
    _trust = trust or {}
    violations: list[str] = []
    required_approvals: set[str] = set()
    rules_evaluated = 0

    # Rule 1: Regulatory scenario requires regulator approval
    rules_evaluated += 1
    if _is_regulatory_scenario(scenario_id):
        violations.append("Regulatory scenario requires regulator approval before execution")
        required_approvals.add("REGULATOR")
        required_approvals.add("CRO")

    # Rule 2: High risk + low confidence blocks auto-execution
    rules_evaluated += 1
    if _is_high_risk_low_confidence(_trust, risk_level):
        violations.append("High risk with low model confidence — manual review required")
        required_approvals.add("CRO")

    # Rule 3: Irreversible actions need multi-level approval
    rules_evaluated += 1
    if _is_irreversible_action(decision):
        violations.append("Irreversible action requires multi-level approval")
        required_approvals.add("CRO")
        owner_role = (ownership or {}).get("owner_role", "")
        if owner_role and owner_role != "CRO":
            required_approvals.add(owner_role)

    # Rule 4: Auto-execution blocked when confidence too low
    rules_evaluated += 1
    if _is_auto_blocked(decision, _trust):
        violations.append("Auto-execution blocked — confidence below threshold with high downside")

    # Rule 5: High-cost actions require CFO approval
    rules_evaluated += 1
    if _exceeds_cost_threshold(decision):
        violations.append(f"Action cost exceeds governance threshold (>${100_000_000:,})")
        required_approvals.add("CFO")

    # Rule 6: SEVERE risk level requires board notification
    rules_evaluated += 1
    if risk_level in ("SEVERE", "CRITICAL"):
        violations.append("Severe risk level — board notification required")
        required_approvals.add("CEO")

    rules_passed = rules_evaluated - len(violations)
    allowed = len(violations) == 0

    return {
        "decision_id": decision_id,
        "allowed": allowed,
        "violations": violations,
        "required_approvals": sorted(required_approvals),
        "rules_evaluated": rules_evaluated,
        "rules_passed": rules_passed,
    }


def evaluate_all_policies(
    actions: list[dict],
    *,
    trust: dict | None = None,
    ownerships: list[dict] | None = None,
    scenario_id: str = "",
    risk_level: str = "MODERATE",
    severity: float = 0.5,
) -> list[dict]:
    """Evaluate governance policy for all decisions."""
    _ownerships = ownerships or []

    results = []
    for action in actions:
        did = action.get("id", action.get("action_id", ""))
        ownership = None
        for o in _ownerships:
            if o.get("decision_id") == did:
                ownership = o
                break

        results.append(evaluate_policy(
            action,
            trust=trust,
            ownership=ownership,
            scenario_id=scenario_id,
            risk_level=risk_level,
            severity=severity,
        ))

    return results
