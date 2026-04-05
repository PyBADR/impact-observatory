"use client";

import { useState, useCallback } from "react";
import { graphClient } from "@/lib/graph-client";
import { api } from "@/lib/api";
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
  error: string | null;
}

export function useGlobeEntities() {
  const [state, setState] = useState<GlobeState>({
    entities: [],
    runResult: null,
    scenarios: [],
    loading: false,
    scenariosLoading: false,
    error: null,
  });

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

  // Run unified pipeline via canonical POST /runs → GET /runs/{id}
  const runScenario = useCallback(
    async (templateId: string, severity = 0.7, horizonHours = 168) => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";
        const headers = {
          "Content-Type": "application/json",
          "X-IO-API-Key": API_KEY,
        };

        // 1. POST /runs — send both template_id (v4) and scenario_id (legacy)
        const postRes = await fetch("/api/v1/runs", {
          method: "POST",
          headers,
          body: JSON.stringify({
            template_id: templateId,
            scenario_id: templateId,
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

        // 2. GET /runs/{id} → Full result (both backends support this)
        const getRes = await fetch(`/api/v1/runs/${runId}`, { headers });
        if (!getRes.ok) throw new Error("Failed to retrieve run result.");
        const getData = await getRes.json();

        // Handle both v4 envelope ({ data: UnifiedRunResult }) and legacy direct
        const rawResult: Record<string, unknown> = getData?.data ?? getData ?? {};

        // Derive typed UnifiedRunResult — works for both v4 and v2 schemas
        const result = rawResult as unknown as UnifiedRunResult;

        // Build impacted entities for the map.
        // v4: map_payload.impacted_entities (with lat/lng)
        // v2: top_impacted_entities is just node ID strings — no geolocation available.
        let entities: ImpactedEntity[] = result.map_payload?.impacted_entities ?? [];
        if (entities.length === 0) {
          // Typed capability state: map data unavailable for this backend version
          // Surface the information but don't block the result
          console.info(
            "[map] map_payload absent — geospatial layer unavailable for this backend schema"
          );
        }

        setState((s) => ({
          ...s,
          runResult: result,
          entities,
          loading: false,
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
    setState((s) => ({ ...s, entities: [], runResult: null }));
  }, []);

  return { ...state, loadScenarios, runScenario, clearRun };
}
