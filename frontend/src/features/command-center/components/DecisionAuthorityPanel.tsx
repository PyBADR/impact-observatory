"use client";

/**
 * Decision Authority Panel — Chief Risk Officer AI
 *
 * NOT a dashboard. NOT a report. A DECISION ENGINE.
 *
 * Renders executive directives with:
 *   - Urgency badge (pulsing for CRITICAL)
 *   - Decision verdict (EXECUTE/ESCALATE/MONITOR/NO_ACTION)
 *   - Financial exposure with inaction multiplier
 *   - Time to failure countdown
 *   - If-ignored block (red-highlighted consequences)
 *   - Ranked action list with owners, deadlines, and tracking status
 *   - Decision pressure gauge (0-100)
 *   - Governance/audit section
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowUpCircle,
  Clock,
  TrendingDown,
  Shield,
  Users,
  Target,
  Zap,
  Lock,
  ChevronDown,
  ChevronRight,
  Play,
  Pause,
  MessageSquare,
  Ban,
} from "lucide-react";
import { api } from "@/lib/api";
import { OperatingLayerView } from "@/features/operating-layer/components";
import type { OperatingLayer } from "@/features/operating-layer/types";

// ── Types ─────────────────────────────────────────────────────────────

interface DecisionAuthorityData {
  operating_layer?: OperatingLayer;
  decision_authority: {
    executive_directive: {
      headline_en: string;
      headline_ar: string;
      internal_decision: string;
      display_decision: string;
      display_decision_ar: string;
      decision: string; // Display label: EXECUTE | ESCALATE | MONITOR | NO_ACTION
      urgency_level: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
      action_statement_en: string;
      action_statement_ar: string;
    };
    why_this_decision: {
      summary_en: string;
      summary_ar: string;
      root_cause: string;
      systemic_risk: string;
      confidence: number;
    };
    if_ignored: {
      financial_impact_usd: number;
      financial_impact_formatted: string;
      inaction_multiplier: number;
      time_to_failure_hours: number;
      risk_escalation_path: string[];
      worst_case_scenario: string;
      regulatory_exposure: string;
      market_impact: string;
    };
    recommended_actions: Array<{
      action_id: string;
      action: string;
      action_ar: string;
      owner: string;
      sector: string;
      deadline_hours: number;
      impact_usd: number;
      impact_formatted: string;
      cost_formatted: string;
      roi_multiple: number;
      priority: number;
      status: string;
      owner_acknowledged: boolean;
      execution_progress: number;
      created_at: string;
      updated_at: string;
      notes: Array<{ timestamp: string; text: string }>;
      feasibility: number;
    }>;
    decision_pressure_score: {
      score: number;
      classification: string;
      drivers: string[];
    };
    governance: {
      audit_id: string;
      run_id: string;
      model_version: string;
      model_confidence: number;
      decision_timestamp: string;
      explainability: string;
      explainability_ar: string;
      risk_classification: string;
    };
  };
  meta?: Record<string, unknown>;
}

interface DecisionAuthorityPanelProps {
  scenarioId: string;
  severity: number;
  horizonHours: number;
  language?: "en" | "ar";
}

// ── Decision badge ────────────────────────────────────────────────────

function DecisionBadge({ decision }: { decision: string }) {
  const config: Record<string, { icon: React.ReactNode; bg: string; text: string; label: string }> = {
    EXECUTE: {
      icon: <CheckCircle size={14} />,
      bg: "bg-emerald-500/15 border-emerald-500/40",
      text: "text-emerald-400",
      label: "EXECUTE",
    },
    ESCALATE: {
      icon: <ArrowUpCircle size={14} />,
      bg: "bg-amber-500/15 border-amber-500/40",
      text: "text-amber-400",
      label: "ESCALATE",
    },
    MONITOR: {
      icon: <Clock size={14} />,
      bg: "bg-blue-500/15 border-blue-500/40",
      text: "text-blue-400",
      label: "MONITOR",
    },
    NO_ACTION: {
      icon: <XCircle size={14} />,
      bg: "bg-slate-500/15 border-slate-500/40",
      text: "text-slate-400",
      label: "NO ACTION",
    },
    // Backward compat: internal labels still work
    APPROVE: {
      icon: <CheckCircle size={14} />,
      bg: "bg-emerald-500/15 border-emerald-500/40",
      text: "text-emerald-400",
      label: "EXECUTE",
    },
    DELAY: {
      icon: <Clock size={14} />,
      bg: "bg-blue-500/15 border-blue-500/40",
      text: "text-blue-400",
      label: "MONITOR",
    },
    REJECT: {
      icon: <XCircle size={14} />,
      bg: "bg-slate-500/15 border-slate-500/40",
      text: "text-slate-400",
      label: "NO ACTION",
    },
  };
  const c = config[decision] ?? config.ESCALATE;
  return (
    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${c.bg} ${c.text}`}>
      {c.icon}
      <span className="text-[11px] font-bold tracking-wider">{c.label}</span>
    </div>
  );
}

// ── Urgency indicator ─────────────────────────────────────────────────

function UrgencyIndicator({ level }: { level: string }) {
  const config: Record<string, { color: string; pulse: boolean }> = {
    CRITICAL: { color: "bg-red-500", pulse: true },
    HIGH: { color: "bg-orange-500", pulse: false },
    MODERATE: { color: "bg-yellow-500", pulse: false },
    LOW: { color: "bg-blue-500", pulse: false },
  };
  const c = config[level] ?? config.MODERATE;
  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <div className={`w-2.5 h-2.5 rounded-full ${c.color}`} />
        {c.pulse && (
          <div className={`absolute inset-0 w-2.5 h-2.5 rounded-full ${c.color} animate-ping opacity-75`} />
        )}
      </div>
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{level}</span>
    </div>
  );
}

// ── Pressure gauge ────────────────────────────────────────────────────

function PressureGauge({ score, classification }: { score: number; classification: string }) {
  const color =
    score >= 80 ? "text-red-400" :
    score >= 60 ? "text-orange-400" :
    score >= 40 ? "text-yellow-400" :
    score >= 20 ? "text-blue-400" :
    "text-emerald-400";
  const barColor =
    score >= 80 ? "bg-red-500" :
    score >= 60 ? "bg-orange-500" :
    score >= 40 ? "bg-yellow-500" :
    score >= 20 ? "bg-blue-500" :
    "bg-emerald-500";

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">Decision Pressure</span>
          <span className={`text-sm font-mono font-bold ${color}`}>{score}</span>
        </div>
        <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
          <div
            className={`h-full rounded-full ${barColor} transition-all duration-1000`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
      <span className="text-[9px] text-slate-600 uppercase w-16 text-right">{classification}</span>
    </div>
  );
}

// ── Collapsible section ────────────────────────────────────────────────

function Section({
  title,
  icon,
  children,
  defaultOpen = true,
  highlight = false,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  highlight?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={`border-b last:border-b-0 ${highlight ? "border-red-500/20 bg-red-500/[0.03]" : "border-white/[0.04]"}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-left hover:bg-white/[0.02] transition-colors"
      >
        {icon}
        <span className={`text-[11px] font-semibold uppercase tracking-wider flex-1 ${highlight ? "text-red-400" : "text-slate-300"}`}>
          {title}
        </span>
        {open ? <ChevronDown size={12} className="text-slate-600" /> : <ChevronRight size={12} className="text-slate-600" />}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

// ── Action control button ─────────────────────────────────────────────

function ActionBtn({
  onClick,
  icon,
  label,
  color,
  disabled = false,
}: {
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  color: string;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-semibold border transition-colors
        ${disabled ? "opacity-30 cursor-not-allowed" : "hover:brightness-125 cursor-pointer"}
        ${color}`}
      title={label}
    >
      {icon}
      {label}
    </button>
  );
}


// ── Note input inline ─────────────────────────────────────────────────

function NoteInput({ onSubmit }: { onSubmit: (text: string) => void }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[8px] font-semibold border border-slate-600/30 text-slate-500 hover:text-slate-300 transition-colors"
        title="Add note"
      >
        <MessageSquare size={8} />
        Note
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-1">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Add operator note..."
        className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded px-2 py-0.5 text-[9px] text-slate-300 placeholder-slate-600 focus:outline-none focus:border-blue-500/40"
        onKeyDown={(e) => {
          if (e.key === "Enter" && text.trim()) {
            onSubmit(text.trim());
            setText("");
            setOpen(false);
          }
          if (e.key === "Escape") {
            setOpen(false);
            setText("");
          }
        }}
        autoFocus
      />
      <button
        onClick={() => {
          if (text.trim()) {
            onSubmit(text.trim());
            setText("");
            setOpen(false);
          }
        }}
        className="px-1.5 py-0.5 rounded text-[8px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30"
      >
        Send
      </button>
      <button
        onClick={() => { setOpen(false); setText(""); }}
        className="px-1 py-0.5 rounded text-[8px] text-slate-600 hover:text-slate-400"
      >
        ✕
      </button>
    </div>
  );
}


// ── Main Component ────────────────────────────────────────────────────

export function DecisionAuthorityPanel({
  scenarioId,
  severity,
  horizonHours,
  language = "en",
}: DecisionAuthorityPanelProps) {
  const [data, setData] = useState<DecisionAuthorityData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null); // action_id being patched
  const fetchedRef = useRef<string | null>(null);

  const cacheKey = `${scenarioId}-${severity}-${horizonHours}`;
  const isAr = language === "ar";

  // ── PATCH action helper ───────────────────────────────────────────
  const patchAction = useCallback(async (
    actionId: string,
    payload: {
      status?: string;
      execution_progress?: number;
      owner_acknowledged?: boolean;
      note?: string;
    },
  ) => {
    setUpdating(actionId);
    try {
      const res = await fetch(`/api/v1/decision/authority/actions/${actionId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-IO-API-Key": process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026",
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) return; // silently fail — executive errors handled server-side
      const result = await res.json();
      const updatedAction = result.action;
      if (!updatedAction || !data) return;

      // Update local state immutably
      setData((prev) => {
        if (!prev) return prev;
        const newActions = prev.decision_authority.recommended_actions.map((a) =>
          a.action_id === actionId ? { ...a, ...updatedAction } : a,
        );
        return {
          ...prev,
          decision_authority: {
            ...prev.decision_authority,
            recommended_actions: newActions,
          },
        };
      });
    } catch {
      // Network error — silent, UI stays consistent
    } finally {
      setUpdating(null);
    }
  }, [data]);

  useEffect(() => {
    if (fetchedRef.current === cacheKey) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch("/api/v1/decision/authority/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-IO-API-Key": process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026",
      },
      body: JSON.stringify({
        scenario_id: scenarioId,
        severity,
        horizon_hours: horizonHours,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`Decision authority failed: ${res.status}`);
        return res.json();
      })
      .then((result) => {
        if (cancelled) return;
        fetchedRef.current = cacheKey;
        setData(result as DecisionAuthorityData);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.message ?? "Failed to generate decision authority directive");
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, [cacheKey, scenarioId, severity, horizonHours]);

  // ── Loading state ─────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <div className="relative">
          <div className="w-8 h-8 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
          <div className="absolute inset-0 w-8 h-8 border-2 border-orange-500/20 border-b-orange-500 rounded-full animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.5s" }} />
        </div>
        <p className="text-[11px] text-slate-400 font-semibold">GENERATING EXECUTIVE DIRECTIVE</p>
        <p className="text-[10px] text-slate-600">Simulation → Narrative → Decision Authority</p>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-center px-6">
        <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center">
          <AlertTriangle size={16} className="text-red-500" />
        </div>
        <p className="text-[11px] font-semibold text-red-400">EXECUTION BLOCKED</p>
        <p className="text-[10px] text-slate-500">{error}</p>
        <p className="text-[10px] text-slate-600">Manual risk assessment required.</p>
      </div>
    );
  }

  if (!data?.decision_authority) return null;

  const da = data.decision_authority;
  const ed = da.executive_directive;
  const why = da.why_this_decision;
  const ignored = da.if_ignored;
  const actions = da.recommended_actions;
  const pressure = da.decision_pressure_score;
  const gov = da.governance;

  return (
    <div className="h-full overflow-y-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Hero: Decision + Urgency + Headline ──────────────────── */}
      <div className="px-4 py-3 border-b border-white/[0.06] bg-[#080C14]">
        <div className="flex items-center justify-between mb-2">
          <DecisionBadge decision={ed.decision} />
          <UrgencyIndicator level={ed.urgency_level} />
        </div>
        <h2 className="text-[13px] font-bold text-white leading-snug mb-2">
          {isAr ? ed.headline_ar : ed.headline_en}
        </h2>
        <PressureGauge score={pressure.score} classification={pressure.classification} />
      </div>

      {/* ── Action Statement ─────────────────────────────────────── */}
      <div className="px-4 py-3 border-b border-white/[0.06] bg-[#0A0E18]">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Executive Directive</p>
        <p className="text-xs text-slate-200 leading-relaxed font-medium">
          {isAr ? ed.action_statement_ar : ed.action_statement_en}
        </p>
      </div>

      {/* ── IF IGNORED (red highlight) ───────────────────────────── */}
      <Section
        title="Failure to Act Will Result In"
        icon={<AlertTriangle size={13} className="text-red-400" />}
        highlight={true}
      >
        <div className="space-y-3">
          {/* Financial escalation */}
          <div className="flex items-center gap-4">
            <div>
              <p className="text-[9px] text-red-500/70 uppercase">Escalated Exposure</p>
              <p className="text-lg font-mono font-bold text-red-400">{ignored.financial_impact_formatted}</p>
              <p className="text-[9px] text-red-500/60">{ignored.inaction_multiplier}x inaction multiplier</p>
            </div>
            <div>
              <p className="text-[9px] text-red-500/70 uppercase">Time to Failure</p>
              <p className="text-lg font-mono font-bold text-red-400">{ignored.time_to_failure_hours}h</p>
            </div>
          </div>

          {/* Escalation path */}
          <div>
            <p className="text-[9px] text-red-500/70 uppercase mb-1.5">Risk Escalation Path</p>
            <div className="space-y-1.5">
              {ignored.risk_escalation_path.map((step, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="flex items-center gap-1 mt-0.5 flex-shrink-0">
                    <span className="w-4 h-4 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center text-[8px] text-red-400 font-bold">
                      {i + 1}
                    </span>
                  </div>
                  <p className="text-[10px] text-red-300/80 leading-relaxed">{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Worst case */}
          <div className="bg-red-500/[0.06] rounded-lg p-2.5 border border-red-500/15">
            <p className="text-[9px] text-red-500/70 uppercase mb-1">Worst Case Scenario</p>
            <p className="text-[10px] text-red-300/90 leading-relaxed">{ignored.worst_case_scenario}</p>
          </div>

          {/* Regulatory + Market */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-[9px] text-red-500/70 uppercase mb-1">Regulatory Exposure</p>
              <p className="text-[10px] text-slate-400 leading-relaxed">{ignored.regulatory_exposure}</p>
            </div>
            <div>
              <p className="text-[9px] text-red-500/70 uppercase mb-1">Market Impact</p>
              <p className="text-[10px] text-slate-400 leading-relaxed">{ignored.market_impact}</p>
            </div>
          </div>
        </div>
      </Section>

      {/* ── Recommended Actions ───────────────────────────────────── */}
      <Section
        title="Recommended Actions (Ranked)"
        icon={<Target size={13} className="text-emerald-400" />}
      >
        <div className="space-y-2">
          {actions.map((a) => {
            const statusColor: Record<string, string> = {
              PENDING: "text-slate-500 bg-slate-500/10 border-slate-500/20",
              ACKNOWLEDGED: "text-blue-400 bg-blue-500/10 border-blue-500/20",
              IN_PROGRESS: "text-amber-400 bg-amber-500/10 border-amber-500/20",
              DONE: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
              BLOCKED: "text-red-400 bg-red-500/10 border-red-500/20",
            };
            const sc = statusColor[a.status] ?? statusColor.PENDING;
            const isUpdating = updating === a.action_id;
            const isDone = a.status === "DONE";
            const isBlocked = a.status === "BLOCKED";

            return (
              <div
                key={a.action_id || a.priority}
                className={`bg-white/[0.02] rounded-lg p-2.5 border transition-colors ${
                  isBlocked ? "border-red-500/20 bg-red-500/[0.02]" :
                  isDone ? "border-emerald-500/15 bg-emerald-500/[0.02]" :
                  "border-white/[0.04]"
                } ${isUpdating ? "opacity-60" : ""}`}
              >
                {/* Row 1: Priority + Action + Status + Sector */}
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold ${
                      isDone ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-400" :
                      isBlocked ? "bg-red-500/20 border border-red-500/40 text-red-400" :
                      "bg-emerald-500/15 border border-emerald-500/30 text-emerald-400"
                    }`}>
                      {isDone ? "✓" : a.priority}
                    </span>
                    <span className={`text-[11px] font-semibold ${isDone ? "text-slate-400 line-through" : "text-slate-200"}`}>
                      {isAr ? a.action_ar || a.action : a.action}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[8px] px-1.5 py-0.5 rounded border font-bold uppercase ${sc}`}>{a.status}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.05] text-slate-500 uppercase">{a.sector}</span>
                  </div>
                </div>

                {/* Progress bar */}
                {(a.execution_progress > 0 || a.status === "IN_PROGRESS") && (
                  <div className="mb-1.5">
                    <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${isDone ? "bg-emerald-500" : isBlocked ? "bg-red-500" : "bg-blue-500"}`}
                        style={{ width: `${a.execution_progress}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-[8px] text-slate-600">{a.execution_progress}% complete</span>
                      {a.status === "IN_PROGRESS" && !isDone && (
                        <div className="flex items-center gap-1">
                          {[25, 50, 75, 100].map((p) => (
                            <button
                              key={p}
                              onClick={() => patchAction(a.action_id, { execution_progress: p })}
                              disabled={isUpdating || a.execution_progress >= p}
                              className={`text-[7px] px-1 py-0 rounded font-mono ${
                                a.execution_progress >= p
                                  ? "text-slate-700 cursor-not-allowed"
                                  : "text-blue-500 hover:bg-blue-500/10 cursor-pointer"
                              }`}
                            >
                              {p}%
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Row 2: Owner, deadline, impact, ROI, acknowledgment */}
                <div className="flex items-center gap-3 text-[9px] flex-wrap mb-1.5">
                  <span className="text-slate-500"><Users size={9} className="inline mr-0.5" />{a.owner}</span>
                  <span className="text-orange-400"><Clock size={9} className="inline mr-0.5" />{a.deadline_hours}h</span>
                  <span className="text-emerald-400"><TrendingDown size={9} className="inline mr-0.5" />{a.impact_formatted}</span>
                  <span className="text-blue-400">ROI {a.roi_multiple}x</span>
                  {a.owner_acknowledged && (
                    <span className="text-emerald-500/70"><CheckCircle size={9} className="inline mr-0.5" />Acknowledged</span>
                  )}
                </div>

                {/* Row 3: Action controls */}
                {!isDone && (
                  <div className="flex items-center gap-1 flex-wrap">
                    {a.status === "PENDING" && (
                      <>
                        <ActionBtn
                          onClick={() => patchAction(a.action_id, { status: "ACKNOWLEDGED", owner_acknowledged: true })}
                          icon={<CheckCircle size={8} />}
                          label="Acknowledge"
                          color="text-blue-400 bg-blue-500/10 border-blue-500/20"
                          disabled={isUpdating}
                        />
                        <ActionBtn
                          onClick={() => patchAction(a.action_id, { status: "IN_PROGRESS" })}
                          icon={<Play size={8} />}
                          label="Start"
                          color="text-amber-400 bg-amber-500/10 border-amber-500/20"
                          disabled={isUpdating}
                        />
                      </>
                    )}
                    {a.status === "ACKNOWLEDGED" && (
                      <ActionBtn
                        onClick={() => patchAction(a.action_id, { status: "IN_PROGRESS" })}
                        icon={<Play size={8} />}
                        label="Start"
                        color="text-amber-400 bg-amber-500/10 border-amber-500/20"
                        disabled={isUpdating}
                      />
                    )}
                    {a.status === "IN_PROGRESS" && (
                      <ActionBtn
                        onClick={() => patchAction(a.action_id, { status: "DONE", execution_progress: 100 })}
                        icon={<CheckCircle size={8} />}
                        label="Done"
                        color="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                        disabled={isUpdating}
                      />
                    )}
                    {!isBlocked && a.status !== "DONE" && (
                      <ActionBtn
                        onClick={() => patchAction(a.action_id, { status: "BLOCKED" })}
                        icon={<Ban size={8} />}
                        label="Block"
                        color="text-red-400 bg-red-500/10 border-red-500/20"
                        disabled={isUpdating}
                      />
                    )}
                    {isBlocked && (
                      <ActionBtn
                        onClick={() => patchAction(a.action_id, { status: "IN_PROGRESS" })}
                        icon={<Play size={8} />}
                        label="Resume"
                        color="text-amber-400 bg-amber-500/10 border-amber-500/20"
                        disabled={isUpdating}
                      />
                    )}
                    <NoteInput onSubmit={(text) => patchAction(a.action_id, { note: text })} />
                  </div>
                )}

                {/* Notes display */}
                {a.notes && a.notes.length > 0 && (
                  <div className="mt-1.5 space-y-0.5">
                    {a.notes.slice(-2).map((n, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-[8px]">
                        <MessageSquare size={7} className="text-slate-600 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-500">{n.text}</span>
                        <span className="text-slate-700 flex-shrink-0">{new Date(n.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Section>

      {/* ── Why This Decision ─────────────────────────────────────── */}
      <Section
        title="Decision Basis"
        icon={<Zap size={13} className="text-amber-400" />}
        defaultOpen={false}
      >
        <div className="space-y-2">
          <p className="text-xs text-slate-300 leading-relaxed">
            {isAr ? why.summary_ar : why.summary_en}
          </p>
          <div>
            <p className="text-[9px] text-slate-600 uppercase mb-0.5">Root Cause</p>
            <p className="text-[10px] text-slate-400">{why.root_cause}</p>
          </div>
          <div>
            <p className="text-[9px] text-slate-600 uppercase mb-0.5">Systemic Risk</p>
            <p className="text-[10px] text-slate-400">{why.systemic_risk}</p>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] text-slate-600">Confidence:</span>
            <span className="text-[10px] font-mono text-slate-400">{Math.round(why.confidence * 100)}%</span>
          </div>
          {/* Pressure drivers */}
          <div>
            <p className="text-[9px] text-slate-600 uppercase mb-1">Pressure Drivers</p>
            {pressure.drivers.map((d, i) => (
              <div key={i} className="flex items-start gap-1.5 mb-0.5">
                <span className="w-1 h-1 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                <span className="text-[10px] text-slate-400">{d}</span>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Governance ────────────────────────────────────────────── */}
      <Section
        title="Governance & Audit"
        icon={<Lock size={13} className="text-slate-500" />}
        defaultOpen={false}
      >
        <div className="space-y-2">
          <div className="flex items-center gap-4 text-[9px] text-slate-600 font-mono">
            <span>Audit: {gov.audit_id}</span>
            <span>Run: {gov.run_id?.slice(0, 12)}...</span>
            <span>v{gov.model_version}</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-relaxed">
            {isAr ? gov.explainability_ar : gov.explainability}
          </p>
          <div className="flex items-center gap-3 text-[9px]">
            <span className="text-slate-600">Confidence: <span className="text-slate-400 font-mono">{Math.round(gov.model_confidence * 100)}%</span></span>
            <span className="text-slate-600">Risk: <span className="text-slate-400">{gov.risk_classification}</span></span>
          </div>
        </div>
      </Section>

      {/* ── Decision Operating Layer ─────────────────────────────── */}
      {data.operating_layer && (
        <div className="px-4 py-4 border-t border-white/[0.06]">
          <OperatingLayerView
            operatingLayer={data.operating_layer}
            language={language}
          />
        </div>
      )}
    </div>
  );
}
