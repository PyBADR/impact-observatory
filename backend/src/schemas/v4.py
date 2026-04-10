"""Impact Observatory | مرصد الأثر — v4 Canonical Schema.

This module is the CANONICAL source of truth for all v4 Pydantic models.
Existing per-file schemas (entity.py, edge.py, etc.) remain for backward
compatibility with v1 consumers.  All new code MUST import from here.

Schema version: 4.0
Pydantic: v2 (BaseModel + ConfigDict)
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import ConfigDict, Field

from src.schemas.base import VersionedModel


# ── helpers ────────────────────────────────────────────────────────────────────

_V4 = "4.0"


class _V4Model(VersionedModel):
    """Private base that pins schema_version to 4.0 for every v4 model."""

    schema_version: str = Field(default=_V4, description="Schema version for audit trail")

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )


# ── RBAC ───────────────────────────────────────────────────────────────────────

class Role(str, Enum):
    """RBAC roles for the Impact Observatory platform."""

    viewer = "viewer"
    analyst = "analyst"
    operator = "operator"
    admin = "admin"
    regulator = "regulator"


# ── 1. RegulatoryProfile ──────────────────────────────────────────────────────

class RegulatoryProfile(_V4Model):
    """Jurisdiction-specific regulatory thresholds applied to a scenario."""

    jurisdiction: str = Field(..., description="ISO country / region code")
    regulatory_version: str = Field(..., description="Regulatory framework version identifier")

    # Banking
    lcr_min: float = Field(..., ge=0.0, description="Minimum Liquidity Coverage Ratio")
    nsfr_min: float = Field(..., ge=0.0, description="Minimum Net Stable Funding Ratio")
    cet1_min: float = Field(..., ge=0.0, description="Minimum CET1 ratio")
    capital_adequacy_min: float = Field(..., ge=0.0, description="Minimum Capital Adequacy Ratio")

    # Insurance
    insurance_solvency_min: float = Field(..., ge=0.0, description="Minimum insurance solvency ratio")
    insurance_reserve_min: float = Field(..., ge=0.0, description="Minimum insurance reserve ratio")

    # Fintech
    fintech_availability_min: float = Field(..., ge=0.0, le=1.0, description="Minimum fintech service availability")
    settlement_delay_max_minutes: int = Field(..., ge=0, description="Maximum settlement delay in minutes")


# ── 2. EntityV4 ───────────────────────────────────────────────────────────────

class EntityV4(_V4Model):
    """A node in the v4 entity graph."""

    entity_id: str = Field(..., description="UUIDv7 identifier")
    entity_type: Literal["bank", "insurer", "fintech", "market_infrastructure"] = Field(
        ..., description="Entity sector type"
    )
    name: str = Field(..., description="Human-readable entity name")
    jurisdiction: str = Field(..., description="ISO jurisdiction code")

    exposure: float = Field(..., description="Total exposure (monetary)")
    capital_buffer: float = Field(..., description="Available capital buffer (monetary)")
    liquidity_buffer: float = Field(..., description="Available liquidity buffer (monetary)")
    capacity: float = Field(..., description="Processing / throughput capacity (monetary)")

    availability: float = Field(..., ge=0.0, le=1.0, description="Service availability ratio")
    route_efficiency: float = Field(..., ge=0.0, le=1.0, description="Routing efficiency ratio")
    criticality: float = Field(..., ge=0.0, le=1.0, description="Systemic criticality score")

    regulatory_classification: Literal["systemic", "material", "standard"] = Field(
        ..., description="Regulatory importance tier"
    )
    active: bool = Field(True, description="Whether the entity is active in the graph")


# ── 3. EdgeV4 ─────────────────────────────────────────────────────────────────

class EdgeV4(_V4Model):
    """A directed relationship between two entities in the v4 graph."""

    edge_id: str = Field(..., description="Unique edge identifier")
    source_entity_id: str = Field(..., description="Source entity UUIDv7")
    target_entity_id: str = Field(..., description="Target entity UUIDv7")

    relation_type: Literal["funding", "payment", "insurance", "technology", "market"] = Field(
        ..., description="Edge relationship type"
    )

    exposure: float = Field(..., description="Exposure along this edge (monetary)")
    transmission_coefficient: float = Field(
        ..., ge=0.0, le=1.0, description="Shock transmission coefficient"
    )
    capacity: float = Field(..., description="Edge throughput capacity (monetary)")
    availability: float = Field(..., ge=0.0, le=1.0, description="Edge availability ratio")
    route_efficiency: float = Field(..., ge=0.0, le=1.0, description="Edge routing efficiency")
    latency_ms: int = Field(..., ge=0, description="Edge latency in milliseconds")
    active: bool = Field(True, description="Whether the edge is active")


# ── 4. ScenarioV4 ─────────────────────────────────────────────────────────────

class ScenarioV4(_V4Model):
    """A complete scenario definition with embedded graph and shock parameters."""

    scenario_id: str = Field(..., description="Unique scenario identifier")
    scenario_version: str = Field(..., description="Scenario revision version")
    name: str = Field(..., description="Human-readable scenario name")
    description: str = Field("", description="Scenario description")
    as_of_date: str = Field(..., description="Valuation / reference date (ISO 8601)")
    horizon_days: int = Field(..., ge=1, le=365, description="Simulation horizon in days")
    currency: str = Field("USD", description="Base currency ISO code")

    # Shock parameters
    shock_intensity: float = Field(..., ge=0.0, le=5.0, description="Overall shock intensity")
    market_liquidity_haircut: float = Field(
        ..., ge=0.0, le=1.0, description="Market-wide liquidity haircut"
    )
    deposit_run_rate: float = Field(..., ge=0.0, le=1.0, description="Deposit run rate")
    claims_spike_rate: float = Field(..., ge=0.0, le=1.0, description="Insurance claims spike rate")
    fraud_loss_rate: float = Field(..., ge=0.0, le=1.0, description="Fintech fraud loss rate")

    # Embedded sub-objects
    regulatory_profile: RegulatoryProfile = Field(..., description="Regulatory thresholds")
    entities: list[EntityV4] = Field(default_factory=list, description="Graph nodes")
    edges: list[EdgeV4] = Field(default_factory=list, description="Graph edges")

    # Audit
    created_by: str = Field(..., description="Creator identifier")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    status: Literal["draft", "active", "archived"] = Field(
        "draft", description="Scenario lifecycle status"
    )


# ── 5. FlowStateV4 ────────────────────────────────────────────────────────────

class FlowStateV4(_V4Model):
    """Point-in-time flow snapshot for a single entity."""

    timestamp: str = Field(..., description="ISO 8601 timestamp")
    entity_id: str = Field(..., description="Entity UUIDv7")

    inbound_flow: float = Field(..., description="Total inbound flow (monetary)")
    outbound_flow: float = Field(..., description="Total outbound flow (monetary)")
    net_flow: float = Field(..., description="Net flow = inbound - outbound")
    capacity: float = Field(..., description="Entity throughput capacity")
    availability: float = Field(..., ge=0.0, le=1.0, description="Service availability")
    route_efficiency: float = Field(..., ge=0.0, le=1.0, description="Routing efficiency")
    computed_flow: float = Field(..., description="Engine-computed effective flow")

    flow_status: Literal["nominal", "degraded", "interrupted"] = Field(
        ..., description="Flow health status"
    )


# ── 6. FinancialImpactV4 ──────────────────────────────────────────────────────

class FinancialImpactV4(_V4Model):
    """Financial impact assessment for a single entity at a point in time."""

    entity_id: str = Field(..., description="Entity UUIDv7")
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    exposure: float = Field(..., description="Total exposure (monetary)")
    shock_intensity: float = Field(..., ge=0.0, le=5.0, description="Applied shock intensity")
    propagation_factor: float = Field(
        ..., ge=0.0, le=5.0, description="Cumulative propagation multiplier"
    )

    loss: float = Field(..., description="Computed loss (monetary)")
    revenue_at_risk: float = Field(..., description="Revenue at risk (monetary)")
    capital_after_loss: float = Field(..., description="Capital remaining after loss")
    liquidity_after_loss: float = Field(..., description="Liquidity remaining after loss")

    impact_status: Literal["stable", "watch", "breach", "default"] = Field(
        ..., description="Impact severity classification"
    )


# ── 7-8. Banking Stress ───────────────────────────────────────────────────────

class BankingBreachFlags(_V4Model):
    """Boolean flags indicating which banking regulatory thresholds are breached."""

    lcr_breach: bool = Field(False, description="LCR below minimum")
    nsfr_breach: bool = Field(False, description="NSFR below minimum")
    cet1_breach: bool = Field(False, description="CET1 ratio below minimum")
    car_breach: bool = Field(False, description="Capital Adequacy Ratio below minimum")


class BankingStressV4(_V4Model):
    """Banking-sector stress metrics for a single entity."""

    entity_id: str = Field(..., description="Entity UUIDv7")
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    deposit_outflow: float = Field(..., description="Deposit outflow (monetary)")
    wholesale_funding_outflow: float = Field(
        ..., description="Wholesale funding outflow (monetary)"
    )
    hqla: float = Field(..., description="High-Quality Liquid Assets (monetary)")
    projected_cash_outflows_30d: float = Field(
        ..., description="Projected cash outflows over 30 days"
    )
    projected_cash_inflows_30d: float = Field(
        ..., description="Projected cash inflows over 30 days"
    )

    lcr: float = Field(..., description="Liquidity Coverage Ratio")
    nsfr: float = Field(..., description="Net Stable Funding Ratio")
    cet1_ratio: float = Field(..., description="CET1 capital ratio")
    capital_adequacy_ratio: float = Field(..., description="Capital Adequacy Ratio")

    breach_flags: BankingBreachFlags = Field(
        default_factory=BankingBreachFlags, description="Regulatory breach flags"
    )


# ── 9-10. Insurance Stress ────────────────────────────────────────────────────

class InsuranceBreachFlags(_V4Model):
    """Boolean flags for insurance regulatory breaches."""

    solvency_breach: bool = Field(False, description="Solvency ratio below minimum")
    reserve_breach: bool = Field(False, description="Reserve ratio below minimum")
    liquidity_breach: bool = Field(False, description="Liquidity gap exceeds threshold")


class InsuranceStressV4(_V4Model):
    """Insurance-sector stress metrics for a single entity."""

    entity_id: str = Field(..., description="Entity UUIDv7")
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    premium_drop: float = Field(..., description="Drop in premium income (monetary)")
    claims_spike: float = Field(..., description="Claims spike amount (monetary)")
    reserve_ratio: float = Field(..., description="Reserve ratio")
    solvency_ratio: float = Field(..., description="Solvency ratio")
    combined_ratio: float = Field(..., description="Combined ratio (loss + expense)")
    liquidity_gap: float = Field(..., description="Liquidity gap (monetary)")

    breach_flags: InsuranceBreachFlags = Field(
        default_factory=InsuranceBreachFlags, description="Regulatory breach flags"
    )


# ── 11-12. Fintech Stress ─────────────────────────────────────────────────────

class FintechBreachFlags(_V4Model):
    """Boolean flags for fintech operational breaches."""

    availability_breach: bool = Field(False, description="Availability below minimum")
    settlement_breach: bool = Field(False, description="Settlement delay exceeds maximum")
    operational_risk_breach: bool = Field(False, description="Operational risk score exceeds threshold")


class FintechStressV4(_V4Model):
    """Fintech-sector stress metrics for a single entity."""

    entity_id: str = Field(..., description="Entity UUIDv7")
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    transaction_failure_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Transaction failure rate"
    )
    fraud_loss: float = Field(..., description="Fraud loss amount (monetary)")
    service_availability: float = Field(
        ..., ge=0.0, le=1.0, description="Service availability ratio"
    )
    settlement_delay_minutes: int = Field(..., ge=0, description="Settlement delay in minutes")
    client_churn_rate: float = Field(..., ge=0.0, le=1.0, description="Client churn rate")
    operational_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Operational risk score"
    )

    breach_flags: FintechBreachFlags = Field(
        default_factory=FintechBreachFlags, description="Operational breach flags"
    )


# ── 13-14. Decision Engine ────────────────────────────────────────────────────

class DecisionActionV4(_V4Model):
    """A single recommended action from the decision engine."""

    action_id: str = Field(..., description="Unique action identifier")
    run_id: str = Field(..., description="Simulation run identifier")

    rank: Literal[1, 2, 3] = Field(..., description="Priority rank (1 = highest)")
    action_type: Literal[
        "inject_liquidity",
        "restrict_exposure",
        "reroute_flow",
        "raise_capital_buffer",
        "increase_reserves",
        "trigger_regulatory_escalation",
        "reduce_counterparty_limit",
        "activate_bcp",
    ] = Field(..., description="Action type")

    target_level: Literal["entity", "sector", "system"] = Field(
        ..., description="Granularity of the action target"
    )
    target_ref: str = Field(..., description="Reference to the target (entity_id, sector name, etc.)")

    # Scoring dimensions
    urgency: float = Field(..., ge=0.0, le=1.0, description="Urgency score")
    value: float = Field(..., ge=0.0, le=1.0, description="Value / benefit score")
    reg_risk: float = Field(..., ge=0.0, le=1.0, description="Regulatory risk score")
    feasibility: float = Field(..., ge=0.0, le=1.0, description="Feasibility score")
    time_effect: float = Field(..., ge=0.0, le=1.0, description="Time-to-effect score")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Composite priority score")

    # Rationale
    reason_codes: list[str] = Field(default_factory=list, description="Machine-readable reason codes")
    preconditions: list[str] = Field(default_factory=list, description="Required preconditions")

    # Expected outcomes
    expected_loss_reduction: float = Field(..., description="Expected loss reduction (monetary)")
    expected_flow_recovery: float = Field(
        ..., ge=0.0, le=1.0, description="Expected flow recovery ratio"
    )
    execution_window_hours: float = Field(
        ..., ge=0.0, le=168.0, description="Execution window in hours (0-168)"
    )
    requires_override: bool = Field(False, description="Whether manual override is required")


class DecisionPlanV4(_V4Model):
    """Top-level decision plan produced by the decision engine for a run."""

    run_id: str = Field(..., description="Simulation run identifier")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    model_version: str = Field(..., description="Decision model version")

    candidate_count: int = Field(..., ge=0, description="Total candidate actions evaluated")
    feasible_count: int = Field(..., ge=0, description="Feasible actions after filtering")

    actions: list[DecisionActionV4] = Field(
        default_factory=list, max_length=3, description="Top-3 recommended actions"
    )
    dropped_actions_count: int = Field(0, ge=0, description="Actions dropped by constraints")

    constrained_by_rbac: bool = Field(False, description="Whether RBAC constrained the plan")
    constrained_by_regulation: bool = Field(
        False, description="Whether regulation constrained the plan"
    )

    plan_status: Literal["complete", "partial", "empty"] = Field(
        ..., description="Plan completeness status"
    )


# ── 15. RegulatoryStateV4 ─────────────────────────────────────────────────────

class RegulatoryStateV4(_V4Model):
    """Aggregate regulatory state for a jurisdiction at a point in time."""

    run_id: str = Field(..., description="Simulation run identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    jurisdiction: str = Field(..., description="ISO jurisdiction code")
    regulatory_version: str = Field(..., description="Regulatory framework version")

    aggregate_lcr: float = Field(..., description="Aggregate LCR across banking entities")
    aggregate_nsfr: float = Field(..., description="Aggregate NSFR across banking entities")
    aggregate_solvency_ratio: float = Field(
        ..., description="Aggregate solvency ratio across insurers"
    )
    aggregate_capital_adequacy_ratio: float = Field(
        ..., description="Aggregate Capital Adequacy Ratio"
    )

    breach_level: Literal["none", "minor", "major", "critical"] = Field(
        ..., description="Highest breach severity"
    )
    mandatory_actions: list[str] = Field(
        default_factory=list, description="Mandatory regulatory actions"
    )
    reporting_required: bool = Field(False, description="Whether regulatory reporting is triggered")


# ── 16-19. Explanation Pack ────────────────────────────────────────────────────

class ExplanationDriver(_V4Model):
    """A single driver contributing to the scenario outcome."""

    driver: str = Field(..., description="Driver name / identifier")
    magnitude: float = Field(..., description="Magnitude of the driver's effect")
    unit: str = Field(..., description="Unit of measurement")
    affected_entities: list[str] = Field(
        default_factory=list, description="Entity IDs affected by this driver"
    )


class StageTrace(_V4Model):
    """Trace record for a single pipeline stage execution."""

    stage: str = Field(..., description="Pipeline stage name")
    status: Literal["completed", "partial", "failed", "skipped"] = Field(
        ..., description="Stage execution status"
    )
    input_ref: Optional[str] = Field(None, description="Reference to stage input artifact")
    output_ref: Optional[str] = Field(None, description="Reference to stage output artifact")
    notes: Optional[str] = Field(None, description="Free-text notes on the stage execution")


class ActionExplanation(_V4Model):
    """Human-readable explanation for a single recommended action."""

    rank: int = Field(..., ge=1, le=3, description="Action rank")
    action_id: str = Field(..., description="Action identifier")
    why_selected: str = Field(..., description="Natural-language justification")
    supporting_metrics: dict = Field(
        default_factory=dict, description="Key metrics supporting the selection"
    )


class ExplanationPackV4(_V4Model):
    """Full explanation package for a simulation run."""

    run_id: str = Field(..., description="Simulation run identifier")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    summary: str = Field(..., description="Executive summary of the run")

    equations: dict = Field(
        ...,
        description=(
            "Core equations used: loss_formula, flow_formula, "
            "propagation_formula, priority_formula"
        ),
    )

    drivers: list[ExplanationDriver] = Field(
        default_factory=list, description="Key drivers of the outcome"
    )
    stage_traces: list[StageTrace] = Field(
        default_factory=list, description="Pipeline stage traces"
    )
    action_explanations: list[ActionExplanation] = Field(
        default_factory=list, description="Per-action explanations"
    )

    assumptions: list[str] = Field(default_factory=list, description="Model assumptions")
    limitations: list[str] = Field(default_factory=list, description="Known limitations")


# ── 20. LossTrajectoryPoint ───────────────────────────────────────────────────

class LossTrajectoryPoint(_V4Model):
    """A single point on the loss trajectory curve."""

    run_id: str = Field(..., description="Simulation run identifier")
    scope_level: Literal["entity", "sector", "system"] = Field(
        ..., description="Aggregation scope"
    )
    scope_ref: str = Field(..., description="Scope reference (entity_id, sector, 'system')")

    timestep_index: int = Field(..., ge=0, description="Zero-based timestep index")
    timestamp: str = Field(..., description="ISO 8601 timestamp for this timestep")

    direct_loss: float = Field(..., description="Direct loss at this timestep (monetary)")
    propagated_loss: float = Field(..., description="Propagated loss at this timestep (monetary)")
    cumulative_loss: float = Field(..., description="Cumulative loss up to this timestep (monetary)")
    revenue_at_risk: float = Field(..., description="Revenue at risk (monetary)")
    loss_velocity: float = Field(..., description="Rate of loss change (monetary / step)")
    loss_acceleration: float = Field(
        ..., description="Acceleration of loss change (monetary / step^2)"
    )

    status: Literal["stable", "deteriorating", "critical", "failed"] = Field(
        ..., description="Trajectory health status"
    )


# ── 21. TimeToFailure ─────────────────────────────────────────────────────────

class TimeToFailure(_V4Model):
    """Predicted time-to-failure for a given scope and failure type."""

    run_id: str = Field(..., description="Simulation run identifier")
    scope_level: Literal["entity", "sector", "system"] = Field(
        ..., description="Aggregation scope"
    )
    scope_ref: str = Field(..., description="Scope reference")

    failure_type: Literal[
        "liquidity_failure",
        "capital_failure",
        "solvency_failure",
        "availability_failure",
        "regulatory_failure",
    ] = Field(..., description="Type of failure being predicted")

    failure_threshold_value: float = Field(..., description="Threshold that defines failure")
    current_value_at_t0: float = Field(..., description="Current metric value at t=0")

    predicted_failure_timestep: Optional[int] = Field(
        None, ge=0, description="Predicted timestep of failure (None if no failure predicted)"
    )
    predicted_failure_timestamp: Optional[str] = Field(
        None, description="ISO 8601 timestamp of predicted failure"
    )
    time_to_failure_hours: Optional[float] = Field(
        None, ge=0.0, description="Hours until predicted failure"
    )

    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    failure_reached_within_horizon: bool = Field(
        ..., description="Whether failure occurs within the simulation horizon"
    )


# ── 22. RegulatoryBreachEvent ─────────────────────────────────────────────────

class RegulatoryBreachEvent(_V4Model):
    """A single regulatory breach event detected during simulation."""

    run_id: str = Field(..., description="Simulation run identifier")
    timestep_index: int = Field(..., ge=0, description="Timestep when breach occurred")
    timestamp: str = Field(..., description="ISO 8601 timestamp of breach")

    scope_level: Literal["entity", "sector", "system"] = Field(
        ..., description="Aggregation scope"
    )
    scope_ref: str = Field(..., description="Scope reference")

    metric_name: str = Field(..., description="Name of the breached metric")
    metric_value: float = Field(..., description="Actual metric value at breach")
    threshold_value: float = Field(..., description="Regulatory threshold value")

    breach_direction: Literal["below_minimum", "above_maximum"] = Field(
        ..., description="Direction of the breach"
    )
    breach_level: Literal["minor", "major", "critical"] = Field(
        ..., description="Breach severity"
    )
    first_breach: bool = Field(..., description="Whether this is the first breach of this metric")
    reportable: bool = Field(..., description="Whether this breach must be reported to regulators")


# ── 23. BusinessImpactSummary ─────────────────────────────────────────────────

class BusinessImpactSummary(_V4Model):
    """Executive-level business impact summary for a simulation run."""

    run_id: str = Field(..., description="Simulation run identifier")
    currency: str = Field("USD", description="Base currency ISO code")

    peak_cumulative_loss: float = Field(..., description="Peak cumulative loss (monetary)")
    peak_loss_timestep: int = Field(..., ge=0, description="Timestep of peak loss")
    peak_loss_timestamp: str = Field(..., description="ISO 8601 timestamp of peak loss")

    system_time_to_first_failure_hours: Optional[float] = Field(
        None, ge=0.0, description="Hours to first system-level failure"
    )
    first_failure_type: Optional[str] = Field(None, description="Type of first failure")
    first_failure_scope_ref: Optional[str] = Field(
        None, description="Scope reference of first failure"
    )

    critical_breach_count: int = Field(..., ge=0, description="Number of critical breaches")
    reportable_breach_count: int = Field(..., ge=0, description="Number of reportable breaches")

    business_severity: Literal["low", "medium", "high", "severe"] = Field(
        ..., description="Overall business severity"
    )
    executive_status: Literal["monitor", "intervene", "escalate", "crisis"] = Field(
        ..., description="Recommended executive action status"
    )


# ── 24. TimeStepState ─────────────────────────────────────────────────────────

class TimeStepState(_V4Model):
    """Aggregate system state at a single simulation timestep."""

    run_id: str = Field(..., description="Simulation run identifier")
    timestep_index: int = Field(..., ge=0, description="Zero-based timestep index")
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    shock_intensity_effective: float = Field(
        ..., ge=0.0, le=5.0, description="Effective shock intensity after decay"
    )
    aggregate_loss: float = Field(..., description="Aggregate system loss (monetary)")
    aggregate_flow: float = Field(..., description="Aggregate system flow (monetary)")
    regulatory_breach_count: int = Field(..., ge=0, description="Number of active breaches")

    system_status: Literal["stable", "degrading", "critical", "failed"] = Field(
        ..., description="Overall system health"
    )


# ── 25. ScenarioTimeConfig ────────────────────────────────────────────────────

class ScenarioTimeConfig(_V4Model):
    """Temporal configuration for a scenario simulation."""

    time_granularity_minutes: int = Field(
        ..., ge=1, le=1440, description="Granularity of each timestep in minutes"
    )
    time_horizon_steps: int = Field(
        ..., ge=1, le=1000, description="Total number of timesteps"
    )
    shock_decay_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Per-step shock decay rate"
    )
    propagation_delay_steps: int = Field(
        ..., ge=0, le=100, description="Propagation delay in timesteps"
    )
    recovery_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Per-step recovery rate"
    )
    max_temporal_iterations_per_step: int = Field(
        ..., ge=1, le=100, description="Max iterations within a single timestep"
    )


# ── 26. RunEnvelope ───────────────────────────────────────────────────────────

class RunEnvelope(_V4Model):
    """Top-level envelope wrapping any run output for API responses."""

    trace_id: str = Field(..., description="Distributed tracing ID")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    data: dict = Field(default_factory=dict, description="Payload data (varies by endpoint)")
    warnings: list[dict] = Field(
        default_factory=list, description="Non-fatal warnings from the run"
    )


# ── __all__ ────────────────────────────────────────────────────────────────────

__all__ = [
    # RBAC
    "Role",
    # Core graph
    "RegulatoryProfile",
    "EntityV4",
    "EdgeV4",
    "ScenarioV4",
    # Engine outputs
    "FlowStateV4",
    "FinancialImpactV4",
    # Sector stress
    "BankingBreachFlags",
    "BankingStressV4",
    "InsuranceBreachFlags",
    "InsuranceStressV4",
    "FintechBreachFlags",
    "FintechStressV4",
    # Decision
    "DecisionActionV4",
    "DecisionPlanV4",
    # Regulatory
    "RegulatoryStateV4",
    # Explanation
    "ExplanationDriver",
    "StageTrace",
    "ActionExplanation",
    "ExplanationPackV4",
    # Temporal / trajectory
    "LossTrajectoryPoint",
    "TimeToFailure",
    "RegulatoryBreachEvent",
    "BusinessImpactSummary",
    "TimeStepState",
    "ScenarioTimeConfig",
    # Envelope
    "RunEnvelope",
]
