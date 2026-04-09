"use client";

/**
 * Impact Observatory — Flow Narrative Panel
 *
 * Renders the narrative engine output as a structured story,
 * filtered by active persona. Each block maps to a pipeline stage.
 *
 * Executive sees: value summaries, ROI, top-level synthesis
 * Analyst sees: reasoning chains, simulation mechanics, full data
 * Regulator sees: audit trail, provenance, traceability
 */

import React, { useMemo, useState } from "react";
import { useFlowStore } from "@/store/flow-store";
import { useAppStore } from "@/store/app-store";
import {
  generateFlowNarrative,
  filterBlocksByPersona,
  getBlockText,
  type NarrativeBlock,
  type FlowNarrative,
} from "@/lib/narrative-engine";
import type { Language } from "@/types/observatory";
import type { Persona } from "@/lib/persona-view-model";

// ─── Module-level stable selectors ───────────────────────────────────────────
type FlowS_FN = ReturnType<typeof useFlowStore.getState>;
type AppS_FN  = ReturnType<typeof useAppStore.getState>;
const selectFlowActiveFlow_FN = (s: FlowS_FN) => s.activeFlow;
const selectPersona_FN        = (s: AppS_FN)  => s.persona;

// ─── Block Severity Styling ─────────────────────────────────────────────────

const SEVERITY_STYLES: Record<string, string> = {
  info:     "border-l-blue-400 bg-blue-50/30",
  warning:  "border-l-amber-400 bg-amber-50/30",
  critical: "border-l-red-400 bg-red-50/30",
  positive: "border-l-emerald-400 bg-emerald-50/30",
};

const SEVERITY_ICON: Record<string, string> = {
  info:     "ℹ️",
  warning:  "⚠️",
  critical: "🔴",
  positive: "✅",
};

const BLOCK_TYPE_LABELS: Record<string, { en: string; ar: string }> = {
  signal:     { en: "Signal Detection",     ar: "رصد الإشارة" },
  reasoning:  { en: "TREK Reasoning",       ar: "تحليل TREK" },
  simulation: { en: "Impact Simulation",    ar: "محاكاة الأثر" },
  decision:   { en: "Decision Actions",     ar: "إجراءات القرار" },
  outcome:    { en: "Outcome Tracking",     ar: "تتبع النتائج" },
  roi:        { en: "Value Computation",    ar: "حساب القيمة" },
  synthesis:  { en: "Flow Synthesis",       ar: "تجميع التدفق" },
};

// ─── Narrative Block Component ──────────────────────────────────────────────

function NarrativeBlockCard({
  block,
  lang,
  isExpanded,
  onToggle,
}: {
  block: NarrativeBlock;
  lang: Language;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const isAr = lang === "ar";
  const text = getBlockText(block, lang);
  const typeLabel = BLOCK_TYPE_LABELS[block.type] ?? { en: block.type, ar: block.type };

  return (
    <div className={`border-l-4 rounded-r-lg ${SEVERITY_STYLES[block.severity]} transition-all`}>
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-white/30 transition-colors"
      >
        {/* Stage indicator */}
        <span className="text-base mt-0.5 shrink-0">{SEVERITY_ICON[block.severity]}</span>

        <div className="flex-1 min-w-0">
          {/* Stage label */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-widest text-io-secondary">
              {isAr ? typeLabel.ar : typeLabel.en}
            </span>
            <span className="text-[10px] text-io-secondary/50">
              Stage {block.order}/7
            </span>
          </div>

          {/* Narrative text */}
          <p className={`text-sm text-io-primary leading-relaxed ${isExpanded ? "" : "line-clamp-2"}`}>
            {text}
          </p>
        </div>

        {/* Expand indicator */}
        <span className="text-xs text-io-secondary shrink-0 mt-1">
          {isExpanded ? "▲" : "▼"}
        </span>
      </button>

      {/* Expanded: metrics + data trail */}
      {isExpanded && (
        <div className="px-4 pb-3 pt-1 space-y-3">
          {/* Metrics */}
          {block.metrics.length > 0 && (
            <div className="flex flex-wrap gap-3">
              {block.metrics.map((m) => (
                <div
                  key={m.label}
                  className={`
                    px-3 py-1.5 rounded-lg border text-xs
                    ${m.sentiment === "positive" ? "bg-emerald-50 border-emerald-200 text-emerald-700" : ""}
                    ${m.sentiment === "negative" ? "bg-red-50 border-red-200 text-red-700" : ""}
                    ${m.sentiment === "neutral" ? "bg-gray-50 border-gray-200 text-gray-600" : ""}
                  `}
                >
                  <span className="font-medium">{isAr ? m.labelAr : m.label}: </span>
                  <span className="font-bold">{m.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Data trail (for analyst/regulator transparency) */}
          <div className="flex flex-wrap gap-1">
            {block.dataTrail.map((trail) => (
              <span
                key={trail}
                className="text-[9px] font-mono px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded text-gray-500"
              >
                {trail}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Panel ─────────────────────────────────────────────────────────────

interface FlowNarrativePanelProps {
  lang: Language;
}

export function FlowNarrativePanel({ lang }: FlowNarrativePanelProps) {
  const activeFlow = useFlowStore(selectFlowActiveFlow_FN);
  const persona    = useAppStore(selectPersona_FN);
  const isAr = lang === "ar";

  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const narrative = useMemo<FlowNarrative | null>(() => {
    if (!activeFlow) return null;
    return generateFlowNarrative(activeFlow);
  }, [activeFlow]);

  const visibleBlocks = useMemo(() => {
    if (!narrative) return [];
    return filterBlocksByPersona(narrative, persona as Persona);
  }, [narrative, persona]);

  if (!narrative || visibleBlocks.length === 0) {
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-io-border bg-io-bg/50">
          <h2 className="text-sm font-bold text-io-primary">
            {isAr ? "السردية" : "Flow Narrative"}
          </h2>
        </div>
        <div className="px-5 py-6 text-center">
          <p className="text-sm text-io-secondary">
            {isAr ? "جارٍ بناء السردية..." : "Narrative building in progress..."}
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-io-border bg-io-bg/50 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-io-primary">
            {isAr ? "سردية الذكاء" : "Intelligence Narrative"}
          </h2>
          <p className="text-[10px] text-io-secondary mt-0.5">
            {isAr ? `عرض: ${persona}` : `Persona: ${persona}`} · {visibleBlocks.length} blocks · {narrative.flowProgress}% complete
          </p>
        </div>
      </div>

      {/* Executive summary banner */}
      <div className="px-5 py-3 bg-io-accent/5 border-b border-io-accent/10">
        <p className="text-sm text-io-primary font-medium leading-relaxed">
          {isAr ? narrative.summaryAr : narrative.summaryEn}
        </p>
      </div>

      {/* Narrative blocks */}
      <div className="p-3 space-y-2">
        {visibleBlocks.map((block, idx) => (
          <NarrativeBlockCard
            key={`${block.type}-${idx}`}
            block={block}
            lang={lang}
            isExpanded={expandedIdx === idx}
            onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
          />
        ))}
      </div>
    </section>
  );
}
