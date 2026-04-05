"use client";

/**
 * Impact Observatory | مرصد الأثر — Impact Map
 *
 * Full-page map visualization showing GCC entities with scenario impact overlay.
 * Uses GCC node registry (42 nodes) + simulation results to render:
 *   - Entity pins with risk classification colors
 *   - Propagation arcs between impacted entities
 *   - Financial loss labels
 *   - Sector stress indicators
 *   - Available data status panel
 *
 * Bilingual (English + Arabic). Light boardroom theme.
 */

import { useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { useAppStore } from "@/store/app-store";
import { useGccNodes, useRunHistory } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { safeNum } from "@/lib/format";
import type {
  RunResult,
  GccNode,
  EntityImpact,
  BottleneckNode,
} from "@/types/observatory";

// ── Risk classification colors ──────────────────────────────────────
const CLASS_COLOR: Record<string, string> = {
  CRITICAL: "#B91C1C",
  SEVERE: "#C2410C",
  HIGH: "#B45309",
  ELEVATED: "#D97706",
  MODERATE: "#15803D",
  LOW: "#22C55E",
  NOMINAL: "#6B7280",
  GUARDED: "#CA8A04",
};

function formatLoss(usd: number): string {
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(1)}B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)}M`;
  if (usd >= 1e3) return `$${(usd / 1e3).toFixed(0)}K`;
  return `$${Math.round(usd).toLocaleString()}`;
}

// ── SVG Map Constants ───────────────────────────────────────────────
const MAP_W = 900;
const MAP_H = 500;
const MIN_LAT = 12;
const MAX_LAT = 34;
const MIN_LNG = 34;
const MAX_LNG = 64;

function toSVG(lat: number, lng: number): [number, number] {
  const x = ((lng - MIN_LNG) / (MAX_LNG - MIN_LNG)) * MAP_W;
  const y = MAP_H - ((lat - MIN_LAT) / (MAX_LAT - MIN_LAT)) * MAP_H;
  return [x, y];
}

// ── Scenario list ───────────────────────────────────────────────────
const SCENARIOS = [
  { id: "hormuz_chokepoint_disruption", label: "Hormuz Chokepoint", label_ar: "مضيق هرمز" },
  { id: "red_sea_trade_corridor_instability", label: "Red Sea Instability", label_ar: "البحر الأحمر" },
  { id: "gcc_cyber_attack", label: "GCC Cyber Attack", label_ar: "هجوم سيبراني" },
  { id: "energy_market_volatility_shock", label: "Energy Volatility", label_ar: "تقلبات الطاقة" },
  { id: "regional_liquidity_stress_event", label: "Liquidity Stress", label_ar: "أزمة سيولة" },
  { id: "critical_port_throughput_disruption", label: "Port Disruption", label_ar: "تعطل الموانئ" },
  { id: "financial_infrastructure_cyber_disruption", label: "Financial Cyber", label_ar: "سيبراني مالي" },
  { id: "saudi_oil_shock", label: "Saudi Oil Shock", label_ar: "صدمة نفط سعودية" },
  { id: "uae_banking_crisis", label: "UAE Banking Crisis", label_ar: "أزمة بنوك الإمارات" },
  { id: "qatar_lng_disruption", label: "Qatar LNG", label_ar: "غاز قطر" },
  { id: "bahrain_sovereign_stress", label: "Bahrain Sovereign", label_ar: "سيادة البحرين" },
  { id: "kuwait_fiscal_shock", label: "Kuwait Fiscal", label_ar: "مالية الكويت" },
  { id: "oman_port_closure", label: "Oman Port Closure", label_ar: "إغلاق ميناء عُمان" },
  { id: "iran_regional_escalation", label: "Iran Escalation", label_ar: "تصعيد إيران" },
];

// ── Data availability item ──────────────────────────────────────────
interface DataItem {
  label: string;
  label_ar: string;
  available: boolean;
  check: (r: RunResult | null, nodes: GccNode[]) => boolean;
}

const DATA_ITEMS: DataItem[] = [
  {
    label: "Financial impact analysis",
    label_ar: "تحليل الأثر المالي",
    available: false,
    check: (r) => !!(r && r.financial_impact && r.financial_impact.total_loss_usd > 0),
  },
  {
    label: "Sector stress indicators",
    label_ar: "مؤشرات إجهاد القطاعات",
    available: false,
    check: (r) => !!(r && r.banking_stress && r.insurance_stress),
  },
  {
    label: "Decision action recommendations",
    label_ar: "توصيات إجراءات القرار",
    available: false,
    check: (r) => !!(r && r.decision_plan && r.decision_plan.actions?.length > 0),
  },
  {
    label: "Business & regulatory timelines",
    label_ar: "الجداول الزمنية التنظيمية",
    available: false,
    check: (r) => !!(r && (r.recovery_trajectory?.length > 0 || r.headline)),
  },
  {
    label: "Geographic entity map",
    label_ar: "خريطة الكيانات الجغرافية",
    available: false,
    check: (r, nodes) => !!(r && nodes.length > 0 && r.financial?.length > 0),
  },
];

// ── Main Component ──────────────────────────────────────────────────
export default function MapPage() {
  const { language } = useAppStore();
  const isAr = language === "ar";

  const [selectedScenario, setSelectedScenario] = useState("");
  const [severity, setSeverity] = useState(0.7);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredEntity, setHoveredEntity] = useState<string | null>(null);

  // Fetch GCC nodes (static, staleTime=Infinity)
  const { data: nodesData } = useGccNodes();
  const gccNodes = nodesData?.nodes ?? [];

  // Build node lookup
  const nodeMap = useMemo(() => {
    const m: Record<string, GccNode> = {};
    for (const n of gccNodes) m[n.id] = n;
    return m;
  }, [gccNodes]);

  // Run scenario
  const handleRun = useCallback(async () => {
    if (!selectedScenario) return;
    setIsRunning(true);
    setError(null);
    try {
      const result = await api.observatory.run({
        scenario_id: selectedScenario,
        severity,
        horizon_hours: 336,
      });
      setRunResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setIsRunning(false);
    }
  }, [selectedScenario, severity]);

  // Map entities from run result to SVG-renderable pins
  const mapEntities = useMemo(() => {
    if (!runResult) return [];
    const entities = runResult.financial ?? runResult.financial_impact?.top_entities ?? [];
    return entities
      .filter((e: EntityImpact) => nodeMap[e.entity_id])
      .map((e: EntityImpact) => ({
        ...e,
        lat: nodeMap[e.entity_id].lat,
        lng: nodeMap[e.entity_id].lng,
        node: nodeMap[e.entity_id],
      }))
      .sort((a, b) => b.loss_usd - a.loss_usd);
  }, [runResult, nodeMap]);

  // Build propagation arcs
  const arcs = useMemo(() => {
    if (!runResult?.propagation_chain) return [];
    const result: Array<{
      from: { lat: number; lng: number };
      to: { lat: number; lng: number };
      impact: number;
    }> = [];
    const chain = runResult.propagation_chain as Array<Record<string, unknown>>;
    const seen = new Set<string>();
    for (const step of chain) {
      const path = (step.path as string[]) ?? [];
      if (path.length >= 2) {
        const fromId = path[path.length - 2];
        const toId = path[path.length - 1];
        const key = `${fromId}-${toId}`;
        if (!seen.has(key) && nodeMap[fromId] && nodeMap[toId]) {
          seen.add(key);
          result.push({
            from: { lat: nodeMap[fromId].lat, lng: nodeMap[fromId].lng },
            to: { lat: nodeMap[toId].lat, lng: nodeMap[toId].lng },
            impact: safeNum(step.impact as number),
          });
        }
      }
    }
    return result.slice(0, 40);
  }, [runResult, nodeMap]);

  // Data availability status
  const dataStatus = useMemo(
    () => DATA_ITEMS.map((d) => ({ ...d, available: d.check(runResult, gccNodes) })),
    [runResult, gccNodes]
  );

  const hasMapData = mapEntities.length > 0;
  const totalLoss = runResult?.headline?.total_loss_usd ?? 0;

  return (
    <div className="flex flex-col h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-6 py-3 bg-io-surface border-b border-io-border shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 flex items-center justify-center bg-io-accent text-white text-xs font-bold rounded">
              IO
            </span>
            <span className="text-base font-bold text-io-primary">
              {isAr ? "مرصد الأثر" : "Impact Observatory"}
            </span>
            <span className="text-[10px] text-io-secondary bg-io-bg px-1.5 py-0.5 rounded border border-io-border">
              v4.0
            </span>
          </div>
        </div>
        <nav className="flex items-center gap-1 text-xs">
          <Link href="/dashboard" className="px-3 py-1.5 text-io-secondary hover:text-io-primary transition rounded">
            {isAr ? "لوحة المعلومات" : "Dashboard"}
          </Link>
          <Link href="/graph-explorer" className="px-3 py-1.5 text-io-secondary hover:text-io-primary transition rounded">
            {isAr ? "الانتشار" : "Propagation"}
          </Link>
          <span className="px-3 py-1.5 bg-io-accent text-white rounded font-medium">
            {isAr ? "خريطة الأثر" : "Impact Map"}
          </span>
          <Link href="/scenario-lab" className="px-3 py-1.5 text-io-secondary hover:text-io-primary transition rounded">
            {isAr ? "المعمل" : "Lab"}
          </Link>
        </nav>
      </header>

      {/* ── Main ───────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ── Left Panel: Parameters ──────────────────────────── */}
        <aside className="w-60 min-w-[240px] bg-io-surface border-r border-io-border p-4 overflow-y-auto shrink-0">
          <h2 className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-3">
            {isAr ? "معاملات السيناريو" : "Scenario Parameters"}
          </h2>

          {/* Scenario selector */}
          <label className="block text-xs text-io-secondary mb-1">
            {isAr ? "السيناريو" : "Scenario"}
          </label>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="w-full mb-4 px-2 py-1.5 text-xs bg-io-bg border border-io-border rounded text-io-primary focus:outline-none focus:border-io-accent"
          >
            <option value="">
              {isAr ? "اختر سيناريو..." : "Select a scenario..."}
            </option>
            {SCENARIOS.map((s) => (
              <option key={s.id} value={s.id}>
                {isAr ? s.label_ar : s.label}
              </option>
            ))}
          </select>

          {/* Severity slider */}
          <label className="flex items-center justify-between text-xs text-io-secondary mb-1">
            <span>{isAr ? "شدة الصدمة" : "Shock Severity"}</span>
            <span className="font-mono font-bold text-io-primary">
              {Math.round(severity * 100)}%
            </span>
          </label>
          <input
            type="range"
            min={0.1}
            max={1}
            step={0.05}
            value={severity}
            onChange={(e) => setSeverity(parseFloat(e.target.value))}
            className="w-full mb-1 accent-io-accent"
          />
          <div className="flex justify-between text-[10px] text-io-secondary mb-4">
            <span>{isAr ? "منخفض 10%" : "Low 10%"}</span>
            <span>{isAr ? "عالي 100%" : "High 100%"}</span>
          </div>

          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={!selectedScenario || isRunning}
            className="w-full py-2 text-sm font-medium bg-io-accent text-white rounded hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed mb-4"
          >
            {isRunning
              ? isAr
                ? "جاري التحليل..."
                : "Running Analysis..."
              : isAr
              ? "تشغيل التحليل"
              : "Run Analysis"}
          </button>

          {error && (
            <div className="mb-4 p-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded">
              {error}
            </div>
          )}

          {/* Geospatial data status */}
          {!hasMapData && runResult && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded">
              <h3 className="text-xs font-bold text-amber-700 mb-1">
                {isAr
                  ? "بيانات جغرافية غير متوفرة"
                  : "Geospatial Data Unavailable"}
              </h3>
              <p className="text-[10px] text-amber-600">
                {isAr
                  ? "لم يتم تحميل بيانات الكيانات. التحليل متوفر من لوحة المعلومات."
                  : "Entity data could not be loaded. Scenario analysis remains accessible from the dashboard."}
              </p>
            </div>
          )}
        </aside>

        {/* ── Center: Map ─────────────────────────────────────── */}
        <main className="flex-1 flex flex-col bg-io-bg relative">
          {!hasMapData ? (
            /* Empty / unavailable state */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-md">
                {!runResult ? (
                  <>
                    <div className="text-5xl mb-4 opacity-60">🌍</div>
                    <h2 className="text-lg font-semibold text-io-primary mb-2">
                      {isAr ? "خريطة الأثر الجغرافي" : "Geographic Impact Map"}
                    </h2>
                    <p className="text-sm text-io-secondary mb-4">
                      {isAr
                        ? "اختر سيناريو وشغّل التحليل لعرض الأثر الجغرافي"
                        : "Select a scenario and run analysis to visualize geographic impact"}
                    </p>
                  </>
                ) : (
                  <>
                    <div className="text-5xl mb-4 opacity-40">🗺️</div>
                    <h2 className="text-lg font-semibold text-io-primary mb-2">
                      {isAr ? "الخريطة التشغيلية غير متوفرة" : "Operational Map Unavailable"}
                    </h2>
                    <p className="text-sm text-io-secondary mb-4">
                      {isAr
                        ? "البيانات الجغرافية غير متوفرة حالياً. التحليل يبقى متاحاً."
                        : "Live geospatial data is currently unavailable. Scenario analysis remains accessible."}
                    </p>
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={handleRun}
                        className="px-4 py-2 text-xs border border-io-border rounded text-io-secondary hover:text-io-primary transition"
                      >
                        {isAr ? "إعادة المحاولة" : "Retry"}
                      </button>
                      <Link
                        href="/dashboard"
                        className="px-4 py-2 text-xs bg-io-accent text-white rounded hover:bg-blue-700 transition"
                      >
                        {isAr ? "الذهاب للوحة المعلومات" : "Go to Dashboard"}
                      </Link>
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            /* Active map view */
            <div className="flex-1 relative">
              {/* Map header bar */}
              <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2 bg-io-surface/90 backdrop-blur border-b border-io-border">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-io-primary">
                    {isAr ? "خريطة أثر دول الخليج" : "GCC Impact Map"}
                  </span>
                  <span className="text-xs text-io-secondary">
                    {mapEntities.length} {isAr ? "كيان متأثر" : "entities"}
                  </span>
                  <span className="text-xs font-bold text-red-600">
                    {formatLoss(totalLoss)} {isAr ? "خسارة" : "total loss"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {["CRITICAL", "SEVERE", "HIGH", "MODERATE", "LOW"].map((cls) => (
                    <div key={cls} className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CLASS_COLOR[cls] }} />
                      <span className="text-[9px] text-io-secondary">{cls}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* SVG Map */}
              <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} className="w-full h-full" style={{ background: "#F8FAFC" }}>
                {/* Grid */}
                {[38, 42, 46, 50, 54, 58, 62].map((lng) => {
                  const [x] = toSVG(22, lng);
                  return <line key={`lng${lng}`} x1={x} y1={0} x2={x} y2={MAP_H} stroke="#E2E8F0" strokeWidth={0.5} />;
                })}
                {[16, 20, 24, 28, 32].map((lat) => {
                  const [, y] = toSVG(lat, 50);
                  return <line key={`lat${lat}`} x1={0} y1={y} x2={MAP_W} y2={y} stroke="#E2E8F0" strokeWidth={0.5} />;
                })}

                {/* Background nodes (all GCC nodes, dimmed) */}
                {gccNodes
                  .filter((n) => !mapEntities.find((e) => e.entity_id === n.id))
                  .map((n) => {
                    const [x, y] = toSVG(n.lat, n.lng);
                    return (
                      <g key={`bg-${n.id}`}>
                        <circle cx={x} cy={y} r={3} fill="#CBD5E1" fillOpacity={0.5} stroke="#94A3B8" strokeWidth={0.5} />
                        <text x={x} y={y - 6} fill="#94A3B8" fontSize={7} textAnchor="middle" fontFamily="system-ui">
                          {n.label.length > 14 ? n.label.slice(0, 14) + "…" : n.label}
                        </text>
                      </g>
                    );
                  })}

                {/* Propagation arcs */}
                {arcs.map((arc, i) => {
                  const [x1, y1] = toSVG(arc.from.lat, arc.from.lng);
                  const [x2, y2] = toSVG(arc.to.lat, arc.to.lng);
                  return (
                    <line
                      key={`arc-${i}`}
                      x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke="#EF4444" strokeWidth={Math.max(0.5, arc.impact * 2)}
                      strokeOpacity={Math.max(0.2, arc.impact * 0.6)}
                    />
                  );
                })}

                {/* Impact entity pins */}
                {mapEntities.map((e) => {
                  const [x, y] = toSVG(e.lat, e.lng);
                  const color = CLASS_COLOR[e.classification] ?? "#6B7280";
                  const r = Math.max(5, Math.min(16, totalLoss > 0 ? (e.loss_usd / totalLoss) * 60 + 5 : 5));
                  const isHovered = hoveredEntity === e.entity_id;
                  return (
                    <g
                      key={e.entity_id}
                      onMouseEnter={() => setHoveredEntity(e.entity_id)}
                      onMouseLeave={() => setHoveredEntity(null)}
                      style={{ cursor: "pointer" }}
                    >
                      {e.classification === "CRITICAL" && (
                        <circle cx={x} cy={y} r={r + 8} fill="none" stroke={color} strokeWidth={1.5} opacity={0.3}>
                          <animate attributeName="r" values={`${r + 4};${r + 10};${r + 4}`} dur="2s" repeatCount="indefinite" />
                          <animate attributeName="opacity" values="0.3;0.1;0.3" dur="2s" repeatCount="indefinite" />
                        </circle>
                      )}
                      <circle cx={x} cy={y} r={isHovered ? r + 2 : r} fill={color} fillOpacity={0.85} stroke="white" strokeWidth={1.5} />
                      <text x={x} y={y - r - 5} fill="#1E293B" fontSize={9} textAnchor="middle" fontWeight="500" fontFamily="system-ui">
                        {isAr ? (e.node?.label_ar ?? e.entity_label) : e.entity_label}
                      </text>
                      <text x={x} y={y + r + 12} fill={color} fontSize={8} textAnchor="middle" fontWeight="bold" fontFamily="monospace">
                        {formatLoss(e.loss_usd)}
                      </text>
                      {isHovered && (
                        <text x={x} y={y + r + 22} fill="#64748B" fontSize={7} textAnchor="middle" fontFamily="system-ui">
                          {e.sector} · stress {(e.stress_score * 100).toFixed(0)}%
                        </text>
                      )}
                    </g>
                  );
                })}

                {/* Water body labels */}
                {[
                  { label: isAr ? "الخليج العربي" : "Persian Gulf", lat: 26.5, lng: 52 },
                  { label: isAr ? "البحر الأحمر" : "Red Sea", lat: 20, lng: 39 },
                  { label: isAr ? "بحر العرب" : "Arabian Sea", lat: 16, lng: 58 },
                ].map(({ label, lat, lng }) => {
                  const [x, y] = toSVG(lat, lng);
                  return (
                    <text key={label} x={x} y={y} fill="#94A3B8" fontSize={10} textAnchor="middle" fontStyle="italic" fontFamily="system-ui">
                      {label}
                    </text>
                  );
                })}
              </svg>
            </div>
          )}

          {/* ── Available Data Status Panel ────────────────────── */}
          <div className="border-t border-io-border bg-io-surface px-4 py-3 shrink-0">
            <h3 className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-2">
              {isAr ? "البيانات المتوفرة" : "Available Data"}
            </h3>
            <div className="space-y-1.5">
              {dataStatus.map((d) => (
                <div key={d.label} className="flex items-center justify-between text-xs">
                  <span className="text-io-primary">{isAr ? d.label_ar : d.label}</span>
                  <span className={`flex items-center gap-1 font-medium ${d.available ? "text-green-600" : "text-red-500"}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${d.available ? "bg-green-500" : "bg-red-500"}`} />
                    {d.available ? (isAr ? "متوفر" : "Available") : (isAr ? "غير متوفر" : "Unavailable")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
