"use client";

/**
 * TransmissionChannels — Horizontal strip showing how impact flows
 * across 4 macro channels: Oil & Energy, Liquidity & FX, Trade & Ports,
 * Fintech & Insurance.
 *
 * Data source: KnowledgeGraphEdge[] + KnowledgeGraphNode[] from the store.
 * Edges are classified into channels by the layers of their source/target
 * nodes. Each channel card shows:
 *   - Channel label (bilingual)
 *   - Directional flow: source → target (highest-transmission edge)
 *   - Transmission strength bar
 *   - Edge count badge
 *
 * Constraint: pure CSS/Tailwind, zero new libraries.
 * All values pass through safe* coercion.
 */

import React, { useMemo } from "react";
import {
  Fuel,
  Landmark,
  Ship,
  Cpu,
  ArrowRight,
} from "lucide-react";
import { formatPct, safeNum, safeArr } from "../lib/format";
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from "@/types/observatory";

// ── Channel definitions ──────────────────────────────────────────────

interface ChannelDef {
  id: string;
  label: string;
  labelAr: string;
  icon: React.ReactNode;
  color: string;        // Tailwind-compatible hex
  accentBg: string;     // icon bg class
  /** Returns true if an edge belongs to this channel */
  match: (edge: KnowledgeGraphEdge, nodeMap: Map<string, KnowledgeGraphNode>) => boolean;
}

const CHANNELS: ChannelDef[] = [
  {
    id: "oil_energy",
    label: "Oil & Energy",
    labelAr: "النفط والطاقة",
    icon: <Fuel size={14} />,
    color: "#F59E0B",
    accentBg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    match: (edge, nodeMap) => {
      const s = nodeMap.get(edge.source);
      const t = nodeMap.get(edge.target);
      if (!s || !t) return false;
      // Edges touching economy-layer corporations (Aramco, ADNOC) or commodities (Brent)
      // or infrastructure-layer ports involved in energy export
      const ids = [edge.source, edge.target];
      const hasEnergy = ids.some((id) => id.includes("crude") || id.includes("aramco") || id.includes("adnoc") || id.includes("tanura"));
      const hasInfra = [s, t].some((n) => n.layer === "economy" && n.type === "commodity");
      return hasEnergy || hasInfra;
    },
  },
  {
    id: "liquidity_fx",
    label: "Liquidity & FX",
    labelAr: "السيولة والعملات",
    icon: <Landmark size={14} />,
    color: "#3B82F6",
    accentBg: "bg-blue-500/10 border-blue-500/20 text-blue-400",
    match: (edge, nodeMap) => {
      const s = nodeMap.get(edge.source);
      const t = nodeMap.get(edge.target);
      if (!s || !t) return false;
      // Edges touching central banks (SAMA, CBUAE) or finance-layer nodes
      return [s, t].some((n) => n.type === "central_bank" || (n.layer === "finance" && n.type !== "sector"));
    },
  },
  {
    id: "trade_ports",
    label: "Trade & Ports",
    labelAr: "التجارة والموانئ",
    icon: <Ship size={14} />,
    color: "#14B8A6",
    accentBg: "bg-teal-500/10 border-teal-500/20 text-teal-400",
    match: (edge, nodeMap) => {
      const s = nodeMap.get(edge.source);
      const t = nodeMap.get(edge.target);
      if (!s || !t) return false;
      const ids = [edge.source, edge.target];
      const hasTrade = ids.some((id) => id.includes("trade") || id.includes("jebel_ali"));
      const hasPort = [s, t].some((n) => n.type === "port" || n.type === "chokepoint");
      return hasTrade || hasPort;
    },
  },
  {
    id: "fintech_insurance",
    label: "Insurance & Fintech",
    labelAr: "التأمين والتقنية المالية",
    icon: <Cpu size={14} />,
    color: "#8B5CF6",
    accentBg: "bg-violet-500/10 border-violet-500/20 text-violet-400",
    match: (edge, nodeMap) => {
      const s = nodeMap.get(edge.source);
      const t = nodeMap.get(edge.target);
      if (!s || !t) return false;
      const ids = [edge.source, edge.target];
      return ids.some((id) => id.includes("insurance") || id.includes("fintech"));
    },
  },
];

// ── Derived channel data ─────────────────────────────────────────────

interface ChannelData {
  def: ChannelDef;
  edges: KnowledgeGraphEdge[];
  topEdge: KnowledgeGraphEdge | null;
  maxTransmission: number;
  avgTransmission: number;
  sourceLabel: string;
  targetLabel: string;
}

function deriveChannels(
  nodes: KnowledgeGraphNode[],
  edges: KnowledgeGraphEdge[],
): ChannelData[] {
  const nodeMap = new Map<string, KnowledgeGraphNode>();
  for (const n of nodes) nodeMap.set(n.id, n);

  // Assign each edge to first matching channel (an edge can only belong to one)
  const assigned = new Set<string>();

  return CHANNELS.map((def) => {
    const matching = edges.filter((e) => {
      if (assigned.has(e.id)) return false;
      return def.match(e, nodeMap);
    });
    // Mark edges as assigned so they aren't double-counted
    for (const e of matching) assigned.add(e.id);

    // Find highest-transmission edge for the headline flow
    let topEdge: KnowledgeGraphEdge | null = null;
    let maxT = 0;
    let sumT = 0;
    for (const e of matching) {
      const t = safeNum(e.transmission);
      sumT += t;
      if (t > maxT) {
        maxT = t;
        topEdge = e;
      }
    }

    const sourceLabel = topEdge ? (nodeMap.get(topEdge.source)?.label ?? topEdge.source) : "—";
    const targetLabel = topEdge ? (nodeMap.get(topEdge.target)?.label ?? topEdge.target) : "—";

    return {
      def,
      edges: matching,
      topEdge,
      maxTransmission: maxT,
      avgTransmission: matching.length > 0 ? sumT / matching.length : 0,
      sourceLabel,
      targetLabel,
    };
  });
}

// ── Channel Card ─────────────────────────────────────────────────────

function ChannelCard({ channel, isAr }: { channel: ChannelData; isAr: boolean }) {
  const { def, edges, maxTransmission, sourceLabel, targetLabel } = channel;
  const pct = Math.min(100, Math.max(0, Math.round(maxTransmission * 100)));
  const hasData = edges.length > 0;

  return (
    <div
      className={`flex-1 min-w-[200px] rounded-lg border bg-[#0D1117] overflow-hidden transition-opacity ${
        hasData ? "opacity-100" : "opacity-40"
      }`}
      style={{ borderColor: `${def.color}25` }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex items-center gap-2">
          <div className={`w-6 h-6 rounded flex items-center justify-center border ${def.accentBg}`}>
            {def.icon}
          </div>
          <div>
            <p className="text-[11px] font-semibold text-slate-300">
              {isAr ? def.labelAr : def.label}
            </p>
            <p className="text-[9px] text-slate-600">
              {edges.length} {isAr ? "رابط" : edges.length === 1 ? "link" : "links"}
            </p>
          </div>
        </div>
        <span
          className="text-xs font-bold tabular-nums"
          style={{ color: hasData ? def.color : "#475569" }}
        >
          {hasData ? formatPct(maxTransmission) : "—"}
        </span>
      </div>

      {/* Transmission bar */}
      <div className="px-3 pb-1.5">
        <div className="w-full h-1 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${pct}%`, backgroundColor: def.color }}
          />
        </div>
      </div>

      {/* Directional flow */}
      {hasData && (
        <div className="flex items-center gap-1.5 px-3 pb-2.5 text-[10px]">
          <span className="text-slate-400 truncate max-w-[80px]" title={sourceLabel}>
            {sourceLabel}
          </span>
          <ArrowRight size={10} style={{ color: def.color }} className="flex-shrink-0" />
          <span className="text-slate-400 truncate max-w-[80px]" title={targetLabel}>
            {targetLabel}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

interface TransmissionChannelsProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  lang?: "en" | "ar";
}

export function TransmissionChannels({ nodes, edges, lang }: TransmissionChannelsProps) {
  const _nodes = safeArr<KnowledgeGraphNode>(nodes);
  const _edges = safeArr<KnowledgeGraphEdge>(edges);
  const isAr = lang === "ar";

  const channels = useMemo(() => deriveChannels(_nodes, _edges), [_nodes, _edges]);

  // Don't render if there are no edges at all
  if (_edges.length === 0) return null;

  return (
    <div className="w-full bg-[#0A0E18] border-b border-white/[0.04] px-6 py-3">
      {/* Section label */}
      <div className="flex items-center gap-2 mb-2.5">
        <div className="w-1 h-3 rounded-full bg-blue-500" />
        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
          {isAr ? "قنوات الانتقال" : "Transmission Channels"}
        </span>
        <div className="flex-1 h-px bg-white/[0.04]" />
      </div>

      {/* Channel cards */}
      <div className="flex items-stretch gap-2 overflow-x-auto">
        {channels.map((ch) => (
          <ChannelCard key={ch.def.id} channel={ch} isAr={isAr} />
        ))}
      </div>
    </div>
  );
}
