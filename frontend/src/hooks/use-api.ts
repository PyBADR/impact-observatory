"use client";

import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAppStore } from "@/store/app-store";
import { filterValidDecisions, filterValidOutcomes, filterValidValues } from "@/lib/graph-contracts";
import type { WsSignalEvent } from "@/types/observatory";

// ============================================================================
// Impact Observatory — Unified Pipeline Hooks
// 3 endpoints: POST /runs, GET /runs/{id}, GET /runs/{id}/status
// ============================================================================

/**
 * Launch a pipeline run against a scenario/template.
 * POST /api/v1/runs → 202
 */
export function useObservatoryRun(
  onSuccess?: (data: Record<string, unknown>) => void,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { template_id: string; severity?: number; horizon_hours?: number }) =>
      api.observatory.run(params),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["observatory"] });
      onSuccess?.(data.data as Record<string, unknown>);
    },
  });
}

/**
 * Poll run status.
 * GET /api/v1/runs/{id}/status
 */
export function useRunStatus(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "status", runId],
    queryFn: () => api.observatory.status(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.data?.status;
      return status === "completed" || status === "failed" ? false : 2000;
    },
  });
}

/**
 * Fetch full UnifiedRunResult.
 * GET /api/v1/runs/{id}
 */
export function useRunResult(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "result", runId],
    queryFn: () => api.observatory.result(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

// ============================================================================
// Phase 1 Execution Engine Hooks — Transmission, Counterfactual, Action Pathways
// ============================================================================

/**
 * Fetch transmission chain for a completed run.
 * GET /api/v1/runs/{id}/transmission
 */
export function useTransmissionChain(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "transmission", runId],
    queryFn: () => api.observatory.transmission(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch calibrated counterfactual for a completed run.
 * GET /api/v1/runs/{id}/counterfactual
 */
export function useCounterfactual(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "counterfactual", runId],
    queryFn: () => api.observatory.counterfactual(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch classified action pathways for a completed run.
 * GET /api/v1/runs/{id}/action-pathways
 */
export function useActionPathways(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "action-pathways", runId],
    queryFn: () => api.observatory.actionPathways(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch decision trust payload for a completed run.
 * GET /api/v1/runs/{id}/decision-trust
 */
export function useDecisionTrust(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "decision-trust", runId],
    queryFn: () => api.observatory.decisionTrust(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch decision integration payload for a completed run.
 * GET /api/v1/runs/{id}/decision-integration
 */
export function useDecisionIntegration(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "decision-integration", runId],
    queryFn: () => api.observatory.decisionIntegration(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch decision value payload for a completed run (Phase 4).
 * GET /api/v1/runs/{id}/decision-value
 */
export function useDecisionValuePayload(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "decision-value", runId],
    queryFn: () => api.observatory.decisionValue(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch governance payload for a completed run (Phase 5).
 * GET /api/v1/runs/{id}/governance
 */
export function useGovernance(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "governance", runId],
    queryFn: () => api.observatory.governance(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

/**
 * Fetch pilot payload for a completed run (Phase 6).
 * GET /api/v1/runs/{id}/pilot
 */
export function usePilotPayload(runId: string | null) {
  return useQuery({
    queryKey: ["observatory", "pilot", runId],
    queryFn: () => api.observatory.pilot(runId!),
    enabled: !!runId,
    staleTime: Infinity,
  });
}

// ============================================================================
// Live Signal Layer hooks
// ============================================================================

/**
 * WebSocket client for the /ws/signals stream with exponential backoff reconnect.
 *
 * Event routing:
 *   signal.scored → store.addLiveSignal(data)
 *   seed.pending  → invalidate "pending-seeds" query
 *   seed.approved → store.removePendingSeed + invalidate runs-list
 *   seed.rejected → store.removePendingSeed + invalidate pending-seeds
 *
 * Resilience:
 *   - Reconnects up to MAX_RETRIES times on unexpected close
 *   - Delay doubles each attempt: 1s → 2s → 4s → 8s → 16s
 *   - Deliberate close (unmount) does NOT trigger reconnect
 *   - After exhausting retries, logs once and stops (no infinite loops)
 */
export function useSignalStream(wsBaseUrl?: string): void {
  const addLiveSignal     = useAppStore((s) => s.addLiveSignal);
  const removePendingSeed = useAppStore((s) => s.removePendingSeed);
  const queryClient       = useQueryClient();

  useEffect(() => {
    const apiBase =
      wsBaseUrl ??
      (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
    const wsBase = apiBase.replace(/^http/, "ws");
    const url    = `${wsBase}/ws/signals`;

    const MAX_RETRIES   = 5;
    const BASE_DELAY_MS = 1_000;

    let ws:          WebSocket | null = null;
    let retries      = 0;
    let retryTimer:  ReturnType<typeof setTimeout> | null = null;
    let cancelled    = false;

    function handleMessage(e: MessageEvent): void {
      let parsed: WsSignalEvent;
      try {
        parsed = JSON.parse(e.data as string) as WsSignalEvent;
      } catch {
        return; // malformed frame — ignore
      }

      if (parsed.event === "signal.scored") {
        addLiveSignal(parsed.data);
      } else if (parsed.event === "seed.pending") {
        queryClient.invalidateQueries({ queryKey: ["pending-seeds"] });
      } else if (parsed.event === "seed.approved") {
        removePendingSeed(parsed.data.seed_id);
        queryClient.invalidateQueries({ queryKey: ["runs-list"] });
        queryClient.invalidateQueries({ queryKey: ["pending-seeds"] });
      } else if (parsed.event === "seed.rejected") {
        removePendingSeed(parsed.data.seed_id);
        queryClient.invalidateQueries({ queryKey: ["pending-seeds"] });
      }
    }

    function connect(): void {
      if (cancelled) return;

      try {
        ws = new WebSocket(url);
      } catch {
        // WebSocket unavailable (SSR, test env) — do not retry
        return;
      }

      ws.onopen = () => {
        retries = 0; // successful connection resets the backoff counter
      };

      ws.onmessage = handleMessage;

      ws.onerror = () => {
        // onclose fires after onerror — reconnect logic lives there
      };

      ws.onclose = (e: CloseEvent) => {
        if (cancelled) return;                 // deliberate unmount — do not reconnect
        if (e.code === 1000) return;           // server sent normal closure — do not reconnect
        if (retries >= MAX_RETRIES) {
          console.warn(
            `[SignalStream] WebSocket ${url} closed after ${MAX_RETRIES} reconnect attempts. Giving up.`
          );
          return;
        }
        const delay = BASE_DELAY_MS * Math.pow(2, retries);
        retries++;
        console.info(
          `[SignalStream] WebSocket closed (code=${e.code}). Reconnecting in ${delay}ms (attempt ${retries}/${MAX_RETRIES})...`
        );
        retryTimer = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (retryTimer !== null) {
        clearTimeout(retryTimer);
        retryTimer = null;
      }
      if (ws) {
        ws.close(1000, "component unmounted");
        ws = null;
      }
    };
  }, [wsBaseUrl, addLiveSignal, removePendingSeed, queryClient]);
}

/**
 * Polls GET /api/v1/signals/pending every 15 s and syncs into the Zustand store.
 * Also re-fetches on WS seed.pending / seed.approved / seed.rejected invalidations.
 */
export function usePendingSeeds() {
  const setPendingSeeds = useAppStore((s) => s.setPendingSeeds);
  const query = useQuery({
    queryKey: ["pending-seeds"],
    queryFn: () => api.signals.listPending(),
    staleTime: 10_000,
    refetchInterval: 15_000,
  });

  useEffect(() => {
    if (query.data) {
      setPendingSeeds(query.data.seeds);
    }
  }, [query.data, setPendingSeeds]);

  return query;
}

/**
 * Submit a raw signal to POST /api/v1/signals.
 * Returns IngestSignalResponse (202) with a PENDING_REVIEW seed.
 * Does NOT trigger the pipeline — seed requires explicit HITL approval.
 */
export function useIngestSignal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (raw: Record<string, unknown>) => api.signals.ingest(raw),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-seeds"] });
    },
  });
}

/**
 * Approve a pending ScenarioSeed (CRO / ADMIN only).
 * Triggers the pipeline synchronously inside hitl.approve() on the backend.
 */
export function useApproveSeed() {
  const removePendingSeed = useAppStore((s) => s.removePendingSeed);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ seedId, reason, reviewedBy }: { seedId: string; reason?: string; reviewedBy?: string }) =>
      api.signals.approve(seedId, reason, reviewedBy),
    onSuccess: (_, { seedId }) => {
      removePendingSeed(seedId);
      queryClient.invalidateQueries({ queryKey: ["pending-seeds"] });
      queryClient.invalidateQueries({ queryKey: ["runs-list"] });
    },
  });
}

// ============================================================================
// Operator Layer — Decision hooks
// ============================================================================

/**
 * List OperatorDecisions, optionally filtered by status, type, and/or run_id.
 * GET /api/v1/decisions
 *
 * When called with no params (app-level), syncs result into the Zustand
 * operatorDecisions slice so all persona views receive decision data from
 * the store. Pattern mirrors useOutcomes / usePendingSeeds.
 */
export function useDecisions(params?: { status?: string; decision_type?: string; run_id?: string; limit?: number }) {
  const setOperatorDecisions = useAppStore((s) => s.setOperatorDecisions);
  const query = useQuery({
    queryKey: ["decisions", params],
    queryFn: () => api.decisions.list(params),
    staleTime: 10_000,
    refetchInterval: 20_000,
  });

  // Sync into store only for top-level (unfiltered) fetches.
  // Limited / filtered calls (e.g. existence-check {limit:1}) must not
  // clobber the full list. Pattern mirrors useOutcomes.
  // Contract enforcement: drop orphan decisions before writing to store.
  useEffect(() => {
    if (!params && query.data) {
      setOperatorDecisions(filterValidDecisions(query.data.decisions));
    }
  }, [params, query.data, setOperatorDecisions]);

  return query;
}

/**
 * Get a single OperatorDecision by ID.
 * GET /api/v1/decisions/{id}
 */
export function useDecision(decisionId: string | null) {
  return useQuery({
    queryKey: ["decision", decisionId],
    queryFn: () => api.decisions.get(decisionId!),
    enabled: !!decisionId,
    staleTime: 10_000,
  });
}

/**
 * Create a new OperatorDecision.
 * POST /api/v1/decisions
 */
export function useCreateDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: import("@/types/observatory").CreateDecisionRequest) =>
      api.decisions.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
    },
  });
}

/**
 * Execute an OperatorDecision (OPERATOR+ only).
 * POST /api/v1/decisions/{id}/execute
 */
export function useExecuteDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      decisionId,
      body,
    }: {
      decisionId: string;
      body?: import("@/types/observatory").ExecuteDecisionRequest;
    }) => api.decisions.execute(decisionId, body),
    onSuccess: (_, { decisionId }) => {
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      queryClient.invalidateQueries({ queryKey: ["decision", decisionId] });
      // Executing TRIGGER_RUN creates a new run — invalidate runs list
      queryClient.invalidateQueries({ queryKey: ["observatory"] });
    },
  });
}

/**
 * Close an OperatorDecision (OPERATOR+ only).
 * POST /api/v1/decisions/{id}/close
 */
export function useCloseDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      decisionId,
      body,
    }: {
      decisionId: string;
      body?: import("@/types/observatory").CloseDecisionRequest;
    }) => api.decisions.close(decisionId, body),
    onSuccess: (_, { decisionId }) => {
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      queryClient.invalidateQueries({ queryKey: ["decision", decisionId] });
    },
  });
}

// ============================================================================
// Outcome Intelligence Layer hooks
// ============================================================================

/**
 * List Outcomes, optionally filtered by decision_id, run_id, or status.
 * GET /api/v1/outcomes
 *
 * When called with no params (app-level), syncs result into the Zustand
 * outcomes slice so all persona views receive outcome data from the store.
 * Pattern mirrors usePendingSeeds.
 */
export function useOutcomes(params?: { decision_id?: string; run_id?: string; status?: string; limit?: number }) {
  const setOutcomes        = useAppStore((s) => s.setOutcomes);
  const operatorDecisions  = useAppStore((s) => s.operatorDecisions);
  const query = useQuery({
    queryKey: ["outcomes", params],
    queryFn: () => api.outcomes.list(params),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });

  // Sync into store only for top-level (unfiltered) fetches.
  // Filtered calls (e.g. by decision_id or run_id) must not clobber the full list.
  // Contract enforcement: drop outcomes whose parent decision is not in the store.
  useEffect(() => {
    if (!params && query.data) {
      setOutcomes(filterValidOutcomes(query.data.outcomes, operatorDecisions));
    }
  }, [params, query.data, setOutcomes, operatorDecisions]);

  return query;
}

/**
 * Get a single Outcome by ID.
 * GET /api/v1/outcomes/{id}
 */
export function useOutcome(outcomeId: string | null) {
  return useQuery({
    queryKey: ["outcome", outcomeId],
    queryFn:  () => api.outcomes.get(outcomeId!),
    enabled:  !!outcomeId,
    staleTime: 15_000,
  });
}

/**
 * Record a new Outcome entity.
 * POST /api/v1/outcomes
 */
export function useCreateOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: import("@/types/observatory").CreateOutcomeRequest) =>
      api.outcomes.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["outcomes"] });
    },
  });
}

/**
 * Observe an outcome — PENDING_OBSERVATION → OBSERVED.
 * POST /api/v1/outcomes/{id}/observe
 */
export function useObserveOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ outcomeId, body }: {
      outcomeId: string;
      body?: import("@/types/observatory").ObserveOutcomeRequest;
    }) => api.outcomes.observe(outcomeId, body),
    onSuccess: (_, { outcomeId }) => {
      queryClient.invalidateQueries({ queryKey: ["outcomes"] });
      queryClient.invalidateQueries({ queryKey: ["outcome", outcomeId] });
    },
  });
}

/**
 * Confirm an outcome with classification — OBSERVED/DISPUTED → CONFIRMED.
 * POST /api/v1/outcomes/{id}/confirm
 */
export function useConfirmOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ outcomeId, body }: {
      outcomeId: string;
      body: import("@/types/observatory").ConfirmOutcomeRequest;
    }) => api.outcomes.confirm(outcomeId, body),
    onSuccess: (_, { outcomeId }) => {
      queryClient.invalidateQueries({ queryKey: ["outcomes"] });
      queryClient.invalidateQueries({ queryKey: ["outcome", outcomeId] });
    },
  });
}

/**
 * Dispute an outcome — OBSERVED → DISPUTED.
 * POST /api/v1/outcomes/{id}/dispute
 */
export function useDisputeOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ outcomeId, body }: {
      outcomeId: string;
      body: import("@/types/observatory").DisputeOutcomeRequest;
    }) => api.outcomes.dispute(outcomeId, body),
    onSuccess: (_, { outcomeId }) => {
      queryClient.invalidateQueries({ queryKey: ["outcomes"] });
      queryClient.invalidateQueries({ queryKey: ["outcome", outcomeId] });
    },
  });
}

/**
 * Close an outcome (terminal state).
 * POST /api/v1/outcomes/{id}/close
 */
export function useCloseOutcome() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ outcomeId, body }: {
      outcomeId: string;
      body?: import("@/types/observatory").CloseOutcomeRequest;
    }) => api.outcomes.close(outcomeId, body),
    onSuccess: (_, { outcomeId }) => {
      queryClient.invalidateQueries({ queryKey: ["outcomes"] });
      queryClient.invalidateQueries({ queryKey: ["outcome", outcomeId] });
    },
  });
}

// ============================================================================
// ROI / Decision Value Layer hooks
// ============================================================================

/**
 * List DecisionValues, optionally filtered.
 * GET /api/v1/values
 *
 * Called at app level to sync into the Zustand decisionValues slice.
 * Pattern mirrors useOutcomes / usePendingSeeds.
 */
export function useDecisionValues(params?: { outcome_id?: string; decision_id?: string; run_id?: string; limit?: number }) {
  const setDecisionValues = useAppStore((s) => s.setDecisionValues);
  const operatorDecisions = useAppStore((s) => s.operatorDecisions);
  const outcomes          = useAppStore((s) => s.outcomes);
  const query = useQuery({
    queryKey: ["decision-values", params],
    queryFn: () => api.values.list(params),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });

  // Sync into store only for top-level (unfiltered) fetches.
  // Filtered calls (e.g. by outcome_id or decision_id) must not clobber the full list.
  // Contract enforcement: drop values whose full chain (value→outcome→decision) is broken.
  useEffect(() => {
    if (!params && query.data) {
      setDecisionValues(filterValidValues(query.data.values, outcomes, operatorDecisions));
    }
  }, [params, query.data, setDecisionValues, outcomes, operatorDecisions]);

  return query;
}

/**
 * Get a single DecisionValue by ID.
 * GET /api/v1/values/{id}
 */
export function useDecisionValue(valueId: string | null) {
  return useQuery({
    queryKey: ["decision-value", valueId],
    queryFn: () => api.values.get(valueId!),
    enabled: !!valueId,
    staleTime: 15_000,
  });
}

/**
 * Compute ROI from an existing Outcome (OPERATOR+).
 * POST /api/v1/values/compute
 */
export function useComputeValue() {
  const upsertDecisionValue = useAppStore((s) => s.upsertDecisionValue);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: import("@/types/observatory").ComputeValueRequest) =>
      api.values.compute(body),
    onSuccess: (value) => {
      upsertDecisionValue(value);
      queryClient.invalidateQueries({ queryKey: ["decision-values"] });
    },
  });
}

/**
 * Recompute an existing DecisionValue with updated inputs (OPERATOR+).
 * POST /api/v1/values/{id}/recompute
 * Writes a NEW row — the original is preserved for audit history.
 */
export function useRecomputeValue() {
  const upsertDecisionValue = useAppStore((s) => s.upsertDecisionValue);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ valueId, body }: {
      valueId: string;
      body: import("@/types/observatory").RecomputeValueRequest;
    }) => api.values.recompute(valueId, body),
    onSuccess: (value) => {
      upsertDecisionValue(value);
      queryClient.invalidateQueries({ queryKey: ["decision-values"] });
    },
  });
}

/**
 * Reject a pending ScenarioSeed (CRO / ADMIN only). No pipeline run is triggered.
 */
export function useRejectSeed() {
  const removePendingSeed = useAppStore((s) => s.removePendingSeed);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ seedId, reason, reviewedBy }: { seedId: string; reason?: string; reviewedBy?: string }) =>
      api.signals.reject(seedId, reason, reviewedBy),
    onSuccess: (_, { seedId }) => {
      removePendingSeed(seedId);
      queryClient.invalidateQueries({ queryKey: ["pending-seeds"] });
    },
  });
}
