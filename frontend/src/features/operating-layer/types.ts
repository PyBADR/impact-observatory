/**
 * Decision Operating Layer — TypeScript Types
 *
 * Maps 1:1 to backend DecisionOperatingLayer output contract.
 * All fields have safe defaults in the backend — frontend can trust them.
 */

// ── Tradeoff Axis ──────────────────────────────────────────────────────

export interface TradeoffAxis {
  axis_en: string;
  axis_ar: string;
  left_en: string;
  left_ar: string;
  right_en: string;
  right_ar: string;
  /** Position on the axis: 0.0 = fully left, 1.0 = fully right */
  position: number;
  rationale_en: string;
  rationale_ar: string;
}

// ── Decision Anchor ────────────────────────────────────────────────────

export interface DecisionAnchor {
  owner: string;
  owner_ar: string;
  decision_type: "emergency" | "strategic" | "operational";
  decision_type_ar: string;
  decision_type_label: string;
  decision_type_label_ar: string;
  deadline_hours: number;
  deadline_classification: "IMMEDIATE" | "URGENT" | "STANDARD" | "EXTENDED";
  tradeoffs: {
    cost_vs_risk: TradeoffAxis;
    speed_vs_accuracy: TradeoffAxis;
    short_term_vs_long_term: TradeoffAxis;
  };
}

// ── Counterfactual Engine ──────────────────────────────────────────────

export interface SectorConsequence {
  sector: string;
  sector_ar: string;
  impact_en: string;
  impact_ar: string;
}

export interface CounterfactualOutcome {
  label_en: string;
  label_ar: string;
  financial_exposure_usd: number;
  financial_exposure_formatted: string;
  time_to_failure_hours: number;
  risk_level: string;
  sector_consequences: SectorConsequence[];
}

export interface DeltaSummary {
  savings_usd: number;
  savings_formatted: string;
  savings_pct: number;
  time_gained_hours: number;
  risk_reduction: string;
  recommendation_en: string;
  recommendation_ar: string;
}

export interface CounterfactualComparison {
  baseline_outcome: CounterfactualOutcome;
  recommended_outcome: CounterfactualOutcome;
  alternative_outcome: CounterfactualOutcome;
  delta_summary: DeltaSummary;
}

// ── Decision Gate ──────────────────────────────────────────────────────

export interface EscalationTrigger {
  trigger_en: string;
  trigger_ar: string;
  active: boolean;
}

export interface EscalationThreshold {
  loss_usd_threshold: number;
  loss_usd_threshold_formatted: string;
  stress_threshold: number;
  time_to_failure_threshold_hours: number;
  pressure_score_threshold: number;
}

export interface DecisionGate {
  gate_status: "open" | "pending_approval" | "escalated" | "executable";
  gate_status_label_en: string;
  gate_status_label_ar: string;
  approval_required: boolean;
  approval_owner: string;
  approval_owner_ar: string;
  escalation_threshold: EscalationThreshold;
  auto_escalation_triggers: EscalationTrigger[];
  active_triggers_count: number;
  gate_audit_hash: string;
  gate_rationale_en: string;
  gate_rationale_ar: string;
}

// ── Operating Layer (top-level) ────────────────────────────────────────

export interface OperatingLayer {
  version: string;
  generated_at: string;
  decision_anchor: DecisionAnchor;
  counterfactual_comparison: CounterfactualComparison;
  decision_gate: DecisionGate;
}
