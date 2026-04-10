"use client";

/**
 * Impact Observatory | مرصد الأثر — Trust Box (Layer 1)
 *
 * Always-visible trust surface: confidence, model version,
 * key assumptions (max 5), trace ID, methodology, engine badge.
 * Executive language — no raw JSON, no developer noise.
 */

import React, { useState } from "react";
import { safePercent } from "@/lib/format";
import type { Language } from "@/types/observatory";

const labels: Record<Language, Record<string, string>> = {
  en: {
    model: "Model",
    confidence: "Confidence",
    methodology: "Methodology",
    engine: "Deterministic Simulation Engine",
    ai_note: "AI for Interpretation Only",
    pipeline: "10-Stage Pipeline",
    trace: "Trace",
    assumptions: "Key Assumptions",
    show_assumptions: "Show Assumptions",
    hide_assumptions: "Hide",
  },
  ar: {
    model: "النموذج",
    confidence: "الثقة",
    methodology: "المنهجية",
    engine: "محرك محاكاة حتمي",
    ai_note: "الذكاء الاصطناعي للتفسير فقط",
    pipeline: "خط أنابيب من 10 مراحل",
    trace: "التتبع",
    assumptions: "الافتراضات الأساسية",
    show_assumptions: "عرض الافتراضات",
    hide_assumptions: "إخفاء",
  },
};

function confidenceColor(value: number): string {
  if (value >= 0.8) return "text-emerald-600";
  if (value >= 0.6) return "text-amber-600";
  return "text-red-600";
}

export default function TrustBox({
  modelVersion,
  confidence,
  assumptions = [],
  auditHash = "",
  runId = "",
  lang = "en",
}: {
  modelVersion: string;
  confidence: number;
  assumptions?: string[];
  auditHash?: string;
  runId?: string;
  lang?: Language;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";
  const [showAssumptions, setShowAssumptions] = useState(false);
  const traceDisplay = auditHash
    ? `${auditHash.slice(0, 8)}...${auditHash.slice(-6)}`
    : runId
    ? runId.slice(0, 12)
    : "—";

  return (
    <div
      className={`bg-io-surface border border-io-border rounded-xl shadow-sm ${isRTL ? "font-ar" : "font-sans"}`}
      dir={isRTL ? "rtl" : "ltr"}
    >
      {/* Main row — always visible */}
      <div className="flex flex-wrap items-center gap-4 px-5 py-3 text-xs">
        {/* Model Version */}
        <div className="flex items-center gap-1.5">
          <span className="text-io-secondary font-medium">{t.model}</span>
          <span className="px-2 py-0.5 bg-io-accent/10 text-io-accent font-bold rounded-md tabular-nums">
            v{modelVersion}
          </span>
        </div>

        <div className="w-px h-4 bg-io-border" />

        {/* Confidence Score */}
        <div className="flex items-center gap-1.5">
          <span className="text-io-secondary font-medium">{t.confidence}</span>
          <span className={`font-bold tabular-nums ${confidenceColor(confidence)}`}>
            {safePercent(confidence, 0)}
          </span>
        </div>

        <div className="w-px h-4 bg-io-border" />

        {/* Methodology */}
        <div className="flex items-center gap-1.5">
          <span className="text-io-secondary font-medium">{t.methodology}</span>
          <span className="text-io-primary font-medium">{t.pipeline}</span>
        </div>

        <div className="w-px h-4 bg-io-border" />

        {/* Trace ID */}
        <div className="flex items-center gap-1.5">
          <span className="text-io-secondary font-medium">{t.trace}</span>
          <span className="font-mono text-[10px] text-io-secondary bg-io-bg px-2 py-0.5 rounded">
            {traceDisplay}
          </span>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Engine Badge */}
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 font-semibold rounded-lg border border-emerald-200 text-[11px] uppercase tracking-wide">
            {t.engine}
          </span>
          <span className="text-io-secondary italic text-[10px]">{t.ai_note}</span>
        </div>

        {/* Assumptions toggle */}
        {assumptions.length > 0 && (
          <>
            <div className="w-px h-4 bg-io-border" />
            <button
              onClick={() => setShowAssumptions(!showAssumptions)}
              className="text-io-accent hover:text-io-accent/80 font-medium transition-colors"
            >
              {showAssumptions ? t.hide_assumptions : t.show_assumptions}
            </button>
          </>
        )}
      </div>

      {/* Assumptions drawer — expandable */}
      {showAssumptions && assumptions.length > 0 && (
        <div className="px-5 pb-3 border-t border-io-border/50">
          <p className="text-xs font-semibold text-io-secondary uppercase tracking-wider mt-3 mb-2">
            {t.assumptions}
          </p>
          <div className="space-y-1">
            {assumptions.slice(0, 5).map((a, i) => (
              <p key={i} className="text-xs text-io-primary pl-3 border-l-2 border-io-accent/30">
                {a}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
