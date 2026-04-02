"use client";

/**
 * Impact Observatory | مرصد الأثر — KPI Card
 * Top-row metric card with severity coloring and trend indicator.
 */

type Severity = "critical" | "severe" | "high" | "medium" | "low" | "normal";
type Trend = "up" | "down" | "stable";

interface KPICardProps {
  label: string;
  labelAr: string;
  value: string;
  severity?: Severity;
  sublabel?: string;
  trend?: Trend;
  locale: "en" | "ar";
}

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "var(--severity-critical, #DC2626)",
  severe: "var(--severity-severe, #EA580C)",
  high: "var(--severity-high, #D97706)",
  medium: "var(--severity-medium, #65A30D)",
  low: "var(--severity-low, #0EA5E9)",
  normal: "var(--color-accent, #1D4ED8)",
};

const SEVERITY_BG: Record<Severity, string> = {
  critical: "bg-red-50 text-red-700",
  severe: "bg-orange-50 text-orange-700",
  high: "bg-amber-50 text-amber-700",
  medium: "bg-lime-50 text-lime-700",
  low: "bg-sky-50 text-sky-700",
  normal: "bg-slate-50 text-slate-700",
};

const TREND_ICONS: Record<Trend, { symbol: string; color: string }> = {
  up: { symbol: "\u2191", color: "text-red-600" },
  down: { symbol: "\u2193", color: "text-green-600" },
  stable: { symbol: "\u2192", color: "text-slate-500" },
};

export function KPICard({
  label,
  labelAr,
  value,
  severity = "normal",
  sublabel,
  trend,
  locale,
}: KPICardProps) {
  const displayLabel = locale === "ar" ? labelAr : label;
  const borderColor = SEVERITY_COLORS[severity];

  return (
    <div
      className="bg-white rounded-xl border border-io-border shadow-sm p-5 flex flex-col gap-2 relative overflow-hidden"
      style={{ borderInlineStartWidth: "4px", borderInlineStartColor: borderColor }}
    >
      {/* Label */}
      <span className="text-xs font-medium uppercase tracking-wider text-io-secondary">
        {displayLabel}
      </span>

      {/* Value + Trend */}
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold tracking-tight text-io-primary font-sans tabular-nums">
          {value}
        </span>
        {trend && (
          <span className={`text-lg font-semibold ${TREND_ICONS[trend].color}`}>
            {TREND_ICONS[trend].symbol}
          </span>
        )}
      </div>

      {/* Severity badge + sublabel */}
      <div className="flex items-center gap-2 mt-1">
        {severity !== "normal" && (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${SEVERITY_BG[severity]}`}
          >
            {severity}
          </span>
        )}
        {sublabel && (
          <span className="text-xs text-io-secondary">{sublabel}</span>
        )}
      </div>
    </div>
  );
}

export default KPICard;
