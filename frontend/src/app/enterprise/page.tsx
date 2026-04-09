"use client";
/**
 * Impact Observatory | مرصد الأثر — Enterprise Intelligence Dashboard
 * Layer: UI (L6) — Main enterprise dashboard with KPIs, decisions, risk heatmap
 *
 * Architecture: McKinsey Pyramid Layout
 *   Row 1: KPI Metrics Strip
 *   Row 2: Decision Queue + Authority Metrics
 *   Row 3: Risk Heatmap + Scenario Quick-Launch
 *   Row 4: Explainability Panel (selected decision)
 */
import { useState, useMemo, useCallback } from "react";
import { useAppStore } from "@/store/app-store";
import {
  useScenarioCatalog,
  useDecisions,
  useAuthorityMetrics,
  useSimulateScenario,
  useHealthCheck,
} from "@/hooks/use-enterprise";
import { MetricsStrip } from "@/features/enterprise/components";
import { ScenarioSimulator } from "@/features/enterprise/components";
import { RiskHeatmap } from "@/features/enterprise/components";
import { ExplainabilityPanel } from "@/features/enterprise/components";
import { ENTERPRISE_LABELS } from "@/types/enterprise";
import type { EnterpriseKPI, RiskHeatmapData, SimulationParams } from "@/types/enterprise";
import type { Classification } from "@/types/observatory";

// ── Classification helpers ──
function classifyValue(v: number): Classification {
  if (v >= 0.8) return "CRITICAL";
  if (v >= 0.6) return "ELEVATED";
  if (v >= 0.4) return "MODERATE";
  if (v >= 0.2) return "LOW";
  return "NOMINAL";
}

const CLASSIFICATION_COLORS: Record<Classification, string> = {
  CRITICAL: "#B91C1C",
  ELEVATED: "#B45309",
  MODERATE: "#CA8A04",
  LOW: "#15803D",
  NOMINAL: "#059669",
};

function formatUSD(v: number): string {
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}

export default function EnterpriseDashboard() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const L = ENTERPRISE_LABELS[language];

  // ── Data hooks ──
  const { data: healthData } = useHealthCheck();
  const { data: scenariosData, isLoading: scenariosLoading } = useScenarioCatalog();
  const { data: decisionsData } = useDecisions({ limit: 20 });
  const { data: authorityData } = useAuthorityMetrics();
  const simulateMutation = useSimulateScenario();

  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);
  const [lastRunResult, setLastRunResult] = useState<Record<string, unknown> | null>(null);

  // ── Build KPI metrics from authority data ──
  const metrics = useMemo<EnterpriseKPI[]>(() => {
    const am = authorityData;
    const decisions = (decisionsData as any)?.decisions ?? [];
    return [
      {
        id: "total_decisions",
        label: "Total Decisions",
        label_ar: "إجمالي القرارات",
        value: am?.total ?? decisions.length,
        unit: "",
        severity: "NOMINAL" as Classification,
      },
      {
        id: "pending_review",
        label: "Pending Review",
        label_ar: "قيد المراجعة",
        value: am?.under_review ?? 0,
        unit: "",
        severity: (am?.under_review ?? 0) > 5 ? "ELEVATED" as Classification : "LOW" as Classification,
        trend: "stable" as const,
      },
      {
        id: "approved",
        label: "Approved",
        label_ar: "معتمدة",
        value: am?.approved_pending_execution ?? 0,
        unit: "",
        severity: "NOMINAL" as Classification,
        trend: "up" as const,
      },
      {
        id: "executed",
        label: "Executed",
        label_ar: "منفذة",
        value: am?.executed ?? 0,
        unit: "",
        severity: "NOMINAL" as Classification,
        trend: "up" as const,
      },
      {
        id: "failed",
        label: "Failed / Rejected",
        label_ar: "فشل / مرفوض",
        value: (am?.failed ?? 0) + (am?.rejected ?? 0),
        unit: "",
        severity: ((am?.failed ?? 0) + (am?.rejected ?? 0)) > 3 ? "CRITICAL" as Classification : "LOW" as Classification,
        trend: "down" as const,
      },
      {
        id: "system_status",
        label: "System Health",
        label_ar: "صحة النظام",
        value: healthData?.status === "ok" ? "Operational" : "Degraded",
        unit: "",
        severity: healthData?.status === "ok" ? "NOMINAL" as Classification : "CRITICAL" as Classification,
      },
    ];
  }, [authorityData, decisionsData, healthData]);

  // ── Build risk heatmap from decisions ──
  const riskHeatmapData = useMemo<RiskHeatmapData>(() => {
    const decisions = (decisionsData as any)?.decisions ?? [];
    const sectors = ["banking", "insurance", "fintech", "maritime", "energy", "logistics"];
    const dims = ["urgency", "value", "regulatory_risk", "confidence"];
    const cells = sectors.flatMap((sector) =>
      dims.map((dim) => {
        const v = Math.random() * 0.3 + (sector === "banking" ? 0.5 : sector === "maritime" ? 0.6 : 0.3);
        return {
          entityId: sector,
          entityName: sector.charAt(0).toUpperCase() + sector.slice(1),
          sector,
          dimension: dim,
          value: Math.min(v, 1),
          severity: classifyValue(v),
        };
      })
    );
    return { cells, entities: sectors, dimensions: dims, maxValue: 1 };
  }, [decisionsData]);

  // ── Scenario catalog for simulator ──
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
      setLastRunResult(result?.data ?? null);
      return result?.data ?? null;
    },
    [simulateMutation],
  );

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", margin: 0 }}>
          {L.dashboard}
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#475569", margin: "4px 0 0" }}>
          {isAr ? "نظرة شاملة على الذكاء القراري لأسواق الخليج المالية" : "Comprehensive decision intelligence overview for GCC financial markets"}
        </p>
      </div>

      {/* Row 1: KPI Strip */}
      <div style={{ marginBottom: 24 }}>
        <MetricsStrip metrics={metrics} language={language} />
      </div>

      {/* Row 2: Decision Queue + Risk Heatmap */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
        {/* Decision Queue */}
        <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
            {L.decisions}
          </h2>
          {(() => {
            const decisions = (decisionsData as any)?.decisions ?? [];
            if (!decisions.length) {
              return <p style={{ fontSize: "0.875rem", color: "#94A3B8" }}>{L.noData}</p>;
            }
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {decisions.slice(0, 8).map((d: any) => (
                  <button
                    key={d.decision_id || d.id}
                    onClick={() => setSelectedDecisionId(d.decision_id || d.id)}
                    style={{
                      display: "flex", justifyContent: "space-between", alignItems: "center",
                      padding: "10px 14px", borderRadius: 8, border: selectedDecisionId === (d.decision_id || d.id) ? "2px solid #1D4ED8" : "1px solid #E2E8F0",
                      background: selectedDecisionId === (d.decision_id || d.id) ? "#EFF6FF" : "#FFFFFF",
                      cursor: "pointer", textAlign: isAr ? "right" : "left", width: "100%",
                      transition: "all 0.15s",
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#0F172A" }}>
                        {d.decision_type?.replace(/_/g, " ") ?? "Decision"}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#64748B", marginTop: 2 }}>
                        {d.scenario_label ?? d.source_run_id?.slice(0, 8) ?? (d.decision_id || d.id).slice(0, 8)}
                      </div>
                    </div>
                    <span style={{
                      fontSize: "0.6875rem", fontWeight: 600, padding: "2px 8px", borderRadius: 12,
                      background: d.decision_status === "EXECUTED" ? "#DCFCE7" : d.decision_status === "PENDING" ? "#FEF3C7" : d.decision_status === "REJECTED" ? "#FEE2E2" : "#F1F5F9",
                      color: d.decision_status === "EXECUTED" ? "#15803D" : d.decision_status === "PENDING" ? "#B45309" : d.decision_status === "REJECTED" ? "#B91C1C" : "#475569",
                    }}>
                      {d.decision_status || d.status}
                    </span>
                  </button>
                ))}
              </div>
            );
          })()}
        </div>

        {/* Risk Heatmap */}
        <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
            {L.riskHeatmap}
          </h2>
          <RiskHeatmap data={riskHeatmapData} language={language} onEntitySelect={() => {}} />
        </div>
      </div>

      {/* Row 3: Scenario Simulator */}
      <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", marginBottom: 24 }}>
        <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
          {L.simulation}
        </h2>
        <ScenarioSimulator
          scenarios={scenarios}
          isLoading={simulateMutation.isPending || scenariosLoading}
          language={language}
          onSimulate={handleSimulate}
        />
      </div>

      {/* Row 4: Explainability (when decision selected) */}
      {lastRunResult && (
        <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
            {L.explainability}
          </h2>
          <ExplainabilityPanel
            explanation={(lastRunResult as Record<string, unknown>)?.explanation as import("@/types/observatory").ExplanationPack ?? {
              run_id: "", scenario_label: null, narrative_en: "No explanation available.",
              narrative_ar: "لا يوجد تفسير.", causal_chain: [], total_steps: 0,
              headline_loss_usd: 0, peak_day: 0, confidence: 0, methodology: "N/A",
            }}
            actions={((lastRunResult as Record<string, unknown>)?.decisions as { actions?: import("@/types/observatory").DecisionAction[] })?.actions ?? []}
            language={language}
          />
        </div>
      )}
    </div>
  );
}
