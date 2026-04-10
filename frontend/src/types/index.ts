// ============================================================
// Impact Observatory | مرصد الأثر — Legacy Canonical Types
// See types/observatory.ts for v1 types
// ============================================================

// --------------- Core Geo / Entity Types ---------------

export interface GeoCoord {
  lat: number;
  lng: number;
}

export interface Event {
  id: string;
  title: string;
  title_ar?: string;
  description?: string;
  event_type: EventType;
  severity_score: number;
  location: GeoCoord;
  country_code: string;
  region: string;
  timestamp: string;
  source: string;
  tags?: string[];
}

export type EventType =
  | "kinetic"
  | "sanctions"
  | "protest"
  | "cyber"
  | "natural_disaster"
  | "political"
  | "economic"
  | "terrorism";

export interface Flight {
  id: string;
  callsign: string;
  airline?: string;
  origin: Airport;
  destination: Airport;
  position?: GeoCoord & { altitude_ft: number; heading: number };
  status: "en_route" | "landed" | "scheduled" | "diverted" | "cancelled";
  risk_score: number;
  departure_time?: string;
  arrival_time?: string;
}

export interface Vessel {
  id: string;
  name: string;
  imo?: string;
  mmsi?: string;
  vessel_type: string;
  flag_country: string;
  position: GeoCoord & { heading: number; speed_knots: number };
  destination_port?: string;
  risk_score: number;
  cargo_type?: string;
  last_updated: string;
}

export interface Airport {
  iata: string;
  name: string;
  location: GeoCoord;
  country_code: string;
}

export interface Port {
  id: string;
  name: string;
  location: GeoCoord;
  country_code: string;
  capacity_teu?: number;
}

export interface Corridor {
  id: string;
  name: string;
  corridor_type: "air" | "sea" | "land" | "pipeline";
  waypoints: GeoCoord[];
  risk_score: number;
  throughput_daily?: number;
}

export interface Region {
  id: string;
  name: string;
  name_ar?: string;
  country_code: string;
  bbox: { north: number; south: number; east: number; west: number };
}

// --------------- Scoring Types ---------------

export interface RiskScore {
  entity_id: string;
  entity_type: string;
  composite_score: number;
  components: RiskComponents;
  confidence: number;
  timestamp: string;
  explanation?: ScoreExplanation;
}

export interface RiskComponents {
  geopolitical: number;   // G
  proximity: number;      // P
  network: number;        // N
  logistic: number;       // L
  temporal: number;       // T
  uncertainty: number;    // U
}

export interface DisruptionScore {
  entity_id: string;
  score: number;
  factors: DisruptionFactor[];
  timestamp: string;
}

export interface DisruptionFactor {
  name: string;
  weight: number;
  value: number;
  contribution: number;
}

export interface ImpactAssessment {
  entity_id: string;
  delta: number;
  pre_score: number;
  post_score: number;
  sector: string;
  region: string;
}

export interface ScoreExplanation {
  summary: string;
  top_drivers: { factor: string; contribution: number; description: string }[];
  confidence_note?: string;
}

// --------------- Scenario Types ---------------

export interface ScenarioTemplate {
  id: string;
  title: string;
  title_ar: string;
  description?: string;
  description_ar?: string;
  scenario_type: ScenarioType;
  horizon_hours: number;
  shock_count: number;
  shocks: ScenarioShock[];
  tags?: string[];
}

export type ScenarioType =
  | "disruption"
  | "escalation"
  | "cascading"
  | "hypothetical";

export interface ScenarioShock {
  shock_type: string;
  target_entity_id?: string;
  target_region?: string;
  severity: number;
  description: string;
  description_ar?: string;
}

export interface Scenario {
  scenario_id: string;
  template_id?: string;
  severity_override?: number;
  custom_shocks?: ScenarioShock[];
  horizon_hours: number;
}

export interface ScenarioResult {
  scenario_id: string;
  title: string;
  title_ar?: string;
  system_stress: number;
  total_economic_loss_usd: number;
  top_impacted_entities: string[];
  impacts: ImpactAssessment[];
  narrative: string;
  narrative_ar?: string;
  recommendations: string[];
  recommendations_ar?: string[];
  propagation_paths?: PropagationResult[];
  timestamp: string;
}

// --------------- Insurance Types ---------------

export interface InsuranceExposure {
  entity_id: string;
  entity_name: string;
  sector: string;
  region: string;
  total_insured_value_usd: number;
  probable_maximum_loss_usd: number;
  risk_score: number;
  exposure_category: "low" | "moderate" | "high" | "critical";
  lines_of_business: LineOfBusiness[];
}

export interface LineOfBusiness {
  line: string;
  insured_value_usd: number;
  loss_ratio: number;
  trend: "improving" | "stable" | "deteriorating";
}

export interface ClaimsSurge {
  scenario_id: string;
  projected_claims_count: number;
  projected_claims_value_usd: number;
  peak_period_hours: number;
  affected_lines: string[];
  severity_distribution: {
    low: number;
    moderate: number;
    high: number;
    catastrophic: number;
  };
  timeline: ClaimsSurgePoint[];
}

export interface ClaimsSurgePoint {
  hour: number;
  cumulative_claims: number;
  cumulative_value_usd: number;
}

export interface UnderwritingWatch {
  entity_id: string;
  entity_name: string;
  watch_level: "monitor" | "review" | "restrict" | "decline";
  reason: string;
  risk_delta: number;
  triggered_at: string;
  recommended_action: string;
}

export interface SeverityProjection {
  scenario_id: string;
  time_horizon_hours: number;
  projections: {
    hour: number;
    system_stress: number;
    economic_loss_usd: number;
    entities_impacted: number;
  }[];
}

// --------------- Graph / Propagation Types ---------------

export interface SystemStress {
  overall_stress: number;
  sector_stress: Record<string, number>;
  region_stress: Record<string, number>;
  critical_nodes: string[];
  chokepoints: Chokepoint[];
  timestamp: string;
}

export interface Chokepoint {
  node_id: string;
  name: string;
  betweenness_centrality: number;
  flow_volume: number;
  risk_score: number;
}

export interface PropagationResult {
  start_node: string;
  paths: PropagationPath[];
  total_affected: number;
  max_depth: number;
}

export interface PropagationPath {
  nodes: string[];
  edge_weights: number[];
  cumulative_impact: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  sector?: string;
  region?: string;
  risk_score: number;
  x?: number;
  y?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  edge_type: string;
}

// --------------- Globe Layer Types ---------------

export type GlobeLayer =
  | "flights"
  | "vessels"
  | "conflicts"
  | "heatmap"
  | "arcs"
  | "infrastructure";

// --------------- Decision Output Types ---------------

export interface DecisionOutput {
  scenario_id: string;
  decision_timestamp: string;
  recommended_actions: DecisionAction[];
  risk_summary: string;
  confidence: number;
}

export interface DecisionAction {
  action_id: string;
  description: string;
  description_ar?: string;
  priority: "critical" | "high" | "medium" | "low";
  target_entity?: string;
  expected_impact: string;
  estimated_cost_usd?: number;
}

// --------------- API Response Wrappers ---------------

export interface PaginatedResponse<T> {
  count: number;
  items: T[];
  offset?: number;
  limit?: number;
}

export interface EventsResponse {
  count: number;
  events: Event[];
}

export interface FlightsResponse {
  count: number;
  flights: Flight[];
}

export interface VesselsResponse {
  count: number;
  vessels: Vessel[];
}

export interface TemplatesResponse {
  templates: ScenarioTemplate[];
}

export interface ChokepointsResponse {
  chokepoints: Chokepoint[];
}

export interface PropagationResponse {
  paths: PropagationPath[];
}
