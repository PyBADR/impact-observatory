"""
Decision Workflow Engine — Phase 3 Engine 2

Converts decisions into real approval flows with escalation paths.
Uses trust data (confidence, risk profile) to determine approval requirements.

Pure function. Never throws. Returns safe defaults.
"""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════════════
# Escalation hierarchy
# ═══════════════════════════════════════════════════════════════════════════════

_ESCALATION_HIERARCHY: dict[str, list[str]] = {
    "CRO": ["CRO", "CEO", "Board"],
    "CFO": ["CFO", "CEO", "Board"],
    "COO": ["COO", "CRO", "CEO"],
    "TREASURY": ["TREASURY", "CFO", "CEO"],
    "RISK": ["RISK", "CRO", "CEO"],
    "REGULATOR": ["REGULATOR", "CRO", "Board"],
}

# Approval thresholds
_LOSS_APPROVAL_THRESHOLD_USD: float = 200_000_000
_CONFIDENCE_ESCALATION_FLOOR: float = 0.50
_CONFIDENCE_APPROVAL_FLOOR: float = 0.65


def _safe_num(v, fb: float = 0.0) -> float:
    if v is None:
        return fb
    try:
        n = float(v)
        return n if n == n and abs(n) != float("inf") else fb
    except (TypeError, ValueError):
        return fb


def _safe_str(v, fb: str = "") -> str:
    if v is None:
        return fb
    s = str(v).strip()
    return s if s else fb


def build_decision_workflow(
    decision: dict,
    *,
    ownership: dict | None = None,
    trust: dict | None = None,
    risk_level: str = "MODERATE",
    severity: float = 0.5,
) -> dict:
    """Build approval workflow for a single decision.

    Args:
        decision: The action/decision dict.
        ownership: DecisionOwnership from ownership_engine.
        trust: Full decision trust payload (Phase 2 output).
        risk_level: Scenario risk level.
        severity: Scenario severity.

    Returns:
        {decision_id, status, approval_required, approver_role, escalation_path}
    """
    decision_id = _safe_str(
        decision.get("id") or decision.get("action_id") or decision.get("rank"),
        f"wf_{id(decision)}",
    )

    owner_role = "CRO"
    if ownership:
        owner_role = _safe_str(ownership.get("owner_role"), "CRO")

    # Extract trust signals
    validation_required = False
    confidence_score = 0.85
    downside = "MEDIUM"
    time_sensitivity = "MEDIUM"

    if trust:
        validation = trust.get("validation", {})
        validation_required = bool(validation.get("required", False))

        risk_profile = trust.get("risk_profile", {})
        downside = _safe_str(risk_profile.get("downside_if_wrong"), "MEDIUM")
        time_sensitivity = _safe_str(risk_profile.get("time_sensitivity"), "MEDIUM")

        # Find action-specific confidence
        action_confs = trust.get("action_confidence", [])
        for ac in action_confs:
            if isinstance(ac, dict) and ac.get("action_id") == decision_id:
                confidence_score = _safe_num(ac.get("confidence_score"), 0.85)
                break

    # Decision: loss magnitude
    loss_avoided = _safe_num(decision.get("loss_avoided_usd"))
    cost = _safe_num(decision.get("cost_usd"))
    financial_magnitude = max(loss_avoided, cost)

    # ── Determine approval requirement ──
    approval_required = False
    approval_reasons = []

    # Rule 1: High/Severe risk level
    if risk_level in ("HIGH", "SEVERE"):
        approval_required = True
        approval_reasons.append(f"risk_level={risk_level}")

    # Rule 2: Validation engine says required
    if validation_required:
        approval_required = True
        approval_reasons.append("trust_validation_required")

    # Rule 3: High downside
    if downside == "HIGH":
        approval_required = True
        approval_reasons.append("high_downside_if_wrong")

    # Rule 4: Large financial magnitude
    if financial_magnitude >= _LOSS_APPROVAL_THRESHOLD_USD:
        approval_required = True
        approval_reasons.append(f"financial_magnitude=${financial_magnitude/1e6:.0f}M")

    # Rule 5: Regulatory scenarios
    if owner_role == "REGULATOR":
        approval_required = True
        approval_reasons.append("regulatory_ownership")

    # ── Determine escalation ──
    needs_escalation = False

    # Escalate if confidence below floor
    if confidence_score < _CONFIDENCE_ESCALATION_FLOOR:
        needs_escalation = True

    # Escalate if severity extreme
    if severity >= 0.85:
        needs_escalation = True

    # Escalate if both high downside and low confidence
    if downside == "HIGH" and confidence_score < _CONFIDENCE_APPROVAL_FLOOR:
        needs_escalation = True

    # ── Build escalation path ──
    base_path = _ESCALATION_HIERARCHY.get(owner_role, ["CRO", "CEO", "Board"])
    if needs_escalation:
        escalation_path = base_path  # full path
    elif approval_required:
        escalation_path = base_path[:2]  # first approver + one level up
    else:
        escalation_path = [base_path[0]]  # owner only

    # ── Determine status ──
    if needs_escalation:
        status = "ESCALATED"
    elif approval_required:
        status = "PENDING"
    else:
        # Auto-approve if time-critical + high confidence + low downside
        if (
            time_sensitivity == "CRITICAL"
            and confidence_score >= 0.75
            and downside != "HIGH"
        ):
            status = "APPROVED"
        else:
            status = "PENDING"

    return {
        "decision_id": decision_id,
        "status": status,
        "approval_required": approval_required,
        "approver_role": escalation_path[0] if escalation_path else owner_role,
        "escalation_path": escalation_path,
    }


def build_all_workflows(
    actions: list[dict],
    *,
    ownerships: list[dict] | None = None,
    trust: dict | None = None,
    risk_level: str = "MODERATE",
    severity: float = 0.5,
) -> list[dict]:
    """Build workflows for all actions."""
    own_list = ownerships or []
    results = []
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        own = own_list[i] if i < len(own_list) else None
        wf = build_decision_workflow(
            action,
            ownership=own,
            trust=trust,
            risk_level=risk_level,
            severity=severity,
        )
        results.append(wf)
    return results
