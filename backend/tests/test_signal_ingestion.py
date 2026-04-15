"""
Impact Observatory | مرصد الأثر
Test Suite: Signal Ingestion Layer v2 — Read-Only Signal Snapshots

Tests:
  1. SignalSource model — creation, serialization
  2. SignalSnapshot normalization — raw → typed
  3. Freshness calculation — age-based classification
  4. Confidence calculation — source weight × freshness penalty
  5. Safe fallback — disabled/missing sources return empty
  6. No mutation of scenario values — simulation engine untouched
  7. Audit log generation — all events recorded
  8. Batch ingestion — end-to-end pipeline
"""
import json
import pytest
from datetime import datetime, timezone, timedelta

from src.signal_ingestion.models import (
    SignalSource,
    SignalSourceType,
    SignalSnapshot,
    SnapshotFreshness,
    SAMPLE_SIGNAL_SOURCES,
)
from src.signal_ingestion.ingestion_service import (
    ingest_signals,
    normalize_snapshot,
    calculate_freshness,
    calculate_confidence,
    SAMPLE_RAW_SIGNALS,
)
from src.signal_ingestion.audit_log import (
    SignalAuditEntry,
    SignalAuditAction,
    SignalAuditLog,
)
from src.simulation_engine import SCENARIO_CATALOG


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SignalSource Model Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalSourceModel:
    def test_create_signal_source(self):
        src = SignalSource(
            source_id="test_src",
            name="Test Source",
            source_type=SignalSourceType.RSS,
            url="https://example.com/feed",
            refresh_frequency_minutes=60,
            confidence_weight=0.80,
            enabled=True,
            notes="Test notes",
        )
        assert src.source_id == "test_src"
        assert src.source_type == SignalSourceType.RSS
        assert src.enabled is True

    def test_signal_source_is_frozen(self):
        src = SignalSource(
            source_id="test", name="Test", source_type=SignalSourceType.API,
            url=None, refresh_frequency_minutes=30, confidence_weight=0.70,
            enabled=False,
        )
        with pytest.raises(AttributeError):
            src.enabled = True  # type: ignore

    def test_sample_sources_registry(self):
        assert len(SAMPLE_SIGNAL_SOURCES) >= 5
        for sid, src in SAMPLE_SIGNAL_SOURCES.items():
            assert isinstance(src, SignalSource)
            assert src.source_id == sid
            assert 0.0 <= src.confidence_weight <= 1.0

    def test_only_one_source_enabled(self):
        """In v2, only the static sample source should be enabled."""
        enabled = [s for s in SAMPLE_SIGNAL_SOURCES.values() if s.enabled]
        assert len(enabled) == 1
        assert enabled[0].source_id == "sig_sample_static"

    def test_source_to_dict_serializable(self):
        for src in SAMPLE_SIGNAL_SOURCES.values():
            d = src.to_dict()
            json.dumps(d)  # Must not raise

    def test_all_source_types_valid(self):
        for src in SAMPLE_SIGNAL_SOURCES.values():
            assert isinstance(src.source_type, SignalSourceType)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SignalSnapshot Normalization Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSnapshotNormalization:
    @pytest.fixture
    def sample_source(self):
        return SAMPLE_SIGNAL_SOURCES["sig_sample_static"]

    def test_normalize_produces_snapshot(self, sample_source):
        raw = SAMPLE_RAW_SIGNALS[0]
        snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert isinstance(snap, SignalSnapshot)
        assert snap.source_id == "sig_sample_static"

    def test_snapshot_has_required_fields(self, sample_source):
        raw = SAMPLE_RAW_SIGNALS[0]
        snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert len(snap.snapshot_id) > 0
        assert len(snap.title) > 0
        assert len(snap.published_at) >= 10
        assert len(snap.ingested_at) >= 10
        assert isinstance(snap.freshness_status, SnapshotFreshness)
        assert 0.0 <= snap.confidence_score <= 1.0

    def test_snapshot_preserves_related_data(self, sample_source):
        raw = SAMPLE_RAW_SIGNALS[0]
        snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert "hormuz_chokepoint_disruption" in snap.related_scenarios
        assert "UAE" in snap.related_countries
        assert "energy" in snap.related_sectors

    def test_snapshot_id_is_deterministic(self, sample_source):
        raw = SAMPLE_RAW_SIGNALS[0]
        a = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        b = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert a.snapshot_id == b.snapshot_id

    def test_snapshot_raw_metadata_excludes_known_fields(self, sample_source):
        raw = SAMPLE_RAW_SIGNALS[0]
        snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert "title" not in snap.raw_metadata
        assert "summary" not in snap.raw_metadata
        assert "source_label" in snap.raw_metadata  # Extra field preserved

    def test_snapshot_to_dict_serializable(self, sample_source):
        for raw in SAMPLE_RAW_SIGNALS:
            snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
            d = snap.to_dict()
            json.dumps(d)  # Must not raise

    def test_normalize_handles_missing_fields(self, sample_source):
        raw = {"title": "Minimal signal"}
        snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert snap.title == "Minimal signal"
        assert snap.summary == ""
        assert snap.url is None
        assert snap.related_scenarios == []

    def test_normalize_handles_empty_input(self, sample_source):
        raw: dict = {}
        snap = normalize_snapshot(raw, sample_source, ingested_at="2026-04-15T12:00:00Z")
        assert snap.title == "Untitled Signal"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Freshness Calculation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFreshnessCalculation:
    def test_fresh_within_window(self):
        pub = "2026-04-15T11:00:00Z"
        ing = "2026-04-15T11:30:00Z"  # 30 min later
        result = calculate_freshness(pub, ing, refresh_frequency_minutes=60)
        assert result == SnapshotFreshness.FRESH

    def test_recent_past_window(self):
        pub = "2026-04-15T10:00:00Z"
        ing = "2026-04-15T11:30:00Z"  # 90 min later (1.5x window)
        result = calculate_freshness(pub, ing, refresh_frequency_minutes=60)
        assert result == SnapshotFreshness.RECENT

    def test_stale_well_past_window(self):
        pub = "2026-04-15T08:00:00Z"
        ing = "2026-04-15T12:00:00Z"  # 4 hours later (4x window)
        result = calculate_freshness(pub, ing, refresh_frequency_minutes=60)
        assert result == SnapshotFreshness.STALE

    def test_expired_very_old(self):
        pub = "2026-04-10T08:00:00Z"
        ing = "2026-04-15T12:00:00Z"  # 5 days later
        result = calculate_freshness(pub, ing, refresh_frequency_minutes=60)
        assert result == SnapshotFreshness.EXPIRED

    def test_unknown_for_zero_frequency(self):
        result = calculate_freshness("2026-04-15T11:00:00Z", "2026-04-15T12:00:00Z", 0)
        assert result == SnapshotFreshness.UNKNOWN

    def test_unknown_for_bad_timestamp(self):
        result = calculate_freshness("not-a-date", "2026-04-15T12:00:00Z", 60)
        assert result == SnapshotFreshness.UNKNOWN

    def test_fresh_for_future_publish(self):
        pub = "2026-04-15T13:00:00Z"
        ing = "2026-04-15T12:00:00Z"  # published in future
        result = calculate_freshness(pub, ing, refresh_frequency_minutes=60)
        assert result == SnapshotFreshness.FRESH


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Confidence Calculation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceCalculation:
    def test_fresh_full_confidence(self):
        result = calculate_confidence(0.80, SnapshotFreshness.FRESH)
        assert result == 0.80

    def test_recent_reduced_confidence(self):
        result = calculate_confidence(0.80, SnapshotFreshness.RECENT)
        assert result == 0.68  # 0.80 * 0.85

    def test_stale_low_confidence(self):
        result = calculate_confidence(0.80, SnapshotFreshness.STALE)
        assert result == 0.48  # 0.80 * 0.60

    def test_expired_very_low_confidence(self):
        result = calculate_confidence(0.80, SnapshotFreshness.EXPIRED)
        assert result == 0.24  # 0.80 * 0.30

    def test_unknown_halved_confidence(self):
        result = calculate_confidence(0.80, SnapshotFreshness.UNKNOWN)
        assert result == 0.40  # 0.80 * 0.50

    def test_confidence_bounded_0_to_1(self):
        for fw in [0.0, 0.5, 1.0, 1.5]:
            for fresh in SnapshotFreshness:
                c = calculate_confidence(fw, fresh)
                assert 0.0 <= c <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Safe Fallback Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeFallback:
    def test_missing_source_returns_empty(self):
        result = ingest_signals([{"title": "test"}], source_id="nonexistent_source")
        assert result == []

    def test_disabled_source_returns_empty(self):
        result = ingest_signals([{"title": "test"}], source_id="sig_reuters_energy")
        assert result == []

    def test_empty_input_returns_empty(self):
        result = ingest_signals([], source_id="sig_sample_static")
        assert result == []

    def test_fallback_does_not_crash(self):
        """Even with bad data, ingestion should not raise."""
        result = ingest_signals(
            [{"title": None}, {}, {"title": 12345}],
            source_id="sig_sample_static",
        )
        assert isinstance(result, list)
        # May produce snapshots (with fallback values) or empty — but never crashes


# ═══════════════════════════════════════════════════════════════════════════════
# 6. No Mutation of Scenario Values
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoScenarioMutation:
    def test_scenario_catalog_unchanged_after_ingestion(self):
        """CRITICAL: Ingesting signals must NOT change SCENARIO_CATALOG."""
        # Capture state before
        before = {
            sid: entry["base_loss_usd"]
            for sid, entry in SCENARIO_CATALOG.items()
        }

        # Run ingestion
        ingest_signals(SAMPLE_RAW_SIGNALS, source_id="sig_sample_static")

        # Verify state unchanged
        after = {
            sid: entry["base_loss_usd"]
            for sid, entry in SCENARIO_CATALOG.items()
        }
        assert before == after

    def test_ingestion_returns_read_only_snapshots(self):
        """Snapshots are frozen — cannot be mutated."""
        snapshots = ingest_signals(
            SAMPLE_RAW_SIGNALS,
            source_id="sig_sample_static",
            ingested_at="2026-04-15T12:00:00Z",
        )
        for snap in snapshots:
            with pytest.raises(AttributeError):
                snap.confidence_score = 999  # type: ignore


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Audit Log Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLog:
    def test_audit_log_records_entries(self):
        log = SignalAuditLog()
        log.record(
            action=SignalAuditAction.SOURCE_CHECKED,
            source_id="test_src",
            detail="Checked test source",
        )
        assert log.count == 1
        assert log.entries[0].action == SignalAuditAction.SOURCE_CHECKED

    def test_audit_log_append_only(self):
        log = SignalAuditLog()
        log.record(action=SignalAuditAction.SOURCE_CHECKED, source_id="a")
        log.record(action=SignalAuditAction.SNAPSHOT_CREATED, source_id="a", snapshot_id="s1")
        assert log.count == 2

    def test_audit_log_filter_by_action(self):
        log = SignalAuditLog()
        log.record(action=SignalAuditAction.SOURCE_CHECKED, source_id="a")
        log.record(action=SignalAuditAction.SNAPSHOT_CREATED, source_id="a")
        log.record(action=SignalAuditAction.SOURCE_FAILED, source_id="b")
        checks = log.entries_by_action(SignalAuditAction.SOURCE_CHECKED)
        assert len(checks) == 1

    def test_audit_log_filter_by_source(self):
        log = SignalAuditLog()
        log.record(action=SignalAuditAction.SOURCE_CHECKED, source_id="a")
        log.record(action=SignalAuditAction.SOURCE_CHECKED, source_id="b")
        a_entries = log.entries_by_source("a")
        assert len(a_entries) == 1

    def test_audit_summary(self):
        log = SignalAuditLog()
        log.record(action=SignalAuditAction.SOURCE_CHECKED, source_id="a")
        log.record(action=SignalAuditAction.SNAPSHOT_CREATED, source_id="a")
        summary = log.summary()
        assert summary["total_entries"] == 2
        assert summary["sources_checked"] == 1
        assert summary["snapshots_created"] == 1

    def test_audit_entry_serializable(self):
        log = SignalAuditLog()
        entry = log.record(action=SignalAuditAction.SOURCE_CHECKED, source_id="a")
        d = entry.to_dict()
        json.dumps(d)  # Must not raise

    def test_ingestion_populates_audit_log(self):
        log = SignalAuditLog()
        ingest_signals(
            SAMPLE_RAW_SIGNALS,
            source_id="sig_sample_static",
            audit_log=log,
            ingested_at="2026-04-15T12:00:00Z",
        )
        assert log.count >= 4  # 1 check + 3 snapshots
        assert log.summary()["snapshots_created"] == 3

    def test_disabled_source_logs_fallback(self):
        log = SignalAuditLog()
        ingest_signals([{"title": "test"}], source_id="sig_reuters_energy", audit_log=log)
        fallbacks = log.entries_by_action(SignalAuditAction.FALLBACK_USED)
        assert len(fallbacks) == 1

    def test_missing_source_logs_failure(self):
        log = SignalAuditLog()
        ingest_signals([{"title": "test"}], source_id="nonexistent", audit_log=log)
        failures = log.entries_by_action(SignalAuditAction.SOURCE_FAILED)
        assert len(failures) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Batch Ingestion End-to-End
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchIngestion:
    def test_ingest_sample_signals(self):
        snapshots = ingest_signals(
            SAMPLE_RAW_SIGNALS,
            source_id="sig_sample_static",
            ingested_at="2026-04-15T12:00:00Z",
        )
        assert len(snapshots) == 3

    def test_all_snapshots_have_source_id(self):
        snapshots = ingest_signals(
            SAMPLE_RAW_SIGNALS,
            source_id="sig_sample_static",
            ingested_at="2026-04-15T12:00:00Z",
        )
        for snap in snapshots:
            assert snap.source_id == "sig_sample_static"

    def test_all_snapshots_json_serializable(self):
        snapshots = ingest_signals(
            SAMPLE_RAW_SIGNALS,
            source_id="sig_sample_static",
            ingested_at="2026-04-15T12:00:00Z",
        )
        for snap in snapshots:
            json.dumps(snap.to_dict())

    def test_ingestion_is_deterministic(self):
        a = ingest_signals(
            SAMPLE_RAW_SIGNALS, source_id="sig_sample_static",
            ingested_at="2026-04-15T12:00:00Z",
        )
        b = ingest_signals(
            SAMPLE_RAW_SIGNALS, source_id="sig_sample_static",
            ingested_at="2026-04-15T12:00:00Z",
        )
        assert [s.snapshot_id for s in a] == [s.snapshot_id for s in b]
        assert [s.confidence_score for s in a] == [s.confidence_score for s in b]
