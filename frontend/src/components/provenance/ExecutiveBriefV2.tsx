"use client";

/**
 * ExecutiveBriefV2 — Wired ExecutiveSnapshot connected to live data.
 *
 * This is the primary integration component that connects:
 *   - useCommandCenter() → scenario, headline, causalChain, decisionActions
 *   - useMetricRanges() → impact card ranges
 *   - useDecisionReasoning() → decision reasoning objects
 *
 * Produces a fully-wired ExecutiveSnapshot that can be dropped into
 * any page with just a runId.
 *
 * Data flow:
 *   runId → useCommandCenter + provenance hooks → transform → ExecutiveSnapshot props
 */

import { useMemo } from "react";
import { useMetricRanges, useDecisionReasoning } from "@/hooks/use-provenance";
import { ExecutiveSnapshot } from "./ExecutiveSnapshot";
import type { MetricRange, DecisionReasoning } from "@/types/provenance";
import type { CausalStep, DecisionActionV2 } from "@/types/observatory";

interface ExecutiveBriefV2Props {
  /** Run ID for provenance queries */
  runId: string | undefined;
  /** Scenario data from useCommandCenter */
  scenarioLabel: string;
  scenarioLabelAr: string;
  severity: string;
  /** Headline data from useCommandCenter */
  totalLossUsd: number;
  averageStress: number;
  propagationDepth: number;
  peakDay: number;
  /** Causal chain from useCommandCenter */
  causalChain: CausalStep[];
  /** Decision actions from useCommandCenter */
  decisionActions: DecisionActionV2[];
  /** Display locale */
  locale: "en" | "ar";
}

function formatUsd(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

/** Map stress level to risk label */
function stressToRisk(stress: number): string {
  if (stress >= 0.80) return "SEVERE";
  if (stress >= 0.65) return "HIGH";
  if (stress >= 0.50) return "ELEVATED";
  if (stress >= 0.35) return "MODERATE";
  if (stress >= 0.20) return "LOW";
  return "NOMINAL";
}

export function ExecutiveBriefV2({
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
  locale,
}: ExecutiveBriefV2Props) {
  // ── Provenance data ──
  const { data: rangeData } = useMetricRanges(runId);
  const { data: reasoningData } = useDecisionReasoning(runId);

  // ── Build propagation statement from causal chain ──
  const { propagationStatement, propagationStatementAr } = useMemo(() => {
    if (causalChain.length === 0) {
      return {
        propagationStatement: `${severity} scenario with ${propagationDepth}-depth propagation. Peak impact at day ${peakDay}. Total exposure: ${formatUsd(totalLossUsd)}.`,
        propagationStatementAr: `سيناريو ${severity} بعمق انتشار ${propagationDepth}. ذروة التأثير في اليوم ${peakDay}. إجمالي التعرض: ${formatUsd(totalLossUsd)}.`,
      };
    }

    const first = causalChain[0];
    const last = causalChain[causalChain.length - 1];
    const mechanisms = [...new Set(causalChain.map((s) => s.mechanism))].slice(0, 3);

    return {
      propagationStatement: `Impact propagates from ${first.entity_label} to ${last.entity_label} via ${mechanisms.join(", ")} (${causalChain.length} steps, depth ${propagationDepth}). Peak at day ${peakDay}. Total exposure: ${formatUsd(totalLossUsd)}.`,
      propagationStatementAr: `ينتشر الأثر من ${first.entity_label_ar || first.entity_label} إلى ${last.entity_label_ar || last.entity_label} عبر ${mechanisms.join("، ")} (${causalChain.length} مراحل). الذروة في اليوم ${peakDay}. إجمالي التعرض: ${formatUsd(totalLossUsd)}.`,
    };
  }, [causalChain, severity, propagationDepth, peakDay, totalLossUsd]);

  // ── Build impact cards ──
  const impacts = useMemo(() => {
    const lossRange = rangeData?.ranges?.find(
      (r) => r.metric_name === "total_loss_usd",
    );
    const stressRange = rangeData?.ranges?.find(
      (r) => r.metric_name === "aggregate_stress",
    );

    return [
      {
        label: "Total Loss",
        labelAr: "إجمالي الخسائر",
        range: lossRange,
        fallbackValue: formatUsd(totalLossUsd),
        severity: stressToRisk(averageStress),
      },
      {
        label: "System Stress",
        labelAr: "ضغط النظام",
        range: stressRange,
        fallbackValue: `${Math.round(averageStress * 100)}%`,
        severity: stressToRisk(averageStress),
      },
      {
        label: "Peak Impact",
        labelAr: "ذروة التأثير",
        fallbackValue: locale === "ar" ? `يوم ${peakDay}` : `Day ${peakDay}`,
      },
    ];
  }, [rangeData, totalLossUsd, averageStress, peakDay, locale]);

  // ── Build decision summaries (top 3) ──
  const decisions = useMemo(() => {
    const topActions = [...decisionActions]
      .sort((a, b) => a.priority - b.priority)
      .slice(0, 3);

    return topActions.map((action, idx) => {
      const reasoning = reasoningData?.reasonings?.find(
        (r) => r.action_id === action.id,
      );

      return {
        rank: idx + 1,
        title: action.action,
        titleAr: action.action_ar,
        netValueUsd: (action.loss_avoided_usd ?? 0) - (action.cost_usd ?? 0),
        reasoning: reasoning as DecisionReasoning | undefined,
      };
    });
  }, [decisionActions, reasoningData]);

  const riskLevel = stressToRisk(averageStress);

  return (
    <ExecutiveSnapshot
      scenarioLabel={scenarioLabel}
      scenarioLabelAr={scenarioLabelAr}
      riskLevel={riskLevel}
      propagationStatement={propagationStatement}
      propagationStatementAr={propagationStatementAr}
      impacts={impacts}
      decisions={decisions}
      locale={locale}
    />
  );
}

export default ExecutiveBriefV2;
