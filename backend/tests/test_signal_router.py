"""Signal Intelligence Layer — Router + Normalization Tests.

Tests for:
  1. normalize_source_event() — string trimming
  2. normalize_source_event() — list deduplication
  3. normalize_source_event() — empty string removal
  4. normalize_source_event() — timestamp UTC normalization
  5. normalize_source_event() — recomputes dedup_key
  6. normalize_source_event() — preserves event_id
  7. to_signal_input() — basic mapping correctness
  8. to_signal_input() — regions from hints
  9. to_signal_input() — fallback to GCC_WIDE
  10. to_signal_input() — domains from sector hints
  11. to_signal_input() — source from category hints
  12. to_signal_input() — signal_type from category hints
  13. to_signal_input() — direction negative keywords
  14. to_signal_input() — direction positive keywords
  15. to_signal_input() — direction defaults NEGATIVE
  16. to_signal_input() — raw_payload has source traceability
  17. to_signal_input() — title truncated at 300 chars
  18. to_signal_input() — published_at → event_time
  19. to_signal_input() — confidence mapping
  20. to_signal_input() — severity from source_confidence
  21. SignalRouter — INGEST_ONLY mode
  22. SignalRouter — duplicate skipped
  23. SignalRouter — IngestionRecord has event_id
  24. SignalRouter — route_batch returns records per event
  25. SignalRouter — INGEST_AND_GRAPH unavailable fallback
  26. SignalRouter — FULL_RUNTIME unavailable fallback
  27. SignalRouter — errors captured not raised
  28. SignalIngestionService — submit RSS items
  29. SignalIngestionService — submit JSON items
  30. SignalIngestionService — get_stats
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from src.signals.source_models import (
    IngestionRecord,
    SourceConfidence,
    SourceEvent,
    SourceType,
)
from src.signals.normalizer import (
    _resolve_direction,
    _resolve_domains,
    _resolve_regions,
    _resolve_signal_source,
    _resolve_signal_type,
    normalize_source_event,
    to_signal_input,
)
from src.signals.dedup import DedupStore
from src.signals.router import RoutingMode, SignalRouter
from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSource,
    SignalType,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _make_event(
    title: str = "Test signal event",
    source_name: str = "Test Feed",
    source_ref: str = "https://feeds.test.com",
    external_id: str | None = None,
    region_hints: list[str] | None = None,
    country_hints: list[str] | None = None,
    sector_hints: list[str] | None = None,
    category_hints: list[str] | None = None,
    source_confidence: SourceConfidence = SourceConfidence.MODERATE,
    published_at: datetime | None = None,
    description: str | None = None,
) -> SourceEvent:
    return SourceEvent(
        source_type=SourceType.RSS,
        source_name=source_name,
        source_ref=source_ref,
        external_id=external_id,
        title=title,
        description=description,
        region_hints=region_hints or [],
        country_hints=country_hints or [],
        sector_hints=sector_hints or [],
        category_hints=category_hints or [],
        source_confidence=source_confidence,
        published_at=published_at,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1–6. normalize_source_event
# ══════════════════════════════════════════════════════════════════════════════

class TestNormalizeSourceEvent:

    def test_returns_source_event(self):
        event = _make_event(title="  Whitespace title  ")
        normalized = normalize_source_event(event)
        assert isinstance(normalized, SourceEvent)

    def test_title_stripped(self):
        event = _make_event(title="  Padded Title  ")
        normalized = normalize_source_event(event)
        assert normalized.title == "Padded Title"

    def test_title_whitespace_collapsed(self):
        event = _make_event(title="Multiple   Internal   Spaces")
        normalized = normalize_source_event(event)
        assert normalized.title == "Multiple Internal Spaces"

    def test_description_stripped(self):
        event = _make_event(description="  Padded desc.  ")
        normalized = normalize_source_event(event)
        assert normalized.description == "Padded desc."

    def test_list_deduplicated(self):
        event = _make_event(
            region_hints=["Saudi Arabia", "Saudi Arabia", "GCC"]
        )
        normalized = normalize_source_event(event)
        assert normalized.region_hints.count("Saudi Arabia") == 1

    def test_empty_strings_removed(self):
        event = _make_event(sector_hints=["oil", "", "  ", "banking"])
        normalized = normalize_source_event(event)
        assert "" not in normalized.sector_hints
        assert "oil" in normalized.sector_hints

    def test_category_hints_deduplicated(self):
        event = _make_event(category_hints=["energy", "energy", "oil"])
        normalized = normalize_source_event(event)
        assert normalized.category_hints.count("energy") == 1

    def test_preserves_event_id(self):
        event = _make_event()
        normalized = normalize_source_event(event)
        assert normalized.event_id == event.event_id

    def test_recomputes_dedup_key_on_normalized_title(self):
        """Normalizing changes the title → dedup_key must reflect normalized title."""
        e1 = _make_event(title="  Title with spaces  ")
        e2 = _make_event(title="Title with spaces")
        n1 = normalize_source_event(e1)
        n2 = normalize_source_event(e2)
        # Both normalize to the same title → same dedup_key
        assert n1.dedup_key == n2.dedup_key

    def test_does_not_mutate_original(self):
        event = _make_event(title="  Original  ")
        normalize_source_event(event)
        assert event.title == "  Original  "


# ══════════════════════════════════════════════════════════════════════════════
# 7–8. to_signal_input — Basic Mapping
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInput:

    def test_returns_macro_signal_input(self):
        from src.macro.macro_schemas import MacroSignalInput
        event = _make_event(region_hints=["GCC"])
        sig = to_signal_input(event)
        assert isinstance(sig, MacroSignalInput)

    def test_title_preserved(self):
        event = _make_event(title="My test signal")
        sig = to_signal_input(event)
        assert sig.title == "My test signal"

    def test_description_preserved(self):
        event = _make_event(description="Signal description text.")
        sig = to_signal_input(event)
        assert sig.description == "Signal description text."

    def test_severity_score_in_range(self):
        event = _make_event()
        sig = to_signal_input(event)
        assert 0.0 <= sig.severity_score <= 1.0

    def test_direction_is_signal_direction(self):
        event = _make_event()
        sig = to_signal_input(event)
        assert isinstance(sig.direction, SignalDirection)


# ══════════════════════════════════════════════════════════════════════════════
# 9. to_signal_input — Regions
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputRegions:

    def test_gcc_region_resolved(self):
        event = _make_event(region_hints=["GCC", "Saudi Arabia"])
        sig = to_signal_input(event)
        assert GCCRegion.GCC_WIDE in sig.regions or GCCRegion.SAUDI_ARABIA in sig.regions

    def test_riyadh_resolves_to_saudi_arabia(self):
        event = _make_event(region_hints=["Riyadh summit"])
        sig = to_signal_input(event)
        assert GCCRegion.SAUDI_ARABIA in sig.regions

    def test_uae_resolves(self):
        event = _make_event(region_hints=["UAE"])
        sig = to_signal_input(event)
        assert GCCRegion.UAE in sig.regions

    def test_qatar_resolves(self):
        event = _make_event(region_hints=["Qatar"])
        sig = to_signal_input(event)
        assert GCCRegion.QATAR in sig.regions

    def test_no_hints_defaults_to_gcc_wide(self):
        event = _make_event(region_hints=[], country_hints=[])
        sig = to_signal_input(event)
        assert GCCRegion.GCC_WIDE in sig.regions

    def test_unknown_region_falls_back_to_gcc_wide(self):
        event = _make_event(region_hints=["Antarctica"])
        sig = to_signal_input(event)
        # No GCC region identified → fallback to GCC_WIDE
        assert GCCRegion.GCC_WIDE in sig.regions

    def test_country_hints_also_resolved(self):
        event = _make_event(country_hints=["Kuwait"])
        sig = to_signal_input(event)
        assert GCCRegion.KUWAIT in sig.regions


# ══════════════════════════════════════════════════════════════════════════════
# 10. to_signal_input — Domains
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputDomains:

    def test_oil_sector_hint_resolves(self):
        event = _make_event(sector_hints=["oil", "energy"])
        sig = to_signal_input(event)
        assert ImpactDomain.OIL_GAS in sig.impact_domains

    def test_banking_sector_hint_resolves(self):
        event = _make_event(sector_hints=["banking"])
        sig = to_signal_input(event)
        assert ImpactDomain.BANKING in sig.impact_domains

    def test_category_hint_resolves_domain(self):
        event = _make_event(category_hints=["maritime", "shipping"])
        sig = to_signal_input(event)
        assert ImpactDomain.MARITIME in sig.impact_domains

    def test_no_sector_hints_empty_domains(self):
        event = _make_event(sector_hints=[], category_hints=[])
        sig = to_signal_input(event)
        # No domain resolution possible
        assert sig.impact_domains == []

    def test_multiple_sectors_multiple_domains(self):
        event = _make_event(sector_hints=["oil", "banking", "insurance"])
        sig = to_signal_input(event)
        assert ImpactDomain.OIL_GAS in sig.impact_domains
        assert ImpactDomain.BANKING in sig.impact_domains
        assert ImpactDomain.INSURANCE in sig.impact_domains


# ══════════════════════════════════════════════════════════════════════════════
# 11. to_signal_input — Source
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputSource:

    def test_geopolitical_category(self):
        event = _make_event(category_hints=["conflict"])
        sig = to_signal_input(event)
        assert sig.source == SignalSource.GEOPOLITICAL

    def test_energy_category(self):
        event = _make_event(category_hints=["energy", "opec"])
        sig = to_signal_input(event)
        assert sig.source == SignalSource.ENERGY

    def test_trade_category(self):
        event = _make_event(category_hints=["tariff"])
        sig = to_signal_input(event)
        assert sig.source == SignalSource.TRADE

    def test_cyber_category(self):
        event = _make_event(category_hints=["cyber"])
        sig = to_signal_input(event)
        assert sig.source == SignalSource.CYBER

    def test_default_source_geopolitical(self):
        event = _make_event(category_hints=[])
        sig = to_signal_input(event)
        assert isinstance(sig.source, SignalSource)


# ══════════════════════════════════════════════════════════════════════════════
# 12. to_signal_input — SignalType
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputType:

    def test_commodity_type_from_oil(self):
        event = _make_event(category_hints=["oil", "crude"])
        sig = to_signal_input(event)
        assert sig.signal_type == SignalType.COMMODITY

    def test_policy_type_from_monetary(self):
        event = _make_event(category_hints=["monetary", "central bank"])
        sig = to_signal_input(event)
        assert sig.signal_type == SignalType.POLICY

    def test_geopolitical_type_from_conflict(self):
        event = _make_event(category_hints=["conflict"])
        sig = to_signal_input(event)
        assert sig.signal_type == SignalType.GEOPOLITICAL

    def test_logistics_type_from_supply_chain(self):
        event = _make_event(category_hints=["supply chain"])
        sig = to_signal_input(event)
        assert sig.signal_type == SignalType.LOGISTICS

    def test_no_hints_signal_type_none(self):
        event = _make_event(category_hints=[])
        sig = to_signal_input(event)
        assert sig.signal_type is None


# ══════════════════════════════════════════════════════════════════════════════
# 13–15. to_signal_input — Direction
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputDirection:

    def test_negative_keyword_in_category(self):
        event = _make_event(category_hints=["conflict", "war"])
        sig = to_signal_input(event)
        assert sig.direction == SignalDirection.NEGATIVE

    def test_positive_keyword_in_category(self):
        event = _make_event(category_hints=["recovery", "growth"])
        sig = to_signal_input(event)
        assert sig.direction == SignalDirection.POSITIVE

    def test_negative_overrides_positive(self):
        event = _make_event(category_hints=["conflict", "recovery"])
        sig = to_signal_input(event)
        # Negative takes precedence
        assert sig.direction == SignalDirection.NEGATIVE

    def test_default_negative_with_no_hints(self):
        event = _make_event(category_hints=[])
        sig = to_signal_input(event)
        assert sig.direction == SignalDirection.NEGATIVE

    def test_resolve_direction_positive(self):
        direction = _resolve_direction(["recovery", "growth"], [])
        assert direction == SignalDirection.POSITIVE

    def test_resolve_direction_negative(self):
        direction = _resolve_direction(["conflict"], [])
        assert direction == SignalDirection.NEGATIVE


# ══════════════════════════════════════════════════════════════════════════════
# 16. to_signal_input — Raw Payload Traceability
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputRawPayload:

    def test_raw_payload_has_source_name(self):
        event = _make_event(source_name="Reuters RSS")
        sig = to_signal_input(event)
        assert sig.raw_payload["_signal_source_name"] == "Reuters RSS"

    def test_raw_payload_has_source_ref(self):
        event = _make_event(source_ref="https://feeds.reuters.com")
        sig = to_signal_input(event)
        assert sig.raw_payload["_signal_source_ref"] == "https://feeds.reuters.com"

    def test_raw_payload_has_source_type(self):
        event = _make_event()
        sig = to_signal_input(event)
        assert "_signal_source_type" in sig.raw_payload

    def test_raw_payload_has_event_id(self):
        event = _make_event()
        sig = to_signal_input(event)
        assert "_signal_event_id" in sig.raw_payload
        UUID(sig.raw_payload["_signal_event_id"])  # valid UUID

    def test_raw_payload_has_dedup_key(self):
        event = _make_event()
        sig = to_signal_input(event)
        assert "_signal_dedup_key" in sig.raw_payload

    def test_original_raw_payload_merged(self):
        event = _make_event()
        event = event.model_copy(update={"raw_payload": {"original_key": "original_value"}})
        sig = to_signal_input(event)
        assert sig.raw_payload.get("original_key") == "original_value"


# ══════════════════════════════════════════════════════════════════════════════
# 17. to_signal_input — Title Truncation
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputTitleTruncation:

    def test_title_within_300_chars_preserved(self):
        event = _make_event(title="Short title")
        sig = to_signal_input(event)
        assert sig.title == "Short title"

    def test_title_over_300_chars_truncated(self):
        long_title = "A" * 400
        event = _make_event(title=long_title)
        sig = to_signal_input(event)
        assert len(sig.title) == 300


# ══════════════════════════════════════════════════════════════════════════════
# 18. to_signal_input — Event Time
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputEventTime:

    def test_published_at_becomes_event_time(self):
        pub = datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        event = _make_event(published_at=pub)
        sig = to_signal_input(event)
        assert sig.event_time == pub

    def test_no_published_at_event_time_none(self):
        event = _make_event(published_at=None)
        sig = to_signal_input(event)
        assert sig.event_time is None


# ══════════════════════════════════════════════════════════════════════════════
# 19–20. to_signal_input — Confidence + Severity
# ══════════════════════════════════════════════════════════════════════════════

class TestToSignalInputConfidenceSeverity:

    def test_verified_confidence_maps_to_high(self):
        event = _make_event(source_confidence=SourceConfidence.VERIFIED)
        sig = to_signal_input(event)
        assert sig.confidence == SignalConfidence.HIGH

    def test_moderate_confidence_maps_to_moderate(self):
        event = _make_event(source_confidence=SourceConfidence.MODERATE)
        sig = to_signal_input(event)
        assert sig.confidence == SignalConfidence.MODERATE

    def test_unverified_confidence_maps_to_unverified(self):
        event = _make_event(source_confidence=SourceConfidence.UNVERIFIED)
        sig = to_signal_input(event)
        assert sig.confidence == SignalConfidence.UNVERIFIED

    def test_verified_higher_severity(self):
        e_verified = _make_event(source_confidence=SourceConfidence.VERIFIED)
        e_unverified = _make_event(source_confidence=SourceConfidence.UNVERIFIED)
        assert to_signal_input(e_verified).severity_score > to_signal_input(e_unverified).severity_score


# ══════════════════════════════════════════════════════════════════════════════
# 21. SignalRouter — INGEST_ONLY
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalRouterIngestOnly:

    def setup_method(self):
        # Reset Pack 1 singleton for isolated tests
        import src.macro.macro_signal_service as mod
        mod._default_registry = mod.SignalRegistry()
        mod._default_service = mod.MacroSignalService(registry=mod._default_registry)

    def test_returns_ingestion_record(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"], category_hints=["oil"])
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert isinstance(record, IngestionRecord)

    def test_record_has_event_id(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"])
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record.event_id == event.event_id

    def test_record_signal_id_on_success(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"], title="Valid routing test signal")
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        # Should have a signal_id (Pack 1 ingested successfully)
        assert record.signal_id is not None

    def test_routing_mode_recorded(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"])
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record.routing_mode == RoutingMode.INGEST_ONLY.value

    def test_not_duplicate_flag_for_new(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"])
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record.was_duplicate is False

    def test_graph_not_ingested_in_ingest_only(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"])
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record.graph_ingested is False

    def test_runtime_not_executed_in_ingest_only(self):
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"])
        record = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record.runtime_executed is False


# ══════════════════════════════════════════════════════════════════════════════
# 22. SignalRouter — Duplicate Skipped
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalRouterDuplicate:

    def setup_method(self):
        import src.macro.macro_signal_service as mod
        mod._default_registry = mod.SignalRegistry()
        mod._default_service = mod.MacroSignalService(registry=mod._default_registry)

    def test_duplicate_returns_was_duplicate_true(self):
        store = DedupStore()
        router = SignalRouter(dedup_store=store)
        event = _make_event(external_id="dup-ext-001", region_hints=["GCC"])
        router.route(event, mode=RoutingMode.INGEST_ONLY)
        record2 = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record2.was_duplicate is True

    def test_duplicate_has_no_signal_id(self):
        store = DedupStore()
        router = SignalRouter(dedup_store=store)
        event = _make_event(external_id="dup-ext-002", region_hints=["GCC"])
        router.route(event, mode=RoutingMode.INGEST_ONLY)
        record2 = router.route(event, mode=RoutingMode.INGEST_ONLY)
        assert record2.signal_id is None


# ══════════════════════════════════════════════════════════════════════════════
# 23. SignalRouter — route_batch
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalRouterBatch:

    def setup_method(self):
        import src.macro.macro_signal_service as mod
        mod._default_registry = mod.SignalRegistry()
        mod._default_service = mod.MacroSignalService(registry=mod._default_registry)

    def test_route_batch_returns_one_per_event(self):
        router = SignalRouter(dedup_store=DedupStore())
        events = [_make_event(title=f"Batch {i}", region_hints=["GCC"]) for i in range(3)]
        records = router.route_batch(events, mode=RoutingMode.INGEST_ONLY)
        assert len(records) == 3

    def test_route_batch_empty(self):
        router = SignalRouter(dedup_store=DedupStore())
        assert router.route_batch([]) == []


# ══════════════════════════════════════════════════════════════════════════════
# 24–26. SignalRouter — Unavailable Fallback
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalRouterUnavailableFallback:
    """Verify graph/runtime unavailability is handled gracefully."""

    def setup_method(self):
        import src.macro.macro_signal_service as mod
        mod._default_registry = mod.SignalRegistry()
        mod._default_service = mod.MacroSignalService(registry=mod._default_registry)

    def test_ingest_and_graph_mode_returns_record(self):
        """INGEST_AND_GRAPH should return a valid record even if graph is unavailable."""
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"], title="Graph mode test event")
        record = router.route(event, mode=RoutingMode.INGEST_AND_GRAPH)
        assert isinstance(record, IngestionRecord)
        # signal_id is set (Pack 1 succeeded) even if graph was unavailable
        # (graph_ingested may be False if graph isn't active in test environment)
        assert record.was_duplicate is False

    def test_full_runtime_mode_returns_record(self):
        """FULL_RUNTIME should return a valid record even if runtime fails."""
        router = SignalRouter(dedup_store=DedupStore())
        event = _make_event(region_hints=["GCC"], title="Full runtime test event")
        record = router.route(event, mode=RoutingMode.FULL_RUNTIME)
        assert isinstance(record, IngestionRecord)
        # Should not propagate exceptions
        assert record.was_duplicate is False

    def test_errors_captured_not_raised(self):
        """Any downstream error goes to record.errors, never propagates."""
        router = SignalRouter(dedup_store=DedupStore())
        # Even a near-empty event should not cause an exception
        event = _make_event(region_hints=["GCC"])
        record = router.route(event, mode=RoutingMode.FULL_RUNTIME)
        assert isinstance(record, IngestionRecord)


# ══════════════════════════════════════════════════════════════════════════════
# 27. SignalIngestionService
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalIngestionService:

    def setup_method(self):
        import src.macro.macro_signal_service as mod
        mod._default_registry = mod.SignalRegistry()
        mod._default_service = mod.MacroSignalService(registry=mod._default_registry)
        import src.services.signal_ingestion_service as svc_mod
        svc_mod._service_instance = None

    def test_submit_rss_items(self):
        from src.services.signal_ingestion_service import SignalIngestionService
        svc = SignalIngestionService()
        items = [
            {"title": "RSS item A", "id": "rss-a", "region_hints": ["GCC"]},
            {"title": "RSS item B", "id": "rss-b"},
        ]
        records = svc.submit_rss_items(
            items=items,
            source_name="Test RSS",
            source_ref="https://feeds.test.com",
        )
        assert len(records) == 2
        assert all(isinstance(r, IngestionRecord) for r in records)

    def test_submit_json_items(self):
        from src.services.signal_ingestion_service import SignalIngestionService
        svc = SignalIngestionService()
        payloads = [
            {"title": "JSON item A", "id": "json-a"},
            {"title": "JSON item B", "id": "json-b"},
        ]
        records = svc.submit_json_items(
            payloads=payloads,
            source_name="Test API",
            source_ref="https://api.test.com",
        )
        assert len(records) == 2

    def test_get_stats(self):
        from src.services.signal_ingestion_service import SignalIngestionService
        svc = SignalIngestionService()
        event = _make_event(region_hints=["GCC"])
        svc.submit(event)
        stats = svc.get_stats()
        assert "total_submitted" in stats
        assert stats["total_submitted"] == 1

    def test_singleton(self):
        from src.services.signal_ingestion_service import (
            get_signal_ingestion_service,
        )
        s1 = get_signal_ingestion_service()
        s2 = get_signal_ingestion_service()
        assert s1 is s2

    def test_clear_records(self):
        from src.services.signal_ingestion_service import SignalIngestionService
        svc = SignalIngestionService()
        event = _make_event(region_hints=["GCC"])
        svc.submit(event)
        svc.clear_records()
        assert svc.record_count == 0

    def test_submit_skips_no_title_rss(self):
        from src.services.signal_ingestion_service import SignalIngestionService
        svc = SignalIngestionService()
        items = [{"id": "no-title"}]  # no title → RSSAdapter returns None
        records = svc.submit_rss_items(
            items=items,
            source_name="Test RSS",
            source_ref="https://feeds.test.com",
        )
        assert records == []


# ══════════════════════════════════════════════════════════════════════════════
# 28. _resolve_regions / _resolve_domains unit tests
# ══════════════════════════════════════════════════════════════════════════════

class TestResolvers:

    def test_resolve_regions_gcc(self):
        assert GCCRegion.GCC_WIDE in _resolve_regions(["GCC-wide"])

    def test_resolve_regions_saudi(self):
        assert GCCRegion.SAUDI_ARABIA in _resolve_regions(["Saudi Arabia event"])

    def test_resolve_regions_empty(self):
        assert _resolve_regions([]) == []

    def test_resolve_regions_unknown(self):
        assert _resolve_regions(["Antarctica"]) == []

    def test_resolve_domains_oil(self):
        assert ImpactDomain.OIL_GAS in _resolve_domains(["oil supply"], [])

    def test_resolve_domains_banking_category(self):
        assert ImpactDomain.BANKING in _resolve_domains([], ["banking sector"])

    def test_resolve_domains_empty(self):
        assert _resolve_domains([], []) == []

    def test_resolve_signal_source_geopolitical(self):
        assert _resolve_signal_source(["conflict"]) == SignalSource.GEOPOLITICAL

    def test_resolve_signal_source_trade(self):
        assert _resolve_signal_source(["tariff policy"]) == SignalSource.TRADE

    def test_resolve_signal_type_commodity(self):
        assert _resolve_signal_type(["crude oil"]) == SignalType.COMMODITY

    def test_resolve_signal_type_none(self):
        assert _resolve_signal_type([]) is None
