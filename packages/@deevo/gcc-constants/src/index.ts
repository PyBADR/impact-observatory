/**
 * @deevo/gcc-constants — GCC Macro-Financial Constants
 *
 * Canonical source for all GCC baseline values used across:
 * - Scenario engines (compute chain steps)
 * - Propagation engine (sector GDP base)
 * - Decision engine (DPS normalization)
 * - Insurance intelligence (exposure calculations)
 *
 * NEVER modify without updating golden test suite.
 * All values in $B USD unless otherwise noted.
 */

// ═══════════════════════════════════════════════
// BASES — GCC Macro-Financial Constants ($B)
// ═══════════════════════════════════════════════
export const BASES = {
  /** GCC annual oil revenue $B */
  oilRevenue: 540,
  /** GCC tourism revenue $B */
  tourismRevenue: 85,
  /** GCC airport passengers M/year */
  airportPax: 350,
  /** GCC port throughput M TEU */
  portTEU: 45,
  /** GCC shipping cost base $B */
  shippingCost: 12,
  /** GCC insurance market $B */
  insurancePremium: 28,
  /** GCC aviation fuel cost $B */
  aviationFuel: 42,
  /** Average GCC ticket price $ */
  baseTicket: 320,
  /** GCC commercial banking assets $B */
  bankingAssets: 2800,
  /** GCC central bank reserves $B */
  cbReserves: 780,
  /** GCC SWF total $B */
  swfAssets: 3500,
  /** GCC combined GDP $B */
  gccGDP: 2100,
  /** GCC power capacity GW */
  powerCapacity: 180,
  /** GCC desalination capacity B liters/day */
  desalCapacity: 22,
  /** GCC food imports $B/year */
  foodImports: 48,
  /** Saudi Hajj/Umrah revenue $B */
  hajjRevenue: 12,
  /** GCC FDI annual $B */
  fdiInflows: 35,
  /** Vision 2030 total committed $B */
  vision2030Budget: 1300,
} as const;

export type BasesKey = keyof typeof BASES;

// ═══════════════════════════════════════════════
// SECTOR GDP BASE — Layer economic weights ($B)
// ═══════════════════════════════════════════════
export type GCCLayer = 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society';

export const SECTOR_GDP_BASE: Record<GCCLayer, number> = {
  geography: 0,
  infrastructure: 210,
  economy: 950,
  finance: 380,
  society: 160,
} as const;

// ═══════════════════════════════════════════════
// HORMUZ ENGINE MULTIPLIERS
// ═══════════════════════════════════════════════
export const HORMUZ_MULTIPLIERS = {
  oilDrop: 0.85,
  shipSpike: 1.2,
  insSpike: 1.5,
  avFuel: 0.6,
  tourDrop: 0.45,
  gdpMultiplier: 0.65,
} as const;

// ═══════════════════════════════════════════════
// DPS NORMALIZATION DIVISORS
// ═══════════════════════════════════════════════
export const DPS_NORMALIZATION = {
  energy: 15,
  depth: 8,
  spread: 5,
  exposure: 80,
  stability: 1,
} as const;

// ═══════════════════════════════════════════════
// DPS WEIGHTS
// ═══════════════════════════════════════════════
export const DPS_WEIGHTS = {
  systemEnergy: 0.25,
  propagationDepth: 0.15,
  sectorSpread: 0.20,
  exposureScore: 0.25,
  stabilityRisk: 0.15,
} as const;

// ═══════════════════════════════════════════════
// APS COST MULTIPLIERS
// ═══════════════════════════════════════════════
export const APS_COST_MULTIPLIER: Record<string, number> = {
  low: 1.0,
  medium: 0.7,
  high: 0.4,
} as const;

// ═══════════════════════════════════════════════
// PHYSICS CONSTANTS
// ═══════════════════════════════════════════════
export const PHYSICS = {
  mu1: 0.35,
  rho: 0.72,
  alpha: 0.58,
  beta: 0.92,
} as const;

// ═══════════════════════════════════════════════
// GCC ASSET CLASS WEIGHTS
// Risk equation: R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U
// ═══════════════════════════════════════════════
export const GCC_ASSET_WEIGHTS: Record<string, [number, number, number, number, number, number]> = {
  airports: [0.27, 0.16, 0.19, 0.17, 0.11, 0.10],
  seaports: [0.24, 0.14, 0.22, 0.23, 0.09, 0.08],
  oilgas:   [0.30, 0.12, 0.18, 0.15, 0.13, 0.12],
  power:    [0.20, 0.18, 0.22, 0.15, 0.12, 0.13],
  telecom:  [0.15, 0.20, 0.25, 0.12, 0.14, 0.14],
  finance:  [0.18, 0.15, 0.20, 0.22, 0.15, 0.10],
  tourism:  [0.25, 0.18, 0.15, 0.12, 0.18, 0.12],
} as const;

// ═══════════════════════════════════════════════
// MONTE CARLO DEFAULTS
// ═══════════════════════════════════════════════
export const MONTE_CARLO = {
  defaultRuns: 500,
  weightNoise: 0.1,
  severityMin: 0.7,
  severityMax: 1.3,
} as const;

// ═══════════════════════════════════════════════
// DECISION ENGINE LIMITS
// ═══════════════════════════════════════════════
export const DECISION_LIMITS = {
  maxMarginalEffectiveness: 0.85,
  minDataReliability: 0.3,
  minScenarioCoherence: 0.4,
} as const;

// ═══════════════════════════════════════════════
// FRESHNESS & PROVENANCE
// ═══════════════════════════════════════════════
export { LAST_UPDATED, SOURCE_ATTRIBUTION, checkStaleness } from './freshness';
export type { SourceKey } from './freshness';
