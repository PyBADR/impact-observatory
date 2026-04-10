/**
 * Institutional Interface API Client.
 *
 * Typed fetch wrappers for Stage 70/80 institutional endpoints.
 * Uses the same auth pattern as the main api.ts client.
 */

import type {
  CalibrationLayerResponse,
  TrustLayerResponse,
  ExplainabilityResponse,
  AuditTrailResponse,
  DecisionSummaryResponse,
} from "@/types/institutional";

const BASE = "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

class InstitutionalApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "InstitutionalApiError";
  }
}

async function fetchInstitutional<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new InstitutionalApiError(
      res.status,
      `Institutional API error ${res.status}: ${text}`,
    );
  }

  return res.json() as Promise<T>;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Stage 70 — Calibration
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch Stage 70 calibration layer output for a run.
 * Includes: audit results, rankings, authority assignments,
 * calibration results, and trust scores.
 */
export async function fetchCalibration(
  runId: string,
): Promise<CalibrationLayerResponse> {
  return fetchInstitutional<CalibrationLayerResponse>(
    `/api/v1/runs/${runId}/calibration`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Stage 80 — Trust
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch Stage 80 trust layer output for a run.
 * Includes: scenario validation, action validation, authority profiles,
 * explanations, learning updates, and override results.
 */
export async function fetchTrust(
  runId: string,
): Promise<TrustLayerResponse> {
  return fetchInstitutional<TrustLayerResponse>(
    `/api/v1/runs/${runId}/trust`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Explainability
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch decision explainability pack for a run.
 * Includes: causal paths, propagation summaries, regime context,
 * ranking rationale, and override verdicts.
 */
export async function fetchExplainability(
  runId: string,
): Promise<ExplainabilityResponse> {
  return fetchInstitutional<ExplainabilityResponse>(
    `/api/v1/runs/${runId}/explainability`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Audit Trail
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch SHA-256 verified audit trail for a run.
 * Every entry includes a payload hash for institutional defensibility.
 */
export async function fetchAuditTrail(
  runId: string,
): Promise<AuditTrailResponse> {
  return fetchInstitutional<AuditTrailResponse>(
    `/api/v1/runs/${runId}/audit-trail`,
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Decision Summary
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Fetch normalized decision summary for institutional display.
 * Bridge object between internal engine outputs and frontend.
 */
export async function fetchDecisionSummary(
  runId: string,
): Promise<DecisionSummaryResponse> {
  return fetchInstitutional<DecisionSummaryResponse>(
    `/api/v1/runs/${runId}/decision-summary`,
  );
}

export { InstitutionalApiError };
