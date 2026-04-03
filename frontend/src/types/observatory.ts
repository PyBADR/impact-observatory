// ============================================================
// Impact Observatory | مرصد الأثر — V1 TypeScript Types
// AUTO-ALIGNED with backend/src/simulation_schemas.py
// Last synced: 2026-04-03
// DO NOT manually edit field types — update simulation_schemas.py first
// ============================================================

// Maps to backend schemas exactly.
// IMPORTANT: sector_losses is List[SectorLoss] (array), NOT a dict.
// Backend contract enforces this — frontend can safely call .map()/.reduce().

export interface ScenarioCreate {
  scenario_id: string;
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

// ── Sub-models (aligned with simulation_schemas.py) ─────────────────

/** Sector-level loss row — always a list item, never a dict key. */
export interface SectorLoss {
  sector: string;
  loss_usd: number;
  pct: number;
}

/**
 * Entity-level financial impact.
 * Maps to backend EntityImpact / FinancialImpact (the entity-level shape).
 * Used in financial_impact.top_entities and the top-level financial[] alias.
 */
export interface EntityImpact {
  entity_id: string;
  entity_label: string;
  loss_usd: number;
  direct_loss_usd: number;
  indirect_loss_usd: number;
  systemic_loss_usd: number;
  stress_score: number;
  classification: string;
  peak_day: number;
  sector: string;
  propagation_factor: number;
}

/**
 * @deprecated Use EntityImpact instead — same shape, renamed for clarity.
 * Kept for backward compat with components that import FinancialImpact.
 */
export interface FinancialImpact extends EntityImpact {
  /** @deprecated use loss_usd */
  loss_pct_gdp?: number;
  /** @deprecated use peak_day */
  recovery_days?: number;
  /** @deprecated use stress_score */
  confidence?: number;
  /** @deprecated use stress_score */
  stress_level?: number;
}

/** Full financial impact block from backend (financial_impact field). */
export interface FinancialImpactBlock {
  total_loss_usd: number;
  total_loss_formatted: string;
  direct_loss_usd: number;
  indirect_loss_usd: number;
  systemic_loss_usd: number;
  systemic_multiplier: number;
  affected_entities: number;
  critical_entities: number;
  top_entities: EntityImpact[];
  gdp_impact_pct: number;
  /** Array of sector losses — backend guarantees this is always an array. */
  sector_losses: SectorLoss[];
  confidence_interval: { lower: number; upper: number; confidence?: number };
}

/**
 * Banking institution detail.
 * The backend may return an empty array for affected_institutions.
 * The normalizeRunResult() function in dashboard/page.tsx populates this.
 */
export interface BankingInstitution {
  id: string;
  name: string;
  name_ar: string;
  country: string;
  exposure_usd: number;
  stress: number;
  projected_car_pct: number;
}

export interface BankingStress {
  run_id: string;
  sector: string;
  total_exposure_usd: number;
  liquidity_stress: number;
  credit_stress: number;
  fx_stress: number;
  market_stress: number;
  wholesale_funding_stress: number;
  interbank_contagion: number;
  time_to_liquidity_breach_hours: number;   // alias for time_to_breach_hours
  time_to_breach_hours?: number;            // backward-compat alias
  capital_adequacy_impact_pct: number;
  car_ratio?: number;
  lcr_ratio?: number;
  outflow_rate?: number;
  aggregate_stress: number;
  classification: Classification;
  affected_institutions: BankingInstitution[];
}

/**
 * Insurance line detail.
 * The backend may return an empty array for affected_lines.
 */
export interface InsuranceLine {
  id: string;
  name: string;
  name_ar: string;
  exposure_usd: number;
  claims_surge: number;
  stress: number;
}

export interface InsuranceStress {
  run_id: string;
  sector: string;
  portfolio_exposure_usd: number;
  tiv_exposure_usd?: number;
  tiv_exposure?: number;
  claims_surge_multiplier: number;
  severity_index: number;
  loss_ratio: number;
  combined_ratio: number;
  reserve_adequacy_ratio: number;
  reserve_adequacy?: number;
  underwriting_status: string;
  /**
   * Time to insolvency in hours.
   * 9999.0 = no imminent insolvency risk — display as "N/A".
   */
  time_to_insolvency_hours: number;
  reinsurance_trigger: boolean;
  ifrs17_risk_adjustment_pct: number;
  aggregate_stress: number;
  classification: Classification;
  affected_lines: InsuranceLine[];
}

/**
 * Fintech platform detail.
 * The backend may return an empty array for affected_platforms.
 */
export interface FintechPlatform {
  id: string;
  name: string;
  name_ar: string;
  country: string;
  volume_impact_pct: number;
  cross_border_stress: number;
  stress: number;
}

export interface FintechStress {
  run_id: string;
  sector: string;
  payment_volume_impact_pct: number;
  settlement_delay_hours: number;
  api_availability_pct: number;
  cross_border_disruption: number;
  digital_banking_stress: number;
  digital_stress?: number;
  liquidity_stress?: number;
  payment_disruption_score?: number;
  time_to_payment_failure_hours: number;
  aggregate_stress: number;
  classification: Classification;
  affected_platforms: FintechPlatform[];
}

/**
 * Decision action — maps to backend DecisionAction / ActionItem.
 * IMPORTANT: the field is `priority_score` (not `priority`) in the backend schema.
 * The normalizeRunResult() in dashboard/page.tsx maps priority_score → priority
 * for backward compatibility with older components.
 */
export interface DecisionAction {
  /** Normalized ID — may come from action_id or rank in raw output. */
  id: string;
  action_id?: string;
  rank?: number;
  action: string;
  action_ar: string | null;
  sector: string;
  owner: string;
  urgency: number;
  /**
   * priority_score is the authoritative backend field.
   * The normalization layer in dashboard/page.tsx also exposes this as `priority`
   * for backward-compat with components that read action.priority.
   */
  priority_score: number;
  /** @deprecated Use priority_score — kept for backward compat in normalized actions. */
  priority?: number;
  /** Normalized value field — computed from priority_score. */
  value?: number;
  regulatory_risk: number;
  feasibility?: number;
  time_to_act_hours: number;
  time_to_failure_hours?: number;
  loss_avoided_usd: number;
  loss_avoided_formatted?: string;
  cost_usd: number;
  cost_formatted?: string;
  confidence?: number;
  status?: string;
  escalation_trigger?: string;
}

export interface DecisionPlan {
  run_id?: string;
  scenario_label?: string | null;
  total_loss_usd?: number;
  peak_day?: number;
  /** Alias used by orchestrator: system_time_to_first_failure_hours */
  time_to_failure_hours?: number;
  time_to_first_failure_hours?: number;
  system_time_to_first_failure_hours?: number;
  business_severity?: string;
  actions: DecisionAction[];
  all_actions?: DecisionAction[];
  escalation_triggers: string[];
  monitoring_priorities: string[];
  immediate_actions?: DecisionAction[];
  short_term_actions?: DecisionAction[];
  long_term_actions?: DecisionAction[];
  priority_matrix?: {
    IMMEDIATE: string[];
    URGENT: string[];
    MONITOR: string[];
    WATCH: string[];
  };
  five_questions?: Record<string, unknown>;
}

export interface CausalStep {
  step: number;
  entity_id: string;
  entity_label: string;
  entity_label_ar?: string | null;
  /** The mechanism description — also may be in mechanism_en */
  event?: string;
  event_ar?: string | null;
  mechanism?: string;
  mechanism_en?: string;
  mechanism_ar?: string;
  impact_usd: number;
  impact_usd_formatted?: string;
  stress_delta: number;
  sector?: string;
  hop?: number;
  confidence?: number;
}

export interface ExplanationPack {
  run_id?: string;
  scenario_label?: string | null;
  narrative_en: string;
  narrative_ar: string;
  causal_chain: CausalStep[];   // Always 20 steps
  total_steps?: number;
  headline_loss_usd?: number;
  peak_day?: number;
  confidence?: number;
  confidence_score?: number;
  methodology: string;
  model_equation?: string;
  source?: string;
  sensitivity?: Record<string, unknown>;
  uncertainty_bands?: Record<string, unknown>;
}

export interface RunHeadline {
  total_loss_usd: number;
  total_loss_formatted?: string;
  peak_day: number;
  max_recovery_days: number;
  average_stress: number;
  affected_entities: number;
  critical_count: number;
  elevated_count: number;
  severity_code?: string;
}

export interface BottleneckNode {
  node_id: string;
  node_label?: string;
  label?: string;
  bottleneck_score?: number;
  utilization?: number;
  criticality?: number;
  redundancy?: number;
  degree?: number;
  rank?: number;
  sector?: string;
  lat?: number;
  lng?: number;
  is_critical_bottleneck?: boolean;
}

export interface PhysicalSystemStatus {
  nodes_assessed: number;
  saturated_nodes: number;
  flow_balance_status: string;
  system_utilization: number;
  /** Always a number — .toFixed() safe */
  congestion_score: number;
  /** Always a number — .toFixed() safe */
  recovery_score: number;
  /** May contain string IDs or BottleneckNode objects */
  bottlenecks: Array<string | BottleneckNode>;
  node_states?: Record<string, unknown>;
}

export interface SectorAnalysisRow {
  sector: string;
  exposure: number;
  stress: number;
  classification: string;
  risk_level: string;
}

export interface RecoveryPoint {
  day: number;
  recovery_fraction: number;
  damage_remaining: number;
  residual_stress: number;
}

export interface RunResult {
  // Identity
  schema_version: string;
  run_id: string;
  model_version: string;
  status: string;
  pipeline_stages_completed: number;
  stage_timings?: Record<string, number>;
  duration_ms: number;

  // Scenario context
  scenario: {
    scenario_id: string;
    label: string;
    label_ar: string | null;
    severity: number;
    horizon_hours: number;
  };
  scenario_id: string;
  severity: number;
  horizon_hours: number;
  time_horizon_days: number;

  // Core numeric outputs — NEVER None
  event_severity: number;
  peak_day: number;
  confidence_score: number;
  propagation_score: number;
  unified_risk_score: number;
  risk_level: string;
  congestion_score: number;       // top-level alias for physical_system_status.congestion_score
  recovery_score: number;         // top-level alias for physical_system_status.recovery_score

  // Structured sub-objects
  financial_impact: FinancialImpactBlock;
  sector_analysis: SectorAnalysisRow[];
  propagation_chain?: Record<string, unknown>[];
  physical_system_status: PhysicalSystemStatus;
  bottlenecks: BottleneckNode[];
  recovery_trajectory: RecoveryPoint[];

  // Sector stress — from simulation engine (banking_stress, insurance_stress, fintech_stress)
  banking_stress: BankingStress;
  insurance_stress: InsuranceStress;
  fintech_stress: FintechStress;

  // Plan and explanation
  explainability: ExplanationPack;
  decision_plan: DecisionPlan;
  headline: RunHeadline;

  // ── Backward-compatible aliases (populated by run_orchestrator.py) ──
  /** financial[] = financial_impact.top_entities (EntityImpact list) */
  financial: EntityImpact[];
  /** banking = banking_stress (alias) */
  banking: BankingStress;
  /** insurance = insurance_stress (alias) */
  insurance: InsuranceStress;
  /** fintech = fintech_stress (alias) */
  fintech: FintechStress;
  /**
   * decisions = decision_plan (remapped by orchestrator)
   * Contains top 3 actions only (not the full plan).
   * Also contains system_time_to_first_failure_hours from decision_plan.
   */
  decisions: DecisionPlan;
  /** explanation = explainability (alias) */
  explanation: ExplanationPack;
  /** system_stress = physical_system_status (alias) */
  system_stress: PhysicalSystemStatus;
  /** system_stress_score = unified_risk_score (numeric alias) */
  system_stress_score: number;

  // Report & extended blocks
  executive_report?: Record<string, unknown>;
  flow_states?: Record<string, unknown>[];
  propagation?: Record<string, unknown>[];
  flow_analysis?: Record<string, unknown>;

  // Business impact, timeline, regulatory
  business_impact?: BusinessImpact;
  timeline?: TimelineResult;
  regulatory_state?: RegulatoryState | Record<string, unknown>;

  // Convenience aliases
  headline_loss_usd?: number;
  severity_pct?: number;

  // Trace
  trace_id?: string;
}

// ── V4 Business Impact Types ──────────────────────────────

export interface LossTrajectoryPoint {
  run_id: string;
  scope_level: "entity" | "sector" | "system";
  scope_ref: string;
  timestep_index: number;
  timestamp: string;
  direct_loss: number;
  propagated_loss: number;
  cumulative_loss: number;
  revenue_at_risk: number;
  loss_velocity: number;
  loss_acceleration: number;
  status: "stable" | "deteriorating" | "critical" | "failed";
}

export interface TimeToFailure {
  run_id: string;
  scope_level: "entity" | "sector" | "system";
  scope_ref: string;
  failure_type: string;
  failure_threshold_value: number;
  current_value_at_t0: number;
  predicted_failure_timestep: number | null;
  predicted_failure_timestamp: string | null;
  time_to_failure_hours: number | null;
  confidence_score: number;
  failure_reached_within_horizon: boolean;
}

export interface RegulatoryBreachEvent {
  run_id: string;
  timestep_index: number;
  timestamp: string;
  scope_level: "entity" | "sector" | "system";
  scope_ref: string;
  metric_name: string;
  metric_value: number;
  threshold_value: number;
  breach_direction: "below_minimum" | "above_maximum";
  breach_level: "minor" | "major" | "critical";
  first_breach: boolean;
  reportable: boolean;
}

export interface BusinessImpactSummary {
  run_id?: string;
  currency?: string;
  peak_cumulative_loss: number;
  peak_loss_timestep?: number;
  peak_loss_timestamp: string;
  system_time_to_first_failure_hours?: number | null;
  first_failure_type?: string | null;
  first_failure_scope_ref?: string | null;
  critical_breach_count?: number;
  reportable_breach_count?: number;
  business_severity: string;
  executive_status: string;
}

export interface BusinessImpact {
  summary: BusinessImpactSummary;
  loss_trajectory?: LossTrajectoryPoint[];
  time_to_failures?: TimeToFailure[];
  regulatory_breach_events: RegulatoryBreachEvent[];
}

export interface TimeStepState {
  run_id: string;
  timestep_index: number;
  timestamp: string;
  shock_intensity_effective: number;
  aggregate_loss: number;
  aggregate_flow: number;
  regulatory_breach_count: number;
  system_status: "stable" | "degrading" | "critical" | "failed";
}

export interface TimelineResult {
  run_id?: string;
  status?: string;
  horizon_days?: number;
  recovery_trajectory?: RecoveryPoint[];
  time_config?: {
    time_granularity_minutes: number;
    time_horizon_steps: number;
    shock_decay_rate: number;
    propagation_delay_steps: number;
    recovery_rate: number;
  };
  timesteps?: TimeStepState[];
}

export interface RegulatoryState {
  run_id?: string;
  timestamp?: string;
  jurisdiction?: string;
  regulatory_version?: string;
  aggregate_lcr?: number;
  aggregate_nsfr?: number;
  aggregate_solvency_ratio?: number;
  aggregate_capital_adequacy_ratio?: number;
  breach_level?: "none" | "minor" | "major" | "critical";
  mandatory_actions?: string[];
  reporting_required?: boolean;
  // Fields from run_orchestrator.py regulatory_state block
  lcr_breached?: boolean;
  car_breached?: boolean;
  combined_ratio_breached?: boolean;
  classification?: string;
}

// ── Extended RunResult with v4 fields ─────────────────────

export interface RunResultV4 extends RunResult {
  business_impact: BusinessImpact;
  timeline: TimelineResult;
  regulatory_state: RegulatoryState;
  headline_loss_usd: number;
  severity_pct: number;
  peak_day: number;
}

export type Classification =
  | "NOMINAL"
  | "LOW"
  | "MODERATE"
  | "ELEVATED"
  | "CRITICAL"
  | "GUARDED"
  | "HIGH"
  | "SEVERE";

export type ViewMode = "executive" | "analyst" | "regulatory";
export type Language = "en" | "ar";
export type Role = "viewer" | "analyst" | "operator" | "admin" | "regulator";

export interface RunSummary {
  run_id: string;
  scenario_id: string;
  severity: number;
  status: string;
  headline_loss_usd: number;
  peak_day: number;
  severity_code: string | null;
  created_at: string | null;
  duration_ms: number | null;
}
