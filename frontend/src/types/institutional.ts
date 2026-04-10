/**
 * Institutional Interface Layer — TypeScript contracts.
 *
 * These types match backend Pydantic models in
 * `backend/src/schemas/institutional_interface.py` exactly.
 *
 * Source of truth: backend Pydantic models → these interfaces → frontend consumers.
 */

// ═══════════════════════════════════════════════════════════════════════════════
//  Stage 70 — Calibration Surface
// ═══════════════════════════════════════════════════════════════════════════════

export interface AuditResultItem {
  decision_id: string;
  action_id: string;
  category_error_flag: boolean;
  scenario_alignment_score: number;
  sector_alignment_score: number;
  node_coverage_score: number;
  urgency_appropriateness: number;
  feasibility_realism: number;
  cost_proportionality: number;
  action_quality_composite: number;
  validation_notes: Array<Record<string, string>>;
}

export interface RankedDecisionItem {
  decision_id: string;
  action_id: string;
  calibrated_rank: number;
  ranking_score: number;
  previous_rank: number;
  rank_delta: number;
  factors: Array<Record<string, number>>;
  crisis_boost: number;
}

export interface AuthorityAssignmentItem {
  decision_id: string;
  action_id: string;
  primary_authority_en: string;
  primary_authority_ar: string;
  escalation_authority_en: string;
  escalation_authority_ar: string;
  oversight_authority_en: string;
  oversight_authority_ar: string;
  operational_authority_en: string;
  operational_authority_ar: string;
  authority_level: string;
  cross_border_coordination: boolean;
}

export interface CalibrationResultItem {
  decision_id: string;
  action_id: string;
  calibration_confidence: number;
  expected_calibration_error: number;
  adjustment_factor: number;
  calibration_grade: string;
  confidence_band_low: number;
  confidence_band_high: number;
  calibration_notes: Array<Record<string, string>>;
}

export interface TrustResultItem {
  decision_id: string;
  action_id: string;
  trust_composite: number;
  trust_level: string;
  execution_mode: string;
  dimension_scores: Record<string, number>;
  hard_constraints_applied: string[];
  trust_notes: Array<Record<string, string>>;
}

export interface CalibrationCounts {
  audited: number;
  ranked: number;
  authorities_assigned: number;
  calibrated: number;
  trust_scored: number;
  category_errors: number;
  high_trust: number;
  medium_trust: number;
  low_trust: number;
  blocked: number;
  auto_executable: number;
}

export interface CalibrationLayerResponse {
  run_id: string;
  stage: number;
  audit_results: AuditResultItem[];
  ranked_decisions: RankedDecisionItem[];
  authority_assignments: AuthorityAssignmentItem[];
  calibration_results: CalibrationResultItem[];
  trust_results: TrustResultItem[];
  stage_timings: Record<string, number>;
  total_time_ms: number;
  counts: CalibrationCounts;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Stage 80 — Trust Surface
// ═══════════════════════════════════════════════════════════════════════════════

export interface ScenarioValidationModel {
  scenario_id: string;
  scenario_type: string;
  scenario_type_ar: string;
  taxonomy_valid: boolean;
  fallback_applied: boolean;
  fallback_method: string;
  classification_confidence: number;
  enforcement_notes: Array<Record<string, string>>;
}

export interface ValidationResultItem {
  decision_id: string;
  action_id: string;
  scenario_valid: boolean;
  sector_valid: boolean;
  node_coverage_valid: boolean;
  operational_feasibility: boolean;
  category_error_flag: boolean;
  validation_status: string;
  validation_status_ar: string;
  dimension_details: Array<Record<string, string>>;
}

export interface AuthorityProfileItem {
  decision_id: string;
  action_id: string;
  country: string;
  country_ar: string;
  primary_owner_en: string;
  primary_owner_ar: string;
  secondary_owner_en: string;
  secondary_owner_ar: string;
  regulator_en: string;
  regulator_ar: string;
  escalation_chain: Array<Record<string, string>>;
  cross_border_entities: Array<Record<string, string>>;
}

export interface CausalStep {
  step: number;
  event_en: string;
  event_ar: string;
  mechanism: string;
  severity_contribution: number;
}

export interface DecisionExplanationItem {
  decision_id: string;
  action_id: string;
  trigger_reason_en: string;
  trigger_reason_ar: string;
  causal_path: CausalStep[];
  propagation_summary_en: string;
  propagation_summary_ar: string;
  regime_context_en: string;
  regime_context_ar: string;
  ranking_reason_en: string;
  ranking_reason_ar: string;
  rejection_reason_en: string;
  rejection_reason_ar: string;
  narrative_en: string;
  narrative_ar: string;
}

export interface LearningUpdateItem {
  decision_id: string;
  action_id: string;
  calibration_error: number;
  action_adjustment: string;
  action_adjustment_ar: string;
  ranking_adjustment: number;
  confidence_adjustment: number;
  learning_velocity: string;
  learning_velocity_ar: string;
  recommendations: Array<Record<string, string>>;
}

export interface OverrideResultItem {
  decision_id: string;
  action_id: string;
  final_status: string;
  final_status_ar: string;
  override_reason_en: string;
  override_reason_ar: string;
  override_rule: string;
  validation_status: string;
  trust_level: string;
  trust_score: number;
  calibration_grade: string;
  learning_action: string;
  taxonomy_confidence: number;
  override_chain: Array<Record<string, string>>;
}

export interface TrustCounts {
  validated: number;
  valid: number;
  conditionally_valid: number;
  rejected: number;
  authorities_refined: number;
  explanations_generated: number;
  learning_updates: number;
  blocked: number;
  human_required: number;
  conditional: number;
  auto_executable: number;
  taxonomy_valid: boolean;
  taxonomy_confidence: number;
}

export interface TrustLayerResponse {
  run_id: string;
  stage: number;
  scenario_validation: ScenarioValidationModel;
  validation_results: ValidationResultItem[];
  authority_profiles: AuthorityProfileItem[];
  explanations: DecisionExplanationItem[];
  learning_updates: LearningUpdateItem[];
  override_results: OverrideResultItem[];
  stage_timings: Record<string, number>;
  total_time_ms: number;
  counts: TrustCounts;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Explainability Surface
// ═══════════════════════════════════════════════════════════════════════════════

export interface ExplainabilityResponse {
  run_id: string;
  scenario_id: string;
  scenario_type: string;
  taxonomy_confidence: number;
  explanations: DecisionExplanationItem[];
  override_summary: OverrideResultItem[];
  total_decisions: number;
  blocked_count: number;
  human_required_count: number;
  auto_executable_count: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Audit Trail Surface
// ═══════════════════════════════════════════════════════════════════════════════

export interface AuditTrailEntry {
  entry_id: string;
  run_id: string;
  decision_id: string;
  timestamp: string;
  source_stage: number;
  source_engine: string;
  event_type: string;
  actor: string;
  payload_hash: string;
  payload: Record<string, unknown>;
}

export interface AuditTrailResponse {
  run_id: string;
  entries: AuditTrailEntry[];
  total_entries: number;
  integrity_verified: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Decision Summary Surface
// ═══════════════════════════════════════════════════════════════════════════════

export interface DecisionSummaryItem {
  decision_id: string;
  action_id: string;
  action_en: string;
  action_ar: string;
  sector: string;
  decision_owner_en: string;
  decision_owner_ar: string;
  deadline_hours: number;
  trust_level: string;
  trust_score: number;
  execution_mode: string;
  execution_mode_ar: string;
  ranking_score: number;
  calibrated_rank: number;
  calibration_grade: string;
  calibration_confidence: number;
  explainability_available: boolean;
  override_rule: string;
  override_reason_en: string;
  override_reason_ar: string;
  audit_entries_count: number;
}

export interface DecisionSummaryResponse {
  run_id: string;
  scenario_id: string;
  scenario_type: string;
  pipeline_stages_completed: number;
  decisions: DecisionSummaryItem[];
  total_decisions: number;
  execution_breakdown: Record<string, number>;
  trust_breakdown: Record<string, number>;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Execution Mode & Trust Level Enums (for UI consumption)
// ═══════════════════════════════════════════════════════════════════════════════

export type ExecutionMode = "BLOCKED" | "HUMAN_REQUIRED" | "CONDITIONAL" | "AUTO_EXECUTABLE";
export type TrustLevel = "LOW" | "MEDIUM" | "HIGH";
export type CalibrationGrade = "A" | "B" | "C" | "D";
export type LearningVelocity = "FAST" | "MODERATE" | "SLOW";
export type ValidationStatus = "VALID" | "CONDITIONALLY_VALID" | "REJECTED";
