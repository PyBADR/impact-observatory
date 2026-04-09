"use client";

/**
 * TrustStrip — Compact horizontal trust and audit layer
 *
 * Sits between Decision Priorities and Operational Detail.
 * Displays confidence, audit hash, model version, data sources,
 * pipeline completion status, and warnings in a single scannable row.
 *
 * Purpose: Build executive trust in the system output before
 * the user drills into operational detail below.
 */

import React from "react";
import {
  CheckCircle2,
  Database,
  Fingerprint,
  ShieldCheck,
  AlertCircle,
  Layers,
} from "lucide-react";
import { safeNum, safeStr, safeArr, formatPct } from "../lib/format";
import type { CommandCenterTrust } from "../lib/command-store";

// ── Types ─────────────────────────────────────────────────────────────

interface TrustStripProps {
  trust: CommandCenterTrust | null;
  confidence: number;
  methodology?: string;
  narrativeEn?: string;
  warnings?: string[];
}

// ── Trust KPI ────────────────────────────────────────────────────────

function TrustKPI({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="text-slate-500 flex-shrink-0">{icon}</div>
      <span className="text-[10px] text-slate-600 uppercase tracking-wider">
        {label}
      </span>
      <span
        className="text-[11px] font-bold tabular-nums"
        style={{ color: color ?? "#CBD5E1" }}
      >
        {value}
      </span>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function TrustStrip({
  trust,
  confidence,
  methodology,
  narrativeEn,
  warnings,
}: TrustStripProps) {
  const _confidence = safeNum(confidence);
  const _warnings = safeArr<string>(warnings);
  const _stagesCompleted = trust ? safeArr<string>(trust.stagesCompleted) : [];
  const _modelVersion = trust ? safeStr(trust.modelVersion, "—") : "—";
  const _auditHash = trust ? safeStr(trust.auditHash, "—") : "—";
  const _dataSources = trust ? safeArr<string>(trust.dataSources) : [];
  const _methodology = safeStr(methodology, "");

  const confColor =
    _confidence >= 0.8
      ? "#22C55E"
      : _confidence >= 0.6
      ? "#EAB308"
      : "#EF4444";

  return (
    <div className="bg-[#080C14] border-t border-b border-white/[0.06]">
      {/* Main trust row */}
      <div className="flex items-center justify-between px-6 py-2.5 gap-6 overflow-x-auto">
        {/* Left: trust metrics */}
        <div className="flex items-center gap-5 flex-shrink-0">
          <TrustKPI
            icon={<ShieldCheck size={12} />}
            label="Confidence"
            value={formatPct(_confidence)}
            color={confColor}
          />
          <TrustKPI
            icon={<Layers size={12} />}
            label="Pipeline"
            value={`${_stagesCompleted.length}/9 stages`}
            color={_stagesCompleted.length >= 9 ? "#22C55E" : "#94A3B8"}
          />
          <TrustKPI
            icon={<Database size={12} />}
            label="Model"
            value={`v${_modelVersion}`}
          />
          {_dataSources.length > 0 && (
            <div className="flex items-center gap-1.5">
              <Database size={10} className="text-slate-600" />
              <span className="text-[10px] text-slate-600">Sources:</span>
              <div className="flex items-center gap-1">
                {_dataSources.slice(0, 3).map((src) => (
                  <span
                    key={src}
                    className="px-1.5 py-0.5 text-[9px] text-slate-500 bg-white/[0.03] border border-white/[0.06] rounded font-medium"
                  >
                    {src}
                  </span>
                ))}
                {_dataSources.length > 3 && (
                  <span className="text-[9px] text-slate-600">
                    +{_dataSources.length - 3}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: audit hash + warnings count */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {_warnings.length > 0 && (
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
              <AlertCircle size={10} className="text-amber-500" />
              <span className="text-[10px] font-bold text-amber-400">
                {_warnings.length} warning{_warnings.length > 1 ? "s" : ""}
              </span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Fingerprint size={10} className="text-slate-700" />
            <span className="text-[10px] font-mono text-slate-700 truncate max-w-[140px]">
              {_auditHash}
            </span>
          </div>
        </div>
      </div>

      {/* Methodology one-liner (if present) */}
      {_methodology && _methodology !== "—" && (
        <div className="px-6 pb-2">
          <p className="text-[10px] text-slate-600 leading-relaxed line-clamp-1">
            <span className="text-slate-500 font-semibold">Methodology:</span>{" "}
            {_methodology}
          </p>
        </div>
      )}
    </div>
  );
}
