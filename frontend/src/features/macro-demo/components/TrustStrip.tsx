"use client";

import { motion } from "framer-motion";
import type { DemoTrust } from "../data";

interface TrustStripProps {
  trust: DemoTrust;
}

export function TrustStrip({ trust }: TrustStripProps) {
  const items = [
    { label: "Model", value: trust.model },
    { label: "Pipeline", value: trust.pipeline },
    { label: "Latency", value: trust.latency },
    { label: "Audit Hash", value: trust.hash },
  ];

  return (
    <motion.footer
      className="px-6 py-8 border-t border-white/5"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.2, ease: "easeOut" }}
    >
      <div className="max-w-4xl mx-auto flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <span className="text-[11px] uppercase tracking-widest text-slate-600">
              {item.label}
            </span>
            <span className="text-xs font-mono text-slate-400">
              {item.value}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 text-center">
        <span className="text-[10px] uppercase tracking-[0.25em] text-slate-600/60">
          Impact Observatory — AI Decision Intelligence
        </span>
      </div>
    </motion.footer>
  );
}
