"use client";

/**
 * ActionTransparencyOverlay — Decision Transparency display for action cards.
 *
 * Renders on each DecisionReasonCard:
 *   - Classification badge (HIGH_VALUE / ACCEPTABLE / LOW_EFFICIENCY / LOSS_INDUCING)
 *   - Cost / Benefit / Net Value / Ratio
 *   - "Why this action?" section
 *   - "Tradeoffs" section
 *   - LOSS_INDUCING red warning (never hidden)
 */

import { useState } from "react";
import type {
  DecisionTransparency,
  OutcomeRecord,
  TrustMemory,
  ConfidenceAdjustment,
} from "@/types/observatory";

interface ActionTransparencyOverlayProps {
  transparency: DecisionTransparency | undefined;
  locale?: "en" | "ar";
  // Sprint 2: Decision Reliability Layer
  outcomeRecord?: OutcomeRecord;
  trustMemory?: TrustMemory;
  confidenceAdjustment?: ConfidenceAdjustment;
}

const CLASSIFICATION_STYLES: Record<string, { bg: string; text: string; border: string; label: string; labelAr: string }> = {
  HIGH_VALUE: {
    bg: "bg-emerald-50",
    text: "text-emerald-800",
    border: "border-emerald-300",
    label: "High Value",
    labelAr: "قيمة عالية",
  },
  ACCEPTABLE: {
    bg: "bg-blue-50",
    text: "text-blue-700",
    border: "border-blue-200",
    label: "Acceptable",
    labelAr: "مقبول",
  },
  LOW_EFFICIENCY: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-300",
    label: "Low Efficiency",
    labelAr: "كفاءة منخفضة",
  },
  LOSS_INDUCING: {
    bg: "bg-red-100",
    text: "text-red-800",
    border: "border-red-400",
    label: "\u26A0 Loss-Inducing",
    labelAr: "\u26A0 مدمر للقيمة",
  },
};

function formatUsd(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `$${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(abs / 1e6).toFixed(0)}M`;
  if (abs >= 1e3) return `$${(abs / 1e3).toFixed(0)}K`;
  return `$${Math.round(abs)}`;
}

export function ActionTransparencyOverlay({
  transparency,
  locale = "en",
  outcomeRecord,
  trustMemory,
  confidenceAdjustment,
}: ActionTransparencyOverlayProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isAr = locale === "ar";

  if (!transparency) return null;

  const cls = CLASSIFICATION_STYLES[transparency.classification] ?? CLASSIFICATION_STYLES.ACCEPTABLE;
  const isLossInducing = transparency.classification === "LOSS_INDUCING";

  return (
    <div className="space-y-2">
      {/* Classification Badge — ALWAYS visible at top */}
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold border ${cls.bg} ${cls.text} ${cls.border}`}
        >
          {isAr ? cls.labelAr : cls.label}
        </span>
        {transparency.cost_benefit_ratio > 0 && (
          <span className="text-[10px] text-slate-500 tabular-nums">
            {isAr ? "النسبة" : "Ratio"}: {transparency.cost_benefit_ratio.toFixed(2)}:1
          </span>
        )}
      </div>

      {/* Loss-Inducing Warning — red, prominent, never hidden */}
      {isLossInducing && (
        <div className="px-3 py-2 bg-red-100 border-2 border-red-400 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 text-lg">{"\u26A0\uFE0F"}</span>
            <p className="text-xs font-bold text-red-800">
              {isAr
                ? "تحذير: هذا الإجراء قد يدمر القيمة. التكلفة تتجاوز الفائدة المتوقعة."
                : "WARNING: This action may destroy value. Cost exceeds projected benefit."}
            </p>
          </div>
        </div>
      )}

      {/* Cost / Benefit / Net Value bars */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-slate-500">{isAr ? "التكلفة" : "Cost"}</span>
          <span className="font-semibold text-red-600 tabular-nums">
            {transparency.cost_formatted}
          </span>
        </div>
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-slate-500">{isAr ? "الفائدة" : "Benefit"}</span>
          <span className="font-semibold text-emerald-600 tabular-nums">
            {transparency.benefit_formatted}
          </span>
        </div>
        <div className="flex items-center justify-between text-[10px] pt-1 border-t border-slate-100">
          <span className="text-slate-600 font-medium">{isAr ? "صافي القيمة" : "Net Value"}</span>
          <span
            className={`font-bold tabular-nums ${
              transparency.is_net_positive ? "text-emerald-700" : "text-red-700"
            }`}
          >
            {transparency.is_net_positive ? "+" : "-"}
            {transparency.net_value_formatted}
          </span>
        </div>
      </div>

      {/* Expandable details */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-[10px] font-semibold text-blue-600 hover:text-blue-800 uppercase tracking-wider flex items-center gap-1"
      >
        <svg
          className={`w-3 h-3 transition-transform ${showDetails ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        {isAr ? "لماذا هذا الإجراء؟" : "Why this action?"}
      </button>

      {showDetails && (
        <div className="space-y-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
          {/* Why Recommended */}
          {transparency.why_recommended.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                {isAr ? "سبب التوصية" : "Why Recommended"}
              </h5>
              <ul className="space-y-1">
                {transparency.why_recommended.map((r, i) => (
                  <li key={i} className="text-slate-600 leading-relaxed pl-3 border-l-2 border-blue-300">
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Tradeoffs */}
          {transparency.tradeoffs.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                {isAr ? "المقايضات" : "Tradeoffs"}
              </h5>
              <ul className="space-y-1">
                {transparency.tradeoffs.map((t, i) => (
                  <li
                    key={i}
                    className={`leading-relaxed pl-3 border-l-2 ${
                      t.startsWith("WARNING") ? "text-red-700 border-red-400 font-medium" : "text-slate-600 border-amber-300"
                    }`}
                  >
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sprint 1.5: Decision Risk Overlay */}
          {transparency.decision_risks && transparency.decision_risks.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                {isAr ? "تقييم المخاطر" : "Risk Assessment"}
              </h5>
              <div className="space-y-1.5">
                {transparency.decision_risks.map((risk, i) => {
                  const severityStyle =
                    risk.severity === "HIGH"
                      ? "bg-red-100 text-red-700 border-red-300"
                      : risk.severity === "MEDIUM"
                        ? "bg-amber-100 text-amber-700 border-amber-300"
                        : "bg-slate-100 text-slate-600 border-slate-300";
                  return (
                    <div key={i} className={`p-2 rounded border ${severityStyle}`}>
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-bold text-[10px]">{risk.severity}</span>
                        <span className="font-semibold">{risk.label}</span>
                      </div>
                      <p className="text-[10px] leading-relaxed opacity-90">{risk.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Sprint 2: Outcome Tracking ── */}
          {outcomeRecord && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                {isAr ? "تتبع النتائج" : "Outcome Tracking"}
              </h5>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">{isAr ? "المتوقع" : "Predicted"}</span>
                  <span className="font-semibold text-slate-700 tabular-nums">{formatUsd(outcomeRecord.predicted_value)}</span>
                </div>
                {outcomeRecord.actual_value != null && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-slate-500">{isAr ? "الفعلي" : "Actual"}</span>
                      <span className="font-semibold text-slate-700 tabular-nums">{formatUsd(outcomeRecord.actual_value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">{isAr ? "الانحراف" : "Deviation"}</span>
                      <span className={`font-bold tabular-nums ${
                        Math.abs(outcomeRecord.deviation_pct ?? 0) <= 15 ? "text-emerald-600" : "text-amber-600"
                      }`}>
                        {outcomeRecord.deviation_pct != null ? `${outcomeRecord.deviation_pct > 0 ? "+" : ""}${outcomeRecord.deviation_pct.toFixed(1)}%` : "—"}
                      </span>
                    </div>
                  </>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-500">{isAr ? "الحالة" : "Status"}</span>
                  <span className={`font-bold ${
                    outcomeRecord.status === "CONFIRMED" ? "text-emerald-600" :
                    outcomeRecord.status === "FAILED" ? "text-red-600" : "text-slate-500"
                  }`}>{outcomeRecord.status}</span>
                </div>
              </div>
            </div>
          )}

          {/* ── Sprint 2: Trust Memory ── */}
          {trustMemory && trustMemory.total_runs > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                {isAr ? "ذاكرة الثقة" : "Trust Memory"}
              </h5>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        trustMemory.trust_score >= 70 ? "bg-emerald-500" :
                        trustMemory.trust_score >= 40 ? "bg-amber-500" : "bg-red-500"
                      }`}
                      style={{ width: `${trustMemory.trust_score}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-bold tabular-nums text-slate-600">{trustMemory.trust_score}/100</span>
                </div>
                <p className="text-[10px] text-slate-500">
                  {isAr
                    ? `${trustMemory.success_count} نجاح من ${trustMemory.total_runs} تشغيل`
                    : `${trustMemory.success_count} of ${trustMemory.total_runs} past runs succeeded`}
                  {trustMemory.failure_count > 0 && (
                    <span className="text-red-500 font-medium">
                      {isAr ? ` — ${trustMemory.failure_count} فشل` : ` — ${trustMemory.failure_count} failed`}
                    </span>
                  )}
                </p>
                {trustMemory.average_deviation !== 0 && (
                  <p className="text-[10px] text-slate-500">
                    {isAr ? "متوسط الانحراف" : "Avg deviation"}: {trustMemory.average_deviation > 0 ? "+" : ""}{trustMemory.average_deviation.toFixed(1)}%
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ── Sprint 2: Confidence Adjustment ── */}
          {confidenceAdjustment && confidenceAdjustment.original_confidence !== confidenceAdjustment.adjusted_confidence && (
            <div className={`p-2 rounded border text-[10px] ${
              confidenceAdjustment.adjusted_confidence < confidenceAdjustment.original_confidence
                ? "bg-amber-50 border-amber-200 text-amber-700"
                : "bg-emerald-50 border-emerald-200 text-emerald-700"
            }`}>
              <div className="flex items-center gap-1.5">
                <span className="font-bold">{isAr ? "ثقة معدّلة" : "Adjusted Confidence"}</span>
                <span className="tabular-nums">{confidenceAdjustment.original_confidence}% → {confidenceAdjustment.adjusted_confidence}%</span>
              </div>
              <p className="mt-0.5 opacity-80">{confidenceAdjustment.adjustment_reason}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ActionTransparencyOverlay;
