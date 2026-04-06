"use client";

/**
 * Impact Observatory — Persona Flow View
 *
 * Unified entry point for all three persona views, wired into the flow engine.
 * Each persona sees the SAME flow through a DIFFERENT lens:
 *
 *   EXECUTIVE:
 *     - Flow Timeline (compact) → Intelligence Summary → KPIs → Sectors
 *     → Priority Actions → Control Tower (full)
 *     Focus: ROI, decisions, value summary
 *
 *   ANALYST:
 *     - Flow Timeline (full) → Narrative (reasoning-heavy) → Run Metadata
 *     → Score Breakdown → Entity Table → Causal Chain → Signals → Decisions
 *     Focus: reasoning chains, propagation logic, signal lineage
 *
 *   REGULATOR:
 *     - Flow Timeline (full) → Narrative (audit-heavy) → Provenance
 *     → Decision Lineage → Signal Trace → Pipeline Accountability → Outcomes
 *     Focus: audit trail, compliance metrics, decision traceability
 *
 * ALL persona views include the FlowTimeline and FlowNarrative.
 * This eliminates the old fragmentation where views were disconnected.
 */

import React from "react";
import { useAppStore } from "@/store/app-store";
import { useFlowStore } from "@/store/flow-store";
import { FlowTimeline } from "@/features/flow/FlowTimeline";
import { FlowNarrativePanel } from "@/features/flow/FlowNarrativePanel";
import { UnifiedControlTower } from "@/features/flow/UnifiedControlTower";
import { FlowTimelineInline } from "@/features/flow/FlowTimeline";
import { ExecutiveView } from "@/features/personas/ExecutiveView";
import { AnalystView } from "@/features/personas/AnalystView";
import { RegulatorView } from "@/features/personas/RegulatorView";
import ExecutiveDashboard from "@/features/dashboard/ExecutiveDashboard";
import { AuthorityQueuePanel } from "@/features/authority/AuthorityQueuePanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import type { RunResult, Language } from "@/types/observatory";
import type { FlowStage } from "@/store/flow-store";

// ─── Flow-Aware Executive View ──────────────────────────────────────────────

function FlowExecutiveView({
  result,
  lang,
  onStageClick,
}: {
  result: RunResult;
  lang: Language;
  onStageClick?: (stage: FlowStage) => void;
}) {
  const isAr = lang === "ar";

  return (
    <div className="space-y-0">
      {/* Flow Timeline — compact for executive, shows progress at a glance */}
      <FlowTimeline lang={lang} onStageClick={onStageClick} compact />

      {/* Unified Control Tower replaces the old dashboard + control tower split */}
      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-8">
        <ErrorBoundary section="Unified Control Tower">
          <UnifiedControlTower result={result} lang={lang} />
        </ErrorBoundary>
      </div>

      {/* Executive Dashboard — boardroom-grade panels below control tower:
          KPI strip, sector stress, decision action cards, timelines, PDF export */}
      <div className="border-t border-io-border">
        <ErrorBoundary section="Executive Dashboard">
          <ExecutiveDashboard data={result} lang={lang} />
        </ErrorBoundary>
      </div>
    </div>
  );
}

// ─── Flow-Aware Analyst View ────────────────────────────────────────────────

function FlowAnalystView({
  result,
  lang,
  onStageClick,
}: {
  result: RunResult;
  lang: Language;
  onStageClick?: (stage: FlowStage) => void;
}) {
  return (
    <div className="space-y-0">
      {/* Flow Timeline — full for analyst, every stage matters */}
      <FlowTimeline lang={lang} onStageClick={onStageClick} />

      {/* Flow Narrative — reasoning-heavy blocks visible */}
      <div className="max-w-6xl mx-auto px-6 lg:px-10 pt-6 pb-2">
        <ErrorBoundary section="Flow Narrative">
          <FlowNarrativePanel lang={lang} />
        </ErrorBoundary>
      </div>

      {/* Authority Queue — Analyst sees Recommendation Queue */}
      <div className="max-w-6xl mx-auto px-6 lg:px-10 pb-2">
        <ErrorBoundary section="Authority Queue">
          <AuthorityQueuePanel lang={lang} />
        </ErrorBoundary>
      </div>

      {/* Original AnalystView — all the deep mechanics */}
      <ErrorBoundary section="Analyst View">
        <AnalystView result={result} lang={lang} />
      </ErrorBoundary>
    </div>
  );
}

// ─── Flow-Aware Regulator View ──────────────────────────────────────────────

function FlowRegulatorView({
  result,
  lang,
  onStageClick,
}: {
  result: RunResult;
  lang: Language;
  onStageClick?: (stage: FlowStage) => void;
}) {
  const activeFlow = useFlowStore((s) => s.activeFlow);
  const isAr = lang === "ar";

  return (
    <div className="space-y-0">
      {/* Flow Timeline — full for regulator, every stage is auditable */}
      <FlowTimeline lang={lang} onStageClick={onStageClick} />

      {/* Flow provenance banner */}
      {activeFlow && (
        <div className="bg-gray-50 border-b border-gray-200 px-6 lg:px-10 py-2">
          <div className="max-w-6xl mx-auto flex items-center justify-between text-xs">
            <div className="flex items-center gap-4 text-io-secondary">
              <span>
                <span className="font-semibold">Flow ID:</span>{" "}
                <code className="font-mono text-[10px]">{activeFlow.flowId}</code>
              </span>
              <span>
                <span className="font-semibold">{isAr ? "بدأ" : "Started"}:</span>{" "}
                <code className="font-mono text-[10px]">
                  {new Date(activeFlow.createdAt).toISOString().replace("T", " ").slice(0, 19)}
                </code>
              </span>
              <span>
                <span className="font-semibold">{isAr ? "المراحل" : "Stages"}:</span>{" "}
                {activeFlow.stages.length}
              </span>
            </div>
            <FlowTimelineInline lang={lang} />
          </div>
        </div>
      )}

      {/* Flow Narrative — audit-heavy blocks visible */}
      <div className="max-w-6xl mx-auto px-6 lg:px-10 pt-6 pb-2">
        <ErrorBoundary section="Flow Narrative">
          <FlowNarrativePanel lang={lang} />
        </ErrorBoundary>
      </div>

      {/* Authority Queue — Regulator sees Compliance & Authority Audit */}
      <div className="max-w-6xl mx-auto px-6 lg:px-10 pb-2">
        <ErrorBoundary section="Authority Queue">
          <AuthorityQueuePanel lang={lang} />
        </ErrorBoundary>
      </div>

      {/* Original RegulatorView — audit tables, lineage, pipeline accountability */}
      <ErrorBoundary section="Regulator View">
        <RegulatorView result={result} lang={lang} />
      </ErrorBoundary>
    </div>
  );
}

// ─── Main: Persona Flow Router ──────────────────────────────────────────────

interface PersonaFlowViewProps {
  result: RunResult;
  lang: Language;
  onStageClick?: (stage: FlowStage) => void;
}

export function PersonaFlowView({ result, lang, onStageClick }: PersonaFlowViewProps) {
  const persona = useAppStore((s) => s.persona);

  switch (persona) {
    case "executive":
      return <FlowExecutiveView result={result} lang={lang} onStageClick={onStageClick} />;
    case "analyst":
      return <FlowAnalystView result={result} lang={lang} onStageClick={onStageClick} />;
    case "regulator":
      return <FlowRegulatorView result={result} lang={lang} onStageClick={onStageClick} />;
    default:
      return <FlowExecutiveView result={result} lang={lang} onStageClick={onStageClick} />;
  }
}
