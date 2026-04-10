/**
 * Impact Observatory | مرصد الأثر — Unified Flow Engine
 *
 * Single state machine governing the entire decision intelligence pipeline:
 *   Signal (Jet Nexus) → Reasoning (TREK) → Simulation (Impact)
 *   → Decision → Outcome → ROI → Control Tower
 *
 * RULES:
 *   - One active flow at a time (the "current scenario journey")
 *   - Every stage transition is timestamped and traceable
 *   - All UI components read from this store — no isolated state
 *   - Personas read the SAME flow, rendered through different lenses
 *   - Control Tower aggregates the full flow, not just the latest stage
 */

import { create } from "zustand";
import type {
  RunResult,
  WsSignalScoredData,
  ScenarioSeed,
  OperatorDecision,
  Outcome,
  DecisionValue,
} from "@/types/observatory";

// ─── Flow Stage Definitions ─────────────────────────────────────────────────

export type FlowStage =
  | "idle"           // No active flow
  | "signal"         // Jet Nexus: signal ingested / scenario selected
  | "reasoning"      // TREK: reasoning layer processing
  | "simulation"     // Impact Observatory: propagation + stress modeling
  | "decision"       // Decision engine: actions generated
  | "outcome"        // Outcome tracking: real-world observation
  | "roi"            // Value computation: net value, avoided loss
  | "control_tower"; // Executive aggregation: full system synthesis

export type FlowStatus = "active" | "completed" | "failed" | "skipped";

export interface FlowStageEntry {
  stage: FlowStage;
  status: FlowStatus;
  enteredAt: string;       // ISO timestamp
  completedAt: string | null;
  durationMs: number | null;
  /** Human-readable label for timeline display */
  label: string;
  labelAr: string;
  /** Key data snapshot at this stage (for narrative engine) */
  snapshot: Record<string, unknown>;
}

// ─── Flow Context: the data payload traveling through the pipeline ───────────

export interface FlowContext {
  /** Originating scenario ID */
  scenarioId: string;
  scenarioLabel: string;
  scenarioLabelAr: string;
  severity: number;

  /** Signal that initiated this flow (live signal or scenario selection) */
  originSignal: WsSignalScoredData | null;
  originSeed: ScenarioSeed | null;

  /** Full RunResult from the pipeline */
  runResult: RunResult | null;
  runId: string | null;

  /** Operator decisions linked to this flow */
  decisions: OperatorDecision[];

  /** Outcomes observed for this flow */
  outcomes: Outcome[];

  /** ROI / decision values computed */
  values: DecisionValue[];
}

// ─── Flow Instance: one complete journey through the pipeline ────────────────

export interface FlowInstance {
  /** Unique flow ID */
  flowId: string;
  /** When this flow was initiated */
  createdAt: string;
  /** Current active stage */
  currentStage: FlowStage;
  /** Ordered history of all stage transitions */
  stages: FlowStageEntry[];
  /** Accumulated context as data flows through stages */
  context: FlowContext;
  /** Is this flow still progressing? */
  isActive: boolean;
  /** Overall flow health */
  health: "healthy" | "degraded" | "failed";
}

// ─── Stage Metadata ─────────────────────────────────────────────────────────

export const FLOW_STAGE_META: Record<FlowStage, { label: string; labelAr: string; icon: string; order: number }> = {
  idle:           { label: "Idle",           labelAr: "خامل",           icon: "○", order: 0 },
  signal:         { label: "Signal",         labelAr: "الإشارة",        icon: "📡", order: 1 },
  reasoning:      { label: "Reasoning",      labelAr: "التحليل",        icon: "🧠", order: 2 },
  simulation:     { label: "Simulation",     labelAr: "المحاكاة",       icon: "🔬", order: 3 },
  decision:       { label: "Decision",       labelAr: "القرار",         icon: "🎯", order: 4 },
  outcome:        { label: "Outcome",        labelAr: "النتيجة",        icon: "📊", order: 5 },
  roi:            { label: "ROI",            labelAr: "العائد",          icon: "💰", order: 6 },
  control_tower:  { label: "Control Tower",  labelAr: "برج التحكم",     icon: "🏛️", order: 7 },
};

export const FLOW_STAGES_ORDERED: FlowStage[] = [
  "signal", "reasoning", "simulation", "decision", "outcome", "roi", "control_tower",
];

// ─── Store Interface ────────────────────────────────────────────────────────

interface FlowState {
  /** The current active flow (null = idle) */
  activeFlow: FlowInstance | null;
  /** Historical flows (completed journeys) */
  flowHistory: FlowInstance[];
  /** Maximum history depth */
  maxHistory: number;

  // ── Actions ──

  /** Initialize a new flow from a scenario selection */
  startFlow: (params: {
    scenarioId: string;
    scenarioLabel: string;
    scenarioLabelAr: string;
    severity: number;
    originSignal?: WsSignalScoredData;
    originSeed?: ScenarioSeed;
  }) => string; // returns flowId

  /** Advance the flow to the next stage */
  advanceStage: (stage: FlowStage, snapshot?: Record<string, unknown>) => void;

  /** Complete the current stage and advance */
  completeCurrentStage: (snapshot?: Record<string, unknown>) => void;

  /** Mark current stage as failed */
  failCurrentStage: (error: string) => void;

  /** Attach RunResult to the flow context */
  attachRunResult: (result: RunResult, runId: string) => void;

  /** Attach operator decisions to flow */
  attachDecisions: (decisions: OperatorDecision[]) => void;

  /** Attach outcomes to flow */
  attachOutcomes: (outcomes: Outcome[]) => void;

  /** Attach decision values to flow */
  attachValues: (values: DecisionValue[]) => void;

  /** Complete the entire flow (moves to control_tower then archives) */
  completeFlow: () => void;

  /** Reset to idle */
  resetFlow: () => void;

  // ── Selectors ──

  /** Get stage completion percentage (0-100) */
  getFlowProgress: () => number;

  /** Get the completed stage entries */
  getCompletedStages: () => FlowStageEntry[];

  /** Is a specific stage complete? */
  isStageComplete: (stage: FlowStage) => boolean;

  /** Get the stage entry for a specific stage */
  getStageEntry: (stage: FlowStage) => FlowStageEntry | null;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function generateFlowId(): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 8);
  return `flow_${ts}_${rand}`;
}

function now(): string {
  return new Date().toISOString();
}

function createStageEntry(stage: FlowStage, snapshot: Record<string, unknown> = {}): FlowStageEntry {
  const meta = FLOW_STAGE_META[stage];
  return {
    stage,
    status: "active",
    enteredAt: now(),
    completedAt: null,
    durationMs: null,
    label: meta.label,
    labelAr: meta.labelAr,
    snapshot,
  };
}

// ─── Re-entry Guards ────────────────────────────────────────────────────────
// Module-level flags prevent recursive/duplicate execution of attach* and
// advanceStage when a Zustand subscriber re-invokes one of these functions
// during the same synchronous set() propagation cycle.
// Flags reset to false immediately after set() returns — no logic is changed.

let _inAdvanceStage     = false;
let _inAttachDecisions  = false;
let _inAttachOutcomes   = false;
let _inAttachValues     = false;

// ─── Store Implementation ───────────────────────────────────────────────────

export const useFlowStore = create<FlowState>((set, get) => ({
  activeFlow: null,
  flowHistory: [],
  maxHistory: 20,

  startFlow: (params) => {
    const flowId = generateFlowId();
    const signalEntry = createStageEntry("signal", {
      scenarioId: params.scenarioId,
      severity: params.severity,
    });
    signalEntry.status = "active";

    const flow: FlowInstance = {
      flowId,
      createdAt: now(),
      currentStage: "signal",
      stages: [signalEntry],
      context: {
        scenarioId: params.scenarioId,
        scenarioLabel: params.scenarioLabel,
        scenarioLabelAr: params.scenarioLabelAr,
        severity: params.severity,
        originSignal: params.originSignal ?? null,
        originSeed: params.originSeed ?? null,
        runResult: null,
        runId: null,
        decisions: [],
        outcomes: [],
        values: [],
      },
      isActive: true,
      health: "healthy",
    };

    set({ activeFlow: flow });
    return flowId;
  },

  advanceStage: (stage, snapshot = {}) => {
    if (_inAdvanceStage) return;
    _inAdvanceStage = true;
    set((state) => {
      if (!state.activeFlow) return state;

      const flow = { ...state.activeFlow };
      const stages = [...flow.stages];

      // Complete current active stage
      const currentIdx = stages.findIndex(
        (s) => s.stage === flow.currentStage && s.status === "active"
      );
      if (currentIdx >= 0) {
        const entry = { ...stages[currentIdx] };
        entry.status = "completed";
        entry.completedAt = now();
        entry.durationMs = new Date(entry.completedAt).getTime() - new Date(entry.enteredAt).getTime();
        stages[currentIdx] = entry;
      }

      // Add new stage entry
      stages.push(createStageEntry(stage, snapshot));

      flow.stages = stages;
      flow.currentStage = stage;

      return { activeFlow: flow };
    });
    _inAdvanceStage = false;
  },

  completeCurrentStage: (snapshot = {}) => {
    set((state) => {
      if (!state.activeFlow) return state;

      const flow = { ...state.activeFlow };
      const stages = [...flow.stages];
      const currentIdx = stages.findIndex(
        (s) => s.stage === flow.currentStage && s.status === "active"
      );
      if (currentIdx >= 0) {
        const entry = { ...stages[currentIdx] };
        entry.status = "completed";
        entry.completedAt = now();
        entry.durationMs = new Date(entry.completedAt).getTime() - new Date(entry.enteredAt).getTime();
        entry.snapshot = { ...entry.snapshot, ...snapshot };
        stages[currentIdx] = entry;
      }

      flow.stages = stages;
      return { activeFlow: flow };
    });
  },

  failCurrentStage: (error) => {
    set((state) => {
      if (!state.activeFlow) return state;

      const flow = { ...state.activeFlow };
      const stages = [...flow.stages];
      const currentIdx = stages.findIndex(
        (s) => s.stage === flow.currentStage && s.status === "active"
      );
      if (currentIdx >= 0) {
        const entry = { ...stages[currentIdx] };
        entry.status = "failed";
        entry.completedAt = now();
        entry.durationMs = new Date(entry.completedAt).getTime() - new Date(entry.enteredAt).getTime();
        entry.snapshot = { ...entry.snapshot, error };
        stages[currentIdx] = entry;
      }

      flow.stages = stages;
      flow.health = "failed";
      return { activeFlow: flow };
    });
  },

  attachRunResult: (result, runId) => {
    set((state) => {
      if (!state.activeFlow) return state;
      const flow = { ...state.activeFlow };
      flow.context = { ...flow.context, runResult: result, runId };
      return { activeFlow: flow };
    });
  },

  attachDecisions: (decisions) => {
    if (_inAttachDecisions) return;
    _inAttachDecisions = true;
    set((state) => {
      if (!state.activeFlow) return state;
      const flow = { ...state.activeFlow };
      flow.context = { ...flow.context, decisions };
      return { activeFlow: flow };
    });
    _inAttachDecisions = false;
  },

  attachOutcomes: (outcomes) => {
    if (_inAttachOutcomes) return;
    _inAttachOutcomes = true;
    set((state) => {
      if (!state.activeFlow) return state;
      const flow = { ...state.activeFlow };
      flow.context = { ...flow.context, outcomes };
      return { activeFlow: flow };
    });
    _inAttachOutcomes = false;
  },

  attachValues: (values) => {
    if (_inAttachValues) return;
    _inAttachValues = true;
    set((state) => {
      if (!state.activeFlow) return state;
      const flow = { ...state.activeFlow };
      flow.context = { ...flow.context, values };
      return { activeFlow: flow };
    });
    _inAttachValues = false;
  },

  completeFlow: () => {
    set((state) => {
      if (!state.activeFlow) return state;

      const flow = { ...state.activeFlow };

      // Complete any active stage
      const stages = [...flow.stages];
      const activeIdx = stages.findIndex((s) => s.status === "active");
      if (activeIdx >= 0) {
        const entry = { ...stages[activeIdx] };
        entry.status = "completed";
        entry.completedAt = now();
        entry.durationMs = new Date(entry.completedAt).getTime() - new Date(entry.enteredAt).getTime();
        stages[activeIdx] = entry;
      }

      // Ensure control_tower stage exists
      if (!stages.some((s) => s.stage === "control_tower")) {
        const ctEntry = createStageEntry("control_tower", {
          flowCompleted: true,
          totalStages: stages.length,
        });
        ctEntry.status = "completed";
        ctEntry.completedAt = now();
        ctEntry.durationMs = 0;
        stages.push(ctEntry);
      }

      flow.stages = stages;
      flow.currentStage = "control_tower";
      flow.isActive = false;

      // Archive to history
      const history = [flow, ...state.flowHistory].slice(0, state.maxHistory);

      return { activeFlow: flow, flowHistory: history };
    });
  },

  resetFlow: () => {
    set({ activeFlow: null });
  },

  // ── Selectors ──

  getFlowProgress: () => {
    const { activeFlow } = get();
    if (!activeFlow) return 0;
    const completedCount = activeFlow.stages.filter((s) => s.status === "completed").length;
    return Math.round((completedCount / FLOW_STAGES_ORDERED.length) * 100);
  },

  getCompletedStages: () => {
    const { activeFlow } = get();
    if (!activeFlow) return [];
    return activeFlow.stages.filter((s) => s.status === "completed");
  },

  isStageComplete: (stage) => {
    const { activeFlow } = get();
    if (!activeFlow) return false;
    return activeFlow.stages.some((s) => s.stage === stage && s.status === "completed");
  },

  getStageEntry: (stage) => {
    const { activeFlow } = get();
    if (!activeFlow) return null;
    return activeFlow.stages.find((s) => s.stage === stage) ?? null;
  },
}));
