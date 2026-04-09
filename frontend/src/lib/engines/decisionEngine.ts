import type { Entity, SignalOutput } from "@/types/decision";

/** Sector-specific risk weight adjustments */
const SECTOR_WEIGHTS: Record<string, number> = {
  Energy: 8,
  Retail: 4,
  Transport: 6,
  Finance: 7,
  Industrial: 5,
  Telecom: 2,
  Healthcare: 1,
};

/**
 * Evaluate risk score (0–100) for a single entity given macro signals.
 * Pure function — deterministic, no randomness.
 */
export function evaluateRisk(entity: Entity, signals: SignalOutput): number {
  const base = 50;

  const inflationImpact = signals.inflationRisk * 25;
  const rateImpact = signals.ratePressure * 18;
  const growthBenefit = signals.growthSignal * 15;

  const sectorAdjustment = SECTOR_WEIGHTS[entity.sector] ?? 3;

  // Higher coverage = more exposure = slightly more risk
  const coverageRisk = Math.log10(entity.coverage) * 1.5;

  const raw = base + inflationImpact + rateImpact - growthBenefit + sectorAdjustment + coverageRisk;

  return Math.round(Math.max(0, Math.min(100, raw)));
}

/**
 * Generate human-readable explanation of what drove the risk score.
 */
export function explainRisk(
  entity: Entity,
  signals: SignalOutput,
  riskScore: number,
  macro: { inflation: number; interestRate: number; gdpGrowth: number },
): string {
  const factors: string[] = [];

  if (signals.inflationRisk > 0.5) {
    factors.push(`High inflation (${macro.inflation}%) increases underwriting risk`);
  }
  if (signals.ratePressure > 0.6) {
    factors.push(`Elevated interest rate (${macro.interestRate}%) pressures debt servicing`);
  }
  if (signals.growthSignal < 0) {
    factors.push(`Negative GDP growth (${macro.gdpGrowth}%) signals economic contraction`);
  } else if (signals.growthSignal > 0.3) {
    factors.push(`Positive GDP growth (${macro.gdpGrowth}%) provides risk cushion`);
  }

  const sectorWeight = SECTOR_WEIGHTS[entity.sector] ?? 3;
  if (sectorWeight > 5) {
    factors.push(`${entity.sector} sector carries elevated macro sensitivity`);
  }

  if (factors.length === 0) {
    factors.push("Macro conditions within normal operating range");
  }

  return factors.join(". ") + `.`;
}
