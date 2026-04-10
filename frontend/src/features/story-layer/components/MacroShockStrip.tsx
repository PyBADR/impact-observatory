"use client";

/**
 * MacroShockStrip — Top banner showing the current macro state
 *
 * Purpose: "Explain what changed in the world"
 * Shows: Oil impact, inflation pressure, interest rate stress,
 *        geopolitical tension, supply chain disruption
 *
 * Data source: RunResult fields (deterministic, not mock)
 * Design: Compact horizontal strip, boardroom-grade, dark theme
 */

import React from "react";
import {
  Fuel,
  TrendingUp,
  Landmark,
  Shield,
  Ship,
  AlertTriangle,
} from "lucide-react";
import type { RunResult, Language } from "@/types/observatory";

// ── Macro indicator derived from RunResult ──────────────────────────

interface MacroIndicator {
  id: string;
  label: string;
  labelAr: string;
  icon: React.ReactNode;
  value: string;
  severity: "low" | "moderate" | "elevated" | "critical";
  color: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  low: "#22C55E",
  moderate: "#EAB308",
  elevated: "#F59E0B",
  critical: "#EF4444",
};

function severityFromStress(stress: number): "low" | "moderate" | "elevated" | "critical" {
  if (stress >= 0.75) return "critical";
  if (stress >= 0.50) return "elevated";
  if (stress >= 0.30) return "moderate";
  return "low";
}

function deriveMacroIndicators(result: RunResult): MacroIndicator[] {
  const scenario = result.scenario;
  const headline = result.headline;
  const banking = result.banking;
  const insurance = result.insurance;
  const fintech = result.fintech;

  // Derive macro indicators from actual scenario data
  const avgStress = headline?.average_stress ?? 0;
  const scenarioId = scenario?.template_id ?? "";

  // Oil & Energy — derived from scenario type + severity + energy sector stress
  const isEnergyScenario = scenarioId.includes("oil") || scenarioId.includes("hormuz") || scenarioId.includes("energy") || scenarioId.includes("lng");
  const energyStress = isEnergyScenario ? Math.min(1, (scenario?.severity ?? 0) * 1.2) : avgStress * 0.6;
  const energySev = severityFromStress(energyStress);

  // Inflation Pressure — derived from total loss relative to GDP coverage ($2.1T)
  const totalLoss = headline?.total_loss_usd ?? 0;
  const inflationProxy = Math.min(1, totalLoss / 500_000_000); // $500M = max pressure
  const inflationSev = severityFromStress(inflationProxy);

  // Liquidity / Interest Rate Stress — from banking stress
  const liquidityStress = banking?.liquidity_stress ?? avgStress * 0.8;
  const liquiditySev = severityFromStress(liquidityStress);

  // Geopolitical Tension — from scenario type + overall severity
  const isGeopolitical = scenarioId.includes("hormuz") || scenarioId.includes("iran") || scenarioId.includes("red_sea");
  const geoStress = isGeopolitical ? Math.min(1, (scenario?.severity ?? 0) * 1.3) : avgStress * 0.5;
  const geoSev = severityFromStress(geoStress);

  // Supply Chain / Trade — from fintech cross-border + maritime scenarios
  const isMaritime = scenarioId.includes("port") || scenarioId.includes("red_sea") || scenarioId.includes("hormuz");
  const supplyStress = isMaritime
    ? Math.min(1, (scenario?.severity ?? 0) * 1.1)
    : (fintech?.cross_border_disruption ?? 0) * 0.8;
  const supplySev = severityFromStress(supplyStress);

  return [
    {
      id: "oil",
      label: "Oil & Energy",
      labelAr: "النفط والطاقة",
      icon: <Fuel size={13} />,
      value: `${Math.round(energyStress * 100)}%`,
      severity: energySev,
      color: SEVERITY_COLORS[energySev],
    },
    {
      id: "inflation",
      label: "Inflation Pressure",
      labelAr: "ضغط التضخم",
      icon: <TrendingUp size={13} />,
      value: `${Math.round(inflationProxy * 100)}%`,
      severity: inflationSev,
      color: SEVERITY_COLORS[inflationSev],
    },
    {
      id: "liquidity",
      label: "Liquidity Stress",
      labelAr: "ضغط السيولة",
      icon: <Landmark size={13} />,
      value: `${Math.round(liquidityStress * 100)}%`,
      severity: liquiditySev,
      color: SEVERITY_COLORS[liquiditySev],
    },
    {
      id: "geopolitical",
      label: "Geopolitical Risk",
      labelAr: "المخاطر الجيوسياسية",
      icon: <Shield size={13} />,
      value: `${Math.round(geoStress * 100)}%`,
      severity: geoSev,
      color: SEVERITY_COLORS[geoSev],
    },
    {
      id: "supply_chain",
      label: "Supply Chain",
      labelAr: "سلسلة الإمداد",
      icon: <Ship size={13} />,
      value: `${Math.round(supplyStress * 100)}%`,
      severity: supplySev,
      color: SEVERITY_COLORS[supplySev],
    },
  ];
}

// ── Single indicator chip ────────────────────────────────────────────

function IndicatorChip({
  indicator,
  isAr,
}: {
  indicator: MacroIndicator;
  isAr: boolean;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white/[0.03] border border-white/[0.06] min-w-[140px]">
      <div
        className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: `${indicator.color}15`, color: indicator.color }}
      >
        {indicator.icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[9px] text-slate-500 uppercase tracking-wider leading-tight truncate">
          {isAr ? indicator.labelAr : indicator.label}
        </p>
        <p
          className="text-sm font-bold tabular-nums leading-tight"
          style={{ color: indicator.color }}
        >
          {indicator.value}
        </p>
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface MacroShockStripProps {
  result: RunResult;
  lang?: Language;
}

export function MacroShockStrip({ result, lang = "en" }: MacroShockStripProps) {
  const isAr = lang === "ar";
  const indicators = deriveMacroIndicators(result);
  const scenarioLabel = isAr
    ? (result.scenario?.label_ar ?? result.scenario?.label ?? "—")
    : (result.scenario?.label ?? "—");

  // Overall severity badge
  const avgStress = result.headline?.average_stress ?? 0;
  const overallSev = severityFromStress(avgStress);
  const overallColor = SEVERITY_COLORS[overallSev];

  return (
    <div className="w-full bg-[#080C16] border-b border-white/[0.06]">
      {/* Section label + scenario context */}
      <div className="flex items-center justify-between px-6 pt-3 pb-1.5">
        <div className="flex items-center gap-2.5">
          <AlertTriangle size={14} style={{ color: overallColor }} />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            {isAr ? "الصدمة الاقتصادية الكلية" : "Macro Shock"}
          </span>
          <div className="h-3 w-px bg-white/[0.08]" />
          <span className="text-[11px] text-slate-500 font-medium truncate max-w-[300px]">
            {scenarioLabel}
          </span>
        </div>
        <div
          className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider"
          style={{
            backgroundColor: `${overallColor}15`,
            color: overallColor,
            border: `1px solid ${overallColor}30`,
          }}
        >
          {overallSev}
        </div>
      </div>

      {/* Indicator chips row */}
      <div className="flex items-center gap-2 px-6 pb-3 overflow-x-auto">
        {indicators.map((ind) => (
          <IndicatorChip key={ind.id} indicator={ind} isAr={isAr} />
        ))}
      </div>
    </div>
  );
}
