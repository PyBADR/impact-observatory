"use client";

/**
 * Impact Observatory | مرصد الأثر — Data Flow Panel (Layer 3)
 *
 * Simplified economic cascade visualization. Max 6-8 nodes,
 * business-readable labels, arrows only. No complex graph physics.
 * Trigger: "Reveal System Intelligence".
 */

import React, { useState } from "react";
import type { Language } from "@/types/observatory";

interface FlowNode {
  id: string;
  label: string;
  label_ar: string;
  color: string;
}

interface FlowEdge {
  from: string;
  to: string;
}

const labels: Record<Language, Record<string, string>> = {
  en: {
    trigger: "Reveal System Intelligence",
    hide: "Hide Intelligence View",
    title: "Economic Cascade Flow",
    subtitle: "How disruptions propagate through the GCC financial ecosystem",
  },
  ar: {
    trigger: "كشف ذكاء النظام",
    hide: "إخفاء عرض الذكاء",
    title: "مسار التأثير الاقتصادي",
    subtitle: "كيف تنتشر الاضطرابات عبر النظام المالي الخليجي",
  },
};

// Fixed cascade topology — 7 nodes representing the GCC economic cascade
const NODES: FlowNode[] = [
  { id: "trigger",     label: "Trigger Event",       label_ar: "الحدث المحفز",       color: "bg-red-100 border-red-300 text-red-800" },
  { id: "supply",      label: "Supply Chain",        label_ar: "سلسلة التوريد",      color: "bg-orange-100 border-orange-300 text-orange-800" },
  { id: "energy",      label: "Energy & Commodities", label_ar: "الطاقة والسلع",     color: "bg-amber-100 border-amber-300 text-amber-800" },
  { id: "banking",     label: "Banking Sector",      label_ar: "القطاع البنكي",      color: "bg-blue-100 border-blue-300 text-blue-800" },
  { id: "insurance",   label: "Insurance Sector",    label_ar: "قطاع التأمين",       color: "bg-indigo-100 border-indigo-300 text-indigo-800" },
  { id: "fintech",     label: "Fintech & Payments",  label_ar: "الفنتك والمدفوعات", color: "bg-violet-100 border-violet-300 text-violet-800" },
  { id: "gdp",         label: "GDP Impact",          label_ar: "الأثر على الناتج",   color: "bg-slate-100 border-slate-300 text-slate-800" },
];

const EDGES: FlowEdge[] = [
  { from: "trigger",   to: "supply" },
  { from: "trigger",   to: "energy" },
  { from: "supply",    to: "banking" },
  { from: "energy",    to: "banking" },
  { from: "banking",   to: "insurance" },
  { from: "banking",   to: "fintech" },
  { from: "insurance", to: "gdp" },
  { from: "fintech",   to: "gdp" },
];

// Layout: 4 columns representing cascade layers
const LAYOUT: Record<string, { col: number; row: number }> = {
  trigger:   { col: 0, row: 0 },
  supply:    { col: 1, row: 0 },
  energy:    { col: 1, row: 1 },
  banking:   { col: 2, row: 0 },
  insurance: { col: 3, row: 0 },
  fintech:   { col: 3, row: 1 },
  gdp:       { col: 4, row: 0 },
};

export default function DataFlowPanel({
  scenarioLabel = "",
  lang = "en",
}: {
  scenarioLabel?: string;
  lang?: Language;
}) {
  const [open, setOpen] = useState(false);
  const t = labels[lang];
  const isRTL = lang === "ar";

  // Group nodes by column for rendering
  const columns: FlowNode[][] = [];
  NODES.forEach((node) => {
    const col = LAYOUT[node.id]?.col ?? 0;
    if (!columns[col]) columns[col] = [];
    columns[col].push(node);
  });

  return (
    <div className={`${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs font-medium text-io-accent hover:text-io-accent/80 transition-colors mb-2"
      >
        {open ? t.hide : t.trigger}
        <span className="text-[10px]">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm overflow-x-auto">
          <div className="mb-4">
            <p className="text-xs font-semibold text-io-secondary uppercase tracking-wider">
              {t.title}
            </p>
            <p className="text-[11px] text-io-secondary mt-0.5">
              {t.subtitle}{scenarioLabel ? ` — ${scenarioLabel}` : ""}
            </p>
          </div>

          {/* Cascade flow: columns with arrows */}
          <div className="flex items-stretch gap-0 min-w-max">
            {columns.map((col, colIdx) => (
              <React.Fragment key={colIdx}>
                {/* Column of nodes */}
                <div className="flex flex-col gap-3 min-w-[140px]">
                  {col.map((node) => (
                    <div
                      key={node.id}
                      className={`px-4 py-3 rounded-lg border text-center ${node.color}`}
                    >
                      <p className="text-[12px] font-semibold leading-tight">
                        {isRTL ? node.label_ar : node.label}
                      </p>
                    </div>
                  ))}
                </div>
                {/* Arrow between columns */}
                {colIdx < columns.length - 1 && (
                  <div className="flex items-center px-2">
                    <div className="w-8 h-px bg-io-border" />
                    <div className="w-0 h-0 border-t-[5px] border-t-transparent border-b-[5px] border-b-transparent border-l-[8px] border-l-io-border" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
