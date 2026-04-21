"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import type { Locale } from "@/i18n/dictionary";
import { useTraceImpactScenario } from "../lib/trace-impact-context";

const SEVERITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: "bg-io-status-severe/10", text: "text-io-status-severe", border: "border-io-status-severe/30" },
  ELEVATED: { bg: "bg-io-status-elevated/10", text: "text-io-status-elevated", border: "border-io-status-elevated/30" },
  HIGH:     { bg: "bg-io-status-high/10",     text: "text-io-status-high",     border: "border-io-status-high/30" },
  MODERATE: { bg: "bg-io-status-guarded/10",  text: "text-io-status-guarded",  border: "border-io-status-guarded/30" },
  LOW:      { bg: "bg-io-status-low/10",      text: "text-io-status-low",      border: "border-io-status-low/30" },
};

interface ShockStepProps {
  locale: Locale;
  /** Live headline total loss, overrides demo if provided */
  totalLossUsd?: number | null;
}

/**
 * HERO IMPACT
 * ─────────────────────────────────────
 * Primary:   one dominant loss number (cinematic, 7xl)
 * Secondary: horizon pill · confidence pill
 * Minimal:   severity badge · scenario name
 */
export function ShockStep({ locale, totalLossUsd }: ShockStepProps) {
  const s = useTraceImpactScenario();
  const isAr = locale === "ar";
  const sev = SEVERITY_COLORS[s.severityLabel.toUpperCase()] ?? SEVERITY_COLORS.ELEVATED;

  const displayLoss =
    totalLossUsd != null
      ? `$${(totalLossUsd / 1e9).toFixed(1)}B`
      : s.financialRanges.withoutAction.base;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className={`max-w-3xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[70vh] ${isAr ? "text-right" : "text-left"}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Minimal: severity + scenario */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex items-center gap-2 mb-10 ${isAr ? "flex-row-reverse" : ""}`}
      >
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-badge text-[10px] font-bold tracking-wider uppercase border ${sev.bg} ${sev.text} ${sev.border}`}
        >
          <AlertTriangle className="w-3 h-3" />
          {s.severityLabel.toUpperCase()}
        </span>
        <span className="text-xs text-io-tertiary font-medium">
          {isAr ? s.nameAr : s.name}
        </span>
      </motion.div>

      {/* PRIMARY — dominant loss number */}
      <motion.div
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.55, ease: "easeOut", delay: 0.15 }}
        className="text-center mb-2"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-io-tertiary mb-3">
          {isAr ? "الخسارة المتوقعة" : "Projected Loss"}
        </p>
        <p
          className="font-bold text-io-status-severe leading-none tabular-nums"
          style={{ fontSize: "clamp(4.5rem, 12vw, 8rem)" }}
        >
          {displayLoss}
        </p>
      </motion.div>

      {/* Single subline — shock headline (replaces detail cells + transmission headline) */}
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.45 }}
        className="max-w-xl text-center text-sm text-io-secondary leading-relaxed mb-10"
      >
        {s.shock.headline}
      </motion.p>

      {/* SECONDARY — horizon + confidence as compact pills */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.6 }}
        className={`flex items-center gap-3 ${isAr ? "flex-row-reverse" : ""}`}
      >
        <div className="flex items-baseline gap-2 px-4 py-2 rounded-full border border-io-border bg-io-surface shadow-quiet">
          <span className="text-sm font-bold text-io-primary tabular-nums">{s.timeHorizon}</span>
          <span className="text-[10px] uppercase tracking-wider text-io-tertiary font-semibold">
            {isAr ? "الأفق" : "Horizon"}
          </span>
        </div>
        <div className="flex items-baseline gap-2 px-4 py-2 rounded-full border border-io-border bg-io-surface shadow-quiet">
          <span className="text-sm font-bold text-io-accent tabular-nums">
            {Math.round(s.confidence * 100)}%
          </span>
          <span className="text-[10px] uppercase tracking-wider text-io-tertiary font-semibold">
            {isAr ? "الثقة" : "Confidence"}
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}
