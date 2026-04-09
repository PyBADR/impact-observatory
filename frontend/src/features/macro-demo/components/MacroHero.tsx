"use client";

import { motion } from "framer-motion";
import type { DemoShock } from "../data";

interface MacroHeroProps {
  shock: DemoShock;
}

export function MacroHero({ shock }: MacroHeroProps) {
  return (
    <motion.section
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-col items-center justify-center text-center px-6 py-24 min-h-[60vh]"
    >
      {/* Severity pulse ring */}
      <motion.div
        className="relative mb-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.8 }}
      >
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            width: 160,
            height: 160,
            background: "radial-gradient(circle, rgba(239,68,68,0.15) 0%, transparent 70%)",
          }}
          animate={{ scale: [1, 1.3, 1], opacity: [0.6, 0.2, 0.6] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />
        <div
          className="relative flex items-center justify-center rounded-full border border-red-500/30"
          style={{ width: 160, height: 160 }}
        >
          <div className="text-center">
            <motion.span
              className="block text-6xl font-bold text-red-400 tabular-nums"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.8 }}
            >
              {shock.severity}
            </motion.span>
            <span className="block text-xs uppercase tracking-widest text-red-400/60 mt-1">
              Severity
            </span>
          </div>
        </div>
      </motion.div>

      {/* Title */}
      <motion.h1
        className="text-5xl md:text-7xl font-bold text-white tracking-tight leading-none"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 1, ease: [0.16, 1, 0.3, 1] }}
      >
        {shock.title}
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        className="mt-5 text-lg md:text-xl text-slate-400 max-w-2xl leading-relaxed"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.8 }}
      >
        {shock.subtitle}
      </motion.p>

      {/* Impact badge */}
      <motion.div
        className="mt-8 flex items-center gap-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.0, duration: 0.6 }}
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-sm font-medium text-red-300 tabular-nums">
            Impact Score: {shock.impact}%
          </span>
        </span>
      </motion.div>
    </motion.section>
  );
}
