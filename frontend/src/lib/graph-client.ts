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
  const envelope = (await res.json()) as Envelope<T>;
  return envelope.data;
}

export const graphClient = {
  /** GET /api/v1/graph/nodes — All 76 nodes, optional layer filter */
  nodes: (layer?: GraphLayer) =>
    gql<GraphNodesResponse>(
      `/api/v1/graph/nodes${layer ? `?layer=${layer}` : ""}`
    ),

  /** GET /api/v1/graph/edges — All edges, optional layer filter */
  edges: (layer?: GraphLayer) =>
    gql<GraphEdgesResponse>(
      `/api/v1/graph/edges${layer ? `?layer=${layer}` : ""}`
    ),

  /** GET /api/v1/graph/nodes/{id} — Single node */
  node: (nodeId: string) =>
    gql<import("@/types/observatory").KnowledgeGraphNode>(
      `/api/v1/graph/nodes/${nodeId}`
    ),

  /** GET /api/v1/graph/subgraph — Ego-network around center node */
  subgraph: (center: string, depth = 2) =>
    gql<SubgraphData>(
      `/api/v1/graph/subgraph?center=${encodeURIComponent(center)}&depth=${depth}`
    ),

  /** GET /api/v1/graph/scenarios — Available scenario templates */
  scenarios: () =>
    gql<{ scenarios: GraphScenarioTemplate[]; total: number }>(
      "/api/v1/graph/scenarios"
    ),

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
