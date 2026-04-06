"use client";

/**
 * Impact Observatory — Executive View
 *
 * Persona: EXECUTIVE
 * Priority order:
 *   1. KPI strip  — headline loss, severity, peak day, liquidity breach, status, confidence
 *   2. Sector summary cards — banking / insurance / fintech with worst-case callout
 *   3. Priority action table — top 3 decisions, loss avoided, time to act
 *   4. Scenario context — label, run ID, narrative summary
 *
 * Not shown: entity-level tables, causal chain, stage logs, signal mechanics,
 * operator decision payloads, pipeline internals.
 */

import React from "react";
import type { RunResult, Language } from "@/types/observatory";
import { useAppStore } from "@/store/app-store";
import {
  toExecutiveViewModel,
  toControlTowerViewModel,
  classColor,
  type ExecutiveKPI,
  type ExecutiveSectorCard,
  type ExecutiveActionRow,
  type ExecutiveOutcomesSummary,
} from "@/lib/persona-view-model";
import { ExecutiveControlTower } from "@/features/personas/ExecutiveControlTower";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AppS_EV = ReturnType<typeof useAppStore.getState>;
const selectOutcomes_EV          = (s: AppS_EV) => s.outcomes;
const selectDecisionValues_EV    = (s: AppS_EV) => s.decisionValues;
const selectOperatorDecisions_EV = (s: AppS_EV) => s.operatorDecisions;

// ─── Classification badge ────────────────────────────────────────────────────

function Badge({ level }: { level: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${classColor(level as never)}`}>
      {level}
    </span>
  );
}

// ─── Status indicator ────────────────────────────────────────────────────────

const EXEC_STATUS_COLORS: Record<string, string> = {
  monitor:   "bg-green-100 text-green-800 border-green-200",
  intervene: "bg-yellow-100 text-yellow-800 border-yellow-200",
  escalate:  "bg-orange-100 text-orange-800 border-orange-200",
  crisis:    "bg-red-100 text-red-800 border-red-200",
};

function ExecStatusBadge({ status }: { status: string }) {
  const cls = EXEC_STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700 border-gray-200";
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest border ${cls}`}>
      {status}
    </span>
  );
}

// ─── KPI strip ───────────────────────────────────────────────────────────────

function KPICard({
  label, value, sub, accent,
}: {
  label: string; value: string; sub?: string; accent?: boolean;
}) {
  return (
    <div className={`bg-io-surface border rounded-xl p-5 shadow-sm ${accent ? "border-io-accent/30 bg-io-accent/5" : "border-io-border"}`}>
      <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{label}</p>
      <p className={`text-3xl font-bold tabular-nums ${accent ? "text-io-accent" : "text-io-primary"}`}>{value}</p>
      {sub && <p className="text-xs text-io-secondary mt-1">{sub}</p>}
    </div>
  );
}

function KPIStrip({ kpis, lang }: { kpis: ExecutiveKPI; lang: Language }) {
  const isAr = lang === "ar";
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      <KPICard
        label={isAr ? "إجمالي الخسارة" : "Headline Loss"}
        value={kpis.headlineLoss}
        sub={isAr ? "خسارة متوقعة" : "projected loss"}
        accent
      />
      <KPICard
        label={isAr ? "مستوى الشدة" : "Severity"}
        value={kpis.severity}
        sub={isAr ? "مدخل السيناريو" : "scenario input"}
      />
      <KPICard
        label={isAr ? "يوم الذروة" : "Peak Day"}
        value={`Day ${kpis.peakDay}`}
        sub={isAr ? "أعلى تأثير" : "highest impact"}
      />
      <KPICard
        label={isAr ? "كسر السيولة" : "Liquidity Breach"}
        value={kpis.liquidityBreachLabel}
        sub={isAr ? "أبكر خرق" : "earliest breach"}
      />
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm flex flex-col">
        <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">
          {isAr ? "الحالة التنفيذية" : "Executive Status"}
        </p>
        <div className="mt-1"><ExecStatusBadge status={kpis.executiveStatus} /></div>
        <p className="text-xs text-io-secondary mt-2">
          {isAr ? "شدة الأعمال: " : "Business: "}
          <span className="font-semibold text-io-primary capitalize">{kpis.businessSeverity}</span>
        </p>
      </div>
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm flex flex-col">
        <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">
          {isAr ? "المستوى الكلي" : "Overall Risk"}
        </p>
        <div className="mt-1"><Badge level={kpis.overallClassification} /></div>
        <p className="text-xs text-io-secondary mt-2">
          {isAr ? "الثقة: " : "Confidence: "}
          <span className="font-semibold text-io-primary">{kpis.confidence}</span>
        </p>
      </div>
    </div>
  );
}

// ─── Sector summary ──────────────────────────────────────────────────────────

function SectorCard({ sector, lang }: { sector: ExecutiveSectorCard; lang: Language }) {
  const isAr = lang === "ar";
  return (
    <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-io-primary">
          {isAr ? sector.nameAr : sector.name}
        </h3>
        <Badge level={sector.classification} />
      </div>
      <p className="text-2xl font-bold tabular-nums text-io-primary mb-3">{sector.stressLabel}</p>
      <div className="space-y-1.5 text-sm">
        <div className="flex justify-between">
          <span className="text-io-secondary">
            {isAr ? sector.primaryMetricLabelAr : sector.primaryMetricLabel}
          </span>
          <span className="font-semibold text-io-primary">{sector.primaryMetricValue}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-io-secondary">{sector.secondaryMetricLabel}</span>
          <span className={`font-semibold ${
            sector.secondaryMetricValue === "TRIGGERED" ? "text-io-danger" : "text-io-primary"
          }`}>{sector.secondaryMetricValue}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Priority action table ───────────────────────────────────────────────────

const URGENCY_COLORS = ["bg-red-500", "bg-orange-400", "bg-yellow-400", "bg-green-400", "bg-gray-200"];

function UrgencyDot({ urgency }: { urgency: number }) {
  const pct = Math.max(0, Math.min(1, urgency));
  const idx = Math.min(Math.floor((1 - pct) * 5), 4);
  return <span className={`inline-block w-2 h-2 rounded-full ${URGENCY_COLORS[idx]}`} />;
}

function ActionTable({ actions, lang }: { actions: ExecutiveActionRow[]; lang: Language }) {
  const isAr = lang === "ar";
  if (actions.length === 0) {
    return (
      <p className="text-sm text-io-secondary py-4 text-center">
        {isAr ? "لا توجد إجراءات" : "No actions available"}
      </p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-io-border">
            <th className="text-left py-2 pr-4 text-xs font-semibold uppercase tracking-wider text-io-secondary">#</th>
            <th className="text-left py-2 pr-4 text-xs font-semibold uppercase tracking-wider text-io-secondary">
              {isAr ? "الإجراء" : "Action"}
            </th>
            <th className="text-left py-2 pr-4 text-xs font-semibold uppercase tracking-wider text-io-secondary">
              {isAr ? "القطاع" : "Sector"}
            </th>
            <th className="text-left py-2 pr-4 text-xs font-semibold uppercase tracking-wider text-io-secondary">
              {isAr ? "المسؤول" : "Owner"}
            </th>
            <th className="text-right py-2 pr-4 text-xs font-semibold uppercase tracking-wider text-io-secondary">
              {isAr ? "الخسارة المتجنبة" : "Loss Avoided"}
            </th>
            <th className="text-right py-2 pr-4 text-xs font-semibold uppercase tracking-wider text-io-secondary">
              {isAr ? "الوقت للتصرف" : "Time to Act"}
            </th>
            <th className="text-center py-2 text-xs font-semibold uppercase tracking-wider text-io-secondary">
              {isAr ? "الإلحاح" : "Urgency"}
            </th>
          </tr>
        </thead>
        <tbody>
          {actions.map((a, i) => (
            <tr key={a.id} className="border-b border-io-border/50 hover:bg-io-bg/50 transition-colors">
              <td className="py-3 pr-4 text-xs font-bold text-io-secondary">{i + 1}</td>
              <td className="py-3 pr-4 text-io-primary font-medium max-w-xs">
                {isAr && a.actionAr ? a.actionAr : a.action}
              </td>
              <td className="py-3 pr-4">
                <span className="text-xs px-2 py-0.5 bg-io-bg border border-io-border rounded font-medium text-io-secondary capitalize">
                  {a.sector}
                </span>
              </td>
              <td className="py-3 pr-4 text-io-secondary text-xs">{a.owner}</td>
              <td className="py-3 pr-4 text-right font-semibold text-green-700">{a.lossAvoided}</td>
              <td className="py-3 pr-4 text-right text-io-primary font-medium">{a.timeToAct}</td>
              <td className="py-3 text-center">
                <UrgencyDot urgency={a.urgency} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Outcome realization panel ───────────────────────────────────────────────

const OUTCOME_STATUS_COLORS: Record<string, string> = {
  confirmed:          "bg-green-50 border-green-200 text-green-800",
  disputed:           "bg-orange-50 border-orange-200 text-orange-700",
  pendingObservation: "bg-blue-50 border-blue-200 text-blue-700",
  observed:           "bg-cyan-50 border-cyan-200 text-cyan-700",
  failed:             "bg-red-50 border-red-200 text-red-700",
  closed:             "bg-gray-50 border-gray-200 text-gray-600",
};

function OutcomeRealizationPanel({ summary, lang }: { summary: ExecutiveOutcomesSummary; lang: Language }) {
  const isAr = lang === "ar";

  if (summary.total === 0) {
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-io-border bg-io-bg/50">
          <h2 className="text-sm font-bold text-io-primary">
            {isAr ? "تحقق النتائج" : "Outcome Realization"}
          </h2>
        </div>
        <div className="px-5 py-6 text-center text-sm text-io-secondary">
          {isAr ? "لا توجد نتائج مسجّلة بعد" : "No outcomes recorded yet"}
        </div>
      </section>
    );
  }

  const tiles = [
    { key: "confirmed",          label: isAr ? "مؤكد"           : "Confirmed",         count: summary.confirmed          },
    { key: "observed",           label: isAr ? "ملاحَظ"          : "Observed",          count: summary.observed           },
    { key: "pendingObservation", label: isAr ? "قيد الانتظار"   : "Pending",           count: summary.pendingObservation },
    { key: "disputed",           label: isAr ? "متنازع عليه"    : "Disputed",          count: summary.disputed           },
    { key: "failed",             label: isAr ? "فاشل"           : "Failed",            count: summary.failed             },
    { key: "closed",             label: isAr ? "مغلق"           : "Closed",            count: summary.closed             },
  ] as const;

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-io-border bg-io-bg/50 flex items-center justify-between">
        <h2 className="text-sm font-bold text-io-primary">
          {isAr ? "تحقق النتائج" : "Outcome Realization"}
        </h2>
        <span className="text-xs text-io-secondary">
          {summary.total} {isAr ? "إجمالي النتائج" : "total outcomes"}
        </span>
      </div>
      <div className="px-5 py-4 space-y-4">
        {/* Status tiles */}
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {tiles.map(({ key, label, count }) => (
            <div
              key={key}
              className={`border rounded-lg px-3 py-2 text-center ${OUTCOME_STATUS_COLORS[key]}`}
            >
              <p className="text-xl font-bold tabular-nums">{count}</p>
              <p className="text-xs font-medium mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Most recent confirmed outcome */}
        {summary.mostRecentConfirmed && (
          <div className="border border-green-200 bg-green-50 rounded-lg px-4 py-3 text-xs">
            <p className="font-semibold text-green-800 mb-1">
              {isAr ? "آخر نتيجة مؤكدة" : "Most Recent Confirmed Outcome"}
            </p>
            <div className="flex flex-wrap gap-4 text-green-700">
              <span>
                {isAr ? "التصنيف: " : "Classification: "}
                <strong>{summary.mostRecentConfirmed.classLabel.replace(/_/g, " ")}</strong>
              </span>
              <span>
                {isAr ? "بواسطة: " : "By: "}
                <strong>{summary.mostRecentConfirmed.recordedBy}</strong>
              </span>
              <span className="font-mono text-green-600">
                {new Date(summary.mostRecentConfirmed.recordedAt).toISOString().replace("T", " ").slice(0, 16)}
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}


// ─── Main component ───────────────────────────────────────────────────────────

interface ExecutiveViewProps {
  result: RunResult;
  lang: Language;
}

export function ExecutiveView({ result, lang }: ExecutiveViewProps) {
  const outcomes          = useAppStore(selectOutcomes_EV);
  const decisionValues    = useAppStore(selectDecisionValues_EV);
  const operatorDecisions = useAppStore(selectOperatorDecisions_EV);
  const vm    = toExecutiveViewModel(result, outcomes, decisionValues);
  const tower = toControlTowerViewModel(operatorDecisions, outcomes, decisionValues);
  const isAr  = lang === "ar";

  return (
    <div className="max-w-6xl mx-auto px-6 lg:px-10 py-8 space-y-8">
      {/* Scenario header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-io-primary">
            {isAr && vm.scenarioLabelAr ? vm.scenarioLabelAr : vm.scenarioLabel}
          </h1>
          <p className="text-xs text-io-secondary mt-1 font-mono">Run {vm.runId}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-io-secondary uppercase tracking-wider font-medium">
            {isAr ? "الوضع الكلي" : "Overall Status"}
          </p>
          <Badge level={vm.kpis.overallClassification} />
        </div>
      </div>

      {/* KPI strip */}
      <KPIStrip kpis={vm.kpis} lang={lang} />

      {/* Sector cards */}
      <section>
        <h2 className="text-sm font-bold text-io-secondary uppercase tracking-wider mb-3">
          {isAr ? "ملخص القطاعات" : "Sector Summary"}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {vm.sectors.map((s) => (
            <SectorCard key={s.name} sector={s} lang={lang} />
          ))}
        </div>
      </section>

      {/* Priority actions */}
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-io-border flex items-center justify-between">
          <h2 className="text-sm font-bold text-io-primary">
            {isAr ? "الإجراءات ذات الأولوية" : "Priority Actions"}
          </h2>
          <span className="text-xs text-io-secondary">
            {isAr ? "أفضل 3 إجراءات بالقيمة والإلحاح" : "Top 3 by value × urgency"}
          </span>
        </div>
        <div className="px-5 py-4">
          <ActionTable actions={vm.topActions} lang={lang} />
        </div>
      </section>

      {/* Outcome realization */}
      <OutcomeRealizationPanel summary={vm.outcomesSummary} lang={lang} />

      {/* Executive Control Tower — Value Overview, Decision Narrative, Drivers, Risk */}
      <ExecutiveControlTower vm={tower} lang={lang} />

      {/* Narrative summary */}
      {vm.narrativeSummary && (
        <section className="bg-io-bg border border-io-border rounded-xl p-5">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-io-secondary mb-2">
            {isAr ? "ملخص تنفيذي" : "Executive Summary"}
          </h2>
          <p className="text-sm text-io-secondary leading-relaxed line-clamp-4">
            {vm.narrativeSummary}
          </p>
        </section>
      )}
    </div>
  );
}
