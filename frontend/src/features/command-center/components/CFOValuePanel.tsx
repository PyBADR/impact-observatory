"use client";

/**
 * CFO Value Panel — Phase 4 Decision Value Visualization
 *
 * Renders CFO-grade value reporting:
 *   1. Portfolio Summary Strip: total value, decisions, success rate, ROI
 *   2. Per-Decision Value Cards: expected vs actual, value created, effectiveness
 *   3. Portfolio Aggregation: best/worst decisions, net delta
 *
 * Data contract: DecisionValuePayload from backend stages 29-32.
 * Pure display component — no side effects, no API calls.
 */

import React, { useMemo, useState } from "react";
import type { DecisionValuePayload } from "@/types/observatory";

// ── Helpers ──────────────────────────────────────────────────────────

function fmtUsd(v: number): string {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

// ── Classification Colors ────────────────────────────────────────────

const EFFECTIVENESS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  SUCCESS: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/20" },
  NEUTRAL: { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/20" },
  FAILURE: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/20" },
};

const ATTRIBUTION_COLORS: Record<string, { bg: string; text: string }> = {
  DIRECT: { bg: "bg-blue-500/10", text: "text-blue-400" },
  PARTIAL: { bg: "bg-amber-500/10", text: "text-amber-400" },
  LOW_CONFIDENCE: { bg: "bg-slate-500/10", text: "text-slate-500" },
};

// ── Sub-Components ───────────────────────────────────────────────────

function PortfolioStrip({ portfolio }: { portfolio: DecisionValuePayload["portfolio_value"] }) {
  const deltaColor = portfolio.net_delta >= 0 ? "text-emerald-400" : "text-red-400";
  const deltaPrefix = portfolio.net_delta >= 0 ? "+" : "";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
      <MetricCard label="Value Created" value={`$${fmtUsd(portfolio.total_value_created)}`} accent="text-emerald-400" />
      <MetricCard label="Decisions" value={String(portfolio.total_decisions)} accent="text-blue-400" />
      <MetricCard label="Success Rate" value={pct(portfolio.success_rate)} accent="text-emerald-400" />
      <MetricCard label="Failures" value={String(portfolio.failure_count)} accent={portfolio.failure_count > 0 ? "text-red-400" : "text-slate-500"} />
      <MetricCard label="ROI Ratio" value={portfolio.roi_ratio.toFixed(2) + "x"} accent="text-blue-400" />
      <MetricCard label="Net Delta" value={`${deltaPrefix}$${fmtUsd(portfolio.net_delta)}`} accent={deltaColor} />
      <MetricCard label="Avg Effectiveness" value={pct(portfolio.avg_effectiveness_score)} accent="text-slate-300" />
    </div>
  );
}

function MetricCard({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div className="rounded-lg bg-[#0D1117] border border-slate-700/50 px-3 py-2.5">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-sm font-semibold ${accent}`}>{value}</p>
    </div>
  );
}

function DecisionValueCard({
  decisionId,
  expected,
  actual,
  delta,
  valueCreated,
  attributionType,
  attributionConfidence,
  score,
  classification,
}: {
  decisionId: string;
  expected: number;
  actual: number;
  delta: number;
  valueCreated: number;
  attributionType: string;
  attributionConfidence: number;
  score: number;
  classification: string;
}) {
  const eff = EFFECTIVENESS_COLORS[classification] ?? EFFECTIVENESS_COLORS.NEUTRAL;
  const attr = ATTRIBUTION_COLORS[attributionType] ?? ATTRIBUTION_COLORS.LOW_CONFIDENCE;
  const deltaColor = delta >= 0 ? "text-emerald-400" : "text-red-400";
  const deltaPrefix = delta >= 0 ? "+" : "";

  // Progress bar width for effectiveness score (0-1)
  const barWidth = Math.max(2, Math.min(100, score * 100));

  return (
    <div className={`rounded-lg border ${eff.border} bg-[#0D1117] p-3`}>
      {/* Header row */}
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-[11px] text-slate-400 font-mono truncate max-w-[180px]" title={decisionId}>
          {decisionId}
        </p>
        <div className="flex items-center gap-2">
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase ${attr.bg} ${attr.text}`}>
            {attributionType.replace("_", " ")}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${eff.bg} ${eff.text}`}>
            {classification}
          </span>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-4 gap-2 mb-2">
        <div>
          <p className="text-[9px] text-slate-600 uppercase">Expected</p>
          <p className="text-xs text-slate-300 font-medium">${fmtUsd(expected)}</p>
        </div>
        <div>
          <p className="text-[9px] text-slate-600 uppercase">Actual</p>
          <p className="text-xs text-slate-300 font-medium">${fmtUsd(actual)}</p>
        </div>
        <div>
          <p className="text-[9px] text-slate-600 uppercase">Delta</p>
          <p className={`text-xs font-medium ${deltaColor}`}>{deltaPrefix}${fmtUsd(delta)}</p>
        </div>
        <div>
          <p className="text-[9px] text-slate-600 uppercase">Value</p>
          <p className={`text-xs font-medium ${valueCreated >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            ${fmtUsd(valueCreated)}
          </p>
        </div>
      </div>

      {/* Effectiveness bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${classification === "SUCCESS" ? "bg-emerald-500" : classification === "FAILURE" ? "bg-red-500" : "bg-slate-500"}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
        <span className="text-[10px] text-slate-500 w-8 text-right">{pct(score)}</span>
        <span className="text-[10px] text-slate-600">conf {pct(attributionConfidence)}</span>
      </div>
    </div>
  );
}

// ── Main Panel ───────────────────────────────────────────────────────

interface CFOValuePanelProps {
  value: DecisionValuePayload | null | undefined;
}

export function CFOValuePanel({ value }: CFOValuePanelProps) {
  const [expanded, setExpanded] = useState(false);

  // Merge per-decision data for card rendering
  const decisionCards = useMemo(() => {
    if (!value) return [];
    const { expected_actual, value_attribution, effectiveness } = value;
    return expected_actual.map((ea) => {
      const va = value_attribution.find((v) => v.decision_id === ea.decision_id);
      const eff = effectiveness.find((e) => e.decision_id === ea.decision_id);
      return {
        decisionId: ea.decision_id,
        expected: ea.expected_outcome,
        actual: ea.actual_outcome,
        delta: ea.delta,
        valueCreated: va?.value_created ?? 0,
        attributionType: va?.attribution_type ?? "LOW_CONFIDENCE",
        attributionConfidence: va?.attribution_confidence ?? 0,
        score: eff?.score ?? 0,
        classification: eff?.classification ?? "NEUTRAL",
      };
    });
  }, [value]);

  if (!value || value.expected_actual.length === 0) return null;

  const portfolio = value.portfolio_value;
  const displayCards = expanded ? decisionCards : decisionCards.slice(0, 4);

  return (
    <section className="flex-shrink-0 px-6 py-4 bg-[#0B0F1A] border-t border-slate-800/60">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 rounded-full bg-emerald-500" />
          <h2 className="text-sm font-semibold text-white tracking-tight">
            CFO Value Report
          </h2>
          <span className="text-[10px] text-slate-500 font-mono">PHASE 4</span>
        </div>
        {portfolio.best_decision_id && (
          <div className="flex items-center gap-2 text-[10px]">
            <span className="text-slate-500">Best:</span>
            <span className="text-emerald-400 font-mono truncate max-w-[120px]" title={portfolio.best_decision_id}>
              {portfolio.best_decision_id}
            </span>
            {portfolio.worst_decision_id && (
              <>
                <span className="text-slate-600 mx-1">|</span>
                <span className="text-slate-500">Worst:</span>
                <span className="text-red-400 font-mono truncate max-w-[120px]" title={portfolio.worst_decision_id}>
                  {portfolio.worst_decision_id}
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Portfolio Summary Strip */}
      <PortfolioStrip portfolio={portfolio} />

      {/* Per-Decision Cards */}
      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
        {displayCards.map((card) => (
          <DecisionValueCard key={card.decisionId} {...card} />
        ))}
      </div>

      {/* Expand / Collapse */}
      {decisionCards.length > 4 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 w-full text-center text-[11px] text-slate-500 hover:text-slate-300 transition-colors py-1"
        >
          {expanded ? `Collapse (showing ${decisionCards.length})` : `Show all ${decisionCards.length} decisions`}
        </button>
      )}
    </section>
  );
}
