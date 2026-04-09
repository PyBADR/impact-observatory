/**
 * Format Utilities — Unit Tests
 *
 * Validates null/NaN/Infinity safety for all formatters,
 * correct USD formatting at all magnitude tiers,
 * stress classification thresholds, and edge cases.
 */

import { describe, it, expect } from "vitest";
import {
  formatUSD,
  formatPct,
  formatHours,
  stressToClassification,
  classificationColor,
  relativeTime,
  safeNum,
} from "../lib/format";

// ── formatUSD ────────────────────────────────────────────────────────────

describe("formatUSD", () => {
  it("formats trillions", () => {
    expect(formatUSD(1_200_000_000_000)).toBe("$1.2T");
  });
  it("formats billions", () => {
    expect(formatUSD(4_270_000_000)).toBe("$4.27B");
  });
  it("formats millions", () => {
    expect(formatUSD(120_000_000)).toBe("$120M");
  });
  it("formats thousands", () => {
    expect(formatUSD(45_000)).toBe("$45K");
  });
  it("formats small values", () => {
    expect(formatUSD(750)).toBe("$750");
  });
  it("handles negative values", () => {
    expect(formatUSD(-2_500_000_000)).toBe("-$2.50B");
  });
  it("returns — for null", () => {
    expect(formatUSD(null)).toBe("—");
  });
  it("returns — for undefined", () => {
    expect(formatUSD(undefined)).toBe("—");
  });
  it("returns — for NaN", () => {
    expect(formatUSD(NaN)).toBe("—");
  });
  it("returns — for Infinity", () => {
    expect(formatUSD(Infinity)).toBe("—");
  });
  it("returns — for -Infinity", () => {
    expect(formatUSD(-Infinity)).toBe("—");
  });
  it("handles zero", () => {
    expect(formatUSD(0)).toBe("$0");
  });
});

// ── formatPct ────────────────────────────────────────────────────────────

describe("formatPct", () => {
  it("formats 0.84 as 84%", () => {
    expect(formatPct(0.84)).toBe("84%");
  });
  it("formats with decimals", () => {
    expect(formatPct(0.847, 1)).toBe("84.7%");
  });
  it("formats 1.0 as 100%", () => {
    expect(formatPct(1.0)).toBe("100%");
  });
  it("formats 0 as 0%", () => {
    expect(formatPct(0)).toBe("0%");
  });
  it("returns — for null", () => {
    expect(formatPct(null)).toBe("—");
  });
  it("returns — for NaN", () => {
    expect(formatPct(NaN)).toBe("—");
  });
  it("returns — for undefined", () => {
    expect(formatPct(undefined)).toBe("—");
  });
});

// ── formatHours ──────────────────────────────────────────────────────────

describe("formatHours", () => {
  it("formats weeks", () => {
    expect(formatHours(336)).toBe("2w");
  });
  it("formats days", () => {
    expect(formatHours(72)).toBe("3d");
  });
  it("formats hours", () => {
    expect(formatHours(18)).toBe("18h");
  });
  it("returns — for null", () => {
    expect(formatHours(null)).toBe("—");
  });
  it("returns — for NaN", () => {
    expect(formatHours(NaN)).toBe("—");
  });
  it("168h = 1w boundary", () => {
    expect(formatHours(168)).toBe("1w");
  });
});

// ── stressToClassification ───────────────────────────────────────────────

describe("stressToClassification", () => {
  it("classifies ≥ 0.80 as CRITICAL", () => {
    expect(stressToClassification(0.80)).toBe("CRITICAL");
    expect(stressToClassification(0.95)).toBe("CRITICAL");
  });
  it("classifies 0.65–0.79 as ELEVATED", () => {
    expect(stressToClassification(0.65)).toBe("ELEVATED");
    expect(stressToClassification(0.79)).toBe("ELEVATED");
  });
  it("classifies 0.50–0.64 as MODERATE", () => {
    expect(stressToClassification(0.50)).toBe("MODERATE");
    expect(stressToClassification(0.64)).toBe("MODERATE");
  });
  it("classifies 0.35–0.49 as LOW", () => {
    expect(stressToClassification(0.35)).toBe("LOW");
    expect(stressToClassification(0.49)).toBe("LOW");
  });
  it("classifies < 0.35 as NOMINAL", () => {
    expect(stressToClassification(0.20)).toBe("NOMINAL");
    expect(stressToClassification(0.0)).toBe("NOMINAL");
  });
  it("returns NOMINAL for null/NaN", () => {
    expect(stressToClassification(null)).toBe("NOMINAL");
    expect(stressToClassification(undefined)).toBe("NOMINAL");
    expect(stressToClassification(NaN)).toBe("NOMINAL");
  });
});

// ── classificationColor ──────────────────────────────────────────────────

describe("classificationColor", () => {
  it("returns red for CRITICAL", () => {
    expect(classificationColor("CRITICAL")).toBe("#EF4444");
  });
  it("returns amber for ELEVATED", () => {
    expect(classificationColor("ELEVATED")).toBe("#F59E0B");
  });
  it("returns slate for unknown", () => {
    expect(classificationColor("UNKNOWN")).toBe("#64748B");
  });
  it("returns slate for null", () => {
    expect(classificationColor(null)).toBe("#64748B");
  });
  it("returns slate for undefined", () => {
    expect(classificationColor(undefined)).toBe("#64748B");
  });
});

// ── relativeTime ─────────────────────────────────────────────────────────

describe("relativeTime", () => {
  it("returns — for null", () => {
    expect(relativeTime(null)).toBe("—");
  });
  it("returns — for invalid ISO", () => {
    expect(relativeTime("not-a-date")).toBe("—");
  });
  it("returns 'just now' for current time", () => {
    expect(relativeTime(new Date().toISOString())).toBe("just now");
  });
  it("returns minutes ago", () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60_000).toISOString();
    expect(relativeTime(fiveMinAgo)).toBe("5m ago");
  });
});

// ── safeNum ──────────────────────────────────────────────────────────────

describe("safeNum", () => {
  it("returns number for valid input", () => {
    expect(safeNum(42)).toBe(42);
  });
  it("returns fallback for null", () => {
    expect(safeNum(null, 0)).toBe(0);
  });
  it("returns fallback for NaN", () => {
    expect(safeNum(NaN, -1)).toBe(-1);
  });
  it("returns fallback for string", () => {
    expect(safeNum("hello", 0)).toBe(0);
  });
  it("returns fallback for Infinity", () => {
    expect(safeNum(Infinity, 0)).toBe(0);
  });
});
