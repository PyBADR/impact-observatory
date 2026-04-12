"""
Evaluation Schemas — Instantiation + Validation Tests
=======================================================

Validates:
  1. All 7 schemas instantiate without Pydantic errors
  2. Default values are correct
  3. Hash computation works
  4. ID generation produces unique IDs
  5. Enum string constants are valid
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from src.data_foundation.schemas.enums import RiskLevel, SignalSeverity
from src.data_foundation.evaluation.schemas import (
    ExpectedOutcome,
    ActualOutcome,
    DecisionEvaluation,
    AnalystFeedbackRecord,
    ReplayRun,
    ReplayRunResult,
    RulePerformanceSnapshot,
    AnalystVerdict,
    FailureMode,
    ObservationSource,
    ObservationCompleteness,
    ReplayStatus,
    RuleSetSource,
    SCORING_METHOD_VERSION,
)


class TestExpectedOutcome:

    def test_instantiation(self):
        e = ExpectedOutcome(
            decision_log_id="DLOG-1",
            rule_id="RULE-OIL-1",
            expected_severity=SignalSeverity.HIGH,
            expected_risk_level=RiskLevel.HIGH,
        )
        assert e.expected_outcome_id.startswith("EXOUT-")
        assert e.decision_log_id == "DLOG-1"

    def test_hash_computation(self):
        e = ExpectedOutcome(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            expected_severity=SignalSeverity.LOW,
            expected_risk_level=RiskLevel.LOW,
            data_state_snapshot={"key": "value"},
        )
        e.compute_hashes()
        assert e.data_state_hash != ""
        assert e.provenance_hash != ""
        assert len(e.data_state_hash) == 64  # SHA-256

    def test_unique_ids(self):
        ids = set()
        for _ in range(100):
            e = ExpectedOutcome(
                decision_log_id="D", rule_id="R",
                expected_severity=SignalSeverity.LOW,
                expected_risk_level=RiskLevel.LOW,
            )
            ids.add(e.expected_outcome_id)
        assert len(ids) == 100


class TestActualOutcome:

    def test_instantiation_minimal(self):
        a = ActualOutcome(
            expected_outcome_id="EXOUT-1",
            decision_log_id="DLOG-1",
        )
        assert a.actual_outcome_id.startswith("ACOUT-")
        assert a.actual_severity is None
        assert a.observation_completeness == ObservationCompleteness.PRELIMINARY

    def test_full_instantiation(self):
        a = ActualOutcome(
            expected_outcome_id="EXOUT-1",
            decision_log_id="DLOG-1",
            actual_severity=SignalSeverity.SEVERE,
            actual_risk_level=RiskLevel.SEVERE,
            actual_affected_entity_ids=["E1", "E2"],
            actual_financial_impact=500.0,
            observation_source=ObservationSource.REAL_SOURCE_DATA,
            observation_completeness=ObservationCompleteness.COMPLETE,
        )
        assert a.actual_severity == SignalSeverity.SEVERE
        assert len(a.actual_affected_entity_ids) == 2


class TestDecisionEvaluation:

    def test_instantiation(self):
        e = DecisionEvaluation(
            expected_outcome_id="EXOUT-1",
            actual_outcome_id="ACOUT-1",
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            correctness_score=0.85,
            severity_alignment_score=0.8,
            entity_alignment_score=0.7,
            timing_alignment_score=0.9,
            sector_alignment_score=0.6,
            confidence_gap=0.1,
            explainability_completeness_score=0.9,
        )
        assert e.evaluation_id.startswith("EVAL-")
        assert e.scoring_method_version == SCORING_METHOD_VERSION

    def test_score_bounds_enforced(self):
        with pytest.raises(Exception):
            DecisionEvaluation(
                expected_outcome_id="E", actual_outcome_id="A",
                decision_log_id="D", rule_id="R",
                correctness_score=1.5,  # Out of bounds
                severity_alignment_score=0.5,
                entity_alignment_score=0.5,
                timing_alignment_score=0.5,
                sector_alignment_score=0.5,
                confidence_gap=0.0,
                explainability_completeness_score=0.5,
            )


class TestAnalystFeedbackRecord:

    def test_instantiation(self):
        f = AnalystFeedbackRecord(
            evaluation_id="EVAL-1",
            decision_log_id="DLOG-1",
            analyst_id="analyst-1",
            verdict=AnalystVerdict.CORRECT,
            override_reason="Confirmed correct based on CBK report.",
        )
        assert f.feedback_id.startswith("AFBK-")
        assert f.verdict == "CORRECT"

    def test_with_override_score(self):
        f = AnalystFeedbackRecord(
            evaluation_id="EVAL-1",
            decision_log_id="DLOG-1",
            analyst_id="analyst-1",
            verdict=AnalystVerdict.PARTIALLY_CORRECT,
            override_correctness_score=0.65,
            failure_mode=FailureMode.SEVERITY_MISS,
            override_reason="Severity was ELEVATED not SEVERE.",
        )
        assert f.override_correctness_score == 0.65
        assert f.failure_mode == "SEVERITY_MISS"


class TestReplayRun:

    def test_instantiation(self):
        r = ReplayRun(
            replay_data_state={"oil_energy_signals.change_pct": -35.0},
            initiated_by="analyst-1",
        )
        assert r.replay_run_id.startswith("RPLAY-")
        assert r.status == ReplayStatus.RUNNING

    def test_hash_computation(self):
        r = ReplayRun(
            replay_data_state={"key": "value"},
            initiated_by="test",
        )
        r.compute_hashes()
        assert r.replay_data_state_hash != ""
        assert r.provenance_hash != ""


class TestReplayRunResult:

    def test_instantiation(self):
        r = ReplayRunResult(
            replay_run_id="RPLAY-1",
            rule_id="RULE-OIL-1",
            rule_version=1,
            triggered=True,
            action="ACTIVATE_CONTINGENCY",
        )
        assert r.replay_result_id.startswith("RRES-")
        assert r.triggered is True


class TestRulePerformanceSnapshot:

    def test_instantiation(self):
        now = datetime.now(timezone.utc)
        s = RulePerformanceSnapshot(
            rule_id="RULE-OIL-1",
            period_start=now - timedelta(days=30),
            period_end=now,
            total_evaluations=10,
            avg_correctness_score=0.85,
        )
        assert s.snapshot_id.startswith("RPERF-")
        assert s.total_evaluations == 10

    def test_defaults(self):
        now = datetime.now(timezone.utc)
        s = RulePerformanceSnapshot(
            rule_id="R", period_start=now, period_end=now,
        )
        assert s.false_positive_count == 0
        assert s.avg_confidence_gap == 0.0


class TestEnumConstants:

    def test_analyst_verdict_values(self):
        assert len(AnalystVerdict.ALL) == 4
        assert "CORRECT" in AnalystVerdict.ALL

    def test_failure_mode_values(self):
        assert len(FailureMode.ALL) == 6
        assert "FALSE_POSITIVE" in FailureMode.ALL

    def test_observation_source_values(self):
        assert len(ObservationSource.ALL) == 4

    def test_replay_status_values(self):
        assert len(ReplayStatus.ALL) == 3

    def test_rule_set_source_values(self):
        assert len(RuleSetSource.ALL) == 3
