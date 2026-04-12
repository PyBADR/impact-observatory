"""
Evaluation Scoring — Determinism + Edge Case Tests
====================================================

Validates:
  1. Each scoring function is deterministic (same inputs → same output)
  2. Boundary conditions produce correct scores
  3. Composite correctness_score weights sum to 1.0
  4. Confidence gap direction (positive = overconfident)
  5. Explainability completeness counts fields correctly
  6. Full evaluate_decision round-trip
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.data_foundation.schemas.enums import RiskLevel, SignalSeverity
from src.data_foundation.evaluation.schemas import (
    ExpectedOutcome,
    ActualOutcome,
    DecisionEvaluation,
    ObservationSource,
    ObservationCompleteness,
)
from src.data_foundation.evaluation.scoring import (
    compute_severity_alignment,
    compute_entity_alignment,
    compute_sector_alignment,
    compute_timing_alignment,
    compute_correctness_score,
    compute_confidence_gap,
    compute_explainability_completeness,
    evaluate_decision,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Severity alignment
# ═══════════════════════════════════════════════════════════════════════════════


class TestSeverityAlignment:

    def test_exact_match_returns_1(self):
        assert compute_severity_alignment("SEVERE", "SEVERE") == 1.0

    def test_adjacent_levels(self):
        # SEVERE=5, HIGH=4 → distance=1 → 1.0 - 1/5 = 0.8
        assert compute_severity_alignment("SEVERE", "HIGH") == 0.8

    def test_max_distance(self):
        # SEVERE=5, NOMINAL=0 → distance=5 → 1.0 - 5/5 = 0.0
        assert compute_severity_alignment("SEVERE", "NOMINAL") == 0.0

    def test_none_actual_returns_0(self):
        assert compute_severity_alignment("SEVERE", None) == 0.0

    def test_symmetric(self):
        a = compute_severity_alignment("HIGH", "LOW")
        b = compute_severity_alignment("LOW", "HIGH")
        assert a == b

    def test_deterministic(self):
        """Same inputs always produce same output."""
        for _ in range(100):
            assert compute_severity_alignment("ELEVATED", "GUARDED") == 0.8


# ═══════════════════════════════════════════════════════════════════════════════
# Entity alignment (Jaccard)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEntityAlignment:

    def test_identical_sets(self):
        assert compute_entity_alignment(["A", "B"], ["A", "B"]) == 1.0

    def test_disjoint_sets(self):
        assert compute_entity_alignment(["A", "B"], ["C", "D"]) == 0.0

    def test_partial_overlap(self):
        # Jaccard({A,B,C}, {B,C,D}) = |{B,C}| / |{A,B,C,D}| = 2/4 = 0.5
        assert compute_entity_alignment(["A", "B", "C"], ["B", "C", "D"]) == 0.5

    def test_both_empty(self):
        assert compute_entity_alignment([], []) == 1.0

    def test_expected_empty_actual_nonempty(self):
        assert compute_entity_alignment([], ["A"]) == 0.0

    def test_expected_nonempty_actual_empty(self):
        assert compute_entity_alignment(["A"], []) == 0.0

    def test_duplicates_ignored(self):
        assert compute_entity_alignment(["A", "A", "B"], ["A", "B"]) == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Sector alignment (Jaccard)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSectorAlignment:

    def test_identical(self):
        assert compute_sector_alignment(["banking", "energy"], ["banking", "energy"]) == 1.0

    def test_disjoint(self):
        assert compute_sector_alignment(["banking"], ["energy"]) == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Timing alignment
# ═══════════════════════════════════════════════════════════════════════════════


class TestTimingAlignment:

    def test_exact_match(self):
        assert compute_timing_alignment(24.0, 24.0) == 1.0

    def test_double_expected(self):
        # |24 - 48| / 24 = 1.0 → max(0, 1 - 1) = 0.0
        assert compute_timing_alignment(24.0, 48.0) == 0.0

    def test_half_expected(self):
        # |24 - 12| / 24 = 0.5 → 1 - 0.5 = 0.5
        assert compute_timing_alignment(24.0, 12.0) == 0.5

    def test_no_expected_returns_1(self):
        """Timing not predicted → neutral score."""
        assert compute_timing_alignment(None, 12.0) == 1.0

    def test_zero_expected_returns_1(self):
        assert compute_timing_alignment(0.0, 12.0) == 1.0

    def test_no_actual_returns_0(self):
        assert compute_timing_alignment(24.0, None) == 0.0

    def test_both_none_returns_1(self):
        assert compute_timing_alignment(None, None) == 1.0

    def test_negative_clamped_to_zero(self):
        # |10 - 100| / 10 = 9.0 → max(0, 1 - 9) = 0.0
        assert compute_timing_alignment(10.0, 100.0) == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Correctness score (weights)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCorrectnessScore:

    def test_all_perfect(self):
        assert compute_correctness_score(1.0, 1.0, 1.0, 1.0) == pytest.approx(1.0)

    def test_all_zero(self):
        assert compute_correctness_score(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_weights_sum_to_1(self):
        """Verify weight values: 0.35 + 0.30 + 0.20 + 0.15 = 1.0"""
        score = compute_correctness_score(1.0, 1.0, 1.0, 1.0)
        assert score == pytest.approx(1.0)

    def test_severity_dominates(self):
        """Severity has highest weight (0.35)."""
        severity_only = compute_correctness_score(1.0, 0.0, 0.0, 0.0)
        entity_only = compute_correctness_score(0.0, 1.0, 0.0, 0.0)
        assert severity_only > entity_only

    def test_sector_has_lowest_weight(self):
        """Sector has lowest weight (0.15)."""
        sector_only = compute_correctness_score(0.0, 0.0, 0.0, 1.0)
        assert sector_only == pytest.approx(0.15)


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence gap
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfidenceGap:

    def test_overconfident(self):
        """Rule confidence 0.9, correctness 0.5 → gap = +0.4."""
        assert compute_confidence_gap(0.9, 0.5) == pytest.approx(0.4)

    def test_underconfident(self):
        """Rule confidence 0.3, correctness 0.8 → gap = -0.5."""
        assert compute_confidence_gap(0.3, 0.8) == pytest.approx(-0.5)

    def test_perfectly_calibrated(self):
        assert compute_confidence_gap(0.7, 0.7) == pytest.approx(0.0)

    def test_clamped_positive(self):
        assert compute_confidence_gap(1.0, 0.0) == 1.0

    def test_clamped_negative(self):
        assert compute_confidence_gap(0.0, 1.0) == -1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Explainability completeness
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplainabilityCompleteness:

    def test_fully_complete(self):
        expected = ExpectedOutcome(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            spec_id="SPEC-OIL-v1",
            expected_severity=SignalSeverity.SEVERE,
            expected_risk_level=RiskLevel.SEVERE,
            expected_affected_entity_ids=["E1"],
            expected_affected_sectors=["banking"],
            expected_affected_countries=["KW"],
            expected_financial_impact=100.0,
            expected_mitigation_effect="Hedge exposure",
            expected_resolution_hours=48.0,
            data_state_snapshot={"key": "value"},
        )
        assert compute_explainability_completeness(expected) == 1.0

    def test_minimal(self):
        """Only severity and risk_level are required fields — everything else empty."""
        expected = ExpectedOutcome(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            expected_severity=SignalSeverity.NOMINAL,
            expected_risk_level=RiskLevel.NOMINAL,
        )
        # severity ✓, risk_level ✓, entities ✗, sectors ✗, countries ✗,
        # financial ✗, mitigation ✗, resolution ✗, data_state ✗, spec_id ✗
        assert compute_explainability_completeness(expected) == 0.2


# ═══════════════════════════════════════════════════════════════════════════════
# Full evaluate_decision round-trip
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvaluateDecision:

    def _make_expected(self):
        return ExpectedOutcome(
            decision_log_id="DLOG-100",
            rule_id="RULE-OIL-BRENT-DROP-30",
            spec_id="SPEC-OIL-BRENT-DROP-30-v1",
            expected_severity=SignalSeverity.SEVERE,
            expected_risk_level=RiskLevel.SEVERE,
            expected_affected_entity_ids=["SA-ARAMCO", "KW-KPC", "AE-ADNOC"],
            expected_affected_sectors=["energy", "banking", "insurance"],
            expected_affected_countries=["SA", "KW", "AE"],
            expected_financial_impact=5000.0,
            expected_mitigation_effect="Activate contingency plan",
            expected_resolution_hours=72.0,
            data_state_snapshot={"oil_energy_signals.change_pct": -35.0},
        )

    def _make_actual_perfect(self):
        return ActualOutcome(
            expected_outcome_id="EXOUT-placeholder",
            decision_log_id="DLOG-100",
            actual_severity=SignalSeverity.SEVERE,
            actual_risk_level=RiskLevel.SEVERE,
            actual_affected_entity_ids=["SA-ARAMCO", "KW-KPC", "AE-ADNOC"],
            actual_affected_sectors=["energy", "banking", "insurance"],
            actual_affected_countries=["SA", "KW", "AE"],
            actual_financial_impact=4800.0,
            actual_resolution_hours=72.0,
            observation_completeness=ObservationCompleteness.COMPLETE,
        )

    def _make_actual_divergent(self):
        return ActualOutcome(
            expected_outcome_id="EXOUT-placeholder",
            decision_log_id="DLOG-100",
            actual_severity=SignalSeverity.ELEVATED,
            actual_affected_entity_ids=["SA-ARAMCO"],
            actual_affected_sectors=["energy"],
            actual_resolution_hours=120.0,
            observation_completeness=ObservationCompleteness.COMPLETE,
        )

    def test_perfect_match_scores_high(self):
        expected = self._make_expected()
        actual = self._make_actual_perfect()
        actual.expected_outcome_id = expected.expected_outcome_id

        evaluation = evaluate_decision(expected, actual, rule_confidence=0.9)

        assert isinstance(evaluation, DecisionEvaluation)
        assert evaluation.severity_alignment_score == 1.0
        assert evaluation.entity_alignment_score == 1.0
        assert evaluation.sector_alignment_score == 1.0
        assert evaluation.timing_alignment_score == 1.0
        assert evaluation.correctness_score == 1.0
        assert evaluation.provenance_hash != ""

    def test_divergent_match_scores_lower(self):
        expected = self._make_expected()
        actual = self._make_actual_divergent()
        actual.expected_outcome_id = expected.expected_outcome_id

        evaluation = evaluate_decision(expected, actual, rule_confidence=0.9)

        assert evaluation.correctness_score < 1.0
        assert evaluation.severity_alignment_score < 1.0
        assert evaluation.entity_alignment_score < 1.0
        assert evaluation.confidence_gap > 0  # overconfident

    def test_evaluation_has_all_fields(self):
        expected = self._make_expected()
        actual = self._make_actual_perfect()
        actual.expected_outcome_id = expected.expected_outcome_id

        evaluation = evaluate_decision(expected, actual)

        assert evaluation.expected_outcome_id == expected.expected_outcome_id
        assert evaluation.actual_outcome_id == actual.actual_outcome_id
        assert evaluation.decision_log_id == "DLOG-100"
        assert evaluation.rule_id == "RULE-OIL-BRENT-DROP-30"
        assert evaluation.spec_id == "SPEC-OIL-BRENT-DROP-30-v1"
        assert evaluation.scoring_method_version == "1.0.0"

    def test_deterministic(self):
        """Same inputs always produce same scores."""
        expected = self._make_expected()
        actual = self._make_actual_divergent()
        actual.expected_outcome_id = expected.expected_outcome_id

        scores = set()
        for _ in range(50):
            ev = evaluate_decision(expected, actual, 0.85)
            scores.add(ev.correctness_score)

        assert len(scores) == 1, "Scoring is non-deterministic!"

    def test_confidence_gap_direction(self):
        """Overconfident rule → positive gap."""
        expected = self._make_expected()
        actual = self._make_actual_divergent()
        actual.expected_outcome_id = expected.expected_outcome_id

        evaluation = evaluate_decision(expected, actual, rule_confidence=0.95)
        assert evaluation.confidence_gap > 0.0
