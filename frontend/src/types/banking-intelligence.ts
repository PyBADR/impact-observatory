/**
 * Banking Intelligence Contract Types
 * TypeScript interfaces mapping backend Pydantic schemas
 * Auto-generated from backend/src/banking_intelligence/schemas/
 */

// ─── Decision Contract Enums ─────────────────────────────────────────────────

export enum DecisionStatus {
  DRAFT = "DRAFT",
  PENDING_APPROVAL = "PENDING_APPROVAL",
  APPROVED = "APPROVED",
  EXECUTING = "EXECUTING",
  EXECUTED = "EXECUTED",
  UNDER_REVIEW = "UNDER_REVIEW",
  CLOSED = "CLOSED",
  ROLLED_BACK = "ROLLED_BACK",
  EXPIRED = "EXPIRED",
  REJECTED = "REJECTED",
}

export enum DecisionType {
  PREVENTIVE = "preventive",
  MITIGATING = "mitigating",
  REACTIVE = "reactive",
  MONITORING = "monitoring",
  ESCALATION = "escalation",
  REGULATORY_COMPLIANCE = "regulatory_compliance",
}

export enum DecisionSector {
  BANKING = "banking",
  FINTECH = "fintech",
  INSURANCE = "insurance",
  PAYMENTS = "payments",
  CAPITAL_MARKETS = "capital_markets",
  CROSS_SECTOR = "cross_sector",
  SOVEREIGN = "sovereign",
}

export enum Reversibility {
  FULLY_REVERSIBLE = "fully_reversible",
  PARTIALLY_REVERSIBLE = "partially_reversible",
  IRREVERSIBLE = "irreversible",
  TIME_BOUNDED_REVERSIBLE = "time_bounded_reversible",
}

export enum ExecutionFeasibility {
  READY = "ready",
  REQUIRES_PREPARATION = "requires_preparation",
  BLOCKED = "blocked",
  CONDITIONAL = "conditional",
}

// ─── Counterfactual Enums ───────────────────────────────────────────────────

export enum ConfidenceLevel {
  VERY_HIGH = "very_high",
  HIGH = "high",
  MODERATE = "moderate",
  LOW = "low",
  VERY_LOW = "very_low",
}

// ─── Propagation Enums ──────────────────────────────────────────────────────

export enum TransferMechanism {
  LIQUIDITY_CHANNEL = "liquidity_channel",
  CREDIT_CHANNEL = "credit_channel",
  PAYMENT_CHANNEL = "payment_channel",
  CONFIDENCE_CHANNEL = "confidence_channel",
  OPERATIONAL_CHANNEL = "operational_channel",
  REGULATORY_CHANNEL = "regulatory_channel",
  MARKET_CHANNEL = "market_channel",
  CONTAGION = "contagion",
}

export enum InterventionType {
  CIRCUIT_BREAKER = "circuit_breaker",
  LIQUIDITY_INJECTION = "liquidity_injection",
  REGULATORY_HALT = "regulatory_halt",
  COLLATERAL_CALL = "collateral_call",
  COUNTERPARTY_ISOLATION = "counterparty_isolation",
  PAYMENT_REROUTING = "payment_rerouting",
  COMMUNICATION_DIRECTIVE = "communication_directive",
  MANUAL_OVERRIDE = "manual_override",
  NO_INTERVENTION_POSSIBLE = "no_intervention_possible",
}

export enum InterventionReadiness {
  READY = "ready",
  REQUIRES_APPROVAL = "requires_approval",
  REQUIRES_COORDINATION = "requires_coordination",
  NOT_READY = "not_ready",
  UNTESTED = "untested",
}

// ─── Outcome Review Enums ───────────────────────────────────────────────────

export enum ReviewWindowStatus {
  PENDING = "PENDING",
  OBSERVATION_COLLECTED = "OBSERVATION_COLLECTED",
  ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE",
  SKIPPED = "SKIPPED",
}

export enum LearningSignalType {
  MODEL_OVERESTIMATED = "model_overestimated",
  MODEL_UNDERESTIMATED = "model_underestimated",
  MODEL_ACCURATE = "model_accurate",
  DIRECTION_WRONG = "direction_wrong",
  TIMING_WRONG = "timing_wrong",
  MECHANISM_DIFFERENT = "mechanism_different",
  EXTERNAL_FACTOR = "external_factor",
}

export enum OutcomeClassification {
  BETTER_THAN_EXPECTED = "better_than_expected",
  AS_EXPECTED = "as_expected",
  WORSE_THAN_EXPECTED = "worse_than_expected",
  SIGNIFICANTLY_WORSE = "significantly_worse",
  OPPOSITE_DIRECTION = "opposite_direction",
}

// ─── Decision Contract Types ────────────────────────────────────────────────

export interface DependencySpec {
  dependency_id: string;
  dependency_type: string;
  is_satisfied: boolean;
  satisfied_at?: string | null;
  blocker_description?: string | null;
}

export interface RollbackPlan {
  is_rollback_possible: boolean;
  rollback_steps: string[];
  rollback_owner_id: string;
  max_rollback_window_hours?: number | null;
  estimated_rollback_cost_usd?: number | null;
  side_effects_of_rollback: string[];
}

export interface ObservationPlan {
  observation_windows_hours: number[];
  primary_metric: string;
  secondary_metrics: string[];
  baseline_value?: number | null;
  target_value?: number | null;
  alert_threshold?: number | null;
  observer_entity_id: string;
}

export interface StatusHistoryEntry {
  from_status: string;
  to_status: string;
  timestamp: string;
  changed_by: string;
  reason?: string | null;
}

export interface DecisionContract {
  decision_id: string;
  scenario_id: string;
  title: string;
  description?: string | null;
  sector: DecisionSector;
  decision_type: DecisionType;
  primary_owner_id: string;
  approver_id: string;
  supporting_entity_ids: string[];
  deadline_at: string;
  created_at: string;
  updated_at: string;
  executed_at?: string | null;
  closed_at?: string | null;
  trigger_condition: string;
  escalation_threshold: number;
  approval_required: boolean;
  auto_execute_on_approval: boolean;
  legal_authority_basis: string;
  reversibility: Reversibility;
  execution_feasibility: ExecutionFeasibility;
  dependencies: DependencySpec[];
  rollback_plan: RollbackPlan;
  observation_plan: ObservationPlan;
  status: DecisionStatus;
  status_reason?: string | null;
  status_history: StatusHistoryEntry[];
  counterfactual_id?: string | null;
  outcome_review_id?: string | null;
  value_audit_id?: string | null;
  source_run_id?: string | null;
}

// ─── Counterfactual Types ───────────────────────────────────────────────────

export interface ConfidenceDimensions {
  directional_confidence: number;
  impact_estimate_confidence: number;
  execution_confidence: number;
  data_sufficiency_confidence: number;
}

export interface DownsideRisk {
  worst_case_loss_usd: number;
  probability_of_worst_case: number;
  description: string;
  tail_risk_multiplier: number;
}

export interface AssumptionRecord {
  assumption_id: string;
  description: string;
  source: string;
  sensitivity: number;
  last_validated_at?: string | null;
}

export interface CounterfactualBranch {
  branch_label: string;
  description: string;
  expected_loss_usd: number;
  expected_cost_usd: number;
  expected_time_to_stabilize_hours: number;
  downside_risk: DownsideRisk;
  confidence: ConfidenceDimensions;
  delta_vs_baseline_usd: number;
  assumptions: AssumptionRecord[];
  net_expected_value_usd: number;
}

export interface CounterfactualContract {
  counterfactual_id: string;
  decision_id: string;
  scenario_id: string;
  created_at: string;
  updated_at: string;
  do_nothing: CounterfactualBranch;
  recommended_action: CounterfactualBranch;
  delayed_action: CounterfactualBranch;
  alternative_action: CounterfactualBranch;
  recommended_net_benefit_usd: number;
  confidence_adjusted_benefit_usd: number;
  delay_penalty_usd: number;
  analysis_horizon_hours: number;
  model_version: string;
  analyst_entity_id?: string | null;
}

// ─── Propagation Types ──────────────────────────────────────────────────────

export interface PropagationEvidence {
  evidence_type: string;
  reference_id?: string | null;
  description: string;
  observed_at?: string | null;
  relevance_score: number;
}

export interface InterventionSpec {
  intervention_type: InterventionType;
  description: string;
  owner_entity_id: string;
  readiness: InterventionReadiness;
  estimated_activation_hours: number;
  estimated_cost_usd?: number | null;
  effectiveness_estimate: number;
  side_effects: string[];
  requires_approval_from?: string | null;
  last_tested_at?: string | null;
  test_result?: string | null;
}

export interface PropagationContract {
  propagation_id: string;
  scenario_id: string;
  from_entity_id: string;
  to_entity_id: string;
  transfer_mechanism: TransferMechanism;
  delay_hours: number;
  severity_transfer: number;
  breakable_point: boolean;
  interventions: InterventionSpec[];
  actionable_owner_id: string;
  evidence_sources: PropagationEvidence[];
  confidence: number;
  created_at: string;
  updated_at: string;
  last_activated_at?: string | null;
  activation_count: number;
}

export interface PropagationChain {
  chain_id: string;
  scenario_id: string;
  links: PropagationContract[];
  total_delay_hours: number;
  cumulative_severity_transfer: number;
  first_breakable_point_index?: number | null;
}

// ─── Outcome Review Types ───────────────────────────────────────────────────

export interface ReviewWindow {
  window_hours: number;
  status: ReviewWindowStatus;
  observation_due_at?: string | null;
  observed_at?: string | null;
  expected_metric_value?: number | null;
  actual_metric_value?: number | null;
  metric_name: string;
  delta_from_expected?: number | null;
  delta_pct?: number | null;
  classification?: OutcomeClassification | null;
  narrative?: string | null;
}

export interface LearningSignal {
  signal_type: LearningSignalType;
  description: string;
  affected_model_component: string;
  suggested_recalibration?: string | null;
  magnitude: number;
  applies_to_scenarios: string[];
}

export interface ConfidenceRecalibration {
  dimension: string;
  original_confidence: number;
  recalibrated_confidence: number;
  adjustment_reason: string;
  evidence_window_hours: number;
}

export interface OutcomeReviewContract {
  review_id: string;
  decision_id: string;
  scenario_id: string;
  windows: ReviewWindow[];
  learning_signals: LearningSignal[];
  recalibrations: ConfidenceRecalibration[];
  overall_classification?: OutcomeClassification | null;
  overall_narrative?: string | null;
  review_complete: boolean;
  created_at: string;
  updated_at: string;
  reviewed_by?: string | null;
}

// ─── Value Audit Types ──────────────────────────────────────────────────────

export interface AssumptionTrace {
  assumption_id: string;
  description: string;
  value_used: number;
  source: string;
  sensitivity_to_outcome: number;
  was_validated: boolean;
  validation_result?: string | null;
}

export interface DecisionValueAudit {
  audit_id: string;
  decision_id: string;
  outcome_review_id: string;
  scenario_id: string;
  gross_loss_avoided_usd: number;
  implementation_cost_usd: number;
  side_effect_cost_usd: number;
  net_value_usd: number;
  confidence_adjusted_value_usd: number;
  composite_confidence: number;
  realized_value_usd?: number | null;
  variance_usd?: number | null;
  variance_pct?: number | null;
  assumptions_trace: AssumptionTrace[];
  cfo_defensible: boolean;
  defensibility_gaps: string[];
  created_at: string;
  updated_at: string;
  auditor_entity_id?: string | null;
}
