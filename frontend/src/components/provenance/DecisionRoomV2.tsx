"use client";

/**
 * DecisionRoomV2 — Sprint 3: Explainability-integrated decision surface.
 *
 * Every metric and decision shown in this component is now defensible.
 * The ExplainabilityPanel surfaces at Level 1 (compact) so the user
 * can immediately see confidence, range, and top drivers without
 * expanding anything.
 *
 * Layout:
 *   Level 1 (always visible):
 *     1. Loss-Inducing Warning (if applicable)
 *     2. Executive Brief (headline KPIs)
 *     3. ExplainabilityPanel (compact) — confidence + range + drivers
 *   Level 2 (expandable):
 *     4. Decision Cards with transparency overlays
 *     5. Sector Stress
 *   Level 3 (deep dive):
 *     6. Propagation Chain
 *     7. ExplainabilityPanel (expanded) — per-metric detail
 *
 * Backend engines: explanation_engine, trust_engine, range_engine,
 * attribution_defense_engine — all already wired. Zero new engines.
 */

import { useState, useMemo } from "react";
import { useDecisionReasoning } from "@/hooks/use-provenance";
import { ExecutiveBriefV2 } from "./ExecutiveBriefV2";
import { DecisionReasonCard } from "./DecisionReasonCard";
import { SectorStressV2 } from "./SectorStressV2";
import { PropagationFallback } from "./PropagationFallback";
import { DepthToggle } from "./DepthToggle";
import type {
  CausalStep,
  DecisionActionV2,
  SectorRollup,
  MetricExplanation,
  DecisionTransparencyResult,
  ReliabilityPayload,
  MacroContext,
} from "@/types/observatory";
import { LossInducingBanner } from "@/components/trust/LossInducingBanner";
import { ActionTransparencyOverlay } from "@/components/trust/ActionTransparencyOverlay";
import { ExplainabilityPanel } from "@/components/trust/ExplainabilityPanel";
import { MacroPanel } from "@/components/macro/MacroPanel";

type DepthLevel = 1 | 2 | 3;
type SectorId = "banking" | "insurance" | "fintech";

interface DecisionRoomV2Props {
  runId: string | undefined;
  scenarioLabel: string;
  scenarioLabelAr: string;
  severity: string;
  totalLossUsd: number;
  averageStress: number;
  propagationDepth: number;
  peakDay: number;
  causalChain: CausalStep[];
  decisionActions: DecisionActionV2[];
  sectorRollups: Record<string, SectorRollup>;
  locale: "en" | "ar";

  // Sprint 1 — Decision Trust Layer
  metricExplanations?: MetricExplanation[];
  decisionTransparency?: DecisionTransparencyResult;

  // Sprint 2 — Decision Reliability Layer
  reliability?: ReliabilityPayload;

  // Sprint 3 — Explainability Layer
  confidenceScore?: number;
  narrativeEn?: string;
  narrativeAr?: string;
  macroContext?: MacroContext;

  onSubmitForReview?: (actionId: string) => void;
}

export function DecisionRoomV2({
  runId,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  totalLossUsd,
  averageStress,
  propagationDepth,
  peakDay,
  causalChain,
  decisionActions,
  sectorRollups,
  locale,
  metricExplanations,
  decisionTransparency,
  reliability,
  confidenceScore,
  narrativeEn,
  narrativeAr,
  macroContext,
  onSubmitForReview,
}: DecisionRoomV2Props) {
  const [depth, setDepth] = useState<DepthLevel>(1);
  const [activeSector, setActiveSector] = useState<SectorId>("banking");
  const isAr = locale === "ar";

  const { data: reasoningData } = useDecisionReasoning(runId);

  const topDecisions = useMemo(
    () =>
      [...decisionActions]
        .sort((a, b) => a.priority - b.priority)
        .slice(0, 3),
    [decisionActions],
  );

  // ── Derive top drivers across all metrics for the inline trust bar ──
  const topDriverLabel = useMemo(() => {
    if (!metricExplanations?.length) return null;
    const allDrivers: { label: string; pct: number }[] = [];
    for (const exp of metricExplanations) {
      for (const d of exp.drivers ?? []) {
        allDrivers.push({ label: d.label, pct: d.contribution_pct });
      }
    }
    // Deduplicate by label, keep highest pct
    const seen = new Map<string, number>();
    for (const d of allDrivers) {
      const existing = seen.get(d.label);
      if (!existing || d.pct > existing) seen.set(d.label, d.pct);
    }
    const sorted = [...seen.entries()].sort((a, b) => b[1] - a[1]);
    return sorted[0]?.[0] ?? null;
  }, [metricExplanations]);

  // ── Derive loss range from reliability ──
  const lossRange = useMemo(() => {
    if (!reliability?.ranges) return null;
    return reliability.ranges.find((r) => r.metric_id === "projected_loss" || r.metric_id === "total_loss");
  }, [reliability]);

  // Confidence display
  const confPct = Math.round((confidenceScore ?? 0) * 100);
  const confColor = confPct >= 75 ? "text-emerald-600" : confPct >= 50 ? "text-amber-600" : "text-red-500";
  const confBg = confPct >= 75 ? "bg-emerald-50" : confPct >= 50 ? "bg-amber-50" : "bg-red-50";

  return (
    <div className="space-y-4" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Row 0: Title + Depth Toggle ── */}
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {isAr ? "غرفة القرار" : "Decision Room"}
        </h2>
        <DepthToggle level={depth} onChange={setDepth} locale={locale} />
      </div>

      {/* ── Loss-Inducing Warning Banner ── */}
      {decisionTransparency && (
        <LossInducingBanner
          hasLossInducing={decisionTransparency.has_loss_inducing}
          lossInducingCount={decisionTransparency.loss_inducing_count}
          lossInducingActions={decisionTransparency.loss_inducing_actions}
          warningBanner={decisionTransparency.warning_banner}
          locale={locale}
        />
      )}

      {/* ── Level 1: Executive Snapshot (always visible) ── */}
      <ExecutiveBriefV2
        runId={runId}
        scenarioLabel={scenarioLabel}
        scenarioLabelAr={scenarioLabelAr}
        severity={severity}
        totalLossUsd={totalLossUsd}
        averageStress={averageStress}
        propagationDepth={propagationDepth}
        peakDay={peakDay}
        causalChain={causalChain}
        decisionActions={decisionActions}
        locale={locale}
      />

      {/* ══════════════════════════════════════════════════════════════
           SPRINT 3: Inline Trust Bar — Always visible at Level 1.
           Answers "Why should I trust this?" in under 5 seconds.
           ══════════════════════════════════════════════════════════════ */}
      {(confidenceScore != null || lossRange || topDriverLabel) && (
        <div className="flex items-center gap-3 px-3 py-2 bg-white border border-slate-200 rounded-lg flex-wrap">
          {/* Confidence badge */}
          {confidenceScore != null && (
            <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded ${confBg}`}>
              <span className="text-[10px] text-slate-500 font-medium">
                {isAr ? "الثقة" : "Confidence"}
              </span>
              <span className={`text-xs font-bold tabular-nums ${confColor}`}>
                {confPct}%
              </span>
            </div>
          )}

          {/* Range badge */}
          {lossRange && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-50">
              <span className="text-[10px] text-slate-500 font-medium">
                {isAr ? "النطاق" : "Range"}
              </span>
              <span className="text-[10px] font-bold tabular-nums text-slate-700">
                {formatUsdCompact(lossRange.low)} – {formatUsdCompact(lossRange.high)}
              </span>
            </div>
          )}

          {/* Top driver badge */}
          {topDriverLabel && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50">
              <span className="text-[10px] text-slate-500 font-medium">
                {isAr ? "المحرك الأول" : "Top Driver"}
              </span>
              <span className="text-[10px] font-bold text-blue-700">
                {topDriverLabel}
              </span>
            </div>
          )}

          {/* Macro SRI badge (if available) */}
          {macroContext && macroContext.system_risk_index > 0 && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-50">
              <span className="text-[10px] text-slate-500 font-medium">
                {isAr ? "المخاطر" : "System Risk"}
              </span>
              <span className="text-[10px] font-bold tabular-nums text-amber-700">
                {(macroContext.system_risk_index * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
           SPRINT 3: ExplainabilityPanel — Full trust panel at Level 1.
           Compact by default, expandable for per-metric detail.
           ══════════════════════════════════════════════════════════════ */}
      <ExplainabilityPanel
        metricExplanations={metricExplanations}
        reliability={reliability}
        confidenceScore={confidenceScore}
        narrativeEn={narrativeEn}
        narrativeAr={narrativeAr}
        locale={locale}
        defaultExpanded={false}
      />

      {/* ── Macro Context (compact, below explainability) ── */}
      {macroContext && (
        <MacroPanel macroContext={macroContext} locale={locale} />
      )}

      {/* ── Level 2: Decision Cards + Sector Stress ── */}
      {depth >= 2 && (
        <>
          {topDecisions.length > 0 && (
            <div>
              <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-3">
                {isAr ? "أهم القرارات" : "Top Decisions"}
              </h3>
              <div className="space-y-3">
                {topDecisions.map((action, idx) => {
                  const reasoning = reasoningData?.reasonings?.find(
                    (r) => r.action_id === action.id,
                  );
                  const actionTransparency = decisionTransparency?.action_transparencies?.find(
                    (at) => at.action_id === action.id,
                  );
                  const outcomeRecord = reliability?.outcome_records?.find(
                    (o) => o.action_id === action.id,
                  );
                  const trustMemory = reliability?.trust_memories?.find(
                    (m) => m.action_id === action.id,
                  );
                  const confAdj = reliability?.confidence_adjustments?.find(
                    (c) => c.metric_id === action.id,
                  );

                  return (
                    <div key={action.id} className="space-y-0">
                      <DecisionReasonCard
                        rank={idx + 1}
                        actionTitle={action.action}
                        actionTitleAr={action.action_ar}
                        reasoning={reasoning ?? buildFallbackReasoning(action)}
                        costUsd={action.cost_usd ?? 0}
                        lossAvoidedUsd={action.loss_avoided_usd ?? 0}
                        confidence={action.confidence ?? 0.5}
                        status="PENDING_REVIEW"
                        locale={locale}
                        onSubmitForReview={onSubmitForReview}
                      />
                      {actionTransparency && (
                        <div className="mx-5 mb-3 -mt-1 pt-3 border-t border-dashed border-slate-200">
                          <ActionTransparencyOverlay
                            transparency={actionTransparency}
                            locale={locale}
                            outcomeRecord={outcomeRecord}
                            trustMemory={trustMemory}
                            confidenceAdjustment={confAdj}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <SectorStressV2
            runId={runId}
            sectorRollups={sectorRollups}
            locale={locale}
            activeSector={activeSector}
            onSectorChange={setActiveSector}
          />
        </>
      )}

      {/* ── Level 3: Full Detail — Propagation Chain ── */}
      {depth >= 3 && (
        <PropagationFallback
          scenarioLabel={scenarioLabel}
          scenarioLabelAr={scenarioLabelAr}
          causalChain={causalChain}
          propagationDepth={propagationDepth}
          peakDay={peakDay}
          totalLossUsd={totalLossUsd}
          locale={locale}
        />
      )}
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────

function buildFallbackReasoning(action: DecisionActionV2) {
  return {
    decision_id: action.id,
    action_id: action.id,
    why_this_decision_en: `Recommended ${action.action} targeting ${action.sector} sector with urgency ${Math.round(action.urgency * 100)}%.`,
    why_this_decision_ar: `يوصى بـ ${action.action_ar} لقطاع ${action.sector} بأولوية ${Math.round(action.urgency * 100)}%.`,
    why_now_en: `Urgency score ${Math.round(action.urgency * 100)}% with regulatory risk at ${Math.round(action.regulatory_risk * 100)}%.`,
    why_now_ar: `درجة الإلحاح ${Math.round(action.urgency * 100)}% مع مخاطر تنظيمية عند ${Math.round(action.regulatory_risk * 100)}%.`,
    why_this_rank_en: `Priority ${action.priority} based on value-urgency composite score.`,
    why_this_rank_ar: `الأولوية ${action.priority} بناءً على مؤشر القيمة والإلحاح المركب.`,
    affected_entities: [action.target_node_id],
    propagation_link_en: "",
    propagation_link_ar: "",
    regime_link_en: "",
    regime_link_ar: "",
    trust_link_en: "",
    trust_link_ar: "",
    tradeoff_summary_en: `If not executed, potential loss of ${formatUsdCompact(action.loss_avoided_usd ?? 0)} in the ${action.sector} sector.`,
    tradeoff_summary_ar: `في حال عدم التنفيذ، خسائر محتملة بقيمة ${formatUsdCompact(action.loss_avoided_usd ?? 0)} في قطاع ${action.sector}.`,
  };
}

function formatUsdCompact(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

export default DecisionRoomV2;
