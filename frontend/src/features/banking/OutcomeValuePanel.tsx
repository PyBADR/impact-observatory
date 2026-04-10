"use client";

import type { OutcomeReviewContract, DecisionValueAudit, ReviewWindow } from "@/types/banking-intelligence";

const fmt = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }).format(v);

const WINDOW_STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-zinc-700 text-zinc-300",
  OBSERVATION_COLLECTED: "bg-blue-900 text-blue-300",
  ANALYSIS_COMPLETE: "bg-emerald-900 text-emerald-300",
  SKIPPED: "bg-zinc-800 text-zinc-500",
};

const CLASSIFICATION_COLORS: Record<string, string> = {
  better_than_expected: "text-emerald-400",
  as_expected: "text-blue-400",
  worse_than_expected: "text-amber-400",
  significantly_worse: "text-red-400",
  opposite_direction: "text-red-500",
};

function ReviewTimeline({ windows, lang }: { windows: ReviewWindow[]; lang: "en" | "ar" }) {
  const completedCount = windows.filter((w) => w.status === "ANALYSIS_COMPLETE").length;
  const pct = windows.length > 0 ? (completedCount / windows.length) * 100 : 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-400">{lang === "ar" ? "نوافذ المراجعة" : "Review Windows"}</span>
        <span className="text-xs text-zinc-500">{completedCount}/{windows.length} complete</span>
      </div>

      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>

      <div className="grid grid-cols-4 gap-2">
        {windows.map((w) => (
          <div key={w.window_hours} className="rounded-lg bg-zinc-900 border border-zinc-700 p-3 text-center">
            <p className="text-lg font-bold text-zinc-100">{w.window_hours}h</p>
            <span className={`inline-block text-[10px] px-1.5 py-0.5 rounded mt-1 ${WINDOW_STATUS_COLORS[w.status] || WINDOW_STATUS_COLORS.PENDING}`}>
              {w.status.replace(/_/g, " ")}
            </span>
            <p className="text-[10px] text-zinc-500 mt-1">{w.metric_name}</p>
            {w.expected_metric_value != null && (
              <p className="text-xs text-zinc-400 mt-0.5">
                Exp: {w.expected_metric_value.toFixed(1)}
              </p>
            )}
            {w.actual_metric_value != null && (
              <p className="text-xs text-zinc-200 mt-0.5">
                Act: {w.actual_metric_value.toFixed(1)}
              </p>
            )}
            {w.delta_from_expected != null && (
              <p className={`text-xs font-mono mt-0.5 ${w.delta_from_expected < 0 ? "text-emerald-400" : "text-red-400"}`}>
                {w.delta_from_expected > 0 ? "+" : ""}{w.delta_from_expected.toFixed(1)}
              </p>
            )}
            {w.classification && (
              <p className={`text-[10px] mt-1 capitalize ${CLASSIFICATION_COLORS[w.classification] || "text-zinc-400"}`}>
                {w.classification.replace(/_/g, " ")}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ValueBreakdown({ audit, lang }: { audit: DecisionValueAudit; lang: "en" | "ar" }) {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold text-zinc-200">{lang === "ar" ? "تحليل القيمة" : "Value Breakdown"}</h4>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-400">{lang === "ar" ? "الخسائر المتجنبة" : "Gross Loss Avoided"}</span>
          <span className="text-sm font-mono text-emerald-400">{fmt(audit.gross_loss_avoided_usd)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-400">{lang === "ar" ? "تكلفة التنفيذ" : "Implementation Cost"}</span>
          <span className="text-sm font-mono text-red-400">-{fmt(audit.implementation_cost_usd)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-400">{lang === "ar" ? "الآثار الجانبية" : "Side Effect Cost"}</span>
          <span className="text-sm font-mono text-orange-400">-{fmt(audit.side_effect_cost_usd)}</span>
        </div>
        <div className="border-t border-zinc-700 pt-2 flex items-center justify-between">
          <span className="text-sm font-semibold text-zinc-200">{lang === "ar" ? "صافي القيمة" : "Net Value"}</span>
          <span className="text-lg font-bold font-mono text-zinc-100">{fmt(audit.net_value_usd)}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-zinc-900 border border-blue-800 p-3 text-center">
          <span className="text-[10px] text-zinc-500 block">{lang === "ar" ? "معدل حسب الثقة" : "Confidence-Adjusted"}</span>
          <p className="text-xl font-bold text-blue-400 font-mono">{fmt(audit.confidence_adjusted_value_usd)}</p>
          <p className="text-[10px] text-zinc-500 mt-0.5">at {(audit.composite_confidence * 100).toFixed(0)}% confidence</p>
        </div>
        <div className="rounded-lg bg-zinc-900 border border-zinc-700 p-3 text-center">
          <span className="text-[10px] text-zinc-500 block">{lang === "ar" ? "القيمة المحققة" : "Realized Value"}</span>
          {audit.realized_value_usd != null ? (
            <>
              <p className="text-xl font-bold text-zinc-100 font-mono">{fmt(audit.realized_value_usd)}</p>
              {audit.variance_usd != null && (
                <p className={`text-[10px] font-mono mt-0.5 ${audit.variance_usd >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {audit.variance_usd >= 0 ? "+" : ""}{fmt(audit.variance_usd)} variance
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-zinc-500 mt-1">{lang === "ar" ? "في انتظار المراجعة" : "Pending review"}</p>
          )}
        </div>
      </div>

      <div className={`rounded-lg p-3 flex items-start gap-3 ${audit.cfo_defensible ? "bg-emerald-950 border border-emerald-800" : "bg-red-950 border border-red-800"}`}>
        <span className="text-lg">{audit.cfo_defensible ? "\u2713" : "\u2717"}</span>
        <div>
          <p className={`text-sm font-semibold ${audit.cfo_defensible ? "text-emerald-300" : "text-red-300"}`}>
            {audit.cfo_defensible
              ? (lang === "ar" ? "قابل للدفاع أمام المدير المالي" : "CFO Defensible")
              : (lang === "ar" ? "غير قابل للدفاع" : "Not CFO Defensible")}
          </p>
          {audit.defensibility_gaps.length > 0 && (
            <ul className="mt-1 space-y-0.5">
              {audit.defensibility_gaps.map((g, i) => (
                <li key={i} className="text-xs text-red-300">{g}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default function OutcomeValuePanel({
  review,
  audit,
  lang,
}: {
  review?: OutcomeReviewContract;
  audit?: DecisionValueAudit;
  lang: "en" | "ar";
}) {
  if (!review && !audit) {
    return (
      <div className="text-center text-zinc-500 py-8">
        {lang === "ar" ? "لا توجد بيانات مراجعة أو تدقيق" : "No review or audit data available"}
      </div>
    );
  }

  return (
    <div dir={lang === "ar" ? "rtl" : "ltr"} className="space-y-6">
      <h3 className="text-lg font-semibold text-zinc-100">
        {lang === "ar" ? "المراجعة والقيمة" : "Outcome Review & Value Audit"}
      </h3>

      {review && <ReviewTimeline windows={review.windows} lang={lang} />}

      {review?.overall_classification && (
        <div className="rounded-lg bg-zinc-900 border border-zinc-700 p-3">
          <span className="text-xs text-zinc-500">{lang === "ar" ? "التصنيف العام" : "Overall Classification"}</span>
          <p className={`text-sm font-medium capitalize mt-0.5 ${CLASSIFICATION_COLORS[review.overall_classification] || "text-zinc-300"}`}>
            {review.overall_classification.replace(/_/g, " ")}
          </p>
          {review.overall_narrative && (
            <p className="text-xs text-zinc-400 mt-1">{review.overall_narrative}</p>
          )}
        </div>
      )}

      {audit && <ValueBreakdown audit={audit} lang={lang} />}
    </div>
  );
}
