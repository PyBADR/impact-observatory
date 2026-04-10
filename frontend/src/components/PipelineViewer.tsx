"use client";

/**
 * Impact Observatory | مرصد الأثر — Pipeline Viewer (Layer 2)
 *
 * Expandable horizontal pipeline showing each simulation stage
 * with completion status and key metric. Trigger: "View Simulation Flow".
 * Simple, no graphs, no clutter — executive readability.
 */

import React, { useState } from "react";
import { safePercent, formatUSD } from "@/lib/format";
import type { Language } from "@/types/observatory";

interface PipelineStage {
  id: string;
  label: string;
  label_ar: string;
  metric?: string;
  status: "completed" | "skipped" | "failed";
}

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Simulation Pipeline",
    trigger: "View Simulation Flow",
    hide: "Hide Pipeline",
    completed: "completed",
    skipped: "skipped",
    failed: "failed",
  },
  ar: {
    title: "خط أنابيب المحاكاة",
    trigger: "عرض مسار المحاكاة",
    hide: "إخفاء المسار",
    completed: "مكتمل",
    skipped: "تم تخطيه",
    failed: "فشل",
  },
};

function buildStages(
  stagesCompleted: string[],
  stageLog: Record<string, { status: string; duration_ms: number; detail?: string }>,
  severity: number,
  headlineLoss: number,
  confidence: number,
): PipelineStage[] {
  const STAGE_META: { id: string; label: string; label_ar: string; metricFn?: () => string }[] = [
    { id: "scenario", label: "Scenario", label_ar: "السيناريو", metricFn: () => `Severity ${safePercent(severity, 0)}` },
    { id: "physics", label: "Physics", label_ar: "الفيزياء" },
    { id: "graph", label: "Graph", label_ar: "الرسم البياني" },
    { id: "propagation", label: "Propagation", label_ar: "الانتشار" },
    { id: "financial", label: "Financial", label_ar: "المالي", metricFn: () => formatUSD(headlineLoss) },
    { id: "risk", label: "Stress Analysis", label_ar: "تحليل الضغط" },
    { id: "risk_scoring", label: "Risk Scoring", label_ar: "تسجيل المخاطر", metricFn: () => `Confidence ${safePercent(confidence, 0)}` },
    { id: "regulatory", label: "Regulatory", label_ar: "التنظيمي" },
    { id: "decision", label: "Decision", label_ar: "القرار" },
    { id: "explanation", label: "Explainability", label_ar: "التفسير" },
  ];

  return STAGE_META.map((s) => {
    const logEntry = stageLog[s.id];
    let status: "completed" | "skipped" | "failed" = "skipped";
    if (logEntry) {
      status = logEntry.status === "completed" ? "completed" : logEntry.status === "failed" ? "failed" : "skipped";
    } else if (stagesCompleted.includes(s.id)) {
      status = "completed";
    }
    return {
      id: s.id,
      label: s.label,
      label_ar: s.label_ar,
      metric: s.metricFn?.(),
      status,
    };
  });
}

const statusIcon: Record<string, string> = {
  completed: "✓",
  skipped: "–",
  failed: "✗",
};

const statusColor: Record<string, string> = {
  completed: "bg-emerald-50 border-emerald-200 text-emerald-800",
  skipped: "bg-gray-50 border-gray-200 text-gray-500",
  failed: "bg-red-50 border-red-200 text-red-700",
};

export default function PipelineViewer({
  stagesCompleted,
  stageLog,
  scenarioSeverity,
  headlineLoss,
  confidence,
  lang = "en",
}: {
  stagesCompleted: string[];
  stageLog: Record<string, { status: string; duration_ms: number; detail?: string }>;
  scenarioSeverity: number;
  headlineLoss: number;
  confidence: number;
  lang?: Language;
}) {
  const [open, setOpen] = useState(false);
  const t = labels[lang];
  const isRTL = lang === "ar";
  const stages = buildStages(stagesCompleted, stageLog, scenarioSeverity, headlineLoss, confidence);
  const completedCount = stages.filter((s) => s.status === "completed").length;

  return (
    <div className={`${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs font-medium text-io-accent hover:text-io-accent/80 transition-colors mb-2"
      >
        <span className="px-2 py-0.5 bg-io-accent/10 rounded text-[10px] font-bold tabular-nums">
          {completedCount}/{stages.length}
        </span>
        {open ? t.hide : t.trigger}
        <span className="text-[10px]">{open ? "▲" : "▼"}</span>
      </button>

      {/* Pipeline flow */}
      {open && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm overflow-x-auto">
          <p className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-4">
            {t.title}
          </p>
          <div className="flex items-stretch gap-0 min-w-max">
            {stages.map((stage, i) => (
              <React.Fragment key={stage.id}>
                {/* Stage chip */}
                <div className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg border text-center min-w-[100px] ${statusColor[stage.status]}`}>
                  <span className="text-lg font-bold">{statusIcon[stage.status]}</span>
                  <span className="text-[11px] font-semibold leading-tight">
                    {isRTL ? stage.label_ar : stage.label}
                  </span>
                  {stage.metric && (
                    <span className="text-[10px] font-medium opacity-75 mt-0.5">
                      {stage.metric}
                    </span>
                  )}
                </div>
                {/* Arrow connector */}
                {i < stages.length - 1 && (
                  <div className="flex items-center px-1">
                    <div className="w-6 h-px bg-io-border" />
                    <div className="w-0 h-0 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent border-l-[6px] border-l-io-border" />
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
