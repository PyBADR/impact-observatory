"use client";

/**
 * MacroOverviewHeader — Top bar of the Decision Command Center
 *
 * Repositions entry from event-first to macro-first:
 *   1. GCC Macro Overview title (bilingual)
 *   2. System Risk Index — composite severity with classification badge
 *   3. Affected Regions — derived from graph nodes (geography + infra layers)
 *   4. Exposure Level — total economic exposure with stress-driven color
 *
 * Scenario-specific context (domain, horizon, trigger) moves to a
 * secondary row beneath the macro bar — still visible, but subordinate.
 *
 * All values pass through safe* coercion — zero NaN, zero undefined.
 */

import React from "react";
import {
  Globe,
  Shield,
  AlertTriangle,
  Activity,
  TrendingDown,
  MapPin,
  Clock,
} from "lucide-react";
import {
  formatUSD,
  formatPct,
  formatHours,
  stressToClassification,
  classificationColor,
  safeNum,
  safeStr,
  safeArr,
  safeDate,
} from "../lib/format";

// ── Types ─────────────────────────────────────────────────────────────

interface MacroOverviewHeaderProps {
  // Macro-level (primary)
  systemRiskIndex: number;
  totalExposureUsd: number;
  affectedRegions: string[];
  nodesImpacted: number;
  criticalCount: number;
  elevatedCount: number;
  confidence: number;
  averageStress: number;

  // Scenario context (secondary)
  scenarioLabel: string;
  scenarioLabelAr?: string;
  domain: string;
  severity: number;
  horizonHours: number;
  triggerTime: string;
  pipelineStages: string[];

  lang?: "en" | "ar";
}

// ── Classification Badge ──────────────────────────────────────────────

function ClassificationBadge({ level, color }: { level: string; color: string }) {
  return (
    <div
      className="px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider"
      style={{
        backgroundColor: `${color}20`,
        color,
        border: `1px solid ${color}40`,
      }}
    >
      {level}
    </div>
  );
}

// ── Risk Index Gauge ──────────────────────────────────────────────────

function RiskGauge({ value, classification, color }: { value: number; classification: string; color: string }) {
  const pct = Math.min(100, Math.max(0, Math.round(value * 100)));
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 min-w-[120px]">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">System Risk Index</span>
          <span className="text-sm font-bold tabular-nums" style={{ color }}>
            {formatPct(value)}
          </span>
        </div>
        <div className="w-full h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
      </div>
      <ClassificationBadge level={classification} color={color} />
    </div>
  );
}

// ── Region Chip ──────────────────────────────────────────────────────

function RegionChip({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-[10px] text-slate-400 font-medium">
      <MapPin size={9} className="text-slate-500" />
      {name}
    </span>
  );
}

// ── Macro KPI ────────────────────────────────────────────────────────

function MacroKPI({
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

// ── Domain Badge (secondary context) ─────────────────────────────────

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

// ── Main Component ────────────────────────────────────────────────────

export function MacroOverviewHeader({
  systemRiskIndex,
  totalExposureUsd,
  affectedRegions,
  nodesImpacted,
  criticalCount,
  elevatedCount,
  confidence,
  averageStress,
  scenarioLabel,
  scenarioLabelAr,
  domain,
  severity,
  horizonHours,
  triggerTime,
  pipelineStages,
  lang,
}: MacroOverviewHeaderProps) {
  // ── Safe coercion ──
  const _risk = safeNum(systemRiskIndex);
  const _exposure = safeNum(totalExposureUsd);
  const _regions = safeArr<string>(affectedRegions);
  const _nodes = safeNum(nodesImpacted);
  const _critical = safeNum(criticalCount);
  const _elevated = safeNum(elevatedCount);
  const _confidence = safeNum(confidence);
  const _avgStress = safeNum(averageStress);
  const _label = safeStr(scenarioLabel, "Unknown Scenario");
  const _domain = safeStr(domain, "UNKNOWN");
  const _horizon = safeNum(horizonHours);
  const _stages = safeArr<string>(pipelineStages);

  const classification = stressToClassification(_risk);
  const classColor = classificationColor(classification);
  const isAr = lang === "ar";

  return (
    <header className="w-full bg-[#0B0F1A] border-b border-white/[0.06]">
      {/* ── Row 1: Macro Overview — primary entry ── */}
      <div className="flex items-center justify-between px-6 py-3">
        {/* Left: Title + Affected Regions */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Globe size={18} className="text-blue-400" />
            <h1 className="text-base font-bold text-white tracking-tight">
              {isAr ? "نظرة عامة على اقتصاد الخليج" : "GCC Macro Overview"}
            </h1>
          </div>
          {_regions.length > 0 && (
            <div className="flex items-center gap-1.5 ml-2">
              {_regions.slice(0, 5).map((r) => (
                <RegionChip key={r} name={r} />
              ))}
              {_regions.length > 5 && (
                <span className="text-[10px] text-slate-500">
                  +{_regions.length - 5}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Right: Risk Index Gauge */}
        <div className="flex items-center gap-4 min-w-[300px]">
          <RiskGauge value={_risk} classification={classification} color={classColor} />
          <div className="flex items-center gap-2">
            <Shield size={14} className="text-slate-500" />
            <span className="text-xs text-slate-400">
              {isAr ? "الثقة" : "Conf."}
            </span>
            <span
              className="text-sm font-bold tabular-nums"
              style={{ color: _confidence >= 0.8 ? "#22C55E" : _confidence >= 0.6 ? "#EAB308" : "#EF4444" }}
            >
              {formatPct(_confidence)}
            </span>
          </div>
        </div>
      </div>

      {/* ── Row 2: Decision-Oriented KPIs ── */}
      <div className="flex items-center gap-2 px-6 pb-2 overflow-x-auto">
        <MacroKPI
          icon={<TrendingDown size={14} />}
          label={isAr ? "إجمالي الخسائر المعرضة" : "Total Loss at Risk"}
          value={formatUSD(_exposure)}
          accent="#EF4444"
        />
        <MacroKPI
          icon={<Activity size={14} />}
          label={isAr ? "متوسط الإجهاد" : "System Stress"}
          value={formatPct(_avgStress, 1)}
          accent={_avgStress >= 0.5 ? "#EF4444" : _avgStress >= 0.35 ? "#F59E0B" : "#22C55E"}
        />
        <MacroKPI
          icon={<AlertTriangle size={14} />}
          label={isAr ? "عقد حرجة" : "Critical"}
          value={`${_critical}`}
          accent={_critical > 0 ? "#EF4444" : "#64748B"}
        />
        <MacroKPI
          icon={<AlertTriangle size={14} />}
          label={isAr ? "عقد مرتفعة" : "Elevated"}
          value={`${_elevated}`}
          accent={_elevated > 0 ? "#F59E0B" : "#64748B"}
        />
        <MacroKPI
          icon={<Globe size={14} />}
          label={isAr ? "عقد متأثرة" : "Nodes Hit"}
          value={`${_nodes}`}
        />
        <MacroKPI
          icon={<Clock size={14} />}
          label={isAr ? "أفق الوقت" : "Horizon"}
          value={formatHours(_horizon)}
          accent="#3B82F6"
        />
      </div>

      {/* ── Row 3: Scenario context (secondary, subdued) ── */}
      <div className="flex items-center gap-3 px-6 pb-2.5 border-t border-white/[0.03] pt-2">
        <span className="text-[10px] text-slate-600 uppercase tracking-wider font-semibold">
          {isAr ? "السيناريو النشط" : "Active Scenario"}
        </span>
        <DomainTag domain={_domain} />
        <span className="text-xs text-slate-400 font-medium">{isAr && scenarioLabelAr ? scenarioLabelAr : _label}</span>
        <span className="text-[10px] text-slate-600">|</span>
        <Clock size={10} className="text-slate-600" />
        <span className="text-[10px] text-slate-500">
          {safeDate(triggerTime)} — {_horizon}h horizon — {_stages.length}/9 stages
        </span>
      </div>
    </header>
  );
}
