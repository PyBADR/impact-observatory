"use client";

/**
 * BoardView — Executive Board Card
 *
 * Compact boardroom-grade summary readable in < 20 seconds.
 * Shows: directive, urgency, if-ignored summary, top 3 actions + status, audit confidence.
 *
 * Self-fetching: calls decision authority API on mount.
 * Designed to sit at the TOP of the command center as a persistent executive summary.
 */

import React, { useState, useEffect, useRef } from "react";
import {
  CheckCircle,
  ArrowUpCircle,
  Clock,
  XCircle,
  AlertTriangle,
  Shield,
  Users,
  TrendingDown,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────

interface BoardViewData {
  decision_authority: {
    executive_directive: {
      headline_en: string;
      headline_ar: string;
      decision: string;
      display_decision?: string;
      urgency_level: string;
      action_statement_en: string;
    };
    if_ignored: {
      financial_impact_formatted: string;
      inaction_multiplier: number;
      time_to_failure_hours: number;
      worst_case_scenario: string;
    };
    recommended_actions: Array<{
      action_id: string;
      action: string;
      owner: string;
      deadline_hours: number;
      priority: number;
      status: string;
      execution_progress: number;
      owner_acknowledged: boolean;
      impact_formatted: string;
    }>;
    decision_pressure_score: {
      score: number;
      classification: string;
    };
    governance: {
      audit_id: string;
      model_confidence: number;
      model_version: string;
    };
  };
}

interface BoardViewProps {
  scenarioId: string;
  severity: number;
  horizonHours: number;
  language?: "en" | "ar";
}

// ── Decision icon ────────────────────────────────────────────────────

function DirectiveIcon({ decision }: { decision: string }) {
  const map: Record<string, { icon: React.ReactNode; color: string }> = {
    EXECUTE: { icon: <CheckCircle size={18} />, color: "text-emerald-400" },
    ESCALATE: { icon: <ArrowUpCircle size={18} />, color: "text-amber-400" },
    MONITOR: { icon: <Clock size={18} />, color: "text-blue-400" },
    NO_ACTION: { icon: <XCircle size={18} />, color: "text-slate-400" },
    // backward compat
    APPROVE: { icon: <CheckCircle size={18} />, color: "text-emerald-400" },
    DELAY: { icon: <Clock size={18} />, color: "text-blue-400" },
    REJECT: { icon: <XCircle size={18} />, color: "text-slate-400" },
  };
  const c = map[decision] ?? map.ESCALATE;
  return <span className={c.color}>{c.icon}</span>;
}

// ── Status dot ───────────────────────────────────────────────────────

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PENDING: "bg-slate-500",
    ACKNOWLEDGED: "bg-blue-400",
    IN_PROGRESS: "bg-amber-400",
    DONE: "bg-emerald-400",
    BLOCKED: "bg-red-400",
  };
  return <div className={`w-1.5 h-1.5 rounded-full ${colors[status] ?? "bg-slate-500"}`} />;
}

// ── Main Component ────────────────────────────────────────────────────

export function BoardView({
  scenarioId,
  severity,
  horizonHours,
  language = "en",
}: BoardViewProps) {
  const [data, setData] = useState<BoardViewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef<string | null>(null);

  const cacheKey = `board-${scenarioId}-${severity}-${horizonHours}`;
  const isAr = language === "ar";

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
        if (!res.ok) throw new Error(`Board view fetch failed: ${res.status}`);
        return res.json();
      })
      .then((result) => {
        if (cancelled) return;
        fetchedRef.current = cacheKey;
        setData(result as BoardViewData);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.message ?? "Failed to load executive summary");
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, [cacheKey, scenarioId, severity, horizonHours]);

  // ── Loading ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="bg-[#080C14] border border-white/[0.06] rounded-xl p-4 flex items-center gap-3">
        <div className="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">Generating executive directive...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#080C14] border border-red-500/20 rounded-xl p-4 flex items-center gap-3">
        <AlertTriangle size={14} className="text-red-500" />
        <span className="text-[10px] text-red-400">{error}</span>
      </div>
    );
  }

  if (!data?.decision_authority) return null;

  const da = data.decision_authority;
  const ed = da.executive_directive;
  const ignored = da.if_ignored;
  const topActions = da.recommended_actions.slice(0, 3);
  const pressure = da.decision_pressure_score;
  const gov = da.governance;

  const allDone = topActions.length > 0 && topActions.every((a) => a.status === "DONE");
  const anyBlocked = topActions.some((a) => a.status === "BLOCKED");
  const decision = ed.display_decision || ed.decision;

  // Decision color schemes
  const decisionBg: Record<string, string> = {
    EXECUTE: "border-emerald-500/30 bg-emerald-500/[0.04]",
    ESCALATE: "border-amber-500/30 bg-amber-500/[0.04]",
    MONITOR: "border-blue-500/30 bg-blue-500/[0.04]",
    NO_ACTION: "border-slate-500/30 bg-slate-500/[0.04]",
    APPROVE: "border-emerald-500/30 bg-emerald-500/[0.04]",
    DELAY: "border-blue-500/30 bg-blue-500/[0.04]",
    REJECT: "border-slate-500/30 bg-slate-500/[0.04]",
  };

  const urgencyColor: Record<string, string> = {
    CRITICAL: "text-red-400",
    HIGH: "text-orange-400",
    MODERATE: "text-yellow-400",
    LOW: "text-blue-400",
  };

  const pressureColor =
    pressure.score >= 80 ? "text-red-400" :
    pressure.score >= 60 ? "text-orange-400" :
    pressure.score >= 40 ? "text-yellow-400" :
    "text-blue-400";

  return (
    <div
      className={`rounded-xl border ${decisionBg[decision] ?? decisionBg.ESCALATE} p-4`}
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* ── Row 1: Directive + Urgency + Pressure ────────────────── */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <DirectiveIcon decision={decision} />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white tracking-wide">{decision.replace("_", " ")}</span>
              <span className={`text-[9px] font-bold uppercase ${urgencyColor[ed.urgency_level] ?? "text-slate-400"}`}>
                {ed.urgency_level === "CRITICAL" && "● "}{ed.urgency_level}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5 max-w-lg leading-snug">
              {isAr ? ed.headline_ar : ed.headline_en}
            </p>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] text-slate-600 uppercase">Pressure</span>
            <span className={`text-lg font-mono font-bold ${pressureColor}`}>{pressure.score}</span>
          </div>
          <span className="text-[8px] text-slate-600">{pressure.classification}</span>
        </div>
      </div>

      {/* ── Row 2: If Ignored Summary + Audit ────────────────────── */}
      <div className="flex items-center justify-between mb-3 py-2 border-y border-white/[0.04]">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-[8px] text-red-500/70 uppercase block">If Ignored</span>
            <span className="text-sm font-mono font-bold text-red-400">{ignored.financial_impact_formatted}</span>
            <span className="text-[8px] text-red-500/50 ml-1">({ignored.inaction_multiplier}x)</span>
          </div>
          <div>
            <span className="text-[8px] text-orange-500/70 uppercase block">Time to Failure</span>
            <span className="text-sm font-mono font-bold text-orange-400">{ignored.time_to_failure_hours}h</span>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[8px] text-slate-600 font-mono">
          <span className="flex items-center gap-1"><Shield size={9} /> {gov.audit_id}</span>
          <span>{Math.round(gov.model_confidence * 100)}% conf</span>
          <span>v{gov.model_version}</span>
        </div>
      </div>

      {/* ── Row 3: Top 3 Actions ─────────────────────────────────── */}
      {allDone ? (
        <div className="bg-emerald-500/[0.06] rounded-lg p-3 border border-emerald-500/20 flex items-center gap-3">
          <CheckCircle size={16} className="text-emerald-400" />
          <div>
            <span className="text-[11px] font-bold text-emerald-400">EXECUTION COMPLETE</span>
            <p className="text-[9px] text-emerald-500/60 mt-0.5">All priority actions executed. Governance audit trail sealed.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2">
          {topActions.map((a) => {
            const isBlocked = a.status === "BLOCKED";
            const isDone = a.status === "DONE";

            return (
              <div
                key={a.action_id || a.priority}
                className={`rounded-lg p-2 border ${
                  isBlocked ? "bg-red-500/[0.06] border-red-500/20" :
                  isDone ? "bg-emerald-500/[0.04] border-emerald-500/15" :
                  "bg-white/[0.03] border-white/[0.04]"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[9px] font-bold truncate flex-1 mr-1 ${
                    isDone ? "text-slate-500 line-through" :
                    isBlocked ? "text-red-300" :
                    "text-slate-300"
                  }`}>{a.action}</span>
                  <StatusDot status={a.status} />
                </div>
                <div className="flex items-center gap-2 text-[8px] text-slate-500">
                  <span><Users size={8} className="inline" /> {a.owner.split("/")[0].trim()}</span>
                  <span className="text-orange-400">{a.deadline_hours}h</span>
                  {a.execution_progress > 0 && (
                    <span className="text-slate-600 font-mono">{a.execution_progress}%</span>
                  )}
                </div>
                {isBlocked && (
                  <div className="mt-1 flex items-center gap-1">
                    <AlertTriangle size={7} className="text-red-400" />
                    <span className="text-[7px] font-bold text-red-400 uppercase">Blocked</span>
                  </div>
                )}
                {a.execution_progress > 0 && !isBlocked && (
                  <div className="mt-1">
                    <div className="h-0.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className={`h-full rounded-full ${isDone ? "bg-emerald-500" : "bg-blue-500"}`}
                        style={{ width: `${a.execution_progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
