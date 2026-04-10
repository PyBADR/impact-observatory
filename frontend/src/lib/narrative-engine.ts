/**
 * Impact Observatory | مرصد الأثر — Narrative Engine
 *
 * Deterministic, traceable, persona-aware narrative generation.
 *
 * For every scenario/decision flowing through the pipeline, this engine generates:
 *   1. WHAT happened          — signal description
 *   2. WHY it happened        — TREK reasoning chain
 *   3. HOW it propagated      — Impact simulation summary
 *   4. WHAT decision was taken — operator action
 *   5. WHAT outcome occurred  — real-world observation
 *   6. WHAT value was created  — ROI computation
 *
 * Properties:
 *   - Deterministic: same input → same narrative (no randomness)
 *   - Traceable: every sentence maps to a data field + stage
 *   - Persona-aware: Executive sees value, Analyst sees mechanics, Regulator sees audit trail
 *
 * NO SIDE EFFECTS. Pure functions only.
 */

import type {
  RunResult,
  OperatorDecision,
  Outcome,
  DecisionValue,
  Classification,
  Language,
} from "@/types/observatory";
import type {
  FlowInstance,
  FlowStage,
  FlowStageEntry,
} from "@/store/flow-store";
import type { Persona } from "@/lib/persona-view-model";
import { formatUSD } from "@/lib/format";

// ─── Narrative Block Types ──────────────────────────────────────────────────

export type NarrativeBlockType =
  | "signal"
  | "reasoning"
  | "simulation"
  | "decision"
  | "outcome"
  | "roi"
  | "synthesis";

export interface NarrativeBlock {
  /** Which pipeline stage this block corresponds to */
  type: NarrativeBlockType;
  /** Display order */
  order: number;
  /** English narrative text */
  textEn: string;
  /** Arabic narrative text */
  textAr: string;
  /** Severity/importance: drives visual weight */
  severity: "info" | "warning" | "critical" | "positive";
  /** Data provenance: field paths that back this narrative */
  dataTrail: string[];
  /** Persona visibility: which personas see this block */
  visibleTo: Persona[];
  /** Key metrics extracted for quick rendering */
  metrics: NarrativeMetric[];
}

export interface NarrativeMetric {
  label: string;
  labelAr: string;
  value: string;
  sentiment: "positive" | "negative" | "neutral";
}

export interface FlowNarrative {
  /** Unique flow this narrative describes */
  flowId: string;
  /** Scenario context */
  scenarioLabel: string;
  scenarioLabelAr: string;
  /** All narrative blocks in pipeline order */
  blocks: NarrativeBlock[];
  /** One-sentence executive summary (English) */
  summaryEn: string;
  /** One-sentence executive summary (Arabic) */
  summaryAr: string;
  /** Generated timestamp */
  generatedAt: string;
  /** Flow completion percentage when narrative was generated */
  flowProgress: number;
}

// ─── Narrative Generator ────────────────────────────────────────────────────

/**
 * Generate a complete flow narrative from a FlowInstance.
 * Pure function — no side effects, no store access.
 */
export function generateFlowNarrative(flow: FlowInstance): FlowNarrative {
  const blocks: NarrativeBlock[] = [];
  const ctx = flow.context;
  const result = ctx.runResult;

  // ── 1. SIGNAL BLOCK ─────────────────────────────────────────────────
  blocks.push(buildSignalBlock(flow));

  // ── 2. REASONING BLOCK ──────────────────────────────────────────────
  if (result) {
    blocks.push(buildReasoningBlock(result, flow));
  }

  // ── 3. SIMULATION BLOCK ─────────────────────────────────────────────
  if (result) {
    blocks.push(buildSimulationBlock(result));
  }

  // ── 4. DECISION BLOCK ───────────────────────────────────────────────
  if ((result?.decisions?.actions?.length ?? 0) > 0 || ctx.decisions.length > 0) {
    blocks.push(buildDecisionBlock(result, ctx.decisions));
  }

  // ── 5. OUTCOME BLOCK ───────────────────────────────────────────────
  if (ctx.outcomes.length > 0) {
    blocks.push(buildOutcomeBlock(ctx.outcomes));
  }

  // ── 6. ROI BLOCK ────────────────────────────────────────────────────
  if (ctx.values.length > 0) {
    blocks.push(buildROIBlock(ctx.values));
  }

  // ── SYNTHESIS ───────────────────────────────────────────────────────
  const synthesis = buildSynthesisBlock(flow, blocks);
  blocks.push(synthesis);

  // ── Executive summary ───────────────────────────────────────────────
  const { summaryEn, summaryAr } = buildExecutiveSummary(flow, result);

  const completedStages = flow.stages.filter((s) => s.status === "completed").length;
  const totalStages = 7; // signal through control_tower

  return {
    flowId: flow.flowId,
    scenarioLabel: ctx.scenarioLabel,
    scenarioLabelAr: ctx.scenarioLabelAr,
    blocks,
    summaryEn,
    summaryAr,
    generatedAt: new Date().toISOString(),
    flowProgress: Math.round((completedStages / totalStages) * 100),
  };
}

/**
 * Filter narrative blocks by persona.
 * Executive sees value summaries. Analyst sees mechanics. Regulator sees audit trails.
 */
export function filterBlocksByPersona(
  narrative: FlowNarrative,
  persona: Persona
): NarrativeBlock[] {
  return narrative.blocks.filter((b) => b.visibleTo.includes(persona));
}

/**
 * Get the narrative text for a specific block in the given language.
 */
export function getBlockText(block: NarrativeBlock, lang: Language): string {
  return lang === "ar" ? block.textAr : block.textEn;
}

// ─── Block Builders ─────────────────────────────────────────────────────────

function buildSignalBlock(flow: FlowInstance): NarrativeBlock {
  const ctx = flow.context;
  const severityPct = Math.round(ctx.severity * 100);

  const textEn = ctx.originSignal
    ? `A live signal from ${ctx.originSignal.source ?? "Jet Nexus"} detected a ${ctx.originSignal.event_type ?? "disruption"} event in the ${ctx.originSignal.sector ?? "cross-sector"} domain, scoring ${Math.round((ctx.originSignal.signal_score ?? 0) * 100)}% risk confidence. This triggered the "${ctx.scenarioLabel}" scenario at ${severityPct}% severity.`
    : `The "${ctx.scenarioLabel}" scenario was initiated at ${severityPct}% severity, simulating a geopolitical or economic disruption across GCC financial markets.`;

  const textAr = ctx.originSignal
    ? `رصدت إشارة حية من ${ctx.originSignal.source ?? "جت نيكسس"} حدث ${ctx.originSignal.event_type ?? "اضطراب"} في مجال ${ctx.originSignal.sector ?? "متعدد القطاعات"}، بثقة مخاطر ${Math.round((ctx.originSignal.signal_score ?? 0) * 100)}%. أدى ذلك لتفعيل سيناريو "${ctx.scenarioLabelAr}" بشدة ${severityPct}%.`
    : `تم تفعيل سيناريو "${ctx.scenarioLabelAr}" بشدة ${severityPct}%، لمحاكاة اضطراب جيوسياسي أو اقتصادي عبر الأسواق المالية الخليجية.`;

  return {
    type: "signal",
    order: 1,
    textEn,
    textAr,
    severity: severityPct >= 80 ? "critical" : severityPct >= 50 ? "warning" : "info",
    dataTrail: ["context.scenarioId", "context.severity", "context.originSignal"],
    visibleTo: ["executive", "analyst", "regulator"],
    metrics: [
      { label: "Severity", labelAr: "الشدة", value: `${severityPct}%`, sentiment: severityPct >= 70 ? "negative" : "neutral" },
      { label: "Scenario", labelAr: "السيناريو", value: ctx.scenarioLabel, sentiment: "neutral" },
    ],
  };
}

function buildReasoningBlock(result: RunResult, flow: FlowInstance): NarrativeBlock {
  const chain = result.explanation?.causal_chain ?? [];
  const chainLength = chain.length;
  const topEntities = chain.slice(0, 3).map((c) => c.entity_label).join(", ");
  const totalImpact = chain.reduce((sum, c) => sum + (c.impact_usd ?? 0), 0);

  const stageEntry = flow.stages.find((s) => s.stage === "reasoning");
  const durationLabel = stageEntry?.durationMs ? `${stageEntry.durationMs}ms` : "—";

  const textEn = chainLength > 0
    ? `TREK reasoning traced a ${chainLength}-step causal chain through the GCC financial network. The propagation path initiated at ${topEntities || "primary entities"}, with a cumulative impact of ${formatUSD(totalImpact)}. Analysis completed in ${durationLabel}.`
    : `TREK reasoning engine processed the scenario through the GCC entity graph. No detailed causal chain was produced for this run.`;

  const textAr = chainLength > 0
    ? `تتبع محرك TREK سلسلة سببية من ${chainLength} خطوة عبر الشبكة المالية الخليجية. بدأ مسار الانتشار من ${topEntities || "الكيانات الرئيسية"}، بتأثير تراكمي قدره ${formatUSD(totalImpact)}.`
    : `عالج محرك TREK السيناريو عبر مخطط الكيانات الخليجية. لم يتم إنتاج سلسلة سببية مفصلة لهذا التشغيل.`;

  return {
    type: "reasoning",
    order: 2,
    textEn,
    textAr,
    severity: chainLength >= 15 ? "critical" : chainLength >= 8 ? "warning" : "info",
    dataTrail: ["result.explanation.causal_chain", "result.explanation.summary"],
    visibleTo: ["analyst", "regulator"], // Executive doesn't need chain mechanics
    metrics: [
      { label: "Chain Length", labelAr: "طول السلسلة", value: `${chainLength} steps`, sentiment: "neutral" },
      { label: "Cumulative Impact", labelAr: "الأثر التراكمي", value: formatUSD(totalImpact), sentiment: totalImpact > 1_000_000_000 ? "negative" : "neutral" },
    ],
  };
}

function buildSimulationBlock(result: RunResult): NarrativeBlock {
  const headline = result.headline;
  const banking = result.banking;
  const insurance = result.insurance;
  const fintech = result.fintech;

  const totalLoss = headline?.total_loss_usd ?? 0;
  const peakDay = headline?.peak_day ?? 0;
  const classification = result.executive_status ?? "low";

  const bankStress = banking?.aggregate_stress ?? 0;
  const insStress = insurance?.aggregate_stress ?? 0;
  const finStress = fintech?.aggregate_stress ?? 0;
  const worstSector = bankStress >= insStress && bankStress >= finStress ? "Banking"
    : insStress >= finStress ? "Insurance" : "Fintech";
  const worstSectorAr = worstSector === "Banking" ? "البنوك" : worstSector === "Insurance" ? "التأمين" : "الفنتك";

  const reinsuranceTrigger = insurance?.reinsurance_trigger ? " Reinsurance trigger activated." : "";
  const reinsuranceTriggerAr = insurance?.reinsurance_trigger ? " تم تفعيل إعادة التأمين." : "";

  const textEn = `Impact simulation projected a total loss of ${formatUSD(totalLoss)} across GCC financial sectors, peaking at day ${peakDay}. Overall classification: ${classification.toUpperCase()}. ${worstSector} shows highest stress at ${Math.round(Math.max(bankStress, insStress, finStress) * 100)}%.${reinsuranceTrigger} The shock propagated through banking (liquidity breach: ${banking?.time_to_liquidity_breach_hours ?? "N/A"}h), insurance (combined ratio: ${Math.round((insurance?.combined_ratio ?? 0) * 100)}%), and fintech sectors.`;

  const textAr = `توقعت المحاكاة خسارة إجمالية قدرها ${formatUSD(totalLoss)} عبر القطاعات المالية الخليجية، بذروة في اليوم ${peakDay}. التصنيف العام: ${classification.toUpperCase()}. قطاع ${worstSectorAr} يظهر أعلى ضغط بنسبة ${Math.round(Math.max(bankStress, insStress, finStress) * 100)}%.${reinsuranceTriggerAr}`;

  return {
    type: "simulation",
    order: 3,
    textEn,
    textAr,
    severity: classification === "CRITICAL" || classification === "SEVERE" ? "critical" : classification === "ELEVATED" ? "warning" : "info",
    dataTrail: [
      "result.headline.total_loss_usd",
      "result.headline.peak_day",
      "result.headline.classification",
      "result.banking.aggregate_stress",
      "result.insurance.aggregate_stress",
      "result.fintech.aggregate_stress",
    ],
    visibleTo: ["executive", "analyst", "regulator"],
    metrics: [
      { label: "Total Loss", labelAr: "إجمالي الخسارة", value: formatUSD(totalLoss), sentiment: "negative" },
      { label: "Peak Day", labelAr: "يوم الذروة", value: `Day ${peakDay}`, sentiment: "neutral" },
      { label: "Classification", labelAr: "التصنيف", value: classification.toUpperCase(), sentiment: classification === "CRITICAL" || classification === "SEVERE" ? "negative" : "neutral" },
      { label: "Worst Sector", labelAr: "أسوأ قطاع", value: worstSector, sentiment: "negative" },
    ],
  };
}

function buildDecisionBlock(
  result: RunResult | null,
  operatorDecisions: OperatorDecision[]
): NarrativeBlock {
  const pipelineDecisions = result?.decisions?.actions ?? [];
  const topActions = pipelineDecisions.slice(0, 3);
  const operatorCount = operatorDecisions.length;
  const closedCount = operatorDecisions.filter((d) => d.decision_status === "CLOSED").length;

  const actionSummary = topActions
    .map((a, i) => `(${i + 1}) ${a.action}`)
    .join("; ");

  const totalLossAvoided = topActions.reduce((sum, a) => sum + (a.loss_avoided_usd ?? 0), 0);

  const textEn = topActions.length > 0
    ? `Decision engine generated ${pipelineDecisions.length} prioritized actions. Top recommendations: ${actionSummary}. Combined loss avoidance potential: ${formatUSD(totalLossAvoided)}.${operatorCount > 0 ? ` ${operatorCount} operator decisions recorded (${closedCount} closed).` : ""}`
    : operatorCount > 0
    ? `${operatorCount} operator decisions were recorded for this scenario. ${closedCount} have been closed.`
    : `No decision actions were generated for this scenario.`;

  const textAr = topActions.length > 0
    ? `ولّد محرك القرار ${pipelineDecisions.length} إجراءات مُرتّبة. إمكانية تجنب خسارة مجمعة: ${formatUSD(totalLossAvoided)}.${operatorCount > 0 ? ` ${operatorCount} قرار مشغّل (${closedCount} مغلق).` : ""}`
    : operatorCount > 0
    ? `تم تسجيل ${operatorCount} قرار مشغّل. ${closedCount} تم إغلاقها.`
    : `لم يتم توليد إجراءات قرار لهذا السيناريو.`;

  return {
    type: "decision",
    order: 4,
    textEn,
    textAr,
    severity: topActions.length > 0 ? "warning" : "info",
    dataTrail: [
      "result.decisions",
      "context.decisions",
    ],
    visibleTo: ["executive", "analyst", "regulator"],
    metrics: [
      { label: "Actions", labelAr: "الإجراءات", value: `${pipelineDecisions.length}`, sentiment: "neutral" },
      { label: "Loss Avoidable", labelAr: "خسارة قابلة للتجنب", value: formatUSD(totalLossAvoided), sentiment: "positive" },
      { label: "Operator Decisions", labelAr: "قرارات المشغّل", value: `${operatorCount}`, sentiment: "neutral" },
    ],
  };
}

function buildOutcomeBlock(outcomes: Outcome[]): NarrativeBlock {
  const total = outcomes.length;
  const confirmed = outcomes.filter((o) => o.outcome_status === "CONFIRMED").length;
  const disputed = outcomes.filter((o) => o.outcome_status === "DISPUTED").length;
  const failed = outcomes.filter((o) => o.outcome_status === "FAILED").length;
  const pending = outcomes.filter(
    (o) => o.outcome_status === "PENDING_OBSERVATION" || o.outcome_status === "OBSERVED"
  ).length;

  const successRate = total > pending ? Math.round((confirmed / (total - pending)) * 100) : 0;

  const textEn = `${total} outcomes tracked. ${confirmed} confirmed, ${disputed} disputed, ${failed} failed, ${pending} pending observation. Confirmation rate: ${successRate}% (excluding pending).`;
  const textAr = `${total} نتيجة مُتتبعة. ${confirmed} مؤكدة، ${disputed} متنازع عليها، ${failed} فاشلة، ${pending} قيد الملاحظة. معدل التأكيد: ${successRate}%.`;

  return {
    type: "outcome",
    order: 5,
    textEn,
    textAr,
    severity: failed > 0 ? "critical" : disputed > 0 ? "warning" : "positive",
    dataTrail: ["context.outcomes"],
    visibleTo: ["executive", "analyst", "regulator"],
    metrics: [
      { label: "Confirmed", labelAr: "مؤكد", value: `${confirmed}`, sentiment: "positive" },
      { label: "Success Rate", labelAr: "معدل النجاح", value: `${successRate}%`, sentiment: successRate >= 70 ? "positive" : "negative" },
      { label: "Pending", labelAr: "معلّق", value: `${pending}`, sentiment: "neutral" },
    ],
  };
}

function buildROIBlock(values: DecisionValue[]): NarrativeBlock {
  const totalNet = values.reduce((sum, v) => sum + (v.net_value ?? 0), 0);
  const totalAvoided = values.reduce((sum, v) => sum + (v.avoided_loss ?? 0), 0);
  const totalCost = values.reduce(
    (sum, v) => sum + (v.operational_cost ?? 0) + (v.decision_cost ?? 0) + (v.latency_cost ?? 0),
    0
  );
  const highValue = values.filter((v) => v.value_classification === "HIGH_VALUE").length;
  const lossInducing = values.filter((v) => v.value_classification === "LOSS_INDUCING").length;

  const textEn = `ROI computation yielded a net value of ${formatUSD(totalNet)} from ${values.length} computed values. Avoided losses: ${formatUSD(totalAvoided)}. Total operational cost: ${formatUSD(totalCost)}. ${highValue} high-value decisions${lossInducing > 0 ? `, ${lossInducing} loss-inducing` : ""}.`;
  const textAr = `حسابات العائد أنتجت قيمة صافية قدرها ${formatUSD(totalNet)} من ${values.length} قيمة محسوبة. خسائر متجنبة: ${formatUSD(totalAvoided)}. تكلفة تشغيلية: ${formatUSD(totalCost)}.`;

  return {
    type: "roi",
    order: 6,
    textEn,
    textAr,
    severity: totalNet >= 0 ? "positive" : "critical",
    dataTrail: ["context.values"],
    visibleTo: ["executive", "analyst", "regulator"],
    metrics: [
      { label: "Net Value", labelAr: "القيمة الصافية", value: formatUSD(totalNet), sentiment: totalNet >= 0 ? "positive" : "negative" },
      { label: "Avoided Loss", labelAr: "الخسارة المتجنبة", value: formatUSD(totalAvoided), sentiment: "positive" },
      { label: "Total Cost", labelAr: "إجمالي التكلفة", value: formatUSD(totalCost), sentiment: "negative" },
    ],
  };
}

function buildSynthesisBlock(flow: FlowInstance, existingBlocks: NarrativeBlock[]): NarrativeBlock {
  const ctx = flow.context;
  const result = ctx.runResult;
  const completedStages = flow.stages.filter((s) => s.status === "completed").length;
  const failedStages = flow.stages.filter((s) => s.status === "failed").length;

  const healthLabel = flow.health === "healthy" ? "healthy"
    : flow.health === "degraded" ? "degraded" : "failed";

  const criticalBlocks = existingBlocks.filter((b) => b.severity === "critical").length;
  const positiveBlocks = existingBlocks.filter((b) => b.severity === "positive").length;

  const classification = result?.executive_status ?? "unknown";

  const textEn = `Flow "${ctx.scenarioLabel}" completed ${completedStages} of 7 pipeline stages (${failedStages > 0 ? `${failedStages} failed` : "no failures"}). System health: ${healthLabel}. Overall risk classification: ${classification.toUpperCase()}. ${criticalBlocks > 0 ? `${criticalBlocks} critical findings require attention.` : positiveBlocks > 0 ? "Outcomes trending positive." : "Assessment complete."}`;

  const textAr = `أكمل تدفق "${ctx.scenarioLabelAr}" ${completedStages} من 7 مراحل (${failedStages > 0 ? `${failedStages} فشل` : "بدون فشل"}). صحة النظام: ${healthLabel}. التصنيف العام: ${classification.toUpperCase()}.`;

  return {
    type: "synthesis",
    order: 7,
    textEn,
    textAr,
    severity: failedStages > 0 ? "critical" : criticalBlocks > 0 ? "warning" : "positive",
    dataTrail: ["flow.stages", "flow.health", "result.headline.classification"],
    visibleTo: ["executive", "analyst", "regulator"],
    metrics: [
      { label: "Stages Completed", labelAr: "المراحل المكتملة", value: `${completedStages}/7`, sentiment: completedStages === 7 ? "positive" : "neutral" },
      { label: "System Health", labelAr: "صحة النظام", value: healthLabel, sentiment: healthLabel === "healthy" ? "positive" : "negative" },
    ],
  };
}

function buildExecutiveSummary(
  flow: FlowInstance,
  result: RunResult | null
): { summaryEn: string; summaryAr: string } {
  const ctx = flow.context;
  const totalLoss = result?.headline?.total_loss_usd ?? 0;
  const classification = result?.executive_status ?? "unknown";
  const decisionCount = result?.decisions?.actions?.length ?? 0;
  const valueCount = ctx.values.length;
  const totalNet = ctx.values.reduce((sum, v) => sum + (v.net_value ?? 0), 0);

  const summaryEn = totalLoss > 0
    ? `"${ctx.scenarioLabel}" projects ${formatUSD(totalLoss)} total loss (${classification}) with ${decisionCount} recommended actions.${valueCount > 0 ? ` Net decision value: ${formatUSD(totalNet)}.` : ""}`
    : `"${ctx.scenarioLabel}" scenario analysis complete. ${decisionCount} actions recommended.`;

  const summaryAr = totalLoss > 0
    ? `يتوقع "${ctx.scenarioLabelAr}" خسارة ${formatUSD(totalLoss)} (${classification}) مع ${decisionCount} إجراء موصى به.${valueCount > 0 ? ` صافي القيمة: ${formatUSD(totalNet)}.` : ""}`
    : `اكتمل تحليل سيناريو "${ctx.scenarioLabelAr}". ${decisionCount} إجراء موصى به.`;

  return { summaryEn, summaryAr };
}
