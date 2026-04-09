import type { Entity } from "@/types/decision";

export type PolicyDecision = "APPROVED" | "REJECTED" | "CONDITIONAL";

interface PolicyResult {
  decision: PolicyDecision;
  policies: string[];
}

/**
 * Apply underwriting policy rules based on risk score and entity profile.
 * Pure function — deterministic rule evaluation.
 */
export function applyPolicies(riskScore: number, entity: Entity): PolicyResult {
  const policies: string[] = [];

  // Core risk thresholds
  if (riskScore > 80) {
    policies.push("RISK_CEILING_BREACH");
  }
  if (riskScore > 70) {
    policies.push("HIGH_RISK_FLAG");
  }
  if (riskScore > 50 && riskScore <= 70) {
    policies.push("CONDITIONAL_REVIEW_REQUIRED");
  }

  // Coverage-based rules
  if (entity.coverage > 1_000_000 && riskScore > 60) {
    policies.push("LARGE_EXPOSURE_REVIEW");
  }

  // Sector-specific rules
  if (entity.sector === "Energy" && riskScore > 55) {
    policies.push("ENERGY_SECTOR_WATCHLIST");
  }
  if (entity.sector === "Finance" && riskScore > 65) {
    policies.push("FINANCIAL_CONTAGION_CHECK");
  }

  const decision = getDecision(riskScore);

  return { decision, policies };
}

function getDecision(riskScore: number): PolicyDecision {
  if (riskScore > 75) return "REJECTED";
  if (riskScore > 55) return "CONDITIONAL";
  return "APPROVED";
}
