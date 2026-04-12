"""
Unified Governance Audit Chain
================================

SHA-256 hash-chained audit trail for all governance events.

Every governance action — policy change, lifecycle transition,
truth validation, calibration event — is logged through this module.

The chain enforces append-only ordering: each entry carries the
hash of the previous entry. Verification walks the chain and
checks that each entry's previous_audit_hash matches the actual
hash of its predecessor.

All functions are pure. No DB access. No side effects.
The caller is responsible for persisting entries and reading
the previous hash from storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import (
    GovernanceAuditEntry,
    GovernanceEventType,
    GovernanceSubjectType,
    RuleLifecycleEvent,
    CalibrationEvent,
    TruthValidationResult,
    GovernancePolicy,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Core: create audit entry
# ═══════════════════════════════════════════════════════════════════════════════


def create_audit_entry(
    event_type: str,
    subject_type: str,
    subject_id: str,
    actor: str,
    detail: Optional[Dict[str, Any]] = None,
    actor_role: Optional[str] = None,
    previous_audit_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    """Create a new audit entry with SHA-256 chaining.

    Pure function. Returns the entry; caller persists it.
    """
    entry = GovernanceAuditEntry(
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor=actor,
        actor_role=actor_role,
        detail=detail or {},
        previous_audit_hash=previous_audit_hash,
    )
    entry.compute_hash()
    return entry


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience factories for specific governance events
# ═══════════════════════════════════════════════════════════════════════════════


def audit_policy_created(
    policy: GovernancePolicy,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.POLICY_CREATED,
        subject_type=GovernanceSubjectType.GOVERNANCE_POLICY,
        subject_id=policy.policy_id,
        actor=actor,
        detail={
            "policy_name": policy.policy_name,
            "policy_type": policy.policy_type,
            "is_active": policy.is_active,
        },
        previous_audit_hash=previous_hash,
    )


def audit_policy_updated(
    policy: GovernancePolicy,
    actor: str,
    changes: Dict[str, Any],
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.POLICY_UPDATED,
        subject_type=GovernanceSubjectType.GOVERNANCE_POLICY,
        subject_id=policy.policy_id,
        actor=actor,
        detail={"changes": changes},
        previous_audit_hash=previous_hash,
    )


def audit_policy_deactivated(
    policy: GovernancePolicy,
    actor: str,
    reason: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.POLICY_DEACTIVATED,
        subject_type=GovernanceSubjectType.GOVERNANCE_POLICY,
        subject_id=policy.policy_id,
        actor=actor,
        detail={"reason": reason},
        previous_audit_hash=previous_hash,
    )


def audit_lifecycle_transition(
    event: RuleLifecycleEvent,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.LIFECYCLE_TRANSITION,
        subject_type=GovernanceSubjectType.RULE_SPEC,
        subject_id=event.spec_id,
        actor=actor,
        detail={
            "event_id": event.event_id,
            "from_status": event.from_status,
            "to_status": event.to_status,
            "transition_type": event.transition_type,
            "reason": event.reason,
        },
        previous_audit_hash=previous_hash,
    )


def audit_truth_validation(
    result: TruthValidationResult,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.TRUTH_VALIDATION,
        subject_type=GovernanceSubjectType.TRUTH_POLICY,
        subject_id=result.policy_id,
        actor=actor,
        detail={
            "result_id": result.result_id,
            "record_id": result.record_id,
            "is_valid": result.is_valid,
            "failure_count": result.field_checks_failed,
        },
        previous_audit_hash=previous_hash,
    )


def audit_calibration_triggered(
    event: CalibrationEvent,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.CALIBRATION_TRIGGERED,
        subject_type=GovernanceSubjectType.CALIBRATION_TRIGGER,
        subject_id=event.trigger_id,
        actor=actor,
        detail={
            "event_id": event.event_id,
            "rule_id": event.rule_id,
            "metric_value": event.metric_value,
            "threshold_value": event.threshold_value,
            "sample_size": event.sample_size,
        },
        previous_audit_hash=previous_hash,
    )


def audit_calibration_resolved(
    event: CalibrationEvent,
    actor: str,
    previous_hash: Optional[str] = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        event_type=GovernanceEventType.CALIBRATION_RESOLVED,
        subject_type=GovernanceSubjectType.CALIBRATION_TRIGGER,
        subject_id=event.trigger_id,
        actor=actor,
        detail={
            "event_id": event.event_id,
            "rule_id": event.rule_id,
            "resolution_notes": event.resolution_notes,
            "resolved_by": event.resolved_by,
        },
        previous_audit_hash=previous_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Chain verification
# ═══════════════════════════════════════════════════════════════════════════════


def verify_chain(entries: List[GovernanceAuditEntry]) -> List[Dict[str, Any]]:
    """Verify the integrity of an audit chain.

    Entries must be in chronological order (oldest first).

    Returns a list of integrity violations. Empty list = chain is valid.
    Each violation is a dict with: entry_id, expected_hash, actual_hash, reason.
    """
    violations: List[Dict[str, Any]] = []

    for i, entry in enumerate(entries):
        # 1. Verify self-hash
        original_hash = entry.audit_hash
        entry.compute_hash()
        if entry.audit_hash != original_hash:
            violations.append({
                "entry_id": entry.entry_id,
                "index": i,
                "reason": "self_hash_mismatch",
                "expected_hash": entry.audit_hash,
                "actual_hash": original_hash,
            })
            # Restore for chain comparison
            entry.audit_hash = original_hash

        # 2. Verify chain link
        if i == 0:
            # First entry may or may not have a previous hash (start of chain)
            continue

        previous_entry = entries[i - 1]
        expected_previous = previous_entry.audit_hash
        actual_previous = entry.previous_audit_hash

        if actual_previous != expected_previous:
            violations.append({
                "entry_id": entry.entry_id,
                "index": i,
                "reason": "chain_link_broken",
                "expected_previous_hash": expected_previous,
                "actual_previous_hash": actual_previous,
            })

    return violations


def get_chain_summary(entries: List[GovernanceAuditEntry]) -> Dict[str, Any]:
    """Produce a summary of an audit chain for reporting."""
    if not entries:
        return {
            "total_entries": 0,
            "chain_valid": True,
            "violations": [],
        }

    violations = verify_chain(entries)
    event_type_counts: Dict[str, int] = {}
    actor_counts: Dict[str, int] = {}

    for entry in entries:
        event_type_counts[entry.event_type] = event_type_counts.get(entry.event_type, 0) + 1
        actor_counts[entry.actor] = actor_counts.get(entry.actor, 0) + 1

    return {
        "total_entries": len(entries),
        "chain_valid": len(violations) == 0,
        "violations": violations,
        "first_entry_at": entries[0].occurred_at.isoformat(),
        "last_entry_at": entries[-1].occurred_at.isoformat(),
        "event_type_counts": event_type_counts,
        "actor_counts": actor_counts,
    }
