"""Service 12: audit_service — Audit Trail.

Records every run with full provenance: who, when, what inputs, what outputs.
Immutable append-only log.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-memory audit log (production: PostgreSQL audit table with RLS)
_audit_log: list[dict] = []


def record_run_start(
    run_id: str,
    template_id: str,
    severity: float,
    horizon_hours: int,
    user_id: str = "system",
) -> dict:
    """Record the start of a scenario run."""
    entry = {
        "event": "run_start",
        "run_id": run_id,
        "template_id": template_id,
        "severity": severity,
        "horizon_hours": horizon_hours,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _audit_log.append(entry)
    logger.info("AUDIT: run_start %s template=%s severity=%.2f", run_id, template_id, severity)
    return entry


def record_run_complete(
    run_id: str,
    total_loss_usd: float,
    critical_count: int,
    actions_count: int,
    duration_ms: float,
) -> dict:
    """Record run completion with summary metrics."""
    entry = {
        "event": "run_complete",
        "run_id": run_id,
        "total_loss_usd": total_loss_usd,
        "critical_count": critical_count,
        "actions_count": actions_count,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _audit_log.append(entry)
    logger.info("AUDIT: run_complete %s loss=$%.2fB criticals=%d", run_id, total_loss_usd / 1e9, critical_count)
    return entry


def record_decision_action(
    run_id: str,
    action_id: str,
    action: str,
    owner: str,
    priority: float,
) -> dict:
    """Record a decision action recommendation."""
    entry = {
        "event": "decision_action",
        "run_id": run_id,
        "action_id": action_id,
        "action": action,
        "owner": owner,
        "priority": priority,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _audit_log.append(entry)
    return entry


def get_audit_log(run_id: str | None = None, limit: int = 100) -> list[dict]:
    """Retrieve audit log entries, optionally filtered by run_id."""
    if run_id:
        entries = [e for e in _audit_log if e.get("run_id") == run_id]
    else:
        entries = list(_audit_log)
    return entries[-limit:]


def get_audit_stats() -> dict:
    """Get aggregate audit statistics."""
    total_runs = sum(1 for e in _audit_log if e["event"] == "run_start")
    completed = sum(1 for e in _audit_log if e["event"] == "run_complete")
    total_actions = sum(1 for e in _audit_log if e["event"] == "decision_action")
    return {
        "total_runs": total_runs,
        "completed_runs": completed,
        "total_actions_generated": total_actions,
        "log_entries": len(_audit_log),
    }
