/**
 * Frontend Data Sanity Guard
 *
 * Prevents invalid values from rendering in the UI.
 * Catches: sentinel hours (9999), percentages >100%, NaN/Infinity, negative losses.
 *
 * Applied defensively at render boundaries — never at data fetch level.
 */

/** Replace 9999h sentinel with null (display as "N/A" or "—") */
export function sanitizeHours(v: number | null | undefined): number | null {
  if (v == null || !Number.isFinite(v)) return null;
  if (v >= 9999) return null;
  if (v < 0) return 0;
  return Math.min(v, 8760); // cap at 1 year
}

/** Format hours with sentinel handling */
export function fmtHours(v: number | null | undefined): string {
  const safe = sanitizeHours(v);
  if (safe === null) return "—";
  if (safe <= 1) return `${Math.round(safe * 60)}m`;
  if (safe < 24) return `${safe.toFixed(1)}h`;
  return `${Math.round(safe / 24)}d`;
}

/** Ensure percentage is 0-100, replacing overflows */
export function sanitizePct(v: number | null | undefined): number {
  if (v == null || !Number.isFinite(v)) return 0;
  return Math.max(0, Math.min(100, v));
}

/** Ensure 0-1 score, replacing overflows */
export function sanitizeScore(v: number | null | undefined): number {
  if (v == null || !Number.isFinite(v)) return 0;
  return Math.max(0, Math.min(1, v));
}

/** Ensure non-negative USD value */
export function sanitizeUsd(v: number | null | undefined): number {
  if (v == null || !Number.isFinite(v)) return 0;
  return Math.max(0, v);
}

/** Ensure ROI ratio is sane (max 50x) */
export function sanitizeRoi(v: number | null | undefined): number {
  if (v == null || !Number.isFinite(v)) return 0;
  return Math.max(-50, Math.min(50, v));
}
