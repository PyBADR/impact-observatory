"use client";

/**
 * Executive Decision Strip — Top 3 decisions visible without scrolling.
 *
 * Each card shows: rank, action text, status badge (CRITICAL/SEVERE/MONITOR),
 * owner, deadline, downside_if_ignored, and a compact cost/benefit indicator.
 * Designed for CRO/board-level scanning — high signal, minimal decoration.
 */

import React from "react";
import {
  AlertTriangle,
  Clock,
  Shield,
  User,
  Zap,
  TrendingDown,
} from "lucide-react";
import { formatUSD, formatHours, formatPct, safeNum, safeStr } from "../lib/format";
import type { ExecutiveDecisionCard } from "../lib/decision-view-models";
import type { ActionConfidence, RiskEnvelope, DecisionOwnership, DecisionWorkflow } from "@/types/observatory";

// ── Status Badge ────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  CRITICAL: {
    bg: "bg-red-500/15",
    border: "border-red-500/30",
    text: "text-red-400",
    icon: Zap,
    label: "Critical",
  },
  SEVERE: {
    bg: "bg-amber-500/15",
    border: "border-amber-500/30",
    text: "text-amber-400",
    icon: AlertTriangle,
    label: "Severe",
  },
  MONITOR: {
    bg: "bg-slate-500/15",
    border: "border-slate-500/30",
    text: "text-slate-400",
    icon: Shield,
    label: "Monitor",
  },
} as const;

function StatusBadge({ status }: { status: "CRITICAL" | "SEVERE" | "MONITOR" }) {
  const cfg = STATUS_CONFIG[status];
  const Icon = cfg.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md ${cfg.bg} border ${cfg.border} ${cfg.text} text-[10px] font-bold uppercase tracking-wider`}
    >
      <Icon size={9} /> {cfg.label}
    </span>
  );
}

// ── Confidence Badge ────────────────────────────────────────────────────

function ConfidenceBadge({
  confidence,
}: {
  confidence: ActionConfidence | undefined;
}) {
  if (!confidence) return null;

  const score = safeNum(confidence.confidence_score);
  const label = confidence.confidence_label ?? "MEDIUM";
  const color =
    label === "HIGH" ? "#22C55E" : label === "LOW" ? "#EF4444" : "#F59E0B";
  const bg =
    label === "HIGH"
      ? "bg-emerald-500/10 border-emerald-500/20"
      : label === "LOW"
      ? "bg-red-500/10 border-red-500/20"
      : "bg-amber-500/10 border-amber-500/20";

  return (
    <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded border ${bg}`}>
      <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-[9px] font-bold tabular-nums" style={{ color }}>
        {formatPct(score)}
      </span>
    </div>
  );
}

// ── Risk Label ──────────────────────────────────────────────────────────

function RiskLabel({ risk }: { risk: RiskEnvelope | undefined }) {
  if (!risk) return null;

  const color =
    risk.downside_if_wrong === "HIGH"
      ? "#EF4444"
      : risk.downside_if_wrong === "MEDIUM"
      ? "#F59E0B"
      : "#22C55E";

  return (
    <span className="text-[9px] font-bold uppercase" style={{ color }}>
      {risk.downside_if_wrong} risk
    </span>
  );
}

// ── Reversibility Indicator ─────────────────────────────────────────────

function ReversibilityDot({ level }: { level: string }) {
  const color =
    level === "HIGH"
      ? "bg-emerald-400"
      : level === "LOW"
      ? "bg-red-400"
      : "bg-amber-400";
  return (
    <div className="flex items-center gap-1">
      <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
      <span className="text-[9px] text-slate-500 uppercase">{level} Rev.</span>
    </div>
  );
}

// ── Single Card ─────────────────────────────────────────────────────────

function DecisionCard({
  card,
  confidence,
  risk,
  ownership,
  workflow,
}: {
  card: ExecutiveDecisionCard;
  confidence?: ActionConfidence;
  risk?: RiskEnvelope;
  ownership?: DecisionOwnership;
  workflow?: DecisionWorkflow;
}) {
  const borderColor =
    card.status === "CRITICAL"
      ? "border-red-500/40"
      : card.status === "SEVERE"
      ? "border-amber-500/30"
      : "border-white/[0.08]";

  const rankColor =
    card.status === "CRITICAL"
      ? "#EF4444"
      : card.status === "SEVERE"
      ? "#F59E0B"
      : "#64748B";

  return (
    <div
      className={`relative bg-[#0F1420] border ${borderColor} rounded-xl overflow-hidden hover:border-white/[0.16] transition-all duration-200`}
    >
      {/* Rank stripe */}
      <div
        className="absolute top-0 left-0 w-1 h-full"
        style={{ backgroundColor: rankColor }}
      />

      <div className="pl-4 pr-4 pt-3.5 pb-3">
        {/* Top row: rank + status + type badge */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-6 rounded-lg flex items-center justify-center text-[11px] font-bold"
              style={{ backgroundColor: `${rankColor}20`, color: rankColor }}
            >
              {card.rank}
            </div>
            <StatusBadge status={card.status} />
            <span className="px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-widest border border-blue-500/30 text-blue-400 rounded">
              {card.type}
            </span>
            <ConfidenceBadge confidence={confidence} />
          </div>
          <div className="flex items-center gap-2 text-[10px] text-slate-600">
            <RiskLabel risk={risk} />
            {ownership && (
              <span className="px-1.5 py-0.5 text-[8px] font-bold rounded border border-slate-600/40 text-slate-300">
                {ownership.owner_role}
              </span>
            )}
            {workflow && (
              <span className={`px-1.5 py-0.5 text-[8px] font-bold rounded border ${
                workflow.status === "APPROVED" ? "border-emerald-500/30 text-emerald-400" :
                workflow.status === "ESCALATED" ? "border-purple-500/30 text-purple-400" :
                workflow.status === "REJECTED" ? "border-red-500/30 text-red-400" :
                "border-amber-500/30 text-amber-400"
              }`}>
                {workflow.status}
              </span>
            )}
            <div className="flex items-center gap-1">
              <User size={10} />
              <span>{card.owner}</span>
            </div>
          </div>
        </div>

        {/* Action description */}
        <p className="text-[13px] font-medium text-slate-200 leading-snug mb-1 line-clamp-2">
          {card.action}
        </p>
        {card.action_ar && card.action_ar !== "—" && (
          <p className="text-[11px] text-slate-500 leading-snug mb-2 line-clamp-1" dir="rtl">
            {card.action_ar}
          </p>
        )}

        {/* Downside if ignored */}
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-red-500/8 border border-red-500/15 mb-2.5">
          <TrendingDown size={11} className="text-red-400 flex-shrink-0" />
          <span className="text-[10px] text-red-300/90 font-medium">
            If ignored: {card.downside_if_ignored}
          </span>
        </div>

        {/* Metrics row */}
        <div className="flex items-center gap-3 text-[10px]">
          <div className="flex items-center gap-1">
            <Clock size={10} className="text-slate-500" />
            <span className="text-slate-500">Deadline</span>
            <span className="font-bold text-amber-400 tabular-nums">
              {formatHours(card.deadline_hours)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-slate-500">Benefit</span>
            <span className="font-bold text-emerald-400 tabular-nums">
              {formatUSD(card.loss_avoided_usd)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-slate-500">Cost</span>
            <span className="font-bold text-red-400 tabular-nums">
              {formatUSD(card.cost_usd)}
            </span>
          </div>
          <ReversibilityDot level={card.reversibility} />
        </div>
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

interface ExecutiveDecisionStripProps {
  cards: ExecutiveDecisionCard[];
  actionConfidence?: ActionConfidence[];
  riskProfile?: RiskEnvelope;
  ownerships?: DecisionOwnership[];
  workflows?: DecisionWorkflow[];
}

export function ExecutiveDecisionStrip({
  cards,
  actionConfidence,
  riskProfile,
  ownerships,
  workflows,
}: ExecutiveDecisionStripProps) {
  if (cards.length === 0) return null;

  const criticalCount = cards.filter((c) => c.status === "CRITICAL").length;

  return (
    <div className="bg-[#0A0E18] border-b border-white/[0.06]">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-2.5 border-b border-white/[0.04]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            Executive Decisions
          </h2>
          <span className="text-[10px] text-slate-600 tabular-nums">
            Top {cards.length} by priority
          </span>
        </div>
        {criticalCount > 0 && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-red-500/10 border border-red-500/20">
            <Zap size={10} className="text-red-500" />
            <span className="text-[10px] font-bold text-red-400">
              {criticalCount} critical
            </span>
          </div>
        )}
      </div>

      {/* Decision cards — 3-column grid */}
      <div className="px-6 py-3">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {cards.map((card) => {
            // Match confidence by looking for the action in the confidence array
            const conf = actionConfidence?.find(
              (c) => c.action_id === card.action?.substring(0, 30) // best-effort match
            ) ?? actionConfidence?.[card.rank - 1]; // fallback to positional match
            const own = ownerships?.[card.rank - 1];
            const wf = workflows?.[card.rank - 1];
            return (
              <DecisionCard
                key={`exec-${card.rank}`}
                card={card}
                confidence={conf}
                risk={riskProfile}
                ownership={own}
                workflow={wf}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
