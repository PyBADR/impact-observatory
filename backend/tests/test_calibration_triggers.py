"""Tests for calibration trigger engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.data_foundation.governance.schemas import CalibrationTrigger
from src.data_foundation.governance.calibration_triggers import (
    evaluate_threshold,
    evaluate_trigger,
    evaluate_triggers_batch,
    extract_metric,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_trigger(**overrides) -> CalibrationTrigger:
    defaults = {
        "trigger_id": "CTRIG-TEST",
        "trigger_name": "Test trigger",
        "trigger_type": "FALSE_POSITIVE_SPIKE",
        "target_metric": "false_positive_rate",
        "threshold_operator": "gt",
        "threshold_value": 0.30,
        "lookback_window_days": 30,
        "min_evaluations": 5,
        "is_active": True,
        "authored_by": "admin",
    }
    defaults.update(overrides)
    return CalibrationTrigger(**defaults)


class TestExtractMetric:
    def test_direct_field(self):
        assert extract_metric({"average_correctness_score": 0.85}, "average_correctness_score") == 0.85

    def test_false_positive_rate(self):
        snapshot = {"false_positive_count": 10, "match_count": 100}
        assert extract_metric(snapshot, "false_positive_rate") == pytest.approx(0.1)

    def test_false_negative_rate(self):
        snapshot = {"false_negative_count": 5, "match_count": 50}
        assert extract_metric(snapshot, "false_negative_rate") == pytest.approx(0.1)

    def test_accuracy_rate(self):
        snapshot = {"confirmed_correct_count": 80, "match_count": 100}
        assert extract_metric(snapshot, "accuracy_rate") == pytest.approx(0.8)

    def test_zero_match_count(self):
        assert extract_metric({"match_count": 0}, "false_positive_rate") is None

    def test_missing_metric(self):
        assert extract_metric({}, "nonexistent_metric") is None

    def test_non_numeric(self):
        assert extract_metric({"average_correctness_score": "bad"}, "average_correctness_score") is None


class TestEvaluateThreshold:
    def test_gt_true(self):
        assert evaluate_threshold(0.5, "gt", 0.3) is True

    def test_gt_false(self):
        assert evaluate_threshold(0.2, "gt", 0.3) is False

    def test_lt_true(self):
        assert evaluate_threshold(0.2, "lt", 0.3) is True

    def test_gte_boundary(self):
        assert evaluate_threshold(0.3, "gte", 0.3) is True

    def test_lte_boundary(self):
        assert evaluate_threshold(0.3, "lte", 0.3) is True

    def test_exceeds_threshold_positive(self):
        assert evaluate_threshold(0.5, "exceeds_threshold", 0.3) is True

    def test_exceeds_threshold_negative(self):
        assert evaluate_threshold(-0.5, "exceeds_threshold", 0.3) is True

    def test_exceeds_threshold_false(self):
        assert evaluate_threshold(0.2, "exceeds_threshold", 0.3) is False

    def test_unknown_operator(self):
        assert evaluate_threshold(0.5, "unknown", 0.3) is False


class TestEvaluateTrigger:
    def test_trigger_fires(self):
        trigger = _make_trigger()
        snapshot = {"false_positive_rate": None, "false_positive_count": 40, "match_count": 100}
        event = evaluate_trigger(
            trigger, snapshot, "RULE-001",
            _utcnow() - timedelta(days=30), _utcnow(), sample_size=100,
        )
        assert event is not None
        assert event.status == "TRIGGERED"
        assert event.rule_id == "RULE-001"

    def test_trigger_does_not_fire(self):
        trigger = _make_trigger()
        snapshot = {"false_positive_count": 5, "match_count": 100}
        event = evaluate_trigger(
            trigger, snapshot, "RULE-001",
            _utcnow() - timedelta(days=30), _utcnow(), sample_size=100,
        )
        assert event is None

    def test_inactive_trigger_skipped(self):
        trigger = _make_trigger(is_active=False)
        snapshot = {"false_positive_count": 40, "match_count": 100}
        event = evaluate_trigger(
            trigger, snapshot, "RULE-001",
            _utcnow() - timedelta(days=30), _utcnow(), sample_size=100,
        )
        assert event is None

    def test_insufficient_sample_size(self):
        trigger = _make_trigger(min_evaluations=50)
        snapshot = {"false_positive_count": 40, "match_count": 100}
        event = evaluate_trigger(
            trigger, snapshot, "RULE-001",
            _utcnow() - timedelta(days=30), _utcnow(), sample_size=10,
        )
        assert event is None

    def test_correctness_degradation(self):
        trigger = _make_trigger(
            trigger_type="CORRECTNESS_DEGRADATION",
            target_metric="average_correctness_score",
            threshold_operator="lt",
            threshold_value=0.50,
        )
        snapshot = {"average_correctness_score": 0.35, "match_count": 20}
        event = evaluate_trigger(
            trigger, snapshot, "RULE-002",
            _utcnow() - timedelta(days=30), _utcnow(), sample_size=20,
        )
        assert event is not None
        assert event.metric_value == pytest.approx(0.35)


class TestEvaluateTriggersBatch:
    def test_batch_multiple_rules(self):
        trigger = _make_trigger()
        snapshots = {
            "RULE-001": {"false_positive_count": 40, "match_count": 100},
            "RULE-002": {"false_positive_count": 5, "match_count": 100},
        }
        events = evaluate_triggers_batch(
            [trigger], snapshots,
            _utcnow() - timedelta(days=30), _utcnow(),
        )
        assert len(events) == 1
        assert events[0].rule_id == "RULE-001"

    def test_batch_multiple_triggers(self):
        trigger1 = _make_trigger(trigger_id="CTRIG-1", target_metric="false_positive_rate", threshold_value=0.30)
        trigger2 = _make_trigger(trigger_id="CTRIG-2", target_metric="average_correctness_score",
                                  threshold_operator="lt", threshold_value=0.50,
                                  trigger_type="CORRECTNESS_DEGRADATION")
        snapshots = {
            "RULE-001": {"false_positive_count": 40, "match_count": 100, "average_correctness_score": 0.3},
        }
        events = evaluate_triggers_batch(
            [trigger1, trigger2], snapshots,
            _utcnow() - timedelta(days=30), _utcnow(),
        )
        assert len(events) == 2

    def test_batch_empty_snapshots(self):
        trigger = _make_trigger()
        events = evaluate_triggers_batch(
            [trigger], {},
            _utcnow() - timedelta(days=30), _utcnow(),
        )
        assert events == []

    def test_batch_empty_triggers(self):
        snapshots = {"RULE-001": {"false_positive_count": 40, "match_count": 100}}
        events = evaluate_triggers_batch(
            [], snapshots,
            _utcnow() - timedelta(days=30), _utcnow(),
        )
        assert events == []
