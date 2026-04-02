"use client";

/**
 * Impact Observatory | مرصد الأثر — Graph Explorer (Light Theme)
 */

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useAppStore } from "@/store/app-store";
import { useGraphNodes, useGraphChokepoints } from "@/hooks/use-api";
import type { GraphNode, GraphEdge } from "@/types";
import Link from "next/link";

interface SimNode extends GraphNode {
  vx: number;
  vy: number;
  fx?: number;
  fy?: number;
}

const SECTORS = [
  "all",
  "energy",
  "aviation",
  "maritime",
  "finance",
  "infrastructure",
  "telecom",
  "government",
];

function riskColor(score: number): string {
  if (score >= 0.7) return "#B91C1C";
  if (score >= 0.4) return "#B45309";
  return "#15803D";
}

export default function GraphExplorerPage() {
  const { language } = useAppStore();
  const isAr = language === "ar";

  const [sectorFilter, setSectorFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const { data: graphData, isLoading } = useGraphNodes({
    sector: sectorFilter === "all" ? undefined : sectorFilter,
    limit: 200,
  });
  const { data: chokepointData } = useGraphChokepoints();

  const nodes = graphData?.nodes ?? [];
  const edges = graphData?.edges ?? [];

  const filteredNodes = useMemo(() => {
    if (!searchQuery) return nodes;
    const q = searchQuery.toLowerCase();
    return nodes.filter(
      (n) =>
        n.label.toLowerCase().includes(q) ||
        n.id.toLowerCase().includes(q) ||
        n.type.toLowerCase().includes(q)
    );
  }, [nodes, searchQuery]);

  const filteredNodeIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes]
  );

  const filteredEdges = useMemo(
    () =>
      edges.filter(
        (e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
      ),
    [edges, filteredNodeIds]
  );

  return (
    <div
      className="flex flex-col h-screen bg-io-bg"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-io-surface border-b border-io-border shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-xs text-io-secondary hover:text-io-primary transition"
          >
            ← {isAr ? "لوحة المعلومات" : "Dashboard"}
          </Link>
          <span className="text-lg font-bold text-io-accent">
            {isAr ? "مستكشف الشبكة" : "Graph Explorer"}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* Sector filter */}
          <div className="flex gap-1">
            {SECTORS.map((s) => (
              <button
                key={s}
                onClick={() => setSectorFilter(s)}
                className={`px-2 py-1 text-[10px] rounded transition ${
                  sectorFilter === s
                    ? "bg-io-accent text-white"
                    : "bg-io-bg text-io-secondary hover:text-io-primary border border-io-border"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
          {/* Search */}
          <input
            type="text"
            placeholder={isAr ? "بحث..." : "Search nodes..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-2 py-1 text-xs bg-io-bg border border-io-border rounded text-io-primary placeholder-io-secondary w-40"
          />
        </div>
      </header>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Graph Canvas */}
        <main className="flex-1 relative bg-io-bg">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-12 h-12 border-2 border-io-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredNodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-io-secondary text-sm">
              {isAr ? "لا توجد عقد" : "No nodes to display"}
            </div>
          ) : (
            <ForceGraph
              nodes={filteredNodes}
              edges={filteredEdges}
              selectedNode={selectedNode}
              onNodeClick={(node) => setSelectedNode(node)}
            />
          )}
        </main>

        {/* Right — Node Detail */}
        <aside className="w-72 bg-io-surface border-l border-io-border overflow-y-auto p-4 shrink-0">
          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <h2 className="text-sm font-bold text-io-primary">
                  {selectedNode.label}
                </h2>
                <p className="text-[10px] text-io-secondary mt-1">
                  {selectedNode.id}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="bg-io-bg p-2 rounded border border-io-border">
                  <div className="text-io-secondary">Type</div>
                  <div className="text-io-primary">{selectedNode.type}</div>
                </div>
                <div className="bg-io-bg p-2 rounded border border-io-border">
                  <div className="text-io-secondary">Sector</div>
                  <div className="text-io-primary">
                    {selectedNode.sector || "—"}
                  </div>
                </div>
                <div className="bg-io-bg p-2 rounded border border-io-border">
                  <div className="text-io-secondary">Region</div>
                  <div className="text-io-primary">
                    {selectedNode.region || "—"}
                  </div>
                </div>
                <div className="bg-io-bg p-2 rounded border border-io-border">
                  <div className="text-io-secondary">Risk</div>
                  <div
                    className="font-bold"
                    style={{ color: riskColor(selectedNode.risk_score) }}
                  >
                    {(selectedNode.risk_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Connected edges */}
              <div>
                <h3 className="text-xs font-bold text-io-accent mb-2">
                  {isAr ? "الاتصالات" : "Connections"}
                </h3>
                <div className="space-y-1 max-h-60 overflow-y-auto">
                  {edges
                    .filter(
                      (e) =>
                        e.source === selectedNode.id ||
                        e.target === selectedNode.id
                    )
                    .map((e, i) => {
                      const otherId =
                        e.source === selectedNode.id ? e.target : e.source;
                      const otherNode = nodes.find((n) => n.id === otherId);
                      return (
                        <div
                          key={i}
                          className="flex items-center justify-between text-[10px] py-1 border-b border-io-border cursor-pointer hover:bg-io-bg rounded px-1"
                          onClick={() => {
                            if (otherNode) setSelectedNode(otherNode);
                          }}
                        >
                          <span className="text-io-primary">
                            {otherNode?.label || otherId}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-io-secondary">
                              {e.edge_type}
                            </span>
                            <span className="text-io-accent font-mono">
                              {e.weight.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              <Link
                href={`/entity/${selectedNode.id}`}
                className="block text-center text-xs text-io-accent border border-io-accent/30 rounded-lg py-2 hover:bg-io-accent/5 transition"
              >
                {isAr ? "عرض تفاصيل الكيان" : "View Entity Details"}
              </Link>
            </div>
          ) : (
            <div className="text-xs text-io-secondary">
              {isAr
                ? "انقر على عقدة لعرض التفاصيل"
                : "Click a node to view details"}
            </div>
          )}

          {/* Chokepoints */}
          {chokepointData?.chokepoints && chokepointData.chokepoints.length > 0 && (
            <div className="mt-6 pt-4 border-t border-io-border">
              <h3 className="text-xs font-bold text-io-warning mb-2">
                {isAr ? "نقاط الاختناق" : "Chokepoints"}
              </h3>
              <div className="space-y-1">
                {chokepointData.chokepoints.slice(0, 8).map((cp) => (
                  <div
                    key={cp.node_id}
                    className="flex items-center justify-between text-[10px] py-1 border-b border-io-border"
                  >
                    <span className="text-io-primary">{cp.name}</span>
                    <span className="text-io-warning font-mono">
                      {cp.betweenness_centrality.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

// ===== Simple Force-Directed Graph (Canvas) =====

interface ForceGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  onNodeClick: (node: GraphNode) => void;
}

function ForceGraph({ nodes, edges, selectedNode, onNodeClick }: ForceGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simNodesRef = useRef<SimNode[]>([]);
  const animFrameRef = useRef<number>(0);

  // Initialize simulation nodes
  useEffect(() => {
    const width = containerRef.current?.clientWidth || 800;
    const height = containerRef.current?.clientHeight || 600;
    const cx = width / 2;
    const cy = height / 2;

    simNodesRef.current = nodes.map((n, i) => ({
      ...n,
      x: n.x ?? cx + (Math.random() - 0.5) * width * 0.6,
      y: n.y ?? cy + (Math.random() - 0.5) * height * 0.6,
      vx: 0,
      vy: 0,
    }));
  }, [nodes]);

  // Force simulation tick
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = container.clientWidth;
    let height = container.clientHeight;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const nodeMap = new Map<string, SimNode>();
    simNodesRef.current.forEach((n) => nodeMap.set(n.id, n));

    const cx = width / 2;
    const cy = height / 2;
    let alpha = 1.0;
    const alphaDecay = 0.002;
    const alphaMin = 0.001;

    function tick() {
      const simNodes = simNodesRef.current;
      if (alpha < alphaMin) {
        draw();
        animFrameRef.current = requestAnimationFrame(tick);
        return;
      }

      alpha *= 1 - alphaDecay;

      // Center gravity
      for (const n of simNodes) {
        n.vx += (cx - (n.x ?? cx)) * 0.0005 * alpha;
        n.vy += (cy - (n.y ?? cy)) * 0.0005 * alpha;
      }

      // Node repulsion
      for (let i = 0; i < simNodes.length; i++) {
        for (let j = i + 1; j < simNodes.length; j++) {
          const a = simNodes[i];
          const b = simNodes[j];
          const dx = (b.x ?? 0) - (a.x ?? 0);
          const dy = (b.y ?? 0) - (a.y ?? 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (80 * alpha) / dist;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }

      // Edge attraction
      for (const e of edges) {
        const source = nodeMap.get(e.source);
        const target = nodeMap.get(e.target);
        if (!source || !target) continue;
        const dx = (target.x ?? 0) - (source.x ?? 0);
        const dy = (target.y ?? 0) - (source.y ?? 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 100) * 0.001 * alpha * e.weight;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      }

      // Apply velocity
      for (const n of simNodes) {
        n.vx *= 0.6;
        n.vy *= 0.6;
        n.x = (n.x ?? cx) + n.vx;
        n.y = (n.y ?? cy) + n.vy;
        n.x = Math.max(20, Math.min(width - 20, n.x));
        n.y = Math.max(20, Math.min(height - 20, n.y));
      }

      draw();
      animFrameRef.current = requestAnimationFrame(tick);
    }

    function draw() {
      if (!ctx) return;
      // Light background
      ctx.fillStyle = "#F8FAFC";
      ctx.fillRect(0, 0, width, height);

      // Draw edges
      for (const e of edges) {
        const source = nodeMap.get(e.source);
        const target = nodeMap.get(e.target);
        if (!source || !target || !source.x || !source.y || !target.x || !target.y) continue;

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(29, 78, 216, ${Math.min(e.weight * 0.3, 0.4)})`;
        ctx.lineWidth = Math.max(0.5, e.weight * 2);
        ctx.stroke();
      }

      // Draw nodes
      for (const n of simNodesRef.current) {
        if (n.x === undefined || n.y === undefined) continue;
        const isSelected = selectedNode?.id === n.id;
        const radius = isSelected ? 8 : 4 + n.risk_score * 4;

        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = riskColor(n.risk_score);
        ctx.fill();

        if (isSelected) {
          ctx.strokeStyle = "#0F172A";
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Label for selected or high-risk
        if (isSelected || n.risk_score > 0.6) {
          ctx.fillStyle = "#0F172A";
          ctx.font = "9px system-ui";
          ctx.textAlign = "center";
          ctx.fillText(n.label, n.x, n.y - radius - 4);
        }
      }
    }

    animFrameRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [nodes, edges, selectedNode]);

  // Click handler
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      let closest: SimNode | null = null;
      let closestDist = 20;

      for (const n of simNodesRef.current) {
        if (n.x === undefined || n.y === undefined) continue;
        const dx = n.x - x;
        const dy = n.y - y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < closestDist) {
          closestDist = dist;
          closest = n;
        }
      }

      if (closest) {
        onNodeClick(closest);
      }
    },
    [onNodeClick]
  );

  return (
    <div ref={containerRef} className="w-full h-full">
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-crosshair"
        onClick={handleClick}
      />
    </div>
  );
}
