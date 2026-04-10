"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
import { scaleLinear } from "d3-scale";
import type { KnowledgeGraphNode, KnowledgeGraphEdge, GraphLayer } from "@/types/observatory";

// ── Layer color scheme ──
const LAYER_COLORS: Record<string, string> = {
  geography: "#22d3ee",      // cyan
  infrastructure: "#f59e0b", // amber
  economy: "#10b981",        // emerald
  finance: "#6366f1",        // indigo
  society: "#ec4899",        // pink
};

const STRESS_COLORS = {
  CRITICAL: "#ef4444",
  ELEVATED: "#f97316",
  MODERATE: "#eab308",
  LOW: "#22c55e",
  NOMINAL: "#64748b",
};

interface D3Node extends SimulationNodeDatum {
  id: string;
  label: string;
  label_ar: string;
  layer: GraphLayer;
  weight: number;
  stress?: number;
  classification?: string;
}

interface D3Link extends SimulationLinkDatum<D3Node> {
  id: string;
  weight: number;
  polarity: number;
  label: string;
  transmission?: number;
}

interface Props {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  onNodeClick?: (nodeId: string) => void;
  selectedNodeId?: string | null;
  showLabels?: boolean;
  isAr?: boolean;
}

export function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
  selectedNodeId,
  showLabels = true,
  isAr = false,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const simRef = useRef<ReturnType<typeof forceSimulation<D3Node>> | null>(null);
  const nodesRef = useRef<D3Node[]>([]);
  const linksRef = useRef<D3Link[]>([]);
  const [hoveredNode, setHoveredNode] = useState<D3Node | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const dragRef = useRef<{ dragging: boolean; startX: number; startY: number; node: D3Node | null }>({
    dragging: false, startX: 0, startY: 0, node: null,
  });

  // ── Build simulation ──
  useEffect(() => {
    const d3Nodes: D3Node[] = nodes.map((n) => ({
      id: n.id,
      label: n.label,
      label_ar: n.label_ar,
      layer: n.layer,
      weight: n.weight,
      stress: n.stress,
      classification: n.classification,
    }));

    const nodeMap = new Map(d3Nodes.map((n) => [n.id, n]));

    const d3Links: D3Link[] = edges
      .filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e) => ({
        id: e.id,
        source: e.source as unknown as D3Node,
        target: e.target as unknown as D3Node,
        weight: e.weight,
        polarity: e.polarity,
        label: e.label,
        transmission: e.transmission,
      }));

    nodesRef.current = d3Nodes;
    linksRef.current = d3Links;

    if (simRef.current) simRef.current.stop();

    const sim = forceSimulation(d3Nodes)
      .force(
        "link",
        forceLink<D3Node, D3Link>(d3Links)
          .id((d) => d.id)
          .distance((d) => 80 / (d.weight + 0.1))
          .strength((d) => d.weight * 0.3)
      )
      .force("charge", forceManyBody().strength(-120))
      .force("center", forceCenter(0, 0))
      .force("collide", forceCollide(18))
      .alphaDecay(0.02);

    sim.on("tick", render);
    simRef.current = sim;

    return () => { sim.stop(); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  // ── Radius scale ──
  const radiusScale = scaleLinear()
    .domain([0, Math.max(...nodes.map((n) => n.weight), 1)])
    .range([4, 16]);

  // ── Render ──
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const { x: tx, y: ty, k } = transform;

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(w / 2 + tx, h / 2 + ty);
    ctx.scale(k, k);

    // Edges
    for (const link of linksRef.current) {
      const s = link.source as D3Node;
      const t = link.target as D3Node;
      if (s.x == null || s.y == null || t.x == null || t.y == null) continue;

      const alpha = Math.min(0.8, link.weight);
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = link.transmission && link.transmission > 0
        ? `rgba(239, 68, 68, ${alpha})`
        : `rgba(100, 116, 139, ${alpha * 0.5})`;
      ctx.lineWidth = Math.max(0.5, link.weight * 2);
      ctx.stroke();
    }

    // Nodes
    for (const node of nodesRef.current) {
      if (node.x == null || node.y == null) continue;

      const r = radiusScale(node.weight);
      const color = node.stress && node.stress > 0
        ? STRESS_COLORS[node.classification as keyof typeof STRESS_COLORS] || LAYER_COLORS[node.layer]
        : LAYER_COLORS[node.layer] || "#64748b";

      // Glow for stressed nodes
      if (node.stress && node.stress > 0.3) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r + 4, 0, Math.PI * 2);
        ctx.fillStyle = `${color}33`;
        ctx.fill();
      }

      // Selected ring
      if (selectedNodeId === node.id) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r + 3, 0, Math.PI * 2);
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "#0f172a";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Label
      if (showLabels && k > 0.6) {
        ctx.font = `${Math.max(8, 10 / k)}px Inter, sans-serif`;
        ctx.fillStyle = "#e2e8f0";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        const label = isAr && node.label_ar ? node.label_ar : node.label;
        ctx.fillText(label, node.x, node.y + r + 3);
      }
    }

    ctx.restore();

    // Hovered tooltip
    if (hoveredNode && hoveredNode.x != null && hoveredNode.y != null) {
      const sx = hoveredNode.x * k + w / 2 + tx;
      const sy = hoveredNode.y * k + h / 2 + ty;
      const label = isAr && hoveredNode.label_ar ? hoveredNode.label_ar : hoveredNode.label;
      const text = hoveredNode.stress
        ? `${label} — Stress: ${(hoveredNode.stress * 100).toFixed(1)}%`
        : `${label} [${hoveredNode.layer}]`;

      ctx.font = "12px Inter, sans-serif";
      const metrics = ctx.measureText(text);
      const pad = 6;
      ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
      ctx.fillRect(sx - metrics.width / 2 - pad, sy - 30, metrics.width + pad * 2, 20);
      ctx.fillStyle = "#f1f5f9";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, sx, sy - 20);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transform, selectedNodeId, showLabels, isAr, hoveredNode]);

  // Re-render when transform/selection changes
  useEffect(() => { render(); }, [render]);

  // ── Resize ──
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width * window.devicePixelRatio;
        canvas.height = rect.height * window.devicePixelRatio;
        canvas.style.width = `${rect.width}px`;
        canvas.style.height = `${rect.height}px`;
        const ctx = canvas.getContext("2d");
        if (ctx) ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      }
      render();
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [render]);

  // ── Hit test ──
  const hitTest = useCallback(
    (mx: number, my: number): D3Node | null => {
      const canvas = canvasRef.current;
      if (!canvas) return null;
      const w = canvas.width / window.devicePixelRatio;
      const h = canvas.height / window.devicePixelRatio;
      const { x: tx, y: ty, k } = transform;

      for (const node of nodesRef.current) {
        if (node.x == null || node.y == null) continue;
        const sx = node.x * k + w / 2 + tx;
        const sy = node.y * k + h / 2 + ty;
        const r = radiusScale(node.weight) * k + 4;
        const dx = mx - sx;
        const dy = my - sy;
        if (dx * dx + dy * dy < r * r) return node;
      }
      return null;
    },
    [transform, radiusScale]
  );

  // ── Mouse handlers ──
  const onMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitTest(mx, my);
      setHoveredNode(hit);

      if (dragRef.current.dragging && dragRef.current.node) {
        const { k } = transform;
        const canvas = canvasRef.current;
        if (!canvas) return;
        const w = canvas.width / window.devicePixelRatio;
        const h = canvas.height / window.devicePixelRatio;
        dragRef.current.node.fx = (mx - w / 2 - transform.x) / k;
        dragRef.current.node.fy = (my - h / 2 - transform.y) / k;
        simRef.current?.alpha(0.3).restart();
      }
    },
    [hitTest, transform]
  );

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const hit = hitTest(mx, my);
      if (hit) {
        dragRef.current = { dragging: true, startX: mx, startY: my, node: hit };
        hit.fx = hit.x;
        hit.fy = hit.y;
      } else {
        dragRef.current = { dragging: true, startX: mx, startY: my, node: null };
      }
    },
    [hitTest]
  );

  const onMouseUp = useCallback(
    (e: React.MouseEvent) => {
      const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const { startX, startY, node } = dragRef.current;

      if (node) {
        node.fx = null;
        node.fy = null;
        // Click detection (small move)
        if (Math.abs(mx - startX) < 5 && Math.abs(my - startY) < 5) {
          onNodeClick?.(node.id);
        }
      } else if (!node && Math.abs(mx - startX) > 3) {
        // Pan
        setTransform((t) => ({
          ...t,
          x: t.x + (mx - startX),
          y: t.y + (my - startY),
        }));
      }

      dragRef.current = { dragging: false, startX: 0, startY: 0, node: null };
    },
    [onNodeClick]
  );

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform((t) => ({
      ...t,
      k: Math.max(0.1, Math.min(5, t.k * factor)),
    }));
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full cursor-grab active:cursor-grabbing"
      onMouseMove={onMouseMove}
      onMouseDown={onMouseDown}
      onMouseUp={onMouseUp}
      onWheel={onWheel}
    />
  );
}
