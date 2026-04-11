"use client";

/**
 * DecisionRoomV2 — Unified Decision Flow Surface
 *
 * Transformation: "Panels showing data" → "Decision driven by Macro → Scenario → Impact → Action"
 *
 * Layout (ALWAYS visible, no depth toggling for core flow):
 *
 *   ┌─────────────────────────────────────────────────────────────┐
 *   │  SCENARIO + MACRO HEADER                                    │
 *   │  Scenario name · Top macro signals · System Risk · Confidence│
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  NARRATIVE FLOW                                             │
 *   │  What happened → What it means → What to do                 │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  IMPACT METRIC (inline drivers + range)                     │
 *   │  $4.27B ← driven by Oil shock (35%), Port congestion (25%) │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  DECISION CARDS (each with "Why this decision?")            │
 *   │  Action + benefit + cost + WHY + drivers                    │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  ADVANCED VIEW (collapsed — ExplainabilityPanel + MacroPanel)│
 *   └─────────────────────────────────────────────────────────────┘
 *
 * CEO test: understand What happened → Why it matters → What to do
 * in under 5 seconds, without clicking anything.
 */

import { useState, useMemo } from "react";
import { useDecisionReasoning } from "@/hooks/use-provenance";
import { ExplainabilityPanel } from "@/components/trust/ExplainabilityPanel";
import { MacroPanel } from "@/components/macro/MacroPanel";
import type {
  CausalStep,
  DecisionActionV2,
  SectorRollup,
  MetricExplanation,
  DecisionTransparencyResult,
  ReliabilityPayload,
  MacroContext,
} from "@/types/observatory";

// ── Props ────────────────────────────────────────────────────────────

interface DecisionRoomV2Props {
  runId: string | undefined;
  scenarioLabel: string;
  scenarioLabelAr: string;
  severity: string;
  totalLossUsd: number;
  averageStress: number;
  propagationDepth: number;
  peakDay: number;
  causalChain: CausalStep[];
  decisionActions: DecisionActionV2[];
  sectorRollups: Record<string, SectorRollup>;
  locale: "en" | "ar";

  // Sprint 1 — Decision Trust Layer
  metricExplanations?: MetricExplanation[];
  decisionTransparency?: DecisionTransparencyResult;

  // Sprint 2 — Decision Reliability Layer
  reliability?: ReliabilityPayload;

  // Sprint 3 — Explainability Layer
  confidenceScore?: number;
  narrativeEn?: string;
  narrativeAr?: string;
  macroContext?: MacroContext;

  onSubmitForReview?: (actionId: string) => void;
}

export function DecisionRoomV2({
  runId,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  totalLossUsd,
  averageStress,
  propagationDepth,
  peakDay,
  causalChain,
  decisionActions,
  sectorRollups,
  locale,
  metricExplanations,
  decisionTransparency,
  reliability,
  confidenceScore,
  narrativeEn,
  narrativeAr,
  macroContext,
  onSubmitForReview,
}: DecisionRoomV2Props) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const isAr = locale === "ar";

  const { data: reasoningData } = useDecisionReasoning(runId);

  // ── Derived data ──────────────────────────────────────────────────

  const topDecisions = useMemo(
    () => [...decisionActions].sort((a, b) => a.priority - b.priority).slice(0, 3),
    [decisionActions],
  );

  // Top macro signals (3-4 key ones)
  const topMacroSignals = useMemo(() => {
    if (!macroContext?.macro_signals) return [];
    return macroContext.macro_signals.slice(0, 4);
  }, [macroContext]);

  // All drivers across metrics, deduplicated
  const allDrivers = useMemo(() => {
    if (!metricExplanations?.length) return [];
    const seen = new Map<string, { label: string; pct: number; rationale: string }>();
    for (const exp of metricExplanations) {
      for (const d of exp.drivers ?? []) {
        const existing = seen.get(d.label);
        if (!existing || d.contribution_pct > existing.pct) {
          seen.set(d.label, { label: d.label, pct: d.contribution_pct, rationale: d.rationale });
        }
      }
    }
    return [...seen.values()].sort((a, b) => b.pct - a.pct).slice(0, 5);
  }, [metricExplanations]);

  // Loss range
  const lossRange = useMemo(() => {
    if (!reliability?.ranges) return null;
    return reliability.ranges.find(
      (r) => r.metric_id === "projected_loss" || r.metric_id === "total_loss",
    );
  }, [reliability]);

  // Confidence
  const confPct = Math.round((confidenceScore ?? 0) * 100);

  // System Risk Level
  const sriValue = macroContext?.system_risk_index ?? averageStress;
  const riskLevel = getRiskLevel(sriValue);

  // Narrative parts — derive What happened / What it means / What to do
  const narrative = useMemo(() => {
    const src = isAr ? narrativeAr : narrativeEn;
    if (!src) {
      return {
        happened: isAr
          ? `سيناريو: ${scenarioLabelAr || scenarioLabel}`
          : `Scenario: ${scenarioLabel}`,
        means: isAr
          ? `مستوى الإجهاد ${(averageStress * 100).toFixed(0)}% عبر ${propagationDepth} مراحل انتشار`
          : `System stress at ${(averageStress * 100).toFixed(0)}% across ${propagationDepth} propagation stages`,
        action: topDecisions[0]
          ? isAr
            ? topDecisions[0].action_ar
            : topDecisions[0].action
          : isAr
            ? "جارٍ تحليل الإجراءات..."
            : "Analyzing actions...",
      };
    }
    // Try to split narrative into 3 parts if it has clear structure
    const lines = src.split(/\.\s+/).filter(Boolean);
    if (lines.length >= 3) {
      return {
        happened: lines[0] + ".",
        means: lines[1] + ".",
        action: lines.slice(2).join(". ") + (src.endsWith(".") ? "" : "."),
      };
    }
    return {
      happened: lines[0] ? lines[0] + "." : src,
      means: lines[1] ? lines[1] + "." : "",
      action: topDecisions[0]
        ? isAr ? topDecisions[0].action_ar : topDecisions[0].action
        : "",
    };
  }, [narrativeEn, narrativeAr, isAr, scenarioLabel, scenarioLabelAr, averageStress, propagationDepth, topDecisions]);

  return (
    <div className="space-y-5" dir={isAr ? "rtl" : "ltr"}>

      {/* ═══════════════════════════════════════════════════════════════
           STEP 1: SCENARIO + MACRO HEADER
           CEO sees scenario, macro context, risk level, confidence
           in the first 2 seconds — no scrolling required.
           ═══════════════════════════════════════════════════════════════ */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800/80 to-slate-900 rounded-xl border border-slate-700/50 overflow-hidden">
        {/* Scenario Title Row */}
        <div className="px-5 pt-4 pb-2 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h1 className="text-base font-bold text-white leading-tight truncate">
              {isAr ? scenarioLabelAr || scenarioLabel : scenarioLabel}
            </h1>
            <p className="text-[10px] text-slate-500 mt-0.5">
              {isAr ? "أفق التأثير" : "Impact horizon"}: {peakDay} {isAr ? "يوم" : "days"}
              {" · "}
              {isAr ? "الشدة" : "Severity"}: {severity}
            </p>
          </div>

          {/* Risk + Confidence badges — top right */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wide ${riskLevel.bg} ${riskLevel.text}`}>
              {isAr ? riskLevel.labelAr : riskLevel.label}
            </span>
            {confPct > 0 && (
              <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold tabular-nums ${confPct >= 75 ? "bg-emerald-500/15 text-emerald-400" : confPct >= 50 ? "bg-amber-500/15 text-amber-400" : "bg-red-500/15 text-red-400"}`}>
                {confPct}%
              </span>
            )}
          </div>
        </div>

        {/* Macro Signals Row — inline, compact, no separate panel */}
        {topMacroSignals.length > 0 && (
          <div className="px-5 pb-3 flex items-center gap-3 flex-wrap">
            {topMacroSignals.map((sig) => (
              <div
                key={sig.id}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] ${
                  sig.impact === "high"
                    ? "bg-red-500/10 text-red-400"
                    : sig.impact === "medium"
                      ? "bg-amber-500/10 text-amber-400"
                      : "bg-slate-700/50 text-slate-400"
                }`}
              >
                <span className="font-medium opacity-70">
                  {isAr ? sig.name_ar : sig.name_en}
                </span>
                <span className="font-bold tabular-nums">{sig.value}</span>
              </div>
            ))}
            {macroContext && macroContext.system_risk_index > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-700/30 text-[10px] text-slate-400">
                <span className="opacity-70">{isAr ? "مؤشر المخاطر" : "SRI"}</span>
                <span className="font-bold tabular-nums text-slate-300">
                  {(macroContext.system_risk_index * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           STEP 7: NARRATIVE FLOW
           What happened → What it means → What to do
           CEO reads 3 lines and understands the situation.
           ═══════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <NarrativeCard
          icon="⚡"
          title={isAr ? "ماذا حدث" : "What happened"}
          text={narrative.happened}
          accent="border-red-500/40"
        />
        <NarrativeCard
          icon="📊"
          title={isAr ? "ماذا يعني" : "What it means"}
          text={narrative.means}
          accent="border-amber-500/40"
        />
        <NarrativeCard
          icon="🎯"
          title={isAr ? "ماذا نفعل" : "What to do"}
          text={narrative.action}
          accent="border-emerald-500/40"
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           STEP 3: IMPACT METRIC — Inline drivers + range
           The primary KPI with WHY visible immediately.
           ═══════════════════════════════════════════════════════════════ */}
      <div className="bg-slate-900/60 rounded-xl border border-slate-700/40 p-5">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          {/* Primary metric */}
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-1">
              {isAr ? "إجمالي الخسائر المتوقعة" : "Projected Total Loss"}
            </p>
            <p className="text-3xl font-bold text-white tabular-nums tracking-tight">
              {formatUsdCompact(totalLossUsd)}
            </p>
            {lossRange && (
              <p className="text-[10px] text-slate-500 mt-1 tabular-nums">
                {isAr ? "النطاق" : "Range"}: {formatUsdCompact(lossRange.low)} – {formatUsdCompact(lossRange.high)}
                <span className="ml-2 opacity-60">
                  ({isAr ? "ثقة" : "conf"} {Math.round(lossRange.confidence * 100)}%)
                </span>
              </p>
            )}
          </div>

          {/* Secondary KPIs */}
          <div className="flex items-center gap-4">
            <MiniKpi
              label={isAr ? "الإجهاد" : "Stress"}
              value={`${(averageStress * 100).toFixed(0)}%`}
              color={averageStress >= 0.65 ? "text-red-400" : averageStress >= 0.35 ? "text-amber-400" : "text-emerald-400"}
            />
            <MiniKpi
              label={isAr ? "الانتشار" : "Depth"}
              value={String(propagationDepth)}
              color="text-slate-300"
            />
            <MiniKpi
              label={isAr ? "ذروة اليوم" : "Peak Day"}
              value={String(peakDay)}
              color="text-slate-300"
            />
          </div>
        </div>

        {/* Inline Drivers — ALWAYS visible, no clicking required */}
        {allDrivers.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-700/30">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-2">
              {isAr ? "المحركات الرئيسية" : "Driven by"}
            </p>
            <div className="space-y-1.5">
              {allDrivers.map((d) => (
                <div key={d.label} className="flex items-center gap-2">
                  <div className="flex-1 flex items-center gap-2 min-w-0">
                    <div
                      className="h-1.5 rounded-full bg-blue-500/60"
                      style={{ width: `${Math.max(d.pct, 8)}%`, maxWidth: "40%" }}
                    />
                    <span className="text-xs text-slate-300 truncate">{d.label}</span>
                  </div>
                  <span className="text-[10px] font-bold tabular-nums text-slate-400 flex-shrink-0">
                    {d.pct}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           STEP 2: DECISION CARDS — Each includes "Why this decision?"
           Decision + benefit + cost + WHY + tradeoffs
           ═══════════════════════════════════════════════════════════════ */}
      {topDecisions.length > 0 && (
        <div>
          <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-3">
            {isAr ? "القرارات المطلوبة" : "Recommended Actions"}
          </h3>
          <div className="space-y-3">
            {topDecisions.map((action, idx) => {
              const actionTransparency = decisionTransparency?.action_transparencies?.find(
                (at) => at.action_id === action.id,
              );
              const reasoning = reasoningData?.reasonings?.find(
                (r) => r.action_id === action.id,
              );

              return (
                <DecisionCard
                  key={action.id}
                  rank={idx + 1}
                  action={action}
                  transparency={actionTransparency}
                  reasoning={reasoning}
                  locale={locale}
                  onSubmitForReview={onSubmitForReview}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
           STEP 4: ADVANCED VIEW — Collapsed by default
           ExplainabilityPanel + MacroPanel live here now.
           Power users expand; CEOs never need to.
           ═══════════════════════════════════════════════════════════════ */}
      <div className="border-t border-slate-700/30 pt-3">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-400 transition-colors"
        >
          <svg
            className={`w-3 h-3 transition-transform ${showAdvanced ? "rotate-90" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          {isAr ? "العرض المتقدم" : "Advanced View"}
          <span className="text-slate-600 normal-case font-normal">
            {isAr ? "— تفاصيل كاملة للمحللين" : "— full detail for analysts"}
          </span>
        </button>

        {showAdvanced && (
          <div className="mt-4 space-y-4">
            <ExplainabilityPanel
              metricExplanations={metricExplanations}
              reliability={reliability}
              confidenceScore={confidenceScore}
              narrativeEn={narrativeEn}
              narrativeAr={narrativeAr}
              locale={locale}
              defaultExpanded={true}
            />
            {macroContext && (
              <MacroPanel macroContext={macroContext} locale={locale} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-components — private to this module, not exported
// ═══════════════════════════════════════════════════════════════════════════════

/** Narrative card — one of the three What happened / means / do blocks */
function NarrativeCard({
  icon,
  title,
  text,
  accent,
}: {
  icon: string;
  title: string;
  text: string;
  accent: string;
}) {
  return (
    <div className={`bg-slate-900/40 rounded-lg border-l-2 ${accent} border border-slate-700/30 px-4 py-3`}>
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className="text-xs">{icon}</span>
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          {title}
        </span>
      </div>
      <p className="text-xs text-slate-300 leading-relaxed">{text}</p>
    </div>
  );
}

/** Mini KPI badge used in the impact metric section */
function MiniKpi({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="text-center">
      <p className="text-[9px] text-slate-500 uppercase tracking-wider">{label}</p>
      <p className={`text-sm font-bold tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

/** Decision card with inline "Why this decision?" section */
function DecisionCard({
  rank,
  action,
  transparency,
  reasoning,
  locale,
  onSubmitForReview,
}: {
  rank: number;
  action: DecisionActionV2;
  transparency?: {
    action_id: string;
    classification: string;
    cost_formatted: string;
    benefit_formatted: string;
    net_value_formatted: string;
    is_net_positive: boolean;
    why_recommended: string[];
    tradeoffs: string[];
  };
  reasoning?: {
    why_this_decision_en: string;
    why_this_decision_ar: string;
    why_now_en: string;
    why_now_ar: string;
  };
  locale: "en" | "ar";
  onSubmitForReview?: (actionId: string) => void;
}) {
  const isAr = locale === "ar";
  const netValue = (action.loss_avoided_usd ?? 0) - (action.cost_usd ?? 0);
  const isNetPositive = netValue > 0;
  const classColor = transparency?.classification === "HIGH_VALUE"
    ? "border-emerald-500/40 bg-emerald-500/5"
    : transparency?.classification === "LOSS_INDUCING"
      ? "border-red-500/40 bg-red-500/5"
      : "border-slate-700/40 bg-slate-900/40";

  // Build "Why this decision?" reasons
  const whyReasons: string[] = [];
  if (transparency?.why_recommended) {
    whyReasons.push(...transparency.why_recommended.slice(0, 3));
  } else if (reasoning) {
    const text = isAr ? reasoning.why_this_decision_ar : reasoning.why_this_decision_en;
    if (text) whyReasons.push(text);
  }
  // Fallback: build from action data
  if (whyReasons.length === 0) {
    if (action.loss_avoided_usd > 0) {
      whyReasons.push(
        isAr
          ? `يتجنب خسائر بقيمة ${formatUsdCompact(action.loss_avoided_usd)}`
          : `Avoids ${formatUsdCompact(action.loss_avoided_usd)} in losses`,
      );
    }
    if (action.sector) {
      whyReasons.push(
        isAr
          ? `يحمي قطاع ${action.sector}`
          : `Protects ${action.sector} sector`,
      );
    }
  }

  return (
    <div className={`rounded-xl border ${classColor} overflow-hidden`}>
      {/* Header row */}
      <div className="px-4 py-3 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          {/* Rank */}
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700/50 flex items-center justify-center text-[10px] font-bold text-slate-400">
            {rank}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white leading-tight">
              {isAr ? action.action_ar : action.action}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              {action.sector} · {action.owner}
            </p>
          </div>
        </div>

        {/* Classification badge */}
        {transparency && (
          <span className={`flex-shrink-0 px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
            transparency.classification === "HIGH_VALUE"
              ? "bg-emerald-500/15 text-emerald-400"
              : transparency.classification === "LOSS_INDUCING"
                ? "bg-red-500/15 text-red-400"
                : "bg-slate-700/50 text-slate-400"
          }`}>
            {transparency.classification.replace("_", " ")}
          </span>
        )}
      </div>

      {/* Cost / Benefit / Net */}
      <div className="px-4 pb-2 flex items-center gap-4 text-[10px]">
        <span className="text-slate-500">
          {isAr ? "التكلفة" : "Cost"}: <span className="text-slate-300 font-semibold tabular-nums">{formatUsdCompact(action.cost_usd ?? 0)}</span>
        </span>
        <span className="text-slate-500">
          {isAr ? "الفائدة" : "Benefit"}: <span className="text-slate-300 font-semibold tabular-nums">{formatUsdCompact(action.loss_avoided_usd ?? 0)}</span>
        </span>
        <span className={`font-bold tabular-nums ${isNetPositive ? "text-emerald-400" : "text-red-400"}`}>
          {isNetPositive ? "+" : ""}{formatUsdCompact(netValue)}
        </span>
      </div>

      {/* STEP 2: "Why this decision?" — always visible */}
      {whyReasons.length > 0 && (
        <div className="px-4 pb-3 pt-2 border-t border-slate-700/20">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
            {isAr ? "لماذا هذا القرار؟" : "Why this decision?"}
          </p>
          <ul className="space-y-1">
            {whyReasons.map((reason, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400 leading-relaxed">
                <span className="text-emerald-500 flex-shrink-0 mt-0.5">+</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
          {/* Tradeoffs */}
          {transparency?.tradeoffs && transparency.tradeoffs.length > 0 && (
            <div className="mt-2">
              {transparency.tradeoffs.slice(0, 2).map((t, i) => (
                <p key={i} className="text-[10px] text-slate-500 leading-relaxed">
                  <span className="text-amber-500">⚠</span> {t}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Submit button */}
      {onSubmitForReview && (
        <div className="px-4 pb-3">
          <button
            onClick={() => onSubmitForReview(action.id)}
            className="w-full py-1.5 rounded-lg text-[10px] font-semibold bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 transition-colors border border-blue-500/20"
          >
            {isAr ? "تقديم للمراجعة" : "Submit for Review"}
          </button>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════════════════

function formatUsdCompact(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

function getRiskLevel(sri: number): {
  label: string;
  labelAr: string;
  bg: string;
  text: string;
} {
  if (sri >= 0.8) return { label: "SEVERE", labelAr: "حرج", bg: "bg-red-500/20", text: "text-red-400" };
  if (sri >= 0.65) return { label: "HIGH", labelAr: "مرتفع", bg: "bg-red-500/15", text: "text-red-400" };
  if (sri >= 0.5) return { label: "ELEVATED", labelAr: "مُرتفع", bg: "bg-orange-500/15", text: "text-orange-400" };
  if (sri >= 0.35) return { label: "GUARDED", labelAr: "حذر", bg: "bg-amber-500/15", text: "text-amber-400" };
  if (sri >= 0.2) return { label: "LOW", labelAr: "منخفض", bg: "bg-emerald-500/15", text: "text-emerald-400" };
  return { label: "NOMINAL", labelAr: "اعتيادي", bg: "bg-slate-700/30", text: "text-slate-400" };
}

export default DecisionRoomV2;
