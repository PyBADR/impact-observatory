/**
 * Impact Observatory | مرصد الأثر — Phase 2 Scenario Adapter
 *
 * Fetches:
 *   GET  /api/v1/scenarios/list          → scenario catalog
 *   POST /api/v1/scenarios/run/{slug}    → run any registered scenario
 *
 * Extends Phase 1 types with pathway_headlines.
 * Reuses Phase 1 adapter's shape converters for demo step compatibility.
 */

import type {
  CountryImpact,
  SectorImpact,
  DecisionAction,
  Explainability,
  PropagationEdge,
  RiskLevel,
  HormuzRunResult,
} from "./simulationAdapter";

import {
  SimulationApiError,
  toGCCCountryImpact,
  toFrontendSectorImpact,
  toFrontendDecision,
} from "./simulationAdapter";

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface ScenarioMeta {
  slug: string;
  name: string;
  name_ar: string;
  type: string;
  description: string;
  default_severity: string;
  default_horizon_hours: string;
}

export interface ScenarioRunRequest {
  severity?: number | null;
  horizon_hours?: number | null;
  extra_params?: Record<string, unknown>;
}

/** Extends HormuzRunResult with Phase 2 fields */
export interface ScenarioRunResult extends HormuzRunResult {
  pathway_headlines: string[];
  scenario_name: string;
  scenario_type: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-IO-API-Key": API_KEY,
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const msg =
      res.status === 404
        ? "Scenario not found. Available: hormuz, liquidity_stress."
        : res.status === 422
        ? "Invalid parameters. Check severity (0–1) and horizon (1–8760h)."
        : res.status >= 500
        ? "Simulation engine temporarily unavailable."
        : `Request failed (HTTP ${res.status})`;
    throw new SimulationApiError(res.status, msg);
  }
  return res.json() as Promise<T>;
}

/**
 * List all available scenarios.
 */
export async function listScenarios(): Promise<ScenarioMeta[]> {
  const data = await fetchJSON<{ scenarios: ScenarioMeta[] }>(
    "/api/v1/scenarios/list",
  );
  return data.scenarios;
}

/**
 * Run a scenario by slug.
 *
 * @param slug - "hormuz" | "liquidity_stress"
 * @param params - Optional overrides
 */
export async function runScenario(
  slug: string,
  params: ScenarioRunRequest = {},
): Promise<ScenarioRunResult> {
  return fetchJSON<ScenarioRunResult>(`/api/v1/scenarios/run/${slug}`, {
    method: "POST",
    body: JSON.stringify({
      severity: params.severity ?? null,
      horizon_hours: params.horizon_hours ?? null,
      extra_params: params.extra_params ?? {},
    }),
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// Demo Adapters — extend Phase 1 converters with pathway support
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Convert ScenarioRunResult to the shapes consumed by each demo step.
 *
 * Usage in a step component:
 *   const adapted = adaptScenarioResult(result);
 *   // adapted.countries → GCCExposureStep
 *   // adapted.sectors   → SectorImpactStep
 *   // adapted.decisions → DecisionStep
 *   // adapted.pathways  → TransmissionStep / PropagationStep
 */
export function adaptScenarioResult(result: ScenarioRunResult) {
  return {
    countries: result.countries.map(toGCCCountryImpact),
    sectors: result.sectors.map(toFrontendSectorImpact),
    decisions: result.decisions.map(toFrontendDecision),
    pathways: result.pathway_headlines,
    explainability: result.explainability,
    meta: {
      scenarioName: result.scenario_name,
      scenarioType: result.scenario_type,
      totalLoss: result.total_loss_usd,
      riskLevel: result.risk_level,
      confidence: result.confidence,
      modelVersion: result.model_version,
    },
  };
}

// Re-export Phase 1 converters for direct use
export { toGCCCountryImpact, toFrontendSectorImpact, toFrontendDecision };
