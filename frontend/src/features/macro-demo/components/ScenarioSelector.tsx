"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { DemoScenario, ScenarioDomain } from "../data";

// ─── Domain visual config ───────────────────────────────────────────────────

const domainStyle: Record<
  ScenarioDomain,
  { color: string; bg: string; icon: string }
> = {
  MARITIME:        { color: "text-sky-400",     bg: "bg-sky-500/10",     icon: "⚓" },
  ENERGY:          { color: "text-amber-400",   bg: "bg-amber-500/10",   icon: "⚡" },
  FINANCIAL:       { color: "text-blue-400",    bg: "bg-blue-500/10",    icon: "🏦" },
  CYBER:           { color: "text-violet-400",  bg: "bg-violet-500/10",  icon: "🛡" },
  TRADE:           { color: "text-emerald-400", bg: "bg-emerald-500/10", icon: "🚢" },
  INFRASTRUCTURE:  { color: "text-orange-400",  bg: "bg-orange-500/10",  icon: "🏗" },
  GEOPOLITICAL:    { color: "text-red-400",     bg: "bg-red-500/10",     icon: "🌐" },
};

// ─── Props ──────────────────────────────────────────────────────────────────

interface ScenarioSelectorProps {
  scenarios: DemoScenario[];
  activeId: string;
  onSelect: (id: string) => void;
}

// ─── Component ──────────────────────────────────────────────────────────────

export function ScenarioSelector({
  scenarios,
  activeId,
  onSelect,
}: ScenarioSelectorProps) {
  const [filterDomain, setFilterDomain] = useState<ScenarioDomain | "ALL">(
    "ALL"
  );

  // Unique domains present in catalog
  const domains = useMemo(() => {
    const set = new Set(scenarios.map((s) => s.meta.domain));
    return Array.from(set).sort();
  }, [scenarios]);

  // Filtered list
  const filtered =
    filterDomain === "ALL"
      ? scenarios
      : scenarios.filter((s) => s.meta.domain === filterDomain);

  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16">
      {/* Header */}
      <motion.div
        className="text-center mb-12"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
          Select Scenario
        </h1>
        <p className="mt-3 text-lg text-slate-400 max-w-xl mx-auto">
          Choose a GCC macroeconomic shock to run through the intelligence
          pipeline
        </p>
      </motion.div>

      {/* Domain filter pills */}
      <motion.div
        className="flex flex-wrap items-center justify-center gap-2 mb-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <FilterPill
          label="All"
          active={filterDomain === "ALL"}
          onClick={() => setFilterDomain("ALL")}
        />
        {domains.map((d) => (
          <FilterPill
            key={d}
            label={d.charAt(0) + d.slice(1).toLowerCase()}
            icon={domainStyle[d]?.icon}
            active={filterDomain === d}
            onClick={() => setFilterDomain(d)}
          />
        ))}
      </motion.div>

      {/* Scenario grid */}
      <motion.div
        className="w-full max-w-5xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        layout
      >
        <AnimatePresence mode="popLayout">
          {filtered.map((scenario, i) => {
            const { meta } = scenario;
            const style = domainStyle[meta.domain];
            const isActive = meta.id === activeId;

            return (
              <motion.button
                key={meta.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{
                  delay: i * 0.04,
                  duration: 0.35,
                  ease: [0.16, 1, 0.3, 1],
                }}
                onClick={() => onSelect(meta.id)}
                className={`
                  group relative text-left rounded-2xl border p-5 cursor-pointer
                  transition-all duration-300
                  ${
                    isActive
                      ? "border-white/20 bg-white/[0.04] shadow-[0_0_30px_rgba(255,255,255,0.04)]"
                      : "border-white/[0.06] bg-white/[0.015] hover:border-white/[0.12] hover:bg-white/[0.03]"
                  }
                `}
              >
                {/* Domain badge */}
                <div className="flex items-center justify-between mb-4">
                  <span
                    className={`inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full ${style.color} ${style.bg}`}
                  >
                    <span>{style.icon}</span>
                    {meta.domain}
                  </span>
                  {isActive && (
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  )}
                </div>

                {/* Name */}
                <h3 className="text-base font-semibold text-white leading-snug mb-3 group-hover:text-white/90 transition-colors">
                  {meta.name}
                </h3>

                {/* Stats row */}
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="tabular-nums font-medium text-slate-300">
                    {meta.baseLossLabel}
                  </span>
                  <span>Peak: {meta.peakDay}</span>
                  <span>
                    {meta.sectors.length} sector{meta.sectors.length > 1 ? "s" : ""}
                  </span>
                </div>

                {/* Sector tags */}
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {meta.sectors.map((s) => (
                    <span
                      key={s}
                      className="text-[10px] text-slate-500 bg-white/[0.04] px-2 py-0.5 rounded"
                    >
                      {s}
                    </span>
                  ))}
                </div>

                {/* Severity bar */}
                <div className="mt-4 w-full h-1 rounded-full bg-white/[0.04] overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{
                      background:
                        scenario.data.shock.severity >= 80
                          ? "linear-gradient(90deg, #EF4444, #F87171)"
                          : scenario.data.shock.severity >= 60
                            ? "linear-gradient(90deg, #F59E0B, #FBBF24)"
                            : "linear-gradient(90deg, #6B7280, #9CA3AF)",
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${scenario.data.shock.severity}%` }}
                    transition={{ delay: 0.2 + i * 0.04, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
              </motion.button>
            );
          })}
        </AnimatePresence>
      </motion.div>
    </section>
  );
}

// ─── Internal sub-components ────────────────────────────────────────────────

function FilterPill({
  label,
  icon,
  active,
  onClick,
}: {
  label: string;
  icon?: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium
        transition-all duration-200 cursor-pointer
        ${
          active
            ? "bg-white/10 text-white border border-white/20"
            : "bg-white/[0.03] text-slate-500 border border-white/[0.06] hover:text-slate-300 hover:border-white/[0.1]"
        }
      `}
    >
      {icon && <span>{icon}</span>}
      {label}
    </button>
  );
}
