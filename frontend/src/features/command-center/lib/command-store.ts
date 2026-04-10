/**
 * Decision Command Center — Zustand State Store
 *
 * Single source of truth for the command center page.
 * Manages: active run data, selected entities, panel focus state,
 * data source (mock vs live), and action execution state.
 *
 * Data Flow:
 *   API (UnifiedRunResult) → store.loadRun() → derived selectors → components
 *   Mock data → store.loadMock() → same derived selectors → components
 */

import { create } from "zustand";
import type {
  UnifiedRunResult,
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  CausalStep,
  SectorImpact,
  DecisionActionV2,
  SectorRollup,
  TransmissionChain,
  CalibratedCounterfactual,
  ActionPathways,
  DecisionTrustPayload,
  DecisionIntegrationPayload,
  DecisionValuePayload,
  GovernancePayload,
  PilotPayload,
} from "@/types/observatory";
import type { SafeImpact } from "@/lib/v2/api-types";
import { mapImpacts } from "@/lib/v2/api-types";
import { safeFixed, safePercent } from "../lib/format";

// ── Derived view-model types ──────────────────────────────────────────

export interface CommandCenterScenario {
  templateId: string;
  label: string;
  labelAr: string | null;
  domain: string;
  severity: number;
  horizonHours: number;
  triggerTime: string;
}

export interface CommandCenterHeadline {
  totalLossUsd: number;
  nodesImpacted: number;
  propagationDepth: number;
  peakDay: number;
  maxRecoveryDays: number;
  averageStress: number;
  criticalCount: number;
  elevatedCount: number;
}

export interface CommandCenterTrust {
  auditHash: string;
  modelVersion: string;
  pipelineVersion: string;
  dataSources: string[];
  stagesCompleted: string[];
  warnings: string[];
  confidence: number;
}

export type PanelFocus = "graph" | "propagation" | "decisions" | "explanation" | null;
export type DataSource = "mock" | "live";

// ── Store Interface ───────────────────────────────────────────────────

/** Per-panel state — each panel tracks its own readiness independently */
export type PanelState = "loading" | "empty" | "error" | "ready";

interface CommandCenterState {
  // ---- Data ----
  dataSource: DataSource;
  runId: string | null;
  status: "idle" | "loading" | "ready" | "error";
  error: string | null;

  // ---- Per-panel states ----
  panelStates: {
    graph: PanelState;
    propagation: PanelState;
    decisions: PanelState;
    explanation: PanelState;
    sectors: PanelState;
  };

  // ---- Scenario + Headline ----
  scenario: CommandCenterScenario | null;
  headline: CommandCenterHeadline | null;

  // ---- Graph ----
  graphNodes: KnowledgeGraphNode[];
  graphEdges: KnowledgeGraphEdge[];

  // ---- Propagation ----
  causalChain: CausalStep[];
  sectorImpacts: SectorImpact[];

  // ---- Sectors ----
  sectorRollups: Record<string, SectorRollup>;

  // ---- Decisions ----
  decisionActions: DecisionActionV2[];

  // ---- Impacts (entity-level, sector-specific) ----
  impacts: SafeImpact[];

  // ---- Explanation ----
  narrativeEn: string;
  narrativeAr: string;
  methodology: string;
  confidence: number;
  totalSteps: number;

  // ---- Trust ----
  trust: CommandCenterTrust | null;

  // ---- Phase 1 Execution Engines ----
  transmissionChain: TransmissionChain | null;
  counterfactual: CalibratedCounterfactual | null;
  actionPathways: ActionPathways | null;

  // ---- Phase 2 Decision Trust ----
  decisionTrust: DecisionTrustPayload | null;

  // ---- Phase 3 Decision Integration ----
  decisionIntegration: DecisionIntegrationPayload | null;

  // ---- Phase 4 Decision Value ----
  decisionValue: DecisionValuePayload | null;

  // ---- Phase 5 Governance ----
  governance: GovernancePayload | null;

  // ---- Phase 6 Pilot Readiness ----
  pilot: PilotPayload | null;

  // ---- UI State ----
  selectedNodeId: string | null;
  panelFocus: PanelFocus;
  executingActionIds: Set<string>;

  // ---- Actions ----
  setDataSource: (source: DataSource) => void;
  setLoading: () => void;
  setError: (error: string) => void;
  loadMock: (data: {
    scenario: CommandCenterScenario;
    headline: CommandCenterHeadline;
    graphNodes: KnowledgeGraphNode[];
    graphEdges: KnowledgeGraphEdge[];
    causalChain: CausalStep[];
    sectorImpacts: SectorImpact[];
    sectorRollups: Record<string, SectorRollup>;
    decisionActions: DecisionActionV2[];
    impacts: SafeImpact[];
    narrativeEn: string;
    narrativeAr: string;
    methodology: string;
    confidence: number;
    totalSteps: number;
    trust: CommandCenterTrust;
  }) => void;
  loadRun: (runId: string, result: UnifiedRunResult) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setPanelFocus: (panel: PanelFocus) => void;
  startExecuting: (actionId: string) => void;
  stopExecuting: (actionId: string) => void;
  reset: () => void;
}

// ── Initial State ─────────────────────────────────────────────────────

const EMPTY_PANEL_STATES: CommandCenterState["panelStates"] = {
  graph: "empty",
  propagation: "empty",
  decisions: "empty",
  explanation: "empty",
  sectors: "empty",
};

const LOADING_PANEL_STATES: CommandCenterState["panelStates"] = {
  graph: "loading",
  propagation: "loading",
  decisions: "loading",
  explanation: "loading",
  sectors: "loading",
};

const INITIAL_STATE = {
  dataSource: "mock" as DataSource,
  runId: null as string | null,
  status: "idle" as const,
  error: null as string | null,
  panelStates: { ...EMPTY_PANEL_STATES },
  scenario: null as CommandCenterScenario | null,
  headline: null as CommandCenterHeadline | null,
  graphNodes: [] as KnowledgeGraphNode[],
  graphEdges: [] as KnowledgeGraphEdge[],
  causalChain: [] as CausalStep[],
  sectorImpacts: [] as SectorImpact[],
  sectorRollups: {} as Record<string, SectorRollup>,
  decisionActions: [] as DecisionActionV2[],
  impacts: [] as SafeImpact[],
  narrativeEn: "",
  narrativeAr: "",
  methodology: "",
  confidence: 0,
  totalSteps: 0,
  trust: null as CommandCenterTrust | null,
  transmissionChain: null as TransmissionChain | null,
  counterfactual: null as CalibratedCounterfactual | null,
  actionPathways: null as ActionPathways | null,
  decisionTrust: null as DecisionTrustPayload | null,
  decisionIntegration: null as DecisionIntegrationPayload | null,
  decisionValue: null as DecisionValuePayload | null,
  governance: null as GovernancePayload | null,
  pilot: null as PilotPayload | null,
  selectedNodeId: null as string | null,
  panelFocus: null as PanelFocus,
  executingActionIds: new Set<string>(),
};

// ── Helpers: extract from UnifiedRunResult ─────────────────────────────

function inferDomain(templateId: string): string {
  if (templateId.includes("hormuz") || templateId.includes("port") || templateId.includes("red_sea")) return "MARITIME";
  if (templateId.includes("oil") || templateId.includes("energy") || templateId.includes("lng")) return "ENERGY";
  if (templateId.includes("banking") || templateId.includes("liquidity") || templateId.includes("fiscal")) return "FINANCIAL";
  if (templateId.includes("cyber")) return "CYBER";
  return "TRADE";
}

function extractSectorImpacts(nodes: KnowledgeGraphNode[]): SectorImpact[] {
  const sectorMap = new Map<string, { total: number; max: number; count: number; topNode: string; topStress: number }>();
  const SECTOR_COLORS: Record<string, string> = {
    geography: "#8B5CF6", infrastructure: "#F59E0B", economy: "#3B82F6",
    finance: "#22C55E", society: "#EC4899",
  };

  for (const node of nodes) {
    const s = node.stress ?? 0;
    const existing = sectorMap.get(node.layer);
    if (existing) {
      existing.total += s;
      existing.count++;
      if (s > existing.max) { existing.max = s; existing.topNode = node.id; existing.topStress = s; }
    } else {
      sectorMap.set(node.layer, { total: s, max: s, count: 1, topNode: node.id, topStress: s });
    }
  }

  return Array.from(sectorMap.entries()).map(([sector, data]) => ({
    sector,
    sectorLabel: sector.charAt(0).toUpperCase() + sector.slice(1),
    avgImpact: data.total / data.count,
    maxImpact: data.max,
    nodeCount: data.count,
    topNode: data.topNode,
    color: SECTOR_COLORS[sector] ?? "#64748B",
  }));
}

/** Safe number — returns fallback for null/undefined/NaN (local to avoid circular import) */
function _sn(v: unknown, fb = 0): number {
  if (typeof v === "number" && isFinite(v)) return v;
  return fb;
}

function extractCausalChain(result: UnifiedRunResult): CausalStep[] {
  const totalLoss = _sn(result.headline?.total_loss_usd);

  // Primary source: propagation_steps (always present in healthy runs)
  if (result.propagation_steps && result.propagation_steps.length > 0) {
    return result.propagation_steps.map((ps, i) => {
      const transmission = _sn(ps.transmission);
      const weight = _sn(ps.weight);
      const label = ps.label || ps.to || "unknown";
      return {
        step: i + 1,
        entity_id: ps.to ?? `step_${i}`,
        entity_label: label,
        entity_label_ar: null,
        event: `${label}: transmission ${safePercent(transmission, 0)}% via weight ${safeFixed(weight, 2)}`,
        event_ar: null,
        impact_usd: transmission * totalLoss * weight,
        stress_delta: transmission,
        mechanism: "propagation",
      };
    });
  }
  // Fallback: sectors.explanation.drivers (richer narrative)
  const drivers = result.sectors?.explanation?.drivers ?? [];
  if (drivers.length > 0) {
    return drivers.map((d, i) => {
      const driverName = d.driver ?? "Unknown Driver";
      const magnitude = _sn(d.magnitude);
      const unit = d.unit ?? "";
      return {
        step: i + 1,
        entity_id: driverName.toLowerCase().replace(/\s+/g, "_"),
        entity_label: driverName,
        entity_label_ar: null,
        event: `${driverName}: magnitude ${magnitude} ${unit}`,
        event_ar: null,
        impact_usd: magnitude > 1 ? magnitude : magnitude * totalLoss,
        stress_delta: Math.min(magnitude / 100, 1),
        mechanism: "propagation",
      };
    });
  }
  return [];
}

function extractNarrative(result: UnifiedRunResult): { en: string; ar: string; methodology: string } {
  const summary = result.sectors?.explanation?.summary ?? "";
  const assumptions = result.sectors?.explanation?.assumptions ?? [];
  const limitations = result.sectors?.explanation?.limitations ?? [];
  const methodology = [
    assumptions.length > 0 ? `Assumptions: ${assumptions.join(". ")}` : "",
    limitations.length > 0 ? `Limitations: ${limitations.join(". ")}` : "",
  ].filter(Boolean).join(" | ") || "9-layer deterministic simulation pipeline.";
  return { en: summary, ar: "", methodology };
}

// ── Store ─────────────────────────────────────────────────────────────

/** Derive per-panel states from loaded data — never returns undefined */
function derivePanelStates(
  nodes: KnowledgeGraphNode[],
  causalChain: CausalStep[],
  decisionActions: DecisionActionV2[],
  narrativeEn: string,
  sectorRollups: Record<string, SectorRollup>,
  impacts: SafeImpact[] = [],
): CommandCenterState["panelStates"] {
  return {
    graph: nodes.length > 0 ? "ready" : "empty",
    propagation: causalChain.length > 0 ? "ready" : "empty",
    decisions: decisionActions.length > 0 ? "ready" : "empty",
    explanation: narrativeEn.length > 0 ? "ready" : "empty",
    sectors: Object.keys(sectorRollups).length > 0 || impacts.length > 0 ? "ready" : "empty",
  };
}

export const useCommandCenterStore = create<CommandCenterState>((set) => ({
  ...INITIAL_STATE,

  setDataSource: (source) => set({ dataSource: source }),

  setLoading: () =>
    set({
      status: "loading",
      error: null,
      panelStates: { ...LOADING_PANEL_STATES },
    }),

  setError: (error) =>
    set({
      status: "error",
      error,
      panelStates: {
        graph: "error",
        propagation: "error",
        decisions: "error",
        explanation: "error",
        sectors: "error",
      },
    }),

  loadMock: (data) =>
    set({
      ...data,
      dataSource: "mock",
      runId: "mock_run",
      status: "ready",
      error: null,
      panelStates: derivePanelStates(
        data.graphNodes,
        data.causalChain,
        data.decisionActions,
        data.narrativeEn,
        data.sectorRollups,
        data.impacts,
      ),
    }),

  loadRun: (runId, result) => {
    // Gate 1: reject failed pipeline runs gracefully
    if (result.status === "failed") {
      set({
        dataSource: "live",
        runId,
        status: "error",
        error: result.error ?? "Pipeline run failed. No analysis data available.",
        panelStates: {
          graph: "error",
          propagation: "error",
          decisions: "error",
          explanation: "error",
          sectors: "error",
        },
      });
      return;
    }

    // Gate 2: reject runs with missing scenario or headline (malformed API response)
    if (!result.scenario || !result.headline) {
      set({
        dataSource: "live",
        runId,
        status: "error",
        error: "Incomplete run data — scenario or headline missing from API response.",
        panelStates: {
          graph: "error",
          propagation: "error",
          decisions: "error",
          explanation: "error",
          sectors: "error",
        },
      });
      return;
    }

    const nodes = result.graph_payload?.nodes ?? [];
    const edges = result.graph_payload?.edges ?? [];
    const criticalCount = nodes.filter((n) => (n.stress ?? 0) >= 0.8).length;
    const elevatedCount = nodes.filter((n) => {
      const s = n.stress ?? 0;
      return s >= 0.65 && s < 0.8;
    }).length;
    const avgStress = nodes.length > 0
      ? nodes.reduce((sum, n) => sum + (n.stress ?? 0), 0) / nodes.length
      : 0;

    // Derive peakDay from propagation depth heuristic (day ≈ depth * severity_factor)
    const depthVal = result.headline?.propagation_depth ?? 3;
    const severityVal = result.scenario?.severity ?? 0.5;
    const estimatedPeakDay = Math.max(1, Math.round(depthVal * severityVal * 2));
    // Recovery estimate: 6× peak day as a conservative bound
    const estimatedRecoveryDays = Math.max(7, estimatedPeakDay * 6);

    const narrative = extractNarrative(result);
    const causalChain = extractCausalChain(result);
    const decisionActions = result.decision_inputs?.actions ?? [];
    const sectorRollups = result.sector_rollups ?? {};
    const impacts = mapImpacts(result as unknown as Record<string, unknown>);

    // Phase 1 Execution Engine outputs (stages 19-21, present in unified response)
    const rawAny = result as unknown as Record<string, unknown>;
    const transmissionChain = (rawAny.transmission_chain as TransmissionChain) ?? null;
    const counterfactual = (rawAny.counterfactual as CalibratedCounterfactual) ?? null;
    const actionPathways = (rawAny.action_pathways as ActionPathways) ?? null;

    // Phase 2 Decision Trust payload
    const trustPayload: DecisionTrustPayload | null = rawAny.action_confidence
      ? {
          action_confidence: (rawAny.action_confidence as DecisionTrustPayload["action_confidence"]) ?? [],
          model_dependency: (rawAny.model_dependency as DecisionTrustPayload["model_dependency"]) ?? { data_completeness: 0, signal_reliability: 0, assumption_sensitivity: "MEDIUM" as const },
          validation: (rawAny.validation as DecisionTrustPayload["validation"]) ?? { required: false, reason: "", validation_type: "NONE" as const },
          confidence_breakdown: (rawAny.confidence_breakdown as DecisionTrustPayload["confidence_breakdown"]) ?? { drivers: [] },
          risk_profile: (rawAny.risk_profile as DecisionTrustPayload["risk_profile"]) ?? { downside_if_wrong: "MEDIUM" as const, reversibility: "MEDIUM" as const, time_sensitivity: "MEDIUM" as const },
        }
      : null;

    // Phase 3 Decision Integration payload
    const integrationPayload: DecisionIntegrationPayload | null = rawAny.decision_ownership
      ? {
          decision_ownership: (rawAny.decision_ownership as DecisionIntegrationPayload["decision_ownership"]) ?? [],
          workflows: (rawAny.decision_workflows as DecisionIntegrationPayload["workflows"]) ?? [],
          execution_triggers: (rawAny.execution_triggers as DecisionIntegrationPayload["execution_triggers"]) ?? [],
          decision_lifecycle: (rawAny.decision_lifecycle as DecisionIntegrationPayload["decision_lifecycle"]) ?? [],
          integration: (rawAny.integration as DecisionIntegrationPayload["integration"]) ?? { available: [], active: [], connectors: {} },
        }
      : null;

    // Phase 4 Decision Value payload
    const valuePayload: DecisionValuePayload | null = rawAny.expected_actual
      ? {
          expected_actual: (rawAny.expected_actual as DecisionValuePayload["expected_actual"]) ?? [],
          value_attribution: (rawAny.value_attribution as DecisionValuePayload["value_attribution"]) ?? [],
          effectiveness: (rawAny.effectiveness as DecisionValuePayload["effectiveness"]) ?? [],
          portfolio_value: (rawAny.portfolio_value as DecisionValuePayload["portfolio_value"]) ?? {
            total_decisions: 0, total_value_created: 0, total_expected: 0, total_actual: 0,
            net_delta: 0, success_rate: 0, failure_count: 0, success_count: 0, neutral_count: 0,
            avg_effectiveness_score: 0, avg_attribution_confidence: 0, best_decision_id: null,
            worst_decision_id: null, roi_ratio: 0,
          },
        }
      : null;

    // Phase 5 Governance payload
    const governancePayload: GovernancePayload | null = rawAny.decision_evidence
      ? {
          decision_evidence: (rawAny.decision_evidence as GovernancePayload["decision_evidence"]) ?? [],
          policy: (rawAny.policy as GovernancePayload["policy"]) ?? [],
          attribution_defense: (rawAny.attribution_defense as GovernancePayload["attribution_defense"]) ?? [],
          overrides: (rawAny.overrides as GovernancePayload["overrides"]) ?? [],
        }
      : null;

    // Phase 6 Pilot payload
    const pilotPayload: PilotPayload | null = rawAny.pilot_scope
      ? {
          pilot_scope: (rawAny.pilot_scope as PilotPayload["pilot_scope"]) ?? { in_scope: false, scenario_id: "", scope_sector: "", execution_mode: "SHADOW" as const, decision_owners: [], approval_flow: [], reason: "", validated_at: "" },
          pilot_kpi: (rawAny.pilot_kpi as PilotPayload["pilot_kpi"]) ?? { total_decisions: 0, decision_latency_hours: 0, latency_reduction_pct: 0, human_vs_system_delta: 0, avoided_loss_estimate: 0, false_positive_rate: 0, accuracy_rate: 0, total_escalations: 0, divergent_count: 0, matched_count: 0 },
          shadow_comparisons: (rawAny.shadow_comparisons as PilotPayload["shadow_comparisons"]) ?? [],
          pilot_report: (rawAny.pilot_report as PilotPayload["pilot_report"]) ?? { period: "", generated_at: "", run_count: 0, total_decisions: 0, matched_decisions: 0, divergent_decisions: 0, divergence_rate: 0, accuracy_rate: 0, value_created: 0, avg_latency_reduction: 0, false_positive_rate: 0, key_findings: [], recommendation: "" },
          failure_modes: (rawAny.failure_modes as PilotPayload["failure_modes"]) ?? [],
        }
      : null;

    set({
      dataSource: "live",
      runId,
      status: "ready",
      error: null,
      panelStates: derivePanelStates(
        nodes,
        causalChain,
        decisionActions,
        narrative.en,
        sectorRollups,
        impacts,
      ),
      scenario: {
        templateId: result.scenario?.template_id ?? "unknown",
        label: result.scenario?.label ?? "Unknown Scenario",
        labelAr: null,
        domain: inferDomain(result.scenario?.template_id ?? ""),
        severity: result.scenario?.severity ?? 0,
        horizonHours: result.scenario?.horizon_hours ?? 168,
        triggerTime: new Date().toISOString(),
      },
      headline: {
        totalLossUsd: result.headline?.total_loss_usd ?? 0,
        nodesImpacted: result.headline?.total_nodes_impacted ?? 0,
        propagationDepth: result.headline?.propagation_depth ?? 0,
        peakDay: estimatedPeakDay,
        maxRecoveryDays: estimatedRecoveryDays,
        averageStress: avgStress,
        criticalCount,
        elevatedCount,
      },
      graphNodes: nodes,
      graphEdges: edges,
      causalChain,
      sectorImpacts: extractSectorImpacts(nodes),
      sectorRollups,
      decisionActions,
      impacts,
      narrativeEn: narrative.en,
      narrativeAr: narrative.ar,
      methodology: narrative.methodology,
      confidence: result.confidence ?? 0,
      totalSteps: result.stages_completed?.length ?? 0,
      trust: result.trust
        ? {
            auditHash: result.trust.audit_hash,
            modelVersion: result.trust.model_version,
            pipelineVersion: result.trust.pipeline_version,
            dataSources: result.trust.data_sources,
            stagesCompleted: result.trust.stages_completed,
            warnings: result.trust.warnings,
            confidence: result.trust.confidence_score,
          }
        : null,
      transmissionChain,
      counterfactual,
      actionPathways,
      decisionTrust: trustPayload,
      decisionIntegration: integrationPayload,
      decisionValue: valuePayload,
      governance: governancePayload,
      pilot: pilotPayload,
    });
  },

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),
  setPanelFocus: (panel) => set({ panelFocus: panel }),

  startExecuting: (actionId) =>
    set((state) => ({
      executingActionIds: new Set([...state.executingActionIds, actionId]),
    })),

  stopExecuting: (actionId) =>
    set((state) => {
      const next = new Set(state.executingActionIds);
      next.delete(actionId);
      return { executingActionIds: next };
    }),

  reset: () => set(INITIAL_STATE),
}));
