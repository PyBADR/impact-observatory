"""Outcome Tracking, Decision Evaluation & Replay — Pydantic v2 schemas.

Seven schema groups aligned 1:1 with ORM models in outcome_tables.py:

  DecisionExpectedOutcome  — predicted outcome from a rule/decision
  DecisionActualOutcome    — observed real-world outcome
  DecisionEvaluation       — deterministic scoring result
  AnalystFeedbackRecord    — human analyst override/confirmation
  ReplayRun                — replay session metadata
  ReplayRunResult          — per-event replay output
  RulePerformanceSnapshot  — aggregated rule accuracy over a window

All inherit FoundationModel (schema_version, tenant_id, timestamps, provenance_hash).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from src.data_foundation.schemas.base import FoundationModel

__all__ = [
    "DecisionExpectedOutcome",
    "DecisionActualOutcome",
    "DecisionEvaluation",
    "AnalystFeedbackRecord",
    "ReplayRun",
    "ReplayRunResult",
    "RulePerformanceSnapshot",
    # Request/response helpers
    "CreateExpectedOutcomeRequest",
    "CreateActualOutcomeRequest",
    "RunEvaluationRequest",
    "CreateFeedbackRequest",
    "RunReplayRequest",
    "SnapshotRequest",
    "EvaluationScores",
    "ReplayReport",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Valid enum-like values (stored as VARCHAR, validated here)
# ═══════════════════════════════════════════════════════════════════════════════

VALID_SEVERITIES = {"NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"}
VALID_DIRECTIONS = {"DETERIORATE", "IMPROVE", "STABLE"}
VALID_VERDICTS = {"CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "INCONCLUSIVE"}
VALID_FAILURE_MODES = {
    "MISSED_SIGNAL", "WRONG_SEVERITY", "WRONG_ENTITY", "TIMING_OFF",
    "RULE_GAP", "FALSE_POSITIVE", "OTHER",
}
VALID_EVALUATION_STATUSES = {"PENDING", "COMPLETED", "OVERRIDDEN"}
VALID_REPLAY_STATUSES = {"PENDING", "RUNNING", "COMPLETED", "FAILED"}


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionExpectedOutcome(FoundationModel):
    """What a rule/decision predicted would happen."""

    expected_outcome_id: str = Field(..., description="Unique expected outcome ID.")
    decision_log_id: str = Field(..., description="FK to df_decision_logs.log_id.")
    event_id: Optional[str] = Field(default=None, description="FK to df_event_signals.event_id.")
    rule_id: str = Field(..., description="FK to df_decision_rules.rule_id.")
    expected_entities: List[str] = Field(default_factory=list, description="Entity IDs expected to be affected.")
    expected_severity: str = Field(..., description="Predicted severity level.")
    expected_direction: str = Field(..., description="DETERIORATE | IMPROVE | STABLE.")
    expected_time_horizon_hours: Optional[float] = Field(default=None, ge=0.0, description="Expected time to materialization.")
    expected_mitigation_effect: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Expected mitigation (0=none, 1=full).")
    expected_notes: Optional[str] = Field(default=None)
    confidence_at_decision_time: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("expected_severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"expected_severity must be one of {VALID_SEVERITIES}, got '{v}'")
        return v

    @field_validator("expected_direction")
    @classmethod
    def _check_direction(cls, v: str) -> str:
        if v not in VALID_DIRECTIONS:
            raise ValueError(f"expected_direction must be one of {VALID_DIRECTIONS}, got '{v}'")
        return v


class DecisionActualOutcome(FoundationModel):
    """What was actually observed post-decision."""

    actual_outcome_id: str = Field(..., description="Unique actual outcome ID.")
    expected_outcome_id: str = Field(..., description="FK to expected outcome.")
    event_id: Optional[str] = Field(default=None)
    observed_entities: List[str] = Field(default_factory=list)
    observed_severity: str = Field(...)
    observed_direction: str = Field(...)
    observed_time_to_materialization_hours: Optional[float] = Field(default=None, ge=0.0)
    actual_effect_value: Optional[float] = Field(default=None)
    observation_source: Optional[str] = Field(default=None)
    observation_notes: Optional[str] = Field(default=None)
    observed_at: datetime = Field(...)

    @field_validator("observed_severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"observed_severity must be one of {VALID_SEVERITIES}, got '{v}'")
        return v

    @field_validator("observed_direction")
    @classmethod
    def _check_direction(cls, v: str) -> str:
        if v not in VALID_DIRECTIONS:
            raise ValueError(f"observed_direction must be one of {VALID_DIRECTIONS}, got '{v}'")
        return v


class EvaluationScores(FoundationModel):
    """Deterministic evaluation scores — output from the evaluation service."""
    correctness_score: float = Field(..., ge=0.0, le=1.0)
    severity_alignment_score: float = Field(..., ge=0.0, le=1.0)
    entity_alignment_score: float = Field(..., ge=0.0, le=1.0)
    timing_alignment_score: float = Field(..., ge=0.0, le=1.0)
    confidence_gap: float = Field(...)  # Can be negative (overconfident) or positive (underconfident)
    explainability_completeness_score: float = Field(..., ge=0.0, le=1.0)


class DecisionEvaluation(FoundationModel):
    """Deterministic scoring of decision quality."""

    evaluation_id: str = Field(...)
    decision_log_id: str = Field(...)
    expected_outcome_id: str = Field(...)
    actual_outcome_id: str = Field(...)
    # Scores
    correctness_score: float = Field(..., ge=0.0, le=1.0)
    severity_alignment_score: float = Field(..., ge=0.0, le=1.0)
    entity_alignment_score: float = Field(..., ge=0.0, le=1.0)
    timing_alignment_score: float = Field(..., ge=0.0, le=1.0)
    confidence_gap: float = Field(...)
    explainability_completeness_score: float = Field(..., ge=0.0, le=1.0)
    # Verdict
    analyst_verdict: Optional[str] = Field(default=None)
    evaluation_status: str = Field(default="PENDING")
    evaluation_notes: Optional[str] = Field(default=None)
    evaluated_at: datetime = Field(...)

    @field_validator("analyst_verdict")
    @classmethod
    def _check_verdict(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_VERDICTS:
            raise ValueError(f"analyst_verdict must be one of {VALID_VERDICTS}, got '{v}'")
        return v

    @field_validator("evaluation_status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in VALID_EVALUATION_STATUSES:
            raise ValueError(f"evaluation_status must be one of {VALID_EVALUATION_STATUSES}, got '{v}'")
        return v


class AnalystFeedbackRecord(FoundationModel):
    """Human analyst verdict and failure-mode annotation."""

    feedback_id: str = Field(...)
    decision_log_id: str = Field(...)
    evaluation_id: Optional[str] = Field(default=None)
    analyst_name: str = Field(..., min_length=1)
    verdict: str = Field(...)
    override_reason: Optional[str] = Field(default=None)
    failure_mode: Optional[str] = Field(default=None)
    feedback_notes: Optional[str] = Field(default=None)

    @field_validator("verdict")
    @classmethod
    def _check_verdict(cls, v: str) -> str:
        if v not in VALID_VERDICTS:
            raise ValueError(f"verdict must be one of {VALID_VERDICTS}, got '{v}'")
        return v

    @field_validator("failure_mode")
    @classmethod
    def _check_failure_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_FAILURE_MODES:
            raise ValueError(f"failure_mode must be one of {VALID_FAILURE_MODES}, got '{v}'")
        return v


class ReplayRun(FoundationModel):
    """Replay session metadata."""

    replay_run_id: str = Field(...)
    source_event_id: str = Field(...)
    replay_version: int = Field(default=1, ge=1)
    initiated_by: str = Field(..., min_length=1)
    replay_reason: Optional[str] = Field(default=None)
    started_at: datetime = Field(...)
    completed_at: Optional[datetime] = Field(default=None)
    replay_status: str = Field(default="PENDING")

    @field_validator("replay_status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in VALID_REPLAY_STATUSES:
            raise ValueError(f"replay_status must be one of {VALID_REPLAY_STATUSES}, got '{v}'")
        return v


class ReplayRunResult(FoundationModel):
    """Per-event output from a replay run."""

    replay_result_id: str = Field(...)
    replay_run_id: str = Field(...)
    event_id: str = Field(...)
    matched_rule_ids: List[str] = Field(default_factory=list)
    replayed_entities: List[str] = Field(default_factory=list)
    replayed_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    replayed_confidence_summary: Dict[str, float] = Field(default_factory=dict)
    actual_outcome_id: Optional[str] = Field(default=None)
    evaluation_id: Optional[str] = Field(default=None)


class RulePerformanceSnapshot(FoundationModel):
    """Aggregated rule performance metrics over a time window."""

    snapshot_id: str = Field(...)
    rule_id: str = Field(...)
    snapshot_date: datetime = Field(...)
    match_count: int = Field(default=0, ge=0)
    confirmed_correct_count: int = Field(default=0, ge=0)
    false_positive_count: int = Field(default=0, ge=0)
    false_negative_count: int = Field(default=0, ge=0)
    average_correctness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_confidence_gap: float = Field(default=0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Request Schemas (for API layer)
# ═══════════════════════════════════════════════════════════════════════════════

class CreateExpectedOutcomeRequest(FoundationModel):
    """POST /outcomes/expected body."""
    decision_log_id: str = Field(...)
    event_id: Optional[str] = Field(default=None)
    rule_id: str = Field(...)
    expected_entities: List[str] = Field(default_factory=list)
    expected_severity: str = Field(...)
    expected_direction: str = Field(...)
    expected_time_horizon_hours: Optional[float] = Field(default=None, ge=0.0)
    expected_mitigation_effect: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    expected_notes: Optional[str] = Field(default=None)
    confidence_at_decision_time: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("expected_severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"expected_severity must be one of {VALID_SEVERITIES}")
        return v

    @field_validator("expected_direction")
    @classmethod
    def _check_direction(cls, v: str) -> str:
        if v not in VALID_DIRECTIONS:
            raise ValueError(f"expected_direction must be one of {VALID_DIRECTIONS}")
        return v


class CreateActualOutcomeRequest(FoundationModel):
    """POST /outcomes/actual body."""
    expected_outcome_id: str = Field(...)
    event_id: Optional[str] = Field(default=None)
    observed_entities: List[str] = Field(default_factory=list)
    observed_severity: str = Field(...)
    observed_direction: str = Field(...)
    observed_time_to_materialization_hours: Optional[float] = Field(default=None, ge=0.0)
    actual_effect_value: Optional[float] = Field(default=None)
    observation_source: Optional[str] = Field(default=None)
    observation_notes: Optional[str] = Field(default=None)
    observed_at: datetime = Field(...)

    @field_validator("observed_severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"observed_severity must be one of {VALID_SEVERITIES}")
        return v

    @field_validator("observed_direction")
    @classmethod
    def _check_direction(cls, v: str) -> str:
        if v not in VALID_DIRECTIONS:
            raise ValueError(f"observed_direction must be one of {VALID_DIRECTIONS}")
        return v


class RunEvaluationRequest(FoundationModel):
    """POST /evaluations/run body."""
    decision_log_id: str = Field(...)
    expected_outcome_id: str = Field(...)
    actual_outcome_id: str = Field(...)


class CreateFeedbackRequest(FoundationModel):
    """POST /feedback body."""
    decision_log_id: str = Field(...)
    evaluation_id: Optional[str] = Field(default=None)
    analyst_name: str = Field(..., min_length=1)
    verdict: str = Field(...)
    override_reason: Optional[str] = Field(default=None)
    failure_mode: Optional[str] = Field(default=None)
    feedback_notes: Optional[str] = Field(default=None)

    @field_validator("verdict")
    @classmethod
    def _check_verdict(cls, v: str) -> str:
        if v not in VALID_VERDICTS:
            raise ValueError(f"verdict must be one of {VALID_VERDICTS}")
        return v

    @field_validator("failure_mode")
    @classmethod
    def _check_failure_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_FAILURE_MODES:
            raise ValueError(f"failure_mode must be one of {VALID_FAILURE_MODES}")
        return v


class RunReplayRequest(FoundationModel):
    """POST /replay/run body."""
    source_event_id: str = Field(...)
    initiated_by: str = Field(..., min_length=1)
    replay_reason: Optional[str] = Field(default=None)


class SnapshotRequest(FoundationModel):
    """POST /rule-performance/snapshot body."""
    rule_id: str = Field(...)
    snapshot_date: datetime = Field(...)


class ReplayReport(FoundationModel):
    """Structured report returned by the replay engine."""
    replay_run: ReplayRun
    results: List[ReplayRunResult] = Field(default_factory=list)
    comparison_available: bool = Field(default=False)
    comparison_summary: Optional[Dict[str, Any]] = Field(default=None)
