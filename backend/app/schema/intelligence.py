"""Intelligence analysis models for the GCC Decision Intelligence Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseEntity
from .enums import EntityType, RiskCategory, ScenarioStatus


class RiskScore(BaseEntity):
    """A risk assessment score for an entity."""

    entity_id: str = Field(description="ID of the entity being assessed")
    entity_type: EntityType = Field(description="Type of entity")
    entity_name: Optional[str] = Field(default=None, description="Name of the entity")
    score: float = Field(
        ge=0.0, le=1.0, description="Overall risk score (0-1)"
    )
    category: RiskCategory = Field(description="Risk category")
    components: dict[str, float] = Field(
        description="Component scores contributing to overall score"
    )
    factors: list[str] = Field(
        default_factory=list, description="Risk factors identified"
    )
    explanation: str = Field(description="Explanation of risk assessment")
    explanation_ar: Optional[str] = Field(
        default=None, description="Explanation in Arabic"
    )
    mitigation_actions: list[str] = Field(
        default_factory=list, description="Recommended mitigation actions"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence in assessment (0-1)"
    )
    assessment_date: datetime = Field(description="Date of assessment")
    valid_until: Optional[datetime] = Field(
        default=None, description="Expiration date of assessment"
    )

    @field_validator("score", "confidence")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        """Ensure scores are valid."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0 and 1")
        return v

    @field_validator("components")
    @classmethod
    def validate_components(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all component scores are valid."""
        for key, value in v.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Component score '{key}' must be between 0 and 1")
        return v


class ImpactAssessment(BaseEntity):
    """Assessment of impact from a scenario or event."""

    scenario_id: str = Field(description="ID of the scenario being assessed")
    scenario_name: Optional[str] = Field(default=None, description="Name of scenario")
    affected_entities: dict[str, list[str]] = Field(
        default_factory=dict, description="Mapping of entity types to affected entity IDs"
    )
    affected_entity_count: int = Field(
        default=0, ge=0, description="Total number of affected entities"
    )
    total_exposure_value_usd: Optional[float] = Field(
        default=None, ge=0.0, description="Total exposure value in USD"
    )
    disruption_score: float = Field(
        ge=0.0, le=1.0, description="Overall disruption score (0-1)"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence in assessment (0-1)"
    )
    affected_regions: list[str] = Field(
        default_factory=list, description="Geographic regions affected"
    )
    affected_countries: list[str] = Field(
        default_factory=list, description="Countries affected (ISO codes)"
    )
    economic_impact_summary: Optional[str] = Field(
        default=None, description="Summary of economic impact"
    )
    supply_chain_disruption_days: Optional[int] = Field(
        default=None, ge=0, description="Estimated supply chain disruption in days"
    )
    humanitarian_impact: Optional[str] = Field(
        default=None, description="Description of humanitarian impact"
    )
    narrative: str = Field(description="Detailed narrative of impacts")
    narrative_ar: Optional[str] = Field(
        default=None, description="Detailed narrative in Arabic"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommended response actions"
    )
    assessment_date: datetime = Field(description="Date of assessment")

    @field_validator("disruption_score", "confidence")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        """Ensure scores are valid."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0 and 1")
        return v


class Scenario(BaseEntity):
    """A simulation scenario in the system."""

    name: str = Field(description="Scenario name")
    name_ar: Optional[str] = Field(default=None, description="Scenario name in Arabic")
    description: str = Field(description="Detailed scenario description")
    description_ar: Optional[str] = Field(
        default=None, description="Detailed scenario description in Arabic"
    )
    scenario_type: str = Field(
        description="Type of scenario (shock, disruption, policy_change, etc.)"
    )
    status: ScenarioStatus = Field(default=ScenarioStatus.DRAFT, description="Current status")
    shock_events: list[str] = Field(
        default_factory=list, description="IDs of shock/trigger events"
    )
    shock_event_names: list[str] = Field(
        default_factory=list, description="Names of shock events"
    )
    simulation_horizon_hours: int = Field(
        default=168, ge=1, description="Simulation horizon in hours (typically 168 for 1 week)"
    )
    baseline_state: dict[str, Any] = Field(
        default_factory=dict, description="Baseline system state at scenario start"
    )
    post_shock_state: Optional[dict[str, Any]] = Field(
        default=None, description="System state after shock application"
    )
    affected_regions: list[str] = Field(
        default_factory=list, description="Affected geographic regions"
    )
    affected_countries: list[str] = Field(
        default_factory=list, description="Affected countries (ISO codes)"
    )
    key_assumptions: list[str] = Field(
        default_factory=list, description="Key assumptions in the scenario"
    )
    uncertainty_factors: list[str] = Field(
        default_factory=list, description="Identified uncertainty factors"
    )
    created_by_user_id: Optional[str] = Field(
        default=None, description="ID of user who created scenario"
    )
    created_by_model: Optional[str] = Field(
        default=None, description="AI model used to generate scenario"
    )
    last_run_at: Optional[datetime] = Field(
        default=None, description="Timestamp of last simulation run"
    )
    next_run_at: Optional[datetime] = Field(
        default=None, description="Scheduled next simulation run"
    )
    simulation_count: int = Field(default=0, ge=0, description="Number of times scenario was simulated")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("simulation_horizon_hours")
    @classmethod
    def validate_horizon(cls, v: int) -> int:
        """Ensure simulation horizon is positive."""
        if v < 1:
            raise ValueError("Simulation horizon must be at least 1 hour")
        return v

    @field_validator("scenario_type")
    @classmethod
    def validate_scenario_type(cls, v: str) -> str:
        """Ensure scenario type is valid."""
        valid_types = [
            "shock",
            "disruption",
            "policy_change",
            "market_shock",
            "conflict_escalation",
            "pandemic",
            "natural_disaster",
            "technical_failure",
            "other",
        ]
        if v not in valid_types:
            raise ValueError(f"Scenario type must be one of: {valid_types}")
        return v


class ScenarioResult(BaseEntity):
    """Results from a scenario simulation run."""

    scenario_id: str = Field(description="ID of the scenario")
    scenario_name: Optional[str] = Field(default=None, description="Name of scenario")
    run_number: int = Field(ge=1, description="Run number for this scenario")
    start_time: datetime = Field(description="Start time of simulation")
    end_time: Optional[datetime] = Field(default=None, description="End time of simulation")
    duration_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Duration of simulation in seconds"
    )
    status: str = Field(
        default="running", description="Status (running, completed, failed, partial)"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if simulation failed"
    )
    impact_assessment_id: Optional[str] = Field(
        default=None, description="ID of associated impact assessment"
    )
    output_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Key output metrics from simulation"
    )
    entity_states: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Final state of each simulated entity"
    )
    timeline_events: list[dict[str, Any]] = Field(
        default_factory=list, description="Key events during simulation timeline"
    )
    critical_findings: list[str] = Field(
        default_factory=list, description="Critical findings from simulation"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations based on results"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is valid."""
        valid_statuses = ["running", "completed", "failed", "partial", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v
