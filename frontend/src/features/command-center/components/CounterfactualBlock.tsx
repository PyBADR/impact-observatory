"use client";

/**
 * Counterfactual Block — 3-column comparison: Baseline vs Recommended vs Alternative.
 *
 * Shows projected loss, risk level, recovery days, operational cost for each
 * scenario. Delta section shows loss reduction and best option. Narrative
 * provides executive-level explanation.
 */

import React from "react";
import {
  TrendingDown,
  TrendingUp,
  ArrowDown,
  CheckCircle2,
  XCircle,
  Minus,
} from "lucide-react";
import { formatUSD, formatPct, safeNum } from "../lib/format";
import type { CounterfactualBlockView } from "../lib/decision-view-models";
import type { CounterfactualOutcome } from "@/types/observatory";

// ── Column Card ─────────────────────────────────────────────────────────

function OutcomeColumn({
  outcome,
  columnLabel,
  highlight,
  isBest,
}: {
  outcome: CounterfactualOutcome;
  columnLabel: string;
  highlight: "green" | "amber" | "red" | "slate";
  isBest: boolean;
}) {
  const borderColor = {
    green: "border-emerald-500/30",
    amber: "border-amber-500/30",
    red: "border-red-500/30",
    slate: "border-white/[0.08]",
  }[highlight];

  const headerColor = {
    green: "text-emerald-400",
    amber: "text-amber-400",
    red: "text-red-400",
    slate: "text-slate-400",
  }[highlight];

  const loss = safeNum(outcome.projected_loss_usd);
  const recoveryDays = safeNum(outcome.recovery_days);
  const opCost = safeNum(outcome.operational_cost_usd);
  const severity = safeNum(outcome.severity);

  return (
    <div
      className={`relative bg-[#0F1420] border ${borderColor} rounded-xl p-4 flex-1 min-w-0`}
    >
      {/* Best option badge */}
      {isBest && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30">
          <span className="text-[8px] font-bold text-emerald-400 uppercase tracking-wider">
            Best Option
          </span>
        </div>
      )}

      {/* Column header */}
      <div className="mb-3">
        <h4 className={`text-[11px] font-bold uppercase tracking-wider ${headerColor} mb-0.5`}>
          {columnLabel}
        </h4>
        <p className="text-[10px] text-slate-600 line-clamp-1">{outcome.label}</p>
        {outcome.label_ar && outcome.label_ar !== "—" && (
          <p className="text-[9px] text-slate-700 line-clamp-1" dir="rtl">
            {outcome.label_ar}
          </p>
        )}
      </div>

      {/* Projected Loss — primary metric */}
      <div className="mb-3 pb-3 border-b border-white/[0.04]">
        <span className="text-[9px] text-slate-500 uppercase tracking-wider block mb-1">
          Projected Loss
        </span>
        <span className="text-lg font-bold text-slate-200 tabular-nums">
          {outcome.projected_loss_formatted || formatUSD(loss)}
        </span>
      </div>

      {/* Secondary metrics */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500">Risk Level</span>
          <span className="text-[10px] font-semibold text-slate-300">
            {outcome.risk_level}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500">Recovery</span>
          <span className="text-[10px] font-bold text-slate-300 tabular-nums">
            {recoveryDays}d
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500">Op. Cost</span>
          <span className="text-[10px] font-bold text-slate-300 tabular-nums">
            {formatUSD(opCost)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500">Severity</span>
          <span className="text-[10px] font-bold text-slate-300 tabular-nums">
            {formatPct(severity)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Delta Banner ────────────────────────────────────────────────────────

function DeltaBanner({ view }: { view: CounterfactualBlockView }) {
  const delta = view.delta;
  const reduction = safeNum(delta.loss_reduction_usd);
  const reductionPct = safeNum(delta.loss_reduction_pct);
  const isPositive = reduction > 0;

  const bestIcon =
    delta.best_option === "recommended"
      ? CheckCircle2
      : delta.best_option === "alternative"
      ? ArrowDown
      : Minus;
  const BestIcon = bestIcon;

  return (
    <div className="bg-[#0F1420] border border-white/[0.08] rounded-xl p-3 mt-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isPositive ? (
            <TrendingDown size={14} className="text-emerald-400" />
          ) : (
            <TrendingUp size={14} className="text-red-400" />
          )}
          <span className="text-[11px] font-bold text-slate-300">
            {isPositive ? "Loss Reduction" : "Loss Increase"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-bold tabular-nums ${isPositive ? "text-emerald-400" : "text-red-400"}`}
          >
            {delta.loss_reduction_formatted || formatUSD(reduction)}
          </span>
          <span className="text-[10px] text-slate-500 tabular-nums">
            ({formatPct(reductionPct)})
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 text-[10px]">
        <BestIcon size={12} className="text-slate-500" />
        <span className="text-slate-500">Best option:</span>
        <span className="font-semibold text-slate-300 capitalize">
          {delta.best_option}
        </span>
        {safeNum(delta.recovery_improvement_days) > 0 && (
          <>
            <span className="text-slate-600">·</span>
            <span className="text-slate-500">
              Recovery: {delta.recovery_improvement_days}d faster
            </span>
          </>
        )}
      </div>

      {/* Narrative */}
      <p className="text-[10px] text-slate-500 mt-2 leading-relaxed">
        {delta.delta_explained}
      </p>
    </div>
  );
}

// ── Consistency Flag ────────────────────────────────────────────────────

function ConsistencyBadge({ flag }: { flag: string }) {
  if (flag === "CONSISTENT") {
    return (
      <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
        <CheckCircle2 size={10} className="text-emerald-400" />
        <span className="text-[10px] font-bold text-emerald-400">Consistent</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
      <XCircle size={10} className="text-amber-400" />
      <span className="text-[10px] font-bold text-amber-400">
        {flag === "CORRECTED_COSTLY" ? "Corrected — Costly" : "Corrected"}
      </span>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

interface CounterfactualBlockProps {
  view: CounterfactualBlockView;
}

export function CounterfactualBlock({ view }: CounterfactualBlockProps) {
  if (!view.baseline.label || view.baseline.label === "—") return null;

  const bestOption = view.delta.best_option;

  return (
    <div className="bg-[#0A0E18] border-b border-white/[0.06]">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-2.5 border-b border-white/[0.04]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            Counterfactual Analysis
          </h2>
          <span className="text-[10px] text-slate-600">
            Savings: {view.savings_formatted}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <ConsistencyBadge flag={view.consistency_flag} />
          <span className="text-[10px] text-slate-600 tabular-nums">
            Conf: {formatPct(view.confidence_score)}
          </span>
        </div>
      </div>

      {/* 3-column comparison */}
      <div className="px-6 py-3">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <OutcomeColumn
            outcome={view.baseline}
            columnLabel="Baseline (No Action)"
            highlight="red"
            isBest={bestOption === "equivalent"}
          />
          <OutcomeColumn
            outcome={view.recommended}
            columnLabel="Recommended"
            highlight="green"
            isBest={bestOption === "recommended"}
          />
          <OutcomeColumn
            outcome={view.alternative}
            columnLabel="Alternative"
            highlight="amber"
            isBest={bestOption === "alternative"}
          />
        </div>

        {/* Delta banner */}
        <DeltaBanner view={view} />

        {/* Narrative */}
        {view.narrative && view.narrative !== "—" && (
          <p className="text-[11px] text-slate-500 mt-3 leading-relaxed px-1">
            {view.narrative}
          </p>
        )}
      </div>
    </div>
  );
}
