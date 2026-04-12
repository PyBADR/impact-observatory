"""
Evaluation Layer — Pydantic Domain Models
==========================================

7 domain models for outcome tracking, decision evaluation,
analyst feedback, replay, and rule performance analysis.

Every model is immutable once persisted. Corrections create new records.
Every model carries a provenance_hash for tamper detection.

Relationship map:
  DecisionLogEntry (existing)
    └─→ ExpectedOutcome (1:1)
          ├─→ ActualOutcome (1:N — partial observations)
          └─→ DecisionEvaluation (1:1)
                └─→ AnalystFeedbackRecord (1:N)
  ReplayRun (standalone)
    └─→ ReplayRunResult (1:N per rule)
  RulePerformanceSnapshot (standalone aggregate)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.data_foundation.schemas.enums import (
    RiskLevel,
    SignalSeverity,
)

__all__ = [
    "ExpectedOutcome",
    "ActualOutcome",
    "DecisionEvaluation",
    "AnalystFeedbackRecord",
    "ReplayRun",
    "ReplayRunResult",
    "RulePerformanceSnapshot",
    "AnalystVerdict",
    "FailureMode",
    "ObservationSource",
    "ObservationCompleteness",
    "ReplayStatus",
    "RuleSetSource",
]


# ═══════════════════════════════════════════════════════════════════════════════
# String-enum constants (avoid StrEnum for Python 3.10 compatibility)
# ═══════════════════════════════════════════════════════════════════════════════


class AnalystVerdict:
    CORRECT = "CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"
    INCONCLUSIVE = "INCONCLUSIVE"
    ALL = [CORRECT, PARTIALLY_CORRECT, INCORRECT, INCONCLUSIVE]


class FailureMode:
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    SEVERITY_MISS = "SEVERITY_MISS"
    TIMING_MISS = "TIMING_MISS"
    ENTITY_MISS = "ENTITY_MISS"
    ACTION_WRONG = "ACTION_WRONG"
    ALL = [FALSE_POSITIVE, FALSE_NEGATIVE, SEVERITY_MISS, TIMING_MISS, ENTITY_MISS, ACTION_WRONG]


class ObservationSource:
    ANALYST_REVIEW = "ANALYST_REVIEW"
    REAL_SOURCE_DATA = "REAL_SOURCE_DATA"
    AUTOMATED_SIGNAL = "AUTOMATED_SIGNAL"
    COMPOSITE = "COMPOSITE"
    ALL = [ANALYST_REVIEW, REAL_SOURCE_DATA, AUTOMATED_SIGNAL, COMPOSITE]


class ObservationCompleteness:
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    PRELIMINARY = "PRELIMINARY"
    ALL = [COMPLETE, PARTIAL, PRELIMINARY]


class ReplayStatus:
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ALL = [RUNNING, COMPLETED, FAILED]


class RuleSetSource:
    CURRENT_ACTIVE = "CURRENT_ACTIVE"
    SPEC_COMPILED = "SPEC_COMPILED"
    HISTORICAL_SNAPSHOT = "HISTORICAL_SNAPSHOT"
    ALL = [CURRENT_ACTIVE, SPEC_COMPILED, HISTORICAL_SNAPSHOT]


# ═══════════════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════════════


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16]}"


def _compute_hash(data: Dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ExpectedOutcome
# ═══════════════════════════════════════════════════════════════════════════════


class ExpectedOutcome(BaseModel):
    """What the system predicted would happen when a decision was proposed.

    Created at decision time. One-to-one with DecisionLogEntry.
    """

    expected_outcome_id: str = Field(
        default_factory=lambda: _generate_id("EXOUT"),
        description="Unique identifier.",
    )
    decision_log_id: str = Field(
        ...,
        description="FK → DecisionLogEntry.log_id — which decision this prediction belongs to.",
    )
    rule_id: str = Field(
        ...,
        description="FK → DecisionRule.rule_id — which rule produced the decision.",
    )
    spec_id: Optional[str] = Field(
        default=None,
        description="RuleSpec.spec_id — traceability to policy layer. Nullable for non-spec rules.",
    )

    # ── Expected impact ────────────────────────────────────────────────────
    expected_severity: SignalSeverity = Field(
        ...,
        description="Predicted severity at outcome.",
    )
    expected_risk_level: RiskLevel = Field(
        ...,
        description="Predicted risk level at resolution.",
    )
    expected_affected_entity_ids: List[str] = Field(
        default_factory=list,
        description="Entity IDs expected to be affected.",
    )
    expected_affected_sectors: List[str] = Field(
        default_factory=list,
        description="Sectors expected to be affected.",
    )
    expected_affected_countries: List[str] = Field(
        default_factory=list,
        description="Countries expected to be affected.",
    )
    expected_financial_impact: Optional[float] = Field(
        default=None,
        description="Predicted financial impact in millions (local currency).",
    )
    expected_mitigation_effect: Optional[str] = Field(
        default=None,
        description="What the proposed action was supposed to achieve.",
    )
    expected_resolution_hours: Optional[float] = Field(
        default=None,
        ge=0,
        description="Expected time for the event to resolve (hours).",
    )

    # ── Frozen data state ──────────────────────────────────────────────────
    data_state_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Frozen DataState.values at trigger time for reproducibility.",
    )
    data_state_hash: str = Field(
        default="",
        description="SHA-256 of data_state_snapshot.",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    provenance_hash: str = Field(
        default="",
        description="SHA-256 for tamper detection.",
    )

    def compute_hashes(self) -> None:
        """Compute data_state_hash and provenance_hash."""
        self.data_state_hash = _compute_hash(self.data_state_snapshot)
        self.provenance_hash = _compute_hash({
            "expected_outcome_id": self.expected_outcome_id,
            "decision_log_id": self.decision_log_id,
            "data_state_hash": self.data_state_hash,
            "created_at": self.created_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ActualOutcome
# ═══════════════════════════════════════════════════════════════════════════════


class ActualOutcome(BaseModel):
    """What actually happened — recorded after the event played out.

    Supports partial and delayed observations. Multiple ActualOutcomes
    can accumulate against one ExpectedOutcome (partial → complete).
    """

    actual_outcome_id: str = Field(
        default_factory=lambda: _generate_id("ACOUT"),
    )
    expected_outcome_id: str = Field(
        ...,
        description="FK → ExpectedOutcome — which prediction this resolves.",
    )
    decision_log_id: str = Field(
        ...,
        description="FK → DecisionLogEntry — redundant FK for fast joins.",
    )

    # ── Observed impact ────────────────────────────────────────────────────
    actual_severity: Optional[SignalSeverity] = Field(
        default=None,
        description="Observed severity. Null if not yet determinable.",
    )
    actual_risk_level: Optional[RiskLevel] = Field(
        default=None,
    )
    actual_affected_entity_ids: List[str] = Field(
        default_factory=list,
    )
    actual_affected_sectors: List[str] = Field(
        default_factory=list,
    )
    actual_affected_countries: List[str] = Field(
        default_factory=list,
    )
    actual_financial_impact: Optional[float] = Field(
        default=None,
        description="Observed financial impact (millions).",
    )
    actual_resolution_hours: Optional[float] = Field(
        default=None,
    )

    # ── Observation metadata ───────────────────────────────────────────────
    observation_source: str = Field(
        default=ObservationSource.ANALYST_REVIEW,
        description="How this actual outcome was determined.",
    )
    observation_completeness: str = Field(
        default=ObservationCompleteness.PRELIMINARY,
        description="COMPLETE, PARTIAL, or PRELIMINARY.",
    )
    observation_notes: Optional[str] = Field(default=None)
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    data_sources_used: List[str] = Field(
        default_factory=list,
        description="Dataset IDs or source references that confirmed this outcome.",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _compute_hash({
            "actual_outcome_id": self.actual_outcome_id,
            "expected_outcome_id": self.expected_outcome_id,
            "observed_at": self.observed_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DecisionEvaluation
# ═══════════════════════════════════════════════════════════════════════════════

SCORING_METHOD_VERSION = "1.0.0"


class DecisionEvaluation(BaseModel):
    """Comparison of expected vs actual with deterministic scoring.

    Created when an ActualOutcome is finalized (observation_completeness = COMPLETE).
    All scores are [0.0–1.0] except confidence_gap which is [-1.0, +1.0].

    Scoring algorithm:
      severity_alignment  = 1.0 - abs(ord(expected) - ord(actual)) / 5.0
      entity_alignment    = jaccard(expected_entities, actual_entities)
      sector_alignment    = jaccard(expected_sectors, actual_sectors)
      timing_alignment    = max(0, 1.0 - abs(expected_h - actual_h) / expected_h)
      correctness_score   = 0.35*severity + 0.30*entity + 0.20*timing + 0.15*sector
      confidence_gap      = rule_confidence - correctness_score
      explainability      = non_null_expected_fields / total_expected_fields
    """

    evaluation_id: str = Field(
        default_factory=lambda: _generate_id("EVAL"),
    )
    expected_outcome_id: str = Field(...)
    actual_outcome_id: str = Field(...)
    decision_log_id: str = Field(...)
    rule_id: str = Field(...)
    spec_id: Optional[str] = Field(default=None)

    # ── Scoring ────────────────────────────────────────────────────────────
    correctness_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Weighted composite of alignment scores.",
    )
    severity_alignment_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Ordinal distance: 1.0 - |ord(exp) - ord(act)| / 5.0.",
    )
    entity_alignment_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Jaccard similarity over entity ID sets.",
    )
    timing_alignment_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="max(0, 1 - |exp_h - act_h| / exp_h).",
    )
    sector_alignment_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Jaccard similarity over sector sets.",
    )
    confidence_gap: float = Field(
        ..., ge=-1.0, le=1.0,
        description="rule_confidence - correctness_score. Positive = overconfident.",
    )
    explainability_completeness_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Ratio of non-null expected outcome fields.",
    )

    # ── Verdict ────────────────────────────────────────────────────────────
    analyst_verdict: Optional[str] = Field(
        default=None,
        description="CORRECT, PARTIALLY_CORRECT, INCORRECT, INCONCLUSIVE. Set by analyst.",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    scoring_method_version: str = Field(
        default=SCORING_METHOD_VERSION,
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _compute_hash({
            "evaluation_id": self.evaluation_id,
            "correctness_score": self.correctness_score,
            "evaluated_at": self.evaluated_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AnalystFeedbackRecord
# ═══════════════════════════════════════════════════════════════════════════════


class AnalystFeedbackRecord(BaseModel):
    """Human-in-the-loop assessment of a decision evaluation.

    An analyst can confirm, dispute, or annotate any evaluation.
    Multiple feedbacks per evaluation are permitted.
    """

    feedback_id: str = Field(
        default_factory=lambda: _generate_id("AFBK"),
    )
    evaluation_id: str = Field(
        ...,
        description="FK → DecisionEvaluation.",
    )
    decision_log_id: str = Field(
        ...,
        description="Redundant FK for querying.",
    )
    analyst_id: str = Field(
        ...,
        description="Who provided the feedback.",
    )

    # ── Assessment ─────────────────────────────────────────────────────────
    verdict: str = Field(
        ...,
        description="CORRECT, PARTIALLY_CORRECT, INCORRECT, INCONCLUSIVE.",
    )
    override_correctness_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Analyst-overridden correctness score. Null = accepts computed score.",
    )
    failure_mode: Optional[str] = Field(
        default=None,
        description=(
            "FALSE_POSITIVE, FALSE_NEGATIVE, SEVERITY_MISS, "
            "TIMING_MISS, ENTITY_MISS, ACTION_WRONG."
        ),
    )
    override_reason: str = Field(
        ...,
        description="Why the analyst confirms or disputes the computed evaluation.",
    )
    recommendations: Optional[str] = Field(
        default=None,
        description="What should change (threshold, scope, transmission path, etc.).",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _compute_hash({
            "feedback_id": self.feedback_id,
            "evaluation_id": self.evaluation_id,
            "verdict": self.verdict,
            "submitted_at": self.submitted_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ReplayRun
# ═══════════════════════════════════════════════════════════════════════════════


class ReplayRun(BaseModel):
    """A replay of a historical event through the current (or specified) rule set.

    Stores frozen inputs — the replay is deterministic given these inputs.
    """

    replay_run_id: str = Field(
        default_factory=lambda: _generate_id("RPLAY"),
    )
    original_decision_log_id: Optional[str] = Field(
        default=None,
        description="If replaying a specific past decision.",
    )
    original_event_id: Optional[str] = Field(
        default=None,
        description="If replaying a specific event signal.",
    )

    # ── Frozen inputs ──────────────────────────────────────────────────────
    replay_data_state: Dict[str, Any] = Field(
        ...,
        description="Frozen DataState.values for the replay.",
    )
    replay_data_state_hash: str = Field(
        default="",
        description="SHA-256 of replay_data_state.",
    )
    rule_set_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Frozen rule IDs + versions used in replay.",
    )
    rule_set_source: str = Field(
        default=RuleSetSource.CURRENT_ACTIVE,
        description="CURRENT_ACTIVE, SPEC_COMPILED, HISTORICAL_SNAPSHOT.",
    )
    replay_scenario_id: Optional[str] = Field(
        default=None,
        description="Simulation scenario ID if replaying a scenario.",
    )

    # ── Execution ──────────────────────────────────────────────────────────
    initiated_by: str = Field(
        ...,
        description="Who triggered the replay.",
    )
    initiated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    completed_at: Optional[datetime] = Field(default=None)
    status: str = Field(
        default=ReplayStatus.RUNNING,
    )
    error_message: Optional[str] = Field(default=None)

    # ── Meta ───────────────────────────────────────────────────────────────
    provenance_hash: str = Field(default="")

    def compute_hashes(self) -> None:
        self.replay_data_state_hash = _compute_hash(self.replay_data_state)
        self.provenance_hash = _compute_hash({
            "replay_run_id": self.replay_run_id,
            "replay_data_state_hash": self.replay_data_state_hash,
            "initiated_at": self.initiated_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ReplayRunResult
# ═══════════════════════════════════════════════════════════════════════════════


class ReplayRunResult(BaseModel):
    """Per-rule result from a replay run. One record per rule evaluated."""

    replay_result_id: str = Field(
        default_factory=lambda: _generate_id("RRES"),
    )
    replay_run_id: str = Field(
        ...,
        description="FK → ReplayRun.",
    )
    rule_id: str = Field(...)
    rule_version: int = Field(..., ge=1)

    # ── Engine output ──────────────────────────────────────────────────────
    triggered: bool = Field(...)
    cooldown_blocked: bool = Field(default=False)
    action: Optional[str] = Field(
        default=None,
        description="Proposed action if triggered.",
    )
    conditions_met: List[bool] = Field(default_factory=list)
    condition_details: List[Dict[str, Any]] = Field(default_factory=list)

    # ── Comparison ─────────────────────────────────────────────────────────
    matches_original: Optional[bool] = Field(
        default=None,
        description="Does this replay result match the original decision?",
    )
    divergence_reason: Optional[str] = Field(
        default=None,
        description="Why replay differs from original (if it does).",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _compute_hash({
            "replay_result_id": self.replay_result_id,
            "replay_run_id": self.replay_run_id,
            "rule_id": self.rule_id,
            "triggered": self.triggered,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 7. RulePerformanceSnapshot
# ═══════════════════════════════════════════════════════════════════════════════


class RulePerformanceSnapshot(BaseModel):
    """Periodic aggregate of rule quality metrics.

    Computed by rule_performance_aggregator.py — not written by hand.
    One snapshot per rule per time window.
    """

    snapshot_id: str = Field(
        default_factory=lambda: _generate_id("RPERF"),
    )
    rule_id: str = Field(...)
    spec_id: Optional[str] = Field(default=None)
    period_start: datetime = Field(...)
    period_end: datetime = Field(...)

    # ── Counts ─────────────────────────────────────────────────────────────
    total_evaluations: int = Field(default=0, ge=0)
    total_triggered: int = Field(default=0, ge=0)
    confirmed_correct: int = Field(default=0, ge=0)
    confirmed_partially_correct: int = Field(default=0, ge=0)
    confirmed_incorrect: int = Field(default=0, ge=0)
    false_positive_count: int = Field(default=0, ge=0)
    false_negative_count: int = Field(default=0, ge=0)

    # ── Averages ───────────────────────────────────────────────────────────
    avg_correctness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_severity_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_entity_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_timing_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_confidence_gap: float = Field(default=0.0, ge=-1.0, le=1.0)
    avg_explainability_completeness: float = Field(default=0.0, ge=0.0, le=1.0)

    # ── Meta ───────────────────────────────────────────────────────────────
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _compute_hash({
            "snapshot_id": self.snapshot_id,
            "rule_id": self.rule_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "computed_at": self.computed_at.isoformat(),
        })
