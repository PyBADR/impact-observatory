"use client";

/**
 * Impact Observatory | مرصد الأثر — Command Center
 *
 * EXECUTIVE SURFACE (Batch 2):
 * ┌─────────────────────────────────────────────────────────────┐
 * │  DEFAULT: SovereignBriefing — executive command surface      │
 * ├─────────────────────────────────────────────────────────────┤
 * │  TAB: Propagation   → Causal chain narrative                │
 * │  TAB: Decision      → Mandate + directives                  │
 * │  TAB: Monitoring    → Governance + accountability            │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 4 tabs. One command flow. No analyst toolbox.
 */

import React, { Suspense, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";

// ── Shell ──
import { ObservatoryShell } from "@/components/shell/ObservatoryShell";

// ── Canonical Intelligence Surface ──
import { SovereignBriefing } from "@/features/command-center/components/SovereignBriefing";
import { useSovereignBriefing } from "@/features/command-center/lib/use-sovereign-briefing";


// ── Executive Tabs ──
import { PropagationView } from "@/components/panels/PropagationView";
import { DecisionRoomV2 } from "@/components/provenance/DecisionRoomV2";
import { RegulatoryAuditView } from "@/components/panels/RegulatoryAuditView";

// ── Loading Skeleton ──

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-[#0071e3]/30 border-t-[#0071e3] rounded-full animate-spin" />
        <p className="text-sm text-[#6e6e73]">Loading intelligence pipeline...</p>
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
    <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-[#e5e5e7] border border-[#d6d6db] flex items-center justify-center mx-auto mb-4">
          <span className="text-[#0071e3] text-lg">!</span>
        </div>
        <h2 className="text-sm font-semibold text-[#1d1d1f] mb-2">Pipeline Error</h2>
        <p className="text-xs text-[#6e6e73] mb-4">{error}</p>
        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#e5e5e7] text-[#1d1d1f] border border-[#d6d6db] hover:border-[#3a3a3e] transition-colors"
            >
              Retry
            </button>
          )}
          {onFallbackMock && (
            <button
              onClick={onFallbackMock}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#e5e5e7] text-[#515154] border border-[#d6d6db] hover:border-[#3a3a3e] transition-colors"
            >
              Load Simulation
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// INNER PAGE — reads searchParams, orchestrates 4 executive tabs
// ══════════════════════════════════════════════════════════════

function CommandCenterInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const language = useAppStore((s) => s.language);
  const locale = language as "en" | "ar";

  const runId = searchParams.get("run");
  // Default is NO tab — the executive lands on SovereignBriefing directly.
  // Analyst tabs are only shown when explicitly selected via ?tab=...
  const activeTab = searchParams.get("tab") || "";

  // ── Canonical intelligence surface ──
  const briefing = useSovereignBriefing();

  const {
    status,
    error,
    dataSource,
    scenario,
    headline,
    causalChain,
    sectorRollups,
    decisionActions,
    narrativeEn,
    confidence,
    trust,

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

  // ── Render active tab content ──
  const renderTabContent = () => {
    switch (activeTab) {
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

      case "decision":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-[#6e6e73] text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من الإحاطة"
                : "No scenario data — select a scenario from the Briefing"}
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
              onSubmitForReview={handleSubmitForReview}
            />
          </div>
        );

      case "monitoring":
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

      // Default: Executive lands on SovereignBriefing
      default:
        if (briefing) {
          return <SovereignBriefing briefing={briefing} />;
        }
        // No briefing data yet → show controlled executive empty state
        return (
          <div className="min-h-[60vh] flex items-center justify-center px-6">
            <div className="max-w-xl text-center">
              <div className="w-12 h-12 rounded-xl bg-[#e5e5e7] border border-[#d6d6db] flex items-center justify-center mx-auto mb-5">
                <span className="text-[#0071e3] text-lg">·</span>
              </div>
              <h2 className="text-[1.125rem] font-semibold text-[#1d1d1f] mb-3">
                {locale === "ar" ? "لا توجد إحاطة جاهزة بعد" : "No briefing available yet"}
              </h2>
              <p className="text-[0.9375rem] leading-relaxed text-[#6e6e73] mb-6">
                {locale === "ar"
                  ? "لم يتم تكوين سطح الإحاطة بعد. أعد المحاولة أو حمّل المحاكاة داخل نفس البيئة التنفيذية."
                  : "The executive briefing surface has not been assembled yet. Retry the run or load the simulation inside the same command environment."}
              </p>
              <div className="flex items-center justify-center gap-3">
                {runId && (
                  <button
                    onClick={() => switchToLive(runId)}
                    className="px-4 py-2 text-[0.8125rem] font-semibold rounded-md bg-[#1d1d1f] text-[#f5f5f7] hover:bg-white transition-colors"
                  >
                    {locale === "ar" ? "إعادة المحاولة" : "Retry Live"}
                  </button>
                )}
                <button
                  onClick={switchToMock}
                  className="px-4 py-2 text-[0.8125rem] font-semibold rounded-md border border-[#d6d6db] text-[#515154] hover:text-[#1d1d1f] hover:border-[#3a3a3e] transition-colors"
                >
                  {locale === "ar" ? "تحميل المحاكاة" : "Load Simulation"}
                </button>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <ObservatoryShell
      scenarioLabel={scenario?.label}
      scenarioLabelAr={scenario?.labelAr ?? undefined}
      dataSource={dataSource}
      activeTab={activeTab}
    >
      {/* Fallback banner (API failed, showing mock) */}
      {error && scenario && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-[#e5e5e7] border-b border-[#d6d6db] flex-shrink-0">
          <p className="text-[11px] text-[#0071e3] truncate">{error}</p>
          {runId && (
            <button
              onClick={() => switchToLive(runId)}
              className="ml-3 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-[#d6d6db] text-[#515154] hover:text-[#1d1d1f] transition-colors"
            >
              Retry Live
            </button>
          )}
        </div>
      )}

      {/* Active tab content */}
      {renderTabContent()}
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
