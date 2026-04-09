"use client";

/**
 * CounterfactualBlock — Baseline vs Recommended vs Alternative outcomes
 *
 * Three-column comparison showing:
 *   - Do Nothing (baseline) — what happens if you ignore
 *   - Recommended Action — what happens if you follow the directive
 *   - Partial Action (50%) — what happens with half-measures
 *
 * Plus delta summary showing savings, time gained, risk reduction
 */

import React from "react";
import {
  Ban,
  CheckCircle,
  AlertTriangle,
  TrendingDown,
  Clock,
  Shield,
  ArrowRight,
} from "lucide-react";
import type {
  CounterfactualComparison,
  CounterfactualOutcome,
  SectorConsequence,
} from "../types";

// ── Outcome Card ────────────────────────────────────────────────────

function OutcomeCard({
  outcome,
  variant,
  isAr,
}: {
  outcome: CounterfactualOutcome;
  variant: "baseline" | "recommended" | "alternative";
  isAr: boolean;
}) {
  const config = {
    baseline: {
      border: "border-red-500/20",
      bg: "bg-red-500/[0.03]",
      accent: "text-red-400",
      icon: <Ban size={14} className="text-red-400" />,
      label: isAr ? "لا شيء" : "Do Nothing",
    },
    recommended: {
      border: "border-emerald-500/20",
      bg: "bg-emerald-500/[0.03]",
      accent: "text-emerald-400",
      icon: <CheckCircle size={14} className="text-emerald-400" />,
      label: isAr ? "الموصى به" : "Recommended",
    },
    alternative: {
      border: "border-amber-500/20",
      bg: "bg-amber-500/[0.03]",
      accent: "text-amber-400",
      icon: <AlertTriangle size={14} className="text-amber-400" />,
      label: isAr ? "جزئي" : "Partial",
    },
  };
  const c = config[variant];

  // Risk level color
  const riskColor: Record<string, string> = {
    NOMINAL: "text-emerald-400",
    LOW: "text-blue-400",
    GUARDED: "text-yellow-400",
    ELEVATED: "text-orange-400",
    HIGH: "text-red-400",
    SEVERE: "text-red-500",
  };

  return (
    <div className={`rounded-lg border ${c.border} ${c.bg} p-3 flex-1 min-w-0`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2.5">
        {c.icon}
        <span className={`text-[10px] font-bold uppercase tracking-wider ${c.accent}`}>
          {c.label}
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-2 mb-3">
        <div>
          <p className="text-[8px] text-slate-600 uppercase tracking-wider">
            {isAr ? "التعرض المالي" : "Financial Exposure"}
          </p>
          <p className={`text-base font-mono font-bold ${c.accent}`}>
            {outcome.financial_exposure_formatted}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div>
            <p className="text-[8px] text-slate-600 uppercase tracking-wider">
              <Clock size={8} className="inline mr-0.5" />
              {isAr ? "وقت الفشل" : "Time to Failure"}
            </p>
            <p className="text-[11px] font-mono font-semibold text-slate-300">
              {outcome.time_to_failure_hours.toFixed(0)}h
            </p>
          </div>
          <div>
            <p className="text-[8px] text-slate-600 uppercase tracking-wider">
              <Shield size={8} className="inline mr-0.5" />
              {isAr ? "مستوى الخطر" : "Risk Level"}
            </p>
            <p
              className={`text-[11px] font-bold ${
                riskColor[outcome.risk_level] ?? "text-slate-400"
              }`}
            >
              {outcome.risk_level}
            </p>
          </div>
        </div>
      </div>

      {/* Sector consequences */}
      {outcome.sector_consequences.length > 0 && (
        <div className="border-t border-white/[0.04] pt-2">
          <p className="text-[8px] text-slate-600 uppercase tracking-wider mb-1.5">
            {isAr ? "تأثير القطاعات" : "Sector Impact"}
          </p>
          <div className="space-y-1.5">
            {outcome.sector_consequences.map((sc, i) => (
              <div key={i} className="flex items-start gap-1.5">
                <span className={`w-1 h-1 rounded-full mt-1.5 flex-shrink-0 ${
                  variant === "baseline" ? "bg-red-400" :
                  variant === "recommended" ? "bg-emerald-400" :
                  "bg-amber-400"
                }`} />
                <div>
                  <span className="text-[8px] font-bold text-slate-500 uppercase">
                    {isAr ? sc.sector_ar : sc.sector}
                  </span>
                  <p className="text-[9px] text-slate-400 leading-relaxed">
                    {isAr ? sc.impact_ar : sc.impact_en}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Delta Summary Bar ───────────────────────────────────────────────

function DeltaSummaryBar({
  delta,
  isAr,
}: {
  delta: CounterfactualComparison["delta_summary"];
  isAr: boolean;
}) {
  return (
    <div className="rounded-lg bg-emerald-500/[0.06] border border-emerald-500/15 p-3 mt-3">
      <div className="flex items-center gap-2 mb-2">
        <TrendingDown size={13} className="text-emerald-400" />
        <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
          {isAr ? "ملخص الفرق" : "Impact Delta"}
        </span>
      </div>

      <div className="flex items-center gap-4 flex-wrap mb-2">
        <div>
          <p className="text-[8px] text-emerald-600 uppercase">
            {isAr ? "التوفير" : "Savings"}
          </p>
          <p className="text-sm font-mono font-bold text-emerald-400">
            {delta.savings_formatted}
          </p>
          <p className="text-[8px] text-emerald-600">
            {delta.savings_pct.toFixed(0)}% {isAr ? "تخفيض" : "reduction"}
          </p>
        </div>
        <div>
          <p className="text-[8px] text-emerald-600 uppercase">
            {isAr ? "الوقت المكتسب" : "Time Gained"}
          </p>
          <p className="text-sm font-mono font-bold text-emerald-400">
            +{delta.time_gained_hours.toFixed(0)}h
          </p>
        </div>
        <div>
          <p className="text-[8px] text-emerald-600 uppercase">
            {isAr ? "تخفيض الخطر" : "Risk Reduction"}
          </p>
          <p className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
            {delta.risk_reduction.split(" → ")[0]}
            <ArrowRight size={10} />
            {delta.risk_reduction.split(" → ")[1]}
          </p>
        </div>
      </div>

      <p className="text-[9px] text-emerald-500/80 leading-relaxed">
        {isAr ? delta.recommendation_ar : delta.recommendation_en}
      </p>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface CounterfactualBlockProps {
  comparison: CounterfactualComparison;
  language?: "en" | "ar";
}

export function CounterfactualBlock({
  comparison,
  language = "en",
}: CounterfactualBlockProps) {
  const isAr = language === "ar";

  return (
    <div>
      <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-3 font-semibold">
        {isAr ? "تحليل النتائج المضادة" : "Counterfactual Analysis"}
      </p>

      {/* Three outcome columns */}
      <div className="flex gap-2">
        <OutcomeCard
          outcome={comparison.baseline_outcome}
          variant="baseline"
          isAr={isAr}
        />
        <OutcomeCard
          outcome={comparison.recommended_outcome}
          variant="recommended"
          isAr={isAr}
        />
        <OutcomeCard
          outcome={comparison.alternative_outcome}
          variant="alternative"
          isAr={isAr}
        />
      </div>

      {/* Delta summary */}
      <DeltaSummaryBar delta={comparison.delta_summary} isAr={isAr} />
    </div>
  );
}
