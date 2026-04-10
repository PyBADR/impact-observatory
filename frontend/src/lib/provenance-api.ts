/**
 * Metrics Provenance API Client.
 *
 * Typed fetch wrappers for the 5 provenance endpoints (Stage 85).
 * Uses the same auth pattern as the main api.ts client.
 */

import type {
  MetricsProvenanceResponse,
  FactorBreakdownResponse,
  MetricRangesResponse,
  DecisionReasoningResponse,
  DataBasisResponse,
} from "@/types/provenance";

const BASE = "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

class ProvenanceApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ProvenanceApiError";
  }
}

async function fetchProvenance<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ProvenanceApiError(
      res.status,
      `Provenance API error ${res.status}: ${text}`,
    );
  }

  return res.json() as Promise<T>;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  1. Metric Provenance — why this number
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch metric provenance for all major metrics in a run.
 * Each metric includes: formula, source, factors, model basis, confidence notes.
 */
export async function fetchMetricsProvenance(
  runId: string,
): Promise<MetricsProvenanceResponse> {
  return fetchProvenance<MetricsProvenanceResponse>(
    `/api/v1/runs/${runId}/metrics-provenance`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  2. Factor Breakdown — what drove this number
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch factor breakdowns for all major metrics in a run.
 * Factors sum coherently — no unexplained residuals.
 */
export async function fetchFactorBreakdown(
  runId: string,
): Promise<FactorBreakdownResponse> {
  return fetchProvenance<FactorBreakdownResponse>(
    `/api/v1/runs/${runId}/factor-breakdown`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  3. Metric Ranges — uncertainty bands
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch uncertainty ranges for all major metrics in a run.
 * Each metric has [min, expected, max] tied to severity and confidence.
 */
export async function fetchMetricRanges(
  runId: string,
): Promise<MetricRangesResponse> {
  return fetchProvenance<MetricRangesResponse>(
    `/api/v1/runs/${runId}/metric-ranges`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  4. Decision Reasoning — why this decision
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch reasoning explanations for all decisions in a run.
 * Each decision: why recommended, why now, why this rank,
 * propagation link, regime link, trust link, tradeoff summary.
 */
export async function fetchDecisionReasoning(
  runId: string,
): Promise<DecisionReasoningResponse> {
  return fetchProvenance<DecisionReasoningResponse>(
    `/api/v1/runs/${runId}/decision-reasoning`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  5. Data Basis — what data period backs this
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch data basis records for all metrics in a run.
 * Shows historical analog, calibration period, freshness assessment.
 * Weak freshness is explicitly flagged.
 */
export async function fetchDataBasis(
  runId: string,
): Promise<DataBasisResponse> {
  return fetchProvenance<DataBasisResponse>(
    `/api/v1/runs/${runId}/data-basis`,
  );
}

export { ProvenanceApiError };
