"""decision_operator_store — Hybrid in-memory + PostgreSQL persistence for operator decisions.

Write path: save to memory immediately, persist to DB async (fire-and-forget).
Read path: memory first, fall back to DB query.
List path: memory (filtered + sorted), DB fallback for production.

Mirrors run_store.py pattern exactly. No external dependencies beyond stdlib + sqlalchemy.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# In-process cache: decision_id → decision dict
_cache: dict[str, dict] = {}
# Process-level warmup flag: True once the first alist_* call has loaded from DB.
# Using a flag (not `if not _cache`) ensures warmup fires even if cache already has
# entries written in the same process before the first list request.
_warmed: bool = False


def _uid() -> str:
    return f"dec_{uuid.uuid4().hex[:12]}"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _classify_value(net: float) -> str:
    if net >= 1_000_000:
        return "HIGH_VALUE"
    if net > 0:
        return "POSITIVE_VALUE"
    if net == 0:
        return "NEUTRAL"
    if net >= -1_000_000:
        return "NEGATIVE_VALUE"
    return "LOSS_INDUCING"


# ── Write operations ─────────────────────────────────────────────────────────

def create(body: dict) -> dict:
    """Create an OperatorDecision and return its full dict.

    Auto-generates decision_id, timestamps, and sets initial status.
    Does NOT auto-create outcome/authority — those are separate store calls
    made by the route handler for explicit lineage control.
    """
    decision_id = _uid()
    now = _iso_now()

    dec = {
        "decision_id":      decision_id,
        "source_signal_id": body.get("source_signal_id"),
        "source_seed_id":   body.get("source_seed_id"),
        "source_run_id":    body.get("source_run_id"),
        "scenario_id":      body.get("scenario_id"),
        "decision_type":    body.get("decision_type", "APPROVE_ACTION"),
        "decision_status":  "CREATED",
        "decision_payload": body.get("decision_payload", {}),
        "rationale":        body.get("rationale"),
        "confidence_score": body.get("confidence_score"),
        "created_by":       body.get("created_by") or "system",
        "outcome_status":   "PENDING",
        "outcome_payload":  {},
        "outcome_id":       None,
        "created_at":       now,
        "updated_at":       now,
        "closed_at":        None,
        "schema_version":   "v1",
    }
    _cache[decision_id] = dec
    _fire_persist(decision_id, dec)
    return dec


def update(decision_id: str, updates: dict) -> dict | None:
    """Apply partial updates to a decision. Returns updated dict or None."""
    dec = _cache.get(decision_id)
    if dec is None:
        return None
    for k, v in updates.items():
        if k in dec and k != "decision_id":
            dec[k] = v
    dec["updated_at"] = _iso_now()
    _fire_persist(decision_id, dec)
    return dec


def execute(decision_id: str, executed_by: str | None = None, notes: str | None = None) -> dict | None:
    """Transition decision to EXECUTED status."""
    return update(decision_id, {
        "decision_status": "EXECUTED",
        "outcome_status":  "SUCCESS",
        "updated_at":      _iso_now(),
    })


def close(decision_id: str, outcome_status: str | None = None, closed_by: str | None = None) -> dict | None:
    """Transition decision to CLOSED status."""
    now = _iso_now()
    updates: dict[str, Any] = {
        "decision_status": "CLOSED",
        "closed_at":       now,
        "updated_at":      now,
    }
    if outcome_status:
        updates["outcome_status"] = outcome_status
    return update(decision_id, updates)


# ── Read operations ──────────────────────────────────────────────────────────

def get(decision_id: str) -> dict | None:
    """Get a single decision by ID. Memory first, DB fallback."""
    if decision_id in _cache:
        return _cache[decision_id]
    # DB fallback (sync)
    import asyncio
    try:
        result = asyncio.run(_load_from_db(decision_id))
        if result:
            _cache[decision_id] = result
        return result
    except Exception:
        return None


async def aget(decision_id: str) -> dict | None:
    """Async get. Memory first, DB fallback."""
    if decision_id in _cache:
        return _cache[decision_id]
    result = await _load_from_db(decision_id)
    if result:
        _cache[decision_id] = result
    return result


def list_decisions(
    *,
    status: str | None = None,
    decision_type: str | None = None,
    run_id: str | None = None,
    scenario_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List decisions from memory, filtered and sorted newest-first."""
    items = sorted(_cache.values(), key=lambda d: d.get("created_at", ""), reverse=True)
    if status:
        items = [d for d in items if d.get("decision_status") == status]
    if decision_type:
        items = [d for d in items if d.get("decision_type") == decision_type]
    if run_id:
        items = [d for d in items if d.get("source_run_id") == run_id]
    if scenario_id:
        items = [d for d in items if d.get("scenario_id") == scenario_id]
    return items[offset: offset + limit]


async def alist_decisions(
    *,
    status: str | None = None,
    decision_type: str | None = None,
    run_id: str | None = None,
    scenario_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Async list with DB cache warmup on first call after process start."""
    global _warmed
    if not _warmed:
        _warmed = True
        rows = await _load_all_from_db()
        for dec in rows:
            dec_id = dec.get("decision_id")
            if dec_id:
                _cache[dec_id] = dec
        if rows:
            logger.debug("Warmed decision cache from DB: %d records", len(rows))
    return list_decisions(
        status=status,
        decision_type=decision_type,
        run_id=run_id,
        scenario_id=scenario_id,
        limit=limit,
        offset=offset,
    )


def count() -> int:
    return len(_cache)


def clear() -> None:
    _cache.clear()


# ── DB persistence helpers ───────────────────────────────────────────────────

def _fire_persist(decision_id: str, dec: dict) -> None:
    """Persist to DB: async fire-and-forget when inside a running loop,
    synchronous asyncio.run() fallback when no loop is active."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_persist(decision_id, dec))
            return
    except RuntimeError:
        pass
    # No running loop — synchronous fallback so the write is not silently dropped.
    try:
        asyncio.run(_persist(decision_id, dec))
    except Exception as e:
        logger.warning("Sync DB persist fallback failed for decision %s: %s", decision_id, e)


async def _load_all_from_db() -> list[dict]:
    """Load recent decisions from DB to warm the in-memory cache."""
    try:
        from sqlalchemy import select, desc
        from src.core.config import settings
        from src.db.postgres import async_session_factory
        from src.models.orm import OperatorDecisionRecord

        async with async_session_factory() as session:
            result = await session.execute(
                select(OperatorDecisionRecord)
                .order_by(desc(OperatorDecisionRecord.created_at))
                .limit(settings.cache_warmup_limit)
            )
            records = result.scalars().all()
            return [r.result_json for r in records if r.result_json]
    except Exception as e:
        logger.debug("DB list warmup failed for decisions: %s", e)
        return []


async def _persist(decision_id: str, dec: dict) -> None:
    """Async write decision to PostgreSQL. Silently skips if DB unavailable."""
    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from src.db.postgres import async_session_factory
        from src.models.orm import OperatorDecisionRecord

        row = {
            "decision_id":      decision_id,
            "source_run_id":    dec.get("source_run_id"),
            "scenario_id":      dec.get("scenario_id"),
            "decision_type":    dec.get("decision_type"),
            "decision_status":  dec.get("decision_status"),
            "result_json":      dec,
            "created_at":       datetime.now(timezone.utc),
            "updated_at":       datetime.now(timezone.utc),
        }

        async with async_session_factory() as session:
            stmt = (
                pg_insert(OperatorDecisionRecord.__table__)
                .values(**row)
                .on_conflict_do_update(
                    index_elements=["decision_id"],
                    set_={
                        "decision_status": row["decision_status"],
                        "result_json":     row["result_json"],
                        "updated_at":      row["updated_at"],
                    },
                )
            )
            await session.execute(stmt)
            await session.commit()
        logger.debug("Persisted decision %s to DB", decision_id)
    except Exception as e:
        logger.debug("DB persist skipped for decision %s: %s", decision_id, e)


async def _load_from_db(decision_id: str) -> dict | None:
    """Load a single decision from DB."""
    try:
        from sqlalchemy import select
        from src.db.postgres import async_session_factory
        from src.models.orm import OperatorDecisionRecord

        async with async_session_factory() as session:
            row = await session.execute(
                select(OperatorDecisionRecord)
                .where(OperatorDecisionRecord.decision_id == decision_id)
            )
            record = row.scalar_one_or_none()
            if record and record.result_json:
                return record.result_json
    except Exception as e:
        logger.debug("DB load failed for decision %s: %s", decision_id, e)
    return None
