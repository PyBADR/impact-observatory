"use client";

/**
 * DecisionRoomV2 — Full page assembly with decision-first ordering.
 *
 * Reorders the current command center zone hierarchy to put decisions
 * and understanding FIRST, operational detail LAST.
 *
 * Layout order:
 *   1. ExecutiveBriefV2 — 5-second comprehension snapshot
 *   2. DepthToggle — progressive disclosure selector
 *   3. DecisionReasonCards — narrative decision cards (Level 2+)
 *   4. SectorStressV2 — sector tabs with provenance (Level 2+)
 *   5. PropagationFallback — propagation chain (Level 3)
 *
 * This component is meant to be dropped into the command center page
 * as a replacement for the top section (above the existing zones).
 *
 * Data flow:
 *   All data comes from props (passed by parent that calls useCommandCenter).
 *   Provenance hooks are called internally by child components using runId.
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
} from "@/types/observatory";

type DepthLevel = 1 | 2 | 3;
type SectorId = "banking" | "insurance" | "fintech";

interface DecisionRoomV2Props {
  /** Run ID for provenance queries */
  runId: string | undefined;

  // ── Scenario (from useCommandCenter) ──
  scenarioLabel: string;
  scenarioLabelAr: string;
  severity: string;

  // ── Headline (from useCommandCenter) ──
  totalLossUsd: number;
  averageStress: number;
  propagationDepth: number;
  peakDay: number;

  // ── Chain & actions (from useCommandCenter) ──
  causalChain: CausalStep[];
  decisionActions: DecisionActionV2[];
  sectorRollups: Record<string, SectorRollup>;

  // ── UI ──
  locale: "en" | "ar";

  /** Callback when user submits a decision for review */
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
  onSubmitForReview,
}: DecisionRoomV2Props) {
  const [depth, setDepth] = useState<DepthLevel>(1);
  const [activeSector, setActiveSector] = useState<SectorId>("banking");
  const isAr = locale === "ar";

  // ── Decision reasoning (for cards) ──
  const { data: reasoningData } = useDecisionReasoning(runId);

  // ── Top 3 decisions sorted by priority ──
  const topDecisions = useMemo(
    () =>
      [...decisionActions]
        .sort((a, b) => a.priority - b.priority)
        .slice(0, 3),
    [decisionActions],
  );

  return (
    <div className="space-y-4" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Row 0: Depth Toggle ── */}
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {isAr ? "غرفة القرار" : "Decision Room"}
        </h2>
        <DepthToggle level={depth} onChange={setDepth} locale={locale} />
      </div>

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

      {/* ── Level 2: Decision Cards + Sector Stress ── */}
      {depth >= 2 && (
        <>
          {/* Decision Reason Cards */}
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

                  return (
                    <DecisionReasonCard
                      key={action.id}
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
                  );
                })}
              </div>
            </div>
          )}

          {/* Sector Stress V2 */}
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

// ── Fallback reasoning when provenance API hasn't loaded ──

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
    tradeoff_summary_en: `If not executed, potential loss of ${formatUsdSimple(action.loss_avoided_usd ?? 0)} in the ${action.sector} sector.`,
    tradeoff_summary_ar: `في حال عدم التنفيذ، خسائر محتملة بقيمة ${formatUsdSimple(action.loss_avoided_usd ?? 0)} في قطاع ${action.sector}.`,
  };
}

function formatUsdSimple(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

export default DecisionRoomV2;
