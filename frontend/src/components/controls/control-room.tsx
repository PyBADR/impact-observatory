"use client";

/**
 * Impact Observatory | مرصد الأثر — Control Room Component (Light Theme)
 */

import { useCallback } from "react";
import { useAppStore } from "@/store/app-store";
import {
  useEvents,
  useFlights,
  useVessels,
  useScenarioTemplates,
  useRunScenario,
  useSystemStress,
} from "@/hooks/use-api";
import { GlobeWrapper } from "@/components/globe";
import { DeckGLOverlayCanvas } from "@/components/globe/deckgl-overlay";
import { ScenarioPanel } from "@/components/panels/scenario-panel";
import { ImpactPanel } from "@/components/panels/impact-panel";
import { ScientistBar } from "@/components/panels/scientist-bar";
import Link from "next/link";

const LAYER_OPTIONS = ["events", "flights", "vessels", "heatmap", "arcs"];

export function ControlRoom() {
  const {
    language,
    setLanguage,
    selectedScenarioId,
    setSelectedScenarioId,
    severity,
    setSeverity,
    scenarioResult,
    setScenarioResult,
    activeLayers,
    toggleLayer,
    cameraPosition,
    selectedEntityId,
    setSelectedEntityId,
    viewMode,
    setViewMode,
  } = useAppStore();

  const isAr = language === "ar";

  // Data queries
  const { data: templates } = useScenarioTemplates();
  const { data: eventsData } = useEvents({ limit: 50 });
  const { data: flightsData } = useFlights({ limit: 50 });
  const { data: vesselsData } = useVessels({ limit: 50 });
  const { data: stressData } = useSystemStress();

  const events = eventsData?.events ?? [];
  const flights = flightsData?.flights ?? [];
  const vessels = vesselsData?.vessels ?? [];

  const runScenario = useRunScenario((data) => setScenarioResult(data));

  const handleEntityClick = useCallback(
    (entityId: string, _entityType: string) => {
      setSelectedEntityId(entityId);
    },
    [setSelectedEntityId]
  );

  return (
    <div className="flex flex-col h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-io-surface border-b border-io-border shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-lg font-bold text-io-accent">
            {isAr ? "مرصد الأثر" : "Impact Observatory"}
          </Link>
          <span className="text-sm text-io-secondary">
            {isAr ? "لوحة المراقبة" : "Monitoring View"}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* System stress */}
          {stressData && (
            <div className="flex items-center gap-1 text-[10px]">
              <span className="text-io-secondary">{isAr ? "إجهاد:" : "Stress:"}</span>
              <span
                className={`font-mono font-bold ${
                  stressData.overall_stress > 0.5
                    ? "text-io-danger"
                    : stressData.overall_stress > 0.2
                    ? "text-io-warning"
                    : "text-io-success"
                }`}
              >
                {(stressData.overall_stress * 100).toFixed(1)}%
              </span>
            </div>
          )}

          {/* Layer toggles */}
          <div className="flex gap-1">
            {LAYER_OPTIONS.map((l) => (
              <button
                key={l}
                onClick={() => toggleLayer(l)}
                className={`px-2 py-1 text-[10px] rounded transition ${
                  activeLayers.has(l)
                    ? "bg-io-accent text-white"
                    : "bg-io-bg text-io-secondary hover:text-io-primary border border-io-border"
                }`}
              >
                {l}
              </button>
            ))}
          </div>

          {/* Mode switcher */}
          <div className="flex gap-1 bg-io-bg rounded p-0.5 border border-io-border">
            <button
              onClick={() => setViewMode("globe")}
              className={`px-2 py-1 text-[10px] rounded ${
                viewMode === "globe" ? "bg-io-accent text-white" : "text-io-secondary"
              }`}
            >
              {isAr ? "كرة" : "Globe"}
            </button>
            <button
              onClick={() => setViewMode("graph")}
              className={`px-2 py-1 text-[10px] rounded ${
                viewMode === "graph" ? "bg-io-accent text-white" : "text-io-secondary"
              }`}
            >
              {isAr ? "شبكة" : "Graph"}
            </button>
          </div>

          {/* Nav links */}
          <div className="flex gap-1 text-[10px]">
            <Link href="/" className="px-2 py-1 bg-io-bg text-io-secondary border border-io-border rounded hover:text-io-primary transition">
              {isAr ? "لوحة المعلومات" : "Dashboard"}
            </Link>
            <Link href="/scenario-lab" className="px-2 py-1 bg-io-bg text-io-secondary border border-io-border rounded hover:text-io-primary transition">
              {isAr ? "معمل" : "Lab"}
            </Link>
            <Link href="/graph-explorer" className="px-2 py-1 bg-io-bg text-io-secondary border border-io-border rounded hover:text-io-primary transition">
              {isAr ? "رسم بياني" : "Graph"}
            </Link>
          </div>

          <button
            onClick={() => setLanguage(isAr ? "en" : "ar")}
            className="px-3 py-1 text-xs bg-io-accent rounded text-white hover:bg-blue-700 transition"
          >
            {isAr ? "EN" : "AR"}
          </button>
        </div>
      </header>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — Scenario Panel */}
        <aside className="w-64 min-w-[256px] bg-io-surface border-r border-io-border overflow-y-auto p-3 shrink-0">
          <ScenarioPanel
            templates={templates?.templates || []}
            selectedId={selectedScenarioId}
            onSelect={(id) => {
              setSelectedScenarioId(id);
              runScenario.mutate({ scenario_id: id, severity_override: severity });
            }}
            severity={severity}
            onSeverityChange={setSeverity}
            isRunning={runScenario.isPending}
            isAr={isAr}
          />
        </aside>

        {/* Center — Globe (keeps dark bg for 3D rendering) */}
        <main className="flex-1 flex flex-col bg-slate-900 relative">
          <div className="flex-1 relative">
            <GlobeWrapper
              flights={flights}
              vessels={vessels}
              events={events}
              selectedEntityId={selectedEntityId}
              onEntityClick={handleEntityClick}
              activeLayers={activeLayers}
              cameraTarget={{
                lat: cameraPosition.lat,
                lng: cameraPosition.lng,
                altitude: cameraPosition.altitude,
              }}
            />

            <DeckGLOverlayCanvas
              events={events}
              flights={flights}
              vessels={vessels}
              activeLayers={activeLayers}
            />

            {/* Selected entity card */}
            {selectedEntityId && (
              <div className="absolute top-3 left-3 bg-io-surface/95 backdrop-blur border border-io-border rounded-lg p-3 max-w-xs z-20 shadow-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-io-accent">{selectedEntityId}</span>
                  <button onClick={() => setSelectedEntityId(null)} className="text-io-secondary hover:text-io-primary text-xs">
                    ✕
                  </button>
                </div>
                <Link href={`/entity/${selectedEntityId}`} className="text-[10px] text-io-accent underline">
                  {isAr ? "عرض التفاصيل" : "View Details →"}
                </Link>
              </div>
            )}
          </div>

          {/* Event feed strip */}
          {events.length > 0 && (
            <div className="absolute bottom-12 left-0 right-0 bg-io-surface/90 backdrop-blur px-4 py-2 border-t border-io-border z-10">
              <div className="flex gap-4 overflow-x-auto text-xs">
                {events.slice(0, 20).map((ev) => (
                  <div
                    key={ev.id}
                    className="flex-shrink-0 flex items-center gap-2 cursor-pointer hover:text-io-primary"
                    onClick={() => setSelectedEntityId(ev.id)}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        ev.severity_score > 0.7
                          ? "bg-io-danger"
                          : ev.severity_score > 0.4
                          ? "bg-io-warning"
                          : "bg-io-success"
                      }`}
                    />
                    <span className="text-io-primary">{ev.title}</span>
                    <span className="text-io-secondary">
                      {(ev.severity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scientist bar */}
          <ScientistBar result={scenarioResult} isAr={isAr} />
        </main>

        {/* Right — Impact Panel */}
        <aside className="w-72 min-w-[288px] bg-io-surface border-l border-io-border overflow-y-auto p-3 shrink-0">
          <ImpactPanel result={scenarioResult} isAr={isAr} />
        </aside>
      </div>
    </div>
  );
}
