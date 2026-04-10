"use client";

/**
 * WhyMetricInline — Universal "Why This Number" wrapper.
 *
 * Wraps any rendered metric value and makes it clickable.
 * On click, opens a MetricExplainer popover that shows:
 *   - Factor breakdown (what drove this number)
 *   - Range bar (min–expected–max)
 *   - Data basis (freshness + calibration)
 *   - Formula (collapsed)
 *
 * Usage:
 *   <WhyMetricInline metricName="total_loss_usd" runId={runId} locale="en">
 *     $2.8B
 *   </WhyMetricInline>
 *
 * The child becomes underlined-dotted and clickable.
 * If provenance data is unavailable, children render as-is (no click, no error).
 */

import { useState, useRef, useMemo } from "react";
import {
  useMetricsProvenance,
  useFactorBreakdown,
  useMetricRanges,
  useDataBasis,
} from "@/hooks/use-provenance";
import { MetricExplainer } from "./MetricExplainer";

interface WhyMetricInlineProps {
  /** Snake_case metric name matching backend provenance keys */
  metricName: string;
  /** Run ID for provenance queries — if undefined, renders children as-is */
  runId: string | undefined;
  /** Display locale */
  locale: "en" | "ar";
  /** The rendered metric value (e.g. "$2.8B", "0.72", a <span>) */
  children: React.ReactNode;
  /** Additional className for the wrapper */
  className?: string;
}

export function WhyMetricInline({
  metricName,
  runId,
  locale,
  children,
  className = "",
}: WhyMetricInlineProps) {
  const [isOpen, setIsOpen] = useState(false);
  const anchorRef = useRef<HTMLButtonElement>(null);

  // ── Provenance queries (all disabled if no runId) ──
  const { data: provenanceData } = useMetricsProvenance(runId);
  const { data: factorData } = useFactorBreakdown(runId);
  const { data: rangeData } = useMetricRanges(runId);
  const { data: basisData } = useDataBasis(runId);

  // ── Find matching records for this metric ──
  const provenance = useMemo(
    () => provenanceData?.metrics?.find((m) => m.metric_name === metricName),
    [provenanceData, metricName],
  );
  const breakdown = useMemo(
    () => factorData?.breakdowns?.find((b) => b.metric_name === metricName),
    [factorData, metricName],
  );
  const range = useMemo(
    () => rangeData?.ranges?.find((r) => r.metric_name === metricName),
    [rangeData, metricName],
  );
  const basis = useMemo(
    () => basisData?.data_bases?.find((d) => d.metric_name === metricName),
    [basisData, metricName],
  );

  // ── If no provenance data available, render children as-is ──
  const hasData = !!(provenance || breakdown || range || basis);

  if (!runId || !hasData) {
    return <span className={className}>{children}</span>;
  }

  return (
    <span className={`relative inline-flex items-center ${className}`}>
      <button
        ref={anchorRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1 border-b border-dotted border-slate-400/50 hover:border-blue-500 transition-colors cursor-help"
        title={locale === "ar" ? "لماذا هذا الرقم؟" : "Why this number?"}
      >
        {children}
        <svg
          width="10"
          height="10"
          viewBox="0 0 16 16"
          fill="none"
          className="text-slate-400 flex-shrink-0"
        >
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
          <text
            x="8"
            y="11.5"
            textAnchor="middle"
            fill="currentColor"
            fontSize="9"
            fontWeight="600"
          >
            ?
          </text>
        </svg>
      </button>

      <MetricExplainer
        metricName={metricName}
        breakdown={breakdown}
        range={range}
        provenance={provenance}
        basis={basis}
        locale={locale}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        anchorRef={anchorRef}
      />
    </span>
  );
}

export default WhyMetricInline;
