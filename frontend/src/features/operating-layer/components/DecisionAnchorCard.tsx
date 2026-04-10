"use client";

/**
 * DecisionAnchorCard — Who owns this decision, what type, what tradeoffs
 *
 * Renders:
 *   - Decision type badge (emergency/strategic/operational)
 *   - Owner + approval chain
 *   - Deadline with urgency classification
 *   - Three tradeoff axes with position sliders
 */

import React from "react";
import { User, Clock, AlertTriangle, Shield, Scale } from "lucide-react";
import type { DecisionAnchor, TradeoffAxis } from "../types";

// ── Tradeoff Slider ─────────────────────────────────────────────────

function TradeoffSlider({
  axis,
  isAr,
}: {
  axis: TradeoffAxis;
  isAr: boolean;
}) {
  const pct = Math.round(axis.position * 100);
  // Color: left-leaning = blue (action-oriented), right-leaning = amber (deliberative)
  const dotColor =
    axis.position < 0.4
      ? "bg-blue-400"
      : axis.position < 0.6
      ? "bg-slate-300"
      : "bg-amber-400";

  return (
    <div className="mb-3 last:mb-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-semibold text-slate-300">
          {isAr ? axis.axis_ar : axis.axis_en}
        </span>
      </div>
      {/* Axis labels */}
      <div className="flex items-center justify-between text-[8px] text-slate-500 mb-1">
        <span>{isAr ? axis.left_ar : axis.left_en}</span>
        <span>{isAr ? axis.right_ar : axis.right_en}</span>
      </div>
      {/* Slider track */}
      <div className="relative h-2 rounded-full bg-white/[0.06] overflow-visible">
        {/* Gradient track */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500/30 via-slate-500/20 to-amber-500/30" />
        {/* Position dot */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full ${dotColor} border-2 border-[#0B0F1A] shadow-sm transition-all`}
          style={{ left: `calc(${pct}% - 6px)` }}
        />
      </div>
      {/* Rationale */}
      <p className="text-[9px] text-slate-500 mt-1 leading-relaxed">
        {isAr ? axis.rationale_ar : axis.rationale_en}
      </p>
    </div>
  );
}

// ── Decision Type Badge ─────────────────────────────────────────────

function TypeBadge({ type, label }: { type: string; label: string }) {
  const config: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    emergency: {
      bg: "bg-red-500/15 border-red-500/40",
      text: "text-red-400",
      icon: <AlertTriangle size={11} />,
    },
    strategic: {
      bg: "bg-amber-500/15 border-amber-500/40",
      text: "text-amber-400",
      icon: <Shield size={11} />,
    },
    operational: {
      bg: "bg-blue-500/15 border-blue-500/40",
      text: "text-blue-400",
      icon: <Scale size={11} />,
    },
  };
  const c = config[type] ?? config.operational;

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${c.bg} ${c.text}`}>
      {c.icon}
      <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
    </div>
  );
}

// ── Deadline Badge ──────────────────────────────────────────────────

function DeadlineBadge({
  hours,
  classification,
}: {
  hours: number;
  classification: string;
}) {
  const color: Record<string, string> = {
    IMMEDIATE: "text-red-400 bg-red-500/10 border-red-500/20",
    URGENT: "text-orange-400 bg-orange-500/10 border-orange-500/20",
    STANDARD: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    EXTENDED: "text-slate-400 bg-slate-500/10 border-slate-500/20",
  };
  const c = color[classification] ?? color.STANDARD;

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg border ${c}`}>
      <Clock size={11} />
      <span className="text-[10px] font-bold font-mono">{hours}h</span>
      <span className="text-[8px] uppercase tracking-wider opacity-70">{classification}</span>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface DecisionAnchorCardProps {
  anchor: DecisionAnchor;
  language?: "en" | "ar";
}

export function DecisionAnchorCard({
  anchor,
  language = "en",
}: DecisionAnchorCardProps) {
  const isAr = language === "ar";

  return (
    <div className="bg-white/[0.02] rounded-xl border border-white/[0.06] overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/[0.04] bg-[#080C14]">
        <div className="flex items-center justify-between mb-2">
          <TypeBadge
            type={anchor.decision_type}
            label={isAr ? anchor.decision_type_label_ar : anchor.decision_type_label}
          />
          <DeadlineBadge
            hours={anchor.deadline_hours}
            classification={anchor.deadline_classification}
          />
        </div>
        <div className="flex items-center gap-4 text-[10px]">
          <span className="text-slate-400">
            <User size={10} className="inline mr-1" />
            {isAr ? anchor.owner_ar : anchor.owner}
          </span>
        </div>
      </div>

      {/* Tradeoffs */}
      <div className="px-4 py-3">
        <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-3 font-semibold">
          {isAr ? "محاور المفاضلة" : "Decision Tradeoffs"}
        </p>
        <TradeoffSlider axis={anchor.tradeoffs.cost_vs_risk} isAr={isAr} />
        <TradeoffSlider axis={anchor.tradeoffs.speed_vs_accuracy} isAr={isAr} />
        <TradeoffSlider axis={anchor.tradeoffs.short_term_vs_long_term} isAr={isAr} />
      </div>
    </div>
  );
}
