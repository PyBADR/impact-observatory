/**
 * Impact Observatory | مرصد الأثر
 * Safe number formatters — never throw on null/undefined/NaN.
 * Use these instead of raw .toFixed() calls throughout the codebase.
 */

/**
 * Format a number to fixed decimal places.
 * Returns `fallback` for null / undefined / NaN values.
 */
export function fmt(
  value: number | null | undefined,
  decimals = 2,
  fallback = "—"
): string {
  if (value === null || value === undefined || !isFinite(value)) return fallback;
  return value.toFixed(decimals);
}

/**
 * Format a 0-1 fraction as a percentage string, e.g. 0.734 → "73.4%"
 */
export function fmtPct(
  value: number | null | undefined,
  decimals = 1,
  fallback = "0%"
): string {
  if (value === null || value === undefined || !isFinite(value)) return fallback;
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format a 0-1 fraction multiplied by 100, e.g. 0.734 → "73.4%"
 */
export function fmtFracPct(
  value: number | null | undefined,
  decimals = 1,
  fallback = "0%"
): string {
  if (value === null || value === undefined || !isFinite(value)) return fallback;
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a USD amount with B/M/K suffix.
 */
export function fmtUSD(
  value: number | null | undefined,
  fallback = "$0"
): string {
  if (value === null || value === undefined || !isFinite(value)) return fallback;
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${Math.round(value)}`;
}

/**
 * Safe toFixed — replaces raw `x.toFixed(n)` calls.
 * Equivalent to `(value ?? 0).toFixed(decimals)` but also handles NaN/Infinity.
 */
export function safeFixed(
  value: number | null | undefined,
  decimals = 2,
  fallback = "0"
): string {
  if (value === null || value === undefined || !isFinite(value)) {
    return Number(0).toFixed(decimals) || fallback;
  }
  return value.toFixed(decimals);
}
