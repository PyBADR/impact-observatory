"""Signal Intelligence Layer — Feed Orchestrator.

Top-level coordinator for the ingestion pipeline:
  1. Manages feed adapter lifecycle
  2. Polls feeds on schedule
  3. Deduplicates items
  4. Maps to MacroSignalInput
  5. Buffers or routes into Pack 1

The orchestrator is the ONLY public entry point for external feed ingestion.
It is NOT an autonomous loop — it must be triggered by API call or scheduler.

Design rules:
  - No background threads or autonomous loops
  - All state is in-memory (swappable to persistent store)
  - Fail-safe: adapter failures don't crash the orchestrator
  - Observable: every step produces audit-quality metrics
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from src.signal_intel.base_adapter import BaseFeedAdapter
from src.signal_intel.dedup import DedupEngine
from src.signal_intel.mapper import map_feed_item
from src.signal_intel.router import RouteResult, SignalRouter
from src.signal_intel.signal_buffer import SignalBuffer
from src.signal_intel.types import (
    FeedConfig,
    FeedResult,
    FeedStatus,
    FeedType,
)

logger = logging.getLogger("signal_intel.orchestrator")


class FeedState:
    """Runtime state for a single feed."""

    def __init__(self, config: FeedConfig, adapter: BaseFeedAdapter) -> None:
        self.config = config
        self.adapter = adapter
        self.status: FeedStatus = FeedStatus.ACTIVE if config.enabled else FeedStatus.DISABLED
        self.last_poll: datetime | None = None
        self.last_result: FeedResult | None = None
        self.total_items_fetched: int = 0
        self.total_items_routed: int = 0
        self.total_errors: int = 0
        self.consecutive_errors: int = 0


class PollCycleResult:
    """Aggregated result of polling all feeds in one cycle."""

    def __init__(self) -> None:
        self.feeds_polled: int = 0
        self.feeds_errored: int = 0
        self.items_fetched: int = 0
        self.items_new: int = 0
        self.items_duplicate: int = 0
        self.items_mapped: int = 0
        self.items_buffered: int = 0
        self.items_routed: int = 0
        self.items_rejected: int = 0
        self.duration_ms: float = 0.0
        self.feed_results: list[FeedResult] = []

    def to_dict(self) -> dict:
        return {
            "feeds_polled": self.feeds_polled,
            "feeds_errored": self.feeds_errored,
            "items_fetched": self.items_fetched,
            "items_new": self.items_new,
            "items_duplicate": self.items_duplicate,
            "items_mapped": self.items_mapped,
            "items_buffered": self.items_buffered,
            "items_routed": self.items_routed,
            "items_rejected": self.items_rejected,
            "duration_ms": round(self.duration_ms, 2),
        }


class FeedOrchestrator:
    """Coordinates feed polling, dedup, mapping, and routing.

    Usage:
        orchestrator = FeedOrchestrator(router=signal_router)
        orchestrator.register_feed(config, adapter)
        result = await orchestrator.poll_all()
    """

    def __init__(
        self,
        router: SignalRouter | None = None,
        dedup: DedupEngine | None = None,
        buffer: SignalBuffer | None = None,
        route_enabled: bool = True,
    ) -> None:
        self._feeds: dict[str, FeedState] = {}
        self._router = router
        self._dedup = dedup or DedupEngine()
        self._buffer = buffer or SignalBuffer()
        self._route_enabled = route_enabled

    @property
    def feed_count(self) -> int:
        return len(self._feeds)

    @property
    def active_feed_count(self) -> int:
        return sum(1 for f in self._feeds.values() if f.status == FeedStatus.ACTIVE)

    # ── Feed Management ─────────────────────────────────────────────────────

    def register_feed(self, config: FeedConfig, adapter: BaseFeedAdapter) -> None:
        """Register a feed adapter.

        Replaces existing feed with same feed_id.
        """
        state = FeedState(config=config, adapter=adapter)
        self._feeds[config.feed_id] = state
        logger.info(
            "Feed registered: %s (%s) url=%s",
            config.feed_id, config.feed_type.value, config.url[:80],
        )

    def unregister_feed(self, feed_id: str) -> bool:
        """Unregister a feed. Returns True if found."""
        return self._feeds.pop(feed_id, None) is not None

    def get_feed_status(self, feed_id: str) -> dict | None:
        """Get status of a specific feed."""
        state = self._feeds.get(feed_id)
        if not state:
            return None
        return {
            "feed_id": state.config.feed_id,
            "feed_type": state.config.feed_type.value,
            "name": state.config.name,
            "status": state.status.value,
            "enabled": state.config.enabled,
            "last_poll": state.last_poll.isoformat() if state.last_poll else None,
            "total_items_fetched": state.total_items_fetched,
            "total_items_routed": state.total_items_routed,
            "total_errors": state.total_errors,
            "consecutive_errors": state.consecutive_errors,
        }

    def list_feeds(self) -> list[dict]:
        """List all registered feeds with status."""
        return [self.get_feed_status(fid) for fid in self._feeds]

    def pause_feed(self, feed_id: str) -> bool:
        """Pause a feed. Returns True if found."""
        state = self._feeds.get(feed_id)
        if state:
            state.status = FeedStatus.PAUSED
            return True
        return False

    def resume_feed(self, feed_id: str) -> bool:
        """Resume a paused feed. Returns True if found."""
        state = self._feeds.get(feed_id)
        if state:
            state.status = FeedStatus.ACTIVE
            state.consecutive_errors = 0
            return True
        return False

    # ── Polling ─────────────────────────────────────────────────────────────

    async def poll_feed(self, feed_id: str) -> FeedResult | None:
        """Poll a single feed. Returns None if feed not found."""
        state = self._feeds.get(feed_id)
        if not state:
            return None
        return await self._poll_single(state)

    async def poll_all(self) -> PollCycleResult:
        """Poll all active feeds sequentially.

        Sequential to avoid overwhelming external APIs.
        For parallel polling, use poll_feed() with asyncio.gather().
        """
        cycle = PollCycleResult()
        start = time.monotonic()

        for feed_id, state in self._feeds.items():
            if state.status != FeedStatus.ACTIVE:
                continue

            result = await self._poll_single(state)
            cycle.feeds_polled += 1
            cycle.items_fetched += result.items_fetched
            cycle.items_new += result.items_new
            cycle.items_duplicate += result.items_duplicate
            cycle.items_routed += result.items_routed
            cycle.items_rejected += result.items_rejected
            cycle.feed_results.append(result)

            if not result.success:
                cycle.feeds_errored += 1

        cycle.items_mapped = cycle.items_new  # mapped = non-duplicate fetched
        cycle.items_buffered = self._buffer.size
        cycle.duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "Poll cycle complete: %d feeds, %d fetched, %d new, %d routed, %d rejected (%.0fms)",
            cycle.feeds_polled, cycle.items_fetched, cycle.items_new,
            cycle.items_routed, cycle.items_rejected, cycle.duration_ms,
        )

        return cycle

    async def _poll_single(self, state: FeedState) -> FeedResult:
        """Poll a single feed through the full pipeline."""
        # Step 1: Fetch + parse via adapter
        result = await state.adapter.poll()
        items = state.adapter.get_items_from_result(result)

        state.last_poll = datetime.now(timezone.utc)
        state.last_result = result
        state.total_items_fetched += result.items_fetched

        if not result.success:
            state.consecutive_errors += 1
            state.total_errors += 1
            if state.consecutive_errors >= 5:
                state.status = FeedStatus.ERROR
                logger.warning(
                    "Feed %s disabled after %d consecutive errors",
                    state.config.feed_id, state.consecutive_errors,
                )
            return result

        state.consecutive_errors = 0

        # Step 2-5: Process each item
        for item in items:
            # Step 2: Dedup
            if self._dedup.is_duplicate(item):
                result.items_duplicate += 1
                continue

            result.items_new += 1

            # Step 3: Map to MacroSignalInput
            mapped = map_feed_item(item)
            if mapped is None:
                result.items_rejected += 1
                continue

            # Step 4: Buffer the signal
            content_hash = item.content_hash or item.compute_content_hash()
            serialized = mapped.model_dump(mode="json")

            self._buffer.add(
                signal_input=serialized,
                content_hash=content_hash,
                feed_id=item.feed_id,
                item_id=item.item_id,
            )

            # Step 5: Route (if enabled)
            if self._route_enabled and self._router:
                route_result = self._router.route(
                    signal_input=mapped,
                    feed_id=item.feed_id,
                    item_id=item.item_id,
                    content_hash=content_hash,
                )
                if route_result.success:
                    result.items_routed += 1
                    state.total_items_routed += 1
                    # Remove from buffer on successful route
                    self._buffer.remove(content_hash)
                else:
                    # Keep in buffer for retry
                    self._buffer.mark_route_failure(
                        content_hash,
                        "; ".join(route_result.errors),
                    )
                    result.items_rejected += 1

            # Mark as seen in dedup cache (after successful buffer/route)
            self._dedup.mark_seen(item)

        return result

    # ── Buffer Operations ───────────────────────────────────────────────────

    def drain_buffer(self, count: int | None = None) -> list[dict]:
        """Drain signals from the buffer. Returns serialized MacroSignalInput dicts."""
        drained = self._buffer.drain(count)
        return [entry.signal_input for entry in drained]

    def retry_buffered(self, count: int = 10) -> int:
        """Retry routing buffered signals. Returns count of successfully routed."""
        if not self._router:
            return 0

        buffered = self._buffer.peek(count)
        routed = 0

        for entry in buffered:
            try:
                from src.macro.macro_schemas import MacroSignalInput
                signal_input = MacroSignalInput.model_validate(entry.signal_input)
                route_result = self._router.route(
                    signal_input=signal_input,
                    feed_id=entry.feed_id,
                    item_id=entry.item_id,
                    content_hash=entry.content_hash,
                )
                if route_result.success:
                    self._buffer.remove(entry.content_hash)
                    routed += 1
                else:
                    self._buffer.mark_route_failure(
                        entry.content_hash,
                        "; ".join(route_result.errors),
                    )
            except Exception as exc:
                logger.warning("Buffer retry failed: %s", exc)
                self._buffer.mark_route_failure(
                    entry.content_hash, str(exc),
                )

        return routed

    # ── Observability ───────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Full orchestrator statistics."""
        return {
            "feeds": {
                "total": self.feed_count,
                "active": self.active_feed_count,
            },
            "dedup": self._dedup.stats,
            "buffer": self._buffer.stats,
            "router": self._router.stats if self._router else {},
        }


# ── Module-level singleton ──────────────────────────────────────────────────

_default_orchestrator: FeedOrchestrator | None = None


def get_feed_orchestrator() -> FeedOrchestrator:
    """Get or create the singleton orchestrator.

    Lazy initialization: creates router with default signal service
    on first access.
    """
    global _default_orchestrator
    if _default_orchestrator is None:
        from src.macro.macro_signal_service import get_signal_service
        from src.signal_intel.router import SignalRouter

        # Try to get graph adapter (optional)
        graph_adapter = None
        try:
            from src.graph_brain.macro_adapter import MacroGraphAdapter
            from src.graph_brain.store import GraphStore
            graph_adapter = MacroGraphAdapter(GraphStore())
        except ImportError:
            logger.info("Graph Brain not available — routing without graph ingestion")

        router = SignalRouter(
            signal_service=get_signal_service(),
            graph_adapter=graph_adapter,
            auto_graph_ingest=True,
        )
        _default_orchestrator = FeedOrchestrator(router=router)

    return _default_orchestrator


def reset_orchestrator() -> None:
    """Reset the singleton. For testing only."""
    global _default_orchestrator
    _default_orchestrator = None
