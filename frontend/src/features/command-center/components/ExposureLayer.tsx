"use client";

/**
 * ExposureLayer — Impact distribution by country and sector
 *
 * Two side-by-side panels:
 *   LEFT:  Country Exposure — GCC nations ranked by aggregate node stress
 *   RIGHT: Sector Exposure  — sectors ranked by aggregate loss/stress
 *
 * Country derivation: lat/lng bounding boxes for each GCC state.
 * Nodes that fall outside all boxes → "GCC-Wide" bucket.
 * Kuwait & Bahrain always appear as placeholders even when no nodes
 * fall within their boundaries.
 *
 * Sector derivation: aggregates from SafeImpact[] (banking, insurance,
 * fintech) and from KnowledgeGraphNode[] layers (infrastructure, economy,
 * finance, geography).
 *
 * All values pass through safe* coercion. Memoized derivation.
 */

import React, { useMemo } from "react";
import { MapPin, BarChart3 } from "lucide-react";
import { formatUSD, formatPct, stressToClassification, classificationColor, safeNum, safeArr } from "../lib/format";
import type { KnowledgeGraphNode } from "@/types/observatory";
import type { SafeImpact } from "@/lib/v2/api-types";

// ── GCC Country Bounding Boxes (lat/lng) ─────────────────────────────

interface CountryDef {
  id: string;
  label: string;
  labelAr: string;
  flag: string;
  latMin: number;
  latMax: number;
  lngMin: number;
  lngMax: number;
}

const GCC_COUNTRIES: CountryDef[] = [
  { id: "SA", label: "Saudi Arabia",  labelAr: "السعودية",  flag: "🇸🇦", latMin: 16.0, latMax: 32.2, lngMin: 34.5, lngMax: 55.7 },
  { id: "AE", label: "UAE",           labelAr: "الإمارات",  flag: "🇦🇪", latMin: 22.6, latMax: 26.1, lngMin: 51.6, lngMax: 56.4 },
  { id: "QA", label: "Qatar",         labelAr: "قطر",       flag: "🇶🇦", latMin: 24.5, latMax: 26.2, lngMin: 50.7, lngMax: 51.7 },
  { id: "KW", label: "Kuwait",        labelAr: "الكويت",    flag: "🇰🇼", latMin: 28.5, latMax: 30.1, lngMin: 46.5, lngMax: 48.5 },
  { id: "BH", label: "Bahrain",       labelAr: "البحرين",   flag: "🇧🇭", latMin: 25.8, latMax: 26.3, lngMin: 50.3, lngMax: 50.7 },
  { id: "OM", label: "Oman",          labelAr: "عمان",      flag: "🇴🇲", latMin: 16.6, latMax: 26.4, lngMin: 52.0, lngMax: 59.8 },
];

function classifyCountry(lat: number, lng: number): string {
  // Check smaller/overlapping countries first (Bahrain, Qatar) before Saudi
  const priority = ["BH", "QA", "KW", "AE", "OM", "SA"];
  for (const id of priority) {
    const c = GCC_COUNTRIES.find((g) => g.id === id)!;
    if (lat >= c.latMin && lat <= c.latMax && lng >= c.lngMin && lng <= c.lngMax) {
      return c.id;
    }
  }
  return "GCC";
}

// ── Derived types ────────────────────────────────────────────────────

interface CountryExposure {
  def: CountryDef | null;
  id: string;
  label: string;
  labelAr: string;
  flag: string;
  nodeCount: number;
  totalStress: number;
  avgStress: number;
  maxStress: number;
  totalLossUsd: number;
  classification: string;
  color: string;
}

interface SectorExposure {
  sector: string;
  label: string;
  labelAr: string;
  lossUsd: number;
  avgStress: number;
  maxStress: number;
  entityCount: number;
  classification: string;
  color: string;
}

// ── Sector label map ─────────────────────────────────────────────────

const SECTOR_LABELS: Record<string, { en: string; ar: string; color: string }> = {
  banking:        { en: "Banking",       ar: "المصارف",        color: "#14B8A6" },
  insurance:      { en: "Insurance",     ar: "التأمين",        color: "#6366F1" },
  fintech:        { en: "Fintech",       ar: "التقنية المالية", color: "#8B5CF6" },
  infrastructure: { en: "Infrastructure", ar: "البنية التحتية", color: "#EF4444" },
  economy:        { en: "Economy",       ar: "الاقتصاد",       color: "#F59E0B" },
  finance:        { en: "Finance",       ar: "المالية",        color: "#3B82F6" },
  geography:      { en: "Geography",     ar: "الجغرافيا",      color: "#8B5CF6" },
};

// ── Derivation functions ─────────────────────────────────────────────

function deriveCountryExposure(nodes: KnowledgeGraphNode[]): CountryExposure[] {
  const buckets = new Map<string, { stress: number[]; loss: number[] }>();

  // Ensure Kuwait + Bahrain always appear
  for (const c of GCC_COUNTRIES) {
    buckets.set(c.id, { stress: [], loss: [] });
  }

  for (const n of nodes) {
    const countryId = classifyCountry(safeNum(n.lat), safeNum(n.lng));
    const bucket = buckets.get(countryId) ?? { stress: [], loss: [] };
    bucket.stress.push(safeNum(n.stress));
    bucket.loss.push(safeNum(n.stress) * 600_000_000); // heuristic loss from stress
    buckets.set(countryId, bucket);
  }

  const results: CountryExposure[] = [];
  for (const [id, data] of buckets) {
    const def = GCC_COUNTRIES.find((c) => c.id === id) ?? null;
    const avg = data.stress.length > 0
      ? data.stress.reduce((a, b) => a + b, 0) / data.stress.length
      : 0;
    const max = data.stress.length > 0 ? Math.max(...data.stress) : 0;
    const totalLoss = data.loss.reduce((a, b) => a + b, 0);
    const classification = stressToClassification(avg);

    results.push({
      def,
      id,
      label: def?.label ?? "GCC-Wide",
      labelAr: def?.labelAr ?? "على مستوى الخليج",
      flag: def?.flag ?? "🌐",
      nodeCount: data.stress.length,
      totalStress: data.stress.reduce((a, b) => a + b, 0),
      avgStress: avg,
      maxStress: max,
      totalLossUsd: totalLoss,
      classification,
      color: classificationColor(classification),
    });
  }

  // Sort: countries with data first (desc by avgStress), then placeholders
  return results.sort((a, b) => {
    if (a.nodeCount === 0 && b.nodeCount > 0) return 1;
    if (a.nodeCount > 0 && b.nodeCount === 0) return -1;
    return b.avgStress - a.avgStress;
  });
}

function deriveSectorExposure(impacts: SafeImpact[], nodes: KnowledgeGraphNode[]): SectorExposure[] {
  const buckets = new Map<string, { loss: number[]; stress: number[] }>();

  // From SafeImpact[] — banking, insurance, fintech
  for (const imp of impacts) {
    const s = imp.sector;
    const bucket = buckets.get(s) ?? { loss: [], stress: [] };
    bucket.loss.push(safeNum(imp.lossUsd));
    bucket.stress.push(safeNum(imp.stressLevel));
    buckets.set(s, bucket);
  }

  // From graph nodes — layers that don't overlap with SafeImpact sectors
  for (const n of nodes) {
    const layer = n.layer;
    if (["banking", "insurance", "fintech"].includes(layer)) continue; // already from SafeImpact
    const bucket = buckets.get(layer) ?? { loss: [], stress: [] };
    bucket.stress.push(safeNum(n.stress));
    bucket.loss.push(safeNum(n.stress) * 600_000_000);
    buckets.set(layer, bucket);
  }

  const results: SectorExposure[] = [];
  for (const [sector, data] of buckets) {
    const meta = SECTOR_LABELS[sector] ?? { en: sector, ar: sector, color: "#64748B" };
    const avg = data.stress.length > 0
      ? data.stress.reduce((a, b) => a + b, 0) / data.stress.length
      : 0;
    const max = data.stress.length > 0 ? Math.max(...data.stress) : 0;
    const totalLoss = data.loss.reduce((a, b) => a + b, 0);
    const classification = stressToClassification(avg);

    results.push({
      sector,
      label: meta.en,
      labelAr: meta.ar,
      lossUsd: totalLoss,
      avgStress: avg,
      maxStress: max,
      entityCount: data.stress.length,
      classification,
      color: meta.color,
    });
  }

  return results.sort((a, b) => b.avgStress - a.avgStress);
}

// ── Country Row ──────────────────────────────────────────────────────

function CountryRow({ country, isAr, onClick }: { country: CountryExposure; isAr: boolean; onClick?: (countryId: string) => void }) {
  const pct = Math.min(100, Math.max(0, Math.round(country.avgStress * 100)));
  const isEmpty = country.nodeCount === 0;

  return (
    <div
      className={`flex items-center gap-3 py-1.5 ${isEmpty ? "opacity-40" : "cursor-pointer hover:bg-white/[0.03] rounded"}`}
      onClick={!isEmpty && onClick ? () => onClick(country.id) : undefined}
      role={!isEmpty && onClick ? "button" : undefined}
      tabIndex={!isEmpty && onClick ? 0 : undefined}
    >
      {/* Flag + Name */}
      <div className="flex items-center gap-2 min-w-[120px]">
        <span className="text-sm">{country.flag}</span>
        <span className="text-[11px] text-slate-300 font-medium">
          {isAr ? country.labelAr : country.label}
        </span>
      </div>

      {/* Stress bar */}
      <div className="flex-1 min-w-[80px]">
        <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, backgroundColor: country.color }}
          />
        </div>
      </div>

      {/* Stress % */}
      <span
        className="text-[11px] font-bold tabular-nums w-[40px] text-right"
        style={{ color: isEmpty ? "#475569" : country.color }}
      >
        {isEmpty ? "—" : formatPct(country.avgStress)}
      </span>

      {/* Cost */}
      <span className="text-[10px] text-slate-500 w-[60px] text-right tabular-nums">
        {isEmpty ? "—" : formatUSD(country.totalLossUsd)}
      </span>

      {/* Node count */}
      <span className="text-[9px] text-slate-600 w-[30px] text-right">
        {isEmpty ? "—" : `${country.nodeCount}n`}
      </span>
    </div>
  );
}

// ── Sector Row ───────────────────────────────────────────────────────

function SectorRow({ sector, isAr, onClick }: { sector: SectorExposure; isAr: boolean; onClick?: (sectorId: string) => void }) {
  const pct = Math.min(100, Math.max(0, Math.round(sector.avgStress * 100)));

  return (
    <div
      className="flex items-center gap-3 py-1.5 cursor-pointer hover:bg-white/[0.03] rounded"
      onClick={onClick ? () => onClick(sector.sector) : undefined}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {/* Color dot + Name */}
      <div className="flex items-center gap-2 min-w-[120px]">
        <div
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: sector.color }}
        />
        <span className="text-[11px] text-slate-300 font-medium">
          {isAr ? sector.labelAr : sector.label}
        </span>
      </div>

      {/* Stress bar */}
      <div className="flex-1 min-w-[80px]">
        <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, backgroundColor: sector.color }}
          />
        </div>
      </div>

      {/* Stress % */}
      <span
        className="text-[11px] font-bold tabular-nums w-[40px] text-right"
        style={{ color: sector.color }}
      >
        {formatPct(sector.avgStress)}
      </span>

      {/* Loss */}
      <span className="text-[10px] text-slate-500 w-[60px] text-right tabular-nums">
        {formatUSD(sector.lossUsd)}
      </span>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

interface ExposureLayerProps {
  nodes: KnowledgeGraphNode[];
  impacts: SafeImpact[];
  lang?: "en" | "ar";
  onCountrySelect?: (countryId: string) => void;
  onSectorSelect?: (sectorId: string) => void;
}

export function ExposureLayer({ nodes, impacts, lang, onCountrySelect, onSectorSelect }: ExposureLayerProps) {
  const _nodes = safeArr<KnowledgeGraphNode>(nodes);
  const _impacts = safeArr<SafeImpact>(impacts);
  const isAr = lang === "ar";

  const countries = useMemo(() => deriveCountryExposure(_nodes), [_nodes]);
  const sectors = useMemo(() => deriveSectorExposure(_impacts, _nodes), [_impacts, _nodes]);

  // Don't render if there are no nodes and no impacts
  if (_nodes.length === 0 && _impacts.length === 0) return null;

  return (
    <div className="w-full bg-[#0A0E18] border-b border-white/[0.04] px-6 py-3">
      {/* Section label */}
      <div className="flex items-center gap-2 mb-2.5">
        <div className="w-1 h-3 rounded-full bg-emerald-500" />
        <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
          {isAr ? "توزيع التعرض" : "Exposure Distribution"}
        </span>
        <div className="flex-1 h-px bg-white/[0.04]" />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-2 gap-6">
        {/* LEFT: Country Exposure */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <MapPin size={11} className="text-slate-500" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
              {isAr ? "حسب الدولة" : "By Country"}
            </span>
          </div>
          <div>
            {countries.map((c) => (
              <CountryRow key={c.id} country={c} isAr={isAr} onClick={onCountrySelect} />
            ))}
          </div>
        </div>

        {/* RIGHT: Sector Exposure */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <BarChart3 size={11} className="text-slate-500" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
              {isAr ? "حسب القطاع" : "By Sector"}
            </span>
          </div>
          <div>
            {sectors.map((s) => (
              <SectorRow key={s.sector} sector={s} isAr={isAr} onClick={onSectorSelect} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
