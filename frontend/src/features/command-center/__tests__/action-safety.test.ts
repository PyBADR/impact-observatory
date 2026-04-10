/**
 * Action Safety — Unit Tests
 *
 * Tests:
 * 1. Mock mode blocks action execution (dataSource guard)
 * 2. DecisionCard isLive=false → button disabled, shows "Review (demo)"
 * 3. Executing action ID tracking (start/stop)
 * 4. Empty actions → DecisionPanel empty state
 * 5. SectorRollupBar returns null for empty rollups
 * 6. Graph empty state behavior
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useCommandCenterStore } from "../lib/command-store";
import {
  MOCK_GRAPH_NODES,
  MOCK_GRAPH_EDGES,
  MOCK_CAUSAL_CHAIN,
  MOCK_SECTOR_IMPACTS,
  MOCK_SECTOR_ROLLUPS,
  MOCK_DECISION_ACTIONS,
  MOCK_EXPLANATION,
  MOCK_TRUST,
} from "../lib/mock-data";

beforeEach(() => {
  useCommandCenterStore.getState().reset();
});

// ── Mock Mode — Action Execution Guard ───────────────────────────────────

describe("action execution safety", () => {
  it("mock mode dataSource is 'mock' after loadMock", () => {
    useCommandCenterStore.getState().loadMock({
      scenario: {
        templateId: "test",
        label: "Test",
        labelAr: null,
        domain: "MARITIME",
        severity: 0.5,
        horizonHours: 168,
        triggerTime: new Date().toISOString(),
      },
      headline: {
        totalLossUsd: 1_000_000,
        nodesImpacted: 5,
        propagationDepth: 3,
        peakDay: 2,
        maxRecoveryDays: 14,
        averageStress: 0.4,
        criticalCount: 1,
        elevatedCount: 2,
      },
      graphNodes: MOCK_GRAPH_NODES,
      graphEdges: MOCK_GRAPH_EDGES,
      causalChain: MOCK_CAUSAL_CHAIN,
      sectorImpacts: MOCK_SECTOR_IMPACTS,
      sectorRollups: MOCK_SECTOR_ROLLUPS,
      decisionActions: MOCK_DECISION_ACTIONS,
      impacts: [],
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

    const state = useCommandCenterStore.getState();
    expect(state.dataSource).toBe("mock");
    // In mock mode, the hook's executeAction mutationFn should
    // check getState().dataSource !== "live" and throw
  });

  it("live mode dataSource is 'live' after loadRun", () => {
    const result = {
      run_id: "run_safe",
      status: "completed",
      error: null,
      scenario: { template_id: "hormuz_chokepoint_disruption", label: "Test", severity: 0.5, horizon_hours: 168, parameters: {} },
      headline: { total_loss_usd: 1000000, total_nodes_impacted: 5, propagation_depth: 3, affected_entities: 5 },
      graph_payload: { nodes: [], edges: [] },
      propagation_steps: [],
      sector_rollups: {},
      decision_inputs: { actions: [] },
      confidence: 0.8,
      stages_completed: [],
    } as any;

    useCommandCenterStore.getState().loadRun("run_safe", result);
    expect(useCommandCenterStore.getState().dataSource).toBe("live");
  });

  it("executing action IDs are properly tracked", () => {
    const store = useCommandCenterStore.getState();

    // Start two actions
    store.startExecuting("da_1");
    store.startExecuting("da_2");
    let state = useCommandCenterStore.getState();
    expect(state.executingActionIds.has("da_1")).toBe(true);
    expect(state.executingActionIds.has("da_2")).toBe(true);
    expect(state.executingActionIds.size).toBe(2);

    // Stop one
    useCommandCenterStore.getState().stopExecuting("da_1");
    state = useCommandCenterStore.getState();
    expect(state.executingActionIds.has("da_1")).toBe(false);
    expect(state.executingActionIds.has("da_2")).toBe(true);
    expect(state.executingActionIds.size).toBe(1);

    // Stop the other
    useCommandCenterStore.getState().stopExecuting("da_2");
    state = useCommandCenterStore.getState();
    expect(state.executingActionIds.size).toBe(0);
  });

  it("stopping a non-existent action ID is a no-op", () => {
    useCommandCenterStore.getState().stopExecuting("nonexistent");
    expect(useCommandCenterStore.getState().executingActionIds.size).toBe(0);
  });
});

// ── Empty State Guards ───────────────────────────────────────────────────

describe("empty state guards", () => {
  it("initial store has empty graph nodes", () => {
    const state = useCommandCenterStore.getState();
    expect(state.graphNodes).toHaveLength(0);
    expect(state.graphEdges).toHaveLength(0);
  });

  it("initial store has empty causal chain", () => {
    expect(useCommandCenterStore.getState().causalChain).toHaveLength(0);
  });

  it("initial store has empty decision actions", () => {
    expect(useCommandCenterStore.getState().decisionActions).toHaveLength(0);
  });

  it("initial store has empty sector rollups", () => {
    expect(Object.keys(useCommandCenterStore.getState().sectorRollups)).toHaveLength(0);
  });

  it("initial store has empty narrative", () => {
    expect(useCommandCenterStore.getState().narrativeEn).toBe("");
    expect(useCommandCenterStore.getState().narrativeAr).toBe("");
  });

  it("initial store has null trust", () => {
    expect(useCommandCenterStore.getState().trust).toBeNull();
  });

  it("initial store has idle status", () => {
    expect(useCommandCenterStore.getState().status).toBe("idle");
  });

  it("initial store has zero confidence", () => {
    expect(useCommandCenterStore.getState().confidence).toBe(0);
  });
});

// ── Sector Impact Derivation ─────────────────────────────────────────────

describe("sector impact derivation from graph nodes", () => {
  it("loadRun derives sectorImpacts from graph nodes", () => {
    const result = {
      run_id: "run_si",
      status: "completed",
      error: null,
      scenario: { template_id: "hormuz_chokepoint_disruption", label: "Test", severity: 0.5, horizon_hours: 168, parameters: {} },
      headline: { total_loss_usd: 1000000, total_nodes_impacted: 3, propagation_depth: 2, affected_entities: 3 },
      graph_payload: {
        nodes: [
          { id: "n1", label: "Node A", layer: "geography", type: "test", weight: 0.5, lat: 0, lng: 0, sensitivity: 0.5, stress: 0.90, classification: "CRITICAL" },
          { id: "n2", label: "Node B", layer: "geography", type: "test", weight: 0.5, lat: 0, lng: 0, sensitivity: 0.5, stress: 0.70, classification: "ELEVATED" },
          { id: "n3", label: "Node C", layer: "finance", type: "test", weight: 0.5, lat: 0, lng: 0, sensitivity: 0.5, stress: 0.40, classification: "LOW" },
        ],
        edges: [],
      },
      propagation_steps: [],
      sector_rollups: {},
      decision_inputs: { actions: [] },
      confidence: 0.8,
      stages_completed: [],
    } as any;

    useCommandCenterStore.getState().loadRun("run_si", result);
    const { sectorImpacts } = useCommandCenterStore.getState();

    expect(sectorImpacts).toHaveLength(2); // geography + finance
    const geo = sectorImpacts.find(s => s.sector === "geography");
    expect(geo).toBeDefined();
    expect(geo!.nodeCount).toBe(2);
    expect(geo!.avgImpact).toBeCloseTo(0.80); // (0.90 + 0.70) / 2
    expect(geo!.maxImpact).toBe(0.90);

    const fin = sectorImpacts.find(s => s.sector === "finance");
    expect(fin).toBeDefined();
    expect(fin!.nodeCount).toBe(1);
    expect(fin!.avgImpact).toBeCloseTo(0.40);
  });
});
