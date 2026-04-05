/**
 * Impact Observatory | مرصد الأثر — Graph API Client
 *
 * Typed fetch wrapper for /api/v1/graph/* endpoints.
 * All UI surfaces (Dashboard, Propagation, Map) use this
 * single client to access the GCC Knowledge Graph and unified pipeline.
 */

import type {
  GraphNodesResponse,
  GraphEdgesResponse,
  SubgraphData,
  ScenarioImpactResult,
  UnifiedRunResult,
  GraphScenarioTemplate,
  GraphLayer,
} from "@/types/observatory";

const BASE = "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

function graphErrorMessage(status: number): string {
  if (status === 404) return "The knowledge graph data could not be located. The service may be initializing — please try again shortly.";
  if (status === 422) return "The graph query parameters were invalid. Please adjust your filters and retry.";
  if (status === 401 || status === 403) return "Access to the knowledge graph is restricted. Please contact your administrator.";
  if (status >= 500) return "The knowledge graph service is temporarily unavailable. Please try again in a moment.";
  return "Unable to retrieve graph data. Please try again.";
}

interface Envelope<T> {
  trace_id: string;
  generated_at: string;
  data: T;
  warnings: { code: string; message: string; stage: string }[];
}

async function gql<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-IO-API-Key": API_KEY,
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(graphErrorMessage(res.status));
  }
  const json = await res.json();
  // Handle both v4 success_response envelope ({ trace_id, data: T, warnings })
  // and older backends that return raw data without an envelope wrapper.
  if (typeof json?.trace_id === "string" && json?.data !== undefined) {
    return json.data as T;
  }
  return json as T;
}

/**
 * Normalise graph node fields from older backend schemas to the canonical shape.
 *
 * Older backends use: latitude, longitude, gdp_weight, criticality, risk_score
 * Canonical schema:   lat,      lng,       weight,     sensitivity, stress
 */
function normalizeGraphNode(n: Record<string, unknown>): import("@/types/observatory").KnowledgeGraphNode {
  return {
    id: n.id as string,
    label: n.label as string,
    label_ar: (n.label_ar as string) ?? "",
    layer: n.layer as import("@/types/observatory").GraphLayer,
    type: (n.type as string) ?? "",
    weight: (n.weight as number) ?? (n.gdp_weight as number) ?? 0,
    lat: (n.lat as number) ?? (n.latitude as number) ?? 0,
    lng: (n.lng as number) ?? (n.longitude as number) ?? 0,
    sensitivity: (n.sensitivity as number) ?? (n.criticality as number) ?? 0.5,
    stress: (n.stress as number) ?? (n.risk_score as number) ?? undefined,
    classification: (n.classification as import("@/types/observatory").StressClassification) ?? undefined,
  };
}

export const graphClient = {
  /** GET /api/v1/graph/nodes — All nodes, optional layer filter.
   *  Normalises old-schema fields (latitude→lat, gdp_weight→weight, etc.)
   *  so consumers always receive the canonical KnowledgeGraphNode shape. */
  nodes: async (layer?: GraphLayer): Promise<GraphNodesResponse> => {
    const raw = await gql<Record<string, unknown>>(
      `/api/v1/graph/nodes${layer ? `?layer=${layer}` : ""}`
    );
    const rawNodes = (raw.nodes as Record<string, unknown>[] | undefined) ?? [];
    const nodes = rawNodes.map(normalizeGraphNode);
    return {
      nodes,
      total: (raw.total as number) ?? nodes.length,
      layers: (raw.layers as string[]) ?? [],
      total_graph_nodes: (raw.total_graph_nodes as number) ?? (raw.total as number) ?? nodes.length,
      total_graph_edges: (raw.total_graph_edges as number) ?? 0,
    };
  },

  /** GET /api/v1/graph/edges — All edges, optional layer filter */
  edges: async (layer?: GraphLayer): Promise<GraphEdgesResponse> => {
    const raw = await gql<Record<string, unknown>>(
      `/api/v1/graph/edges${layer ? `?layer=${layer}` : ""}`
    );
    const rawEdges = (raw.edges as import("@/types/observatory").KnowledgeGraphEdge[] | undefined) ?? [];
    return {
      edges: rawEdges,
      total: (raw.total as number) ?? rawEdges.length,
    };
  },

  /** GET /api/v1/graph/nodes/{id} — Single node */
  node: async (nodeId: string): Promise<import("@/types/observatory").KnowledgeGraphNode> => {
    const raw = await gql<Record<string, unknown>>(`/api/v1/graph/nodes/${nodeId}`);
    return normalizeGraphNode(raw);
  },

  /** GET /api/v1/graph/subgraph — Ego-network around center node */
  subgraph: (center: string, depth = 2) =>
    gql<SubgraphData>(
      `/api/v1/graph/subgraph?center=${encodeURIComponent(center)}&depth=${depth}`
    ),

  /**
   * GET /api/v1/graph/scenarios — Available scenario templates.
   * Falls back to GET /api/v1/scenarios if the graph-specific route returns 404
   * (older backends that pre-date the /graph/scenarios endpoint).
   */
  scenarios: async (): Promise<{ scenarios: GraphScenarioTemplate[]; total: number }> => {
    try {
      const raw = await gql<Record<string, unknown>>("/api/v1/graph/scenarios");
      return {
        scenarios: (raw.scenarios as GraphScenarioTemplate[]) ?? [],
        total: (raw.total as number) ?? 0,
      };
    } catch {
      // Fallback: /api/v1/scenarios (standard catalog on all backend versions)
      const raw = await gql<Record<string, unknown>>("/api/v1/scenarios");
      const templates = (raw.templates as Record<string, unknown>[] | undefined)
        ?? (raw.scenarios as Record<string, unknown>[] | undefined)
        ?? [];
      const scenarios: GraphScenarioTemplate[] = templates.map((t) => ({
        id: (t.id as string) ?? (t.template_id as string) ?? "",
        label: (t.name as string) ?? (t.label as string) ?? "",
        label_ar: (t.name_ar as string) ?? (t.label_ar as string) ?? "",
        sector: ((t.sectors_affected as string[]) ?? [])[0] ?? "",
        severity_range: [0, 1] as [number, number],
      }));
      return { scenarios, total: scenarios.length };
    }
  },

  /** POST /api/v1/graph/scenario/{id}/impacts — Graph-only impact */
  scenarioImpacts: (scenarioId: string, severity = 0.7) =>
    gql<ScenarioImpactResult>(`/api/v1/graph/scenario/${scenarioId}/impacts`, {
      method: "POST",
      body: JSON.stringify({ severity }),
    }),

  /** POST /api/v1/graph/unified-run — Full 13-stage pipeline */
  unifiedRun: (params: {
    template_id: string;
    severity?: number;
    horizon_hours?: number;
    label?: string;
  }) =>
    gql<UnifiedRunResult>("/api/v1/graph/unified-run", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};
