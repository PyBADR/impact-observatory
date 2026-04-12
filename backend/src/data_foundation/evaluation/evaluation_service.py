"""
Evaluation Layer — Evaluation Service
=======================================

Orchestrates the expected → actual → evaluation pipeline.
Stateless service functions — DB interaction happens in callers via repositories.

Functions:
  create_expected_from_trigger — Build ExpectedOutcome from a rule evaluation result
  record_actual_observation    — Build ActualOutcome from post-hoc data
  evaluate_decision_pair       — Compare expected vs actual, produce DecisionEvaluation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.data_foundation.schemas.enums import (
    DecisionAction,
    RiskLevel,
    SignalSeverity,
)
from src.data_foundation.decision.rule_engine import (
    DataState,
    RuleEvaluationResult,
)
from src.data_foundation.schemas.decision_rules import DecisionRule

from .schemas import (
    ExpectedOutcome,
    ActualOutcome,
    DecisionEvaluation,
    ObservationSource,
    ObservationCompleteness,
)
from .scoring import evaluate_decision

__all__ = [
    "create_expected_from_trigger",
    "record_actual_observation",
    "evaluate_decision_pair",
]


def create_expected_from_trigger(
    decision_log_id: str,
    rule: DecisionRule,
    evaluation_result: RuleEvaluationResult,
    data_state: DataState,
    spec_id: Optional[str] = None,
    expected_affected_entity_ids: Optional[List[str]] = None,
    expected_affected_sectors: Optional[List[str]] = None,
    expected_financial_impact: Optional[float] = None,
    expected_mitigation_effect: Optional[str] = None,
) -> ExpectedOutcome:
    """Create an ExpectedOutcome from a triggered rule evaluation.

    Called immediately after a rule triggers and a decision log is created.
    Captures the system's prediction of what will happen.

    Args:
        decision_log_id: The decision log entry this expectation belongs to.
        rule: The DecisionRule that triggered.
        evaluation_result: The RuleEvaluationResult from the engine.
        data_state: The DataState snapshot at trigger time.
        spec_id: Optional RuleSpec ID for traceability.
        expected_affected_entity_ids: Entities expected to be affected.
        expected_affected_sectors: Sectors expected to be affected.
        expected_financial_impact: Predicted financial impact (millions).
        expected_mitigation_effect: What the proposed action should achieve.

    Returns:
        ExpectedOutcome with all hashes computed.
    """
    # Derive severity from risk level (risk level → severity mapping)
    risk_to_severity = {
        RiskLevel.NOMINAL: SignalSeverity.NOMINAL,
        RiskLevel.LOW: SignalSeverity.LOW,
        RiskLevel.GUARDED: SignalSeverity.GUARDED,
        RiskLevel.ELEVATED: SignalSeverity.ELEVATED,
        RiskLevel.HIGH: SignalSeverity.HIGH,
        RiskLevel.SEVERE: SignalSeverity.SEVERE,
        RiskLevel.CRITICAL: SignalSeverity.SEVERE,  # CRITICAL maps to SEVERE (no CRITICAL in severity)
    }

    expected_severity = risk_to_severity.get(
        rule.escalation_level,
        SignalSeverity.ELEVATED,
    )

    # Extract time_to_act from action_params if present
    time_to_act = None
    if rule.action_params:
        time_to_act = rule.action_params.get("_time_to_act_hours")

    # Extract countries from rule scope
    countries = [c.value if hasattr(c, "value") else str(c) for c in rule.applicable_countries]

    expected = ExpectedOutcome(
        decision_log_id=decision_log_id,
        rule_id=rule.rule_id,
        spec_id=spec_id or rule.action_params.get("_spec_id") if rule.action_params else None,
        expected_severity=expected_severity,
        expected_risk_level=rule.escalation_level,
        expected_affected_entity_ids=expected_affected_entity_ids or [],
        expected_affected_sectors=[
            s.value if hasattr(s, "value") else str(s)
            for s in (expected_affected_sectors or rule.applicable_sectors)
        ],
        expected_affected_countries=countries,
        expected_financial_impact=expected_financial_impact,
        expected_mitigation_effect=expected_mitigation_effect or f"Action: {rule.action.value}",
        expected_resolution_hours=time_to_act,
        data_state_snapshot=data_state.values,
    )
    expected.compute_hashes()
    return expected


def record_actual_observation(
    expected_outcome_id: str,
    decision_log_id: str,
    actual_severity: Optional[SignalSeverity] = None,
    actual_risk_level: Optional[RiskLevel] = None,
    actual_affected_entity_ids: Optional[List[str]] = None,
    actual_affected_sectors: Optional[List[str]] = None,
    actual_affected_countries: Optional[List[str]] = None,
    actual_financial_impact: Optional[float] = None,
    actual_resolution_hours: Optional[float] = None,
    observation_source: str = ObservationSource.ANALYST_REVIEW,
    observation_completeness: str = ObservationCompleteness.PRELIMINARY,
    observation_notes: Optional[str] = None,
    data_sources_used: Optional[List[str]] = None,
) -> ActualOutcome:
    """Record an actual observation against an expected outcome.

    Can be called multiple times as more data becomes available
    (PRELIMINARY → PARTIAL → COMPLETE).

    Args:
        expected_outcome_id: Which expectation this observation resolves.
        decision_log_id: Redundant FK for fast joins.
        actual_*: Observed values. All optional for partial observations.
        observation_source: How the outcome was determined.
        observation_completeness: COMPLETE, PARTIAL, or PRELIMINARY.
        observation_notes: Analyst-provided notes.
        data_sources_used: Dataset IDs that confirmed the outcome.

    Returns:
        ActualOutcome with hash computed.
    """
    actual = ActualOutcome(
        expected_outcome_id=expected_outcome_id,
        decision_log_id=decision_log_id,
        actual_severity=actual_severity,
        actual_risk_level=actual_risk_level,
        actual_affected_entity_ids=actual_affected_entity_ids or [],
        actual_affected_sectors=actual_affected_sectors or [],
        actual_affected_countries=actual_affected_countries or [],
        actual_financial_impact=actual_financial_impact,
        actual_resolution_hours=actual_resolution_hours,
        observation_source=observation_source,
        observation_completeness=observation_completeness,
        observation_notes=observation_notes,
        data_sources_used=data_sources_used or [],
    )
    actual.compute_hash()
    return actual


def evaluate_decision_pair(
    expected: ExpectedOutcome,
    actual: ActualOutcome,
    rule_confidence: float = 0.5,
) -> DecisionEvaluation:
    """Compare expected vs actual and produce a DecisionEvaluation.

    Delegates to scoring.evaluate_decision for the actual computation.
    This function exists as the public API for the evaluation pipeline.

    Args:
        expected: The prediction made at decision time.
        actual: The observed outcome (should be COMPLETE for final eval).
        rule_confidence: The rule's declared confidence score [0-1].

    Returns:
        DecisionEvaluation with all scores and hashes computed.
    """
    return evaluate_decision(expected, actual, rule_confidence)
