"""Impact Observatory | مرصد الأثر — Operator Decision, Outcome & Value Schemas.

Pydantic models for the persistent decision execution layer.
These are the source of truth — frontend TypeScript types must match exactly.

Lifecycle:
  OperatorDecision  → CREATED → IN_REVIEW → EXECUTED/FAILED/CLOSED
  Outcome           → PENDING_OBSERVATION → OBSERVED → CONFIRMED → DISPUTED → CLOSED/FAILED
  DecisionValue     → Computed from confirmed Outcome
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.schemas.base import VersionedModel

# ── Enums ────────────────────────────────────────────────────────────────────

DecisionType = Literal[
    "APPROVE_ACTION",
    "REJECT_ACTION",
    "ESCALATE_ACTION",
    "OVERRIDE_THRESHOLD",
    "MANUAL_INTERVENTION",
    "TRIGGER_RUN",
    "OVERRIDE_RUN_RESULT",
]

OperatorDecisionStatus = Literal[
    "CREATED",
    "IN_REVIEW",
    "EXECUTED",
    "FAILED",
    "CLOSED",
]

OutcomeStatus = Literal["PENDING", "SUCCESS", "FAILURE", "PARTIAL"]

OutcomeLifecycleStatus = Literal[
    "PENDING_OBSERVATION",
    "OBSERVED",
    "CONFIRMED",
    "DISPUTED",
    "CLOSED",
    "FAILED",
]

OutcomeClassification = Literal[
    "TRUE_POSITIVE",
    "FALSE_POSITIVE",
    "TRUE_NEGATIVE",
    "FALSE_NEGATIVE",
    "PARTIALLY_CORRECT",
    "INCONCLUSIVE",
    "OPERATIONALLY_FAILED",
]

ValueClassification = Literal[
    "HIGH_VALUE",
    "POSITIVE_VALUE",
    "NEUTRAL",
    "NEGATIVE_VALUE",
    "LOSS_INDUCING",
]


# ── OperatorDecision ─────────────────────────────────────────────────────────

class OperatorDecision(VersionedModel):
    """An operator-layer decision linked to a signal, seed, and/or run.

    Created when an operator acts on a simulation-generated recommendation.
    Carries full lineage: source_run_id, source_signal_id, source_seed_id,
    scenario_id for cross-session traceability.
    """
    decision_id:      str
    source_signal_id: str | None        = None
    source_seed_id:   str | None        = None
    source_run_id:    str | None        = None
    scenario_id:      str | None        = Field(None, description="Scenario that produced the source run")
    decision_type:    DecisionType      = "APPROVE_ACTION"
    decision_status:  OperatorDecisionStatus = "CREATED"
    decision_payload: dict              = Field(default_factory=dict)
    rationale:        str | None        = None
    confidence_score: float | None      = None
    created_by:       str               = "system"
    outcome_status:   OutcomeStatus     = "PENDING"
    outcome_payload:  dict              = Field(default_factory=dict)
    outcome_id:       str | None        = Field(None, description="Linked outcome (bidirectional)")
    created_at:       str               = ""
    updated_at:       str               = ""
    closed_at:        str | None        = None


class CreateOperatorDecisionRequest(VersionedModel):
    """Body for POST /api/v1/decisions."""
    decision_type:    DecisionType      = "APPROVE_ACTION"
    source_run_id:    str | None        = None
    scenario_id:      str | None        = None
    source_signal_id: str | None        = None
    source_seed_id:   str | None        = None
    decision_payload: dict              = Field(default_factory=dict)
    rationale:        str | None        = None
    confidence_score: float | None      = None
    created_by:       str | None        = None


class ExecuteDecisionRequest(VersionedModel):
    """Body for POST /api/v1/decisions/{id}/execute."""
    executed_by: str | None = None
    notes:       str | None = None


class CloseDecisionRequest(VersionedModel):
    """Body for POST /api/v1/decisions/{id}/close."""
    outcome_status: OutcomeStatus | None = None
    closed_by:      str | None           = None


class OperatorDecisionListResponse(VersionedModel):
    """Response for GET /api/v1/decisions."""
    count:     int
    decisions: list[OperatorDecision]


# ── Outcome ──────────────────────────────────────────────────────────────────

class Outcome(VersionedModel):
    """A first-class outcome entity linked to a decision and/or run.

    Tracks the real-world result of a decision action through its full
    lifecycle from pending observation to confirmed/disputed/closed.
    """
    outcome_id:                  str
    source_decision_id:          str | None = None
    source_run_id:               str | None = None
    source_signal_id:            str | None = None
    source_seed_id:              str | None = None
    outcome_status:              OutcomeLifecycleStatus = "PENDING_OBSERVATION"
    outcome_classification:      OutcomeClassification | None = None
    observed_at:                 str | None = None
    recorded_at:                 str        = ""
    updated_at:                  str        = ""
    closed_at:                   str | None = None
    recorded_by:                 str        = "system"
    expected_value:              float | None = None
    realized_value:              float | None = None
    error_flag:                  bool       = False
    time_to_resolution_seconds:  float | None = None
    evidence_payload:            dict       = Field(default_factory=dict)
    notes:                       str | None = None


class CreateOutcomeRequest(VersionedModel):
    """Body for POST /api/v1/outcomes."""
    source_decision_id:     str | None = None
    source_run_id:          str | None = None
    source_signal_id:       str | None = None
    source_seed_id:         str | None = None
    outcome_classification: OutcomeClassification | None = None
    expected_value:         float | None = None
    realized_value:         float | None = None
    evidence_payload:       dict         = Field(default_factory=dict)
    notes:                  str | None   = None
    recorded_by:            str | None   = None


class ObserveOutcomeRequest(VersionedModel):
    """Body for POST /api/v1/outcomes/{id}/observe."""
    evidence_payload: dict       = Field(default_factory=dict)
    realized_value:   float | None = None
    notes:            str | None   = None
    observed_by:      str | None   = None


class ConfirmOutcomeRequest(VersionedModel):
    """Body for POST /api/v1/outcomes/{id}/confirm."""
    outcome_classification: OutcomeClassification
    realized_value:         float | None = None
    notes:                  str | None   = None
    confirmed_by:           str | None   = None


class DisputeOutcomeRequest(VersionedModel):
    """Body for POST /api/v1/outcomes/{id}/dispute."""
    reason:       str
    notes:        str | None = None
    disputed_by:  str | None = None


class CloseOutcomeRequest(VersionedModel):
    """Body for POST /api/v1/outcomes/{id}/close."""
    notes:     str | None = None
    closed_by: str | None = None


class OutcomeListResponse(VersionedModel):
    """Response for GET /api/v1/outcomes."""
    count:    int
    outcomes: list[Outcome]


# ── DecisionValue ────────────────────────────────────────────────────────────

class DecisionValue(VersionedModel):
    """A computed ROI entity derived from a confirmed Outcome.

    net_value = avoided_loss - (operational_cost + decision_cost + latency_cost)

    Classification thresholds:
      HIGH_VALUE     → net_value ≥ 1_000_000
      POSITIVE_VALUE → 0 < net_value < 1_000_000
      NEUTRAL        → net_value == 0
      NEGATIVE_VALUE → -1_000_000 < net_value < 0
      LOSS_INDUCING  → net_value ≤ -1_000_000
    """
    value_id:               str
    source_outcome_id:      str
    source_decision_id:     str | None = None
    source_run_id:          str | None = None
    computed_at:            str        = ""
    computed_by:            str        = "system"
    expected_value:         float | None = None
    realized_value:         float | None = None
    avoided_loss:           float      = 0.0
    operational_cost:       float      = 0.0
    decision_cost:          float      = 0.0
    latency_cost:           float      = 0.0
    total_cost:             float      = 0.0
    net_value:              float      = 0.0
    value_confidence_score: float      = 0.75
    value_classification:   ValueClassification = "NEUTRAL"
    calculation_trace:      dict       = Field(default_factory=dict)
    notes:                  str | None = None


class ComputeValueRequest(VersionedModel):
    """Body for POST /api/v1/values/compute."""
    source_outcome_id: str
    avoided_loss:      float | None = None
    operational_cost:  float        = 0.0
    decision_cost:     float        = 0.0
    latency_cost:      float        = 0.0
    notes:             str | None   = None
    computed_by:       str | None   = None


class RecomputeValueRequest(VersionedModel):
    """Body for POST /api/v1/values/{id}/recompute."""
    avoided_loss:     float | None = None
    operational_cost: float | None = None
    decision_cost:    float | None = None
    latency_cost:     float | None = None
    notes:            str | None   = None
    computed_by:      str | None   = None


class DecisionValueListResponse(VersionedModel):
    """Response for GET /api/v1/values."""
    count:  int
    values: list[DecisionValue]
