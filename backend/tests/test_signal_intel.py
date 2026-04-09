"""Signal Intelligence Layer — Comprehensive Test Suite.

Tests the full ingestion pipeline:
  Feed Adapters → Dedup → Mapper → Buffer → Router → Pack 1

Coverage:
  1. RSS adapter: parse RSS 2.0, Atom, invalid XML
  2. JSON API adapter: field mapping, auto-detect, nested fields
  3. Economic adapter: severity thresholds, direction detection
  4. Dedup engine: exact match, TTL expiry, capacity overflow
  5. Mapper: region resolution, domain resolution, confidence mapping
  6. Signal buffer: add, drain, overflow eviction, idempotency
  7. Router: Pack 1 acceptance, rejection, graph fallback
  8. Orchestrator: full pipeline end-to-end
  9. Contract validation: output matches MacroSignalInput schema

All tests are deterministic. No network calls.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.signal_intel.types import (
    FeedConfig,
    FeedResult,
    FeedType,
    IngestionStatus,
    RawFeedItem,
)
from src.signal_intel.dedup import DedupEngine
from src.signal_intel.mapper import (
    _resolve_regions,
    _resolve_domains,
    map_feed_item,
)
from src.signal_intel.signal_buffer import SignalBuffer
from src.signal_intel.router import SignalRouter, RouteResult
from src.signal_intel.adapters.rss_adapter import RSSFeedAdapter
from src.signal_intel.adapters.json_api_adapter import JSONAPIAdapter
from src.signal_intel.adapters.economic_adapter import EconomicAdapter

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSource,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def rss_config():
    return FeedConfig(
        feed_id="test-rss",
        feed_type=FeedType.RSS,
        name="Test RSS Feed",
        url="https://example.com/feed.xml",
        source_quality=0.7,
        default_confidence="moderate",
        default_regions=["GCC"],
        default_domains=["oil_gas"],
        tags=["test"],
    )


@pytest.fixture
def json_config():
    return FeedConfig(
        feed_id="test-json",
        feed_type=FeedType.JSON_API,
        name="Test JSON API",
        url="https://api.example.com/news",
        source_quality=0.8,
        default_confidence="high",
        default_regions=["SA"],
        default_domains=["banking"],
    )


@pytest.fixture
def economic_config():
    return FeedConfig(
        feed_id="test-economic",
        feed_type=FeedType.ECONOMIC,
        name="Test Economic Feed",
        url="https://api.example.com/indicators",
        source_quality=0.9,
        default_confidence="high",
        default_regions=["GCC"],
        default_domains=["oil_gas"],
    )


@pytest.fixture
def sample_rss_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Oil prices surge amid GCC tensions</title>
      <link>https://example.com/article/1</link>
      <description>Brent crude rose 8% following regional events.</description>
      <pubDate>Mon, 07 Apr 2026 14:30:00 GMT</pubDate>
      <guid>article-001</guid>
      <category>Energy</category>
      <category>GCC</category>
    </item>
    <item>
      <title>UAE banking sector reports record growth</title>
      <link>https://example.com/article/2</link>
      <description>Major UAE banks exceed profit expectations.</description>
      <pubDate>Mon, 07 Apr 2026 10:00:00 GMT</pubDate>
      <guid>article-002</guid>
      <category>Banking</category>
    </item>
    <item>
      <title>Hi</title>
      <link>https://example.com/article/3</link>
    </item>
  </channel>
</rss>"""


@pytest.fixture
def sample_atom_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <entry>
    <title>Qatar LNG exports hit new highs</title>
    <link href="https://example.com/entry/1"/>
    <id>entry-001</id>
    <summary>Qatar increases LNG shipments to Asia.</summary>
    <updated>2026-04-07T12:00:00Z</updated>
  </entry>
</feed>"""


@pytest.fixture
def sample_json_api_response():
    return {
        "articles": [
            {
                "id": "news-001",
                "title": "Saudi Aramco announces production changes",
                "description": "Major policy shift in oil output strategy",
                "url": "https://example.com/news/001",
                "published_at": "2026-04-07T15:00:00Z",
                "severity": 0.7,
                "region": "SA",
                "category": "oil_gas",
            },
            {
                "id": "news-002",
                "title": "Bahrain sovereign bond yields spike",
                "description": "Yields rise amid fiscal concerns",
                "url": "https://example.com/news/002",
                "published_at": "2026-04-07T14:00:00Z",
                "region": "BH",
                "category": "sovereign_fiscal",
            },
        ]
    }


@pytest.fixture
def sample_economic_response():
    return {
        "data": [
            {
                "indicator": "oil_price",
                "value": 85.4,
                "change_pct": -5.2,
                "date": "2026-04-07",
                "description": "Brent crude fell 5.2% on oversupply concerns",
            },
            {
                "indicator": "interest_rate",
                "value": 5.25,
                "change_pct": 0.25,
                "date": "2026-04-07",
                "description": "Saudi central bank raised rates by 25bp",
            },
            {
                "indicator": "cpi",
                "value": 3.8,
                "change_pct": 3.8,
                "date": "2026-04-07",
                "description": "UAE CPI rose to 3.8% year-over-year",
            },
        ]
    }


def _make_feed_item(
    feed_id: str = "test-feed",
    title: str = "Test signal about GCC oil markets",
    description: str = "Some description",
    severity_hint: float = 0.5,
    region_hints: list[str] | None = None,
    domain_hints: list[str] | None = None,
    direction_hint: str = "negative",
) -> RawFeedItem:
    item = RawFeedItem(
        feed_id=feed_id,
        feed_type=FeedType.RSS,
        title=title,
        description=description,
        severity_hint=severity_hint,
        region_hints=region_hints or ["GCC"],
        domain_hints=domain_hints or ["oil_gas"],
        direction_hint=direction_hint,
    )
    item.compute_content_hash()
    return item


# ═══════════════════════════════════════════════════════════════════════════
# 1. RSS ADAPTER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestRSSAdapter:

    def test_parse_rss_items(self, rss_config, sample_rss_xml):
        adapter = RSSFeedAdapter(rss_config)
        items = adapter.parse_items(sample_rss_xml)
        # 3 items in XML but the third has a short title "Hi" — still parsed
        assert len(items) == 3

    def test_rss_item_fields(self, rss_config, sample_rss_xml):
        adapter = RSSFeedAdapter(rss_config)
        items = adapter.parse_items(sample_rss_xml)
        first = items[0]
        assert first.title == "Oil prices surge amid GCC tensions"
        assert first.feed_id == "test-rss"
        assert first.feed_type == FeedType.RSS
        assert first.url == "https://example.com/article/1"
        assert first.source_quality == 0.7
        assert first.confidence == "moderate"
        assert "GCC" in first.region_hints

    def test_rss_pubdate_parsing(self, rss_config, sample_rss_xml):
        adapter = RSSFeedAdapter(rss_config)
        items = adapter.parse_items(sample_rss_xml)
        first = items[0]
        assert first.published_at is not None
        assert first.published_at.year == 2026

    def test_parse_atom_items(self, rss_config, sample_atom_xml):
        adapter = RSSFeedAdapter(rss_config)
        items = adapter.parse_items(sample_atom_xml)
        assert len(items) == 1
        assert items[0].title == "Qatar LNG exports hit new highs"

    def test_parse_empty_xml(self, rss_config):
        adapter = RSSFeedAdapter(rss_config)
        assert adapter.parse_items("") == []
        assert adapter.parse_items("not xml at all") == []
        assert adapter.parse_items(None) == []

    def test_content_hash_computed(self, rss_config, sample_rss_xml):
        adapter = RSSFeedAdapter(rss_config)
        items = adapter.parse_items(sample_rss_xml)
        for item in items:
            item.compute_content_hash()
            assert item.content_hash != ""
            assert len(item.content_hash) == 64  # SHA-256 hex

    def test_content_hash_deterministic(self, rss_config, sample_rss_xml):
        adapter = RSSFeedAdapter(rss_config)
        items1 = adapter.parse_items(sample_rss_xml)
        items2 = adapter.parse_items(sample_rss_xml)
        for i1, i2 in zip(items1, items2):
            i1.compute_content_hash()
            i2.compute_content_hash()
            assert i1.content_hash == i2.content_hash


# ═══════════════════════════════════════════════════════════════════════════
# 2. JSON API ADAPTER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestJSONAPIAdapter:

    def test_parse_json_items(self, json_config, sample_json_api_response):
        adapter = JSONAPIAdapter(json_config)
        items = adapter.parse_items(sample_json_api_response)
        assert len(items) == 2

    def test_json_field_mapping(self, json_config, sample_json_api_response):
        adapter = JSONAPIAdapter(json_config)
        items = adapter.parse_items(sample_json_api_response)
        first = items[0]
        assert first.title == "Saudi Aramco announces production changes"
        assert first.severity_hint == 0.7
        assert "SA" in first.region_hints

    def test_json_auto_detect_key(self, json_config):
        adapter = JSONAPIAdapter(json_config)
        # Test with "data" key
        items = adapter.parse_items({"data": [{"title": "Test event data", "id": "1"}]})
        assert len(items) == 1
        # Test with "results" key
        items = adapter.parse_items({"results": [{"title": "Test event results", "id": "2"}]})
        assert len(items) == 1

    def test_json_direct_array(self, json_config):
        adapter = JSONAPIAdapter(json_config)
        items = adapter.parse_items([{"title": "Direct array item", "id": "3"}])
        assert len(items) == 1

    def test_json_explicit_items_key(self, json_config):
        adapter = JSONAPIAdapter(json_config, items_key="records")
        data = {"records": [{"title": "Custom key item", "id": "4"}]}
        items = adapter.parse_items(data)
        assert len(items) == 1

    def test_json_skip_no_title(self, json_config):
        adapter = JSONAPIAdapter(json_config)
        items = adapter.parse_items({"articles": [{"description": "No title here"}]})
        assert len(items) == 0

    def test_json_null_input(self, json_config):
        adapter = JSONAPIAdapter(json_config)
        assert adapter.parse_items(None) == []
        assert adapter.parse_items({}) == []


# ═══════════════════════════════════════════════════════════════════════════
# 3. ECONOMIC ADAPTER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestEconomicAdapter:

    def test_parse_economic_items(self, economic_config, sample_economic_response):
        adapter = EconomicAdapter(economic_config)
        items = adapter.parse_items(sample_economic_response)
        assert len(items) == 3

    def test_oil_severity_scoring(self, economic_config, sample_economic_response):
        adapter = EconomicAdapter(economic_config)
        items = adapter.parse_items(sample_economic_response)
        oil_item = items[0]  # 5.2% change
        assert oil_item.severity_hint is not None
        assert oil_item.severity_hint >= 0.50  # ≥5% → elevated

    def test_rate_severity_scoring(self, economic_config, sample_economic_response):
        adapter = EconomicAdapter(economic_config)
        items = adapter.parse_items(sample_economic_response)
        rate_item = items[1]  # 0.25% change
        assert rate_item.severity_hint is not None
        assert rate_item.severity_hint >= 0.35  # ≥25bp → guarded

    def test_direction_detection(self, economic_config, sample_economic_response):
        adapter = EconomicAdapter(economic_config)
        items = adapter.parse_items(sample_economic_response)
        oil_item = items[0]  # -5.2%
        assert oil_item.direction_hint == "negative"

    def test_domain_hints_from_indicator(self, economic_config, sample_economic_response):
        adapter = EconomicAdapter(economic_config)
        items = adapter.parse_items(sample_economic_response)
        oil_item = items[0]
        # oil_price → oil_gas, energy_grid, sovereign_fiscal
        assert "oil_gas" in oil_item.domain_hints
        assert "energy_grid" in oil_item.domain_hints

    def test_signal_type_hint(self, economic_config, sample_economic_response):
        adapter = EconomicAdapter(economic_config)
        items = adapter.parse_items(sample_economic_response)
        assert items[0].signal_type_hint == "commodity"  # oil_price
        assert items[1].signal_type_hint == "policy"     # interest_rate
        assert items[2].signal_type_hint == "market"     # cpi


# ═══════════════════════════════════════════════════════════════════════════
# 4. DEDUP ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestDedupEngine:

    def test_new_item_not_duplicate(self):
        dedup = DedupEngine()
        item = _make_feed_item()
        assert dedup.is_duplicate(item) is False

    def test_seen_item_is_duplicate(self):
        dedup = DedupEngine()
        item = _make_feed_item()
        dedup.mark_seen(item)
        assert dedup.is_duplicate(item) is True

    def test_different_items_not_duplicate(self):
        dedup = DedupEngine()
        item1 = _make_feed_item(title="First signal about oil markets")
        item2 = _make_feed_item(title="Second signal about banking")
        dedup.mark_seen(item1)
        assert dedup.is_duplicate(item2) is False

    def test_ttl_expiry(self):
        dedup = DedupEngine(ttl_seconds=1)
        item = _make_feed_item()
        dedup.mark_seen(item)
        assert dedup.is_duplicate(item) is True
        # Manually expire
        for entry in dedup._cache.values():
            dedup._cache[entry.content_hash] = entry._replace(
                timestamp=time.time() - 2
            )
        assert dedup.is_duplicate(item) is False

    def test_capacity_overflow(self):
        dedup = DedupEngine(max_entries=3)
        for i in range(5):
            item = _make_feed_item(title=f"Signal number {i} about markets")
            dedup.mark_seen(item)
        assert dedup.size == 3  # capped at max

    def test_stats_tracking(self):
        dedup = DedupEngine()
        item = _make_feed_item()
        dedup.is_duplicate(item)
        dedup.mark_seen(item)
        dedup.is_duplicate(item)
        stats = dedup.stats
        assert stats["checked"] == 2
        assert stats["duplicates"] == 1

    def test_evict_expired(self):
        dedup = DedupEngine(ttl_seconds=0)
        item = _make_feed_item()
        dedup.mark_seen(item)
        time.sleep(0.01)
        evicted = dedup.evict_expired()
        assert evicted == 1
        assert dedup.size == 0


# ═══════════════════════════════════════════════════════════════════════════
# 5. MAPPER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMapper:

    def test_basic_mapping(self):
        item = _make_feed_item()
        result = map_feed_item(item)
        assert result is not None
        assert result.title == "Test signal about GCC oil markets"
        # Severity is now enriched (multi-factor scoring) rather than pass-through
        assert 0.0 <= result.severity_score <= 1.0
        assert result.direction == SignalDirection.NEGATIVE

    def test_region_resolution_iso(self):
        regions = _resolve_regions(["SA", "AE"])
        assert GCCRegion.SAUDI_ARABIA in regions
        assert GCCRegion.UAE in regions

    def test_region_resolution_names(self):
        regions = _resolve_regions(["Saudi Arabia", "Qatar", "Dubai"])
        assert GCCRegion.SAUDI_ARABIA in regions
        assert GCCRegion.QATAR in regions
        assert GCCRegion.UAE in regions  # Dubai → UAE

    def test_region_resolution_arabic(self):
        regions = _resolve_regions(["السعودية", "قطر"])
        assert GCCRegion.SAUDI_ARABIA in regions
        assert GCCRegion.QATAR in regions

    def test_region_fallback_gcc_wide(self):
        regions = _resolve_regions(["unknown_place"])
        assert GCCRegion.GCC_WIDE in regions

    def test_domain_resolution(self):
        domains = _resolve_domains(["oil", "banking", "cyber"])
        assert ImpactDomain.OIL_GAS in domains
        assert ImpactDomain.BANKING in domains
        assert ImpactDomain.CYBER_INFRASTRUCTURE in domains

    def test_short_title_rejected(self):
        item = _make_feed_item(title="Hi")
        result = map_feed_item(item)
        assert result is None

    def test_source_mapping_by_feed_type(self):
        # RSS items now get content-aware source classification via enrichment.
        # "Test signal about GCC oil markets" contains "market" keyword →
        # signal_type "market" → source overridden to MARKET.
        rss_item = _make_feed_item()
        rss_item.feed_type = FeedType.RSS
        result = map_feed_item(rss_item)
        assert result.source in (SignalSource.GEOPOLITICAL, SignalSource.MARKET)

        econ_item = _make_feed_item()
        econ_item.feed_type = FeedType.ECONOMIC
        result = map_feed_item(econ_item)
        assert result.source == SignalSource.ECONOMIC

    def test_confidence_mapping(self):
        item = _make_feed_item()
        item.confidence = "verified"
        result = map_feed_item(item)
        assert result.confidence == SignalConfidence.VERIFIED

        item.confidence = "low"
        result = map_feed_item(item)
        assert result.confidence == SignalConfidence.LOW

    def test_external_id_format(self):
        item = _make_feed_item(feed_id="my-feed")
        result = map_feed_item(item)
        assert result.external_id.startswith("signal_intel:my-feed:")

    def test_mapped_output_is_valid_macro_signal_input(self):
        """Contract test: verify output conforms to MacroSignalInput schema."""
        from src.macro.macro_schemas import MacroSignalInput
        item = _make_feed_item(
            title="Oil price shock affects Saudi economy",
            region_hints=["SA", "GCC"],
            domain_hints=["oil_gas", "banking"],
        )
        result = map_feed_item(item)
        assert result is not None
        # Re-validate through Pydantic
        validated = MacroSignalInput.model_validate(result.model_dump())
        assert validated.title == result.title
        assert validated.severity_score == result.severity_score


# ═══════════════════════════════════════════════════════════════════════════
# 6. SIGNAL BUFFER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSignalBuffer:

    def test_add_and_drain(self):
        buf = SignalBuffer()
        buf.add({"title": "test"}, "hash1", "feed1", "item1")
        assert buf.size == 1
        drained = buf.drain()
        assert len(drained) == 1
        assert buf.size == 0

    def test_idempotent_add(self):
        buf = SignalBuffer()
        buf.add({"title": "test"}, "hash1", "feed1", "item1")
        buf.add({"title": "test"}, "hash1", "feed1", "item1")
        assert buf.size == 1

    def test_overflow_eviction(self):
        buf = SignalBuffer(max_capacity=3)
        for i in range(5):
            buf.add({"title": f"test{i}"}, f"hash{i}", "feed1", f"item{i}")
        assert buf.size == 3
        assert buf.stats["evicted"] == 2

    def test_partial_drain(self):
        buf = SignalBuffer()
        for i in range(5):
            buf.add({"title": f"test{i}"}, f"hash{i}", "feed1", f"item{i}")
        drained = buf.drain(2)
        assert len(drained) == 2
        assert buf.size == 3

    def test_peek_does_not_remove(self):
        buf = SignalBuffer()
        buf.add({"title": "test"}, "hash1", "feed1", "item1")
        peeked = buf.peek()
        assert len(peeked) == 1
        assert buf.size == 1

    def test_route_failure_tracking(self):
        buf = SignalBuffer()
        buf.add({"title": "test"}, "hash1", "feed1", "item1")
        buf.mark_route_failure("hash1", "timeout")
        entry = buf._buffer["hash1"]
        assert entry.route_attempts == 1
        assert entry.last_route_error == "timeout"


# ═══════════════════════════════════════════════════════════════════════════
# 7. ROUTER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestRouter:

    def test_route_without_service(self):
        router = SignalRouter(signal_service=None)
        item = _make_feed_item()
        mapped = map_feed_item(item)
        result = router.route(mapped, "feed1", "item1", "hash1")
        assert not result.success
        assert "not configured" in result.errors[0]

    def test_route_with_mock_service(self):
        """Test routing with a mock Pack 1 service."""
        from unittest.mock import MagicMock
        from src.macro.macro_schemas import SignalRegistryEntry, NormalizedSignal

        mock_service = MagicMock()
        # Simulate successful intake
        mock_entry = MagicMock()
        mock_entry.signal.signal_id = uuid4()
        mock_entry.registry_id = uuid4()
        mock_service.ingest_signal.return_value = (mock_entry, None, [])

        router = SignalRouter(signal_service=mock_service, auto_graph_ingest=False)
        item = _make_feed_item()
        mapped = map_feed_item(item)
        result = router.route(mapped, "feed1", "item1", "hash1")

        assert result.success
        assert result.pack1_accepted
        assert result.signal_id == mock_entry.signal.signal_id

    def test_route_pack1_rejection(self):
        from unittest.mock import MagicMock
        from src.macro.macro_schemas import SignalRejection

        mock_service = MagicMock()
        mock_rejection = MagicMock()
        mock_rejection.errors = ["invalid severity"]
        mock_service.ingest_signal.return_value = (None, mock_rejection, [])

        router = SignalRouter(signal_service=mock_service)
        item = _make_feed_item()
        mapped = map_feed_item(item)
        result = router.route(mapped, "feed1", "item1", "hash1")

        assert not result.success
        assert not result.pack1_accepted
        assert router.stats["pack1_rejected"] == 1

    def test_route_graph_failure_nonfatal(self):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_entry = MagicMock()
        mock_entry.signal.signal_id = uuid4()
        mock_entry.registry_id = uuid4()
        mock_service.ingest_signal.return_value = (mock_entry, None, [])

        mock_graph = MagicMock()
        mock_graph.is_available.return_value = True
        mock_graph.ensure_ingested.side_effect = RuntimeError("graph down")

        router = SignalRouter(
            signal_service=mock_service,
            graph_adapter=mock_graph,
            auto_graph_ingest=True,
        )
        item = _make_feed_item()
        mapped = map_feed_item(item)
        result = router.route(mapped, "feed1", "item1", "hash1")

        # Pack 1 still succeeded despite graph failure
        assert result.success
        assert result.pack1_accepted
        assert not result.graph_ingested
        assert any("Graph" in w for w in result.warnings)

    def test_audit_records(self):
        from unittest.mock import MagicMock

        mock_service = MagicMock()
        mock_entry = MagicMock()
        mock_entry.signal.signal_id = uuid4()
        mock_entry.registry_id = uuid4()
        mock_service.ingest_signal.return_value = (mock_entry, None, [])

        router = SignalRouter(signal_service=mock_service, auto_graph_ingest=False)
        item = _make_feed_item()
        mapped = map_feed_item(item)
        router.route(mapped, "feed1", "item1", "hash1")

        records = router.get_records()
        assert len(records) == 1
        assert records[0].status == IngestionStatus.ROUTED


# ═══════════════════════════════════════════════════════════════════════════
# 8. FEED CONFIG VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestFeedConfig:

    def test_valid_config(self):
        config = FeedConfig(
            feed_id="my-feed",
            feed_type=FeedType.RSS,
            name="My Feed",
            url="https://example.com/feed",
        )
        assert config.feed_id == "my-feed"

    def test_invalid_feed_id(self):
        with pytest.raises(Exception):
            FeedConfig(
                feed_id="INVALID ID!",  # uppercase, spaces, special chars
                feed_type=FeedType.RSS,
                name="Bad Feed",
                url="https://example.com/feed",
            )

    def test_invalid_confidence(self):
        with pytest.raises(Exception):
            FeedConfig(
                feed_id="test",
                feed_type=FeedType.RSS,
                name="Test",
                url="https://example.com/feed",
                default_confidence="invalid_level",
            )

    def test_source_quality_bounds(self):
        with pytest.raises(Exception):
            FeedConfig(
                feed_id="test",
                feed_type=FeedType.RSS,
                name="Test",
                url="https://example.com/feed",
                source_quality=1.5,  # out of bounds
            )


# ═══════════════════════════════════════════════════════════════════════════
# 9. CONTENT HASH DETERMINISM TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestContentHash:

    def test_hash_deterministic(self):
        item1 = _make_feed_item(title="Same title for both items")
        item2 = _make_feed_item(title="Same title for both items")
        assert item1.content_hash == item2.content_hash

    def test_hash_different_for_different_content(self):
        item1 = _make_feed_item(title="First unique title here")
        item2 = _make_feed_item(title="Second unique title here")
        assert item1.content_hash != item2.content_hash

    def test_hash_is_sha256(self):
        item = _make_feed_item()
        assert len(item.content_hash) == 64
        assert all(c in "0123456789abcdef" for c in item.content_hash)


# ═══════════════════════════════════════════════════════════════════════════
# 10. FEED REGISTRY / ADAPTER FACTORY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestFeedRegistry:

    def test_create_rss_adapter(self, rss_config):
        from src.signal_intel.feed_registry import create_adapter
        adapter = create_adapter(rss_config)
        assert isinstance(adapter, RSSFeedAdapter)
        assert adapter.feed_type == FeedType.RSS

    def test_create_json_adapter(self, json_config):
        from src.signal_intel.feed_registry import create_adapter
        adapter = create_adapter(json_config)
        assert isinstance(adapter, JSONAPIAdapter)

    def test_create_economic_adapter(self, economic_config):
        from src.signal_intel.feed_registry import create_adapter
        adapter = create_adapter(economic_config)
        assert isinstance(adapter, EconomicAdapter)

    def test_unsupported_feed_type(self):
        from src.signal_intel.feed_registry import create_adapter
        config = FeedConfig(
            feed_id="test",
            feed_type=FeedType.RSS,
            name="Test",
            url="https://example.com/feed",
        )
        # Force invalid type
        config.feed_type = "unsupported"  # type: ignore
        with pytest.raises(ValueError):
            create_adapter(config)

    def test_load_default_templates(self):
        from src.signal_intel.feed_registry import load_default_templates
        templates = load_default_templates()
        assert len(templates) > 0
        for tmpl in templates:
            assert isinstance(tmpl, FeedConfig)
            assert not tmpl.enabled  # all disabled by default
