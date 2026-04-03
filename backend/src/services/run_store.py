"""run_store — Hybrid in-memory + PostgreSQL persistence for pipeline runs.

Write path: save to memory immediately, persist to DB async (fire-and-forget).
Read path: memory first, fall back to DB query.
List path: DB first (paginated), fall back to memory snapshot.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# In-process cache (survives restart only if DB is populated)
_cache: dict[str, dict] = {}

# ─── Org-scoped cache ────────────────────────────────────────────────────────
# Structure: {org_id: {run_id: result_dict}}
_org_cache: dict[str, dict[str, dict]] = {}
_DEFAULT_ORG = "default"


def put(run_id: str, result: dict) -> None:
    """Store run result in memory cache and async-persist to DB."""
    _cache[run_id] = result
    # Fire-and-forget DB write
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_persist(run_id, result))
    except RuntimeError:
        pass  # No event loop — skip DB write


def get(run_id: str) -> dict | None:
    """Retrieve from memory; fall back to DB synchronously if needed."""
    if run_id in _cache:
        return _cache[run_id]
    # Try DB (sync fallback via asyncio.run)
    import asyncio
    try:
        result = asyncio.run(_load_from_db(run_id))
        if result:
            _cache[run_id] = result
        return result
    except Exception:
        return None


async def aget(run_id: str) -> dict | None:
    """Async retrieve from memory; fall back to DB."""
    if run_id in _cache:
        return _cache[run_id]
    result = await _load_from_db(run_id)
    if result:
        _cache[run_id] = result
    return result


async def alist(limit: int = 20, offset: int = 0) -> list[dict]:
    """List runs, newest first. DB first, falls back to memory."""
    try:
        rows = await _list_from_db(limit=limit, offset=offset)
        if rows is not None:
            return rows
    except Exception as e:
        logger.debug("DB list failed, using memory: %s", e)

    # Memory fallback: return summaries sorted by run_id (no timestamp in memory)
    items = list(_cache.values())
    # Sort by run_id descending (run IDs contain UUID hex so approximate order)
    items.sort(key=lambda r: r.get("run_id", ""), reverse=True)
    return _summarize_many(items[offset: offset + limit])


def all_run_ids() -> list[str]:
    """Return all known run IDs from cache."""
    return list(_cache.keys())


# ─── Org-scoped operations ────────────────────────────────────────────────────

def put_for_org(run_id: str, result: dict, org: str = _DEFAULT_ORG) -> None:
    """Store run result scoped to an organization."""
    if org not in _org_cache:
        _org_cache[org] = {}
    _org_cache[org][run_id] = result
    # Also put in global cache for backward compat
    _cache[run_id] = result
    # Tag the result with org
    result["_org"] = org
    # Fire-and-forget DB write (org-scoped)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_persist(run_id, result))
    except RuntimeError:
        pass


async def aget_for_org(run_id: str, org: str = _DEFAULT_ORG) -> dict | None:
    """Get run, enforcing org scope."""
    # Check org cache first
    org_runs = _org_cache.get(org, {})
    if run_id in org_runs:
        return org_runs[run_id]
    # Check global cache — verify org matches
    if run_id in _cache:
        result = _cache[run_id]
        if result.get("_org", _DEFAULT_ORG) == org or org == "default":
            return result
        return None  # belongs to another org
    # Try DB
    result = await _load_from_db(run_id)
    if result:
        result_org = result.get("_org", _DEFAULT_ORG)
        if result_org != org and org != "default":
            return None  # org mismatch
        _cache[run_id] = result
        if org not in _org_cache:
            _org_cache[org] = {}
        _org_cache[org][run_id] = result
    return result


async def alist_for_org(org: str = _DEFAULT_ORG, limit: int = 20, offset: int = 0) -> list[dict]:
    """List runs for a specific organization, newest first."""
    try:
        rows = await _list_from_db_for_org(org=org, limit=limit, offset=offset)
        if rows is not None:
            return rows
    except Exception as e:
        logger.debug("DB org list failed: %s", e)

    # Memory fallback — filter by org
    org_runs = list(_org_cache.get(org, {}).values())
    if not org_runs and org != _DEFAULT_ORG:
        # Fall back to all runs for single-org setups
        org_runs = list(_cache.values())
    org_runs.sort(key=lambda r: r.get("run_id", ""), reverse=True)
    return _summarize_many(org_runs[offset: offset + limit])


async def _list_from_db_for_org(org: str, limit: int = 20, offset: int = 0) -> list[dict] | None:
    """List runs from DB filtered by org."""
    try:
        from sqlalchemy import select, desc
        from src.db.postgres import async_session_factory
        from src.models.orm import RunRecord

        async with async_session_factory() as session:
            # Filter by _org field in result_json, or no org field (legacy)
            query = (
                select(RunRecord)
                .order_by(desc(RunRecord.created_at))
                .offset(offset)
                .limit(limit)
            )
            # If not default org, filter by org in result_json
            if org != _DEFAULT_ORG:
                query = query.where(
                    RunRecord.result_json["_org"].astext == org
                )
            result = await session.execute(query)
            records = result.scalars().all()
            return [_summarize_record(r) for r in records]
    except Exception as e:
        logger.debug("DB org list failed: %s", e)
        return None


# ─── DB helpers ───────────────────────────────────────────────────────────────

async def _persist(run_id: str, result: dict) -> None:
    """Async write run to PostgreSQL. Silently skips if DB is unavailable."""
    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from src.db.postgres import async_session_factory
        from src.models.orm import RunRecord
        from datetime import timezone

        headline = result.get("headline", {})
        now = datetime.now(timezone.utc)

        row = {
            "run_id": run_id,
            "template_id": result.get("scenario_id", result.get("template_id", "unknown")),
            "severity": float(result.get("severity", 0.5)),
            "horizon_hours": int(result.get("horizon_hours", 336)),
            "status": "completed",
            "headline_loss_usd": float(headline.get("total_loss_usd", 0)),
            "peak_day": int(headline.get("peak_day", 0)),
            "severity_code": headline.get("severity_code"),
            "result_json": result,
            "created_at": now,
            "completed_at": now,
            "duration_ms": result.get("duration_ms"),
        }

        async with async_session_factory() as session:
            stmt = (
                pg_insert(RunRecord.__table__)
                .values(**row)
                .on_conflict_do_nothing(index_elements=["run_id"])
            )
            await session.execute(stmt)
            await session.commit()
        logger.debug("Persisted run %s to DB", run_id)
    except Exception as e:
        logger.debug("DB persist skipped for %s: %s", run_id, e)


async def _load_from_db(run_id: str) -> dict | None:
    """Load a single run result from DB."""
    try:
        from sqlalchemy import select
        from src.db.postgres import async_session_factory
        from src.models.orm import RunRecord

        async with async_session_factory() as session:
            row = await session.execute(
                select(RunRecord).where(RunRecord.run_id == run_id)
            )
            record = row.scalar_one_or_none()
            if record and record.result_json:
                return record.result_json
    except Exception as e:
        logger.debug("DB load failed for %s: %s", run_id, e)
    return None


async def _list_from_db(limit: int = 20, offset: int = 0) -> list[dict] | None:
    """List run summaries from DB, newest first."""
    try:
        from sqlalchemy import select, desc
        from src.db.postgres import async_session_factory
        from src.models.orm import RunRecord

        async with async_session_factory() as session:
            result = await session.execute(
                select(RunRecord)
                .order_by(desc(RunRecord.created_at))
                .offset(offset)
                .limit(limit)
            )
            records = result.scalars().all()
            return [_summarize_record(r) for r in records]
    except Exception as e:
        logger.debug("DB list failed: %s", e)
        return None


def _summarize_record(r: Any) -> dict:
    """Convert RunRecord ORM object to summary dict."""
    return {
        "run_id": r.run_id,
        "scenario_id": r.template_id,
        "template_id": r.template_id,
        "severity": r.severity,
        "status": r.status,
        "headline_loss_usd": r.headline_loss_usd,
        "peak_day": r.peak_day,
        "severity_code": r.severity_code,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "duration_ms": r.duration_ms,
    }


def _derive_severity_code(headline: dict) -> str:
    """Derive severity code from headline stress/loss metrics."""
    stress = headline.get("average_stress", 0)
    critical = headline.get("critical_count", 0)
    if stress >= 0.75 or critical >= 5:
        return "CRITICAL"
    if stress >= 0.55 or critical >= 3:
        return "SEVERE"
    if stress >= 0.35 or critical >= 1:
        return "HIGH"
    return "MODERATE"


def _summarize_many(results: list[dict]) -> list[dict]:
    """Create summary dicts from full result dicts (memory fallback)."""
    out = []
    for r in results:
        h = r.get("headline", {})
        severity_code = h.get("severity_code") or _derive_severity_code(h)
        scenario_id = r.get("scenario_id", r.get("template_id", "unknown"))
        out.append({
            "run_id": r.get("run_id"),
            "scenario_id": scenario_id,
            "template_id": scenario_id,
            "severity": r.get("severity", 0.5),
            "status": "completed",
            "headline_loss_usd": h.get("total_loss_usd", 0),
            "peak_day": h.get("peak_day", 0),
            "severity_code": severity_code,
            "created_at": None,
            "duration_ms": r.get("duration_ms"),
        })
    return out
