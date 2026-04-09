/**
 * V2 Data Source — Mock / Live Switch with Automatic Fallback
 *
 * Provides a single fetchData() that:
 *   1. In "mock" mode → returns deterministic mock data (zero network)
 *   2. In "live" mode → calls /api/v1/runs or /api/v1/macro/propagate/inline
 *   3. On live failure → falls back to mock, preserves error message
 *
 * Safety:
 *   - AbortController timeout (default 30s) prevents hung requests
 *   - try/catch around every network call — never throws to caller
 *   - All outputs routed through mapApiToUI → SafeApiResult (no undefined/null)
 */

import { mapApiToUI, type SafeApiResult } from "./api-types";

// ═══════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════

export type DataMode = "mock" | "live";

export interface FetchResult {
  data: SafeApiResult;
  source: DataMode;
  /** Non-empty when live failed and mock was used as fallback */
  fallbackError: string;
}

export interface FetchOptions {
  /** "mock" skips network entirely. "live" attempts API, falls back to mock. */
  mode: DataMode;
  /** For live: existing run ID to fetch via GET /api/v1/runs/{id} */
  runId?: string;
  /** For live: launch a new run via POST /api/v1/runs */
  launchParams?: {
    template_id: string;
    severity?: number;
    horizon_hours?: number;
    label?: string;
  };
  /** For live: inline propagation via POST /api/v1/macro/propagate/inline */
  inlineSignal?: Record<string, unknown>;
  /** Request timeout in ms. Default 30_000. */
  timeoutMs?: number;
}

// ═══════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════

const DEFAULT_TIMEOUT_MS = 30_000;
const API_KEY =
  typeof process !== "undefined"
    ? process.env?.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026"
    : "io_master_key_2026";

// ═══════════════════════════════════════════════════════════════════════
// Mock Data Loader (lazy import to avoid bundling in live-only paths)
// ═══════════════════════════════════════════════════════════════════════

function buildMockPayload(): Record<string, unknown> {
  // Dynamic import is async — but we need this sync for the fallback path.
  // Instead, inline a minimal mock payload that maps through mapApiToUI.
  // For full mock, the command-center hook uses mock-data.ts directly.
  // This is the V2 data-source fallback — a complete but compact payload.
  return {
    run_id: "mock_v2_fallback",
    status: "completed",
    scenario: {
      template_id: "hormuz_chokepoint_disruption",
      label: "Strait of Hormuz Partial Blockage",
      severity: 0.72,
      horizon_hours: 168,
    },
    headline: {
      total_loss_usd: 4_270_000_000,
      total_nodes_impacted: 31,
      propagation_depth: 5,
    },
    confidence: 0.78,
    warnings: [],
    stages_completed: [
      "graph_load",
      "scenario_init",
      "shock_inject",
      "propagation",
      "physics",
      "math",
      "sector_banking",
      "sector_insurance",
      "sector_fintech",
    ],
    duration_ms: 0,
    propagation_steps: [
      { from: "hormuz_strait", to: "oil_terminals", weight: 0.92, transmission: 0.88, label: "Maritime → Energy" },
      { from: "oil_terminals", to: "gcc_banking", weight: 0.74, transmission: 0.65, label: "Energy → Banking" },
      { from: "gcc_banking", to: "insurance_pool", weight: 0.58, transmission: 0.42, label: "Banking → Insurance" },
    ],
    sector_rollups: {
      banking: { aggregate_stress: 0.68, total_loss: 1_800_000_000, node_count: 8, classification: "ELEVATED" },
      insurance: { aggregate_stress: 0.52, total_loss: 900_000_000, node_count: 6, classification: "MODERATE" },
      fintech: { aggregate_stress: 0.41, total_loss: 320_000_000, node_count: 5, classification: "LOW" },
    },
    decision_inputs: {
      run_id: "mock_v2_fallback",
      total_loss_usd: 4_270_000_000,
      actions: [
        {
          id: "mock_action_1",
          action: "Activate reinsurance treaty for marine hull portfolio",
          action_ar: "تفعيل اتفاقية إعادة التأمين لمحفظة أجسام السفن",
          sector: "insurance",
          owner: "CRO",
          urgency: 88,
          value: 76,
          regulatory_risk: 0.3,
          priority: 91,
          target_node_id: "insurance_pool",
          target_lat: 25.2,
          target_lng: 55.3,
          loss_avoided_usd: 420_000_000,
          cost_usd: 12_000_000,
          confidence: 0.82,
        },
        {
          id: "mock_action_2",
          action: "Hedge crude oil exposure via futures contracts",
          action_ar: "تحوط تعرض النفط الخام عبر العقود الآجلة",
          sector: "energy",
          owner: "Treasury",
          urgency: 92,
          value: 84,
          regulatory_risk: 0.15,
          priority: 95,
          target_node_id: "oil_terminals",
          target_lat: 26.2,
          target_lng: 50.2,
          loss_avoided_usd: 680_000_000,
          cost_usd: 28_000_000,
          confidence: 0.75,
        },
      ],
      all_actions: [],
    },
    sectors: {
      banking_stresses: [
        { entity_id: "bank_uae_01", lcr: 0.92, cet1_ratio: 0.14, capital_adequacy_ratio: 0.16, aggregate_stress: 0.68 },
      ],
      insurance_stresses: [
        { entity_id: "ins_gcc_01", solvency_ratio: 1.45, combined_ratio: 0.98, aggregate_stress: 0.52 },
      ],
      fintech_stresses: [
        { entity_id: "ft_gcc_01", service_availability: 0.94, settlement_delay_minutes: 45, aggregate_stress: 0.41 },
      ],
    },
    graph_payload: { nodes: [], edges: [], categories: [] },
    trust: {
      audit_hash: "mock_v2_sha256_placeholder",
      model_version: "2.1.0-mock",
      pipeline_version: "17-stage-v2",
      data_sources: ["deterministic_mock"],
      confidence_score: 0.78,
      warnings: [],
      stages_completed: [],
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════
// Network Helpers
// ═══════════════════════════════════════════════════════════════════════

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "X-IO-API-Key": API_KEY,
        ...init.headers,
      },
    });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

function formatError(err: unknown): string {
  if (err instanceof DOMException && err.name === "AbortError") {
    return "Request timed out";
  }
  if (err instanceof Error) {
    return err.message;
  }
  return String(err);
}

// ═══════════════════════════════════════════════════════════════════════
// Core: fetchData
// ═══════════════════════════════════════════════════════════════════════

/**
 * Fetch simulation data from mock or live source.
 *
 * Never throws. Always returns a FetchResult with safe-typed data.
 *
 * Priority:
 *   1. mode === "mock" → immediate mock return
 *   2. mode === "live" + runId → GET /api/v1/runs/{runId}
 *   3. mode === "live" + launchParams → POST /api/v1/runs
 *   4. mode === "live" + inlineSignal → POST /api/v1/macro/propagate/inline
 *   5. Any live failure → fallback to mock with error preserved
 */
export async function fetchData(opts: FetchOptions): Promise<FetchResult> {
  const timeout = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  // ── Mock fast path ─────────────────────────────────────────────
  if (opts.mode === "mock") {
    return {
      data: mapApiToUI(buildMockPayload()),
      source: "mock",
      fallbackError: "",
    };
  }

  // ── Live path ──────────────────────────────────────────────────
  try {
    let raw: unknown;

    if (opts.runId) {
      // GET existing run result
      const res = await fetchWithTimeout(
        `/api/v1/runs/${opts.runId}`,
        { method: "GET" },
        timeout,
      );
      if (!res.ok) {
        throw new Error(`GET /api/v1/runs/${opts.runId} → ${res.status} ${res.statusText}`);
      }
      const json = await res.json();
      // API wraps in { data: ... } envelope
      raw = json.data ?? json;

    } else if (opts.launchParams) {
      // POST new run
      const res = await fetchWithTimeout(
        "/api/v1/runs",
        { method: "POST", body: JSON.stringify(opts.launchParams) },
        timeout,
      );
      if (!res.ok) {
        throw new Error(`POST /api/v1/runs → ${res.status} ${res.statusText}`);
      }
      const json = await res.json();
      raw = json.data ?? json;

    } else if (opts.inlineSignal) {
      // POST inline propagation (macro pipeline)
      const res = await fetchWithTimeout(
        "/api/v1/macro/propagate/inline",
        { method: "POST", body: JSON.stringify({ signal: opts.inlineSignal }) },
        timeout,
      );
      if (!res.ok) {
        throw new Error(`POST /api/v1/macro/propagate/inline → ${res.status} ${res.statusText}`);
      }
      const json = await res.json();
      // Propagation API returns { result: PropagationResult, message: ... }
      raw = json.result ?? json;

    } else {
      throw new Error("Live mode requires runId, launchParams, or inlineSignal");
    }

    return {
      data: mapApiToUI(raw),
      source: "live",
      fallbackError: "",
    };

  } catch (err) {
    // ── Fallback to mock ───────────────────────────────────────
    const errorMsg = formatError(err);
    return {
      data: mapApiToUI(buildMockPayload()),
      source: "mock",
      fallbackError: `Live API failed — showing demo data. (${errorMsg})`,
    };
  }
}
