"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";

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
  const absValue = Math.abs(value);

  if (absValue >= 1e12) {
    return `$${(value / 1e12).toFixed(1)}T`;
  }
  if (absValue >= 1e9) {
    return `$${(value / 1e9).toFixed(1)}B`;
  }
  if (absValue >= 1e6) {
    return `$${(value / 1e6).toFixed(1)}M`;
  }
  if (absValue >= 1e3) {
    return `$${(value / 1e3).toFixed(1)}K`;
  }
  return `$${value.toFixed(0)}`;
};

const getStressColor = (stress: number, maxStress: number): string => {
  const normalized = Math.min(stress / maxStress, 1);

  if (normalized < 0.2) return "from-green-500/20 to-green-600/10";
  if (normalized < 0.4) return "from-yellow-500/20 to-yellow-600/10";
  if (normalized < 0.6) return "from-amber-500/20 to-amber-600/10";
  if (normalized < 0.8) return "from-orange-500/20 to-orange-600/10";
  return "from-red-500/20 to-red-600/10";
};

const getStressBorderColor = (stress: number, maxStress: number): string => {
  const normalized = Math.min(stress / maxStress, 1);

  if (normalized < 0.2) return "border-green-500/40";
  if (normalized < 0.4) return "border-yellow-500/40";
  if (normalized < 0.6) return "border-amber-500/40";
  if (normalized < 0.8) return "border-orange-500/40";
  return "border-red-500/40";
};

const getSeverityColor = (severity?: number): string => {
  if (!severity) return "text-gray-400";
  if (severity < 0.2) return "text-green-400";
  if (severity < 0.35) return "text-yellow-400";
  if (severity < 0.5) return "text-amber-400";
  if (severity < 0.65) return "text-orange-400";
  if (severity < 0.8) return "text-red-400";
  return "text-red-500";
};

const getSeverityLabel = (severity?: number, locale: "en" | "ar" = "en"): string => {
  if (!severity) return locale === "en" ? "Unknown" : "غير معروف";
  if (severity < 0.2) return locale === "en" ? "Nominal" : "عادي";
  if (severity < 0.35) return locale === "en" ? "Low" : "منخفض";
  if (severity < 0.5) return locale === "en" ? "Guarded" : "محدود";
  if (severity < 0.65) return locale === "en" ? "Elevated" : "مرتفع";
  if (severity < 0.8) return locale === "en" ? "High" : "عالي";
  return locale === "en" ? "Severe" : "حرج";
};

export const PropagationView: React.FC<PropagationViewProps> = ({
  locale,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  totalLossUsd,
  causalChain,
}) => {
  const hasData = causalChain && causalChain.length > 0;
  const maxStress = hasData
    ? Math.max(...causalChain.map((step) => Math.abs(step.stress_delta)))
    : 1;
  const peakStressStep = hasData
    ? causalChain.reduce((max, step) =>
        Math.abs(step.stress_delta) > Math.abs(max.stress_delta) ? step : max
      )
    : null;

  return (
    <div
      className="w-full h-full flex flex-col bg-[#060910] rounded-lg border border-slate-700/50 overflow-hidden"
      dir={locale === "ar" ? "rtl" : "ltr"}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/30">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-lg font-bold text-white mb-1">
              {locale === "en" ? "Propagation Chain" : "سلسلة الانتشار"}
            </h2>
            {scenarioLabel && (
              <p className="text-sm text-slate-300">
                {locale === "en" ? scenarioLabel : scenarioLabelAr || scenarioLabel}
              </p>
            )}
          </div>
          {severity !== undefined && (
            <div className="text-right">
              <div className={`text-2xl font-bold ${getSeverityColor(severity)}`}>
                {(severity * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-slate-400">
                {getSeverityLabel(severity, locale)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {!hasData ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <AlertTriangle className="w-12 h-12 text-slate-500 mx-auto mb-3 opacity-50" />
              <p className="text-slate-400 text-sm">
                {locale === "en"
                  ? "No propagation data available"
                  : "لا توجد بيانات انتشار متاحة"}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Propagation Chain */}
            {causalChain.map((step, idx) => {
              const isLast = idx === causalChain.length - 1;
              const cumulativeStress = causalChain
                .slice(0, idx + 1)
                .reduce((sum, s) => sum + Math.abs(s.stress_delta), 0);

              return (
                <div key={`step-${step.step}`} className="relative">
                  {/* Vertical connecting line */}
                  {!isLast && (
                    <div className="absolute left-[24px] top-[60px] w-0.5 h-[40px] bg-gradient-to-b from-slate-600 to-transparent" />
                  )}

                  {/* Step Card */}
                  <div className="relative flex gap-4">
                    {/* Step Number Circle */}
                    <div className="flex-shrink-0 pt-1">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white text-sm relative z-10 bg-gradient-to-br ${getStressColor(cumulativeStress, maxStress * causalChain.length)} border-2 ${getStressBorderColor(cumulativeStress, maxStress * causalChain.length)}`}
                      >
                        {step.step}
                      </div>
                    </div>

                    {/* Step Content */}
                    <div className="flex-1 pt-1">
                      <div
                        className={`rounded-lg border-2 ${getStressBorderColor(cumulativeStress, maxStress * causalChain.length)} bg-gradient-to-br ${getStressColor(cumulativeStress, maxStress * causalChain.length)} p-4 hover:border-opacity-70 transition-all`}
                      >
                        {/* Entity Header */}
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1">
                            <h3 className="font-semibold text-white text-sm leading-tight">
                              {locale === "en" ? step.entity_label : step.entity_label_ar || step.entity_label}
                            </h3>
                            {locale === "ar" && step.entity_label_ar && (
                              <p className="text-xs text-slate-300 mt-0.5">{step.entity_label}</p>
                            )}
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="text-sm font-bold text-white">
                              {formatUsd(step.impact_usd)}
                            </div>
                            <div className="text-xs text-slate-300">
                              {locale === "en" ? "Impact" : "التأثير"}
                            </div>
                          </div>
                        </div>

                        {/* Event Description */}
                        <p className="text-xs text-slate-200 mb-3 leading-snug">
                          {locale === "en" ? step.event : step.event_ar || step.event}
                        </p>

                        {/* Metrics Row */}
                        <div className="grid grid-cols-2 gap-3">
                          <div className="bg-slate-800/40 rounded px-2.5 py-2">
                            <div className="text-xs text-slate-400 mb-0.5">
                              {locale === "en" ? "Stress Δ" : "تغير الضغط"}
                            </div>
                            <div className="text-sm font-bold text-white">
                              {step.stress_delta > 0 ? "+" : ""}
                              {(step.stress_delta * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div className="bg-slate-800/40 rounded px-2.5 py-2">
                            <div className="text-xs text-slate-400 mb-0.5">
                              {locale === "en" ? "Mechanism" : "الآلية"}
                            </div>
                            <div className="text-xs font-semibold text-slate-100 truncate">
                              {step.mechanism}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Summary Footer */}
      {hasData && (
        <div className="border-t border-slate-700/50 bg-slate-900/30 px-6 py-4">
          <div className="grid grid-cols-3 gap-4">
            {/* Total Steps */}
            <div>
              <div className="text-xs text-slate-400 mb-1">
                {locale === "en" ? "Total Steps" : "إجمالي الخطوات"}
              </div>
              <div className="text-xl font-bold text-white">{causalChain.length}</div>
            </div>

            {/* Total Propagation Loss */}
            <div>
              <div className="text-xs text-slate-400 mb-1">
                {locale === "en" ? "Total Loss" : "إجمالي الخسارة"}
              </div>
              <div className="text-xl font-bold text-red-400">
                {formatUsd(totalLossUsd || causalChain.reduce((sum, s) => sum + s.impact_usd, 0))}
              </div>
            </div>

            {/* Peak Stress Entity */}
            <div>
              <div className="text-xs text-slate-400 mb-1">
                {locale === "en" ? "Peak Stress" : "ذروة الضغط"}
              </div>
              <div className="text-sm font-semibold text-orange-400 truncate">
                {peakStressStep
                  ? locale === "en"
                    ? peakStressStep.entity_label
                    : peakStressStep.entity_label_ar || peakStressStep.entity_label
                  : "—"}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PropagationView;
