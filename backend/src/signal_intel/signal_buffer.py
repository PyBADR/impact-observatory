"""Signal Intelligence Layer — Fail-Safe Signal Buffer.

If downstream routing is disabled or fails, normalized signals
are stored here safely. The buffer persists signals until they
are either successfully routed or explicitly drained.

Storage: in-memory ordered dict with configurable max capacity.
Swappable to PostgreSQL/Redis in production via interface.

Design rules:
  - Buffer accepts MacroSignalInput (Pack 1 intake format)
  - Buffer never drops signals silently — capacity overflow
    triggers oldest eviction with audit log
  - All operations are idempotent via content_hash tracking
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.signal_intel.types import IngestionRecord, IngestionStatus

logger = logging.getLogger("signal_intel.buffer")


class BufferedSignal(BaseModel):
    """A signal waiting in the buffer for downstream routing."""
    buffer_id: UUID = Field(default_factory=uuid4)
    content_hash: str
    feed_id: str
    item_id: str
    signal_input: dict  # Serialized MacroSignalInput
    buffered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    route_attempts: int = 0
    last_route_error: Optional[str] = None


class SignalBuffer:
    """Fail-safe buffer for signals pending downstream routing.

    Thread-safe under Python GIL.
    """

    def __init__(self, max_capacity: int = 10_000) -> None:
        self._max_capacity = max_capacity
        self._buffer: OrderedDict[str, BufferedSignal] = OrderedDict()
        self._audit: list[IngestionRecord] = []
        self._stats = {
            "buffered": 0,
            "drained": 0,
            "evicted": 0,
            "route_failures": 0,
        }

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def stats(self) -> dict:
        return {**self._stats, "buffer_size": self.size}

    def add(
        self,
        signal_input: dict,
        content_hash: str,
        feed_id: str,
        item_id: str,
    ) -> BufferedSignal:
        """Add a signal to the buffer.

        If content_hash already buffered, returns existing entry (idempotent).
        If at capacity, evicts oldest signal with audit log.
        """
        # Idempotent check
        if content_hash in self._buffer:
            return self._buffer[content_hash]

        # Capacity check
        if len(self._buffer) >= self._max_capacity:
            evicted_hash, evicted = self._buffer.popitem(last=False)
            self._stats["evicted"] += 1
            logger.warning(
                "Buffer full (%d). Evicted oldest: feed=%s item=%s hash=%s",
                self._max_capacity, evicted.feed_id, evicted.item_id,
                evicted_hash[:16],
            )
            self._audit.append(IngestionRecord(
                item_id=evicted.item_id,
                feed_id=evicted.feed_id,
                content_hash=evicted_hash,
                status=IngestionStatus.FAILED,
                error="evicted_from_buffer_overflow",
            ))

        entry = BufferedSignal(
            content_hash=content_hash,
            feed_id=feed_id,
            item_id=item_id,
            signal_input=signal_input,
        )
        self._buffer[content_hash] = entry
        self._stats["buffered"] += 1

        return entry

    def drain(self, count: int | None = None) -> list[BufferedSignal]:
        """Remove and return signals from the buffer (FIFO order).

        Args:
            count: Max signals to drain. None = drain all.

        Returns:
            List of BufferedSignal in insertion order.
        """
        if count is None:
            count = len(self._buffer)

        drained: list[BufferedSignal] = []
        keys_to_remove = list(self._buffer.keys())[:count]

        for key in keys_to_remove:
            entry = self._buffer.pop(key)
            drained.append(entry)
            self._stats["drained"] += 1

        return drained

    def peek(self, count: int = 10) -> list[BufferedSignal]:
        """Peek at the oldest signals without removing them."""
        return list(self._buffer.values())[:count]

    def mark_route_failure(self, content_hash: str, error: str) -> None:
        """Record a routing failure for a buffered signal."""
        if content_hash in self._buffer:
            entry = self._buffer[content_hash]
            entry.route_attempts += 1
            entry.last_route_error = error
            self._stats["route_failures"] += 1

    def remove(self, content_hash: str) -> BufferedSignal | None:
        """Remove a specific signal by content hash."""
        return self._buffer.pop(content_hash, None)

    def get_audit_log(self, limit: int = 100) -> list[IngestionRecord]:
        """Return recent audit records."""
        return list(reversed(self._audit[-limit:]))

    def clear(self) -> None:
        """Clear buffer and audit log. For testing only."""
        self._buffer.clear()
        self._audit.clear()
        self._stats = {
            "buffered": 0, "drained": 0, "evicted": 0, "route_failures": 0,
        }
