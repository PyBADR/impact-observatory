/**
 * Impact Observatory | مرصد الأثر — Backend Capability Flags
 *
 * Explicit capability gating for features that depend on specific
 * backend pipeline support. Prevents rendering attempts against
 * unsupported payloads and eliminates generic error states.
 *
 * graph_supported — requires graph_payload.nodes (v4 unified pipeline)
 * map_supported   — requires map_payload.impacted_entities with lat/lng
 *
 * Production v2 backend provides neither; both flags resolve to false.
 */

export interface BackendCapabilities {
  /** True when a full graph payload with nodes and edges is available */
  graph_supported: boolean;
  /** True when a map payload with geolocated impacted entities is available */
  map_supported: boolean;
}

export const CAPABILITIES_NONE: BackendCapabilities = {
  graph_supported: false,
  map_supported: false,
};

/**
 * Derive capabilities from a raw run result payload.
 * Both capabilities require positive evidence — neither is assumed.
 */
export function deriveCapabilitiesFromResult(
  result: Record<string, unknown>
): BackendCapabilities {
  const graphPayload = result?.graph_payload as Record<string, unknown> | undefined;
  const mapPayload = result?.map_payload as Record<string, unknown> | undefined;

  const graphNodes = graphPayload?.nodes;
  const mapEntities = mapPayload?.impacted_entities;

  return {
    graph_supported:
      Array.isArray(graphNodes) && graphNodes.length > 0,
    map_supported:
      Array.isArray(mapEntities) && mapEntities.length > 0,
  };
}

/**
 * Derive graph capability from static graph load result.
 * Graph is only considered supported if both nodes AND edges loaded.
 * Nodes without edges produce a disconnected graph with no propagation paths.
 */
export function deriveGraphCapabilityFromLoad(
  nodeCount: number,
  edgeCount: number
): boolean {
  return nodeCount > 0 && edgeCount > 0;
}
