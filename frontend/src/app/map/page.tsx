"use client";

/**
 * Impact Observatory | مرصد الأثر — Impact Map
 *
 * SVG entity map showing impacted GCC institutions and corridors.
 * Institutional light controls sidebar + geographic visualization.
 *
 * Capability gating: EntityLayer is never rendered when map_supported = false.
 * The backend's absence of map_payload is a structural capability limitation,
 * not an error. The MapCapabilityState is shown instead — no retry, no error.
 */

import { useState, useEffect, useCallback } from "react";
import AppShell from "@/components/shell/AppShell";
import { useAppStore } from "@/store/app-store";
import { useRunState } from "@/lib/run-state";
import { useGlobeEntities } from "@/features/globe/useGlobeEntities";
import { EntityLayer } from "@/features/globe/EntityLayer";
import { ImpactOverlay } from "@/features/globe/ImpactOverlay";
import {
  ClassificationBadge,
  DataRow,
} from "@/components/ui";
import type { ImpactedEntity } from "@/types/observatory";

// ── Map capability state (geospatial not supported by current backend) ──

function MapCapabilityState({ isAr }: { isAr: boolean }) {
  return (
    <div className="absolute inset-0 bg-slate-950 flex items-center justify-center">
      <div className="max-w-sm w-full mx-6 text-center">
        <div className="w-12 h-12 border border-slate-700 rounded-xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
          </svg>
        </div>
        <p className="text-sm font-semibold text-slate-300 mb-2">
          {isAr
            ? "التحليل الجغرافي غير متاح لهذا السيناريو"
            : "Geospatial analysis is not available for this scenario"}
        </p>
        <p className="text-xs text-slate-500 leading-relaxed mb-4">
          {isAr
            ? "لا تتضمن نتيجة هذا السيناريو بيانات الموقع الجغرافي. يظل تحليل الأثر المالي متاحاً من لوحة المعلومات."
            : "This scenario result does not include geolocation data. Financial impact analysis remains accessible from the dashboard."}
        </p>
        <a
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
        >
          {isAr ? "عرض التحليل الكامل" : "View Full Analysis"}
        </a>
      </div>
    </div>
  );
}

// ── Selected entity detail panel ───────────────────────────────────────

function EntityDetailPanel({
  entity,
  onClose,
  isAr,
}: {
  entity: ImpactedEntity;
  onClose: () => void;
  isAr: boolean;
}) {
  const formatUSD = (v: number | undefined) => {
    if (!v) return "—";
    if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    return `$${v.toLocaleString()}`;
  };

  return (
    <div className="p-4 border-t border-io-border bg-io-surface">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-0.5">
            {isAr ? "الكيان المحدد" : "Selected Entity"}
          </p>
          <p className="text-sm font-semibold text-io-primary leading-snug">
            {isAr && entity.label_ar ? entity.label_ar : entity.label ?? entity.node_id}
          </p>
        </div>
        <button
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded text-io-secondary hover:text-io-primary hover:bg-io-bg transition-colors flex-shrink-0"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-0">
        {entity.loss_usd !== undefined && (
          <DataRow
            label={isAr ? "الخسارة المقدّرة" : "Estimated Loss"}
            value={formatUSD(entity.loss_usd)}
            mono
          />
        )}
        {entity.stress !== undefined && (
          <DataRow
            label={isAr ? "مستوى الضغط" : "Stress Level"}
            value={`${(entity.stress * 100).toFixed(1)}%`}
            mono
          />
        )}
        {entity.classification && (
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-io-secondary">
              {isAr ? "التصنيف" : "Classification"}
            </span>
            <ClassificationBadge
              level={entity.classification}
              lang={isAr ? "ar" : "en"}
              size="xs"
            />
          </div>
        )}
        {entity.layer && (
          <DataRow
            label={isAr ? "الطبقة" : "Layer"}
            value={entity.layer}
          />
        )}
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────

export default function MapPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const adaptedResult = useRunState((s) => s.adaptedResult);
  const scenarioLabel = adaptedResult?.scenario?.label ?? undefined;

  const {
    entities,
    runResult,
    scenarios,
    loading,
    scenariosLoading,
    mapSupported,
    error,
    loadScenarios,
    runScenario,
    clearRun,
  } = useGlobeEntities();

  const [selectedScenario, setSelectedScenario] = useState("");
  const [severity, setSeverity] = useState(0.7);
  const [selectedEntity, setSelectedEntity] = useState<ImpactedEntity | null>(null);

  useEffect(() => {
    loadScenarios();
  }, [loadScenarios]);

  const handleRun = useCallback(async () => {
    if (!selectedScenario) return;
    setSelectedEntity(null);
    await runScenario(selectedScenario, severity);
  }, [selectedScenario, severity, runScenario]);

  const handleEntityClick = useCallback((entity: ImpactedEntity) => {
    setSelectedEntity((prev) =>
      prev?.node_id === entity.node_id ? null : entity
    );
  }, []);

  return (
    <AppShell activeRoute="map" scenarioLabel={scenarioLabel}>
      <div className="flex h-[calc(100vh-56px)]" dir={isAr ? "rtl" : "ltr"}>

        {/* ── Left: Institutional controls panel ──────────────────── */}
        <div className="w-72 flex-shrink-0 border-r border-io-border bg-io-surface flex flex-col overflow-y-auto">

          {/* Panel header */}
          <div className="px-4 py-3.5 border-b border-io-border flex-shrink-0">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-0.5">
              {isAr ? "محاكاة السيناريو" : "Scenario Parameters"}
            </p>
            <p className="text-xs text-io-secondary">
              {isAr
                ? "اختر سيناريو لعرض الكيانات المتأثرة"
                : "Select a scenario to visualize impacted entities"}
            </p>
          </div>

          <div className="flex-1 flex flex-col p-4 gap-4">
            {/* Scenario selector */}
            <div>
              <label className="block text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-1.5">
                {isAr ? "السيناريو" : "Scenario"}
              </label>
              {scenariosLoading ? (
                <div className="h-9 bg-io-bg border border-io-border rounded-lg flex items-center px-3">
                  <span className="text-xs text-io-secondary">
                    {isAr ? "تحميل..." : "Loading…"}
                  </span>
                </div>
              ) : (
                <select
                  value={selectedScenario}
                  onChange={(e) => setSelectedScenario(e.target.value)}
                  className="w-full bg-io-bg border border-io-border rounded-lg px-3 py-2 text-xs text-io-primary focus:outline-none focus:border-io-accent transition-colors"
                >
                  <option value="">
                    {isAr ? "اختر سيناريو..." : "Select a scenario…"}
                  </option>
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Severity control */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest">
                  {isAr ? "شدة الصدمة" : "Shock Severity"}
                </label>
                <span className="text-xs font-bold tabular-nums text-io-primary">
                  {(severity * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={severity}
                onChange={(e) => setSeverity(parseFloat(e.target.value))}
                className="w-full accent-io-accent"
              />
              <div className="flex justify-between text-[10px] text-io-secondary mt-1">
                <span>{isAr ? "منخفضة ١٠٪" : "Low 10%"}</span>
                <span>{isAr ? "عالية ١٠٠٪" : "High 100%"}</span>
              </div>
            </div>

            {/* Run button */}
            <button
              onClick={handleRun}
              disabled={!selectedScenario || loading}
              className="w-full py-2.5 px-4 bg-io-accent text-white text-xs font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading
                ? isAr ? "جاري التحليل..." : "Running analysis…"
                : isAr ? "تشغيل التحليل" : "Run Analysis"}
            </button>

            {runResult && (
              <button
                onClick={clearRun}
                className="w-full py-2 px-4 border border-io-border text-io-secondary hover:text-io-primary text-xs font-medium rounded-lg transition-colors"
              >
                {isAr ? "مسح النتائج" : "Clear Results"}
              </button>
            )}

            {/* Hard API error (network failure, not capability limitation) */}
            {error && !runResult && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs font-semibold text-amber-800 mb-1">
                  {isAr ? "تعذّر تشغيل التحليل" : "Analysis Run Failed"}
                </p>
                <p className="text-xs text-amber-700">
                  {error}
                </p>
              </div>
            )}

            {/* Impact summary — always shown when result present, regardless of map support */}
            {runResult && (
              <div className="flex-1 overflow-y-auto">
                <div className="border-t border-io-border pt-3">
                  <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-3">
                    {isAr ? "ملخص الأثر" : "Impact Summary"}
                  </p>
                  <ImpactOverlay
                    result={runResult}
                    selectedEntity={selectedEntity}
                    isAr={isAr}
                    stagesCompleted={adaptedResult?.pipeline_stages_completed ?? 0}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Entity detail panel — only shown when map data is present */}
          {selectedEntity && mapSupported && (
            <EntityDetailPanel
              entity={selectedEntity}
              onClose={() => setSelectedEntity(null)}
              isAr={isAr}
            />
          )}
        </div>

        {/* ── Right: Map canvas area ───────────────────────────────── */}
        <div className="flex-1 relative overflow-hidden">
          {!runResult ? (
            /* Pre-run: waiting for scenario selection */
            <div className="absolute inset-0 bg-slate-950 flex items-center justify-center">
              <div className="text-center max-w-sm px-6">
                {scenariosLoading ? (
                  <>
                    <div className="w-10 h-10 border border-slate-700 rounded-xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-5 h-5 animate-spin text-slate-400" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    </div>
                    <p className="text-xs text-slate-400">
                      {isAr ? "تحميل السيناريوهات..." : "Loading scenarios…"}
                    </p>
                  </>
                ) : (
                  <>
                    <div className="w-12 h-12 border border-slate-700 rounded-xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-6 h-6 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                      </svg>
                    </div>
                    <p className="text-sm font-semibold text-slate-300 mb-2">
                      {isAr ? "خريطة الأثر" : "GCC Impact Map"}
                    </p>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      {isAr
                        ? "اختر سيناريو من القائمة وشغّل التحليل لعرض الكيانات المتأثرة على الخريطة الجغرافية."
                        : "Select a scenario from the controls panel and run the analysis to visualize impacted GCC entities on the geographic map."}
                    </p>
                  </>
                )}
              </div>
            </div>
          ) : mapSupported ? (
            /* Capability confirmed: render entity layer */
            <EntityLayer
              entities={entities}
              selectedEntityId={selectedEntity?.node_id}
              onEntityClick={handleEntityClick}
              isAr={isAr}
            />
          ) : (
            /* Capability gate: map_payload absent — clean capability state, no retry */
            <MapCapabilityState isAr={isAr} />
          )}

          {/* Analysis progress bar */}
          {loading && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-io-border">
              <div className="h-full bg-io-accent animate-pulse w-full" />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
