"use client";

/**
 * Impact Observatory — Analyst View
 *
 * Persona: ANALYST
 * Priority order:
 *   1. Run metadata — IDs, timing, stages, audit hash, assumptions
 *   2. Score breakdown — all stress vectors per sector (6-factor table)
 *   3. Entity table — all financial entities sorted by loss
 *   4. Full decision actions — all actions, not just top 3
 *   5. Causal chain — 20-step propagation narrative
 *   6. Live signals — recent scored signals from WS
 *   7. Pending seeds — awaiting HITL review
 *   8. Operator decisions — full payload detail
 *
 * Not shown: executive KPI framing, sector summary cards, ROI framing.
 */

import React, { useState } from "react";
import type { RunResult, Language, DecisionAction, Outcome, OutcomeLifecycleStatus, DecisionValue, ValueClassification } from "@/types/observatory";
import { useAppStore } from "@/store/app-store";
import {
  toAnalystViewModel,
  classColor,
  type AnalystViewModel,
} from "@/lib/persona-view-model";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AppS_AV = ReturnType<typeof useAppStore.getState>;
const selectLiveSignals_AV       = (s: AppS_AV) => s.liveSignals;
const selectPendingSeeds_AV      = (s: AppS_AV) => s.pendingSeeds;
const selectOperatorDecisions_AV = (s: AppS_AV) => s.operatorDecisions;
const selectOutcomes_AV          = (s: AppS_AV) => s.outcomes;
const selectDecisionValues_AV    = (s: AppS_AV) => s.decisionValues;

// ─── Classification badge ────────────────────────────────────────────────────

function Badge({ level }: { level: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${classColor(level as never)}`}>
      {level}
    </span>
  );
}

// ─── Section wrapper ─────────────────────────────────────────────────────────

function Section({ title, children, mono }: { title: string; children: React.ReactNode; mono?: boolean }) {
  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-io-border bg-io-bg/50">
        <h2 className={`text-xs font-bold uppercase tracking-wider text-io-secondary ${mono ? "font-mono" : ""}`}>
          {title}
        </h2>
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

// ─── Run metadata ─────────────────────────────────────────────────────────────

function RunMetaPanel({ vm }: { vm: AnalystViewModel }) {
  const { runMeta } = vm;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-2 text-sm">
        {[
          ["Run ID", runMeta.runId],
          ["Template", runMeta.templateId],
          ["Scenario", runMeta.scenarioLabel],
          ["Severity", `${Math.round(runMeta.severity * 100)}%`],
          ["Horizon", `${runMeta.horizonHours}h`],
          ["Duration", `${runMeta.durationMs}ms`],
          ["Confidence", `${Math.round(runMeta.globalConfidence * 100)}%`],
        ].map(([k, v]) => (
          <div key={k} className="flex gap-3">
            <span className="w-28 flex-shrink-0 text-io-secondary">{k}</span>
            <span className="font-mono text-io-primary text-xs break-all">{v}</span>
          </div>
        ))}
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex gap-3">
          <span className="w-28 flex-shrink-0 text-io-secondary">Audit Hash</span>
          <span className="font-mono text-xs text-io-secondary break-all">{runMeta.auditHash}</span>
        </div>
        <div>
          <p className="text-io-secondary mb-1">Stages Completed ({runMeta.stagesCompleted.length})</p>
          <div className="flex flex-wrap gap-1">
            {runMeta.stagesCompleted.map((s) => (
              <span key={s} className="px-2 py-0.5 text-xs bg-green-50 border border-green-200 text-green-700 rounded font-mono">{s}</span>
            ))}
          </div>
        </div>
        {runMeta.assumptions.length > 0 && (
          <div>
            <p className="text-io-secondary mb-1">Assumptions</p>
            <ul className="space-y-0.5">
              {runMeta.assumptions.map((a, i) => (
                <li key={i} className="text-xs text-io-secondary flex gap-2">
                  <span className="text-io-accent">·</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Stage log ───────────────────────────────────────────────────────────────

function StageLog({ vm }: { vm: AnalystViewModel }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-io-border">
            {["Stage", "Status", "Duration (ms)", "Detail"].map((h) => (
              <th key={h} className="text-left py-2 pr-4 font-semibold text-io-secondary">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {vm.runMeta.stageLog.map((row) => (
            <tr key={row.stage} className="border-b border-io-border/40">
              <td className="py-1.5 pr-4 text-io-primary">{row.stage}</td>
              <td className="py-1.5 pr-4">
                <span className={`${row.status === "ok" ? "text-green-600" : "text-red-600"} font-semibold`}>
                  {row.status}
                </span>
              </td>
              <td className="py-1.5 pr-4 tabular-nums text-io-secondary">{row.durationMs}</td>
              <td className="py-1.5 text-io-secondary truncate max-w-xs">{row.detail ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Score breakdown ─────────────────────────────────────────────────────────

function ScoreBreakdown({ vm }: { vm: AnalystViewModel }) {
  const { scores } = vm;
  const sectors = [
    {
      name: "Banking",
      cls: scores.banking.classification,
      rows: [
        ["Liquidity Stress", scores.banking.liquidityStress],
        ["Credit Stress", scores.banking.creditStress],
        ["FX Stress", scores.banking.fxStress],
        ["Interbank Contagion", scores.banking.interbankContagion],
        ["Capital Adequacy Impact", scores.banking.capitalAdequacyImpact],
        ["Aggregate", scores.banking.aggregate],
        ["Institutions Affected", String(scores.banking.institutionCount)],
        ["Top Institution", scores.banking.topInstitution],
        ["Top Institution Stress", scores.banking.topInstitutionStress],
      ],
    },
    {
      name: "Insurance",
      cls: scores.insurance.classification,
      rows: [
        ["Claims Surge", scores.insurance.claimsSurge],
        ["Severity Index", scores.insurance.severityIndex],
        ["Loss Ratio", scores.insurance.lossRatio],
        ["Combined Ratio", scores.insurance.combinedRatio],
        ["Reinsurance Trigger", scores.insurance.reinsuranceTrigger ? "YES" : "NO"],
        ["IFRS-17 Adjustment", scores.insurance.ifrs17Adjustment],
        ["Aggregate", scores.insurance.aggregate],
        ["Lines Affected", String(scores.insurance.lineCount)],
      ],
    },
    {
      name: "Fintech",
      cls: scores.fintech.classification,
      rows: [
        ["Payment Volume Impact", scores.fintech.paymentVolumeImpact],
        ["Settlement Delay", scores.fintech.settlementDelayHours],
        ["API Availability", scores.fintech.apiAvailability],
        ["Cross-Border Disruption", scores.fintech.crossBorderDisruption],
        ["Aggregate", scores.fintech.aggregate],
        ["Platforms Affected", String(scores.fintech.platformCount)],
      ],
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {sectors.map((sector) => (
        <div key={sector.name}>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-bold uppercase tracking-wider text-io-primary">{sector.name}</p>
            <Badge level={sector.cls} />
          </div>
          <table className="w-full text-xs">
            <tbody>
              {sector.rows.map(([k, v]) => (
                <tr key={k} className="border-b border-io-border/30">
                  <td className="py-1 pr-2 text-io-secondary">{k}</td>
                  <td className={`py-1 text-right font-mono font-semibold ${
                    v === "YES" ? "text-orange-600" :
                    v === "NO" ? "text-green-600" : "text-io-primary"
                  }`}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

// ─── Entity table ─────────────────────────────────────────────────────────────

function EntityTable({ vm }: { vm: AnalystViewModel }) {
  const [showAll, setShowAll] = useState(false);
  const rows = showAll ? vm.entities : vm.entities.slice(0, 10);

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-io-border">
              {["Entity", "Sector", "Loss", "Stress", "Peak Day", "Recovery", "Level", "Confidence"].map((h) => (
                <th key={h} className={`py-2 ${h === "Loss" || h === "Stress" || h === "Peak Day" || h === "Recovery" || h === "Confidence" ? "text-right" : "text-left"} pr-3 font-semibold text-io-secondary uppercase tracking-wider`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.entityId} className="border-b border-io-border/40 hover:bg-io-bg/50 transition-colors">
                <td className="py-1.5 pr-3 font-medium text-io-primary">{e.label}</td>
                <td className="py-1.5 pr-3 capitalize text-io-secondary">{e.sector}</td>
                <td className="py-1.5 pr-3 text-right font-mono text-io-danger font-semibold">{e.lossFormatted}</td>
                <td className="py-1.5 pr-3 text-right font-mono text-io-primary">{e.stressLabel}</td>
                <td className="py-1.5 pr-3 text-right text-io-secondary">{e.peakDay}</td>
                <td className="py-1.5 pr-3 text-right text-io-secondary">{e.recoveryDays}d</td>
                <td className="py-1.5 pr-3"><Badge level={e.classification} /></td>
                <td className="py-1.5 text-right text-io-secondary">{e.confidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {vm.entities.length > 10 && (
        <button
          onClick={() => setShowAll((v) => !v)}
          className="mt-3 text-xs text-io-accent hover:underline"
        >
          {showAll ? `Show top 10` : `Show all ${vm.entities.length} entities`}
        </button>
      )}
    </>
  );
}

// ─── Causal chain ────────────────────────────────────────────────────────────

function CausalChain({ vm, lang }: { vm: AnalystViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const chain = vm.causalChain;
  if (chain.length === 0) return <p className="text-xs text-io-secondary">No causal chain available.</p>;

  return (
    <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
      {chain.map((step) => (
        <div key={step.step} className="flex gap-3 text-xs">
          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-io-accent/10 border border-io-accent/20 flex items-center justify-center text-io-accent font-bold">
            {step.step}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-io-primary">
                {(isAr && step.entity_label_ar) ? step.entity_label_ar : step.entity_label}
              </span>
              <span className="text-io-secondary">→</span>
              <span className="text-io-secondary">
                {(isAr && step.event_ar) ? step.event_ar : step.event}
              </span>
            </div>
            <div className="flex gap-4 mt-0.5 text-io-secondary">
              <span>Loss: <span className="text-io-danger font-mono">${(step.impact_usd / 1e6).toFixed(0)}M</span></span>
              <span>Stress Δ: <span className="font-mono">{(step.stress_delta * 100).toFixed(1)}%</span></span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── All decisions table ─────────────────────────────────────────────────────

function DecisionsTable({ decisions, lang }: { decisions: DecisionAction[]; lang: Language }) {
  const isAr = lang === "ar";
  if (decisions.length === 0) return <p className="text-xs text-io-secondary">No decisions.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border">
            {["#", "Action", "Sector", "Owner", "Urgency", "Value", "Reg Risk", "Loss Avoided", "Cost", "Time to Act", "Confidence"].map((h) => (
              <th key={h} className="text-left py-2 pr-3 font-semibold text-io-secondary uppercase tracking-wider whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {decisions.map((a, i) => (
            <tr key={a.id} className="border-b border-io-border/40 hover:bg-io-bg/50">
              <td className="py-1.5 pr-3 text-io-secondary font-bold">{i + 1}</td>
              <td className="py-1.5 pr-3 text-io-primary font-medium max-w-xs">
                {(isAr && a.action_ar) ? a.action_ar : a.action}
              </td>
              <td className="py-1.5 pr-3 capitalize text-io-secondary">{a.sector}</td>
              <td className="py-1.5 pr-3 text-io-secondary">{a.owner}</td>
              <td className="py-1.5 pr-3 font-mono">{a.urgency.toFixed(2)}</td>
              <td className="py-1.5 pr-3 font-mono">{a.value.toFixed(2)}</td>
              <td className="py-1.5 pr-3 font-mono">{a.regulatory_risk.toFixed(2)}</td>
              <td className="py-1.5 pr-3 font-mono text-green-700">${(a.loss_avoided_usd / 1e6).toFixed(0)}M</td>
              <td className="py-1.5 pr-3 font-mono">${(a.cost_usd / 1e6).toFixed(0)}M</td>
              <td className="py-1.5 pr-3 font-mono">{Math.round(a.time_to_act_hours)}h</td>
              <td className="py-1.5 font-mono">{(a.confidence * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Live signals ─────────────────────────────────────────────────────────────

function LiveSignalsList({ vm }: { vm: AnalystViewModel }) {
  const signals = vm.liveSignals.slice(0, 8);
  if (signals.length === 0) return <p className="text-xs text-io-secondary">No live signals captured.</p>;

  return (
    <div className="space-y-2">
      {signals.map((s) => (
        <div key={s.signal_id} className="flex items-center justify-between text-xs border-b border-io-border/40 pb-1.5">
          <div>
            <span className="font-mono text-io-secondary">{s.signal_id.slice(0, 12)}…</span>
            <span className="ml-2 capitalize text-io-primary font-medium">{s.event_type}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-io-secondary capitalize">{s.sector}</span>
            <span className="font-mono font-semibold text-io-primary">
              {(s.signal_score * 100).toFixed(0)}%
            </span>
            <span className="text-io-secondary">{s.source}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Pending seeds ────────────────────────────────────────────────────────────

function PendingSeedsList({ vm }: { vm: AnalystViewModel }) {
  const seeds = vm.pendingSeeds;
  if (seeds.length === 0) return <p className="text-xs text-io-secondary">No pending seeds.</p>;

  return (
    <div className="space-y-2">
      {seeds.map((s) => (
        <div key={s.seed_id} className="border border-io-border rounded-lg p-3 text-xs">
          <div className="flex justify-between items-start mb-1">
            <span className="font-mono text-io-secondary">{s.seed_id.slice(0, 12)}…</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
              s.status === "PENDING_REVIEW" ? "bg-yellow-100 text-yellow-800" :
              s.status === "APPROVED" ? "bg-green-100 text-green-800" :
              "bg-gray-100 text-gray-600"
            }`}>{s.status}</span>
          </div>
          <p className="text-io-primary font-medium">{s.suggested_template_id}</p>
          <p className="text-io-secondary mt-0.5">
            Severity {Math.round(s.suggested_severity * 100)}% · {s.suggested_horizon_hours}h · {s.sector}
          </p>
          <p className="text-io-secondary mt-1 italic">{s.rationale}</p>
        </div>
      ))}
    </div>
  );
}

// ─── Operator decisions (full payload) ──────────────────────────────────────

function OperatorDecisionsList({ vm }: { vm: AnalystViewModel }) {
  const decisions = vm.operatorDecisions.slice(0, 5);
  if (decisions.length === 0) return <p className="text-xs text-io-secondary">No operator decisions.</p>;

  return (
    <div className="space-y-3">
      {decisions.map((d) => (
        <div key={d.decision_id} className="border border-io-border rounded-lg p-3 text-xs">
          <div className="flex justify-between items-start mb-1.5">
            <div>
              <span className="font-mono text-io-secondary">{d.decision_id.slice(0, 12)}…</span>
              <span className="ml-2 font-semibold text-io-primary">{d.decision_type}</span>
            </div>
            <span className={`px-2 py-0.5 rounded font-semibold ${
              d.decision_status === "EXECUTED" ? "bg-green-100 text-green-800" :
              d.decision_status === "FAILED" ? "bg-red-100 text-red-800" :
              d.decision_status === "CLOSED" ? "bg-gray-100 text-gray-600" :
              "bg-blue-100 text-blue-800"
            }`}>{d.decision_status}</span>
          </div>
          {d.rationale && <p className="text-io-secondary italic mb-1">{d.rationale}</p>}
          <div className="flex flex-wrap gap-2 text-io-secondary">
            {d.source_signal_id && <span>SIG: <code className="font-mono">{d.source_signal_id.slice(0, 8)}</code></span>}
            {d.source_seed_id && <span>SEED: <code className="font-mono">{d.source_seed_id.slice(0, 8)}</code></span>}
            {d.source_run_id && <span>RUN: <code className="font-mono">{d.source_run_id.slice(0, 8)}</code></span>}
            <span>by <strong>{d.created_by}</strong></span>
          </div>
          {Object.keys(d.decision_payload ?? {}).length > 0 && (
            <details className="mt-1.5">
              <summary className="cursor-pointer text-io-accent">Payload</summary>
              <pre className="mt-1 text-xs bg-io-bg p-2 rounded overflow-x-auto text-io-secondary">
                {JSON.stringify(d.decision_payload, null, 2)}
              </pre>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Outcome detail table ────────────────────────────────────────────────────

const OUTCOME_LIFECYCLE_COLORS: Record<OutcomeLifecycleStatus, string> = {
  PENDING_OBSERVATION: "bg-blue-50 text-blue-700 border-blue-200",
  OBSERVED:            "bg-cyan-50 text-cyan-700 border-cyan-200",
  CONFIRMED:           "bg-green-50 text-green-700 border-green-200",
  DISPUTED:            "bg-orange-50 text-orange-700 border-orange-200",
  FAILED:              "bg-red-50 text-red-700 border-red-200",
  CLOSED:              "bg-gray-50 text-gray-600 border-gray-200",
};

function OutcomeDetailTable({ outcomes }: { outcomes: Outcome[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (outcomes.length === 0) {
    return <p className="text-xs text-io-secondary">No outcomes recorded.</p>;
  }

  const fmt = (iso: string | null) =>
    iso ? new Date(iso).toISOString().replace("T", " ").slice(0, 19) : "—";

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border">
            {[
              "Outcome ID", "Status", "Classification", "Recorded By",
              "Recorded At", "Observed At", "TTR (s)", "Error", "Evidence Keys",
            ].map((h) => (
              <th key={h} className="text-left py-2 pr-3 font-semibold text-io-secondary uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {outcomes.map((o) => (
            <React.Fragment key={o.outcome_id}>
              <tr
                className="border-b border-io-border/40 hover:bg-io-bg/50 cursor-pointer"
                onClick={() => setExpanded(expanded === o.outcome_id ? null : o.outcome_id)}
              >
                <td className="py-1.5 pr-3 font-mono text-io-secondary">
                  {o.outcome_id.slice(0, 12)}…
                </td>
                <td className="py-1.5 pr-3">
                  <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${OUTCOME_LIFECYCLE_COLORS[o.outcome_status]}`}>
                    {o.outcome_status.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="py-1.5 pr-3 text-io-primary">
                  {o.outcome_classification
                    ? o.outcome_classification.replace(/_/g, " ")
                    : <span className="text-io-secondary">—</span>}
                </td>
                <td className="py-1.5 pr-3 font-semibold text-io-primary">{o.recorded_by}</td>
                <td className="py-1.5 pr-3 font-mono text-io-secondary whitespace-nowrap">{fmt(o.recorded_at)}</td>
                <td className="py-1.5 pr-3 font-mono text-io-secondary whitespace-nowrap">{fmt(o.observed_at)}</td>
                <td className="py-1.5 pr-3 font-mono text-io-primary">
                  {o.time_to_resolution_seconds != null ? o.time_to_resolution_seconds : "—"}
                </td>
                <td className="py-1.5 pr-3">
                  {o.error_flag
                    ? <span className="text-red-600 font-bold">YES</span>
                    : <span className="text-green-600">—</span>}
                </td>
                <td className="py-1.5 font-mono text-io-secondary">
                  {Object.keys(o.evidence_payload ?? {}).length}
                </td>
              </tr>
              {expanded === o.outcome_id && (
                <tr className="bg-io-bg/80">
                  <td colSpan={9} className="px-4 py-3">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Linkage</p>
                        <div className="space-y-0.5">
                          <p>Decision: <code className="font-mono">{o.source_decision_id ?? "—"}</code></p>
                          <p>Run: <code className="font-mono">{o.source_run_id ?? "—"}</code></p>
                          <p>Signal: <code className="font-mono">{o.source_signal_id ?? "—"}</code></p>
                          <p>Seed: <code className="font-mono">{o.source_seed_id ?? "—"}</code></p>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Values</p>
                        <div className="space-y-0.5">
                          <p>Expected: <span className="font-mono">{o.expected_value ?? "—"}</span></p>
                          <p>Realized: <span className="font-mono">{o.realized_value ?? "—"}</span></p>
                          <p>Closed at: <span className="font-mono">{fmt(o.closed_at)}</span></p>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Evidence Payload</p>
                        {Object.keys(o.evidence_payload ?? {}).length > 0 ? (
                          <pre className="text-io-secondary bg-io-surface border border-io-border rounded p-2 overflow-x-auto max-h-32">
                            {JSON.stringify(o.evidence_payload, null, 2)}
                          </pre>
                        ) : (
                          <p className="text-io-secondary italic">No evidence recorded</p>
                        )}
                        {o.notes && (
                          <p className="mt-2 italic text-io-secondary">{o.notes}</p>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Value detail table (forensic ROI view) ──────────────────────────────────

const VALUE_CLASS_BADGE: Record<ValueClassification, string> = {
  HIGH_VALUE:     "bg-emerald-100 text-emerald-800",
  POSITIVE_VALUE: "bg-green-100 text-green-700",
  NEUTRAL:        "bg-gray-100 text-gray-600",
  NEGATIVE_VALUE: "bg-orange-100 text-orange-700",
  LOSS_INDUCING:  "bg-red-100 text-red-700",
};

function ValueDetailTable({ values }: { values: DecisionValue[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (values.length === 0) {
    return <p className="text-sm text-io-secondary text-center py-4">No values computed yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border text-io-secondary">
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Value ID</th>
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Classification</th>
            <th className="text-right py-2 pr-3 font-semibold uppercase tracking-wider">Net Value</th>
            <th className="text-right py-2 pr-3 font-semibold uppercase tracking-wider">Avoided Loss</th>
            <th className="text-right py-2 pr-3 font-semibold uppercase tracking-wider">Total Cost</th>
            <th className="text-right py-2 pr-3 font-semibold uppercase tracking-wider">Confidence</th>
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Computed By</th>
            <th className="text-left py-2 font-semibold uppercase tracking-wider">Computed At</th>
          </tr>
        </thead>
        <tbody>
          {values.map((v) => (
            <React.Fragment key={v.value_id}>
              <tr
                className="border-b border-io-border/50 hover:bg-io-bg/50 cursor-pointer transition-colors"
                onClick={() => setExpanded(expanded === v.value_id ? null : v.value_id)}
              >
                <td className="py-2 pr-3 font-mono text-io-secondary">{v.value_id.slice(0, 14)}</td>
                <td className="py-2 pr-3">
                  <span className={`px-2 py-0.5 rounded-full font-semibold ${VALUE_CLASS_BADGE[v.value_classification]}`}>
                    {v.value_classification.replace(/_/g, " ")}
                  </span>
                </td>
                <td className={`py-2 pr-3 text-right font-bold tabular-nums ${v.net_value >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                  {v.net_value >= 0 ? "+" : ""}{v.net_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </td>
                <td className="py-2 pr-3 text-right tabular-nums text-io-secondary">
                  {v.avoided_loss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </td>
                <td className="py-2 pr-3 text-right tabular-nums text-io-secondary">
                  {v.total_cost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  {Math.round(v.value_confidence_score * 100)}%
                </td>
                <td className="py-2 pr-3 text-io-primary">{v.computed_by}</td>
                <td className="py-2 font-mono text-io-secondary">
                  {new Date(v.computed_at).toISOString().replace("T", " ").slice(0, 16)}
                </td>
              </tr>
              {expanded === v.value_id && (
                <tr className="bg-io-bg/80 border-b border-io-border">
                  <td colSpan={8} className="py-3 px-3">
                    <div className="grid grid-cols-3 gap-4 text-xs">
                      {/* Linkage */}
                      <div className="space-y-1">
                        <p className="font-semibold text-io-secondary uppercase tracking-wider mb-1">Linkage</p>
                        <p><span className="text-io-secondary">Outcome: </span><span className="font-mono">{v.source_outcome_id}</span></p>
                        <p><span className="text-io-secondary">Decision: </span><span className="font-mono">{v.source_decision_id ?? "—"}</span></p>
                        <p><span className="text-io-secondary">Run: </span><span className="font-mono">{v.source_run_id ?? "—"}</span></p>
                      </div>
                      {/* Cost breakdown */}
                      <div className="space-y-1">
                        <p className="font-semibold text-io-secondary uppercase tracking-wider mb-1">Cost Breakdown</p>
                        <p><span className="text-io-secondary">Operational: </span>{v.operational_cost.toLocaleString()}</p>
                        <p><span className="text-io-secondary">Decision: </span>{v.decision_cost.toLocaleString()}</p>
                        <p><span className="text-io-secondary">Latency: </span>{v.latency_cost.toLocaleString()}</p>
                        <p><span className="text-io-secondary">Expected value: </span>{v.expected_value ?? "—"}</p>
                        <p><span className="text-io-secondary">Realized value: </span>{v.realized_value ?? "—"}</p>
                      </div>
                      {/* Calculation trace */}
                      <div>
                        <p className="font-semibold text-io-secondary uppercase tracking-wider mb-1">Calculation Trace</p>
                        <pre className="text-io-secondary bg-io-surface border border-io-border rounded p-2 overflow-auto max-h-40 text-[10px]">
                          {JSON.stringify(v.calculation_trace, null, 2)}
                        </pre>
                      </div>
                    </div>
                    {v.notes && (
                      <p className="mt-2 text-xs text-io-secondary italic border-t border-io-border pt-2">
                        Notes: {v.notes}
                      </p>
                    )}
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

interface AnalystViewProps {
  result: RunResult;
  lang: Language;
}

export function AnalystView({ result, lang }: AnalystViewProps) {
  const liveSignals       = useAppStore(selectLiveSignals_AV);
  const pendingSeeds      = useAppStore(selectPendingSeeds_AV);
  const operatorDecisions = useAppStore(selectOperatorDecisions_AV);
  const outcomes          = useAppStore(selectOutcomes_AV);
  const decisionValues    = useAppStore(selectDecisionValues_AV);

  const vm = toAnalystViewModel(result, liveSignals, pendingSeeds, operatorDecisions, outcomes, decisionValues);
  const isAr = lang === "ar";

  return (
    <div className="max-w-6xl mx-auto px-6 lg:px-10 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-io-primary">
          {isAr ? "محطة عمل المحلل" : "Analyst Workbench"}
        </h1>
        <p className="text-xs text-io-secondary font-mono mt-1">{vm.runMeta.runId}</p>
      </div>

      {/* Run meta */}
      <Section title="Run Metadata & Inputs">
        <RunMetaPanel vm={vm} />
      </Section>

      {/* Stage log */}
      {vm.runMeta.stageLog.length > 0 && (
        <Section title="Pipeline Stage Log" mono>
          <StageLog vm={vm} />
        </Section>
      )}

      {/* Score breakdown */}
      <Section title="Score Breakdown — All Stress Vectors">
        <ScoreBreakdown vm={vm} />
      </Section>

      {/* Entity table */}
      <Section title={`Financial Impact — All ${vm.entities.length} Entities`}>
        <EntityTable vm={vm} />
      </Section>

      {/* Causal chain */}
      <Section title="Causal Propagation Chain">
        <div className="mb-3 text-xs text-io-secondary border-b border-io-border pb-2">
          {isAr ? vm.narrativeAr : vm.narrativeEn}
        </div>
        <CausalChain vm={vm} lang={lang} />
      </Section>

      {/* All decisions */}
      <Section title={`Decision Actions — All ${vm.allDecisions.length}`}>
        <DecisionsTable decisions={vm.allDecisions} lang={lang} />
      </Section>

      {/* Live layer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title={`Live Signals (${vm.liveSignals.length})`}>
          <LiveSignalsList vm={vm} />
        </Section>
        <Section title={`Pending Seeds (${vm.pendingSeeds.length})`}>
          <PendingSeedsList vm={vm} />
        </Section>
      </div>

      {/* Operator decisions */}
      <Section title={`Operator Decisions (${vm.operatorDecisions.length})`}>
        <OperatorDecisionsList vm={vm} />
      </Section>

      {/* Outcome intelligence — full detail view */}
      <Section title={`Outcome Intelligence — ${vm.outcomes.length} Record${vm.outcomes.length !== 1 ? "s" : ""}`}>
        <OutcomeDetailTable outcomes={vm.outcomes} />
      </Section>

      {/* Decision value / ROI layer — forensic detail with calculation trace */}
      <Section title={`Decision ROI — ${vm.values.length} Computed Value${vm.values.length !== 1 ? "s" : ""}`}>
        <ValueDetailTable values={vm.values} />
      </Section>
    </div>
  );
}
