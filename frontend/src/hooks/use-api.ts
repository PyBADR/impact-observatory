"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioResult } from "@/types";

// ---- Events ----
export function useEvents(params?: { limit?: number; severity_min?: number; event_type?: string }) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: () => api.events(params),
    refetchInterval: 30_000,
  });
}

// ---- Flights ----
export function useFlights(params?: { limit?: number; status?: string }) {
  return useQuery({
    queryKey: ["flights", params],
    queryFn: () => api.flights(params),
    refetchInterval: 15_000,
  });
}

// ---- Vessels ----
export function useVessels(params?: { limit?: number; vessel_type?: string }) {
  return useQuery({
    queryKey: ["vessels", params],
    queryFn: () => api.vessels(params),
    refetchInterval: 15_000,
  });
}

// ---- Scenario Templates ----
export function useScenarioTemplates() {
  return useQuery({
    queryKey: ["scenario-templates"],
    queryFn: () => api.scenarioTemplates(),
    staleTime: 60_000,
  });
}

// ---- Run Scenario (Mutation) ----
export function useRunScenario(onSuccess?: (data: ScenarioResult) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { scenario_id?: string; severity_override?: number; horizon_hours?: number }) =>
      api.scenarioRun(params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["system-stress"] });
      onSuccess?.(data);
    },
  });
}

// ---- Risk Scores ----
export function useRiskScores(params?: { sector?: string; region?: string; limit?: number }) {
  return useQuery({
    queryKey: ["risk-scores", params],
    queryFn: () => api.riskScores(params),
  });
}

// ---- System Stress ----
export function useSystemStress() {
  return useQuery({
    queryKey: ["system-stress"],
    queryFn: () => api.systemStress(),
    refetchInterval: 30_000,
  });
}

// ---- Insurance Exposure ----
export function useInsuranceExposure(params?: { sector?: string; region?: string }) {
  return useQuery({
    queryKey: ["insurance-exposure", params],
    queryFn: () => api.insuranceExposure(params),
  });
}

// ---- Claims Surge ----
export function useClaimsSurge(scenarioId: string | null) {
  return useQuery({
    queryKey: ["claims-surge", scenarioId],
    queryFn: () => api.claimsSurge(scenarioId!),
    enabled: !!scenarioId,
  });
}

// ---- Underwriting Watch ----
export function useUnderwritingWatch(params?: { watch_level?: string }) {
  return useQuery({
    queryKey: ["underwriting", params],
    queryFn: () => api.underwritingWatch(params),
  });
}

// ---- Severity Projection ----
export function useSeverityProjection(scenarioId: string | null, horizonHours?: number) {
  return useQuery({
    queryKey: ["severity-projection", scenarioId, horizonHours],
    queryFn: () => api.severityProjection(scenarioId!, horizonHours),
    enabled: !!scenarioId,
  });
}

// ---- Decision Output ----
export function useDecisionOutput(scenarioId: string | null) {
  return useQuery({
    queryKey: ["decision-output", scenarioId],
    queryFn: () => api.decisionOutput(scenarioId!),
    enabled: !!scenarioId,
  });
}

// ---- Graph Nodes ----
export function useGraphNodes(params?: { sector?: string; limit?: number }) {
  return useQuery({
    queryKey: ["graph-nodes", params],
    queryFn: () => api.graphNodes(params),
  });
}

// ---- Graph Chokepoints ----
export function useGraphChokepoints() {
  return useQuery({
    queryKey: ["graph-chokepoints"],
    queryFn: () => api.graphChokepoints(),
  });
}

// ---- Entity Detail ----
export function useEntityDetail(entityId: string | null) {
  return useQuery({
    queryKey: ["entity-detail", entityId],
    queryFn: () => api.entityDetail(entityId!),
    enabled: !!entityId,
  });
}

// ---- Runs List (history) ----
export function useRunsList(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["runs-list", params],
    queryFn: () => api.runsList(params),
    staleTime: 5_000,
    refetchInterval: 15_000,
  });
}

// ---- Run History (alias with observatory API) ----
export function useRunHistory(limit = 20) {
  return useQuery({
    queryKey: ["run-history", limit],
    queryFn: () => api.observatory.listRuns({ limit }),
    staleTime: 5_000,
    refetchInterval: 15_000,
  });
}

// ---- Single Run Result ----
export function useRunResult(runId: string | null) {
  return useQuery({
    queryKey: ["run-result", runId],
    queryFn: () => api.observatory.getResult(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

// ---- GCC Node Registry (static — stale-time = Infinity) ----
export function useGccNodes() {
  return useQuery({
    queryKey: ["gcc-nodes"],
    queryFn: () => api.observatory.nodes(),
    staleTime: Infinity, // nodes never change
  });
}

// ================================================================
// Impact Observatory v1 Hooks
// ================================================================

/** Run a scenario through the full 17-stage pipeline */
export function useObservatoryRun(
  onSuccess?: (data: import("@/types/observatory").RunResult) => void
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: import("@/types/observatory").ScenarioCreate) =>
      api.observatory.run(params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["runs-list"] });
      queryClient.invalidateQueries({ queryKey: ["run-history"] });
      onSuccess?.(data);
    },
  });
}

/** Get scenario templates from v1 API */
export function useObservatoryTemplates() {
  return useQuery({
    queryKey: ["observatory-templates"],
    queryFn: () => api.observatory.templates(),
    staleTime: 60_000,
  });
}

/** Get decision plan for a specific run */
export function useDecisionPlan(runId: string | null) {
  return useQuery({
    queryKey: ["decision-plan", runId],
    queryFn: () => api.observatory.decision(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get explanation pack for a specific run */
export function useExplanationPack(runId: string | null) {
  return useQuery({
    queryKey: ["explanation-pack", runId],
    queryFn: () => api.observatory.explanation(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get banking stress for a specific run */
export function useBankingStress(runId: string | null) {
  return useQuery({
    queryKey: ["banking-stress", runId],
    queryFn: () => api.observatory.banking(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get insurance stress for a specific run */
export function useInsuranceStress(runId: string | null) {
  return useQuery({
    queryKey: ["insurance-stress", runId],
    queryFn: () => api.observatory.insurance(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get fintech stress for a specific run */
export function useFintechStress(runId: string | null) {
  return useQuery({
    queryKey: ["fintech-stress", runId],
    queryFn: () => api.observatory.fintech(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get financial impacts for a specific run */
export function useFinancialImpacts(runId: string | null) {
  return useQuery({
    queryKey: ["financial-impacts", runId],
    queryFn: () => api.observatory.financial(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get map payload — geo-located entities + propagation arcs */
export function useMapPayload(runId: string | null) {
  return useQuery({
    queryKey: ["map-payload", runId],
    queryFn: () => api.observatory.mapPayload(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get graph payload — nodes + edges for graph visualization */
export function useGraphPayload(runId: string | null) {
  return useQuery({
    queryKey: ["graph-payload", runId],
    queryFn: () => api.observatory.graphPayload(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

/** Get system status — all connectors + engine health */
export function useSystemStatus() {
  return useQuery({
    queryKey: ["system-status"],
    queryFn: () => api.observatory.systemStatus(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}
