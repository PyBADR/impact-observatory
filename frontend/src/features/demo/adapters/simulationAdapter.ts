/**
 * Impact Observatory | مرصد الأثر — Phase 1 Simulation Adapter
 *
 * Fetches POST /api/v1/simulation/run-hormuz and returns typed results.
 * Maps backend Pydantic models to frontend TypeScript interfaces.
 *
 * Usage:
 *   import { runHormuzSimulation } from './adapters/simulationAdapter';
 *   const result = await runHormuzSimulation({ severity: 0.72 });
 *
 * Does NOT redesign the UI — only provides the data bridge.
 * Existing demo steps can consume these types to replace hardcoded values.
 */

// ═══════════════════════════════════════════════════════════════════════════════
// Request Types
// ═══════════════════════════════════════════════════════════════════════════════

export interface HormuzRunRequest {
  severity?: number;           // 0.0–1.0, default 0.72
  horizon_hours?: number;      // 1–8760, default 168
  transit_reduction_pct?: number; // 0.0–1.0, default 0.60
}

// ═══════════════════════════════════════════════════════════════════════════════
// Response Types — mirrors backend Pydantic schemas exactly
// ═══════════════════════════════════════════════════════════════════════════════

export type GCCCountryCode = "KWT" | "SAU" | "UAE" | "QAT" | "BHR" | "OMN";

export type SectorCode =
  | "oil_gas"
  | "banking"
  | "insurance"
  | "fintech"
  | "real_estate"
  | "government";

export type RiskLevel =
  | "NOMINAL"
  | "LOW"
  | "GUARDED"
  | "ELEVATED"
  | "HIGH"
  | "SEVERE";

export type Urgency = "IMMEDIATE" | "24H" | "72H";

export interface CountryImpact {
  country_code: GCCCountryCode;
  country_name: string;
  loss_usd: number;
  dominant_sector: SectorCode;
  primary_driver: string;
  transmission_channel: string;
  risk_level: RiskLevel;
  stress_score: number;
}

export interface SectorImpact {
  sector: SectorCode;
  sector_label: string;
  stress: number;
  primary_driver: string;
  secondary_risk: string;
  recommended_lever: string;
  risk_level: RiskLevel;
}

export interface PropagationEdge {
  source: string;
  target: string;
  weight: number;
  channel: string;
}

export interface DecisionAction {
  action: string;
  owner: string;
  timing: Urgency;
  value_avoided_usd: number;
  downside_risk: string;
}

export interface Explainability {
  why_total_loss: string;
  why_country: Record<GCCCountryCode, string>;
  why_sector: Record<SectorCode, string>;
  why_act_now: string;
}

export interface HormuzRunResult {
  scenario_id: string;
  model_version: string;
  timestamp: string;
  severity: number;
  horizon_hours: number;
  transit_reduction_pct: number;
  total_loss_usd: number;
  risk_level: RiskLevel;
  confidence: number;
  countries: CountryImpact[];
  sectors: SectorImpact[];
  propagation_edges: PropagationEdge[];
  decisions: DecisionAction[];
  explainability: Explainability;
  sha256_digest: string | null;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

export class SimulationApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "SimulationApiError";
  }
}

/**
 * Execute the Hormuz disruption simulation.
 *
 * @param params - Optional overrides for severity, horizon, transit reduction
 * @returns Full simulation result with countries, sectors, decisions, and explanations
 * @throws SimulationApiError on HTTP errors
 */
export async function runHormuzSimulation(
  params: HormuzRunRequest = {},
): Promise<HormuzRunResult> {
  const body: HormuzRunRequest = {
    severity: params.severity ?? 0.72,
    horizon_hours: params.horizon_hours ?? 168,
    transit_reduction_pct: params.transit_reduction_pct ?? 0.60,
  };

  const res = await fetch(`${API_BASE}/api/v1/simulation/run-hormuz`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-IO-API-Key": API_KEY,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const msg = res.status === 422
      ? "Invalid simulation parameters. Please check severity (0–1) and horizon (1–8760h)."
      : res.status >= 500
      ? "Simulation engine temporarily unavailable. Please retry."
      : `Simulation request failed (HTTP ${res.status})`;
    throw new SimulationApiError(res.status, msg);
  }

  return res.json() as Promise<HormuzRunResult>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Demo Adapter — maps HormuzRunResult to existing demo-scenario.ts shapes
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Convert a backend CountryImpact to the existing GCCCountryImpact shape
 * used by demo steps (GCCExposureStep, GCCImpactStep).
 */
export function toGCCCountryImpact(c: CountryImpact) {
  const FLAGS: Record<GCCCountryCode, string> = {
    KWT: "🇰🇼",
    SAU: "🇸🇦",
    UAE: "🇦🇪",
    QAT: "🇶🇦",
    BHR: "🇧🇭",
    OMN: "🇴🇲",
  };

  return {
    country: c.country_name,
    flag: FLAGS[c.country_code],
    sectorStress: c.stress_score,
    estimatedLoss: formatUSD(c.loss_usd),
    impactLevel: c.risk_level as "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL",
    topSector: c.dominant_sector.replace("_", " "),
    driver: c.primary_driver,
    channel: c.transmission_channel,
  };
}

/**
 * Convert a backend SectorImpact to the existing SectorImpact shape
 * used by SectorImpactStep / SectorStressStep.
 */
export function toFrontendSectorImpact(s: SectorImpact) {
  const ICONS: Record<SectorCode, string> = {
    oil_gas: "⛽",
    banking: "🏦",
    insurance: "🛡️",
    fintech: "💳",
    real_estate: "🏗️",
    government: "🏛️",
  };

  return {
    name: s.sector_label,
    icon: ICONS[s.sector],
    signal: s.primary_driver,
    impact: `${(s.stress * 100).toFixed(0)}% stress`,
    riskLevel: s.risk_level as "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL",
    explanation: `Primary: ${s.primary_driver}. Secondary: ${s.secondary_risk}`,
    currentStress: s.stress,
    topDriver: s.primary_driver,
    secondOrderRisk: s.secondary_risk,
    confidenceBand: s.stress >= 0.5 ? "±8–12%" : "±5–8%",
    recommendedLever: s.recommended_lever,
  };
}

/**
 * Convert backend DecisionAction to existing DecisionAction shape.
 */
export function toFrontendDecision(d: DecisionAction) {
  return {
    title: d.action,
    owner: d.owner,
    urgency: d.timing as "IMMEDIATE" | "24H" | "72H",
    expectedEffect: `Avoids ${formatUSD(d.value_avoided_usd)} in potential losses`,
    consequence: d.downside_risk,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// Utilities
// ═══════════════════════════════════════════════════════════════════════════════

function formatUSD(value: number): string {
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}
