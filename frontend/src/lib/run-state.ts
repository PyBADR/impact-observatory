/**
 * Impact Observatory | مرصد الأثر — Shared Run State
 *
 * Zustand store slice for cross-page run state synchronization.
 * All pages (Dashboard, Propagation, Map) share the same
 * latest run result so navigation doesn't lose context.
 *
 * Supports both UnifiedRunResult (graph pipeline) and RunResult (legacy).
 */

import { create } from "zustand";
import type { UnifiedRunResult, RunResult } from "@/types/observatory";
import { unifiedToRunResult } from "./unified-adapter";

export type RunSource = "unified" | "legacy" | "none";

interface RunState {
  /** Latest unified pipeline result (from POST /graph/unified-run) */
  unifiedResult: UnifiedRunResult | null;
  /** Latest legacy pipeline result (from POST /runs) */
  legacyResult: RunResult | null;
  /** Adapted result: unified → RunResult shape for Dashboard */
  adaptedResult: RunResult | null;
  /** Which pipeline produced the latest result */
  activeSource: RunSource;
  /** Currently selected scenario ID */
  scenarioId: string;
  /** Currently selected severity */
  severity: number;
  /** Loading state */
  isRunning: boolean;
  /** Error message if any */
  error: string | null;

  // Actions
  setUnifiedResult: (result: UnifiedRunResult) => void;
  setLegacyResult: (result: RunResult) => void;
  setScenario: (scenarioId: string, severity?: number) => void;
  setRunning: (running: boolean) => void;
  setError: (error: string | null) => void;
  clear: () => void;

  /** Get the RunResult for Dashboard (prefers unified → adapted, falls back to legacy) */
  getRunResult: () => RunResult | null;
}

export const useRunState = create<RunState>((set, get) => ({
  unifiedResult: null,
  legacyResult: null,
  adaptedResult: null,
  activeSource: "none",
  scenarioId: "",
  severity: 0.7,
  isRunning: false,
  error: null,

  setUnifiedResult: (result) => {
    // Adapt unified → RunResult for Dashboard
    let adapted: RunResult | null = null;
    try {
      adapted = unifiedToRunResult(result as any);
    } catch (e) {
      console.warn("[run-state] Failed to adapt unified result:", e);
    }
    // Handle both v4 (template_id) and v2 (scenario_id) schemas
    const u = result as unknown as Record<string, unknown>;
    const rawScenario = (result.scenario ?? {}) as Record<string, unknown>;
    const scenarioId =
      (rawScenario.template_id as string)
      ?? (rawScenario.scenario_id as string)
      ?? (u.scenario_id as string)
      ?? "";
    const severity = (rawScenario.severity as number) ?? (u.severity as number) ?? 0.7;
    set({
      unifiedResult: result,
      adaptedResult: adapted,
      activeSource: "unified",
      scenarioId,
      severity,
      isRunning: false,
      error: null,
    });
  },

  setLegacyResult: (result) => {
    set({
      legacyResult: result,
      activeSource: "legacy",
      scenarioId: result.scenario.template_id,
      severity: result.scenario.severity,
      isRunning: false,
      error: null,
    });
  },

  setScenario: (scenarioId, severity) => {
    set({
      scenarioId,
      ...(severity !== undefined ? { severity } : {}),
    });
  },

  setRunning: (running) => set({ isRunning: running, error: null }),
  setError: (error) => set({ error, isRunning: false }),
  clear: () =>
    set({
      unifiedResult: null,
      legacyResult: null,
      adaptedResult: null,
      activeSource: "none",
      isRunning: false,
      error: null,
    }),

  getRunResult: () => {
    const state = get();
    if (state.activeSource === "unified") return state.adaptedResult;
    if (state.activeSource === "legacy") return state.legacyResult;
    return null;
  },
}));
