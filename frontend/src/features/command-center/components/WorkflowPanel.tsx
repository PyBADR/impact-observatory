"use client";

/**
 * Decision Workflow Panel — Phase 3
 *
 * Shows approval requirement, escalation path, and current status
 * for all decisions from the Decision Workflow Engine.
 */

import React, { useState } from "react";
import type {
  DecisionWorkflow,
  DecisionOwnership,
} from "@/types/observatory";

// ── Status badge ──────────────────────────────────────────────────

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  PENDING:   { bg: "bg-amber-500/15 border-amber-500/30", text: "text-amber-400", label: "Pending" },
  APPROVED:  { bg: "bg-emerald-500/15 border-emerald-500/30", text: "text-emerald-400", label: "Approved" },
  REJECTED:  { bg: "bg-red-500/15 border-red-500/30", text: "text-red-400", label: "Rejected" },
  ESCALATED: { bg: "bg-purple-500/15 border-purple-500/30", text: "text-purple-400", label: "Escalated" },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.PENDING;
  return (
    <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  );
}

// ── Owner badge ──────────────────────────────────────────────────

const ROLE_COLORS: Record<string, string> = {
  CRO: "text-red-400",
  CFO: "text-blue-400",
  COO: "text-green-400",
  TREASURY: "text-yellow-400",
  RISK: "text-orange-400",
  REGULATOR: "text-purple-400",
};

function OwnerBadge({ role, unit }: { role: string; unit: string }) {
  const color = ROLE_COLORS[role] ?? "text-slate-400";
  return (
    <div className="flex items-center gap-2">
      <span className={`text-xs font-bold ${color}`}>{role}</span>
      <span className="text-[10px] text-slate-500">{unit}</span>
    </div>
  );
}

// ── Escalation path ──────────────────────────────────────────────

function EscalationPath({ path }: { path: string[] }) {
  if (!path.length) return null;
  return (
    <div className="flex items-center gap-1 text-[10px] text-slate-500">
      {path.map((step, i) => (
        <React.Fragment key={step}>
          {i > 0 && <span className="text-slate-600">→</span>}
          <span className={i === 0 ? "text-slate-300 font-semibold" : ""}>{step}</span>
        </React.Fragment>
      ))}
    </div>
  );
}

// ── Workflow row ──────────────────────────────────────────────────

function WorkflowRow({
  workflow,
  ownership,
}: {
  workflow: DecisionWorkflow;
  ownership?: DecisionOwnership;
}) {
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-800/40 border border-slate-700/40">
      <div className="flex flex-col gap-1 min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 font-mono truncate">
            {workflow.decision_id}
          </span>
          <StatusBadge status={workflow.status} />
          {workflow.approval_required && (
            <span className="text-[9px] text-amber-500/80 font-semibold uppercase">
              approval required
            </span>
          )}
        </div>
        {ownership && (
          <OwnerBadge role={ownership.owner_role} unit={ownership.organization_unit} />
        )}
      </div>
      <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-3">
        <span className="text-[10px] text-slate-500">
          Approver: <span className="text-slate-300">{workflow.approver_role}</span>
        </span>
        <EscalationPath path={workflow.escalation_path} />
      </div>
    </div>
  );
}

// ── Main panel ───────────────────────────────────────────────────

interface WorkflowPanelProps {
  workflows?: DecisionWorkflow[];
  ownerships?: DecisionOwnership[];
}

export function WorkflowPanel({ workflows, ownerships }: WorkflowPanelProps) {
  const [expanded, setExpanded] = useState(true);

  if (!workflows?.length) return null;

  // Build ownership lookup
  const ownerMap = new Map<string, DecisionOwnership>();
  for (const o of ownerships ?? []) {
    ownerMap.set(o.decision_id, o);
  }

  const pendingCount = workflows.filter((w) => w.status === "PENDING").length;
  const escalatedCount = workflows.filter((w) => w.status === "ESCALATED").length;
  const approvedCount = workflows.filter((w) => w.status === "APPROVED").length;

  return (
    <section className="px-6 py-4 bg-[#0B0F1A]">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center justify-between w-full mb-3"
      >
        <div className="flex items-center gap-3">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Decision Workflow
          </h3>
          <div className="flex items-center gap-2">
            {pendingCount > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-amber-500/15 text-amber-400">
                {pendingCount} pending
              </span>
            )}
            {escalatedCount > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-purple-500/15 text-purple-400">
                {escalatedCount} escalated
              </span>
            )}
            {approvedCount > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-emerald-500/15 text-emerald-400">
                {approvedCount} approved
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
        <div className="flex flex-col gap-2">
          {workflows.map((wf) => (
            <WorkflowRow
              key={wf.decision_id}
              workflow={wf}
              ownership={ownerMap.get(wf.decision_id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
