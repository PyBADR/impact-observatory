"""Signal Intelligence Layer — Adapter Tests.

Tests for:
  1. RSSAdapter — basic parsing
  2. RSSAdapter — missing optional fields tolerated
  3. RSSAdapter — title fallback chain
  4. RSSAdapter — timestamp parsing (struct_time, ISO string)
  5. RSSAdapter — category extraction (feedparser tags format)
  6. RSSAdapter — region_hints merged from adapter + item
  7. RSSAdapter — parse_feed batch skips unparseable items
  8. RSSAdapter — raw_payload preserved
  9. JSONAdapter — basic parsing
  10. JSONAdapter — custom field mapping
  11. JSONAdapter — title fallback keys
  12. JSONAdapter — description fallback keys
  13. JSONAdapter — timestamp formats (ISO, unix epoch, string)
  14. JSONAdapter — category_hints from tags/labels/keywords
  15. JSONAdapter — dot-separated nested key path
  16. JSONAdapter — parse_batch skips unparseable items
  17. JSONAdapter — raw_payload preserved
  18. SourceEvent — dedup_key with external_id
  19. SourceEvent — dedup_key hash fallback
  20. Adapter returns None for unrecoverable items (no title)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.signals.source_models import SourceConfidence, SourceEvent, SourceType
from src.signals.rss_adapter import RSSAdapter, _parse_time_struct
from src.signals.json_adapter import FieldMapping, JSONAdapter, _parse_datetime


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _rss_adapter(**kwargs) -> RSSAdapter:
    return RSSAdapter(
        source_name=kwargs.get("source_name", "Test RSS Feed"),
        source_ref=kwargs.get("source_ref", "https://feeds.test.com/rss"),
        source_confidence=kwargs.get("source_confidence", SourceConfidence.MODERATE),
        region_hints=kwargs.get("region_hints", []),
    )


def _json_adapter(**kwargs) -> JSONAdapter:
    return JSONAdapter(
        source_name=kwargs.get("source_name", "Test JSON API"),
        source_ref=kwargs.get("source_ref", "https://api.test.com/events"),
        source_confidence=kwargs.get("source_confidence", SourceConfidence.MODERATE),
        mapping=kwargs.get("mapping", None),
        region_hints=kwargs.get("region_hints", []),
    )


def _minimal_rss_item() -> dict:
    return {
        "title": "Oil prices surge amid supply disruption",
        "id": "item-001",
        "link": "https://news.test.com/article-001",
    }


def _full_rss_item() -> dict:
    return {
        "title": "Saudi Aramco cuts output",
        "summary": "Saudi Arabia announced a 1Mb/d production cut effective next month.",
        "id": "guid-002",
        "link": "https://news.test.com/aramco-cut",
        "published_parsed": time.strptime("2024-01-15 10:30:00", "%Y-%m-%d %H:%M:%S"),
        "tags": [
            {"term": "energy", "label": "Energy"},
            {"term": "oil", "label": "Oil & Gas"},
        ],
        "region_hints": ["Saudi Arabia"],
        "sector_hints": ["oil", "energy"],
    }


def _minimal_json_payload() -> dict:
    return {
        "title": "Qatar LNG contract dispute",
        "id": "json-001",
    }


def _full_json_payload() -> dict:
    return {
        "title": "UAE banking sector stress warning",
        "description": "UAE central bank issued a stress advisory for Q1.",
        "id": "json-002",
        "url": "https://api.test.com/events/json-002",
        "published_at": "2024-02-20T08:00:00Z",
        "regions": ["UAE", "GCC"],
        "countries": ["United Arab Emirates"],
        "sectors": ["banking", "finance"],
        "categories": ["regulatory", "economic"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. RSSAdapter — Basic Parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterBasic:

    def test_returns_source_event(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_minimal_rss_item())
        assert isinstance(event, SourceEvent)

    def test_source_type_is_rss(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_minimal_rss_item())
        assert event.source_type == SourceType.RSS

    def test_source_name_preserved(self):
        adapter = _rss_adapter(source_name="Reuters GCC")
        event = adapter.parse_item(_minimal_rss_item())
        assert event.source_name == "Reuters GCC"

    def test_source_ref_preserved(self):
        adapter = _rss_adapter(source_ref="https://feeds.reuters.com/gcc")
        event = adapter.parse_item(_minimal_rss_item())
        assert event.source_ref == "https://feeds.reuters.com/gcc"

    def test_title_extracted(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_minimal_rss_item())
        assert event.title == "Oil prices surge amid supply disruption"

    def test_external_id_from_guid(self):
        adapter = _rss_adapter()
        item = {"title": "Test", "id": "guid-abc"}
        event = adapter.parse_item(item)
        assert event.external_id == "guid-abc"

    def test_url_from_link(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_minimal_rss_item())
        assert event.url == "https://news.test.com/article-001"

    def test_description_from_summary(self):
        adapter = _rss_adapter()
        item = {**_minimal_rss_item(), "summary": "Detailed summary here."}
        event = adapter.parse_item(item)
        assert event.description == "Detailed summary here."

    def test_source_confidence_preserved(self):
        adapter = _rss_adapter(source_confidence=SourceConfidence.HIGH)
        event = adapter.parse_item(_minimal_rss_item())
        assert event.source_confidence == SourceConfidence.HIGH

    def test_event_id_is_uuid(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_minimal_rss_item())
        assert isinstance(event.event_id, UUID)

    def test_detected_at_is_set(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_minimal_rss_item())
        assert event.detected_at is not None
        assert event.detected_at.tzinfo is not None


# ══════════════════════════════════════════════════════════════════════════════
# 2. RSSAdapter — Optional Fields Tolerated
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterOptionalFields:

    def test_no_id_returns_event(self):
        adapter = _rss_adapter()
        item = {"title": "Minimal item"}
        event = adapter.parse_item(item)
        assert event is not None
        assert event.external_id is None

    def test_no_link_url_is_none(self):
        adapter = _rss_adapter()
        item = {"title": "No link item"}
        event = adapter.parse_item(item)
        assert event.url is None

    def test_no_published_published_at_is_none(self):
        adapter = _rss_adapter()
        item = {"title": "No date"}
        event = adapter.parse_item(item)
        assert event.published_at is None

    def test_no_summary_description_is_none(self):
        adapter = _rss_adapter()
        item = {"title": "No description"}
        event = adapter.parse_item(item)
        assert event.description is None

    def test_no_categories_empty_list(self):
        adapter = _rss_adapter()
        item = {"title": "No categories"}
        event = adapter.parse_item(item)
        assert event.category_hints == []

    def test_empty_tags_list(self):
        adapter = _rss_adapter()
        item = {"title": "Empty tags", "tags": []}
        event = adapter.parse_item(item)
        assert event.category_hints == []


# ══════════════════════════════════════════════════════════════════════════════
# 3. RSSAdapter — Title Fallback Chain
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterTitleFallback:

    def test_title_field_first(self):
        adapter = _rss_adapter()
        item = {"title": "Title field", "summary": "Summary field"}
        event = adapter.parse_item(item)
        assert event.title == "Title field"

    def test_summary_fallback_when_no_title(self):
        adapter = _rss_adapter()
        item = {"summary": "Summary used as title"}
        event = adapter.parse_item(item)
        assert event.title == "Summary used as title"

    def test_description_fallback_when_no_title_or_summary(self):
        adapter = _rss_adapter()
        item = {"description": "Description used as title"}
        event = adapter.parse_item(item)
        assert event.title == "Description used as title"

    def test_no_title_returns_none(self):
        adapter = _rss_adapter()
        item = {"id": "no-title"}
        result = adapter.parse_item(item)
        assert result is None

    def test_empty_title_returns_none(self):
        adapter = _rss_adapter()
        item = {"title": "   "}
        result = adapter.parse_item(item)
        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# 4. RSSAdapter — Timestamp Parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterTimestamps:

    def test_published_parsed_struct_time(self):
        adapter = _rss_adapter()
        item = {
            "title": "Timestamped",
            "published_parsed": time.strptime("2024-03-10 12:00:00", "%Y-%m-%d %H:%M:%S"),
        }
        event = adapter.parse_item(item)
        assert event.published_at is not None
        assert event.published_at.year == 2024
        assert event.published_at.month == 3
        assert event.published_at.day == 10

    def test_published_iso_string(self):
        adapter = _rss_adapter()
        item = {"title": "ISO date", "published": "2024-04-05T08:30:00Z"}
        event = adapter.parse_item(item)
        assert event.published_at is not None
        assert event.published_at.year == 2024

    def test_updated_parsed_fallback(self):
        adapter = _rss_adapter()
        item = {
            "title": "Updated",
            "updated_parsed": time.strptime("2024-05-01 00:00:00", "%Y-%m-%d %H:%M:%S"),
        }
        event = adapter.parse_item(item)
        assert event.published_at is not None

    def test_parse_time_struct_utc(self):
        ts = time.strptime("2024-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        dt = _parse_time_struct(ts)
        assert dt is not None
        assert dt.tzinfo == timezone.utc

    def test_parse_time_struct_none(self):
        assert _parse_time_struct(None) is None


# ══════════════════════════════════════════════════════════════════════════════
# 5. RSSAdapter — Category Extraction
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterCategories:

    def test_feedparser_tags_label(self):
        adapter = _rss_adapter()
        item = {
            "title": "Cats",
            "tags": [{"term": "energy", "label": "Energy"}, {"term": "oil"}],
        }
        event = adapter.parse_item(item)
        assert "Energy" in event.category_hints

    def test_feedparser_tags_term_fallback(self):
        adapter = _rss_adapter()
        item = {
            "title": "Cats",
            "tags": [{"term": "geopolitical", "label": None}],
        }
        event = adapter.parse_item(item)
        assert "geopolitical" in event.category_hints

    def test_plain_category_string(self):
        adapter = _rss_adapter()
        item = {"title": "Cat string", "category": "finance"}
        event = adapter.parse_item(item)
        assert "finance" in event.category_hints

    def test_category_list(self):
        adapter = _rss_adapter()
        item = {"title": "Cat list", "category": ["oil", "banking"]}
        event = adapter.parse_item(item)
        assert "oil" in event.category_hints
        assert "banking" in event.category_hints


# ══════════════════════════════════════════════════════════════════════════════
# 6. RSSAdapter — Region Hints Merging
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterRegionHints:

    def test_adapter_level_region_hints(self):
        adapter = _rss_adapter(region_hints=["Saudi Arabia", "GCC"])
        event = adapter.parse_item({"title": "Test"})
        assert "Saudi Arabia" in event.region_hints
        assert "GCC" in event.region_hints

    def test_item_level_region_hints_merged(self):
        adapter = _rss_adapter(region_hints=["GCC"])
        item = {"title": "Test", "region_hints": ["Qatar", "UAE"]}
        event = adapter.parse_item(item)
        assert "GCC" in event.region_hints
        assert "Qatar" in event.region_hints
        assert "UAE" in event.region_hints

    def test_no_region_hints_empty(self):
        adapter = _rss_adapter()
        event = adapter.parse_item({"title": "No hints"})
        assert event.region_hints == []

    def test_sector_hints_from_item(self):
        adapter = _rss_adapter()
        item = {"title": "Test", "sector_hints": ["oil", "banking"]}
        event = adapter.parse_item(item)
        assert "oil" in event.sector_hints

    def test_country_hints_from_item(self):
        adapter = _rss_adapter()
        item = {"title": "Test", "country_hints": ["Kuwait"]}
        event = adapter.parse_item(item)
        assert "Kuwait" in event.country_hints


# ══════════════════════════════════════════════════════════════════════════════
# 7. RSSAdapter — Batch Parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterBatch:

    def test_parse_feed_returns_list(self):
        adapter = _rss_adapter()
        items = [_minimal_rss_item(), _full_rss_item()]
        events = adapter.parse_feed(items)
        assert isinstance(events, list)
        assert len(events) == 2

    def test_parse_feed_skips_no_title(self):
        adapter = _rss_adapter()
        items = [
            {"title": "Valid item"},
            {"id": "no-title"},  # no title
            {"title": "Another valid"},
        ]
        events = adapter.parse_feed(items)
        assert len(events) == 2

    def test_parse_feed_empty_list(self):
        adapter = _rss_adapter()
        events = adapter.parse_feed([])
        assert events == []

    def test_parse_item_never_raises(self):
        adapter = _rss_adapter()
        # Completely malformed input
        result = adapter.parse_item({"garbage": object()})
        # Either returns None or a SourceEvent — never raises
        assert result is None or isinstance(result, SourceEvent)


# ══════════════════════════════════════════════════════════════════════════════
# 8. RSSAdapter — Raw Payload Preserved
# ══════════════════════════════════════════════════════════════════════════════

class TestRSSAdapterRawPayload:

    def test_raw_payload_is_dict(self):
        adapter = _rss_adapter()
        event = adapter.parse_item(_full_rss_item())
        assert isinstance(event.raw_payload, dict)

    def test_raw_payload_contains_original_fields(self):
        adapter = _rss_adapter()
        item = {"title": "Test", "id": "abc", "custom_field": "custom_value"}
        event = adapter.parse_item(item)
        assert event.raw_payload.get("custom_field") == "custom_value"


# ══════════════════════════════════════════════════════════════════════════════
# 9. JSONAdapter — Basic Parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterBasic:

    def test_returns_source_event(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_minimal_json_payload())
        assert isinstance(event, SourceEvent)

    def test_source_type_is_json_api(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_minimal_json_payload())
        assert event.source_type == SourceType.JSON_API

    def test_title_extracted(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_minimal_json_payload())
        assert event.title == "Qatar LNG contract dispute"

    def test_external_id_extracted(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_minimal_json_payload())
        assert event.external_id == "json-001"

    def test_full_payload_parsed(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_full_json_payload())
        assert event.title == "UAE banking sector stress warning"
        assert event.description is not None
        assert "UAE" in event.region_hints
        assert "banking" in event.sector_hints
        assert "regulatory" in event.category_hints

    def test_source_confidence_preserved(self):
        adapter = _json_adapter(source_confidence=SourceConfidence.HIGH)
        event = adapter.parse_item(_minimal_json_payload())
        assert event.source_confidence == SourceConfidence.HIGH

    def test_url_extracted(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_full_json_payload())
        assert "json-002" in event.url


# ══════════════════════════════════════════════════════════════════════════════
# 10. JSONAdapter — Custom Field Mapping
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterCustomMapping:

    def test_custom_title_field(self):
        mapping = FieldMapping(title="headline")
        adapter = _json_adapter(mapping=mapping)
        payload = {"headline": "Custom headline field", "id": "x"}
        event = adapter.parse_item(payload)
        assert event.title == "Custom headline field"

    def test_custom_description_field(self):
        mapping = FieldMapping(description="body")
        adapter = _json_adapter(mapping=mapping)
        payload = {"title": "Test", "body": "Custom body text"}
        event = adapter.parse_item(payload)
        assert event.description == "Custom body text"

    def test_custom_external_id_field(self):
        mapping = FieldMapping(external_id="event_id")
        adapter = _json_adapter(mapping=mapping)
        payload = {"title": "Test", "event_id": "custom-ext-id"}
        event = adapter.parse_item(payload)
        assert event.external_id == "custom-ext-id"

    def test_custom_published_at_field(self):
        mapping = FieldMapping(published_at="timestamp")
        adapter = _json_adapter(mapping=mapping)
        payload = {"title": "Test", "timestamp": "2024-06-01T12:00:00Z"}
        event = adapter.parse_item(payload)
        assert event.published_at is not None
        assert event.published_at.year == 2024

    def test_custom_regions_field(self):
        mapping = FieldMapping(region_hints="geo")
        adapter = _json_adapter(mapping=mapping)
        payload = {"title": "Test", "geo": ["Saudi Arabia"]}
        event = adapter.parse_item(payload)
        assert "Saudi Arabia" in event.region_hints

    def test_custom_categories_field(self):
        mapping = FieldMapping(category_hints="tags")
        adapter = _json_adapter(mapping=mapping)
        payload = {"title": "Test", "tags": ["oil", "energy"]}
        event = adapter.parse_item(payload)
        assert "oil" in event.category_hints


# ══════════════════════════════════════════════════════════════════════════════
# 11. JSONAdapter — Title Fallback Keys
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterTitleFallback:

    def test_headline_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"headline": "Headline text"})
        assert event.title == "Headline text"

    def test_name_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"name": "Name as title"})
        assert event.title == "Name as title"

    def test_subject_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"subject": "Subject line"})
        assert event.title == "Subject line"

    def test_no_title_returns_none(self):
        adapter = _json_adapter()
        result = adapter.parse_item({"id": "no-title"})
        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# 12. JSONAdapter — Description Fallback Keys
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterDescriptionFallback:

    def test_body_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "Test", "body": "Body text"})
        assert event.description == "Body text"

    def test_content_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "Test", "content": "Content text"})
        assert event.description == "Content text"

    def test_summary_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "Test", "summary": "Summary text"})
        assert event.description == "Summary text"


# ══════════════════════════════════════════════════════════════════════════════
# 13. JSONAdapter — Timestamp Formats
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterTimestamps:

    def test_iso_z_format(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "published_at": "2024-01-15T08:00:00Z"})
        assert event.published_at.year == 2024

    def test_iso_with_offset(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "published_at": "2024-03-10T12:00:00+03:00"})
        assert event.published_at is not None

    def test_unix_epoch_int(self):
        adapter = _json_adapter()
        ts = int(datetime(2024, 6, 1, tzinfo=timezone.utc).timestamp())
        event = adapter.parse_item({"title": "T", "published_at": ts})
        assert event.published_at.year == 2024

    def test_unix_epoch_float(self):
        adapter = _json_adapter()
        ts = datetime(2024, 7, 1, tzinfo=timezone.utc).timestamp()
        event = adapter.parse_item({"title": "T", "published_at": ts})
        assert event.published_at.year == 2024

    def test_date_only_string(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "published_at": "2024-08-01"})
        assert event.published_at is not None

    def test_timestamp_fallback_key(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "timestamp": "2024-09-15T10:00:00Z"})
        assert event.published_at is not None

    def test_created_at_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "created_at": "2024-10-01T00:00:00Z"})
        assert event.published_at is not None

    def test_invalid_timestamp_none(self):
        dt = _parse_datetime("not-a-date")
        assert dt is None

    def test_none_timestamp_none(self):
        dt = _parse_datetime(None)
        assert dt is None


# ══════════════════════════════════════════════════════════════════════════════
# 14. JSONAdapter — Category Hints from Multiple Keys
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterCategoryHints:

    def test_categories_field(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "categories": ["oil", "energy"]})
        assert "oil" in event.category_hints

    def test_tags_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "tags": ["banking"]})
        assert "banking" in event.category_hints

    def test_labels_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "labels": ["geopolitical"]})
        assert "geopolitical" in event.category_hints

    def test_keywords_fallback(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "keywords": ["sanctions"]})
        assert "sanctions" in event.category_hints

    def test_string_category_to_list(self):
        adapter = _json_adapter()
        event = adapter.parse_item({"title": "T", "categories": "finance"})
        assert "finance" in event.category_hints


# ══════════════════════════════════════════════════════════════════════════════
# 15. JSONAdapter — Nested Key Path
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterNestedPath:

    def test_dot_separated_path(self):
        mapping = FieldMapping(title="event.details.headline")
        adapter = _json_adapter(mapping=mapping)
        payload = {"event": {"details": {"headline": "Nested title"}}}
        event = adapter.parse_item(payload)
        assert event.title == "Nested title"

    def test_missing_nested_path_returns_none_not_raise(self):
        mapping = FieldMapping(title="missing.path.here")
        adapter = _json_adapter(mapping=mapping)
        # Falls back to generic key search
        result = adapter.parse_item({"headline": "Fallback headline"})
        assert result is not None
        assert result.title == "Fallback headline"


# ══════════════════════════════════════════════════════════════════════════════
# 16. JSONAdapter — Batch Parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterBatch:

    def test_parse_batch_returns_list(self):
        adapter = _json_adapter()
        events = adapter.parse_batch([_minimal_json_payload(), _full_json_payload()])
        assert len(events) == 2

    def test_parse_batch_skips_no_title(self):
        adapter = _json_adapter()
        payloads = [
            {"title": "Valid"},
            {"id": "no-title-item"},
            {"title": "Also valid"},
        ]
        events = adapter.parse_batch(payloads)
        assert len(events) == 2

    def test_parse_batch_empty(self):
        adapter = _json_adapter()
        assert adapter.parse_batch([]) == []

    def test_parse_item_never_raises(self):
        adapter = _json_adapter()
        result = adapter.parse_item({"bad_key": object()})
        assert result is None or isinstance(result, SourceEvent)


# ══════════════════════════════════════════════════════════════════════════════
# 17. JSONAdapter — Raw Payload Preserved
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONAdapterRawPayload:

    def test_raw_payload_is_dict(self):
        adapter = _json_adapter()
        event = adapter.parse_item(_full_json_payload())
        assert isinstance(event.raw_payload, dict)

    def test_raw_payload_contains_original_fields(self):
        adapter = _json_adapter()
        payload = {"title": "Test", "custom": "value_123"}
        event = adapter.parse_item(payload)
        assert event.raw_payload.get("custom") == "value_123"


# ══════════════════════════════════════════════════════════════════════════════
# 18. SourceEvent — Dedup Key with External ID
# ══════════════════════════════════════════════════════════════════════════════

class TestSourceEventDedupKey:

    def test_external_id_prefix(self):
        event = SourceEvent(
            source_type=SourceType.RSS,
            source_name="Test",
            source_ref="https://feeds.test.com",
            external_id="abc-123",
            title="Test event",
        )
        assert event.dedup_key == "ext:abc-123"

    def test_hash_fallback_without_external_id(self):
        event = SourceEvent(
            source_type=SourceType.RSS,
            source_name="Test",
            source_ref="https://feeds.test.com",
            title="Test event without external id",
        )
        assert event.dedup_key.startswith("hash:")
        assert len(event.dedup_key) > 10

    def test_same_content_same_dedup_key(self):
        kwargs = dict(
            source_type=SourceType.RSS,
            source_name="Test Feed",
            source_ref="https://feeds.test.com",
            title="Identical content",
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        e1 = SourceEvent(**kwargs)
        e2 = SourceEvent(**kwargs)
        assert e1.dedup_key == e2.dedup_key

    def test_different_title_different_dedup_key(self):
        base = dict(
            source_type=SourceType.RSS,
            source_name="Test",
            source_ref="https://feeds.test.com",
        )
        e1 = SourceEvent(**base, title="Title A")
        e2 = SourceEvent(**base, title="Title B")
        assert e1.dedup_key != e2.dedup_key

    def test_dedup_key_not_empty(self):
        event = SourceEvent(
            source_type=SourceType.JSON_API,
            source_name="API",
            source_ref="https://api.test.com",
            title="Any title",
        )
        assert event.dedup_key != ""
