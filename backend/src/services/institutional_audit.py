"""Institutional Audit Trail — SHA-256-hashed, append-only persistence.

Every decision chain output (trust verdicts, calibration results, override
decisions, explanations, status changes) is recorded as an immutable entry
with a SHA-256 payload hash for institutional defensibility.

Storage: in-memory (production: PostgreSQL audit table with RLS).
Contract: entries are never overwritten, only appended.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Append-only audit store ──────────────────────────────────────────────────
# Structure: {run_id: [AuditEntry, ...]}
_audit_store: dict[str, list[dict]] = {}


def _compute_hash(payload: dict) -> str:
    """Compute SHA-256 hash of a JSON-serializable payload."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def persist_audit_entry(
    run_id: str,
    source_stage: int,
    source_engine: str,
    event_type: str,
    payload: dict[str, Any],
    decision_id: str = "",
    actor: str = "system",
) -> dict:
    """Append an immutable audit entry with SHA-256 integrity hash.

    Args:
        run_id:        Pipeline run identifier.
        source_stage:  Pipeline stage number (70 or 80).
        source_engine: Engine name (e.g., "TrustOverrideEngine").
        event_type:    Event category (e.g., "OVERRIDE_VERDICT", "CALIBRATION_RESULT").
        payload:       Arbitrary dict to hash and store.
        decision_id:   Optional decision identifier.
        actor:         System or user who generated the entry.

    Returns:
        The stored audit entry dict (including entry_id and payload_hash).
    """
    entry = {
        "entry_id": f"audit_{uuid.uuid4().hex[:12]}",
        "run_id": run_id,
        "decision_id": decision_id,
        "timestamp": _now_iso(),
        "source_stage": source_stage,
        "source_engine": source_engine,
        "event_type": event_type,
        "actor": actor,
        "payload_hash": _compute_hash(payload),
        "payload": payload,
    }

    if run_id not in _audit_store:
        _audit_store[run_id] = []
    _audit_store[run_id].append(entry)

    logger.debug(
        "AUDIT_TRAIL: %s stage=%d engine=%s decision=%s hash=%s",
        event_type, source_stage, source_engine, decision_id, entry["payload_hash"][:16],
    )
    return entry


def persist_calibration_audit(run_id: str, calibration_dict: dict) -> list[dict]:
    """Persist all Stage 70 calibration results as audit entries.

    Creates one entry per engine output category:
    audit_results, ranked_decisions, authority_assignments,
    calibration_results, trust_results.
    """
    entries: list[dict] = []

    # Audit results
    for item in calibration_dict.get("audit_results", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=70,
            source_engine="AuditEngine", event_type="ACTION_AUDIT",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Ranked decisions
    for item in calibration_dict.get("ranked_decisions", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=70,
            source_engine="RankingEngine", event_type="RANKING_RESULT",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Authority assignments
    for item in calibration_dict.get("authority_assignments", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=70,
            source_engine="AuthorityEngine", event_type="AUTHORITY_ASSIGNMENT",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Calibration results
    for item in calibration_dict.get("calibration_results", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=70,
            source_engine="CalibrationEngine", event_type="CALIBRATION_RESULT",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Trust results
    for item in calibration_dict.get("trust_results", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=70,
            source_engine="TrustEngine", event_type="TRUST_SCORE",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    logger.info("AUDIT_TRAIL: persisted %d calibration entries for run %s", len(entries), run_id)
    return entries


def persist_trust_audit(run_id: str, trust_dict: dict) -> list[dict]:
    """Persist all Stage 80 trust layer results as audit entries.

    Creates entries for: scenario_validation, validation_results,
    authority_profiles, explanations, learning_updates, override_results.
    """
    entries: list[dict] = []

    # Scenario validation (single entry)
    sv = trust_dict.get("scenario_validation", {})
    if sv:
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=80,
            source_engine="ScenarioEnforcementEngine",
            event_type="SCENARIO_VALIDATION",
            payload=sv,
        ))

    # Validation results
    for item in trust_dict.get("validation_results", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=80,
            source_engine="ActionValidationEngine",
            event_type="ACTION_VALIDATION",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Authority profiles
    for item in trust_dict.get("authority_profiles", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=80,
            source_engine="AuthorityRealismEngine",
            event_type="AUTHORITY_PROFILE",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Explanations
    for item in trust_dict.get("explanations", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=80,
            source_engine="ExplainabilityEngine",
            event_type="DECISION_EXPLANATION",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Learning updates
    for item in trust_dict.get("learning_updates", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=80,
            source_engine="LearningClosureEngine",
            event_type="LEARNING_UPDATE",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    # Override results — the critical institutional verdicts
    for item in trust_dict.get("override_results", []):
        entries.append(persist_audit_entry(
            run_id=run_id, source_stage=80,
            source_engine="TrustOverrideEngine",
            event_type="OVERRIDE_VERDICT",
            payload=item, decision_id=item.get("decision_id", ""),
        ))

    logger.info("AUDIT_TRAIL: persisted %d trust entries for run %s", len(entries), run_id)
    return entries


def get_audit_trail(run_id: str) -> list[dict]:
    """Retrieve all audit entries for a run, in chronological order."""
    return list(_audit_store.get(run_id, []))


def get_audit_trail_for_decision(run_id: str, decision_id: str) -> list[dict]:
    """Retrieve audit entries for a specific decision within a run."""
    return [
        e for e in _audit_store.get(run_id, [])
        if e.get("decision_id") == decision_id
    ]


def get_audit_entry_count(run_id: str) -> int:
    """Count audit entries for a run."""
    return len(_audit_store.get(run_id, []))


def verify_audit_integrity(run_id: str) -> tuple[bool, list[str]]:
    """Verify SHA-256 integrity of all audit entries for a run.

    Returns:
        (all_valid, list_of_corrupted_entry_ids)
    """
    entries = _audit_store.get(run_id, [])
    corrupted: list[str] = []

    for entry in entries:
        payload = entry.get("payload", {})
        stored_hash = entry.get("payload_hash", "")
        computed_hash = _compute_hash(payload)
        if stored_hash != computed_hash:
            corrupted.append(entry.get("entry_id", "unknown"))

    return len(corrupted) == 0, corrupted


def get_all_run_ids_with_audit() -> list[str]:
    """Return all run IDs that have audit trail entries."""
    return list(_audit_store.keys())
