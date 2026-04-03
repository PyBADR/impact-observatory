"use client";

/**
 * ImpactGlobeWrapper — renders entity impact overlay on the GCC globe.
 *
 * Layers:
 *   1. Entity pins — color = classification (CRITICAL/SEVERE/HIGH/MODERATE)
 *   2. Propagation arcs — lines from source to each impacted entity
 *   3. Loss labels — $XB loss on hover
 *
 * Falls back to SVG mini-map if no Cesium token.
 */

import { useMemo } from "react";
import type { RunResult, Language } from "@/types/observatory";
import type { GraphNode } from "@/types";

interface EntityImpact {
  entity_id: string;
  entity_label: string;
  loss_usd: number;
  stress_score: number;
  classification: string;
  lat: number;
  lng: number;
}

interface PropagationArc {
  from: { lat: number; lng: number; label: string };
  to: { lat: number; lng: number; label: string };
  impact: number;
  hop: number;
}

const CLASS_COLOR: Record<string, string> = {
  CRITICAL: "#B91C1C",
  SEVERE: "#C2410C",
  HIGH: "#B45309",
  ELEVATED: "#B45309",
  MODERATE: "#15803D",
  LOW: "#15803D",
  NOMINAL: "#6B7280",
};

function formatLoss(usd: number | null | undefined): string {
  const v = (usd === null || usd === undefined || !isFinite(usd as number)) ? 0 : (usd as number);
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${Math.round(v).toLocaleString()}`;
}

interface ImpactGlobeProps {
  runResult: RunResult | null;
  entities: GraphNode[];
  lang?: Language;
  className?: string;
}

export default function ImpactGlobe({
  runResult,
  entities,
  lang = "en",
  className = "",
}: ImpactGlobeProps) {
  const isAr = lang === "ar";

  // Build entity lookup: id → {lat, lng}
  const entityCoords = useMemo(() => {
    const map: Record<
      string,
      { lat: number; lng: number; label: string; label_ar?: string }
    > = {};
    for (const e of entities) {
      const node = e as GraphNode & {
        latitude?: number;
        longitude?: number;
        label_ar?: string;
      };
      if (node.latitude != null && node.longitude != null) {
        map[e.id] = {
          lat: node.latitude,
          lng: node.longitude,
          label: e.label,
          label_ar: node.label_ar,
        };
      }
    }
    return map;
  }, [entities]);

  // Build impact pins — support both `financial_impacts` (API field) and
  // `financial` (typed field in RunResult).
  const rawImpacts = useMemo(() => {
    if (!runResult) return [];
    const r = runResult as RunResult & {
      financial_impacts?: Array<Record<string, unknown>>;
    };
    if (r.financial_impacts && r.financial_impacts.length > 0) {
      return r.financial_impacts;
    }
    // Fall back to typed `financial` array, coercing shape
    return (r.financial ?? []).map((fi) => ({
      entity_id: fi.entity_id,
      entity_label: fi.entity_label ?? fi.entity_id,
      loss_usd: fi.loss_usd,
      stress_score: fi.stress_score ?? 0,
      classification: fi.classification,
    })) as Array<Record<string, unknown>>;
  }, [runResult]);

  const impacts: EntityImpact[] = useMemo(() => {
    return rawImpacts
      .filter((fi) => entityCoords[fi.entity_id as string])
      .map((fi) => ({
        entity_id: fi.entity_id as string,
        entity_label: (fi.entity_label as string) || (fi.entity_id as string),
        loss_usd: (fi.loss_usd as number) || 0,
        stress_score: (fi.stress_score as number) || 0,
        classification: (fi.classification as string) || "MODERATE",
        lat: entityCoords[fi.entity_id as string].lat,
        lng: entityCoords[fi.entity_id as string].lng,
      }))
      .sort((a, b) => b.loss_usd - a.loss_usd);
  }, [rawImpacts, entityCoords]);

  // Build propagation arcs (hop 0→1 connections)
  const arcs: PropagationArc[] = useMemo(() => {
    if (!runResult?.propagation) return [];
    const result: PropagationArc[] = [];
    const seen = new Set<string>();
    for (const prop of runResult.propagation as Array<Record<string, unknown>>) {
      const path: string[] = (prop.path as string[]) || [];
      if (path.length >= 2) {
        const fromId = path[path.length - 2];
        const toId = path[path.length - 1];
        const key = `${fromId}-${toId}`;
        if (!seen.has(key) && entityCoords[fromId] && entityCoords[toId]) {
          seen.add(key);
          result.push({
            from: { ...entityCoords[fromId] },
            to: { ...entityCoords[toId] },
            impact: (prop.impact as number) || 0,
            hop: (prop.hop as number) || 0,
          });
        }
      }
    }
    return result.slice(0, 30); // cap at 30 arcs for perf
  }, [runResult, entityCoords]);

  // SVG map: GCC bounding box roughly 15-32°N, 42-62°E
  const MAP_W = 800;
  const MAP_H = 400;
  const MIN_LAT = 15,
    MAX_LAT = 32,
    MIN_LNG = 42,
    MAX_LNG = 62;

  function toSVG(lat: number, lng: number): [number, number] {
    const x = ((lng - MIN_LNG) / (MAX_LNG - MIN_LNG)) * MAP_W;
    const y = MAP_H - ((lat - MIN_LAT) / (MAX_LAT - MIN_LAT)) * MAP_H;
    return [x, y];
  }

  const headline = runResult?.headline;
  const totalLoss = headline?.total_loss_usd ?? 0;
  const peakDay = headline?.peak_day ?? 0;

  return (
    <div
      className={`flex flex-col bg-slate-900 rounded-lg overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-white">
            {isAr ? "خريطة الأثر الجغرافي" : "GCC Impact Map"}
          </span>
          {runResult && (
            <>
              <span className="text-xs text-slate-400">
                {impacts.length} {isAr ? "كيان متأثر" : "entities impacted"}
              </span>
              <span className="text-xs font-bold text-red-400">
                {formatLoss(totalLoss)} {isAr ? "خسارة" : "loss"}
              </span>
              <span className="text-xs text-slate-400">
                {isAr ? "ذروة اليوم" : "Peak day"} {peakDay}
              </span>
            </>
          )}
        </div>
        {/* Legend */}
        <div className="flex items-center gap-2">
          {["CRITICAL", "SEVERE", "HIGH", "MODERATE"].map((cls) => (
            <div key={cls} className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CLASS_COLOR[cls] }}
              />
              <span className="text-[10px] text-slate-400">{cls}</span>
            </div>
          ))}
        </div>
      </div>

      {/* SVG Map */}
      <div className="relative flex-1 min-h-[320px]">
        {!runResult ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-3xl mb-3">🌍</div>
              <p className="text-slate-400 text-sm">
                {isAr
                  ? "شغّل سيناريو لرؤية الأثر الجغرافي"
                  : "Run a scenario to visualize geographic impact"}
              </p>
            </div>
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${MAP_W} ${MAP_H}`}
            className="w-full h-full"
            style={{
              background: "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
            }}
          >
            {/* Grid lines */}
            {[46, 50, 54, 58].map((lng) => {
              const [x] = toSVG(22, lng);
              return (
                <line
                  key={lng}
                  x1={x}
                  y1={0}
                  x2={x}
                  y2={MAP_H}
                  stroke="#334155"
                  strokeWidth={0.5}
                  strokeDasharray="4,4"
                />
              );
            })}
            {[20, 24, 28].map((lat) => {
              const [, y] = toSVG(lat, 50);
              return (
                <line
                  key={lat}
                  x1={0}
                  y1={y}
                  x2={MAP_W}
                  y2={y}
                  stroke="#334155"
                  strokeWidth={0.5}
                  strokeDasharray="4,4"
                />
              );
            })}

            {/* Propagation arcs */}
            {arcs.map((arc, i) => {
              const [x1, y1] = toSVG(arc.from.lat, arc.from.lng);
              const [x2, y2] = toSVG(arc.to.lat, arc.to.lng);
              const opacity = Math.max(0.15, arc.impact * 0.8);
              const color =
                arc.hop === 0
                  ? "#EF4444"
                  : arc.hop === 1
                  ? "#F97316"
                  : "#FBBF24";
              return (
                <line
                  key={i}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={color}
                  strokeWidth={Math.max(0.5, arc.impact * 2)}
                  strokeOpacity={opacity}
                  strokeDasharray={arc.hop > 1 ? "3,3" : undefined}
                />
              );
            })}

            {/* Entity pins */}
            {impacts.map((imp) => {
              const [x, y] = toSVG(imp.lat, imp.lng);
              const color = CLASS_COLOR[imp.classification] || "#6B7280";
              const radius = Math.max(
                4,
                Math.min(
                  14,
                  totalLoss > 0 ? (imp.loss_usd / totalLoss) * 60 + 4 : 4
                )
              );
              return (
                <g key={imp.entity_id}>
                  {/* Pulse ring for CRITICAL */}
                  {imp.classification === "CRITICAL" && (
                    <circle
                      cx={x}
                      cy={y}
                      r={radius + 6}
                      fill="none"
                      stroke={color}
                      strokeWidth={1}
                      opacity={0.3}
                    />
                  )}
                  <circle
                    cx={x}
                    cy={y}
                    r={radius}
                    fill={color}
                    fillOpacity={0.85}
                    stroke="white"
                    strokeWidth={1}
                  />
                  {/* Label */}
                  <text
                    x={x}
                    y={y - radius - 4}
                    fill="white"
                    fontSize={9}
                    textAnchor="middle"
                    fontFamily="monospace"
                  >
                    {imp.entity_label.length > 12
                      ? imp.entity_label.slice(0, 12) + "…"
                      : imp.entity_label}
                  </text>
                  <text
                    x={x}
                    y={y + radius + 10}
                    fill={color}
                    fontSize={8}
                    textAnchor="middle"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {formatLoss(imp.loss_usd)}
                  </text>
                </g>
              );
            })}

            {/* Region labels */}
            {[
              { label: "Persian Gulf", lat: 26.5, lng: 52 },
              { label: "Red Sea", lat: 20, lng: 38.5 },
              { label: "Arabian Sea", lat: 18, lng: 58 },
            ].map(({ label, lat, lng }) => {
              const [x, y] = toSVG(lat, lng);
              return (
                <text
                  key={label}
                  x={x}
                  y={y}
                  fill="#475569"
                  fontSize={10}
                  textAnchor="middle"
                  fontStyle="italic"
                >
                  {label}
                </text>
              );
            })}
          </svg>
        )}
      </div>

      {/* Impact table footer */}
      {impacts.length > 0 && (
        <div className="px-4 py-2 bg-slate-800 border-t border-slate-700 max-h-32 overflow-y-auto">
          <div className="grid grid-cols-4 gap-2">
            {impacts.slice(0, 8).map((imp) => (
              <div key={imp.entity_id} className="flex items-center gap-1.5">
                <div
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{
                    backgroundColor: CLASS_COLOR[imp.classification],
                  }}
                />
                <span className="text-[10px] text-slate-300 truncate">
                  {imp.entity_label}
                </span>
                <span
                  className="text-[10px] font-bold ml-auto"
                  style={{ color: CLASS_COLOR[imp.classification] }}
                >
                  {formatLoss(imp.loss_usd)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
