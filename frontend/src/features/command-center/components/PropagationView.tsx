"use client";

/**
 * PropagationView — Causal cascade visualization
 *
 * Shows the propagation chain as a directed flow from source event
 * through intermediate nodes to terminal impacts. Two modes:
 * 1. Chain view: step-by-step causal trace
 * 2. Sector heatmap: sector-level impact summary
 */

import React, { useState } from "react";
import {
  Layers,
  GitBranch,
} from "lucide-react";
import { formatUSD, formatPct, classificationColor, stressToClassification, safeNum, safeStr } from "../lib/format";
import type { CausalStep, SectorImpact } from "@/types/observatory";

// ── Types ─────────────────────────────────────────────────────────────

interface PropagationViewProps {
  causalChain: CausalStep[];
  sectorImpacts: SectorImpact[];
  totalLossUsd: number;
  propagationDepth: number;
  confidence: number;
}

// ── Mechanism Badge ───────────────────────────────────────────────────

const MECHANISM_STYLES: Record<string, string> = {
  direct_shock: "text-red-400 bg-red-400/10",
  price_transmission: "text-amber-400 bg-amber-400/10",
  physical_constraint: "text-orange-400 bg-orange-400/10",
  capacity_overflow: "text-yellow-400 bg-yellow-400/10",
  supply_chain: "text-blue-400 bg-blue-400/10",
  claims_cascade: "text-indigo-400 bg-indigo-400/10",
  monetary_transmission: "text-emerald-400 bg-emerald-400/10",
};

function MechanismTag({ mechanism }: { mechanism: string }) {
  const safeMechanism = safeStr(mechanism, "unknown");
  const style =
    MECHANISM_STYLES[safeMechanism] ?? "text-slate-400 bg-slate-400/10";
  const label = safeMechanism.replace(/_/g, " ");
  return (
    <span
      className={`px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider rounded ${style}`}
    >
      {label}
    </span>
  );
}

// ── Causal Step Row ───────────────────────────────────────────────────

function CausalStepRow({
  step,
  isLast,
}: {
  step: CausalStep;
  isLast: boolean;
}) {
  const _stressDelta = safeNum(step.stress_delta);
  const _impactUsd = safeNum(step.impact_usd);
  const _stepNum = safeNum(step.step, 1);
  const _label = safeStr(step.entity_label, "Unknown Entity");
  const _mechanism = safeStr(step.mechanism, "propagation");
  const _event = safeStr(step.event, "No event description");

  const classification = stressToClassification(_stressDelta);
  const nodeColor = classificationColor(classification);

  return (
    <div className="flex gap-3">
      {/* Timeline rail */}
      <div className="flex flex-col items-center flex-shrink-0 w-6">
        <div
          className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
          style={{
            borderColor: nodeColor,
            backgroundColor: `${nodeColor}20`,
          }}
        >
          <span className="text-[8px] font-bold tabular-nums" style={{ color: nodeColor }}>
            {_stepNum}
          </span>
        </div>
        {!isLast && (
          <div className="w-px flex-1 min-h-[24px] bg-white/[0.08]" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-4 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[12px] font-semibold text-white">
            {_label}
          </span>
          <MechanismTag mechanism={_mechanism} />
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed mb-1.5">
          {_event}
        </p>
        <div className="flex items-center gap-3 text-[10px]">
          {_impactUsd > 0 && (
            <span className="text-red-400 font-semibold tabular-nums">
              {formatUSD(_impactUsd)} impact
            </span>
          )}
          <span
            className="font-semibold tabular-nums"
            style={{ color: nodeColor }}
          >
            Stress: {formatPct(_stressDelta)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Sector Impact Bar ─────────────────────────────────────────────────

function SectorBar({ sector }: { sector: SectorImpact }) {
  const pct = Math.round(safeNum(sector.avgImpact) * 100);
  const _label = safeStr(sector.sectorLabel, "Unknown");
  const _color = safeStr(sector.color, "#64748B");
  const _nodeCount = safeNum(sector.nodeCount);

  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-20 text-right">
        <span className="text-[11px] font-medium text-slate-400">
          {_label}
        </span>
      </div>
      <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            backgroundColor: _color,
          }}
        />
      </div>
      <div className="w-16 text-right">
        <span
          className="text-[11px] font-bold tabular-nums"
          style={{ color: _color }}
        >
          {pct}%
        </span>
      </div>
      <div className="w-10 text-right">
        <span className="text-[10px] text-slate-600 tabular-nums">
          {_nodeCount}n
        </span>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function PropagationView({
  causalChain,
  sectorImpacts,
  totalLossUsd,
  propagationDepth,
  confidence,
}: PropagationViewProps) {
  const [mode, setMode] = useState<"chain" | "sectors">("chain");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Propagation Trace
        </h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setMode("chain")}
            className={`px-2 py-1 text-[10px] font-medium rounded transition-colors ${
              mode === "chain"
                ? "bg-blue-600/20 text-blue-400"
                : "text-slate-600 hover:text-slate-400"
            }`}
          >
            <GitBranch size={10} className="inline mr-0.5" />
            Chain
          </button>
          <button
            onClick={() => setMode("sectors")}
            className={`px-2 py-1 text-[10px] font-medium rounded transition-colors ${
              mode === "sectors"
                ? "bg-blue-600/20 text-blue-400"
                : "text-slate-600 hover:text-slate-400"
            }`}
          >
            <Layers size={10} className="inline mr-0.5" />
            Sectors
          </button>
        </div>
      </div>

      {/* Summary strip */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-white/[0.04] bg-white/[0.01]">
        <span className="text-[10px] text-slate-600">
          Depth: <span className="text-slate-300 font-bold">{propagationDepth}</span>
        </span>
        <span className="text-[10px] text-slate-600">
          Loss: <span className="text-red-400 font-bold">{formatUSD(totalLossUsd)}</span>
        </span>
        <span className="text-[10px] text-slate-600">
          Conf: <span className="text-slate-300 font-bold">{formatPct(confidence)}</span>
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {mode === "chain" ? (
          causalChain.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center px-4">
                <p className="text-xs text-slate-500 mb-1">No causal chain available</p>
                <p className="text-[10px] text-slate-700">
                  Causal steps populate from the propagation engine output.
                </p>
              </div>
            </div>
          ) : (
            <div>
              {causalChain.map((step, i) => (
                <CausalStepRow
                  key={step.step}
                  step={step}
                  isLast={i === causalChain.length - 1}
                />
              ))}
            </div>
          )
        ) : sectorImpacts.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center px-4">
              <p className="text-xs text-slate-500 mb-1">No sector data available</p>
              <p className="text-[10px] text-slate-700">
                Sector impacts derive from graph node stress values.
              </p>
            </div>
          </div>
        ) : (
          <div>
            <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-3">
              Average Impact by Sector
            </p>
            {[...sectorImpacts]
              .sort((a, b) => safeNum(b.avgImpact) - safeNum(a.avgImpact))
              .map((s) => (
                <SectorBar key={s.sector} sector={s} />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
