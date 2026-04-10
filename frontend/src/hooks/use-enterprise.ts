"use client";
/**
 * Impact Observatory | مرصد الأثر — Enterprise Intelligence Hooks
 * Layer: UI (L6) — Data fetching for Enterprise Decision Intelligence views
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Keys ──
const KEYS = {
  scenarios: ["enterprise", "scenarios"] as const,
  runs: (params?: Record<string, string>) => ["enterprise", "runs", params] as const,
  run: (id: string) => ["enterprise", "run", id] as const,
  decisions: (params?: Record<string, string>) => ["enterprise", "decisions", params] as const,
  decision: (id: string) => ["enterprise", "decision", id] as const,
  outcomes: (params?: Record<string, string>) => ["enterprise", "outcomes", params] as const,
  authority: (params?: Record<string, string>) => ["enterprise", "authority", params] as const,
  authorityMetrics: ["enterprise", "authority", "metrics"] as const,
  authorityEvents: (id: string) => ["enterprise", "authority", "events", id] as const,
  authorityVerify: (id: string) => ["enterprise", "authority", "verify", id] as const,
  values: (params?: Record<string, string>) => ["enterprise", "values", params] as const,
  health: ["enterprise", "health"] as const,
};

// ── Scenario Intelligence ──
export function useScenarioCatalog() {
  return useQuery({
    queryKey: KEYS.scenarios,
    queryFn: () => api.observatory.scenarios(),
    staleTime: 5 * 60_000, // Scenarios rarely change
  });
}

export function useSimulateScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: { template_id: string; severity?: number; horizon_hours?: number; label?: string }) =>
      api.observatory.run(params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["enterprise", "runs"] });
    },
  });
}

export function useRunResult(runId: string | null) {
  return useQuery({
    queryKey: KEYS.run(runId ?? ""),
    queryFn: () => api.observatory.result(runId!),
    enabled: !!runId,
    staleTime: 30_000,
  });
}

// ── Decision Intelligence ──
export function useDecisions(params?: { status?: string; decision_type?: string; run_id?: string; limit?: number }) {
  return useQuery({
    queryKey: KEYS.decisions(params as Record<string, string> | undefined),
    queryFn: () => api.decisions.list(params),
    refetchInterval: 20_000, // Live polling
  });
}

export function useDecisionDetail(decisionId: string | null) {
  return useQuery({
    queryKey: KEYS.decision(decisionId ?? ""),
    queryFn: () => api.decisions.get(decisionId!),
    enabled: !!decisionId,
  });
}

export function useCreateDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof api.decisions.create>[0]) => api.decisions.create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["enterprise", "decisions"] }),
  });
}

export function useExecuteDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body?: Parameters<typeof api.decisions.execute>[1] }) =>
      api.decisions.execute(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["enterprise", "decisions"] }),
  });
}

// ── Authority / Governance Intelligence ──
export function useAuthorityMetrics() {
  return useQuery({
    queryKey: KEYS.authorityMetrics,
    queryFn: () => api.authority.metrics(),
    refetchInterval: 15_000,
  });
}

export function useAuthorityEnvelopes(params?: { status?: string; limit?: number }) {
  return useQuery({
    queryKey: KEYS.authority(params as Record<string, string> | undefined),
    queryFn: () => api.authority.list(params),
    refetchInterval: 15_000,
  });
}

export function useAuthorityEvents(decisionId: string | null) {
  return useQuery({
    queryKey: KEYS.authorityEvents(decisionId ?? ""),
    queryFn: () => api.authority.events(decisionId!, 50),
    enabled: !!decisionId,
  });
}

export function useAuthorityVerify(decisionId: string | null) {
  return useQuery({
    queryKey: KEYS.authorityVerify(decisionId ?? ""),
    queryFn: () => api.authority.verify(decisionId!),
    enabled: !!decisionId,
    staleTime: 60_000,
  });
}

// ── Outcome Intelligence ──
export function useOutcomes(params?: { decision_id?: string; run_id?: string; status?: string; limit?: number }) {
  return useQuery({
    queryKey: KEYS.outcomes(params as Record<string, string> | undefined),
    queryFn: () => api.outcomes.list(params),
    refetchInterval: 30_000,
  });
}

// ── Value / ROI Intelligence ──
export function useValues(params?: { outcome_id?: string; decision_id?: string; run_id?: string; limit?: number }) {
  return useQuery({
    queryKey: KEYS.values(params as Record<string, string> | undefined),
    queryFn: () => api.values.list(params),
    refetchInterval: 30_000,
  });
}

export function useComputeValue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof api.values.compute>[0]) => api.values.compute(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["enterprise", "values"] }),
  });
}

// ── Health ──
export function useHealthCheck() {
  return useQuery({
    queryKey: KEYS.health,
    queryFn: () => api.health(),
    refetchInterval: 60_000,
  });
}

export { KEYS as ENTERPRISE_QUERY_KEYS };
