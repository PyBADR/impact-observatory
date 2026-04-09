"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { SCENARIOS } from "@/lib/scenarios";
import { PORTFOLIO } from "@/lib/portfolio";
import type { MacroInput, DecisionResult } from "@/types/decision";

type V1Context = {
  available: boolean;
  decisionsLoaded: number;
  authorityMetrics: Record<string, number> | null;
};

type TenantInfo = {
  tenantId: string;
  userId: string;
  evaluationNumber: number;
};

type EventBusStats = {
  processed: number;
  failed: number;
  logSize: number;
  mode?: string;
};

const DECISION_COLORS: Record<string, string> = {
  APPROVED: "text-[var(--io-success)] bg-green-50 border-green-200",
  CONDITIONAL: "text-[var(--io-warning)] bg-amber-50 border-amber-200",
  REJECTED: "text-[var(--io-danger)] bg-red-50 border-red-200",
};

const DECISION_LABELS: Record<string, { en: string; ar: string }> = {
  APPROVED: { en: "Approved", ar: "مُعتمد" },
  CONDITIONAL: { en: "Conditional", ar: "مشروط" },
  REJECTED: { en: "Rejected", ar: "مرفوض" },
};

function formatCoverage(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n}`;
}

export default function MacroPage() {
  const [scenarioKey, setScenarioKey] = useState("recession");
  const [macro, setMacro] = useState<MacroInput>(SCENARIOS.recession.macro);
  const [results, setResults] = useState<DecisionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastEval, setLastEval] = useState<string | null>(null);
  const [v1Context, setV1Context] = useState<V1Context | null>(null);
  const [tenantInfo, setTenantInfo] = useState<TenantInfo | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [evaluationId, setEvaluationId] = useState<string | null>(null);
  const [eventBusStats, setEventBusStats] = useState<EventBusStats | null>(null);
  const evalCount = useRef(0);

  const runEvaluation = useCallback(async (m: MacroInput, scenario: string) => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/decision/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          macro: m,
          entities: PORTFOLIO,
          scenario,
          tenantId: "tenant_001",
          userId: "operator_main",
          role: "operator",
        }),
      });
      const data = await res.json();
      setResults(data.results);
      setLastEval(data.timestamp);
      setV1Context(data.v1Context ?? null);
      setTenantInfo(data.tenant ?? null);
      setLatencyMs(data.latencyMs ?? null);
      setEvaluationId(data.evaluationId ?? null);
      setEventBusStats(data.eventBus ?? null);
      evalCount.current++;
    } catch {
      // Keep previous results on error
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-evaluate on scenario change
  useEffect(() => {
    const m = SCENARIOS[scenarioKey].macro;
    setMacro(m);
    runEvaluation(m, scenarioKey);
  }, [scenarioKey, runEvaluation]);

  // Re-evaluate on manual macro adjustment
  const handleMacroChange = (field: keyof MacroInput, value: number) => {
    const updated = { ...macro, [field]: value };
    setMacro(updated);
    runEvaluation(updated, scenarioKey);
  };

  const approved = results.filter((r) => r.decision === "APPROVED").length;
  const conditional = results.filter((r) => r.decision === "CONDITIONAL").length;
  const rejected = results.filter((r) => r.decision === "REJECTED").length;
  const avgRisk = results.length
    ? Math.round(results.reduce((s, r) => s + r.riskScore, 0) / results.length)
    : 0;

  return (
    <div className="min-h-screen bg-[var(--io-bg)] p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--io-primary)]">
            Portfolio Decision Engine
          </h1>
          <p className="text-sm text-[var(--io-secondary)] mt-1">
            Scenario-driven underwriting intelligence across {PORTFOLIO.length} entities
          </p>
        </div>
        {lastEval && (
          <div className="text-xs text-[var(--io-secondary)] text-right space-y-0.5">
            {tenantInfo && (
              <div className="font-mono">
                {tenantInfo.tenantId} / {tenantInfo.userId}
              </div>
            )}
            <div>
              Evaluation #{tenantInfo?.evaluationNumber ?? evalCount.current}
              {evaluationId && (
                <span className="ml-2 text-[10px] text-[var(--io-secondary)]">
                  {evaluationId}
                </span>
              )}
            </div>
            <div>
              {new Date(lastEval).toLocaleTimeString()}
              {latencyMs !== null && (
                <span className={`ml-2 font-mono ${latencyMs > 500 ? "text-[var(--io-warning)]" : "text-[var(--io-success)]"}`}>
                  {latencyMs}ms
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* V1 Backend Status */}
      {v1Context && (
        <div className={`flex items-center gap-4 px-4 py-2.5 rounded-md border text-xs ${
          v1Context.available
            ? "bg-green-50 border-green-200 text-green-800"
            : "bg-slate-50 border-[var(--io-border)] text-[var(--io-secondary)]"
        }`}>
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${v1Context.available ? "bg-green-500" : "bg-slate-400"}`} />
            V1 Backend: {v1Context.available ? "Connected" : "Offline (macro-only mode)"}
          </span>
          {v1Context.available && (
            <>
              <span>Decisions loaded: {v1Context.decisionsLoaded}</span>
              {v1Context.authorityMetrics && (
                <span>
                  Authority: {v1Context.authorityMetrics.total} total,{" "}
                  {v1Context.authorityMetrics.executed} executed
                </span>
              )}
            </>
          )}
        </div>
      )}

      {/* Event Bus Status */}
      {eventBusStats && (
        <div className="flex items-center gap-4 px-4 py-2 rounded-md border border-[var(--io-border)] bg-[var(--io-surface)] text-xs text-[var(--io-secondary)]">
          <span className="font-medium uppercase tracking-wider">Event Bus{eventBusStats.mode ? ` (${eventBusStats.mode})` : ""}</span>
          <span>Processed: <span className="font-mono font-semibold text-[var(--io-primary)]">{eventBusStats.processed}</span></span>
          <span>Failed: <span className={`font-mono font-semibold ${eventBusStats.failed > 0 ? "text-[var(--io-danger)]" : "text-[var(--io-primary)]"}`}>{eventBusStats.failed}</span></span>
          <span>Log: <span className="font-mono font-semibold text-[var(--io-primary)]">{eventBusStats.logSize}</span></span>
        </div>
      )}

      {/* Scenario Switcher */}
      <div className="io-card p-4">
        <div className="text-xs font-medium text-[var(--io-secondary)] uppercase tracking-wider mb-3">
          Scenario Preset
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(SCENARIOS).map(([key, s]) => (
            <button
              key={key}
              onClick={() => setScenarioKey(key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all border ${
                scenarioKey === key
                  ? "bg-[var(--io-accent)] text-white border-[var(--io-accent)] shadow-sm"
                  : "bg-[var(--io-surface)] text-[var(--io-primary)] border-[var(--io-border)] hover:border-[var(--io-accent)] hover:text-[var(--io-accent)]"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Macro Controls */}
      <div className="io-card p-4">
        <div className="text-xs font-medium text-[var(--io-secondary)] uppercase tracking-wider mb-3">
          Macro Parameters
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MacroSlider
            label="Inflation"
            unit="%"
            value={macro.inflation}
            min={0}
            max={15}
            step={0.5}
            onChange={(v) => handleMacroChange("inflation", v)}
          />
          <MacroSlider
            label="Interest Rate"
            unit="%"
            value={macro.interestRate}
            min={0}
            max={15}
            step={0.5}
            onChange={(v) => handleMacroChange("interestRate", v)}
          />
          <MacroSlider
            label="GDP Growth"
            unit="%"
            value={macro.gdpGrowth}
            min={-5}
            max={10}
            step={0.5}
            onChange={(v) => handleMacroChange("gdpGrowth", v)}
          />
        </div>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Avg Risk" value={`${avgRisk}`} sub="/100" />
        <KpiCard
          label="Approved"
          value={`${approved}`}
          color="var(--io-success)"
        />
        <KpiCard
          label="Conditional"
          value={`${conditional}`}
          color="var(--io-warning)"
        />
        <KpiCard
          label="Rejected"
          value={`${rejected}`}
          color="var(--io-danger)"
        />
      </div>

      {/* Portfolio Grid */}
      <div className="io-card overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--io-border)] flex items-center justify-between">
          <span className="text-xs font-medium text-[var(--io-secondary)] uppercase tracking-wider">
            Portfolio Evaluation
          </span>
          {loading && (
            <span className="text-xs text-[var(--io-accent)] animate-pulse">
              Evaluating...
            </span>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-[var(--io-secondary)] uppercase tracking-wider border-b border-[var(--io-border)]">
                <th className="px-4 py-3 font-medium">Entity</th>
                <th className="px-4 py-3 font-medium">Sector</th>
                <th className="px-4 py-3 font-medium">Coverage</th>
                <th className="px-4 py-3 font-medium">Risk Score</th>
                <th className="px-4 py-3 font-medium">Delta</th>
                <th className="px-4 py-3 font-medium">Decision</th>
                <th className="px-4 py-3 font-medium">V1</th>
                <th className="px-4 py-3 font-medium">Policy Flags</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => {
                const entity = PORTFOLIO[i];
                return (
                  <tr
                    key={entity?.id ?? i}
                    className="border-b border-[var(--io-border)] last:border-0 hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-[var(--io-primary)]">
                      {r.entity}
                    </td>
                    <td className="px-4 py-3 text-[var(--io-secondary)]">
                      {entity?.sector}
                    </td>
                    <td className="px-4 py-3 font-mono text-[var(--io-secondary)]">
                      {entity ? formatCoverage(entity.coverage) : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBar score={r.riskScore} />
                    </td>
                    <td className="px-4 py-3 font-mono">
                      <DeltaBadge delta={r.delta} />
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold border ${DECISION_COLORS[r.decision]}`}
                      >
                        {DECISION_LABELS[r.decision]?.en ?? r.decision}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {"v1Linked" in r && (r as Record<string, unknown>).v1Linked ? (
                        <span className="text-[10px] px-1.5 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded font-mono">
                          LINKED
                        </span>
                      ) : (
                        <span className="text-[var(--io-secondary)] text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {r.policies.filter(p => !p.startsWith("V1_")).length > 0
                          ? r.policies.filter(p => !p.startsWith("V1_")).map((p) => (
                              <span
                                key={p}
                                className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-[var(--io-secondary)] rounded font-mono"
                              >
                                {p}
                              </span>
                            ))
                          : <span className="text-[var(--io-secondary)] text-xs">—</span>}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Explainability Panel */}
      {results.length > 0 && (
        <div className="io-card p-4">
          <div className="text-xs font-medium text-[var(--io-secondary)] uppercase tracking-wider mb-3">
            Risk Explanations
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {results.map((r, i) => (
              <div
                key={i}
                className="p-3 rounded-md border border-[var(--io-border)] bg-slate-50"
              >
                <div className="font-medium text-sm text-[var(--io-primary)] mb-1">
                  {r.entity}
                </div>
                <p className="text-xs text-[var(--io-secondary)] leading-relaxed">
                  {r.explanation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Sub-components ─── */

function MacroSlider({
  label,
  unit,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  unit: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm text-[var(--io-primary)]">{label}</span>
        <span className="text-sm font-mono font-semibold text-[var(--io-primary)]">
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-[var(--io-accent)]"
      />
    </div>
  );
}

function KpiCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="io-card p-4">
      <div className="text-xs text-[var(--io-secondary)] uppercase tracking-wider mb-1">
        {label}
      </div>
      <div
        className="text-2xl font-bold font-mono"
        style={{ color: color ?? "var(--io-primary)" }}
      >
        {value}
        {sub && (
          <span className="text-sm font-normal text-[var(--io-secondary)]">
            {sub}
          </span>
        )}
      </div>
    </div>
  );
}

function RiskBar({ score }: { score: number }) {
  const color =
    score > 75
      ? "var(--io-danger)"
      : score > 55
        ? "var(--io-warning)"
        : "var(--io-success)";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-xs font-semibold" style={{ color }}>
        {score}
      </span>
    </div>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span className="text-[var(--io-secondary)] text-xs">—</span>;
  const isUp = delta > 0;
  return (
    <span
      className={`text-xs font-semibold ${isUp ? "text-[var(--io-danger)]" : "text-[var(--io-success)]"}`}
    >
      {isUp ? "▲" : "▼"} {Math.abs(delta)}
    </span>
  );
}
