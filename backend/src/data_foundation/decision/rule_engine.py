"""
P1 Decision Layer — Rule Evaluation Engine
=============================================

Evaluates decision rules against current data state.
Produces DecisionProposals when rule conditions are met.

This is a deterministic, auditable rule engine — not ML.
Every evaluation is traceable: input data → condition check → output proposal.

Architecture Layer: Data → Decision (Layer 1 → Layer 4)
Owner: Decision Intelligence Team
Consumers: Decision brain, alert system, governance dashboard

Design:
  - Rules are loaded from decision_rules dataset
  - Data state is assembled from P1 signal/indicator datasets
  - Conditions are evaluated left-to-right with AND/OR logic
  - Cooldown enforcement prevents trigger storms
  - All evaluations are logged regardless of outcome
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from src.data_foundation.schemas.enums import (
    DecisionAction,
    DecisionStatus,
    RiskLevel,
    GCCCountry,
)
from src.data_foundation.schemas.decision_rules import DecisionRule, RuleCondition

__all__ = [
    "DataState",
    "RuleEvaluationResult",
    "RuleEngineOutput",
    "evaluate_rule",
    "evaluate_all_rules",
]


class DataState(BaseModel):
    """Snapshot of current data state for rule evaluation.

    Keys are dot-notation field paths matching rule conditions.
    Values are the current values from P1 datasets.

    Example:
        DataState(values={
            "oil_energy_signals.change_pct": -35.0,
            "banking_sector_profiles.npl_ratio_pct": 6.2,
            "banking_sector_profiles.is_dsib": True,
            "event_signals.severity_score": 0.72,
            "fx_signals.deviation_from_peg_bps": 55,
        })
    """
    values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current data values keyed by dot-notation field paths.",
    )
    snapshot_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    source_record_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of field path → source record ID for audit trail.",
    )


class RuleEvaluationResult(BaseModel):
    """Result of evaluating a single rule against current data state."""
    rule_id: str
    rule_version: int
    triggered: bool
    conditions_met: List[bool] = Field(
        default_factory=list,
        description="Result of each condition in order.",
    )
    condition_details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-condition evaluation details for audit.",
    )
    action: Optional[DecisionAction] = None
    risk_level: Optional[RiskLevel] = None
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    reason: str = Field(
        default="",
        description="Human-readable explanation.",
    )
    cooldown_blocked: bool = Field(
        default=False,
        description="True if rule matched but was blocked by cooldown.",
    )


class RuleEngineOutput(BaseModel):
    """Complete output from evaluating all rules against current data state."""
    evaluations: List[RuleEvaluationResult] = Field(default_factory=list)
    triggered_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    blocked_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    total_evaluated: int = 0
    total_triggered: int = 0
    total_blocked: int = 0
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    data_state_hash: str = Field(
        default="",
        description="SHA-256 of the data state for audit reproducibility.",
    )


def _evaluate_condition(condition: RuleCondition, data_state: DataState) -> Tuple[bool, Dict[str, Any]]:
    """Evaluate a single rule condition against the data state.

    Returns (passed: bool, details: dict).
    """
    field = condition.field
    actual = data_state.values.get(field)
    threshold = condition.threshold
    op = condition.operator

    detail = {
        "field": field,
        "operator": op,
        "threshold": threshold,
        "actual_value": actual,
    }

    if actual is None:
        detail["reason"] = f"Field '{field}' not present in data state."
        return False, detail

    try:
        if op == "gt":
            result = float(actual) > float(threshold)
        elif op == "gte":
            result = float(actual) >= float(threshold)
        elif op == "lt":
            result = float(actual) < float(threshold)
        elif op == "lte":
            result = float(actual) <= float(threshold)
        elif op == "eq":
            result = actual == threshold
        elif op == "neq":
            result = actual != threshold
        elif op == "in":
            result = actual in threshold if isinstance(threshold, list) else str(actual) in str(threshold)
        elif op == "not_in":
            result = actual not in threshold if isinstance(threshold, list) else str(actual) not in str(threshold)
        elif op == "between":
            if isinstance(threshold, list) and len(threshold) == 2:
                result = float(threshold[0]) <= float(actual) <= float(threshold[1])
            else:
                result = False
        elif op == "exceeds_threshold":
            result = abs(float(actual)) > abs(float(threshold))
        else:
            detail["reason"] = f"Unknown operator: {op}"
            return False, detail

        detail["result"] = result
        return result, detail

    except (ValueError, TypeError) as e:
        detail["reason"] = f"Evaluation error: {e}"
        return False, detail


def evaluate_rule(
    rule: DecisionRule,
    data_state: DataState,
    last_trigger_times: Optional[Dict[str, datetime]] = None,
) -> RuleEvaluationResult:
    """Evaluate a single decision rule against the current data state.

    Args:
        rule: The decision rule to evaluate
        data_state: Current data snapshot
        last_trigger_times: Map of rule_id → last trigger time for cooldown

    Returns:
        RuleEvaluationResult with trigger status and audit details
    """
    if not rule.is_active:
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            triggered=False,
            reason="Rule is inactive.",
        )

    # Check expiry
    if rule.expiry_date and datetime.now(timezone.utc) > rule.expiry_date:
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            triggered=False,
            reason="Rule has expired.",
        )

    # Evaluate conditions
    conditions_met: List[bool] = []
    condition_details: List[Dict[str, Any]] = []

    for condition in rule.conditions:
        met, detail = _evaluate_condition(condition, data_state)
        conditions_met.append(met)
        condition_details.append(detail)

    # Apply logic (AND/OR)
    if rule.condition_logic == "OR":
        all_conditions_satisfied = any(conditions_met)
    else:  # AND (default)
        all_conditions_satisfied = all(conditions_met)

    if not all_conditions_satisfied:
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            triggered=False,
            conditions_met=conditions_met,
            condition_details=condition_details,
            reason="Not all conditions met.",
        )

    # Check cooldown
    if last_trigger_times:
        last_trigger = last_trigger_times.get(rule.rule_id)
        if last_trigger:
            cooldown_until = last_trigger + timedelta(minutes=rule.cooldown_minutes)
            if datetime.now(timezone.utc) < cooldown_until:
                return RuleEvaluationResult(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    triggered=True,
                    cooldown_blocked=True,
                    conditions_met=conditions_met,
                    condition_details=condition_details,
                    action=rule.action,
                    risk_level=rule.escalation_level,
                    reason=f"Blocked by cooldown until {cooldown_until.isoformat()}.",
                )

    return RuleEvaluationResult(
        rule_id=rule.rule_id,
        rule_version=rule.version,
        triggered=True,
        conditions_met=conditions_met,
        condition_details=condition_details,
        action=rule.action,
        risk_level=rule.escalation_level,
        reason=f"All conditions met. Action: {rule.action.value}.",
    )


def evaluate_all_rules(
    rules: List[DecisionRule],
    data_state: DataState,
    last_trigger_times: Optional[Dict[str, datetime]] = None,
) -> RuleEngineOutput:
    """Evaluate all active rules against the current data state.

    Returns a complete RuleEngineOutput with triggered, blocked, and inactive rules.
    """
    evaluations: List[RuleEvaluationResult] = []
    triggered: List[RuleEvaluationResult] = []
    blocked: List[RuleEvaluationResult] = []

    for rule in rules:
        result = evaluate_rule(rule, data_state, last_trigger_times)
        evaluations.append(result)

        if result.triggered and not result.cooldown_blocked:
            triggered.append(result)
        elif result.cooldown_blocked:
            blocked.append(result)

    # Compute data state hash for audit reproducibility
    state_canonical = json.dumps(data_state.values, sort_keys=True, default=str)
    state_hash = hashlib.sha256(state_canonical.encode("utf-8")).hexdigest()

    return RuleEngineOutput(
        evaluations=evaluations,
        triggered_rules=triggered,
        blocked_rules=blocked,
        total_evaluated=len(evaluations),
        total_triggered=len(triggered),
        total_blocked=len(blocked),
        data_state_hash=state_hash,
    )
