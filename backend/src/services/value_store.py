"""value_store — Hybrid in-memory + PostgreSQL persistence for decision values.

Follows the run_store.py pattern: memory-first read, fire-and-forget DB write.
DecisionValues are computed ROI entities derived from confirmed Outcomes.
  net_value = avoided_loss - (operational_cost + decision_cost + latency_cost)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-process cache: value_id → value dict
_cache: dict[str, dict] = {}
_warmed: bool = False


def _uid() -> str:
    return f"val_{uuid.uuid4().hex[:12]}"


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

def compute(body: dict, outcome: dict | None = None) -> dict:
    """Compute a DecisionValue from an outcome and cost breakdown.

    If `outcome` is provided, derives source_decision_id, source_run_id,
    and expected_value from it. Body overrides take precedence.
    """
    value_id = _uid()
    now = _iso_now()

    avoided_loss     = body.get("avoided_loss") or (outcome.get("expected_value") if outcome else None) or 0.0
    operational_cost = body.get("operational_cost", 0.0)
    decision_cost    = body.get("decision_cost", 0.0)
    latency_cost     = body.get("latency_cost", 0.0)
    total_cost       = operational_cost + decision_cost + latency_cost
    net_value        = avoided_loss - total_cost

    val = {
        "value_id":               value_id,
        "source_outcome_id":      body.get("source_outcome_id", ""),
        "source_decision_id":     outcome.get("source_decision_id") if outcome else None,
        "source_run_id":          outcome.get("source_run_id") if outcome else None,
        "computed_at":            now,
        "computed_by":            body.get("computed_by") or "system",
        "expected_value":         avoided_loss if avoided_loss > 0 else None,
        "realized_value":         None,
        "avoided_loss":           avoided_loss,
        "operational_cost":       operational_cost,
        "decision_cost":          decision_cost,
        "latency_cost":           latency_cost,
        "total_cost":             total_cost,
        "net_value":              net_value,
        "value_confidence_score": 0.75,
        "value_classification":   _classify_value(net_value),
        "calculation_trace": {
            "avoided_loss":      avoided_loss,
            "operational_cost":  operational_cost,
            "decision_cost":     decision_cost,
            "latency_cost":      latency_cost,
            "total_cost":        total_cost,
        },
        "notes":                  body.get("notes"),
        "schema_version":         "v1",
    }
    _cache[value_id] = val
    _fire_persist(value_id, val)
    return val


def recompute(value_id: str, body: dict) -> dict | None:
    """Recompute a value with updated cost inputs. Returns updated dict or None."""
    existing = _cache.get(value_id)
    if existing is None:
        return None

    avoided_loss     = body.get("avoided_loss", existing["avoided_loss"])
    operational_cost = body.get("operational_cost", existing["operational_cost"])
    decision_cost    = body.get("decision_cost", existing["decision_cost"])
    latency_cost     = body.get("latency_cost", existing["latency_cost"])
    total_cost       = operational_cost + decision_cost + latency_cost
    net_value        = avoided_loss - total_cost

    existing.update({
        "avoided_loss":           avoided_loss,
        "operational_cost":       operational_cost,
        "decision_cost":          decision_cost,
        "latency_cost":           latency_cost,
        "total_cost":             total_cost,
        "net_value":              net_value,
        "value_classification":   _classify_value(net_value),
        "expected_value":         avoided_loss if avoided_loss > 0 else None,
        "computed_at":            _iso_now(),
        "computed_by":            body.get("computed_by") or existing["computed_by"],
        "notes":                  body.get("notes") or existing.get("notes"),
        "calculation_trace": {
            "avoided_loss":      avoided_loss,
            "operational_cost":  operational_cost,
            "decision_cost":     decision_cost,
            "latency_cost":      latency_cost,
            "total_cost":        total_cost,
        },
    })
    _fire_persist(value_id, existing)
    return existing


# ── Read operations ──────────────────────────────────────────────────────────

def get(value_id: str) -> dict | None:
    if value_id in _cache:
        return _cache[value_id]
    import asyncio
    try:
        result = asyncio.run(_load_from_db(value_id))
        if result:
            _cache[value_id] = result
        return result
    except Exception:
        return None


async def aget(value_id: str) -> dict | None:
    if value_id in _cache:
        return _cache[value_id]
    result = await _load_from_db(value_id)
    if result:
        _cache[value_id] = result
    return result


def list_values(
    *,
    outcome_id: str | None = None,
    decision_id: str | None = None,
    run_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    items = sorted(_cache.values(), key=lambda v: v.get("computed_at", ""), reverse=True)
    if outcome_id:
        items = [v for v in items if v.get("source_outcome_id") == outcome_id]
    if decision_id:
        items = [v for v in items if v.get("source_decision_id") == decision_id]
    if run_id:
        items = [v for v in items if v.get("source_run_id") == run_id]
    return items[offset: offset + limit]


async def alist_values(
    *,
    outcome_id: str | None = None,
    decision_id: str | None = None,
    run_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Async list with DB cache warmup on first call after process start."""
    global _warmed
    if not _warmed:
        _warmed = True
        rows = await _load_all_from_db()
        for val in rows:
            val_id = val.get("value_id")
            if val_id:
                _cache[val_id] = val
        if rows:
            logger.debug("Warmed value cache from DB: %d records", len(rows))
    return list_values(
        outcome_id=outcome_id,
        decision_id=decision_id,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )


def count() -> int:
    return len(_cache)


def clear() -> None:
    _cache.clear()


# ── DB persistence helpers ───────────────────────────────────────────────────

def _fire_persist(value_id: str, val: dict) -> None:
    """Persist to DB: async fire-and-forget when inside a running loop,
    synchronous asyncio.run() fallback when no loop is active."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_persist(value_id, val))
            return
    except RuntimeError:
        pass
    try:
        asyncio.run(_persist(value_id, val))
    except Exception as e:
        logger.warning("Sync DB persist fallback failed for value %s: %s", value_id, e)


async def _load_all_from_db() -> list[dict]:
    """Load recent values from DB to warm the in-memory cache."""
    try:
        from sqlalchemy import select, desc
        from src.core.config import settings
        from src.db.postgres import async_session_factory
        from src.models.orm import DecisionValueRecord

        async with async_session_factory() as session:
            result = await session.execute(
                select(DecisionValueRecord)
                .order_by(desc(DecisionValueRecord.created_at))
                .limit(settings.cache_warmup_limit)
            )
            records = result.scalars().all()
            return [r.result_json for r in records if r.result_json]
    except Exception as e:
        logger.debug("DB list warmup failed for values: %s", e)
        return []


async def _persist(value_id: str, val: dict) -> None:
    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from src.db.postgres import async_session_factory
        from src.models.orm import DecisionValueRecord

        row = {
            "value_id":            value_id,
            "source_outcome_id":   val.get("source_outcome_id"),
            "source_decision_id":  val.get("source_decision_id"),
            "source_run_id":       val.get("source_run_id"),
            "net_value":           val.get("net_value", 0.0),
            "value_classification": val.get("value_classification", "NEUTRAL"),
            "result_json":         val,
            "created_at":          datetime.now(timezone.utc),
        }

        async with async_session_factory() as session:
            stmt = (
                pg_insert(DecisionValueRecord.__table__)
                .values(**row)
                .on_conflict_do_update(
                    index_elements=["value_id"],
                    set_={
                        "net_value":            row["net_value"],
                        "value_classification": row["value_classification"],
                        "result_json":          row["result_json"],
                    },
                )
            )
            await session.execute(stmt)
            await session.commit()
        logger.debug("Persisted value %s to DB", value_id)
    except Exception as e:
        logger.debug("DB persist skipped for value %s: %s", value_id, e)


async def _load_from_db(value_id: str) -> dict | None:
    try:
        from sqlalchemy import select
        from src.db.postgres import async_session_factory
        from src.models.orm import DecisionValueRecord

        async with async_session_factory() as session:
            row = await session.execute(
                select(DecisionValueRecord)
                .where(DecisionValueRecord.value_id == value_id)
            )
            record = row.scalar_one_or_none()
            if record and record.result_json:
                return record.result_json
    except Exception as e:
        logger.debug("DB load failed for value %s: %s", value_id, e)
    return None
