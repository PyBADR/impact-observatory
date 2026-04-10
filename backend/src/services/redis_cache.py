"""
Impact Observatory | مرصد الأثر — Redis Cache Service

Layer: Services (L4) — Redis-backed caching and coordination.

Redis is the acceleration layer, NOT source of truth. PostgreSQL owns state.

Responsibilities:
  - Short-lived cache of authority directive results
  - Action status cache for fast reads (invalidated on PATCH)
  - Run deduplication / locking to prevent parallel re-execution
  - Graceful degradation: all operations silently skip if Redis unavailable

Design Decision:
  All methods are async, all catch exceptions internally, all return
  fallback values on failure. No Redis failure should ever propagate
  to the API response or block the user.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default TTLs (seconds)
DIRECTIVE_TTL = 600       # 10 min for authority directive cache
ACTION_STATUS_TTL = 300   # 5 min for action status summaries
RUN_LOCK_TTL = 30         # 30 sec dedup lock for authority runs


def _redis_available() -> bool:
    """Check if Redis pool is initialized."""
    try:
        from src.db.redis import get_redis
        get_redis()
        return True
    except (RuntimeError, Exception):
        return False


def _get_pool():
    """Get Redis pool or None."""
    try:
        from src.db.redis import get_redis
        return get_redis()
    except (RuntimeError, Exception):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Directive Cache
# ─────────────────────────────────────────────────────────────────────────────

async def cache_directive(run_id: str, tenant_id: str, payload: dict, ttl: int = DIRECTIVE_TTL) -> bool:
    """Cache a decision authority directive result."""
    pool = _get_pool()
    if not pool:
        return False
    try:
        key = f"io:directive:{tenant_id}:{run_id}"
        await pool.setex(key, ttl, json.dumps(payload, default=str))
        return True
    except Exception as e:
        logger.debug("Redis cache_directive failed: %s", e)
        return False


async def get_cached_directive(run_id: str, tenant_id: str) -> dict | None:
    """Retrieve cached directive. Returns None on miss or failure."""
    pool = _get_pool()
    if not pool:
        return None
    try:
        key = f"io:directive:{tenant_id}:{run_id}"
        raw = await pool.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.debug("Redis get_cached_directive failed: %s", e)
        return None


async def invalidate_directive(run_id: str, tenant_id: str) -> bool:
    """Invalidate a cached directive (e.g. after action state change)."""
    pool = _get_pool()
    if not pool:
        return False
    try:
        key = f"io:directive:{tenant_id}:{run_id}"
        await pool.delete(key)
        return True
    except Exception as e:
        logger.debug("Redis invalidate_directive failed: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Action Status Cache
# ─────────────────────────────────────────────────────────────────────────────

async def cache_action_summary(run_id: str, tenant_id: str, summary: dict, ttl: int = ACTION_STATUS_TTL) -> bool:
    """Cache action tracking summary for a run."""
    pool = _get_pool()
    if not pool:
        return False
    try:
        key = f"io:actions_summary:{tenant_id}:{run_id}"
        await pool.setex(key, ttl, json.dumps(summary, default=str))
        return True
    except Exception as e:
        logger.debug("Redis cache_action_summary failed: %s", e)
        return False


async def get_cached_action_summary(run_id: str, tenant_id: str) -> dict | None:
    """Get cached action summary. Returns None on miss."""
    pool = _get_pool()
    if not pool:
        return None
    try:
        key = f"io:actions_summary:{tenant_id}:{run_id}"
        raw = await pool.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.debug("Redis get_cached_action_summary failed: %s", e)
        return None


async def invalidate_action_cache(run_id: str, tenant_id: str) -> bool:
    """Invalidate action summary cache after a status change."""
    pool = _get_pool()
    if not pool:
        return False
    try:
        key = f"io:actions_summary:{tenant_id}:{run_id}"
        await pool.delete(key)
        return True
    except Exception as e:
        logger.debug("Redis invalidate_action_cache failed: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Run Deduplication Lock
# ─────────────────────────────────────────────────────────────────────────────

async def acquire_run_lock(scenario_id: str, severity: float, tenant_id: str, ttl: int = RUN_LOCK_TTL) -> bool:
    """Acquire a dedup lock for a scenario run. Returns True if lock acquired."""
    pool = _get_pool()
    if not pool:
        return True  # No Redis = no dedup = always allow
    try:
        key = f"io:run_lock:{tenant_id}:{scenario_id}:{severity}"
        result = await pool.set(key, "1", ex=ttl, nx=True)
        return result is not None
    except Exception as e:
        logger.debug("Redis acquire_run_lock failed: %s", e)
        return True  # Fail open — allow the run


async def release_run_lock(scenario_id: str, severity: float, tenant_id: str) -> bool:
    """Release a run dedup lock."""
    pool = _get_pool()
    if not pool:
        return True
    try:
        key = f"io:run_lock:{tenant_id}:{scenario_id}:{severity}"
        await pool.delete(key)
        return True
    except Exception as e:
        logger.debug("Redis release_run_lock failed: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Pub/Sub Hooks (placeholder for real-time updates)
# ─────────────────────────────────────────────────────────────────────────────

async def publish_action_update(tenant_id: str, run_id: str, action_id: str, status: str) -> bool:
    """Publish action status change to a Redis channel.

    Future WebSocket subscribers can listen on this channel for live updates.
    """
    pool = _get_pool()
    if not pool:
        return False
    try:
        channel = f"io:action_updates:{tenant_id}"
        message = json.dumps({
            "run_id": run_id,
            "action_id": action_id,
            "status": status,
        })
        await pool.publish(channel, message)
        return True
    except Exception as e:
        logger.debug("Redis publish_action_update failed: %s", e)
        return False
