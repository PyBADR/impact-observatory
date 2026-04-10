"use client";

/**
 * Decision Trust Panel — compact block rendering all 5 trust dimensions:
 *   - Model Dependency (data completeness, signal reliability, sensitivity)
 *   - Validation Requirement (required flag, reason, type)
 *   - Confidence Breakdown (human-readable drivers)
 *   - Risk Profile (downside, reversibility, time sensitivity)
 *
 * Not a full zone — sits as a compact insight panel between decision blocks.
 */

import React from "react";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Database,
  Radio,
  Activity,
  Clock,
  ArrowDownRight,
  RotateCcw,
  Info,
} from "lucide-react";
import { formatPct, safeNum, safeStr } from "../lib/format";
import type { DecisionTrustPayload } from "@/types/observatory";

// ── Severity tier color for labels ──────────────────────────────────────

function tierColor(tier: string): string {
  switch (tier.toUpperCase()) {
    case "HIGH":
    case "CRITICAL":
      return "#EF4444";
    case "MEDIUM":
      return "#F59E0B";
    case "LOW":
    case "NONE":
      return "#22C55E";
    default:
      return "#64748B";
  }
}

function tierBg(tier: string): string {
  switch (tier.toUpperCase()) {
    case "HIGH":
    case "CRITICAL":
      return "bg-red-500/10 border-red-500/20";
    case "MEDIUM":
      return "bg-amber-500/10 border-amber-500/20";
    case "LOW":
    case "NONE":
      return "bg-emerald-500/10 border-emerald-500/20";
    default:
      return "bg-slate-500/10 border-slate-500/20";
  }
}

// ── Metric Pill ─────────────────────────────────────────────────────────

function MetricPill({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <Icon size={11} className="text-slate-500" />
      <span className="text-[10px] text-slate-500">{label}</span>
      <span
        className="text-[10px] font-bold tabular-nums"
        style={{ color: color ?? "#CBD5E1" }}
      >
        {value}
      </span>
    </div>
  );
}

// ── Label Badge ─────────────────────────────────────────────────────────

function LabelBadge({ label }: { label: string }) {
  const color = tierColor(label);
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${tierBg(label)}`}
      style={{ color }}
    >
      {label}
    </span>
  );
}

// ── Validation Alert ────────────────────────────────────────────────────

function ValidationAlert({
  validation,
}: {
  validation: DecisionTrustPayload["validation"];
}) {
  if (!validation?.required) {
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/8 border border-emerald-500/15">
        <ShieldCheck size={12} className="text-emerald-400 flex-shrink-0" />
        <span className="text-[10px] text-emerald-300/90">
          No validation required — metrics within acceptable bounds
        </span>
      </div>
    );
  }

  const typeColor = validation.validation_type === "REGULATORY"
    ? "text-red-400"
    : validation.validation_type === "RISK"
    ? "text-amber-400"
    : "text-blue-400";

  return (
    <div className="px-2.5 py-2 rounded-lg bg-amber-500/8 border border-amber-500/20">
      <div className="flex items-center gap-1.5 mb-1">
        <ShieldAlert size={12} className="text-amber-400 flex-shrink-0" />
        <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
          Validation Required
        </span>
        <span className={`text-[9px] font-bold uppercase ${typeColor}`}>
          ({validation.validation_type})
        </span>
      </div>
      <p className="text-[10px] text-slate-400 leading-relaxed pl-5">
        {validation.reason}
      </p>
    </div>
  );
}

// ── Confidence Drivers ──────────────────────────────────────────────────

function ConfidenceDrivers({
  drivers,
}: {
  drivers: string[];
}) {
  if (!drivers || drivers.length === 0) return null;

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1 text-[9px] text-slate-500 uppercase tracking-wider font-semibold">
        <Info size={9} />
        <span>Confidence Drivers</span>
      </div>
      <div className="space-y-0.5 pl-3">
        {drivers.map((d, i) => (
          <p key={i} className="text-[10px] text-slate-400 leading-snug">
            • {d}
          </p>
        ))}
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────

interface DecisionTrustPanelProps {
  trust: DecisionTrustPayload | null | undefined;
}

export function DecisionTrustPanel({ trust }: DecisionTrustPanelProps) {
  if (!trust) return null;

  const dep = trust.model_dependency;
  const risk = trust.risk_profile;
  const breakdown = trust.confidence_breakdown;

  return (
    <div className="bg-[#0A0E18] border-b border-white/[0.06]">
      {/* Section header */}
      <div className="flex items-center justify-between px-6 py-2.5 border-b border-white/[0.04]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            Decision Trust
          </h2>
          <span className="text-[10px] text-slate-600">
            Model dependency · Validation · Risk envelope
          </span>
        </div>
        {risk && (
          <div className="flex items-center gap-2">
            <LabelBadge label={risk.downside_if_wrong} />
            <LabelBadge label={risk.time_sensitivity} />
          </div>
        )}
      </div>

      <div className="px-6 py-3">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {/* Column 1: Model Dependency */}
          <div className="bg-[#0F1420] border border-white/[0.08] rounded-xl p-3">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              Model Dependency
            </h4>
            <div className="space-y-2">
              <MetricPill
                label="Data Coverage"
                value={formatPct(safeNum(dep?.data_completeness))}
                icon={Database}
                color={safeNum(dep?.data_completeness) >= 0.70 ? "#22C55E" : safeNum(dep?.data_completeness) >= 0.50 ? "#F59E0B" : "#EF4444"}
              />
              <MetricPill
                label="Signal Reliability"
                value={formatPct(safeNum(dep?.signal_reliability))}
                icon={Radio}
                color={safeNum(dep?.signal_reliability) >= 0.70 ? "#22C55E" : "#F59E0B"}
              />
              <div className="flex items-center gap-1.5">
                <Activity size={11} className="text-slate-500" />
                <span className="text-[10px] text-slate-500">Sensitivity</span>
                <LabelBadge label={safeStr(dep?.assumption_sensitivity, "MEDIUM")} />
              </div>
            </div>
          </div>

          {/* Column 2: Risk Envelope */}
          <div className="bg-[#0F1420] border border-white/[0.08] rounded-xl p-3">
            <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              Risk Envelope
            </h4>
            <div className="space-y-2">
              <div className="flex items-center gap-1.5">
                <ArrowDownRight size={11} className="text-slate-500" />
                <span className="text-[10px] text-slate-500">Downside</span>
                <LabelBadge label={safeStr(risk?.downside_if_wrong, "MEDIUM")} />
              </div>
              <div className="flex items-center gap-1.5">
                <RotateCcw size={11} className="text-slate-500" />
                <span className="text-[10px] text-slate-500">Reversibility</span>
                <LabelBadge label={safeStr(risk?.reversibility, "MEDIUM")} />
              </div>
              <div className="flex items-center gap-1.5">
                <Clock size={11} className="text-slate-500" />
                <span className="text-[10px] text-slate-500">Time Sensitivity</span>
                <LabelBadge label={safeStr(risk?.time_sensitivity, "MEDIUM")} />
              </div>
            </div>
          </div>

          {/* Column 3: Confidence Breakdown */}
          <div className="bg-[#0F1420] border border-white/[0.08] rounded-xl p-3">
            <ConfidenceDrivers drivers={breakdown?.drivers ?? []} />
          </div>
        </div>

        {/* Validation alert — full width below */}
        <div className="mt-3">
          <ValidationAlert validation={trust.validation} />
        </div>
      </div>
    </div>
  );
}
