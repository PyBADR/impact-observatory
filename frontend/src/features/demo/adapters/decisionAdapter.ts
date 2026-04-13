/**
 * Impact Observatory | مرصد الأثر — Phase 3 Decision Adapter
 *
 * Fetches: POST /api/v1/decisions/analyze/{slug}
 *          GET  /api/v1/decisions/ownership
 *          GET  /api/v1/decisions/escalation-rules
 *
 * Returns ownership-enriched decisions, escalation alerts, and authority
 * hierarchy for the Decision Command Centre UI.
 *
 * Usage:
 *   import { analyzeDecisions, adaptForCommandCentre } from './decisionAdapter';
 *   const analysis = await analyzeDecisions("hormuz", { severity: 0.72 });
 *   const cc = adaptForCommandCentre(analysis);
 */

import { SimulationApiError } from "./simulationAdapter";
import type { RiskLevel } from "./simulationAdapter";

// ═══════════════════════════════════════════════════════════════════════════════
// Types — mirrors backend Pydantic schemas
// ═══════════════════════════════════════════════════════════════════════════════

export interface DecisionDetail {
  action: string;
  owner: string;
  timing: string;
  value_avoided_usd: number;
  downside_risk: string;
  owner_entity_type: string;
  owner_role: string;
  owner_role_ar: string;
  authority_level: "operational" | "tactical" | "strategic" | "sovereign";
  deadline_hours: number;
  escalation_path: string[];
  regulatory_reference: string;
  failure_consequence: string;
  country_entity_name: string;
  country_entity_name_ar: string;
}

export interface EscalationDetail {
  trigger: string;
  severity: "warning" | "critical" | "emergency";
  authority_required: "operational" | "tactical" | "strategic" | "sovereign";
  headline: string;
  headline_ar: string;
  affected_entities: string[];
  affected_countries: string[];
  affected_sectors: string[];
  time_to_act_hours: number;
  narrative: string;
  recommended_actions: string[];
}

export interface DecisionAnalysisResponse {
  scenario_slug: string;
  model_version: string;
  timestamp: string;
  sha256_digest: string;
  total_loss_usd: number;
  risk_level: RiskLevel;
  total_decisions: number;
  decisions: DecisionDetail[];
  total_escalations: number;
  sovereign_alerts: number;
  escalations: EscalationDetail[];
  entities_breached: number;
  breached_entities: string[];
  immediate_actions: number;
  urgent_actions: number;
  standard_actions: number;
}

export interface DecisionAnalysisRequest {
  severity?: number | null;
  horizon_hours?: number | null;
  country_code?: string | null;
  extra_params?: Record<string, unknown>;
}

export interface OwnershipRule {
  action: string;
  sector: string;
  owner_entity_type: string;
  owner_role: string;
  owner_role_ar: string;
  authority_level: string;
  deadline_hours: number;
  escalation_path: string[];
  regulatory_reference: string;
  failure_consequence: string;
}

export interface OwnershipRegistryResponse {
  total_rules: number;
  rules: OwnershipRule[];
}

export interface EscalationRule {
  rule_name: string;
  threshold_value: number;
  description: string;
  authority_required: string;
}

export interface EscalationRulesResponse {
  rules: EscalationRule[];
}

// ═══════════════════════════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

const headers = {
  "Content-Type": "application/json",
  "X-IO-API-Key": API_KEY,
};

/**
 * Run decision analysis for a scenario.
 */
export async function analyzeDecisions(
  slug: string,
  params: DecisionAnalysisRequest = {},
): Promise<DecisionAnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/v1/decisions/analyze/${slug}`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      severity: params.severity ?? null,
      horizon_hours: params.horizon_hours ?? null,
      country_code: params.country_code ?? null,
      extra_params: params.extra_params ?? {},
    }),
  });

  if (!res.ok) {
    const msg =
      res.status === 404
        ? "Scenario not found."
        : res.status >= 500
        ? "Decision analysis engine temporarily unavailable."
        : `Decision analysis failed (HTTP ${res.status})`;
    throw new SimulationApiError(res.status, msg);
  }

  return res.json() as Promise<DecisionAnalysisResponse>;
}

/**
 * Fetch all ownership mappings.
 */
export async function fetchOwnershipRules(): Promise<OwnershipRegistryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/decisions/ownership`, { headers });
  if (!res.ok) {
    throw new SimulationApiError(res.status, `Ownership fetch failed (HTTP ${res.status})`);
  }
  return res.json() as Promise<OwnershipRegistryResponse>;
}

/**
 * Fetch escalation threshold rules.
 */
export async function fetchEscalationRules(): Promise<EscalationRulesResponse> {
  const res = await fetch(`${API_BASE}/api/v1/decisions/escalation-rules`, { headers });
  if (!res.ok) {
    throw new SimulationApiError(res.status, `Escalation rules fetch failed (HTTP ${res.status})`);
  }
  return res.json() as Promise<EscalationRulesResponse>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Command Centre Adapter
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * A decision card for the Command Centre UI.
 */
export interface CommandCentreCard {
  title: string;
  owner: string;
  ownerAr: string;
  entityName: string;
  entityNameAr: string;
  authorityLevel: string;
  urgencyBadge: "IMMEDIATE" | "URGENT" | "STANDARD";
  deadlineLabel: string;
  valueAvoided: string;
  downsideIfSkipped: string;
  failureConsequence: string;
  escalationChain: string;
  regulatoryRef: string;
}

/**
 * An escalation banner for the Command Centre.
 */
export interface EscalationBanner {
  headline: string;
  headlineAr: string;
  severity: "warning" | "critical" | "emergency";
  authorityRequired: string;
  timeToAct: string;
  narrative: string;
  actions: string[];
}

/**
 * Complete Command Centre rendering data.
 */
export interface CommandCentreData {
  /** Top-level status */
  totalLoss: string;
  riskLevel: RiskLevel;
  timestamp: string;

  /** Decision cards sorted by urgency */
  cards: CommandCentreCard[];

  /** Escalation banners (highest severity first) */
  banners: EscalationBanner[];

  /** Summary stats */
  immediateActions: number;
  urgentActions: number;
  standardActions: number;
  entitiesBreached: number;
  sovereignAlerts: number;
}

function formatUSD(value: number): string {
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}

function urgencyBadge(deadlineHours: number): "IMMEDIATE" | "URGENT" | "STANDARD" {
  if (deadlineHours <= 4) return "IMMEDIATE";
  if (deadlineHours <= 12) return "URGENT";
  return "STANDARD";
}

function deadlineLabel(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)}min`;
  if (hours < 24) return `${hours}h`;
  return `${Math.round(hours / 24)}d`;
}

/**
 * Transform decision analysis response into Command Centre rendering data.
 *
 * Drop this into the Decision Command Centre component:
 *   const cc = adaptForCommandCentre(analysisResponse);
 *   cc.cards.forEach(card => renderDecisionCard(card));
 *   cc.banners.forEach(banner => renderEscalationBanner(banner));
 */
export function adaptForCommandCentre(
  analysis: DecisionAnalysisResponse,
): CommandCentreData {
  const cards: CommandCentreCard[] = analysis.decisions.map((d) => ({
    title: d.action,
    owner: d.owner_role,
    ownerAr: d.owner_role_ar,
    entityName: d.country_entity_name,
    entityNameAr: d.country_entity_name_ar,
    authorityLevel: d.authority_level.toUpperCase(),
    urgencyBadge: urgencyBadge(d.deadline_hours),
    deadlineLabel: deadlineLabel(d.deadline_hours),
    valueAvoided: formatUSD(d.value_avoided_usd),
    downsideIfSkipped: d.downside_risk,
    failureConsequence: d.failure_consequence,
    escalationChain: d.escalation_path.join(" → "),
    regulatoryRef: d.regulatory_reference,
  }));

  // Sort: IMMEDIATE first, then URGENT, then STANDARD
  const urgencyOrder = { IMMEDIATE: 0, URGENT: 1, STANDARD: 2 };
  cards.sort((a, b) => urgencyOrder[a.urgencyBadge] - urgencyOrder[b.urgencyBadge]);

  const banners: EscalationBanner[] = analysis.escalations.map((e) => ({
    headline: e.headline,
    headlineAr: e.headline_ar,
    severity: e.severity,
    authorityRequired: e.authority_required.toUpperCase(),
    timeToAct: deadlineLabel(e.time_to_act_hours),
    narrative: e.narrative,
    actions: e.recommended_actions,
  }));

  return {
    totalLoss: formatUSD(analysis.total_loss_usd),
    riskLevel: analysis.risk_level,
    timestamp: analysis.timestamp,
    cards,
    banners,
    immediateActions: analysis.immediate_actions,
    urgentActions: analysis.urgent_actions,
    standardActions: analysis.standard_actions,
    entitiesBreached: analysis.entities_breached,
    sovereignAlerts: analysis.sovereign_alerts,
  };
}
