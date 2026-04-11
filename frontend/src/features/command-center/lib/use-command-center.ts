/**
 * Decision Command Center — React Hook (API Binding)
 *
 * Orchestrates data flow:
 *   1. On mount with runId → fetch UnifiedRunResult → store.loadRun()
 *   2. On mount without runId → store.loadMock() with deterministic data
 *   3. On API failure with runId → fallback to mock, preserve error message
 *   4. Action execution → api.decisions.create() + api.authority.propose()
 *
 * Returns stable selectors for all 5 panels.
 *
 * Safety:
 *   - useEffect deps use individual selectors (not full store) to prevent loops
 *   - selectNode reads current selectedNodeId via getState() to avoid stale closure
 *   - executeAction guards: blocks if dataSource === "mock"
 *   - runQuery error surfaces through status/error return fields
 *   - API failure auto-falls back to mock with error preserved
 */

"use client";

import { useEffect, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { useCommandCenterStore } from "./command-store";
import type { UnifiedRunResult } from "@/types/observatory";

import {
  MOCK_SCENARIO,
  MOCK_HEADLINE,
  MOCK_GRAPH_NODES,
  MOCK_GRAPH_EDGES,
  MOCK_CAUSAL_CHAIN,
  MOCK_SECTOR_IMPACTS,
  MOCK_SECTOR_ROLLUPS,
  MOCK_DECISION_ACTIONS,
  MOCK_EXPLANATION,
  MOCK_TRUST,
} from "./mock-data";
import type { SafeImpact, SeverityTier } from "@/lib/v2/api-types";

// ── Mock impacts (deterministic, matches mock scenario) ──────────────

function classifyStressTier(s: number): SeverityTier {
  if (s >= 0.80) return "SEVERE";
  if (s >= 0.65) return "HIGH";
  if (s >= 0.50) return "ELEVATED";
  if (s >= 0.35) return "GUARDED";
  if (s >= 0.20) return "LOW";
  return "NOMINAL";
}

const MOCK_IMPACTS: SafeImpact[] = [
  {
    entityId: "banking_gcc_aggregate",
    entityLabel: "GCC Banking Sector",
    sector: "banking",
    lossUsd: 2_800_000_000,
    exposure: 2_800_000_000,
    stressLevel: 0.72,
    stressTier: classifyStressTier(0.72),
    impactStatus: "STRESSED",
    lcr: 0.85,
    cet1Ratio: 0.14,
    capitalAdequacyRatio: 0.16,
    solvencyRatio: 0,
    combinedRatio: 0,
    serviceAvailability: 0,
    settlementDelayMinutes: 0,
  },
  {
    entityId: "insurance_gcc_aggregate",
    entityLabel: "GCC Insurance Sector",
    sector: "insurance",
    lossUsd: 1_200_000_000,
    exposure: 1_200_000_000,
    stressLevel: 0.58,
    stressTier: classifyStressTier(0.58),
    impactStatus: "STRESSED",
    lcr: 0,
    cet1Ratio: 0,
    capitalAdequacyRatio: 0,
    solvencyRatio: 1.45,
    combinedRatio: 0.98,
    serviceAvailability: 0,
    settlementDelayMinutes: 0,
  },
  {
    entityId: "fintech_gcc_aggregate",
    entityLabel: "GCC Fintech Sector",
    sector: "fintech",
    lossUsd: 450_000_000,
    exposure: 450_000_000,
    stressLevel: 0.41,
    stressTier: classifyStressTier(0.41),
    impactStatus: "DEGRADED",
    lcr: 0,
    cet1Ratio: 0,
    capitalAdequacyRatio: 0,
    solvencyRatio: 0,
    combinedRatio: 0,
    serviceAvailability: 0.92,
    settlementDelayMinutes: 45,
  },
];

// ── Mock loader (shared between no-runId path and fallback) ──────────

function loadMockIntoStore(
  loadMock: ReturnType<typeof useCommandCenterStore.getState>["loadMock"],
) {
  loadMock({
    scenario: {
      templateId: MOCK_SCENARIO.template_id,
      label: MOCK_SCENARIO.label,
      labelAr: MOCK_SCENARIO.label_ar,
      domain: MOCK_SCENARIO.domain,
      severity: MOCK_SCENARIO.severity,
      horizonHours: MOCK_SCENARIO.horizon_hours,
      triggerTime: MOCK_SCENARIO.trigger_time,
    },
    headline: {
      totalLossUsd: MOCK_HEADLINE.total_loss_usd,
      nodesImpacted: MOCK_HEADLINE.total_nodes_impacted,
      propagationDepth: MOCK_HEADLINE.propagation_depth,
      peakDay: MOCK_HEADLINE.peak_day,
      maxRecoveryDays: MOCK_HEADLINE.max_recovery_days,
      averageStress: MOCK_HEADLINE.average_stress,
      criticalCount: MOCK_HEADLINE.critical_count,
      elevatedCount: MOCK_HEADLINE.elevated_count,
    },
    graphNodes: MOCK_GRAPH_NODES,
    graphEdges: MOCK_GRAPH_EDGES,
    causalChain: MOCK_CAUSAL_CHAIN,
    sectorImpacts: MOCK_SECTOR_IMPACTS,
    sectorRollups: MOCK_SECTOR_ROLLUPS,
    decisionActions: MOCK_DECISION_ACTIONS,
    impacts: MOCK_IMPACTS,
    narrativeEn: MOCK_EXPLANATION.narrative_en,
    narrativeAr: MOCK_EXPLANATION.narrative_ar,
    methodology: MOCK_EXPLANATION.methodology,
    confidence: MOCK_EXPLANATION.confidence,
    totalSteps: MOCK_EXPLANATION.total_steps,
    trust: {
      auditHash: MOCK_TRUST.audit_hash,
      modelVersion: MOCK_TRUST.model_version,
      pipelineVersion: MOCK_TRUST.pipeline_version,
      dataSources: MOCK_TRUST.data_sources,
      stagesCompleted: MOCK_TRUST.stages_completed,
      warnings: MOCK_TRUST.warnings,
      confidence: MOCK_TRUST.confidence_score,
    },
  });
}

// ── Hook ──────────────────────────────────────────────────────────────

export function useCommandCenter(runId?: string | null) {
  const store = useCommandCenterStore();
  const queryClient = useQueryClient();
  // Track whether mock has been loaded to prevent double-load
  const mockLoaded = useRef(false);
  // Track whether fallback has fired so we don't loop
  const fallbackFired = useRef(false);

  // ---- Fetch live run result ----
  const runQuery = useQuery({
    queryKey: ["command-center", "run", runId],
    queryFn: async () => {
      const res = await api.observatory.result(runId!);
      return res.data as unknown as UnifiedRunResult;
    },
    enabled: !!runId,
    staleTime: Infinity,
    retry: 2,
  });

  // ---- Load data into store ----
  const storeStatus = store.status;
  const loadRun = store.loadRun;
  const loadMock = store.loadMock;

  useEffect(() => {
    // Path A: Live data arrived → load it
    if (runId && runQuery.data) {
      fallbackFired.current = false;
      loadRun(runId, runQuery.data);
      return;
    }

    // Path B: API failed with runId → fallback to mock, preserve error
    if (runId && runQuery.isError && !fallbackFired.current) {
      fallbackFired.current = true;
      const errorMsg =
        runQuery.error instanceof ApiError
          ? `API ${runQuery.error.status}: ${runQuery.error.message}`
          : runQuery.error?.message ?? "Unknown API error";

      loadMockIntoStore(loadMock);
      // Overwrite store error so UI can show the original failure reason
      useCommandCenterStore.setState({
        error: `Live fetch failed — showing demo data. (${errorMsg})`,
      });
      return;
    }

    // Path C: No runId → pure mock mode
    if (!runId && storeStatus === "idle" && !mockLoaded.current) {
      mockLoaded.current = true;
      loadMockIntoStore(loadMock);
    }
  }, [runId, runQuery.data, runQuery.isError, runQuery.error, storeStatus, loadRun, loadMock]);

  // ---- Manual mock/live toggle ----
  const switchToMock = useCallback(() => {
    fallbackFired.current = false;
    mockLoaded.current = true;
    loadMockIntoStore(loadMock);
  }, [loadMock]);

  const switchToLive = useCallback(
    (liveRunId: string) => {
      fallbackFired.current = false;
      mockLoaded.current = false;
      useCommandCenterStore.setState({ status: "idle", error: null, dataSource: "live" });
      queryClient.invalidateQueries({ queryKey: ["command-center", "run", liveRunId] });
    },
    [queryClient],
  );

  // ---- Execute action → operator authority flow ----
  const executeAction = useMutation({
    mutationFn: async (actionId: string) => {
      // Safety gate: block execution in mock mode
      const currentState = useCommandCenterStore.getState();
      if (currentState.dataSource !== "live") {
        throw new Error("Action execution is disabled in demo mode. Connect to a live backend.");
      }

      currentState.startExecuting(actionId);
      try {
        // Step 1: Create operator decision
        const decision = await api.decisions.create({
          decision_type: "APPROVE_ACTION",
          source_run_id: currentState.runId,
          decision_payload: { action_id: actionId },
          rationale: `Command Center action execution for ${actionId}`,
        });

        // Step 2: Propose to authority layer
        await api.authority.propose({
          decision_id: decision.decision_id,
          source_run_id: currentState.runId ?? undefined,
          rationale: `Action ${actionId} submitted from Decision Command Center`,
        });

        return decision;
      } finally {
        useCommandCenterStore.getState().stopExecuting(actionId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["authority"] });
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
    },
  });

  // ---- Node selection handler (reads current state, no stale closure) ----
  const selectNode = useCallback(
    (nodeId: string | null) => {
      const current = useCommandCenterStore.getState().selectedNodeId;
      useCommandCenterStore.getState().setSelectedNode(
        current === nodeId ? null : nodeId,
      );
    },
    [],
  );

  return {
    // State
    status: runId
      ? runQuery.isLoading
        ? "loading" as const
        : runQuery.isError
          ? "error" as const
          : storeStatus
      : storeStatus,
    error: runQuery.error?.message ?? store.error,
    dataSource: store.dataSource,

    // Data
    scenario: store.scenario,
    headline: store.headline,
    graphNodes: store.graphNodes,
    graphEdges: store.graphEdges,
    causalChain: store.causalChain,
    sectorImpacts: store.sectorImpacts,
    sectorRollups: store.sectorRollups,
    decisionActions: store.decisionActions,
    impacts: store.impacts,
    narrativeEn: store.narrativeEn,
    narrativeAr: store.narrativeAr,
    methodology: store.methodology,
    confidence: store.confidence,
    totalSteps: store.totalSteps,
    trust: store.trust,

    // Phase 1 Execution Engine data
    transmissionChain: store.transmissionChain,
    counterfactual: store.counterfactual,
    actionPathways: store.actionPathways,

    // Phase 2 Decision Trust data
    decisionTrust: store.decisionTrust,

    // Phase 3 Decision Integration data
    decisionIntegration: store.decisionIntegration,

    // Phase 4 Decision Value data
    decisionValue: store.decisionValue,

    // Phase 5 Governance data
    governance: store.governance,

    // Phase 6 Pilot Readiness data
    pilot: store.pilot,

    // Decision Trust Layer (Sprint 1)
    metricExplanations: store.metricExplanations,
    decisionTransparencyResult: store.decisionTransparencyResult,

    // Decision Reliability Layer (Sprint 2)
    reliabilityPayload: store.reliabilityPayload,

    // Macro Context (Sprint 3)
    macroContext: store.macroContext,

    // UI State
    selectedNodeId: store.selectedNodeId,
    panelFocus: store.panelFocus,
    panelStates: store.panelStates,
    executingActionIds: store.executingActionIds,

    // Actions
    selectNode,
    setPanelFocus: store.setPanelFocus,
    executeAction: executeAction.mutate,
    isExecutingAction: executeAction.isPending,

    // Mock/Live switch
    switchToMock,
    switchToLive,
  };
}
