"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import type { SectorImpact } from "@/features/demo/data/demo-scenario";
import type { Locale } from "@/i18n/dictionary";
import { useTraceImpactScenario } from "../lib/trace-impact-context";

// Risk rank for sorting (higher first)
const RISK_RANK: Record<SectorImpact["riskLevel"], number> = {
  CRITICAL: 5,
  ELEVATED: 4,
  MODERATE: 3,
  LOW: 2,
  NOMINAL: 1,
};

// Increased-contrast palette for HIGH-risk sectors vs baseline
const RISK_STYLE: Record<
  SectorImpact["riskLevel"],
  { bar: string; text: string; cardBg: string; cardBorder: string; label: string }
> = {
  CRITICAL: {
    bar: "bg-io-status-severe",
    text: "text-io-status-severe",
    cardBg: "bg-io-status-severe/10",
    cardBorder: "border-io-status-severe/40",
    label: "border-io-status-severe/60",
  },
  ELEVATED: {
    bar: "bg-io-status-elevated",
    text: "text-io-status-elevated",
    cardBg: "bg-io-status-elevated/8",
    cardBorder: "border-io-status-elevated/35",
    label: "border-io-status-elevated/50",
  },
  MODERATE: {
    bar: "bg-io-status-guarded",
    text: "text-io-status-guarded",
    cardBg: "bg-io-surface",
    cardBorder: "border-io-border",
    label: "border-io-border",
  },
  LOW: {
    bar: "bg-io-status-low",
    text: "text-io-status-low",
    cardBg: "bg-io-surface",
    cardBorder: "border-io-border",
    label: "border-io-border",
  },
  NOMINAL: {
    bar: "bg-io-tertiary",
    text: "text-io-tertiary",
    cardBg: "bg-io-surface",
    cardBorder: "border-io-border",
    label: "border-io-border",
  },
};

const REVEAL_MS = 320;
const TOP_N = 3;

interface ExposureStepProps {
  locale: Locale;
}

/**
 * EXPOSURE STEP
 * ─────────────────────────────────────
 * Primary:   total exposure hero number
 * Secondary: top-3 sectors (sequential reveal, high-contrast for CRITICAL/ELEVATED)
 * Minimal:   "Show all" expansion + country flag strip
 */
export function ExposureStep({ locale }: ExposureStepProps) {
  const s = useTraceImpactScenario();
  const isAr = locale === "ar";

  // Rank ALL sectors by risk; take top-N for initial view
  const rankedSectors = useMemo(
    () =>
      [...s.sectors].sort(
        (a, b) =>
          RISK_RANK[b.riskLevel] - RISK_RANK[a.riskLevel] ||
          b.currentStress - a.currentStress
      ),
    [s.sectors]
  );
  const topSectors = rankedSectors.slice(0, TOP_N);
  const remainingSectors = rankedSectors.slice(TOP_N);

  const [visibleSectors, setVisibleSectors] = useState(0);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (visibleSectors >= topSectors.length) return;
    const t = setInterval(() => {
      setVisibleSectors((c) => Math.min(c + 1, topSectors.length));
    }, REVEAL_MS);
    return () => clearInterval(t);
  }, [visibleSectors, topSectors.length]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={`max-w-3xl mx-auto px-6 py-10 ${isAr ? "text-right" : "text-left"}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* PRIMARY — total exposure hero */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center mb-10"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-io-tertiary mb-2">
          {isAr ? "إجمالي التعرض" : "Total Exposure"}
        </p>
        <p
          className="font-bold text-io-primary leading-none tabular-nums"
          style={{ fontSize: "clamp(3rem, 8vw, 5rem)" }}
        >
          {s.financialRanges.withoutAction.base}
        </p>
        {/* Country flag strip — minimal, inline */}
        <div className={`flex items-center justify-center gap-1.5 mt-4 ${isAr ? "flex-row-reverse" : ""}`}>
          {s.countries.map((c) => (
            <span
              key={c.country}
              className="text-base grayscale-0 opacity-80"
              role="img"
              aria-label={c.country}
              title={`${c.country} · ${c.estimatedLoss}`}
            >
              {getFlag(c.flag)}
            </span>
          ))}
        </div>
      </motion.div>

      {/* SECONDARY — top-3 sectors with high contrast */}
      <div className="mb-4">
        <div className={`flex items-baseline justify-between mb-3 ${isAr ? "flex-row-reverse" : ""}`}>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-io-tertiary">
            {isAr ? "أعلى 3 قطاعات تأثراً" : "Top 3 Affected Sectors"}
          </h3>
          <span className="text-[10px] text-io-tertiary tabular-nums">
            {topSectors.length} / {rankedSectors.length}
          </span>
        </div>

        <div className="space-y-2.5">
          {topSectors.map((sector, i) => {
            const visible = i < visibleSectors;
            const style = RISK_STYLE[sector.riskLevel];
            const isHighRisk =
              sector.riskLevel === "CRITICAL" || sector.riskLevel === "ELEVATED";
            return (
              <AnimatePresence key={sector.name}>
                {visible && (
                  <motion.div
                    initial={{ opacity: 0, x: isAr ? 16 : -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.35, ease: "easeOut" }}
                    className={`rounded-card border ${style.cardBorder} ${style.cardBg} ${isHighRisk ? "shadow-quiet-md" : "shadow-quiet"} p-4`}
                  >
                    <div className={`flex items-center justify-between gap-3 mb-2 ${isAr ? "flex-row-reverse" : ""}`}>
                      <div className={`flex items-center gap-2 ${isAr ? "flex-row-reverse" : ""}`}>
                        <span className={`w-1.5 h-6 rounded-full ${style.bar}`} />
                        <p className={`text-sm font-bold ${isHighRisk ? "text-io-primary" : "text-io-primary"}`}>
                          {sector.name}
                        </p>
                      </div>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-badge border ${style.label} ${style.text}`}
                      >
                        {sector.riskLevel}
                      </span>
                    </div>
                    {/* Stress bar */}
                    <div className="w-full h-1.5 rounded-full bg-io-muted overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${sector.currentStress * 100}%` }}
                        transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
                        className={`h-full rounded-full ${style.bar}`}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            );
          })}
        </div>
      </div>

      {/* COUNTRY EXPOSURE INTERPRETATION — all 6 GCC countries */}
      {visibleSectors >= topSectors.length && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="mb-6"
        >
          <div className={`flex items-baseline justify-between mb-3 ${isAr ? "flex-row-reverse" : ""}`}>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-io-tertiary">
              {isAr ? "التعرض الإقليمي — دول مجلس التعاون" : "Regional Exposure — GCC Countries"}
            </h3>
          </div>
          <div className="space-y-2">
            {s.countries.map((c) => {
              const isCritical = c.impactLevel === "CRITICAL";
              const isElevated = c.impactLevel === "ELEVATED";
              const borderColor = isCritical
                ? "border-io-status-severe/40"
                : isElevated
                ? "border-io-status-elevated/35"
                : "border-io-border";
              const lossColor = isCritical
                ? "text-io-status-severe"
                : isElevated
                ? "text-io-status-elevated"
                : "text-io-primary";
              return (
                <div
                  key={c.country}
                  className={`rounded-card border ${borderColor} bg-io-surface px-4 py-3`}
                >
                  <div className={`flex items-start justify-between gap-3 ${isAr ? "flex-row-reverse" : ""}`}>
                    <div className={`flex items-center gap-2 ${isAr ? "flex-row-reverse" : ""}`}>
                      <span className="text-base">{getFlag(c.flag)}</span>
                      <div>
                        <p className="text-sm font-semibold text-io-primary leading-none">
                          {c.country}
                        </p>
                        <p className="text-[10px] text-io-tertiary mt-0.5">{c.topSector}</p>
                      </div>
                    </div>
                    <p className={`text-sm font-bold tabular-nums ${lossColor} flex-shrink-0`}>
                      {c.estimatedLoss}
                    </p>
                  </div>
                  <p className="text-[11px] text-io-secondary mt-2 leading-snug">
                    {c.driver}
                  </p>
                  <p className="text-[10px] text-io-tertiary mt-1">
                    {isAr ? "مسار:" : "Channel:"}{" "}
                    <span className="font-medium text-io-secondary">{c.channel}</span>
                  </p>
                </div>
              );
            })}
          </div>

          {/* Cross-border risk footer */}
          <div className={`mt-3 px-4 py-3 rounded-card bg-io-muted border border-io-border flex items-start gap-2.5 ${isAr ? "flex-row-reverse" : ""}`}>
            <span className="text-[11px] text-io-secondary leading-snug">
              {isAr
                ? "ينتقل الضغط عبر صادرات السلع والتسويات المالية والشبكات الإقليمية. تتأثر جميع دول المجلس الست في آنٍ واحد."
                : "Stress transmits through commodity exports, financial settlements, and regional supply networks. All six GCC economies face simultaneous pressure."}
            </span>
          </div>
        </motion.div>
      )}

      {/* Expansion toggle */}
      {remainingSectors.length > 0 && visibleSectors >= topSectors.length && (
        <>
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            onClick={() => setExpanded((e) => !e)}
            className={`mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-io-accent hover:text-io-accent-hover transition-colors ${isAr ? "flex-row-reverse" : ""}`}
          >
            <ChevronDown
              className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
            {expanded
              ? isAr
                ? "إخفاء"
                : "Hide"
              : isAr
              ? `عرض ${remainingSectors.length} أخرى`
              : `Show ${remainingSectors.length} more`}
          </motion.button>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-3 grid grid-cols-2 gap-2 overflow-hidden"
              >
                {remainingSectors.map((sector) => {
                  const style = RISK_STYLE[sector.riskLevel];
                  return (
                    <div
                      key={sector.name}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg border border-io-border bg-io-surface"
                    >
                      <span className={`w-1 h-4 rounded-full ${style.bar}`} />
                      <span className="text-xs font-medium text-io-primary flex-1 truncate">
                        {sector.name}
                      </span>
                      <span className={`text-[10px] font-bold ${style.text}`}>
                        {Math.round(sector.currentStress * 100)}%
                      </span>
                    </div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </motion.div>
  );
}

const FLAG_MAP: Record<string, string> = {
  SA: "🇸🇦", AE: "🇦🇪", KW: "🇰🇼", QA: "🇶🇦", BH: "🇧🇭", OM: "🇴🇲",
};
function getFlag(code: string) {
  return FLAG_MAP[code] ?? "🏳️";
}
