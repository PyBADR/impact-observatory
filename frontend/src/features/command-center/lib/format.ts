/**
 * Decision Command Center — Formatting Utilities
 *
 * All formatters are null/NaN/Infinity-safe. They return "—" for any
 * value that cannot be meaningfully displayed.
 */

export function formatUSD(value: number | null | undefined): string {
  if (value == null || !isFinite(value) || isNaN(value)) return "—";
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(0)}M`;
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(0)}K`;
  return `${sign}$${Math.round(abs).toLocaleString()}`;
}

export function formatPct(value: number | null | undefined, decimals = 0): string {
  if (value == null || !isFinite(value) || isNaN(value)) return "—";
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatHours(hours: number | null | undefined): string {
  if (hours == null || !isFinite(hours) || isNaN(hours)) return "—";
  if (hours >= 168) return `${Math.round(hours / 168)}w`;
  if (hours >= 24) return `${Math.round(hours / 24)}d`;
  return `${Math.round(hours)}h`;
}

export function stressToClassification(stress: number | null | undefined): "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL" | "UNKNOWN" {
  if (stress == null || !isFinite(stress) || isNaN(stress)) return "UNKNOWN";
  if (stress >= 0.80) return "CRITICAL";
  if (stress >= 0.65) return "ELEVATED";
  if (stress >= 0.50) return "MODERATE";
  if (stress >= 0.35) return "LOW";
  return "NOMINAL";
}

export function classificationColor(c: string | null | undefined): string {
  switch (c) {
    case "CRITICAL": return "#EF4444";
    case "ELEVATED": return "#F59E0B";
    case "MODERATE": return "#EAB308";
    case "LOW":      return "#22C55E";
    case "NOMINAL":  return "#64748B";
    case "UNKNOWN":  return "#94A3B8";
    default:         return "#94A3B8";
  }
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ts = new Date(iso).getTime();
  if (isNaN(ts)) return "—";
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/** Safe number coercion — returns fallback for null/undefined/NaN */
export function safeNum(value: unknown, fallback = 0): number {
  if (typeof value === "number" && isFinite(value)) return value;
  return fallback;
}

/** Safe string coercion — returns fallback for null/undefined/empty */
export function safeStr(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined) return fallback;
  const s = String(value).trim();
  return s.length === 0 ? fallback : s;
}

/** Safe date formatting — returns fallback string for invalid/missing dates */
export function safeDate(
  value: unknown,
  opts?: Intl.DateTimeFormatOptions,
  fallback = "—",
): string {
  if (!value) return fallback;
  const ts = new Date(String(value)).getTime();
  if (isNaN(ts)) return fallback;
  return new Date(ts).toLocaleString("en-US", opts ?? {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Safe array coercion — returns empty array for non-array values */
export function safeArr<T>(value: unknown): T[] {
  return Array.isArray(value) ? value : [];
}

// Re-export root-level safe formatters so command-center components
// can import everything from a single "../lib/format" path.
export { safeFixed, safePercent, formatUSD as safeFormatUSD } from "@/lib/format";
