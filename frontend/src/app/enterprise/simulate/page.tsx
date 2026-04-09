"use client";
/**
 * Impact Observatory | مرصد الأثر — Enterprise Scenario Simulation Page
 * Layer: UI (L6) — Full-page simulation with before/after + explainability
 */
import { useState, useMemo, useCallback } from "react";
import { useAppStore } from "@/store/app-store";
import {
  useScenarioCatalog,
  useSimulateScenario,
} from "@/hooks/use-enterprise";
import { ScenarioSimulator } from "@/features/enterprise/components";
import { ExplainabilityPanel } from "@/features/enterprise/components";
import { RiskHeatmap } from "@/features/enterprise/components";
import { MetricsStrip } from "@/features/enterprise/components";
import { ENTERPRISE_LABELS } from "@/types/enterprise";
import type { EnterpriseKPI, RiskHeatmapData, SimulationParams } from "@/types/enterprise";
import type { Classification, ExplanationPack, DecisionAction } from "@/types/observatory";

function classifyValue(v: number): Classification {
  if (v >= 0.8) return "CRITICAL";
  if (v >= 0.6) return "ELEVATED";
  if (v >= 0.4) return "MODERATE";
  if (v >= 0.2) return "LOW";
  return "NOMINAL";
}

function formatUSD(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

export default function SimulationPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const L = ENTERPRISE_LABELS[language];

  const { data: scenariosData, isLoading: scenariosLoading } = useScenarioCatalog();
  const simulateMutation = useSimulateScenario();

  const [runResults, setRunResults] = useState<Record<string, unknown>[]>([]);
  const currentResult = runResults[runResults.length - 1] ?? null;
  const previousResult = runResults.length > 1 ? runResults[runResults.length - 2] : null;

  const scenarios = useMemo(() => {
    const raw = scenariosData as { data?: { scenarios?: Array<{ scenario_id: string; scenario_name_en: string; scenario_name_ar: string; domain: string; trigger_type: string; severity_level: string; affected_sectors: string[]; shock_intensity_default: number; scenario_parameters: Record<string, number> }> } } | undefined;
    return raw?.data?.scenarios ?? [];
  }, [scenariosData]);

  const handleSimulate = useCallback(
    async (params: SimulationParams) => {
      const result = await simulateMutation.mutateAsync({
        template_id: params.templateId,
        severity: params.severity,
        horizon_hours: params.horizonHours,
        label: params.label,
      });
      if (result?.data) {
        setRunResults((prev) => [...prev.slice(-4), result.data as Record<string, unknown>]);
      }
      return result?.data ?? null;
    },
    [simulateMutation],
  );

  // ── Extract result metrics ──
  const resultMetrics = useMemo<EnterpriseKPI[]>(() => {
    if (!currentResult) return [];
    const headline = (currentResult as Record<string, unknown>).headline as Record<string, number> | undefined;
    const scenario = (currentResult as Record<string, unknown>).scenario as Record<string, unknown> | undefined;
    return [
      {
        id: "total_loss",
        label: "Total Loss",
        label_ar: "إجمالي الخسائر",
        value: formatUSD(headline?.total_loss_usd ?? 0),
        unit: "USD",
        severity: classifyValue((headline?.average_stress ?? 0)),
      },
      {
        id: "peak_day",
        label: "Peak Impact Day",
        label_ar: "يوم الذروة",
        value: headline?.peak_day ?? 0,
        unit: isAr ? "يوم" : "day",
        severity: "MODERATE" as Classification,
      },
      {
        id: "entities",
        label: "Affected Entities",
        label_ar: "الكيانات المتأثرة",
        value: headline?.affected_entities ?? headline?.total_nodes_impacted ?? 0,
        unit: "",
        severity: "ELEVATED" as Classification,
      },
      {
        id: "severity",
        label: "Scenario Severity",
        label_ar: "شدة السيناريو",
        value: `${((scenario?.severity as number ?? 0) * 100).toFixed(0)}%`,
        unit: "",
        severity: classifyValue(scenario?.severity as number ?? 0),
      },
    ];
  }, [currentResult, isAr]);

  // ── Risk heatmap from financial impacts ──
  const riskHeatmap = useMemo<RiskHeatmapData>(() => {
    const financial = ((currentResult as Record<string, unknown>)?.financial as Array<Record<string, unknown>>) ?? [];
    const dims = ["loss_pct_gdp", "stress_level", "confidence", "peak_day_norm"];
    const entities = financial.map((f) => String(f.entity_label ?? f.entity_id ?? "Unknown"));
    const cells = financial.flatMap((f) => {
      const stress = Number(f.stress_level ?? 0);
      const conf = Number(f.confidence ?? 0);
      const lossPct = Number(f.loss_pct_gdp ?? 0);
      const peakNorm = Math.min(Number(f.peak_day ?? 0) / 30, 1);
      return [
        { entityId: String(f.entity_id), entityName: String(f.entity_label ?? f.entity_id), sector: String(f.sector ?? ""), dimension: "loss_pct_gdp", value: Math.min(lossPct * 10, 1), severity: classifyValue(lossPct * 10) },
        { entityId: String(f.entity_id), entityName: String(f.entity_label ?? f.entity_id), sector: String(f.sector ?? ""), dimension: "stress_level", value: stress, severity: classifyValue(stress) },
        { entityId: String(f.entity_id), entityName: String(f.entity_label ?? f.entity_id), sector: String(f.sector ?? ""), dimension: "confidence", value: conf, severity: classifyValue(1 - conf) },
        { entityId: String(f.entity_id), entityName: String(f.entity_label ?? f.entity_id), sector: String(f.sector ?? ""), dimension: "peak_day_norm", value: peakNorm, severity: classifyValue(peakNorm) },
      ];
    });
    return { cells, entities, dimensions: dims, maxValue: 1 };
  }, [currentResult]);

  // ── Explanation ──
  const explanation = (currentResult as Record<string, unknown>)?.explanation as ExplanationPack | undefined;
  const actions = ((currentResult as Record<string, unknown>)?.decisions as { actions?: DecisionAction[]; all_actions?: DecisionAction[] })?.all_actions
    ?? ((currentResult as Record<string, unknown>)?.decisions as { actions?: DecisionAction[] })?.actions
    ?? [];

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", margin: 0 }}>
          {L.simulation}
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#475569", margin: "4px 0 0" }}>
          {isAr
            ? "قم بتشغيل محاكاة فورية لسيناريوهات GCC المالية وقارن النتائج"
            : "Run real-time GCC financial scenario simulations and compare before/after impact"}
        </p>
      </div>

      {/* Simulator Form */}
      <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", marginBottom: 24 }}>
        <ScenarioSimulator
          scenarios={scenarios}
          isLoading={simulateMutation.isPending || scenariosLoading}
          language={language}
          onSimulate={handleSimulate}
          previousResult={previousResult ? {
            totalLoss: (previousResult.headline as Record<string, number>)?.total_loss_usd ?? 0,
            peakDay: (previousResult.headline as Record<string, number>)?.peak_day ?? 0,
            affectedEntities: (previousResult.headline as Record<string, number>)?.affected_entities ?? 0,
            avgStress: (previousResult.headline as Record<string, number>)?.average_stress ?? 0,
          } : undefined}
        />
      </div>

      {/* Results Section */}
      {currentResult && (
        <>
          {/* Result KPIs */}
          <div style={{ marginBottom: 24 }}>
            <MetricsStrip metrics={resultMetrics} language={language} />
          </div>

          {/* Two-Column: Heatmap + Explainability */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
            {/* Risk Heatmap */}
            {riskHeatmap.cells.length > 0 && (
              <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
                  {L.riskHeatmap}
                </h3>
                <RiskHeatmap data={riskHeatmap} language={language} onEntitySelect={() => {}} />
              </div>
            )}

            {/* Recommended Actions */}
            <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
                {L.actions} ({actions.length})
              </h3>
              {actions.length === 0 ? (
                <p style={{ fontSize: "0.8125rem", color: "#94A3B8" }}>{L.noData}</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {actions.slice(0, 6).map((a, i) => (
                    <div key={a.id ?? i} style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "10px 14px", borderRadius: 8, border: "1px solid #E2E8F0", background: "#FAFBFC" }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
                        background: a.priority > 0.7 ? "#FEE2E2" : a.priority > 0.4 ? "#FEF3C7" : "#DCFCE7",
                        color: a.priority > 0.7 ? "#B91C1C" : a.priority > 0.4 ? "#B45309" : "#15803D",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: "0.75rem", fontWeight: 700,
                      }}>
                        {i + 1}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#0F172A" }}>
                          {isAr ? (a.action_ar ?? a.action) : a.action}
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "#64748B", marginTop: 2 }}>
                          {a.sector} · {a.owner} · {isAr ? "أولوية" : "Priority"}: {(a.priority * 100).toFixed(0)}%
                        </div>
                        <div style={{ display: "flex", gap: 12, marginTop: 6, fontSize: "0.6875rem", color: "#475569" }}>
                          <span>{isAr ? "خسائر مُجنبة" : "Loss Avoided"}: {formatUSD(a.loss_avoided_usd)}</span>
                          <span>{isAr ? "تكلفة" : "Cost"}: {formatUSD(a.cost_usd)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Explainability */}
          {explanation && (
            <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
                {L.explainability}
              </h3>
              <ExplainabilityPanel
                explanation={explanation}
                actions={actions}
                language={language}
              />
            </div>
          )}

          {/* Run History */}
          {runResults.length > 1 && (
            <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", marginTop: 24 }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
                {isAr ? "سجل المحاكاة" : "Simulation History"} ({runResults.length})
              </h3>
              <div style={{ display: "flex", gap: 12, overflowX: "auto" }}>
                {runResults.map((r, i) => {
                  const h = (r as Record<string, unknown>).headline as Record<string, number> | undefined;
                  const s = (r as Record<string, unknown>).scenario as Record<string, unknown> | undefined;
                  const isCurrent = i === runResults.length - 1;
                  return (
                    <div
                      key={i}
                      style={{
                        minWidth: 180, padding: "12px 16px", borderRadius: 8,
                        border: isCurrent ? "2px solid #1D4ED8" : "1px solid #E2E8F0",
                        background: isCurrent ? "#EFF6FF" : "#FFFFFF",
                        cursor: "pointer", flexShrink: 0,
                      }}
                      onClick={() => setRunResults((prev) => [...prev.slice(0, i), ...prev.slice(i + 1), prev[i]])}
                    >
                      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#0F172A" }}>
                        Run #{i + 1} {isCurrent ? "(current)" : ""}
                      </div>
                      <div style={{ fontSize: "0.6875rem", color: "#64748B", marginTop: 4 }}>
                        {String(s?.label ?? s?.template_id ?? "Unknown")}
                      </div>
                      <div style={{ fontSize: "1rem", fontWeight: 700, color: "#0F172A", marginTop: 6 }}>
                        {formatUSD(h?.total_loss_usd ?? 0)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
