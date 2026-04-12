"""
Enforcement Audit Integration
===============================

Convenience factories that write enforcement events into
the existing governance audit chain (GovernanceAuditEntry).

Pure functions — caller persists.
"""

from __future__ import annotations

from typing import Dict, Optional

from src.data_foundation.governance.governance_audit import create_audit_entry
from src.data_foundation.governance.schemas import (
    GovernanceAuditEntry,
    GovernanceEventType,
    GovernanceSubjectType,
)

from .schemas import (
    ApprovalRequest,
    EnforcementDecision,
    EnforcementPolicy,
    ExecutionGateResult,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Extend governance event/subject types for enforcement
# ═══════════════════════════════════════════════════════════════════════════════

# These are additive string constants — no changes to existing GovernanceEventType
ENFORCEMENT_EVENT_POLICY_CREATED = "ENFORCEMENT_POLICY_CREATED"
ENFORCEMENT_EVENT_EVALUATED = "ENFORCEMENT_EVALUATED"
ENFORCEMENT_EVENT_GATE_RESOLVED = "ENFORCEMENT_GATE_RESOLVED"
ENFORCEMENT_EVENT_APPROVAL_REQUESTED = "ENFORCEMENT_APPROVAL_REQUESTED"
ENFORCEMENT_EVENT_APPROVAL_RESOLVED = "ENFORCEMENT_APPROVAL_RESOLVED"

ENFORCEMENT_SUBJECT_POLICY = "ENFORCEMENT_POLICY"
ENFORCEMENT_SUBJECT_DECISION = "ENFORCEMENT_DECISION"
ENFORCEMENT_SUBJECT_GATE = "EXECUTION_GATE"
ENFORCEMENT_SUBJECT_APPROVAL = "APPROVAL_REQUEST"


# ═══════════════════════════════════════════════════════════════════════════════
# Audit factories
# ═══════════════════════════════════════════════════════════════════════════════


def audit_enforcement_policy_created(
    policy: EnforcementPolicy,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    """Audit entry for a new enforcement policy."""
    return create_audit_entry(
        event_type=ENFORCEMENT_EVENT_POLICY_CREATED,
        subject_type=ENFORCEMENT_SUBJECT_POLICY,
        subject_id=policy.policy_id,
        actor=actor,
        detail={
            "policy_name": policy.policy_name,
            "enforcement_action": policy.enforcement_action,
            "priority": policy.priority,
        },
        previous_audit_hash=previous_hash,
    )


def audit_enforcement_evaluated(
    decision: EnforcementDecision,
    actor: str = "system",
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    """Audit entry for an enforcement evaluation."""
    return create_audit_entry(
        event_type=ENFORCEMENT_EVENT_EVALUATED,
        subject_type=ENFORCEMENT_SUBJECT_DECISION,
        subject_id=decision.decision_id,
        actor=actor,
        detail={
            "decision_log_id": decision.decision_log_id,
            "rule_id": decision.rule_id,
            "enforcement_action": decision.enforcement_action,
            "is_executable": decision.is_executable,
            "triggered_policy_ids": decision.triggered_policy_ids,
            "trigger_reasons": decision.trigger_reasons,
            "original_confidence": decision.original_confidence,
            "effective_confidence": decision.effective_confidence,
        },
        previous_audit_hash=previous_hash,
    )


def audit_gate_resolved(
    gate: ExecutionGateResult,
    actor: str = "system",
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    """Audit entry for execution gate resolution."""
    return create_audit_entry(
        event_type=ENFORCEMENT_EVENT_GATE_RESOLVED,
        subject_type=ENFORCEMENT_SUBJECT_GATE,
        subject_id=gate.gate_id,
        actor=actor,
        detail={
            "decision_log_id": gate.decision_log_id,
            "gate_outcome": gate.gate_outcome,
            "may_execute": gate.may_execute,
            "is_shadow_mode": gate.is_shadow_mode,
            "applied_confidence": gate.applied_confidence,
            "applied_fallback_action": gate.applied_fallback_action,
        },
        previous_audit_hash=previous_hash,
    )


def audit_approval_requested(
    approval: ApprovalRequest,
    actor: str = "system",
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    """Audit entry for a new approval request."""
    return create_audit_entry(
        event_type=ENFORCEMENT_EVENT_APPROVAL_REQUESTED,
        subject_type=ENFORCEMENT_SUBJECT_APPROVAL,
        subject_id=approval.request_id,
        actor=actor,
        detail={
            "decision_log_id": approval.decision_log_id,
            "enforcement_decision_id": approval.enforcement_decision_id,
            "required_approver_role": approval.required_approver_role,
            "timeout_hours": approval.timeout_hours,
        },
        previous_audit_hash=previous_hash,
    )


def audit_approval_resolved(
    approval: ApprovalRequest,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    """Audit entry for approval resolution."""
    return create_audit_entry(
        event_type=ENFORCEMENT_EVENT_APPROVAL_RESOLVED,
        subject_type=ENFORCEMENT_SUBJECT_APPROVAL,
        subject_id=approval.request_id,
        actor=actor,
        detail={
            "decision_log_id": approval.decision_log_id,
            "status": approval.status,
            "approved_by": approval.approved_by,
            "approval_reason": approval.approval_reason,
        },
        previous_audit_hash=previous_hash,
    )
