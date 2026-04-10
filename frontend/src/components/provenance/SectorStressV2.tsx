"use client";

/**
 * SectorStressV2 — Enhanced sector stress panels with provenance overlays.
 *
 * Wraps existing BankingDetailPanel / InsuranceDetailPanel / FintechDetailPanel
 * with provenance enhancements:
 *   - WhyMetricInline on key metrics (aggregate_stress, total_loss, etc.)
 *   - FreshnessBadge next to sector headers
 *   - Factor breakdown summary for sector-level stress
 *   - Range bars for key sector metrics
 *
 * Does NOT replace existing sector panels. Composes around them.
 *
 * Data flow:
 *   sectorRollups (from store) → sector metric names → provenance hooks → overlays
 */

import { useMemo } from "react";
import {
  useFactorBreakdown,
  useMetricRanges,
  useDataBasis,
} from "@/hooks/use-provenance";
import { WhyMetricInline } from "./WhyMetricInline";
import { FreshnessBadge } from "./FreshnessBadge";
import { RangeBar } from "./RangeBar";
import { FactorBar } from "./FactorBar";
import type { SectorRollup } from "@/types/observatory";

type SectorId = "banking" | "insurance" | "fintech";

interface SectorStressV2Props {
  /** Run ID for provenance queries */
  runId: string | undefined;
  /** Sector rollups from useCommandCenter */
  sectorRollups: Record<string, SectorRollup>;
  /** Display locale */
  locale: "en" | "ar";
  /** Which sector tab is active (controlled externally) */
  activeSector?: SectorId;
  /** Callback when user selects a sector tab */
  onSectorChange?: (sector: SectorId) => void;
}

const SECTORS: Array<{
  id: SectorId;
  labelEn: string;
  labelAr: string;
  metricPrefix: string;
  icon: string;
}> = [
  { id: "banking", labelEn: "Banking", labelAr: "البنوك", metricPrefix: "banking_", icon: "🏦" },
  { id: "insurance", labelEn: "Insurance", labelAr: "التأمين", metricPrefix: "insurance_", icon: "🛡" },
  { id: "fintech", labelEn: "Fintech", labelAr: "التكنولوجيا المالية", metricPrefix: "fintech_", icon: "⚡" },
];

const CLASSIFICATION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: "bg-red-100", text: "text-red-800", border: "border-red-200" },
  ELEVATED: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
  MODERATE: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  LOW: { bg: "bg-sky-50", text: "text-sky-700", border: "border-sky-200" },
  NOMINAL: { bg: "bg-slate-50", text: "text-slate-600", border: "border-slate-200" },
};

function formatUsd(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

export function SectorStressV2({
  runId,
  sectorRollups,
  locale,
  activeSector = "banking",
  onSectorChange,
}: SectorStressV2Props) {
  const isAr = locale === "ar";

  // ── Provenance data ──
  const { data: factorData } = useFactorBreakdown(runId);
  const { data: rangeData } = useMetricRanges(runId);
  const { data: basisData } = useDataBasis(runId);

  // ── Active sector data ──
  const sectorDef = SECTORS.find((s) => s.id === activeSector) ?? SECTORS[0];
  const rollup = sectorRollups[activeSector];

  // ── Find provenance data for active sector's aggregate stress ──
  const stressMetricName = `${sectorDef.metricPrefix}aggregate_stress`;
  const lossMetricName = `${sectorDef.metricPrefix}total_loss`;

  const stressBreakdown = useMemo(
    () => factorData?.breakdowns?.find((b) => b.metric_name === stressMetricName),
    [factorData, stressMetricName],
  );
  const stressRange = useMemo(
    () => rangeData?.ranges?.find((r) => r.metric_name === stressMetricName),
    [rangeData, stressMetricName],
  );
  const stressBasis = useMemo(
    () => basisData?.data_bases?.find((d) => d.metric_name === stressMetricName),
    [basisData, stressMetricName],
  );

  const maxPct = stressBreakdown?.factors?.length
    ? Math.max(...stressBreakdown.factors.map((f) => f.contribution_pct))
    : 100;

  return (
    <div
      className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* ── Sector Tabs ── */}
      <div className="flex border-b border-slate-200">
        {SECTORS.map((sector) => {
          const r = sectorRollups[sector.id];
          const isActive = sector.id === activeSector;
          const style = r ? CLASSIFICATION_COLORS[r.classification] ?? CLASSIFICATION_COLORS.NOMINAL : CLASSIFICATION_COLORS.NOMINAL;

          return (
            <button
              key={sector.id}
              onClick={() => onSectorChange?.(sector.id)}
              className={`flex-1 px-4 py-3 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-white border-b-2 border-blue-600 text-slate-800"
                  : "bg-slate-50 text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                <span>{sector.icon}</span>
                <span>{isAr ? sector.labelAr : sector.labelEn}</span>
                {r && (
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border ${style.bg} ${style.text} ${style.border}`}>
                    {r.classification}
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Sector Content ── */}
      <div className="p-5 space-y-4">
        {!rollup ? (
          <p className="text-xs text-slate-400 text-center py-4">
            {isAr ? "لا تتوفر بيانات لهذا القطاع" : "No data available for this sector"}
          </p>
        ) : (
          <>
            {/* Header row: sector name + classification + freshness */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-bold text-slate-800">
                  {isAr ? sectorDef.labelAr : sectorDef.labelEn}
                </h3>
                {stressBasis && (
                  <FreshnessBadge basis={stressBasis} locale={locale} showLabel />
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">
                  {rollup.node_count} {isAr ? "عقدة" : "nodes"}
                </span>
              </div>
            </div>

            {/* Key metrics with WhyMetricInline */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                  {isAr ? "إجمالي الضغط" : "Aggregate Stress"}
                </p>
                <WhyMetricInline
                  metricName={stressMetricName}
                  runId={runId}
                  locale={locale}
                  className="text-lg font-bold text-slate-800 tabular-nums"
                >
                  {Math.round(rollup.aggregate_stress * 100)}%
                </WhyMetricInline>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                  {isAr ? "إجمالي الخسائر" : "Total Loss"}
                </p>
                <WhyMetricInline
                  metricName={lossMetricName}
                  runId={runId}
                  locale={locale}
                  className="text-lg font-bold text-slate-800 tabular-nums"
                >
                  {formatUsd(rollup.total_loss)}
                </WhyMetricInline>
              </div>
            </div>

            {/* Range bar if available */}
            {stressRange && (
              <div>
                <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  {isAr ? "النطاق المتوقع" : "Expected Range"}
                </h4>
                <RangeBar range={stressRange} locale={locale} />
              </div>
            )}

            {/* Factor breakdown if available */}
            {stressBreakdown && stressBreakdown.factors.length > 0 && (
              <div>
                <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  {isAr ? "عوامل الضغط" : "Stress Factors"}
                </h4>
                <div className="space-y-1.5">
                  {stressBreakdown.factors.slice(0, 5).map((factor, idx) => (
                    <FactorBar
                      key={factor.factor_name}
                      factor={factor}
                      index={idx}
                      maxPct={maxPct}
                      unit={stressBreakdown.unit}
                      locale={locale}
                    />
                  ))}
                </div>
                <p className="text-[10px] text-slate-400 mt-1.5">
                  {Math.round(stressBreakdown.coverage_pct)}%{" "}
                  {isAr ? "من القيمة مفسّرة" : "of value explained"}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default SectorStressV2;
