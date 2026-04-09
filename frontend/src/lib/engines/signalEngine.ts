import type { MacroInput, SignalOutput } from "@/types/decision";

/**
 * Transform raw macro indicators into normalized risk signals (0–1 range).
 * Pure function — no side effects, independently testable.
 */
export function generateSignals(macro: MacroInput): SignalOutput {
  return {
    inflationRisk: clamp(macro.inflation / 10),
    ratePressure: clamp(macro.interestRate / 10),
    growthSignal: clamp(macro.gdpGrowth / 10),
  };
}

function clamp(value: number, min = -1, max = 1): number {
  return Math.max(min, Math.min(max, value));
}
