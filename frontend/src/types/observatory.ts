// ============================================================
// Impact Observatory | مرصد الأثر — V1 TypeScript Types
// ============================================================

// Maps to backend schemas exactly

export interface ScenarioCreate {
  template_id: string;
  severity: number;
  horizon_hours: number;
  label?: string;
}

export interface ScenarioTemplate {
  id: string;
  label_en: string;
  label_ar: string;
  sectors_affected: string[];
  base_loss_usd: number;
}

export interface FinancialImpact {
  entity_id: string;
  entity_label: string | null;
  sector: string;
  loss_usd: number;
  loss_pct_gdp: number;
  peak_day: number;
  recovery_days: number;
  confidence: number;
  stress_level: number;
  classification: Classification;
}

export interface BankingStress {
  run_id: string;
  total_exposure_usd: number;
  liquidity_stress: number;
  credit_stress: number;
  fx_stress: number;
  interbank_contagion: number;
  time_to_liquidity_breach_hours: number;
  capital_adequacy_impact_pct: number;
  aggregate_stress: number;
  classification: Classification;
  affected_institutions: BankingInstitution[];
}

export interface BankingInstitution {
  id: string;
  name: string;
  name_ar: string;
  country: string;
  exposure_usd: number;
  stress: number;
  projected_car_pct: number;
}

export interface InsuranceStress {
  run_id: string;
  portfolio_exposure_usd: number;
  claims_surge_multiplier: number;
  severity_index: number;
  loss_ratio: number;
  combined_ratio: number;
  underwriting_status: string;
  time_to_insolvency_hours: number;
  reinsurance_trigger: boolean;
  ifrs17_risk_adjustment_pct: number;
  aggregate_stress: number;
  classification: Classification;
  affected_lines: InsuranceLine[];
}

export interface InsuranceLine {
  id: string;
  name: string;
  name_ar: string;
  exposure_usd: number;
  claims_surge: number;
  stress: number;
}

export interface FintechStress {
  run_id: string;
  payment_volume_impact_pct: number;
  settlement_delay_hours: number;
  api_availability_pct: number;
  cross_border_disruption: number;
  digital_banking_stress: number;
  time_to_payment_failure_hours: number;
  aggregate_stress: number;
  classification: Classification;
  affected_platforms: FintechPlatform[];
}

export interface FintechPlatform {
  id: string;
  name: string;
  name_ar: string;
  country: string;
  volume_impact_pct: number;
  cross_border_stress: number;
  stress: number;
}

export interface DecisionAction {
  id: string;
  action: string;
  action_ar: string | null;
  sector: string;
  owner: string;
  urgency: number;
  value: number;
  regulatory_risk: number;
  priority: number;
  time_to_act_hours: number;
  time_to_failure_hours: number;
  loss_avoided_usd: number;
  cost_usd: number;
  confidence: number;
}

export interface DecisionPlan {
  run_id: string;
  scenario_label: string | null;
  total_loss_usd: number;
  peak_day: number;
  time_to_failure_hours: number;
  actions: DecisionAction[];
  all_actions: DecisionAction[];
}

export interface CausalStep {
  step: number;
  entity_id: string;
  entity_label: string;
  entity_label_ar: string | null;
  event: string;
  event_ar: string | null;
  impact_usd: number;
  stress_delta: number;
  mechanism: string;
}

export interface ExplanationPack {
  run_id: string;
  scenario_label: string | null;
  narrative_en: string;
  narrative_ar: string;
  causal_chain: CausalStep[];
  total_steps: number;
  headline_loss_usd: number;
  peak_day: number;
  confidence: number;
  methodology: string;
}

export interface RunHeadline {
  total_loss_usd: number;
  peak_day: number;
  max_recovery_days: number;
  average_stress: number;
  affected_entities: number;
  critical_count: number;
  elevated_count: number;
}

// ── Timeline Types ──
export interface TimelineStep {
  timestep: number;
  timestamp: string;
  cumulative_loss: number;
  aggregate_stress: number;
  entity_states: Record<string, { stress: number; loss: number }>;
}

export interface RegulatoryEvent {
  timestep: number;
  breach_level: "none" | "minor" | "major" | "critical";
  mandatory_actions: string[];
  sector: string;
}

export type BusinessSeverity = "low" | "medium" | "high" | "severe";
export type ExecutiveStatus = "monitor" | "intervene" | "escalate" | "crisis";

export interface RunResult {
  schema_version: string;
  run_id: string;
  status: string;
  pipeline_stages_completed: number;
  scenario: {
    template_id: string;
    label: string;
    label_ar: string | null;
    severity: number;
    horizon_hours: number;
  };
  headline: RunHeadline;
  financial: FinancialImpact[];
  banking: BankingStress;
  insurance: InsuranceStress;
  fintech: FintechStress;
  decisions: DecisionPlan;
  explanation: ExplanationPack;
  // ── Trust Layer fields ──
  business_severity: BusinessSeverity;
  executive_status: ExecutiveStatus;
  model_version: string;
  global_confidence: number;
  assumptions: string[];
  audit_hash: string;
  stages_completed: string[];
  stage_log: Record<string, { status: string; duration_ms: number; detail?: string }>;
  // ── Timeline fields ──
  timeline: TimelineStep[];
  regulatory_events: RegulatoryEvent[];
  // ── Legacy compatibility ──
  executive_report: Record<string, unknown>;
  flow_states: Record<string, unknown>[];
  propagation: Record<string, unknown>[];
  duration_ms: number;
}

export type Classification =
  | "NOMINAL"
  | "LOW"
  | "MODERATE"
  | "ELEVATED"
  | "CRITICAL";

export type ViewMode = "executive" | "analyst" | "regulatory";
export type Language = "en" | "ar";

// ── Propagation Engine Types ──
export interface PropagationStep {
  from: string;
  fromLabel: string;
  to: string;
  toLabel: string;
  weight: number;
  polarity: number;
  impact: number;
  label: string;
  iteration: number;
}

export interface SectorImpact {
  sector: string;
  sectorLabel: string;
  avgImpact: number;
  maxImpact: number;
  nodeCount: number;
  topNode: string;
  color: string;
}

export interface PropagationResult {
  nodeImpacts: Record<string, number>;
  propagationChain: PropagationStep[];
  affectedSectors: SectorImpact[];
  topDrivers: { nodeId: string; label: string; impact: number; layer: string; outDegree: number }[];
  totalLoss: number;
  confidence: number;
  systemEnergy: number;
  propagationDepth: number;
  spreadLevel: string;
  spreadLevelAr: string;
}

// ── Physics System Types ──
export interface BottleneckNode {
  entity_id: string;
  name: string;
  utilization: number;
  bottleneck_score: number;
  severity: string;
}

export interface PhysicsResult {
  physical_system_status: {
    utilization_map: Record<string, { capacity: number; throughput: number; utilization: number }>;
    bottleneck_count: number;
    congestion_score: number;
    flow_valid: boolean;
    flow_violation_count: number;
    system_balance_ratio: number;
  };
  bottlenecks: {
    bottleneck_nodes: BottleneckNode[];
    congestion_score: number;
    bottleneck_count: number;
  };
  congestion_score: number;
  flow_conservation: {
    valid: boolean;
    violations: { entity_id: string; name: string; inflow: number; outflow: number; imbalance_ratio: number }[];
    violation_count: number;
    total_inflow: number;
    total_outflow: number;
    system_balance_ratio: number;
  };
  recovery: {
    recovery_score: number;
    avg_residual_impact: number;
    full_recovery_days_est: number;
    entity_recovery: { entity_id: string; recovery_ratio: number; residual_impact: number }[];
  };
  propagation_depth: number;
  system_energy: number;
  event_severity: string;
}

// ── Risk Score Types ──
export interface UnifiedRiskScore {
  entity_id: string;
  entity_name: string;
  raw_score: number;
  normalized_score: number;
  severity: string;
  components: {
    geopolitical_threat: number;
    proximity_score: number;
    network_centrality: number;
    logistics_pressure: number;
    temporal_persistence: number;
    uncertainty: number;
  };
  asset_class: string;
  regional_multiplier: number;
}

export interface RiskScoreResult {
  unified_risk_scores: UnifiedRiskScore[];
  confidence_score: number;
  event_severity: string;
}

// ── Scenario Catalog Types ──
export interface ScenarioCatalogEntry {
  scenario_id: string;
  scenario_name_en: string;
  scenario_name_ar: string;
  domain: string;
  trigger_type: string;
  severity_level: string;
  affected_sectors: string[];
  shock_intensity_default: number;
  scenario_parameters: Record<string, number>;
}

// ============================================================
// Core Intelligence Layer — Graph + Unified Pipeline Types
// ============================================================

export type GraphLayer = "geography" | "infrastructure" | "economy" | "finance" | "society";

export type StressClassification = "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL";

/** GCC Knowledge Graph node (76 nodes, 5 layers) */
export interface KnowledgeGraphNode {
  id: string;
  label: string;
  label_ar: string;
  layer: GraphLayer;
  type: string;
  weight: number;
  lat: number;
  lng: number;
  sensitivity: number;
  stress?: number;
  classification?: StressClassification;
}

/** GCC Knowledge Graph edge (190 causal edges) */
export interface KnowledgeGraphEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  polarity: number;
  label: string;
  label_ar: string;
  transmission?: number;
}

/** Subgraph response from /graph/subgraph */
export interface SubgraphData {
  center: string;
  depth: number;
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  node_count: number;
  edge_count: number;
}

/** Graph listing response */
export interface GraphNodesResponse {
  nodes: KnowledgeGraphNode[];
  total: number;
  layers: string[];
  total_graph_nodes: number;
  total_graph_edges: number;
}

export interface GraphEdgesResponse {
  edges: KnowledgeGraphEdge[];
  total: number;
}

/** Impacted entity on globe/map */
export interface ImpactedEntity {
  node_id: string;
  label: string;
  label_ar: string;
  lat: number;
  lng: number;
  stress: number;
  loss_usd: number;
  classification: StressClassification;
  layer: GraphLayer;
}

/** Scenario impact result from /graph/scenario/{id}/impacts */
export interface ScenarioImpactResult {
  scenario_id: string;
  severity: number;
  impacted_nodes: KnowledgeGraphNode[];
  activated_edges: KnowledgeGraphEdge[];
  total_nodes_impacted: number;
  total_estimated_loss_usd: number;
  propagation_depth: number;
}

/** Sector rollup from unified pipeline */
export interface SectorRollup {
  aggregate_stress: number;
  total_loss: number;
  node_count: number;
  classification: StressClassification;
}

/** Decision action from unified pipeline */
export interface DecisionActionV2 {
  id: string;
  action: string;
  action_ar: string;
  sector: string;
  owner: string;
  urgency: number;
  value: number;
  regulatory_risk: number;
  priority: number;
  target_node_id: string;
  target_lat: number;
  target_lng: number;
  loss_avoided_usd: number;
  cost_usd: number;
  confidence: number;
}

/** Trust metadata from unified pipeline */
export interface TrustMetadata {
  trace_id: string;
  audit_id: string;
  audit_hash: string;
  model_version: string;
  pipeline_version: string;
  data_sources: string[];
  confidence_score: number;
  warnings: string[];
  explanations: string[];
  stages_completed: string[];
  stage_log: Record<string, { status: string; duration_ms: number; detail?: string }>;
  provenance_chain: string[];
}

/** Full unified pipeline run result */
export interface UnifiedRunResult {
  run_id: string;
  status: "completed" | "failed";
  error?: string;
  scenario: {
    template_id: string;
    label: string;
    severity: number;
    horizon_hours: number;
  };
  headline: {
    total_loss_usd: number;
    total_nodes_impacted: number;
    propagation_depth: number;
  };
  graph_payload: {
    nodes: KnowledgeGraphNode[];
    edges: KnowledgeGraphEdge[];
    categories: string[];
  };
  map_payload: {
    impacted_entities: ImpactedEntity[];
    total_estimated_loss_usd: number;
  };
  propagation_steps: {
    from: string;
    to: string;
    weight: number;
    transmission: number;
    label: string;
  }[];
  sector_rollups: {
    banking: SectorRollup;
    insurance: SectorRollup;
    fintech: SectorRollup;
    [key: string]: SectorRollup;
  };
  decision_inputs: {
    run_id: string;
    total_loss_usd: number;
    actions: DecisionActionV2[];
    all_actions: DecisionActionV2[];
  };
  confidence: number;
  warnings: string[];
  stages_completed: string[];
  stage_log: Record<string, unknown>;
  duration_ms: number;
  trust?: TrustMetadata;
  /** Physics engine output (8 sub-fields) */
  physics?: {
    utilization_map: Record<string, unknown>;
    bottlenecks: { bottlenecks: unknown[]; severity: number };
    flow_conservation: { balanced: boolean; [k: string]: unknown };
    recovery: { recovery_score: number; [k: string]: unknown };
    system_stress: { stress_level: string; [k: string]: unknown };
    system_pressure: { pressure: number; [k: string]: unknown };
    shockwave_field: unknown[];
    propagation_result: Record<string, unknown>;
  };
  /** Math engine output (8 sub-fields) */
  math?: {
    risk_scores: Array<{ node_id: string; label: string; normalized_score: number; severity: string; [k: string]: unknown }>;
    model_confidence: number;
    confidence_interval: { mean: number; lower: number; upper: number };
    disruption_index: { score: number; [k: string]: unknown };
    sector_exposure: Record<string, unknown>;
    system_energy: number;
    propagation_depth: number;
    sector_spread: number;
  };
  /** Sector engine output (11 sub-fields) */
  sectors?: {
    financial_impacts: Array<{ entity_id: string; loss: number; exposure: number; impact_status: string; [k: string]: unknown }>;
    financial_headline: Record<string, unknown>;
    banking_stresses: Array<{ entity_id: string; lcr: number; cet1_ratio: number; capital_adequacy_ratio: number; [k: string]: unknown }>;
    banking_aggregate: Record<string, unknown>;
    insurance_stresses: Array<{ entity_id: string; solvency_ratio: number; combined_ratio: number; [k: string]: unknown }>;
    insurance_aggregate: Record<string, unknown>;
    fintech_stresses: Array<{ entity_id: string; service_availability: number; settlement_delay_minutes: number; [k: string]: unknown }>;
    fintech_aggregate: Record<string, unknown>;
    decision_plan: { actions: Array<{ action_id: string; rank: number; action_type: string; target_ref: string; priority_score: number; urgency: number; value: number; feasibility: number; expected_loss_reduction: number; execution_window_hours: number; [k: string]: unknown }>; [k: string]: unknown };
    explanation: { summary: string; drivers: Array<{ driver: string; magnitude: number; unit: string }>; assumptions: string[]; limitations: string[]; [k: string]: unknown };
    regulatory_state: { breach_level: string; aggregate_lcr: number; aggregate_solvency_ratio: number; mandatory_actions: string[]; [k: string]: unknown };
  };
  /** Model assumptions */
  assumptions?: string[];
}

/** Available scenario template for graph impact */
export interface GraphScenarioTemplate {
  id: string;
  label: string;
  label_ar?: string;
  sector?: string;
  severity_range?: [number, number];
  shock_count?: number;
}

// ── Live Signal Layer types ───────────────────────────────────────────────────

export type SeedStatus = "PENDING_REVIEW" | "APPROVED" | "REJECTED" | "EXPIRED";
export type SignalSector = "banking" | "fintech";
export type SignalSource = "acled" | "aisstream" | "opensky" | "crucix" | "manual";

/** Shape of a seed returned by GET /api/v1/signals/pending */
export interface ScenarioSeed {
  seed_id: string;
  signal_id: string;
  status: SeedStatus;
  sector: SignalSector;
  suggested_template_id: string;
  suggested_severity: number;
  suggested_horizon_hours: number;
  rationale: string;
  reviewed_by: string | null;
  review_reason: string | null;
  created_at: string;
}

/** Response from GET /api/v1/signals/pending */
export interface SeedListResponse {
  count: number;
  seeds: ScenarioSeed[];
}

/** Response from POST /api/v1/signals (202 Accepted) */
export interface IngestSignalResponse {
  seed_id: string;
  signal_id: string;
  status: SeedStatus;
  sector: SignalSector;
  suggested_template_id: string;
  suggested_severity: number;
  suggested_horizon_hours: number;
  signal_score: number;
  rationale: string;
}

/** Response from POST /api/v1/signals/seeds/{id}/approve */
export interface ApproveSeedResponse {
  seed_id: string;
  status: SeedStatus;
  run_id: string;
  reviewed_by: string;
  review_reason: string | null;
}

/** Response from POST /api/v1/signals/seeds/{id}/reject */
export interface RejectSeedResponse {
  seed_id: string;
  status: SeedStatus;
  reviewed_by: string;
  review_reason: string | null;
}

/** WebSocket event payload for signal.scored */
export interface WsSignalScoredData {
  signal_id: string;
  sector: SignalSector;
  event_type: string;
  signal_score: number;
  source: SignalSource;
  scored_at: string;
}

/** Discriminated union of all WebSocket event shapes from /ws/signals */
export type WsSignalEvent =
  | { event: "signal.scored"; data: WsSignalScoredData }
  | { event: "seed.pending";  data: { seed_id: string; signal_id: string; sector: SignalSector; suggested_template_id: string; suggested_severity: number; suggested_horizon_hours: number; rationale: string } }
  | { event: "seed.approved"; data: { seed_id: string; run_id: string; reviewed_by: string; sector: SignalSector; suggested_template_id: string } }
  | { event: "seed.rejected"; data: { seed_id: string; reviewed_by: string; sector: SignalSector; reason: string | null } };

// ── Operator Layer — Decision types ──────────────────────────────────────────

export type DecisionType =
  | "APPROVE_ACTION"
  | "REJECT_ACTION"
  | "ESCALATE"
  | "IGNORE"
  | "TRIGGER_RUN"
  | "OVERRIDE_RUN_RESULT";

export type OperatorDecisionStatus =
  | "CREATED"
  | "IN_REVIEW"
  | "EXECUTED"
  | "FAILED"
  | "CLOSED";

export type OutcomeStatus = "PENDING" | "SUCCESS" | "FAILURE" | "PARTIAL";

/** An operator-layer decision linked to a signal, seed, and/or run */
export interface OperatorDecision {
  decision_id:       string;
  source_signal_id:  string | null;
  source_seed_id:    string | null;
  source_run_id:     string | null;
  scenario_id:       string | null;
  decision_type:     DecisionType;
  decision_status:   OperatorDecisionStatus;
  decision_payload:  Record<string, unknown>;
  rationale:         string | null;
  confidence_score:  number | null;
  created_by:        string;
  outcome_status:    OutcomeStatus;
  outcome_payload:   Record<string, unknown>;
  outcome_id:        string | null;
  created_at:        string;
  updated_at:        string;
  closed_at:         string | null;
}

/** Response from GET /api/v1/decisions */
export interface DecisionListResponse {
  count:     number;
  decisions: OperatorDecision[];
}

/** Body for POST /api/v1/decisions */
export interface CreateDecisionRequest {
  decision_type:    DecisionType;
  source_signal_id?: string | null;
  source_seed_id?:   string | null;
  source_run_id?:    string | null;
  scenario_id?:      string | null;
  decision_payload?: Record<string, unknown>;
  rationale?:        string | null;
  confidence_score?: number | null;
  created_by?:       string | null;
}

/** Body for POST /api/v1/decisions/{id}/execute */
export interface ExecuteDecisionRequest {
  params?:      Record<string, unknown>;
  executed_by?: string | null;
}

/** Body for POST /api/v1/decisions/{id}/close */
export interface CloseDecisionRequest {
  outcome_status?: OutcomeStatus;
  closed_by?:      string | null;
}

// ── Outcome Intelligence Layer types ─────────────────────────────────────────

/** Full lifecycle status of an Outcome entity (separate from OperatorDecision.outcome_status) */
export type OutcomeLifecycleStatus =
  | "PENDING_OBSERVATION"
  | "OBSERVED"
  | "CONFIRMED"
  | "DISPUTED"
  | "CLOSED"
  | "FAILED";

/** Signal-detection classification: was the action correct given what happened? */
export type OutcomeClassification =
  | "TRUE_POSITIVE"
  | "FALSE_POSITIVE"
  | "TRUE_NEGATIVE"
  | "FALSE_NEGATIVE"
  | "PARTIALLY_REALIZED"
  | "NO_MATERIAL_IMPACT"
  | "OPERATIONALLY_SUCCESSFUL"
  | "OPERATIONALLY_FAILED";

/** A first-class outcome entity linked to a decision and/or run */
export interface Outcome {
  outcome_id:                  string;
  source_decision_id:          string | null;
  source_run_id:               string | null;
  source_signal_id:            string | null;
  source_seed_id:              string | null;
  outcome_status:              OutcomeLifecycleStatus;
  outcome_classification:      OutcomeClassification | null;
  observed_at:                 string | null;
  recorded_at:                 string;
  updated_at:                  string;
  closed_at:                   string | null;
  recorded_by:                 string;
  expected_value:              number | null;
  realized_value:              number | null;
  error_flag:                  boolean;
  time_to_resolution_seconds:  number | null;
  evidence_payload:            Record<string, unknown>;
  notes:                       string | null;
}

export interface OutcomeListResponse {
  count:    number;
  outcomes: Outcome[];
}

export interface CreateOutcomeRequest {
  source_decision_id?:     string | null;
  source_run_id?:          string | null;
  source_signal_id?:       string | null;
  source_seed_id?:         string | null;
  outcome_classification?: OutcomeClassification | null;
  expected_value?:         number | null;
  realized_value?:         number | null;
  evidence_payload?:       Record<string, unknown>;
  notes?:                  string | null;
  recorded_by?:            string | null;
}

export interface ObserveOutcomeRequest {
  evidence_payload?: Record<string, unknown>;
  realized_value?:   number | null;
  notes?:            string | null;
  observed_by?:      string | null;
}

export interface ConfirmOutcomeRequest {
  outcome_classification: OutcomeClassification;
  realized_value?:        number | null;
  notes?:                 string | null;
  confirmed_by?:          string | null;
}

export interface DisputeOutcomeRequest {
  reason:       string;
  notes?:       string | null;
  disputed_by?: string | null;
}

export interface CloseOutcomeRequest {
  notes?:     string | null;
  closed_by?: string | null;
}

// ── ROI / Decision Value Layer types ─────────────────────────────────────────

/** Deterministic classification of a computed net_value. */
export type ValueClassification =
  | "HIGH_VALUE"      // net_value ≥  1_000_000
  | "POSITIVE_VALUE"  // 0 < net_value < 1_000_000
  | "NEUTRAL"         // net_value ≈ 0 (±1 band)
  | "NEGATIVE_VALUE"  // -1_000_000 < net_value < 0
  | "LOSS_INDUCING";  // net_value ≤ -1_000_000

/**
 * A computed ROI entity derived from a confirmed Outcome.
 * Mirrors backend DecisionValue domain model exactly.
 * net_value = avoided_loss - (operational_cost + decision_cost + latency_cost)
 */
export interface DecisionValue {
  value_id:               string;
  source_outcome_id:      string;
  source_decision_id:     string | null;
  source_run_id:          string | null;
  computed_at:            string;         // ISO 8601 UTC
  computed_by:            string;
  expected_value:         number | null;  // copied from source Outcome
  realized_value:         number | null;  // copied from source Outcome
  avoided_loss:           number;
  operational_cost:       number;
  decision_cost:          number;
  latency_cost:           number;
  total_cost:             number;
  net_value:              number;
  value_confidence_score: number;         // 0.0–1.0
  value_classification:   ValueClassification;
  calculation_trace:      Record<string, unknown>;
  notes:                  string | null;
}

/** Response from GET /api/v1/values */
export interface DecisionValueListResponse {
  count:  number;
  values: DecisionValue[];
}

/** Body for POST /api/v1/values/compute */
export interface ComputeValueRequest {
  source_outcome_id:  string;
  avoided_loss?:      number | null;
  operational_cost?:  number;
  decision_cost?:     number;
  latency_cost?:      number;
  notes?:             string | null;
  computed_by?:       string | null;
}

/** Body for POST /api/v1/values/{id}/recompute */
export interface RecomputeValueRequest {
  avoided_loss?:      number | null;
  operational_cost?:  number | null;
  decision_cost?:     number | null;
  latency_cost?:      number | null;
  notes?:             string | null;
  computed_by?:       string | null;
}
