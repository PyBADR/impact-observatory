import { create } from "zustand";
import type { ScenarioResult, GlobeLayer, GeoCoord } from "@/types";
import type { WsSignalScoredData, ScenarioSeed, OperatorDecision, Outcome, DecisionValue } from "@/types/observatory";
import type { Persona } from "@/lib/persona-view-model";
import type { IntelligencePerspective } from "@/lib/intelligence/perspectiveEngine";

const _PERSONA_KEY = "io_persona_v1";

/**
 * Restore persona from localStorage AFTER hydration.
 * Store always initializes with "executive" so server & client match.
 * Call this inside a useEffect in consuming components.
 */
export function hydratePersonaFromStorage() {
  if (typeof window === "undefined") return;
  const stored = window.localStorage.getItem(_PERSONA_KEY);
  if (stored === "executive" || stored === "analyst" || stored === "regulator") {
    useAppStore.setState({ persona: stored });
  }
}

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

  // ---- Persona (role-based view) ----
  /** Active persona: drives which composed view renders in the results screen. */
  persona: Persona;
  setPersona: (p: Persona) => void;

  // ---- View Mode (visualization: globe vs graph) ----
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

  // ---- Intelligence Perspective ----
  activePerspective: IntelligencePerspective;
  setActivePerspective: (p: IntelligencePerspective) => void;

  // ---- Time Horizon ----
  timeHorizon: 24 | 72 | 168;
  setTimeHorizon: (h: 24 | 72 | 168) => void;

  // ---- Live Signal Layer ----
  /** Most recent signal.scored events from /ws/signals (capped at 50). */
  liveSignals: WsSignalScoredData[];
  addLiveSignal: (signal: WsSignalScoredData) => void;
  /** Seeds currently in PENDING_REVIEW awaiting HITL decision. */
  pendingSeeds: ScenarioSeed[];
  setPendingSeeds: (seeds: ScenarioSeed[]) => void;
  removePendingSeed: (seedId: string) => void;

  // ---- Operator Layer ----
  /** Active operator decisions (all non-CLOSED, newest first). */
  operatorDecisions: OperatorDecision[];
  setOperatorDecisions: (decisions: OperatorDecision[]) => void;
  upsertOperatorDecision: (decision: OperatorDecision) => void;
  /** Selected decision for detail view. */
  selectedDecisionId: string | null;
  setSelectedDecisionId: (id: string | null) => void;

  // ---- Outcome Intelligence Layer ----
  /** Outcomes, newest first. Populated by useOutcomes() query polling. */
  outcomes: Outcome[];
  setOutcomes: (outcomes: Outcome[]) => void;
  upsertOutcome: (outcome: Outcome) => void;

  // ---- ROI / Decision Value Layer ----
  /** Computed decision values, newest first. Populated by useDecisionValues() polling. */
  decisionValues: DecisionValue[];
  setDecisionValues: (values: DecisionValue[]) => void;
  upsertDecisionValue: (value: DecisionValue) => void;
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

  // ---- Persona (always "executive" at init — localStorage restored post-hydration) ----
  persona: "executive",
  setPersona: (p) => {
    if (typeof window !== "undefined") window.localStorage.setItem(_PERSONA_KEY, p);
    set({ persona: p });
  },

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

  // ---- Intelligence Perspective ----
  activePerspective: "gcc_sovereign" as IntelligencePerspective,
  setActivePerspective: (p) => set({ activePerspective: p }),

  // ---- Time Horizon ----
  timeHorizon: 72,
  setTimeHorizon: (h) => set({ timeHorizon: h }),

  // ---- Live Signal Layer ----
  liveSignals: [],
  addLiveSignal: (signal) =>
    set((state) => ({
      liveSignals: [signal, ...state.liveSignals].slice(0, 50),
    })),
  pendingSeeds: [],
  setPendingSeeds: (seeds) => set({ pendingSeeds: seeds }),
  removePendingSeed: (seedId) =>
    set((state) => ({
      pendingSeeds: state.pendingSeeds.filter((s) => s.seed_id !== seedId),
    })),

  // ---- Operator Layer ----
  operatorDecisions: [],
  setOperatorDecisions: (decisions) => set({ operatorDecisions: decisions }),
  upsertOperatorDecision: (decision) =>
    set((state) => {
      const existing = state.operatorDecisions.findIndex(
        (d) => d.decision_id === decision.decision_id
      );
      if (existing >= 0) {
        const next = [...state.operatorDecisions];
        next[existing] = decision;
        return { operatorDecisions: next };
      }
      return { operatorDecisions: [decision, ...state.operatorDecisions] };
    }),
  selectedDecisionId: null,
  setSelectedDecisionId: (id) => set({ selectedDecisionId: id }),

  // ---- Outcome Intelligence Layer ----
  outcomes: [],
  setOutcomes: (outcomes) => set({ outcomes }),
  upsertOutcome: (outcome) =>
    set((state) => {
      const existing = state.outcomes.findIndex((o) => o.outcome_id === outcome.outcome_id);
      if (existing >= 0) {
        const next = [...state.outcomes];
        next[existing] = outcome;
        return { outcomes: next };
      }
      return { outcomes: [outcome, ...state.outcomes] };
    }),

  // ---- ROI / Decision Value Layer ----
  decisionValues: [],
  setDecisionValues: (values) => set({ decisionValues: values }),
  upsertDecisionValue: (value) =>
    set((state) => {
      const existing = state.decisionValues.findIndex((v) => v.value_id === value.value_id);
      if (existing >= 0) {
        const next = [...state.decisionValues];
        next[existing] = value;
        return { decisionValues: next };
      }
      return { decisionValues: [value, ...state.decisionValues] };
    }),
}));
