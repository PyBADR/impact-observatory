"use client";

import { motion } from "framer-motion";
import type { TransmissionNode } from "../data";

interface TransmissionFlowProps {
  nodes: TransmissionNode[];
}

export function TransmissionFlow({ nodes }: TransmissionFlowProps) {
  return (
    <section className="px-6 py-20 max-w-5xl mx-auto">
      <motion.h2
        className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-3 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        Transmission Path
      </motion.h2>
      <motion.p
        className="text-2xl md:text-3xl font-semibold text-white text-center mb-14"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      >
        How the shock propagates
      </motion.p>

      <div className="flex items-center justify-center gap-0 overflow-hidden">
        {nodes.map((node, i) => (
          <motion.div
            key={node.label}
            className="flex items-center"
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{
              delay: 0.3 + i * 0.18,
              duration: 0.6,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            {/* Node */}
            <div className="flex flex-col items-center min-w-[100px] md:min-w-[120px]">
              <div
                className="w-14 h-14 md:w-16 md:h-16 rounded-2xl flex items-center justify-center text-xl font-bold tabular-nums border"
                style={{
                  background: `rgba(239, 68, 68, ${0.06 + i * 0.04})`,
                  borderColor: `rgba(239, 68, 68, ${0.12 + i * 0.06})`,
                  color: `rgba(248, 113, 113, ${0.6 + i * 0.1})`,
                }}
              >
                {i + 1}
              </div>
              <span className="mt-3 text-sm font-medium text-slate-300 text-center leading-tight">
                {node.label}
              </span>
              <span className="mt-1 text-xs text-slate-500 tabular-nums">
                {node.delay}
              </span>
            </div>

            {/* Connector arrow */}
            {i < nodes.length - 1 && (
              <motion.div
                className="flex items-center mx-1 md:mx-2"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: 0.5 + i * 0.18, duration: 0.4 }}
                style={{ originX: 0 }}
              >
                <div className="w-6 md:w-10 h-px bg-gradient-to-r from-red-500/40 to-red-500/10" />
                <div className="w-0 h-0 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent border-l-[6px] border-l-red-500/30" />
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </section>
  );
}
