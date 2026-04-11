"""Governance Audit Chain — SHA-256 hash-chained audit trail.

Every governance action (policy change, lifecycle transition, truth validation,
calibration event, override) is logged with a tamper-evident hash chain.

Seven convenience factories for common audit events.
Chain verification with tamper detection and integrity reporting.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.data_foundation.governance.schemas import GovernanceAuditEntry

__all__ = [
    "compute_hash",
    "create_audit_entry",
    "audit_policy_created",
    "audit_policy_updated",
    "audit_lifecycle_transition",
    "audit_truth_validation",
    "audit_calibration_triggered",
    "audit_calibration_resolved",
    "audit_override_applied",
    "verify_chain",
]


def _gen_id() -> str:
    return f"GAUD-{str(uuid4())[:12]}"


def compute_hash(entry: GovernanceAuditEntry) -> str:
    """Compute SHA-256 hash of an audit entry's canonical fields."""
    data = {
        "entry_id": entry.entry_id,
        "event_type": entry.event_type,
        "subject_type": entry.subject_type,
        "subject_id": entry.subject_id,
        "actor": entry.actor,
        "occurred_at": entry.occurred_at.isoformat(),
        "previous_audit_hash": entry.previous_audit_hash,
        "detail": entry.detail,
    }
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_audit_entry(
    event_type: str,
    subject_type: str,
    subject_id: str,
    actor: str,
    detail: Dict[str, Any] | None = None,
    *,
    actor_role: str | None = None,
    previous_audit_hash: str | None = None,
    occurred_at: datetime | None = None,
) -> GovernanceAuditEntry:
    """Create a new audit entry with computed hash."""
    now = occurred_at or datetime.now(timezone.utc)
    entry = GovernanceAuditEntry(
        entry_id=_gen_id(),
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor=actor,
        actor_role=actor_role,
        detail=detail or {},
        occurred_at=now,
        previous_audit_hash=previous_audit_hash,
    )
    # Compute and set the audit hash
    entry.audit_hash = compute_hash(entry)
    return entry


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience Factories
# ═══════════════════════════════════════════════════════════════════════════════

def audit_policy_created(
    policy_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "POLICY_CREATED", "GOVERNANCE_POLICY", policy_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_policy_updated(
    policy_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "POLICY_UPDATED", "GOVERNANCE_POLICY", policy_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_lifecycle_transition(
    spec_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "LIFECYCLE_TRANSITION", "RULE_SPEC", spec_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_truth_validation(
    policy_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "TRUTH_VALIDATION", "TRUTH_POLICY", policy_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_calibration_triggered(
    trigger_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "CALIBRATION_TRIGGERED", "CALIBRATION_TRIGGER", trigger_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_calibration_resolved(
    trigger_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "CALIBRATION_RESOLVED", "CALIBRATION_TRIGGER", trigger_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


def audit_override_applied(
    decision_log_id: str, actor: str, detail: Dict[str, Any] | None = None,
    *, previous_hash: str | None = None,
) -> GovernanceAuditEntry:
    return create_audit_entry(
        "OVERRIDE_APPLIED", "DECISION_LOG", decision_log_id,
        actor, detail, previous_audit_hash=previous_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Chain Verification
# ═══════════════════════════════════════════════════════════════════════════════

def verify_chain(entries: List[GovernanceAuditEntry]) -> Dict[str, Any]:
    """Verify integrity of an audit chain.

    Checks:
      1. Each entry's audit_hash matches recomputed hash
      2. Each entry's previous_audit_hash matches the prior entry's audit_hash
      3. First entry has no previous_audit_hash (or matches expected)

    Returns:
        {
            "valid": bool,
            "total_entries": int,
            "verified": int,
            "tampered": List[str],  # entry_ids with hash mismatches
            "chain_breaks": List[str],  # entry_ids with broken links
        }
    """
    tampered: List[str] = []
    chain_breaks: List[str] = []
    verified = 0

    for i, entry in enumerate(entries):
        # Check self-hash
        recomputed = compute_hash(entry)
        if entry.audit_hash and entry.audit_hash != recomputed:
            tampered.append(entry.entry_id)
        else:
            verified += 1

        # Check chain link (skip first entry)
        if i > 0:
            prev_entry = entries[i - 1]
            if entry.previous_audit_hash != prev_entry.audit_hash:
                chain_breaks.append(entry.entry_id)

    return {
        "valid": len(tampered) == 0 and len(chain_breaks) == 0,
        "total_entries": len(entries),
        "verified": verified,
        "tampered": tampered,
        "chain_breaks": chain_breaks,
    }
