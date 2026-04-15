"""
Impact Observatory | مرصد الأثر
Test Suite: Governance Decision Gate v5

Tests:
  1. Default mode is OFF or ADVISORY (never SCORING)
  2. SCORING is disabled by default
  3. Low confidence triggers fallback/advisory
  4. Stale signal triggers advisory
  5. Expired signal triggers block
  6. Bounds exceeded triggers block
  7. Mode transitions are correct
  8. Governance verdicts are serializable
  9. Constants are sane
  10. No scenario catalog mutation
"""
import json
import os
import pytest
from unittest.mock import patch

from src.signal_ingestion.governance import (
    ImpactMode,
    GovernanceDecision,
    GovernanceVerdict,
    resolve_impact_mode,
    evaluate_governance_gate,
    MIN_SOURCE_CONFIDENCE,
    MIN_SNAPSHOT_CONFIDENCE,
    MIN_SCORING_CONFIDENCE,
    MAX_ADJUSTMENT_FACTOR,
    MAX_CONSECUTIVE_FAILURES,
    FRESHNESS_WINDOWS,
)
from src.signal_ingestion.models import SnapshotFreshness
from src.simulation_engine import SCENARIO_CATALOG


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Default Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDefaultMode:
    def test_default_mode_is_off(self):
        """With no env vars, mode must be OFF."""
        with patch.dict(os.environ, {}, clear=True):
            mode = resolve_impact_mode()
            assert mode == ImpactMode.OFF

    def test_preview_only_gives_advisory(self):
        """With preview enabled but scoring off, mode is ADVISORY."""
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "false",
        }):
            mode = resolve_impact_mode()
            assert mode == ImpactMode.ADVISORY

    def test_both_flags_gives_scoring(self):
        """With both flags, mode is SCORING."""
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            mode = resolve_impact_mode()
            assert mode == ImpactMode.SCORING


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SCORING Disabled by Default
# ═══════════════════════════════════════════════════════════════════════════════

class TestScoringDisabled:
    def test_scoring_blocked_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            verdict = evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.05,
            )
            assert verdict.decision != GovernanceDecision.ALLOWED
            assert verdict.decision == GovernanceDecision.BLOCKED_FLAG_OFF
            assert verdict.fallback_used is True

    def test_scoring_blocked_with_preview_only(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            verdict = evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.05,
            )
            assert verdict.decision == GovernanceDecision.ADVISORY_ONLY
            assert verdict.adjustment_allowed == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Low Confidence Triggers Fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestLowConfidence:
    def test_low_source_confidence_blocked(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            verdict = evaluate_governance_gate(
                source_confidence=0.40,  # Below MIN_SOURCE_CONFIDENCE (0.60)
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.FRESH,
            )
            assert verdict.decision == GovernanceDecision.BLOCKED_LOW_CONFIDENCE
            assert verdict.fallback_used is True

    def test_low_snapshot_confidence_advisory(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            verdict = evaluate_governance_gate(
                source_confidence=0.80,
                snapshot_confidence=0.30,  # Below MIN_SNAPSHOT_CONFIDENCE (0.40)
                freshness=SnapshotFreshness.FRESH,
            )
            assert verdict.decision == GovernanceDecision.ADVISORY_ONLY
            assert verdict.fallback_used is True

    def test_scoring_confidence_check(self):
        """Even in SCORING mode, below MIN_SCORING_CONFIDENCE → advisory."""
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            verdict = evaluate_governance_gate(
                source_confidence=0.70,
                snapshot_confidence=0.45,  # Below MIN_SCORING_CONFIDENCE (0.50)
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.05,
            )
            assert verdict.decision == GovernanceDecision.ADVISORY_ONLY


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Stale Signal Triggers Advisory
# ═══════════════════════════════════════════════════════════════════════════════

class TestStaleSignal:
    def test_stale_signal_advisory(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            verdict = evaluate_governance_gate(
                source_confidence=0.80,
                snapshot_confidence=0.60,
                freshness=SnapshotFreshness.STALE,
            )
            assert verdict.decision == GovernanceDecision.ADVISORY_ONLY
            assert "stale" in verdict.reason.lower()

    def test_stale_in_scoring_mode_still_advisory(self):
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            verdict = evaluate_governance_gate(
                source_confidence=0.80,
                snapshot_confidence=0.60,
                freshness=SnapshotFreshness.STALE,
                adjustment_factor=0.05,
            )
            assert verdict.decision == GovernanceDecision.ADVISORY_ONLY
            assert verdict.adjustment_allowed == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Expired Signal Triggers Block
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpiredSignal:
    def test_expired_signal_blocked(self):
        with patch.dict(os.environ, {"ENABLE_DEV_SIGNAL_PREVIEW": "true"}):
            verdict = evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.EXPIRED,
            )
            assert verdict.decision == GovernanceDecision.BLOCKED_EXPIRED
            assert verdict.fallback_used is True

    def test_expired_in_scoring_mode_still_blocked(self):
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            verdict = evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.EXPIRED,
                adjustment_factor=0.10,
            )
            assert verdict.decision == GovernanceDecision.BLOCKED_EXPIRED


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Bounds Exceeded Triggers Block
# ═══════════════════════════════════════════════════════════════════════════════

class TestBoundsExceeded:
    def test_adjustment_exceeds_bounds(self):
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            verdict = evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.25,  # Exceeds ±0.15
            )
            assert verdict.decision == GovernanceDecision.BLOCKED_BOUNDS_EXCEEDED
            assert verdict.adjustment_allowed == 0.0

    def test_negative_bounds_exceeded(self):
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            verdict = evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=-0.20,
            )
            assert verdict.decision == GovernanceDecision.BLOCKED_BOUNDS_EXCEEDED


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Full Gate Pass (SCORING mode)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullGatePass:
    def test_all_gates_pass_in_scoring_mode(self):
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            verdict = evaluate_governance_gate(
                source_confidence=0.85,
                snapshot_confidence=0.70,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.10,
            )
            assert verdict.decision == GovernanceDecision.ALLOWED
            assert verdict.mode == ImpactMode.SCORING
            assert verdict.fallback_used is False
            assert verdict.adjustment_allowed == 0.10
            assert verdict.approved_by == "feature_flag"

    def test_adjustment_clamped_to_bounds(self):
        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            # adjustment_factor=0.14 is within bounds
            verdict = evaluate_governance_gate(
                source_confidence=0.85,
                snapshot_confidence=0.70,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.14,
            )
            assert verdict.decision == GovernanceDecision.ALLOWED
            assert verdict.adjustment_allowed == 0.14


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Serialization
# ═══════════════════════════════════════════════════════════════════════════════

class TestSerialization:
    def test_verdict_to_dict_serializable(self):
        with patch.dict(os.environ, {}, clear=True):
            verdict = evaluate_governance_gate(
                source_confidence=0.80,
                snapshot_confidence=0.60,
                freshness=SnapshotFreshness.FRESH,
            )
            d = verdict.to_dict()
            json.dumps(d)  # Must not raise

    def test_all_decisions_serializable(self):
        for d in GovernanceDecision:
            json.dumps(d.value)

    def test_all_modes_serializable(self):
        for m in ImpactMode:
            json.dumps(m.value)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Constants Sanity
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstants:
    def test_confidence_thresholds_ordered(self):
        assert MIN_SNAPSHOT_CONFIDENCE < MIN_SCORING_CONFIDENCE < MIN_SOURCE_CONFIDENCE

    def test_adjustment_factor_positive(self):
        assert MAX_ADJUSTMENT_FACTOR > 0
        assert MAX_ADJUSTMENT_FACTOR <= 0.20  # Never more than 20%

    def test_max_failures_positive(self):
        assert MAX_CONSECUTIVE_FAILURES >= 1

    def test_freshness_windows_complete(self):
        expected_types = {"rss", "api", "market", "government", "manual"}
        assert set(FRESHNESS_WINDOWS.keys()) == expected_types
        for st, windows in FRESHNESS_WINDOWS.items():
            if st != "manual":
                assert windows["fresh"] < windows["recent"] < windows["stale"]


# ═══════════════════════════════════════════════════════════════════════════════
# 10. No Scenario Mutation
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoMutation:
    def test_catalog_unchanged_after_governance_check(self):
        before = {sid: e["base_loss_usd"] for sid, e in SCENARIO_CATALOG.items()}

        with patch.dict(os.environ, {
            "ENABLE_DEV_SIGNAL_PREVIEW": "true",
            "ENABLE_SIGNAL_SCORING_V5": "true",
        }):
            evaluate_governance_gate(
                source_confidence=0.90,
                snapshot_confidence=0.80,
                freshness=SnapshotFreshness.FRESH,
                adjustment_factor=0.10,
            )

        after = {sid: e["base_loss_usd"] for sid, e in SCENARIO_CATALOG.items()}
        assert before == after
