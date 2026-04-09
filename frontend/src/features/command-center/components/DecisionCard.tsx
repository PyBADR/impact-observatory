"use client";

/**
 * DecisionCard — Ranked decision action card for the Decision Panel
 *
 * Shows: rank, action text, urgency/value bars, loss avoided, cost,
 * confidence, owner, sector tag. Executive-grade decision terminal.
 */

import React, { useState } from "react";
import {
  ChevronRight,
  DollarSign,
  Target,
  User,
  BarChart3,
  ShieldCheck,
} from "lucide-react";
import { formatUSD, formatPct, classificationColor, stressToClassification } from "../lib/format";
import type { DecisionActionV2 } from "@/types/observatory";

// ── Safe accessors (never NaN, never undefined) ──────────────────────

function safeNum(v: unknown, fallback: number = 0): number {
  if (v === null || v === undefined) return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function safeStr(v: unknown, fallback: string = "—"): string {
  if (v === null || v === undefined) return fallback;
  const s = String(v).trim();
  return s.length === 0 ? fallback : s;
}

// ── Types ─────────────────────────────────────────────────────────────

interface DecisionCardProps {
  action: DecisionActionV2;
  rank: number;
  onExecute?: (id: string) => void;
  isExecuting?: boolean;
  /** Disables execute button in mock/demo mode */
  isLive?: boolean;
}

// ── Metric Bar ────────────────────────────────────────────────────────

function MetricBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">
          {label}
        </span>
        <span className="text-[11px] font-bold tabular-nums text-slate-300">
          {Math.round(value)}
        </span>
      </div>
      <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ── Sector Tag ────────────────────────────────────────────────────────

const SECTOR_COLORS: Record<string, string> = {
  energy: "border-amber-500/40 text-amber-400",
  maritime: "border-blue-500/40 text-blue-400",
  insurance: "border-indigo-500/40 text-indigo-400",
  finance: "border-emerald-500/40 text-emerald-400",
  banking: "border-teal-500/40 text-teal-400",
  fintech: "border-violet-500/40 text-violet-400",
};

function SectorTag({ sector }: { sector: string }) {
  const style =
    SECTOR_COLORS[sector.toLowerCase()] ??
    "border-slate-500/40 text-slate-400";
  return (
    <span
      className={`px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest border rounded ${style}`}
    >
      {sector}
    </span>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function DecisionCard({
  action,
  rank,
  onExecute,
  isExecuting = false,
  isLive = false,
}: DecisionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [confirming, setConfirming] = useState(false);

  // ── Safe-read all fields once (never NaN / undefined in render) ──
  const urgency = safeNum(action.urgency);
  const value = safeNum(action.value);
  const priority = safeNum(action.priority);
  const lossAvoided = safeNum(action.loss_avoided_usd);
  const costUsd = safeNum(action.cost_usd);
  const confidence = safeNum(action.confidence);
  const regRisk = safeNum(action.regulatory_risk);
  const sector = safeStr(action.sector, "general");
  const owner = safeStr(action.owner, "Unassigned");
  const actionText = safeStr(action.action, "No action description");
  const actionAr = safeStr(action.action_ar, "");
  const actionId = safeStr(action.id, `action_${rank}`);

  const classification = stressToClassification(urgency / 100);
  const accentColor = classificationColor(classification);

  return (
    <div
      className="group bg-[#0F1420] border border-white/[0.06] rounded-xl overflow-hidden hover:border-white/[0.12] transition-all duration-200"
      style={{ borderLeftWidth: "3px", borderLeftColor: accentColor }}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 px-4 py-3.5 text-left"
      >
        {/* Rank */}
        <div
          className="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center mt-0.5"
          style={{ backgroundColor: `${accentColor}20`, color: accentColor }}
        >
          <span className="text-xs font-bold tabular-nums">{rank}</span>
        </div>

        {/* Action text + reasoning preview */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <SectorTag sector={sector} />
            <span className="text-[10px] text-slate-600">
              <User size={10} className="inline mr-0.5" />
              {owner}
            </span>
          </div>
          <p className="text-[13px] font-medium text-slate-200 leading-snug">
            {actionText}
          </p>
          {/* Reasoning line — shows Arabic action text as rationale proxy when available */}
          {actionAr.length > 0 && actionAr !== "—" && (
            <p className="text-[11px] text-slate-500 leading-snug mt-1 line-clamp-2" dir="rtl">
              {actionAr}
            </p>
          )}
        </div>

        {/* Expand chevron */}
        <ChevronRight
          size={16}
          className={`text-slate-600 transition-transform flex-shrink-0 mt-1 ${
            expanded ? "rotate-90" : ""
          }`}
        />
      </button>

      {/* Metrics strip — always visible */}
      <div className="flex items-center gap-4 px-4 pb-3">
        <MetricBar label="Urgency" value={urgency} max={100} color="#EF4444" />
        <MetricBar label="Value" value={value} max={100} color="#22C55E" />
        <MetricBar label="Priority" value={priority} max={100} color="#3B82F6" />
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-white/[0.04] bg-white/[0.02] px-4 py-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">
                Loss Avoided
              </p>
              <p className="text-sm font-bold text-emerald-400 tabular-nums">
                <DollarSign size={12} className="inline" />
                {formatUSD(lossAvoided).replace("$", "")}
              </p>
            </div>
            <div>
              <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">
                Est. Cost
              </p>
              <p className="text-sm font-bold text-red-400 tabular-nums">
                <DollarSign size={12} className="inline" />
                {formatUSD(costUsd).replace("$", "")}
              </p>
            </div>
            <div>
              <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">
                Confidence
              </p>
              <p className="text-sm font-bold text-slate-300 tabular-nums">
                <ShieldCheck size={12} className="inline mr-0.5" />
                {formatPct(confidence)}
              </p>
            </div>
            <div>
              <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">
                Reg. Risk
              </p>
              <p className="text-sm font-bold text-amber-400 tabular-nums">
                <BarChart3 size={12} className="inline mr-0.5" />
                {formatPct(regRisk)}
              </p>
            </div>
          </div>

          {/* ROI indicator */}
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target size={12} className="text-slate-600" />
              <span className="text-[10px] text-slate-500">
                Net Value:{" "}
                <span className="font-bold text-emerald-400">
                  {formatUSD(lossAvoided - costUsd)}
                </span>
              </span>
            </div>
            {onExecute && !confirming && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (!isLive) return; // Block in mock mode
                  setConfirming(true);
                }}
                disabled={isExecuting || !isLive}
                title={!isLive ? "Connect to live backend to enable actions" : undefined}
                className="px-3 py-1.5 text-[11px] font-semibold rounded-md bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {isExecuting ? "Submitting..." : !isLive ? "Review (demo)" : "Submit for Review"}
              </button>
            )}
            {confirming && (
              <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                <span className="text-[10px] text-amber-400">Confirm?</span>
                <button
                  onClick={() => { onExecute!(actionId); setConfirming(false); }}
                  className="px-2 py-1 text-[10px] font-semibold rounded bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
                >
                  Yes
                </button>
                <button
                  onClick={() => setConfirming(false)}
                  className="px-2 py-1 text-[10px] font-semibold rounded bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
                >
                  No
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Decision Panel (container for multiple cards) ─────────────────────

interface DecisionPanelProps {
  actions: DecisionActionV2[];
  onExecute?: (id: string) => void;
  /** Pass true when connected to live backend — enables action execution */
  isLive?: boolean;
}

export function DecisionPanel({ actions, onExecute, isLive = false }: DecisionPanelProps) {
  const sorted = [...actions].sort((a, b) => safeNum(b.priority) - safeNum(a.priority));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Decision Actions
        </h2>
        <span className="text-[10px] text-slate-600 tabular-nums">
          {actions.length} actions — ranked by priority
        </span>
      </div>
      {actions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center px-6">
            <p className="text-xs text-slate-500 mb-1">No actions generated</p>
            <p className="text-[10px] text-slate-700">
              Decision actions populate after the sector engine completes.
            </p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {sorted.map((action, i) => (
            <DecisionCard
              key={action.id}
              action={action}
              rank={i + 1}
              onExecute={onExecute}
              isLive={isLive}
            />
          ))}
        </div>
      )}
    </div>
  );
}
