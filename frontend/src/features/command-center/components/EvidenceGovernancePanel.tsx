"use client";

/**
 * Evidence & Governance Panel — Phase 5 Decision Auditability
 *
 * Three tabbed views:
 *   1. Evidence View — full decision evidence chain (signal → value)
 *   2. Governance View — policy status, violations, required approvals
 *   3. Audit View — override history, attribution defensibility
 *
 * Data contract: GovernancePayload from backend stages 33-36.
 * Pure display component — no side effects, no API calls.
 */

import React, { useMemo, useState } from "react";
import type { GovernancePayload, DecisionEvidence, DecisionPolicy, AttributionDefense, DecisionOverride } from "@/types/observatory";

// ── Helpers ──────────────────────────────────────────────────────────

function fmtUsd(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

function pct(v: number): string {
  return `${(v * 100).toFixed(0)}%`;
}

type TabId = "evidence" | "governance" | "audit";

// ── Evidence View ────────────────────────────────────────────────────

function EvidenceView({ evidence }: { evidence: DecisionEvidence[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (evidence.length === 0) {
    return <p className="text-xs text-slate-500 py-3">No evidence packs available.</p>;
  }

  return (
    <div className="space-y-2">
      {evidence.map((ev) => {
        const isExpanded = expandedId === ev.decision_id;
        const completeness = ev.completeness as unknown as Record<string, boolean>;
        const layerCount = [
          completeness.has_signal,
          completeness.has_transmission,
          completeness.has_counterfactual,
          completeness.has_trust,
          completeness.has_execution,
          completeness.has_outcome,
        ].filter(Boolean).length;

        return (
          <div key={ev.decision_id} className="rounded-lg border border-slate-700/50 bg-[#0D1117]">
            {/* Collapsed header */}
            <button
              onClick={() => setExpandedId(isExpanded ? null : ev.decision_id)}
              className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-800/30 transition-colors rounded-lg"
            >
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-400 font-mono truncate max-w-[200px]">{ev.decision_id}</span>
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${completeness.complete ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                  {completeness.complete ? "COMPLETE" : `${layerCount}/6 LAYERS`}
                </span>
              </div>
              <svg className={`w-3 h-3 text-slate-500 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div className="px-3 pb-3 space-y-2 border-t border-slate-800/60">
                <EvidenceLayer label="Signal Snapshot" data={ev.signal_snapshot as Record<string, unknown>} has={completeness.has_signal} />
                <EvidenceLayer label="Transmission Evidence" data={ev.transmission_evidence as Record<string, unknown>} has={completeness.has_transmission} />
                <EvidenceLayer label="Counterfactual Basis" data={ev.counterfactual_basis as Record<string, unknown>} has={completeness.has_counterfactual} />
                <EvidenceLayer label="Trust Basis" data={ev.trust_basis as Record<string, unknown>} has={completeness.has_trust} />
                <EvidenceLayer label="Execution Evidence" data={ev.execution_evidence as Record<string, unknown>} has={completeness.has_execution} />
                <EvidenceLayer label="Outcome Evidence" data={ev.outcome_evidence as Record<string, unknown>} has={completeness.has_outcome} />
                <p className="text-[9px] text-slate-600 pt-1">Assembled: {ev.assembled_at}</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function EvidenceLayer({ label, data, has }: { label: string; data: Record<string, unknown>; has: boolean }) {
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined && v !== "" && v !== 0);
  return (
    <div className="pt-2">
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-1.5 h-1.5 rounded-full ${has ? "bg-emerald-500" : "bg-slate-600"}`} />
        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      {entries.length > 0 ? (
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 pl-3.5">
          {entries.slice(0, 6).map(([k, v]) => (
            <div key={k} className="flex items-baseline gap-1.5">
              <span className="text-[9px] text-slate-600">{k.replace(/_/g, " ")}:</span>
              <span className="text-[10px] text-slate-400 truncate max-w-[150px]">
                {typeof v === "number" ? (v > 10000 ? `$${fmtUsd(v)}` : typeof v === "number" && v <= 1 && v >= 0 ? pct(v) : String(v)) : String(v)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[9px] text-slate-600 pl-3.5">No data</p>
      )}
    </div>
  );
}

// ── Governance View ──────────────────────────────────────────────────

function GovernanceView({ policies }: { policies: DecisionPolicy[] }) {
  if (policies.length === 0) {
    return <p className="text-xs text-slate-500 py-3">No policy evaluations available.</p>;
  }

  const blockedCount = policies.filter((p) => !p.allowed).length;
  const totalViolations = policies.reduce((sum, p) => sum + p.violations.length, 0);

  return (
    <div className="space-y-3">
      {/* Summary strip */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${blockedCount === 0 ? "bg-emerald-500" : "bg-red-500"}`} />
          <span className="text-[11px] text-slate-300">
            {blockedCount === 0 ? "All decisions cleared" : `${blockedCount} decision${blockedCount > 1 ? "s" : ""} blocked`}
          </span>
        </div>
        <span className="text-[10px] text-slate-500">{totalViolations} total violation{totalViolations !== 1 ? "s" : ""}</span>
        <span className="text-[10px] text-slate-500">{policies.length} evaluated</span>
      </div>

      {/* Per-decision policy cards */}
      {policies.map((policy) => (
        <div
          key={policy.decision_id}
          className={`rounded-lg border px-3 py-2 ${policy.allowed ? "border-emerald-500/20 bg-emerald-500/5" : "border-red-500/20 bg-red-500/5"}`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] text-slate-400 font-mono truncate max-w-[200px]">{policy.decision_id}</span>
            <div className="flex items-center gap-2">
              <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${policy.allowed ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                {policy.allowed ? "ALLOWED" : "BLOCKED"}
              </span>
              <span className="text-[9px] text-slate-500">{policy.rules_passed}/{policy.rules_evaluated} rules</span>
            </div>
          </div>

          {policy.violations.length > 0 && (
            <div className="space-y-0.5 mt-1.5">
              {policy.violations.map((v, i) => (
                <p key={i} className="text-[10px] text-red-400/80 flex items-start gap-1.5">
                  <span className="text-red-500 mt-0.5 flex-shrink-0">!</span>
                  {v}
                </p>
              ))}
            </div>
          )}

          {policy.required_approvals.length > 0 && (
            <div className="flex items-center gap-1.5 mt-1.5">
              <span className="text-[9px] text-slate-500">Required:</span>
              {policy.required_approvals.map((role) => (
                <span key={role} className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-blue-500/10 text-blue-400">{role}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Audit View ───────────────────────────────────────────────────────

function AuditView({ defenses, overrides }: { defenses: AttributionDefense[]; overrides: DecisionOverride[] }) {
  const overrideCount = overrides.filter((o) => o.overridden).length;

  return (
    <div className="space-y-3">
      {/* Override Summary */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${overrideCount === 0 ? "bg-emerald-500" : "bg-amber-500"}`} />
          <span className="text-[11px] text-slate-300">
            {overrideCount === 0 ? "No overrides recorded" : `${overrideCount} override${overrideCount > 1 ? "s" : ""} recorded`}
          </span>
        </div>
        <span className="text-[10px] text-slate-500">{defenses.length} attribution defense{defenses.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Override cards */}
      {overrides.filter((o) => o.overridden).map((ov) => (
        <div key={ov.decision_id} className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] text-slate-400 font-mono truncate max-w-[200px]">{ov.decision_id}</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-amber-500/10 text-amber-400">
              {ov.override_type?.replace("_", " ")}
            </span>
          </div>
          <p className="text-[10px] text-slate-400">{ov.reason}</p>
          <div className="flex items-center gap-3 mt-1">
            {ov.overridden_by && <span className="text-[9px] text-slate-500">By: <span className="text-amber-400">{ov.overridden_by}</span></span>}
            {ov.timestamp && <span className="text-[9px] text-slate-600">{new Date(ov.timestamp).toLocaleString()}</span>}
          </div>
        </div>
      ))}

      {/* Attribution Defense cards */}
      {defenses.length > 0 && (
        <div className="pt-1">
          <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider mb-2">Attribution Defensibility</p>
          {defenses.map((def) => (
            <div key={def.decision_id} className="rounded-lg border border-slate-700/50 bg-[#0D1117] px-3 py-2 mb-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] text-slate-400 font-mono truncate max-w-[180px]">{def.decision_id}</span>
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                    def.attribution_type === "DIRECT" ? "bg-blue-500/10 text-blue-400" :
                    def.attribution_type === "ASSISTED" ? "bg-amber-500/10 text-amber-400" :
                    "bg-slate-500/10 text-slate-500"
                  }`}>
                    {def.attribution_type}
                  </span>
                  <span className="text-[9px] text-slate-500">{pct(def.confidence_band)} conf</span>
                </div>
              </div>
              <p className="text-[10px] text-slate-400 leading-relaxed">{def.explanation}</p>
              {def.external_factors.length > 0 && (
                <div className="flex items-center gap-1.5 mt-1">
                  <span className="text-[9px] text-slate-600">External:</span>
                  {def.external_factors.map((f) => (
                    <span key={f} className="px-1.5 py-0.5 rounded text-[8px] bg-slate-700/50 text-slate-500">{f}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Panel ───────────────────────────────────────────────────────

interface EvidenceGovernancePanelProps {
  governance: GovernancePayload | null | undefined;
}

export function EvidenceGovernancePanel({ governance }: EvidenceGovernancePanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("evidence");

  const evidence = useMemo(() => (governance?.decision_evidence ?? []) as unknown as DecisionEvidence[], [governance]);
  const policies = useMemo(() => (governance?.policy ?? []) as unknown as DecisionPolicy[], [governance]);
  const defenses = useMemo(() => (governance?.attribution_defense ?? []) as unknown as AttributionDefense[], [governance]);
  const overrides = useMemo(() => (governance?.overrides ?? []) as unknown as DecisionOverride[], [governance]);

  if (!governance || evidence.length === 0) return null;

  const blockedCount = policies.filter((p) => !p.allowed).length;
  const overrideCount = overrides.filter((o) => o.overridden).length;

  const tabs: { id: TabId; label: string; badge?: number; badgeColor?: string }[] = [
    { id: "evidence", label: "Evidence" },
    { id: "governance", label: "Governance", badge: blockedCount > 0 ? blockedCount : undefined, badgeColor: "bg-red-500" },
    { id: "audit", label: "Audit Trail", badge: overrideCount > 0 ? overrideCount : undefined, badgeColor: "bg-amber-500" },
  ];

  return (
    <section className="flex-shrink-0 px-6 py-4 bg-[#0B0F1A] border-t border-slate-800/60">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 rounded-full bg-violet-500" />
          <h2 className="text-sm font-semibold text-white tracking-tight">
            Evidence & Governance
          </h2>
          <span className="text-[10px] text-slate-500 font-mono">PHASE 5</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
          <span>{evidence.length} decisions</span>
          <span className="text-slate-700">|</span>
          <span>{policies.filter((p) => p.allowed).length} cleared</span>
          <span className="text-slate-700">|</span>
          <span>{overrideCount} overrides</span>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex items-center gap-1 mb-3 bg-[#0D1117] rounded-lg p-0.5 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-all flex items-center gap-1.5 ${
              activeTab === tab.id
                ? "bg-slate-700/60 text-white"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab.label}
            {tab.badge !== undefined && (
              <span className={`px-1 py-0.5 rounded text-[8px] text-white ${tab.badgeColor}`}>{tab.badge}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "evidence" && <EvidenceView evidence={evidence} />}
      {activeTab === "governance" && <GovernanceView policies={policies} />}
      {activeTab === "audit" && <AuditView defenses={defenses} overrides={overrides} />}
    </section>
  );
}
