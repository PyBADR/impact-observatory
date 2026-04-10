"""Signal Intelligence Layer — API Routes (v1).

Endpoints:
  POST   /api/v1/feeds                   — register a new feed
  GET    /api/v1/feeds                   — list all feeds with status
  GET    /api/v1/feeds/{feed_id}         — get feed status
  POST   /api/v1/feeds/{feed_id}/poll    — trigger a single feed poll
  POST   /api/v1/feeds/poll-all          — trigger poll of all active feeds
  POST   /api/v1/feeds/{feed_id}/pause   — pause a feed
  POST   /api/v1/feeds/{feed_id}/resume  — resume a feed
  DELETE /api/v1/feeds/{feed_id}         — unregister a feed
  GET    /api/v1/feeds/stats             — aggregated ingestion stats
  POST   /api/v1/feeds/buffer/retry      — retry routing buffered signals
  GET    /api/v1/feeds/buffer/peek       — peek at buffered signals

No business logic. Routes delegate to FeedOrchestrator.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.signal_intel.feed_registry import create_adapter
from src.signal_intel.orchestrator import FeedOrchestrator, get_feed_orchestrator
from src.signal_intel.types import FeedConfig

router = APIRouter(prefix="/api/v1/feeds", tags=["signal-intelligence"])


# ── Response Models ─────────────────────────────────────────────────────────

class FeedRegistrationResponse(BaseModel):
    feed_id: str
    status: str
    message: str


class PollResponse(BaseModel):
    feeds_polled: int = 0
    items_fetched: int = 0
    items_new: int = 0
    items_duplicate: int = 0
    items_routed: int = 0
    items_rejected: int = 0
    duration_ms: float = 0.0


class BufferRetryResponse(BaseModel):
    retried: int = 0
    routed: int = 0


# ── POST /feeds — Register Feed ────────────────────────────────────────────

@router.post(
    "",
    response_model=FeedRegistrationResponse,
    status_code=201,
    summary="Register a new feed source",
)
async def register_feed(
    config: FeedConfig,
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    try:
        adapter = create_adapter(config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    orchestrator.register_feed(config, adapter)
    return FeedRegistrationResponse(
        feed_id=config.feed_id,
        status="registered",
        message=f"Feed '{config.name}' registered successfully",
    )


# ── GET /feeds — List Feeds ────────────────────────────────────────────────

@router.get(
    "",
    summary="List all registered feeds",
)
async def list_feeds(
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    return {"feeds": orchestrator.list_feeds()}


# ── GET /feeds/stats — Aggregated Stats ─────────────────────────────────────

@router.get(
    "/stats",
    summary="Get aggregated ingestion statistics",
)
async def get_stats(
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    return orchestrator.get_stats()


# ── GET /feeds/{feed_id} — Feed Status ──────────────────────────────────────

@router.get(
    "/{feed_id}",
    summary="Get status of a specific feed",
)
async def get_feed(
    feed_id: str,
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    status = orchestrator.get_feed_status(feed_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Feed '{feed_id}' not found")
    return status


# ── POST /feeds/{feed_id}/poll — Poll Single Feed ───────────────────────────

@router.post(
    "/{feed_id}/poll",
    response_model=PollResponse,
    summary="Trigger poll for a single feed",
)
async def poll_feed(
    feed_id: str,
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    result = await orchestrator.poll_feed(feed_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Feed '{feed_id}' not found")

    return PollResponse(
        feeds_polled=1,
        items_fetched=result.items_fetched,
        items_new=result.items_new,
        items_duplicate=result.items_duplicate,
        items_routed=result.items_routed,
        items_rejected=result.items_rejected,
        duration_ms=result.duration_ms,
    )


# ── POST /feeds/poll-all — Poll All Active Feeds ───────────────────────────

@router.post(
    "/poll-all",
    response_model=PollResponse,
    summary="Trigger poll for all active feeds",
)
async def poll_all_feeds(
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    cycle = await orchestrator.poll_all()
    return PollResponse(
        feeds_polled=cycle.feeds_polled,
        items_fetched=cycle.items_fetched,
        items_new=cycle.items_new,
        items_duplicate=cycle.items_duplicate,
        items_routed=cycle.items_routed,
        items_rejected=cycle.items_rejected,
        duration_ms=cycle.duration_ms,
    )


# ── POST /feeds/{feed_id}/pause — Pause Feed ───────────────────────────────

@router.post(
    "/{feed_id}/pause",
    summary="Pause a feed (stop polling)",
)
async def pause_feed(
    feed_id: str,
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    if not orchestrator.pause_feed(feed_id):
        raise HTTPException(status_code=404, detail=f"Feed '{feed_id}' not found")
    return {"feed_id": feed_id, "status": "paused"}


# ── POST /feeds/{feed_id}/resume — Resume Feed ─────────────────────────────

@router.post(
    "/{feed_id}/resume",
    summary="Resume a paused feed",
)
async def resume_feed(
    feed_id: str,
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    if not orchestrator.resume_feed(feed_id):
        raise HTTPException(status_code=404, detail=f"Feed '{feed_id}' not found")
    return {"feed_id": feed_id, "status": "active"}


# ── DELETE /feeds/{feed_id} — Unregister Feed ──────────────────────────────

@router.delete(
    "/{feed_id}",
    summary="Unregister a feed",
)
async def unregister_feed(
    feed_id: str,
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    if not orchestrator.unregister_feed(feed_id):
        raise HTTPException(status_code=404, detail=f"Feed '{feed_id}' not found")
    return {"feed_id": feed_id, "status": "unregistered"}


# ── POST /feeds/buffer/retry — Retry Buffered Signals ───────────────────────

@router.post(
    "/buffer/retry",
    response_model=BufferRetryResponse,
    summary="Retry routing buffered signals",
)
async def retry_buffer(
    count: int = Query(10, ge=1, le=100),
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    routed = orchestrator.retry_buffered(count)
    return BufferRetryResponse(retried=count, routed=routed)


# ── GET /feeds/buffer/peek — Peek at Buffer ─────────────────────────────────

@router.get(
    "/buffer/peek",
    summary="Peek at signals in the fail-safe buffer",
)
async def peek_buffer(
    count: int = Query(10, ge=1, le=50),
    orchestrator: FeedOrchestrator = Depends(get_feed_orchestrator),
):
    buffered = orchestrator._buffer.peek(count)
    return {
        "buffer_size": orchestrator._buffer.size,
        "items": [
            {
                "buffer_id": str(b.buffer_id),
                "feed_id": b.feed_id,
                "item_id": b.item_id,
                "content_hash": b.content_hash[:16] + "...",
                "buffered_at": b.buffered_at.isoformat(),
                "route_attempts": b.route_attempts,
                "last_error": b.last_route_error,
            }
            for b in buffered
        ],
    }
