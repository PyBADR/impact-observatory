"use client";

/**
 * MACRO ENTRY SCREEN — Step 0
 * ─────────────────────────────────────────────────────────────
 * The first screen of the Trace Impact experience.
 *
 * Shows BEFORE any propagation, exposure, or decision step.
 * Answers: "What macro environment triggered this scenario?"
 *
 * Primary:   Regime label + system state sentence
 * Secondary: 4 regime metrics (exposure nodes, horizon, est. loss, confidence)
 * Detail:    Active macro signals with change direction + magnitude
 * Footer:    "Why the system is ELEVATED" interpretive block
 */

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";
import type { Locale } from "@/i18n/dictionary";
import { useTraceImpactScenario } from "../lib/trace-impact-context";
import { stagger, staggerItem } from "../lib/transitions";

interface MacroEntryStepProps {
  locale: Locale;
}

/** Signals that represent risk when moving up */
const RISK_UP_SIGNALS = ["Crude", "Rate", "Premium", "CDS", "Spread", "War", "Interbank", "Drawdown"];

function isRiskSignal(indicator: string, direction: "up" | "down"): boolean {
  if (direction === "down" && (indicator.includes("Baltic") || indicator.includes("Volume") || indicator.includes("Reserves"))) return true;
  if (direction === "up") return RISK_UP_SIGNALS.some((k) => indicator.includes(k));
  return false;
}

export function MacroEntryStep({ locale }: MacroEntryStepProps) {
  const s = useTraceImpactScenario();
  const isAr = locale === "ar";
  const regime = s.macroRegime;

  const regimeMetrics = [
    {
      label: isAr ? "نقاط التعرض" : "Exposure Points",
      value: `${regime.regimeMetrics.exposurePoints} / ${regime.regimeMetrics.totalPoints}`,
      sub: isAr ? "عُقد نشطة" : "active nodes",
    },
    {
      label: isAr ? "الأفق الزمني" : "Impact Horizon",
      value: regime.regimeMetrics.timeHorizon,
      sub: isAr ? "نافذة الأثر" : "window",
    },
    {
      label: isAr ? "الانكشاف المقدر" : "Est. Exposure",
      value: regime.regimeMetrics.estimatedExposure,
      sub: isAr ? "بدون تدخل" : "without action",
    },
    {
      label: isAr ? "الثقة" : "Confidence",
      value: `${Math.round(regime.regimeMetrics.confidence * 100)}%`,
      sub: isAr ? "توافق الإشارات" : "cross-signal",
    },
  ];

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className={`max-w-3xl mx-auto px-6 py-10 ${isAr ? "text-right" : "text-left"} min-h-[70vh] flex flex-col justify-center`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Regime severity badge */}
      <motion.div
        variants={staggerItem}
        className={`flex ${isAr ? "justify-end" : ""} mb-6`}
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-io-status-elevated/10 border border-io-status-elevated/30">
          <Activity className="w-3.5 h-3.5 text-io-status-elevated" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-io-status-elevated">
            {regime.severityTier}
          </span>
        </div>
      </motion.div>

      {/* Title */}
      <motion.div variants={staggerItem} className="mb-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-io-tertiary mb-2">
          {isAr ? "الذكاء الاقتصادي الكلي لدول مجلس التعاون" : "Macroeconomic Intelligence for the GCC"}
        </p>
        <h1
          className="font-bold text-io-primary leading-tight"
          style={{ fontSize: "clamp(1.75rem, 4vw, 2.75rem)" }}
        >
          {isAr
            ? "كيف وصلنا إلى هذه اللحظة"
            : "How We Got Here"}
        </h1>
      </motion.div>

      {/* System state — the "why this is happening" sentence */}
      <motion.p
        variants={staggerItem}
        className="text-sm text-io-secondary leading-relaxed mb-8 max-w-xl"
      >
        {isAr
          ? "تتحول الظروف الاقتصادية الكلية الإقليمية. أفضى الضغط الناجم عن قطاع الطاقة إلى ارتفاع المخاطر المنهجية عبر اقتصادات دول الخليج الست. الإشارات تنتقل عبر قنوات متعددة في آنٍ واحد."
          : regime.systemState}
      </motion.p>

      {/* Regime metrics — 4 KPIs */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8"
      >
        {regimeMetrics.map((m) => (
          <div
            key={m.label}
            className="bg-io-surface rounded-card border border-io-border p-3 text-center"
          >
            <p className="text-[9px] uppercase tracking-widest text-io-tertiary mb-1">{m.label}</p>
            <p className="text-lg font-bold text-io-primary tabular-nums">{m.value}</p>
            <p className="text-[10px] text-io-tertiary mt-0.5">{m.sub}</p>
          </div>
        ))}
      </motion.div>

      {/* Active macro signals */}
      <motion.div variants={staggerItem}>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-io-tertiary mb-3">
          {isAr ? "الإشارات الاقتصادية الكلية النشطة" : "Active Macro Signals"}
        </p>
        <div className="space-y-2">
          {regime.signals.map((sig) => {
            const risk = isRiskSignal(sig.indicator, sig.direction);
            return (
              <div
                key={sig.indicator}
                className={`flex items-center justify-between px-4 py-2.5 rounded-card border bg-io-surface border-io-border ${isAr ? "flex-row-reverse" : ""}`}
              >
                <p className="text-sm font-medium text-io-primary">{sig.indicator}</p>
                <div className={`flex items-center gap-2 ${isAr ? "flex-row-reverse" : ""}`}>
                  <span
                    className={`text-sm font-bold tabular-nums ${risk ? "text-io-status-elevated" : "text-io-primary"}`}
                  >
                    {sig.value}
                  </span>
                  <span
                    className={`flex items-center gap-0.5 text-[11px] font-semibold tabular-nums ${
                      risk ? "text-io-status-elevated" : "text-emerald-600"
                    }`}
                  >
                    {sig.direction === "up" ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {sig.change}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Why elevated — interpretive footer */}
      <motion.div
        variants={staggerItem}
        className={`mt-6 px-4 py-4 rounded-card bg-io-status-elevated/8 border border-io-status-elevated/25 flex items-start gap-3 ${isAr ? "flex-row-reverse" : ""}`}
      >
        <div className="w-6 h-6 rounded-full bg-io-status-elevated/15 flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-[10px] font-bold text-io-status-elevated">!</span>
        </div>
        <div>
          <p className="text-xs font-semibold text-io-status-elevated mb-1">
            {isAr
              ? `لماذا النظام في مستوى: ${regime.severityTier}`
              : `Why the system is: ${regime.severityTier}`}
          </p>
          <p className="text-xs text-io-secondary leading-relaxed">
            {isAr
              ? "تُشير الطاقة المتزامنة للإشارات — ارتفاع أسعار الخام، وتصاعد معدلات الإقراض بين البنوك، وانفراج هوامش مقايضة مخاطر الائتمان — إلى انتقال عبر قنوات متعددة في آنٍ واحد. الاحتواء بقطاع واحد غير كافٍ."
              : "The simultaneous energy of signals — crude surge, interbank rate pressure, CDS spread widening — indicates multi-channel transmission occurring simultaneously. Single-sector containment is insufficient. Coordinated cross-institution response is required."}
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}
