"""
Impact Observatory | مرصد الأثر
Test Suite: Advisory Signal Layer v5 — Advisory Only, No Scoring

Tests:
  1. Feature flag defaults to false
  2. Advisory disabled when flag is false
  3. metric_after == metric_before (always)
  4. scoring_applied == False (always)
  5. Low confidence returns fallback advisory
  6. Stale signal returns fallback advisory
  7. Expired signal returns fallback advisory
  8. SCENARIO_CATALOG unchanged after evaluation
  9. No scoring function called
  10. Advisory model serialization
  11. Batch advisory evaluation
  12. Unknown scenario returns None
  13. Audit log records advisory events
"""
import copy
import os
import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from src.signal_ingestion.models import (
    SignalSnapshot,
    SnapshotFreshness,
)
from src.signal_ingestion.advisory_model import SignalAdvisory
from src.signal_ingestion.advisory_service import (
    evaluate_advisory,
    evaluate_advisories,
)
from src.signal_ingestion.audit_log import SignalAuditLog, SignalAuditAction
from src.signal_ingestion.feature_flags import is_signal_advisory_v5_enabled
from src.simulation_engine import SCENARIO_CATALOG


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

def _make_snapshot(
    *,
    freshness: SnapshotFreshness = SnapshotFreshness.FRESH,
    confidence: float = 0.72,
    scenarios: list[str] | None = None,
    sectors: list[str] | None = None,
) -> SignalSnapshot:
    """Create a test snapshot with configurable freshness/confidence."""
    return SignalSnapshot(
        snapshot_id="snap_test_001",
        source_id="sig_sample_static",
        title="Test Signal — advisory evaluation",
        summary="Test signal for advisory v5 evaluation.",
        url=None,
        published_at="2026-04-15T08:00:00Z",
        ingested_at="2026-04-15T12:00:00Z",
        freshness_status=freshness,
        confidence_score=confidence,
        related_scenarios=scenarios or ["hormuz_chokepoint_disruption"],
        related_countries=["UAE"],
        related_sectors=sectors or ["energy"],
        raw_metadata={},
    )


VALID_SCENARIO = "hormuz_chokepoint_disruption"
INVALID_SCENARIO = "nonexistent_scenario_xyz"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Feature Flag Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFeatureFlagDefaults:
    def test_advisory_v5_flag_defaults_false(self):
        """ENABLE_SIGNAL_ADVISORY_V5 defaults to false."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove the flag if it exists
            os.environ.pop("ENABLE_SIGNAL_ADVISORY_V5", None)
            assert is_signal_advisory_v5_enabled() is False

    def test_advisory_v5_flag_enabled_when_set(self):
        """ENABLE_SIGNAL_ADVISORY_V5=true enables the flag."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            assert is_signal_advisory_v5_enabled() is True

    def test_advisory_v5_flag_false_when_explicit(self):
        """ENABLE_SIGNAL_ADVISORY_V5=false keeps it disabled."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "false"}):
            assert is_signal_advisory_v5_enabled() is False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Advisory Disabled When Flag Off
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryDisabledByDefault:
    def test_returns_none_when_flag_off(self):
        """Advisory returns None when feature flag is disabled."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ENABLE_SIGNAL_ADVISORY_V5", None)
            snapshot = _make_snapshot()
            result = evaluate_advisory(snapshot, VALID_SCENARIO)
            assert result is None

    def test_audit_records_fallback_when_flag_off(self):
        """Audit log records fallback when advisory flag is off."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ENABLE_SIGNAL_ADVISORY_V5", None)
            snapshot = _make_snapshot()
            audit_log = SignalAuditLog()
            evaluate_advisory(snapshot, VALID_SCENARIO, audit_log=audit_log)
            assert audit_log.count >= 1
            fallbacks = audit_log.entries_by_action(SignalAuditAction.FALLBACK_USED)
            assert len(fallbacks) >= 1
            assert "Advisory v5 flag is disabled" in fallbacks[0].detail


# ═══════════════════════════════════════════════════════════════════════════════
# 3. metric_after == metric_before (HARD RULE)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetricUnchanged:
    def test_metric_after_equals_metric_before_fresh(self):
        """metric_after must equal metric_before for fresh signals."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.80)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            assert result.metric_after == result.metric_before

    def test_metric_after_equals_metric_before_stale(self):
        """metric_after must equal metric_before for stale signals."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.STALE, confidence=0.45)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            assert result.metric_after == result.metric_before

    def test_metric_after_equals_metric_before_expired(self):
        """metric_after must equal metric_before for expired signals."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.EXPIRED, confidence=0.20)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            assert result.metric_after == result.metric_before

    def test_metric_matches_scenario_base_loss(self):
        """metric_before must match the scenario's base_loss_usd."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.80)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            expected = float(SCENARIO_CATALOG[VALID_SCENARIO]["base_loss_usd"])
            assert result.metric_before == expected
            assert result.metric_after == expected


# ═══════════════════════════════════════════════════════════════════════════════
# 4. scoring_applied == False (HARD RULE)
# ═══════════════════════════════════════════════════════════════════════════════

class TestScoringNeverApplied:
    def test_scoring_applied_false_for_fresh_signal(self):
        """scoring_applied must be False for fresh high-confidence signals."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.90)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.90)
            assert result is not None
            assert result.scoring_applied is False

    def test_scoring_applied_false_for_all_freshness_levels(self):
        """scoring_applied must be False for every freshness level."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            for freshness in SnapshotFreshness:
                snapshot = _make_snapshot(freshness=freshness, confidence=0.80)
                result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
                assert result is not None
                assert result.scoring_applied is False, \
                    f"scoring_applied should be False for {freshness.value}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Low Confidence → Fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestLowConfidenceFallback:
    def test_low_source_confidence_returns_fallback(self):
        """Source confidence below MIN_SOURCE_CONFIDENCE triggers fallback."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(confidence=0.30)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.30)
            assert result is not None
            assert result.fallback_used is True
            assert result.scoring_applied is False
            assert result.metric_after == result.metric_before

    def test_low_snapshot_confidence_returns_fallback(self):
        """Snapshot confidence below MIN_SNAPSHOT_CONFIDENCE triggers fallback."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(confidence=0.20)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.70)
            assert result is not None
            assert result.fallback_used is True


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Stale Signal → Fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestStaleSignalFallback:
    def test_stale_signal_returns_fallback(self):
        """Stale signals produce fallback advisory."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.STALE, confidence=0.60)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            assert result.scoring_applied is False
            assert result.metric_after == result.metric_before


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Expired Signal → Fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpiredSignalFallback:
    def test_expired_signal_returns_fallback(self):
        """Expired signals produce fallback advisory."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.EXPIRED, confidence=0.20)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            assert result.fallback_used is True
            assert result.scoring_applied is False
            assert result.metric_after == result.metric_before


# ═══════════════════════════════════════════════════════════════════════════════
# 8. SCENARIO_CATALOG Unchanged
# ═══════════════════════════════════════════════════════════════════════════════

class TestScenarioCatalogUnchanged:
    def test_catalog_not_modified_by_advisory(self):
        """SCENARIO_CATALOG must be identical before and after advisory evaluation."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            catalog_before = copy.deepcopy(SCENARIO_CATALOG)
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.85)
            evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.85)
            assert SCENARIO_CATALOG == catalog_before

    def test_base_loss_not_modified_by_advisory(self):
        """base_loss_usd for each scenario must be unchanged."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            losses_before = {
                k: v["base_loss_usd"] for k, v in SCENARIO_CATALOG.items()
            }
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.85)
            for scenario_id in list(SCENARIO_CATALOG.keys())[:5]:
                evaluate_advisory(snapshot, scenario_id, source_confidence=0.85)
            losses_after = {
                k: v["base_loss_usd"] for k, v in SCENARIO_CATALOG.items()
            }
            assert losses_before == losses_after


# ═══════════════════════════════════════════════════════════════════════════════
# 9. No Scoring Function Called
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoScoringCalled:
    def test_no_scoring_imports_in_advisory_service(self):
        """Advisory service must not import scoring functions."""
        import src.signal_ingestion.advisory_service as mod
        source = open(mod.__file__).read()
        # Must not import or call any scoring functions
        assert "compute_unified_risk_score" not in source
        assert "compute_event_severity" not in source
        assert "compute_financial_losses" not in source
        assert "compute_sector_exposure" not in source
        assert "compute_propagation" not in source
        assert "compute_liquidity_stress" not in source
        assert "compute_insurance_stress" not in source
        assert "compute_confidence_score" not in source


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Advisory Model Serialization
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdvisoryModelSerialization:
    def test_advisory_to_dict_roundtrip(self):
        """SignalAdvisory.to_dict() produces expected keys."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.80)
            result = evaluate_advisory(snapshot, VALID_SCENARIO, source_confidence=0.80)
            assert result is not None
            d = result.to_dict()
            expected_keys = {
                "advisory_id", "scenario_id", "snapshot_id", "source_id",
                "confidence", "freshness_status", "advisory_text",
                "risk_context", "suggested_review", "metric_before",
                "metric_after", "scoring_applied", "fallback_used", "timestamp",
            }
            assert set(d.keys()) == expected_keys
            assert d["scoring_applied"] is False
            assert d["metric_before"] == d["metric_after"]


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Batch Advisory Evaluation
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchAdvisory:
    def test_batch_returns_list_of_advisories(self):
        """evaluate_advisories returns a list of SignalAdvisory objects."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshots = [
                _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.80),
                _make_snapshot(freshness=SnapshotFreshness.STALE, confidence=0.45),
            ]
            results = evaluate_advisories(
                snapshots, VALID_SCENARIO, source_confidence=0.80,
            )
            assert len(results) == 2
            for r in results:
                assert isinstance(r, SignalAdvisory)
                assert r.scoring_applied is False
                assert r.metric_after == r.metric_before


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Unknown Scenario → None
# ═══════════════════════════════════════════════════════════════════════════════

class TestUnknownScenario:
    def test_unknown_scenario_returns_none(self):
        """Advisory for nonexistent scenario returns None."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot()
            result = evaluate_advisory(snapshot, INVALID_SCENARIO)
            assert result is None

    def test_unknown_scenario_records_audit(self):
        """Audit log records fallback for unknown scenario."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot()
            audit_log = SignalAuditLog()
            evaluate_advisory(snapshot, INVALID_SCENARIO, audit_log=audit_log)
            fallbacks = audit_log.entries_by_action(SignalAuditAction.FALLBACK_USED)
            assert len(fallbacks) >= 1
            assert INVALID_SCENARIO in fallbacks[0].detail


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Audit Log Records Advisory Events
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLogRecords:
    def test_audit_records_advisory_generation(self):
        """Audit log records event when advisory is generated."""
        with patch.dict(os.environ, {"ENABLE_SIGNAL_ADVISORY_V5": "true"}):
            snapshot = _make_snapshot(freshness=SnapshotFreshness.FRESH, confidence=0.80)
            audit_log = SignalAuditLog()
            result = evaluate_advisory(
                snapshot, VALID_SCENARIO,
                source_confidence=0.80,
                audit_log=audit_log,
            )
            assert result is not None
            assert audit_log.count >= 1
            # Check that audit detail includes key fields
            entries = audit_log.entries
            advisory_entry = entries[-1]
            assert "Advisory generated" in advisory_entry.detail
            assert "scoring_applied=False" in advisory_entry.detail
            assert "metric_before=" in advisory_entry.detail
            assert "metric_after=" in advisory_entry.detail
