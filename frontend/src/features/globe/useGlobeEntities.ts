"use client";

import { useState, useEffect, useCallback } from "react";
import { graphClient } from "@/lib/graph-client";
import { useRunState } from "@/lib/run-state";
import type {
  ImpactedEntity,
  UnifiedRunResult,
  GraphScenarioTemplate,
} from "@/types/observatory";

export interface GlobeState {
  entities: ImpactedEntity[];
  runResult: UnifiedRunResult | null;
  scenarios: GraphScenarioTemplate[];
  loading: boolean;
  scenariosLoading: boolean;
  /**
   * Explicit capability flag for geospatial rendering.
   * False until a run completes WITH map_payload.impacted_entities present.
   * Pages MUST check this before attempting to render EntityLayer.
   */
  mapSupported: boolean;
  /** Hard fetch/network error — distinct from capability limitations */
  error: string | null;
}

export function useGlobeEntities() {
  const [state, setState] = useState<GlobeState>({
    entities: [],
    runResult: null,
    scenarios: [],
    loading: false,
    scenariosLoading: false,
    mapSupported: false,
    error: null,
  });

  // On mount: hydrate from dashboard run-state if a scenario was already run.
  // Also subscribes to future dashboard runs so navigating to this page
  // after a dashboard run immediately shows the map without re-running.
  useEffect(() => {
    function hydrateFromRunState(unifiedResult: UnifiedRunResult | null) {
      if (!unifiedResult) return;
      const entities: ImpactedEntity[] = unifiedResult.map_payload?.impacted_entities ?? [];
      if (entities.length === 0) return;

      setState((s) => {
        // Don't overwrite an in-progress or already-populated run
        if (s.entities.length > 0 || s.loading) return s;
        return {
          ...s,
          entities,
          runResult: unifiedResult,
          mapSupported: true,
        };
      });
    }

    // Hydrate immediately from any run that completed before this page mounted
    hydrateFromRunState(useRunState.getState().unifiedResult);

    // Subscribe for live updates when the dashboard runs a new scenario
    const unsub = useRunState.subscribe((state, prevState) => {
      if (state.unifiedResult !== prevState.unifiedResult) {
        hydrateFromRunState(state.unifiedResult);
      }
    });

    return () => { unsub(); };
  }, []);

  // Load available scenarios — falls back to /api/v1/scenarios via graphClient.scenarios()
  const loadScenarios = useCallback(async () => {
    setState((s) => ({ ...s, scenariosLoading: true, error: null }));
    try {
      const res = await graphClient.scenarios();
      setState((s) => ({ ...s, scenarios: res.scenarios, scenariosLoading: false }));
    } catch (err) {
      // Non-fatal: scenarios list unavailable; map will show empty selector
      setState((s) => ({
        ...s,
        scenariosLoading: false,
        // Only surface error if no scenarios loaded at all
        error: s.scenarios.length === 0
          ? err instanceof Error ? err.message : "Failed to load scenarios"
          : s.error,
      }));
    }
  }, []);

  // Run analysis via POST /runs — populates mapSupported based on result payload
  const runScenario = useCallback(
    async (templateId: string, severity = 0.7, horizonHours = 168) => {
      setState((s) => ({ ...s, loading: true, error: null, mapSupported: false }));
      try {
        const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";
        const headers = {
          "Content-Type": "application/json",
          "X-IO-API-Key": API_KEY,
        };

        // POST /runs — send both template_id (v4) and scenario_id (legacy)
        const postRes = await fetch("/api/v1/runs", {
          method: "POST",
          headers,
          body: JSON.stringify({
            template_id: templateId,
            severity,
            horizon_hours: horizonHours,
          }),
        });
        if (!postRes.ok) {
          throw new Error(
            postRes.status >= 500
              ? "The analysis service is temporarily unavailable."
              : `Scenario run failed (${postRes.status})`
          );
        }
        const postData = await postRes.json();

        // Handle both v4 envelope ({ data: { run_id } }) and legacy direct ({ run_id })
        const runMeta: Record<string, unknown> = postData?.data ?? postData ?? {};
        const runId = (runMeta.run_id as string) ?? "";
        if (!runId) throw new Error("Backend did not return a run ID.");

        // GET /runs/{id} → full result
        const getRes = await fetch(`/api/v1/runs/${runId}`, { headers });
        if (!getRes.ok) throw new Error("Failed to retrieve run result.");
        const getData = await getRes.json();

        // Handle both v4 envelope ({ data: UnifiedRunResult }) and legacy direct
        const rawResult: Record<string, unknown> = getData?.data ?? getData ?? {};
        const result = rawResult as unknown as UnifiedRunResult;

        // Capability gating: map is only supported when geospatial entities are present.
        // v2 backend returns no map_payload — this is a structural capability limitation,
        // not a failure. mapSupported = false is the correct and expected state.
        const entities: ImpactedEntity[] = result.map_payload?.impacted_entities ?? [];
        const mapSupported = entities.length > 0;

        setState((s) => ({
          ...s,
          runResult: result,
          entities,
          mapSupported,
          loading: false,
          // No error — absent map_payload is a capability limitation, not a failure
        }));

        // Store in shared state for cross-page sync (Dashboard, etc.)
        useRunState.getState().setUnifiedResult(result);
        return result;
      } catch (err) {
        setState((s) => ({
          ...s,
          loading: false,
          error: err instanceof Error ? err.message : "Pipeline run failed",
        }));
        return null;
      }
    },
    []
  );

  const clearRun = useCallback(() => {
    setState((s) => ({
      ...s,
      entities: [],
      runResult: null,
      mapSupported: false,
      error: null,
    }));
  }, []);

  return { ...state, loadScenarios, runScenario, clearRun };
}
