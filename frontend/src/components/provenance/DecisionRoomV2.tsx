"use client";

/**
 * DecisionRoomV2 — Executive Mandate Page
 *
 * One dominant directive. Why now. Owner. Urgency. Consequence of delay.
 * Maximum 2 supporting directives.
 *
 * This is a mandate page, not a decision register.
 * No cards. No grids. No comparison. No analytics.
 */

import React from "react";
import type {
  CausalStep,
  DecisionActionV2,
  SectorRollup,
  MetricExplanation,
  DecisionTransparencyResult,
  ReliabilityPayload,
  MacroContext,
} from "@/types/observatory";

interface TrustInfo {
  auditHash?: string;
  modelVersion?: string;
  pipelineVersion?: string;
  dataSources?: string[];
  stagesCompleted?: string[];
  warnings?: string[];
  confidence?: number;
}

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
  metricExplanations?: MetricExplanation[];
  decisionTransparency?: DecisionTransparencyResult;
  reliability?: ReliabilityPayload;
  confidenceScore?: number;
  narrativeEn?: string;
  narrativeAr?: string;
  macroContext?: MacroContext;
  trustInfo?: TrustInfo;
  onSubmitForReview?: (actionId: string) => void;
}

export function DecisionRoomV2({
  scenarioLabel,
  scenarioLabelAr,
  severity,
  totalLossUsd,
  decisionActions,
  locale,
  confidenceScore,
  narrativeEn,
  narrativeAr,
}: DecisionRoomV2Props) {
  const isAr = locale === "ar";
  const displayLabel = isAr ? (scenarioLabelAr || scenarioLabel) : scenarioLabel;
  const narrative = isAr ? (narrativeAr || narrativeEn) : narrativeEn;
  const severityPct = Math.round(parseFloat(severity) * 100);

  const primary = decisionActions[0] ?? null;
  const supporting = decisionActions.slice(1, 3);

  const formatUsd = (v: number): string => {
    if (v >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    return `$${(v / 1e3).toFixed(0)}K`;
  };

  return (
    <div
      className="max-w-3xl mx-auto px-6 sm:px-8 py-10"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* ── Context header ── */}
      <div className="mb-12">
        <h2 className="text-[1.375rem] sm:text-[1.625rem] font-bold text-[#1d1d1f] leading-tight tracking-tight mb-3">
          {isAr ? "القرار التنفيذي" : "Executive Decision"}
        </h2>
        <p className="text-[0.875rem] text-[#6e6e73] leading-relaxed">
          {displayLabel}
          <span className="text-[#0071e3] ml-2">· {severityPct}% severity</span>
          {totalLossUsd > 0 && (
            <span className="ml-2">· {formatUsd(totalLossUsd)} projected loss</span>
          )}
        </p>
      </div>

      {/* ── No directives state ── */}
      {!primary && (
        <p className="text-[0.9375rem] text-[#6e6e73]">
          {isAr
            ? "لا توجد توجيهات نشطة — النظام في وضع المراقبة."
            : "No active directives — system in monitoring posture."}
        </p>
      )}

      {/* ── Primary directive — the mandate ── */}
      {primary && (
        <>
          {/* Why now — the narrative justification */}
          {narrative && (
            <div className="mb-12">
              <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
                {isAr ? "لماذا الآن" : "Why Now"}
              </p>
              <div className="h-px bg-[#e5e5e7] mb-6" />
              <p className="text-[0.9375rem] text-[#515154] leading-[1.75]">
                {narrative}
              </p>
            </div>
          )}

          {/* The directive — dominant visual element */}
          <div className="mb-12">
            <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
              {isAr ? "التوجيه الرئيسي" : "Primary Directive"}
            </p>
            <div className="h-px bg-[#e5e5e7] mb-6" />

            <p className="text-[1.125rem] font-bold text-[#1d1d1f] leading-snug mb-4">
              {primary.action}
            </p>

            {/* Owner, sector, urgency — inline prose, not grid */}
            <p className="text-[0.8125rem] text-[#6e6e73] leading-[1.75] mb-5">
              {isAr ? "المسؤول" : "Owner"}: <span className="text-[#1d1d1f] font-semibold">{primary.owner || (isAr ? "غير محدد" : "Unassigned")}</span>
              <span className="mx-2 text-[#8e8e93]">·</span>
              {isAr ? "القطاع" : "Sector"}: <span className="text-[#1d1d1f] font-semibold">{primary.sector || "Cross-sector"}</span>
              <span className="mx-2 text-[#8e8e93]">·</span>
              {isAr ? "الإلحاح" : "Urgency"}: <span className="text-[#0071e3] font-semibold">{
                primary.urgency != null && primary.urgency > 0
                  ? `${Math.round(primary.urgency)}%`
                  : isAr ? "فوري" : "Immediate"
              }</span>
              {confidenceScore != null && (
                <>
                  <span className="mx-2 text-[#8e8e93]">·</span>
                  {isAr ? "الثقة" : "Confidence"}: <span className="text-[#515154] font-semibold">{Math.round(confidenceScore * 100)}%</span>
                </>
              )}
            </p>

            {/* Consequence of delay — amber, urgent */}
            <div className="border-l-2 border-[#0071e3]/40 pl-5">
              <p className="text-[0.6875rem] text-[#6e6e73] uppercase tracking-widest font-medium mb-1.5">
                {isAr ? "عواقب التأخير" : "Consequence of Delay"}
              </p>
              <p className="text-[0.875rem] text-[#0071e3] leading-[1.75]">
                {totalLossUsd > 0
                  ? isAr
                    ? `التأخير في التنفيذ يعرض النظام لخسائر إضافية تتجاوز ${formatUsd(totalLossUsd)}. يتسارع الضغط عبر القطاعات المترابطة.`
                    : `Delay in execution exposes the system to losses exceeding ${formatUsd(totalLossUsd)}. Pressure accelerates across interconnected sectors.`
                  : isAr
                    ? "التأخير يضيق نافذة الاستجابة ويزيد من مخاطر التصعيد."
                    : "Delay narrows the response window and increases escalation risk."}
              </p>
            </div>
          </div>

          {/* ── Supporting directives — max 2, deliberately smaller ── */}
          {supporting.length > 0 && (
            <div className="mb-12">
              <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
                {isAr ? "توجيهات داعمة" : "Supporting Directives"}
              </p>
              <div className="h-px bg-[#e5e5e7] mb-6" />

              <div className="space-y-6 border-l-2 border-[#e5e5e7] pl-5">
                {supporting.map((action, i) => (
                  <div key={i}>
                    <p className="text-[0.9375rem] text-[#515154] leading-snug mb-2">
                      {action.action}
                    </p>
                    <p className="text-[0.75rem] text-[#6e6e73]">
                      {action.owner || (isAr ? "غير محدد" : "Unassigned")}
                      <span className="mx-2 text-[#8e8e93]">·</span>
                      {action.sector || "Cross-sector"}
                      {action.urgency != null && action.urgency > 0 && (
                        <>
                          <span className="mx-2 text-[#8e8e93]">·</span>
                          <span className="text-[#0071e3]">
                            {Math.round(action.urgency)}% urgency
                          </span>
                        </>
                      )}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Remaining count if more than 3 ── */}
          {decisionActions.length > 3 && (
            <p className="text-[0.8125rem] text-[#6e6e73]">
              {decisionActions.length - 3} {isAr ? "توجيهات إضافية في النظام" : "additional directives in the system"}.
            </p>
          )}
        </>
      )}

      {/* Timestamp */}
      <div className="mt-14 pt-5 border-t border-[#e5e5e7]">
        <p className="text-[0.625rem] text-[#8e8e93] tracking-wider">
          {isAr ? "صفحة القرار التنفيذي" : "Executive mandate"} · {displayLabel}
        </p>
      </div>
    </div>
  );
}

export default DecisionRoomV2;
