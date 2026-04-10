"use client";

/**
 * MetricExplainer — "Why This Number" popover.
 *
 * Appears on click of any bold metric. Shows:
 *   1. Factor breakdown (horizontal bars with percentages)
 *   2. Range bar (min — expected — max)
 *   3. Data basis (freshness badge + analog reference)
 *   4. Full formula (hidden by default, expand on click)
 *
 * This is the single most important UX component in the provenance layer.
 * It transforms every number from "black box" to "transparent + traceable."
 */

import { useState, useRef, useEffect } from "react";
import type {
  MetricFactorBreakdown,
  MetricRange,
  MetricProvenance,
  DataBasis,
} from "@/types/provenance";
import { FactorBar } from "./FactorBar";
import { RangeBar } from "./RangeBar";
import { FreshnessBadge } from "./FreshnessBadge";

interface MetricExplainerProps {
  metricName: string;
  breakdown?: MetricFactorBreakdown;
  range?: MetricRange;
  provenance?: MetricProvenance;
  basis?: DataBasis;
  locale: "en" | "ar";
  isOpen: boolean;
  onClose: () => void;
  anchorRef?: React.RefObject<HTMLElement | null>;
}

export function MetricExplainer({
  metricName,
  breakdown,
  range,
  provenance,
  basis,
  locale,
  isOpen,
  onClose,
  anchorRef,
}: MetricExplainerProps) {
  const [showFormula, setShowFormula] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    function handleClick(e: MouseEvent) {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target as Node) &&
        anchorRef?.current &&
        !anchorRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [isOpen, onClose, anchorRef]);

  if (!isOpen) return null;

  const displayName = locale === "ar"
    ? (provenance?.metric_name_ar || breakdown?.metric_name_ar || metricName)
    : metricName.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  const maxPct = breakdown?.factors?.length
    ? Math.max(...breakdown.factors.map(f => f.contribution_pct))
    : 100;

  return (
    <div
      ref={panelRef}
      className="absolute z-50 w-[380px] bg-white rounded-xl border border-slate-200 shadow-xl p-5 space-y-4"
      style={{ top: "100%", left: 0, marginTop: 8 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800">{displayName}</h3>
          {provenance && (
            <p className="text-xs text-slate-400 mt-0.5">
              {provenance.unit} · {provenance.time_horizon}
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 text-sm leading-none"
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      {/* Section 1: Factor Breakdown */}
      {breakdown && breakdown.factors.length > 0 && (
        <div>
          <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            {locale === "ar" ? "لماذا هذا الرقم" : "Why This Number"}
          </h4>
          <div className="space-y-1.5">
            {breakdown.factors.map((factor, idx) => (
              <FactorBar
                key={factor.factor_name}
                factor={factor}
                index={idx}
                maxPct={maxPct}
                unit={breakdown.unit}
                locale={locale}
              />
            ))}
          </div>
          <p className="text-[10px] text-slate-400 mt-1.5">
            {Math.round(breakdown.coverage_pct)}%{" "}
            {locale === "ar" ? "من القيمة مفسّرة" : "of value explained"}
          </p>
        </div>
      )}

      {/* Section 2: Range */}
      {range && (
        <div>
          <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            {locale === "ar" ? "النطاق المتوقع" : "Expected Range"}
          </h4>
          <RangeBar range={range} locale={locale} />
        </div>
      )}

      {/* Section 3: Data Basis */}
      {basis && (
        <div>
          <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            {locale === "ar" ? "أساس البيانات" : "Data Basis"}
          </h4>
          <div className="flex items-start gap-2">
            <FreshnessBadge basis={basis} locale={locale} showLabel />
            {basis.analog_event && (
              <span className="text-[10px] text-slate-500">
                {basis.analog_event} ({basis.analog_period})
                {basis.analog_relevance > 0 && (
                  <> · {Math.round(basis.analog_relevance * 100)}%{" "}
                    {locale === "ar" ? "ملاءمة" : "match"}</>
                )}
              </span>
            )}
          </div>
          {basis.freshness_weak && (
            <p className="text-[10px] text-amber-600 mt-1">
              ⚠ {locale === "ar"
                ? "معايرة محدودة — تعامل مع المخرجات كمؤشرات"
                : "Limited calibration — treat outputs as indicative"}
            </p>
          )}
        </div>
      )}

      {/* Section 4: Formula (collapsed by default) */}
      {provenance?.formula && (
        <div>
          <button
            onClick={() => setShowFormula(!showFormula)}
            className="text-[10px] text-blue-600 hover:text-blue-800 font-medium"
          >
            {showFormula
              ? (locale === "ar" ? "▾ إخفاء الصيغة" : "▾ Hide formula")
              : (locale === "ar" ? "▸ عرض الصيغة الكاملة" : "▸ Show full formula")}
          </button>
          {showFormula && (
            <div className="mt-1.5 p-2 bg-slate-50 rounded text-[10px] text-slate-600 font-mono leading-relaxed">
              {provenance.formula}
              {provenance.confidence_notes && (
                <p className="mt-1 font-sans text-slate-400">
                  {provenance.confidence_notes}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MetricExplainer;
