"use client";

/**
 * SectorRollupBar — Horizontal sector stress summary strip
 *
 * Shows all sector rollups as a compact bar chart with stress index,
 * total loss, node count, and classification badge.
 * Sits between the main grid and explanation panel.
 */

import React from "react";
import {
  Building2,
  Shield,
  Cpu,
  Fuel,
  Ship,
  Landmark,
} from "lucide-react";
import { formatUSD, stressToClassification, classificationColor, safeNum, safeStr } from "../lib/format";
import type { SectorRollup, StressClassification } from "@/types/observatory";

// ── Types ─────────────────────────────────────────────────────────────

interface SectorRollupBarProps {
  rollups: Record<string, SectorRollup>;
}

// ── Sector Icon Map ───────────────────────────────────────────────────

const SECTOR_ICONS: Record<string, React.ReactNode> = {
  banking: <Landmark size={14} />,
  insurance: <Shield size={14} />,
  fintech: <Cpu size={14} />,
  energy: <Fuel size={14} />,
  trade: <Ship size={14} />,
};

const SECTOR_LABELS: Record<string, string> = {
  banking: "Banking",
  insurance: "Insurance",
  fintech: "Fintech",
  energy: "Energy",
  trade: "Trade",
};

// ── Single Sector Card ────────────────────────────────────────────────

function SectorCard({
  sectorKey,
  rollup,
}: {
  sectorKey: string;
  rollup: SectorRollup;
}) {
  const _classification = safeStr(rollup.classification, "NOMINAL");
  const color = classificationColor(_classification);
  const _aggregateStress = safeNum(rollup.aggregate_stress);
  const stressIndex = Math.round(_aggregateStress * 100);
  const _totalLoss = safeNum(rollup.total_loss);
  const _nodeCount = safeNum(rollup.node_count);
  const icon = SECTOR_ICONS[sectorKey] ?? <Building2 size={14} />;
  const label = SECTOR_LABELS[sectorKey] ?? sectorKey;

  return (
    <div
      className="flex-1 min-w-[140px] bg-[#0F1420] border border-white/[0.06] rounded-lg px-3 py-2.5 relative overflow-hidden"
      style={{ borderTopWidth: "2px", borderTopColor: color }}
    >
      {/* Background stress fill */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          background: `linear-gradient(90deg, ${color} 0%, transparent ${stressIndex}%)`,
        }}
      />

      <div className="relative">
        <div className="flex items-center gap-1.5 mb-1.5">
          <span style={{ color }}>{icon}</span>
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            {label}
          </span>
        </div>

        <div className="flex items-baseline gap-1 mb-1">
          <span
            className="text-lg font-bold tabular-nums leading-none"
            style={{ color }}
          >
            {stressIndex}
          </span>
          <span className="text-[10px] text-slate-600">/100</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-600 tabular-nums">
            {formatUSD(_totalLoss)}
          </span>
          <span className="text-[9px] text-slate-600">
            {_nodeCount}n
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function SectorRollupBar({ rollups }: SectorRollupBarProps) {
  const entries = Object.entries(rollups ?? {}).sort(
    ([, a], [, b]) => safeNum(b.aggregate_stress) - safeNum(a.aggregate_stress),
  );

  if (entries.length === 0) return null;

  return (
    <div className="w-full bg-[#080C14] border-t border-b border-white/[0.04] px-4 py-3">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
          Sector Exposure
        </h3>
        <span className="text-[10px] text-slate-700">
          {entries.length} sectors
        </span>
      </div>
      <div className="flex gap-2 overflow-x-auto">
        {entries.map(([key, rollup]) => (
          <SectorCard key={key} sectorKey={key} rollup={rollup} />
        ))}
      </div>
    </div>
  );
}
