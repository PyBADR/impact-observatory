"use client";

/**
 * SectorImpactStory — Which sectors absorb the shock
 *
 * Purpose: "Explain which sectors are hit and how hard"
 * Shows: Banking, Insurance, Fintech stress with narrative context
 *
 * Data source: RunResult.banking, .insurance, .fintech (real data)
 * Design: Horizontal sector cards with stress gauge + one-line story
 */

import React from "react";
import {
  Landmark,
  Shield,
  Cpu,
  AlertTriangle,
  TrendingDown,
  Clock,
} from "lucide-react";
import type { RunResult, Language, Classification } from "@/types/observatory";

// ── Sector data extraction ──────────────────────────────────────────

interface SectorStory {
  id: string;
  label: string;
  labelAr: string;
  icon: React.ReactNode;
  stressIndex: number;
  classification: string;
  totalExposure: number;
  timeToFailure: number;
  storyEn: string;
  storyAr: string;
  color: string;
  accentBg: string;
}

function classColor(c: string): string {
  switch (c) {
    case "CRITICAL": return "#EF4444";
    case "ELEVATED": return "#F59E0B";
    case "MODERATE": return "#EAB308";
    case "LOW": return "#22C55E";
    default: return "#64748B";
  }
}

function formatUSD(value: number): string {
  if (!isFinite(value) || isNaN(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e9) return `$${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(abs / 1e6).toFixed(0)}M`;
  if (abs >= 1e3) return `$${(abs / 1e3).toFixed(0)}K`;
  return `$${Math.round(abs)}`;
}

function deriveSectors(result: RunResult): SectorStory[] {
  const sectors: SectorStory[] = [];
  const banking = result.banking;
  const insurance = result.insurance;
  const fintech = result.fintech;

  if (banking) {
    const stress = banking.aggregate_stress ?? 0;
    const cls = banking.classification ?? "NOMINAL";
    sectors.push({
      id: "banking",
      label: "Banking",
      labelAr: "القطاع البنكي",
      icon: <Landmark size={16} />,
      stressIndex: stress,
      classification: cls,
      totalExposure: banking.total_exposure_usd ?? 0,
      timeToFailure: banking.time_to_liquidity_breach_hours ?? 0,
      storyEn: stress >= 0.6
        ? `Liquidity stress at ${Math.round(banking.liquidity_stress * 100)}%. Interbank contagion risk: ${Math.round(banking.interbank_contagion * 100)}%. Capital adequacy impact: ${(banking.capital_adequacy_impact_pct ?? 0).toFixed(1)}%.`
        : `Banking sector absorbing shock. Liquidity stress at ${Math.round((banking.liquidity_stress ?? 0) * 100)}%. Interbank channels stable.`,
      storyAr: stress >= 0.6
        ? `ضغط السيولة عند ${Math.round(banking.liquidity_stress * 100)}%. خطر العدوى المصرفية: ${Math.round(banking.interbank_contagion * 100)}%.`
        : `القطاع البنكي يمتص الصدمة. ضغط السيولة عند ${Math.round((banking.liquidity_stress ?? 0) * 100)}%.`,
      color: classColor(cls),
      accentBg: "bg-blue-500/10",
    });
  }

  if (insurance) {
    const stress = insurance.aggregate_stress ?? 0;
    const cls = insurance.classification ?? "NOMINAL";
    sectors.push({
      id: "insurance",
      label: "Insurance",
      labelAr: "التأمين",
      icon: <Shield size={16} />,
      stressIndex: stress,
      classification: cls,
      totalExposure: insurance.portfolio_exposure_usd ?? 0,
      timeToFailure: insurance.time_to_insolvency_hours ?? 0,
      storyEn: stress >= 0.6
        ? `Claims surge multiplier: ${(insurance.claims_surge_multiplier ?? 0).toFixed(1)}x. Combined ratio breached at ${Math.round((insurance.combined_ratio ?? 0) * 100)}%. ${insurance.reinsurance_trigger ? "Reinsurance triggered." : ""}`
        : `Insurance sector under pressure. Claims multiplier at ${(insurance.claims_surge_multiplier ?? 0).toFixed(1)}x. Combined ratio: ${Math.round((insurance.combined_ratio ?? 0) * 100)}%.`,
      storyAr: stress >= 0.6
        ? `مضاعف المطالبات: ${(insurance.claims_surge_multiplier ?? 0).toFixed(1)}x. النسبة المجمعة: ${Math.round((insurance.combined_ratio ?? 0) * 100)}%.`
        : `قطاع التأمين تحت الضغط. مضاعف المطالبات: ${(insurance.claims_surge_multiplier ?? 0).toFixed(1)}x.`,
      color: classColor(cls),
      accentBg: "bg-amber-500/10",
    });
  }

  if (fintech) {
    const stress = fintech.aggregate_stress ?? 0;
    const cls = fintech.classification ?? "NOMINAL";
    sectors.push({
      id: "fintech",
      label: "Fintech & Payments",
      labelAr: "الفنتك والمدفوعات",
      icon: <Cpu size={16} />,
      stressIndex: stress,
      classification: cls,
      totalExposure: 0, // fintech doesn't have a single exposure number
      timeToFailure: fintech.time_to_payment_failure_hours ?? 0,
      storyEn: stress >= 0.6
        ? `Payment volume down ${Math.round((fintech.payment_volume_impact_pct ?? 0) * 100)}%. Settlement delays: ${(fintech.settlement_delay_hours ?? 0).toFixed(0)}h. Cross-border disruption: ${Math.round((fintech.cross_border_disruption ?? 0) * 100)}%.`
        : `Fintech infrastructure absorbing impact. API availability at ${Math.round((fintech.api_availability_pct ?? 1) * 100)}%. Settlement stable.`,
      storyAr: stress >= 0.6
        ? `انخفاض حجم المدفوعات ${Math.round((fintech.payment_volume_impact_pct ?? 0) * 100)}%. تأخر التسوية: ${(fintech.settlement_delay_hours ?? 0).toFixed(0)} ساعة.`
        : `البنية التحتية المالية تمتص الأثر. توفر الواجهات: ${Math.round((fintech.api_availability_pct ?? 1) * 100)}%.`,
      color: classColor(cls),
      accentBg: "bg-violet-500/10",
    });
  }

  // Sort by stress descending — worst hit first
  return sectors.sort((a, b) => b.stressIndex - a.stressIndex);
}

// ── Sector Card ─────────────────────────────────────────────────────

function SectorStoryCard({
  sector,
  isAr,
}: {
  sector: SectorStory;
  isAr: boolean;
}) {
  const stressPct = Math.round(sector.stressIndex * 100);

  return (
    <div
      className="flex-1 min-w-[260px] rounded-lg border bg-[#0D1117] overflow-hidden"
      style={{ borderColor: `${sector.color}25`, borderTopWidth: "2px", borderTopColor: sector.color }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded flex items-center justify-center"
            style={{ backgroundColor: `${sector.color}15`, color: sector.color }}
          >
            {sector.icon}
          </div>
          <div>
            <p className="text-[12px] font-semibold text-slate-200">
              {isAr ? sector.labelAr : sector.label}
            </p>
            <p className="text-[10px] text-slate-600 uppercase tracking-wider font-medium">
              {isAr ? "ضغط القطاع" : "Sector Pressure"}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold tabular-nums" style={{ color: sector.color }}>
            {stressPct}
          </p>
          <p className="text-[9px] text-slate-600">/100</p>
        </div>
      </div>

      {/* Stress bar */}
      <div className="px-4 pb-1">
        <div className="w-full h-1 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${stressPct}%`, backgroundColor: sector.color }}
          />
        </div>
      </div>

      {/* Narrative story */}
      <div className="px-4 py-2.5 border-t border-white/[0.04] mt-1">
        <p className="text-[11px] text-slate-400 leading-relaxed">
          {isAr ? sector.storyAr : sector.storyEn}
        </p>
      </div>

      {/* Bottom metrics */}
      <div className="flex items-center gap-3 px-4 pb-3">
        {sector.totalExposure > 0 && (
          <div className="flex items-center gap-1">
            <TrendingDown size={10} className="text-slate-600" />
            <span className="text-[10px] text-slate-500 tabular-nums">
              {formatUSD(sector.totalExposure)}
            </span>
          </div>
        )}
        {sector.timeToFailure > 0 && (
          <div className="flex items-center gap-1">
            <Clock size={10} className="text-slate-600" />
            <span className="text-[10px] text-slate-500 tabular-nums">
              {Math.round(sector.timeToFailure)}h
            </span>
          </div>
        )}
        <div
          className="ml-auto px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider"
          style={{
            backgroundColor: `${sector.color}15`,
            color: sector.color,
          }}
        >
          {sector.classification}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface SectorImpactStoryProps {
  result: RunResult;
  lang?: Language;
}

export function SectorImpactStory({ result, lang = "en" }: SectorImpactStoryProps) {
  const isAr = lang === "ar";
  const sectors = deriveSectors(result);

  if (sectors.length === 0) return null;

  return (
    <div className="w-full bg-[#080C14] border-b border-white/[0.05]">
      {/* Section header */}
      <div className="flex items-center gap-2 px-6 pt-3 pb-1.5">
        <AlertTriangle size={13} className="text-amber-400" />
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          {isAr ? "ضغط القطاعات" : "Sector Pressure"}
        </span>
        <div className="flex-1 h-px bg-white/[0.04]" />
        <span className="text-[10px] text-slate-600">
          {sectors.length} {isAr ? "قطاعات متأثرة" : "sectors impacted"}
        </span>
      </div>

      {/* Subtitle */}
      <p className="px-6 pb-2.5 text-[11px] text-slate-500">
        {isAr
          ? "القطاعات التي تمتص الصدمة — مرتبة حسب شدة الضغط"
          : "Sectors absorbing the shock — ranked by stress severity"}
      </p>

      {/* Sector cards */}
      <div className="flex items-stretch gap-3 px-6 pb-4 overflow-x-auto">
        {sectors.map((sector) => (
          <SectorStoryCard key={sector.id} sector={sector} isAr={isAr} />
        ))}
      </div>
    </div>
  );
}
