"use client";

/**
 * Impact Observatory | مرصد الأثر — Financial Impact Panel
 * Large panel showing loss headline, sector exposure bars, propagation summary.
 */

interface FinancialImpactPanelProps {
  loss_usd: number;
  loss_baseline_usd: number;
  peak_loss_day: number;
  duration_days: number;
  liquidity_breach_hours?: number;
  sector_exposure: Record<string, number>;
  severity_code: string;
  locale: "en" | "ar";
}

function formatLoss(usd: number): string {
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(1)}B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)}M`;
  if (usd >= 1e3) return `$${(usd / 1e3).toFixed(0)}K`;
  return `$${Math.round(usd)}`;
}

function formatHours(h: number): string {
  if (h >= 24) return `${Math.round(h / 24)}d`;
  return `${Math.round(h)}h`;
}

const SEVERITY_BG: Record<string, string> = {
  CRITICAL: "bg-red-100 text-red-800",
  SEVERE: "bg-orange-100 text-orange-800",
  HIGH: "bg-amber-100 text-amber-800",
  ELEVATED: "bg-orange-50 text-orange-700",
  MEDIUM: "bg-lime-100 text-lime-800",
  MODERATE: "bg-yellow-50 text-yellow-700",
  LOW: "bg-sky-100 text-sky-800",
  NOMINAL: "bg-slate-100 text-slate-700",
};

const SECTOR_LABELS_EN: Record<string, string> = {
  energy: "Energy",
  maritime: "Maritime",
  aviation: "Aviation",
  banking: "Banking",
  insurance: "Insurance",
  fintech: "Fintech",
  trade: "Trade",
  logistics: "Logistics",
  infrastructure: "Infrastructure",
};

const SECTOR_LABELS_AR: Record<string, string> = {
  energy: "\u0627\u0644\u0637\u0627\u0642\u0629",
  maritime: "\u0627\u0644\u0646\u0642\u0644 \u0627\u0644\u0628\u062D\u0631\u064A",
  aviation: "\u0627\u0644\u0637\u064A\u0631\u0627\u0646",
  banking: "\u0627\u0644\u0628\u0646\u0648\u0643",
  insurance: "\u0627\u0644\u062A\u0623\u0645\u064A\u0646",
  fintech: "\u0627\u0644\u062A\u0642\u0646\u064A\u0629 \u0627\u0644\u0645\u0627\u0644\u064A\u0629",
  trade: "\u0627\u0644\u062A\u062C\u0627\u0631\u0629",
  logistics: "\u0627\u0644\u0644\u0648\u062C\u0633\u062A\u064A\u0627\u062A",
  infrastructure: "\u0627\u0644\u0628\u0646\u064A\u0629 \u0627\u0644\u062A\u062D\u062A\u064A\u0629",
};

const BAR_COLORS = [
  "bg-io-accent",
  "bg-blue-500",
  "bg-blue-400",
  "bg-sky-400",
  "bg-sky-300",
  "bg-slate-400",
  "bg-slate-300",
  "bg-slate-200",
];

export function FinancialImpactPanel({
  loss_usd,
  loss_baseline_usd,
  peak_loss_day,
  duration_days,
  liquidity_breach_hours,
  sector_exposure,
  severity_code,
  locale,
}: FinancialImpactPanelProps) {
  const sectorLabels = locale === "ar" ? SECTOR_LABELS_AR : SECTOR_LABELS_EN;
  const severityBg = SEVERITY_BG[severity_code.toUpperCase()] ?? SEVERITY_BG.NOMINAL;

  // Sort sectors by exposure descending
  const sortedSectors = Object.entries(sector_exposure)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8);

  const maxExposure = sortedSectors.length > 0 ? sortedSectors[0][1] : 1;
  const lossRatio = loss_baseline_usd > 0 ? loss_usd / loss_baseline_usd : 0;

  return (
    <div className="bg-white rounded-xl border border-io-border shadow-sm p-6 flex flex-col gap-5 h-full">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-io-secondary uppercase tracking-wide">
            {locale === "ar" ? "\u0627\u0644\u0623\u062B\u0631 \u0627\u0644\u0645\u0627\u0644\u064A" : "Financial Impact"}
          </h2>
          <div className="mt-2 flex items-baseline gap-3">
            <span className="text-4xl font-bold text-io-primary tabular-nums">
              {formatLoss(loss_usd)}
            </span>
            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold uppercase ${severityBg}`}>
              {severity_code}
            </span>
          </div>
        </div>
      </div>

      {/* Quick stats row */}
      <div className="grid grid-cols-3 gap-4 py-3 border-y border-io-border">
        <div>
          <span className="text-xs text-io-secondary">
            {locale === "ar" ? "\u064A\u0648\u0645 \u0627\u0644\u0630\u0631\u0648\u0629" : "Peak Day"}
          </span>
          <p className="text-sm font-semibold text-io-primary">
            {locale === "ar"
              ? `\u0627\u0644\u064A\u0648\u0645 ${peak_loss_day} \u0645\u0646 ${duration_days}`
              : `Day ${peak_loss_day} of ${duration_days}`}
          </p>
        </div>
        <div>
          <span className="text-xs text-io-secondary">
            {locale === "ar" ? "\u0646\u0633\u0628\u0629 \u0627\u0644\u062E\u0633\u0627\u0631\u0629" : "Loss Ratio"}
          </span>
          <p className="text-sm font-semibold text-io-primary">
            {(lossRatio * 100).toFixed(1)}%
          </p>
        </div>
        {liquidity_breach_hours !== undefined && liquidity_breach_hours < Infinity && (
          <div>
            <span className="text-xs text-io-secondary">
              {locale === "ar" ? "\u0643\u0633\u0631 \u0627\u0644\u0633\u064A\u0648\u0644\u0629" : "Liquidity Breach"}
            </span>
            <p className="text-sm font-semibold text-red-600">
              {formatHours(liquidity_breach_hours)}
            </p>
          </div>
        )}
      </div>

      {/* Sector exposure bars */}
      <div>
        <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wide mb-3">
          {locale === "ar" ? "\u062A\u0639\u0631\u0636 \u0627\u0644\u0642\u0637\u0627\u0639\u0627\u062A" : "Sector Exposure"}
        </h3>
        <div className="space-y-2.5">
          {sortedSectors.map(([sector, exposure], idx) => {
            const barWidth = maxExposure > 0 ? (exposure / maxExposure) * 100 : 0;
            const barColor = BAR_COLORS[idx] ?? BAR_COLORS[BAR_COLORS.length - 1];
            return (
              <div key={sector} className="flex items-center gap-3">
                <span className="text-xs text-io-secondary w-24 flex-shrink-0 truncate text-end">
                  {sectorLabels[sector] ?? sector}
                </span>
                <div className="flex-1 h-3 bg-io-bg rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${barColor}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-io-primary tabular-nums w-16 text-end">
                  {formatLoss(exposure)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Propagation summary */}
      <div className="mt-auto pt-3 border-t border-io-border">
        <p className="text-xs text-io-secondary leading-relaxed">
          {locale === "ar"
            ? `\u0633\u064A\u0646\u0627\u0631\u064A\u0648 \u0645\u062F\u062A\u0647 ${duration_days} \u064A\u0648\u0645 \u0628\u0645\u0633\u062A\u0648\u0649 ${severity_code}. \u0627\u0644\u0630\u0631\u0648\u0629 \u0641\u064A \u0627\u0644\u064A\u0648\u0645 ${peak_loss_day}. \u062A\u0623\u062B\u0631 ${sortedSectors.length} \u0642\u0637\u0627\u0639\u0627\u062A \u0628\u062E\u0633\u0627\u0631\u0629 \u0625\u062C\u0645\u0627\u0644\u064A\u0629 ${formatLoss(loss_usd)}.`
            : `${duration_days}-day ${severity_code} scenario. Peak impact at Day ${peak_loss_day}. ${sortedSectors.length} sectors affected with ${formatLoss(loss_usd)} total projected loss.`}
        </p>
      </div>
    </div>
  );
}

export default FinancialImpactPanel;
