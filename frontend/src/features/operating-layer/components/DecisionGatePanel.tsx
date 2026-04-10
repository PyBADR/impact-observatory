"use client";

/**
 * DecisionGatePanel — Controls whether this decision can proceed
 *
 * Shows:
 *   - Gate status badge (open/pending/escalated/executable)
 *   - Approval requirements
 *   - Escalation thresholds
 *   - Auto-escalation triggers (active + potential)
 *   - Gate audit trail
 */

import React from "react";
import {
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpCircle,
  Shield,
  Zap,
} from "lucide-react";
import type { DecisionGate, EscalationTrigger } from "../types";

// ── Gate Status Badge ───────────────────────────────────────────────

function GateStatusBadge({
  status,
  label,
}: {
  status: string;
  label: string;
}) {
  const config: Record<
    string,
    { bg: string; text: string; icon: React.ReactNode; pulse: boolean }
  > = {
    open: {
      bg: "bg-emerald-500/15 border-emerald-500/40",
      text: "text-emerald-400",
      icon: <Unlock size={13} />,
      pulse: false,
    },
    pending_approval: {
      bg: "bg-amber-500/15 border-amber-500/40",
      text: "text-amber-400",
      icon: <Clock size={13} />,
      pulse: true,
    },
    escalated: {
      bg: "bg-red-500/15 border-red-500/40",
      text: "text-red-400",
      icon: <ArrowUpCircle size={13} />,
      pulse: true,
    },
    executable: {
      bg: "bg-blue-500/15 border-blue-500/40",
      text: "text-blue-400",
      icon: <CheckCircle size={13} />,
      pulse: false,
    },
  };
  const c = config[status] ?? config.pending_approval;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${c.bg} ${c.text}`}>
      <div className="relative">
        {c.icon}
        {c.pulse && (
          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-current animate-ping opacity-50" />
        )}
      </div>
      <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
    </div>
  );
}

// ── Trigger Item ────────────────────────────────────────────────────

function TriggerItem({
  trigger,
  isAr,
}: {
  trigger: EscalationTrigger;
  isAr: boolean;
}) {
  return (
    <div
      className={`flex items-start gap-2 py-1.5 ${
        trigger.active ? "" : "opacity-40"
      }`}
    >
      <div className="mt-0.5 flex-shrink-0">
        {trigger.active ? (
          <div className="relative">
            <Zap size={10} className="text-red-400" />
            <div className="absolute inset-0 animate-ping opacity-30">
              <Zap size={10} className="text-red-400" />
            </div>
          </div>
        ) : (
          <div className="w-2.5 h-2.5 rounded-full border border-slate-600" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p
          className={`text-[10px] leading-relaxed ${
            trigger.active ? "text-red-300 font-medium" : "text-slate-500"
          }`}
        >
          {isAr ? trigger.trigger_ar : trigger.trigger_en}
        </p>
        {trigger.active && (
          <span className="text-[8px] text-red-500/70 font-bold uppercase">
            {isAr ? "نشط" : "ACTIVE"}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface DecisionGatePanelProps {
  gate: DecisionGate;
  language?: "en" | "ar";
}

export function DecisionGatePanel({
  gate,
  language = "en",
}: DecisionGatePanelProps) {
  const isAr = language === "ar";

  return (
    <div className="bg-white/[0.02] rounded-xl border border-white/[0.06] overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/[0.04] bg-[#080C14]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock size={13} className="text-slate-500" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-300">
              {isAr ? "بوابة القرار" : "Decision Gate"}
            </span>
          </div>
          <GateStatusBadge
            status={gate.gate_status}
            label={isAr ? gate.gate_status_label_ar : gate.gate_status_label_en}
          />
        </div>
      </div>

      <div className="px-4 py-3 space-y-4">
        {/* Approval requirement */}
        {gate.approval_required && (
          <div className="flex items-center gap-3 p-2.5 rounded-lg bg-amber-500/[0.05] border border-amber-500/15">
            <Shield size={14} className="text-amber-400 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-amber-400">
                {isAr ? "يتطلب موافقة" : "Approval Required"}
              </p>
              <p className="text-[9px] text-amber-500/70">
                {isAr ? gate.approval_owner_ar : gate.approval_owner}
              </p>
            </div>
          </div>
        )}

        {!gate.approval_required && gate.gate_status === "open" && (
          <div className="flex items-center gap-3 p-2.5 rounded-lg bg-emerald-500/[0.05] border border-emerald-500/15">
            <Unlock size={14} className="text-emerald-400 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-emerald-400">
                {isAr
                  ? "لا تتطلب موافقة — يمكن المتابعة"
                  : "No Approval Required — Proceed"}
              </p>
            </div>
          </div>
        )}

        {gate.gate_status === "executable" && (
          <div className="flex items-center gap-3 p-2.5 rounded-lg bg-blue-500/[0.05] border border-blue-500/15">
            <CheckCircle size={14} className="text-blue-400 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-blue-400">
                {isAr
                  ? "معتمد — جاهز للتنفيذ"
                  : "Approved — Ready for Execution"}
              </p>
            </div>
          </div>
        )}

        {/* Escalation thresholds */}
        <div>
          <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-2 font-semibold">
            {isAr ? "عتبات التصعيد" : "Escalation Thresholds"}
          </p>
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
              <p className="text-[8px] text-slate-600 uppercase">
                {isAr ? "عتبة الخسارة" : "Loss Threshold"}
              </p>
              <p className="text-[11px] font-mono font-semibold text-slate-300">
                {gate.escalation_threshold.loss_usd_threshold_formatted}
              </p>
            </div>
            <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
              <p className="text-[8px] text-slate-600 uppercase">
                {isAr ? "عتبة الضغط" : "Stress Threshold"}
              </p>
              <p className="text-[11px] font-mono font-semibold text-slate-300">
                {(gate.escalation_threshold.stress_threshold * 100).toFixed(0)}%
              </p>
            </div>
            <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
              <p className="text-[8px] text-slate-600 uppercase">
                {isAr ? "عتبة الوقت" : "Time Threshold"}
              </p>
              <p className="text-[11px] font-mono font-semibold text-slate-300">
                {gate.escalation_threshold.time_to_failure_threshold_hours.toFixed(0)}h
              </p>
            </div>
            <div className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
              <p className="text-[8px] text-slate-600 uppercase">
                {isAr ? "عتبة الضغط" : "Pressure Threshold"}
              </p>
              <p className="text-[11px] font-mono font-semibold text-slate-300">
                {gate.escalation_threshold.pressure_score_threshold}/100
              </p>
            </div>
          </div>
        </div>

        {/* Auto-escalation triggers */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-[9px] text-slate-600 uppercase tracking-wider font-semibold">
              {isAr ? "محفزات التصعيد التلقائي" : "Auto-Escalation Triggers"}
            </p>
            {gate.active_triggers_count > 0 && (
              <span className="text-[8px] font-bold text-red-400 bg-red-500/10 border border-red-500/20 rounded px-1.5 py-0.5">
                {gate.active_triggers_count} {isAr ? "نشط" : "ACTIVE"}
              </span>
            )}
          </div>
          <div className="space-y-0.5">
            {gate.auto_escalation_triggers.map((trigger, i) => (
              <TriggerItem key={i} trigger={trigger} isAr={isAr} />
            ))}
          </div>
        </div>

        {/* Audit */}
        <div className="border-t border-white/[0.04] pt-3">
          <p className="text-[8px] text-slate-700 font-mono">
            Gate Audit: {gate.gate_audit_hash}
          </p>
          <p className="text-[8px] text-slate-600 mt-0.5 leading-relaxed">
            {isAr ? gate.gate_rationale_ar : gate.gate_rationale_en}
          </p>
        </div>
      </div>
    </div>
  );
}
