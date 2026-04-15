"use client";

/**
 * DevSignalPreview — Dev-only signal snapshot preview panel.
 *
 * Visible ONLY when NEXT_PUBLIC_ENABLE_DEV_SIGNAL_PREVIEW=true.
 * Shows latest signal snapshots from the RSS fixture connector.
 * Collapsed by default. Does NOT affect scenario scoring.
 *
 * Wording rules:
 *   - Never says "real-time" or "live intelligence"
 *   - Uses: "dev fixture", "read-only", "no scoring impact"
 */

import React, { useState, useMemo } from "react";
import { Radio, ChevronDown, ChevronUp, FileText, Clock } from "lucide-react";
import type { SignalSnapshot, SnapshotFreshness } from "@/types/signal-snapshot";

// ── Feature gate ─────────────────────────────────────────────────────

const DEV_PREVIEW_ENABLED =
  process.env.NEXT_PUBLIC_ENABLE_DEV_SIGNAL_PREVIEW === "true";

// ── Static fixture snapshots (mirrors backend RSS fixture) ──────────

const FIXTURE_SNAPSHOTS: SignalSnapshot[] = [
  {
    snapshot_id: "snap_fixture_01",
    source_id: "sig_rss_pilot",
    title: "Brent crude rises 3% on Hormuz tension reports",
    summary:
      "Oil prices climbed after reports of increased military activity near the Strait of Hormuz.",
    url: null,
    published_at: "2026-04-10T08:30:00Z",
    ingested_at: "2026-04-15T12:00:00Z",
    freshness_status: "expired",
    confidence_score: 0.225,
    related_scenarios: [
      "hormuz_chokepoint_disruption",
      "energy_market_volatility_shock",
    ],
    related_countries: ["UAE", "SAUDI", "QATAR"],
    related_sectors: ["energy", "maritime"],
    raw_metadata: {},
  },
  {
    snapshot_id: "snap_fixture_02",
    source_id: "sig_rss_pilot",
    title: "CBUAE holds rates steady, flags regional liquidity tightening",
    summary:
      "The Central Bank of the UAE maintained its benchmark rate but warned of tightening liquidity.",
    url: null,
    published_at: "2026-04-12T14:00:00Z",
    ingested_at: "2026-04-15T12:00:00Z",
    freshness_status: "stale",
    confidence_score: 0.45,
    related_scenarios: [
      "uae_banking_crisis",
      "regional_liquidity_stress_event",
    ],
    related_countries: ["UAE"],
    related_sectors: ["banking", "fintech"],
    raw_metadata: {},
  },
  {
    snapshot_id: "snap_fixture_03",
    source_id: "sig_rss_pilot",
    title: "Qatar LNG shipments rerouted via Cape of Good Hope",
    summary:
      "Several Qatar LNG carriers diverted, adding 12-15 days transit time.",
    url: null,
    published_at: "2026-04-08T11:15:00Z",
    ingested_at: "2026-04-15T12:00:00Z",
    freshness_status: "expired",
    confidence_score: 0.225,
    related_scenarios: [
      "qatar_lng_disruption",
      "red_sea_trade_corridor_instability",
    ],
    related_countries: ["QATAR"],
    related_sectors: ["energy", "maritime", "logistics"],
    raw_metadata: {},
  },
];

// ── Helpers ───────────────────────────────────────────────────────────

function freshnessColor(status: SnapshotFreshness): string {
  switch (status) {
    case "fresh":
      return "text-emerald-600";
    case "recent":
      return "text-blue-600";
    case "stale":
      return "text-amber-600";
    case "expired":
      return "text-red-500";
    default:
      return "text-slate-500";
  }
}

function freshnessLabel(status: SnapshotFreshness): string {
  switch (status) {
    case "fresh":
      return "Fresh";
    case "recent":
      return "Recent";
    case "stale":
      return "Stale";
    case "expired":
      return "Expired";
    default:
      return "Unknown";
  }
}

// ── Component ─────────────────────────────────────────────────────────

interface DevSignalPreviewProps {
  locale?: "en" | "ar";
}

export function DevSignalPreview({ locale = "en" }: DevSignalPreviewProps) {
  const [expanded, setExpanded] = useState(false);

  // Gate: only render if dev preview flag is true
  if (!DEV_PREVIEW_ENABLED) {
    return null;
  }

  const isAr = locale === "ar";
  const snapshots = FIXTURE_SNAPSHOTS;

  return (
    <div className="mx-6 mb-3" dir={isAr ? "rtl" : "ltr"}>
      {/* Collapsed header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2">
          <Radio size={14} className="text-indigo-500" />
          <span className="text-[11px] font-semibold text-indigo-700 tracking-wide uppercase">
            {isAr ? "معاينة الإشارات — تطوير" : "Signal Preview — Dev"}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-200 text-indigo-700 font-medium">
            {isAr ? "بيانات تجريبية" : "Dev fixture"}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-indigo-500">
            {snapshots.length} {isAr ? "لقطات" : "snapshots"}
          </span>
          {expanded ? (
            <ChevronUp size={12} className="text-indigo-400" />
          ) : (
            <ChevronDown size={12} className="text-indigo-400" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-1 px-4 py-3 bg-white border border-indigo-200 border-t-0 rounded-b-lg space-y-3">
          {/* Status bar */}
          <div className="flex items-center gap-4 text-[10px] text-indigo-500">
            <span>
              Source: <span className="font-semibold">Dev fixture (RSS)</span>
            </span>
            <span className="text-indigo-300">|</span>
            <span>
              Scoring impact: <span className="font-semibold">None</span>
            </span>
            <span className="text-indigo-300">|</span>
            <span>
              Live feeds: <span className="font-semibold">Not connected</span>
            </span>
          </div>

          {/* Snapshot list */}
          {snapshots.map((snap) => (
            <div
              key={snap.snapshot_id}
              className="border border-slate-150 rounded-lg p-3 space-y-1.5"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5 min-w-0">
                  <FileText size={12} className="text-slate-400 flex-shrink-0" />
                  <p className="text-xs font-semibold text-slate-800 truncate">
                    {snap.title}
                  </p>
                </div>
                <span
                  className={`text-[10px] font-bold flex-shrink-0 ${freshnessColor(snap.freshness_status)}`}
                >
                  {freshnessLabel(snap.freshness_status)}
                </span>
              </div>
              <p className="text-[11px] text-slate-600 line-clamp-2">
                {snap.summary}
              </p>
              <div className="flex items-center gap-3 text-[10px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock size={10} />
                  {new Date(snap.published_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
                <span>
                  Confidence:{" "}
                  <span className="font-semibold tabular-nums">
                    {(snap.confidence_score * 100).toFixed(0)}%
                  </span>
                </span>
                {snap.related_scenarios.length > 0 && (
                  <span className="truncate">
                    Scenarios: {snap.related_scenarios.slice(0, 2).join(", ")}
                  </span>
                )}
              </div>
            </div>
          ))}

          {/* Footer */}
          <div className="pt-2 border-t border-indigo-100">
            <p className="text-[10px] text-indigo-400">
              {isAr
                ? "معاينة بيانات تجريبية — لا تؤثر على حسابات السيناريو. مصادر البيانات الحية غير متصلة."
                : "Dev fixture preview — does not affect scenario scoring. Live feeds not connected."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
