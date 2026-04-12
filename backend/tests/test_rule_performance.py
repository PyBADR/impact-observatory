"""
Rule Performance Aggregator — Tests
=====================================

Validates:
  1. Empty evaluations produce zero-ed snapshot
  2. Averages computed correctly
  3. Verdict counts from feedbacks
  4. Failure mode counting
  5. Multiple feedbacks per evaluation (latest wins)
  6. aggregate_all_rules handles multiple rules
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from src.data_foundation.evaluation.schemas import (
    DecisionEvaluation,
    AnalystFeedbackRecord,
    RulePerformanceSnapshot,
    AnalystVerdict,
    FailureMode,
)
from src.data_foundation.evaluation.rule_performance_aggregator import (
    aggregate_rule_performance,
    aggregate_all_rules,
)

NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=30)
END = NOW


def _make_eval(
    rule_id: str = "RULE-TEST",
    correctness: float = 0.8,
    severity: float = 0.8,
    entity: float = 0.6,
    timing: float = 0.7,
    sector: float = 0.5,
    confidence_gap: float = 0.1,
    explainability: float = 0.9,
    verdict: str = None,
) -> DecisionEvaluation:
    return DecisionEvaluation(
        expected_outcome_id=f"EXOUT-{id(correctness)}",
        actual_outcome_id=f"ACOUT-{id(correctness)}",
        decision_log_id=f"DLOG-{id(correctness)}",
        rule_id=rule_id,
        correctness_score=correctness,
        severity_alignment_score=severity,
        entity_alignment_score=entity,
        timing_alignment_score=timing,
        sector_alignment_score=sector,
        confidence_gap=confidence_gap,
        explainability_completeness_score=explainability,
        analyst_verdict=verdict,
    )


def _make_feedback(
    evaluation_id: str,
    verdict: str = AnalystVerdict.CORRECT,
    failure_mode: str = None,
    offset_minutes: int = 0,
) -> AnalystFeedbackRecord:
    return AnalystFeedbackRecord(
        evaluation_id=evaluation_id,
        decision_log_id="DLOG-1",
        analyst_id="analyst-1",
        verdict=verdict,
        override_reason="Test",
        failure_mode=failure_mode,
        submitted_at=NOW + timedelta(minutes=offset_minutes),
    )


class TestAggregateRulePerformance:

    def test_empty_evaluations(self):
        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=[],
            feedbacks=[],
            period_start=START,
            period_end=END,
        )
        assert snapshot.total_evaluations == 0
        assert snapshot.total_triggered == 0
        assert snapshot.avg_correctness_score == 0.0
        assert snapshot.provenance_hash != ""

    def test_single_evaluation_averages(self):
        e = _make_eval(correctness=0.8, severity=0.6, entity=0.4, timing=0.5)
        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=[e],
            feedbacks=[],
            period_start=START,
            period_end=END,
        )
        assert snapshot.total_evaluations == 1
        assert snapshot.avg_correctness_score == pytest.approx(0.8)
        assert snapshot.avg_severity_alignment == pytest.approx(0.6)
        assert snapshot.avg_entity_alignment == pytest.approx(0.4)

    def test_multiple_evaluations_average(self):
        evals = [
            _make_eval(correctness=0.8),
            _make_eval(correctness=0.6),
            _make_eval(correctness=0.4),
        ]
        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=evals,
            feedbacks=[],
            period_start=START,
            period_end=END,
        )
        assert snapshot.total_evaluations == 3
        assert snapshot.avg_correctness_score == pytest.approx(0.6)

    def test_verdict_counting_from_feedback(self):
        e1 = _make_eval()
        e2 = _make_eval()
        e3 = _make_eval()

        feedbacks = [
            _make_feedback(e1.evaluation_id, AnalystVerdict.CORRECT),
            _make_feedback(e2.evaluation_id, AnalystVerdict.INCORRECT, FailureMode.FALSE_POSITIVE),
            _make_feedback(e3.evaluation_id, AnalystVerdict.PARTIALLY_CORRECT),
        ]

        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=[e1, e2, e3],
            feedbacks=feedbacks,
            period_start=START,
            period_end=END,
        )
        assert snapshot.confirmed_correct == 1
        assert snapshot.confirmed_incorrect == 1
        assert snapshot.confirmed_partially_correct == 1
        assert snapshot.false_positive_count == 1

    def test_latest_feedback_wins(self):
        """When multiple feedbacks exist for same evaluation, latest wins."""
        e = _make_eval()
        feedbacks = [
            _make_feedback(e.evaluation_id, AnalystVerdict.INCORRECT, offset_minutes=0),
            _make_feedback(e.evaluation_id, AnalystVerdict.CORRECT, offset_minutes=10),
        ]

        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=[e],
            feedbacks=feedbacks,
            period_start=START,
            period_end=END,
        )
        # Latest feedback says CORRECT
        assert snapshot.confirmed_correct == 1
        assert snapshot.confirmed_incorrect == 0

    def test_verdict_from_evaluation_when_no_feedback(self):
        """Fallback to evaluation.analyst_verdict when no feedback exists."""
        e = _make_eval(verdict=AnalystVerdict.CORRECT)
        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=[e],
            feedbacks=[],
            period_start=START,
            period_end=END,
        )
        assert snapshot.confirmed_correct == 1

    def test_false_negative_counting(self):
        e = _make_eval()
        fb = _make_feedback(
            e.evaluation_id,
            AnalystVerdict.INCORRECT,
            FailureMode.FALSE_NEGATIVE,
        )
        snapshot = aggregate_rule_performance(
            rule_id="RULE-TEST",
            evaluations=[e],
            feedbacks=[fb],
            period_start=START,
            period_end=END,
        )
        assert snapshot.false_negative_count == 1
        assert snapshot.false_positive_count == 0


class TestAggregateAllRules:

    def test_multiple_rules(self):
        evals_by_rule = {
            "RULE-A": [_make_eval(rule_id="RULE-A", correctness=0.9)],
            "RULE-B": [
                _make_eval(rule_id="RULE-B", correctness=0.6),
                _make_eval(rule_id="RULE-B", correctness=0.4),
            ],
        }
        snapshots = aggregate_all_rules(
            evaluations_by_rule=evals_by_rule,
            feedbacks_by_evaluation={},
            period_start=START,
            period_end=END,
        )
        assert len(snapshots) == 2

        a = next(s for s in snapshots if s.rule_id == "RULE-A")
        b = next(s for s in snapshots if s.rule_id == "RULE-B")

        assert a.total_evaluations == 1
        assert a.avg_correctness_score == pytest.approx(0.9)
        assert b.total_evaluations == 2
        assert b.avg_correctness_score == pytest.approx(0.5)
