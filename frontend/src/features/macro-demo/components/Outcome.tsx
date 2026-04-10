"use client";

import { motion } from "framer-motion";
import type { DemoOutcome } from "../data";

interface OutcomeProps {
  outcome: DemoOutcome;
}

export function Outcome({ outcome }: OutcomeProps) {
  return (
    <section className="px-6 py-24 flex flex-col items-center text-center">
      <motion.h2
        className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        Projected Outcome
      </motion.h2>

      {/* Main metric — strong pop-in */}
      <motion.div
        className="mt-6 relative"
        initial={{ opacity: 0, scale: 0.6 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{
          duration: 0.8,
          ease: [0.16, 1, 0.3, 1],
          type: "spring",
          stiffness: 200,
          damping: 15,
        }}
      >
        {/* Background glow */}
        <div
          className="absolute inset-0 -m-8 rounded-full blur-3xl pointer-events-none"
          style={{ background: "radial-gradient(circle, rgba(16,185,129,0.12) 0%, transparent 70%)" }}
        />

        <motion.span
          className="relative block text-8xl md:text-[10rem] font-bold text-white tabular-nums leading-none"
          animate={{ opacity: [0.85, 1, 0.85] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          {outcome.net}
          <span className="text-emerald-400">%</span>
        </motion.span>
      </motion.div>

      <motion.p
        className="mt-4 text-xl text-slate-300 font-medium"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.6 }}
      >
        {outcome.label}
      </motion.p>

      {/* Confidence bar */}
      <motion.div
        className="mt-8 w-full max-w-sm"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-widest text-slate-500">
            Model Confidence
          </span>
          <span className="text-sm font-bold text-emerald-400 tabular-nums">
            {outcome.confidence}%
          </span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400"
            initial={{ width: 0 }}
            animate={{ width: `${outcome.confidence}%` }}
            transition={{ delay: 0.8, duration: 1, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
      </motion.div>
    </section>
  );
}
