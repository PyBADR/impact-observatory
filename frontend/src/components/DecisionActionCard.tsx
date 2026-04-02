"use client";

/**
 * Impact Observatory | مرصد الأثر — Decision Action Card
 * Ranked action card with human-in-the-loop review button.
 */

type ActionStatus = "PENDING_REVIEW" | "APPROVED" | "EXECUTING";

interface DecisionActionCardProps {
  rank: 1 | 2 | 3;
  actionId: string;
  priority_score: number;
  title_en: string;
  title_ar: string;
  urgency: number;
  value: number;
  time_to_act_hours: number;
  cost_usd: number;
  loss_avoided_usd: number;
  status: ActionStatus;
  locale: "en" | "ar";
  onSubmitForReview: (actionId: string) => void;
}

const RANK_STYLES: Record<number, { bg: string; border: string; label: string }> = {
  1: { bg: "bg-amber-50", border: "border-amber-300", label: "bg-amber-400 text-white" },
  2: { bg: "bg-slate-50", border: "border-slate-300", label: "bg-slate-400 text-white" },
  3: { bg: "bg-orange-50", border: "border-orange-300", label: "bg-orange-300 text-white" },
};

const STATUS_STYLES: Record<ActionStatus, string> = {
  PENDING_REVIEW: "bg-amber-50 text-amber-700 border-amber-200",
  APPROVED: "bg-green-50 text-green-700 border-green-200",
  EXECUTING: "bg-blue-50 text-blue-700 border-blue-200",
};

const STATUS_LABELS: Record<ActionStatus, Record<string, string>> = {
  PENDING_REVIEW: { en: "Pending Review", ar: "\u0628\u0627\u0646\u062A\u0638\u0627\u0631 \u0627\u0644\u0645\u0631\u0627\u062C\u0639\u0629" },
  APPROVED: { en: "Approved", ar: "\u0645\u0639\u062A\u0645\u062F" },
  EXECUTING: { en: "Executing", ar: "\u0642\u064A\u062F \u0627\u0644\u062A\u0646\u0641\u064A\u0630" },
};

function formatLoss(usd: number): string {
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(1)}B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)}M`;
  if (usd >= 1e3) return `$${(usd / 1e3).toFixed(0)}K`;
  return `$${Math.round(usd)}`;
}

function formatPct(n: number): string {
  return `${(n * 100).toFixed(0)}%`;
}

function formatHours(h: number): string {
  if (h >= 24) return `${Math.round(h / 24)}d`;
  return `${Math.round(h)}h`;
}

export function DecisionActionCard({
  rank,
  actionId,
  priority_score,
  title_en,
  title_ar,
  urgency,
  value,
  time_to_act_hours,
  cost_usd,
  loss_avoided_usd,
  status,
  locale,
  onSubmitForReview,
}: DecisionActionCardProps) {
  const title = locale === "ar" ? title_ar : title_en;
  const rankStyle = RANK_STYLES[rank] ?? RANK_STYLES[3];
  const priorityWidth = Math.min(100, Math.max(0, Math.round(priority_score * 100)));

  const priorityColor =
    priority_score >= 0.7
      ? "bg-red-500"
      : priority_score >= 0.4
        ? "bg-amber-500"
        : "bg-blue-500";

  return (
    <div
      className={`rounded-xl border shadow-sm p-5 flex flex-col gap-3 ${rankStyle.bg} ${rankStyle.border}`}
    >
      {/* Header: Rank badge + Title + Status */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${rankStyle.label}`}
          >
            {rank}
          </span>
          <div>
            <h3 className="text-sm font-semibold text-io-primary leading-tight">
              {title}
            </h3>
            <span className="text-xs text-io-secondary">
              {locale === "ar" ? "\u0627\u0644\u0623\u0648\u0644\u0648\u064A\u0629" : "Priority"}: {formatPct(priority_score)}
            </span>
          </div>
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${STATUS_STYLES[status]}`}
        >
          {STATUS_LABELS[status][locale]}
        </span>
      </div>

      {/* Priority bar */}
      <div className="w-full">
        <div className="w-full h-2 bg-white/60 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${priorityColor}`}
            style={{ width: `${priorityWidth}%` }}
          />
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
        <div>
          <span className="text-io-secondary">
            {locale === "ar" ? "\u0627\u0644\u0627\u0633\u062A\u0639\u062C\u0627\u0644" : "Urgency"}
          </span>
          <p className="font-semibold text-io-primary">{formatPct(urgency)}</p>
        </div>
        <div>
          <span className="text-io-secondary">
            {locale === "ar" ? "\u0627\u0644\u0642\u064A\u0645\u0629" : "Value"}
          </span>
          <p className="font-semibold text-io-primary">{formatPct(value)}</p>
        </div>
        <div>
          <span className="text-io-secondary">
            {locale === "ar" ? "\u0648\u0642\u062A \u0627\u0644\u062A\u0646\u0641\u064A\u0630" : "Time to Act"}
          </span>
          <p className="font-semibold text-io-primary">{formatHours(time_to_act_hours)}</p>
        </div>
        <div>
          <span className="text-io-secondary">
            {locale === "ar" ? "\u0627\u0644\u062A\u0643\u0644\u0641\u0629" : "Cost"}
          </span>
          <p className="font-semibold text-io-primary">{formatLoss(cost_usd)}</p>
        </div>
        <div className="col-span-2">
          <span className="text-io-secondary">
            {locale === "ar" ? "\u0627\u0644\u062E\u0633\u0627\u0626\u0631 \u0627\u0644\u0645\u062A\u062C\u0646\u0628\u0629" : "Loss Avoided"}
          </span>
          <p className="font-semibold text-green-700">{formatLoss(loss_avoided_usd)}</p>
        </div>
      </div>

      {/* Submit for Review — only visible when PENDING_REVIEW */}
      {status === "PENDING_REVIEW" && (
        <button
          onClick={() => onSubmitForReview(actionId)}
          className="mt-1 w-full py-2 px-4 rounded-lg bg-io-accent text-white text-sm font-semibold hover:bg-blue-800 transition-colors focus:outline-none focus:ring-2 focus:ring-io-accent focus:ring-offset-2"
        >
          {locale === "ar"
            ? "\u0625\u0631\u0633\u0627\u0644 \u0644\u0644\u0645\u0631\u0627\u062C\u0639\u0629"
            : "Submit for Review"}
        </button>
      )}
    </div>
  );
}

export default DecisionActionCard;
