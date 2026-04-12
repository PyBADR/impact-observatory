"""
Calibration Trigger Engine — Tests
=====================================

Validates:
  1. Single trigger evaluation fires/doesn't fire
  2. Operator evaluation (gt, lt, gte, lte, exceeds_threshold)
  3. Minimum evaluation count enforcement
  4. Inactive trigger skipping
  5. Missing metric handling
  6. Batch evaluation across triggers and rules
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

from src.data_foundation.governance.schemas import (
    CalibrationTrigger,
    CalibrationEvent,
    CalibrationTriggerType,
    CalibrationEventStatus,
)
from src.data_foundation.governance.calibration_triggers import (
    evaluate_trigger,
    evaluate_all_triggers,
    evaluate_triggers_for_all_rules,
    _evaluate_operator,
    _extract_metric,
)


NOW = datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc)
START = NOW - timedelta(days=30)


def _make_trigger(**kwargs):
    defaults = dict(
        trigger_name="Test Trigger",
        trigger_type=CalibrationTriggerType.CONFIDENCE_DRIFT,
        target_metric="avg_confidence_gap",
        threshold_operator="gt",
        threshold_value=0.25,
        min_evaluations=5,
        authored_by="admin",
    )
    defaults.update(kwargs)
    return CalibrationTrigger(**defaults)


def _make_snapshot(**kwargs):
    defaults = dict(
        avg_confidence_gap=0.3,
        avg_correctness_score=0.7,
        false_positive_count=2,
        false_negative_count=1,
        total_evaluations=10,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# Operator evaluation
# ═══════════════════════════════════════════════════════════════════════════════


class TestOperatorEvaluation:

    def test_gt_fires(self):
        assert _evaluate_operator("gt", 0.3, 0.25) is True

    def test_gt_no_fire(self):
        assert _evaluate_operator("gt", 0.2, 0.25) is False

    def test_gt_equal_no_fire(self):
        assert _evaluate_operator("gt", 0.25, 0.25) is False

    def test_lt_fires(self):
        assert _evaluate_operator("lt", 0.5, 0.7) is True

    def test_lt_no_fire(self):
        assert _evaluate_operator("lt", 0.8, 0.7) is False

    def test_gte_fires_equal(self):
        assert _evaluate_operator("gte", 0.25, 0.25) is True

    def test_lte_fires_equal(self):
        assert _evaluate_operator("lte", 0.25, 0.25) is True

    def test_exceeds_threshold_alias(self):
        assert _evaluate_operator("exceeds_threshold", 0.3, 0.25) is True
        assert _evaluate_operator("exceeds_threshold", 0.2, 0.25) is False

    def test_unknown_operator_never_fires(self):
        assert _evaluate_operator("invalid", 999.0, 0.0) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Metric extraction
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractMetric:

    def test_from_object(self):
        snap = _make_snapshot(avg_confidence_gap=0.35)
        assert _extract_metric(snap, "avg_confidence_gap") == 0.35

    def test_from_dict(self):
        snap = {"avg_confidence_gap": 0.35, "total_evaluations": 10}
        assert _extract_metric(snap, "avg_confidence_gap") == 0.35

    def test_missing_attribute(self):
        snap = _make_snapshot()
        assert _extract_metric(snap, "nonexistent_metric") is None

    def test_missing_dict_key(self):
        snap = {"avg_confidence_gap": 0.35}
        assert _extract_metric(snap, "nonexistent") is None


# ═══════════════════════════════════════════════════════════════════════════════
# Single trigger evaluation
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvaluateTrigger:

    def test_fires_when_threshold_breached(self):
        trigger = _make_trigger(threshold_value=0.25)
        snapshot = _make_snapshot(avg_confidence_gap=0.30)
        event = evaluate_trigger(trigger, snapshot, "RULE-1")
        assert event is not None
        assert isinstance(event, CalibrationEvent)
        assert event.metric_value == 0.30
        assert event.threshold_value == 0.25
        assert event.status == CalibrationEventStatus.TRIGGERED

    def test_no_fire_when_below_threshold(self):
        trigger = _make_trigger(threshold_value=0.5)
        snapshot = _make_snapshot(avg_confidence_gap=0.2)
        event = evaluate_trigger(trigger, snapshot, "RULE-1")
        assert event is None

    def test_inactive_trigger_skipped(self):
        trigger = _make_trigger(is_active=False)
        snapshot = _make_snapshot(avg_confidence_gap=999.0)
        event = evaluate_trigger(trigger, snapshot, "RULE-1")
        assert event is None

    def test_insufficient_evaluations_skipped(self):
        trigger = _make_trigger(min_evaluations=20)
        snapshot = _make_snapshot(total_evaluations=5)
        event = evaluate_trigger(trigger, snapshot, "RULE-1")
        assert event is None

    def test_missing_metric_skipped(self):
        trigger = _make_trigger(target_metric="nonexistent_metric")
        snapshot = _make_snapshot()
        event = evaluate_trigger(trigger, snapshot, "RULE-1")
        assert event is None

    def test_lt_operator_fires(self):
        trigger = _make_trigger(
            trigger_type=CalibrationTriggerType.CORRECTNESS_DEGRADATION,
            target_metric="avg_correctness_score",
            threshold_operator="lt",
            threshold_value=0.6,
        )
        snapshot = _make_snapshot(avg_correctness_score=0.5)
        event = evaluate_trigger(trigger, snapshot, "RULE-1")
        assert event is not None

    def test_event_has_correct_metadata(self):
        trigger = _make_trigger()
        snapshot = _make_snapshot(avg_confidence_gap=0.4, total_evaluations=15)
        event = evaluate_trigger(
            trigger, snapshot, "RULE-OIL-1",
            spec_id="SPEC-OIL-v1",
            lookback_start=START,
            lookback_end=NOW,
        )
        assert event.rule_id == "RULE-OIL-1"
        assert event.spec_id == "SPEC-OIL-v1"
        assert event.sample_size == 15
        assert event.provenance_hash != ""


# ═══════════════════════════════════════════════════════════════════════════════
# Batch evaluation
# ═══════════════════════════════════════════════════════════════════════════════


class TestBatchEvaluation:

    def test_evaluate_all_triggers_multiple_fire(self):
        t1 = _make_trigger(trigger_name="T1", target_metric="avg_confidence_gap", threshold_value=0.25)
        t2 = _make_trigger(
            trigger_name="T2",
            trigger_type=CalibrationTriggerType.FALSE_POSITIVE_SPIKE,
            target_metric="false_positive_count",
            threshold_value=1.0,
        )
        snapshot = _make_snapshot(avg_confidence_gap=0.3, false_positive_count=5)
        events = evaluate_all_triggers([t1, t2], snapshot, "RULE-1")
        assert len(events) == 2

    def test_evaluate_all_triggers_none_fire(self):
        t1 = _make_trigger(threshold_value=0.9)
        snapshot = _make_snapshot(avg_confidence_gap=0.1)
        events = evaluate_all_triggers([t1], snapshot, "RULE-1")
        assert len(events) == 0

    def test_evaluate_for_all_rules(self):
        trigger = _make_trigger(threshold_value=0.2)
        snapshots = {
            "RULE-A": _make_snapshot(avg_confidence_gap=0.3),
            "RULE-B": _make_snapshot(avg_confidence_gap=0.1),  # Below threshold
        }
        results = evaluate_triggers_for_all_rules(
            [trigger], snapshots,
        )
        assert "RULE-A" in results
        assert "RULE-B" not in results
        assert len(results["RULE-A"]) == 1
