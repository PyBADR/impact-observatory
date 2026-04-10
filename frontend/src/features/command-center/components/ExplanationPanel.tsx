"use client";

/**
 * ExplanationPanel — Structured narrative + methodology + trust metadata
 *
 * Renders the AI-generated explanation in a format that builds executive trust:
 * narrative summary, methodology disclosure, data sources, audit trail.
 */

import React, { useState } from "react";
import {
  BookOpen,
  Fingerprint,
  Database,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
} from "lucide-react";
import { safeNum, safeStr, safeArr, safePercent } from "../lib/format";

// ── Types ─────────────────────────────────────────────────────────────

interface ExplanationPanelProps {
  narrativeEn: string;
  narrativeAr: string;
  methodology: string;
  confidence: number;
  totalSteps: number;
  auditHash: string;
  modelVersion: string;
  dataSources: string[];
  stagesCompleted: string[];
  warnings: string[];
  lang?: "en" | "ar";
}

// ── Collapsible Section ───────────────────────────────────────────────

function Section({
  icon,
  label,
  defaultOpen = false,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-white/[0.04] last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-left hover:bg-white/[0.02] transition-colors"
      >
        <div className="text-slate-500 flex-shrink-0">{icon}</div>
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex-1">
          {label}
        </span>
        <ChevronDown
          size={12}
          className={`text-slate-600 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function ExplanationPanel({
  narrativeEn,
  narrativeAr,
  methodology,
  confidence,
  totalSteps,
  auditHash,
  modelVersion,
  dataSources,
  stagesCompleted,
  warnings,
  lang = "en",
}: ExplanationPanelProps) {
  // ── Safe coercion ──
  const _confidence = safeNum(confidence);
  const _totalSteps = safeNum(totalSteps);
  const _auditHash = safeStr(auditHash, "N/A");
  const _modelVersion = safeStr(modelVersion, "unknown");
  const _dataSources = safeArr<string>(dataSources);
  const _stagesCompleted = safeArr<string>(stagesCompleted);
  const _warnings = safeArr<string>(warnings);

  const narrative = lang === "ar" ? safeStr(narrativeAr, "") : safeStr(narrativeEn, "");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Explanation
        </h2>
        <span className="text-[10px] text-slate-600">
          {_totalSteps}-step causal trace
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Narrative */}
        <Section icon={<BookOpen size={13} />} label="Intelligence Narrative" defaultOpen>
          {narrative ? (
            <p className="text-[12px] text-slate-300 leading-relaxed">
              {narrative}
            </p>
          ) : (
            <p className="text-[11px] text-slate-600 italic">
              No narrative generated for this run. The explanation engine may not have completed.
            </p>
          )}
        </Section>

        {/* Methodology */}
        <Section icon={<Database size={13} />} label="Methodology">
          {methodology ? (
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {methodology}
            </p>
          ) : (
            <p className="text-[11px] text-slate-600 italic">
              Methodology details are unavailable for this run.
            </p>
          )}
        </Section>

        {/* Data Sources */}
        <Section icon={<Database size={13} />} label="Data Sources">
          <div className="flex flex-wrap gap-1.5">
            {_dataSources.length > 0 ? _dataSources.map((src) => (
              <span
                key={src}
                className="px-2 py-0.5 text-[10px] font-medium text-slate-400 bg-white/[0.04] border border-white/[0.06] rounded"
              >
                {src}
              </span>
            )) : (
              <span className="text-[10px] text-slate-600 italic">No data sources recorded</span>
            )}
          </div>
        </Section>

        {/* Pipeline Stages */}
        <Section icon={<CheckCircle2 size={13} />} label="Pipeline Stages">
          <div className="flex flex-wrap gap-1.5">
            {_stagesCompleted.length > 0 ? _stagesCompleted.map((stage) => (
              <span
                key={stage}
                className="px-2 py-0.5 text-[10px] font-medium text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 rounded"
              >
                <CheckCircle2 size={8} className="inline mr-0.5" />
                {safeStr(stage, "stage").replace(/_/g, " ")}
              </span>
            )) : (
              <span className="text-[10px] text-slate-600 italic">No stages completed</span>
            )}
          </div>
        </Section>

        {/* Warnings */}
        {_warnings.length > 0 && (
          <Section icon={<AlertCircle size={13} />} label="Warnings">
            <div className="space-y-1">
              {_warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-1.5">
                  <AlertCircle size={10} className="text-amber-500 mt-0.5 flex-shrink-0" />
                  <span className="text-[11px] text-amber-400">{w}</span>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Audit Trail */}
        <Section icon={<Fingerprint size={13} />} label="Audit Trail">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-600">Model Version</span>
              <span className="text-[10px] font-mono text-slate-400">
                {_modelVersion}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-600">Audit Hash</span>
              <span className="text-[10px] font-mono text-slate-500 truncate max-w-[200px]">
                {_auditHash}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-600">Confidence</span>
              <span
                className="text-[11px] font-bold tabular-nums"
                style={{
                  color:
                    _confidence >= 0.8
                      ? "#22C55E"
                      : _confidence >= 0.6
                      ? "#EAB308"
                      : "#EF4444",
                }}
              >
                {safePercent(_confidence, 0)}
              </span>
            </div>
          </div>
        </Section>
      </div>
    </div>
  );
}
