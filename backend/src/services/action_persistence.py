"""
Impact Observatory | مرصد الأثر — Action Tracking Persistence

Layer: Services (L4) — PostgreSQL-backed persistence with Redis acceleration.

Architecture:
  PostgreSQL = source of truth
  Redis = cache + coordination (graceful degradation)
  In-memory = hot fallback if PG unavailable

Write path:  memory → PG (async) → Redis invalidate
Read path:   Redis cache → memory → PG query
List path:   Redis cached summary → PG query with tenant filter

This module replaces the pure in-memory action_tracking_store with
durable PostgreSQL persistence while maintaining identical function signatures
for backward compatibility with the API layer.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update as sa_update, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.action_tracking import (
    AuthorityRunRecord,
    TrackedActionRecord,
    ActionHistoryRecord,
)

logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Valid transitions (reused from in-memory store)
# ─────────────────────────────────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "PENDING":       {"ACKNOWLEDGED", "IN_PROGRESS", "BLOCKED"},
    "ACKNOWLEDGED":  {"IN_PROGRESS", "BLOCKED"},
    "IN_PROGRESS":   {"DONE", "BLOCKED"},
    "BLOCKED":       {"IN_PROGRESS", "PENDING"},
    "DONE":          set(),
}

_ALL_STATUSES = {"PENDING", "ACKNOWLEDGED", "IN_PROGRESS", "DONE", "BLOCKED"}


def is_valid_transition(current: str, target: str) -> bool:
    return target in _VALID_TRANSITIONS.get(current, set())


# ─────────────────────────────────────────────────────────────────────────────
# Authority Run Persistence
# ─────────────────────────────────────────────────────────────────────────────

async def persist_authority_run(
    session: AsyncSession,
    *,
    run_id: str,
    tenant_id: str,
    scenario_id: str,
    severity: float,
    horizon_hours: int,
    authority_result: dict,
) -> AuthorityRunRecord:
    """Persist a decision authority run to PostgreSQL."""
    da = authority_result.get("decision_authority", {})
    ed = da.get("executive_directive", {})
    pressure = da.get("decision_pressure_score", {})
    gov = da.get("governance", {})

    record = AuthorityRunRecord(
        run_id=run_id,
        tenant_id=tenant_id,
        scenario_id=scenario_id,
        severity=severity,
        horizon_hours=horizon_hours,
        decision=ed.get("internal_decision", "ESCALATE"),
        display_decision=ed.get("display_decision", ed.get("decision", "ESCALATE")),
        urgency=ed.get("urgency_level", "MODERATE"),
        pressure_score=pressure.get("score", 0),
        raw_payload_json=authority_result,
        summary_json={
            "headline_en": ed.get("headline_en", ""),
            "decision": ed.get("decision", ""),
            "urgency": ed.get("urgency_level", ""),
            "pressure": pressure.get("score", 0),
        },
        audit_id=gov.get("audit_id"),
        model_version=gov.get("model_version", "2.1.0"),
    )
    session.add(record)
    await session.flush()
    return record


async def get_authority_run(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
) -> dict | None:
    """Retrieve persisted authority run by run_id + tenant_id."""
    result = await session.execute(
        select(AuthorityRunRecord).where(
            AuthorityRunRecord.run_id == run_id,
            AuthorityRunRecord.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None
    return record.raw_payload_json


# ─────────────────────────────────────────────────────────────────────────────
# Action Seeding
# ─────────────────────────────────────────────────────────────────────────────

async def seed_actions_pg(
    session: AsyncSession,
    *,
    run_id: str,
    tenant_id: str,
    actions: list[dict],
) -> list[dict]:
    """Persist recommended actions to PostgreSQL.

    Creates TrackedActionRecord + initial ActionHistoryRecord per action.
    Returns the actions list with any PG-assigned defaults.
    """
    ts = _utcnow()

    for action in actions:
        action_id = action.get("action_id")
        if not action_id:
            continue

        record = TrackedActionRecord(
            action_id=action_id,
            run_id=run_id,
            tenant_id=tenant_id,
            entity_id=action.get("entity_id", action.get("sector", "unknown")),
            action=action.get("action", ""),
            action_ar=action.get("action_ar", ""),
            sector=action.get("sector", "cross-sector"),
            owner=action.get("owner", "Chief Risk Officer"),
            owner_id=action.get("owner_id"),
            priority=action.get("priority", 1),
            impact_usd=action.get("impact_usd", 0.0),
            impact_formatted=action.get("impact_formatted", "$0"),
            cost_usd=action.get("cost_usd", 0.0),
            cost_formatted=action.get("cost_formatted", "$0"),
            roi_multiple=action.get("roi_multiple", 0.0),
            feasibility=action.get("feasibility", 0.8),
            status="PENDING",
            owner_acknowledged=False,
            deadline_hours=action.get("deadline_hours", 24),
            execution_progress=0,
            notes_json=action.get("notes", []),
            created_at=ts,
            updated_at=ts,
        )
        session.add(record)

        # Initial history entry
        audit_hash = hashlib.sha256(f"{action_id}:CREATED:{ts.isoformat()}".encode()).hexdigest()[:12]
        history = ActionHistoryRecord(
            action_id=action_id,
            tenant_id=tenant_id,
            previous_status=None,
            new_status="PENDING",
            actor="system",
            notes="Action created by DecisionAuthorityEngine.",
            changes_json=["status: → PENDING"],
            audit_hash=audit_hash,
            timestamp=ts,
        )
        session.add(history)

    await session.flush()
    return actions


# ─────────────────────────────────────────────────────────────────────────────
# Action Reads
# ─────────────────────────────────────────────────────────────────────────────

async def get_action_pg(
    session: AsyncSession,
    action_id: str,
    tenant_id: str,
) -> dict | None:
    """Get a single action by ID, tenant-scoped."""
    result = await session.execute(
        select(TrackedActionRecord).where(
            TrackedActionRecord.action_id == action_id,
            TrackedActionRecord.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    return _action_to_dict(record) if record else None


async def list_actions_for_run_pg(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
) -> list[dict]:
    """List all actions for a run, tenant-scoped, ordered by priority."""
    result = await session.execute(
        select(TrackedActionRecord)
        .where(
            TrackedActionRecord.run_id == run_id,
            TrackedActionRecord.tenant_id == tenant_id,
        )
        .order_by(TrackedActionRecord.priority)
    )
    records = result.scalars().all()
    return [_action_to_dict(r) for r in records]


# ─────────────────────────────────────────────────────────────────────────────
# Action Updates
# ─────────────────────────────────────────────────────────────────────────────

async def update_action_pg(
    session: AsyncSession,
    action_id: str,
    tenant_id: str,
    *,
    status: str | None = None,
    execution_progress: int | None = None,
    owner_acknowledged: bool | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> dict | None:
    """Update an action's tracking state in PostgreSQL.

    Validates transitions, appends history, returns updated dict.
    """
    result = await session.execute(
        select(TrackedActionRecord).where(
            TrackedActionRecord.action_id == action_id,
            TrackedActionRecord.tenant_id == tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None

    ts = _utcnow()
    previous_status = record.status
    changes: list[str] = []

    # Status transition
    if status is not None:
        if status not in _ALL_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid: {sorted(_ALL_STATUSES)}")
        if not is_valid_transition(previous_status, status):
            valid = sorted(_VALID_TRANSITIONS.get(previous_status, set()))
            raise ValueError(
                f"Invalid transition {previous_status} → {status}. "
                f"Valid transitions from {previous_status}: {valid}"
            )
        record.status = status
        changes.append(f"status: {previous_status} → {status}")
        if status in ("ACKNOWLEDGED", "IN_PROGRESS", "DONE"):
            record.owner_acknowledged = True

    # Progress
    if execution_progress is not None:
        old_progress = record.execution_progress
        progress = max(0, min(100, execution_progress))
        record.execution_progress = progress
        changes.append(f"progress: {old_progress}% → {progress}%")
        if progress == 100 and record.status == "IN_PROGRESS":
            record.status = "DONE"
            changes.append("status: IN_PROGRESS → DONE (auto-complete)")

    # Acknowledgment
    if owner_acknowledged is not None:
        record.owner_acknowledged = owner_acknowledged
        changes.append(f"owner_acknowledged: {owner_acknowledged}")

    # Note
    if note:
        notes = record.notes_json or []
        notes.append({"timestamp": ts.isoformat(), "text": note})
        record.notes_json = notes
        changes.append("note added")

    record.updated_at = ts

    # Audit hash
    audit_payload = f"{action_id}:{record.status}:{ts.isoformat()}"
    update_hash = hashlib.sha256(audit_payload.encode()).hexdigest()[:12]
    record.last_update_hash = update_hash

    # History entry
    history = ActionHistoryRecord(
        action_id=action_id,
        tenant_id=tenant_id,
        previous_status=previous_status,
        new_status=record.status,
        actor=actor or "operator",
        notes=note or "; ".join(changes),
        changes_json=changes,
        audit_hash=update_hash,
        timestamp=ts,
    )
    session.add(history)
    await session.flush()

    return _action_to_dict(record)


# ─────────────────────────────────────────────────────────────────────────────
# Action History
# ─────────────────────────────────────────────────────────────────────────────

async def get_action_history_pg(
    session: AsyncSession,
    action_id: str,
    tenant_id: str,
) -> list[dict]:
    """Get full audit history for an action, tenant-scoped."""
    result = await session.execute(
        select(ActionHistoryRecord)
        .where(
            ActionHistoryRecord.action_id == action_id,
            ActionHistoryRecord.tenant_id == tenant_id,
        )
        .order_by(ActionHistoryRecord.timestamp)
    )
    records = result.scalars().all()
    return [_history_to_dict(r) for r in records]


# ─────────────────────────────────────────────────────────────────────────────
# Run Summary
# ─────────────────────────────────────────────────────────────────────────────

async def get_run_summary_pg(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
) -> dict:
    """Compute action tracking summary for a run."""
    actions = await list_actions_for_run_pg(session, run_id, tenant_id)
    if not actions:
        return {"run_id": run_id, "total": 0, "by_status": {}}

    by_status: dict[str, int] = {}
    total_progress = 0
    acknowledged_count = 0

    for a in actions:
        s = a.get("status", "PENDING")
        by_status[s] = by_status.get(s, 0) + 1
        total_progress += a.get("execution_progress", 0)
        if a.get("owner_acknowledged"):
            acknowledged_count += 1

    total = len(actions)
    return {
        "run_id": run_id,
        "total": total,
        "by_status": by_status,
        "overall_progress": round(total_progress / max(total, 1), 1),
        "acknowledged": acknowledged_count,
        "acknowledged_pct": round(acknowledged_count / max(total, 1) * 100, 1),
        "all_done": by_status.get("DONE", 0) == total,
        "any_blocked": by_status.get("BLOCKED", 0) > 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Serialization helpers
# ─────────────────────────────────────────────────────────────────────────────

def _action_to_dict(r: TrackedActionRecord) -> dict:
    """Convert ORM record to API-compatible dict."""
    return {
        "action_id": r.action_id,
        "run_id": r.run_id,
        "entity_id": r.entity_id,
        "action": r.action,
        "action_ar": r.action_ar or "",
        "sector": r.sector,
        "owner": r.owner,
        "owner_id": r.owner_id,
        "priority": r.priority,
        "impact_usd": r.impact_usd,
        "impact_formatted": r.impact_formatted,
        "cost_usd": r.cost_usd,
        "cost_formatted": r.cost_formatted,
        "roi_multiple": r.roi_multiple,
        "feasibility": r.feasibility,
        "status": r.status,
        "owner_acknowledged": r.owner_acknowledged,
        "deadline_hours": r.deadline_hours,
        "execution_progress": r.execution_progress,
        "notes": r.notes_json or [],
        "last_update_hash": r.last_update_hash,
        "created_at": r.created_at.isoformat() if r.created_at else "",
        "updated_at": r.updated_at.isoformat() if r.updated_at else "",
    }


def _history_to_dict(r: ActionHistoryRecord) -> dict:
    """Convert history ORM record to API-compatible dict."""
    return {
        "history_id": r.history_id,
        "action_id": r.action_id,
        "previous_status": r.previous_status,
        "new_status": r.new_status,
        "actor": r.actor,
        "notes": r.notes,
        "changes": r.changes_json or [],
        "audit_hash": r.audit_hash,
        "timestamp": r.timestamp.isoformat() if r.timestamp else "",
    }
