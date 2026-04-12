"""
Calibration Trigger Engine
============================

Evaluates RulePerformanceSnapshot metrics against CalibrationTrigger
thresholds. Purely deterministic — no ML, no side effects.

When a trigger fires, it produces a CalibrationEvent record.
The caller is responsible for persisting the event and appending
to the governance audit chain.

Supported operators: gt, lt, gte, lte, exceeds_threshold (alias for gt).
Supported metrics: any numeric field on RulePerformanceSnapshot.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    CalibrationTrigger,
    CalibrationEvent,
    CalibrationTriggerType,
    CalibrationEventStatus,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Operator evaluation — pure functions
# ═══════════════════════════════════════════════════════════════════════════════


def _evaluate_operator(
    operator: str,
    actual_value: float,
    threshold_value: float,
) -> bool:
    """Evaluate a threshold comparison. Returns True if the trigger fires."""
    if operator == "gt" or operator == "exceeds_threshold":
        return actual_value > threshold_value
    elif operator == "lt":
        return actual_value < threshold_value
    elif operator == "gte":
        return actual_value >= threshold_value
    elif operator == "lte":
        return actual_value <= threshold_value
    else:
        return False  # Unknown operator = never fires (safe default)


def _extract_metric(
    snapshot: Any,
    target_metric: str,
) -> Optional[float]:
    """Extract a numeric metric from a RulePerformanceSnapshot.

    Supports both attribute access and dict access.
    """
    if isinstance(snapshot, dict):
        value = snapshot.get(target_metric)
    else:
        value = getattr(snapshot, target_metric, None)

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Single trigger evaluation
# ═══════════════════════════════════════════════════════════════════════════════


def evaluate_trigger(
    trigger: CalibrationTrigger,
    snapshot: Any,
    rule_id: str,
    spec_id: Optional[str] = None,
    lookback_start: Optional[datetime] = None,
    lookback_end: Optional[datetime] = None,
) -> Optional[CalibrationEvent]:
    """Evaluate a single trigger against a performance snapshot.

    Returns CalibrationEvent if the trigger fires, None otherwise.

    Pure function. No DB. No side effects.

    Args:
        trigger: The calibration trigger definition.
        snapshot: A RulePerformanceSnapshot (or dict with the same keys).
        rule_id: The rule being evaluated.
        spec_id: Optional spec ID for traceability.
        lookback_start: Start of the evaluation window.
        lookback_end: End of the evaluation window.
    """
    if not trigger.is_active:
        return None

    # Extract metric
    metric_value = _extract_metric(snapshot, trigger.target_metric)
    if metric_value is None:
        return None  # Metric not available — cannot evaluate

    # Check minimum sample size
    total_evaluations = _extract_metric(snapshot, "total_evaluations")
    if total_evaluations is not None and total_evaluations < trigger.min_evaluations:
        return None  # Insufficient data — don't fire

    # Evaluate threshold
    if not _evaluate_operator(trigger.threshold_operator, metric_value, trigger.threshold_value):
        return None  # Threshold not breached

    # Trigger fires — build event
    now = datetime.now(timezone.utc)
    event = CalibrationEvent(
        trigger_id=trigger.trigger_id,
        rule_id=rule_id,
        spec_id=spec_id,
        metric_value=metric_value,
        threshold_value=trigger.threshold_value,
        lookback_start=lookback_start or now,
        lookback_end=lookback_end or now,
        sample_size=int(total_evaluations or 0),
        status=CalibrationEventStatus.TRIGGERED,
    )
    event.compute_hash()
    return event


# ═══════════════════════════════════════════════════════════════════════════════
# Batch evaluation
# ═══════════════════════════════════════════════════════════════════════════════


def evaluate_all_triggers(
    triggers: List[CalibrationTrigger],
    snapshot: Any,
    rule_id: str,
    spec_id: Optional[str] = None,
    lookback_start: Optional[datetime] = None,
    lookback_end: Optional[datetime] = None,
) -> List[CalibrationEvent]:
    """Evaluate all triggers against a single performance snapshot.

    Returns list of CalibrationEvent for each trigger that fires.
    """
    events: List[CalibrationEvent] = []
    for trigger in triggers:
        event = evaluate_trigger(
            trigger=trigger,
            snapshot=snapshot,
            rule_id=rule_id,
            spec_id=spec_id,
            lookback_start=lookback_start,
            lookback_end=lookback_end,
        )
        if event is not None:
            events.append(event)
    return events


def evaluate_triggers_for_all_rules(
    triggers: List[CalibrationTrigger],
    snapshots_by_rule: Dict[str, Any],
    spec_ids_by_rule: Optional[Dict[str, str]] = None,
    lookback_start: Optional[datetime] = None,
    lookback_end: Optional[datetime] = None,
) -> Dict[str, List[CalibrationEvent]]:
    """Evaluate all triggers against all rule performance snapshots.

    Returns dict: rule_id → list of fired CalibrationEvents.
    """
    spec_map = spec_ids_by_rule or {}
    result: Dict[str, List[CalibrationEvent]] = {}

    for rule_id, snapshot in snapshots_by_rule.items():
        events = evaluate_all_triggers(
            triggers=triggers,
            snapshot=snapshot,
            rule_id=rule_id,
            spec_id=spec_map.get(rule_id),
            lookback_start=lookback_start,
            lookback_end=lookback_end,
        )
        if events:
            result[rule_id] = events

    return result
