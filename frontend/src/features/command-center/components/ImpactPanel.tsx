"use client";

/**
 * ImpactPanel — Per-entity impact grid for the Command Center
 *
 * Renders SafeImpact[] as a compact table grouped by sector.
 * Shows: domain, entity, exposure, severity tier, stress bar,
 * and sector-specific metrics (LCR, solvency, availability).
 *
 * No charts — text/grid only per spec.
 */

import React, { useMemo, useState } from "react";
import { formatUSD, formatPct, classificationColor, stressToClassification } from "../lib/format";
import type { SafeImpact, SeverityTier } from "@/lib/v2/api-types";

// ── Types ─────────────────────────────────────────────────────────────

interface ImpactPanelProps {
  impacts: SafeImpact[];
}

// ── Severity badge ────────────────────────────────────────────────────

function SeverityBadge({ tier }: { tier: SeverityTier }) {
  const color = classificationColor(
    tier === "SEVERE" ? "CRITICAL" :
    tier === "HIGH" ? "ELEVATED" :
    tier === "GUARDED" ? "MODERATE" :
    tier,
  );
  return (
    <span
      className="px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded"
      style={{ color, backgroundColor: `${color}18` }}
    >
      {tier}
    </span>
  );
}

// ── Stress bar (inline) ──────────────────────────────────────────────

function StressBar({ value }: { value: number }) {
  const pct = Math.min(Math.max(value * 100, 0), 100);
  const cls = stressToClassification(value);
  const color = classificationColor(cls);
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-bold tabular-nums w-8 text-right" style={{ color }}>
        {Math.round(pct)}
      </span>
    </div>
  );
}

// ── Sector-specific detail (inline, compact) ─────────────────────────

function SectorDetail({ impact }: { impact: SafeImpact }) {
  switch (impact.sector) {
    case "banking":
      return (
        <div className="flex items-center gap-3 text-[10px] text-slate-500">
          <span>LCR: <span className="text-slate-300 font-semibold">{formatPct(impact.lcr)}</span></span>
          <span>CET1: <span className="text-slate-300 font-semibold">{formatPct(impact.cet1Ratio)}</span></span>
          <span>CAR: <span className="text-slate-300 font-semibold">{formatPct(impact.capitalAdequacyRatio)}</span></span>
        </div>
      );
    case "insurance":
      return (
        <div className="flex items-center gap-3 text-[10px] text-slate-500">
          <span>Solvency: <span className="text-slate-300 font-semibold">{formatPct(impact.solvencyRatio)}</span></span>
          <span>Combined: <span className="text-slate-300 font-semibold">{formatPct(impact.combinedRatio)}</span></span>
        </div>
      );
    case "fintech":
      return (
        <div className="flex items-center gap-3 text-[10px] text-slate-500">
          <span>Avail: <span className="text-slate-300 font-semibold">{formatPct(impact.serviceAvailability)}</span></span>
          <span>Delay: <span className="text-slate-300 font-semibold">{Math.round(impact.settlementDelayMinutes)}m</span></span>
        </div>
      );
    default:
      return null;
  }
}

// ── Impact row ───────────────────────────────────────────────────────

function ImpactRow({ impact }: { impact: SafeImpact }) {
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/[0.02] transition-colors border-b border-white/[0.03] last:border-b-0">
      {/* Entity + sector */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[12px] font-medium text-slate-200 truncate">
            {impact.entityLabel}
          </span>
          <SeverityBadge tier={impact.stressTier} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">
            {impact.sector}
          </span>
          <SectorDetail impact={impact} />
        </div>
      </div>

      {/* Exposure */}
      <div className="text-right flex-shrink-0 w-20">
        <p className="text-[10px] text-slate-600 uppercase tracking-wider">Exposure</p>
        <p className="text-[12px] font-bold text-red-400 tabular-nums">
          {formatUSD(impact.lossUsd)}
        </p>
      </div>

      {/* Stress bar */}
      <div className="flex-shrink-0 w-28">
        <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">Stress</p>
        <StressBar value={impact.stressLevel} />
      </div>
    </div>
  );
}

// ── Sector filter tabs ───────────────────────────────────────────────

const SECTOR_ORDER = ["all", "banking", "insurance", "fintech", "financial"] as const;
type SectorFilter = (typeof SECTOR_ORDER)[number];

const SECTOR_TAB_COLORS: Record<string, string> = {
  all: "text-slate-400",
  banking: "text-teal-400",
  insurance: "text-indigo-400",
  fintech: "text-violet-400",
  financial: "text-emerald-400",
};

// ── Main Component ────────────────────────────────────────────────────

export function ImpactPanel({ impacts }: ImpactPanelProps) {
  const [filter, setFilter] = useState<SectorFilter>("all");

  // Compute available sectors from data
  const availableSectors = useMemo(() => {
    const sectors = new Set(impacts.map((i) => i.sector));
    return SECTOR_ORDER.filter((s) => s === "all" || sectors.has(s));
  }, [impacts]);

  // Filter + sort by stress descending
  const filtered = useMemo(() => {
    const base = filter === "all" ? impacts : impacts.filter((i) => i.sector === filter);
    return [...base].sort((a, b) => b.stressLevel - a.stressLevel);
  }, [impacts, filter]);

  // Headline stats
  const totalExposure = useMemo(
    () => impacts.reduce((sum, i) => sum + i.lossUsd, 0),
    [impacts],
  );
  const avgStress = useMemo(
    () => impacts.length > 0 ? impacts.reduce((sum, i) => sum + i.stressLevel, 0) / impacts.length : 0,
    [impacts],
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Impact Assessment
        </h2>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="text-slate-600">
            {impacts.length} entities
          </span>
          <span className="text-slate-600">
            Exposure: <span className="text-red-400 font-bold">{formatUSD(totalExposure)}</span>
          </span>
          <span className="text-slate-600">
            Avg stress: <span className="font-bold" style={{ color: classificationColor(stressToClassification(avgStress)) }}>
              {Math.round(avgStress * 100)}
            </span>
          </span>
        </div>
      </div>

      {/* Sector filter tabs */}
      {availableSectors.length > 2 && (
        <div className="flex items-center gap-1 px-4 py-2 border-b border-white/[0.04]">
          {availableSectors.map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-2 py-1 text-[10px] font-medium rounded transition-colors capitalize ${
                filter === s
                  ? `bg-white/[0.06] ${SECTOR_TAB_COLORS[s] ?? "text-slate-400"}`
                  : "text-slate-600 hover:text-slate-400"
              }`}
            >
              {s === "all" ? `All (${impacts.length})` : `${s} (${impacts.filter((i) => i.sector === s).length})`}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {impacts.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center px-6">
            <p className="text-xs text-slate-500 mb-1">No impact data available</p>
            <p className="text-[10px] text-slate-700">
              Impact assessment populates after the sector engine completes.
            </p>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center px-6">
            <p className="text-xs text-slate-500">No entities in this sector</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          {filtered.map((impact, i) => (
            <ImpactRow key={`${impact.entityId}-${i}`} impact={impact} />
          ))}
        </div>
      )}
    </div>
  );
}
