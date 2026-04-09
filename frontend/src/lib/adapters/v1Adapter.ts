import type { Entity } from "@/types/decision";
import type { OperatorDecision } from "@/types/observatory";

/**
 * V1 Adapter — bridges the macro portfolio engine with the existing
 * V1 backend (Python/FastAPI) decision and authority APIs.
 *
 * All calls target the backend directly via NEXT_PUBLIC_API_URL,
 * NOT the Next.js proxy routes (which would cause infinite loops).
 */

const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

function backendUrl(): string | null {
  return process.env.NEXT_PUBLIC_API_URL || null;
}

function headers(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-IO-API-Key": API_KEY,
  };
}

// ── V1 Decision Layer ────────────────────────────────────────────────────────

export interface V1DecisionContext {
  decisions: OperatorDecision[];
  count: number;
  available: boolean;
}

/**
 * Fetch active V1 operator decisions from the backend.
 * Returns empty context gracefully if backend is unreachable.
 */
export async function fetchV1Decisions(params?: {
  status?: string;
  limit?: number;
}): Promise<V1DecisionContext> {
  const base = backendUrl();
  if (!base) return { decisions: [], count: 0, available: false };

  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.limit != null) qs.set("limit", String(params.limit));
  const q = qs.toString();

  try {
    const res = await fetch(`${base}/api/v1/decisions${q ? `?${q}` : ""}`, {
      headers: headers(),
      cache: "no-store",
    });
    if (!res.ok) return { decisions: [], count: 0, available: false };
    const data = await res.json();
    return {
      decisions: data.decisions ?? [],
      count: data.count ?? 0,
      available: true,
    };
  } catch {
    return { decisions: [], count: 0, available: false };
  }
}

// ── V1 Authority Layer ───────────────────────────────────────────────────────

export interface V1AuthorityMetrics {
  proposed: number;
  under_review: number;
  approved_pending_execution: number;
  executed: number;
  rejected: number;
  total_active: number;
  total: number;
  available: boolean;
}

/**
 * Fetch authority queue metrics from the backend.
 */
export async function fetchV1AuthorityMetrics(): Promise<V1AuthorityMetrics> {
  const base = backendUrl();
  const empty: V1AuthorityMetrics = {
    proposed: 0, under_review: 0, approved_pending_execution: 0,
    executed: 0, rejected: 0, total_active: 0, total: 0, available: false,
  };
  if (!base) return empty;

  try {
    const res = await fetch(`${base}/api/v1/authority/metrics`, {
      headers: headers(),
      cache: "no-store",
    });
    if (!res.ok) return empty;
    const data = await res.json();
    return { ...data, available: true };
  } catch {
    return empty;
  }
}

// ── Entity Matching ──────────────────────────────────────────────────────────

/**
 * Attempt to match a portfolio entity with a V1 operator decision.
 * Matches by entity name appearing in the decision payload or rationale.
 */
export function matchEntityToV1Decision(
  entity: Entity,
  decisions: OperatorDecision[],
): OperatorDecision | null {
  const name = entity.name.toLowerCase();
  const sector = entity.sector.toLowerCase();

  for (const d of decisions) {
    const payload = JSON.stringify(d.decision_payload ?? {}).toLowerCase();
    const rationale = (d.rationale ?? "").toLowerCase();

    if (payload.includes(name) || rationale.includes(name)) return d;
    if (payload.includes(sector) || rationale.includes(sector)) return d;
  }
  return null;
}
