/**
 * Live Mappers — safe transforms from API → Command Center view-models
 *
 * Rules:
 *  - NEVER throw
 *  - null / undefined / missing → safe defaults ("—" or 0)
 *  - Pure functions only
 */

import type {
  UnifiedRunResult,
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  CausalStep,
  SectorImpact,
  DecisionActionV2,
  SectorRollup,
  StressClassification,
} from "@/types/observatory";

import type {
  CommandCenterScenario,
  CommandCenterHeadline,
  CommandCenterTrust,
} from "./command-store";

// ── Primitives ───────────────────────────────────────────────────────

/** Coerce any value to a display-safe string. Returns "—" for null/undefined/empty. */
export function safeString(value: unknown): string {
  if (value === null || value === undefined) return "—";
  const s = String(value).trim();
  return s.length === 0 ? "—" : s;
}

/** Coerce any value to a finite number. Returns `fallback` (default 0) for NaN/null/undefined/Infinity. */
export function safeNumber(value: unknown, fallback: number = 0): number {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

// ── Helpers ──────────────────────────────────────────────────────────

function safeArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value : [];
}

function safeRecord<T>(value: unknown): Record<string, T> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, T>)
    : {} as Record<string, T>;
}

function safeClassification(value: unknown): StressClassification {
  const valid: StressClassification[] = ["CRITICAL", "ELEVATED", "MODERATE", "LOW", "NOMINAL"];
  if (typeof value === "string" && valid.includes(value as StressClassification)) {
    return value as StressClassification;
  }
  return "NOMINAL";
}

// ── Main Mapper ──────────────────────────────────────────────────────

export interface MappedRunResult {
  runId: string;
  scenario: CommandCenterScenario;
  headline: CommandCenterHeadline;
  trust: CommandCenterTrust;
  graphNodes: KnowledgeGraphNode[];
  graphEdges: KnowledgeGraphEdge[];
  causalChain: CausalStep[];
  sectorImpacts: SectorImpact[];
  sectorRollups: Record<string, SectorRollup>;
  decisions: DecisionActionV2[];
  allDecisions: DecisionActionV2[];
  confidence: number;
  warnings: string[];
  stagesCompleted: string[];
  durationMs: number;
}

/**
 * Transform a raw UnifiedRunResult (possibly partial / malformed) into
 * a fully-defaulted view-model the Command Center can render without
 * null-checks.
 */
export function mapRunResult(input: unknown): MappedRunResult {
  const raw = safeRecord<unknown>(input);

  // ── Scenario ─────────────────────────────────────────────────────
  const rawScenario = safeRecord<unknown>(raw.scenario);
  const scenario: CommandCenterScenario = {
    templateId: safeString(rawScenario.template_id),
    label: safeString(rawScenario.label),
    labelAr: rawScenario.label_ar != null ? safeString(rawScenario.label_ar) : null,
    domain: safeString(rawScenario.domain),
    severity: safeNumber(rawScenario.severity),
    horizonHours: safeNumber(rawScenario.horizon_hours),
    triggerTime: safeString(rawScenario.trigger_time),
  };

  // ── Headline ─────────────────────────────────────────────────────
  const rawHeadline = safeRecord<unknown>(raw.headline);
  const graphNodes = safeArray<KnowledgeGraphNode>(
    safeRecord<unknown>(raw.graph_payload)?.nodes ?? raw.graphNodes,
  );

  const headline: CommandCenterHeadline = {
    totalLossUsd: safeNumber(rawHeadline.total_loss_usd),
    nodesImpacted: safeNumber(rawHeadline.total_nodes_impacted ?? graphNodes.length),
    propagationDepth: safeNumber(rawHeadline.propagation_depth),
    peakDay: safeNumber(rawHeadline.peak_day),
    maxRecoveryDays: safeNumber(rawHeadline.max_recovery_days),
    averageStress: safeNumber(rawHeadline.average_stress),
    criticalCount: safeNumber(rawHeadline.critical_count),
    elevatedCount: safeNumber(rawHeadline.elevated_count),
  };

  // ── Trust ────────────────────────────────────────────────────────
  const rawTrust = safeRecord<unknown>(raw.trust);
  const trust: CommandCenterTrust = {
    auditHash: safeString(rawTrust.audit_hash ?? raw.audit_hash),
    modelVersion: safeString(rawTrust.model_version ?? raw.model_version),
    pipelineVersion: safeString(rawTrust.pipeline_version),
    dataSources: safeArray<string>(rawTrust.data_sources),
    stagesCompleted: safeArray<string>(rawTrust.stages_completed ?? raw.stages_completed),
    warnings: safeArray<string>(rawTrust.warnings ?? raw.warnings),
    confidence: safeNumber(rawTrust.confidence_score ?? raw.confidence),
  };

  // ── Graph ────────────────────────────────────────────────────────
  const rawGraph = safeRecord<unknown>(raw.graph_payload);
  const graphEdges = safeArray<KnowledgeGraphEdge>(rawGraph.edges);

  // ── Propagation → causal chain ───────────────────────────────────
  const rawSteps = safeArray<Record<string, unknown>>(raw.propagation_steps);
  const causalChain: CausalStep[] = rawSteps.map((s, i) => ({
    step: safeNumber(s.step ?? i + 1),
    entity_id: safeString(s.to ?? s.entity_id),
    entity_label: safeString(s.label ?? s.entity_label),
    entity_label_ar: s.entity_label_ar != null ? safeString(s.entity_label_ar) : null,
    event: safeString(s.event ?? s.label),
    event_ar: s.event_ar != null ? safeString(s.event_ar) : null,
    impact_usd: safeNumber(s.impact_usd ?? s.transmission),
    stress_delta: safeNumber(s.stress_delta ?? s.weight),
    mechanism: safeString(s.mechanism ?? "propagation"),
  }));

  // ── Sector rollups ───────────────────────────────────────────────
  const rawRollups = safeRecord<unknown>(raw.sector_rollups);
  const defaultRollup: SectorRollup = {
    aggregate_stress: 0,
    total_loss: 0,
    node_count: 0,
    classification: "NOMINAL",
  };

  const sectorRollups: Record<string, SectorRollup> = {};
  for (const [key, val] of Object.entries(rawRollups)) {
    const r = safeRecord<unknown>(val);
    sectorRollups[key] = {
      aggregate_stress: safeNumber(r.aggregate_stress),
      total_loss: safeNumber(r.total_loss),
      node_count: safeNumber(r.node_count),
      classification: safeClassification(r.classification),
    };
  }
  if (!sectorRollups.banking) sectorRollups.banking = { ...defaultRollup };
  if (!sectorRollups.insurance) sectorRollups.insurance = { ...defaultRollup };
  if (!sectorRollups.fintech) sectorRollups.fintech = { ...defaultRollup };

  // ── Sector impacts (derived from rollups for graph display) ──────
  const sectorColors: Record<string, string> = {
    banking: "#ef4444",
    insurance: "#f59e0b",
    fintech: "#3b82f6",
    energy: "#10b981",
    logistics: "#8b5cf6",
  };

  const sectorImpacts: SectorImpact[] = Object.entries(sectorRollups).map(
    ([sector, rollup]) => ({
      sector,
      sectorLabel: sector.charAt(0).toUpperCase() + sector.slice(1),
      avgImpact: rollup.node_count > 0
        ? rollup.aggregate_stress / rollup.node_count
        : 0,
      maxImpact: rollup.aggregate_stress,
      nodeCount: rollup.node_count,
      topNode: "—",
      color: sectorColors[sector] ?? "#6b7280",
    }),
  );

  // ── Decisions ────────────────────────────────────────────────────
  const rawDecisions = safeRecord<unknown>(raw.decision_inputs);
  const decisions = safeArray<DecisionActionV2>(rawDecisions.actions);
  const allDecisions = safeArray<DecisionActionV2>(rawDecisions.all_actions ?? rawDecisions.actions);

  // ── Assemble ─────────────────────────────────────────────────────
  return {
    runId: safeString(raw.run_id),
    scenario,
    headline,
    trust,
    graphNodes,
    graphEdges,
    causalChain,
    sectorImpacts,
    sectorRollups,
    decisions,
    allDecisions,
    confidence: safeNumber(raw.confidence),
    warnings: safeArray<string>(raw.warnings),
    stagesCompleted: safeArray<string>(raw.stages_completed),
    durationMs: safeNumber(raw.duration_ms),
  };
}
