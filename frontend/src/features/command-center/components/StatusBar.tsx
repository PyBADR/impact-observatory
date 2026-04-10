"use client";

/**
 * StatusBar — Bottom-of-screen pipeline status and audit metadata
 *
 * Shows: data source indicator, pipeline stages, audit hash,
 * model version, confidence, latency. Minimal footprint.
 */

import React from "react";
import {
  CheckCircle2,
  Database,
  Fingerprint,
  Clock,
  Wifi,
  WifiOff,
} from "lucide-react";
import type { DataSource, CommandCenterTrust } from "../lib/command-store";
import { safeNum, safeStr, safeArr, safeFixed, safePercent } from "../lib/format";

// ── Types ─────────────────────────────────────────────────────────────

interface StatusBarProps {
  dataSource: DataSource;
  trust: CommandCenterTrust | null;
  confidence: number;
  durationMs?: number;
}

// ── Main Component ────────────────────────────────────────────────────

export function StatusBar({
  dataSource,
  trust,
  confidence,
  durationMs,
}: StatusBarProps) {
  const _confidence = safeNum(confidence);
  const _durationMs = safeNum(durationMs, -1);
  const _stagesCompleted = trust ? safeArr<string>(trust.stagesCompleted) : [];
  const _modelVersion = trust ? safeStr(trust.modelVersion, "—") : "—";
  const _auditHash = trust ? safeStr(trust.auditHash, "—") : "—";

  return (
    <footer className="w-full bg-[#060910] border-t border-white/[0.06] px-4 py-1.5">
      <div className="flex items-center gap-4 text-[10px]">
        {/* Data source */}
        <div className="flex items-center gap-1">
          {dataSource === "live" ? (
            <Wifi size={10} className="text-emerald-500" />
          ) : (
            <WifiOff size={10} className="text-amber-500" />
          )}
          <span
            className={
              dataSource === "live" ? "text-emerald-400" : "text-amber-400"
            }
          >
            {dataSource === "live" ? "LIVE" : "MOCK"}
          </span>
        </div>

        {/* Separator */}
        <span className="text-slate-800">|</span>

        {/* Pipeline stages */}
        {trust && (
          <div className="flex items-center gap-1">
            <CheckCircle2 size={10} className="text-emerald-600" />
            <span className="text-slate-500">
              {_stagesCompleted.length}/9 stages
            </span>
          </div>
        )}

        <span className="text-slate-800">|</span>

        {/* Confidence */}
        <div className="flex items-center gap-1">
          <Database size={10} className="text-slate-600" />
          <span className="text-slate-500">
            Confidence:{" "}
            <span
              style={{
                color:
                  _confidence >= 0.8
                    ? "#22C55E"
                    : _confidence >= 0.6
                    ? "#EAB308"
                    : "#EF4444",
              }}
            >
              {safePercent(_confidence, 0)}%
            </span>
          </span>
        </div>

        <span className="text-slate-800">|</span>

        {/* Model version */}
        {trust && (
          <div className="flex items-center gap-1">
            <span className="text-slate-600">v{_modelVersion}</span>
          </div>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Audit hash (truncated) */}
        {trust && (
          <div className="flex items-center gap-1">
            <Fingerprint size={10} className="text-slate-700" />
            <span className="font-mono text-slate-700 truncate max-w-[180px]">
              {_auditHash}
            </span>
          </div>
        )}

        {/* Duration */}
        {_durationMs >= 0 && (
          <div className="flex items-center gap-1">
            <Clock size={10} className="text-slate-700" />
            <span className="text-slate-600 tabular-nums">
              {_durationMs >= 1000
                ? `${safeFixed(_durationMs / 1000, 1)}s`
                : `${_durationMs}ms`}
            </span>
          </div>
        )}
      </div>
    </footer>
  );
}
