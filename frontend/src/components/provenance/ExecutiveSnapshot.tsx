"use client";

/**
 * ExecutiveSnapshot — 5-second comprehension executive summary.
 *
 * Fixed at top of every view. No scrolling. 4 rows maximum:
 *   Row 1: Scenario identity + severity badge
 *   Row 2: One-line propagation statement
 *   Row 3: Three impact cards (loss range, risk level, breach timing)
 *   Row 4: Three decision summaries (action + net value)
 *
 * This is the FIRST thing any user sees.
 * If they need to "read everything" → this component has FAILED.
 */

import type { MetricRange, DecisionReasoning } from "@/types/provenance";
import { RangeBar } from "./RangeBar";

interface ImpactCard {
  label: string;
  labelAr: string;
  range?: MetricRange;
  fallbackValue?: string;
  severity?: string;
}

interface DecisionSummary {
  rank: number;
  title: string;
  titleAr: string;
  netValueUsd: number;
  reasoning?: DecisionReasoning;
}

interface ExecutiveSnapshotProps {
  scenarioLabel: string;
  scenarioLabelAr: string;
  riskLevel: string;
  propagationStatement: string;
  propagationStatementAr: string;
  impacts: ImpactCard[];
  decisions: DecisionSummary[];
  locale: "en" | "ar";
}

const RISK_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: "bg-red-100", text: "text-red-800", border: "border-red-200" },
  SEVERE: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
  HIGH: { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
  ELEVATED: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  MODERATE: { bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200" },
  LOW: { bg: "bg-sky-50", text: "text-sky-700", border: "border-sky-200" },
  NOMINAL: { bg: "bg-slate-50", text: "text-slate-600", border: "border-slate-200" },
};

function formatUsd(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

export function ExecutiveSnapshot({
  scenarioLabel,
  scenarioLabelAr,
  riskLevel,
  propagationStatement,
  propagationStatementAr,
  impacts,
  decisions,
  locale,
}: ExecutiveSnapshotProps) {
  const isAr = locale === "ar";
  const riskStyle = RISK_COLORS[riskLevel.toUpperCase()] ?? RISK_COLORS.MODERATE;

  return (
    <div
      className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Row 1: Scenario Identity */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold text-slate-800 leading-tight">
          {isAr ? scenarioLabelAr : scenarioLabel}
        </h2>
        <span
          className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border ${riskStyle.bg} ${riskStyle.text} ${riskStyle.border}`}
        >
          {riskLevel}
        </span>
      </div>

      {/* Row 2: One-Line Propagation Statement */}
      <div className="px-3 py-2 bg-slate-50 border border-slate-100 rounded-lg">
        <p className="text-xs text-slate-700 leading-relaxed font-medium">
          {isAr ? propagationStatementAr : propagationStatement}
        </p>
      </div>

      {/* Row 3: Three Impact Cards */}
      <div className="grid grid-cols-3 gap-3">
        {impacts.slice(0, 3).map((impact, idx) => (
          <div
            key={idx}
            className="p-3 bg-slate-50 border border-slate-100 rounded-lg space-y-1.5"
          >
            <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              {isAr ? impact.labelAr : impact.label}
            </h4>
            {impact.range ? (
              <RangeBar range={impact.range} locale={locale} compact />
            ) : (
              <p className="text-sm font-bold text-slate-800 tabular-nums">
                {impact.fallbackValue ?? "—"}
              </p>
            )}
            {impact.severity && (
              <SeverityDot level={impact.severity} />
            )}
          </div>
        ))}
      </div>

      {/* Row 4: Three Decision Summaries */}
      {decisions.length > 0 && (
        <div>
          <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            {isAr ? "أهم القرارات" : "Top Decisions"}
          </h4>
          <div className="space-y-1.5">
            {decisions.slice(0, 3).map((d) => (
              <div
                key={d.rank}
                className="flex items-center gap-3 px-3 py-2 bg-slate-50 border border-slate-100 rounded-lg"
              >
                <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex-shrink-0">
                  {d.rank}
                </span>
                <span className="text-xs text-slate-700 font-medium flex-1 truncate">
                  {isAr ? d.titleAr : d.title}
                </span>
                <span
                  className={`text-xs font-bold tabular-nums flex-shrink-0 ${
                    d.netValueUsd >= 0 ? "text-emerald-700" : "text-red-600"
                  }`}
                >
                  {d.netValueUsd >= 0 ? "+" : ""}{formatUsd(d.netValueUsd)}{" "}
                  <span className="font-normal text-slate-400">
                    {isAr ? "صافي" : "net"}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────

function SeverityDot({ level }: { level: string }) {
  const colors: Record<string, string> = {
    CRITICAL: "bg-red-500",
    SEVERE: "bg-red-400",
    HIGH: "bg-orange-500",
    ELEVATED: "bg-amber-500",
    MODERATE: "bg-yellow-500",
    LOW: "bg-sky-500",
    NOMINAL: "bg-slate-400",
  };
  return (
    <div className="flex items-center gap-1">
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${colors[level.toUpperCase()] ?? "bg-slate-400"}`} />
      <span className="text-[10px] text-slate-500 uppercase">{level}</span>
    </div>
  );
}

export default ExecutiveSnapshot;
