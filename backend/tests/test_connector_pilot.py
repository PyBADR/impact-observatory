"""
Impact Observatory | مرصد الأثر
Test Suite: Live Data v3 — One Connector Pilot (RSS)

Tests:
  1. Connector health check — fixture parseable
  2. RSS fixture parsing — all items extracted
  3. Normalization into SignalSnapshot — typed, serializable
  4. Freshness/confidence calculation — correct per entry age
  5. Audit log integration — all events recorded
  6. Safe failure — missing file, bad XML, disabled connector
  7. No mutation of scenario catalog
  8. No network call required — everything from static fixture
"""
import json
import pytest
from pathlib import Path

from src.signal_ingestion.connectors.base import BaseConnector, ConnectorStatus
from src.signal_ingestion.connectors.rss_connector import (
    RSSConnector,
    PILOT_RSS_SOURCE,
)
from src.signal_ingestion.models import SignalSnapshot, SnapshotFreshness
from src.signal_ingestion.audit_log import SignalAuditLog, SignalAuditAction
from src.simulation_engine import SCENARIO_CATALOG


# ── Fixture path ─────────────────────────────────────────────────────

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_rss_feed.xml"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Connector Health Check
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_healthy_with_fixture(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        status = conn.health_check()
        assert status == ConnectorStatus.HEALTHY

    def test_disabled_returns_disabled(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=False)
        status = conn.health_check()
        assert status == ConnectorStatus.DISABLED

    def test_unavailable_without_file(self):
        conn = RSSConnector(
            fixture_path=Path("/nonexistent/feed.xml"),
            enabled=True,
        )
        status = conn.health_check()
        assert status == ConnectorStatus.UNAVAILABLE

    def test_unavailable_with_bad_xml(self):
        conn = RSSConnector(xml_content="not xml at all {{{{", enabled=True)
        status = conn.health_check()
        assert status == ConnectorStatus.UNAVAILABLE

    def test_health_check_updates_state(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        assert conn.state.status == ConnectorStatus.UNCHECKED
        conn.health_check()
        assert conn.state.status == ConnectorStatus.HEALTHY
        assert conn.state.last_checked_at is not None

    def test_health_check_logs_disabled(self):
        log = SignalAuditLog()
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=False)
        conn.health_check(audit_log=log)
        fallbacks = log.entries_by_action(SignalAuditAction.FALLBACK_USED)
        assert len(fallbacks) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RSS Fixture Parsing
# ═══════════════════════════════════════════════════════════════════════════════

class TestRSSParsing:
    def test_fetch_returns_5_items(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        raw = conn.fetch()
        assert len(raw) == 5

    def test_each_item_has_title(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        raw = conn.fetch()
        for item in raw:
            assert "title" in item
            assert len(item["title"]) > 0

    def test_each_item_has_published_at(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        raw = conn.fetch()
        for item in raw:
            assert "published_at" in item
            assert "T" in item["published_at"]  # ISO-8601

    def test_categories_mapped_to_scenarios(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        raw = conn.fetch()
        # First item has energy + maritime categories
        first = raw[0]
        assert "hormuz_chokepoint_disruption" in first.get("related_scenarios", [])
        assert "energy_market_volatility_shock" in first.get("related_scenarios", [])

    def test_categories_mapped_to_countries(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        raw = conn.fetch()
        first = raw[0]
        assert "UAE" in first.get("related_countries", [])

    def test_categories_mapped_to_sectors(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        raw = conn.fetch()
        first = raw[0]
        assert "energy" in first.get("related_sectors", [])

    def test_disabled_returns_empty(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=False)
        raw = conn.fetch()
        assert raw == []

    def test_xml_string_input(self):
        xml = FIXTURE_PATH.read_text()
        conn = RSSConnector(xml_content=xml, enabled=True)
        raw = conn.fetch()
        assert len(raw) == 5


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Normalization into SignalSnapshot
# ═══════════════════════════════════════════════════════════════════════════════

class TestNormalization:
    def test_normalize_produces_snapshots(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        assert len(snaps) == 5
        for s in snaps:
            assert isinstance(s, SignalSnapshot)

    def test_snapshots_have_correct_source_id(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        for s in snaps:
            assert s.source_id == "sig_rss_pilot"

    def test_snapshots_have_valid_freshness(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        for s in snaps:
            assert isinstance(s.freshness_status, SnapshotFreshness)

    def test_snapshots_have_bounded_confidence(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        for s in snaps:
            assert 0.0 <= s.confidence_score <= 1.0

    def test_snapshots_are_frozen(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        with pytest.raises(AttributeError):
            snaps[0].confidence_score = 999  # type: ignore

    def test_snapshots_json_serializable(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        for s in snaps:
            json.dumps(s.to_dict())

    def test_normalize_disabled_returns_empty(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=False)
        snaps = conn.normalize()
        assert snaps == []


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Freshness and Confidence
# ═══════════════════════════════════════════════════════════════════════════════

class TestFreshnessConfidence:
    def test_fixture_items_are_stale_or_expired(self):
        """Fixture dates are April 7–12, ingested April 15 → stale/expired."""
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        for s in snaps:
            assert s.freshness_status in (
                SnapshotFreshness.STALE,
                SnapshotFreshness.EXPIRED,
            )

    def test_confidence_reduced_for_stale_items(self):
        """Stale/expired items should have confidence < source weight (0.75)."""
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        for s in snaps:
            assert s.confidence_score < 0.75

    def test_deterministic_confidence(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        a = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        b = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        assert [s.confidence_score for s in a] == [s.confidence_score for s in b]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Audit Log Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditIntegration:
    def test_normalize_populates_audit_log(self):
        log = SignalAuditLog()
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        conn.normalize(audit_log=log, ingested_at="2026-04-15T12:00:00Z")
        assert log.count >= 6  # 1 fetch-check + 1 source-check + 5 snapshots

    def test_audit_records_source_checked(self):
        log = SignalAuditLog()
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        conn.normalize(audit_log=log, ingested_at="2026-04-15T12:00:00Z")
        checks = log.entries_by_action(SignalAuditAction.SOURCE_CHECKED)
        assert len(checks) >= 1

    def test_audit_records_snapshots_created(self):
        log = SignalAuditLog()
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        conn.normalize(audit_log=log, ingested_at="2026-04-15T12:00:00Z")
        created = log.entries_by_action(SignalAuditAction.SNAPSHOT_CREATED)
        assert len(created) == 5

    def test_disabled_connector_logs_fallback(self):
        log = SignalAuditLog()
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=False)
        conn.normalize(audit_log=log)
        fallbacks = log.entries_by_action(SignalAuditAction.FALLBACK_USED)
        assert len(fallbacks) >= 1

    def test_audit_summary_correct(self):
        log = SignalAuditLog()
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        conn.normalize(audit_log=log, ingested_at="2026-04-15T12:00:00Z")
        summary = log.summary()
        assert summary["snapshots_created"] == 5
        assert summary["failures"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Safe Failure
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeFailure:
    def test_missing_file_returns_empty(self):
        conn = RSSConnector(
            fixture_path=Path("/nonexistent/feed.xml"),
            enabled=True,
        )
        result = conn.normalize()
        assert result == []

    def test_bad_xml_returns_empty(self):
        conn = RSSConnector(xml_content="<<<not xml>>>", enabled=True)
        result = conn.normalize()
        assert result == []

    def test_empty_channel_returns_empty(self):
        xml = '<?xml version="1.0"?><rss><channel></channel></rss>'
        conn = RSSConnector(xml_content=xml, enabled=True)
        result = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        assert result == []

    def test_failure_updates_state(self):
        conn = RSSConnector(xml_content="<<<bad>>>", enabled=True)
        conn.normalize()
        assert conn.state.status == ConnectorStatus.UNAVAILABLE
        assert conn.state.failure_reason is not None

    def test_failure_logs_to_audit(self):
        log = SignalAuditLog()
        conn = RSSConnector(xml_content="<<<bad>>>", enabled=True)
        conn.normalize(audit_log=log)
        failures = log.entries_by_action(SignalAuditAction.SOURCE_FAILED)
        assert len(failures) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# 7. No Mutation of Scenario Catalog
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoScenarioMutation:
    def test_catalog_unchanged_after_connector_run(self):
        """CRITICAL: Running the connector must NOT change SCENARIO_CATALOG."""
        before = {
            sid: entry["base_loss_usd"]
            for sid, entry in SCENARIO_CATALOG.items()
        }

        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        conn.normalize(ingested_at="2026-04-15T12:00:00Z")

        after = {
            sid: entry["base_loss_usd"]
            for sid, entry in SCENARIO_CATALOG.items()
        }
        assert before == after


# ═══════════════════════════════════════════════════════════════════════════════
# 8. No Network Call Required
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoNetworkCall:
    def test_connector_reads_local_file_only(self):
        """Connector uses fixture_path — no HTTP, no DNS, no sockets."""
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        # This would fail if any network call was attempted (no internet in test)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        assert len(snaps) == 5

    def test_connector_reads_string_only(self):
        xml = FIXTURE_PATH.read_text()
        conn = RSSConnector(xml_content=xml, enabled=True)
        snaps = conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        assert len(snaps) == 5

    def test_connector_state_serializable(self):
        conn = RSSConnector(fixture_path=FIXTURE_PATH, enabled=True)
        conn.normalize(ingested_at="2026-04-15T12:00:00Z")
        d = conn.to_dict()
        json.dumps(d)
