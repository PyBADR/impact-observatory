"use client";

/**
 * Decision Lifecycle Panel — Phase 3
 *
 * Shows the issued → approved → executed timeline for all decisions,
 * along with execution mode and trigger readiness from the Execution Trigger Layer.
 */

import React, { useState } from "react";
import type {
  DecisionLifecycle,
  ExecutionTrigger,
  IntegrationStatus,
} from "@/types/observatory";

// ── Lifecycle status indicator ──────────────────────────────────

const LC_STYLES: Record<string, { color: string; icon: string }> = {
  ISSUED:    { color: "text-slate-400", icon: "○" },
  APPROVED:  { color: "text-emerald-400", icon: "◉" },
  EXECUTED:  { color: "text-blue-400", icon: "●" },
  COMPLETED: { color: "text-green-400", icon: "✓" },
};

function LifecycleTimeline({ lc }: { lc: DecisionLifecycle }) {
  const stages = ["ISSUED", "APPROVED", "EXECUTED", "COMPLETED"];
  const currentIdx = stages.indexOf(lc.status);

  return (
    <div className="flex items-center gap-1">
      {stages.map((stage, i) => {
        const active = i <= currentIdx;
        const s = LC_STYLES[stage];
        return (
          <React.Fragment key={stage}>
            {i > 0 && (
              <div
                className={`w-6 h-px ${active ? "bg-emerald-500/50" : "bg-slate-700"}`}
              />
            )}
            <div className="flex flex-col items-center gap-0.5">
              <span
                className={`text-[10px] font-mono ${active ? s.color : "text-slate-700"}`}
              >
                {s.icon}
              </span>
              <span
                className={`text-[8px] uppercase ${active ? "text-slate-300" : "text-slate-600"}`}
              >
                {stage}
              </span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Execution mode badge ─────────────────────────────────────────

const EXEC_MODE_STYLES: Record<string, { bg: string; text: string }> = {
  MANUAL: { bg: "bg-slate-500/15 border-slate-500/30", text: "text-slate-400" },
  AUTO:   { bg: "bg-cyan-500/15 border-cyan-500/30", text: "text-cyan-400" },
  API:    { bg: "bg-indigo-500/15 border-indigo-500/30", text: "text-indigo-400" },
};

function ExecModeBadge({ mode }: { mode: string }) {
  const s = EXEC_MODE_STYLES[mode] ?? EXEC_MODE_STYLES.MANUAL;
  return (
    <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded border ${s.bg} ${s.text}`}>
      {mode}
    </span>
  );
}

// ── Lifecycle row ────────────────────────────────────────────────

function LifecycleRow({
  lifecycle,
  trigger,
}: {
  lifecycle: DecisionLifecycle;
  trigger?: ExecutionTrigger;
}) {
  return (
    <div className="py-2 px-3 rounded-lg bg-slate-800/40 border border-slate-700/40">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] text-slate-400 font-mono truncate">
          {lifecycle.decision_id}
        </span>
        <div className="flex items-center gap-2">
          {trigger && <ExecModeBadge mode={trigger.execution_mode} />}
          {trigger && (
            <span
              className={`text-[9px] font-bold ${trigger.trigger_ready ? "text-emerald-400" : "text-slate-600"}`}
            >
              {trigger.trigger_ready ? "READY" : "NOT READY"}
            </span>
          )}
        </div>
      </div>

      <LifecycleTimeline lc={lifecycle} />

      <div className="flex items-center gap-4 mt-1.5 text-[9px] text-slate-600">
        <span>Issued: {lifecycle.issued_at ? new Date(lifecycle.issued_at).toLocaleTimeString() : "—"}</span>
        {lifecycle.approved_at && (
          <span>Approved: {new Date(lifecycle.approved_at).toLocaleTimeString()}</span>
        )}
        {lifecycle.executed_at && (
          <span>Executed: {new Date(lifecycle.executed_at).toLocaleTimeString()}</span>
        )}
        {trigger?.system_target && (
          <span>Target: <span className="text-slate-400">{trigger.system_target}</span></span>
        )}
      </div>

      {lifecycle.outcome && (
        <div className="mt-1 text-[9px] text-slate-500 italic">
          {lifecycle.outcome}
        </div>
      )}
    </div>
  );
}

// ── Integration status footer ────────────────────────────────────

function IntegrationFooter({ integration }: { integration?: IntegrationStatus }) {
  if (!integration) return null;

  return (
    <div className="mt-3 px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-800/60">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">
          Integrations
        </span>
        <span className="text-[9px] text-slate-500">
          {integration.active.length}/{integration.available.length} active
        </span>
      </div>
      <div className="flex items-center gap-3">
        {integration.available.map((name) => {
          const isActive = integration.active.includes(name);
          return (
            <div key={name} className="flex items-center gap-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${isActive ? "bg-emerald-500" : "bg-slate-700"}`}
              />
              <span
                className={`text-[10px] ${isActive ? "text-slate-300" : "text-slate-600"}`}
              >
                {name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main panel ───────────────────────────────────────────────────

interface LifecyclePanelProps {
  lifecycles?: DecisionLifecycle[];
  triggers?: ExecutionTrigger[];
  integration?: IntegrationStatus;
}

export function LifecyclePanel({ lifecycles, triggers, integration }: LifecyclePanelProps) {
  const [expanded, setExpanded] = useState(true);

  if (!lifecycles?.length) return null;

  // Build trigger lookup
  const triggerMap = new Map<string, ExecutionTrigger>();
  for (const t of triggers ?? []) {
    triggerMap.set(t.action_id, t);
  }

  const executedCount = lifecycles.filter((l) => l.status === "EXECUTED").length;
  const approvedCount = lifecycles.filter((l) => l.status === "APPROVED").length;

  return (
    <section className="px-6 py-4 bg-[#0B0F1A]">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center justify-between w-full mb-3"
      >
        <div className="flex items-center gap-3">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Decision Lifecycle
          </h3>
          <div className="flex items-center gap-2">
            {approvedCount > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-emerald-500/15 text-emerald-400">
                {approvedCount} approved
              </span>
            )}
            {executedCount > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-blue-500/15 text-blue-400">
                {executedCount} executed
              </span>
            )}
          </div>
        </div>
        <svg
          className={`w-3.5 h-3.5 text-slate-500 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <>
          <div className="flex flex-col gap-2">
            {lifecycles.map((lc) => (
              <LifecycleRow
                key={lc.decision_id}
                lifecycle={lc}
                trigger={triggerMap.get(lc.decision_id)}
              />
            ))}
          </div>
          <IntegrationFooter integration={integration} />
        </>
      )}
    </section>
  );
}
