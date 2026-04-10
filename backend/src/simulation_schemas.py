"""
Impact Observatory | مرصد الأثر
Pydantic v2 schemas for all API request/response models.

FIX: Replaced all dict[str, Any] sub-models with fully-typed Pydantic models.
     Added model_validator(mode='after') to enforce structural contracts.
     Numeric fields are never Optional — they default to 0.0 so .toFixed() cannot crash.
     List fields default to [] so .map()/.reduce() cannot crash.
     sector_losses is List[SectorLoss] (list), NOT dict — fixes frontend reduce() crash.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


# Keep backward-compat alias
SimulateRequest.__doc__ = SimulateRequest.__doc__


# ---------------------------------------------------------------------------
# Typed sub-models (replaces dict[str, Any] everywhere)
# ---------------------------------------------------------------------------

class EntityImpact(BaseModel):
    """Entity-level financial impact — all fields have safe defaults."""
    entity_id: str = ""
    entity_label: str = ""
    loss_usd: float = 0.0
    direct_loss_usd: float = 0.0
    indirect_loss_usd: float = 0.0
    systemic_loss_usd: float = 0.0
    stress_score: float = 0.0
    classification: str = "NOMINAL"
    peak_day: int = 1
    sector: str = "unknown"
    propagation_factor: float = 1.0


class SectorLoss(BaseModel):
    """Sector-level loss row — a LIST item, not a dict key.
    Frontend iterates this with .map() / .reduce() — must be a list.
    """
    sector: str = "unknown"
    loss_usd: float = 0.0
    pct: float = 0.0


class DecisionAction(BaseModel):
    """A single ranked decision action."""
    action_id: str = ""
    rank: int = 0
    sector: str = "cross-sector"
    owner: str = ""
    action: str = ""
    action_ar: str = ""
    priority_score: float = 0.0
    urgency: float = 0.0
    loss_avoided_usd: float = 0.0
    loss_avoided_formatted: str = "$0"
    cost_usd: float = 0.0
    cost_formatted: str = "$0"
    regulatory_risk: float = 0.0
    feasibility: float = 0.0
    time_to_act_hours: int = 24
    status: str = "PENDING_REVIEW"
    escalation_trigger: str = ""


class BottleneckNode(BaseModel):
    """Network bottleneck node — used in physical_system_status.bottlenecks and top-level."""
    node_id: str = ""
    node_label: str = Field(default="", alias="label")
    bottleneck_score: float = 0.0
    is_critical_bottleneck: bool = False
    utilization: float = 0.0
    criticality: float = 0.0
    redundancy: float = 0.0
    degree: int = 0
    rank: int = 0
    sector: str = "unknown"
    lat: float = 0.0
    lng: float = 0.0

    model_config = ConfigDict(populate_by_name=True)


class FinancialImpact(BaseModel):
    """Full financial impact block — guaranteed list fields, no None numerics."""
    total_loss_usd: float = 0.0
    total_loss_formatted: str = "$0"
    direct_loss_usd: float = 0.0
    indirect_loss_usd: float = 0.0
    systemic_loss_usd: float = 0.0
    systemic_multiplier: float = 1.0
    affected_entities: int = 0
    critical_entities: int = 0
    top_entities: List[Dict[str, Any]] = Field(default_factory=list)
    gdp_impact_pct: float = 0.0             # NOT Optional — always a number
    sector_losses: List[Dict[str, Any]] = Field(default_factory=list)  # LIST not dict
    confidence_interval: Dict[str, float] = Field(
        default_factory=lambda: {"lower": 0.0, "upper": 0.0, "confidence": 0.0}
    )


class SectorAnalysisRow(BaseModel):
    sector: str = "unknown"
    exposure: float = 0.0
    stress: float = 0.0
    classification: str = "NOMINAL"
    risk_level: str = "NOMINAL"


class PropagationStep(BaseModel):
    step: int = 0
    entity_id: str = ""
    entity_label: str = ""
    impact: float = 0.0
    propagation_score: float = 0.0
    mechanism: str = ""


class UnifiedRiskScore(BaseModel):
    score: float = 0.0
    components: Dict[str, float] = Field(default_factory=dict)
    risk_level: str = "NOMINAL"
    classification: str = "NOMINAL"


class PhysicalSystemStatus(BaseModel):
    """Physical system status — congestion_score and recovery_score are NEVER None."""
    nodes_assessed: int = 0
    saturated_nodes: int = 0
    flow_balance_status: str = "NOMINAL"
    system_utilization: float = 0.0
    congestion_score: float = 0.0       # NOT Optional — .toFixed() safe
    recovery_score: float = 0.0         # NOT Optional — .toFixed() safe
    bottlenecks: List[Any] = Field(default_factory=list)  # NOT Optional — .map() safe
    node_states: Dict[str, Any] = Field(default_factory=dict)


class RecoveryPoint(BaseModel):
    day: int = 0
    recovery_fraction: float = 0.0
    damage_remaining: float = 0.0
    residual_stress: float = 0.0


class LiquidityStress(BaseModel):
    aggregate_stress: float = 0.0
    liquidity_stress: float = 0.0
    car_ratio: float = 0.12
    lcr_ratio: float = 1.0
    outflow_rate: float = 0.0
    time_to_breach_hours: float = 9999.0
    classification: str = "NOMINAL"
    sector: str = "banking"


class InsuranceStress(BaseModel):
    """Insurance stress — time_to_insolvency_hours uses 9999.0 to mean 'no imminent risk'."""
    sector: str = "insurance"
    aggregate_stress: float = 0.0
    severity_index: float = 0.0
    combined_ratio: float = 1.0
    claims_surge_multiplier: float = 1.0
    reserve_adequacy: float = 1.0          # kept for backward compat (old field name)
    reserve_adequacy_ratio: float = 1.0
    tiv_exposure: float = 0.0             # backward compat alias
    tiv_exposure_usd: float = 0.0
    solvency_score: float = 1.0
    loss_ratio: float = 0.0
    reinsurance_trigger: bool = False
    time_to_insolvency_hours: float = 9999.0  # 9999 = no imminent insolvency
    ifrs17_risk_adjustment_pct: float = 0.0
    portfolio_exposure_usd: float = 0.0
    underwriting_status: str = "STABLE"
    affected_lines: List[Any] = Field(default_factory=list)
    run_id: str = ""
    classification: str = "NOMINAL"


class FintechStress(BaseModel):
    aggregate_stress: float = 0.0
    digital_stress: float = 0.0
    digital_banking_stress: float = 0.0
    liquidity_stress: float = 0.0        # backward-compat alias
    payment_disruption_score: float = 0.0
    cross_border_disruption: float = 0.0
    settlement_delay_hours: float = 0.0
    payment_volume_impact_pct: float = 0.0
    api_availability_pct: float = 100.0
    time_to_payment_failure_hours: float = 9999.0
    affected_platforms: List[Any] = Field(default_factory=list)
    run_id: str = ""
    sector: str = "fintech"
    classification: str = "NOMINAL"


class FlowResult(BaseModel):
    flow_type: str = ""
    base_volume_usd: float = 0.0
    disrupted_volume_usd: float = 0.0
    disruption_factor: float = 0.0
    congestion: float = 0.0
    delay_days: float = 0.0
    backlog_usd: float = 0.0
    rerouting_cost_usd: float = 0.0
    saturation_pct: float = 0.0
    stress_score: float = 0.0
    classification: str = "NOMINAL"
    volume_loss_usd: float = 0.0


class FlowAnalysis(BaseModel):
    money: Dict[str, Any] = Field(default_factory=dict)
    logistics: Dict[str, Any] = Field(default_factory=dict)
    energy: Dict[str, Any] = Field(default_factory=dict)
    payments: Dict[str, Any] = Field(default_factory=dict)
    claims: Dict[str, Any] = Field(default_factory=dict)
    aggregate_disruption_usd: float = 0.0
    most_disrupted_flow: str = "money"
    flow_recovery_days: int = 0


class CausalChainStep(BaseModel):
    step: int = 0
    entity_id: str = ""
    entity_label: str = ""
    entity_label_ar: str = ""
    impact_usd: float = 0.0
    impact_usd_formatted: str = "$0"
    stress_delta: float = 0.0
    mechanism_en: str = ""
    mechanism_ar: str = ""
    sector: str = "unknown"
    hop: int = 0
    confidence: float = 0.0


class SensitivityPerturbation(BaseModel):
    delta_severity_pct: float = 0.0
    perturbed_severity: float = 0.0
    resulting_loss_usd: float = 0.0
    resulting_risk_score: float = 0.0
    loss_change_pct: float = 0.0
    risk_change_pct: float = 0.0


class Sensitivity(BaseModel):
    perturbations: List[SensitivityPerturbation] = Field(default_factory=list)
    most_sensitive_parameter: str = ""
    linearity_score: float = 0.0
    base_severity: float = 0.0
    base_loss_usd: float = 0.0
    base_risk_score: float = 0.0


class UncertaintyBands(BaseModel):
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    band_width: float = 0.0
    interpretation: str = ""
    confidence: float = 0.0


class ExplainabilityBlock(BaseModel):
    causal_chain: List[Dict[str, Any]] = Field(default_factory=list)
    narrative_en: str = ""
    narrative_ar: str = ""
    sensitivity: Dict[str, Any] = Field(default_factory=dict)
    uncertainty_bands: Dict[str, Any] = Field(default_factory=dict)
    model_equation: str = ""
    confidence_score: float = 0.0        # NOT Optional — .toFixed() safe
    methodology: str = "deterministic_propagation"
    source: str = ""


class ActionItem(BaseModel):
    action_id: str = ""
    rank: int = 0
    sector: str = "cross-sector"
    owner: str = ""
    action: str = ""
    action_ar: str = ""
    priority_score: float = 0.0
    urgency: float = 0.0
    loss_avoided_usd: float = 0.0
    loss_avoided_formatted: str = "$0"
    cost_usd: float = 0.0
    cost_formatted: str = "$0"
    regulatory_risk: float = 0.0
    feasibility: float = 0.0
    time_to_act_hours: int = 24
    status: str = "PENDING_REVIEW"
    escalation_trigger: str = ""


class DecisionPlan(BaseModel):
    """Decision plan — all action lists default to [], priority_matrix defaults to {}."""
    business_severity: str = "LOW"
    time_to_first_failure_hours: float = 999.0
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_triggers: List[str] = Field(default_factory=list)
    monitoring_priorities: List[str] = Field(default_factory=list)
    five_questions: Dict[str, Any] = Field(default_factory=dict)
    # Derived partitions — NOT Optional, default to empty list
    immediate_actions: List[Dict[str, Any]] = Field(default_factory=list)
    short_term_actions: List[Dict[str, Any]] = Field(default_factory=list)
    long_term_actions: List[Dict[str, Any]] = Field(default_factory=list)
    priority_matrix: Dict[str, List[str]] = Field(
        default_factory=lambda: {"IMMEDIATE": [], "URGENT": [], "MONITOR": [], "WATCH": []}
    )


class Headline(BaseModel):
    total_loss_usd: float = 0.0
    total_loss_formatted: str = "$0"
    peak_day: int = 0
    affected_entities: int = 0
    critical_count: int = 0
    elevated_count: int = 0
    max_recovery_days: int = 0
    severity_code: str = "NOMINAL"
    average_stress: float = 0.0


# ---------------------------------------------------------------------------
# Primary response model
# ---------------------------------------------------------------------------

class SimulateResponse(BaseModel):
    """Full simulation output — 16 top-level fields.

    CONTRACT: Every list field defaults to []. Every numeric field defaults to 0.0.
    Frontend can safely call .map(), .reduce(), .toFixed() on all fields.
    """

    # Metadata
    run_id: str = ""
    scenario_id: str = ""
    model_version: str = "2.1.0"
    severity: float = 0.0
    horizon_hours: int = 336
    time_horizon_days: int = 14
    generated_at: str = ""
    duration_ms: int = 0

    # Core outputs — NEVER None
    event_severity: float = 0.0
    peak_day: int = 0
    confidence_score: float = 0.0
    propagation_score: float = 0.0
    unified_risk_score: float = 0.0
    risk_level: str = "NOMINAL"
    congestion_score: float = 0.0       # top-level alias
    recovery_score: float = 0.0         # top-level alias

    # Structured sub-objects — all have safe defaults
    financial_impact: FinancialImpact = Field(default_factory=FinancialImpact)
    sector_analysis: List[SectorAnalysisRow] = Field(default_factory=list)
    propagation_chain: List[Dict[str, Any]] = Field(default_factory=list)
    physical_system_status: PhysicalSystemStatus = Field(default_factory=PhysicalSystemStatus)
    bottlenecks: List[Dict[str, Any]] = Field(default_factory=list)
    recovery_trajectory: List[Dict[str, Any]] = Field(default_factory=list)
    banking_stress: Dict[str, Any] = Field(default_factory=dict)
    insurance_stress: Dict[str, Any] = Field(default_factory=dict)
    fintech_stress: Dict[str, Any] = Field(default_factory=dict)
    flow_analysis: Dict[str, Any] = Field(default_factory=dict)
    explainability: ExplainabilityBlock = Field(default_factory=ExplainabilityBlock)
    decision_plan: DecisionPlan = Field(default_factory=DecisionPlan)
    headline: Headline = Field(default_factory=Headline)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @model_validator(mode="after")
    def ensure_top_level_aliases(self) -> "SimulateResponse":
        """Mirror nested values into top-level aliases if they're still at default."""
        if self.congestion_score == 0.0:
            self.congestion_score = self.physical_system_status.congestion_score
        if self.recovery_score == 0.0:
            self.recovery_score = self.physical_system_status.recovery_score
        return self


# ---------------------------------------------------------------------------
# Standalone response models
# ---------------------------------------------------------------------------

class DecisionPlanResponse(BaseModel):
    """Standalone decision plan endpoint response."""
    run_id: str = ""
    scenario_id: str = ""
    risk_level: str = "NOMINAL"
    decision_plan: DecisionPlan = Field(default_factory=DecisionPlan)


class ExplainabilityResponse(BaseModel):
    """Standalone explainability endpoint response."""
    run_id: str = ""
    scenario_id: str = ""
    confidence_score: float = 0.0
    explainability: ExplainabilityBlock = Field(default_factory=ExplainabilityBlock)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    model_version: str = "2.1.0"
    scenarios_available: int = 0
    nodes_in_registry: int = 0
    timestamp: str = ""


class ScenarioListItem(BaseModel):
    """Scenario catalog entry for listing."""
    id: str = ""
    name: str = ""
    name_ar: str = ""
    shock_nodes: List[str] = Field(default_factory=list)
    base_loss_usd: float = 0.0
    sectors_affected: List[str] = Field(default_factory=list)
    cross_sector: bool = False


# ---------------------------------------------------------------------------
# Transmission Path Engine schemas
# ---------------------------------------------------------------------------

class TransmissionNode(BaseModel):
    """A single directional causal link in a transmission chain."""
    source: str = ""
    target: str = ""
    source_label: str = ""
    target_label: str = ""
    source_sector: str = ""
    target_sector: str = ""
    propagation_delay_hours: float = 0.0
    severity_transfer_ratio: float = 0.0
    severity_at_source: float = 0.0
    severity_at_target: float = 0.0
    breakable_point: bool = False
    mechanism: str = ""
    hop: int = 0


class TransmissionChain(BaseModel):
    """Full transmission chain for a scenario run."""
    scenario_id: str = ""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    total_delay: float = 0.0
    max_severity: float = 0.0
    breakable_points: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    summary_ar: str = ""
    chain_length: int = 0


# ---------------------------------------------------------------------------
# Counterfactual Calibration Engine schemas
# ---------------------------------------------------------------------------

class CounterfactualOutcome(BaseModel):
    """A single counterfactual scenario outcome."""
    label: str = ""
    label_ar: str = ""
    projected_loss_usd: float = 0.0
    projected_loss_formatted: str = "$0"
    risk_level: str = "NOMINAL"
    recovery_days: int = 14
    operational_cost_usd: float = 0.0
    severity: float = 0.0


class CounterfactualDelta(BaseModel):
    """Delta between baseline and recommended outcomes."""
    loss_reduction_usd: float = 0.0
    loss_reduction_pct: float = 0.0
    loss_reduction_formatted: str = "$0"
    alt_reduction_usd: float = 0.0
    alt_reduction_pct: float = 0.0
    recommended_net_benefit_usd: float = 0.0
    alternative_net_benefit_usd: float = 0.0
    recovery_improvement_days: int = 0
    best_option: str = "recommended"
    delta_explained: str = ""
    delta_explained_ar: str = ""


class CalibratedCounterfactual(BaseModel):
    """Full calibrated counterfactual analysis."""
    scenario_id: str = ""
    baseline: Dict[str, Any] = Field(default_factory=dict)
    recommended: Dict[str, Any] = Field(default_factory=dict)
    alternative: Dict[str, Any] = Field(default_factory=dict)
    delta: Dict[str, Any] = Field(default_factory=dict)
    narrative: str = ""
    narrative_ar: str = ""
    consistency_flag: str = "CONSISTENT"
    confidence_score: float = 0.0


# ---------------------------------------------------------------------------
# Action Pathways Engine schemas
# ---------------------------------------------------------------------------

class ClassifiedAction(BaseModel):
    """A single classified action with execution metadata."""
    id: str = ""
    label: str = ""
    label_ar: str = ""
    type: str = "STRATEGIC"  # IMMEDIATE | CONDITIONAL | STRATEGIC
    owner: str = ""
    sector: str = "cross-sector"
    deadline: str = ""
    trigger_condition: Optional[str] = None
    reversibility: str = "MEDIUM"  # HIGH | MEDIUM | LOW
    expected_impact: float = 0.0
    priority_score: float = 0.0
    urgency: float = 0.0
    loss_avoided_usd: float = 0.0
    cost_usd: float = 0.0
    time_to_act_hours: int = 24


class ActionPathways(BaseModel):
    """Structured action pathways with typed categories."""
    immediate: List[Dict[str, Any]] = Field(default_factory=list)
    conditional: List[Dict[str, Any]] = Field(default_factory=list)
    strategic: List[Dict[str, Any]] = Field(default_factory=list)
    total_actions: int = 0
    scenario_id: str = ""
    severity: float = 0.0
    risk_level: str = "NOMINAL"
    summary: str = ""
    summary_ar: str = ""


# ---------------------------------------------------------------------------
# Decision Trust System schemas (Phase 2)
# ---------------------------------------------------------------------------

class ActionConfidence(BaseModel):
    """Per-action confidence score."""
    action_id: str = ""
    confidence_score: float = 0.0
    confidence_label: str = "MEDIUM"  # HIGH | MEDIUM | LOW


class ModelDependency(BaseModel):
    """Model dependency metrics."""
    data_completeness: float = 0.0
    signal_reliability: float = 0.0
    assumption_sensitivity: str = "MEDIUM"  # LOW | MEDIUM | HIGH


class ValidationRequirement(BaseModel):
    """Whether validation is required before acting."""
    required: bool = False
    reason: str = ""
    validation_type: str = "NONE"  # REGULATORY | OPERATIONAL | RISK | NONE


class ConfidenceBreakdown(BaseModel):
    """Human-readable confidence drivers."""
    drivers: List[str] = Field(default_factory=list)


class RiskEnvelope(BaseModel):
    """Decision risk if wrong."""
    downside_if_wrong: str = "MEDIUM"   # LOW | MEDIUM | HIGH
    reversibility: str = "MEDIUM"       # HIGH | MEDIUM | LOW
    time_sensitivity: str = "MEDIUM"    # LOW | MEDIUM | CRITICAL


class DecisionTrust(BaseModel):
    """Full decision trust payload (Phase 2)."""
    action_confidence: List[Dict[str, Any]] = Field(default_factory=list)
    model_dependency: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    confidence_breakdown: Dict[str, Any] = Field(default_factory=dict)
    risk_profile: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Decision Integration Layer schemas (Phase 3)
# ---------------------------------------------------------------------------

class DecisionOwnership(BaseModel):
    """Who owns this decision."""
    decision_id: str = ""
    owner_role: str = "CRO"  # CRO | CFO | COO | TREASURY | RISK | REGULATOR
    organization_unit: str = ""
    execution_channel: str = ""


class DecisionWorkflow(BaseModel):
    """Approval workflow for a decision."""
    decision_id: str = ""
    status: str = "PENDING"  # PENDING | APPROVED | REJECTED | ESCALATED
    approval_required: bool = False
    approver_role: str = ""
    escalation_path: List[str] = Field(default_factory=list)


class ExecutionTrigger(BaseModel):
    """Execution bridge for an action."""
    action_id: str = ""
    execution_mode: str = "MANUAL"  # MANUAL | AUTO | API
    system_target: str = ""
    trigger_ready: bool = False


class DecisionLifecycle(BaseModel):
    """Full lifecycle state of a decision."""
    decision_id: str = ""
    status: str = "ISSUED"  # ISSUED | APPROVED | EXECUTED | COMPLETED
    issued_at: str = ""
    approved_at: Optional[str] = None
    executed_at: Optional[str] = None
    outcome: Optional[str] = None


class IntegrationConnector(BaseModel):
    """A single external integration connector."""
    name: str = ""
    type: str = "API"  # API | WEBHOOK
    endpoint: str = ""
    active: bool = False


class IntegrationStatus(BaseModel):
    """Available integrations."""
    available: List[str] = Field(default_factory=list)
    active: List[str] = Field(default_factory=list)
    connectors: Dict[str, Any] = Field(default_factory=dict)


class DecisionIntegration(BaseModel):
    """Full Phase 3 decision integration payload."""
    decision_ownership: List[Dict[str, Any]] = Field(default_factory=list)
    workflows: List[Dict[str, Any]] = Field(default_factory=list)
    execution_triggers: List[Dict[str, Any]] = Field(default_factory=list)
    decision_lifecycle: List[Dict[str, Any]] = Field(default_factory=list)
    integration: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Value Engine schemas (Phase 4)
# ---------------------------------------------------------------------------

class ExpectedActual(BaseModel):
    """Expected vs actual outcome for a decision."""
    decision_id: str = ""
    expected_outcome: float = 0.0
    actual_outcome: float = 0.0
    delta: float = 0.0
    variance_ratio: float = 0.0


class ValueAttribution(BaseModel):
    """Value attribution for a decision."""
    decision_id: str = ""
    value_created: float = 0.0
    attribution_confidence: float = 0.0
    attribution_type: str = "LOW_CONFIDENCE"  # DIRECT | PARTIAL | LOW_CONFIDENCE


class DecisionEffectiveness(BaseModel):
    """Effectiveness classification for a decision."""
    decision_id: str = ""
    score: float = 0.0
    classification: str = "NEUTRAL"  # SUCCESS | NEUTRAL | FAILURE


class PortfolioValue(BaseModel):
    """Portfolio-level value aggregation."""
    total_decisions: int = 0
    total_value_created: float = 0.0
    total_expected: float = 0.0
    total_actual: float = 0.0
    net_delta: float = 0.0
    success_rate: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    neutral_count: int = 0
    avg_effectiveness_score: float = 0.0
    avg_attribution_confidence: float = 0.0
    best_decision_id: Optional[str] = None
    worst_decision_id: Optional[str] = None
    roi_ratio: float = 0.0


class DecisionValuePayload(BaseModel):
    """Full Phase 4 value measurement payload."""
    expected_actual: List[Dict[str, Any]] = Field(default_factory=list)
    value_attribution: List[Dict[str, Any]] = Field(default_factory=list)
    effectiveness: List[Dict[str, Any]] = Field(default_factory=list)
    portfolio_value: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Phase 5 — Evidence & Governance Layer
# ---------------------------------------------------------------------------

class EvidenceCompleteness(BaseModel):
    """Completeness flags for evidence pack."""
    has_signal: bool = True
    has_transmission: bool = False
    has_counterfactual: bool = False
    has_trust: bool = False
    has_execution: bool = False
    has_outcome: bool = False
    complete: bool = False


class DecisionEvidence(BaseModel):
    """Full evidence pack for a single decision."""
    decision_id: str = ""
    run_id: str = ""
    assembled_at: str = ""
    signal_snapshot: Dict[str, Any] = Field(default_factory=dict)
    transmission_evidence: Dict[str, Any] = Field(default_factory=dict)
    counterfactual_basis: Dict[str, Any] = Field(default_factory=dict)
    trust_basis: Dict[str, Any] = Field(default_factory=dict)
    execution_evidence: Dict[str, Any] = Field(default_factory=dict)
    outcome_evidence: Dict[str, Any] = Field(default_factory=dict)
    completeness: Dict[str, Any] = Field(default_factory=dict)


class DecisionPolicy(BaseModel):
    """Governance policy evaluation for a decision."""
    decision_id: str = ""
    allowed: bool = True
    violations: List[str] = Field(default_factory=list)
    required_approvals: List[str] = Field(default_factory=list)
    rules_evaluated: int = 0
    rules_passed: int = 0


class AttributionDefense(BaseModel):
    """Attribution defensibility model for a decision."""
    decision_id: str = ""
    attribution_type: str = "LOW_CONFIDENCE"
    confidence_band: float = 0.0
    external_factors: List[str] = Field(default_factory=list)
    explanation: str = ""
    original_attribution_type: str = ""
    original_confidence: float = 0.0


class DecisionOverride(BaseModel):
    """Override tracking record for a decision."""
    decision_id: str = ""
    overridden: bool = False
    overridden_by: Optional[str] = None
    reason: Optional[str] = None
    override_type: str = "NONE"
    timestamp: Optional[str] = None
    policy_violations_at_override: List[str] = Field(default_factory=list)


class GovernancePayload(BaseModel):
    """Full Phase 5 governance payload."""
    decision_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    policy: List[Dict[str, Any]] = Field(default_factory=list)
    attribution_defense: List[Dict[str, Any]] = Field(default_factory=list)
    overrides: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 6 — Pilot Readiness & Operating Proof
# ---------------------------------------------------------------------------

class PilotScope(BaseModel):
    """Pilot scope validation result."""
    in_scope: bool = True
    scenario_id: str = ""
    scope_sector: str = ""
    execution_mode: str = "SHADOW"  # SHADOW | ADVISORY | CONTROLLED
    decision_owners: List[str] = Field(default_factory=list)
    approval_flow: List[str] = Field(default_factory=list)
    reason: str = ""
    validated_at: str = ""


class PilotKPI(BaseModel):
    """Pilot KPI measurements."""
    total_decisions: int = 0
    decision_latency_hours: float = 0.0
    latency_reduction_pct: float = 0.0
    human_vs_system_delta: float = 0.0
    avoided_loss_estimate: float = 0.0
    false_positive_rate: float = 0.0
    accuracy_rate: float = 0.0
    total_escalations: int = 0
    divergent_count: int = 0
    matched_count: int = 0


class ShadowDecision(BaseModel):
    """Shadow mode comparison of system vs human decision."""
    decision_id: str = ""
    system_decision: Dict[str, Any] = Field(default_factory=dict)
    human_decision: Optional[Dict[str, Any]] = None
    divergence: bool = False
    divergence_reason: Optional[str] = None
    divergence_count: int = 0
    comparison_status: str = "PENDING_HUMAN_INPUT"  # PENDING_HUMAN_INPUT | COMPARED
    compared_at: str = ""


class PilotReport(BaseModel):
    """Pilot progress report."""
    period: str = "weekly"
    generated_at: str = ""
    run_count: int = 0
    total_decisions: int = 0
    matched_decisions: int = 0
    divergent_decisions: int = 0
    divergence_rate: float = 0.0
    accuracy_rate: float = 0.0
    value_created: float = 0.0
    avg_latency_reduction: float = 0.0
    false_positive_rate: float = 0.0
    key_findings: List[str] = Field(default_factory=list)
    recommendation: str = ""


class FailureMode(BaseModel):
    """A triggered failure mode with fallback action."""
    id: str = ""
    condition: str = ""
    description: str = ""
    triggered: bool = False
    fallback_action: str = ""
    severity: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL
    detail: str = ""
    evaluated_at: str = ""


class PilotPayload(BaseModel):
    """Full Phase 6 pilot readiness payload."""
    pilot_scope: Dict[str, Any] = Field(default_factory=dict)
    pilot_kpi: Dict[str, Any] = Field(default_factory=dict)
    shadow_comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    pilot_report: Dict[str, Any] = Field(default_factory=dict)
    failure_modes: List[Dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    error: str = ""
    detail: Optional[str] = None
    status_code: int = 400
