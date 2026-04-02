from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')

# Health and metadata models
class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    timestamp: datetime
    service_name: str = Field(..., example="Impact Observatory")
    version: str = Field(..., example="1.0.0")

class VersionResponse(BaseModel):
    version: str = Field(..., example="1.0.0")
    build_date: datetime
    environment: str = Field(..., example="production")

# Scenario models
class ScenarioRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scenario_type: str = Field(..., example="disruption")
    parameters: dict = Field(default_factory=dict)

class ScenarioResponse(BaseModel):
    scenario_id: str
    name: str
    description: Optional[str]
    scenario_type: str
    parameters: dict
    created_at: datetime
    updated_at: datetime

class ScenarioRunResponse(BaseModel):
    run_id: str
    scenario_id: str
    status: str = Field(..., example="completed")
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[dict] = None
    error: Optional[str] = None

class ScenarioRunListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[ScenarioRunResponse]

class ScenarioListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[ScenarioResponse]

# Entity models
class EventEntity(BaseModel):
    event_id: str
    event_type: str
    severity: int
    location: str
    timestamp: datetime

class AirportEntity(BaseModel):
    airport_id: str
    name: str
    country: str
    status: str
    latitude: float
    longitude: float

class PortEntity(BaseModel):
    port_id: str
    name: str
    country: str
    status: str
    latitude: float
    longitude: float

class CorridorEntity(BaseModel):
    corridor_id: str
    name: str
    corridor_type: str
    origin: str
    destination: str
    capacity: int

class FlightEntity(BaseModel):
    flight_id: str
    flight_number: str
    status: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: Optional[datetime] = None

class VesselEntity(BaseModel):
    vessel_id: str
    name: str
    vessel_type: str
    status: str
    current_location: str
    latitude: float
    longitude: float

class ActorEntity(BaseModel):
    actor_id: str
    name: str
    actor_type: str
    influence_score: float
    specialization: str

class EntityListResponse(BaseModel):
    entity_type: str
    total: int
    skip: int
    limit: int
    data: list[dict]

# Graph query models
class RiskPropagationRequest(BaseModel):
    source_entity_id: str
    source_entity_type: str
    max_hops: int = Field(default=3, ge=1, le=10)
    risk_threshold: float = Field(default=0.3, ge=0, le=1)

class RiskPropagationPath(BaseModel):
    entity_id: str
    entity_type: str
    risk_score: float
    distance: int
    propagation_vector: str

class ChokePointRequest(BaseModel):
    region: Optional[str] = None
    corridor_type: Optional[str] = None

class ChokePointAnalysis(BaseModel):
    entity_id: str
    entity_type: str
    criticality_score: float
    alternate_routes: int
    dependency_count: int

class RerouteRequest(BaseModel):
    source_location: str
    destination_location: str
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    avoid_regions: Optional[list[str]] = None

class RerouteAlternative(BaseModel):
    route_id: str
    distance_km: float
    estimated_duration_hours: float
    corridor_ids: list[str]
    risk_level: str

class NearestImpactedRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = Field(default=500, gt=0)
    entity_types: Optional[list[str]] = None

class NearestImpactedResult(BaseModel):
    entity_id: str
    entity_type: str
    distance_km: float
    impact_severity: float
    location_name: str

class RegionCascadeRequest(BaseModel):
    region: str
    event_id: str

class CascadeEffect(BaseModel):
    source_entity_id: str
    target_entity_id: str
    target_entity_type: str
    effect_type: str
    intensity: float

class ScenarioSubgraphRequest(BaseModel):
    scenario_id: str
    include_relationships: bool = True

class GraphNode(BaseModel):
    node_id: str
    node_type: str
    properties: dict

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict

class GraphSubgraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

class ActorInfluenceRequest(BaseModel):
    actor_id: str

class ActorInfluenceAnalysis(BaseModel):
    actor_id: str
    total_influence_score: float
    influenced_entities_count: int
    primary_influence_vectors: list[str]
    risk_contribution: float

class GraphQueryResponse(BaseModel):
    query_type: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: int = Field(default=0)

class GraphQueryRequest(BaseModel):
    query_type: str
    parameters: dict

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=1000)

class IngestionStatusResponse(BaseModel):
    timestamp: datetime
    status: str
    pending_jobs: int
    completed_jobs: int
    failed_jobs: int
    last_ingest_timestamp: Optional[datetime] = None

# Error response
class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    timestamp: datetime

# Generic pagination wrapper
class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    data: list[T]

# Conflict Intelligence models
class ConflictListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[dict]

class ConflictDetailResponse(BaseModel):
    conflict_id: str
    region: str
    conflict_type: str
    severity: float
    actors: list[str]
    latest_event_date: datetime
    status: str
    description: str

class ConflictHeatmapResponse(BaseModel):
    bounds: dict
    cells: list[dict]
    total_conflicts: int
    timestamp: datetime

class ConflictAnalysisResponse(BaseModel):
    conflict_count: int
    regions_involved: list[str]
    types_involved: list[str]
    actors_involved: list[str]
    avg_severity: float
    max_severity: float
    severity_trend: str
    temporal_pattern: str
    escalation_risk: float
    spillover_risk: float
    recommended_actions: list[str]
    analysis_timestamp: datetime

# Incident Intelligence models
class IncidentListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[dict]

class IncidentDetailResponse(BaseModel):
    incident_id: str
    incident_type: str
    severity: float
    location: str
    status: str
    impact_assessment: dict
    timestamp: datetime

class IncidentTimelineResponse(BaseModel):
    incident_id: str
    incident_type: str
    total_events: int
    events: list[dict]
    timeline_period_start: datetime
    timeline_period_end: datetime

class CorrelationResponse(BaseModel):
    incident_id_1: str
    incident_id_2: str
    correlation_score: float
    common_factors: list[str]
    geographic_distance_km: float

# Insurance Portfolio models
class InsuranceExposureResponse(BaseModel):
    portfolio_id: str
    total_exposure_value: float
    exposure_by_entity_type: dict
    high_risk_assets: list[dict]
    time_window_days: int
    timestamp: datetime

class ClaimsSurgeResponse(BaseModel):
    surge_detected: bool
    baseline_claim_rate: float
    current_claim_rate: float
    increase_percentage: float
    claims_count: int
    affected_policies: int
    anomaly_score: float
    timestamp: datetime

class UnderwritingResponse(BaseModel):
    recommendation: str
    risk_adjustment_factor: float
    revised_premium_percentage: float
    confidence_score: float
    key_risk_factors: list[str]
    pricing_notes: str

class SeverityResponse(BaseModel):
    event_type: str
    severity_score: float
    financial_impact_estimate: float
    affected_assets: int
    affected_policies: int

class ScenarioInsuranceImpactResponse(BaseModel):
    scenario_id: str
    estimated_claims: float
    estimated_recovery_cost: float
    timeline_days: int
    confidence_score: float
    risk_mitigation_options: list[dict]

# Decision Generation models
class DecisionOutputResponse(BaseModel):
    decision_id: str
    decision_type: str
    recommended_action: str
    priority_level: str
    confidence_score: float
    rationale: str
    alternative_actions: list[str]
    timestamp: datetime

class ExplanationResponse(BaseModel):
    decision_id: str
    explanation_text: str
    contributing_factors: list[dict]
    data_sources: list[str]
    confidence_level: float

class RecommendationResponse(BaseModel):
    recommendation_id: str
    title: str
    description: str
    priority: str
    estimated_impact: dict
    implementation_cost: float
    timeline_hours: int
    risk_reduction_percentage: float

# Risk Score models (moved from scores.py)
class ScoreRequest(BaseModel):
    """Request model for individual score computation."""
    entity_id: str = Field(..., description="Unique identifier for the entity")
    entity_type: str = Field(..., description="Type of entity (port, airport, corridor, etc.)")
    supply_chain_risk: float = Field(..., ge=0, le=1, description="Supply chain risk component")
    geopolitical_risk: float = Field(..., ge=0, le=1, description="Geopolitical risk component")
    infrastructure_risk: float = Field(..., ge=0, le=1, description="Infrastructure risk component")
    demand_disruption_risk: float = Field(..., ge=0, le=1, description="Demand disruption risk component")
    financial_risk: float = Field(..., ge=0, le=1, description="Financial risk component")

class ComputeScoresRequest(BaseModel):
    """Request model for batch score computation."""
    entities: list[ScoreRequest] = Field(..., description="List of entities to compute scores for")
    scenario_id: Optional[str] = Field(None, description="Optional scenario context for computation")

class ScoreResponse(BaseModel):
    """Response model for individual risk score."""
    score_id: str
    entity_id: str
    entity_type: str
    overall_score: float = Field(..., ge=0, le=1, description="Composite risk score 0-1")
    supply_chain_risk: float
    geopolitical_risk: float
    infrastructure_risk: float
    demand_disruption_risk: float
    financial_risk: float
    risk_level: str = Field(..., description="Severity level: critical, high, medium, low")
    weighted_components: dict
    timestamp: datetime
    scenario_id: Optional[str] = None

class ScoresListResponse(BaseModel):
    """Paginated response for score list."""
    total: int
    skip: int
    limit: int
    data: list[ScoreResponse]

class ComputeScoresResponse(BaseModel):
    """Response model for batch score computation."""
    batch_id: str
    total_computed: int
    scores: list[ScoreResponse]
    timestamp: datetime

class ScoreSummaryResponse(BaseModel):
    """Response model for aggregate score summary."""
    summary_id: str
    total_entities_scored: int
    average_overall_score: float
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    risk_distribution: dict
    component_averages: dict
    highest_risk_entities: list[dict] = Field(..., description="Top 5 highest risk entities")
    timestamp: datetime

class ScoreHistoryEntry(BaseModel):
    """Individual entry in score history."""
    score_id: str
    entity_id: str
    overall_score: float
    risk_level: str
    timestamp: datetime
    scenario_id: Optional[str] = None

class ScoreHistoryResponse(BaseModel):
    """Response model for historical score data."""
    entity_id: str
    entity_type: str
    total_records: int
    skip: int
    limit: int
    time_range_start: datetime
    time_range_end: datetime
    history: list[ScoreHistoryEntry]
    trend: str = Field(..., description="Trend direction: increasing, decreasing, stable")
    average_score: float

class AnalyzeScoresRequest(BaseModel):
    """Request model for score analysis."""
    risk_threshold: float = Field(default=0.5, ge=0, le=1, description="Threshold for filtering analysis")
    entity_type_filter: Optional[str] = Field(None, description="Optional entity type filter")
    scenario_id: Optional[str] = Field(None, description="Optional scenario context")

class ScoreDistribution(BaseModel):
    """Distribution statistics for scores."""
    mean: float
    median: float
    std_dev: float
    min: float
    max: float
    percentile_25: float
    percentile_75: float
    percentile_95: float

class AnalyzeScoresResponse(BaseModel):
    """Response model for score analysis."""
    analysis_id: str
    total_analyzed: int
    above_threshold_count: int
    distribution: ScoreDistribution
    component_analysis: dict
    correlations: dict
    outliers: list[dict] = Field(..., description="Entities with outlier scores")
    timestamp: datetime

# Decision Output Contract (Master Prompt specification)
class BilingualTextModel(BaseModel):
    """Bilingual text container for EN/AR content."""
    en: str = Field(..., description="English text")
    ar: str = Field(..., description="Arabic text")

class ConfidenceBreakdown(BaseModel):
    """Confidence breakdown by component."""
    simulation_confidence: float = Field(..., ge=0, le=1, description="Confidence in simulation results")
    economic_confidence: float = Field(..., ge=0, le=1, description="Confidence in economic impact estimates")
    insurance_confidence: float = Field(..., ge=0, le=1, description="Confidence in insurance impact estimates")
    recommendation_confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendations")

class WeightConfig(BaseModel):
    """Weight configuration used in analysis."""
    geopolitical_weight: float = Field(..., ge=0, le=1)
    infrastructure_weight: float = Field(..., ge=0, le=1)
    economic_weight: float = Field(..., ge=0, le=1)
    insurance_weight: float = Field(..., ge=0, le=1)

class Explanation(BaseModel):
    """Detailed explanation of decision reasoning."""
    top_causal_factors: list[str] = Field(..., description="Top 3-5 causal factors")
    propagation_path: list[dict] = Field(..., description="Path of risk propagation through supply chain")
    confidence_breakdown: ConfidenceBreakdown
    weight_config_used: WeightConfig

class InsuranceImpactModel(BaseModel):
    """Insurance portfolio impact assessment."""
    exposure_score: float = Field(..., ge=0, le=100, description="Portfolio exposure score 0-100")
    claims_surge_potential: float = Field(..., ge=0, le=1, description="Probability of claims surge")
    underwriting_class: str = Field(..., description="Underwriting class: standard, restricted, critical")
    expected_claims_uplift: float = Field(..., description="Expected claims uplift in USD millions")

class DecisionOutputContract(BaseModel):
    """Master Prompt compliant decision output contract."""
    event: BilingualTextModel = Field(..., description="What happened event description")
    timestamp: datetime = Field(..., description="Decision output timestamp")
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    disruption_score: float = Field(..., ge=0, le=100, description="Disruption severity 0-100")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence level 0-1")
    system_stress: str = Field(..., description="System stress level: nominal, elevated, high, critical")
    affected_airports: list[str] = Field(default_factory=list, description="List of affected airport codes")
    affected_ports: list[str] = Field(default_factory=list, description="List of affected port codes")
    affected_corridors: list[str] = Field(default_factory=list, description="List of affected corridor IDs")
    affected_routes: list[str] = Field(default_factory=list, description="List of affected trade routes")
    economic_impact_estimate: float = Field(..., description="Economic impact in USD millions")
    insurance_impact: InsuranceImpactModel
    recommended_action: BilingualTextModel = Field(..., description="Recommended action")
    scenario_horizon: str = Field(..., description="Time horizon: immediate, short-term, medium-term, long-term")
    explanation: Explanation
