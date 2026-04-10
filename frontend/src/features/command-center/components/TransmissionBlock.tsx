"use client";

/**
 * Transmission Block — Propagation path visualization with breakable points.
 *
 * Shows the causal transmission chain as a horizontal flow: source → target
 * with delay, severity transfer ratio, and breakable-point markers.
 * Critical window alert when total delay ≤ 24h AND max severity ≥ 0.45.
 */

import React, { useState } from "react";
import {
  ArrowRight,
  AlertTriangle,
  Clock,
  Scissors,
  Activity,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { formatHours, formatPct, safeNum } from "../lib/format";
import type { TransmissionBlockView } from "../lib/decision-view-models";
import type { TransmissionNode } from "@/types/observatory";

// ── Severity Color ──────────────────────────────────────────────────────

function severityColor(severity: number): string {
  if (severity >= 0.8) return "#EF4444";
  if (severity >= 0.6) return "#F59E0B";
  if (severity >= 0.4) return "#EAB308";
  if (severity >= 0.2) return "#22C55E";
  return "#64748B";
}

// ── Chain Node Visual ───────────────────────────────────────────────────

function ChainNode({
  node,
  isLast,
}: {
  node: TransmissionNode;
  isLast: boolean;
}) {
  const sevColor = severityColor(safeNum(node.severity_at_target));
  const isBreakable = node.breakable_point;

  return (
    <div className="flex items-center gap-0">
      {/* Node box */}
      <div
        className={`relative flex-shrink-0 px-3 py-2 rounded-lg border ${
          isBreakable
            ? "border-amber-500/40 bg-amber-500/8"
            : "border-white/[0.08] bg-[#0F1420]"
        }`}
      >
        {/* Breakable point marker */}
        {isBreakable && (
          <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
            <Scissors size={8} className="text-amber-400" />
          </div>
        )}

        <p className="text-[11px] font-semibold text-slate-200 leading-tight max-w-[120px] truncate">
          {node.target_label || node.target}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[9px] text-slate-500 uppercase">
            {node.target_sector}
          </span>
          <span
            className="text-[9px] font-bold tabular-nums"
            style={{ color: sevColor }}
          >
            {formatPct(safeNum(node.severity_at_target))}
          </span>
        </div>
      </div>

      {/* Arrow connector with delay label */}
      {!isLast && (
        <div className="flex flex-col items-center mx-1 flex-shrink-0">
          <span className="text-[8px] text-slate-600 tabular-nums mb-0.5">
            {formatHours(safeNum(node.propagation_delay_hours))}
          </span>
          <ArrowRight size={12} className="text-slate-600" />
          <span className="text-[8px] text-slate-700 tabular-nums mt-0.5">
            {formatPct(safeNum(node.severity_transfer_ratio))}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

interface TransmissionBlockProps {
  view: TransmissionBlockView;
}

export function TransmissionBlock({ view }: TransmissionBlockProps) {
  const [expanded, setExpanded] = useState(false);

  if (view.nodes.length === 0) return null;

  const visibleNodes = expanded ? view.nodes : view.nodes.slice(0, 5);
  const hasMore = view.nodes.length > 5;

  return (
    <div className="bg-[#0A0E18] border-b border-white/[0.06]">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-2.5 border-b border-white/[0.04]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            Transmission Path
          </h2>
          <span className="text-[10px] text-slate-600 tabular-nums">
            {view.chain_length} hops · {formatHours(view.total_delay_hours)} total delay
          </span>
        </div>
        <div className="flex items-center gap-2">
          {view.breakable_points.length > 0 && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
              <Scissors size={10} className="text-amber-400" />
              <span className="text-[10px] font-bold text-amber-400">
                {view.breakable_points.length} breakable
              </span>
            </div>
          )}
          {view.critical_window_active && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-red-500/10 border border-red-500/20">
              <AlertTriangle size={10} className="text-red-500" />
              <span className="text-[10px] font-bold text-red-400">
                Critical Window
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Summary bar */}
      <div className="px-6 py-2 flex items-center gap-4 border-b border-white/[0.03]">
        <div className="flex items-center gap-1.5">
          <Clock size={11} className="text-slate-500" />
          <span className="text-[10px] text-slate-500">Total Delay</span>
          <span className="text-[11px] font-bold text-slate-300 tabular-nums">
            {formatHours(view.total_delay_hours)}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Activity size={11} className="text-slate-500" />
          <span className="text-[10px] text-slate-500">Max Severity</span>
          <span
            className="text-[11px] font-bold tabular-nums"
            style={{ color: severityColor(view.max_severity) }}
          >
            {formatPct(view.max_severity)}
          </span>
        </div>
        <div className="flex-1" />
        <p className="text-[10px] text-slate-600 max-w-[300px] truncate">
          {view.summary}
        </p>
      </div>

      {/* Chain visualization */}
      <div className="px-6 py-3 overflow-x-auto">
        <div className="flex items-center gap-0 min-w-min">
          {visibleNodes.map((node, i) => (
            <ChainNode
              key={`tx-${node.hop}-${node.target}`}
              node={node}
              isLast={i === visibleNodes.length - 1}
            />
          ))}
        </div>

        {/* Expand/collapse */}
        {hasMore && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-400 transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded
              ? "Show fewer"
              : `+${view.nodes.length - 5} more hops`}
          </button>
        )}
      </div>
    </div>
  );
}
