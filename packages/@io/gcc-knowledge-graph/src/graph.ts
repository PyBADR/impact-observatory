/**
 * @io/gcc-knowledge-graph — GCCGraph Class
 *
 * In-memory graph structure with O(1) lookups, adjacency traversal,
 * layer filtering, and scenario shock application.
 */

import { GCCNode, GCCEdge, GCCLayer, GCCScenario, ScenarioShock, LayerMeta } from './types';
import { gccNodes } from './nodes';
import { gccEdges } from './edges';

// ═══════════════════════════════════════════════
// LAYER METADATA
// ═══════════════════════════════════════════════
export const LAYER_META: Record<GCCLayer, LayerMeta> = {
  geography:      { label: 'Geography',      labelAr: 'الجغرافيا',       color: '#2DD4A0', yBase: 40 },
  infrastructure: { label: 'Infrastructure', labelAr: 'البنية التحتية',  color: '#F5A623', yBase: 170 },
  economy:        { label: 'Economy',        labelAr: 'الاقتصاد',        color: '#5B7BF8', yBase: 310 },
  finance:        { label: 'Finance',        labelAr: 'المالية',          color: '#A78BFA', yBase: 450 },
  society:        { label: 'Society',        labelAr: 'المجتمع',          color: '#EF5454', yBase: 580 },
};

export class GCCGraph {
  private readonly _nodes: ReadonlyArray<GCCNode>;
  private readonly _edges: ReadonlyArray<GCCEdge>;
  private readonly _nodeMap: Map<string, GCCNode>;
  private readonly _edgeMap: Map<string, GCCEdge>;
  private readonly _adjacencyOut: Map<string, GCCEdge[]>;
  private readonly _adjacencyIn: Map<string, GCCEdge[]>;

  constructor(
    nodes: ReadonlyArray<GCCNode> = gccNodes,
    edges: ReadonlyArray<GCCEdge> = gccEdges,
  ) {
    this._nodes = nodes;
    this._edges = edges;

    // Build index maps
    this._nodeMap = new Map(nodes.map(n => [n.id, n]));
    this._edgeMap = new Map(edges.map(e => [e.id, e]));

    // Build adjacency lists
    this._adjacencyOut = new Map<string, GCCEdge[]>();
    this._adjacencyIn = new Map<string, GCCEdge[]>();

    for (const n of nodes) {
      this._adjacencyOut.set(n.id, []);
      this._adjacencyIn.set(n.id, []);
    }

    for (const e of edges) {
      this._adjacencyOut.get(e.source)?.push(e);
      this._adjacencyIn.get(e.target)?.push(e);
    }
  }

  // ─── Accessors ─────────────────────────────────
  get nodes(): ReadonlyArray<GCCNode> { return this._nodes; }
  get edges(): ReadonlyArray<GCCEdge> { return this._edges; }
  get nodeCount(): number { return this._nodes.length; }
  get edgeCount(): number { return this._edges.length; }

  // ─── Node Lookups ──────────────────────────────
  getNode(id: string): GCCNode | undefined {
    return this._nodeMap.get(id);
  }

  getNodeOrThrow(id: string): GCCNode {
    const n = this._nodeMap.get(id);
    if (!n) throw new Error(`Node not found: ${id}`);
    return n;
  }

  hasNode(id: string): boolean {
    return this._nodeMap.has(id);
  }

  getNodesByLayer(layer: GCCLayer): GCCNode[] {
    return this._nodes.filter(n => n.layer === layer);
  }

  getNodesByType(type: string): GCCNode[] {
    return this._nodes.filter(n => n.type === type);
  }

  // ─── Edge Lookups ──────────────────────────────
  getEdge(id: string): GCCEdge | undefined {
    return this._edgeMap.get(id);
  }

  getOutEdges(nodeId: string): GCCEdge[] {
    return this._adjacencyOut.get(nodeId) ?? [];
  }

  getInEdges(nodeId: string): GCCEdge[] {
    return this._adjacencyIn.get(nodeId) ?? [];
  }

  getNeighbors(nodeId: string): GCCNode[] {
    const outTargets = this.getOutEdges(nodeId).map(e => e.target);
    const inSources = this.getInEdges(nodeId).map(e => e.source);
    const uniqueIds = new Set([...outTargets, ...inSources]);
    return Array.from(uniqueIds)
      .map(id => this._nodeMap.get(id))
      .filter((n): n is GCCNode => n !== undefined);
  }

  getAnimatedEdges(): GCCEdge[] {
    return this._edges.filter(e => e.animated === true);
  }

  // ─── Graph Metrics ─────────────────────────────
  /**
   * Compute in-degree for all nodes.
   * Returns Map<nodeId, inDegree>.
   */
  inDegreeMap(): Map<string, number> {
    const m = new Map<string, number>();
    for (const n of this._nodes) m.set(n.id, 0);
    for (const e of this._edges) m.set(e.target, (m.get(e.target) ?? 0) + 1);
    return m;
  }

  /**
   * Compute out-degree for all nodes.
   */
  outDegreeMap(): Map<string, number> {
    const m = new Map<string, number>();
    for (const n of this._nodes) m.set(n.id, 0);
    for (const e of this._edges) m.set(e.source, (m.get(e.source) ?? 0) + 1);
    return m;
  }

  /**
   * BFS shortest path (hop count) between two nodes.
   * Returns -1 if unreachable.
   */
  shortestPath(fromId: string, toId: string): number {
    if (fromId === toId) return 0;
    const visited = new Set<string>([fromId]);
    let frontier = [fromId];
    let depth = 0;

    while (frontier.length > 0) {
      depth++;
      const next: string[] = [];
      for (const nid of frontier) {
        for (const e of this.getOutEdges(nid)) {
          if (e.target === toId) return depth;
          if (!visited.has(e.target)) {
            visited.add(e.target);
            next.push(e.target);
          }
        }
      }
      frontier = next;
    }
    return -1;
  }

  /**
   * Get all nodes reachable from a source within maxHops.
   */
  reachableNodes(sourceId: string, maxHops: number): Map<string, number> {
    const distances = new Map<string, number>([[sourceId, 0]]);
    let frontier = [sourceId];

    for (let hop = 1; hop <= maxHops; hop++) {
      const next: string[] = [];
      for (const nid of frontier) {
        for (const e of this.getOutEdges(nid)) {
          if (!distances.has(e.target)) {
            distances.set(e.target, hop);
            next.push(e.target);
          }
        }
      }
      frontier = next;
      if (frontier.length === 0) break;
    }

    return distances;
  }

  // ─── Scenario Operations ───────────────────────
  /**
   * Validate that all shock targets exist in the graph.
   */
  validateShocks(shocks: ScenarioShock[]): { valid: boolean; missing: string[] } {
    const missing = shocks
      .filter(s => !this._nodeMap.has(s.nodeId))
      .map(s => s.nodeId);
    return { valid: missing.length === 0, missing };
  }

  /**
   * Get the subgraph (nodes + edges) affected by a scenario's shocks
   * within a given propagation depth.
   */
  scenarioSubgraph(scenario: GCCScenario, maxHops: number = 3): {
    nodes: GCCNode[];
    edges: GCCEdge[];
    shockNodeIds: Set<string>;
  } {
    const shockNodeIds = new Set(scenario.shocks.map(s => s.nodeId));
    const affectedIds = new Set<string>();

    for (const s of scenario.shocks) {
      const reachable = this.reachableNodes(s.nodeId, maxHops);
      for (const id of reachable.keys()) affectedIds.add(id);
    }

    const nodes = this._nodes.filter(n => affectedIds.has(n.id));
    const edges = this._edges.filter(e => affectedIds.has(e.source) && affectedIds.has(e.target));

    return { nodes, edges, shockNodeIds };
  }

  // ─── Serialization ─────────────────────────────
  toJSON(): { nodes: GCCNode[]; edges: GCCEdge[]; meta: { nodeCount: number; edgeCount: number } } {
    return {
      nodes: [...this._nodes],
      edges: [...this._edges],
      meta: { nodeCount: this.nodeCount, edgeCount: this.edgeCount },
    };
  }
}

// ─── Default singleton ───────────────────────────
let _defaultGraph: GCCGraph | null = null;

export function getDefaultGraph(): GCCGraph {
  if (!_defaultGraph) {
    _defaultGraph = new GCCGraph();
  }
  return _defaultGraph;
}
