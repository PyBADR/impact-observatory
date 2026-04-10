"use client";

import { motion } from "framer-motion";
import type { DecisionOption } from "../data";

interface DecisionEngineProps {
  decisions: DecisionOption[];
  highlightBest: boolean;
}

const tagConfig: Record<DecisionOption["tag"], { border: string; bg: string; text: string; label: string }> = {
  recommended: {
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/8",
    text: "text-emerald-400",
    label: "Recommended",
  },
  alternative: {
    border: "border-amber-500/20",
    bg: "bg-amber-500/5",
    text: "text-amber-400",
    label: "Alternative",
  },
  risk: {
    border: "border-red-500/20",
    bg: "bg-red-500/5",
    text: "text-red-400",
    label: "High Risk",
  },
};

export function DecisionEngine({ decisions, highlightBest }: DecisionEngineProps) {
  return (
    <section className="px-6 py-20 max-w-4xl mx-auto">
      <motion.h2
        className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-3 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        Decision Engine
      </motion.h2>
      <motion.p
        className="text-2xl md:text-3xl font-semibold text-white text-center mb-14"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      >
        What the system recommends
      </motion.p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {decisions.map((decision, i) => {
          const cfg = tagConfig[decision.tag];
          const isBest = decision.tag === "recommended";
          const isGlowing = isBest && highlightBest;

          return (
            <motion.div
              key={decision.action}
              className={`
                relative rounded-2xl border p-6 flex flex-col items-center text-center
                transition-all duration-700
                ${cfg.border}
                ${isGlowing ? "shadow-[0_0_40px_rgba(16,185,129,0.15)]" : ""}
              `}
              style={{
                background: isGlowing
                  ? "linear-gradient(180deg, rgba(16,185,129,0.06) 0%, rgba(16,185,129,0.01) 100%)"
                  : "rgba(255,255,255,0.02)",
              }}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.3 + i * 0.15,
                duration: 0.6,
                ease: [0.16, 1, 0.3, 1],
              }}
            >
              {/* Tag badge */}
              <span
                className={`inline-block text-xs font-semibold uppercase tracking-wider px-3 py-1 rounded-full mb-5 ${cfg.text}`}
                style={{
                  background:
                    decision.tag === "recommended"
                      ? "rgba(16,185,129,0.1)"
                      : decision.tag === "alternative"
                        ? "rgba(245,158,11,0.08)"
                        : "rgba(239,68,68,0.08)",
                }}
              >
                {cfg.label}
              </span>

              {/* Value */}
              <motion.span
                className={`text-5xl font-bold tabular-nums ${
                  decision.value > 0 ? "text-white" : "text-red-400"
                }`}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{
                  scale: isGlowing ? [1, 1.06, 1] : 1,
                  opacity: 1,
                }}
                transition={{
                  delay: 0.5 + i * 0.15,
                  duration: isGlowing ? 1.5 : 0.5,
                  repeat: isGlowing ? Infinity : 0,
                  repeatType: "reverse",
                }}
              >
                {decision.value > 0 ? "+" : ""}
                {decision.value}
              </motion.span>
              <span className="text-xs text-slate-500 mt-1 tabular-nums">
                $ Billion
              </span>

              {/* Action label */}
              <p className="mt-5 text-sm text-slate-300 leading-relaxed">
                {decision.action}
              </p>

              {/* Glow ring on recommended */}
              {isGlowing && (
                <motion.div
                  className="absolute inset-0 rounded-2xl pointer-events-none"
                  style={{
                    boxShadow: "0 0 0 2px rgba(16,185,129,0.2)",
                  }}
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                />
              )}
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
