/**
 * Command Store — Contract Validation Tests
 *
 * Tests:
 * 1. loadRun() correctly maps UnifiedRunResult fields to store state
 * 2. loadRun() handles partial payloads (missing graph, trust, sectors)
 * 3. loadRun() rejects failed pipeline runs with error state
 * 4. loadMock() sets correct data source and status
 * 5. Mock/live data source switching
 * 6. Node selection toggle behavior
 * 7. Action execution state management (start/stop)
 * 8. Reset returns to initial state
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useCommandCenterStore } from "../lib/command-store";
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
} from "../lib/mock-data";

// ── Helpers ──────────────────────────────────────────────────────────────

/** Minimal valid UnifiedRunResult for loadRun tests */
function makeRunResult(overrides: Partial<UnifiedRunResult> = {}): UnifiedRunResult {
  return {
    run_id: "run_test_001",
    status: "completed",
    error: undefined,
    scenario: {
      template_id: "hormuz_chokepoint_disruption",
      label: "Strait of Hormuz Partial Blockage",
      severity: 0.72,
      horizon_hours: 168,
      parameters: {},
    },
    headline: {
      total_loss_usd: 4_270_000_000,
      total_nodes_impacted: 31,
      propagation_depth: 5,
      affected_entities: 31,
    },
    graph_payload: {
      nodes: MOCK_GRAPH_NODES,
      edges: MOCK_GRAPH_EDGES,
    },
    propagation_steps: [
      { from: "hormuz_strait", fromLabel: "Hormuz", to: "ras_tanura", toLabel: "Ras Tanura", weight: 0.92, polarity: 1, impact: 0.88, label: "Blockage", iteration: 1 },
      { from: "ras_tanura", fromLabel: "Ras Tanura", to: "aramco", toLabel: "Aramco", weight: 0.85, polarity: 1, impact: 0.65, label: "Export cut", iteration: 2 },
    ],
    sector_rollups: {
      banking: { aggregate_stress: 0.52, total_loss: 890_000_000, node_count: 6, classification: "MODERATE" },
      energy: { aggregate_stress: 0.78, total_loss: 2_100_000_000, node_count: 5, classification: "ELEVATED" },
    },
    decision_inputs: {
      actions: MOCK_DECISION_ACTIONS.slice(0, 2),
    },
    confidence: 0.84,
    stages_completed: ["signal_ingest", "graph_activation", "causal_trace"],
    trust: {
      audit_hash: "sha256:abc123",
      model_version: "io-v4.0.0",
      pipeline_version: "unified-v2.1",
      confidence_score: 0.84,
      data_sources: ["ACLED", "AIS-Stream"],
      stages_completed: ["signal_ingest", "graph_activation"],
      warnings: ["AIS data latency: +12min"],
    },
    sectors: {
      explanation: {
        summary: "Hormuz blockage cascades across maritime/energy/finance.",
        assumptions: ["Diplomatic resolution within 10 days"],
        limitations: ["Limited AIS data feed"],
        drivers: [],
      },
    },
    ...overrides,
  } as unknown as UnifiedRunResult;
}

function mockPayload() {
  return {
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
  };
}

// ── Reset store before each test ─────────────────────────────────────────

beforeEach(() => {
  useCommandCenterStore.getState().reset();
});

// ── loadMock Tests ───────────────────────────────────────────────────────

describe("loadMock", () => {
  it("sets status to ready and dataSource to mock", () => {
    const store = useCommandCenterStore.getState();
    store.loadMock(mockPayload());

    const state = useCommandCenterStore.getState();
    expect(state.status).toBe("ready");
    expect(state.dataSource).toBe("mock");
    expect(state.runId).toBe("mock_run");
    expect(state.error).toBeNull();
  });

  it("loads scenario fields correctly", () => {
    useCommandCenterStore.getState().loadMock(mockPayload());
    const { scenario } = useCommandCenterStore.getState();
    expect(scenario).not.toBeNull();
    expect(scenario!.templateId).toBe("hormuz_chokepoint_disruption");
    expect(scenario!.label).toBe("Strait of Hormuz Partial Blockage");
    expect(scenario!.severity).toBe(0.72);
    expect(scenario!.horizonHours).toBe(168);
  });

  it("loads headline KPI fields", () => {
    useCommandCenterStore.getState().loadMock(mockPayload());
    const { headline } = useCommandCenterStore.getState();
    expect(headline!.totalLossUsd).toBe(4_270_000_000);
    expect(headline!.nodesImpacted).toBe(31);
    expect(headline!.propagationDepth).toBe(5);
    expect(headline!.criticalCount).toBe(7);
    expect(headline!.elevatedCount).toBe(12);
  });

  it("loads graph nodes and edges", () => {
    useCommandCenterStore.getState().loadMock(mockPayload());
    const state = useCommandCenterStore.getState();
    expect(state.graphNodes).toHaveLength(10);
    expect(state.graphEdges).toHaveLength(10);
    expect(state.graphNodes[0].id).toBe("hormuz_strait");
  });

  it("loads causal chain", () => {
    useCommandCenterStore.getState().loadMock(mockPayload());
    const state = useCommandCenterStore.getState();
    expect(state.causalChain).toHaveLength(7);
    expect(state.causalChain[0].mechanism).toBe("direct_shock");
  });

  it("loads decision actions", () => {
    useCommandCenterStore.getState().loadMock(mockPayload());
    const state = useCommandCenterStore.getState();
    expect(state.decisionActions).toHaveLength(4);
    expect(state.decisionActions[0].id).toBe("da_1");
  });

  it("loads trust metadata", () => {
    useCommandCenterStore.getState().loadMock(mockPayload());
    const state = useCommandCenterStore.getState();
    expect(state.trust).not.toBeNull();
    expect(state.trust!.auditHash).toContain("sha256:");
    expect(state.trust!.modelVersion).toBe("io-v4.0.0");
    expect(state.trust!.dataSources).toHaveLength(5);
  });
});

// ── loadRun Contract Validation ──────────────────────────────────────────

describe("loadRun — contract validation", () => {
  it("maps scenario fields from UnifiedRunResult", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { scenario } = useCommandCenterStore.getState();
    expect(scenario).not.toBeNull();
    expect(scenario!.templateId).toBe("hormuz_chokepoint_disruption");
    expect(scenario!.label).toBe("Strait of Hormuz Partial Blockage");
    expect(scenario!.severity).toBe(0.72);
    expect(scenario!.horizonHours).toBe(168);
    expect(scenario!.domain).toBe("MARITIME"); // inferred from template_id
  });

  it("maps headline fields with derived metrics", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { headline } = useCommandCenterStore.getState();
    expect(headline!.totalLossUsd).toBe(4_270_000_000);
    expect(headline!.nodesImpacted).toBe(31);
    expect(headline!.propagationDepth).toBe(5);
    // peakDay = round(depth * severity * 2) = round(5 * 0.72 * 2) = round(7.2) = 7
    expect(headline!.peakDay).toBe(7);
    // maxRecoveryDays = max(7, peakDay * 6) = max(7, 42) = 42
    expect(headline!.maxRecoveryDays).toBe(42);
  });

  it("computes criticalCount and elevatedCount from graph nodes", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { headline, graphNodes } = useCommandCenterStore.getState();
    // Count from mock nodes: stress ≥ 0.8 → hormuz_strait (0.88) = 1 critical
    const expectedCritical = graphNodes.filter(n => (n.stress ?? 0) >= 0.8).length;
    const expectedElevated = graphNodes.filter(n => {
      const s = n.stress ?? 0;
      return s >= 0.65 && s < 0.8;
    }).length;
    expect(headline!.criticalCount).toBe(expectedCritical);
    expect(headline!.elevatedCount).toBe(expectedElevated);
  });

  it("maps graph_payload.nodes and edges", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const state = useCommandCenterStore.getState();
    expect(state.graphNodes).toHaveLength(10);
    expect(state.graphEdges).toHaveLength(10);
  });

  it("extracts causal chain from propagation_steps (primary source)", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { causalChain } = useCommandCenterStore.getState();
    expect(causalChain.length).toBeGreaterThan(0);
    expect(causalChain[0].entity_id).toBe("ras_tanura"); // first step target
    expect(causalChain[0].step).toBe(1);
  });

  it("falls back to drivers when propagation_steps is empty", () => {
    const result = makeRunResult({
      propagation_steps: [],
      sectors: {
        explanation: {
          summary: "Test",
          assumptions: [],
          limitations: [],
          drivers: [
            { driver: "Oil Price Spike", magnitude: 18, unit: "$/bbl" },
            { driver: "Trade Volume Drop", magnitude: 40, unit: "%" },
          ],
        },
      },
    } as any);
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { causalChain } = useCommandCenterStore.getState();
    expect(causalChain).toHaveLength(2);
    expect(causalChain[0].entity_label).toBe("Oil Price Spike");
  });

  it("returns empty causal chain when both sources are absent", () => {
    const result = makeRunResult({
      propagation_steps: [],
      sectors: undefined,
    } as any);
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { causalChain } = useCommandCenterStore.getState();
    expect(causalChain).toHaveLength(0);
  });

  it("maps sector_rollups", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { sectorRollups } = useCommandCenterStore.getState();
    expect(sectorRollups).toHaveProperty("banking");
    expect(sectorRollups).toHaveProperty("energy");
    expect(sectorRollups.banking.aggregate_stress).toBe(0.52);
  });

  it("maps decision_inputs.actions", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { decisionActions } = useCommandCenterStore.getState();
    expect(decisionActions).toHaveLength(2);
    expect(decisionActions[0].id).toBe("da_1");
  });

  it("maps trust metadata", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { trust } = useCommandCenterStore.getState();
    expect(trust).not.toBeNull();
    expect(trust!.auditHash).toBe("sha256:abc123");
    expect(trust!.modelVersion).toBe("io-v4.0.0");
    expect(trust!.warnings).toContain("AIS data latency: +12min");
  });

  it("extracts narrative from sectors.explanation.summary", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { narrativeEn } = useCommandCenterStore.getState();
    expect(narrativeEn).toContain("Hormuz blockage");
  });

  it("builds methodology from assumptions + limitations", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const { methodology } = useCommandCenterStore.getState();
    expect(methodology).toContain("Assumptions");
    expect(methodology).toContain("Limitations");
  });

  it("sets dataSource to live", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const state = useCommandCenterStore.getState();
    expect(state.dataSource).toBe("live");
    expect(state.status).toBe("ready");
    expect(state.runId).toBe("run_001");
  });

  it("maps confidence and totalSteps", () => {
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_001", result);

    const state = useCommandCenterStore.getState();
    expect(state.confidence).toBe(0.84);
    expect(state.totalSteps).toBe(3); // stages_completed.length
  });
});

// ── loadRun — Partial Payload Handling ───────────────────────────────────

describe("loadRun — partial payloads", () => {
  it("handles missing graph_payload gracefully", () => {
    const result = makeRunResult({ graph_payload: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_002", result);

    const state = useCommandCenterStore.getState();
    expect(state.graphNodes).toHaveLength(0);
    expect(state.graphEdges).toHaveLength(0);
    expect(state.status).toBe("ready"); // Should not crash
  });

  it("handles missing trust gracefully", () => {
    const result = makeRunResult({ trust: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_003", result);

    const state = useCommandCenterStore.getState();
    expect(state.trust).toBeNull();
    expect(state.status).toBe("ready");
  });

  it("handles missing decision_inputs gracefully", () => {
    const result = makeRunResult({ decision_inputs: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_004", result);

    const state = useCommandCenterStore.getState();
    expect(state.decisionActions).toHaveLength(0);
  });

  it("handles missing sector_rollups gracefully", () => {
    const result = makeRunResult({ sector_rollups: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_005", result);

    const state = useCommandCenterStore.getState();
    expect(state.sectorRollups).toEqual({});
  });

  it("handles missing sectors.explanation gracefully", () => {
    const result = makeRunResult({ sectors: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_006", result);

    const state = useCommandCenterStore.getState();
    // Falls back to default methodology
    expect(state.methodology).toContain("9-layer deterministic");
  });

  it("handles missing confidence gracefully", () => {
    const result = makeRunResult({ confidence: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_007", result);

    const state = useCommandCenterStore.getState();
    expect(state.confidence).toBe(0);
  });

  it("handles missing stages_completed gracefully", () => {
    const result = makeRunResult({ stages_completed: undefined } as any);
    useCommandCenterStore.getState().loadRun("run_008", result);

    const state = useCommandCenterStore.getState();
    expect(state.totalSteps).toBe(0);
  });
});

// ── loadRun — Failed Pipeline Rejection ──────────────────────────────────

describe("loadRun — failed pipeline", () => {
  it("rejects failed run with error state", () => {
    const result = makeRunResult({
      status: "failed",
      error: "Pipeline timeout at stage 4",
    });
    useCommandCenterStore.getState().loadRun("run_fail", result);

    const state = useCommandCenterStore.getState();
    expect(state.status).toBe("error");
    expect(state.error).toContain("Pipeline timeout");
    expect(state.dataSource).toBe("live");
    // Should NOT populate any analysis data
    expect(state.scenario).toBeNull();
    expect(state.headline).toBeNull();
  });

  it("provides default error message for failed run without error text", () => {
    const result = makeRunResult({ status: "failed", error: undefined });
    useCommandCenterStore.getState().loadRun("run_fail_2", result);

    const state = useCommandCenterStore.getState();
    expect(state.status).toBe("error");
    expect(state.error).toContain("Pipeline run failed");
  });
});

// ── Domain Inference ─────────────────────────────────────────────────────

describe("domain inference", () => {
  it("infers MARITIME for hormuz template", () => {
    const result = makeRunResult();
    result.scenario.template_id = "hormuz_chokepoint_disruption";
    useCommandCenterStore.getState().loadRun("run_d1", result);
    expect(useCommandCenterStore.getState().scenario!.domain).toBe("MARITIME");
  });

  it("infers ENERGY for oil template", () => {
    const result = makeRunResult();
    result.scenario.template_id = "saudi_oil_shock";
    useCommandCenterStore.getState().loadRun("run_d2", result);
    expect(useCommandCenterStore.getState().scenario!.domain).toBe("ENERGY");
  });

  it("infers FINANCIAL for banking template", () => {
    const result = makeRunResult();
    result.scenario.template_id = "uae_banking_crisis";
    useCommandCenterStore.getState().loadRun("run_d3", result);
    expect(useCommandCenterStore.getState().scenario!.domain).toBe("FINANCIAL");
  });

  it("infers CYBER for cyber template", () => {
    const result = makeRunResult();
    result.scenario.template_id = "gcc_cyber_attack";
    useCommandCenterStore.getState().loadRun("run_d4", result);
    expect(useCommandCenterStore.getState().scenario!.domain).toBe("CYBER");
  });

  it("defaults to TRADE for unknown template", () => {
    const result = makeRunResult();
    result.scenario.template_id = "unknown_scenario";
    useCommandCenterStore.getState().loadRun("run_d5", result);
    expect(useCommandCenterStore.getState().scenario!.domain).toBe("TRADE");
  });
});

// ── UI State Management ──────────────────────────────────────────────────

describe("UI state", () => {
  it("toggles selected node", () => {
    const store = useCommandCenterStore.getState();
    store.setSelectedNode("hormuz_strait");
    expect(useCommandCenterStore.getState().selectedNodeId).toBe("hormuz_strait");

    store.setSelectedNode(null);
    expect(useCommandCenterStore.getState().selectedNodeId).toBeNull();
  });

  it("sets panel focus", () => {
    const store = useCommandCenterStore.getState();
    store.setPanelFocus("graph");
    expect(useCommandCenterStore.getState().panelFocus).toBe("graph");

    store.setPanelFocus(null);
    expect(useCommandCenterStore.getState().panelFocus).toBeNull();
  });

  it("manages executing action IDs", () => {
    const store = useCommandCenterStore.getState();
    store.startExecuting("da_1");
    expect(useCommandCenterStore.getState().executingActionIds.has("da_1")).toBe(true);

    store.startExecuting("da_2");
    expect(useCommandCenterStore.getState().executingActionIds.size).toBe(2);

    useCommandCenterStore.getState().stopExecuting("da_1");
    expect(useCommandCenterStore.getState().executingActionIds.has("da_1")).toBe(false);
    expect(useCommandCenterStore.getState().executingActionIds.has("da_2")).toBe(true);
  });
});

// ── Reset ────────────────────────────────────────────────────────────────

describe("reset", () => {
  it("returns to idle state with all fields cleared", () => {
    // Load data first
    useCommandCenterStore.getState().loadMock(mockPayload());
    expect(useCommandCenterStore.getState().status).toBe("ready");

    // Reset
    useCommandCenterStore.getState().reset();
    const state = useCommandCenterStore.getState();
    expect(state.status).toBe("idle");
    expect(state.dataSource).toBe("mock");
    expect(state.runId).toBeNull();
    expect(state.scenario).toBeNull();
    expect(state.headline).toBeNull();
    expect(state.graphNodes).toHaveLength(0);
    expect(state.graphEdges).toHaveLength(0);
    expect(state.causalChain).toHaveLength(0);
    expect(state.decisionActions).toHaveLength(0);
    expect(state.trust).toBeNull();
    expect(state.selectedNodeId).toBeNull();
    expect(state.executingActionIds.size).toBe(0);
  });
});

// ── Mock/Live Switching ──────────────────────────────────────────────────

describe("mock/live switching", () => {
  it("transitions from mock to live on loadRun", () => {
    // Start in mock
    useCommandCenterStore.getState().loadMock(mockPayload());
    expect(useCommandCenterStore.getState().dataSource).toBe("mock");

    // Switch to live
    const result = makeRunResult();
    useCommandCenterStore.getState().loadRun("run_switch", result);
    expect(useCommandCenterStore.getState().dataSource).toBe("live");
    expect(useCommandCenterStore.getState().status).toBe("ready");
  });

  it("setDataSource changes dataSource field", () => {
    useCommandCenterStore.getState().setDataSource("live");
    expect(useCommandCenterStore.getState().dataSource).toBe("live");

    useCommandCenterStore.getState().setDataSource("mock");
    expect(useCommandCenterStore.getState().dataSource).toBe("mock");
  });
});
