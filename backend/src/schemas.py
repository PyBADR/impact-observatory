"""
Impact Observatory | مرصد الأثر
Pydantic v2 schemas for all API request/response models.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    """Request body for POST /simulate."""

    scenario_id: str = Field(
        ...,
        description="Scenario identifier from the scenario catalog.",
        examples=["hormuz_chokepoint_disruption"],
    )
    severity: float = Field(
        ...,
        ge=0.01,
        le=1.0,
        description="Base severity of the event [0.01–1.0].",
        examples=[0.75],
    )
    horizon_hours: int = Field(
        default=336,
        ge=24,
        le=2160,
        description="Simulation horizon in hours (24h–2160h / 14 days–90 days).",
    )
    label: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional human-readable run label.",
    )

    @field_validator("scenario_id")
    @classmethod
    def scenario_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scenario_id must not be empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class EntityImpact(BaseModel):
    entity_id: str
    entity_label: str
    loss_usd: float
    direct_loss_usd: float
    indirect_loss_usd: float
    systemic_loss_usd: float
    stress_score: float
    classification: str
    peak_day: int
    sector: str
    propagation_factor: float


class FinancialImpact(BaseModel):
    total_loss_usd: float
    total_loss_formatted: str
    direct_loss_usd: float
    indirect_loss_usd: float
    systemic_loss_usd: float
    systemic_multiplier: float
    affected_entities: int
    critical_entities: int
    top_entities: list[dict[str, Any]]


class SectorAnalysisRow(BaseModel):
    sector: str
    exposure: float
    stress: float
    classification: str
    risk_level: str


class PropagationStep(BaseModel):
    step: int
    entity_id: str
    entity_label: str
    impact: float
    propagation_score: float
    mechanism: str


class UnifiedRiskScore(BaseModel):
    score: float
    components: dict[str, float]
    risk_level: str
    classification: str


class BottleneckNode(BaseModel):
    node_id: str
    label: str
    bottleneck_score: float
    is_critical_bottleneck: bool
    utilization: float
    criticality: float
    redundancy: float
    degree: int
    rank: int


class PhysicalSystemStatus(BaseModel):
    nodes_assessed: int
    saturated_nodes: int
    flow_balance_status: str
    system_utilization: float


class RecoveryPoint(BaseModel):
    day: int
    recovery_fraction: float
    damage_remaining: float
    residual_stress: float


class LiquidityStress(BaseModel):
    aggregate_stress: float
    liquidity_stress: float
    car_ratio: float
    lcr_ratio: float
    outflow_rate: float
    time_to_breach_hours: float
    classification: str
    sector: str


class InsuranceStress(BaseModel):
    severity_index: float
    claims_surge_multiplier: float
    combined_ratio: float
    reserve_adequacy: float
    tiv_exposure: float
    loss_ratio: float
    classification: str
    sector: str


class FintechStress(BaseModel):
    aggregate_stress: float
    liquidity_stress: float
    sector: str
    classification: str


class FlowResult(BaseModel):
    flow_type: str
    base_volume_usd: float
    disrupted_volume_usd: float
    disruption_factor: float
    congestion: float
    delay_days: float
    backlog_usd: float
    rerouting_cost_usd: float
    saturation_pct: float
    stress_score: float
    classification: str
    volume_loss_usd: float


class FlowAnalysis(BaseModel):
    money: dict[str, Any]
    logistics: dict[str, Any]
    energy: dict[str, Any]
    payments: dict[str, Any]
    claims: dict[str, Any]
    aggregate_disruption_usd: float
    most_disrupted_flow: str
    flow_recovery_days: int


class CausalChainStep(BaseModel):
    step: int
    entity_id: str
    entity_label: str
    entity_label_ar: str
    impact_usd: float
    impact_usd_formatted: str
    stress_delta: float
    mechanism_en: str
    mechanism_ar: str
    sector: str
    hop: int
    confidence: float


class SensitivityPerturbation(BaseModel):
    delta_severity_pct: float
    perturbed_severity: float
    resulting_loss_usd: float
    resulting_risk_score: float
    loss_change_pct: float
    risk_change_pct: float


class Sensitivity(BaseModel):
    perturbations: list[SensitivityPerturbation]
    most_sensitive_parameter: str
    linearity_score: float
    base_severity: float
    base_loss_usd: float
    base_risk_score: float


class UncertaintyBands(BaseModel):
    lower_bound: float
    upper_bound: float
    band_width: float
    interpretation: str
    confidence: float


class ExplainabilityBlock(BaseModel):
    causal_chain: list[dict[str, Any]]
    narrative_en: str
    narrative_ar: str
    sensitivity: dict[str, Any]
    uncertainty_bands: dict[str, Any]
    model_equation: str


class ActionItem(BaseModel):
    action_id: str
    rank: int
    sector: str
    owner: str
    action: str
    action_ar: str
    priority_score: float
    urgency: float
    loss_avoided_usd: float
    loss_avoided_formatted: str
    cost_usd: float
    cost_formatted: str
    regulatory_risk: float
    feasibility: float
    time_to_act_hours: int
    status: str
    escalation_trigger: str


class DecisionPlan(BaseModel):
    business_severity: str
    time_to_first_failure_hours: float
    actions: list[dict[str, Any]]
    escalation_triggers: list[str]
    monitoring_priorities: list[str]
    five_questions: dict[str, Any]


class Headline(BaseModel):
    total_loss_usd: float
    total_loss_formatted: str
    peak_day: int
    affected_entities: int
    critical_count: int
    severity_code: str
    average_stress: float


# ---------------------------------------------------------------------------
# Primary response model
# ---------------------------------------------------------------------------

class SimulateResponse(BaseModel):
    """Full simulation output — 16 top-level fields."""

    # Metadata
    run_id: str
    scenario_id: str
    model_version: str
    severity: float
    horizon_hours: int
    time_horizon_days: int
    generated_at: str
    duration_ms: int

    # Core outputs
    event_severity: float
    peak_day: int
    confidence_score: float

    # Financial
    financial_impact: FinancialImpact

    # Sector
    sector_analysis: list[SectorAnalysisRow]

    # Propagation
    propagation_score: float
    propagation_chain: list[dict[str, Any]]

    # Risk
    unified_risk_score: float
    risk_level: str

    # Physics
    physical_system_status: PhysicalSystemStatus
    bottlenecks: list[dict[str, Any]]
    congestion_score: float
    recovery_score: float
    recovery_trajectory: list[dict[str, Any]]

    # Sector stress
    banking_stress: dict[str, Any]
    insurance_stress: dict[str, Any]
    fintech_stress: dict[str, Any]
    flow_analysis: dict[str, Any]

    # Explainability
    explainability: ExplainabilityBlock

    # Decision
    decision_plan: DecisionPlan

    # Headline
    headline: Headline

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Standalone response models
# ---------------------------------------------------------------------------

class DecisionPlanResponse(BaseModel):
    """Standalone decision plan endpoint response."""
    run_id: str
    scenario_id: str
    risk_level: str
    decision_plan: DecisionPlan


class ExplainabilityResponse(BaseModel):
    """Standalone explainability endpoint response."""
    run_id: str
    scenario_id: str
    confidence_score: float
    explainability: ExplainabilityBlock


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    model_version: str
    scenarios_available: int
    nodes_in_registry: int
    timestamp: str


class ScenarioListItem(BaseModel):
    """Scenario catalog entry for listing."""
    id: str
    name: str
    name_ar: str
    shock_nodes: list[str]
    base_loss_usd: float
    sectors_affected: list[str]
    cross_sector: bool


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    error: str
    detail: Optional[str] = None
    status_code: int = 400
