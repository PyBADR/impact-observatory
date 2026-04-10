"""
Banking Intelligence — Outcome Review + Decision Value Audit
=============================================================
Closes the learning loop:

OutcomeReviewContract:
  - Expected vs actual comparison at multiple time windows
  - Learning signals for model recalibration
  - Confidence recalibration based on actual outcomes

DecisionValueAudit:
  - Gross loss avoided
  - Implementation costs (operational, side-effect)
  - Confidence-adjusted value
  - Realized value (once observed)
  - Variance analysis
  - CFO-defensible flag

This is what makes the platform a decision INTELLIGENCE system
rather than a decision LOGGING system.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ─── Outcome Review Enums ──────────────────────────────────────────────────

class ReviewWindowStatus(str, Enum):
    PENDING = "PENDING"
    OBSERVATION_COLLECTED = "OBSERVATION_COLLECTED"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    SKIPPED = "SKIPPED"


class LearningSignalType(str, Enum):
    MODEL_OVERESTIMATED = "model_overestimated"
    MODEL_UNDERESTIMATED = "model_underestimated"
    MODEL_ACCURATE = "model_accurate"
    DIRECTION_WRONG = "direction_wrong"
    TIMING_WRONG = "timing_wrong"
    MECHANISM_DIFFERENT = "mechanism_different"
    EXTERNAL_FACTOR = "external_factor"


class OutcomeClassification(str, Enum):
    BETTER_THAN_EXPECTED = "better_than_expected"
    AS_EXPECTED = "as_expected"
    WORSE_THAN_EXPECTED = "worse_than_expected"
    SIGNIFICANTLY_WORSE = "significantly_worse"
    OPPOSITE_DIRECTION = "opposite_direction"


# ─── Review Window ──────────────────────────────────────────────────────────

class ReviewWindow(BaseModel):
    """Single observation window within an outcome review."""
    window_hours: float = Field(
        ..., gt=0,
        description="Hours after decision execution: 6, 24, 72, 168"
    )
    status: ReviewWindowStatus = Field(default=ReviewWindowStatus.PENDING)
    observation_due_at: Optional[datetime] = None
    observed_at: Optional[datetime] = None

    # ── Expected vs Actual ──────────────────────────────────────────────
    expected_metric_value: Optional[float] = None
    actual_metric_value: Optional[float] = None
    metric_name: str = Field(
        ..., description="What we're measuring: 'liquidity_ratio', 'npl_rate'"
    )
    delta_from_expected: Optional[float] = Field(
        None, description="actual - expected (negative = better than expected)"
    )
    delta_pct: Optional[float] = Field(
        None, description="Percentage deviation from expected"
    )

    # ── Classification ──────────────────────────────────────────────────
    classification: Optional[OutcomeClassification] = None
    narrative: Optional[str] = Field(
        None, description="Human-readable explanation of what happened"
    )

    @model_validator(mode="after")
    def compute_delta(self) -> "ReviewWindow":
        if self.actual_metric_value is not None and self.expected_metric_value is not None:
            self.delta_from_expected = self.actual_metric_value - self.expected_metric_value
            if self.expected_metric_value != 0:
                self.delta_pct = (self.delta_from_expected / abs(self.expected_metric_value)) * 100
        return self


# ─── Learning Signal ───────────────────────────────────────────────────────

class LearningSignal(BaseModel):
    """Extracted insight from comparing expected vs actual."""
    signal_type: LearningSignalType
    description: str = Field(..., min_length=5)
    affected_model_component: str = Field(
        ..., description="Which model component needs recalibration"
    )
    suggested_recalibration: Optional[str] = Field(
        None, description="Specific adjustment recommendation"
    )
    magnitude: float = Field(
        ..., ge=0.0, le=1.0,
        description="How significant is this signal? 1.0 = very significant"
    )
    applies_to_scenarios: list[str] = Field(
        default_factory=list,
        description="Scenario IDs this learning applies to"
    )


# ─── Confidence Recalibration ──────────────────────────────────────────────

class ConfidenceRecalibration(BaseModel):
    """Adjusts confidence scores based on outcome observations."""
    dimension: str = Field(
        ..., description="'directional', 'impact_estimate', 'execution', 'data_sufficiency'"
    )
    original_confidence: float = Field(..., ge=0.0, le=1.0)
    recalibrated_confidence: float = Field(..., ge=0.0, le=1.0)
    adjustment_reason: str = Field(..., min_length=5)
    evidence_window_hours: float = Field(
        ..., gt=0,
        description="Which review window drove this recalibration"
    )


# ─── Outcome Review Contract ───────────────────────────────────────────────

class OutcomeReviewContract(BaseModel):
    """
    Multi-window outcome review for a decision.

    Standard windows: 6h (immediate), 24h (next-day), 72h (short-term),
    168h (weekly). Each window independently collects observations
    and generates learning signals.
    """
    review_id: str = Field(
        ..., min_length=3, pattern=r"^review:[a-z0-9_\-]+$",
        description="Unique ID: 'review:hormuz_liquidity_20260410'"
    )
    decision_id: str = Field(
        ..., description="Linked DecisionContract ID"
    )
    scenario_id: str = Field(
        ..., description="SCENARIO_CATALOG key"
    )

    # ── Review Windows ──────────────────────────────────────────────────
    windows: list[ReviewWindow] = Field(
        ..., min_length=1,
        description="Observation windows (typically 6h, 24h, 72h, 168h)"
    )

    # ── Learning Signals ────────────────────────────────────────────────
    learning_signals: list[LearningSignal] = Field(default_factory=list)

    # ── Confidence Recalibration ────────────────────────────────────────
    recalibrations: list[ConfidenceRecalibration] = Field(default_factory=list)

    # ── Overall Assessment ──────────────────────────────────────────────
    overall_classification: Optional[OutcomeClassification] = None
    overall_narrative: Optional[str] = None
    review_complete: bool = False

    # ── Metadata ────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    reviewed_by: Optional[str] = Field(
        None, description="canonical_id of reviewing entity"
    )

    @property
    def completed_windows(self) -> int:
        return sum(
            1 for w in self.windows
            if w.status == ReviewWindowStatus.ANALYSIS_COMPLETE
        )

    @property
    def completion_pct(self) -> float:
        if not self.windows:
            return 0.0
        return (self.completed_windows / len(self.windows)) * 100

    @classmethod
    def create_standard_review(
        cls,
        review_id: str,
        decision_id: str,
        scenario_id: str,
        metric_name: str,
        expected_values: dict[float, float],
        execution_time: Optional[datetime] = None,
    ) -> "OutcomeReviewContract":
        """
        Factory: creates a standard 4-window review.
        expected_values: {window_hours: expected_metric_value}
        """
        base_time = execution_time or datetime.now(timezone.utc)
        windows = []
        for hours in [6.0, 24.0, 72.0, 168.0]:
            from datetime import timedelta
            windows.append(ReviewWindow(
                window_hours=hours,
                metric_name=metric_name,
                expected_metric_value=expected_values.get(hours),
                observation_due_at=base_time + timedelta(hours=hours),
            ))
        return cls(
            review_id=review_id,
            decision_id=decision_id,
            scenario_id=scenario_id,
            windows=windows,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Decision Value Audit
# ═══════════════════════════════════════════════════════════════════════════

class AssumptionTrace(BaseModel):
    """Trace of an assumption used in value computation."""
    assumption_id: str
    description: str
    value_used: float
    source: str
    sensitivity_to_outcome: float = Field(
        ..., ge=0.0, le=1.0,
        description="How much the outcome changes if this assumption is wrong"
    )
    was_validated: bool = False
    validation_result: Optional[str] = None


class DecisionValueAudit(BaseModel):
    """
    CFO-defensible value audit for a decision.

    The formula:
      confidence_adjusted_value = (gross_loss_avoided - implementation_cost - side_effect_cost)
                                  × composite_confidence
      variance = realized_value - confidence_adjusted_value

    cfo_defensible = True when:
      - All assumptions are documented
      - Confidence dimensions are independently assessed
      - Realized value is within 1.5× of adjusted value
      - No untraced cost components
    """
    audit_id: str = Field(
        ..., min_length=3, pattern=r"^audit:[a-z0-9_\-]+$",
        description="Unique ID: 'audit:hormuz_liquidity_20260410'"
    )
    decision_id: str = Field(
        ..., description="Linked DecisionContract ID"
    )
    outcome_review_id: str = Field(
        ..., description="Linked OutcomeReviewContract ID"
    )
    scenario_id: str = Field(
        ..., description="SCENARIO_CATALOG key"
    )

    # ── Value Components ────────────────────────────────────────────────
    gross_loss_avoided_usd: float = Field(
        ..., ge=0,
        description="Total loss that would have occurred without the decision"
    )
    implementation_cost_usd: float = Field(
        ..., ge=0,
        description="Direct cost of executing the decision"
    )
    side_effect_cost_usd: float = Field(
        ..., ge=0,
        description="Indirect costs and unintended consequences"
    )

    # ── Computed Values ─────────────────────────────────────────────────
    net_value_usd: float = Field(
        default=0.0,
        description="gross_loss_avoided - implementation_cost - side_effect_cost"
    )
    confidence_adjusted_value_usd: float = Field(
        default=0.0,
        description="net_value × composite_confidence"
    )
    composite_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="From CounterfactualContract confidence dimensions"
    )

    # ── Realized (post-observation) ─────────────────────────────────────
    realized_value_usd: Optional[float] = Field(
        None, description="Actual value realized after outcome review"
    )
    variance_usd: Optional[float] = Field(
        None, description="realized - confidence_adjusted (negative = overestimated)"
    )
    variance_pct: Optional[float] = None

    # ── Assumptions ─────────────────────────────────────────────────────
    assumptions_trace: list[AssumptionTrace] = Field(
        ..., min_length=1,
        description="Every number must be traceable"
    )

    # ── CFO Defensibility ───────────────────────────────────────────────
    cfo_defensible: bool = Field(
        default=False,
        description="Auto-computed: is this audit CFO-defensible?"
    )
    defensibility_gaps: list[str] = Field(
        default_factory=list,
        description="Reasons this audit is not yet defensible"
    )

    # ── Metadata ────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    auditor_entity_id: Optional[str] = None

    @model_validator(mode="after")
    def compute_values_and_defensibility(self) -> "DecisionValueAudit":
        # Net value
        self.net_value_usd = (
            self.gross_loss_avoided_usd
            - self.implementation_cost_usd
            - self.side_effect_cost_usd
        )

        # Confidence-adjusted
        self.confidence_adjusted_value_usd = (
            self.net_value_usd * self.composite_confidence
        )

        # Variance (if realized)
        if self.realized_value_usd is not None:
            self.variance_usd = self.realized_value_usd - self.confidence_adjusted_value_usd
            if self.confidence_adjusted_value_usd != 0:
                self.variance_pct = (
                    self.variance_usd / abs(self.confidence_adjusted_value_usd)
                ) * 100

        # CFO defensibility check
        gaps: list[str] = []

        if not self.assumptions_trace:
            gaps.append("No assumptions documented")

        unvalidated = [a for a in self.assumptions_trace if not a.was_validated]
        if len(unvalidated) > len(self.assumptions_trace) * 0.5:
            gaps.append(f"{len(unvalidated)}/{len(self.assumptions_trace)} assumptions unvalidated")

        if self.composite_confidence < 0.30:
            gaps.append(f"Composite confidence too low ({self.composite_confidence:.2f})")

        if self.variance_usd is not None and self.confidence_adjusted_value_usd != 0:
            ratio = abs(self.variance_usd / self.confidence_adjusted_value_usd)
            if ratio > 0.50:
                gaps.append(f"Variance too high ({ratio:.0%} of adjusted value)")

        self.defensibility_gaps = gaps
        self.cfo_defensible = len(gaps) == 0

        return self
