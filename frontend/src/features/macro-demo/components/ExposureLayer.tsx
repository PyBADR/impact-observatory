"use client";

import { motion } from "framer-motion";
import type { ExposureEntry } from "../data";

interface ExposureLayerProps {
  entries: ExposureEntry[];
}

export function ExposureLayer({ entries }: ExposureLayerProps) {
  const maxPercent = Math.max(...entries.map((e) => e.percent));

  return (
    <section className="px-6 py-20 max-w-3xl mx-auto">
      <motion.h2
        className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-3 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        Exposure Map
      </motion.h2>
      <motion.p
        className="text-2xl md:text-3xl font-semibold text-white text-center mb-14"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      >
        Who bears the risk
      </motion.p>

      <div className="space-y-5">
        {entries.map((entry, i) => (
          <motion.div
            key={entry.country}
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{
              delay: 0.3 + i * 0.12,
              duration: 0.5,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className="text-xl">{entry.flag}</span>
                <span className="text-base font-medium text-slate-200">
                  {entry.country}
                </span>
              </div>
              <span className="text-lg font-bold text-white tabular-nums">
                {entry.percent}%
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-white/5 overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background:
                    entry.percent === maxPercent
                      ? "linear-gradient(90deg, #EF4444 0%, #F87171 100%)"
                      : "linear-gradient(90deg, rgba(148,163,184,0.4) 0%, rgba(148,163,184,0.2) 100%)",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${entry.percent}%` }}
                transition={{
                  delay: 0.5 + i * 0.12,
                  duration: 0.8,
                  ease: [0.16, 1, 0.3, 1],
                }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
