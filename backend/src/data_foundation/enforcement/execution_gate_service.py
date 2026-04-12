"""
Execution Gate Service — Final Resolution
===========================================

Pure functions. No DB access.
Takes an EnforcementDecision and resolves it into a final
ExecutionGateResult and optional ApprovalRequest.

Gate resolution logic:
  ALLOW              → PROCEED (may_execute=True)
  DEGRADE_CONFIDENCE → PROCEED (may_execute=True, reduced confidence)
  BLOCK              → BLOCKED (may_execute=False)
  ESCALATE           → BLOCKED (may_execute=False)
  REQUIRE_APPROVAL   → AWAITING_APPROVAL (may_execute=False, creates ApprovalRequest)
  SHADOW_ONLY        → SHADOW_MODE (may_execute=False, is_shadow_mode=True)
  FALLBACK           → FALLBACK_APPLIED (may_execute=True, substituted action)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from .schemas import (
    ApprovalRequest,
    ApprovalStatus,
    EnforcementAction,
    EnforcementDecision,
    ExecutionGateResult,
    GateOutcome,
)


def resolve_gate(
    enforcement: EnforcementDecision,
    approval_timeout_hours: Optional[float] = None,
) -> Tuple[ExecutionGateResult, Optional[ApprovalRequest]]:
    """Resolve an enforcement decision into a final execution gate.

    Returns (gate_result, approval_request). approval_request is
    non-None only for REQUIRE_APPROVAL enforcement.
    """
    action = enforcement.enforcement_action
    approval_request: Optional[ApprovalRequest] = None

    if action == EnforcementAction.ALLOW:
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.PROCEED,
            may_execute=True,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    elif action == EnforcementAction.DEGRADE_CONFIDENCE:
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.PROCEED,
            may_execute=True,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    elif action == EnforcementAction.BLOCK:
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.BLOCKED,
            may_execute=False,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    elif action == EnforcementAction.ESCALATE:
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.BLOCKED,
            may_execute=False,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    elif action == EnforcementAction.REQUIRE_APPROVAL:
        # Create approval request
        now = datetime.now(timezone.utc)
        timeout = approval_timeout_hours or 24.0
        expires = now + timedelta(hours=timeout)

        approval_request = ApprovalRequest(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            required_approver_role=enforcement.required_approver or "chief_risk_officer",
            status=ApprovalStatus.PENDING,
            timeout_hours=timeout,
            expires_at=expires,
            requested_at=now,
        )
        approval_request.compute_hash()

        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.AWAITING_APPROVAL,
            may_execute=False,
            approval_request_id=approval_request.request_id,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    elif action == EnforcementAction.SHADOW_ONLY:
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.SHADOW_MODE,
            may_execute=False,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=True,
        )

    elif action == EnforcementAction.FALLBACK:
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.FALLBACK_APPLIED,
            may_execute=True,
            applied_fallback_action=enforcement.fallback_action,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    else:
        # Unknown action — block by default (defensive)
        gate = ExecutionGateResult(
            enforcement_decision_id=enforcement.decision_id,
            decision_log_id=enforcement.decision_log_id,
            gate_outcome=GateOutcome.BLOCKED,
            may_execute=False,
            applied_confidence=enforcement.effective_confidence,
            is_shadow_mode=False,
        )

    gate.compute_hash()
    return gate, approval_request


def resolve_approval(
    approval: ApprovalRequest,
    approved: bool,
    approver: str,
    reason: Optional[str] = None,
) -> ApprovalRequest:
    """Resolve a pending approval request.

    Returns a new ApprovalRequest with updated status.
    Pure function — caller persists.
    """
    now = datetime.now(timezone.utc)

    resolved = ApprovalRequest(
        request_id=approval.request_id,
        enforcement_decision_id=approval.enforcement_decision_id,
        decision_log_id=approval.decision_log_id,
        gate_id=approval.gate_id,
        required_approver_role=approval.required_approver_role,
        status=ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED,
        approved_by=approver,
        approval_reason=reason,
        timeout_hours=approval.timeout_hours,
        expires_at=approval.expires_at,
        requested_at=approval.requested_at,
        resolved_at=now,
    )
    resolved.compute_hash()
    return resolved
