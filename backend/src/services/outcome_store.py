"""outcome_store — Hybrid in-memory + PostgreSQL persistence for outcomes.

Follows the run_store.py pattern: memory-first read, fire-and-forget DB write.
Outcomes track the real-world result of operator decisions through a full lifecycle:
  PENDING_OBSERVATION → OBSERVED → CONFIRMED → DISPUTED → CLOSED/FAILED
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# In-process cache: outcome_id → outcome dict
_cache: dict[str, dict] = {}
_warmed: bool = False


def _uid() -> str:
    return f"out_{uuid.uuid4().hex[:12]}"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Write operations ─────────────────────────────────────────────────────────

def create(body: dict) -> dict:
    """Create an Outcome and return its full dict."""
    outcome_id = _uid()
    now = _iso_now()

    out = {
        "outcome_id":                  outcome_id,
        "source_decision_id":          body.get("source_decision_id"),
        "source_run_id":               body.get("source_run_id"),
        "source_signal_id":            body.get("source_signal_id"),
        "source_seed_id":              body.get("source_seed_id"),
        "outcome_status":              "PENDING_OBSERVATION",
        "outcome_classification":      body.get("outcome_classification"),
        "observed_at":                 None,
        "recorded_at":                 now,
        "updated_at":                  now,
        "closed_at":                   None,
        "recorded_by":                 body.get("recorded_by") or "system",
        "expected_value":              body.get("expected_value"),
        "realized_value":              body.get("realized_value"),
        "error_flag":                  False,
        "time_to_resolution_seconds":  None,
        "evidence_payload":            body.get("evidence_payload", {}),
        "notes":                       body.get("notes"),
        "schema_version":              "v1",
    }
    _cache[outcome_id] = out
    _fire_persist(outcome_id, out)
    return out


def update(outcome_id: str, updates: dict) -> dict | None:
    """Apply partial updates to an outcome. Returns updated dict or None."""
    out = _cache.get(outcome_id)
    if out is None:
        return None
    for k, v in updates.items():
        if k in out and k != "outcome_id":
            out[k] = v
    out["updated_at"] = _iso_now()
    _fire_persist(outcome_id, out)
    return out


def observe(outcome_id: str, body: dict) -> dict | None:
    """Transition to OBSERVED status with evidence."""
    now = _iso_now()
    updates: dict[str, Any] = {
        "outcome_status": "OBSERVED",
        "observed_at":    now,
    }
    if "evidence_payload" in body:
        updates["evidence_payload"] = body["evidence_payload"]
    if "realized_value" in body:
        updates["realized_value"] = body["realized_value"]
    if "notes" in body:
        updates["notes"] = body["notes"]
    return update(outcome_id, updates)


def confirm(outcome_id: str, body: dict) -> dict | None:
    """Transition to CONFIRMED status with classification."""
    updates: dict[str, Any] = {
        "outcome_status":         "CONFIRMED",
        "outcome_classification": body.get("outcome_classification"),
    }
    if "realized_value" in body:
        updates["realized_value"] = body["realized_value"]
    if "notes" in body:
        updates["notes"] = body["notes"]
    return update(outcome_id, updates)


def dispute(outcome_id: str, body: dict) -> dict | None:
    """Transition to DISPUTED status."""
    updates: dict[str, Any] = {
        "outcome_status": "DISPUTED",
    }
    if "notes" in body:
        updates["notes"] = body["notes"]
    return update(outcome_id, updates)


def close(outcome_id: str, body: dict) -> dict | None:
    """Transition to CLOSED status."""
    now = _iso_now()
    updates: dict[str, Any] = {
        "outcome_status": "CLOSED",
        "closed_at":      now,
    }
    if "notes" in body:
        updates["notes"] = body["notes"]
    return update(outcome_id, updates)


# ── Read operations ──────────────────────────────────────────────────────────

def get(outcome_id: str) -> dict | None:
    """Get a single outcome by ID. Memory first, DB fallback."""
    if outcome_id in _cache:
        return _cache[outcome_id]
    import asyncio
    try:
        result = asyncio.run(_load_from_db(outcome_id))
        if result:
            _cache[outcome_id] = result
        return result
    except Exception:
        return None


async def aget(outcome_id: str) -> dict | None:
    """Async get. Memory first, DB fallback."""
    if outcome_id in _cache:
        return _cache[outcome_id]
    result = await _load_from_db(outcome_id)
    if result:
        _cache[outcome_id] = result
    return result


def list_outcomes(
    *,
    decision_id: str | None = None,
    run_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List outcomes from memory, filtered and sorted newest-first."""
    items = sorted(_cache.values(), key=lambda o: o.get("recorded_at", ""), reverse=True)
    if decision_id:
        items = [o for o in items if o.get("source_decision_id") == decision_id]
    if run_id:
        items = [o for o in items if o.get("source_run_id") == run_id]
    if status:
        items = [o for o in items if o.get("outcome_status") == status]
    return items[offset: offset + limit]


async def alist_outcomes(
    *,
    decision_id: str | None = None,
    run_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Async list with DB cache warmup on first call after process start."""
    global _warmed
    if not _warmed:
        _warmed = True
        rows = await _load_all_from_db()
        for out in rows:
            out_id = out.get("outcome_id")
            if out_id:
                _cache[out_id] = out
        if rows:
            logger.debug("Warmed outcome cache from DB: %d records", len(rows))
    return list_outcomes(
        decision_id=decision_id,
        run_id=run_id,
        status=status,
        limit=limit,
        offset=offset,
    )


def count() -> int:
    return len(_cache)


def clear() -> None:
    _cache.clear()


# ── DB persistence helpers ───────────────────────────────────────────────────

def _fire_persist(outcome_id: str, out: dict) -> None:
    """Persist to DB: async fire-and-forget when inside a running loop,
    synchronous asyncio.run() fallback when no loop is active."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_persist(outcome_id, out))
            return
    except RuntimeError:
        pass
    try:
        asyncio.run(_persist(outcome_id, out))
    except Exception as e:
        logger.warning("Sync DB persist fallback failed for outcome %s: %s", outcome_id, e)


async def _load_all_from_db() -> list[dict]:
    """Load recent outcomes from DB to warm the in-memory cache."""
    try:
        from sqlalchemy import select, desc
        from src.core.config import settings
        from src.db.postgres import async_session_factory
        from src.models.orm import OutcomeRecord

        async with async_session_factory() as session:
            result = await session.execute(
                select(OutcomeRecord)
                .order_by(desc(OutcomeRecord.created_at))
                .limit(settings.cache_warmup_limit)
            )
            records = result.scalars().all()
            return [r.result_json for r in records if r.result_json]
    except Exception as e:
        logger.debug("DB list warmup failed for outcomes: %s", e)
        return []


async def _persist(outcome_id: str, out: dict) -> None:
    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from src.db.postgres import async_session_factory
        from src.models.orm import OutcomeRecord

        row = {
            "outcome_id":          outcome_id,
            "source_decision_id":  out.get("source_decision_id"),
            "source_run_id":       out.get("source_run_id"),
            "outcome_status":      out.get("outcome_status"),
            "result_json":         out,
            "created_at":          datetime.now(timezone.utc),
            "updated_at":          datetime.now(timezone.utc),
        }

        async with async_session_factory() as session:
            stmt = (
                pg_insert(OutcomeRecord.__table__)
                .values(**row)
                .on_conflict_do_update(
                    index_elements=["outcome_id"],
                    set_={
                        "outcome_status": row["outcome_status"],
                        "result_json":    row["result_json"],
                        "updated_at":     row["updated_at"],
                    },
                )
            )
            await session.execute(stmt)
            await session.commit()
        logger.debug("Persisted outcome %s to DB", outcome_id)
    except Exception as e:
        logger.debug("DB persist skipped for outcome %s: %s", outcome_id, e)


async def _load_from_db(outcome_id: str) -> dict | None:
    try:
        from sqlalchemy import select
        from src.db.postgres import async_session_factory
        from src.models.orm import OutcomeRecord

        async with async_session_factory() as session:
            row = await session.execute(
                select(OutcomeRecord)
                .where(OutcomeRecord.outcome_id == outcome_id)
            )
            record = row.scalar_one_or_none()
            if record and record.result_json:
                return record.result_json
    except Exception as e:
        logger.debug("DB load failed for outcome %s: %s", outcome_id, e)
    return None
