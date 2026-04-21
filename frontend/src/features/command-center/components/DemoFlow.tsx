"use client";

/**
 * DemoFlow — Cinematic Presentation Mode for Stakeholder Meetings
 *
 * A full-screen, step-through narrative overlay that transforms the
 * intelligence dashboard into a boardroom-ready presentation.
 *
 * 5-step flow:
 *   Step 1: SCENARIO  — What happened? (animated entry)
 *   Step 2: CASCADE   — How it spreads (causal chain animation)
 *   Step 3: EXPOSURE  — Who gets hit (country/sector heatmap)
 *   Step 4: DECISIONS — What to do (cost/benefit cards)
 *   Step 5: OUTCOME   — Net position (summary + confidence)
 *
 * Controls:
 *   - Arrow keys (← →) or click to navigate
 *   - Spacebar to auto-advance (5s per step)
 *   - ESC to exit back to dashboard
 *   - Progress dots at bottom
 *
 * All data sourced from existing useCommandCenter hook — zero new API calls.
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  ChevronRight,
  Clock,
  DollarSign,
  Globe,
  Layers,
  Play,
  Pause,
  Shield,
  ShieldAlert,
  Target,
  TrendingDown,
  TrendingUp,
  X,
  Zap,
} from "lucide-react";
import {
  formatUSD,
  formatPct,
  classificationColor,
  stressToClassification,
  safeNum,
  safeStr,
} from "../lib/format";
import { mechanismLabelFor } from "@/lib/mechanism-labels";
import type {
  CausalStep,
  SectorImpact,
  DecisionActionV2,
  KnowledgeGraphNode,
} from "@/types/observatory";
import type { SafeImpact } from "@/lib/v2/api-types";

// ── Types ─────────────────────────────────────────────────────────────

interface DemoFlowProps {
  // Scenario
  scenarioLabel: string;
  scenarioLabelAr?: string;
  domain: string;
  severity: number;
  horizonHours: number;

  // Headline
  systemRiskIndex: number;
  totalLossUsd: number;
  nodesImpacted: number;
  criticalCount: number;
  elevatedCount: number;
  confidence: number;

  // Cascade
  causalChain: CausalStep[];
  sectorImpacts: SectorImpact[];
  graphNodes: KnowledgeGraphNode[];

  // Decisions
  decisionActions: DecisionActionV2[];

  // Impacts
  impacts: SafeImpact[];

  // Narrative
  narrativeEn: string;

  // Trust
  auditHash?: string;
  modelVersion?: string;
  stagesCompleted?: string[];

  // Control
  onExit: () => void;
}

type StepId = "scenario" | "cascade" | "exposure" | "decisions" | "outcome";

const STEPS: { id: StepId; label: string; labelAr: string }[] = [
  { id: "scenario", label: "Scenario", labelAr: "السيناريو" },
  { id: "cascade", label: "Cascade", labelAr: "التسلسل" },
  { id: "exposure", label: "Exposure", labelAr: "التعرض" },
  { id: "decisions", label: "Decisions", labelAr: "القرارات" },
  { id: "outcome", label: "Outcome", labelAr: "النتيجة" },
];

// ── Animated Number Counter ──────────────────────────────────────────

function AnimatedValue({
  value,
  format,
  duration = 1200,
  className,
}: {
  value: number;
  format: (n: number) => string;
  duration?: number;
  className?: string;
}) {
  const [display, setDisplay] = useState(0);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const start = performance.now();
    const from = 0;
    const to = value;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(from + (to - from) * eased);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      }
    }

    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  return <span className={className}>{format(display)}</span>;
}

// ── Cascade Step Animation ───────────────────────────────────────────

function CascadeStep({
  step,
  index,
  visible,
}: {
  step: CausalStep;
  index: number;
  visible: boolean;
}) {
  const mechColor: Record<string, string> = {
    direct_shock: "#EF4444",
    price_transmission: "#F59E0B",
    physical_constraint: "#F97316",
    capacity_overflow: "#EAB308",
    supply_chain: "#3B82F6",
    claims_cascade: "#6366F1",
    monetary_transmission: "#10B981",
  };

  const color = mechColor[step.mechanism] ?? "#94A3B8";

  return (
    <div
      className="flex items-start gap-4 transition-all duration-700"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateX(0)" : "translateX(40px)",
        transitionDelay: `${index * 200}ms`,
      }}
    >
      {/* Step number */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2"
        style={{ borderColor: color, color }}
      >
        {step.step}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-bold text-white">
            {step.entity_label}
          </span>
          <span
            className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {mechanismLabelFor(step.mechanism)}
          </span>
        </div>
        <p className="text-[13px] text-slate-300 leading-relaxed">
          {step.event}
        </p>
        <div className="flex items-center gap-4 mt-1.5">
          {step.impact_usd > 0 && (
            <span className="text-[11px] text-red-400 font-bold tabular-nums">
              <DollarSign size={10} className="inline" />
              {formatUSD(step.impact_usd)}
            </span>
          )}
          <span className="text-[11px] text-slate-500">
            Stress: +{formatPct(step.stress_delta)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Decision Summary Card (Presentation Mode) ────────────────────────

function DecisionSummaryCard({
  action,
  rank,
  visible,
}: {
  action: DecisionActionV2;
  rank: number;
  visible: boolean;
}) {
  const lossAvoided = safeNum(action.loss_avoided_usd);
  const costUsd = safeNum(action.cost_usd);
  const net = lossAvoided - costUsd;
  const isLoss = costUsd > lossAvoided && costUsd > 0;
  const urgency = safeNum(action.urgency);

  const maxVal = Math.max(lossAvoided, costUsd, 1);
  const benefitPct = (lossAvoided / maxVal) * 100;
  const costPct = (costUsd / maxVal) * 100;

  return (
    <div
      className="bg-[#0F1420] border border-white/[0.08] rounded-xl p-5 transition-all duration-700"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(30px)",
        transitionDelay: `${rank * 250}ms`,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-bold">
            {rank}
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
            {safeStr(action.sector)}
          </span>
          {urgency >= 80 && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-red-500/15 text-red-400 text-[9px] font-bold">
              <Zap size={8} /> IMMEDIATE
            </span>
          )}
        </div>
        {isLoss && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-red-500/10 border border-red-500/25">
            <ShieldAlert size={10} className="text-red-500" />
            <span className="text-[9px] font-bold text-red-400">LOSS-INDUCING</span>
          </div>
        )}
      </div>

      {/* Action text */}
      <p className="text-[14px] font-medium text-slate-200 leading-snug mb-4">
        {safeStr(action.action)}
      </p>

      {/* Cost vs Benefit bars */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-emerald-500 w-14 text-right">Benefit</span>
          <div className="flex-1 h-2.5 bg-white/[0.04] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-500/80 transition-all duration-1000"
              style={{ width: `${benefitPct}%` }}
            />
          </div>
          <span className="text-[11px] font-bold text-emerald-400 tabular-nums w-16 text-right">
            {formatUSD(lossAvoided)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-red-400 w-14 text-right">Cost</span>
          <div className="flex-1 h-2.5 bg-white/[0.04] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-red-500/80 transition-all duration-1000"
              style={{ width: `${costPct}%` }}
            />
          </div>
          <span className="text-[11px] font-bold text-red-400 tabular-nums w-16 text-right">
            {formatUSD(costUsd)}
          </span>
        </div>
      </div>

      {/* Net value */}
      <div className="flex items-center justify-between pt-3 border-t border-white/[0.06]">
        <span className="text-[11px] text-slate-500">
          <Target size={11} className="inline mr-1" />
          Net Value
        </span>
        <span
          className={`text-sm font-bold tabular-nums ${isLoss ? "text-red-400" : "text-emerald-400"}`}
        >
          {isLoss ? (
            <TrendingDown size={13} className="inline mr-1" />
          ) : (
            <TrendingUp size={13} className="inline mr-1" />
          )}
          {formatUSD(net)}
        </span>
      </div>
    </div>
  );
}

// ── Country Exposure Row (Presentation Mode) ─────────────────────────

const GCC_LABELS: Record<string, { en: string; ar: string; flag: string }> = {
  SA: { en: "Saudi Arabia", ar: "المملكة العربية السعودية", flag: "🇸🇦" },
  AE: { en: "United Arab Emirates", ar: "الإمارات", flag: "🇦🇪" },
  QA: { en: "Qatar", ar: "قطر", flag: "🇶🇦" },
  KW: { en: "Kuwait", ar: "الكويت", flag: "🇰🇼" },
  BH: { en: "Bahrain", ar: "البحرين", flag: "🇧🇭" },
  OM: { en: "Oman", ar: "عُمان", flag: "🇴🇲" },
};

const COUNTRY_BOXES: Record<string, [number, number, number, number]> = {
  BH: [25.8, 26.3, 50.3, 50.7],
  QA: [24.5, 26.2, 50.7, 51.7],
  KW: [28.5, 30.1, 46.5, 48.5],
  AE: [22.6, 26.1, 51.6, 56.4],
  OM: [16.6, 26.4, 52.0, 59.8],
  SA: [16.0, 32.2, 34.5, 55.7],
};

function classifyCountry(lat: number, lng: number): string | null {
  for (const [code, [latMin, latMax, lngMin, lngMax]] of Object.entries(COUNTRY_BOXES)) {
    if (lat >= latMin && lat <= latMax && lng >= lngMin && lng <= lngMax) return code;
  }
  return null;
}

// ── Main Component ───────────────────────────────────────────────────

export function DemoFlow(props: DemoFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);
  const [stepsRevealed, setStepsRevealed] = useState(0);
  const autoPlayRef = useRef<NodeJS.Timeout | null>(null);

  const totalSteps = STEPS.length;

  // Keyboard navigation
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        setCurrentStep((s) => Math.min(s + 1, totalSteps - 1));
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setCurrentStep((s) => Math.max(s - 1, 0));
      }
      if (e.key === "Escape") {
        props.onExit();
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [totalSteps, props]);

  // Auto-play timer
  useEffect(() => {
    if (autoPlay) {
      autoPlayRef.current = setInterval(() => {
        setCurrentStep((s) => {
          if (s >= totalSteps - 1) {
            setAutoPlay(false);
            return s;
          }
          return s + 1;
        });
      }, 6000);
    }
    return () => {
      if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    };
  }, [autoPlay, totalSteps]);

  // Animate cascade steps progressively
  useEffect(() => {
    if (STEPS[currentStep]?.id === "cascade") {
      setStepsRevealed(0);
      const chain = props.causalChain;
      let i = 0;
      const interval = setInterval(() => {
        i++;
        setStepsRevealed(i);
        if (i >= chain.length) clearInterval(interval);
      }, 400);
      return () => clearInterval(interval);
    }
  }, [currentStep, props.causalChain]);

  const goNext = useCallback(() => setCurrentStep((s) => Math.min(s + 1, totalSteps - 1)), [totalSteps]);
  const goPrev = useCallback(() => setCurrentStep((s) => Math.max(s - 1, 0)), []);

  // ── Derived data ──
  const sorted = [...props.decisionActions].sort(
    (a, b) => safeNum(b.priority) - safeNum(a.priority)
  );
  const topActions = sorted.slice(0, 3);
  const totalBenefit = topActions.reduce((s, a) => s + safeNum(a.loss_avoided_usd), 0);
  const totalCost = topActions.reduce((s, a) => s + safeNum(a.cost_usd), 0);
  const netPosition = totalBenefit - totalCost;
  const lossCount = topActions.filter(
    (a) => safeNum(a.cost_usd) > safeNum(a.loss_avoided_usd) && safeNum(a.cost_usd) > 0
  ).length;

  // Country exposure
  const countryExposure = Object.entries(GCC_LABELS)
    .map(([code, info]) => {
      const nodes = props.graphNodes.filter((n) => {
        const lat = typeof n.lat === "number" && isFinite(n.lat) ? n.lat : 0;
        const lng = typeof n.lng === "number" && isFinite(n.lng) ? n.lng : 0;
        return classifyCountry(lat, lng) === code;
      });
      const totalStress = nodes.reduce((s, n) => s + safeNum(n.stress), 0);
      const avgStress = nodes.length > 0 ? totalStress / nodes.length : 0;
      return { code, ...info, nodeCount: nodes.length, avgStress };
    })
    .filter((c) => c.nodeCount > 0)
    .sort((a, b) => b.avgStress - a.avgStress);

  const classification = stressToClassification(props.systemRiskIndex);
  const classColor = classificationColor(classification);

  // ── Step rendering ──
  function renderStep() {
    const stepId = STEPS[currentStep]?.id;

    // ─── STEP 1: SCENARIO ───────────────────────────────
    if (stepId === "scenario") {
      return (
        <div className="flex flex-col items-center justify-center h-full px-8">
          {/* Classification badge */}
          <div
            className="px-5 py-2 rounded-lg text-sm font-bold uppercase tracking-widest mb-6 animate-fade-in"
            style={{
              backgroundColor: `${classColor}20`,
              color: classColor,
              border: `1px solid ${classColor}40`,
            }}
          >
            {classification}
          </div>

          {/* Scenario title */}
          <h1 className="text-4xl lg:text-5xl font-bold text-white text-center mb-3 animate-slide-up">
            {props.scenarioLabel}
          </h1>
          {props.scenarioLabelAr && (
            <p className="text-xl text-slate-400 text-center mb-8 animate-slide-up-delay" dir="rtl">
              {props.scenarioLabelAr}
            </p>
          )}

          {/* Hero KPIs */}
          <div className="flex items-center gap-8 mt-4 animate-fade-in-delay">
            <div className="text-center">
              <p className="text-[11px] text-slate-500 uppercase tracking-wider mb-1">Total Loss at Risk</p>
              <p className="text-3xl font-bold text-red-400 tabular-nums">
                <AnimatedValue value={props.totalLossUsd} format={formatUSD} />
              </p>
            </div>
            <div className="w-px h-12 bg-white/[0.08]" />
            <div className="text-center">
              <p className="text-[11px] text-slate-500 uppercase tracking-wider mb-1">System Risk</p>
              <p className="text-3xl font-bold tabular-nums" style={{ color: classColor }}>
                <AnimatedValue value={props.systemRiskIndex} format={(n) => formatPct(n, 1)} />
              </p>
            </div>
            <div className="w-px h-12 bg-white/[0.08]" />
            <div className="text-center">
              <p className="text-[11px] text-slate-500 uppercase tracking-wider mb-1">Nodes Impacted</p>
              <p className="text-3xl font-bold text-white tabular-nums">
                <AnimatedValue value={props.nodesImpacted} format={(n) => String(Math.round(n))} />
              </p>
            </div>
            <div className="w-px h-12 bg-white/[0.08]" />
            <div className="text-center">
              <p className="text-[11px] text-slate-500 uppercase tracking-wider mb-1">Confidence</p>
              <p className="text-3xl font-bold text-emerald-400 tabular-nums">
                <AnimatedValue value={props.confidence} format={(n) => formatPct(n, 0)} />
              </p>
            </div>
          </div>

          {/* Domain + horizon */}
          <div className="flex items-center gap-3 mt-8 text-slate-500 text-sm animate-fade-in-delay-2">
            <Globe size={14} />
            <span className="uppercase tracking-wider font-semibold">{props.domain}</span>
            <span>|</span>
            <Clock size={14} />
            <span>{props.horizonHours}h horizon</span>
            <span>|</span>
            <AlertTriangle size={14} />
            <span>{props.criticalCount} critical / {props.elevatedCount} elevated nodes</span>
          </div>
        </div>
      );
    }

    // ─── STEP 2: CASCADE ────────────────────────────────
    if (stepId === "cascade") {
      return (
        <div className="flex flex-col h-full px-8 py-6 overflow-hidden">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-1">Propagation Cascade</h2>
            <p className="text-sm text-slate-400">
              {props.causalChain.length}-step causal chain — how the shock spreads across GCC infrastructure
            </p>
          </div>

          <div className="flex-1 overflow-y-auto max-w-3xl mx-auto w-full">
            <div className="relative pl-6 border-l border-white/[0.08]">
              {props.causalChain.map((step, i) => (
                <CascadeStep
                  key={step.step}
                  step={step}
                  index={i}
                  visible={i < stepsRevealed}
                />
              ))}
            </div>
          </div>

          {/* Summary strip */}
          <div className="flex items-center justify-center gap-8 mt-4 pt-4 border-t border-white/[0.06]">
            <span className="text-[11px] text-slate-500">
              <Layers size={11} className="inline mr-1" />
              {props.causalChain.length} propagation hops
            </span>
            <span className="text-[11px] text-red-400 font-bold">
              <DollarSign size={11} className="inline" />
              {formatUSD(props.totalLossUsd)} total impact
            </span>
            <span className="text-[11px] text-slate-500">
              <Shield size={11} className="inline mr-1" />
              {formatPct(props.confidence)} confidence
            </span>
          </div>
        </div>
      );
    }

    // ─── STEP 3: EXPOSURE ───────────────────────────────
    if (stepId === "exposure") {
      return (
        <div className="flex flex-col h-full px-8 py-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-1">Country & Sector Exposure</h2>
            <p className="text-sm text-slate-400">
              GCC-wide impact distribution by geography and sector
            </p>
          </div>

          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto w-full">
            {/* Country exposure */}
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
                By Country
              </h3>
              <div className="space-y-3">
                {countryExposure.map((country, i) => {
                  const stressColor = classificationColor(
                    stressToClassification(country.avgStress)
                  );
                  return (
                    <div
                      key={country.code}
                      className="flex items-center gap-3 transition-all duration-500"
                      style={{
                        opacity: 1,
                        transitionDelay: `${i * 150}ms`,
                      }}
                    >
                      <span className="text-lg w-8">{country.flag}</span>
                      <span className="text-sm text-slate-300 w-28 truncate">
                        {country.en}
                      </span>
                      <div className="flex-1 h-3 bg-white/[0.04] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-1000"
                          style={{
                            width: `${Math.round(country.avgStress * 100)}%`,
                            backgroundColor: stressColor,
                          }}
                        />
                      </div>
                      <span
                        className="text-sm font-bold tabular-nums w-12 text-right"
                        style={{ color: stressColor }}
                      >
                        {formatPct(country.avgStress)}
                      </span>
                      <span className="text-[10px] text-slate-600 w-8 text-right">
                        {country.nodeCount}n
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Sector exposure */}
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
                By Sector
              </h3>
              <div className="space-y-3">
                {props.sectorImpacts.map((sector, i) => {
                  const stressColor = classificationColor(
                    stressToClassification(sector.avgImpact)
                  );
                  return (
                    <div
                      key={sector.sector}
                      className="flex items-center gap-3 transition-all duration-500"
                      style={{
                        opacity: 1,
                        transitionDelay: `${i * 150}ms`,
                      }}
                    >
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: sector.color }}
                      />
                      <span className="text-sm text-slate-300 w-28 truncate">
                        {sector.sectorLabel}
                      </span>
                      <div className="flex-1 h-3 bg-white/[0.04] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-1000"
                          style={{
                            width: `${Math.round(sector.avgImpact * 100)}%`,
                            backgroundColor: stressColor,
                          }}
                        />
                      </div>
                      <span
                        className="text-sm font-bold tabular-nums w-12 text-right"
                        style={{ color: stressColor }}
                      >
                        {formatPct(sector.avgImpact)}
                      </span>
                      <span className="text-[10px] text-slate-600 w-8 text-right">
                        {sector.nodeCount}n
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      );
    }

    // ─── STEP 4: DECISIONS ──────────────────────────────
    if (stepId === "decisions") {
      return (
        <div className="flex flex-col h-full px-8 py-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-1">Decision Priorities</h2>
            <p className="text-sm text-slate-400">
              Top {topActions.length} recommended actions — ranked by priority score
              {lossCount > 0 && (
                <span className="text-red-400 ml-2">
                  ({lossCount} loss-inducing)
                </span>
              )}
            </p>
          </div>

          <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-5 max-w-6xl mx-auto w-full">
            {topActions.map((action, i) => (
              <DecisionSummaryCard
                key={action.id}
                action={action}
                rank={i + 1}
                visible={true}
              />
            ))}
          </div>

          {/* Aggregate summary */}
          <div className="flex items-center justify-center gap-8 mt-4 pt-4 border-t border-white/[0.06]">
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Total Benefit</p>
              <p className="text-sm font-bold text-emerald-400 tabular-nums">
                {formatUSD(totalBenefit)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Total Cost</p>
              <p className="text-sm font-bold text-red-400 tabular-nums">
                {formatUSD(totalCost)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Net Position</p>
              <p
                className={`text-lg font-bold tabular-nums ${
                  netPosition >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {formatUSD(netPosition)}
              </p>
            </div>
          </div>
        </div>
      );
    }

    // ─── STEP 5: OUTCOME ────────────────────────────────
    if (stepId === "outcome") {
      return (
        <div className="flex flex-col items-center justify-center h-full px-8">
          <h2 className="text-3xl font-bold text-white mb-2 animate-slide-up">
            Net Decision Position
          </h2>
          <p className="text-sm text-slate-400 mb-8 animate-slide-up-delay">
            If all recommended actions are executed
          </p>

          {/* Big net number */}
          <div className="animate-fade-in-delay">
            <p
              className={`text-6xl lg:text-7xl font-bold tabular-nums ${
                netPosition >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {netPosition >= 0 ? (
                <TrendingUp size={48} className="inline mr-3" />
              ) : (
                <TrendingDown size={48} className="inline mr-3" />
              )}
              <AnimatedValue value={netPosition} format={formatUSD} duration={1500} />
            </p>
          </div>

          {/* Summary grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mt-10 animate-fade-in-delay-2">
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Loss Avoided</p>
              <p className="text-xl font-bold text-emerald-400 tabular-nums">{formatUSD(totalBenefit)}</p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Execution Cost</p>
              <p className="text-xl font-bold text-red-400 tabular-nums">{formatUSD(totalCost)}</p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Actions</p>
              <p className="text-xl font-bold text-white">{topActions.length}</p>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Confidence</p>
              <p className="text-xl font-bold text-emerald-400 tabular-nums">{formatPct(props.confidence)}</p>
            </div>
          </div>

          {/* Narrative excerpt */}
          {props.narrativeEn && (
            <div className="max-w-2xl mt-8 p-4 bg-white/[0.02] rounded-xl border border-white/[0.06] animate-fade-in-delay-2">
              <p className="text-[12px] text-slate-400 leading-relaxed line-clamp-3">
                {props.narrativeEn}
              </p>
            </div>
          )}

          {/* Trust footer */}
          <div className="flex items-center gap-4 mt-6 text-[10px] text-slate-600 animate-fade-in-delay-2">
            {props.modelVersion && <span>Model v{props.modelVersion}</span>}
            {props.stagesCompleted && (
              <span>{props.stagesCompleted.length}/9 pipeline stages</span>
            )}
            {props.auditHash && (
              <span className="font-mono truncate max-w-[200px]">{props.auditHash}</span>
            )}
          </div>
        </div>
      );
    }

    return null;
  }

  return (
    <div className="fixed inset-0 z-50 bg-[#060910] flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/[0.06] flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
            Impact Observatory — Presentation Mode
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* Auto-play toggle */}
          <button
            onClick={() => setAutoPlay(!autoPlay)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-semibold rounded-lg bg-white/[0.04] border border-white/[0.08] text-slate-400 hover:text-white hover:border-white/[0.16] transition-all"
          >
            {autoPlay ? <Pause size={10} /> : <Play size={10} />}
            {autoPlay ? "Pause" : "Auto-play"}
          </button>

          {/* Exit */}
          <button
            onClick={props.onExit}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-semibold rounded-lg bg-white/[0.04] border border-white/[0.08] text-slate-400 hover:text-white hover:border-white/[0.16] transition-all"
          >
            <X size={10} />
            Exit <span className="text-slate-600 ml-0.5">(ESC)</span>
          </button>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {renderStep()}
      </div>

      {/* Navigation bar */}
      <div className="flex items-center justify-between px-6 py-3 border-t border-white/[0.06] flex-shrink-0">
        {/* Prev button */}
        <button
          onClick={goPrev}
          disabled={currentStep === 0}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          <ArrowLeft size={12} /> Previous
        </button>

        {/* Step indicators */}
        <div className="flex items-center gap-2">
          {STEPS.map((step, i) => (
            <button
              key={step.id}
              onClick={() => setCurrentStep(i)}
              className="flex items-center gap-1.5 group"
            >
              <div
                className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                  i === currentStep
                    ? "bg-blue-500 scale-125"
                    : i < currentStep
                    ? "bg-blue-500/40"
                    : "bg-white/[0.12]"
                }`}
              />
              <span
                className={`text-[10px] font-semibold uppercase tracking-wider transition-colors ${
                  i === currentStep ? "text-blue-400" : "text-slate-600"
                }`}
              >
                {step.label}
              </span>
            </button>
          ))}
        </div>

        {/* Next button */}
        <button
          onClick={goNext}
          disabled={currentStep === totalSteps - 1}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          Next <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
}
