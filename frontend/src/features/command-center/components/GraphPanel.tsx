"use client";

/**
 * GraphPanel — Interactive node-link graph for the knowledge graph
 *
 * Renders graph nodes as circles on a force-directed layout with edges.
 * Dark theme, stress-colored nodes, animated edge transmission.
 * Uses pure SVG — no external graph library dependency.
 */

import React, { useMemo, useRef, useState, useCallback } from "react";
import { formatPct, classificationColor, stressToClassification, safeFixed } from "../lib/format";
import type { KnowledgeGraphNode, KnowledgeGraphEdge, StressClassification } from "@/types/observatory";

// ── Types ─────────────────────────────────────────────────────────────

interface GraphPanelProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  onNodeSelect?: (nodeId: string) => void;
  selectedNodeId?: string | null;
}

// ── Layer Colors ──────────────────────────────────────────────────────

const LAYER_COLORS: Record<string, string> = {
  geography: "#8B5CF6",
  infrastructure: "#F59E0B",
  economy: "#3B82F6",
  finance: "#22C55E",
  society: "#EC4899",
};

// ── Adaptive layout (scales for 10–200 nodes) ────────────────────────

function layoutNodes(
  nodes: KnowledgeGraphNode[],
  _edges: KnowledgeGraphEdge[],
  width: number,
  height: number,
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  if (nodes.length === 0) return positions;

  const layerOrder = ["geography", "infrastructure", "economy", "finance", "society"];
  const layerGroups: Record<string, KnowledgeGraphNode[]> = {};
  nodes.forEach((n) => {
    const layer = layerOrder.includes(n.layer) ? n.layer : "society";
    if (!layerGroups[layer]) layerGroups[layer] = [];
    layerGroups[layer].push(n);
  });

  const cx = width / 2;
  const cy = height / 2;
  // Scale outer radius to fit viewbox with 20px padding
  const maxRadius = Math.min(cx, cy) - 20;
  // Compute per-layer radius — distribute evenly, geography gets small inner ring
  const activeLayers = layerOrder.filter((l) => (layerGroups[l]?.length ?? 0) > 0);
  const ringCount = Math.max(activeLayers.length, 1);

  activeLayers.forEach((layer, li) => {
    const group = layerGroups[layer] ?? [];
    // First layer at 15% of max, outer at 100%
    const t = ringCount === 1 ? 1.0 : 0.15 + (0.85 * li) / (ringCount - 1);
    const r = maxRadius * t;
    // Distribute nodes evenly on ring with golden-angle offset per layer
    const goldenOffset = li * 0.618 * Math.PI;
    group.forEach((node, ni) => {
      const angle =
        (2 * Math.PI * ni) / Math.max(group.length, 1) -
        Math.PI / 2 +
        goldenOffset;
      positions.set(node.id, {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      });
    });
  });

  return positions;
}

/** Adaptive node radius — smaller for dense graphs */
function nodeRadius(weight: number, totalNodes: number): number {
  if (totalNodes > 60) return 4 + weight * 4;
  if (totalNodes > 30) return 6 + weight * 6;
  return 8 + weight * 8;
}

// ── Main Component ────────────────────────────────────────────────────

/** Max nodes before we truncate to top-stress nodes for render performance */
const MAX_RENDER_NODES = 200;

/** Filter out nodes with missing/invalid id or layer, and cap at MAX_RENDER_NODES */
function sanitizeNodes(
  raw: KnowledgeGraphNode[],
): { nodes: KnowledgeGraphNode[]; truncated: boolean } {
  const valid = raw.filter(
    (n) =>
      n &&
      typeof n.id === "string" &&
      n.id.length > 0 &&
      typeof n.layer === "string",
  );
  if (valid.length <= MAX_RENDER_NODES) {
    return { nodes: valid, truncated: false };
  }
  // Keep top-stress nodes so the most important ones render
  const sorted = [...valid].sort(
    (a, b) => (b.stress ?? 0) - (a.stress ?? 0),
  );
  return { nodes: sorted.slice(0, MAX_RENDER_NODES), truncated: true };
}

/** Drop edges that reference nodes not in the render set */
function sanitizeEdges(
  raw: KnowledgeGraphEdge[],
  nodeIds: Set<string>,
): KnowledgeGraphEdge[] {
  return raw.filter(
    (e) =>
      e &&
      typeof e.id === "string" &&
      typeof e.source === "string" &&
      typeof e.target === "string" &&
      nodeIds.has(e.source) &&
      nodeIds.has(e.target),
  );
}

// ── Text-based Node Row ──────────────────────────────────────────────

function NodeRow({
  node,
  edgeCount,
  isSelected,
  onClick,
}: {
  node: KnowledgeGraphNode;
  edgeCount: number;
  isSelected: boolean;
  onClick: () => void;
}) {
  const stress = node.stress ?? 0;
  const cls = stressToClassification(stress);
  const color = classificationColor(cls);
  const layerColor = LAYER_COLORS[node.layer] ?? "#64748B";

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors border-b border-white/[0.03] last:border-b-0 ${
        isSelected ? "bg-white/[0.04]" : "hover:bg-white/[0.02]"
      }`}
    >
      <span
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: layerColor }}
      />
      <div className="flex-1 min-w-0">
        <span className="text-[12px] font-medium text-slate-200 truncate block">
          {node.label || node.id}
        </span>
        <span className="text-[10px] text-slate-600 capitalize">{node.layer}</span>
      </div>
      <span
        className="text-[10px] font-bold tabular-nums w-8 text-right"
        style={{ color }}
      >
        {Math.round(stress * 100)}
      </span>
      <span className="text-[10px] text-slate-600 tabular-nums w-8 text-right">
        {edgeCount}e
      </span>
    </button>
  );
}

// ── Text-based Relationship Row ──────────────────────────────────────

function EdgeRow({ edge, nodeMap }: { edge: KnowledgeGraphEdge; nodeMap: Map<string, KnowledgeGraphNode> }) {
  const src = nodeMap.get(edge.source);
  const tgt = nodeMap.get(edge.target);
  return (
    <div className="flex items-center gap-2 px-4 py-1.5 text-[11px] border-b border-white/[0.02] last:border-b-0">
      <span className="text-slate-300 truncate flex-1">{src?.label ?? edge.source}</span>
      <span className="text-slate-600 flex-shrink-0">→</span>
      <span className="text-slate-300 truncate flex-1">{tgt?.label ?? edge.target}</span>
      <span className="text-[10px] text-slate-600 tabular-nums flex-shrink-0 w-12 text-right">
        w:{safeFixed(edge.weight ?? 0, 2)}
      </span>
    </div>
  );
}

// ── View mode type ───────────────────────────────────────────────────

type GraphViewMode = "visual" | "nodes" | "edges";

export function GraphPanel({
  nodes: rawNodes,
  edges: rawEdges,
  onNodeSelect,
  selectedNodeId,
}: GraphPanelProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<GraphViewMode>("visual");
  const W = 520;
  const H = 420;

  // Sanitize + cap
  const { nodes, truncated } = useMemo(() => sanitizeNodes(rawNodes), [rawNodes]);
  const nodeIdSet = useMemo(() => new Set(nodes.map((n) => n.id)), [nodes]);
  const edges = useMemo(() => sanitizeEdges(rawEdges, nodeIdSet), [rawEdges, nodeIdSet]);

  const positions = useMemo(() => layoutNodes(nodes, edges, W, H), [nodes, edges]);
  const totalNodes = nodes.length;

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      onNodeSelect?.(nodeId);
    },
    [onNodeSelect],
  );

  // Find connected edges for hover highlight
  const connectedEdges = useMemo(() => {
    const target = hoveredNode ?? selectedNodeId;
    if (!target) return new Set<string>();
    return new Set(
      edges
        .filter((e) => e.source === target || e.target === target)
        .map((e) => e.id),
    );
  }, [hoveredNode, selectedNodeId, edges]);

  // Edge count per node (for list view)
  const edgeCountMap = useMemo(() => {
    const counts = new Map<string, number>();
    for (const e of edges) {
      counts.set(e.source, (counts.get(e.source) ?? 0) + 1);
      counts.set(e.target, (counts.get(e.target) ?? 0) + 1);
    }
    return counts;
  }, [edges]);

  // Node lookup map (for edge list view)
  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  // Sorted node list (stress descending)
  const sortedNodes = useMemo(
    () => [...nodes].sort((a, b) => (b.stress ?? 0) - (a.stress ?? 0)),
    [nodes],
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Knowledge Graph
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-600 tabular-nums">
            {nodes.length}{truncated ? `/${rawNodes.length}` : ""} nodes — {edges.length} edges
          </span>
          {/* View mode toggle */}
          {nodes.length > 0 && (
            <div className="flex items-center gap-0.5 ml-2">
              {(["visual", "nodes", "edges"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setViewMode(m)}
                  className={`px-1.5 py-0.5 text-[9px] font-medium rounded transition-colors capitalize ${
                    viewMode === m
                      ? "bg-blue-600/20 text-blue-400"
                      : "text-slate-600 hover:text-slate-400"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-white/[0.04]">
        {Object.entries(LAYER_COLORS).map(([layer, color]) => (
          <div key={layer} className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            <span className="text-[9px] text-slate-600 capitalize">{layer}</span>
          </div>
        ))}
      </div>

      {/* Density / truncation warning */}
      {(totalNodes > 100 || truncated) && (
        <div className="px-4 py-1.5 bg-amber-500/5 border-b border-amber-500/10">
          <p className="text-[10px] text-amber-500">
            {truncated
              ? `Showing top ${MAX_RENDER_NODES} of ${rawNodes.length} nodes (by stress). Hover to inspect.`
              : `Dense graph (${totalNodes} nodes) — hover to inspect. Some overlap is expected.`}
          </p>
        </div>
      )}

      {/* Content — empty / visual / nodes list / edges list */}
      {nodes.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center px-6">
            <p className="text-xs text-slate-500 mb-1">No graph data available</p>
            <p className="text-[10px] text-slate-700">
              Graph nodes populate when a pipeline run completes with graph_payload.
            </p>
          </div>
        </div>
      ) : viewMode === "nodes" ? (
        /* ── Node list view ──────────────────────────────────── */
        <div className="flex-1 overflow-y-auto">
          {sortedNodes.map((node) => (
            <NodeRow
              key={node.id}
              node={node}
              edgeCount={edgeCountMap.get(node.id) ?? 0}
              isSelected={selectedNodeId === node.id}
              onClick={() => handleNodeClick(node.id)}
            />
          ))}
        </div>
      ) : viewMode === "edges" ? (
        /* ── Edge list view ──────────────────────────────────── */
        <div className="flex-1 overflow-y-auto">
          {edges.length === 0 ? (
            <div className="flex-1 flex items-center justify-center py-8">
              <p className="text-xs text-slate-500">No relationships</p>
            </div>
          ) : (
            edges.map((edge) => (
              <EdgeRow key={edge.id} edge={edge} nodeMap={nodeMap} />
            ))
          )}
        </div>
      ) : (
        /* ── SVG visual view (default) ───────────────────────── */
        <div className="flex-1 overflow-hidden relative">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${W} ${H}`}
            className="w-full h-full"
            style={{ background: "#080C14" }}
          >
            {/* Edges */}
            {edges.map((edge) => {
              const from = positions.get(edge.source);
              const to = positions.get(edge.target);
              if (!from || !to) return null;
              const highlighted = connectedEdges.has(edge.id);
              return (
                <line
                  key={edge.id}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke={highlighted ? "#3B82F6" : "rgba(255,255,255,0.06)"}
                  strokeWidth={highlighted ? 1.5 : 0.5}
                  strokeDasharray={highlighted ? undefined : "2,2"}
                />
              );
            })}

            {/* Edge arrows (for highlighted) */}
            {edges
              .filter((e) => connectedEdges.has(e.id))
              .map((edge) => {
                const from = positions.get(edge.source);
                const to = positions.get(edge.target);
                if (!from || !to) return null;
                const dx = to.x - from.x;
                const dy = to.y - from.y;
                const len = Math.sqrt(dx * dx + dy * dy);
                if (len === 0) return null;
                const nx = dx / len;
                const ny = dy / len;
                const arrowX = to.x - nx * 14;
                const arrowY = to.y - ny * 14;
                return (
                  <circle
                    key={`arrow-${edge.id}`}
                    cx={arrowX}
                    cy={arrowY}
                    r={2}
                    fill="#3B82F6"
                  />
                );
              })}

            {/* Nodes */}
            {nodes.map((node) => {
              const pos = positions.get(node.id);
              if (!pos) return null;
              const stress = node.stress ?? 0;
              const classification = stressToClassification(stress);
              const stressColor = classificationColor(classification);
              const layerColor = LAYER_COLORS[node.layer] ?? "#64748B";
              const isSelected = selectedNodeId === node.id;
              const isHovered = hoveredNode === node.id;
              const r = nodeRadius(node.weight, totalNodes);

              return (
                <g
                  key={node.id}
                  className="cursor-pointer"
                  onClick={() => handleNodeClick(node.id)}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  {/* Stress ring */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={r + 3}
                    fill="none"
                    stroke={stressColor}
                    strokeWidth={isSelected || isHovered ? 2 : 0.5}
                    opacity={isSelected || isHovered ? 0.8 : 0.3}
                  />
                  {/* Node body */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={r}
                    fill={`${layerColor}30`}
                    stroke={layerColor}
                    strokeWidth={isSelected ? 2 : 1}
                  />
                  {/* Label */}
                  {(isHovered || isSelected) && (
                    <text
                      x={pos.x}
                      y={pos.y - r - 6}
                      textAnchor="middle"
                      className="text-[9px] font-medium fill-slate-300 pointer-events-none"
                    >
                      {node.label}
                    </text>
                  )}
                  {/* Stress value on hover */}
                  {(isHovered || isSelected) && (
                    <text
                      x={pos.x}
                      y={pos.y + 3}
                      textAnchor="middle"
                      className="text-[8px] font-bold pointer-events-none"
                      fill={stressColor}
                    >
                      {Math.round(stress * 100)}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      )}
    </div>
  );
}
