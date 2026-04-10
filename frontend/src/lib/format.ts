/**
 * Impact Observatory | مرصد الأثر — Null-Safe Formatting Utilities
 *
 * Boundary guards for numeric and array formatting. These do NOT replace
 * root-cause fixes — they exist to prevent .toFixed() / .map() crashes
 * if any future schema drift occurs.
 *
 * Every feature component should import from this module instead of
 * calling .toFixed() directly.
 */

const FALLBACK = "—";

/**
 * Null-safe .toFixed() replacement.
 * Returns formatted string or fallback for undefined/null/NaN.
 */
export function safeFixed(
  value: unknown,
  digits = 1,
  fallback = FALLBACK
): string {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  return n.toFixed(digits);
}

/**
 * Null-safe percentage formatter.
 * Multiplies by 100 and appends "%". Returns fallback for non-numeric input.
 */
export function safePercent(
  value: unknown,
  digits = 1,
  fallback = FALLBACK
): string {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  return `${(n * 100).toFixed(digits)}%`;
}

/**
 * Format USD amounts with B/M/K suffixes.
 * Returns fallback for non-numeric input.
 */
export function formatUSD(value: unknown, fallback = FALLBACK): string {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${Math.round(n).toLocaleString()}`;
}

/**
 * Format hours into human-readable duration (h / d / mo).
 * Returns "N/A" for null/undefined (meaning: data not available).
 */
export function formatHours(value: unknown, fallback = "N/A"): string {
  if (value === null || value === undefined) return fallback;
  const h = Number(value);
  if (!isFinite(h)) return fallback;
  if (h >= 720) return `${Math.round(h / 720)}mo`;
  if (h >= 24) return `${Math.round(h / 24)}d`;
  return `${Math.round(h)}h`;
}

/**
 * Ensure value is an array. Returns empty array for non-array input.
 * Use at system boundaries to prevent .map() on undefined/null/object.
 */
export function safeArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  return [];
}

/**
 * Count true values in a breach flags object.
 * Backend returns breach_flags as {lcr_breach: bool, nsfr_breach: bool, ...}.
 * This converts to an integer count.
 */
export function countBreaches(flags: object | null | undefined): number {
  if (!flags || typeof flags !== "object") return 0;
  return Object.values(flags).filter((v) => v === true).length;
}

/**
 * Classify severity based on breach count.
 */
export function classifyByBreaches(
  breachCount: number,
  thresholds: { critical: number; elevated: number } = { critical: 3, elevated: 1 }
): "CRITICAL" | "ELEVATED" | "MODERATE" {
  if (breachCount >= thresholds.critical) return "CRITICAL";
  if (breachCount >= thresholds.elevated) return "ELEVATED";
  return "MODERATE";
}
