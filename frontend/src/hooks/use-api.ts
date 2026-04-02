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
