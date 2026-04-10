"use client";

/**
 * Action Readiness Block — IMMEDIATE / CONDITIONAL / STRATEGIC sections.
 *
 * Renders classified actions from the Action Pathways Engine in 3 swim lanes.
 * Each action shows: label, owner, deadline, trigger condition (conditional only),
 * reversibility, expected impact, and priority score.
 */

import React, { useState } from "react";
import {
  Zap,
  Clock,
  Target,
  AlertTriangle,
  User,
  ChevronDown,
  ChevronUp,
  ArrowRight,
} from "lucide-react";
import { formatUSD, formatHours, formatPct, safeNum, safeStr } from "../lib/format";
import type { ClassifiedAction, ActionType, ActionPathways, ActionConfidence, ExecutionTrigger } from "@/types/observatory";

// ── Lane Config ─────────────────────────────────────────────────────────

const LANE_CONFIG: Record<
  ActionType,
  { color: string; bg: string; border: string; icon: React.ElementType; label: string }
> = {
  IMMEDIATE: {
    color: "#EF4444",
    bg: "bg-red-500/8",
    border: "border-red-500/20",
    icon: Zap,
    label: "Immediate",
  },
  CONDITIONAL: {
    color: "#F59E0B",
    bg: "bg-amber-500/8",
    border: "border-amber-500/20",
    icon: Clock,
    label: "Conditional",
  },
  STRATEGIC: {
    color: "#3B82F6",
    bg: "bg-blue-500/8",
    border: "border-blue-500/20",
    icon: Target,
    label: "Strategic",
  },
};

// ── Reversibility Badge ─────────────────────────────────────────────────

function RevBadge({ level }: { level: string }) {
  const cfg =
    level === "HIGH"
      ? { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" }
      : level === "LOW"
      ? { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" }
      : { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" };

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${cfg.color} ${cfg.bg} border ${cfg.border}`}
    >
      {level}
    </span>
  );
}

// ── Single Action Row ───────────────────────────────────────────────────

// ── Action Confidence Indicator ──────────────────────────────────────────

function ActionConfBadge({ conf }: { conf: ActionConfidence | undefined }) {
  if (!conf) return null;
  const score = safeNum(conf.confidence_score);
  const label = conf.confidence_label ?? "MEDIUM";
  const isLow = label === "LOW";
  const color = label === "HIGH" ? "#22C55E" : label === "LOW" ? "#EF4444" : "#F59E0B";
  const bg = isLow ? "bg-red-500/10 border-red-500/20" : "bg-white/[0.03] border-white/[0.06]";

  return (
    <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded border ${bg}`}>
      <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-[9px] font-bold tabular-nums" style={{ color }}>
        {formatPct(score)}
      </span>
      {isLow && (
        <AlertTriangle size={8} className="text-red-400" />
      )}
    </div>
  );
}

function ActionRow({ action, confidence, trigger }: { action: ClassifiedAction; confidence?: ActionConfidence; trigger?: ExecutionTrigger }) {
  const urgency = safeNum(action.urgency);
  const priority = safeNum(action.priority_score);
  const hours = safeNum(action.time_to_act_hours);
  const isLowConf = confidence?.confidence_label === "LOW";

  return (
    <div className={`px-3 py-2.5 rounded-lg bg-[#0F1420] border ${
      isLowConf ? "border-red-500/20 bg-red-500/[0.03]" : "border-white/[0.06]"
    } hover:border-white/[0.12] transition-all`}>
      {/* Top row: label + owner */}
      <div className="flex items-start justify-between mb-1.5">
        <p className="text-[12px] font-medium text-slate-200 leading-snug flex-1 mr-3">
          {safeStr(action.label)}
        </p>
        <div className="flex items-center gap-1 text-[10px] text-slate-600 flex-shrink-0">
          <User size={9} />
          <span>{safeStr(action.owner)}</span>
        </div>
      </div>

      {/* Arabic label */}
      {action.label_ar && action.label_ar !== "—" && (
        <p className="text-[10px] text-slate-600 mb-1.5 line-clamp-1" dir="rtl">
          {action.label_ar}
        </p>
      )}

      {/* Trigger condition (conditional only) */}
      {action.trigger_condition && (
        <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-amber-500/8 border border-amber-500/15 mb-2">
          <AlertTriangle size={10} className="text-amber-400 flex-shrink-0" />
          <span className="text-[10px] text-amber-300/80">
            Trigger: {action.trigger_condition}
          </span>
        </div>
      )}

      {/* Metrics row */}
      <div className="flex items-center gap-3 text-[10px]">
        <div className="flex items-center gap-1">
          <Clock size={9} className="text-slate-500" />
          <span className="text-slate-500">Window</span>
          <span className="font-bold text-slate-300 tabular-nums">
            {formatHours(hours)}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-slate-500">Benefit</span>
          <span className="font-bold text-emerald-400 tabular-nums">
            {formatUSD(safeNum(action.loss_avoided_usd))}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-slate-500">Cost</span>
          <span className="font-bold text-red-400 tabular-nums">
            {formatUSD(safeNum(action.cost_usd))}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-slate-500">Priority</span>
          <span className="font-bold text-blue-400 tabular-nums">
            {Math.round(priority)}
          </span>
        </div>
        <RevBadge level={action.reversibility ?? "MEDIUM"} />
        <ActionConfBadge conf={confidence} />
        {trigger && (
          <span className={`px-1.5 py-0.5 text-[8px] font-bold rounded border ${
            trigger.execution_mode === "AUTO" ? "border-cyan-500/30 text-cyan-400" :
            trigger.execution_mode === "API" ? "border-indigo-500/30 text-indigo-400" :
            "border-slate-600/40 text-slate-400"
          }`}>
            {trigger.execution_mode}
          </span>
        )}
        {trigger && (
          <span className={`text-[8px] font-bold ${trigger.trigger_ready ? "text-emerald-400" : "text-slate-600"}`}>
            {trigger.trigger_ready ? "●" : "○"}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Swim Lane ───────────────────────────────────────────────────────────

function SwimLane({
  type,
  actions,
  defaultExpanded,
  actionConfidence,
  executionTriggers,
}: {
  type: ActionType;
  actions: ClassifiedAction[];
  defaultExpanded: boolean;
  actionConfidence?: ActionConfidence[];
  executionTriggers?: ExecutionTrigger[];
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const cfg = LANE_CONFIG[type];
  const Icon = cfg.icon;

  if (actions.length === 0) return null;

  return (
    <div className={`rounded-xl border ${cfg.border} overflow-hidden`}>
      {/* Lane header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full flex items-center justify-between px-4 py-2.5 ${cfg.bg} hover:brightness-110 transition-all`}
      >
        <div className="flex items-center gap-2">
          <Icon size={14} style={{ color: cfg.color }} />
          <span
            className="text-[11px] font-bold uppercase tracking-wider"
            style={{ color: cfg.color }}
          >
            {cfg.label}
          </span>
          <span className="text-[10px] text-slate-500 tabular-nums">
            {actions.length} {actions.length === 1 ? "action" : "actions"}
          </span>
        </div>
        {expanded ? (
          <ChevronUp size={14} className="text-slate-500" />
        ) : (
          <ChevronDown size={14} className="text-slate-500" />
        )}
      </button>

      {/* Action list */}
      {expanded && (
        <div className="p-3 space-y-2">
          {actions.map((action, i) => {
            const conf = actionConfidence?.find(
              (c) => c.action_id === (action.id ?? `action_${i}`)
            ) ?? actionConfidence?.[i];
            const trig = executionTriggers?.find(
              (t) => t.action_id === (action.id ?? `action_${i}`)
            ) ?? executionTriggers?.[i];
            return (
              <ActionRow key={`${type}-${action.id || i}`} action={action} confidence={conf} trigger={trig} />
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

interface ActionReadinessBlockProps {
  pathways: ActionPathways | null | undefined;
  actionConfidence?: ActionConfidence[];
  executionTriggers?: ExecutionTrigger[];
}

export function ActionReadinessBlock({ pathways, actionConfidence, executionTriggers }: ActionReadinessBlockProps) {
  if (!pathways) return null;

  const imm = pathways.immediate ?? [];
  const cond = pathways.conditional ?? [];
  const strat = pathways.strategic ?? [];
  const total = safeNum(pathways.total_actions, imm.length + cond.length + strat.length);

  if (total === 0) return null;

  return (
    <div className="bg-[#0A0E18] border-b border-white/[0.06]">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-2.5 border-b border-white/[0.04]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            Action Readiness
          </h2>
          <span className="text-[10px] text-slate-600 tabular-nums">
            {total} classified actions
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          {imm.length > 0 && (
            <span className="text-red-400 font-bold">{imm.length} immediate</span>
          )}
          {cond.length > 0 && (
            <span className="text-amber-400 font-bold">{cond.length} conditional</span>
          )}
          {strat.length > 0 && (
            <span className="text-blue-400 font-bold">{strat.length} strategic</span>
          )}
        </div>
      </div>

      {/* Summary */}
      {pathways.summary && pathways.summary !== "—" && (
        <div className="px-6 py-2 border-b border-white/[0.03]">
          <p className="text-[10px] text-slate-500">{pathways.summary}</p>
        </div>
      )}

      {/* Swim lanes */}
      <div className="px-6 py-3 space-y-3">
        <SwimLane type="IMMEDIATE" actions={imm} defaultExpanded={true} actionConfidence={actionConfidence} executionTriggers={executionTriggers} />
        <SwimLane type="CONDITIONAL" actions={cond} defaultExpanded={true} actionConfidence={actionConfidence} executionTriggers={executionTriggers} />
        <SwimLane type="STRATEGIC" actions={strat} defaultExpanded={false} actionConfidence={actionConfidence} executionTriggers={executionTriggers} />
      </div>
    </div>
  );
}
