"use client";

/**
 * TransmissionStoryPanel — How the macro shock propagates
 *
 * Purpose: "Explain how impact travels"
 * Shows a causal chain derived from the scenario's explanation.causal_chain
 * as a compact, left-to-right flow of cause → effect steps.
 *
 * Data source: RunResult.explanation.causal_chain (real pipeline data)
 * Design: Compact flow chips with arrows, boardroom aesthetic
 */

import React, { useMemo } from "react";
import { ArrowRight, Zap } from "lucide-react";
import type { RunResult, Language, CausalStep } from "@/types/observatory";

// ── Derive simplified transmission chain ────────────────────────────

interface TransmissionStep {
  label: string;
  labelAr: string | null;
  impactUsd: number;
  stressDelta: number;
  mechanism: string;
  entity: string;
}

function deriveTransmissionChain(result: RunResult): TransmissionStep[] {
  const chain = result.explanation?.causal_chain ?? [];
  if (chain.length === 0) return [];

  // Take up to 6 key steps from the causal chain
  // Pick steps with highest stress_delta for narrative impact
  const sorted = [...chain]
    .sort((a, b) => Math.abs(b.stress_delta) - Math.abs(a.stress_delta))
    .slice(0, 6)
    .sort((a, b) => a.step - b.step);

  return sorted.map((step) => ({
    label: step.event,
    labelAr: step.event_ar,
    impactUsd: step.impact_usd,
    stressDelta: step.stress_delta,
    mechanism: step.mechanism,
    entity: step.entity_label ?? step.entity_id,
  }));
}

function formatCompactUSD(value: number): string {
  if (!isFinite(value) || isNaN(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e9) return `$${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(abs / 1e6).toFixed(0)}M`;
  if (abs >= 1e3) return `$${(abs / 1e3).toFixed(0)}K`;
  return `$${Math.round(abs)}`;
}

// ── Flow Step Chip ──────────────────────────────────────────────────

function FlowChip({
  step,
  isAr,
  isLast,
  index,
}: {
  step: TransmissionStep;
  isAr: boolean;
  isLast: boolean;
  index: number;
}) {
  const intensity = Math.min(1, Math.abs(step.stressDelta) * 3);
  const color =
    intensity >= 0.7 ? "#EF4444" : intensity >= 0.4 ? "#F59E0B" : "#3B82F6";

  return (
    <div className="flex items-center gap-1.5 flex-shrink-0">
      <div
        className="rounded-lg border px-3 py-2 min-w-[160px] max-w-[200px] bg-[#0D1117]"
        style={{ borderColor: `${color}30` }}
      >
        {/* Step number + entity */}
        <div className="flex items-center gap-1.5 mb-1">
          <span
            className="text-[9px] font-bold tabular-nums rounded px-1 py-0.5"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="text-[10px] text-slate-500 font-medium truncate">
            {step.entity}
          </span>
        </div>

        {/* Event description */}
        <p className="text-[11px] text-slate-300 font-medium leading-snug line-clamp-2 mb-1.5">
          {isAr && step.labelAr ? step.labelAr : step.label}
        </p>

        {/* Impact metrics */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold tabular-nums" style={{ color }}>
            {formatCompactUSD(step.impactUsd)}
          </span>
          <span className="text-[9px] text-slate-600">
            {step.mechanism}
          </span>
        </div>
      </div>

      {/* Arrow connector */}
      {!isLast && (
        <ArrowRight size={14} className="text-slate-700 flex-shrink-0 mx-0.5" />
      )}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface TransmissionStoryPanelProps {
  result: RunResult;
  lang?: Language;
}

export function TransmissionStoryPanel({
  result,
  lang = "en",
}: TransmissionStoryPanelProps) {
  const isAr = lang === "ar";
  const chain = useMemo(() => deriveTransmissionChain(result), [result]);

  if (chain.length === 0) return null;

  return (
    <div className="w-full bg-[#090D17] border-b border-white/[0.05]">
      {/* Section header */}
      <div className="flex items-center gap-2 px-6 pt-3 pb-2">
        <Zap size={13} className="text-blue-400" />
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          {isAr ? "مسار الانتقال" : "Transmission Path"}
        </span>
        <div className="flex-1 h-px bg-white/[0.04]" />
        <span className="text-[10px] text-slate-600">
          {chain.length} {isAr ? "مرحلة" : "stages"}
        </span>
      </div>

      {/* Subtitle — one-line story */}
      <p className="px-6 pb-2 text-[11px] text-slate-500 leading-relaxed">
        {isAr
          ? "كيف تنتشر الصدمة عبر الاقتصاد الخليجي — من الحدث إلى الأثر المالي"
          : "How the shock propagates across the GCC economy — from trigger event to financial outcome"}
      </p>

      {/* Horizontal flow chain */}
      <div className="flex items-start gap-0 px-6 pb-4 overflow-x-auto">
        {chain.map((step, i) => (
          <FlowChip
            key={i}
            step={step}
            isAr={isAr}
            isLast={i === chain.length - 1}
            index={i}
          />
        ))}
      </div>
    </div>
  );
}
