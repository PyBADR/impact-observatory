"use client";

import { useState, useEffect, useCallback } from "react";
import { graphClient } from "@/lib/graph-client";
import { useRunState } from "@/lib/run-state";
import { deriveGraphCapabilityFromLoad } from "@/lib/capabilities";
import type {
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  GraphLayer,
  ScenarioImpactResult,
  UnifiedRunResult,
} from "@/types/observatory";

export interface GraphDataState {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  loading: boolean;
  /**
   * Explicit capability flag — null while loading, true/false after.
   * False when edges = 0 (disconnected graph has no propagation paths)
   * or when the graph endpoint is unreachable.
   * Pages MUST check this before attempting to render GraphCanvas.
   */
  graphSupported: boolean | null;
  totalNodes: number;
  totalEdges: number;
  layers: string[];
  activeLayer: GraphLayer | null;
  scenarioResult: ScenarioImpactResult | null;
  scenarioLoading: boolean;
}

export function useGraphData() {
  const [state, setState] = useState<GraphDataState>({
    nodes: [],
    edges: [],
    loading: true,
    graphSupported: null,
    totalNodes: 0,
    totalEdges: 0,
    layers: [],
    activeLayer: null,
    scenarioResult: null,
    scenarioLoading: false,
  });

  // Load full graph on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [nodesRes, edgesRes] = await Promise.all([
          graphClient.nodes(),
          graphClient.edges(),
        ]);
        if (!cancelled) {
          const supported = deriveGraphCapabilityFromLoad(
            nodesRes.nodes.length,
            edgesRes.edges.length
          );
          setState((s) => ({
            ...s,
            nodes: nodesRes.nodes,
            edges: edgesRes.edges,
            totalNodes: nodesRes.total_graph_nodes,
            totalEdges: nodesRes.total_graph_edges,
            layers: nodesRes.layers,
            loading: false,
            // Capability gating: false when edges absent (no propagation paths)
            graphSupported: supported,
          }));
        }
      } catch {
        // Load failed — capability not supported, not a generic error
        if (!cancelled) {
          setState((s) => ({
            ...s,
            loading: false,
            graphSupported: false,
          }));
        }
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Fallback: hydrate from dashboard run-state when standalone API returns empty.
  // Maps ImpactedNode (node_id, node_type) → KnowledgeGraphNode (id, type)
  // and ActivatedEdge (edge_id) → KnowledgeGraphEdge (id).
  // Only activates when standalone load produced 0 nodes to avoid overwriting
  // a successful standalone load.
  useEffect(() => {
    function hydrateFromRunState(unified: UnifiedRunResult | null) {
      if (!unified) return;
      const rawNodes = (unified.graph_payload?.nodes ?? []) as unknown as Record<string, unknown>[];
      const rawEdges = (unified.graph_payload?.edges ?? []) as unknown as Record<string, unknown>[];
      if (rawNodes.length === 0) return;

      setState((s) => {
        // Don't overwrite a successful standalone load
        if (s.nodes.length > 0) return s;

        // Remap backend ImpactedNode schema → KnowledgeGraphNode
        const nodes: KnowledgeGraphNode[] = rawNodes.map((n) => ({
          id: ((n.node_id ?? n.id) as string) ?? "",
          label: (n.label as string) ?? "",
          label_ar: (n.label_ar as string) ?? "",
          layer: (n.layer as KnowledgeGraphNode["layer"]) ?? "economy",
          type: ((n.node_type ?? n.type) as string) ?? "Topic",
          weight: (n.weight as number) ?? 0,
          lat: (n.lat as number) ?? 0,
          lng: (n.lng as number) ?? 0,
          sensitivity: (n.sensitivity as number) ?? 0.5,
          stress: (n.stress as number) ?? 0,
          classification: (n.classification as KnowledgeGraphNode["classification"]) ?? "NOMINAL",
        }));

        // Remap backend ActivatedEdge schema → KnowledgeGraphEdge
        const edges: KnowledgeGraphEdge[] = rawEdges.map((e) => ({
          id: ((e.edge_id ?? e.id) as string) ?? "",
          source: (e.source as string) ?? "",
          target: (e.target as string) ?? "",
          weight: (e.weight as number) ?? 0,
          polarity: (e.polarity as number) ?? 1,
          label: (e.label as string) ?? "",
          label_ar: (e.label_ar as string) ?? "",
          transmission: (e.transmission as number) ?? 0,
        }));

        return {
          ...s,
          nodes,
          edges,
          totalNodes: nodes.length,
          totalEdges: edges.length,
          layers: [...new Set(rawNodes.map((n) => (n.layer as string) ?? ""))].filter(Boolean),
          loading: false,
          graphSupported: nodes.length > 0 && edges.length > 0,
        };
      });
    }

    // Hydrate immediately if a run already completed before this page mounted
    hydrateFromRunState(useRunState.getState().unifiedResult);

    // Subscribe to future dashboard runs
    const unsub = useRunState.subscribe((state, prevState) => {
      if (state.unifiedResult !== prevState.unifiedResult) {
        hydrateFromRunState(state.unifiedResult);
      }
    });

    return () => { unsub(); };
  }, []);

  // Filter by layer — only callable when graphSupported = true
  const filterByLayer = useCallback(async (layer: GraphLayer | null) => {
    setState((s) => ({ ...s, loading: true, activeLayer: layer }));
    try {
      const [nodesRes, edgesRes] = await Promise.all([
        layer ? graphClient.nodes(layer) : graphClient.nodes(),
        layer ? graphClient.edges(layer) : graphClient.edges(),
      ]);
      setState((s) => ({
        ...s,
        nodes: nodesRes.nodes,
        edges: edgesRes.edges,
        loading: false,
      }));
    } catch {
      // Filter failed — don't change graphSupported, just stop loading
      setState((s) => ({ ...s, loading: false }));
    }
  }, []);

  // Run scenario impact
  const runScenario = useCallback(async (scenarioId: string, severity = 0.7) => {
    setState((s) => ({ ...s, scenarioLoading: true }));
    try {
      const result = await graphClient.scenarioImpacts(scenarioId, severity);
      setState((s) => ({
        ...s,
        scenarioResult: result,
        scenarioLoading: false,
      }));
      return result;
    } catch {
      setState((s) => ({ ...s, scenarioLoading: false }));
      return null;
    }
  }, []);

  return { ...state, filterByLayer, runScenario };
}
