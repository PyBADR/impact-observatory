"use client";

/**
 * EventHeader — Top bar of the Decision Command Center
 *
 * Shows: scenario label, severity, domain tag, headline KPIs,
 * executive status, confidence score, and time context.
 * Single-row command bar — the first thing the executive reads.
 */

import React from "react";
import {
  AlertTriangle,
  Clock,
  Shield,
  Activity,
  TrendingDown,
  Zap,
} from "lucide-react";
import { formatUSD, formatPct, stressToClassification, safeNum, safeStr, safeDate, safeArr } from "../lib/format";

// ── Types ─────────────────────────────────────────────────────────────

interface EventHeaderProps {
  scenarioLabel: string;
  scenarioLabelAr?: string;
  domain: string;
  severity: number;
  horizonHours: number;
  triggerTime: string;
  totalLossUsd: number;
  nodesImpacted: number;
  propagationDepth: number;
  confidence: number;
  peakDay: number;
  criticalCount: number;
  pipelineStages: string[];
  lang?: "en" | "ar";
}

// ── Severity Pulse ────────────────────────────────────────────────────

function SeverityPulse({ severity }: { severity: number }) {
  const classification = stressToClassification(severity);
  const colors: Record<string, string> = {
    CRITICAL: "bg-red-500",
    ELEVATED: "bg-amber-500",
    MODERATE: "bg-yellow-500",
    LOW: "bg-emerald-500",
    NOMINAL: "bg-slate-500",
  };
  return (
    <span className="relative flex h-3 w-3">
      <span
        className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${colors[classification]}`}
      />
      <span
        className={`relative inline-flex rounded-full h-3 w-3 ${colors[classification]}`}
      />
    </span>
  );
}

// ── Domain Badge ──────────────────────────────────────────────────────

const DOMAIN_COLORS: Record<string, string> = {
  MARITIME: "border-blue-400/60 text-blue-300",
  ENERGY: "border-amber-400/60 text-amber-300",
  FINANCIAL: "border-indigo-400/60 text-indigo-300",
  CYBER: "border-red-400/60 text-red-300",
  AVIATION: "border-sky-400/60 text-sky-300",
  TRADE: "border-teal-400/60 text-teal-300",
};

function DomainTag({ domain }: { domain: string }) {
  const style = DOMAIN_COLORS[domain] ?? "border-slate-400/60 text-slate-300";
  return (
    <span
      className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest border rounded ${style}`}
    >
      {domain}
    </span>
  );
}

// ── KPI Chip ──────────────────────────────────────────────────────────

function KPIChip({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
      <div className="text-slate-400 flex-shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider leading-tight">
          {label}
        </p>
        <p
          className="text-sm font-bold tabular-nums leading-tight"
          style={{ color: accent ?? "#E2E8F0" }}
        >
          {value}
        </p>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function EventHeader({
  scenarioLabel,
  domain,
  severity,
  horizonHours,
  triggerTime,
  totalLossUsd,
  nodesImpacted,
  propagationDepth,
  confidence,
  peakDay,
  criticalCount,
  pipelineStages,
}: EventHeaderProps) {
  // ── Safe coercion — zero runtime crashes on malformed data ──
  const _severity = safeNum(severity);
  const _confidence = safeNum(confidence);
  const _horizonHours = safeNum(horizonHours);
  const _nodesImpacted = safeNum(nodesImpacted);
  const _propagationDepth = safeNum(propagationDepth);
  const _peakDay = safeNum(peakDay);
  const _criticalCount = safeNum(criticalCount);
  const _totalLossUsd = safeNum(totalLossUsd);
  const _scenarioLabel = safeStr(scenarioLabel, "Unknown Scenario");
  const _domain = safeStr(domain, "UNKNOWN");
  const _pipelineStages = safeArr<string>(pipelineStages);

  const classification = stressToClassification(_severity);
  const classColors: Record<string, string> = {
    CRITICAL: "#EF4444",
    ELEVATED: "#F59E0B",
    MODERATE: "#EAB308",
    LOW: "#22C55E",
    NOMINAL: "#64748B",
  };

  return (
    <header className="w-full bg-[#0B0F1A] border-b border-white/[0.06]">
      {/* Top row: scenario + meta */}
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <SeverityPulse severity={_severity} />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white tracking-tight">
                {_scenarioLabel}
              </h1>
              <DomainTag domain={_domain} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Triggered {safeDate(triggerTime)}{" "}
              — {_horizonHours}h horizon — {_pipelineStages.length}/9 stages
            </p>
          </div>
        </div>

        {/* Right: Classification + Confidence */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield size={14} className="text-slate-500" />
            <span className="text-xs text-slate-400">Confidence</span>
            <span
              className="text-sm font-bold tabular-nums"
              style={{ color: _confidence >= 0.8 ? "#22C55E" : _confidence >= 0.6 ? "#EAB308" : "#EF4444" }}
            >
              {formatPct(_confidence)}
            </span>
          </div>
          <div
            className="px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider"
            style={{
              backgroundColor: `${classColors[classification]}20`,
              color: classColors[classification],
              border: `1px solid ${classColors[classification]}40`,
            }}
          >
            {classification}
          </div>
        </div>
      </div>

      {/* KPI strip */}
      <div className="flex items-center gap-2 px-6 pb-3 overflow-x-auto">
        <KPIChip
          icon={<TrendingDown size={14} />}
          label="Total Loss"
          value={formatUSD(_totalLossUsd)}
          accent="#EF4444"
        />
        <KPIChip
          icon={<Zap size={14} />}
          label="Nodes Hit"
          value={`${_nodesImpacted}`}
          accent="#F59E0B"
        />
        <KPIChip
          icon={<Activity size={14} />}
          label="Prop. Depth"
          value={`${_propagationDepth} layers`}
        />
        <KPIChip
          icon={<AlertTriangle size={14} />}
          label="Critical"
          value={`${_criticalCount} entities`}
          accent="#EF4444"
        />
        <KPIChip
          icon={<Clock size={14} />}
          label="Peak Day"
          value={`Day ${_peakDay}`}
          accent="#F59E0B"
        />
      </div>
    </header>
  );
}
