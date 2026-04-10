/**
 * Phase 1.5 — View-Model Adapter Layer
 *
 * Maps raw backend engine outputs (TransmissionChain, CalibratedCounterfactual,
 * ActionPathways) into UI-ready view-model shapes for the 5 decision experience
 * components. Pure functions, never throw, safe defaults everywhere.
 */

import type {
  TransmissionChain,
  TransmissionNode,
  CalibratedCounterfactual,
  CounterfactualOutcome,
  CounterfactualDelta,
  ActionPathways,
  ClassifiedAction,
  ActionType,
  Reversibility,
} from "@/types/observatory";

// ── Primitives ──────────────────────────────────────────────────────────

function sn(v: unknown, fb = 0): number {
  if (typeof v === "number" && isFinite(v)) return v;
  return fb;
}

function ss(v: unknown, fb = "—"): string {
  if (v === null || v === undefined) return fb;
  const s = String(v).trim();
  return s.length === 0 ? fb : s;
}

// ── Executive Decision Strip View-Model ─────────────────────────────────

export interface ExecutiveDecisionCard {
  rank: number;
  action: string;
  action_ar: string;
  sector: string;
  owner: string;
  status: "CRITICAL" | "SEVERE" | "MONITOR";
  deadline: string;
  deadline_hours: number;
  downside_if_ignored: string;
  loss_avoided_usd: number;
  cost_usd: number;
  priority_score: number;
  urgency: number;
  type: ActionType;
  reversibility: Reversibility;
}

export function buildExecutiveStrip(
  pathways: ActionPathways | null | undefined,
): ExecutiveDecisionCard[] {
  if (!pathways) return [];

  const allActions: ClassifiedAction[] = [
    ...(pathways.immediate ?? []),
    ...(pathways.conditional ?? []),
    ...(pathways.strategic ?? []),
  ];

  // Sort by priority descending, take top 3
  const sorted = [...allActions].sort(
    (a, b) => sn(b.priority_score) - sn(a.priority_score),
  );

  return sorted.slice(0, 3).map((a, i) => {
    const urgency = sn(a.urgency);
    const hours = sn(a.time_to_act_hours);

    let status: "CRITICAL" | "SEVERE" | "MONITOR" = "MONITOR";
    if (a.type === "IMMEDIATE" || urgency >= 0.85) status = "CRITICAL";
    else if (a.type === "CONDITIONAL" || urgency >= 0.6) status = "SEVERE";

    // Compute downside narrative
    const lossAvoided = sn(a.loss_avoided_usd);
    let downside = `$${(lossAvoided / 1e6).toFixed(0)}M exposure left unmitigated`;
    if (lossAvoided >= 1e9)
      downside = `$${(lossAvoided / 1e9).toFixed(1)}B exposure left unmitigated`;

    return {
      rank: i + 1,
      action: ss(a.label),
      action_ar: ss(a.label_ar),
      sector: ss(a.sector),
      owner: ss(a.owner),
      status,
      deadline: ss(a.deadline),
      deadline_hours: hours,
      downside_if_ignored: downside,
      loss_avoided_usd: lossAvoided,
      cost_usd: sn(a.cost_usd),
      priority_score: sn(a.priority_score),
      urgency,
      type: a.type ?? "STRATEGIC",
      reversibility: a.reversibility ?? "MEDIUM",
    };
  });
}

// ── Decision Gate View-Model ────────────────────────────────────────────

export interface DecisionGateView {
  gate_status: "OPEN" | "REQUIRES_APPROVAL" | "AUTO_ESCALATED";
  approval_required: boolean;
  escalation_target: string;
  auto_escalation: boolean;
  risk_level: string;
  immediate_count: number;
  conditional_count: number;
  strategic_count: number;
  total_actions: number;
  highest_urgency: number;
  summary: string;
  summary_ar: string;
}

export function buildDecisionGate(
  pathways: ActionPathways | null | undefined,
): DecisionGateView {
  if (!pathways) {
    return {
      gate_status: "OPEN",
      approval_required: false,
      escalation_target: "—",
      auto_escalation: false,
      risk_level: "NOMINAL",
      immediate_count: 0,
      conditional_count: 0,
      strategic_count: 0,
      total_actions: 0,
      highest_urgency: 0,
      summary: "No actions pending",
      summary_ar: "لا توجد إجراءات معلقة",
    };
  }

  const imm = pathways.immediate ?? [];
  const cond = pathways.conditional ?? [];
  const strat = pathways.strategic ?? [];
  const riskLevel = ss(pathways.risk_level, "MODERATE");

  const allUrgencies = [...imm, ...cond, ...strat].map((a) => sn(a.urgency));
  const highestUrgency = allUrgencies.length > 0 ? Math.max(...allUrgencies) : 0;

  // Gate logic
  const isHighRisk = riskLevel === "HIGH" || riskLevel === "SEVERE";
  const hasImmediateActions = imm.length > 0;
  const autoEscalation = isHighRisk && highestUrgency >= 0.9;

  let gateStatus: "OPEN" | "REQUIRES_APPROVAL" | "AUTO_ESCALATED" = "OPEN";
  if (autoEscalation) gateStatus = "AUTO_ESCALATED";
  else if (hasImmediateActions || isHighRisk) gateStatus = "REQUIRES_APPROVAL";

  const escalationTarget = isHighRisk ? "CRO / Board Risk Committee" : "Risk Manager";

  return {
    gate_status: gateStatus,
    approval_required: gateStatus !== "OPEN",
    escalation_target: escalationTarget,
    auto_escalation: autoEscalation,
    risk_level: riskLevel,
    immediate_count: imm.length,
    conditional_count: cond.length,
    strategic_count: strat.length,
    total_actions: sn(pathways.total_actions),
    highest_urgency: highestUrgency,
    summary: ss(pathways.summary),
    summary_ar: ss(pathways.summary_ar),
  };
}

// ── Transmission Block View-Model ───────────────────────────────────────

export interface TransmissionBlockView {
  nodes: TransmissionNode[];
  total_delay_hours: number;
  max_severity: number;
  breakable_points: TransmissionNode[];
  chain_length: number;
  summary: string;
  summary_ar: string;
  critical_window_active: boolean;
}

export function buildTransmissionView(
  chain: TransmissionChain | null | undefined,
): TransmissionBlockView {
  if (!chain) {
    return {
      nodes: [],
      total_delay_hours: 0,
      max_severity: 0,
      breakable_points: [],
      chain_length: 0,
      summary: "No transmission data available",
      summary_ar: "لا تتوفر بيانات انتقال",
      critical_window_active: false,
    };
  }

  const nodes = chain.nodes ?? [];
  const breakable = chain.breakable_points ?? [];
  const totalDelay = sn(chain.total_delay);
  const maxSeverity = sn(chain.max_severity);

  return {
    nodes,
    total_delay_hours: totalDelay,
    max_severity: maxSeverity,
    breakable_points: breakable,
    chain_length: sn(chain.chain_length, nodes.length),
    summary: ss(chain.summary),
    summary_ar: ss(chain.summary_ar),
    critical_window_active: totalDelay <= 24 && maxSeverity >= 0.45,
  };
}

// ── Counterfactual Block View-Model ─────────────────────────────────────

export interface CounterfactualBlockView {
  baseline: CounterfactualOutcome;
  recommended: CounterfactualOutcome;
  alternative: CounterfactualOutcome;
  delta: CounterfactualDelta;
  narrative: string;
  narrative_ar: string;
  consistency_flag: string;
  confidence_score: number;
  recommended_is_better: boolean;
  savings_formatted: string;
}

const EMPTY_OUTCOME: CounterfactualOutcome = {
  label: "—",
  label_ar: "—",
  projected_loss_usd: 0,
  projected_loss_formatted: "$0",
  risk_level: "NOMINAL",
  recovery_days: 0,
  operational_cost_usd: 0,
  severity: 0,
};

const EMPTY_DELTA: CounterfactualDelta = {
  loss_reduction_usd: 0,
  loss_reduction_pct: 0,
  loss_reduction_formatted: "$0",
  alt_reduction_usd: 0,
  alt_reduction_pct: 0,
  recommended_net_benefit_usd: 0,
  alternative_net_benefit_usd: 0,
  recovery_improvement_days: 0,
  best_option: "equivalent",
  delta_explained: "No comparison available",
  delta_explained_ar: "لا تتوفر مقارنة",
};

export function buildCounterfactualView(
  cf: CalibratedCounterfactual | null | undefined,
): CounterfactualBlockView {
  if (!cf) {
    return {
      baseline: EMPTY_OUTCOME,
      recommended: EMPTY_OUTCOME,
      alternative: EMPTY_OUTCOME,
      delta: EMPTY_DELTA,
      narrative: "No counterfactual analysis available",
      narrative_ar: "لا يتوفر تحليل مقارن",
      consistency_flag: "CONSISTENT",
      confidence_score: 0,
      recommended_is_better: false,
      savings_formatted: "$0",
    };
  }

  const delta = cf.delta ?? EMPTY_DELTA;
  const savings = sn(delta.loss_reduction_usd);
  let savingsFormatted = `$${(savings / 1e6).toFixed(0)}M`;
  if (savings >= 1e9) savingsFormatted = `$${(savings / 1e9).toFixed(1)}B`;

  return {
    baseline: cf.baseline ?? EMPTY_OUTCOME,
    recommended: cf.recommended ?? EMPTY_OUTCOME,
    alternative: cf.alternative ?? EMPTY_OUTCOME,
    delta,
    narrative: ss(cf.narrative),
    narrative_ar: ss(cf.narrative_ar),
    consistency_flag: ss(cf.consistency_flag, "CONSISTENT"),
    confidence_score: sn(cf.confidence_score),
    recommended_is_better: sn(cf.recommended?.projected_loss_usd) <= sn(cf.baseline?.projected_loss_usd),
    savings_formatted: savingsFormatted,
  };
}
