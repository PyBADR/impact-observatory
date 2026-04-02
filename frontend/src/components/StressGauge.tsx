"use client";

/**
 * Impact Observatory | مرصد الأثر — Sector Stress Gauge
 * SVG arc gauge for banking/insurance/fintech stress scores.
 */

interface StressGaugeProps {
  sector: "banking" | "insurance" | "fintech";
  sectorLabel: string;
  sectorLabelAr: string;
  score: number;
  classification: string;
  indicators: string[];
  indicatorsAr: string[];
  locale: "en" | "ar";
}

function getScoreColor(score: number): string {
  if (score >= 90) return "var(--severity-critical, #DC2626)";
  if (score >= 75) return "var(--severity-severe, #EA580C)";
  if (score >= 60) return "var(--severity-high, #D97706)";
  if (score >= 40) return "var(--severity-medium, #65A30D)";
  return "var(--severity-low, #0EA5E9)";
}

function getClassificationBg(classification: string): string {
  const upper = classification.toUpperCase();
  if (upper === "CRITICAL") return "bg-red-50 text-red-700";
  if (upper === "ELEVATED") return "bg-orange-50 text-orange-700";
  if (upper === "MODERATE") return "bg-amber-50 text-amber-700";
  if (upper === "LOW") return "bg-green-50 text-green-700";
  return "bg-slate-50 text-slate-700";
}

const SECTOR_ICONS: Record<string, string> = {
  banking: "\uD83C\uDFE6",
  insurance: "\uD83D\uDEE1\uFE0F",
  fintech: "\uD83D\uDCB3",
};

export function StressGauge({
  sector,
  sectorLabel,
  sectorLabelAr,
  score,
  classification,
  indicators,
  indicatorsAr,
  locale,
}: StressGaugeProps) {
  const displayLabel = locale === "ar" ? sectorLabelAr : sectorLabel;
  const displayIndicators = locale === "ar" ? indicatorsAr : indicators;
  const color = getScoreColor(score);
  const clampedScore = Math.min(100, Math.max(0, Math.round(score)));

  // Arc gauge SVG parameters
  const size = 120;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;

  // Arc from 135deg to 405deg (270deg sweep)
  const startAngle = 135;
  const endAngle = 405;
  const sweepAngle = endAngle - startAngle;
  const scoreAngle = startAngle + (sweepAngle * clampedScore) / 100;

  const polarToCartesian = (angle: number) => {
    const rad = ((angle - 90) * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  };

  const describeArc = (start: number, end: number) => {
    const s = polarToCartesian(start);
    const e = polarToCartesian(end);
    const largeArc = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${largeArc} 1 ${e.x} ${e.y}`;
  };

  const bgArc = describeArc(startAngle, endAngle);
  const valueArc =
    clampedScore > 0 ? describeArc(startAngle, scoreAngle) : "";

  return (
    <div className="bg-white rounded-xl border border-io-border shadow-sm p-4 flex flex-col items-center gap-3">
      {/* Sector label */}
      <div className="flex items-center gap-2">
        <span className="text-lg">{SECTOR_ICONS[sector]}</span>
        <span className="text-sm font-semibold text-io-primary uppercase tracking-wide">
          {displayLabel}
        </span>
      </div>

      {/* SVG Arc Gauge */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background arc */}
          <path
            d={bgArc}
            fill="none"
            stroke="var(--border, #E2E8F0)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Value arc */}
          {valueArc && (
            <path
              d={valueArc}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />
          )}
        </svg>
        {/* Score number centered */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-2xl font-bold tabular-nums"
            style={{ color }}
          >
            {clampedScore}
          </span>
          <span className="text-xs text-io-secondary">/100</span>
        </div>
      </div>

      {/* Classification badge */}
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${getClassificationBg(classification)}`}
      >
        {classification}
      </span>

      {/* Indicators */}
      <div className="w-full space-y-1">
        {displayIndicators.slice(0, 2).map((indicator, idx) => (
          <div
            key={idx}
            className="text-xs text-io-secondary flex items-center gap-1.5"
          >
            <span
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            {indicator}
          </div>
        ))}
      </div>
    </div>
  );
}

export default StressGauge;
