"use client";

/**
 * PropagationView — Causal Narrative Surface
 *
 * One continuous story: cause → transmission → consequence.
 * Maximum 4 steps visible. Plain prose. No cards. No boxes.
 * Executive reads this like a briefing paragraph.
 */

import React from "react";

interface CausalChainStep {
  step: number;
  entity_id: string;
  entity_label: string;
  entity_label_ar?: string | null;
  event: string;
  event_ar?: string | null;
  impact_usd: number;
  stress_delta: number;
  mechanism: string;
}

interface PropagationViewProps {
  locale: "en" | "ar";
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  severity?: number;
  totalLossUsd?: number;
  causalChain?: CausalChainStep[];
}

const formatUsd = (value: number): string => {
  if (value === 0) return "$0";
  const abs = Math.abs(value);
  if (abs >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${(value / 1e3).toFixed(0)}K`;
};

export const PropagationView: React.FC<PropagationViewProps> = ({
  locale,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  totalLossUsd,
  causalChain,
}) => {
  const isAr = locale === "ar";
  const hasData = causalChain && causalChain.length > 0;
  const steps = hasData ? causalChain.slice(0, 4) : [];
  const displayLabel = isAr ? (scenarioLabelAr || scenarioLabel) : scenarioLabel;

  return (
    <div
      className="max-w-3xl mx-auto px-6 sm:px-8 py-10"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* ── Opening context ── */}
      <div className="mb-12">
        <h2 className="text-[1.375rem] sm:text-[1.625rem] font-bold text-[#1d1d1f] leading-tight tracking-tight mb-3">
          {isAr ? "كيف ينتقل الضغط" : "How Pressure Spreads"}
        </h2>
        {displayLabel && (
          <p className="text-[0.875rem] text-[#6e6e73] leading-relaxed">
            {displayLabel}
            {severity != null && (
              <span className="text-[#0071e3] ml-2">
                · {Math.round(severity * 100)}% severity
              </span>
            )}
            {totalLossUsd != null && totalLossUsd > 0 && (
              <span className="ml-2">
                · {formatUsd(totalLossUsd)} projected loss
              </span>
            )}
          </p>
        )}
      </div>

      {/* ── Empty state ── */}
      {!hasData && (
        <p className="text-[0.9375rem] text-[#6e6e73]">
          {isAr
            ? "لا توجد سلسلة انتشار نشطة — اختر سيناريو من الإحاطة."
            : "No active propagation chain — select a scenario from the Briefing."}
        </p>
      )}

      {/* ── Causal narrative — max 4 steps ── */}
      {hasData && (
        <div className="space-y-10">
          {steps.map((step, idx) => {
            const entity = isAr
              ? (step.entity_label_ar || step.entity_label)
              : step.entity_label;
            const event = isAr
              ? (step.event_ar || step.event)
              : step.event;
            const stressPct = Math.abs(step.stress_delta * 100).toFixed(1);
            const isLast = idx === steps.length - 1;

            return (
              <div key={step.step}>
                {/* Step number — gold, anchors the eye */}
                <p className="text-[0.75rem] text-[#0071e3] font-bold tracking-widest uppercase mb-3">
                  {isAr ? `الخطوة ${step.step}` : `Step ${step.step}`}
                </p>

                {/* Trigger — what entity is affected */}
                <p className="text-[1.0625rem] font-semibold text-[#1d1d1f] leading-snug mb-2">
                  {entity}
                </p>

                {/* Event — the consequence at this node */}
                <p className="text-[0.9375rem] text-[#515154] leading-[1.75] mb-3">
                  {event}
                </p>

                {/* Transmission channel + stress delta + impact — inline, not boxed */}
                <p className="text-[0.8125rem] text-[#6e6e73] leading-relaxed">
                  {isAr ? "القناة" : "Channel"}: <span className="text-[#515154]">{step.mechanism}</span>
                  <span className="mx-2 text-[#8e8e93]">·</span>
                  {isAr ? "تأثير الضغط" : "Stress impact"}: <span className="text-[#515154]">+{stressPct}%</span>
                  {step.impact_usd > 0 && (
                    <>
                      <span className="mx-2 text-[#8e8e93]">·</span>
                      {isAr ? "الخسارة" : "Loss"}: <span className="text-[#515154]">{formatUsd(step.impact_usd)}</span>
                    </>
                  )}
                </p>

                {/* Connecting line between steps */}
                {!isLast && (
                  <div className="mt-6">
                    <div className="h-px bg-[#e5e5e7]" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Closing — total if more steps exist beyond 4 ── */}
      {hasData && causalChain.length > 4 && (
        <div className="mt-10 pt-5 border-t border-[#e5e5e7]">
          <p className="text-[0.8125rem] text-[#6e6e73]">
            {causalChain.length - 4} {isAr ? "خطوات إضافية في سلسلة الانتشار" : "additional steps in the propagation chain"}.
            {totalLossUsd != null && totalLossUsd > 0 && (
              <span className="text-[#515154] ml-1">
                {isAr ? "إجمالي الخسارة المتوقعة" : "Total projected loss"}: {formatUsd(totalLossUsd)}.
              </span>
            )}
          </p>
        </div>
      )}

      {/* Timestamp */}
      <div className="mt-14 pt-5 border-t border-[#e5e5e7]">
        <p className="text-[0.625rem] text-[#8e8e93] tracking-wider">
          {isAr ? "سلسلة الانتشار" : "Propagation chain"} · {steps.length} {isAr ? "خطوات مرئية" : "steps visible"}
        </p>
      </div>
    </div>
  );
};

export default PropagationView;
