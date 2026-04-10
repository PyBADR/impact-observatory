"""Institutional Interface Layer — Pydantic response models.

Typed, stable API contracts for Stage 70 (Calibration) and Stage 80 (Trust)
outputs.  Every field is explicitly typed — no ``dict`` blobs, no ``Any``.

These models are the **source of truth** for:
  • API endpoint response shapes
  • Frontend TypeScript contract alignment
  • SHA-256 audit-trail payload hashing
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
#  Stage 70 — Calibration Surface Models
# ═══════════════════════════════════════════════════════════════════════════════

class AuditResultItem(BaseModel):
    """Single action audit result from Stage 70 AuditEngine."""
    decision_id: str
    action_id: str
    category_error_flag: bool
    scenario_alignment_score: float
    sector_alignment_score: float
    node_coverage_score: float
    urgency_appropriateness: float
    feasibility_realism: float
    cost_proportionality: float
    action_quality_composite: float
    validation_notes: list[dict[str, str]] = Field(default_factory=list)


class RankedDecisionItem(BaseModel):
    """Single ranked decision from Stage 70 RankingEngine."""
    decision_id: str
    action_id: str
    calibrated_rank: int
    ranking_score: float
    previous_rank: int
    rank_delta: int
    factors: list[dict[str, float]] = Field(default_factory=list)
    crisis_boost: float


class AuthorityAssignmentItem(BaseModel):
    """Authority assignment from Stage 70 AuthorityEngine."""
    decision_id: str
    action_id: str
    primary_authority_en: str
    primary_authority_ar: str
    escalation_authority_en: str
    escalation_authority_ar: str
    oversight_authority_en: str
    oversight_authority_ar: str
    operational_authority_en: str
    operational_authority_ar: str
    authority_level: str
    cross_border_coordination: bool


class CalibrationResultItem(BaseModel):
    """Outcome calibration result from Stage 70 CalibrationEngine."""
    decision_id: str
    action_id: str
    calibration_confidence: float
    expected_calibration_error: float
    adjustment_factor: float
    calibration_grade: str
    confidence_band_low: float
    confidence_band_high: float
    calibration_notes: list[dict[str, str]] = Field(default_factory=list)


class TrustResultItem(BaseModel):
    """Trust score from Stage 70 TrustEngine."""
    decision_id: str
    action_id: str
    trust_composite: float
    trust_level: str
    execution_mode: str
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    hard_constraints_applied: list[str] = Field(default_factory=list)
    trust_notes: list[dict[str, str]] = Field(default_factory=list)


class CalibrationCountsModel(BaseModel):
    """Aggregate counts for the calibration layer."""
    audited: int = 0
    ranked: int = 0
    authorities_assigned: int = 0
    calibrated: int = 0
    trust_scored: int = 0
    category_errors: int = 0
    high_trust: int = 0
    medium_trust: int = 0
    low_trust: int = 0
    blocked: int = 0
    auto_executable: int = 0


class CalibrationLayerResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/calibration — full Stage 70 output."""
    run_id: str
    stage: int = 70
    audit_results: list[AuditResultItem] = Field(default_factory=list)
    ranked_decisions: list[RankedDecisionItem] = Field(default_factory=list)
    authority_assignments: list[AuthorityAssignmentItem] = Field(default_factory=list)
    calibration_results: list[CalibrationResultItem] = Field(default_factory=list)
    trust_results: list[TrustResultItem] = Field(default_factory=list)
    stage_timings: dict[str, float] = Field(default_factory=dict)
    total_time_ms: float = 0.0
    counts: CalibrationCountsModel = Field(default_factory=CalibrationCountsModel)


# ═══════════════════════════════════════════════════════════════════════════════
#  Stage 80 — Trust Surface Models
# ═══════════════════════════════════════════════════════════════════════════════

class ScenarioValidationModel(BaseModel):
    """Scenario taxonomy enforcement result."""
    scenario_id: str = ""
    scenario_type: str = ""
    scenario_type_ar: str = ""
    taxonomy_valid: bool = False
    fallback_applied: bool = False
    fallback_method: str = "none"
    classification_confidence: float = 0.0
    enforcement_notes: list[dict[str, str]] = Field(default_factory=list)


class ValidationResultItem(BaseModel):
    """Structural action validation from Stage 80 ValidationEngine."""
    decision_id: str
    action_id: str
    scenario_valid: bool
    sector_valid: bool
    node_coverage_valid: bool
    operational_feasibility: bool
    category_error_flag: bool
    validation_status: str
    validation_status_ar: str = ""
    dimension_details: list[dict[str, str]] = Field(default_factory=list)


class AuthorityProfileItem(BaseModel):
    """Country-specific authority profile from Stage 80."""
    decision_id: str
    action_id: str
    country: str
    country_ar: str = ""
    primary_owner_en: str
    primary_owner_ar: str = ""
    secondary_owner_en: str
    secondary_owner_ar: str = ""
    regulator_en: str
    regulator_ar: str = ""
    escalation_chain: list[dict[str, str]] = Field(default_factory=list)
    cross_border_entities: list[dict[str, str]] = Field(default_factory=list)


class CausalStepModel(BaseModel):
    """Single step in the causal explanation path."""
    step: int
    event_en: str
    event_ar: str = ""
    mechanism: str
    severity_contribution: float


class DecisionExplanationItem(BaseModel):
    """Full causal explanation for a decision from Stage 80."""
    decision_id: str
    action_id: str
    trigger_reason_en: str
    trigger_reason_ar: str = ""
    causal_path: list[CausalStepModel] = Field(default_factory=list)
    propagation_summary_en: str = ""
    propagation_summary_ar: str = ""
    regime_context_en: str = ""
    regime_context_ar: str = ""
    ranking_reason_en: str = ""
    ranking_reason_ar: str = ""
    rejection_reason_en: str = ""
    rejection_reason_ar: str = ""
    narrative_en: str = ""
    narrative_ar: str = ""


class LearningUpdateItem(BaseModel):
    """Learning closure signal from Stage 80."""
    decision_id: str
    action_id: str
    calibration_error: float
    action_adjustment: str
    action_adjustment_ar: str = ""
    ranking_adjustment: float
    confidence_adjustment: float
    learning_velocity: str
    learning_velocity_ar: str = ""
    recommendations: list[dict[str, str]] = Field(default_factory=list)


class OverrideResultItem(BaseModel):
    """Final trust override for a decision from Stage 80."""
    decision_id: str
    action_id: str
    final_status: str
    final_status_ar: str = ""
    override_reason_en: str
    override_reason_ar: str = ""
    override_rule: str
    validation_status: str
    trust_level: str
    trust_score: float
    calibration_grade: str
    learning_action: str
    taxonomy_confidence: float
    override_chain: list[dict[str, str]] = Field(default_factory=list)


class TrustCountsModel(BaseModel):
    """Aggregate counts for the trust layer."""
    validated: int = 0
    valid: int = 0
    conditionally_valid: int = 0
    rejected: int = 0
    authorities_refined: int = 0
    explanations_generated: int = 0
    learning_updates: int = 0
    blocked: int = 0
    human_required: int = 0
    conditional: int = 0
    auto_executable: int = 0
    taxonomy_valid: bool = False
    taxonomy_confidence: float = 0.0


class TrustLayerResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/trust — full Stage 80 output."""
    run_id: str
    stage: int = 80
    scenario_validation: ScenarioValidationModel = Field(
        default_factory=lambda: ScenarioValidationModel(
            scenario_id="", scenario_type="", taxonomy_valid=False,
            fallback_applied=False, fallback_method="none", classification_confidence=0.0,
        )
    )
    validation_results: list[ValidationResultItem] = Field(default_factory=list)
    authority_profiles: list[AuthorityProfileItem] = Field(default_factory=list)
    explanations: list[DecisionExplanationItem] = Field(default_factory=list)
    learning_updates: list[LearningUpdateItem] = Field(default_factory=list)
    override_results: list[OverrideResultItem] = Field(default_factory=list)
    stage_timings: dict[str, float] = Field(default_factory=dict)
    total_time_ms: float = 0.0
    counts: TrustCountsModel = Field(default_factory=TrustCountsModel)


# ═══════════════════════════════════════════════════════════════════════════════
#  Explainability Surface
# ═══════════════════════════════════════════════════════════════════════════════

class ExplainabilityResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/explainability — all decision explanations."""
    run_id: str
    scenario_id: str
    scenario_type: str
    taxonomy_confidence: float
    explanations: list[DecisionExplanationItem] = Field(default_factory=list)
    override_summary: list[OverrideResultItem] = Field(default_factory=list)
    total_decisions: int = 0
    blocked_count: int = 0
    human_required_count: int = 0
    auto_executable_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Audit Trail Surface
# ═══════════════════════════════════════════════════════════════════════════════

class AuditTrailEntry(BaseModel):
    """Single immutable audit trail entry."""
    entry_id: str
    run_id: str
    decision_id: str = ""
    timestamp: str
    source_stage: int
    source_engine: str
    event_type: str
    actor: str = "system"
    payload_hash: str
    payload: dict = Field(default_factory=dict)


class AuditTrailResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/audit-trail — SHA-256-hashed audit log."""
    run_id: str
    entries: list[AuditTrailEntry] = Field(default_factory=list)
    total_entries: int = 0
    integrity_verified: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
#  Decision Summary Surface
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionSummaryItem(BaseModel):
    """Normalized summary of a single decision for institutional display."""
    decision_id: str
    action_id: str
    action_en: str
    action_ar: str = ""
    sector: str
    decision_owner_en: str
    decision_owner_ar: str = ""
    deadline_hours: float
    trust_level: str
    trust_score: float
    execution_mode: str
    execution_mode_ar: str = ""
    ranking_score: float
    calibrated_rank: int
    calibration_grade: str
    calibration_confidence: float
    explainability_available: bool
    override_rule: str
    override_reason_en: str
    override_reason_ar: str = ""
    audit_entries_count: int = 0


class DecisionSummaryResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/decision-summary — bridge object."""
    run_id: str
    scenario_id: str
    scenario_type: str
    pipeline_stages_completed: int = 80
    decisions: list[DecisionSummaryItem] = Field(default_factory=list)
    total_decisions: int = 0
    execution_breakdown: dict[str, int] = Field(default_factory=dict)
    trust_breakdown: dict[str, int] = Field(default_factory=dict)
