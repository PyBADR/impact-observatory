"use client";

/**
 * TraceImpact Scenario Context
 *
 * Single source of truth for all trace-impact steps.
 * Steps read activeScenario via useTraceImpactScenario() instead of
 * importing demoScenario directly — enabling scenario switching without
 * touching individual step files.
 */

import { createContext, useContext } from "react";
import { demoScenario, getScenario, type Scenario, type ScenarioId } from "@/features/demo/data/demo-scenario";

const TraceImpactContext = createContext<Scenario>(demoScenario);

export function TraceImpactProvider({
  children,
  scenarioId,
}: {
  children: React.ReactNode;
  scenarioId?: ScenarioId | null;
}) {
  const scenario = scenarioId ? getScenario(scenarioId) : demoScenario;
  return (
    <TraceImpactContext.Provider value={scenario}>
      {children}
    </TraceImpactContext.Provider>
  );
}

/** Hook for all trace-impact steps to read the active scenario */
export function useTraceImpactScenario(): Scenario {
  return useContext(TraceImpactContext);
}
