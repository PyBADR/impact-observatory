"use client";

/**
 * MetricWhyCard — Expandable "Why?" explanation for any metric.
 *
 * Sprint 1: Top drivers, reasoning chain, assumptions.
 * Sprint 1.5: Business explanation, confidence meter, data context.
 *
 * Drops into any metric card. Collapses by default. Expand = trust.
 */

import { useState } from "react";
import type {
  MetricExplanation,
  RangeEstimate,
  SensitivityAnalysis,
  ConfidenceAdjustment,
} from "@/types/observatory";

interface MetricWhyCardProps {
  explanation: MetricExplanation | undefined;
  locale?: "en" | "ar";
  // Sprint 2: Decision Reliability Layer
  range?: RangeEstimate;
  sensitivity?: SensitivityAnalysis;
  confidenceAdjustment?: ConfidenceAdjustment;
}

const IMPACT_STYLES: Record<string, { bg: string; text: string }> = {
  HIGH: { bg: "bg-red-100", text: "text-red-700" },
  MEDIUM: { bg: "bg-amber-100", text: "text-amber-700" },
  LOW: { bg: "bg-slate-100", text: "text-slate-600" },
};

const FRESHNESS_STYLES: Record<string, { bg: string; text: string; label: string; labelAr: string }> = {
  LIVE: { bg: "bg-emerald-100", text: "text-emerald-700", label: "Live", labelAr: "مباشر" },
  RECENT: { bg: "bg-blue-100", text: "text-blue-700", label: "Recent", labelAr: "حديث" },
  SIMULATED: { bg: "bg-purple-100", text: "text-purple-700", label: "Simulated", labelAr: "محاكاة" },
  HISTORICAL: { bg: "bg-slate-100", text: "text-slate-600", label: "Historical", labelAr: "تاريخي" },
};

function ConfidenceMeter({ value, locale }: { value: number; locale: string }) {
  const isAr = locale === "ar";
  const color =
    value >= 75 ? "bg-emerald-500" : value >= 50 ? "bg-amber-500" : "bg-red-500";
  const label =
    value >= 75
      ? isAr ? "عالية" : "High"
      : value >= 50
        ? isAr ? "متوسطة" : "Moderate"
        : isAr ? "منخفضة" : "Low";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-[10px] font-bold tabular-nums text-slate-600">{value}%</span>
      <span className="text-[10px] text-slate-500">({label})</span>
    </div>
  );
}

export function MetricWhyCard({ explanation, locale = "en", range, sensitivity, confidenceAdjustment }: MetricWhyCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!explanation) return null;

  const isAr = locale === "ar";
  const drivers = explanation.drivers.slice(0, 3);
  const maxPct = Math.max(...drivers.map((d) => d.contribution_pct), 1);
  const biz = explanation.business_explanation;
  const conf = explanation.confidence;
  const confReasons = explanation.confidence_reasons;
  const ctx = explanation.data_context;

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[10px] font-semibold text-blue-600 hover:text-blue-800 transition-colors uppercase tracking-wider"
      >
        <svg
          className={`w-3 h-3 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        {isAr ? "لماذا هذه القيمة؟" : "Why this value?"}
      </button>

      {expanded && (
        <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-xs">

          {/* ── Sprint 1.5: Business Explanation (CRO-readable) ── */}
          {biz && biz.summary && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "الملخص التنفيذي" : "Business Summary"}
              </h5>
              <p className="text-slate-700 leading-relaxed mb-2">{biz.summary}</p>
              {biz.drivers.length > 0 && (
                <div className="space-y-1.5">
                  {biz.drivers.map((bd, i) => {
                    const style = IMPACT_STYLES[bd.impact] ?? IMPACT_STYLES.LOW;
                    return (
                      <div key={i} className="flex items-start gap-2">
                        <span className={`shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold ${style.bg} ${style.text}`}>
                          {bd.impact}
                        </span>
                        <div>
                          <span className="font-medium text-slate-700">{bd.label}</span>
                          <span className="text-slate-500"> — {bd.explanation}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ── Sprint 2: Range Estimate ── */}
          {range && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "النطاق المتوقع" : "Expected Range"}
              </h5>
              <div className="relative h-4 bg-slate-200 rounded-full overflow-visible">
                {/* Low–High band */}
                {(() => {
                  const spread = range.high - range.low || 1;
                  const basePos = ((range.base - range.low) / spread) * 100;
                  return (
                    <>
                      <div className="absolute inset-y-0 bg-blue-200 rounded-full" style={{ left: "0%", right: "0%" }} />
                      <div
                        className="absolute top-0 bottom-0 w-1.5 bg-blue-600 rounded-full"
                        style={{ left: `${Math.max(0, Math.min(100, basePos))}%` }}
                        title={`Base: ${typeof range.base === "number" && range.base > 1000 ? `$${(range.base / 1e6).toFixed(0)}M` : range.base.toFixed(2)}`}
                      />
                    </>
                  );
                })()}
              </div>
              <div className="flex justify-between mt-1 text-[9px] text-slate-500 tabular-nums">
                <span>{typeof range.low === "number" && range.low > 1000 ? `$${(range.low / 1e6).toFixed(0)}M` : range.low.toFixed(2)}</span>
                <span className="font-bold text-blue-700">{typeof range.base === "number" && range.base > 1000 ? `$${(range.base / 1e6).toFixed(0)}M` : range.base.toFixed(2)}</span>
                <span>{typeof range.high === "number" && range.high > 1000 ? `$${(range.high / 1e6).toFixed(0)}M` : range.high.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[9px] px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded font-medium">{range.method}</span>
                <span className="text-[9px] text-slate-400">{range.confidence}% {isAr ? "ثقة" : "confidence"}</span>
              </div>
              {range.notes && range.notes.length > 0 && (
                <ul className="mt-1 space-y-0.5">
                  {range.notes.map((n, i) => (
                    <li key={i} className="text-[9px] text-slate-400 pl-2 border-l border-slate-200">{n}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* ── Sprint 2: Sensitivity ── */}
          {sensitivity && sensitivity.points.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "تحليل الحساسية" : "Sensitivity"}: {sensitivity.variable_tested}
              </h5>
              <div className="space-y-0.5">
                {sensitivity.points.map((pt, i) => {
                  const isBaseline = Math.abs(pt.output_value - sensitivity.baseline_value) < sensitivity.baseline_value * 0.01;
                  const maxOut = Math.max(...sensitivity.points.map((p) => p.output_value), 1);
                  const barPct = (pt.output_value / maxOut) * 100;
                  return (
                    <div key={i} className="flex items-center gap-2">
                      <span className="w-8 text-[9px] text-slate-500 tabular-nums text-right shrink-0">{(pt.input_value * 100).toFixed(0)}%</span>
                      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${isBaseline ? "bg-blue-600" : "bg-slate-400"}`}
                          style={{ width: `${barPct}%` }}
                        />
                      </div>
                      <span className={`w-14 text-[9px] tabular-nums text-right shrink-0 ${isBaseline ? "font-bold text-blue-700" : "text-slate-500"}`}>
                        {pt.output_value > 1000 ? `$${(pt.output_value / 1e6).toFixed(0)}M` : pt.output_value.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
              </div>
              {sensitivity.trend && (
                <p className="text-[9px] text-slate-400 mt-1">{isAr ? "الاتجاه" : "Trend"}: {sensitivity.trend}</p>
              )}
            </div>
          )}

          {/* ── Sprint 1.5: Confidence Meter ── */}
          {conf !== undefined && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "مستوى الثقة" : "Confidence Level"}
              </h5>
              <ConfidenceMeter value={conf} locale={locale} />
              {confReasons && confReasons.length > 0 && (
                <ul className="mt-1.5 space-y-0.5">
                  {confReasons.map((r, i) => (
                    <li key={i} className="text-[10px] text-slate-500 pl-2 border-l border-slate-300">
                      {r}
                    </li>
                  ))}
                </ul>
              )}
              {/* Sprint 2: Confidence Adjustment */}
              {confidenceAdjustment && confidenceAdjustment.original_confidence !== confidenceAdjustment.adjusted_confidence && (
                <div className={`mt-1.5 p-1.5 rounded text-[9px] ${
                  confidenceAdjustment.adjusted_confidence < confidenceAdjustment.original_confidence
                    ? "bg-amber-50 text-amber-700" : "bg-emerald-50 text-emerald-700"
                }`}>
                  {confidenceAdjustment.original_confidence}% → {confidenceAdjustment.adjusted_confidence}% — {confidenceAdjustment.adjustment_reason}
                </div>
              )}
            </div>
          )}

          {/* ── Sprint 1.5: Data Context ── */}
          {ctx && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "مصدر البيانات" : "Data Source"}
              </h5>
              <div className="flex items-center gap-2 mb-1">
                {(() => {
                  const fr = FRESHNESS_STYLES[ctx.freshness_label] ?? FRESHNESS_STYLES.SIMULATED;
                  return (
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold ${fr.bg} ${fr.text}`}>
                      {isAr ? fr.labelAr : fr.label}
                    </span>
                  );
                })()}
                <span className="text-[10px] text-slate-500">{ctx.source_type}</span>
              </div>
              <p className="text-[10px] text-slate-600">{ctx.source_summary}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {isAr ? "الفترة المرجعية" : "Period"}: {ctx.reference_period}
              </p>
            </div>
          )}

          {/* ── Sprint 1: Technical Drivers ── */}
          <div>
            <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              {isAr ? "العوامل الرئيسية" : "Top Drivers"}
            </h5>
            <div className="space-y-1.5">
              {drivers.map((d, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-slate-700 font-medium">{d.label}</span>
                    <span className="text-slate-500 tabular-nums">{d.contribution_pct.toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(d.contribution_pct / maxPct) * 100}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5">{d.rationale}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Reasoning Chain */}
          {explanation.reasoning_chain.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "سلسلة الاستدلال" : "Reasoning Chain"}
              </h5>
              <ol className="space-y-1 list-decimal list-inside">
                {explanation.reasoning_chain.map((step, i) => (
                  <li key={i} className="text-slate-600 leading-relaxed">
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Assumptions */}
          {explanation.assumptions.length > 0 && (
            <div>
              <h5 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {isAr ? "الافتراضات" : "Assumptions"}
              </h5>
              <div className="space-y-0.5">
                {explanation.assumptions.map((a, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-slate-500 shrink-0">{a.label}:</span>
                    <span className="text-slate-700 font-mono text-[10px]">
                      {typeof a.value === "object" ? JSON.stringify(a.value) : String(a.value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MetricWhyCard;
