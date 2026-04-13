/**
 * Impact Observatory | مرصد الأثر — Phase 3 Graph Adapter
 *
 * Fetches: GET  /api/v1/graph/entities
 *          GET  /api/v1/graph/entities/{country}
 *          POST /api/v1/graph/run/{slug}
 *
 * Returns entity registry and Phase 3 simulation results with entity overlay.
 * Designed to wire into CesiumJS globe and force-graph visualizations.
 *
 * Usage:
 *   import { fetchEntities, runGraphSimulation, adaptForGlobe } from './graphAdapter';
 *   const entities = await fetchEntities();
 *   const result = await runGraphSimulation("hormuz", { severity: 0.72 });
 *   const globeData = adaptForGlobe(result);
 */

import { SimulationApiError } from "./simulationAdapter";
import type { RiskLevel } from "./simulationAdapter";

// ═══════════════════════════════════════════════════════════════════════════════
// Types — mirrors backend Pydantic schemas
// ═══════════════════════════════════════════════════════════════════════════════

export interface EntityInfo {
  entity_id: string;
  entity_type: string;
  country_code: string;
  name: string;
  name_ar: string;
  absorber_capacity: number;
}

export interface EntityLinkInfo {
  entity_id: string;
  country_code: string;
  sector_code: string;
  link_type: "absorbs" | "amplifies" | "triggers";
  weight: number;
  channel: string;
}

export interface EntityRegistryResponse {
  total_entities: number;
  total_links: number;
  entities: EntityInfo[];
  links: EntityLinkInfo[];
}

export interface EntityState {
  entity_id: string;
  entity_type: string;
  country_code: string;
  name: string;
  name_ar: string;
  absorber_capacity: number;
  current_utilization: number;
  stress: number;
  breached: boolean;
  remaining_capacity: number;
}

export interface EscalationAlert {
  trigger: string;
  severity: "warning" | "critical" | "emergency";
  authority_required: "operational" | "tactical" | "strategic" | "sovereign";
  headline: string;
  headline_ar: string;
  affected_entities: string[];
  affected_countries: string[];
  affected_sectors: string[];
  time_to_act_hours: number;
  narrative: string;
  recommended_actions: string[];
}

export interface EnrichedDecision {
  action: string;
  owner: string;
  timing: string;
  value_avoided_usd: number;
  downside_risk: string;
  owner_entity_type: string;
  owner_role: string;
  owner_role_ar: string;
  authority_level: string;
  deadline_hours: number;
  escalation_path: string[];
  regulatory_reference: string;
  failure_consequence: string;
  country_entity_name: string;
  country_entity_name_ar: string;
}

export interface GraphRunResponse {
  scenario_slug: string;
  model_version: string;
  timestamp: string;
  severity: number;
  horizon_hours: number;
  sha256_digest: string;
  total_loss_usd: number;
  risk_level: RiskLevel;
  confidence: number;
  converged: boolean;
  iterations_run: number;
  entity_states: EntityState[];
  escalation_alerts: EscalationAlert[];
  enriched_decisions: EnrichedDecision[];
  entities_breached: number;
  escalation_count: number;
  sovereign_alerts: number;
  pathway_headlines: string[];
  explainability: {
    why_total_loss: string;
    why_country: Record<string, string>;
    why_sector: Record<string, string>;
    why_act_now: string;
  };
}

export interface GraphRunRequest {
  severity?: number | null;
  horizon_hours?: number | null;
  country_code?: string | null;
  extra_params?: Record<string, unknown>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

const headers = {
  "Content-Type": "application/json",
  "X-IO-API-Key": API_KEY,
};

/**
 * Fetch entity registry (all countries or specific country).
 */
export async function fetchEntities(
  countryCode?: string,
): Promise<EntityRegistryResponse> {
  const path = countryCode
    ? `${API_BASE}/api/v1/graph/entities/${countryCode}`
    : `${API_BASE}/api/v1/graph/entities`;

  const res = await fetch(path, { headers });

  if (!res.ok) {
    throw new SimulationApiError(
      res.status,
      res.status === 400
        ? "Invalid country code."
        : `Entity registry fetch failed (HTTP ${res.status})`,
    );
  }

  return res.json() as Promise<EntityRegistryResponse>;
}

/**
 * Run Phase 3 graph simulation.
 */
export async function runGraphSimulation(
  slug: string,
  params: GraphRunRequest = {},
): Promise<GraphRunResponse> {
  const res = await fetch(`${API_BASE}/api/v1/graph/run/${slug}`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      severity: params.severity ?? null,
      horizon_hours: params.horizon_hours ?? null,
      country_code: params.country_code ?? null,
      extra_params: params.extra_params ?? {},
    }),
  });

  if (!res.ok) {
    const msg =
      res.status === 404
        ? "Scenario not found."
        : res.status >= 500
        ? "Graph simulation engine temporarily unavailable."
        : `Graph simulation failed (HTTP ${res.status})`;
    throw new SimulationApiError(res.status, msg);
  }

  return res.json() as Promise<GraphRunResponse>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Globe Visualization Adapter
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GCC country coordinates for CesiumJS globe rendering.
 */
const COUNTRY_COORDS: Record<string, { lat: number; lng: number }> = {
  KWT: { lat: 29.3759, lng: 47.9774 },
  SAU: { lat: 23.8859, lng: 45.0792 },
  UAE: { lat: 23.4241, lng: 53.8478 },
  QAT: { lat: 25.3548, lng: 51.1839 },
  BHR: { lat: 26.0667, lng: 50.5577 },
  OMN: { lat: 21.4735, lng: 55.9754 },
};

export interface GlobeNode {
  id: string;
  label: string;
  labelAr: string;
  lat: number;
  lng: number;
  type: "entity" | "country";
  stress: number;
  breached: boolean;
  entityType?: string;
  countryCode: string;
  absorberCapacity?: number;
  remainingCapacity?: number;
}

export interface GlobeEdge {
  source: string;
  target: string;
  weight: number;
  linkType: string;
  channel: string;
}

export interface GlobeData {
  nodes: GlobeNode[];
  edges: GlobeEdge[];
  alerts: EscalationAlert[];
  summary: {
    totalLoss: string;
    riskLevel: RiskLevel;
    entitiesBreached: number;
    escalationCount: number;
    sovereignAlerts: number;
  };
}

function formatUSD(value: number): string {
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}

/**
 * Transform Phase 3 graph result into CesiumJS-compatible globe data.
 *
 * Produces entity nodes with stress coloring, links showing
 * absorber/amplifier relationships, and escalation overlay.
 */
export function adaptForGlobe(result: GraphRunResponse): GlobeData {
  const nodes: GlobeNode[] = [];

  // Entity nodes (with slight coordinate offsets to avoid overlap)
  const entityOffsets: Record<string, number> = {
    central_bank: 0,
    energy_producer: 0.3,
    port_operator: 0.6,
    reinsurance_layer: -0.3,
    payment_rail: -0.6,
    sovereign_buffer: 0.9,
    real_estate_finance: -0.9,
  };

  for (const entity of result.entity_states) {
    const coords = COUNTRY_COORDS[entity.country_code];
    if (!coords) continue;

    const offset = entityOffsets[entity.entity_type] ?? 0;
    nodes.push({
      id: entity.entity_id,
      label: entity.name,
      labelAr: entity.name_ar,
      lat: coords.lat + offset * 0.15,
      lng: coords.lng + offset * 0.15,
      type: "entity",
      stress: entity.stress,
      breached: entity.breached,
      entityType: entity.entity_type,
      countryCode: entity.country_code,
      absorberCapacity: entity.absorber_capacity,
      remainingCapacity: entity.remaining_capacity,
    });
  }

  // We don't have entity links in the run response, so edges are empty
  // In a real implementation, you'd fetch links separately or include them
  const edges: GlobeEdge[] = [];

  return {
    nodes,
    edges,
    alerts: result.escalation_alerts,
    summary: {
      totalLoss: formatUSD(result.total_loss_usd),
      riskLevel: result.risk_level,
      entitiesBreached: result.entities_breached,
      escalationCount: result.escalation_count,
      sovereignAlerts: result.sovereign_alerts,
    },
  };
}
