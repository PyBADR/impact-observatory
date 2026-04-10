/**
 * Metrics Provenance Layer — TypeScript contracts.
 *
 * These types match backend Pydantic models in
 * `backend/src/schemas/provenance_models.py` exactly.
 *
 * Source of truth: backend Pydantic models → these interfaces → frontend consumers.
 */

// ═══════════════════════════════════════════════════════════════════════════════
//  1. Metric Provenance — why this number
// ═══════════════════════════════════════════════════════════════════════════════

export interface ContributingFactor {
  factor_name: string;
  factor_name_ar: string;
  factor_value: number;
  weight: number;
  description_en: string;
  description_ar: string;
}

export interface MetricProvenance {
  metric_name: string;
  metric_name_ar: string;
  metric_value: number;
  unit: string;
  time_horizon: string;
  source_basis: string;
  model_basis: string;
  formula: string;
  contributing_factors: ContributingFactor[];
  data_recency: string;
  confidence_notes: string;
}

export interface MetricsProvenanceResponse {
  run_id: string;
  scenario_id: string;
  metrics: MetricProvenance[];
  total_metrics: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  2. Factor Breakdown — what drove this number
// ═══════════════════════════════════════════════════════════════════════════════

export interface FactorContribution {
  factor_name: string;
  factor_name_ar: string;
  contribution_value: number;
  contribution_pct: number;
  rationale_en: string;
  rationale_ar: string;
}

export interface MetricFactorBreakdown {
  metric_name: string;
  metric_name_ar: string;
  metric_value: number;
  unit: string;
  factors: FactorContribution[];
  factors_sum: number;
  coverage_pct: number;
}

export interface FactorBreakdownResponse {
  run_id: string;
  scenario_id: string;
  breakdowns: MetricFactorBreakdown[];
  total_metrics: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  3. Metric Range — uncertainty bands
// ═══════════════════════════════════════════════════════════════════════════════

export interface MetricRange {
  metric_name: string;
  metric_name_ar: string;
  min_value: number;
  expected_value: number;
  max_value: number;
  confidence_band: string;
  unit: string;
  reasoning_en: string;
  reasoning_ar: string;
}

export interface MetricRangesResponse {
  run_id: string;
  scenario_id: string;
  ranges: MetricRange[];
  total_metrics: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  4. Decision Reasoning — why this decision, why this rank
// ═══════════════════════════════════════════════════════════════════════════════

export interface DecisionReasoning {
  decision_id: string;
  action_id: string;
  why_this_decision_en: string;
  why_this_decision_ar: string;
  why_now_en: string;
  why_now_ar: string;
  why_this_rank_en: string;
  why_this_rank_ar: string;
  affected_entities: string[];
  propagation_link_en: string;
  propagation_link_ar: string;
  regime_link_en: string;
  regime_link_ar: string;
  trust_link_en: string;
  trust_link_ar: string;
  tradeoff_summary_en: string;
  tradeoff_summary_ar: string;
}

export interface DecisionReasoningResponse {
  run_id: string;
  scenario_id: string;
  reasonings: DecisionReasoning[];
  total_decisions: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  5. Data Basis — what data period backs this metric
// ═══════════════════════════════════════════════════════════════════════════════

export type FreshnessFlag =
  | "CALIBRATED"
  | "SIMULATED"
  | "DERIVED"
  | "PARAMETRIC";

export interface DataBasis {
  metric_name: string;
  metric_name_ar: string;
  historical_basis_en: string;
  historical_basis_ar: string;
  scenario_basis_en: string;
  scenario_basis_ar: string;
  calibration_basis_en: string;
  calibration_basis_ar: string;
  freshness_flag: FreshnessFlag;
  freshness_detail_en: string;
  freshness_detail_ar: string;
  freshness_weak: boolean;
  model_type: string;
  analog_event: string;
  analog_period: string;
  analog_relevance: number;
}

export interface DataBasisResponse {
  run_id: string;
  scenario_id: string;
  data_bases: DataBasis[];
  total_metrics: number;
  weak_freshness_count: number;
}
