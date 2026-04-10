/**
 * Impact Observatory | مرصد الأثر — Persona View Model Layer
 *
 * Pure transformation functions. No hooks, no side effects.
 * Components consume these view models — they do not parse raw RunResult directly.
 *
 * Personas:
 *   executive  → headline KPIs, sector summary, top decisions, ROI framing
 *   analyst    → full score breakdown, entity table, causal chain, run mechanics
 *   regulator  → decision lineage, audit trail, signal trace, pipeline accountability
 */

import type {
  RunResult,
  DecisionAction,
  Classification,
  BusinessSeverity,
  ExecutiveStatus,
  Language,
  WsSignalScoredData,
  ScenarioSeed,
  OperatorDecision,
  Outcome,
  OutcomeLifecycleStatus,
  OutcomeClassification,
  DecisionValue,
  ValueClassification,
} from "@/types/observatory";
import { formatUSD, formatHours, safePercent, safeFixed, safeArray } from "@/lib/format";
import { emitAudit } from "@/lib/audit";

/** Guard: parse a date string/number into a sort-safe timestamp.
 *  Invalid or missing values return 0 so they sort to the end consistently. */
function safeTime(v: unknown): number {
  if (!v) return 0;
  const t = new Date(v as string).getTime();
  return isFinite(t) ? t : 0;
}

/** Guard: coerce a value to a finite number; returns 0 for NaN/Infinity/null/undefined. */
function safeNum(v: unknown): number {
  const n = Number(v);
  return isFinite(n) ? n : 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// EXECUTIVE VIEW MODEL
// Emphasis: financial impact, sector status, decision priority, urgency framing
// ─────────────────────────────────────────────────────────────────────────────

export interface ExecutiveKPI {
  headlineLoss: string;
  headlineLossRaw: number;
  severity: string;
  severityRaw: number;
  peakDay: number;
  liquidityBreachLabel: string;
  liquidityBreachHours: number;
  businessSeverity: BusinessSeverity;
  executiveStatus: ExecutiveStatus;
  overallClassification: Classification;
  confidence: string;
  affectedEntities: number;
}

export interface ExecutiveSectorCard {
  name: string;
  nameAr: string;
  stress: number;
  stressLabel: string;
  classification: Classification;
  primaryMetricLabel: string;
  primaryMetricLabelAr: string;
  primaryMetricValue: string;
  secondaryMetricLabel: string;
  secondaryMetricValue: string;
}

export interface ExecutiveActionRow {
  id: string;
  action: string;
  actionAr: string | null;
  sector: string;
  owner: string;
  priority: number;
  lossAvoided: string;
  cost: string;
  timeToAct: string;
  urgency: number;
  confidence: number;
}

export interface ExecutiveOutcomesSummary {
  total: number;
  confirmed: number;
  disputed: number;
  pendingObservation: number;
  observed: number;
  failed: number;
  closed: number;
  mostRecentConfirmed: {
    outcomeId: string;
    classLabel: string;
    recordedBy: string;
    recordedAt: string;
  } | null;
}

export interface ExecutiveValueSummary {
  /** Total count of computed values */
  total: number;
  /** Sum of all net_values */
  totalNetValue: number;
  totalNetValueFormatted: string;
  /** Average confidence score across all values */
  avgConfidence: number;
  /** Count by classification */
  byClassification: Record<ValueClassification, number>;
  /** Highest net_value row — null when no values */
  topValue: {
    valueId: string;
    netValue: number;
    netValueFormatted: string;
    classification: ValueClassification;
    computedBy: string;
    computedAt: string;
    sourceOutcomeId: string;
  } | null;
}

export interface ExecutiveViewModel {
  kpis: ExecutiveKPI;
  sectors: ExecutiveSectorCard[];
  topActions: ExecutiveActionRow[];
  runId: string;
  scenarioLabel: string;
  scenarioLabelAr: string | null;
  narrativeSummary: string;
  totalLossFormatted: string;
  outcomesSummary: ExecutiveOutcomesSummary;
  valueSummary: ExecutiveValueSummary;
}

export function toExecutiveViewModel(result: RunResult, outcomes: Outcome[] = [], values: DecisionValue[] = []): ExecutiveViewModel {
  const { headline, banking, insurance, fintech, decisions, scenario, explanation } = result;

  // Derive overall worst classification
  const classRank: Record<Classification, number> = {
    NOMINAL: 0, LOW: 1, MODERATE: 2, ELEVATED: 3, CRITICAL: 4,
  };
  const overallClassification: Classification = [
    banking.classification, insurance.classification, fintech.classification,
  ].reduce<Classification>((worst, c) =>
    classRank[c] > classRank[worst] ? c : worst, "NOMINAL"
  );

  const kpis: ExecutiveKPI = {
    headlineLoss: formatUSD(headline.total_loss_usd),
    headlineLossRaw: headline.total_loss_usd,
    severity: `${Math.round(scenario.severity * 100)}%`,
    severityRaw: scenario.severity,
    peakDay: headline.peak_day,
    liquidityBreachHours: banking.time_to_liquidity_breach_hours,
    liquidityBreachLabel:
      banking.time_to_liquidity_breach_hours > 0
        ? formatHours(banking.time_to_liquidity_breach_hours)
        : "No breach projected",
    businessSeverity: result.business_severity,
    executiveStatus: result.executive_status,
    overallClassification,
    confidence: `${Math.round(result.global_confidence * 100)}%`,
    affectedEntities: headline.affected_entities,
  };

  const sectors: ExecutiveSectorCard[] = [
    {
      name: "Banking",
      nameAr: "القطاع البنكي",
      stress: banking.aggregate_stress,
      stressLabel: safePercent(banking.aggregate_stress),
      classification: banking.classification,
      primaryMetricLabel: "Total Exposure",
      primaryMetricLabelAr: "إجمالي التعرض",
      primaryMetricValue: formatUSD(banking.total_exposure_usd),
      secondaryMetricLabel: "Liquidity Breach",
      secondaryMetricValue: formatHours(banking.time_to_liquidity_breach_hours),
    },
    {
      name: "Insurance",
      nameAr: "التأمين",
      stress: insurance.aggregate_stress,
      stressLabel: safePercent(insurance.aggregate_stress),
      classification: insurance.classification,
      primaryMetricLabel: "Claims Surge",
      primaryMetricLabelAr: "ارتفاع المطالبات",
      primaryMetricValue: `${safeFixed(insurance.claims_surge_multiplier, 1)}×`,
      secondaryMetricLabel: "Reinsurance Trigger",
      secondaryMetricValue: insurance.reinsurance_trigger ? "TRIGGERED" : "Not triggered",
    },
    {
      name: "Fintech",
      nameAr: "الفنتك",
      stress: fintech.aggregate_stress,
      stressLabel: safePercent(fintech.aggregate_stress),
      classification: fintech.classification,
      primaryMetricLabel: "Payment Volume Impact",
      primaryMetricLabelAr: "أثر حجم المدفوعات",
      primaryMetricValue: `${Math.round(fintech.payment_volume_impact_pct)}%`,
      secondaryMetricLabel: "Settlement Delay",
      secondaryMetricValue: formatHours(fintech.settlement_delay_hours),
    },
  ];

  const topActions: ExecutiveActionRow[] = (decisions.actions ?? [])
    .slice(0, 3)
    .map((a: DecisionAction) => ({
      id: a.id,
      action: a.action,
      actionAr: a.action_ar,
      sector: a.sector,
      owner: a.owner,
      priority: a.priority,
      lossAvoided: formatUSD(a.loss_avoided_usd),
      cost: formatUSD(a.cost_usd),
      timeToAct: formatHours(a.time_to_act_hours),
      urgency: a.urgency,
      confidence: a.confidence,
    }));

  const confirmedOutcomes = outcomes.filter((o) => o.outcome_status === "CONFIRMED");
  const sortedConfirmed = [...confirmedOutcomes].sort(
    (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime(),
  );
  const mostRecentConfirmed = sortedConfirmed[0] ?? null;

  const outcomesSummary: ExecutiveOutcomesSummary = {
    total: outcomes.length,
    confirmed: confirmedOutcomes.length,
    disputed: outcomes.filter((o) => o.outcome_status === "DISPUTED").length,
    pendingObservation: outcomes.filter((o) => o.outcome_status === "PENDING_OBSERVATION").length,
    observed: outcomes.filter((o) => o.outcome_status === "OBSERVED").length,
    failed: outcomes.filter((o) => o.outcome_status === "FAILED").length,
    closed: outcomes.filter((o) => o.outcome_status === "CLOSED").length,
    mostRecentConfirmed: mostRecentConfirmed
      ? {
          outcomeId: mostRecentConfirmed.outcome_id,
          classLabel: mostRecentConfirmed.outcome_classification ?? "UNCLASSIFIED",
          recordedBy: mostRecentConfirmed.recorded_by,
          recordedAt: mostRecentConfirmed.recorded_at,
        }
      : null,
  };

  const _valueClassInit: Record<ValueClassification, number> = {
    HIGH_VALUE: 0, POSITIVE_VALUE: 0, NEUTRAL: 0, NEGATIVE_VALUE: 0, LOSS_INDUCING: 0,
  };
  const byClassification = values.reduce<Record<ValueClassification, number>>((acc, v) => {
    acc[v.value_classification] = (acc[v.value_classification] ?? 0) + 1;
    return acc;
  }, { ..._valueClassInit });

  const totalNetValue = values.reduce((sum, v) => sum + v.net_value, 0);
  const avgConfidence = values.length > 0
    ? values.reduce((sum, v) => sum + v.value_confidence_score, 0) / values.length
    : 0;
  const topValueRow = values.length > 0
    ? values.reduce((best, v) => v.net_value > best.net_value ? v : best, values[0])
    : null;

  const valueSummary: ExecutiveValueSummary = {
    total: values.length,
    totalNetValue,
    totalNetValueFormatted: formatUSD(totalNetValue),
    avgConfidence,
    byClassification,
    topValue: topValueRow ? {
      valueId: topValueRow.value_id,
      netValue: topValueRow.net_value,
      netValueFormatted: formatUSD(topValueRow.net_value),
      classification: topValueRow.value_classification,
      computedBy: topValueRow.computed_by,
      computedAt: topValueRow.computed_at,
      sourceOutcomeId: topValueRow.source_outcome_id,
    } : null,
  };

  return {
    kpis,
    sectors,
    topActions,
    runId: result.run_id,
    scenarioLabel: scenario.label,
    scenarioLabelAr: scenario.label_ar,
    narrativeSummary: explanation?.narrative_en ?? "",
    totalLossFormatted: formatUSD(headline.total_loss_usd),
    outcomesSummary,
    valueSummary,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// ANALYST VIEW MODEL
// Emphasis: mechanics, score factors, entity detail, causal chain, run inputs
// ─────────────────────────────────────────────────────────────────────────────

export interface AnalystSectorScores {
  banking: {
    liquidityStress: string;
    creditStress: string;
    fxStress: string;
    interbankContagion: string;
    capitalAdequacyImpact: string;
    aggregate: string;
    classification: Classification;
    institutionCount: number;
    topInstitution: string;
    topInstitutionStress: string;
  };
  insurance: {
    claimsSurge: string;
    severityIndex: string;
    lossRatio: string;
    combinedRatio: string;
    reinsuranceTrigger: boolean;
    ifrs17Adjustment: string;
    aggregate: string;
    classification: Classification;
    lineCount: number;
  };
  fintech: {
    paymentVolumeImpact: string;
    settlementDelayHours: string;
    apiAvailability: string;
    crossBorderDisruption: string;
    aggregate: string;
    classification: Classification;
    platformCount: number;
  };
}

export interface AnalystEntityRow {
  entityId: string;
  label: string;
  sector: string;
  lossFormatted: string;
  lossRaw: number;
  stressLabel: string;
  peakDay: number;
  recoveryDays: number;
  classification: Classification;
  confidence: string;
}

export interface AnalystStageRecord {
  stage: string;
  status: string;
  durationMs: number;
  detail?: string;
}

export interface AnalystRunMeta {
  runId: string;
  templateId: string;
  scenarioLabel: string;
  severity: number;
  horizonHours: number;
  stagesCompleted: string[];
  durationMs: number;
  auditHash: string;
  globalConfidence: number;
  assumptions: string[];
  stageLog: AnalystStageRecord[];
}

export interface AnalystViewModel {
  runMeta: AnalystRunMeta;
  scores: AnalystSectorScores;
  entities: AnalystEntityRow[];
  allDecisions: DecisionAction[];
  causalChain: RunResult["explanation"]["causal_chain"];
  narrativeEn: string;
  narrativeAr: string;
  liveSignals: WsSignalScoredData[];
  pendingSeeds: ScenarioSeed[];
  operatorDecisions: OperatorDecision[];
  outcomes: Outcome[];
  /** Full DecisionValue rows — calculation_trace accessible for forensic review. */
  values: DecisionValue[];
}

export function toAnalystViewModel(
  result: RunResult,
  liveSignals: WsSignalScoredData[],
  pendingSeeds: ScenarioSeed[],
  operatorDecisions: OperatorDecision[],
  outcomes: Outcome[] = [],
  values: DecisionValue[] = [],
): AnalystViewModel {
  const { banking, insurance, fintech } = result;

  const topBankInst = (banking.affected_institutions ?? []).reduce(
    (best, inst) => (inst.stress > (best?.stress ?? 0) ? inst : best),
    banking.affected_institutions?.[0] ?? null,
  );

  const scores: AnalystSectorScores = {
    banking: {
      liquidityStress: safePercent(banking.liquidity_stress),
      creditStress: safePercent(banking.credit_stress),
      fxStress: safePercent(banking.fx_stress),
      interbankContagion: safePercent(banking.interbank_contagion),
      capitalAdequacyImpact: safeFixed(banking.capital_adequacy_impact_pct, 2) + "%",
      aggregate: safePercent(banking.aggregate_stress),
      classification: banking.classification,
      institutionCount: banking.affected_institutions?.length ?? 0,
      topInstitution: topBankInst?.name ?? "—",
      topInstitutionStress: safePercent(topBankInst?.stress ?? 0),
    },
    insurance: {
      claimsSurge: `${safeFixed(insurance.claims_surge_multiplier, 1)}×`,
      severityIndex: safeFixed(insurance.severity_index, 3),
      lossRatio: safeFixed(insurance.loss_ratio, 3),
      combinedRatio: safeFixed(insurance.combined_ratio, 3),
      reinsuranceTrigger: insurance.reinsurance_trigger,
      ifrs17Adjustment: safeFixed(insurance.ifrs17_risk_adjustment_pct, 2) + "%",
      aggregate: safePercent(insurance.aggregate_stress),
      classification: insurance.classification,
      lineCount: insurance.affected_lines?.length ?? 0,
    },
    fintech: {
      paymentVolumeImpact: `${Math.round(fintech.payment_volume_impact_pct)}%`,
      settlementDelayHours: formatHours(fintech.settlement_delay_hours),
      apiAvailability: safeFixed(fintech.api_availability_pct, 1) + "%",
      crossBorderDisruption: safeFixed(fintech.cross_border_disruption, 3),
      aggregate: safePercent(fintech.aggregate_stress),
      classification: fintech.classification,
      platformCount: fintech.affected_platforms?.length ?? 0,
    },
  };

  const entities: AnalystEntityRow[] = (result.financial ?? [])
    .sort((a, b) => b.loss_usd - a.loss_usd)
    .map((fi) => ({
      entityId: fi.entity_id,
      label: fi.entity_label ?? fi.entity_id,
      sector: fi.sector,
      lossFormatted: formatUSD(fi.loss_usd),
      lossRaw: fi.loss_usd,
      stressLabel: safePercent(fi.stress_level),
      peakDay: fi.peak_day,
      recoveryDays: fi.recovery_days,
      classification: fi.classification,
      confidence: `${Math.round(fi.confidence * 100)}%`,
    }));

  const stageLog: AnalystStageRecord[] = Object.entries(result.stage_log ?? {}).map(
    ([stage, rec]) => ({ stage, status: rec.status, durationMs: rec.duration_ms, detail: rec.detail }),
  );

  return {
    runMeta: {
      runId: result.run_id,
      templateId: result.scenario.template_id,
      scenarioLabel: result.scenario.label,
      severity: result.scenario.severity,
      horizonHours: result.scenario.horizon_hours,
      stagesCompleted: result.stages_completed ?? [],
      durationMs: result.duration_ms,
      auditHash: result.audit_hash,
      globalConfidence: result.global_confidence,
      assumptions: result.assumptions ?? [],
      stageLog,
    },
    scores,
    entities,
    allDecisions: result.decisions.all_actions ?? result.decisions.actions ?? [],
    causalChain: result.explanation?.causal_chain ?? [],
    narrativeEn: result.explanation?.narrative_en ?? "",
    narrativeAr: result.explanation?.narrative_ar ?? "",
    liveSignals,
    pendingSeeds,
    operatorDecisions,
    outcomes,
    values,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// REGULATOR VIEW MODEL
// Emphasis: decision lineage, audit trail, actor/timestamp, signal→run chain
// ─────────────────────────────────────────────────────────────────────────────

export interface RegulatorDecisionRow {
  decisionId: string;
  decisionType: string;
  status: string;
  outcomeStatus: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  closedAt: string | null;
  rationale: string | null;
  sourceSignalId: string | null;
  sourceSeedId: string | null;
  sourceRunId: string | null;
  linkedEntities: string; // "signal → seed → run" chain label
  outcomeDetail: string;
}

export interface RegulatorSignalTrace {
  signalId: string;
  sector: string;
  eventType: string;
  score: number;
  source: string;
  scoredAt: string;
}

export interface RegulatorPipelineRecord {
  stage: string;
  status: string;
  durationMs: number;
  detail?: string;
}

export interface RegulatorRegulatoryEvent {
  timestep: number;
  breachLevel: string;
  sector: string;
  mandatoryActions: string[];
}

export interface RegulatorOutcomeRow {
  outcomeId: string;
  status: OutcomeLifecycleStatus;
  classification: OutcomeClassification | null;
  recordedBy: string;
  recordedAt: string;
  observedAt: string | null;
  closedAt: string | null;
  errorFlag: boolean;
  timeToResolutionSeconds: number | null;
  sourceDecisionId: string | null;
  sourceRunId: string | null;
  notes: string | null;
  evidenceKeysCount: number;
}

export interface RegulatorValueRow {
  /** PK of the value row */
  valueId: string;
  /** Who triggered the computation and when */
  computedBy: string;
  computedAt: string;
  /** Linkage to the outcome that sourced this value */
  sourceOutcomeId: string;
  sourceDecisionId: string | null;
  sourceRunId: string | null;
  /** Core computed fields */
  netValue: number;
  netValueFormatted: string;
  classification: ValueClassification;
  confidenceScore: number;
  /** Whether this is a recomputed row (lineage in trace) */
  recomputedFrom: string | null;
  notes: string | null;
}

export interface RegulatorViewModel {
  decisions: RegulatorDecisionRow[];
  signalTrace: RegulatorSignalTrace[];
  pipelineRecord: RegulatorPipelineRecord[];
  regulatoryEvents: RegulatorRegulatoryEvent[];
  pendingSeeds: ScenarioSeed[];
  outcomeAuditRows: RegulatorOutcomeRow[];
  /** ROI audit rows — actor, linkage, classification, confidence, recomputation lineage */
  valueAuditRows: RegulatorValueRow[];
  auditHash: string;
  runId: string;
  scenarioLabel: string;
  stagesCompleted: string[];
  globalConfidence: string;
  durationMs: number;
}

export function toRegulatorViewModel(
  result: RunResult,
  operatorDecisions: OperatorDecision[],
  liveSignals: WsSignalScoredData[],
  pendingSeeds: ScenarioSeed[],
  outcomes: Outcome[] = [],
  values: DecisionValue[] = [],
): RegulatorViewModel {
  const decisions: RegulatorDecisionRow[] = operatorDecisions.map((d) => {
    const parts: string[] = [];
    if (d.source_signal_id) parts.push(`SIG:${d.source_signal_id.slice(0, 8)}`);
    if (d.source_seed_id) parts.push(`SEED:${d.source_seed_id.slice(0, 8)}`);
    if (d.source_run_id) parts.push(`RUN:${d.source_run_id.slice(0, 8)}`);

    const outcomePayload = d.outcome_payload ?? {};
    const outcomeDetail =
      Object.keys(outcomePayload).length > 0
        ? JSON.stringify(outcomePayload).slice(0, 120)
        : "—";

    return {
      decisionId: d.decision_id,
      decisionType: d.decision_type,
      status: d.decision_status,
      outcomeStatus: d.outcome_status,
      createdBy: d.created_by,
      createdAt: d.created_at,
      updatedAt: d.updated_at,
      closedAt: d.closed_at ?? null,
      rationale: d.rationale ?? null,
      sourceSignalId: d.source_signal_id ?? null,
      sourceSeedId: d.source_seed_id ?? null,
      sourceRunId: d.source_run_id ?? null,
      linkedEntities: parts.join(" → ") || "—",
      outcomeDetail,
    };
  });

  const signalTrace: RegulatorSignalTrace[] = liveSignals.slice(0, 25).map((s) => ({
    signalId: s.signal_id,
    sector: s.sector,
    eventType: s.event_type,
    score: s.signal_score,
    source: s.source,
    scoredAt: s.scored_at,
  }));

  const pipelineRecord: RegulatorPipelineRecord[] = Object.entries(result.stage_log ?? {}).map(
    ([stage, rec]) => ({
      stage,
      status: rec.status,
      durationMs: rec.duration_ms,
      detail: rec.detail,
    }),
  );

  const regulatoryEvents: RegulatorRegulatoryEvent[] = (result.regulatory_events ?? []).map((e) => ({
    timestep: e.timestep,
    breachLevel: e.breach_level,
    sector: e.sector,
    mandatoryActions: e.mandatory_actions,
  }));

  const outcomeAuditRows: RegulatorOutcomeRow[] = outcomes.map((o) => ({
    outcomeId: o.outcome_id,
    status: o.outcome_status,
    classification: o.outcome_classification,
    recordedBy: o.recorded_by,
    recordedAt: o.recorded_at,
    observedAt: o.observed_at,
    closedAt: o.closed_at,
    errorFlag: o.error_flag,
    timeToResolutionSeconds: o.time_to_resolution_seconds,
    sourceDecisionId: o.source_decision_id,
    sourceRunId: o.source_run_id,
    notes: o.notes,
    evidenceKeysCount: Object.keys(o.evidence_payload ?? {}).length,
  }));

  const valueAuditRows: RegulatorValueRow[] = values.map((v) => ({
    valueId: v.value_id,
    computedBy: v.computed_by,
    computedAt: v.computed_at,
    sourceOutcomeId: v.source_outcome_id,
    sourceDecisionId: v.source_decision_id,
    sourceRunId: v.source_run_id,
    netValue: v.net_value,
    netValueFormatted: formatUSD(v.net_value),
    classification: v.value_classification,
    confidenceScore: v.value_confidence_score,
    recomputedFrom: (v.calculation_trace?.recomputed_from_value_id as string | undefined) ?? null,
    notes: v.notes,
  }));

  return {
    decisions,
    signalTrace,
    pipelineRecord,
    regulatoryEvents,
    pendingSeeds,
    outcomeAuditRows,
    valueAuditRows,
    auditHash: result.audit_hash,
    runId: result.run_id,
    scenarioLabel: result.scenario.label,
    stagesCompleted: result.stages_completed ?? [],
    globalConfidence: `${Math.round(result.global_confidence * 100)}%`,
    durationMs: result.duration_ms,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// EXECUTIVE CONTROL TOWER VIEW MODEL
// Pure composition layer: decisions × outcomes × values → executive narrative
// No DB entity. No new persistence. No recomputation.
// ─────────────────────────────────────────────────────────────────────────────

export interface ControlTowerValueOverview {
  totalValues: number;
  totalNetValue: number;
  totalNetValueFormatted: string;
  totalAvoidedLoss: number;
  totalAvoidedLossFormatted: string;
  totalCost: number;
  totalCostFormatted: string;
  /**
   * Σ(net_value × confidence_score) / n
   * DERIVED IN FRONTEND — not persisted. Formula: Σ(net_value × confidence) / n.
   * Do not present as a backend-computed or audited figure.
   */
  confidenceWeightedValue: number;
  confidenceWeightedValueFormatted: string;
  /** Count by classification — covers ALL values (decision-linked + run-linked). */
  byClassification: Record<ValueClassification, number>;
  /** How many of totalValues appear in a narrative entry (decision or run-level). */
  valueCoverage: number;
  valueCoveragePct: number;
}

export interface ControlTowerDecisionPerf {
  decisionId: string;
  decisionType: string;
  decisionStatus: string;
  createdBy: string;
  createdAt: string;
  confidenceScore: number;
  /** Latest outcome linked to this decision (by recorded_at). */
  linkedOutcomeId: string | null;
  linkedOutcomeStatus: string | null;
  linkedOutcomeClassification: string | null;
  /** Count of all outcomes linked to this decision. */
  outcomeCount: number;
  /** Latest value computed from any outcome linked to this decision (by computed_at). */
  linkedValueId: string | null;
  netValue: number | null;
  netValueFormatted: string | null;
  valueClassification: ValueClassification | null;
  /** Count of all values linked to this decision. */
  valueCount: number;
}

export interface ControlTowerOutcomeStats {
  total: number;
  confirmed: number;
  disputed: number;
  pending: number;
  failed: number;
  /**
   * confirmed / validOutcomes (excludes PENDING_OBSERVATION from denominator).
   * validOutcomes = total - pending.
   * 0 when validOutcomes === 0.
   */
  confirmedRate: number;
  /** validOutcomes = total − pending (actionable denominator). */
  validOutcomes: number;
  /** Mean time-to-resolution across outcomes that have time_to_resolution_seconds. */
  avgResolutionSeconds: number | null;
  totalExpectedValue: number;
  totalRealizedValue: number;
  /** (totalRealized / totalExpected) * 100 — null when expected === 0 */
  realizedVsExpectedPct: number | null;
}

export interface ControlTowerValueDriver {
  groupKey: string;
  label: string;
  valueCount: number;
  totalNetValue: number;
  totalNetValueFormatted: string;
  avgConfidence: number;
}

export type ControlTowerRiskType = "LOSS_INDUCING" | "NEGATIVE_VALUE" | "LOW_CONFIDENCE";

export interface ControlTowerRiskItem {
  decisionId: string | null;
  valueId: string | null;
  label: string;
  netValue: number;
  netValueFormatted: string;
  classification: ValueClassification;
  riskType: ControlTowerRiskType;
}

/**
 * Per-decision narrative: signal → decision → outcome → value → confidence.
 * entryType="decision" rows are sourced from an OperatorDecision.
 * entryType="run"      rows are run-level values with no linked OperatorDecision.
 * Every field is traceable to a persisted row.
 */
export interface ControlTowerNarrativeEntry {
  /** Discriminates decision-linked vs run-level-only rows. */
  entryType: "decision" | "run";
  /** Populated for entryType="decision". */
  decisionId: string | null;
  decisionType: string | null;
  createdBy: string;
  createdAt: string;
  /** Latest outcome linked to this decision (by recorded_at). */
  outcomeId: string | null;
  outcomeStatus: string | null;
  outcomeClassification: string | null;
  /** Latest value (by computed_at) linked to this decision or run. */
  valueId: string | null;
  netValue: number | null;
  netValueFormatted: string | null;
  valueClassification: ValueClassification | null;
  confidenceScore: number | null;
  /**
   * true when outcome is TRUE_POSITIVE and value is HIGH_VALUE or POSITIVE_VALUE.
   * Only meaningful for entryType="decision".
   */
  shouldRepeat: boolean;
  /** Human-readable one-line story for executive consumption. */
  story: string;
  /** Source run_id — populated for both types when value has source_run_id. */
  sourceRunId: string | null;
}

export interface ControlTowerViewModel {
  valueOverview: ControlTowerValueOverview;
  /** All operator decisions enriched with linked outcome + value (newest first). */
  decisionPerformance: ControlTowerDecisionPerf[];
  outcomeStats: ControlTowerOutcomeStats;
  /** Net value grouped by decision_type, descending by totalNetValue. */
  valueDrivers: ControlTowerValueDriver[];
  /** Loss-inducing, negative, and low-confidence risk items. */
  riskPanel: ControlTowerRiskItem[];
  /** Per-decision narrative entries (same order as decisionPerformance). */
  narratives: ControlTowerNarrativeEntry[];
  hasData: boolean;
}

export function toControlTowerViewModel(
  operatorDecisions: OperatorDecision[] = [],
  outcomes: Outcome[] = [],
  values: DecisionValue[] = [],
): ControlTowerViewModel {
  // Runtime guard: coerce all three inputs to arrays before any reduce/map/filter.
  // Track which inputs were non-arrays so we can emit a render_fallback_invoked
  // event — this surfaces contract violations without silently swallowing them.
  const coerced: string[]                            = [];
  const originalTypes: Record<string, string>        = {};
  if (!Array.isArray(operatorDecisions)) { coerced.push("operatorDecisions"); originalTypes.operatorDecisions = typeof operatorDecisions; }
  if (!Array.isArray(outcomes))          { coerced.push("outcomes");          originalTypes.outcomes          = typeof outcomes; }
  if (!Array.isArray(values))            { coerced.push("values");            originalTypes.values            = typeof values; }

  operatorDecisions = safeArray<OperatorDecision>(operatorDecisions);
  outcomes          = safeArray<Outcome>(outcomes);
  values            = safeArray<DecisionValue>(values);

  if (coerced.length > 0) {
    emitAudit({
      event_type: "render_fallback_invoked",
      entity_id:  "toControlTowerViewModel",
      actor:      "adapter",
      details: {
        coerced,
        original_types: originalTypes,
        hint: "One or more inputs to toControlTowerViewModel were not arrays; safeArray() substituted []",
      },
      lineage_ref: null,
    });
  }

  const hasData = operatorDecisions.length > 0 || outcomes.length > 0 || values.length > 0;

  // ── A. Value Overview (all values — no exclusions) ─────────────────────────
  const _classInit: Record<ValueClassification, number> = {
    HIGH_VALUE: 0, POSITIVE_VALUE: 0, NEUTRAL: 0, NEGATIVE_VALUE: 0, LOSS_INDUCING: 0,
  };
  const byClassification = values.reduce<Record<ValueClassification, number>>((acc, v) => {
    acc[v.value_classification] = (acc[v.value_classification] ?? 0) + 1;
    return acc;
  }, { ..._classInit });

  // safeNum() guards NaN/Infinity from malformed API numeric fields
  const totalNetValue    = values.reduce((s, v) => s + safeNum(v.net_value), 0);
  const totalAvoidedLoss = values.reduce((s, v) => s + safeNum(v.avoided_loss), 0);
  const totalCost        = values.reduce((s, v) => s + safeNum(v.total_cost), 0);
  // Derived in frontend only. Not persisted. Formula: Σ(net_value × confidence) / n.
  const confidenceWeighted = values.length > 0
    ? values.reduce((s, v) => s + safeNum(v.net_value) * safeNum(v.value_confidence_score), 0) / values.length
    : 0;

  // ── B. Decision Performance ─────────────────────────────────────────────────
  // FIX C: multi-value maps — keep ALL outcomes/values per decision_id,
  // then resolve to latest (by recorded_at / computed_at).

  const outcomesByDecision = new Map<string, Outcome[]>();
  for (const o of outcomes) {
    if (!o.source_decision_id) continue;
    const arr = outcomesByDecision.get(o.source_decision_id) ?? [];
    arr.push(o);
    outcomesByDecision.set(o.source_decision_id, arr);
  }
  const valuesByDecision = new Map<string, DecisionValue[]>();
  for (const v of values) {
    if (!v.source_decision_id) continue;
    const arr = valuesByDecision.get(v.source_decision_id) ?? [];
    arr.push(v);
    valuesByDecision.set(v.source_decision_id, arr);
  }

  // Latest outcome for a decision: sort by recorded_at desc, take [0]
  function latestOutcome(decisionId: string): Outcome | null {
    const arr = outcomesByDecision.get(decisionId);
    if (!arr || arr.length === 0) return null;
    return arr.slice().sort(
      (a, b) => safeTime(b.recorded_at) - safeTime(a.recorded_at)
    )[0];
  }
  // Latest value for a decision: sort by computed_at desc, take [0]
  function latestValue(decisionId: string): DecisionValue | null {
    const arr = valuesByDecision.get(decisionId);
    if (!arr || arr.length === 0) return null;
    return arr.slice().sort(
      (a, b) => safeTime(b.computed_at) - safeTime(a.computed_at)
    )[0];
  }

  const decisionPerformance: ControlTowerDecisionPerf[] = operatorDecisions.map((d) => {
    const outcome    = latestOutcome(d.decision_id);
    const value      = latestValue(d.decision_id);
    const oCnt       = outcomesByDecision.get(d.decision_id)?.length ?? 0;
    const vCnt       = valuesByDecision.get(d.decision_id)?.length ?? 0;
    return {
      decisionId:                  d.decision_id,
      decisionType:                d.decision_type,
      decisionStatus:              d.decision_status,
      createdBy:                   d.created_by,
      createdAt:                   d.created_at,
      confidenceScore:             d.confidence_score ?? 0,
      linkedOutcomeId:             outcome?.outcome_id ?? null,
      linkedOutcomeStatus:         outcome?.outcome_status ?? null,
      linkedOutcomeClassification: outcome?.outcome_classification ?? null,
      outcomeCount:                oCnt,
      linkedValueId:               value?.value_id ?? null,
      netValue:                    value?.net_value ?? null,
      netValueFormatted:           value != null ? formatUSD(value.net_value) : null,
      valueClassification:         value?.value_classification ?? null,
      valueCount:                  vCnt,
    };
  });

  // ── C. Outcome Stats — FIX E: correct denominator ─────────────────────────
  const confirmedOutcomes = outcomes.filter((o) => o.outcome_status === "CONFIRMED");
  const pendingCount      = outcomes.filter((o) => o.outcome_status === "PENDING_OBSERVATION").length;
  // validOutcomes excludes PENDING_OBSERVATION from the denominator.
  const validOutcomes     = outcomes.length - pendingCount;

  const resolvedTimes = outcomes
    .filter((o) => o.time_to_resolution_seconds != null)
    .map((o) => o.time_to_resolution_seconds as number);
  const avgResolution = resolvedTimes.length > 0
    ? resolvedTimes.reduce((s, t) => s + t, 0) / resolvedTimes.length
    : null;
  const totalExpected = outcomes.reduce((s, o) => s + (o.expected_value ?? 0), 0);
  const totalRealized = outcomes.reduce((s, o) => s + (o.realized_value ?? 0), 0);

  const outcomeStats: ControlTowerOutcomeStats = {
    total:                 outcomes.length,
    confirmed:             confirmedOutcomes.length,
    disputed:              outcomes.filter((o) => o.outcome_status === "DISPUTED").length,
    pending:               pendingCount,
    failed:                outcomes.filter((o) => o.outcome_status === "FAILED").length,
    confirmedRate:         validOutcomes > 0 ? confirmedOutcomes.length / validOutcomes : 0,
    validOutcomes,
    avgResolutionSeconds:  avgResolution,
    totalExpectedValue:    totalExpected,
    totalRealizedValue:    totalRealized,
    realizedVsExpectedPct: totalExpected > 0 ? (totalRealized / totalExpected) * 100 : null,
  };

  // ── D. Value Drivers ────────────────────────────────────────────────────────
  const decisionTypeIndex = new Map<string, string>();
  for (const d of operatorDecisions) decisionTypeIndex.set(d.decision_id, d.decision_type);

  const driverGroups = new Map<string, DecisionValue[]>();
  for (const v of values) {
    // Run-linked values with no decision are grouped as "RUN LEVEL"
    const key = (v.source_decision_id && decisionTypeIndex.get(v.source_decision_id))
      ?? (v.source_run_id ? "RUN LEVEL" : "UNLINKED");
    const grp = driverGroups.get(key) ?? [];
    grp.push(v);
    driverGroups.set(key, grp);
  }

  const valueDrivers: ControlTowerValueDriver[] = Array.from(driverGroups.entries())
    .map(([key, grp]) => {
      const gnv = grp.reduce((s, v) => s + safeNum(v.net_value), 0);
      return {
        groupKey:               key,
        label:                  key.replace(/_/g, " "),
        valueCount:             grp.length,
        totalNetValue:          gnv,
        totalNetValueFormatted: formatUSD(gnv),
        avgConfidence:          grp.length > 0
          ? grp.reduce((s, v) => s + safeNum(v.value_confidence_score), 0) / grp.length
          : 0,
      };
    })
    .sort((a, b) => b.totalNetValue - a.totalNetValue);

  // ── E. Risk Panel ───────────────────────────────────────────────────────────
  const riskPanel: ControlTowerRiskItem[] = [];
  const seenRiskIds = new Set<string>();

  for (const v of values) {
    if (v.value_classification === "LOSS_INDUCING") {
      seenRiskIds.add(v.value_id);
      const src = v.source_decision_id?.slice(0, 12) ?? v.source_run_id?.slice(0, 12) ?? "unlinked";
      riskPanel.push({
        decisionId:        v.source_decision_id,
        valueId:           v.value_id,
        label:             `Loss-inducing · ${src}`,
        netValue:          v.net_value,
        netValueFormatted: formatUSD(v.net_value),
        classification:    v.value_classification,
        riskType:          "LOSS_INDUCING",
      });
    } else if (v.value_classification === "NEGATIVE_VALUE") {
      seenRiskIds.add(v.value_id);
      const src = v.source_decision_id?.slice(0, 12) ?? v.source_run_id?.slice(0, 12) ?? "unlinked";
      riskPanel.push({
        decisionId:        v.source_decision_id,
        valueId:           v.value_id,
        label:             `Negative value · ${src}`,
        netValue:          v.net_value,
        netValueFormatted: formatUSD(v.net_value),
        classification:    v.value_classification,
        riskType:          "NEGATIVE_VALUE",
      });
    }
  }
  for (const v of values) {
    if (!seenRiskIds.has(v.value_id) && v.value_confidence_score < 0.5 && Math.abs(v.net_value) > 100_000) {
      riskPanel.push({
        decisionId:        v.source_decision_id,
        valueId:           v.value_id,
        label:             `Low confidence (${Math.round(v.value_confidence_score * 100)}%) · ${formatUSD(v.net_value)}`,
        netValue:          v.net_value,
        netValueFormatted: formatUSD(v.net_value),
        classification:    v.value_classification,
        riskType:          "LOW_CONFIDENCE",
      });
    }
  }

  // ── F. Decision Narratives — FIX A + FIX C ─────────────────────────────────
  // Part 1: decision-linked narratives (use latest outcome + latest value)
  const decisionLinkedValueIds = new Set<string>();

  const decisionNarratives: ControlTowerNarrativeEntry[] = operatorDecisions.map((d) => {
    const outcome = latestOutcome(d.decision_id);
    const value   = latestValue(d.decision_id);
    if (value) decisionLinkedValueIds.add(value.value_id);

    const shouldRepeat =
      outcome?.outcome_classification === "TRUE_POSITIVE" &&
      (value?.value_classification === "HIGH_VALUE" || value?.value_classification === "POSITIVE_VALUE");

    const parts: string[] = [
      `${d.decision_type.replace(/_/g, " ")} by ${d.created_by}`,
    ];
    if (outcome) {
      const cls = outcome.outcome_classification?.replace(/_/g, " ") ?? null;
      parts.push(`→ ${outcome.outcome_status}${cls ? ` (${cls})` : ""}`);
    } else {
      parts.push("→ no outcome recorded");
    }
    if (value) {
      parts.push(`→ ${formatUSD(value.net_value)} · ${Math.round(value.value_confidence_score * 100)}% confidence`);
    } else {
      parts.push("→ no value computed");
    }
    if (shouldRepeat) parts.push("· Recommended to repeat");

    return {
      entryType:             "decision",
      decisionId:            d.decision_id,
      decisionType:          d.decision_type,
      createdBy:             d.created_by,
      createdAt:             d.created_at,
      outcomeId:             outcome?.outcome_id ?? null,
      outcomeStatus:         outcome?.outcome_status ?? null,
      outcomeClassification: outcome?.outcome_classification ?? null,
      valueId:               value?.value_id ?? null,
      netValue:              value?.net_value ?? null,
      netValueFormatted:     value != null ? formatUSD(value.net_value) : null,
      valueClassification:   value?.value_classification ?? null,
      confidenceScore:       value?.value_confidence_score ?? null,
      shouldRepeat,
      story:                 parts.join(" "),
      sourceRunId:           value?.source_run_id ?? null,
    };
  });

  // Part 2: run-level-only narratives (FIX A — values with no linked decision)
  const runLevelNarratives: ControlTowerNarrativeEntry[] = values
    .filter((v) => !v.source_decision_id && v.source_run_id && !decisionLinkedValueIds.has(v.value_id))
    .map((v) => {
      const parts = [
        `RUN-LEVEL VALUE (no direct decision) · run ${v.source_run_id!.slice(0, 12)}`,
        `→ ${formatUSD(v.net_value)} · ${Math.round(v.value_confidence_score * 100)}% confidence`,
      ];
      return {
        entryType:             "run" as const,
        decisionId:            null,
        decisionType:          null,
        createdBy:             v.computed_by,
        createdAt:             v.computed_at,
        outcomeId:             v.source_outcome_id ?? null,
        outcomeStatus:         null,
        outcomeClassification: null,
        valueId:               v.value_id,
        netValue:              v.net_value,
        netValueFormatted:     formatUSD(v.net_value),
        valueClassification:   v.value_classification,
        confidenceScore:       v.value_confidence_score,
        shouldRepeat:          false,
        story:                 parts.join(" "),
        sourceRunId:           v.source_run_id,
      };
    });

  const narratives = [...decisionNarratives, ...runLevelNarratives];

  // ── G. Value Coverage (optional metric) ────────────────────────────────────
  const coveredIds = new Set<string>();
  for (const n of narratives) if (n.valueId) coveredIds.add(n.valueId);
  const valueCoverage    = coveredIds.size;
  const valueCoveragePct = values.length > 0 ? Math.round((valueCoverage / values.length) * 100) : 100;

  const valueOverview: ControlTowerValueOverview = {
    totalValues: values.length,
    totalNetValue,
    totalNetValueFormatted:            formatUSD(totalNetValue),
    totalAvoidedLoss,
    totalAvoidedLossFormatted:         formatUSD(totalAvoidedLoss),
    totalCost,
    totalCostFormatted:                formatUSD(totalCost),
    confidenceWeightedValue:           confidenceWeighted,
    confidenceWeightedValueFormatted:  formatUSD(confidenceWeighted),
    byClassification,
    valueCoverage,
    valueCoveragePct,
  };

  return {
    valueOverview,
    decisionPerformance,
    outcomeStats,
    valueDrivers,
    riskPanel,
    narratives,
    hasData,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

export type Persona = "executive" | "analyst" | "regulator";

const PERSONA_LABELS: Record<Persona, { en: string; ar: string }> = {
  executive: { en: "Executive", ar: "تنفيذي" },
  analyst:   { en: "Analyst",   ar: "محلل" },
  regulator: { en: "Regulator", ar: "منظِّم" },
};

export function getPersonaLabel(persona: Persona, lang: Language): string {
  return PERSONA_LABELS[persona][lang];
}

const CLASS_COLORS: Record<Classification, string> = {
  CRITICAL: "bg-io-critical text-white",
  ELEVATED: "bg-io-elevated text-white",
  MODERATE: "bg-io-moderate text-white",
  LOW:      "bg-io-low text-white",
  NOMINAL:  "bg-io-nominal text-white",
};

export function classColor(c: Classification): string {
  return CLASS_COLORS[c] ?? "bg-gray-200 text-gray-700";
}

const STATUS_BADGE_COLORS: Record<string, string> = {
  CREATED:   "bg-blue-100 text-blue-800",
  IN_REVIEW: "bg-yellow-100 text-yellow-800",
  EXECUTED:  "bg-green-100 text-green-800",
  FAILED:    "bg-red-100 text-red-800",
  CLOSED:    "bg-gray-100 text-gray-600",
};

export function statusBadgeColor(status: string): string {
  return STATUS_BADGE_COLORS[status] ?? "bg-gray-100 text-gray-600";
}
