"use client";

/**
 * DecisionReasonCard — Narrative-first decision card.
 *
 * Replaces the metrics-grid approach of DecisionActionCard with:
 *   1. WHY THIS DECISION — plain-language trigger explanation
 *   2. WHY NOW — time-to-act, regime, urgency
 *   3. ECONOMICS — cost vs benefit bar + net value
 *   4. IF NOT EXECUTED — tradeoff / consequence summary
 *
 * The user reads the REASON first, then confirms the ECONOMICS.
 * Decision visible + understandable in 3–5 seconds.
 */

import type { DecisionReasoning } from "@/types/provenance";

type ActionStatus = "PENDING_REVIEW" | "APPROVED" | "EXECUTING";

interface DecisionReasonCardProps {
  rank: number;
  actionTitle: string;
  actionTitleAr: string;
  reasoning: DecisionReasoning;
  costUsd: number;
  lossAvoidedUsd: number;
  confidence: number;
  status: ActionStatus;
  locale: "en" | "ar";
  onSubmitForReview?: (actionId: string) => void;
}

function formatUsd(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

const RANK_COLORS: Record<number, string> = {
  1: "bg-amber-400 text-white",
  2: "bg-slate-400 text-white",
  3: "bg-orange-300 text-white",
};

const STATUS_STYLES: Record<ActionStatus, string> = {
  PENDING_REVIEW: "bg-amber-50 text-amber-700 border-amber-200",
  APPROVED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  EXECUTING: "bg-blue-50 text-blue-700 border-blue-200",
};

const STATUS_LABELS: Record<ActionStatus, Record<string, string>> = {
  PENDING_REVIEW: { en: "Pending Review", ar: "بانتظار المراجعة" },
  APPROVED: { en: "Approved", ar: "معتمد" },
  EXECUTING: { en: "Executing", ar: "قيد التنفيذ" },
};

export function DecisionReasonCard({
  rank,
  actionTitle,
  actionTitleAr,
  reasoning,
  costUsd,
  lossAvoidedUsd,
  confidence,
  status,
  locale,
  onSubmitForReview,
}: DecisionReasonCardProps) {
  const isAr = locale === "ar";
  const title = isAr ? actionTitleAr : actionTitle;
  const netValue = lossAvoidedUsd - costUsd;
  const isNetPositive = netValue > 0;
  const maxBar = Math.max(costUsd, lossAvoidedUsd, 1);

  const whyDecision = isAr ? reasoning.why_this_decision_ar : reasoning.why_this_decision_en;
  const whyNow = isAr ? reasoning.why_now_ar : reasoning.why_now_en;
  const tradeoff = isAr ? reasoning.tradeoff_summary_ar : reasoning.tradeoff_summary_en;

  const rankColor = RANK_COLORS[rank] ?? RANK_COLORS[3];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      {/* Header: Rank + Title + Status */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${rankColor}`}>
            {rank}
          </span>
          <div>
            <h3 className="text-sm font-bold text-slate-800 leading-tight uppercase">
              {title}
            </h3>
            {!isAr && actionTitleAr && (
              <p className="text-[10px] text-slate-400 mt-0.5" dir="rtl">
                {actionTitleAr}
              </p>
            )}
          </div>
        </div>
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${STATUS_STYLES[status]}`}>
          {STATUS_LABELS[status][locale]}
        </span>
      </div>

      {/* WHY THIS DECISION */}
      {whyDecision && (
        <ReasonBlock
          label={isAr ? "لماذا هذا القرار" : "Why This Decision"}
          text={whyDecision}
          accentColor="border-blue-400"
        />
      )}

      {/* WHY NOW */}
      {whyNow && (
        <ReasonBlock
          label={isAr ? "لماذا الآن" : "Why Now"}
          text={whyNow}
          accentColor="border-amber-400"
        />
      )}

      {/* ECONOMICS */}
      <div>
        <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
          {isAr ? "الاقتصاديات" : "Economics"}
        </h4>
        <div className="space-y-1.5">
          <EconomicsRow
            label={isAr ? "التكلفة" : "Cost"}
            value={costUsd}
            maxBar={maxBar}
            color="bg-red-400"
          />
          <EconomicsRow
            label={isAr ? "الخسائر المتجنبة" : "Loss Avoided"}
            value={lossAvoidedUsd}
            maxBar={maxBar}
            color="bg-emerald-500"
          />
        </div>
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100">
          <span className="text-xs text-slate-500">
            {isAr ? "صافي الفائدة" : "Net Benefit"}
          </span>
          <span className={`text-sm font-bold tabular-nums ${isNetPositive ? "text-emerald-700" : "text-red-600"}`}>
            {isNetPositive ? "+" : ""}{formatUsd(netValue)}
          </span>
        </div>
        {/* Confidence bar */}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-[10px] text-slate-400">
            {isAr ? "الثقة" : "Confidence"}
          </span>
          <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${Math.round(confidence * 100)}%` }}
            />
          </div>
          <span className="text-[10px] font-semibold text-slate-600 tabular-nums">
            {Math.round(confidence * 100)}%
          </span>
        </div>
      </div>

      {/* IF NOT EXECUTED */}
      {tradeoff && (
        <div className="px-3 py-2 bg-red-50 border border-red-100 rounded-lg">
          <h4 className="text-[10px] font-semibold text-red-600 uppercase tracking-wider mb-1">
            {isAr ? "في حال عدم التنفيذ" : "If Not Executed"}
          </h4>
          <p className="text-xs text-red-700 leading-relaxed">{tradeoff}</p>
        </div>
      )}

      {/* Submit CTA */}
      {status === "PENDING_REVIEW" && onSubmitForReview && (
        <button
          onClick={() => onSubmitForReview(reasoning.action_id)}
          className="w-full py-2.5 px-4 rounded-lg bg-blue-700 text-white text-sm font-semibold hover:bg-blue-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {isAr ? "إرسال للمراجعة" : "Submit for Review"}
        </button>
      )}
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────

function ReasonBlock({
  label,
  text,
  accentColor,
}: {
  label: string;
  text: string;
  accentColor: string;
}) {
  return (
    <div className={`border-l-2 ${accentColor} pl-3`}>
      <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
        {label}
      </h4>
      <p className="text-xs text-slate-700 leading-relaxed">{text}</p>
    </div>
  );
}

function EconomicsRow({
  label,
  value,
  maxBar,
  color,
}: {
  label: string;
  value: number;
  maxBar: number;
  color: string;
}) {
  const width = maxBar > 0 ? (value / maxBar) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-500 w-24 text-end">{label}</span>
      <div className="flex-1 h-3 bg-slate-100 rounded overflow-hidden">
        <div
          className={`h-full rounded ${color}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-700 tabular-nums w-16 text-end">
        {formatUsd(value)}
      </span>
    </div>
  );
}

export default DecisionReasonCard;
