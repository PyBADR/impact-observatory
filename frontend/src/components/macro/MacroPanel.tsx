"use client";

/**
 * MacroPanel — Compact macro-economic context display.
 *
 * Shows system risk index + top macro signals derived from scenario
 * simulation results. All signals are marked "simulated" in the UI.
 *
 * Renders at the top of DecisionRoomV2 to answer:
 *  "What macro conditions triggered this scenario?"
 *
 * Data source: macro_context block from API response (stage 41h).
 * Reuses existing MacroContext / MacroSignal types from observatory.ts.
 */

import { useMemo } from "react";
import type { MacroContext, MacroSignal } from "@/types/observatory";

// ── Bilingual labels ──────────────────────────────────────────────────────

const L = {
  title:      { en: "Macro Context",              ar: "السياق الاقتصادي الكلي" },
  sri:        { en: "System Risk",                 ar: "مخاطر النظام" },
  triggered:  { en: "Triggered by",                ar: "ناتج عن" },
  simulated:  { en: "Simulated",                   ar: "محاكاة" },
  noSignals:  { en: "No macro signals derived",    ar: "لم يتم استخلاص إشارات" },
} as const;

function t(key: keyof typeof L, locale: "en" | "ar"): string {
  return L[key][locale];
}

// ── Impact styling ────────────────────────────────────────────────────────

const IMPACT_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  high:   { bg: "bg-red-50",    text: "text-red-700",    dot: "bg-red-500" },
  medium: { bg: "bg-amber-50",  text: "text-amber-700",  dot: "bg-amber-500" },
  low:    { bg: "bg-slate-50",  text: "text-slate-600",  dot: "bg-slate-400" },
};

const SRI_COLORS: Record<string, { bg: string; text: string; label_en: string; label_ar: string }> = {
  severe:   { bg: "bg-red-600",    text: "text-white",    label_en: "SEVERE",   label_ar: "حرج" },
  high:     { bg: "bg-red-500",    text: "text-white",    label_en: "HIGH",     label_ar: "عالي" },
  elevated: { bg: "bg-amber-500",  text: "text-white",    label_en: "ELEVATED", label_ar: "مرتفع" },
  guarded:  { bg: "bg-amber-400",  text: "text-slate-800", label_en: "GUARDED", label_ar: "متحفظ" },
  low:      { bg: "bg-emerald-500", text: "text-white",   label_en: "LOW",      label_ar: "منخفض" },
  nominal:  { bg: "bg-slate-400",  text: "text-white",    label_en: "NOMINAL",  label_ar: "طبيعي" },
};

function sriLevel(score: number): keyof typeof SRI_COLORS {
  if (score >= 0.80) return "severe";
  if (score >= 0.65) return "high";
  if (score >= 0.50) return "elevated";
  if (score >= 0.35) return "guarded";
  if (score >= 0.20) return "low";
  return "nominal";
}

// ── Props ─────────────────────────────────────────────────────────────────

interface MacroPanelProps {
  macroContext?: MacroContext;
  locale: "en" | "ar";
}

// ── Component ─────────────────────────────────────────────────────────────

export function MacroPanel({ macroContext, locale }: MacroPanelProps) {
  const isAr = locale === "ar";

  const topSignals = useMemo(() => {
    if (!macroContext?.macro_signals) return [];
    return macroContext.macro_signals.slice(0, 4);
  }, [macroContext?.macro_signals]);

  if (!macroContext) return null;

  const sri = macroContext.system_risk_index;
  const level = sriLevel(sri);
  const sriStyle = SRI_COLORS[level];

  return (
    <div
      className="border border-slate-200 bg-white rounded-lg px-4 py-2.5"
      dir={isAr ? "rtl" : "ltr"}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left: Title + SRI badge */}
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            {t("title", locale)}
          </span>
          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold ${sriStyle.bg} ${sriStyle.text}`}>
            {t("sri", locale)}: {isAr ? sriStyle.label_ar : sriStyle.label_en}
            <span className="opacity-80 font-mono">({(sri * 100).toFixed(0)}%)</span>
          </span>
          {/* Simulated badge */}
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-500 font-medium">
            {t("simulated", locale)}
          </span>
        </div>

        {/* Right: Top signals inline */}
        <div className="flex items-center gap-2 overflow-x-auto">
          {topSignals.length === 0 && (
            <span className="text-[10px] text-slate-400">{t("noSignals", locale)}</span>
          )}
          {topSignals.map((sig) => {
            const style = IMPACT_STYLES[sig.impact] ?? IMPACT_STYLES.low;
            return (
              <div
                key={sig.name}
                className={`flex items-center gap-1.5 px-2 py-1 rounded ${style.bg} shrink-0`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
                <span className={`text-[10px] font-medium ${style.text}`}>
                  {isAr ? sig.name_ar : sig.name_en}
                </span>
                <span className={`text-[10px] font-bold tabular-nums ${style.text}`}>
                  {sig.value}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Trigger summary (subtle, below) */}
      {macroContext.trigger_summary_en && (
        <p className="mt-1.5 text-[10px] text-slate-400 leading-relaxed">
          {isAr ? macroContext.trigger_summary_ar : macroContext.trigger_summary_en}
        </p>
      )}
    </div>
  );
}

export default MacroPanel;
