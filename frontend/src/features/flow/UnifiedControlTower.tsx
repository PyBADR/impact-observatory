"use client";

/**
 * Impact Observatory — Unified Control Tower
 *
 * The CENTRAL BRAIN of the system. Not a dashboard — a command center.
 *
 * Consumes ALL intelligence layers:
 *   - Signals (Jet Nexus)
 *   - Reasoning (TREK)
 *   - Simulation (Impact)
 *   - Decisions
 *   - Outcomes
 *   - ROI
 *
 * Persona-aware: renders different depth for Executive / Analyst / Regulator.
 * Flow-aware: shows the current flow state and progress.
 * Narrative-first: every data point has a story.
 *
 * This component REPLACES the old ExecutiveControlTower as the system's hub.
 * The old ExecutiveControlTower still renders its 5 panels (Value, Narrative,
 * Drivers, Performance, Risk) — this component wraps it with flow context,
 * pipeline narrative, and cross-persona awareness.
 */

import React, { useMemo } from "react";
import { useFlowStore, FLOW_STAGES_ORDERED, FLOW_STAGE_META } from "@/store/flow-store";
import { useAppStore } from "@/store/app-store";
import {
  toControlTowerViewModel,
  toExecutiveViewModel,
  toRegulatorViewModel,
  toAnalystViewModel,
} from "@/lib/persona-view-model";
import { ExecutiveControlTower } from "@/features/personas/ExecutiveControlTower";
import { FlowTimeline } from "@/features/flow/FlowTimeline";
import { FlowNarrativePanel } from "@/features/flow/FlowNarrativePanel";
import { FlowTimelineInline } from "@/features/flow/FlowTimeline";
import { AuthorityQueuePanel } from "@/features/authority/AuthorityQueuePanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import type { Language, RunResult } from "@/types/observatory";
import type { Persona } from "@/lib/persona-view-model";
import type { FlowStage } from "@/store/flow-store";
import { formatUSD } from "@/lib/format";

// ─── System Health Indicator ────────────────────────────────────────────────

function SystemHealthBadge({ health }: { health: "healthy" | "degraded" | "failed" }) {
  const styles = {
    healthy:  "bg-emerald-100 border-emerald-200 text-emerald-700",
    degraded: "bg-amber-100 border-amber-200 text-amber-700",
    failed:   "bg-red-100 border-red-200 text-red-700",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${styles[health]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${health === "healthy" ? "bg-emerald-500" : health === "degraded" ? "bg-amber-500" : "bg-red-500"}`} />
      {health}
    </span>
  );
}

// ─── Flow Stage Summary Cards ───────────────────────────────────────────────

function StageSummaryCards({
  lang,
  pipelineStagesCompleted,
}: {
  lang: Language;
  // CRIT-02: pass the backend pipeline count (e.g. 18) so it shows in the card
  // instead of the flow store's UI-stage count which maxes out at 7.
  pipelineStagesCompleted: number;
}) {
  const activeFlow = useFlowStore((s) => s.activeFlow);
  const isAr = lang === "ar";

  if (!activeFlow) return null;

  const activeStages = activeFlow.stages.filter((s) => s.status === "active");
  const failedStages = activeFlow.stages.filter((s) => s.status === "failed");
  // Show the authoritative backend pipeline stage count when available;
  // fall back to flow store UI stage count so the card is never empty.
  const completedCount =
    pipelineStagesCompleted > 0
      ? pipelineStagesCompleted
      : activeFlow.stages.filter((s) => s.status === "completed").length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-center">
        <p className="text-2xl font-bold text-emerald-700">{completedCount}</p>
        <p className="text-xs text-emerald-600 font-medium">
          {isAr ? "مراحل مكتملة" : "Stages Complete"}
        </p>
      </div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-center">
        <p className="text-2xl font-bold text-blue-700">{activeStages.length}</p>
        <p className="text-xs text-blue-600 font-medium">
          {isAr ? "نشط الآن" : "Active Now"}
        </p>
      </div>
      <div className={`${failedStages.length > 0 ? "bg-red-50 border-red-200" : "bg-gray-50 border-gray-200"} border rounded-lg px-4 py-3 text-center`}>
        <p className={`text-2xl font-bold ${failedStages.length > 0 ? "text-red-700" : "text-gray-400"}`}>
          {failedStages.length}
        </p>
        <p className={`text-xs font-medium ${failedStages.length > 0 ? "text-red-600" : "text-gray-400"}`}>
          {isAr ? "فشل" : "Failed"}
        </p>
      </div>
      <div className="bg-io-bg border border-io-border rounded-lg px-4 py-3 text-center">
        <p className="text-2xl font-bold text-io-primary">{FLOW_STAGES_ORDERED.length}</p>
        <p className="text-xs text-io-secondary font-medium">
          {isAr ? "إجمالي المراحل" : "Total Stages"}
        </p>
      </div>
    </div>
  );
}

// ─── Cross-Layer Intelligence Summary ───────────────────────────────────────

function IntelligenceSummary({
  result,
  lang,
}: {
  result: RunResult;
  lang: Language;
}) {
  const isAr = lang === "ar";
  const outcomes = useAppStore((s) => s.outcomes);
  const values = useAppStore((s) => s.decisionValues);
  const signals = useAppStore((s) => s.liveSignals);
  const decisions = useAppStore((s) => s.operatorDecisions);

  const totalLoss = result.headline?.total_loss_usd ?? 0;
  const classification = result.executive_status ?? "unknown";
  const actionCount = result.decisions?.actions?.length ?? 0;
  const netValue = values.reduce((sum, v) => sum + (v.net_value ?? 0), 0);
  const confirmedOutcomes = outcomes.filter((o) => o.outcome_status === "CONFIRMED").length;

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-io-border bg-gradient-to-r from-io-accent/5 to-transparent">
        <h2 className="text-sm font-bold text-io-primary flex items-center gap-2">
          <span className="text-base">🏛️</span>
          {isAr ? "ملخص الذكاء الشامل" : "Cross-Layer Intelligence Summary"}
        </h2>
      </div>
      <div className="px-5 py-4">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Signals Layer */}
          <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "الإشارات" : "Signals"}
            </p>
            <p className="text-lg font-bold text-io-primary">{signals.length}</p>
            <p className="text-[10px] text-io-secondary">
              {isAr ? "إشارات حية" : "live signals"}
            </p>
          </div>

          {/* Simulation Layer */}
          <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "الأثر" : "Impact"}
            </p>
            <p className="text-lg font-bold text-red-700">{formatUSD(totalLoss)}</p>
            <p className="text-[10px] text-io-secondary uppercase">{classification}</p>
          </div>

          {/* Decision Layer */}
          <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "القرارات" : "Decisions"}
            </p>
            <p className="text-lg font-bold text-io-primary">{actionCount + decisions.length}</p>
            <p className="text-[10px] text-io-secondary">
              {actionCount} {isAr ? "إجراء" : "actions"} + {decisions.length} {isAr ? "مشغّل" : "operator"}
            </p>
          </div>

          {/* Outcome Layer */}
          <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "النتائج" : "Outcomes"}
            </p>
            <p className="text-lg font-bold text-io-primary">{outcomes.length}</p>
            <p className="text-[10px] text-io-secondary">
              {confirmedOutcomes} {isAr ? "مؤكد" : "confirmed"}
            </p>
          </div>

          {/* ROI Layer */}
          <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "العائد" : "ROI"}
            </p>
            <p className={`text-lg font-bold ${netValue >= 0 ? "text-emerald-700" : "text-red-700"}`}>
              {formatUSD(netValue)}
            </p>
            <p className="text-[10px] text-io-secondary">
              {values.length} {isAr ? "قيمة" : "values"}
            </p>
          </div>

          {/* Operator Layer */}
          <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "المشغّل" : "Operator"}
            </p>
            <p className="text-lg font-bold text-io-primary">{decisions.length}</p>
            <p className="text-[10px] text-io-secondary">
              {decisions.filter((d) => d.decision_status === "CLOSED").length} {isAr ? "مغلق" : "closed"}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Main: Unified Control Tower ────────────────────────────────────────────

interface UnifiedControlTowerProps {
  result: RunResult;
  lang: Language;
}

export function UnifiedControlTower({ result, lang }: UnifiedControlTowerProps) {
  const persona = useAppStore((s) => s.persona);
  const outcomes = useAppStore((s) => s.outcomes);
  const decisionValues = useAppStore((s) => s.decisionValues);
  const operatorDecisions = useAppStore((s) => s.operatorDecisions);
  const activeFlow = useFlowStore((s) => s.activeFlow);
  const isAr = lang === "ar";

  // Build the existing control tower view model (preserves backward compat)
  const towerVm = useMemo(
    () => toControlTowerViewModel(operatorDecisions, outcomes, decisionValues),
    [operatorDecisions, outcomes, decisionValues]
  );

  return (
    <div className="space-y-6">
      {/* ── Control Tower Header ────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-io-primary flex items-center gap-2">
            <span className="text-2xl">🏛️</span>
            {isAr ? "برج التحكم" : "Control Tower"}
          </h1>
          <p className="text-xs text-io-secondary mt-1">
            {isAr
              ? "المركز الشامل لذكاء القرار — جميع الطبقات في سياق واحد"
              : "Unified Decision Intelligence Hub — all layers in context"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {activeFlow && <SystemHealthBadge health={activeFlow.health} />}
          <FlowTimelineInline lang={lang} />
        </div>
      </div>

      {/* ── Flow Stage Summary ──────────────────────────────────────────── */}
      <ErrorBoundary section="Stage Summary">
        <StageSummaryCards
          lang={lang}
          pipelineStagesCompleted={result.pipeline_stages_completed ?? 0}
        />
      </ErrorBoundary>

      {/* ── Cross-Layer Intelligence Summary ────────────────────────────── */}
      <ErrorBoundary section="Intelligence Summary">
        <IntelligenceSummary result={result} lang={lang} />
      </ErrorBoundary>

      {/* ── Decision Authority Queue ─────────────────────────────────── */}
      <ErrorBoundary section="Authority Queue">
        <AuthorityQueuePanel lang={lang} />
      </ErrorBoundary>

      {/* ── Flow Narrative (persona-filtered) ───────────────────────────── */}
      <ErrorBoundary section="Flow Narrative">
        <FlowNarrativePanel lang={lang} />
      </ErrorBoundary>

      {/* ── Existing Control Tower Panels (Value, Drivers, Performance, Risk) */}
      <ErrorBoundary section="Executive Control Tower">
        <ExecutiveControlTower vm={towerVm} lang={lang} />
      </ErrorBoundary>
    </div>
  );
}
