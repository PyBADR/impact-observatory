"use client";

/**
 * PilotPanel — Phase 6: Pilot Readiness & Operating Proof
 *
 * Four tabbed views:
 *   1. Overview — pilot mode, scope, decision count, divergence rate
 *   2. KPI — latency reduction, value created, false positives, accuracy
 *   3. Shadow — system vs human comparison per decision
 *   4. Report — findings, metrics, trends, recommendation
 */

import React, { useState } from "react";
import type { PilotPayload } from "@/types/observatory";

interface Props {
  pilot: PilotPayload | null | undefined;
}

type Tab = "overview" | "kpi" | "shadow" | "report";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Pilot Overview" },
  { key: "kpi", label: "KPI" },
  { key: "shadow", label: "Shadow Comparison" },
  { key: "report", label: "Report" },
];

export function PilotPanel({ pilot }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  if (!pilot) {
    return (
      <section className="px-6 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
          Pilot Readiness
        </h2>
        <p className="text-xs text-slate-500 py-3">
          No pilot data available. Run a scenario within pilot scope to generate pilot metrics.
        </p>
      </section>
    );
  }

  return (
    <section className="px-6 py-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
        Pilot Readiness & Operating Proof
      </h2>

      {/* Tab bar */}
      <div className="flex gap-1 mb-4 border-b border-slate-800">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              activeTab === t.key
                ? "text-emerald-400 border-b-2 border-emerald-400"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && <OverviewView pilot={pilot} />}
      {activeTab === "kpi" && <KPIView kpi={pilot.pilot_kpi} />}
      {activeTab === "shadow" && <ShadowView comparisons={pilot.shadow_comparisons} />}
      {activeTab === "report" && <ReportView report={pilot.pilot_report} failures={pilot.failure_modes} />}
    </section>
  );
}

// ── Sub-views ────────────────────────────────────────────────────────────

function OverviewView({ pilot }: { pilot: PilotPayload }) {
  const scope = pilot.pilot_scope;
  const kpi = pilot.pilot_kpi;
  const modeColor =
    scope.execution_mode === "SHADOW"
      ? "text-cyan-400 bg-cyan-400/10 border-cyan-400/20"
      : scope.execution_mode === "ADVISORY"
      ? "text-amber-400 bg-amber-400/10 border-amber-400/20"
      : "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";

  const scopeColor = scope.in_scope
    ? "text-emerald-400"
    : "text-red-400";

  return (
    <div className="space-y-3">
      {/* Mode + Scope strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Pilot Mode</p>
          <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded border ${modeColor}`}>
            {scope.execution_mode}
          </span>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Scope</p>
          <p className="text-sm font-medium text-white capitalize">{scope.scope_sector}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Decisions</p>
          <p className="text-sm font-semibold text-white">{kpi.total_decisions}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Divergence</p>
          <p className="text-sm font-semibold text-white">
            {(kpi.human_vs_system_delta * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Scope validation */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
        <p className={`text-xs ${scopeColor}`}>
          {scope.in_scope ? "IN SCOPE" : "OUT OF SCOPE"}: {scope.reason}
        </p>
        <p className="text-[10px] text-slate-600 mt-1">
          Owners: {scope.decision_owners.join(", ")} | Flow: {scope.approval_flow.join(" → ")}
        </p>
      </div>

      {/* Failure modes */}
      {pilot.failure_modes.length > 0 && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3">
          <p className="text-[10px] uppercase tracking-wider text-red-400 mb-1 font-semibold">
            Active Failure Modes ({pilot.failure_modes.length})
          </p>
          {pilot.failure_modes.map((fm) => (
            <div key={fm.id} className="flex items-start gap-2 py-1">
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                fm.severity === "CRITICAL" ? "bg-red-500/20 text-red-400" :
                fm.severity === "HIGH" ? "bg-orange-500/20 text-orange-400" :
                "bg-yellow-500/20 text-yellow-400"
              }`}>
                {fm.severity}
              </span>
              <div>
                <p className="text-xs text-slate-300">{fm.description}</p>
                <p className="text-[10px] text-slate-500">Fallback: {fm.fallback_action} | {fm.detail}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function KPIView({ kpi }: { kpi: PilotPayload["pilot_kpi"] }) {
  const kpis = [
    { label: "Latency Reduction", value: `${kpi.latency_reduction_pct.toFixed(0)}%`, color: "text-cyan-400" },
    { label: "Value Created", value: kpi.avoided_loss_estimate >= 1e6 ? `+$${(kpi.avoided_loss_estimate / 1e6).toFixed(1)}M` : `+$${kpi.avoided_loss_estimate.toFixed(0)}`, color: "text-emerald-400" },
    { label: "False Positive Rate", value: `${(kpi.false_positive_rate * 100).toFixed(1)}%`, color: kpi.false_positive_rate < 0.15 ? "text-emerald-400" : "text-amber-400" },
    { label: "Accuracy Rate", value: `${(kpi.accuracy_rate * 100).toFixed(0)}%`, color: kpi.accuracy_rate >= 0.8 ? "text-emerald-400" : "text-amber-400" },
    { label: "Decision Latency", value: `${kpi.decision_latency_hours.toFixed(1)}h faster`, color: "text-blue-400" },
    { label: "Matched Decisions", value: `${kpi.matched_count} / ${kpi.total_decisions}`, color: "text-slate-300" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {kpis.map((k) => (
        <div key={k.label} className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{k.label}</p>
          <p className={`text-lg font-semibold ${k.color}`}>{k.value}</p>
        </div>
      ))}
    </div>
  );
}

function ShadowView({ comparisons }: { comparisons: PilotPayload["shadow_comparisons"] }) {
  if (!comparisons || comparisons.length === 0) {
    return <p className="text-xs text-slate-500 py-3">No shadow comparisons available.</p>;
  }

  return (
    <div className="space-y-2">
      {comparisons.map((sc) => (
        <div
          key={sc.decision_id}
          className={`bg-slate-900/60 border rounded-lg p-3 ${
            sc.divergence ? "border-amber-500/30" : "border-slate-800"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-medium text-white">{sc.decision_id}</p>
            <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
              sc.divergence
                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
            }`}>
              {sc.divergence ? "DIVERGED" : "MATCHED"}
            </span>
          </div>
          {sc.divergence && sc.divergence_reason && (
            <p className="text-[10px] text-amber-300/80 mt-1">{sc.divergence_reason}</p>
          )}
          {sc.system_decision && (
            <p className="text-[10px] text-slate-500 mt-1">
              System: priority {((sc.system_decision as Record<string, number>).priority_score ?? 0).toFixed(2)},
              {" "}{(sc.system_decision as Record<string, number>).time_to_act_hours ?? 24}h
              {sc.human_decision && (
                <> | Human: priority {((sc.human_decision as Record<string, number>).priority_score ?? 0).toFixed(2)},
                {" "}{(sc.human_decision as Record<string, number>).time_to_act_hours ?? 24}h</>
              )}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function ReportView({ report, failures }: { report: PilotPayload["pilot_report"]; failures: PilotPayload["failure_modes"] }) {
  return (
    <div className="space-y-3">
      {/* Metrics strip */}
      <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
        {[
          { label: "Total Decisions", value: report.total_decisions },
          { label: "Matched", value: report.matched_decisions },
          { label: "Divergent", value: report.divergent_decisions },
          { label: "Accuracy", value: `${(report.accuracy_rate * 100).toFixed(0)}%` },
          { label: "Runs", value: report.run_count },
        ].map((m) => (
          <div key={m.label} className="bg-slate-900/60 border border-slate-800 rounded-lg p-2 text-center">
            <p className="text-[10px] text-slate-500">{m.label}</p>
            <p className="text-sm font-semibold text-white">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Key findings */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
        <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2 font-semibold">Key Findings</p>
        <div className="space-y-1.5">
          {report.key_findings.map((f, i) => (
            <p key={i} className="text-xs text-slate-300 flex items-start gap-2">
              <span className="text-emerald-400 mt-0.5 flex-shrink-0">-</span>
              {f}
            </p>
          ))}
        </div>
      </div>

      {/* Recommendation */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
        <p className="text-[10px] uppercase tracking-wider text-blue-400 mb-1 font-semibold">Recommendation</p>
        <p className="text-xs text-slate-300">{report.recommendation}</p>
      </div>

      {/* Failure mode catalog */}
      {failures.length === 0 && (
        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3">
          <p className="text-xs text-emerald-400">No failure modes triggered. System operating within bounds.</p>
        </div>
      )}
    </div>
  );
}
