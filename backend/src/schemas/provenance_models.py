"""Explainability + Metrics Provenance Layer — Pydantic response models.

Typed contracts for the 5 provenance engines:
  1. MetricProvenanceEngine  — why this number, what computed it
  2. FactorBreakdownEngine   — what drove this number
  3. MetricRangeEngine       — expected range, not a false-precision point
  4. DecisionReasoningEngine — why this decision, why this rank
  5. DataBasisEngine         — what data period / source backs this
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
#  1. Metric Provenance
# ═══════════════════════════════════════════════════════════════════════════════

class ContributingFactor(BaseModel):
    """Single contributing factor to a metric."""
    factor_name: str
    factor_name_ar: str = ""
    factor_value: float
    weight: float = 0.0
    description_en: str = ""
    description_ar: str = ""


class MetricProvenance(BaseModel):
    """Full provenance record for a single metric."""
    metric_name: str
    metric_name_ar: str = ""
    metric_value: float
    unit: str
    time_horizon: str = ""
    source_basis: str = ""
    model_basis: str = ""
    formula: str = ""
    contributing_factors: list[ContributingFactor] = Field(default_factory=list)
    data_recency: str = ""
    confidence_notes: str = ""


class MetricsProvenanceResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/metrics-provenance"""
    run_id: str
    scenario_id: str
    metrics: list[MetricProvenance] = Field(default_factory=list)
    total_metrics: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Factor Breakdown
# ═══════════════════════════════════════════════════════════════════════════════

class FactorContribution(BaseModel):
    """Single driver contributing to a metric."""
    factor_name: str
    factor_name_ar: str = ""
    contribution_value: float
    contribution_pct: float
    rationale_en: str = ""
    rationale_ar: str = ""


class MetricFactorBreakdown(BaseModel):
    """Factor breakdown for a single metric."""
    metric_name: str
    metric_name_ar: str = ""
    metric_value: float
    unit: str
    factors: list[FactorContribution] = Field(default_factory=list)
    factors_sum: float = 0.0
    coverage_pct: float = 0.0


class FactorBreakdownResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/factor-breakdown"""
    run_id: str
    scenario_id: str
    breakdowns: list[MetricFactorBreakdown] = Field(default_factory=list)
    total_metrics: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Metric Range / Uncertainty
# ═══════════════════════════════════════════════════════════════════════════════

class MetricRange(BaseModel):
    """Uncertainty range for a single metric."""
    metric_name: str
    metric_name_ar: str = ""
    min_value: float
    expected_value: float
    max_value: float
    confidence_band: str = ""
    unit: str = ""
    reasoning_en: str = ""
    reasoning_ar: str = ""


class MetricRangesResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/metric-ranges"""
    run_id: str
    scenario_id: str
    ranges: list[MetricRange] = Field(default_factory=list)
    total_metrics: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Decision Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionReasoning(BaseModel):
    """Full reasoning explanation for a single decision."""
    decision_id: str
    action_id: str
    why_this_decision_en: str
    why_this_decision_ar: str = ""
    why_now_en: str
    why_now_ar: str = ""
    why_this_rank_en: str
    why_this_rank_ar: str = ""
    affected_entities: list[str] = Field(default_factory=list)
    propagation_link_en: str = ""
    propagation_link_ar: str = ""
    regime_link_en: str = ""
    regime_link_ar: str = ""
    trust_link_en: str = ""
    trust_link_ar: str = ""
    tradeoff_summary_en: str = ""
    tradeoff_summary_ar: str = ""


class DecisionReasoningResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/decision-reasoning"""
    run_id: str
    scenario_id: str
    reasonings: list[DecisionReasoning] = Field(default_factory=list)
    total_decisions: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  5. Data Basis / Recency
# ═══════════════════════════════════════════════════════════════════════════════

class DataBasis(BaseModel):
    """Data provenance basis for a single metric."""
    metric_name: str
    metric_name_ar: str = ""
    historical_basis_en: str = ""
    historical_basis_ar: str = ""
    scenario_basis_en: str = ""
    scenario_basis_ar: str = ""
    calibration_basis_en: str = ""
    calibration_basis_ar: str = ""
    freshness_flag: str = ""
    freshness_detail_en: str = ""
    freshness_detail_ar: str = ""
    freshness_weak: bool = False
    model_type: str = ""
    analog_event: str = ""
    analog_period: str = ""
    analog_relevance: float = 0.0


class DataBasisResponse(BaseModel):
    """GET /api/v1/runs/{run_id}/data-basis"""
    run_id: str
    scenario_id: str
    data_bases: list[DataBasis] = Field(default_factory=list)
    total_metrics: int = 0
    weak_freshness_count: int = 0
