"use client";

/**
 * Impact Observatory | مرصد الأثر — Provenance Data Hooks
 *
 * React Query hooks for the 5 provenance API endpoints.
 * All use staleTime: Infinity — provenance is immutable per completed run.
 */

import { useQuery } from "@tanstack/react-query";
import {
  fetchMetricsProvenance,
  fetchFactorBreakdown,
  fetchMetricRanges,
  fetchDecisionReasoning,
  fetchDataBasis,
} from "@/lib/provenance-api";
import type {
  MetricsProvenanceResponse,
  FactorBreakdownResponse,
  MetricRangesResponse,
  DecisionReasoningResponse,
  DataBasisResponse,
} from "@/types/provenance";

export function useMetricsProvenance(runId: string | undefined) {
  return useQuery<MetricsProvenanceResponse>({
    queryKey: ["provenance", "metrics", runId],
    queryFn: () => fetchMetricsProvenance(runId!),
    staleTime: Infinity,
    enabled: !!runId,
  });
}

export function useFactorBreakdown(runId: string | undefined) {
  return useQuery<FactorBreakdownResponse>({
    queryKey: ["provenance", "factors", runId],
    queryFn: () => fetchFactorBreakdown(runId!),
    staleTime: Infinity,
    enabled: !!runId,
  });
}

export function useMetricRanges(runId: string | undefined) {
  return useQuery<MetricRangesResponse>({
    queryKey: ["provenance", "ranges", runId],
    queryFn: () => fetchMetricRanges(runId!),
    staleTime: Infinity,
    enabled: !!runId,
  });
}

export function useDecisionReasoning(runId: string | undefined) {
  return useQuery<DecisionReasoningResponse>({
    queryKey: ["provenance", "reasoning", runId],
    queryFn: () => fetchDecisionReasoning(runId!),
    staleTime: Infinity,
    enabled: !!runId,
  });
}

export function useDataBasis(runId: string | undefined) {
  return useQuery<DataBasisResponse>({
    queryKey: ["provenance", "basis", runId],
    queryFn: () => fetchDataBasis(runId!),
    staleTime: Infinity,
    enabled: !!runId,
  });
}
