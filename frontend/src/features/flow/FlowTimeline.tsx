"use client";

/**
 * Impact Observatory — Flow Timeline
 *
 * Visual pipeline indicator that shows the current stage of the
 * unified decision intelligence flow:
 *
 *   Signal → Reasoning → Simulation → Decision → Outcome → ROI → Control Tower
 *
 * Always visible during an active flow. Shows:
 *   - Which stages are complete (green)
 *   - Which stage is active (pulsing blue)
 *   - Which stages are pending (gray)
 *   - Which stages failed (red)
 *   - Overall flow progress percentage
 *
 * Clicking a completed stage scrolls to that section in the persona view.
 */

import React from "react";
import { useFlowStore, FLOW_STAGES_ORDERED, FLOW_STAGE_META } from "@/store/flow-store";
import type { FlowStage } from "@/store/flow-store";
import type { Language } from "@/types/observatory";

// ─── Module-level stable selectors ───────────────────────────────────────────
type FlowS_FT = ReturnType<typeof useFlowStore.getState>;
const selectFlowActiveFlow = (s: FlowS_FT) => s.activeFlow;

// ─── Stage Status Colors ────────────────────────────────────────────────────

const STATUS_STYLES = {
  completed: {
    dot: "bg-emerald-500 border-emerald-400",
    line: "bg-emerald-400",
    label: "text-emerald-700 font-semibold",
  },
  active: {
    dot: "bg-blue-500 border-blue-400 animate-pulse ring-4 ring-blue-200",
    line: "bg-io-border",
    label: "text-blue-700 font-bold",
  },
  failed: {
    dot: "bg-red-500 border-red-400",
    line: "bg-red-300",
    label: "text-red-700 font-semibold",
  },
  pending: {
    dot: "bg-gray-200 border-gray-300",
    line: "bg-io-border",
    label: "text-io-secondary",
  },
  skipped: {
    dot: "bg-gray-200 border-gray-300 opacity-50",
    line: "bg-io-border opacity-50",
    label: "text-io-secondary opacity-50",
  },
};

type StageVisualStatus = keyof typeof STATUS_STYLES;

function getStageStatus(stage: FlowStage): StageVisualStatus {
  const flow = useFlowStore.getState().activeFlow;
  if (!flow) return "pending";

  const entry = flow.stages.find((s) => s.stage === stage);
  if (!entry) return "pending";
  if (entry.status === "completed") return "completed";
  if (entry.status === "failed") return "failed";
  if (entry.status === "skipped") return "skipped";
  if (entry.status === "active") return "active";
  return "pending";
}

// ─── Timeline Node ──────────────────────────────────────────────────────────

interface TimelineNodeProps {
  stage: FlowStage;
  isLast: boolean;
  lang: Language;
  onStageClick?: (stage: FlowStage) => void;
}

function TimelineNode({ stage, isLast, lang, onStageClick }: TimelineNodeProps) {
  const meta = FLOW_STAGE_META[stage];
  const status = getStageStatus(stage);
  const styles = STATUS_STYLES[status];
  const isAr = lang === "ar";
  const isClickable = status === "completed" || status === "active";

  return (
    <div className="flex items-center">
      {/* Node */}
      <button
        onClick={() => isClickable && onStageClick?.(stage)}
        disabled={!isClickable}
        className={`flex flex-col items-center gap-1 group ${isClickable ? "cursor-pointer" : "cursor-default"}`}
        title={`${meta.label}: ${status}`}
      >
        {/* Dot */}
        <div
          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm transition-all
            ${styles.dot}
            ${isClickable ? "group-hover:scale-110" : ""}
          `}
        >
          {status === "completed" ? (
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          ) : status === "failed" ? (
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <span className="text-xs">{meta.icon}</span>
          )}
        </div>
        {/* Label */}
        <span className={`text-[10px] leading-tight text-center whitespace-nowrap ${styles.label}`}>
          {isAr ? meta.labelAr : meta.label}
        </span>
      </button>

      {/* Connector line */}
      {!isLast && (
        <div className={`h-0.5 w-6 md:w-10 lg:w-14 ${styles.line} mx-1`} />
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────────────

interface FlowTimelineProps {
  lang: Language;
  onStageClick?: (stage: FlowStage) => void;
  compact?: boolean;
}

export function FlowTimeline({ lang, onStageClick, compact = false }: FlowTimelineProps) {
  const activeFlow = useFlowStore(selectFlowActiveFlow);
  const getFlowProgress = useFlowStore((s) => s.getFlowProgress);
  const isAr = lang === "ar";

  if (!activeFlow) return null;

  const progress = getFlowProgress();

  return (
    <div className={`bg-io-surface border-b border-io-border ${compact ? "px-4 py-2" : "px-6 lg:px-10 py-3"}`}>
      <div className="max-w-6xl mx-auto">
        {/* Progress bar */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-io-secondary">
            {isAr ? "مسار الذكاء" : "Intelligence Flow"}
          </span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-1.5 bg-io-border rounded-full overflow-hidden">
              <div
                className="h-full bg-io-accent rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-io-secondary">{progress}%</span>
          </div>
        </div>

        {/* Stage nodes */}
        <div className="flex items-start justify-center overflow-x-auto pb-1" dir="ltr">
          {FLOW_STAGES_ORDERED.map((stage, idx) => (
            <TimelineNode
              key={stage}
              stage={stage}
              isLast={idx === FLOW_STAGES_ORDERED.length - 1}
              lang={lang}
              onStageClick={onStageClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Compact Inline Version (for embedding in panels) ───────────────────────

export function FlowTimelineInline({ lang }: { lang: Language }) {
  const activeFlow = useFlowStore(selectFlowActiveFlow);
  const isAr = lang === "ar";

  if (!activeFlow) return null;

  return (
    <div className="flex items-center gap-1.5 text-[10px]">
      {FLOW_STAGES_ORDERED.map((stage, idx) => {
        const status = getStageStatus(stage);
        const meta = FLOW_STAGE_META[stage];
        const isActive = status === "active";
        const isComplete = status === "completed";
        const isFailed = status === "failed";

        return (
          <React.Fragment key={stage}>
            <span
              className={`
                inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full
                ${isComplete ? "bg-emerald-100 text-emerald-700" : ""}
                ${isActive ? "bg-blue-100 text-blue-700 font-bold" : ""}
                ${isFailed ? "bg-red-100 text-red-700" : ""}
                ${!isComplete && !isActive && !isFailed ? "bg-gray-100 text-gray-400" : ""}
              `}
              title={isAr ? meta.labelAr : meta.label}
            >
              {isComplete ? "✓" : isFailed ? "✗" : meta.icon}
            </span>
            {idx < FLOW_STAGES_ORDERED.length - 1 && (
              <span className={`text-[8px] ${isComplete ? "text-emerald-400" : "text-gray-300"}`}>→</span>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
