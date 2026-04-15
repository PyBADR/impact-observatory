"use client";

/**
 * AdvisorySignalPanel — v5 advisory-only signal context panel.
 *
 * Visible ONLY when NEXT_PUBLIC_ENABLE_SIGNAL_ADVISORY_V5=true.
 * Collapsed by default. Does NOT affect scenario scoring.
 *
 * Wording rules:
 *   - "Advisory only — metrics unchanged"
 *   - "Scoring not applied"
 *   - "Signal explains context, not outcome"
 *   - Never says "real-time", "live intelligence", or "live alert"
 */

import React, { useState } from "react";
import { Info, ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";
import type { SignalAdvisory } from "@/types/signal-snapshot";

// ── Feature gate ─────────────────────────────────────────────────────

const ADVISORY_V5_ENABLED =
  process.env.NEXT_PUBLIC_ENABLE_SIGNAL_ADVISORY_V5 === "true";

// ── Static fixture advisories (mirrors backend sample signals) ──────

const FIXTURE_ADVISORIES: SignalAdvisory[] = [
  {
    advisory_id: "adv_fixture_01",
    scenario_id: "hormuz_chokepoint_disruption",
    snapshot_id: "snap_fixture_01",
    source_id: "sig_sample_static",
    confidence: 0.25,
    freshness_status: "expired",
    advisory_text:
      'Signal "Brent crude rises 3% on Hormuz tension reports" was evaluated but did not meet confidence or freshness thresholds (Signal expired). Displayed as background context only — no metrics changed.',
    risk_context:
      "This signal relates to the energy, maritime sector(s) and may provide additional context for assessing the Strait of Hormuz Disruption scenario.",
    suggested_review:
      "Signal confidence is below threshold or data is stale. Treat as background context only. No action required.",
    metric_before: 3200000000,
    metric_after: 3200000000,
    scoring_applied: false,
    fallback_used: true,
    timestamp: "2026-04-15T12:00:00Z",
  },
  {
    advisory_id: "adv_fixture_02",
    scenario_id: "uae_banking_crisis",
    snapshot_id: "snap_fixture_02",
    source_id: "sig_sample_static",
    confidence: 0.45,
    freshness_status: "stale",
    advisory_text:
      'Signal "CBUAE holds rates steady, flags regional liquidity tightening" was evaluated but did not meet confidence or freshness thresholds (Signal is stale). Displayed as background context only — no metrics changed.',
    risk_context:
      "This signal relates to the banking, fintech sector(s) and may provide additional context for assessing the UAE Banking System Stress scenario.",
    suggested_review:
      "Signal confidence is below threshold or data is stale. Treat as background context only. No action required.",
    metric_before: 1800000000,
    metric_after: 1800000000,
    scoring_applied: false,
    fallback_used: true,
    timestamp: "2026-04-15T12:00:00Z",
  },
];

// ── Helpers ───────────────────────────────────────────────────────────

function confidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "text-emerald-600";
  if (confidence >= 0.5) return "text-blue-600";
  if (confidence >= 0.35) return "text-amber-600";
  return "text-red-500";
}

// ── Component ─────────────────────────────────────────────────────────

interface AdvisorySignalPanelProps {
  locale?: "en" | "ar";
}

export function AdvisorySignalPanel({ locale = "en" }: AdvisorySignalPanelProps) {
  const [expanded, setExpanded] = useState(false);

  // Gate: only render if advisory v5 flag is true
  if (!ADVISORY_V5_ENABLED) {
    return null;
  }

  const isAr = locale === "ar";
  const advisories = FIXTURE_ADVISORIES;

  return (
    <div className="mx-6 mb-3" dir={isAr ? "rtl" : "ltr"}>
      {/* Collapsed header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2">
          <Info size={14} className="text-amber-600" />
          <span className="text-[11px] font-semibold text-amber-800 tracking-wide uppercase">
            {isAr ? "سياق الإشارة الاستشارية" : "Advisory Signal Context"}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-200 text-amber-800 font-medium">
            {isAr ? "استشاري فقط" : "Advisory only"}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-amber-600">
            {advisories.length} {isAr ? "إشارات" : "signals"}
          </span>
          {expanded ? (
            <ChevronUp size={12} className="text-amber-500" />
          ) : (
            <ChevronDown size={12} className="text-amber-500" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-1 px-4 py-3 bg-white border border-amber-200 border-t-0 rounded-b-lg space-y-3">
          {/* Status bar */}
          <div className="flex items-center gap-4 text-[10px] text-amber-600">
            <span className="flex items-center gap-1">
              <ShieldCheck size={10} />
              {isAr ? "استشاري فقط — المقاييس لم تتغير" : "Advisory only — metrics unchanged"}
            </span>
            <span className="text-amber-300">|</span>
            <span>
              {isAr ? "التسجيل غير مطبق" : "Scoring not applied"}
            </span>
            <span className="text-amber-300">|</span>
            <span>
              {isAr ? "الإشارة تشرح السياق، لا النتيجة" : "Signal explains context, not outcome"}
            </span>
          </div>

          {/* Advisory list */}
          {advisories.map((adv) => (
            <div
              key={adv.advisory_id}
              className="border border-slate-150 rounded-lg p-3 space-y-1.5"
            >
              <p className="text-xs text-slate-700">
                {adv.advisory_text}
              </p>
              <p className="text-[11px] text-slate-500 italic">
                {adv.risk_context}
              </p>
              <div className="flex items-center gap-3 text-[10px] text-slate-400">
                <span>
                  {isAr ? "الثقة" : "Confidence"}:{" "}
                  <span className={`font-semibold tabular-nums ${confidenceColor(adv.confidence)}`}>
                    {(adv.confidence * 100).toFixed(0)}%
                  </span>
                </span>
                <span>
                  {isAr ? "التسجيل" : "Scoring"}:{" "}
                  <span className="font-semibold text-slate-600">
                    {adv.scoring_applied ? "Applied" : "Not applied"}
                  </span>
                </span>
                {adv.fallback_used && (
                  <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">
                    {isAr ? "احتياطي" : "Fallback"}
                  </span>
                )}
              </div>
            </div>
          ))}

          {/* Footer */}
          <div className="pt-2 border-t border-amber-100">
            <p className="text-[10px] text-amber-500">
              {isAr
                ? "استشاري فقط — لا تؤثر على حسابات السيناريو. التسجيل غير مطبق. الإشارة تشرح السياق، لا النتيجة."
                : "Advisory only — metrics unchanged. Scoring not applied. Signal explains context, not outcome."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
