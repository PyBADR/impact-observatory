"use client";

import { motion } from "framer-motion";
import { Clock } from "lucide-react";
import { BeforeAfterDecisionPanel } from "../components/BeforeAfterDecisionPanel";
import type { Locale } from "@/i18n/dictionary";
import { useTraceImpactScenario } from "../lib/trace-impact-context";

interface DecisionSplitStepProps {
  locale: Locale;
}

/**
 * DECISION SPLIT (MOST IMPORTANT)
 * ─────────────────────────────────────
 * Primary:   WITHOUT vs WITH dominant comparison (center SAVED delta + % reduction)
 * Secondary: decision window countdown pill
 * Minimal:   single-line escalation caption
 */
export function DecisionSplitStep({ locale }: DecisionSplitStepProps) {
  const s = useTraceImpactScenario();
  const isAr = locale === "ar";
  const { decisionPressure } = s;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35 }}
      className={`max-w-3xl mx-auto px-6 py-10 ${isAr ? "text-right" : "text-left"}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Minimal — decision window pill */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex items-center justify-center mb-6 ${isAr ? "flex-row-reverse" : ""}`}
      >
        <div
          className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-io-status-severe/30 bg-io-status-severe/5 ${isAr ? "flex-row-reverse" : ""}`}
        >
          <Clock className="w-3.5 h-3.5 text-io-status-severe" />
          <span className="text-xs font-bold text-io-status-severe tabular-nums">
            {decisionPressure.clockValue}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-io-status-severe/70 font-semibold">
            {decisionPressure.clockLabel}
          </span>
        </div>
      </motion.div>

      {/* PRIMARY — Before/After dominant */}
      <BeforeAfterDecisionPanel scenario={s} locale={locale} />

      {/* Minimal closing caption — replaces decisions list + inaction card */}
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.5 }}
        className="mt-6 text-xs text-io-tertiary text-center leading-relaxed max-w-md mx-auto"
      >
        {decisionPressure.escalationBanner}
      </motion.p>
    </motion.div>
  );
}
