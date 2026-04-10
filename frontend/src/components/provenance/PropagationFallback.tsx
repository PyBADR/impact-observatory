"use client";

/**
 * PropagationFallback — Empty-state propagation display.
 *
 * When the globe/map hasn't loaded or data is minimal, this component
 * renders the propagation chain as a readable sentence + timeline
 * instead of a blank white rectangle.
 *
 * Shows:
 *   1. Scenario context line
 *   2. Propagation chain as a step-by-step sentence
 *   3. Breach timing callout
 *   4. Causal chain steps (compact)
 *
 * Never blank. If chain is empty, shows a "No propagation data" message.
 */

import type { CausalStep } from "@/types/observatory";

interface PropagationFallbackProps {
  /** Scenario label for context */
  scenarioLabel: string;
  scenarioLabelAr?: string;
  /** Causal chain from useCommandCenter */
  causalChain: CausalStep[];
  /** Propagation depth from headline */
  propagationDepth: number;
  /** Peak day from headline */
  peakDay: number;
  /** Total loss */
  totalLossUsd: number;
  /** Display locale */
  locale: "en" | "ar";
}

function formatUsd(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

export function PropagationFallback({
  scenarioLabel,
  scenarioLabelAr,
  causalChain,
  propagationDepth,
  peakDay,
  totalLossUsd,
  locale,
}: PropagationFallbackProps) {
  const isAr = locale === "ar";
  const label = isAr ? (scenarioLabelAr || scenarioLabel) : scenarioLabel;

  // Build propagation sentence from causal chain
  const propagationSentence = buildPropagationSentence(causalChain, locale);

  if (causalChain.length === 0) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 text-center">
        <p className="text-xs text-slate-400">
          {isAr
            ? "لا تتوفر بيانات انتشار لهذا السيناريو"
            : "No propagation data available for this scenario"}
        </p>
      </div>
    );
  }

  return (
    <div
      className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Context line */}
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {isAr ? "سلسلة الانتشار" : "Propagation Chain"}
        </h3>
        <div className="flex items-center gap-3 text-[10px] text-slate-400">
          <span>
            {isAr ? "العمق" : "Depth"}: {propagationDepth}
          </span>
          <span>
            {isAr ? "الذروة" : "Peak"}: {isAr ? `يوم ${peakDay}` : `Day ${peakDay}`}
          </span>
          <span className="font-semibold text-slate-600">
            {formatUsd(totalLossUsd)}
          </span>
        </div>
      </div>

      {/* Propagation sentence */}
      <div className="px-3 py-2 bg-slate-50 border border-slate-100 rounded-lg">
        <p className="text-xs text-slate-700 leading-relaxed font-medium">
          {propagationSentence}
        </p>
      </div>

      {/* Causal chain steps */}
      <div className="space-y-0">
        {causalChain.map((step, idx) => (
          <div key={step.step} className="flex items-start gap-3">
            {/* Step connector */}
            <div className="flex flex-col items-center flex-shrink-0">
              <StepDot
                index={idx}
                total={causalChain.length}
                stressDelta={step.stress_delta}
              />
              {idx < causalChain.length - 1 && (
                <div className="w-px h-6 bg-slate-200" />
              )}
            </div>

            {/* Step content */}
            <div className="pb-4 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-700 truncate">
                  {isAr ? (step.entity_label_ar || step.entity_label) : step.entity_label}
                </span>
                {step.impact_usd > 0 && (
                  <span className="text-[10px] font-medium text-red-600 flex-shrink-0">
                    {formatUsd(step.impact_usd)}
                  </span>
                )}
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">
                {isAr ? (step.event_ar || step.event) : step.event}
              </p>
              <span className="inline-flex items-center mt-1 px-1.5 py-0.5 rounded text-[9px] font-medium bg-slate-100 text-slate-500">
                {step.mechanism}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────

function StepDot({
  index,
  total,
  stressDelta,
}: {
  index: number;
  total: number;
  stressDelta: number;
}) {
  // Color intensity based on position and stress
  const intensity = total > 1 ? index / (total - 1) : 0;
  const isHigh = stressDelta > 0.1 || intensity > 0.7;
  const isMid = stressDelta > 0.05 || intensity > 0.3;

  const color = isHigh
    ? "bg-red-500"
    : isMid
      ? "bg-orange-400"
      : "bg-blue-400";

  return (
    <div
      className={`w-2.5 h-2.5 rounded-full ${color} flex-shrink-0 mt-1`}
    />
  );
}

function buildPropagationSentence(
  chain: CausalStep[],
  locale: "en" | "ar",
): string {
  if (chain.length === 0) return "";

  const isAr = locale === "ar";

  if (chain.length === 1) {
    const step = chain[0];
    return isAr
      ? `يبدأ الأثر من ${step.entity_label_ar || step.entity_label} عبر ${step.mechanism}`
      : `Impact originates at ${step.entity_label} via ${step.mechanism}`;
  }

  const first = chain[0];
  const last = chain[chain.length - 1];
  const middleCount = chain.length - 2;

  if (isAr) {
    const mid = middleCount > 0
      ? ` عبر ${middleCount} ${middleCount === 1 ? "كيان وسيط" : "كيانات وسيطة"}`
      : "";
    return `ينتشر الأثر من ${first.entity_label_ar || first.entity_label}${mid} إلى ${last.entity_label_ar || last.entity_label} (${chain.length} مراحل)`;
  }

  const mid = middleCount > 0
    ? ` through ${middleCount} intermediar${middleCount === 1 ? "y" : "ies"}`
    : "";
  return `Impact propagates from ${first.entity_label}${mid} to ${last.entity_label} (${chain.length} steps)`;
}

export default PropagationFallback;
