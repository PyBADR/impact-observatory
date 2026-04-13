/**
 * Impact Observatory | مرصد الأثر — Phase 2 Counterfactual Adapter
 *
 * Fetches: POST /api/v1/counterfactuals/{slug}
 *
 * Returns the no_action baseline + per-decision "what-if" branches.
 * Designed to wire into the Decision Room (DecisionStep / DecisionEngineStep).
 *
 * Usage:
 *   import { runCounterfactual, adaptForDecisionRoom } from './counterfactualAdapter';
 *   const cf = await runCounterfactual("hormuz", { severity: 0.72 });
 *   const roomData = adaptForDecisionRoom(cf);
 */

import { SimulationApiError } from "./simulationAdapter";
import type { RiskLevel } from "./simulationAdapter";

// ═══════════════════════════════════════════════════════════════════════════════
// Types — mirrors backend Pydantic schemas
// ═══════════════════════════════════════════════════════════════════════════════

export interface NoActionBaseline {
  total_loss_usd: number;
  risk_level: RiskLevel;
  confidence: number;
  decision_count: number;
  pathway_headlines: string[];
}

export interface CounterfactualBranch {
  action: string;
  owner: string;
  timing: string;
  total_loss_usd: number;
  loss_reduction_usd: number;
  loss_reduction_pct: number;
  risk_level: RiskLevel;
  confidence: number;
  top_country_code: string | null;
  top_country_loss_usd: number | null;
  top_sector: string | null;
  top_sector_stress: number | null;
  pathway_headline: string;
  downside_risk: string;
}

export interface CounterfactualResponse {
  scenario_slug: string;
  severity: number;
  horizon_hours: number;
  no_action: NoActionBaseline;
  branches: CounterfactualBranch[];
  best_action: string | null;
  best_action_saves_usd: number | null;
  combined_max_avoidable_usd: number;
  combined_max_avoidable_pct: number;
}

export interface CounterfactualRequest {
  severity?: number | null;
  horizon_hours?: number | null;
  extra_params?: Record<string, unknown>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

/**
 * Run counterfactual analysis for a scenario.
 */
export async function runCounterfactual(
  slug: string,
  params: CounterfactualRequest = {},
): Promise<CounterfactualResponse> {
  const res = await fetch(`${API_BASE}/api/v1/counterfactuals/${slug}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-IO-API-Key": API_KEY,
    },
    body: JSON.stringify({
      severity: params.severity ?? null,
      horizon_hours: params.horizon_hours ?? null,
      extra_params: params.extra_params ?? {},
    }),
  });

  if (!res.ok) {
    const msg =
      res.status === 404
        ? "Scenario not found for counterfactual analysis."
        : res.status >= 500
        ? "Counterfactual engine temporarily unavailable."
        : `Counterfactual request failed (HTTP ${res.status})`;
    throw new SimulationApiError(res.status, msg);
  }

  return res.json() as Promise<CounterfactualResponse>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Decision Room Adapter
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Shape for rendering each decision card in the Decision Room.
 * Shows the action, who owns it, what it saves, and what happens if skipped.
 */
export interface DecisionRoomCard {
  title: string;
  owner: string;
  urgency: string;
  lossWithAction: string;
  lossReduction: string;
  reductionPct: string;
  riskAfterAction: RiskLevel;
  downsideIfSkipped: string;
  pathwayHeadline: string;
  isBestAction: boolean;
}

export interface DecisionRoomData {
  /** Headline: total loss with no intervention */
  baselineLoss: string;
  baselineRisk: RiskLevel;
  /** Each decision as a card */
  cards: DecisionRoomCard[];
  /** Summary banner */
  bestActionSummary: string;
  combinedSavings: string;
  combinedSavingsPct: string;
}

function formatUSD(value: number): string {
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}

/**
 * Transform raw counterfactual API response into Decision Room rendering data.
 *
 * Drop this into DecisionStep / DecisionEngineStep:
 *   const roomData = adaptForDecisionRoom(cfResponse);
 *   roomData.cards.forEach(card => renderDecisionCard(card));
 */
export function adaptForDecisionRoom(cf: CounterfactualResponse): DecisionRoomData {
  const cards: DecisionRoomCard[] = cf.branches.map((b) => ({
    title: b.action,
    owner: b.owner,
    urgency: b.timing,
    lossWithAction: formatUSD(b.total_loss_usd),
    lossReduction: formatUSD(b.loss_reduction_usd),
    reductionPct: `${(b.loss_reduction_pct * 100).toFixed(1)}%`,
    riskAfterAction: b.risk_level,
    downsideIfSkipped: b.downside_risk,
    pathwayHeadline: b.pathway_headline,
    isBestAction: b.action === cf.best_action,
  }));

  const bestSummary = cf.best_action
    ? `Best single action: "${cf.best_action}" saves ${formatUSD(cf.best_action_saves_usd ?? 0)}`
    : "No actions available at current stress levels";

  return {
    baselineLoss: formatUSD(cf.no_action.total_loss_usd),
    baselineRisk: cf.no_action.risk_level,
    cards,
    bestActionSummary: bestSummary,
    combinedSavings: formatUSD(cf.combined_max_avoidable_usd),
    combinedSavingsPct: `${(cf.combined_max_avoidable_pct * 100).toFixed(1)}%`,
  };
}
