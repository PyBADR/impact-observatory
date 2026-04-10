"use client";

/**
 * RangeBar — Visual min–expected–max range for a metric.
 *
 * Replaces false-precision single-point values with honest uncertainty bands.
 * Shows: ├── min ────── expected ────── max ──┤ with confidence.
 */

import type { MetricRange } from "@/types/provenance";

interface RangeBarProps {
  range: MetricRange;
  locale: "en" | "ar";
  compact?: boolean;
}

function formatRangeValue(v: number, unit: string): string {
  if (unit === "USD") {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
    return `$${Math.round(v)}`;
  }
  if (unit === "score [0-1]") return v.toFixed(2);
  if (unit === "day") return `Day ${Math.round(v)}`;
  if (unit === "hours") return `${Math.round(v)}h`;
  return String(Math.round(v * 100) / 100);
}

export function RangeBar({ range, locale, compact = false }: RangeBarProps) {
  const { min_value, expected_value, max_value, confidence_band, unit } = range;
  const spread = max_value - min_value;
  const expectedPos = spread > 0
    ? ((expected_value - min_value) / spread) * 100
    : 50;
  const reasoning = locale === "ar" ? range.reasoning_ar : range.reasoning_en;

  if (compact) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-500">
        <span className="tabular-nums">{formatRangeValue(min_value, unit)}</span>
        <span>—</span>
        <span className="font-semibold text-slate-700 tabular-nums">
          {formatRangeValue(expected_value, unit)}
        </span>
        <span>—</span>
        <span className="tabular-nums">{formatRangeValue(max_value, unit)}</span>
        {confidence_band && (
          <span className="text-slate-400 ml-1">({confidence_band})</span>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {/* Labels row */}
      <div className="flex justify-between text-[10px] text-slate-400">
        <span className="tabular-nums">{formatRangeValue(min_value, unit)}</span>
        <span className="font-semibold text-slate-600 tabular-nums">
          {formatRangeValue(expected_value, unit)}
        </span>
        <span className="tabular-nums">{formatRangeValue(max_value, unit)}</span>
      </div>
      {/* Bar */}
      <div className="relative h-2 bg-slate-100 rounded-full overflow-hidden">
        {/* Fill from min to max */}
        <div className="absolute inset-0 bg-blue-100 rounded-full" />
        {/* Expected marker */}
        <div
          className="absolute top-0 h-full w-1 bg-blue-600 rounded-full"
          style={{ left: `${expectedPos}%`, transform: "translateX(-50%)" }}
        />
      </div>
      {/* Confidence + reasoning */}
      <div className="flex items-center justify-between text-[10px]">
        {confidence_band && (
          <span className="text-slate-400">{confidence_band}</span>
        )}
        {reasoning && (
          <span className="text-slate-400 truncate ml-2">{reasoning}</span>
        )}
      </div>
    </div>
  );
}

export default RangeBar;
