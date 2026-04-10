"""Signal Intelligence Layer — Deduplication Engine.

Two-tier deduplication strategy:
  1. Content hash exact match (SHA-256 of canonical fields)
  2. Sliding window TTL expiry (auto-evict old hashes)

The dedup engine operates BEFORE Pack 1 intake to prevent
redundant submissions. Pack 1 has its own content_hash dedup
as a second defense layer.

No LLM inference. Pure hash comparison.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from typing import NamedTuple

from src.signal_intel.types import RawFeedItem

logger = logging.getLogger("signal_intel.dedup")


class DedupEntry(NamedTuple):
    """A single dedup cache entry."""
    content_hash: str
    feed_id: str
    item_id: str
    timestamp: float  # monotonic or epoch


class DedupEngine:
    """Content-hash-based deduplication with TTL eviction.

    Thread-safe under Python GIL (single-process FastAPI).
    """

    def __init__(
        self,
        ttl_seconds: int = 86400,  # 24h default
        max_entries: int = 50_000,
    ) -> None:
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        # OrderedDict for efficient LRU-style eviction
        self._cache: OrderedDict[str, DedupEntry] = OrderedDict()
        self._stats = {"checked": 0, "duplicates": 0, "evicted": 0}

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> dict:
        return {**self._stats, "cache_size": self.size}

    def is_duplicate(self, item: RawFeedItem) -> bool:
        """Check if item is a duplicate. Does NOT add to cache.

        Call mark_seen() after successful processing to register the item.
        """
        self._stats["checked"] += 1

        content_hash = item.content_hash or item.compute_content_hash()

        if content_hash in self._cache:
            entry = self._cache[content_hash]
            # Check TTL
            if (time.time() - entry.timestamp) < self._ttl:
                self._stats["duplicates"] += 1
                logger.debug(
                    "Dedup hit: feed=%s item=%s hash=%s",
                    item.feed_id, item.item_id, content_hash[:16],
                )
                return True
            else:
                # Expired — remove and treat as new
                del self._cache[content_hash]
                self._stats["evicted"] += 1

        return False

    def mark_seen(self, item: RawFeedItem) -> None:
        """Register an item as seen in the dedup cache.

        Call this AFTER the item has been successfully processed/buffered.
        """
        content_hash = item.content_hash or item.compute_content_hash()

        self._cache[content_hash] = DedupEntry(
            content_hash=content_hash,
            feed_id=item.feed_id,
            item_id=item.item_id,
            timestamp=time.time(),
        )
        # Move to end (most recent)
        self._cache.move_to_end(content_hash)

        # Evict oldest if over capacity
        self._evict_overflow()

    def _evict_overflow(self) -> None:
        """Evict oldest entries if cache exceeds max_entries."""
        while len(self._cache) > self._max_entries:
            self._cache.popitem(last=False)
            self._stats["evicted"] += 1

    def evict_expired(self) -> int:
        """Manually evict all expired entries. Returns count evicted."""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if (now - v.timestamp) >= self._ttl
        ]
        for k in expired_keys:
            del self._cache[k]
        self._stats["evicted"] += len(expired_keys)
        return len(expired_keys)

    def clear(self) -> None:
        """Reset the dedup cache. For testing only."""
        self._cache.clear()
        self._stats = {"checked": 0, "duplicates": 0, "evicted": 0}
