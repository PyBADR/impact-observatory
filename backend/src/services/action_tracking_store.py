"""action_tracking_store — In-memory persistence for decision authority action tracking.

State machine: PENDING → ACKNOWLEDGED → IN_PROGRESS → DONE | BLOCKED

Write path: save to memory immediately.
Read path: memory-only (no DB — actions are ephemeral per run lifecycle).
List path: memory, filtered by run_id.

Actions are seeded when DecisionAuthorityEngine.generate() creates recommended_actions.
Operators update status via PATCH /api/v1/decision/authority/actions/{action_id}.

Mirrors decision_operator_store.py pattern. Lightweight — no DB persistence needed
since actions regenerate on each simulation run.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# In-process caches
_action_cache: dict[str, dict] = {}           # action_id → action dict
_run_actions: dict[str, list[str]] = {}       # run_id → [action_id, ...]
_action_history: dict[str, list[dict]] = {}   # action_id → [history_entry, ...]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Valid transitions ───────────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "PENDING":       {"ACKNOWLEDGED", "IN_PROGRESS", "BLOCKED"},
    "ACKNOWLEDGED":  {"IN_PROGRESS", "BLOCKED"},
    "IN_PROGRESS":   {"DONE", "BLOCKED"},
    "BLOCKED":       {"IN_PROGRESS", "PENDING"},
    "DONE":          set(),  # terminal
}

_ALL_STATUSES = {"PENDING", "ACKNOWLEDGED", "IN_PROGRESS", "DONE", "BLOCKED"}


def is_valid_transition(current: str, target: str) -> bool:
    """Check if a status transition is valid."""
    return target in _VALID_TRANSITIONS.get(current, set())


# ── Seed operations (called by API after engine.generate()) ─────────────────

def seed_actions(run_id: str, actions: list[dict]) -> list[dict]:
    """Seed the action store with recommended actions from a directive.

    Called after DecisionAuthorityEngine.generate() produces actions.
    Stores each action keyed by action_id and indexes by run_id.
    Initializes audit history with a CREATED entry.

    Returns the actions (unchanged — already have tracking fields).
    """
    ts = _iso_now()
    action_ids = []
    for action in actions:
        action_id = action.get("action_id")
        if not action_id:
            continue

        # Ensure tracking metadata fields
        action["run_id"] = run_id
        action.setdefault("entity_id", action.get("sector", "unknown"))
        action.setdefault("owner_id", None)
        action.setdefault("history", [])

        # Initialize audit history
        history_entry = {
            "timestamp": ts,
            "previous_status": None,
            "new_status": "PENDING",
            "actor": "system",
            "notes": "Action created by DecisionAuthorityEngine.",
            "audit_hash": hashlib.sha256(
                f"{action_id}:CREATED:{ts}".encode()
            ).hexdigest()[:12],
        }
        action["history"].append(history_entry)
        _action_history[action_id] = [history_entry]

        _action_cache[action_id] = action
        action_ids.append(action_id)

    _run_actions[run_id] = action_ids
    logger.debug("Seeded %d actions for run %s", len(action_ids), run_id)
    return actions


# ── Read operations ─────────────────────────────────────────────────────────

def get_action(action_id: str) -> dict | None:
    """Get a single action by ID."""
    return _action_cache.get(action_id)


def list_actions_for_run(run_id: str) -> list[dict]:
    """List all actions for a given run, ordered by priority."""
    action_ids = _run_actions.get(run_id, [])
    actions = [_action_cache[aid] for aid in action_ids if aid in _action_cache]
    return sorted(actions, key=lambda a: a.get("priority", 999))


def list_all_actions(
    *,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List all tracked actions, optionally filtered by status."""
    items = sorted(
        _action_cache.values(),
        key=lambda a: a.get("created_at", ""),
        reverse=True,
    )
    if status:
        items = [a for a in items if a.get("status") == status]
    return items[offset: offset + limit]


# ── Write operations ────────────────────────────────────────────────────────

def update_action(
    action_id: str,
    *,
    status: str | None = None,
    execution_progress: int | None = None,
    owner_acknowledged: bool | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> dict | None:
    """Update an action's tracking state.

    Validates state transitions. Appends timestamped notes.
    Records full audit history entry for every mutation.
    Returns updated action dict or None if not found.
    """
    action = _action_cache.get(action_id)
    if action is None:
        return None

    ts = _iso_now()
    previous_status = action.get("status", "PENDING")
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
        action["status"] = status
        changes.append(f"status: {previous_status} → {status}")

        # Auto-acknowledge on any forward transition
        if status in ("ACKNOWLEDGED", "IN_PROGRESS", "DONE"):
            action["owner_acknowledged"] = True

    # Progress update
    if execution_progress is not None:
        old_progress = action.get("execution_progress", 0)
        progress = max(0, min(100, execution_progress))
        action["execution_progress"] = progress
        changes.append(f"progress: {old_progress}% → {progress}%")
        # Auto-complete if progress hits 100
        if progress == 100 and action.get("status") == "IN_PROGRESS":
            action["status"] = "DONE"
            changes.append(f"status: IN_PROGRESS → DONE (auto-complete)")

    # Owner acknowledgment
    if owner_acknowledged is not None:
        action["owner_acknowledged"] = owner_acknowledged
        changes.append(f"owner_acknowledged: {owner_acknowledged}")

    # Append note
    if note:
        notes = action.get("notes", [])
        notes.append({
            "timestamp": ts,
            "text": note,
        })
        action["notes"] = notes
        changes.append(f"note added")

    action["updated_at"] = ts

    # Generate audit hash for this update
    audit_payload = f"{action_id}:{action.get('status')}:{ts}"
    update_hash = hashlib.sha256(audit_payload.encode()).hexdigest()[:12]
    action["last_update_hash"] = update_hash

    # ── Audit history entry ─────────────────────────────────────────
    history_entry = {
        "timestamp": ts,
        "previous_status": previous_status,
        "new_status": action.get("status", previous_status),
        "actor": actor or "operator",
        "notes": note or "; ".join(changes),
        "changes": changes,
        "audit_hash": update_hash,
    }

    # Append to action's inline history
    if "history" not in action:
        action["history"] = []
    action["history"].append(history_entry)

    # Append to dedicated history index
    if action_id not in _action_history:
        _action_history[action_id] = []
    _action_history[action_id].append(history_entry)

    return action


def acknowledge_action(action_id: str, note: str | None = None, actor: str | None = None) -> dict | None:
    """Shorthand: move action to ACKNOWLEDGED and mark owner_acknowledged=True."""
    return update_action(
        action_id,
        status="ACKNOWLEDGED",
        owner_acknowledged=True,
        note=note or "Owner acknowledged action.",
        actor=actor or "owner",
    )


def get_action_history(action_id: str) -> list[dict]:
    """Return full audit history for an action, ordered chronologically."""
    return _action_history.get(action_id, [])


# ── Aggregate queries ───────────────────────────────────────────────────────

def get_run_summary(run_id: str) -> dict:
    """Return action tracking summary for a run."""
    actions = list_actions_for_run(run_id)
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


# ── Cleanup ─────────────────────────────────────────────────────────────────

def clear() -> None:
    """Clear all caches. Used in testing."""
    _action_cache.clear()
    _run_actions.clear()
    _action_history.clear()


def count() -> int:
    return len(_action_cache)
