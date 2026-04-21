"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Locale } from "@/i18n/dictionary";
import { useTraceImpactScenario } from "../lib/trace-impact-context";

const NODE_COLORS: Record<string, { bg: string; ring: string; dot: string }> = {
  oil:        { bg: "bg-amber-50",   ring: "ring-amber-300",   dot: "bg-amber-500" },
  shipping:   { bg: "bg-blue-50",    ring: "ring-blue-300",    dot: "bg-blue-500" },
  banking:    { bg: "bg-indigo-50",  ring: "ring-indigo-300",  dot: "bg-indigo-500" },
  insurance:  { bg: "bg-violet-50",  ring: "ring-violet-300",  dot: "bg-violet-500" },
  government: { bg: "bg-slate-50",   ring: "ring-slate-300",   dot: "bg-slate-500" },
};

const REVEAL_MS = 500; // sequential cadence (300–600ms band)

interface PropagationStepProps {
  locale: Locale;
}

/**
 * PROPAGATION FLOW
 * ─────────────────────────────────────
 * Primary:   sequential node reveal with animated connector
 * Secondary: rotating caption for active node
 * Minimal:   post-cascade summary line
 */
export function PropagationStep({ locale }: PropagationStepProps) {
  const s = useTraceImpactScenario();
  const isAr = locale === "ar";
  const points = s.transmission.points;
  const cascadeLabels = s.transmission.cascadeLabels;

  const [visibleCount, setVisibleCount] = useState(1);
  const allVisible = visibleCount >= points.length;

  useEffect(() => {
    if (allVisible) return;
    const timer = setInterval(() => {
      setVisibleCount((c) => Math.min(c + 1, points.length));
    }, REVEAL_MS);
    return () => clearInterval(timer);
  }, [allVisible, points.length]);

  const activeIndex = Math.min(visibleCount - 1, points.length - 1);
  const activeLabel = cascadeLabels[activeIndex];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35 }}
      className={`max-w-3xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-[65vh] ${isAr ? "text-right" : "text-left"}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Minimal header */}
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-io-tertiary mb-8">
        {isAr ? "مسار الانتقال" : "Transmission Path"}
      </p>

      {/* PRIMARY — node chain with flowing connectors */}
      <div
        className={`relative flex items-center justify-center flex-wrap gap-0 mb-10 ${isAr ? "flex-row-reverse" : ""}`}
        aria-live="polite"
      >
        {points.map((point, i) => {
          const visible = i < visibleCount;
          const isActive = i === activeIndex;
          const colors = NODE_COLORS[point.id] ?? NODE_COLORS.government;
          const showConnector = i < points.length - 1;

          return (
            <div
              key={point.id}
              className={`flex items-center ${isAr ? "flex-row-reverse" : ""}`}
            >
              {/* Node */}
              <AnimatePresence>
                {visible && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.6, y: 8 }}
                    animate={{
                      opacity: 1,
                      scale: isActive ? 1.05 : 1,
                      y: 0,
                    }}
                    transition={{ duration: 0.35, ease: "easeOut" }}
                    className={`relative flex flex-col items-center gap-2 px-4 py-3 rounded-xl ring-2 ${colors.bg} ${colors.ring} ${isActive ? "shadow-quiet-lg" : "shadow-quiet"}`}
                  >
                    <span className={`w-2 h-2 rounded-full ${colors.dot} ${isActive ? "animate-pulse" : ""}`} />
                    <span className="text-[11px] font-bold tracking-wide text-io-primary whitespace-nowrap">
                      {point.label}
                    </span>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Connector — animated flowing line between revealed nodes */}
              {showConnector && (
                <div className="w-8 h-[2px] mx-1 relative overflow-hidden">
                  <div className="absolute inset-0 bg-io-border" />
                  <AnimatePresence>
                    {i < visibleCount - 1 && (
                      <motion.div
                        initial={{ scaleX: 0, originX: isAr ? 1 : 0 }}
                        animate={{ scaleX: 1 }}
                        transition={{ duration: 0.4, ease: "easeOut" }}
                        className="absolute inset-0 bg-io-charcoal"
                        style={{ transformOrigin: isAr ? "right" : "left" }}
                      />
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* SECONDARY — single rotating caption for the active node */}
      <div className="h-14 flex items-start justify-center max-w-lg">
        <AnimatePresence mode="wait">
          <motion.p
            key={activeIndex}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.28, ease: "easeOut" }}
            className="text-sm text-io-secondary leading-relaxed text-center"
          >
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-io-charcoal text-white text-[10px] font-bold mr-2 align-middle">
              {activeIndex + 1}
            </span>
            {activeLabel}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Minimal closing line — after full cascade */}
      <AnimatePresence>
        {allVisible && (
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="mt-8 text-xs uppercase tracking-[0.18em] font-semibold text-io-status-severe"
          >
            {isAr ? "الأثر الكامل" : "Full Cascade · Systemic"}
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
