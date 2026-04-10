"use client";

/**
 * Decision Gate / Escalation Block — Shows approval state and escalation path.
 *
 * Gate status: OPEN (green), REQUIRES_APPROVAL (amber), AUTO_ESCALATED (red).
 * Displays: gate status, approval requirement, escalation target, action counts
 * by category (IMMEDIATE / CONDITIONAL / STRATEGIC), and highest urgency.
 */

import React from "react";
import {
  ShieldCheck,
  ShieldAlert,
  AlertOctagon,
  ArrowUpRight,
  Zap,
  Clock,
  Target,
} from "lucide-react";
import { formatPct } from "../lib/format";
import type { DecisionGateView } from "../lib/decision-view-models";

// ── Gate Status Visual ──────────────────────────────────────────────────

const GATE_CONFIG = {
  OPEN: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    icon: ShieldCheck,
    label: "Gate Open",
    sublabel: "Actions within normal authority",
  },
  REQUIRES_APPROVAL: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
    icon: ShieldAlert,
    label: "Approval Required",
    sublabel: "Escalation path active",
  },
  AUTO_ESCALATED: {
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
    icon: AlertOctagon,
    label: "Auto-Escalated",
    sublabel: "Risk threshold exceeded — routed to board",
  },
} as const;

// ── Action Count Pill ───────────────────────────────────────────────────

function CountPill({
  label,
  count,
  color,
  icon: Icon,
}: {
  label: string;
  count: number;
  color: string;
  icon: React.ElementType;
}) {
  if (count === 0) return null;
  return (
    <div
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border"
      style={{
        backgroundColor: `${color}10`,
        borderColor: `${color}30`,
      }}
    >
      <Icon size={11} style={{ color }} />
      <span className="text-[11px] font-bold tabular-nums" style={{ color }}>
        {count}
      </span>
      <span className="text-[10px] text-slate-500 uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

interface DecisionGateBlockProps {
  gate: DecisionGateView;
}

export function DecisionGateBlock({ gate }: DecisionGateBlockProps) {
  const cfg = GATE_CONFIG[gate.gate_status];
  const Icon = cfg.icon;

  return (
    <div className="bg-[#0A0E18] border-b border-white/[0.06]">
      <div className="px-6 py-3">
        <div className="flex items-start gap-4">
          {/* Gate status indicator */}
          <div
            className={`flex-shrink-0 w-12 h-12 rounded-xl ${cfg.bg} border ${cfg.border} flex items-center justify-center`}
          >
            <Icon size={20} className={cfg.text} />
          </div>

          {/* Gate info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h3 className={`text-sm font-bold ${cfg.text}`}>{cfg.label}</h3>
              <span className="text-[10px] text-slate-600 uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/[0.03] border border-white/[0.06]">
                {gate.risk_level}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mb-2">{cfg.sublabel}</p>

            {/* Action category counts */}
            <div className="flex items-center gap-2 flex-wrap">
              <CountPill
                label="Immediate"
                count={gate.immediate_count}
                color="#EF4444"
                icon={Zap}
              />
              <CountPill
                label="Conditional"
                count={gate.conditional_count}
                color="#F59E0B"
                icon={Clock}
              />
              <CountPill
                label="Strategic"
                count={gate.strategic_count}
                color="#3B82F6"
                icon={Target}
              />
            </div>
          </div>

          {/* Escalation target */}
          {gate.approval_required && (
            <div className="flex-shrink-0 text-right">
              <div className="flex items-center gap-1 text-[10px] text-slate-500 mb-1">
                <ArrowUpRight size={10} />
                <span className="uppercase tracking-wider">Escalation Target</span>
              </div>
              <p className="text-[12px] font-semibold text-slate-300">
                {gate.escalation_target}
              </p>
              {gate.highest_urgency > 0 && (
                <p className="text-[10px] text-slate-600 mt-0.5">
                  Peak urgency: {formatPct(gate.highest_urgency)}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
