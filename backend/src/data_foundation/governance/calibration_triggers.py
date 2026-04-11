"""Calibration Trigger Engine — deterministic threshold evaluation.

Evaluates CalibrationTrigger definitions against RulePerformanceSnapshot
metrics. NOT ML — purely threshold-based deterministic checks.

Supports: gt, lt, gte, lte, exceeds_threshold operators.
Enforces minimum sample size before a trigger can fire.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.data_foundation.governance.schemas import (
    CalibrationEvent,
    CalibrationTrigger,
)

__all__ = [
    "extract_metric",
    "evaluate_threshold",
    "evaluate_trigger",
    "evaluate_triggers_batch",
]


def _gen_id() -> str:
    return f"CEVT-{str(uuid4())[:12]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Metric Extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_metric(
    snapshot: Dict[str, Any],
    metric_name: str,
) -> float | None:
    """Extract a metric value from a performance snapshot dict.

    Supported metrics:
      - average_correctness_score
      - average_confidence_gap
      - false_positive_count / false_positive_rate
      - false_negative_count / false_negative_rate
      - match_count
      - confirmed_correct_count
    """
    if metric_name in snapshot and snapshot[metric_name] is not None:
        try:
            return float(snapshot[metric_name])
        except (TypeError, ValueError):
            return None

    # Computed rates
    match_count = snapshot.get("match_count", 0)
    if match_count == 0:
        return None

    if metric_name == "false_positive_rate":
        fp = snapshot.get("false_positive_count", 0)
        return float(fp) / float(match_count)

    if metric_name == "false_negative_rate":
        fn = snapshot.get("false_negative_count", 0)
        return float(fn) / float(match_count)

    if metric_name == "accuracy_rate":
        correct = snapshot.get("confirmed_correct_count", 0)
        return float(correct) / float(match_count)

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Threshold Evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_threshold(
    metric_value: float,
    operator: str,
    threshold: float,
) -> bool:
    """Evaluate a single threshold condition.

    Args:
        metric_value: Current metric value.
        operator: One of gt, lt, gte, lte, exceeds_threshold.
        threshold: Threshold value to compare against.

    Returns:
        True if the condition is met (trigger should fire).
    """
    if operator == "gt":
        return metric_value > threshold
    elif operator == "lt":
        return metric_value < threshold
    elif operator == "gte":
        return metric_value >= threshold
    elif operator == "lte":
        return metric_value <= threshold
    elif operator == "exceeds_threshold":
        return abs(metric_value) > abs(threshold)
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Trigger Evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_trigger(
    trigger: CalibrationTrigger,
    snapshot: Dict[str, Any],
    rule_id: str,
    lookback_start: datetime,
    lookback_end: datetime,
    sample_size: int,
    spec_id: str | None = None,
) -> CalibrationEvent | None:
    """Evaluate a single calibration trigger against a performance snapshot.

    Returns a CalibrationEvent if the trigger fires, else None.
    """
    if not trigger.is_active:
        return None

    # Minimum sample size check
    if sample_size < trigger.min_evaluations:
        return None

    # Extract the target metric
    metric_value = extract_metric(snapshot, trigger.target_metric)
    if metric_value is None:
        return None

    # Evaluate threshold
    fired = evaluate_threshold(metric_value, trigger.threshold_operator, trigger.threshold_value)
    if not fired:
        return None

    now = datetime.now(timezone.utc)
    return CalibrationEvent(
        event_id=_gen_id(),
        trigger_id=trigger.trigger_id,
        rule_id=rule_id,
        spec_id=spec_id,
        metric_value=metric_value,
        threshold_value=trigger.threshold_value,
        lookback_start=lookback_start,
        lookback_end=lookback_end,
        sample_size=sample_size,
        status="TRIGGERED",
        triggered_at=now,
    )


def evaluate_triggers_batch(
    triggers: List[CalibrationTrigger],
    snapshots: Dict[str, Dict[str, Any]],
    lookback_start: datetime,
    lookback_end: datetime,
) -> List[CalibrationEvent]:
    """Evaluate multiple triggers against multiple rule snapshots.

    Args:
        triggers: List of active CalibrationTrigger definitions.
        snapshots: {rule_id: snapshot_dict} map.
        lookback_start: Start of the evaluation window.
        lookback_end: End of the evaluation window.

    Returns:
        List of fired CalibrationEvents.
    """
    events: List[CalibrationEvent] = []

    for rule_id, snapshot in snapshots.items():
        sample_size = snapshot.get("match_count", 0)
        for trigger in triggers:
            event = evaluate_trigger(
                trigger=trigger,
                snapshot=snapshot,
                rule_id=rule_id,
                lookback_start=lookback_start,
                lookback_end=lookback_end,
                sample_size=sample_size,
            )
            if event is not None:
                events.append(event)

    return events
