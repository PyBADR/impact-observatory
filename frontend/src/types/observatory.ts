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
  executive_report: Record<string, unknown>;
  flow_states: Record<string, unknown>[];
  propagation: Record<string, unknown>[];
  duration_ms: number;
}

// ── V4 Business Impact Types ──────────────────────────────────

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
  run_id: string;
  currency: string;
  peak_cumulative_loss: number;
  peak_loss_timestep: number;
  peak_loss_timestamp: string;
  system_time_to_first_failure_hours: number | null;
  first_failure_type: string | null;
  first_failure_scope_ref: string | null;
  critical_breach_count: number;
  reportable_breach_count: number;
  business_severity: "low" | "medium" | "high" | "severe";
  executive_status: "monitor" | "intervene" | "escalate" | "crisis";
}

export interface BusinessImpact {
  summary: BusinessImpactSummary;
  loss_trajectory: LossTrajectoryPoint[];
  time_to_failures: TimeToFailure[];
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
  run_id: string;
  status: string;
  time_config: {
    time_granularity_minutes: number;
    time_horizon_steps: number;
    shock_decay_rate: number;
    propagation_delay_steps: number;
    recovery_rate: number;
  };
  timesteps: TimeStepState[];
}

export interface RegulatoryState {
  run_id: string;
  timestamp: string;
  jurisdiction: string;
  regulatory_version: string;
  aggregate_lcr: number;
  aggregate_nsfr: number;
  aggregate_solvency_ratio: number;
  aggregate_capital_adequacy_ratio: number;
  breach_level: "none" | "minor" | "major" | "critical";
  mandatory_actions: string[];
  reporting_required: boolean;
}

// ── Extended RunResult with v4 fields ─────────────────────────

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
  | "CRITICAL";

export type ViewMode = "executive" | "analyst" | "regulatory";
export type Language = "en" | "ar";
export type Role = "viewer" | "analyst" | "operator" | "admin" | "regulator";
