"use client";

/**
 * Impact Observatory — Regulator View
 *
 * Persona: REGULATOR
 * Priority order:
 *   1. Run identity + audit hash — provenance header
 *   2. Decision lineage table — full operator decision lifecycle with actor/timestamp
 *   3. Signal trace — most recent signals ingested by the system
 *   4. Pipeline accountability — stage-by-stage execution record
 *   5. Regulatory events — breach levels and mandatory actions
 *   6. Pending seeds — what awaits HITL review (HITL accountability)
 *
 * Not shown: loss KPIs, sector stress, executive framing, score mechanics.
 * All tables are timestamp-ordered and actor-attributed.
 */

import React, { useState } from "react";
import type { RunResult, Language } from "@/types/observatory";
import { useAppStore } from "@/store/app-store";
import {
  toRegulatorViewModel,
  statusBadgeColor,
  type RegulatorViewModel,
  type RegulatorDecisionRow,
  type RegulatorOutcomeRow,
  type RegulatorValueRow,
} from "@/lib/persona-view-model";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AppS_RV = ReturnType<typeof useAppStore.getState>;
const selectOperatorDecisions_RV = (s: AppS_RV) => s.operatorDecisions;
const selectLiveSignals_RV       = (s: AppS_RV) => s.liveSignals;
const selectPendingSeeds_RV      = (s: AppS_RV) => s.pendingSeeds;
const selectOutcomes_RV          = (s: AppS_RV) => s.outcomes;
const selectDecisionValues_RV    = (s: AppS_RV) => s.decisionValues;

// ─── Section wrapper ─────────────────────────────────────────────────────────

function Section({ title, subtitle, children }: {
  title: string; subtitle?: string; children: React.ReactNode;
}) {
  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-io-border bg-io-bg/50">
        <div className="flex items-baseline justify-between gap-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-io-secondary">{title}</h2>
          {subtitle && <span className="text-xs text-io-secondary">{subtitle}</span>}
        </div>
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

// ─── Audit header ─────────────────────────────────────────────────────────────

function AuditHeader({ vm }: { vm: RegulatorViewModel }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[
        { label: "Run ID", value: vm.runId, mono: true },
        { label: "Scenario", value: vm.scenarioLabel, mono: false },
        { label: "Confidence", value: vm.globalConfidence, mono: true },
        { label: "Duration", value: `${vm.durationMs}ms`, mono: true },
        { label: "Stages Completed", value: String(vm.stagesCompleted.length), mono: true },
        { label: "Audit Hash", value: vm.auditHash, mono: true, truncate: true },
      ].map(({ label, value, mono, truncate }) => (
        <div key={label} className="bg-io-bg border border-io-border rounded-lg px-4 py-3">
          <p className="text-xs uppercase tracking-wider text-io-secondary mb-1">{label}</p>
          <p className={`text-sm font-semibold text-io-primary ${mono ? "font-mono" : ""} ${truncate ? "truncate" : ""}`}>
            {value}
          </p>
        </div>
      ))}
    </div>
  );
}

// ─── Decision lineage table ───────────────────────────────────────────────────

function DecisionLineageTable({
  decisions, lang,
}: { decisions: RegulatorDecisionRow[]; lang: Language }) {
  const isAr = lang === "ar";
  const [expanded, setExpanded] = useState<string | null>(null);

  if (decisions.length === 0) {
    return (
      <p className="text-xs text-io-secondary py-4 text-center">
        {isAr ? "لا توجد قرارات مسجّلة" : "No operator decisions recorded"}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border">
            {[
              "Decision ID",
              "Type",
              "Status",
              "Outcome",
              "Created By",
              "Created At",
              "Updated At",
              "Closed At",
              "Lineage",
            ].map((h) => (
              <th key={h} className="text-left py-2 pr-3 font-semibold text-io-secondary uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {decisions.map((d) => (
            <React.Fragment key={d.decisionId}>
              <tr
                className="border-b border-io-border/40 hover:bg-io-bg/50 cursor-pointer"
                onClick={() => setExpanded(expanded === d.decisionId ? null : d.decisionId)}
              >
                <td className="py-2 pr-3 font-mono text-io-secondary">
                  {d.decisionId.slice(0, 12)}…
                </td>
                <td className="py-2 pr-3">
                  <span className="px-1.5 py-0.5 bg-io-bg border border-io-border rounded text-io-primary font-semibold">
                    {d.decisionType}
                  </span>
                </td>
                <td className="py-2 pr-3">
                  <span className={`px-2 py-0.5 rounded font-semibold ${statusBadgeColor(d.status)}`}>
                    {d.status}
                  </span>
                </td>
                <td className="py-2 pr-3">
                  <span className={`px-2 py-0.5 rounded font-semibold ${
                    d.outcomeStatus === "SUCCESS" ? "bg-green-100 text-green-800" :
                    d.outcomeStatus === "FAILURE" ? "bg-red-100 text-red-800" :
                    d.outcomeStatus === "PARTIAL" ? "bg-yellow-100 text-yellow-800" :
                    "bg-gray-100 text-gray-600"
                  }`}>{d.outcomeStatus}</span>
                </td>
                <td className="py-2 pr-3 font-semibold text-io-primary">{d.createdBy}</td>
                <td className="py-2 pr-3 font-mono text-io-secondary whitespace-nowrap">
                  {new Date(d.createdAt).toISOString().replace("T", " ").slice(0, 19)}
                </td>
                <td className="py-2 pr-3 font-mono text-io-secondary whitespace-nowrap">
                  {new Date(d.updatedAt).toISOString().replace("T", " ").slice(0, 19)}
                </td>
                <td className="py-2 pr-3 font-mono text-io-secondary whitespace-nowrap">
                  {d.closedAt
                    ? new Date(d.closedAt).toISOString().replace("T", " ").slice(0, 19)
                    : "—"}
                </td>
                <td className="py-2 font-mono text-io-accent">{d.linkedEntities}</td>
              </tr>
              {expanded === d.decisionId && (
                <tr className="bg-io-bg/80">
                  <td colSpan={9} className="px-4 py-3">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Rationale</p>
                        <p className="text-io-primary italic">{d.rationale ?? "—"}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Source Linkage</p>
                        <div className="space-y-0.5">
                          <p>Signal: <code className="font-mono">{d.sourceSignalId ?? "—"}</code></p>
                          <p>Seed:   <code className="font-mono">{d.sourceSeedId ?? "—"}</code></p>
                          <p>Run:    <code className="font-mono">{d.sourceRunId ?? "—"}</code></p>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Outcome Detail</p>
                        <pre className="text-io-secondary bg-io-surface border border-io-border rounded p-2 overflow-x-auto">
                          {d.outcomeDetail}
                        </pre>
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

// ─── Signal trace ────────────────────────────────────────────────────────────

function SignalTraceTable({ vm }: { vm: RegulatorViewModel }) {
  if (vm.signalTrace.length === 0) {
    return <p className="text-xs text-io-secondary">No signals in the live stream.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border">
            {["Signal ID", "Sector", "Event Type", "Score", "Source", "Scored At"].map((h) => (
              <th key={h} className="text-left py-2 pr-3 font-semibold text-io-secondary uppercase tracking-wider whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {vm.signalTrace.map((s) => (
            <tr key={s.signalId} className="border-b border-io-border/40 hover:bg-io-bg/50">
              <td className="py-1.5 pr-3 font-mono text-io-secondary">{s.signalId.slice(0, 16)}…</td>
              <td className="py-1.5 pr-3 capitalize text-io-primary">{s.sector}</td>
              <td className="py-1.5 pr-3 text-io-primary">{s.eventType}</td>
              <td className="py-1.5 pr-3 font-mono font-semibold text-io-primary">
                {(s.score * 100).toFixed(0)}%
              </td>
              <td className="py-1.5 pr-3 capitalize text-io-secondary">{s.source}</td>
              <td className="py-1.5 font-mono text-io-secondary whitespace-nowrap">
                {s.scoredAt ? new Date(s.scoredAt).toISOString().replace("T", " ").slice(0, 19) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Pipeline accountability ─────────────────────────────────────────────────

function PipelineRecord({ vm }: { vm: RegulatorViewModel }) {
  if (vm.pipelineRecord.length === 0) {
    return <p className="text-xs text-io-secondary">No stage log available.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-io-border">
            {["Stage", "Status", "Duration (ms)", "Detail"].map((h) => (
              <th key={h} className="text-left py-2 pr-4 font-semibold text-io-secondary uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {vm.pipelineRecord.map((row) => (
            <tr key={row.stage} className="border-b border-io-border/40">
              <td className="py-1.5 pr-4 text-io-primary">{row.stage}</td>
              <td className="py-1.5 pr-4">
                <span className={row.status === "ok" ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
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

// ─── Regulatory events ───────────────────────────────────────────────────────

const BREACH_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  major:    "bg-orange-100 text-orange-800 border-orange-200",
  minor:    "bg-yellow-100 text-yellow-800 border-yellow-200",
  none:     "bg-gray-100 text-gray-600 border-gray-200",
};

function RegulatoryEvents({ vm, lang }: { vm: RegulatorViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const events = vm.regulatoryEvents.filter((e) => e.breachLevel !== "none");
  if (events.length === 0) {
    return (
      <p className="text-xs text-io-secondary">
        {isAr ? "لا توجد خروقات تنظيمية مُكتشفة" : "No regulatory breaches detected"}
      </p>
    );
  }
  return (
    <div className="space-y-2">
      {events.map((e, i) => (
        <div key={i} className={`border rounded-lg px-4 py-3 ${BREACH_COLORS[e.breachLevel] ?? BREACH_COLORS.minor}`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold uppercase">{e.breachLevel} breach</span>
            <span className="text-xs font-mono">T+{e.timestep} · {e.sector}</span>
          </div>
          {e.mandatoryActions.length > 0 && (
            <ul className="space-y-0.5 mt-1">
              {e.mandatoryActions.map((a, j) => (
                <li key={j} className="text-xs flex gap-1.5">
                  <span>▸</span><span>{a}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Pending seeds (HITL accountability) ─────────────────────────────────────

function PendingSeedsAudit({ vm }: { vm: RegulatorViewModel }) {
  if (vm.pendingSeeds.length === 0) {
    return <p className="text-xs text-io-secondary">No seeds pending review.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border">
            {["Seed ID", "Signal ID", "Status", "Sector", "Template", "Severity", "Reviewed By", "Created At"].map((h) => (
              <th key={h} className="text-left py-2 pr-3 font-semibold text-io-secondary uppercase tracking-wider whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {vm.pendingSeeds.map((s) => (
            <tr key={s.seed_id} className="border-b border-io-border/40 hover:bg-io-bg/50">
              <td className="py-1.5 pr-3 font-mono text-io-secondary">{s.seed_id.slice(0, 12)}…</td>
              <td className="py-1.5 pr-3 font-mono text-io-secondary">{s.signal_id.slice(0, 12)}…</td>
              <td className="py-1.5 pr-3">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  s.status === "PENDING_REVIEW" ? "bg-yellow-100 text-yellow-800" :
                  s.status === "APPROVED" ? "bg-green-100 text-green-800" :
                  s.status === "REJECTED" ? "bg-red-100 text-red-800" :
                  "bg-gray-100 text-gray-600"
                }`}>{s.status}</span>
              </td>
              <td className="py-1.5 pr-3 capitalize text-io-primary">{s.sector}</td>
              <td className="py-1.5 pr-3 font-mono text-io-secondary text-xs">{s.suggested_template_id}</td>
              <td className="py-1.5 pr-3 font-mono text-io-primary">{Math.round(s.suggested_severity * 100)}%</td>
              <td className="py-1.5 pr-3 text-io-secondary">{s.reviewed_by ?? "—"}</td>
              <td className="py-1.5 font-mono text-io-secondary whitespace-nowrap">
                {new Date(s.created_at).toISOString().replace("T", " ").slice(0, 19)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Outcome audit table ─────────────────────────────────────────────────────

const OUTCOME_AUDIT_STATUS_COLORS: Record<string, string> = {
  PENDING_OBSERVATION: "bg-blue-100 text-blue-700",
  OBSERVED:            "bg-cyan-100 text-cyan-700",
  CONFIRMED:           "bg-green-100 text-green-700",
  DISPUTED:            "bg-orange-100 text-orange-700",
  FAILED:              "bg-red-100 text-red-700",
  CLOSED:              "bg-gray-100 text-gray-500",
};

function OutcomeAuditTable({ rows, lang }: { rows: RegulatorOutcomeRow[]; lang: Language }) {
  const isAr = lang === "ar";
  const [expanded, setExpanded] = useState<string | null>(null);

  if (rows.length === 0) {
    return (
      <p className="text-xs text-io-secondary py-4 text-center">
        {isAr ? "لا توجد نتائج مسجّلة" : "No outcomes recorded"}
      </p>
    );
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
              "Recorded At", "Observed At", "Error", "Evidence", "TTR (s)",
            ].map((h) => (
              <th key={h} className="text-left py-2 pr-3 font-semibold text-io-secondary uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <React.Fragment key={r.outcomeId}>
              <tr
                className="border-b border-io-border/40 hover:bg-io-bg/50 cursor-pointer"
                onClick={() => setExpanded(expanded === r.outcomeId ? null : r.outcomeId)}
              >
                <td className="py-2 pr-3 font-mono text-io-secondary">
                  {r.outcomeId.slice(0, 12)}…
                </td>
                <td className="py-2 pr-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${OUTCOME_AUDIT_STATUS_COLORS[r.status] ?? "bg-gray-100 text-gray-500"}`}>
                    {r.status.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="py-2 pr-3 text-io-primary">
                  {r.classification
                    ? r.classification.replace(/_/g, " ")
                    : <span className="text-io-secondary">—</span>}
                </td>
                <td className="py-2 pr-3 font-semibold text-io-primary">{r.recordedBy}</td>
                <td className="py-2 pr-3 font-mono text-io-secondary whitespace-nowrap">{fmt(r.recordedAt)}</td>
                <td className="py-2 pr-3 font-mono text-io-secondary whitespace-nowrap">{fmt(r.observedAt)}</td>
                <td className="py-2 pr-3">
                  {r.errorFlag
                    ? <span className="text-red-600 font-bold uppercase">YES</span>
                    : <span className="text-io-secondary">—</span>}
                </td>
                <td className="py-2 pr-3 font-mono text-io-secondary">{r.evidenceKeysCount}</td>
                <td className="py-2 font-mono text-io-secondary">
                  {r.timeToResolutionSeconds != null ? r.timeToResolutionSeconds : "—"}
                </td>
              </tr>
              {expanded === r.outcomeId && (
                <tr className="bg-io-bg/80">
                  <td colSpan={9} className="px-4 py-3">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Decision Linkage</p>
                        <div className="space-y-0.5">
                          <p>Decision: <code className="font-mono">{r.sourceDecisionId ?? "—"}</code></p>
                          <p>Run: <code className="font-mono">{r.sourceRunId ?? "—"}</code></p>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Lifecycle Timestamps</p>
                        <div className="space-y-0.5">
                          <p>Recorded: <span className="font-mono">{fmt(r.recordedAt)}</span></p>
                          <p>Observed: <span className="font-mono">{fmt(r.observedAt)}</span></p>
                          <p>Closed: <span className="font-mono">{fmt(r.closedAt)}</span></p>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-io-secondary mb-1">Notes</p>
                        <p className="text-io-secondary italic">
                          {r.notes ?? (isAr ? "لا ملاحظات" : "No notes recorded")}
                        </p>
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

// ─── Value audit table ────────────────────────────────────────────────────────

const VALUE_CLASS_BADGE_REG: Record<string, string> = {
  HIGH_VALUE:     "bg-emerald-100 text-emerald-800",
  POSITIVE_VALUE: "bg-green-100 text-green-700",
  NEUTRAL:        "bg-gray-100 text-gray-500",
  NEGATIVE_VALUE: "bg-orange-100 text-orange-700",
  LOSS_INDUCING:  "bg-red-100 text-red-700",
};

function ValueAuditTable({ rows, lang }: { rows: RegulatorValueRow[]; lang: Language }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const isAr = lang === "ar";

  if (rows.length === 0) {
    return (
      <p className="text-sm text-io-secondary text-center py-4">
        {isAr ? "لا توجد قيم محسوبة بعد" : "No computed values yet."}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-io-border text-io-secondary">
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Value ID</th>
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Computed By</th>
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Computed At</th>
            <th className="text-left py-2 pr-3 font-semibold uppercase tracking-wider">Classification</th>
            <th className="text-right py-2 pr-3 font-semibold uppercase tracking-wider">Net Value</th>
            <th className="text-right py-2 pr-3 font-semibold uppercase tracking-wider">Confidence</th>
            <th className="text-left py-2 font-semibold uppercase tracking-wider">Recomputed From</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <React.Fragment key={r.valueId}>
              <tr
                className="border-b border-io-border/50 hover:bg-io-bg/50 cursor-pointer transition-colors"
                onClick={() => setExpanded(expanded === r.valueId ? null : r.valueId)}
              >
                <td className="py-2 pr-3 font-mono text-io-secondary">{r.valueId.slice(0, 16)}</td>
                <td className="py-2 pr-3 font-semibold text-io-primary">{r.computedBy}</td>
                <td className="py-2 pr-3 font-mono text-io-secondary">
                  {new Date(r.computedAt).toISOString().replace("T", " ").slice(0, 16)}
                </td>
                <td className="py-2 pr-3">
                  <span className={`px-2 py-0.5 rounded-full font-semibold ${VALUE_CLASS_BADGE_REG[r.classification] ?? "bg-gray-100 text-gray-600"}`}>
                    {r.classification.replace(/_/g, " ")}
                  </span>
                </td>
                <td className={`py-2 pr-3 text-right font-bold tabular-nums ${r.netValue >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                  {r.netValue >= 0 ? "+" : ""}{r.netValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </td>
                <td className="py-2 pr-3 text-right tabular-nums">
                  {Math.round(r.confidenceScore * 100)}%
                </td>
                <td className="py-2 font-mono text-io-secondary text-[10px]">
                  {r.recomputedFrom ? r.recomputedFrom.slice(0, 16) : "—"}
                </td>
              </tr>
              {expanded === r.valueId && (
                <tr className="bg-io-bg/80 border-b border-io-border">
                  <td colSpan={7} className="py-3 px-3">
                    <div className="grid grid-cols-3 gap-4 text-xs">
                      {/* Decision linkage */}
                      <div className="space-y-1">
                        <p className="font-semibold text-io-secondary uppercase tracking-wider mb-1">Decision Linkage</p>
                        <p><span className="text-io-secondary">Outcome: </span><span className="font-mono">{r.sourceOutcomeId}</span></p>
                        <p><span className="text-io-secondary">Decision: </span><span className="font-mono">{r.sourceDecisionId ?? "—"}</span></p>
                        <p><span className="text-io-secondary">Run: </span><span className="font-mono">{r.sourceRunId ?? "—"}</span></p>
                      </div>
                      {/* Audit trail */}
                      <div className="space-y-1">
                        <p className="font-semibold text-io-secondary uppercase tracking-wider mb-1">Audit Trail</p>
                        <p><span className="text-io-secondary">Net Value: </span><strong>{r.netValueFormatted}</strong></p>
                        <p><span className="text-io-secondary">Confidence: </span>{Math.round(r.confidenceScore * 100)}%</p>
                        {r.recomputedFrom && (
                          <p className="text-orange-600">
                            <span className="text-io-secondary">Recomputed from: </span>
                            <span className="font-mono">{r.recomputedFrom}</span>
                          </p>
                        )}
                      </div>
                      {/* Notes */}
                      <div>
                        <p className="font-semibold text-io-secondary uppercase tracking-wider mb-1">Notes</p>
                        <p className="text-io-secondary italic">{r.notes ?? "—"}</p>
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

// ─── Main component ───────────────────────────────────────────────────────────

interface RegulatorViewProps {
  result: RunResult;
  lang: Language;
}

export function RegulatorView({ result, lang }: RegulatorViewProps) {
  const operatorDecisions = useAppStore(selectOperatorDecisions_RV);
  const liveSignals       = useAppStore(selectLiveSignals_RV);
  const pendingSeeds      = useAppStore(selectPendingSeeds_RV);
  const outcomes          = useAppStore(selectOutcomes_RV);
  const decisionValues    = useAppStore(selectDecisionValues_RV);

  const vm = toRegulatorViewModel(result, operatorDecisions, liveSignals, pendingSeeds, outcomes, decisionValues);
  const isAr = lang === "ar";

  return (
    <div className="max-w-6xl mx-auto px-6 lg:px-10 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-io-primary">
            {isAr ? "مراجعة الامتثال التنظيمي" : "Regulatory Audit View"}
          </h1>
          <p className="text-xs text-io-secondary mt-1">{vm.scenarioLabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full border border-io-border text-io-secondary">
            {isAr ? "محمي" : "READ-ONLY"}
          </span>
        </div>
      </div>

      {/* Audit provenance */}
      <Section title="Run Provenance & Identity" subtitle={`${vm.stagesCompleted.length} stages · ${vm.globalConfidence} confidence`}>
        <AuditHeader vm={vm} />
      </Section>

      {/* Decision lineage — most important for regulator */}
      <Section
        title="Decision Lifecycle & Lineage"
        subtitle={`${vm.decisions.length} operator decision${vm.decisions.length !== 1 ? "s" : ""}`}
      >
        <DecisionLineageTable decisions={vm.decisions} lang={lang} />
      </Section>

      {/* Signal trace */}
      <Section title="Signal Trace (Live Ingest)" subtitle={`${vm.signalTrace.length} most recent`}>
        <SignalTraceTable vm={vm} />
      </Section>

      {/* Pending seeds — HITL accountability */}
      <Section
        title="HITL Seed Review Log"
        subtitle={`${vm.pendingSeeds.length} seed${vm.pendingSeeds.length !== 1 ? "s" : ""}`}
      >
        <PendingSeedsAudit vm={vm} />
      </Section>

      {/* Outcome audit trail */}
      <Section
        title="Outcome Audit Trail"
        subtitle={`${vm.outcomeAuditRows.length} outcome${vm.outcomeAuditRows.length !== 1 ? "s" : ""}`}
      >
        <OutcomeAuditTable rows={vm.outcomeAuditRows} lang={lang} />
      </Section>

      {/* ROI audit — who computed, linkage to outcome/decision, classification, confidence */}
      <Section
        title="Decision Value Audit (ROI)"
        subtitle={`${vm.valueAuditRows.length} computed value${vm.valueAuditRows.length !== 1 ? "s" : ""}`}
      >
        <ValueAuditTable rows={vm.valueAuditRows} lang={lang} />
      </Section>

      {/* Pipeline accountability */}
      <Section title="Pipeline Execution Record">
        <PipelineRecord vm={vm} />
      </Section>

      {/* Regulatory events */}
      <Section title="Regulatory Breach Events">
        <RegulatoryEvents vm={vm} lang={lang} />
      </Section>
    </div>
  );
}
