"use client";

/**
 * FactorBar — Single horizontal bar showing one contributing factor.
 *
 * Used inside MetricExplainer to show why a number is what it is.
 * Each bar: label · bar fill · absolute value · percentage.
 */

import type { FactorContribution } from "@/types/provenance";

const BAR_COLORS = [
  "bg-blue-600",
  "bg-blue-500",
  "bg-sky-500",
  "bg-sky-400",
  "bg-slate-400",
];

interface FactorBarProps {
  factor: FactorContribution;
  index: number;
  maxPct: number;
  unit: string;
  locale: "en" | "ar";
}

function formatValue(v: number, unit: string): string {
  if (unit === "USD") {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
    return `$${Math.round(v)}`;
  }
  if (unit === "score [0-1]") return v.toFixed(3);
  return String(Math.round(v * 100) / 100);
}

export function FactorBar({ factor, index, maxPct, unit, locale }: FactorBarProps) {
  const pct = Math.max(0, Math.min(100, factor.contribution_pct));
  const barWidth = maxPct > 0 ? (pct / maxPct) * 100 : 0;
  const barColor = BAR_COLORS[index] ?? BAR_COLORS[BAR_COLORS.length - 1];
  const label = locale === "ar" ? factor.factor_name_ar : factor.factor_name;
  const rationale = locale === "ar" ? factor.rationale_ar : factor.rationale_en;

  return (
    <div className="group">
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-500 w-32 flex-shrink-0 truncate text-end">
          {label || factor.factor_name}
        </span>
        <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden">
          <div
            className={`h-full rounded ${barColor} transition-all duration-300`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
        <span className="text-xs font-semibold text-slate-700 tabular-nums w-16 text-end">
          {formatValue(factor.contribution_value, unit)}
        </span>
        <span className="text-xs text-slate-400 tabular-nums w-10 text-end">
          {Math.round(pct)}%
        </span>
      </div>
      {rationale && (
        <p className="hidden group-hover:block mt-1 ml-[140px] text-[10px] text-slate-400 leading-tight">
          {rationale}
        </p>
      )}
    </div>
  );
}

export default FactorBar;
