import type {
  EventsResponse,
  FlightsResponse,
  VesselsResponse,
  TemplatesResponse,
  ScenarioResult,
  RiskScore,
  DisruptionScore,
  SystemStress,
  InsuranceExposure,
  ClaimsSurge,
  UnderwritingWatch,
  SeverityProjection,
  DecisionOutput,
  ChokepointsResponse,
  PropagationResponse,
  GraphNode,
  GraphEdge,
} from "@/types";
import type { RunSummary } from "@/types/observatory";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // ================================================================
  // DEPRECATED — Legacy V0 API (globe-only, pre-Observatory)
  // Use api.observatory.* for all new code.
  // Routes below target /events /flights /vessels /scores /graph etc.
  // These endpoints no longer exist in the active backend.
  // ================================================================

  /** @deprecated Legacy V0 — use api.observatory.run() */
  health: () => fetchJSON<{ status: string }>("/health"),

  /** @deprecated Legacy V0 — no active /events route */
  events: (params?: { limit?: number; severity_min?: number; event_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.severity_min) qs.set("severity_min", String(params.severity_min));
    if (params?.event_type) qs.set("event_type", params.event_type);
    return fetchJSON<EventsResponse>(`/events?${qs}`);
  },

  /** @deprecated Legacy V0 — no active /flights route */
  flights: (params?: { limit?: number; status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.status) qs.set("status", params.status);
    return fetchJSON<FlightsResponse>(`/flights?${qs}`);
  },

  /** @deprecated Legacy V0 — no active /vessels route */
  vessels: (params?: { limit?: number; vessel_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.vessel_type) qs.set("vessel_type", params.vessel_type);
    return fetchJSON<VesselsResponse>(`/vessels?${qs}`);
  },

  /** @deprecated Legacy V0 — no active /events/threat-field route */
  threatField: (lat: number, lng: number) =>
    fetchJSON<{ threat_intensity: number; top_contributors: { id: string; contribution: number }[] }>(
      `/events/threat-field?lat=${lat}&lng=${lng}`
    ),

  /** @deprecated Legacy V0 — use api.observatory.run() for scenario-driven risk */
  riskScore: (body: Record<string, number>) =>
    fetchJSON<RiskScore>("/scores/risk", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** @deprecated Legacy V0 — use api.observatory.run() for scenario-driven risk */
  riskScores: (params?: { sector?: string; region?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.region) qs.set("region", params.region);
    if (params?.limit) qs.set("limit", String(params.limit));
    return fetchJSON<{ scores: RiskScore[] }>(`/scores/risk?${qs}`);
  },

  /** @deprecated Legacy V0 — use api.observatory.run() for scenario-driven disruption */
  disruptionScore: (body: Record<string, number>) =>
    fetchJSON<DisruptionScore>("/scores/disruption", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** @deprecated Legacy V0 — no active /scores/confidence route */
  confidenceScore: (params: Record<string, number | string>) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    );
    return fetchJSON<{ score: number; factors: { name: string; value: number }[] }>(
      `/scores/confidence?${qs}`
    );
  },

  /** @deprecated Legacy V0 — use api.observatory.run() for system-wide stress */
  systemStress: () => fetchJSON<SystemStress>("/system/stress"),

  /** @deprecated Legacy V0 — use api.observatory.templates() */
  scenarioTemplates: () =>
    fetchJSON<TemplatesResponse>("/scenario/templates"),

  /** @deprecated Legacy V0 — use api.observatory.run() */
  scenarioRun: (body: {
    scenario_id?: string;
    severity_override?: number;
    custom_shocks?: { shock_type: string; severity: number; target_entity_id?: string }[];
    horizon_hours?: number;
  }) =>
    fetchJSON<ScenarioResult>("/scenario/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** @deprecated Legacy V0 — no active /graph/propagation-path route */
  graphPropagation: (startNodeId: string, maxHops?: number) => {
    const qs = new URLSearchParams({ start_node_id: startNodeId });
    if (maxHops) qs.set("max_hops", String(maxHops));
    return fetchJSON<PropagationResponse>(`/graph/propagation-path?${qs}`);
  },

  /** @deprecated Legacy V0 — no active /graph/chokepoints route */
  graphChokepoints: () =>
    fetchJSON<ChokepointsResponse>("/graph/chokepoints"),

  /** @deprecated Legacy V0 — no active /graph/nodes route */
  graphNodes: (params?: { sector?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.limit) qs.set("limit", String(params.limit));
    return fetchJSON<{ nodes: GraphNode[]; edges: GraphEdge[] }>(`/graph/nodes?${qs}`);
  },

  /** @deprecated Legacy V0 — use api.observatory.insurance() */
  insuranceExposure: (params?: { sector?: string; region?: string }) => {
    const qs = new URLSearchParams();
    if (params?.sector) qs.set("sector", params.sector);
    if (params?.region) qs.set("region", params.region);
    return fetchJSON<{ exposures: InsuranceExposure[] }>(`/insurance/exposure?${qs}`);
  },

  /** @deprecated Legacy V0 — use api.observatory.insurance() */
  claimsSurge: (scenarioId: string) =>
    fetchJSON<ClaimsSurge>(`/insurance/claims-surge?scenario_id=${scenarioId}`),

  /** @deprecated Legacy V0 — use api.observatory.insurance() */
  underwritingWatch: (params?: { watch_level?: string }) => {
    const qs = new URLSearchParams();
    if (params?.watch_level) qs.set("watch_level", params.watch_level);
    return fetchJSON<{ watches: UnderwritingWatch[] }>(`/insurance/underwriting?${qs}`);
  },

  /** @deprecated Legacy V0 — use api.observatory.insurance() */
  severityProjection: (scenarioId: string, horizonHours?: number) => {
    const qs = new URLSearchParams({ scenario_id: scenarioId });
    if (horizonHours) qs.set("horizon_hours", String(horizonHours));
    return fetchJSON<SeverityProjection>(`/insurance/severity-projection?${qs}`);
  },

  /** @deprecated Legacy V0 — use api.observatory.decision() */
  decisionOutput: (scenarioId: string) =>
    fetchJSON<DecisionOutput>(`/decision/output?scenario_id=${scenarioId}`),

  /** @deprecated Legacy V0 — no active /entity/:id route */
  entityDetail: (entityId: string) =>
    fetchJSON<{
      id: string;
      name: string;
      name_ar?: string;
      type: string;
      sector: string;
      region: string;
      risk_score: RiskScore;
      disruption_score: DisruptionScore;
      insurance_exposure?: InsuranceExposure;
      connected_entities: { id: string; name: string; edge_type: string; weight: number }[];
    }>(`/entity/${entityId}`),

  // ================================================================
  // Impact Observatory v1 API
  // ================================================================

  /** List scenario templates */
  observatory: {
    templates: () =>
      fetchJSON<{ count: number; templates: import("@/types/observatory").ScenarioTemplate[] }>(
        "/api/v1/scenarios"
      ),

    /** Execute a full run through all 12 services */
    run: (body: import("@/types/observatory").ScenarioCreate) =>
      fetchJSON<import("@/types/observatory").RunResult>("/api/v1/runs", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** Get full run result */
    getResult: (runId: string) =>
      fetchJSON<import("@/types/observatory").RunResult>(`/api/v1/runs/${runId}`),

    /** Get financial impacts */
    financial: (runId: string) =>
      fetchJSON<{ run_id: string; headline: import("@/types/observatory").RunHeadline; financial: import("@/types/observatory").FinancialImpact[] }>(
        `/api/v1/runs/${runId}/financial`
      ),

    /** Get banking stress */
    banking: (runId: string) =>
      fetchJSON<import("@/types/observatory").BankingStress>(`/api/v1/runs/${runId}/banking`),

    /** Get insurance stress */
    insurance: (runId: string) =>
      fetchJSON<import("@/types/observatory").InsuranceStress>(`/api/v1/runs/${runId}/insurance`),

    /** Get fintech stress */
    fintech: (runId: string) =>
      fetchJSON<import("@/types/observatory").FintechStress>(`/api/v1/runs/${runId}/fintech`),

    /** Get decision plan (top 3 actions) */
    decision: (runId: string) =>
      fetchJSON<import("@/types/observatory").DecisionPlan>(`/api/v1/runs/${runId}/decision`),

    /** Get explanation pack (bilingual) */
    explanation: (runId: string) =>
      fetchJSON<import("@/types/observatory").ExplanationPack>(`/api/v1/runs/${runId}/explanation`),

    /** Get report in mode: executive | analyst | regulatory */
    report: (runId: string, mode: string, lang: string = "en") =>
      fetchJSON<Record<string, unknown>>(`/api/v1/runs/${runId}/report/${mode}?lang=${lang}`),

    /** Get bilingual labels */
    labels: (lang: string = "en") =>
      fetchJSON<Record<string, string>>(`/api/v1/runs/labels?lang=${lang}`),
  },

  // ---- Runs List (v1) ----
  runsList: (params?: { limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    const headers: Record<string, string> = {};
    const apiKey = process.env.NEXT_PUBLIC_API_KEY || "observatory-dev-key";
    if (apiKey) headers["X-API-Key"] = apiKey;
    return fetchJSON<{ runs: RunSummary[]; count: number; limit: number; offset: number }>(
      `/api/v1/runs?${qs}`,
      { headers }
    );
  },
};
