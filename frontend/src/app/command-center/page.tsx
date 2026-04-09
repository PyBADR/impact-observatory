"use client";

/**
 * Decision Command Center — Macro-First Intelligence Terminal
 *
 * Product Surface: Decision Intelligence (NOT pipeline/log viewer)
 *
 * Layout (6-zone vertical hierarchy):
 * ┌───────────────────────────────────────────────────────────┐
 * │  1. GCC MACRO OVERVIEW (hero)                             │
 * │     System Risk | Exposure | Critical Nodes | Confidence  │
 * ├───────────────────────────────────────────────────────────┤
 * │  2. TRANSMISSION CHANNELS                                 │
 * │     Oil & Energy | Liquidity & FX | Trade & Ports | Ins   │
 * ├───────────────────────────────────────────────────────────┤
 * │  3. COUNTRY & SECTOR EXPOSURE                             │
 * │     By Country (6 GCC) | By Sector                        │
 * ├───────────────────────────────────────────────────────────┤
 * │  4. DECISION PRIORITIES ← PRIMARY FOCUS                   │
 * │     Full-width cards, cost vs benefit bars, loss flags     │
 * │     Visible without scrolling on most screens              │
 * ├───────────────────────────────────────────────────────────┤
 * │  5. TRUST LAYER                                           │
 * │     Confidence | Pipeline | Model | Sources | Audit Hash  │
 * ├───────────────────────────────────────────────────────────┤
 * │  6. OPERATIONAL DETAIL (tabbed, collapsible)               │
 * │     [Graph] [Propagation] [Sectors] [Explanation]          │
 * ├───────────────────────────────────────────────────────────┤
 * │  STATUS BAR                                               │
 * └───────────────────────────────────────────────────────────┘
 *
 * Design rules:
 *   - No tables at the top
 *   - No logs in primary view
 *   - No pipeline-first rendering
 *   - Decision visible without scrolling
 *   - Cost vs benefit prominent
 *   - Loss-inducing actions flagged
 *
 * Data flow: single pipeline, no duplication, no extra API calls.
 *   ?run=<id>  →  useCommandCenter(runId)  →  live UnifiedRunResult
 *   no param   →  useCommandCenter(null)   →  deterministic mock data
 */

import React, { Suspense, useMemo, useCallback, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";
import { MacroOverviewHeader } from "@/features/command-center/components/MacroOverviewHeader";
import { TransmissionChannels } from "@/features/command-center/components/TransmissionChannels";
import { ExposureLayer } from "@/features/command-center/components/ExposureLayer";
import { DecisionPriorities } from "@/features/command-center/components/DecisionPriorities";
import { TrustStrip } from "@/features/command-center/components/TrustStrip";
import { OperationalDetail } from "@/features/command-center/components/OperationalDetail";
import { StatusBar } from "@/features/command-center/components/StatusBar";
import { DemoFlow } from "@/features/command-center/components/DemoFlow";
import { BoardView } from "@/features/command-center/components/BoardView";

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
    graphNodes,
    graphEdges,
    causalChain,
    sectorImpacts,
    sectorRollups,
    decisionActions,
    impacts,
    narrativeEn,
    narrativeAr,
    methodology,
    confidence,
    totalSteps,
    trust,
    selectedNodeId,
    selectNode,
    executeAction,
    switchToMock,
    switchToLive,
  } = useCommandCenter(runId);

  const isLive = dataSource === "live";
  const [presentationMode, setPresentationMode] = useState(false);

  // ── Memoized derivations (avoid new-ref-per-render) ──
  const affectedRegions = useMemo(
    () =>
      graphNodes
        .filter((n) => n.layer === "geography" || n.layer === "infrastructure")
        .map((n) => n.label)
        .filter((v, i, a) => a.indexOf(v) === i),
    [graphNodes],
  );

  // ── Exposure → Graph bridge: clicking a country selects its highest-stress node ──
  const handleCountrySelect = useCallback(
    (countryId: string) => {
      const countryNodes = graphNodes.filter((n) => {
        const lat = typeof n.lat === "number" && isFinite(n.lat) ? n.lat : 0;
        const lng = typeof n.lng === "number" && isFinite(n.lng) ? n.lng : 0;
        const boxes: Record<string, [number, number, number, number]> = {
          BH: [25.8, 26.3, 50.3, 50.7],
          QA: [24.5, 26.2, 50.7, 51.7],
          KW: [28.5, 30.1, 46.5, 48.5],
          AE: [22.6, 26.1, 51.6, 56.4],
          OM: [16.6, 26.4, 52.0, 59.8],
          SA: [16.0, 32.2, 34.5, 55.7],
        };
        const box = boxes[countryId];
        if (!box) return false;
        return lat >= box[0] && lat <= box[1] && lng >= box[2] && lng <= box[3];
      });
      const sorted = [...countryNodes].sort(
        (a, b) => ((b.stress as number) ?? 0) - ((a.stress as number) ?? 0),
      );
      if (sorted.length > 0) selectNode(sorted[0].id);
    },
    [graphNodes, selectNode],
  );

  const handleSectorSelect = useCallback(
    (sectorId: string) => {
      const match = graphNodes.find((n) => n.layer === sectorId);
      if (match) selectNode(match.id);
    },
    [graphNodes, selectNode],
  );

  // ---- Panel states: loading → error → empty → ready ----
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
      {presentationMode && scenario && headline && (
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

      {/* ── Presentation Mode Toggle ── */}
      <div className="flex-shrink-0 flex items-center justify-end px-6 pt-2 pb-0 bg-[#0B0F1A]">
        <button
          onClick={() => setPresentationMode(true)}
          className="flex items-center gap-2 px-4 py-2 text-[11px] font-semibold rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 hover:bg-blue-600/30 hover:border-blue-500/50 transition-all"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          Presentation Mode
        </button>
      </div>

      {/* ── BOARD VIEW: Executive Decision Card ──────────── */}
      {scenario.templateId && (
        <div className="flex-shrink-0 px-6 pb-2 bg-[#0B0F1A]">
          <BoardView
            scenarioId={scenario.templateId}
            severity={scenario.severity}
            horizonHours={scenario.horizonHours}
          />
        </div>
      )}

      {/* ── ZONE 1: GCC Macro Overview (hero) ───────────── */}
      <MacroOverviewHeader
        systemRiskIndex={headline.averageStress}
        totalExposureUsd={headline.totalLossUsd}
        affectedRegions={affectedRegions}
        nodesImpacted={headline.nodesImpacted}
        criticalCount={headline.criticalCount}
        elevatedCount={headline.elevatedCount}
        confidence={confidence}
        averageStress={headline.averageStress}
        scenarioLabel={scenario.label}
        scenarioLabelAr={scenario.labelAr ?? undefined}
        domain={scenario.domain}
        severity={scenario.severity}
        horizonHours={scenario.horizonHours}
        triggerTime={scenario.triggerTime}
        pipelineStages={trust?.stagesCompleted ?? []}
      />

      {/* ── ZONE 2: Transmission Channels ───────────────── */}
      <TransmissionChannels
        nodes={graphNodes}
        edges={graphEdges}
      />

      {/* ── ZONE 3: Country & Sector Exposure ──────────── */}
      <ExposureLayer
        nodes={graphNodes}
        impacts={impacts}
        onCountrySelect={handleCountrySelect}
        onSectorSelect={handleSectorSelect}
      />

      {/* ── ZONE 4: Decision Priorities (PRIMARY FOCUS) ── */}
      <DecisionPriorities
        actions={decisionActions}
        onExecute={executeAction}
        isLive={isLive}
      />

      {/* ── ZONE 5: Trust Layer ─────────────────────────── */}
      <TrustStrip
        trust={trust}
        confidence={confidence}
        methodology={methodology}
        narrativeEn={narrativeEn}
        warnings={trust?.warnings}
      />

      {/* ── ZONE 6: Operational Detail (tabbed) ─────────── */}
      <OperationalDetail
        graphNodes={graphNodes}
        graphEdges={graphEdges}
        selectedNodeId={selectedNodeId}
        onNodeSelect={selectNode}
        causalChain={causalChain}
        sectorImpacts={sectorImpacts}
        totalLossUsd={headline.totalLossUsd}
        propagationDepth={headline.propagationDepth}
        impacts={impacts}
        sectorRollups={sectorRollups}
        scenarioId={scenario.templateId}
        scenarioSeverity={scenario.severity}
        scenarioHorizonHours={scenario.horizonHours}
        narrativeEn={narrativeEn}
        narrativeAr={narrativeAr}
        methodology={methodology}
        confidence={confidence}
        totalSteps={totalSteps}
        auditHash={trust?.auditHash ?? ""}
        modelVersion={trust?.modelVersion ?? ""}
        dataSources={trust?.dataSources ?? []}
        stagesCompleted={trust?.stagesCompleted ?? []}
        warnings={trust?.warnings ?? []}
      />

      {/* ── Status Bar ───────────────────────────────────── */}
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
