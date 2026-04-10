"use client";

/**
 * Decision Command Center — مركز القرار
 *
 * Product Surface: Single-screen decision intelligence terminal.
 *
 * Architecture:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  DECISION ROOM V2 (primary operating surface)               │
 * │  ├─ Level 1: Executive Snapshot (always visible)            │
 * │  ├─ Level 2: Decision Cards + Sector Stress (expandable)    │
 * │  └─ Level 3: Propagation Chain (full detail)                │
 * ├─────────────────────────────────────────────────────────────┤
 * │  OPERATIONAL INTELLIGENCE (scroll-to-reveal)                │
 * │  ├─ Decision Trust    ├─ Workflows   ├─ CFO Value           │
 * │  ├─ Evidence & Gov    ├─ Pilot       └─ Banking Intel       │
 * ├─────────────────────────────────────────────────────────────┤
 * │  STATUS BAR                                                 │
 * └─────────────────────────────────────────────────────────────┘
 *
 * Data flow:
 *   ?run=<id>  →  useCommandCenter(runId)  →  live UnifiedRunResult
 *   no param   →  useCommandCenter(null)   →  deterministic mock data
 *
 * DecisionRoomV2 is THE interface. No duplicate entry points.
 */

import React, { Suspense, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";

// ── Primary Surface ──
import { DecisionRoomV2 } from "@/components/provenance/DecisionRoomV2";

// ── Operational Intelligence (deep-dive, non-duplicate) ──
import { DecisionTrustPanel } from "@/features/command-center/components/DecisionTrustPanel";
import { WorkflowPanel } from "@/features/command-center/components/WorkflowPanel";
import { LifecyclePanel } from "@/features/command-center/components/LifecyclePanel";
import { CFOValuePanel } from "@/features/command-center/components/CFOValuePanel";
import { EvidenceGovernancePanel } from "@/features/command-center/components/EvidenceGovernancePanel";
import { PilotPanel } from "@/features/command-center/components/PilotPanel";
import { BankingDecisionView } from "@/features/banking/BankingDecisionView";

// ── Chrome ──
import { StatusBar } from "@/features/command-center/components/StatusBar";
import { DemoFlow } from "@/features/command-center/components/DemoFlow";

// ── Loading Skeleton ──────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[#060910] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-sm text-slate-500">Loading intelligence pipeline...</p>
      </div>
    </div>
  );
}

// ── Error State ───────────────────────────────────────────────────────

function ErrorState({
  error,
  onRetry,
  onFallbackMock,
}: {
  error: string;
  onRetry?: () => void;
  onFallbackMock?: () => void;
}) {
  return (
    <div className="min-h-screen bg-[#060910] flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-500 text-lg">!</span>
        </div>
        <h2 className="text-sm font-semibold text-white mb-2">
          Pipeline Error
        </h2>
        <p className="text-xs text-slate-400 mb-4">{error}</p>
        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors"
            >
              Retry
            </button>
          )}
          {onFallbackMock && (
            <button
              onClick={onFallbackMock}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
            >
              Load Demo Data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Empty State ──────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="min-h-screen bg-[#060910] flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-slate-500/10 border border-slate-500/20 flex items-center justify-center mx-auto mb-4">
          <span className="text-slate-500 text-lg">?</span>
        </div>
        <h2 className="text-sm font-semibold text-white mb-2">
          No Simulation Data
        </h2>
        <p className="text-xs text-slate-400">
          Run a scenario from the Observatory to populate this view, or remove the
          &ldquo;run&rdquo; parameter to load demo data.
        </p>
      </div>
    </div>
  );
}

// ── Operational Intelligence Section ─────────────────────────────────

function OperationalIntelligence({
  runId,
  scenarioId,
  decisionTrust,
  decisionIntegration,
  decisionValue,
  governance,
  pilot,
}: {
  runId: string | null;
  scenarioId: string | undefined;
  decisionTrust: ReturnType<typeof useCommandCenter>["decisionTrust"];
  decisionIntegration: ReturnType<typeof useCommandCenter>["decisionIntegration"];
  decisionValue: ReturnType<typeof useCommandCenter>["decisionValue"];
  governance: ReturnType<typeof useCommandCenter>["governance"];
  pilot: ReturnType<typeof useCommandCenter>["pilot"];
}) {
  const [expanded, setExpanded] = useState(false);

  const hasData =
    decisionTrust || decisionIntegration || decisionValue || governance || pilot;

  if (!hasData) return null;

  return (
    <div className="border-t border-slate-800/60">
      {/* Toggle header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-3 hover:bg-slate-800/20 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-600" />
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Operational Intelligence
          </span>
          <span className="text-[10px] text-slate-600">
            Trust · Workflows · Value · Governance · Pilot
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-slate-500 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Panels */}
      {expanded && (
        <div className="space-y-0">
          <DecisionTrustPanel trust={decisionTrust} />

          <WorkflowPanel
            workflows={decisionIntegration?.workflows}
            ownerships={decisionIntegration?.decision_ownership}
          />
          <LifecyclePanel
            lifecycles={decisionIntegration?.decision_lifecycle}
            triggers={decisionIntegration?.execution_triggers}
            integration={decisionIntegration?.integration}
          />

          <CFOValuePanel value={decisionValue} />

          <EvidenceGovernancePanel governance={governance} />

          <PilotPanel pilot={pilot} />

          <BankingDecisionView
            runId={runId}
            scenarioId={scenarioId}
            lang="en"
          />
        </div>
      )}
    </div>
  );
}

// ── Inner Page (reads searchParams) ───────────────────────────────────

function CommandCenterInner() {
  const searchParams = useSearchParams();
  const runId = searchParams.get("run");

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

    // Phase 2-6 deep-dive data
    decisionTrust,
    decisionIntegration,
    decisionValue,
    governance,
    pilot,

    // Decision Trust Layer (Sprint 1)
    metricExplanations,
    decisionTransparencyResult,

    // Decision Reliability Layer (Sprint 2)
    reliabilityPayload,

    // Actions
    executeAction,
    switchToMock,
    switchToLive,
  } = useCommandCenter(runId);

  const [presentationMode, setPresentationMode] = useState(false);

  const handleSubmitForReview = useCallback(
    (actionId: string) => {
      executeAction(actionId);
    },
    [executeAction],
  );

  // ---- State gates ----
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
  if (!scenario || !headline) return <EmptyState />;

  return (
    <div className="h-screen bg-[#060910] text-slate-200 flex flex-col overflow-y-auto overflow-x-hidden">
      {/* ── Presentation Mode Overlay ── */}
      {presentationMode && (
        <DemoFlow
          scenarioLabel={scenario.label}
          scenarioLabelAr={scenario.labelAr ?? undefined}
          domain={scenario.domain}
          severity={scenario.severity}
          horizonHours={scenario.horizonHours}
          systemRiskIndex={headline.averageStress}
          totalLossUsd={headline.totalLossUsd}
          nodesImpacted={headline.nodesImpacted}
          criticalCount={headline.criticalCount}
          elevatedCount={headline.elevatedCount}
          confidence={confidence}
          causalChain={causalChain}
          sectorImpacts={sectorImpacts}
          graphNodes={graphNodes}
          decisionActions={decisionActions}
          impacts={impacts}
          narrativeEn={narrativeEn}
          auditHash={trust?.auditHash}
          modelVersion={trust?.modelVersion}
          stagesCompleted={trust?.stagesCompleted}
          onExit={() => setPresentationMode(false)}
        />
      )}

      {/* ── Fallback banner (API failed, showing mock) ── */}
      {error && scenario && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-amber-500/10 border-b border-amber-500/20 flex-shrink-0">
          <p className="text-[11px] text-amber-400 truncate">{error}</p>
          {runId && (
            <button
              onClick={() => switchToLive(runId)}
              className="ml-3 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-amber-600/20 text-amber-300 hover:bg-amber-600/30 transition-colors"
            >
              Retry Live
            </button>
          )}
        </div>
      )}

      {/* ── Top Bar: data source indicator + presentation toggle ── */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 pt-3 pb-1">
        <div className="flex items-center gap-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              dataSource === "live" ? "bg-emerald-500" : "bg-amber-500"
            }`}
          />
          <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
            {dataSource === "live" ? "Live Intelligence" : "Demo Mode"}
          </span>
        </div>
        <button
          onClick={() => setPresentationMode(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-semibold rounded-md bg-slate-800/50 border border-slate-700/50 text-slate-400 hover:text-slate-300 hover:border-slate-600/50 transition-all"
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          Present
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           PRIMARY OPERATING SURFACE: Decision Room V2
           ═══════════════════════════════════════════════════════════════ */}
      <div className="flex-1 px-6 py-4">
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
          locale="en"
          metricExplanations={metricExplanations}
          decisionTransparency={decisionTransparencyResult ?? undefined}
          reliability={reliabilityPayload ?? undefined}
          onSubmitForReview={handleSubmitForReview}
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           OPERATIONAL INTELLIGENCE (collapsed, scroll-to-reveal)
           Non-duplicate deep-dive panels: Trust, Workflows, Value,
           Evidence, Governance, Pilot, Banking Intelligence.
           ═══════════════════════════════════════════════════════════════ */}
      <OperationalIntelligence
        runId={runId}
        scenarioId={scenario.templateId}
        decisionTrust={decisionTrust}
        decisionIntegration={decisionIntegration}
        decisionValue={decisionValue}
        governance={governance}
        pilot={pilot}
      />

      {/* ── Status Bar ── */}
      <StatusBar
        dataSource={dataSource}
        trust={trust}
        confidence={confidence}
      />
    </div>
  );
}

// ── Page Export (Suspense-wrapped for useSearchParams) ─────────────────

export default function CommandCenterPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <CommandCenterInner />
    </Suspense>
  );
}
