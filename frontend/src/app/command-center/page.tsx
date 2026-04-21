"use client";

/**
 * Impact Observatory | مرصد الأثر — Command Center (White Enterprise Theme)
 *
 * RESTORED ARCHITECTURE:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  OBSERVATORY SHELL (identity, language, scenario bar, tabs) │
 * ├─────────────────────────────────────────────────────────────┤
 * │  TAB: Dashboard     → Scenario Library + Intelligence Brief │
 * │  TAB: Scenarios     → Full ScenarioLibrary page             │
 * │  TAB: Macro         → MacroIntelligenceView (top-down flow) │
 * │  TAB: Propagation   → Causal chain flow diagram             │
 * │  TAB: Map           → GCC 6-country impact map              │
 * │  TAB: Sectors       → Banking / Insurance / Fintech stress  │\n * │  TAB: Decisions     → DecisionRoomV2 (full decision engine) │\n * │  TAB: Audit         → Audit trail + regulatory breaches     │\n * └─────────────────────────────────────────────────────────────┘\n *\n * Scenario context is preserved across all tabs via URL params.\n * Data flow: useCommandCenter(runId) feeds all views.\n */

import React, { Suspense, useState, useCallback, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";
import type { BankingStress, InsuranceStress } from "@/types/observatory";
import { api } from "@/lib/api";

// ── Shell & Navigation ──
import { ObservatoryShell } from "@/components/shell/ObservatoryShell";

// ── Tab: Dashboard (Scenario Library + Brief) ──
import { ScenarioLibrary } from "@/components/scenario/ScenarioLibrary";
import { ScenarioSelector } from "@/components/scenario/ScenarioSelector";

// ── Tab: Decision Room ──
import { DecisionRoomV2 } from "@/components/provenance/DecisionRoomV2";

// ── Tab: Impact Map ──
import { GCCImpactMap } from "@/components/map/GCCImpactMap";

// ── Tab: Propagation ──
import { PropagationView } from "@/components/panels/PropagationView";

// ── Tab: Sector Intelligence ──
import { SectorIntelligenceView } from "@/components/panels/SectorIntelligenceView";

// ── Tab: Regulatory / Audit ──
import { RegulatoryAuditView } from "@/components/panels/RegulatoryAuditView";

// ── Operational Deep-Dive (existing) ──
import { StatusBar } from "@/features/command-center/components/StatusBar";

// ── Trace Impact Experience ──
import { TraceImpactExperience } from "@/features/trace-impact/TraceImpactExperience";
import { TraceImpactCTA } from "@/features/trace-impact/components/TraceImpactCTA";

// ── Loading Skeleton ──

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-io-accent/30 border-t-io-accent rounded-full animate-spin" />
        <p className="text-sm text-slate-500">Loading intelligence pipeline...</p>
      </div>
    </div>
  );
}

// ── Error State ──

function ErrorState(
  {
    error,
    onRetry,
    onFallbackMock,
  }: {
    error: string;
    onRetry?: () => void;
    onFallbackMock?: () => void;
  }
) {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-lg">!</span>
        </div>
        <h2 className="text-sm font-semibold text-slate-900 mb-2">Pipeline Error</h2>
        <p className="text-xs text-slate-600 mb-4">{error}</p>
        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-io-accent-hover transition-colors"
            >
              Retry
            </button>
          )}
          {onFallbackMock && (
            <button
              onClick={onFallbackMock}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Load Demo Data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// DASHBOARD TAB — Scenario Library + Intelligence Brief
// ══════════════════════════════════════════════════════════════

function DashboardView(
  {
    scenario,
    headline,
    narrativeEn,
    narrativeAr,
    macroContext,
    confidence,
    causalChain,
    sectorRollups,
    decisionActions,
    locale,
    onSelectScenario,
    isRunningScenario,
  }: {
    scenario: ReturnType<typeof useCommandCenter>["scenario"];
    headline: ReturnType<typeof useCommandCenter>["headline"];
    narrativeEn?: string;
    narrativeAr?: string;
    macroContext?: ReturnType<typeof useCommandCenter>["macroContext"];
    confidence?: number;
    causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
    sectorRollups: ReturnType<typeof useCommandCenter>["sectorRollups"];
    decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
    locale: "en" | "ar";
    onSelectScenario: (id: string) => void;
    isRunningScenario: boolean;
  }
) {
  const isAr = locale === "ar";

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Executive Intelligence Brief ── */}
      {scenario && headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900">
              {isAr ? "الإحاطة التنفيذية" : "Executive Briefing"}
            </h2>
            <span className="text-xs text-io-secondary">
              {isAr ? scenario.labelAr || scenario.label : scenario.label}
            </span>
          </div>

          {/* Executive Summary Line */}
          <div className="bg-io-accent/5 border border-io-accent/15 rounded-lg p-4 mb-5">
            <p className="text-sm text-slate-800 leading-relaxed">
              {isAr
                ? (narrativeAr || narrativeEn || `خسائر متوقعة بقيمة $${(headline.totalLossUsd / 1e9).toFixed(1)} مليار عبر ${headline.propagationDepth} قنوات انتقال — ذروة الضغط في اليوم ${headline.peakDay}`)
                : (narrativeEn || narrativeAr || `$${(headline.totalLossUsd / 1e9).toFixed(1)}B projected loss across ${headline.propagationDepth} transmission channels — stress peaks Day ${headline.peakDay}`)}
            </p>
          </div>

          {/* Headline Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
            <MetricCard
              label={isAr ? "الخسارة الرئيسية" : "Headline Loss"}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-io-status-severe"
            />
            <MetricCard
              label={isAr ? "متوسط الضغط" : "Avg Stress"}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-io-status-elevated"
            />
            <MetricCard
              label={isAr ? "عمق الانتشار" : "Propagation Depth"}
              value={`${headline.propagationDepth}`}
              color="text-io-accent"
            />
            <MetricCard
              label={isAr ? "يوم الذروة" : "Peak Day"}
              value={`${isAr ? "اليوم" : "Day"} ${headline.peakDay}`}
              color="text-io-status-high"
            />
          </div>

          {/* Propagation Summary — elevated per Sarah's directive */}
          {causalChain && causalChain.length > 0 && (
            <div className="border border-slate-200 rounded-lg p-4 mb-5">
              <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-3">
                {isAr ? "مسار الانتقال الرئيسي" : "Primary Transmission Path"}
              </h3>
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                {causalChain.slice(0, 5).map((step, idx) => (
                  <React.Fragment key={idx}>
                    <div className="flex-shrink-0 bg-slate-50 rounded-lg px-3 py-2 text-center min-w-[100px]">
                      <p className="text-xs font-semibold text-slate-900 truncate">{step.entity_label}</p>
                      <p className="text-[10px] text-io-status-elevated tabular-nums mt-0.5">
                        {step.stress_delta > 0 ? "+" : ""}{(step.stress_delta * 100).toFixed(0)}%
                      </p>
                    </div>
                    {idx < Math.min(causalChain.length, 5) - 1 && (
                      <span className="text-io-accent text-xs flex-shrink-0">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Top Decision — owner/timing per Sarah */}
          {decisionActions && decisionActions.length > 0 && (() => {
            const top = [...decisionActions].sort((a: any, b: any) => a.priority - b.priority)[0] as any;
            return (
              <div className="border border-io-accent/20 bg-io-accent/5 rounded-lg p-4 mb-5">
                <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-2">
                  {isAr ? "القرار الأول — مطلوب الآن" : "Priority Decision — Required Now"}
                </h3>
                <p className="text-sm font-semibold text-slate-900 mb-2">
                  {isAr && top.action_ar ? top.action_ar : top.action}
                </p>
                <div className="flex flex-wrap gap-3 text-xs text-io-secondary">
                  {top.owner && (
                    <span><span className="font-medium text-slate-700">{isAr ? "المسؤول:" : "Owner:"}</span> {top.owner}</span>
                  )}
                  {top.time_to_act_hours != null && (
                    <span><span className="font-medium text-slate-700">{isAr ? "الوقت المتاح:" : "Window:"}</span> {top.time_to_act_hours}h</span>
                  )}
                  {top.loss_avoided_usd > 0 && (
                    <span><span className="font-medium text-slate-700">{isAr ? "خسائر متجنبة:" : "Loss avoided:"}</span> ${(top.loss_avoided_usd / 1e9).toFixed(1)}B</span>
                  )}
                  {top.cost_usd > 0 && (
                    <span><span className="font-medium text-slate-700">{isAr ? "التكلفة:" : "Cost:"}</span> ${(top.cost_usd / 1e6).toFixed(0)}M</span>
                  )}
                </div>
              </div>
            );
          })()}

          {/* System Risk + Confidence */}
          <div className="flex items-center gap-4 text-xs">
            {macroContext?.system_risk_index != null && (
              <span className="px-2 py-1 rounded bg-io-status-severe/10 text-io-status-severe font-semibold">
                {isAr ? "مخاطر النظام" : "System Risk"}: {(macroContext.system_risk_index * 100).toFixed(0)}%
              </span>
            )}
            {confidence != null && (
              <span className="px-2 py-1 rounded bg-io-accent/10 text-io-accent font-semibold">
                {isAr ? "الثقة" : "Confidence"}: {(confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Trace Impact Experience CTA ── */}
      <TraceImpactCTA variant="hero" locale={locale} />

      {/* ── Scenario Library ── */}
      <div>
        <h2 className="text-base font-bold text-slate-900 mb-4">
          {isAr ? "مكتبة السيناريوهات" : "Scenario Library"}
        </h2>
        <ScenarioLibrary
          onSelectScenario={onSelectScenario}
          isLoading={isRunningScenario}
          locale={locale}
        />
      </div>
    </div>
  );
}

function MetricCard(
  { label, value, color }: { label: string; value: string; color: string }
) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-lg font-bold ${color}`}>{value}</p>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// MACRO INTELLIGENCE VIEW — Top-down flow with enterprise cards
// ══════════════════════════════════════════════════════════════

function MacroIntelligenceView(
  {
    scenario,
    headline,
    narrativeEn,
    narrativeAr,
    macroContext,
    confidence,
    causalChain,
    sectorRollups,
    decisionActions,
    trust,
    locale,
  }: {
    scenario: ReturnType<typeof useCommandCenter>["scenario"];
    headline: ReturnType<typeof useCommandCenter>["headline"];
    narrativeEn?: string;
    narrativeAr?: string;
    macroContext?: ReturnType<typeof useCommandCenter>["macroContext"];
    confidence?: number;
    causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
    sectorRollups: ReturnType<typeof useCommandCenter>["sectorRollups"];
    decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
    trust?: ReturnType<typeof useCommandCenter>["trust"];
    locale: "en" | "ar";
  }
) {
  const isAr = locale === "ar";

  const sectionLabel = (en: string, ar: string) => (isAr ? ar : en);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>

      {/* 0. Macro Interpretation — "So What?" briefing block */}
      <div className="bg-[#1B1B19] text-white rounded-xl p-5 shadow-md">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-[10px]">IO</span>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-white">
                {isAr ? "ملخص المخاطر الاقتصادية الكلية" : "Macro Risk Briefing"}
              </h3>
              {scenario?.severity != null && (
                <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                  scenario.severity >= 0.80 ? "bg-red-500/20 text-red-300"
                  : scenario.severity >= 0.65 ? "bg-orange-500/20 text-orange-300"
                  : scenario.severity >= 0.50 ? "bg-yellow-500/20 text-yellow-300"
                  : "bg-green-500/20 text-green-300"
                }`}>
                  {scenario.severity >= 0.80 ? (isAr ? "حرج" : "SEVERE")
                    : scenario.severity >= 0.65 ? (isAr ? "عالٍ" : "HIGH")
                    : scenario.severity >= 0.50 ? (isAr ? "مرتفع" : "ELEVATED")
                    : (isAr ? "محدود" : "GUARDED")}
                </span>
              )}
            </div>
            <p className="text-xs text-white/60 mt-0.5">
              {scenario ? (isAr ? scenario.labelAr || scenario.label : scenario.label) : (isAr ? "جارٍ تحليل السيناريو..." : "Analysing scenario…")}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <p className="text-[10px] text-white/50 uppercase tracking-wider mb-1.5 font-semibold">
              {isAr ? "ما الذي حدث؟" : "What triggered this?"}
            </p>
            <p className="text-xs text-white/80 leading-relaxed">
              {isAr
                ? `اضطراب في ${scenario?.domain || "القطاع المالي"} أطلق موجة ضغط منهجية عبر مؤسسات ${headline?.nodesImpacted ?? "—"} عقدة متصلة.`
                : `A ${scenario?.domain || "financial"}-sector disruption triggered a systemic stress wave across ${headline?.nodesImpacted ?? "—"} connected institutional nodes.`}
            </p>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <p className="text-[10px] text-white/50 uppercase tracking-wider mb-1.5 font-semibold">
              {isAr ? "ماذا يعني ذلك للقرارات؟" : "What does it mean for decisions?"}
            </p>
            <p className="text-xs text-white/80 leading-relaxed">
              {isAr
                ? `الخسارة المتوقعة تبلغ $${headline ? (headline.totalLossUsd / 1e9).toFixed(1) : "—"}B خلال ${headline?.maxRecoveryDays ?? "—"} يوماً. نافذة القرار محدودة — التأخر يُضاعف الخسائر.`
                : `Projected loss of $${headline ? (headline.totalLossUsd / 1e9).toFixed(1) : "—"}B over ${headline?.maxRecoveryDays ?? "—"} days. Decision window is narrow — delay amplifies losses.`}
            </p>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <p className="text-[10px] text-white/50 uppercase tracking-wider mb-1.5 font-semibold">
              {isAr ? "لماذا مستوى الخطر مرتفع؟" : "Why is the regime ELEVATED?"}
            </p>
            <p className="text-xs text-white/80 leading-relaxed">
              {isAr
                ? `${headline?.criticalCount ?? "—"} عقدة حرجة و${headline?.elevatedCount ?? "—"} عقدة مرتفعة الخطر. عمق الانتشار ${headline?.propagationDepth ?? "—"} طبقة — فوق عتبة التدخل.`
                : `${headline?.criticalCount ?? "—"} critical nodes, ${headline?.elevatedCount ?? "—"} elevated. Propagation depth ${headline?.propagationDepth ?? "—"} layers — above intervention threshold.`}
            </p>
          </div>
        </div>

        {narrativeEn && !isAr && (
          <p className="text-xs text-white/60 leading-relaxed border-t border-white/10 pt-3">
            {narrativeEn.slice(0, 280)}{narrativeEn.length > 280 ? "…" : ""}
          </p>
        )}
        {narrativeAr && isAr && (
          <p className="text-xs text-white/60 leading-relaxed border-t border-white/10 pt-3">
            {narrativeAr.slice(0, 280)}{narrativeAr.length > 280 ? "…" : ""}
          </p>
        )}
      </div>

      {/* 1. Macro Shock */}
      {headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              1
            </span>
            {sectionLabel("Macro Shock", "الصدمة الكلية")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label={sectionLabel("Headline Loss", "الخسارة الرئيسية")}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-io-status-severe"
            />
            <MetricCard
              label={sectionLabel("Avg Stress", "متوسط الضغط")}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-io-status-elevated"
            />
            <MetricCard
              label={sectionLabel("Propagation Depth", "عمق الانتشار")}
              value={`${headline.propagationDepth}`}
              color="text-io-accent"
            />
            <MetricCard
              label={sectionLabel("Peak Day", "يوم الذروة")}
              value={`Day ${headline.peakDay}`}
              color="text-io-status-high"
            />
          </div>
        </div>
      )}

      {/* 1b. Macro-Financial Signals — derived from backend simulation engine */}
      {macroContext && macroContext.macro_signals && macroContext.macro_signals.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              &#9670;
            </span>
            {sectionLabel("Macro-Financial Signals", "الإشارات الاقتصادية والمالية الكلية")}
          </h3>
          {/* Trigger summary */}
          <p className="text-xs text-slate-600 mb-4">
            {isAr ? macroContext.trigger_summary_ar : macroContext.trigger_summary_en}
          </p>
          {/* Signal grid — all signals from backend, not capped */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {macroContext.macro_signals.map((signal: any) => {
              const impactColor = signal.impact === "high"
                ? "text-io-status-severe"
                : signal.impact === "medium"
                  ? "text-io-status-elevated"
                  : "text-io-secondary";
              const impactBg = signal.impact === "high"
                ? "bg-io-status-severe/5"
                : signal.impact === "medium"
                  ? "bg-io-status-elevated/5"
                  : "bg-slate-50";
              return (
                <div key={signal.id} className={`${impactBg} rounded-lg p-3`}>
                  <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-1">
                    {isAr ? signal.name_ar : signal.name_en}
                  </p>
                  <p className={`text-sm font-bold tabular-nums ${impactColor}`}>
                    {signal.value}
                  </p>
                  <div className="flex items-center gap-1 mt-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      signal.impact === "high" ? "bg-io-status-severe"
                        : signal.impact === "medium" ? "bg-io-status-elevated"
                          : "bg-io-tertiary"
                    }`} />
                    <span className="text-[9px] text-slate-400 uppercase">
                      {signal.impact}
                    </span>
                    {signal.status === "simulated" && (
                      <span className="text-[8px] px-1 py-0.5 rounded bg-purple-50 text-purple-500 font-medium ml-auto">
                        {isAr ? "محاكاة" : "sim"}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {/* System Risk Index */}
          <div className="mt-3 flex items-center gap-3 text-xs">
            <span className="px-2 py-1 rounded bg-io-status-severe/10 text-io-status-severe font-semibold">
              {isAr ? "مخاطر النظام" : "System Risk"}: {(macroContext.system_risk_index * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}

      {/* 2. Transmission Channels */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              2
            </span>
            {sectionLabel("Transmission Channels", "قنوات الانتقال")}
          </h3>
          <div className="space-y-2">
            {causalChain.slice(0, 5).map((link, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-slate-50 p-3 rounded-lg">
                <div className="text-xs font-semibold text-slate-500 mt-0.5">→</div>
                <div className="flex-1">
                  <p className="text-sm text-slate-700">{link.entity_label}: {link.event}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Sector Impact */}
      {sectorRollups && Object.keys(sectorRollups).length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              3
            </span>
            {sectionLabel("Sector Impact", "تأثير القطاع")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(sectorRollups).map(([sector, data]: any) => (
              <div key={sector} className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                  {sector}
                </p>
                <p className="text-sm font-bold text-slate-900">
                  {((data?.stress || 0) * 100).toFixed(0)}% stress
                </p>
                <p className="text-xs text-slate-600">
                  Loss: ${((data?.loss_usd || 0) / 1e9).toFixed(1)}B
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Entity Exposure */}
      {scenario && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              4
            </span>
            {sectionLabel("Entity Exposure", "تعريض الكيانات")}
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-700">
              {isAr
                ? `السيناريو: ${scenario.labelAr || scenario.label}`
                : `Scenario: ${scenario.label}`}
            </p>
            <p className="text-xs text-slate-600 mt-2">
              {isAr ? "الحساسية: " : "Sensitivity: "}
              <span className="font-semibold text-slate-700">
                {scenario.severity != null ? `${(scenario.severity * 100).toFixed(0)}%` : "N/A"}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* 5. Decision Actions */}
      {decisionActions && decisionActions.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              5
            </span>
            {sectionLabel("Decision Actions", "إجراءات القرار")}
          </h3>
          <div className="space-y-2">
            {decisionActions.slice(0, 5).map((action: any, idx: number) => (
              <div key={idx} className="bg-slate-50 p-3 rounded-lg">
                <p className="text-sm font-semibold text-slate-900">
                  {action.title || action.label || `Action ${idx + 1}`}
                </p>
                {action.rationale && (
                  <p className="text-xs text-slate-600 mt-1">{action.rationale}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Value / ROI */}
      {macroContext && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              6
            </span>
            {sectionLabel("Value / ROI", "القيمة / العائد")}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                {sectionLabel("System Risk Index", "مؤشر مخاطر النظام")}
              </p>
              <p className="text-lg font-bold text-io-status-severe">
                {macroContext.system_risk_index != null
                  ? `${(macroContext.system_risk_index * 100).toFixed(0)}%`
                  : "N/A"}
              </p>
            </div>
            {macroContext.macro_signals && macroContext.macro_signals.length > 0 && (
              <div className="bg-slate-50 rounded-lg p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  {sectionLabel("Active Signals", "الإشارات النشطة")}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {macroContext.macro_signals
                    .filter((s: any) => s.impact === "high" || s.impact === "medium")
                    .map((s: any) => (
                      <span
                        key={s.id}
                        className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                          s.impact === "high"
                            ? "bg-io-status-severe/10 text-io-status-severe"
                            : "bg-io-status-elevated/10 text-io-status-elevated"
                        }`}
                      >
                        {isAr ? s.name_ar : s.name_en}: {s.value}
                      </span>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 7. Trust / Confidence / Audit */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4">
          <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
            7
          </span>
          {sectionLabel("Trust / Confidence / Audit", "الثقة / الموثوقية / التدقيق")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Confidence", "الثقة")}
            </p>
            <p className="text-lg font-bold text-io-accent">
              {confidence != null ? `${(confidence * 100).toFixed(0)}%` : "N/A"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Methodology", "المنهجية")}
            </p>
            <p className="text-xs text-slate-600">
              {(trust as any)?.methodology_confidence
                ? `${((trust as any).methodology_confidence * 100).toFixed(0)}% confidence`
                : "Standard pipeline"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Data Quality", "جودة البيانات")}
            </p>
            <p className="text-xs text-slate-600">
              {(trust as any)?.data_quality_score
                ? `${((trust as any).data_quality_score * 100).toFixed(0)}% quality`
                : "Enterprise grade"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// INNER PAGE — reads searchParams, orchestrates tabs
// ══════════════════════════════════════════════════════════════

function CommandCenterInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const language = useAppStore((s) => s.language);
  const locale = language as "en" | "ar";

  const runId = searchParams.get("run");
  const activeTab = searchParams.get("tab") || "dashboard";
  const activeMode = searchParams.get("mode") ?? undefined;
  const [isRunningScenario, setIsRunningScenario] = useState(false);
  const [scenarioFallbackId, setScenarioFallbackId] = useState<string | null>(null);

  const {
    status,
    error,
    dataSource,
    scenario,
    headline,
    causalChain,
    sectorRollups,
    decisionActions,
    graphNodes,
    sectorImpacts,
    impacts,
    narrativeEn,
    confidence,
    trust,

    // Counterfactual analysis
    counterfactual,

    // Deep-dive data
    decisionTrust,
    decisionIntegration,
    decisionValue,
    governance,
    pilot,

    // Decision Trust Layer
    metricExplanations,
    decisionTransparencyResult,

    // Decision Reliability Layer
    reliabilityPayload,

    // Explainability Layer
    narrativeAr,
    macroContext,

    // Actions
    executeAction,
    switchToMock,
    switchToLive,
  } = useCommandCenter(runId);

  // ── Scenario selection: POST /api/v1/runs → navigate to new run ──
  const handleScenarioSelect = useCallback(
    async (templateId: string) => {
      setIsRunningScenario(true);
      setScenarioFallbackId(null);
      try {
        const result = await api.observatory.run({ template_id: templateId, severity: 0.75 });
        const newRunId = (result as any)?.data?.run_id ?? (result as any)?.run_id;
        if (newRunId) {
          router.push(`/command-center?run=${newRunId}`);
        }
      } catch {
        // Backend unavailable — load mock data but override the scenario label
        // so all downstream panels show the correct selected scenario name.
        switchToMock(templateId);
        setScenarioFallbackId(templateId);
      } finally {
        setIsRunningScenario(false);
      }
    },
    [router, switchToMock],
  );

  const handleSubmitForReview = useCallback(
    (actionId: string) => {
      executeAction(actionId);
    },
    [executeAction],
  );

  // ── State gates ──
  if (status === "loading") return <LoadingSkeleton />;
  if (status === "error" && !scenario) {
    return (
      <ErrorState
        error={error ?? "Unknown error"}
        onRetry={runId ? () => switchToLive(runId) : undefined}
        onFallbackMock={switchToMock}
      />
    );
  }

  // ── Derive country exposures from impacts for the map ──
  const countryExposures = useMemo(() => {
    if (!impacts?.length) return undefined;
    const exposures: Record<
      string,
      { stressLevel: number; lossUsd: number; dominantSector: string; entities: string[] }
    > = {};

    // Map sector-level impacts to countries
    const sectorToCountry: Record<string, string[]> = {
      banking: ["SA", "AE", "BH"],
      insurance: ["SA", "AE", "QA"],
      fintech: ["AE", "SA", "BH"],
      energy: ["SA", "QA", "KW"],
      logistics: ["OM", "AE", "QA"],
    };

    for (const impact of impacts) {
      const countries = sectorToCountry[impact.sector] || ["SA"];
      for (const cc of countries) {
        if (!exposures[cc]) {
          exposures[cc] = {
            stressLevel: 0,
            lossUsd: 0,
            dominantSector: impact.sector,
            entities: [],
          };
        }
        exposures[cc].stressLevel = Math.max(exposures[cc].stressLevel, impact.stressLevel);
        exposures[cc].lossUsd += (impact.lossUsd || 0) / countries.length;
      }
    }
    return Object.keys(exposures).length > 0 ? exposures : undefined;
  }, [impacts]);

  // ── Derive BankingStress from impacts (fills sector detail panel) ──
  const bankingStress = useMemo((): BankingStress | undefined => {
    const b = impacts?.find((i) => i.sector === "banking");
    if (!b) return undefined;
    return {
      run_id: runId ?? "mock",
      total_exposure_usd: b.lossUsd,
      liquidity_stress: b.lcr ? Math.max(0, 1 - b.lcr) : 0.40,
      credit_stress: 0.55,
      fx_stress: 0.28,
      interbank_contagion: 0.62,
      time_to_liquidity_breach_hours: 48,
      capital_adequacy_impact_pct: b.cet1Ratio ? Math.max(0, (0.20 - b.cet1Ratio) * 100) : 6,
      aggregate_stress: b.stressLevel,
      classification: b.stressTier as any,
      affected_institutions: [],
    };
  }, [impacts, runId]);

  // ── Derive InsuranceStress from impacts (fills sector detail panel) ──
  const insuranceStress = useMemo((): InsuranceStress | undefined => {
    const ins = impacts?.find((i) => i.sector === "insurance");
    if (!ins) return undefined;
    return {
      run_id: runId ?? "mock",
      portfolio_exposure_usd: ins.lossUsd,
      claims_surge_multiplier: 2.4,
      severity_index: ins.stressLevel,
      loss_ratio: 0.78,
      combined_ratio: ins.combinedRatio || 1.05,
      underwriting_status: "STRESSED",
      time_to_insolvency_hours: 96,
      reinsurance_trigger: true,
      ifrs17_risk_adjustment_pct: 0.12,
      aggregate_stress: ins.stressLevel,
      classification: ins.stressTier as any,
      affected_lines: [],
    };
  }, [impacts, runId]);

  // ── Render active tab content ──
  const renderTabContent = () => {
    switch (activeTab) {
      case "scenarios":
        return (
          <div className="p-6 max-w-7xl mx-auto">
            <ScenarioLibrary
              onSelectScenario={handleScenarioSelect}
              isLoading={isRunningScenario}
              locale={locale}
            />
          </div>
        );

      case "macro":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-slate-500 text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من لوحة المعلومات"
                : "No scenario data — select a scenario from the Dashboard"}
            </div>
          );
        }
        return (
          <MacroIntelligenceView
            scenario={scenario}
            headline={headline}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr}
            macroContext={macroContext}
            confidence={confidence}
            causalChain={causalChain}
            sectorRollups={sectorRollups}
            decisionActions={decisionActions}
            trust={trust}
            locale={locale}
          />
        );

      case "propagation":
        return (
          <PropagationView
            locale={locale}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            totalLossUsd={headline?.totalLossUsd}
            causalChain={causalChain}
          />
        );

      case "map": {
        const isAr = locale === "ar";
        return (
          <div className="p-6 max-w-7xl mx-auto space-y-5">
            {/* GCC Exposure Interpretation Block */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-start gap-3 mb-4">
                <div className="w-8 h-8 rounded-lg bg-[#1B1B19] flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold text-[10px]">GCC</span>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    {isAr ? "لماذا تتعرض دول مجلس التعاون الخليجي كلها لهذا؟" : "Why All 6 GCC Countries Are Exposed"}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {isAr
                      ? "ترابط منهجي — المخاطر تنتقل عبر القنوات المالية والتجارية والطاقة"
                      : "Systemic interconnection — risk propagates across financial, trade, and energy channels"}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div className="bg-orange-50 border border-orange-100 rounded-lg p-3">
                  <p className="text-[10px] font-bold text-orange-700 uppercase tracking-wider mb-1">
                    {isAr ? "قناة الطاقة" : "Energy Channel"}
                  </p>
                  <p className="text-xs text-slate-700">
                    {isAr
                      ? "الهيدروكربونات تشكّل 50-70٪ من إيرادات الدولة. اضطراب التصدير يضغط مباشرة على الميزانيات السيادية."
                      : "Hydrocarbons represent 50–70% of state revenue. Export disruption directly pressures sovereign budgets."}
                  </p>
                </div>
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                  <p className="text-[10px] font-bold text-blue-700 uppercase tracking-wider mb-1">
                    {isAr ? "قناة التجارة" : "Trade Channel"}
                  </p>
                  <p className="text-xs text-slate-700">
                    {isAr
                      ? "60٪+ من واردات السلع يمر عبر ممرات بحرية مشتركة. إغلاق أي مسار رئيسي يؤثر على سلاسل التوريد الإقليمية."
                      : "60%+ of goods imports transit shared maritime corridors. Closure of any major route disrupts regional supply chains."}
                  </p>
                </div>
                <div className="bg-purple-50 border border-purple-100 rounded-lg p-3">
                  <p className="text-[10px] font-bold text-purple-700 uppercase tracking-wider mb-1">
                    {isAr ? "قناة التمويل" : "Financial Channel"}
                  </p>
                  <p className="text-xs text-slate-700">
                    {isAr
                      ? "البنوك الإقليمية المترابطة والتعرض المشترك لصناديق الثروة السيادية ينشر الضغط عبر الحدود."
                      : "Interconnected regional banks and shared sovereign wealth fund exposure spread stress across borders."}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                {[
                  { flag: "🇸🇦", code: "SA", name: isAr ? "السعودية" : "Saudi Arabia", role: isAr ? "مصدر الصدمة الأساسي" : "Primary shock origin", color: "border-red-300" },
                  { flag: "🇦🇪", code: "AE", name: isAr ? "الإمارات" : "UAE", role: isAr ? "مركز تمويلي مرتبط" : "Linked financial hub", color: "border-orange-300" },
                  { flag: "🇰🇼", code: "KW", name: isAr ? "الكويت" : "Kuwait", role: isAr ? "ضغط على الميزانية النفطية" : "Oil budget pressure", color: "border-amber-300" },
                  { flag: "🇶🇦", code: "QA", name: isAr ? "قطر" : "Qatar", role: isAr ? "خسائر تصدير الغاز" : "LNG export losses", color: "border-yellow-300" },
                  { flag: "🇧🇭", code: "BH", name: isAr ? "البحرين" : "Bahrain", role: isAr ? "تدفق مخاطر إعادة التأمين" : "Reinsurance risk spill", color: "border-blue-300" },
                  { flag: "🇴🇲", code: "OM", name: isAr ? "عُمان" : "Oman", role: isAr ? "اضطراب مينائي وتجاري" : "Port & trade disruption", color: "border-green-300" },
                ].map((c) => (
                  <div key={c.code} className={`bg-slate-50 border ${c.color} rounded-lg p-2 text-center`}>
                    <span className="text-lg block mb-0.5">{c.flag}</span>
                    <p className="text-[10px] font-bold text-slate-800">{c.name}</p>
                    <p className="text-[9px] text-slate-500 leading-tight mt-0.5">{c.role}</p>
                  </div>
                ))}
              </div>

              <p className="text-[10px] text-slate-400 mt-3 border-t border-slate-100 pt-2">
                {isAr
                  ? "⚠ المخاطر العابرة للحدود: الصدمة الأولية تضاعف من خلال شبكات التعرض السيادية البينية"
                  : "⚠ Cross-border contagion: primary shock amplified through sovereign inter-exposure networks"}
              </p>
            </div>

            <GCCImpactMap
              countryExposures={countryExposures}
              sectorRollups={
                sectorRollups as unknown as
                  | Record<string, { stress: number; loss_usd: number }>
                  | undefined
              }
              scenarioLabel={scenario?.label}
              locale={locale}
            />
          </div>
        );
      }

      case "sectors":
        return (
          <SectorIntelligenceView
            locale={locale}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr ?? undefined}
            systemRiskIndex={macroContext?.system_risk_index}
            macroSignals={macroContext?.macro_signals}
            causalChain={causalChain}
            decisionActions={decisionActions as any}
            bankingStress={bankingStress}
            insuranceStress={insuranceStress}
          />
        );

      case "decisions":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-slate-500 text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من لوحة المعلومات"
                : "No scenario data — select a scenario from the Dashboard"}
            </div>
          );
        }
        return (
          <div className="p-6">
            <DecisionRoomV2
              runId={runId ?? undefined}
              scenarioLabel={scenario.label}
              scenarioLabelAr={scenario.labelAr ?? ""}
              severity={String(scenario.severity)}
              totalLossUsd={headline.totalLossUsd}
              averageStress={headline.averageStress}
              propagationDepth={headline.propagationDepth}
              peakDay={headline.peakDay}
              causalChain={causalChain}
              decisionActions={decisionActions}
              sectorRollups={sectorRollups}
              locale={locale}
              metricExplanations={metricExplanations}
              decisionTransparency={decisionTransparencyResult ?? undefined}
              reliability={reliabilityPayload ?? undefined}
              confidenceScore={confidence}
              narrativeEn={narrativeEn}
              narrativeAr={narrativeAr ?? ""}
              macroContext={macroContext ?? undefined}
              trustInfo={trust ?? undefined}
              counterfactual={counterfactual ?? undefined}
              onSubmitForReview={handleSubmitForReview}
            />
          </div>
        );

      case "audit":
        return (
          <RegulatoryAuditView
            locale={locale}
            runId={runId ?? undefined}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            horizonHours={scenario?.horizonHours}
            trustInfo={trust ?? undefined}
            decisionActions={decisionActions}
          />
        );

      // Dashboard (default)
      default:
        return (
          <DashboardView
            scenario={scenario}
            headline={headline}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr ?? undefined}
            macroContext={macroContext}
            confidence={confidence}
            causalChain={causalChain}
            sectorRollups={sectorRollups}
            decisionActions={decisionActions}
            locale={locale}
            onSelectScenario={handleScenarioSelect}
            isRunningScenario={isRunningScenario}
          />
        );
    }
  };

  // ── Experience mode shortcircuit ──
  if (activeMode === "experience") {
    return (
      <ObservatoryShell
        scenarioLabel={scenario?.label}
        scenarioLabelAr={scenario?.labelAr ?? undefined}
        dataSource={dataSource}
        activeTab={activeTab}
        activeMode={activeMode}
      >
        <TraceImpactExperience
          locale={locale}
          runId={runId}
          headline={headline}
        />
      </ObservatoryShell>
    );
  }

  return (
    <ObservatoryShell
      scenarioLabel={scenario?.label}
      scenarioLabelAr={scenario?.labelAr ?? undefined}
      dataSource={dataSource}
      activeTab={activeTab}
      activeMode={activeMode}
    >
      {/* Fallback banner (API failed, showing mock) */}
      {error && scenario && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-amber-50 border-b border-amber-200 flex-shrink-0">
          <p className="text-[11px] text-amber-700 truncate">{error}</p>
          {runId && (
            <button
              onClick={() => switchToLive(runId)}
              className="ml-3 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-amber-100 text-amber-800 hover:bg-amber-200 transition-colors"
            >
              Retry Live
            </button>
          )}
        </div>
      )}

      {/* Scenario fallback banner (backend unreachable on scenario selection) */}
      {scenarioFallbackId && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-amber-50 border-b border-amber-200 flex-shrink-0">
          <p className="text-[11px] text-amber-700">
            {locale === "ar"
              ? `الخادم غير متاح — يتم عرض بيانات تجريبية للسيناريو: ${scenarioFallbackId.replace(/_/g, " ")}`
              : `Live backend unavailable — showing demo data for: ${scenarioFallbackId.replace(/_/g, " ")}`}
          </p>
          <button
            onClick={() => setScenarioFallbackId(null)}
            className="ml-3 flex-shrink-0 text-[10px] text-amber-700 hover:text-amber-900 font-semibold transition-colors"
          >
            ✕
          </button>
        </div>
      )}

      {/* Scenario quick-switcher (compact pill bar) */}
      {scenario && activeTab !== "dashboard" && (
        <div className="px-6 pt-3">
          <ScenarioSelector
            activeScenarioId={scenario.templateId}
            onSelect={handleScenarioSelect}
            isLoading={isRunningScenario}
            locale={locale}
          />
        </div>
      )}

      {/* Active tab content */}
      {renderTabContent()}

      {/* Status Bar */}
      <StatusBar dataSource={dataSource} trust={trust} confidence={confidence} />
    </ObservatoryShell>
  );
}

// ── Page Export ──

export default function CommandCenterPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <CommandCenterInner />
    </Suspense>
  );
}
