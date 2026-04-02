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

export type Classification =
  | "NOMINAL"
  | "LOW"
  | "MODERATE"
  | "ELEVATED"
  | "CRITICAL";

export type ViewMode = "executive" | "analyst" | "regulatory";
export type Language = "en" | "ar";
