"use client";

/**
 * DecisionPriorities — Primary decision surface for the Command Center
 *
 * This is the MAIN content zone of the dashboard. Decisions are visible
 * without scrolling. Each card shows:
 *   - Action description with rank and sector
 *   - Cost vs Benefit bar (prominent, always visible)
 *   - Loss-inducing flag (red warning when cost > benefit)
 *   - Urgency timeline (time-critical-days countdown)
 *   - Execute CTA with confirmation gate
 *
 * Layout: Full-width horizontal card grid (1-3 cards above fold).
 * No expandable sections — key metrics are always visible.
 */

import React, { useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  DollarSign,
  ShieldAlert,
  ShieldCheck,
  Target,
  TrendingDown,
  TrendingUp,
  User,
  Zap,
} from "lucide-react";
import {
  formatUSD,
  formatPct,
  classificationColor,
  stressToClassification,
  safeNum,
  safeStr,
} from "../lib/format";
import type { DecisionActionV2 } from "@/types/observatory";

// ── Safe accessors ──────────────────────────────────────────────────

function isLossInducing(action: DecisionActionV2): boolean {
  const cost = safeNum(action.cost_usd);
  const benefit = safeNum(action.loss_avoided_usd);
  return cost > benefit && cost > 0;
}

function netValue(action: DecisionActionV2): number {
  return safeNum(action.loss_avoided_usd) - safeNum(action.cost_usd);
}

// ── Urgency Badge ───────────────────────────────────────────────────

function UrgencyBadge({ urgency }: { urgency: number }) {
  const pct = Math.min(urgency, 100);
  if (pct >= 80) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-red-500/15 border border-red-500/30 text-red-400 text-[10px] font-bold uppercase tracking-wider">
        <Zap size={9} /> Immediate
      </span>
    );
  }
  if (pct >= 50) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
        <Clock size={9} /> Urgent
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-500/15 border border-slate-500/30 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
      <Clock size={9} /> Monitor
    </span>
  );
}

// ── Sector Colors ───────────────────────────────────────────────────

const SECTOR_ACCENT: Record<string, string> = {
  energy: "#F59E0B",
  maritime: "#3B82F6",
  insurance: "#6366F1",
  finance: "#10B981",
  banking: "#14B8A6",
  fintech: "#8B5CF6",
  logistics: "#06B6D4",
  trade: "#0D9488",
};

// ── Cost vs Benefit Bar ──────────────────────────────────────────────

function CostBenefitBar({
  lossAvoided,
  cost,
}: {
  lossAvoided: number;
  cost: number;
}) {
  const maxVal = Math.max(lossAvoided, cost, 1);
  const benefitPct = (lossAvoided / maxVal) * 100;
  const costPct = (cost / maxVal) * 100;
  const net = lossAvoided - cost;
  const isNeg = net < 0;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-slate-500 uppercase tracking-wider font-semibold">
          Cost vs Benefit
        </span>
        <span
          className={`font-bold tabular-nums ${isNeg ? "text-red-400" : "text-emerald-400"}`}
        >
          Net: {formatUSD(net)}
        </span>
      </div>

      {/* Benefit bar */}
      <div className="flex items-center gap-2">
        <span className="text-[9px] text-emerald-500 w-[52px] text-right font-medium">
          Benefit
        </span>
        <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-emerald-500/80 transition-all duration-500"
            style={{ width: `${benefitPct}%` }}
          />
        </div>
        <span className="text-[10px] text-emerald-400 font-bold tabular-nums w-[72px]">
          {formatUSD(lossAvoided)}
        </span>
      </div>

      {/* Cost bar */}
      <div className="flex items-center gap-2">
        <span className="text-[9px] text-red-400 w-[52px] text-right font-medium">
          Cost
        </span>
        <div className="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-red-500/80 transition-all duration-500"
            style={{ width: `${costPct}%` }}
          />
        </div>
        <span className="text-[10px] text-red-400 font-bold tabular-nums w-[72px]">
          {formatUSD(cost)}
        </span>
      </div>
    </div>
  );
}

// ── Loss-Inducing Warning ────────────────────────────────────────────

function LossFlag() {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-red-500/10 border border-red-500/25">
      <ShieldAlert size={12} className="text-red-500 flex-shrink-0" />
      <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider">
        Loss-Inducing — Cost Exceeds Benefit
      </span>
    </div>
  );
}

// ── Single Priority Card ─────────────────────────────────────────────

function PriorityCard({
  action,
  rank,
  onExecute,
  isLive,
}: {
  action: DecisionActionV2;
  rank: number;
  onExecute?: (id: string) => void;
  isLive: boolean;
}) {
  const [confirming, setConfirming] = useState(false);

  const urgency = safeNum(action.urgency);
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
  // time_critical_days may come from extended API responses
  const timeCriticalDays = safeNum((action as unknown as Record<string, unknown>).time_critical_days, 0);

  const isLoss = isLossInducing(action);
  const sectorColor = SECTOR_ACCENT[sector.toLowerCase()] ?? "#94A3B8";
  const classification = stressToClassification(urgency / 100);
  const accentColor = classificationColor(classification);

  return (
    <div
      className={`relative bg-[#0F1420] border rounded-xl overflow-hidden transition-all duration-200 ${
        isLoss
          ? "border-red-500/30 hover:border-red-500/50"
          : "border-white/[0.08] hover:border-white/[0.16]"
      }`}
    >
      {/* Rank stripe */}
      <div
        className="absolute top-0 left-0 w-1 h-full"
        style={{ backgroundColor: accentColor }}
      />

      <div className="pl-4 pr-4 pt-4 pb-3">
        {/* Top row: rank + sector + urgency + owner */}
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold"
              style={{
                backgroundColor: `${accentColor}20`,
                color: accentColor,
              }}
            >
              {rank}
            </div>
            <span
              className="px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest border rounded"
              style={{
                borderColor: `${sectorColor}60`,
                color: sectorColor,
              }}
            >
              {sector}
            </span>
            <UrgencyBadge urgency={urgency} />
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-600">
            <User size={10} />
            <span>{owner}</span>
          </div>
        </div>

        {/* Action description */}
        <p className="text-[13px] font-medium text-slate-200 leading-snug mb-1">
          {actionText}
        </p>
        {actionAr && actionAr !== "\u2014" && (
          <p
            className="text-[11px] text-slate-500 leading-snug mb-3 line-clamp-1"
            dir="rtl"
          >
            {actionAr}
          </p>
        )}

        {/* Loss-inducing warning */}
        {isLoss && (
          <div className="mb-3">
            <LossFlag />
          </div>
        )}

        {/* Cost vs Benefit — always visible, prominent */}
        <div className="mb-3">
          <CostBenefitBar lossAvoided={lossAvoided} cost={costUsd} />
        </div>

        {/* Metrics row: confidence, regulatory risk, time-critical */}
        <div className="flex items-center gap-4 mb-3">
          <div className="flex items-center gap-1">
            <ShieldCheck size={11} className="text-slate-500" />
            <span className="text-[10px] text-slate-500">Confidence</span>
            <span
              className="text-[11px] font-bold tabular-nums"
              style={{
                color:
                  confidence >= 0.8
                    ? "#22C55E"
                    : confidence >= 0.6
                    ? "#EAB308"
                    : "#EF4444",
              }}
            >
              {formatPct(confidence)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <AlertTriangle size={11} className="text-slate-500" />
            <span className="text-[10px] text-slate-500">Reg. Risk</span>
            <span
              className="text-[11px] font-bold tabular-nums"
              style={{
                color:
                  regRisk >= 0.7
                    ? "#EF4444"
                    : regRisk >= 0.4
                    ? "#F59E0B"
                    : "#22C55E",
              }}
            >
              {formatPct(regRisk)}
            </span>
          </div>
          {timeCriticalDays > 0 && (
            <div className="flex items-center gap-1">
              <Clock size={11} className="text-slate-500" />
              <span className="text-[10px] text-slate-500">Deadline</span>
              <span className="text-[11px] font-bold tabular-nums text-amber-400">
                {timeCriticalDays}d
              </span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Target size={11} className="text-slate-500" />
            <span className="text-[10px] text-slate-500">Priority</span>
            <span className="text-[11px] font-bold tabular-nums text-blue-400">
              {Math.round(priority)}
            </span>
          </div>
        </div>

        {/* Action CTA */}
        <div className="flex items-center justify-between pt-2 border-t border-white/[0.04]">
          <div className="flex items-center gap-1.5">
            {isLoss ? (
              <TrendingDown size={12} className="text-red-400" />
            ) : (
              <TrendingUp size={12} className="text-emerald-400" />
            )}
            <span
              className={`text-[11px] font-bold tabular-nums ${isLoss ? "text-red-400" : "text-emerald-400"}`}
            >
              Net: {formatUSD(netValue(action))}
            </span>
          </div>

          {onExecute && !confirming && (
            <button
              onClick={() => {
                if (!isLive) return;
                setConfirming(true);
              }}
              disabled={!isLive}
              title={
                !isLive
                  ? "Connect to live backend to enable actions"
                  : undefined
              }
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 text-[11px] font-semibold rounded-lg transition-colors ${
                isLoss
                  ? "bg-red-600/20 text-red-300 hover:bg-red-600/30 border border-red-500/30"
                  : "bg-blue-600 text-white hover:bg-blue-500"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {!isLive ? (
                "Review (demo)"
              ) : isLoss ? (
                <>
                  <ShieldAlert size={11} /> Review with Caution
                </>
              ) : (
                <>
                  Submit for Review <ArrowRight size={11} />
                </>
              )}
            </button>
          )}
          {confirming && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-amber-400">
                {isLoss ? "This action is loss-inducing. Confirm?" : "Confirm?"}
              </span>
              <button
                onClick={() => {
                  onExecute!(actionId);
                  setConfirming(false);
                }}
                className="px-2.5 py-1 text-[10px] font-semibold rounded-md bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
              >
                Yes
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="px-2.5 py-1 text-[10px] font-semibold rounded-md bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
              >
                No
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────

interface DecisionPrioritiesProps {
  actions: DecisionActionV2[];
  onExecute?: (id: string) => void;
  isLive?: boolean;
}

export function DecisionPriorities({
  actions,
  onExecute,
  isLive = false,
}: DecisionPrioritiesProps) {
  const sorted = [...actions].sort(
    (a, b) => safeNum(b.priority) - safeNum(a.priority)
  );

  // Show top 3 above fold, rest collapsible
  const topActions = sorted.slice(0, 3);
  const remainingActions = sorted.slice(3);
  const [showAll, setShowAll] = useState(false);

  if (actions.length === 0) {
    return (
      <div className="bg-[#0A0E18] border-t border-b border-white/[0.06] px-6 py-6">
        <div className="text-center">
          <p className="text-xs text-slate-500">
            No decision actions generated for this scenario.
          </p>
        </div>
      </div>
    );
  }

  const lossCount = actions.filter(isLossInducing).length;

  return (
    <div className="bg-[#0A0E18] border-t border-white/[0.06]">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/[0.04]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            Decision Priorities
          </h2>
          <span className="text-[10px] text-slate-600 tabular-nums">
            {actions.length} actions ranked by priority
          </span>
        </div>
        <div className="flex items-center gap-3">
          {lossCount > 0 && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-red-500/10 border border-red-500/20">
              <ShieldAlert size={10} className="text-red-500" />
              <span className="text-[10px] font-bold text-red-400">
                {lossCount} loss-inducing
              </span>
            </div>
          )}
          {!isLive && (
            <span className="text-[10px] text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              Demo Mode
            </span>
          )}
        </div>
      </div>

      {/* Top priority cards — full-width grid */}
      <div className="px-6 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {topActions.map((action, i) => (
            <PriorityCard
              key={action.id}
              action={action}
              rank={i + 1}
              onExecute={onExecute}
              isLive={isLive}
            />
          ))}
        </div>

        {/* Remaining actions (collapsible) */}
        {remainingActions.length > 0 && (
          <div className="mt-3">
            {!showAll ? (
              <button
                onClick={() => setShowAll(true)}
                className="w-full py-2 text-[11px] text-slate-500 hover:text-slate-400 border border-dashed border-white/[0.06] rounded-lg hover:border-white/[0.12] transition-all"
              >
                +{remainingActions.length} more actions
              </button>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
                {remainingActions.map((action, i) => (
                  <PriorityCard
                    key={action.id}
                    action={action}
                    rank={topActions.length + i + 1}
                    onExecute={onExecute}
                    isLive={isLive}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
