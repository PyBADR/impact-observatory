"use client";

import { motion } from "framer-motion";
import { CheckCircle, TrendingDown, BarChart2, ArrowRight, ArrowLeft } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import type { Locale } from "@/i18n/dictionary";
import { useTraceImpactScenario } from "../lib/trace-impact-context";

interface OutcomeStepProps {
  locale: Locale;
}

/**
 * OUTCOME STEP
 * ─────────────────────────────────────
 * Primary:   dominant closing CTA → Enter Decision Room
 * Secondary: Loss Avoided · Risk Reduction
 * Minimal:   one-line confirmation + compact pipeline footer
 */
export function OutcomeStep({ locale }: OutcomeStepProps) {
  const s = useTraceImpactScenario();
  const isAr = locale === "ar";
  const { outcome, trust } = s;
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleGoToDecisions = () => {
    const params = new URLSearchParams();
    params.set("tab", "decisions");
    const runId = searchParams.get("run");
    if (runId) params.set("run", runId);
    router.push(`/command-center?${params.toString()}`);
  };

  const ArrowIcon = isAr ? ArrowLeft : ArrowRight;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35 }}
      className={`max-w-3xl mx-auto px-6 py-12 flex flex-col items-center min-h-[70vh] ${isAr ? "text-right" : "text-left"}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Minimal — confirmation line */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-io-status-low/25 bg-io-status-low/5 mb-6 ${isAr ? "flex-row-reverse" : ""}`}
      >
        <CheckCircle className="w-3.5 h-3.5 text-io-status-low" />
        <span className="text-xs font-semibold text-io-status-low">
          {isAr ? "تم احتواء الأثر" : "Impact Contained"}
        </span>
      </motion.div>

      {/* SECONDARY — two core stats */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.15 }}
        className="w-full max-w-lg grid grid-cols-2 gap-3 mb-10"
      >
        <div className="rounded-card border border-io-status-low/25 bg-io-status-low/5 p-5 text-center">
          <TrendingDown className="w-4 h-4 mx-auto mb-2 text-io-status-low" />
          <p className="text-3xl font-bold text-io-status-low tabular-nums leading-none mb-1">
            {outcome.saved.amount}
          </p>
          <p className="text-[10px] uppercase tracking-wider text-io-tertiary font-semibold">
            {isAr ? "خسائر متجنبة" : "Loss Avoided"}
          </p>
        </div>
        <div className="rounded-card border border-io-accent/25 bg-io-accent/5 p-5 text-center">
          <BarChart2 className="w-4 h-4 mx-auto mb-2 text-io-accent" />
          <p className="text-3xl font-bold text-io-accent tabular-nums leading-none mb-1">
            −{outcome.withAction.riskReduction}
          </p>
          <p className="text-[10px] uppercase tracking-wider text-io-tertiary font-semibold">
            {isAr ? "تقليص المخاطر" : "Risk Reduction"}
          </p>
        </div>
      </motion.div>

      {/* PRIMARY — dominant closing CTA */}
      <motion.button
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        onClick={handleGoToDecisions}
        className={`group relative inline-flex items-center justify-center gap-3 px-10 py-5 text-base font-bold rounded-xl bg-io-accent text-white hover:bg-io-accent-hover shadow-quiet-lg hover:shadow-xl transition-all ${isAr ? "flex-row-reverse" : ""}`}
      >
        <span className="tracking-wide">
          {isAr ? "ادخل غرفة القرار" : "Enter Decision Room"}
        </span>
        <ArrowIcon className="w-5 h-5 transition-transform group-hover:translate-x-1" />
      </motion.button>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.5 }}
        className="mt-3 text-[11px] text-io-tertiary"
      >
        {isAr ? "راجع القرارات الموصى بها" : "Review recommended decisions"}
      </motion.p>

      {/* Minimal — trust footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.6 }}
        className={`mt-auto pt-8 flex items-center gap-2 flex-wrap justify-center text-[10px] text-io-tertiary ${isAr ? "flex-row-reverse" : ""}`}
      >
        <span className="font-semibold uppercase tracking-wider">
          {isAr ? "المصادر:" : "Sources:"}
        </span>
        {trust.dataSources.slice(0, 3).map((src) => (
          <span
            key={src}
            className="px-1.5 py-0.5 rounded-badge border border-io-border bg-io-surface"
          >
            {src.split(" (")[0]}
          </span>
        ))}
        <span className="text-io-tertiary/70">
          · {Math.round(trust.confidence * 100)}% {isAr ? "ثقة" : "confidence"}
        </span>
      </motion.div>
    </motion.div>
  );
}
