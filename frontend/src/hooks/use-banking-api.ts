"use client";

/**
 * Banking Intelligence — TanStack Query Hooks
 *
 * Data flow: banking-api.ts (fetch) → use-banking-api.ts (hooks) → components
 * Follows same patterns as use-api.ts (useQuery/useMutation + queryClient).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchDecisionChain,
  bridgeFromRun,
  fetchBankingEntities,
  fetchDecisionContracts,
  fetchCounterfactual,
  fetchPropagations,
  fetchOutcomeReview,
  fetchValueAudit,
  transitionDecision,
  fetchDedupStats,
  type BankingDecisionChain,
} from "@/lib/banking-api";
import { DecisionStatus } from "@/types/banking-intelligence";

// ─── Query Key Factory ─────────────────────────────────────────────────────

const bankingKeys = {
  all: ["banking"] as const,
  chains: () => [...bankingKeys.all, "chain"] as const,
  chain: (runId: string) => [...bankingKeys.chains(), runId] as const,
  entities: () => [...bankingKeys.all, "entities"] as const,
  entityList: (params?: Record<string, unknown>) =>
    [...bankingKeys.entities(), params ?? {}] as const,
  decisions: () => [...bankingKeys.all, "decisions"] as const,
  decisionList: (params?: Record<string, unknown>) =>
    [...bankingKeys.decisions(), params ?? {}] as const,
  counterfactual: (cfId: string) =>
    [...bankingKeys.all, "counterfactual", cfId] as const,
  propagations: (params?: Record<string, unknown>) =>
    [...bankingKeys.all, "propagations", params ?? {}] as const,
  outcomeReview: (reviewId: string) =>
    [...bankingKeys.all, "outcome-review", reviewId] as const,
  valueAudit: (auditId: string) =>
    [...bankingKeys.all, "value-audit", auditId] as const,
  dedupStats: () => [...bankingKeys.all, "dedup-stats"] as const,
};

// ─── Chain Hooks ────────────────────────────────────────────────────────────

/**
 * Fetch a complete banking decision chain by run ID.
 * Returns decision + counterfactual + propagation + review + metadata.
 */
export function useBankingChain(runId: string | null) {
  return useQuery({
    queryKey: bankingKeys.chain(runId ?? ""),
    queryFn: () => fetchDecisionChain(runId!),
    enabled: !!runId,
    staleTime: 5 * 60 * 1000, // 5 min — chains are relatively stable
    retry: 1,
  });
}

/**
 * Execute simulation + bridge to banking contracts in one call.
 * POST /banking/chain/from-run/{runId}
 */
export function useBridgeFromRun(
  onSuccess?: (chain: BankingDecisionChain) => void
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      runId,
      scenarioId,
      baselineUrs,
    }: {
      runId: string;
      scenarioId: string;
      baselineUrs?: number;
    }) => bridgeFromRun(runId, scenarioId, baselineUrs),
    onSuccess: (data, variables) => {
      // Cache the chain result
      queryClient.setQueryData(bankingKeys.chain(variables.runId), data);
      queryClient.invalidateQueries({ queryKey: bankingKeys.decisions() });
      onSuccess?.(data);
    },
  });
}

// ─── Entity Hooks ───────────────────────────────────────────────────────────

/**
 * Fetch banking entities with optional type/country filtering.
 */
export function useBankingEntities(params?: {
  entity_type?: string;
  country_code?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: bankingKeys.entityList(params as Record<string, unknown>),
    queryFn: () => fetchBankingEntities(params),
    staleTime: 10 * 60 * 1000, // 10 min
  });
}

/**
 * Fetch dedup registry stats.
 */
export function useDedupStats() {
  return useQuery({
    queryKey: bankingKeys.dedupStats(),
    queryFn: () => fetchDedupStats(),
    staleTime: 30 * 1000, // 30 sec
  });
}

// ─── Decision Contract Hooks ────────────────────────────────────────────────

/**
 * Fetch decision contracts with optional filtering.
 */
export function useBankingDecisions(params?: {
  scenario_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: bankingKeys.decisionList(params as Record<string, unknown>),
    queryFn: () => fetchDecisionContracts(params),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Transition a decision contract to a new status.
 */
export function useTransitionDecision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      decisionId,
      targetStatus,
      changedBy,
      reason,
    }: {
      decisionId: string;
      targetStatus: DecisionStatus;
      changedBy: string;
      reason?: string;
    }) => transitionDecision(decisionId, targetStatus, changedBy, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: bankingKeys.decisions() });
      queryClient.invalidateQueries({ queryKey: bankingKeys.chains() });
    },
  });
}

// ─── Counterfactual Hooks ───────────────────────────────────────────────────

/**
 * Fetch a single counterfactual analysis by ID.
 */
export function useBankingCounterfactual(cfId: string | null) {
  return useQuery({
    queryKey: bankingKeys.counterfactual(cfId ?? ""),
    queryFn: () => fetchCounterfactual(cfId!),
    enabled: !!cfId,
    staleTime: 5 * 60 * 1000,
  });
}

// ─── Propagation Hooks ──────────────────────────────────────────────────────

/**
 * Fetch propagation contracts with optional filtering.
 */
export function useBankingPropagations(params?: {
  scenario_id?: string;
  breakable_only?: boolean;
}) {
  return useQuery({
    queryKey: bankingKeys.propagations(params as Record<string, unknown>),
    queryFn: () => fetchPropagations(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ─── Outcome Review Hooks ───────────────────────────────────────────────────

/**
 * Fetch an outcome review by ID.
 */
export function useBankingOutcomeReview(reviewId: string | null) {
  return useQuery({
    queryKey: bankingKeys.outcomeReview(reviewId ?? ""),
    queryFn: () => fetchOutcomeReview(reviewId!),
    enabled: !!reviewId,
    staleTime: 2 * 60 * 1000,
  });
}

// ─── Value Audit Hooks ──────────────────────────────────────────────────────

/**
 * Fetch a value audit by ID.
 */
export function useBankingValueAudit(auditId: string | null) {
  return useQuery({
    queryKey: bankingKeys.valueAudit(auditId ?? ""),
    queryFn: () => fetchValueAudit(auditId!),
    enabled: !!auditId,
    staleTime: 5 * 60 * 1000,
  });
}
