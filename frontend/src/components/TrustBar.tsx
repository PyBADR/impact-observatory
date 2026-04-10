"use client";

/**
 * Impact Observatory | مرصد الأثر — Product Trust Bar
 *
 * Renders model version, confidence score, methodology, and deterministic
 * engine positioning. This is the first thing an enterprise client sees
 * after the headline — it establishes that the system is auditable,
 * versioned, and LLM-free in the core math path.
 */

import React from "react";
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
  },
  ar: {
    model: "النموذج",
    confidence: "الثقة",
    methodology: "المنهجية",
    engine: "محرك محاكاة حتمي",
    ai_note: "الذكاء الاصطناعي للتفسير فقط",
    pipeline: "خط أنابيب من 10 مراحل",
  },
};

function confidenceColor(value: number): string {
  if (value >= 0.8) return "text-emerald-600";
  if (value >= 0.6) return "text-amber-600";
  return "text-red-600";
}

export default function TrustBar({
  modelVersion,
  confidence,
  lang = "en",
}: {
  modelVersion: string;
  confidence: number;
  lang?: Language;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";

  return (
    <div
      className={`flex flex-wrap items-center gap-4 px-5 py-3 bg-io-surface border border-io-border rounded-xl shadow-sm text-xs ${isRTL ? "font-ar" : "font-sans"}`}
      dir={isRTL ? "rtl" : "ltr"}
    >
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

      {/* Spacer pushes engine badge to the right */}
      <div className="flex-1" />

      {/* Engine Badge */}
      <div className="flex items-center gap-2">
        <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 font-semibold rounded-lg border border-emerald-200 text-[11px] uppercase tracking-wide">
          {t.engine}
        </span>
        <span className="text-io-secondary italic">{t.ai_note}</span>
      </div>
    </div>
  );
}
