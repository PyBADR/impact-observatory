import { create } from "zustand";
import type { ScenarioResult, GlobeLayer, GeoCoord } from "@/types";

interface CameraPosition {
  lat: number;
  lng: number;
  altitude: number;
  heading?: number;
  pitch?: number;
}

interface AppState {
  // ---- Language ----
  language: "en" | "ar";
  setLanguage: (lang: "en" | "ar") => void;

  // ---- View Mode ----
  viewMode: "globe" | "graph";
  setViewMode: (mode: "globe" | "graph") => void;

  // ---- Scenario ----
  selectedScenarioId: string | null;
  setSelectedScenarioId: (id: string | null) => void;
  severity: number;
  setSeverity: (s: number) => void;
  scenarioResult: ScenarioResult | null;
  setScenarioResult: (result: ScenarioResult | null) => void;

  // ---- Globe Camera ----
  cameraPosition: CameraPosition;
  setCameraPosition: (pos: CameraPosition) => void;
  flyTo: (target: GeoCoord & { altitude?: number }) => void;

  // ---- Selected Entity ----
  selectedEntityId: string | null;
  setSelectedEntityId: (id: string | null) => void;
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;

  // ---- Active Layers ----
  activeLayers: Set<string>;
  toggleLayer: (layer: string) => void;
  setLayers: (layers: GlobeLayer[]) => void;

  // ---- Insurance View ----
  insuranceViewOpen: boolean;
  setInsuranceViewOpen: (open: boolean) => void;
  insuranceSector: string | null;
  setInsuranceSector: (sector: string | null) => void;

  // ---- Decision Output ----
  decisionOutputOpen: boolean;
  setDecisionOutputOpen: (open: boolean) => void;

  // ---- Time Horizon ----
  timeHorizon: 24 | 72 | 168;
  setTimeHorizon: (h: 24 | 72 | 168) => void;
}

const GCC_CENTER: CameraPosition = {
  lat: 25,
  lng: 52,
  altitude: 3_000_000,
  heading: 0,
  pitch: -90,
};

export const useAppStore = create<AppState>((set) => ({
  // ---- Language ----
  language: "en",
  setLanguage: (lang) => set({ language: lang }),

  // ---- View Mode ----
  viewMode: "globe",
  setViewMode: (mode) => set({ viewMode: mode }),

  // ---- Scenario ----
  selectedScenarioId: null,
  setSelectedScenarioId: (id) => set({ selectedScenarioId: id }),
  severity: 0.6,
  setSeverity: (s) => set({ severity: s }),
  scenarioResult: null,
  setScenarioResult: (result) => set({ scenarioResult: result }),

  // ---- Globe Camera ----
  cameraPosition: GCC_CENTER,
  setCameraPosition: (pos) => set({ cameraPosition: pos }),
  flyTo: (target) =>
    set({
      cameraPosition: {
        lat: target.lat,
        lng: target.lng,
        altitude: target.altitude ?? 500_000,
        heading: 0,
        pitch: -45,
      },
    }),

  // ---- Selected Entity ----
  selectedEntityId: null,
  setSelectedEntityId: (id) => set({ selectedEntityId: id }),
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),

  // ---- Active Layers ----
  activeLayers: new Set(["events", "flights", "vessels", "heatmap"]),
  toggleLayer: (layer) =>
    set((state) => {
      const next = new Set(state.activeLayers);
      if (next.has(layer)) next.delete(layer);
      else next.add(layer);
      return { activeLayers: next };
    }),
  setLayers: (layers) => set({ activeLayers: new Set(layers) }),

  // ---- Insurance View ----
  insuranceViewOpen: false,
  setInsuranceViewOpen: (open) => set({ insuranceViewOpen: open }),
  insuranceSector: null,
  setInsuranceSector: (sector) => set({ insuranceSector: sector }),

  // ---- Decision Output ----
  decisionOutputOpen: false,
  setDecisionOutputOpen: (open) => set({ decisionOutputOpen: open }),

  // ---- Time Horizon ----
  timeHorizon: 72,
  setTimeHorizon: (h) => set({ timeHorizon: h }),
}));
