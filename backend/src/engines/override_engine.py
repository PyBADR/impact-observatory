"""
Phase 5 — Override & Exception System

Tracks human overrides and exceptions for every decision.
Overrides are immutable audit records — once logged, they cannot be modified.

Layer ownership: Governance Layer (Stage 36)
Data flow: Decision + Policy → Override Record
"""
from __future__ import annotations

from datetime import datetime, timezone


def track_override(
    decision: dict,
    *,
    policy: dict | None = None,
    workflow: dict | None = None,
) -> dict:
    """Create an override tracking record for a decision.

    In the deterministic pipeline, overrides are initialized based on:
    - Policy violations that were overridden by workflow approval
    - Escalated workflows that were resolved
    - Auto-approved decisions that bypassed policy

    Returns:
        {
            "decision_id": str,
            "overridden": bool,
            "overridden_by": str | None,
            "reason": str | None,
            "override_type": str,  # POLICY_OVERRIDE | ESCALATION_RESOLUTION | NONE
            "timestamp": str | None,
            "policy_violations_at_override": list[str],
        }
    """
    decision_id = decision.get("id", decision.get("action_id", ""))
    _policy = policy or {}
    _workflow = workflow or {}

    violations = _policy.get("violations", [])
    policy_allowed = _policy.get("allowed", True)
    workflow_status = _workflow.get("status", "PENDING")
    approver_role = _workflow.get("approver_role", "")

    # Determine if an override occurred
    overridden = False
    overridden_by: str | None = None
    reason: str | None = None
    override_type = "NONE"
    timestamp: str | None = None

    # Case 1: Policy blocked but workflow approved → policy override
    if not policy_allowed and workflow_status == "APPROVED":
        overridden = True
        overridden_by = approver_role or "APPROVER"
        reason = f"Policy violations overridden by {overridden_by} approval: {'; '.join(violations)}"
        override_type = "POLICY_OVERRIDE"
        timestamp = datetime.now(timezone.utc).isoformat()

    # Case 2: Escalated workflow that was resolved
    elif workflow_status == "ESCALATED":
        overridden = True
        escalation_path = _workflow.get("escalation_path", [])
        overridden_by = escalation_path[-1] if escalation_path else "ESCALATION_AUTHORITY"
        reason = f"Decision escalated through approval chain: {' → '.join(escalation_path)}"
        override_type = "ESCALATION_RESOLUTION"
        timestamp = datetime.now(timezone.utc).isoformat()

    # Case 3: No override — decision followed standard policy path
    # overridden remains False, all fields remain None

    return {
        "decision_id": decision_id,
        "overridden": overridden,
        "overridden_by": overridden_by,
        "reason": reason,
        "override_type": override_type,
        "timestamp": timestamp,
        "policy_violations_at_override": violations if overridden else [],
    }


def track_all_overrides(
    actions: list[dict],
    *,
    policies: list[dict] | None = None,
    workflows: list[dict] | None = None,
) -> list[dict]:
    """Track overrides for all decisions."""
    _policies = policies or []
    _workflows = workflows or []
    results = []

    for action in actions:
        did = action.get("id", action.get("action_id", ""))
        policy = None
        for p in _policies:
            if p.get("decision_id") == did:
                policy = p
                break

        workflow = None
        for w in _workflows:
            if w.get("decision_id") == did:
                workflow = w
                break

        results.append(track_override(
            action,
            policy=policy,
            workflow=workflow,
        ))

    return results
