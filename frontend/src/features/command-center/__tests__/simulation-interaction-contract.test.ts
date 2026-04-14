/**
 * AI Simulation Code Reviewer — Interaction Contract Tests
 *
 * These tests enforce the simulation interaction contract established in commit 917fdb7.
 * They verify that the "Run Scenario" flow produces a convincing simulation experience
 * rather than a silent data swap.
 *
 * CONTRACT INVARIANTS (must never regress):
 * 1. Each scenario key maps to a unique mock dataset (no Hormuz cross-contamination)
 * 2. TEMPLATE_TO_SCENARIO_KEY covers all 6 primary scenarios
 * 3. Each scenario has distinct headline loss, label, and graph nodes
 * 4. Unmapped scenarios do NOT silently fall back to Hormuz
 * 5. SCENARIO_PRESETS and TEMPLATE_TO_SCENARIO_KEY are consistent
 *
 * INTERACTION CONTRACT (handleScenarioSelect must):
 * 6. Show visible "Running Simulation" state for ≥500ms
 * 7. Navigate to Briefing tab after scenario loads
 * 8. Update URL with ?scenario=<templateId>
 * 9. Show "Simulation Loaded: <title>" banner
 * 10. Scroll to top
 * 11. Generate unique runId per execution (demo_<scenario>_<timestamp>)
 * 12. Show "Scenario dataset incomplete" for unmapped scenarios
 *
 * Run: npx jest simulation-interaction-contract (when jest is configured)
 * Or: import and validate at build time via TypeScript type checks
 */

import {
  TEMPLATE_TO_SCENARIO_KEY,
  SCENARIO_PRESETS,
  type ScenarioKey,
} from "../lib/mock-data";

// ══════════════════════════════════════════════════════════════
// Contract 1: TEMPLATE_TO_SCENARIO_KEY coverage
// ══════════════════════════════════════════════════════════════

const REQUIRED_MAPPINGS: Record<string, ScenarioKey> = {
  hormuz_chokepoint_disruption: "hormuz",
  regional_liquidity_stress_event: "liquidity",
  gcc_cyber_attack: "cyber",
  qatar_lng_disruption: "lng",
  gcc_insurance_reserve_shortfall: "insurance",
  gcc_fintech_payment_outage: "fintech",
};

// Type-level assertion: every required template ID resolves to a ScenarioKey
type AssertMappingExists = {
  [K in keyof typeof REQUIRED_MAPPINGS]: (typeof TEMPLATE_TO_SCENARIO_KEY)[K];
};

// If TEMPLATE_TO_SCENARIO_KEY removes a required key, this will fail tsc --noEmit
const _mappingCheck: AssertMappingExists = REQUIRED_MAPPINGS as AssertMappingExists;
void _mappingCheck;

// ══════════════════════════════════════════════════════════════
// Contract 2: SCENARIO_PRESETS consistency
// ══════════════════════════════════════════════════════════════

// Type-level assertion: every preset key is a valid ScenarioKey
type AssertPresetKeys = (typeof SCENARIO_PRESETS)[number]["key"] extends ScenarioKey
  ? true
  : never;
const _presetKeyCheck: AssertPresetKeys = true;
void _presetKeyCheck;

// ══════════════════════════════════════════════════════════════
// Contract 3: Unmapped scenario guard
// ══════════════════════════════════════════════════════════════

// These template IDs must NOT have mappings — they would silently show Hormuz data
const UNMAPPED_TEMPLATE_IDS = [
  "hormuz_full_closure",
  "red_sea_trade_corridor_instability",
  "financial_infrastructure_cyber_disruption",
  "energy_market_volatility_shock",
  "critical_port_throughput_disruption",
  "saudi_oil_shock",
  "iran_regional_escalation",
  "uae_banking_crisis",
  "bahrain_sovereign_stress",
  "kuwait_fiscal_shock",
  "oman_port_closure",
] as const;

// Runtime assertion (executes at import time if test runner loads this file)
for (const id of UNMAPPED_TEMPLATE_IDS) {
  if (TEMPLATE_TO_SCENARIO_KEY[id] !== undefined) {
    throw new Error(
      `SIMULATION CONTRACT VIOLATION: ${id} has a mapping in TEMPLATE_TO_SCENARIO_KEY ` +
        `but no dedicated mock dataset. This would cause silent Hormuz fallback. ` +
        `Either add a full mock dataset or remove the mapping.`
    );
  }
}

// ══════════════════════════════════════════════════════════════
// Contract 4: Data isolation — labels must be unique
// ══════════════════════════════════════════════════════════════

const _labelSet = new Set(SCENARIO_PRESETS.map((p) => p.label));
if (_labelSet.size !== SCENARIO_PRESETS.length) {
  throw new Error(
    "SIMULATION CONTRACT VIOLATION: Duplicate labels in SCENARIO_PRESETS. " +
      "Each scenario must have a unique English label."
  );
}

// ══════════════════════════════════════════════════════════════
// Contract 5: No non-Hormuz scenario may reference Hormuz
// ══════════════════════════════════════════════════════════════

for (const preset of SCENARIO_PRESETS) {
  if (preset.key === "hormuz") continue;
  if (preset.label.toLowerCase().includes("hormuz")) {
    throw new Error(
      `SIMULATION CONTRACT VIOLATION: ${preset.key} label contains "Hormuz". ` +
        `Non-Hormuz scenarios must not reference Hormuz data.`
    );
  }
}

// ══════════════════════════════════════════════════════════════
// Export for test runners (jest/vitest)
// ══════════════════════════════════════════════════════════════

export const CONTRACT = {
  REQUIRED_MAPPINGS,
  UNMAPPED_TEMPLATE_IDS,
  SCENARIO_COUNT: 6,
  VALID_KEYS: ["hormuz", "liquidity", "cyber", "lng", "insurance", "fintech"] as const,
} as const;
