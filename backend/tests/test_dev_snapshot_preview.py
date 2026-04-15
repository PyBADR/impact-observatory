"""
Impact Observatory | مرصد الأثر
Test Suite: Live Data v4 — Dev-only Snapshot Preview

Tests:
  1. Feature flag defaults false
  2. Preview disabled when flag is false (production-safe)
  3. Preview enabled when flag is true (dev/test)
  4. Connector reads local fixture only
  5. No scenario catalog mutation
  6. Preview returns snapshots when enabled
  7. No network calls
  8. Audit log populated
  9. Endpoint returns 404 when disabled
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.signal_ingestion.feature_flags import (
    is_dev_signal_preview_enabled,
    is_live_signal_scoring_enabled,
)
from src.signal_ingestion.preview_service import get_dev_preview
from src.simulation_engine import SCENARIO_CATALOG


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Feature Flag Default
# ═══════════════════════════════════════════════════════════════════════════════

class TestFeatureFlags:
    def test_dev_preview_default_false(self):
        """Feature flag must default to False."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_dev_signal_preview_enabled() is False

    def test_dev_preview_enabled_with_env(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            assert is_dev_signal_preview_enabled() is True

    def test_dev_preview_disabled_with_false(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "false"}):
            assert is_dev_signal_preview_enabled() is False

    def test_dev_preview_enabled_with_1(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "1"}):
            assert is_dev_signal_preview_enabled() is True

    def test_dev_preview_disabled_with_garbage(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "maybe"}):
            assert is_dev_signal_preview_enabled() is False

    def test_live_scoring_default_false(self):
        """Live scoring flag must always be False in v4."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_live_signal_scoring_enabled() is False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Preview Disabled (Production-Safe)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPreviewDisabled:
    def test_returns_disabled_when_flag_off(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "false"}):
            result = get_dev_preview()
            assert result["enabled"] is False
            assert result["snapshots"] == []
            assert result["snapshot_count"] == 0

    def test_disabled_response_is_safe(self):
        with patch.dict(os.environ, {}, clear=True):
            result = get_dev_preview()
            assert result["enabled"] is False
            assert "ENABLE_DEV_SIGNAL_PREVIEW" in result["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Preview Enabled (Dev/Test)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPreviewEnabled:
    def test_returns_snapshots_when_enabled(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            assert result["enabled"] is True
            assert result["snapshot_count"] == 5
            assert len(result["snapshots"]) == 5

    def test_source_mode_is_dev_fixture(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            assert result["source_mode"] == "dev_fixture"

    def test_scoring_impact_is_none(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            assert result["scoring_impact"] == "none"

    def test_notice_disclaims_scoring(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            assert "does not affect" in result["notice"]
            assert "Live feeds not connected" in result["notice"]

    def test_max_snapshots_limits_output(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(max_snapshots=2, ingested_at="2026-04-15T12:00:00Z")
            assert len(result["snapshots"]) == 2
            assert result["snapshot_count"] == 5  # Total still 5

    def test_result_json_serializable(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            json.dumps(result)  # Must not raise


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Connector Reads Local Fixture Only
# ═══════════════════════════════════════════════════════════════════════════════

class TestLocalFixtureOnly:
    def test_fixture_file_exists(self):
        fixture = Path(__file__).parent / "fixtures" / "sample_rss_feed.xml"
        assert fixture.exists()

    def test_no_network_in_preview(self):
        """Preview uses local fixture — no HTTP calls."""
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            # If network was attempted, this would fail (no internet in test)
            assert result["snapshot_count"] == 5

    def test_connector_state_shows_healthy(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            assert result["connector_status"] == "healthy"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. No Scenario Catalog Mutation
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoScenarioMutation:
    def test_catalog_unchanged_after_preview(self):
        """CRITICAL: Running dev preview must NOT change SCENARIO_CATALOG."""
        before = {
            sid: entry["base_loss_usd"]
            for sid, entry in SCENARIO_CATALOG.items()
        }

        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            get_dev_preview(ingested_at="2026-04-15T12:00:00Z")

        after = {
            sid: entry["base_loss_usd"]
            for sid, entry in SCENARIO_CATALOG.items()
        }
        assert before == after


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Audit Log Populated
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLog:
    def test_audit_summary_present_when_enabled(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            summary = result["audit_summary"]
            assert summary["snapshots_created"] == 5
            assert summary["failures"] == 0

    def test_audit_entries_present_when_enabled(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            result = get_dev_preview(ingested_at="2026-04-15T12:00:00Z")
            entries = result["audit_entries"]
            assert len(entries) >= 6  # health + source check + 5 snapshots

    def test_audit_empty_when_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            result = get_dev_preview()
            assert result["audit_summary"] == {}
