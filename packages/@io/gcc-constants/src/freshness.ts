/**
 * @io/gcc-constants — Freshness & Provenance Tracking
 *
 * Tracks the last update date of constants and maps each constant
 * to its authoritative source. Critical for data governance and
 * identifying stale assumptions in scenario engines.
 */

// ═══════════════════════════════════════════════
// LAST UPDATED TIMESTAMP
// ═══════════════════════════════════════════════
export const LAST_UPDATED = "2026-03-31";

// ═══════════════════════════════════════════════
// SOURCE ATTRIBUTION
// Maps each constant family to its authoritative source
// ═══════════════════════════════════════════════
export const SOURCE_ATTRIBUTION = {
  // BASES sources
  oilRevenue: "OPEC Annual Statistical Bulletin",
  tourismRevenue: "GCC Tourism Board 2026 Report",
  airportPax: "Airports Council International (ACI)",
  portTEU: "Port Authority GCC Coordination Office",
  shippingCost: "IMF World Economic Outlook (Oct 2025)",
  insurancePremium: "GCC Insurance Federation",
  aviationFuel: "IATA Cost Index",
  baseTicket: "GCC Airlines Association",
  bankingAssets: "GCC Central Banks Survey",
  cbReserves: "IMF International Reserves Database",
  swfAssets: "SWF Institute Global Database",
  gccGDP: "GCC Stat (Gulf Cooperation Council)",
  powerCapacity: "IRENA Renewable Capacity Stats",
  desalCapacity: "GCC Water & Electricity Ministry",
  foodImports: "GCC Trade Statistics Portal",
  hajjRevenue: "Saudi General Authority for Statistics",
  fdiInflows: "UNCTAD World Investment Report",
  vision2030Budget: "Saudi Vision 2030 Council",

  // SECTOR_GDP_BASE sources
  geography: "GCC Stat Economic Classifications",
  infrastructure: "GCC Stat Economic Classifications",
  economy: "GCC Stat Economic Classifications",
  finance: "GCC Stat Economic Classifications",
  society: "GCC Stat Economic Classifications",

  // HORMUZ_MULTIPLIERS sources
  hormuzMultipliers: "Energy Security Bureau Stress Analysis",

  // DPS_NORMALIZATION sources
  dpsNormalization: "Decision Engine Empirical Calibration",

  // DPS_WEIGHTS sources
  dpsWeights: "Decision Engine Empirical Calibration",

  // APS_COST_MULTIPLIER sources
  apsCostMultiplier: "Analytical Priority Scoring Study (2025)",

  // PHYSICS sources
  physicsConstants: "GCC System Dynamics Research Lab",

  // GCC_ASSET_WEIGHTS sources
  gccAssetWeights: "Risk Assessment Framework v3.2",

  // MONTE_CARLO sources
  monteCarloDefaults: "Scenario Engine Best Practices",

  // DECISION_LIMITS sources
  decisionLimits: "Decision Engine Governance Board",
} as const;

export type SourceKey = keyof typeof SOURCE_ATTRIBUTION;

// ═══════════════════════════════════════════════
// STALENESS CHECK FUNCTION
// Returns freshness metadata for this constants snapshot
// ═══════════════════════════════════════════════

/**
 * Checks whether the constants snapshot is stale (>90 days old)
 * @returns Object with staleness status and time metrics
 */
export function checkStaleness() {
  const lastUpdatedDate = new Date(LAST_UPDATED);
  const today = new Date();

  // Calculate days since update
  const millisecondsSinceUpdate = today.getTime() - lastUpdatedDate.getTime();
  const daysSinceUpdate = Math.floor(millisecondsSinceUpdate / (1000 * 60 * 60 * 24));

  // Determine staleness threshold (90 days)
  const staleThreshold = 90;
  const isStale = daysSinceUpdate > staleThreshold;

  return {
    stale: isStale,
    daysSinceUpdate,
    lastUpdated: LAST_UPDATED,
    ...(isStale && {
      alert: `WARNING: Constants are ${daysSinceUpdate} days old (threshold: ${staleThreshold} days). Consider refreshing from authoritative sources.`,
    }),
  };
}
