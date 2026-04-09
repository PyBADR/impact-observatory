"""Signal Intelligence Layer — Deduplication.

Deterministic deduplication for SourceEvent objects.

Algorithm (in priority order):
  1. external_id (from feed item) — most precise
  2. content hash of (source_name, source_ref, title, published_at) — fallback

The DedupStore maintains a set of seen dedup_keys for the current session.
It is intentionally in-memory and reset per service restart — no persistent
cross-session dedup. Persistent dedup is a storage concern outside this layer.

Design rules:
  - Deterministic: same SourceEvent → same dedup_key
  - No ML, no fuzzy matching
  - dedup_key is pre-computed on SourceEvent by model_validator
  - DedupStore is thread-safe for single-process FastAPI
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.signals.source_models import SourceEvent

logger = logging.getLogger("signals.dedup")


# ── Dedup Key Accessor ────────────────────────────────────────────────────────

def compute_dedup_key(event: SourceEvent) -> str:
    """Return the dedup key for a SourceEvent.

    The key is already computed by SourceEvent.model_validator and stored
    in event.dedup_key. This function is a stable accessor for external callers.

    Key format:
      - "ext:{external_id}"   when external_id is present
      - "hash:{sha256}"       fallback content hash
    """
    return event.dedup_key


# ── In-Memory Dedup Store ─────────────────────────────────────────────────────

class DedupStore:
    """In-memory set of seen dedup_keys for session-scoped deduplication.

    Entries expire after ttl_seconds (default: no expiry / session-scoped).
    For persistent cross-session dedup, replace this with a Redis/DB-backed store.

    Usage:
        store = DedupStore()
        if store.is_duplicate(event):
            skip
        else:
            store.mark_seen(event)
            process(event)
    """

    def __init__(self, ttl_seconds: int | None = None) -> None:
        """
        Args:
            ttl_seconds: If set, entries expire after this many seconds.
                         None (default) = session-scoped, no expiry.
        """
        self._seen: dict[str, datetime] = {}  # key → first_seen_at
        self.ttl_seconds = ttl_seconds

    @property
    def size(self) -> int:
        """Number of tracked dedup keys (may include expired ones)."""
        return len(self._seen)

    def is_duplicate(self, event: SourceEvent) -> bool:
        """Return True if this event has already been seen.

        Checks event.dedup_key against the store.
        If TTL is set, expired entries are treated as new.
        """
        key = event.dedup_key
        if key not in self._seen:
            return False

        if self.ttl_seconds is None:
            return True

        # TTL check
        first_seen = self._seen[key]
        now = datetime.now(timezone.utc)
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        elapsed = (now - first_seen).total_seconds()
        if elapsed > self.ttl_seconds:
            # Expired — remove and treat as new
            del self._seen[key]
            return False
        return True

    def mark_seen(self, event: SourceEvent) -> None:
        """Record event's dedup_key as seen."""
        key = event.dedup_key
        if key not in self._seen:
            self._seen[key] = datetime.now(timezone.utc)
            logger.debug("DedupStore: marked seen key=%s", key[:32])

    def check_and_mark(self, event: SourceEvent) -> bool:
        """Atomically check if duplicate and mark as seen if not.

        Returns True if the event IS a duplicate (should be skipped).
        Returns False if the event is new (has been marked seen).
        """
        if self.is_duplicate(event):
            logger.debug(
                "DedupStore: duplicate detected key=%s title='%s'",
                event.dedup_key[:32], event.title[:60],
            )
            return True
        self.mark_seen(event)
        return False

    def has_key(self, key: str) -> bool:
        """Check if a specific key is in the store (TTL-aware)."""
        if key not in self._seen:
            return False
        if self.ttl_seconds is None:
            return True
        first_seen = self._seen[key]
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - first_seen).total_seconds()
        if elapsed > self.ttl_seconds:
            del self._seen[key]
            return False
        return True

    def remove(self, key: str) -> None:
        """Remove a key from the store (e.g. if processing failed)."""
        self._seen.pop(key, None)

    def clear(self) -> None:
        """Clear all entries. Primarily for tests."""
        self._seen.clear()

    def snapshot(self) -> dict[str, datetime]:
        """Return a copy of the current seen-keys dict."""
        return dict(self._seen)


# ── Functional Interface ──────────────────────────────────────────────────────

def is_duplicate(event: SourceEvent, store: DedupStore) -> bool:
    """Functional alias for store.is_duplicate(event)."""
    return store.is_duplicate(event)


def filter_duplicates(
    events: list[SourceEvent],
    store: DedupStore,
) -> tuple[list[SourceEvent], list[SourceEvent]]:
    """Partition events into (new_events, duplicate_events).

    Marks each new event as seen in the store.
    Does NOT mark duplicates.

    Returns:
        (new_events, duplicate_events)
    """
    new_events: list[SourceEvent] = []
    duplicates: list[SourceEvent] = []

    for event in events:
        if store.check_and_mark(event):
            duplicates.append(event)
        else:
            new_events.append(event)

    if duplicates:
        logger.info(
            "filter_duplicates: %d new, %d duplicates (total %d)",
            len(new_events), len(duplicates), len(events),
        )

    return new_events, duplicates
