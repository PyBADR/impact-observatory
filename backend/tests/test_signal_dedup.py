"""Signal Intelligence Layer — Deduplication Tests.

Tests for:
  1. DedupStore.is_duplicate() — not duplicate when unseen
  2. DedupStore.is_duplicate() — duplicate after mark_seen
  3. DedupStore.check_and_mark() — atomic check+mark
  4. DedupStore.check_and_mark() — returns True for duplicate
  5. DedupStore.check_and_mark() — returns False for new
  6. DedupStore.has_key() — key lookup
  7. DedupStore.remove() — key removal
  8. DedupStore.clear() — clears all entries
  9. DedupStore.snapshot() — returns copy
  10. DedupStore.size — correct count
  11. DedupStore TTL — expired key treated as new
  12. DedupStore TTL — unexpired key still duplicate
  13. filter_duplicates() — correct partition
  14. filter_duplicates() — marks new events seen
  15. compute_dedup_key() — delegates to event.dedup_key
  16. is_duplicate() functional alias
  17. Dedup key stability: same event → same key
  18. External ID dedup key format
  19. Hash dedup key format
  20. Different sources → different keys
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.signals.source_models import SourceEvent, SourceType
from src.signals.dedup import (
    DedupStore,
    compute_dedup_key,
    filter_duplicates,
    is_duplicate,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _make_event(
    title: str = "Test event",
    external_id: str | None = None,
    source_name: str = "Test Source",
    published_at: datetime | None = None,
) -> SourceEvent:
    return SourceEvent(
        source_type=SourceType.RSS,
        source_name=source_name,
        source_ref="https://feeds.test.com",
        external_id=external_id,
        title=title,
        published_at=published_at,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1–2. is_duplicate after mark
# ══════════════════════════════════════════════════════════════════════════════

class TestIsDuplicate:

    def test_not_duplicate_when_unseen(self):
        store = DedupStore()
        event = _make_event()
        assert store.is_duplicate(event) is False

    def test_duplicate_after_mark_seen(self):
        store = DedupStore()
        event = _make_event()
        store.mark_seen(event)
        assert store.is_duplicate(event) is True

    def test_different_event_not_duplicate(self):
        store = DedupStore()
        e1 = _make_event(title="Event One")
        e2 = _make_event(title="Event Two")
        store.mark_seen(e1)
        assert store.is_duplicate(e2) is False

    def test_same_external_id_is_duplicate(self):
        store = DedupStore()
        e1 = _make_event(external_id="ext-abc")
        e2 = _make_event(title="Different title", external_id="ext-abc")
        store.mark_seen(e1)
        # Same external_id → same dedup_key → duplicate
        assert store.is_duplicate(e2) is True

    def test_different_external_id_not_duplicate(self):
        store = DedupStore()
        e1 = _make_event(external_id="ext-001")
        e2 = _make_event(external_id="ext-002")
        store.mark_seen(e1)
        assert store.is_duplicate(e2) is False


# ══════════════════════════════════════════════════════════════════════════════
# 3–5. check_and_mark
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckAndMark:

    def test_returns_false_for_new_event(self):
        store = DedupStore()
        event = _make_event()
        result = store.check_and_mark(event)
        assert result is False

    def test_returns_true_for_duplicate(self):
        store = DedupStore()
        event = _make_event(external_id="dedup-001")
        store.check_and_mark(event)  # first call marks it
        result = store.check_and_mark(event)  # second call should be duplicate
        assert result is True

    def test_marks_event_seen_on_first_call(self):
        store = DedupStore()
        event = _make_event()
        store.check_and_mark(event)
        assert store.is_duplicate(event) is True

    def test_does_not_remark_on_duplicate(self):
        """check_and_mark on a duplicate should not update first_seen_at."""
        store = DedupStore()
        event = _make_event(external_id="stable-id")
        store.check_and_mark(event)
        first_seen = store.snapshot()[event.dedup_key]
        store.check_and_mark(event)
        assert store.snapshot()[event.dedup_key] == first_seen


# ══════════════════════════════════════════════════════════════════════════════
# 6. has_key
# ══════════════════════════════════════════════════════════════════════════════

class TestHasKey:

    def test_has_key_after_mark(self):
        store = DedupStore()
        event = _make_event(external_id="key-001")
        store.mark_seen(event)
        assert store.has_key(event.dedup_key) is True

    def test_no_key_before_mark(self):
        store = DedupStore()
        event = _make_event()
        assert store.has_key(event.dedup_key) is False


# ══════════════════════════════════════════════════════════════════════════════
# 7. remove
# ══════════════════════════════════════════════════════════════════════════════

class TestRemove:

    def test_remove_key(self):
        store = DedupStore()
        event = _make_event(external_id="remove-me")
        store.mark_seen(event)
        assert store.is_duplicate(event) is True
        store.remove(event.dedup_key)
        assert store.is_duplicate(event) is False

    def test_remove_nonexistent_key_no_error(self):
        store = DedupStore()
        store.remove("nonexistent-key")  # should not raise


# ══════════════════════════════════════════════════════════════════════════════
# 8. clear
# ══════════════════════════════════════════════════════════════════════════════

class TestClear:

    def test_clear_resets_store(self):
        store = DedupStore()
        for i in range(5):
            store.mark_seen(_make_event(external_id=f"ext-{i}"))
        assert store.size == 5
        store.clear()
        assert store.size == 0

    def test_after_clear_events_not_duplicate(self):
        store = DedupStore()
        event = _make_event(external_id="after-clear")
        store.mark_seen(event)
        store.clear()
        assert store.is_duplicate(event) is False


# ══════════════════════════════════════════════════════════════════════════════
# 9. snapshot
# ══════════════════════════════════════════════════════════════════════════════

class TestSnapshot:

    def test_snapshot_returns_copy(self):
        store = DedupStore()
        event = _make_event(external_id="snap-001")
        store.mark_seen(event)
        snap = store.snapshot()
        assert isinstance(snap, dict)
        assert event.dedup_key in snap

    def test_snapshot_is_copy_not_reference(self):
        store = DedupStore()
        event = _make_event(external_id="snap-002")
        store.mark_seen(event)
        snap = store.snapshot()
        snap.clear()
        # Store should still have the key
        assert store.has_key(event.dedup_key) is True


# ══════════════════════════════════════════════════════════════════════════════
# 10. size
# ══════════════════════════════════════════════════════════════════════════════

class TestSize:

    def test_size_starts_zero(self):
        assert DedupStore().size == 0

    def test_size_increments(self):
        store = DedupStore()
        for i in range(3):
            store.mark_seen(_make_event(title=f"Event {i}"))
        assert store.size == 3

    def test_size_same_key_no_increment(self):
        store = DedupStore()
        event = _make_event(external_id="same-key")
        store.mark_seen(event)
        store.mark_seen(event)
        assert store.size == 1


# ══════════════════════════════════════════════════════════════════════════════
# 11–12. TTL behavior
# ══════════════════════════════════════════════════════════════════════════════

class TestTTL:

    def test_ttl_none_never_expires(self):
        store = DedupStore(ttl_seconds=None)
        event = _make_event(external_id="no-expire")
        store.mark_seen(event)
        # Manually set first_seen to 1 year ago
        store._seen[event.dedup_key] = datetime.now(timezone.utc) - timedelta(days=365)
        assert store.is_duplicate(event) is True

    def test_ttl_expired_treated_as_new(self):
        store = DedupStore(ttl_seconds=10)  # 10 seconds TTL
        event = _make_event(external_id="expire-me")
        store.mark_seen(event)
        # Manually set first_seen to well past TTL
        store._seen[event.dedup_key] = datetime.now(timezone.utc) - timedelta(seconds=60)
        # Should be treated as new (expired)
        assert store.is_duplicate(event) is False

    def test_ttl_not_expired_still_duplicate(self):
        store = DedupStore(ttl_seconds=3600)  # 1 hour TTL
        event = _make_event(external_id="not-expired")
        store.mark_seen(event)
        # Just 5 seconds ago — still valid
        store._seen[event.dedup_key] = datetime.now(timezone.utc) - timedelta(seconds=5)
        assert store.is_duplicate(event) is True

    def test_has_key_ttl_expired(self):
        store = DedupStore(ttl_seconds=10)
        event = _make_event(external_id="key-expire")
        store.mark_seen(event)
        store._seen[event.dedup_key] = datetime.now(timezone.utc) - timedelta(seconds=60)
        assert store.has_key(event.dedup_key) is False


# ══════════════════════════════════════════════════════════════════════════════
# 13–14. filter_duplicates
# ══════════════════════════════════════════════════════════════════════════════

class TestFilterDuplicates:

    def test_all_new_events(self):
        store = DedupStore()
        events = [_make_event(title=f"Event {i}") for i in range(3)]
        new, dupes = filter_duplicates(events, store)
        assert len(new) == 3
        assert len(dupes) == 0

    def test_all_duplicate_events(self):
        store = DedupStore()
        events = [_make_event(external_id="same-ext") for _ in range(3)]
        # First pass marks them
        new1, _ = filter_duplicates(events[:1], store)
        # Second pass — remaining are duplicates
        new2, dupes = filter_duplicates(events[1:], store)
        assert len(dupes) == 2
        assert len(new2) == 0

    def test_mixed_events(self):
        store = DedupStore()
        e1 = _make_event(external_id="unique-1")
        e2 = _make_event(external_id="unique-2")
        store.mark_seen(e1)

        new, dupes = filter_duplicates([e1, e2], store)
        assert len(new) == 1
        assert len(dupes) == 1
        assert new[0].dedup_key == e2.dedup_key
        assert dupes[0].dedup_key == e1.dedup_key

    def test_marks_new_events_as_seen(self):
        store = DedupStore()
        events = [_make_event(external_id=f"mark-{i}") for i in range(2)]
        filter_duplicates(events, store)
        for e in events:
            assert store.is_duplicate(e) is True

    def test_empty_list(self):
        store = DedupStore()
        new, dupes = filter_duplicates([], store)
        assert new == []
        assert dupes == []

    def test_preserves_event_order(self):
        store = DedupStore()
        events = [_make_event(title=f"Ordered {i}") for i in range(4)]
        new, _ = filter_duplicates(events, store)
        titles = [e.title for e in new]
        assert titles == [f"Ordered {i}" for i in range(4)]


# ══════════════════════════════════════════════════════════════════════════════
# 15. compute_dedup_key
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeDedupKey:

    def test_returns_event_dedup_key(self):
        event = _make_event(external_id="test-key")
        assert compute_dedup_key(event) == event.dedup_key

    def test_returns_hash_for_no_external_id(self):
        event = _make_event()
        key = compute_dedup_key(event)
        assert key.startswith("hash:")


# ══════════════════════════════════════════════════════════════════════════════
# 16. is_duplicate functional alias
# ══════════════════════════════════════════════════════════════════════════════

class TestIsDuplicateAlias:

    def test_functional_alias_matches_store(self):
        store = DedupStore()
        event = _make_event(external_id="alias-test")
        assert is_duplicate(event, store) is False
        store.mark_seen(event)
        assert is_duplicate(event, store) is True


# ══════════════════════════════════════════════════════════════════════════════
# 17–20. Dedup key properties
# ══════════════════════════════════════════════════════════════════════════════

class TestDedupKeyProperties:

    def test_same_external_id_same_key(self):
        e1 = _make_event(title="Different A", external_id="shared-ext")
        e2 = _make_event(title="Different B", external_id="shared-ext")
        assert e1.dedup_key == e2.dedup_key

    def test_different_external_id_different_key(self):
        e1 = _make_event(external_id="ext-alpha")
        e2 = _make_event(external_id="ext-beta")
        assert e1.dedup_key != e2.dedup_key

    def test_external_id_key_format(self):
        event = _make_event(external_id="my-guid-123")
        assert event.dedup_key == "ext:my-guid-123"

    def test_hash_key_format(self):
        event = _make_event(title="Hash test")
        assert event.dedup_key.startswith("hash:")
        hash_part = event.dedup_key[5:]
        assert len(hash_part) == 64  # SHA-256 hex

    def test_different_source_names_different_keys(self):
        e1 = _make_event(title="Same title", source_name="Source A")
        e2 = _make_event(title="Same title", source_name="Source B")
        assert e1.dedup_key != e2.dedup_key

    def test_dedup_key_never_empty(self):
        for i in range(5):
            event = _make_event(title=f"Event {i}")
            assert event.dedup_key != ""
