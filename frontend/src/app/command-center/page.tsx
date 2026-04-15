"use client";

/**
 * Impact Observatory | مرصد الأثر — Command Center (White Enterprise Theme)
 *
 * RESTORED ARCHITECTURE:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  OBSERVATORY SHELL (identity, language, scenario bar, tabs) │
 * ├─────────────────────────────────────────────────────────────┤
 * │  TAB: Dashboard     → Scenario Library + Intelligence Brief │
 * │  TAB: Scenarios     → Full ScenarioLibrary page             │
 * │  TAB: Macro         → MacroIntelligenceView (top-down flow) │
 * │  TAB: Propagation   → Causal chain flow diagram             │
 * │  TAB: Map           → GCC 6-country impact map              │
 * │  TAB: Sectors       → Banking / Insurance / Fintech stress  │\n * │  TAB: Decisions     → DecisionRoomV2 (full decision engine) │\n * │  TAB: Audit         → Audit trail + regulatory breaches     │\n * └─────────────────────────────────────────────────────────────┘\n *\n * Scenario context is preserved across all tabs via URL params.\n * Data flow: useCommandCenter(runId) feeds all views.\n */

import React, { Suspense, useState, useCallback, useMemo, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";
import { useCommandCenterStore } from "@/features/command-center/lib/command-store";
import type { CountryBakeEntry } from "@/features/command-center/lib/intelligence-engine";
import type { UnifiedScenarioRun } from "@/types/observatory";
import { TEMPLATE_TO_SCENARIO_KEY } from "@/features/command-center/lib/mock-data";
import { generateScenarioPdf, type PdfExportPayload } from "@/features/command-center/lib/pdf-export";

// ── Scenario Label Catalog (for demo mode label override) ──
const SCENARIO_LABELS: Record<string, { en: string; ar: string }> = {
  hormuz_chokepoint_disruption: { en: "Energy & Trade Flow Disruption — Strait of Hormuz", ar: "اضطراب تدفق الطاقة والتجارة — مضيق هرمز" },
  hormuz_full_closure: { en: "Full Hormuz Closure — Extreme Scenario", ar: "إغلاق مضيق هرمز الكامل — سيناريو متطرف" },
  qatar_lng_disruption: { en: "Qatar LNG Export Disruption", ar: "تعطل صادرات الغاز القطري المسال" },
  gcc_cyber_attack: { en: "GCC Cyber Infrastructure Attack", ar: "هجوم سيبراني على البنية التحتية الخليجية" },
  red_sea_trade_corridor_instability: { en: "Red Sea Trade Corridor Instability", ar: "عدم استقرار ممر تجارة البحر الأحمر" },
  regional_liquidity_stress_event: { en: "Regional Liquidity Stress Event — Cross-Border Banking", ar: "حدث ضغط سيولة إقليمي — القطاع المصرفي العابر للحدود" },
  saudi_oil_shock: { en: "Saudi Aramco Production Shock", ar: "صدمة إنتاج أرامكو السعودية" },
  uae_banking_crisis: { en: "UAE Banking Sector Stress", ar: "ضغط القطاع المصرفي الإماراتي" },
  bahrain_sovereign_stress: { en: "Bahrain Fiscal & Sovereign Stress", ar: "ضغط مالي وسيادي بحريني" },
  kuwait_fiscal_shock: { en: "Kuwait Oil Revenue Shock", ar: "صدمة إيرادات النفط الكويتية" },
  oman_port_closure: { en: "Oman Port Closure — Salalah/Sohar", ar: "إغلاق موانئ عمان — صلالة/صحار" },
  energy_market_volatility_shock: { en: "GCC Energy Price Shock", ar: "صدمة أسعار الطاقة الخليجية" },
  critical_port_throughput_disruption: { en: "Multi-Port Throughput Failure", ar: "فشل إنتاجية الموانئ المتعددة" },
  financial_infrastructure_cyber_disruption: { en: "Financial System Cyber Attack", ar: "هجوم سيبراني على النظام المالي" },
  iran_regional_escalation: { en: "Iran Regional Geopolitical Escalation", ar: "تصعيد جيوسياسي إيراني إقليمي" },
  gcc_insurance_reserve_shortfall: { en: "GCC Insurance Reserve Shortfall — IFRS 17 Compliance Crisis", ar: "عجز احتياطيات التأمين الخليجي — أزمة الامتثال لمعيار IFRS 17" },
  gcc_fintech_payment_outage: { en: "GCC Fintech Payment System Outage — Digital Infrastructure", ar: "انقطاع نظام الدفع في التكنولوجيا المالية الخليجية — البنية التحتية الرقمية" },
};

// ── Shell & Navigation ──
import { ObservatoryShell } from "@/components/shell/ObservatoryShell";

// ── Tab: Dashboard (Scenario Library + Brief) ──
import { ScenarioLibrary } from "@/components/scenario/ScenarioLibrary";
import { ScenarioSelector } from "@/components/scenario/ScenarioSelector";

// ── Tab: Decision Room ──
import { DecisionRoomV2 } from "@/components/provenance/DecisionRoomV2";

// ── Tab: Impact Map ──
import { GCCImpactMap } from "@/components/map/GCCImpactMap";

// ── Tab: Propagation ──
import { PropagationView } from "@/components/panels/PropagationView";

// ── Tab: Sector Intelligence ──
import { SectorIntelligenceView } from "@/components/panels/SectorIntelligenceView";

// ── Tab: Regulatory / Audit ──
import { RegulatoryAuditView } from "@/components/panels/RegulatoryAuditView";

// ── Operational Deep-Dive (existing) ──
import { StatusBar } from "@/features/command-center/components/StatusBar";

// ── Data Trust Layer ──
import { DataTrustPanel } from "@/features/command-center/components/DataTrustPanel";
import { useDataTrust } from "@/features/command-center/lib/use-data-trust";

// ── Dev Signal Preview (gated by NEXT_PUBLIC_ENABLE_DEV_SIGNAL_PREVIEW) ──
import { DevSignalPreview } from "@/features/command-center/components/DevSignalPreview";

// ── PDF Export ──

const IO_API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

function exportErrorMessage(status: number): string {
  if (status === 404) return "Report not found. Please re-run the scenario and try again.";
  if (status === 425) return "Report is still generating. Please wait a moment and try again.";
  if (status === 403) return "Report export requires elevated permissions.";
  if (status >= 500) return "Export service temporarily unavailable.";
  return "Report export could not be completed.";
}

async function downloadRunPDF(runId: string, lang: string): Promise<void> {
  const res = await fetch(`/api/v1/runs/${runId}/export?lang=${lang}`, {
    headers: { "X-IO-API-Key": IO_API_KEY },
  });
  if (!res.ok) throw new Error(exportErrorMessage(res.status));
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `impact-observatory-${runId.slice(0, 8)}-${lang}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Loading Skeleton ──

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-io-bg flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-io-accent/30 border-t-io-accent rounded-full animate-spin" />
        <p className="text-sm text-slate-500">Loading intelligence pipeline...</p>
      </div>
    </div>
  );
}

// ── Error State ──

function ErrorState(
  {
    error,
    onRetry,
    onFallbackMock,
  }: {
    error: string;
    onRetry?: () => void;
    onFallbackMock?: () => void;
  }
) {
  return (
    <div className="min-h-screen bg-io-bg flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-lg">!</span>
        </div>
        <h2 className="text-sm font-semibold text-slate-900 mb-2">Pipeline Error</h2>
        <p className="text-xs text-slate-600 mb-4">{error}</p>
        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-io-accent-hover transition-colors"
            >
              Retry
            </button>
          )}
          {onFallbackMock && (
            <button
              onClick={onFallbackMock}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Load Demo Data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// DASHBOARD TAB — Scenario Library + Intelligence Brief
// ══════════════════════════════════════════════════════════════

function DashboardView(
  {
    runId,
    scenario,
    headline,
    narrativeEn,
    narrativeAr,
    macroContext,
    confidence,
    causalChain,
    sectorRollups,
    decisionActions,
    locale,
    onSelectScenario,
    isRunningScenario,
    executiveStatus,
    countryBake,
    sectorFormulas,
    decisionROI,
    outcomeConfirmation,
    collaborationStage,
    demoContract,
  }: {
    runId?: string | null;
    scenario: ReturnType<typeof useCommandCenter>["scenario"];
    headline: ReturnType<typeof useCommandCenter>["headline"];
    narrativeEn?: string;
    narrativeAr?: string;
    macroContext?: ReturnType<typeof useCommandCenter>["macroContext"];
    confidence?: number;
    causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
    sectorRollups: ReturnType<typeof useCommandCenter>["sectorRollups"];
    decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
    locale: "en" | "ar";
    onSelectScenario: (id: string) => void;
    isRunningScenario: boolean;
    executiveStatus: ReturnType<typeof useCommandCenter>["executiveStatus"];
    countryBake: ReturnType<typeof useCommandCenter>["countryBake"];
    sectorFormulas: ReturnType<typeof useCommandCenter>["sectorFormulas"];
    decisionROI: ReturnType<typeof useCommandCenter>["decisionROI"];
    outcomeConfirmation: ReturnType<typeof useCommandCenter>["outcomeConfirmation"];
    collaborationStage: ReturnType<typeof useCommandCenter>["collaborationStage"];
    demoContract?: UnifiedScenarioRun | null;
  }
) {
  const isAr = locale === "ar";
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExportPDF = useCallback(async () => {
    setIsExporting(true);
    setExportError(null);
    try {
      // Live mode: download from backend API
      if (runId) {
        await downloadRunPDF(runId, locale);
        return;
      }
      // Demo/mock mode: generate client-side PDF from intelligence engine data
      if (scenario && headline) {
        const payload: PdfExportPayload = {
          scenario,
          headline,
          narrativeEn: narrativeEn ?? "",
          confidence: confidence ?? 0.84,
          causalChain,
          executiveStatus: executiveStatus ?? null,
          countryBake: countryBake ?? [],
          sectorFormulas: sectorFormulas ?? [],
          decisionROI: decisionROI ?? [],
          outcomeConfirmation: outcomeConfirmation ?? null,
          demoContract: demoContract ?? null,
          sectorRollups: sectorRollups as PdfExportPayload["sectorRollups"],
        };
        generateScenarioPdf(payload);
        return;
      }
      throw new Error("No scenario data available for export.");
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  }, [runId, locale, scenario, headline, narrativeEn, confidence, causalChain, executiveStatus, countryBake, sectorFormulas, decisionROI, outcomeConfirmation, demoContract, sectorRollups]);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Executive Intelligence Brief ── */}
      {scenario && headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900">
              {isAr ? "الإحاطة التنفيذية" : "Executive Briefing"}
            </h2>
            <div className="flex items-center gap-3">
              <span className="text-xs text-io-secondary">
                {isAr ? scenario.labelAr || scenario.label : scenario.label}
              </span>
              <button
                onClick={handleExportPDF}
                disabled={isExporting}
                className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-io-border bg-white text-io-primary hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                {isExporting ? (
                  <>
                    <span className="w-3 h-3 border border-io-secondary/40 border-t-io-secondary rounded-full animate-spin" />
                    {isAr ? "جارٍ التصدير..." : "Exporting..."}
                  </>
                ) : (
                  <>
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 10v3a1 1 0 01-1 1H3a1 1 0 01-1-1v-3M8 2v8M5 7l3 3 3-3" />
                    </svg>
                    {isAr ? "تصدير PDF" : "Export PDF"}
                  </>
                )}
              </button>
            </div>
          </div>
          {exportError && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
              {exportError}
            </div>
          )}

          {/* Executive Summary Line */}
          <div className="bg-io-accent/5 border border-io-accent/15 rounded-lg p-4 mb-5">
            <p className="text-sm text-slate-800 leading-relaxed">
              {isAr
                ? (narrativeAr || narrativeEn || `خسائر متوقعة بقيمة $${(headline.totalLossUsd / 1e9).toFixed(1)} مليار عبر ${headline.propagationDepth} قنوات انتقال — ذروة الضغط في اليوم ${headline.peakDay}`)
                : (narrativeEn || narrativeAr || `$${(headline.totalLossUsd / 1e9).toFixed(1)}B projected loss across ${headline.propagationDepth} transmission channels — stress peaks Day ${headline.peakDay}`)}
            </p>
          </div>

          {/* Headline Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
            <MetricCard
              label={isAr ? "الخسارة الرئيسية" : "Headline Loss"}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-io-status-severe"
              source="17-stage simulation engine"
              formula="Σ(node_loss) across 42-node GCC graph"
              assumption="Severity-calibrated; Monte Carlo confidence band ±8-12%"
            />
            <MetricCard
              label={isAr ? "متوسط الضغط" : "Avg Stress"}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-io-status-elevated"
              source="Graph propagation engine"
              formula="mean(node.stress) for all impacted nodes"
              assumption="Stress range 0-100%; ≥80% = Severe, ≥65% = High"
            />
            <MetricCard
              label={isAr ? "عمق الانتشار" : "Propagation Depth"}
              value={`${headline.propagationDepth}`}
              color="text-io-accent"
              source="Causal chain trace"
              formula="Max hop count in transmission path"
              assumption="Deeper propagation = wider systemic exposure"
            />
            <MetricCard
              label={isAr ? "يوم الذروة" : "Peak Day"}
              value={`${isAr ? "اليوم" : "Day"} ${headline.peakDay}`}
              color="text-io-status-high"
              source="Scenario peak_day_offset"
              formula="min(scenario.peak_day_offset, horizon_days)"
              assumption="Assumes no secondary shock after initial event"
            />
          </div>

          {/* Propagation Summary — transmission chain visualization */}
          {causalChain && causalChain.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-4 mb-5 shadow-sm">
              <h3 className="text-[10px] font-bold text-io-secondary uppercase tracking-widest mb-3">
                {isAr ? "مسار الانتقال الرئيسي" : "Primary Transmission Path"}
              </h3>
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                {causalChain.slice(0, 5).map((step, idx) => (
                  <React.Fragment key={idx}>
                    <div className="flex-shrink-0 bg-slate-50 border border-slate-200 rounded-lg px-3.5 py-2.5 text-center min-w-[110px] hover:bg-slate-100 transition-colors">
                      <p className="text-[11px] font-semibold text-slate-900 truncate">{step.entity_label}</p>
                      <p className="text-[10px] text-io-status-elevated tabular-nums mt-1 font-medium">
                        {step.stress_delta > 0 ? "+" : ""}{(step.stress_delta * 100).toFixed(0)}%
                      </p>
                    </div>
                    {idx < Math.min(causalChain.length, 5) - 1 && (
                      <div className="flex-shrink-0 flex items-center">
                        <div className="w-4 h-px bg-io-accent/40" />
                        <svg width="8" height="8" viewBox="0 0 8 8" className="text-io-accent/60 -ml-px flex-shrink-0">
                          <path d="M1 1L4 4L1 7" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Top Decision — owner/timing per Sarah */}
          {decisionActions && decisionActions.length > 0 && (() => {
            const top = [...decisionActions].sort((a: any, b: any) => a.priority - b.priority)[0] as any;
            return (
              <div className="border border-io-accent/20 bg-io-accent/5 rounded-lg p-4 mb-5">
                <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-2">
                  {isAr ? "القرار الأول — مطلوب الآن" : "Priority Decision — Required Now"}
                </h3>
                <p className="text-sm font-semibold text-slate-900 mb-2">
                  {isAr && top.action_ar ? top.action_ar : top.action}
                </p>
                <div className="flex flex-wrap gap-3 text-xs text-io-secondary">
                  {top.owner && (
                    <span><span className="font-medium text-slate-700">{isAr ? "المسؤول:" : "Owner:"}</span> {top.owner}</span>
                  )}
                  {top.time_to_act_hours != null && (
                    <span><span className="font-medium text-slate-700">{isAr ? "الوقت المتاح:" : "Window:"}</span> {top.time_to_act_hours}h</span>
                  )}
                  {top.loss_avoided_usd > 0 && (
                    <span><span className="font-medium text-slate-700">{isAr ? "خسائر متجنبة:" : "Loss avoided:"}</span> ${(top.loss_avoided_usd / 1e9).toFixed(1)}B</span>
                  )}
                  {top.cost_usd > 0 && (
                    <span><span className="font-medium text-slate-700">{isAr ? "التكلفة:" : "Cost:"}</span> ${(top.cost_usd / 1e6).toFixed(0)}M</span>
                  )}
                </div>
              </div>
            );
          })()}

          {/* System Risk + Confidence */}
          <div className="flex items-center gap-4 text-xs">
            {macroContext?.system_risk_index != null && (
              <span className="px-2 py-1 rounded bg-io-status-severe/10 text-io-status-severe font-semibold">
                {isAr ? "مخاطر النظام" : "System Risk"}: {(macroContext.system_risk_index * 100).toFixed(0)}%
              </span>
            )}
            {confidence != null && (
              <span className="px-2 py-1 rounded bg-io-accent/10 text-io-accent font-semibold">
                {isAr ? "الثقة" : "Confidence"}: {(confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Executive Status Engine ── */}
      {executiveStatus && executiveStatus.status !== "STABLE" && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900">
              {isAr ? "حالة القرار التنفيذي" : "Executive Decision Status"}
            </h2>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                executiveStatus.status === "CRITICAL" ? "bg-io-status-severe/15 text-io-status-severe" :
                executiveStatus.status === "SEVERE" ? "bg-io-status-high/15 text-io-status-high" :
                executiveStatus.status === "ELEVATED" ? "bg-io-status-elevated/15 text-io-status-elevated" :
                "bg-io-status-guarded/15 text-io-status-guarded"
              }`}>
                {isAr ? executiveStatus.statusAr : executiveStatus.status}
              </span>
              <span className={`px-2 py-1 rounded text-[10px] font-semibold ${
                executiveStatus.decisionUrgency === "IMMEDIATE" ? "bg-red-100 text-red-800" :
                executiveStatus.decisionUrgency === "URGENT" ? "bg-amber-100 text-amber-800" :
                "bg-blue-100 text-blue-800"
              }`}>
                {executiveStatus.decisionUrgency}
                {executiveStatus.decisionUrgencyHours > 0 && ` (${executiveStatus.decisionUrgencyHours}h)`}
              </span>
            </div>
          </div>

          <p className="text-sm text-slate-700 mb-3">
            {isAr ? executiveStatus.severityRationaleAr : executiveStatus.severityRationale}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {executiveStatus.affectedCountries.length > 0 && (
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                  {isAr ? "الدول المتأثرة" : "Affected Countries"}
                </p>
                <p className="text-xs font-semibold text-slate-900">{executiveStatus.affectedCountries.join(", ")}</p>
              </div>
            )}
            {executiveStatus.affectedSectors.length > 0 && (
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                  {isAr ? "القطاعات المتأثرة" : "Affected Sectors"}
                </p>
                <p className="text-xs font-semibold text-slate-900">{executiveStatus.affectedSectors.join(", ")}</p>
              </div>
            )}
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                {isAr ? "ثقة التقييم" : "Assessment Confidence"}
              </p>
              <p className="text-xs font-semibold text-io-accent">{(executiveStatus.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>
      )}

      {/* ── GCC Country Exposure Layer ── */}
      {countryBake && countryBake.length > 0 && headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {isAr ? "تعرض الدول الخليجية" : "GCC Country Exposure"}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {countryBake.filter(c => c.exposureUsd > 0 || c.stressPercent > 0).map(country => (
              <div key={country.code} className="bg-slate-50 rounded-lg p-4 group relative">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold text-slate-900">
                    {isAr ? country.nameAr : country.name}
                  </p>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    country.stressPercent >= 0.65 ? "bg-io-status-severe/15 text-io-status-severe" :
                    country.stressPercent >= 0.45 ? "bg-io-status-elevated/15 text-io-status-elevated" :
                    country.stressPercent >= 0.2 ? "bg-io-status-guarded/15 text-io-status-guarded" :
                    "bg-io-accent/10 text-io-accent"
                  }`}>
                    {(country.stressPercent * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-slate-600">
                  <p>
                    <span className="font-medium text-slate-700">{isAr ? "التعرض:" : "Exposure:"}</span>{" "}
                    ${(country.exposureUsd / 1e9).toFixed(2)}B
                  </p>
                  <p>
                    <span className="font-medium text-slate-700">{isAr ? "القطاع الرئيسي:" : "Primary Sector:"}</span>{" "}
                    {isAr ? country.primarySectorAr : country.primarySector}
                  </p>
                  <p>
                    <span className="font-medium text-slate-700">{isAr ? "المحرك:" : "Driver:"}</span>{" "}
                    {isAr ? country.primaryDriverAr : country.primaryDriver}
                  </p>
                </div>
                {/* Hover detail */}
                <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-[10px] text-slate-600 space-y-1 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                  <p><span className="font-semibold text-slate-700">{isAr ? "قناة الانتقال:" : "Transmission:"}</span> {isAr ? country.transmissionChannelAr : country.transmissionChannel}</p>
                  <p><span className="font-semibold text-slate-700">{isAr ? "أداة السياسة:" : "Policy Lever:"}</span> {isAr ? country.policyLeverAr : country.policyLever}</p>
                  <p><span className="font-semibold text-slate-700">{isAr ? "الثقة:" : "Confidence:"}</span> {(country.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Sector Formula Lab ── */}
      {sectorFormulas && sectorFormulas.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {isAr ? "مختبر صيغ القطاعات" : "Sector Formula Lab"}
          </h2>
          <div className="space-y-2">
            {sectorFormulas.map(sf => (
              <div key={sf.sector} className="bg-slate-50 rounded-lg p-4 group relative">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-slate-900">{sf.sectorLabel}</p>
                  <span className="text-sm font-bold text-io-status-severe tabular-nums">
                    ${(sf.sectorLoss / 1e9).toFixed(2)}B
                  </span>
                </div>
                <div className="flex flex-wrap gap-3 text-[10px] text-slate-500">
                  <span>Allocation: {(sf.allocationWeight * 100).toFixed(0)}%</span>
                  <span>Sensitivity: {(sf.scenarioSensitivity * 100).toFixed(0)}%</span>
                  <span>Propagation: {(sf.propagationWeight * 100).toFixed(0)}%</span>
                  <span>Confidence: {(sf.confidence * 100).toFixed(0)}%</span>
                </div>
                {/* Hover provenance */}
                <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-[10px] text-slate-600 space-y-1 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                  <p><span className="font-semibold text-slate-700">Formula:</span> {sf.formula}</p>
                  <p><span className="font-semibold text-slate-700">Source:</span> {sf.source}</p>
                  <p><span className="font-semibold text-slate-700">Assumption:</span> {sf.assumption}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Decision ROI Summary ── */}
      {decisionROI && decisionROI.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {isAr ? "عائد الاستثمار على القرار" : "Decision ROI Engine"}
          </h2>
          <div className="space-y-3">
            {decisionROI.slice(0, 5).map(roi => (
              <div key={roi.id} className="bg-slate-50 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-sm font-semibold text-slate-900 flex-1">
                    {isAr ? roi.actionAr : roi.action}
                  </p>
                  <span className={`ml-2 px-2 py-0.5 rounded text-[10px] font-bold tabular-nums ${
                    roi.roiMultiple >= 5 ? "bg-green-100 text-green-800" :
                    roi.roiMultiple >= 2 ? "bg-emerald-100 text-emerald-700" :
                    "bg-slate-200 text-slate-700"
                  }`}>
                    {roi.roiMultiple.toFixed(1)}x ROI
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-600 mb-2">
                  <span><span className="font-medium text-slate-700">{isAr ? "التكلفة:" : "Cost:"}</span> ${(roi.costUsd / 1e6).toFixed(0)}M</span>
                  <span><span className="font-medium text-slate-700">{isAr ? "خسائر متجنبة:" : "Avoided:"}</span> ${(roi.lossAvoidedUsd / 1e9).toFixed(2)}B</span>
                  <span><span className="font-medium text-slate-700">{isAr ? "صافي الفائدة:" : "Net:"}</span> ${(roi.netBenefit / 1e9).toFixed(2)}B</span>
                  <span><span className="font-medium text-slate-700">{isAr ? "المسؤول:" : "Owner:"}</span> {roi.owner}</span>
                </div>
                {roi.deadlineHours > 0 && (
                  <div className="flex items-center gap-3 text-[10px] text-slate-500">
                    <span className="font-medium text-amber-700">{isAr ? "الموعد النهائي:" : "Deadline:"} {roi.deadlineHours}h</span>
                    <span>{isAr ? roi.consequenceOfDelayAr : roi.consequenceOfDelay}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Outcome Counterfactual ── */}
      {outcomeConfirmation && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {isAr ? "تأكيد النتائج — المقارنة المضادة" : "Outcome Confirmation — Counterfactual"}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Without Action */}
            <div className="border border-red-200 bg-red-50/50 rounded-lg p-4">
              <p className="text-[10px] text-red-600 uppercase tracking-wider font-semibold mb-2">
                {isAr ? "بدون تدخل" : "Without Intervention"}
              </p>
              <p className="text-lg font-bold text-red-800 tabular-nums mb-1">
                ${(outcomeConfirmation.withoutAction.projectedLossLow / 1e9).toFixed(1)}B – ${(outcomeConfirmation.withoutAction.projectedLossHigh / 1e9).toFixed(1)}B
              </p>
              <p className="text-xs text-red-700">
                {isAr ? `التعافي: ${outcomeConfirmation.withoutAction.recoveryDays} يوم` : `Recovery: ${outcomeConfirmation.withoutAction.recoveryDays} days`}
              </p>
              <p className="text-[10px] text-slate-600 mt-2">
                {isAr ? outcomeConfirmation.withoutAction.descriptionAr : outcomeConfirmation.withoutAction.description}
              </p>
            </div>
            {/* Coordinated Response */}
            <div className="border border-emerald-200 bg-emerald-50/50 rounded-lg p-4">
              <p className="text-[10px] text-emerald-600 uppercase tracking-wider font-semibold mb-2">
                {isAr ? "استجابة منسقة" : "Coordinated Response"}
              </p>
              <p className="text-lg font-bold text-emerald-800 tabular-nums mb-1">
                ${(outcomeConfirmation.coordinatedResponse.projectedLossLow / 1e9).toFixed(1)}B – ${(outcomeConfirmation.coordinatedResponse.projectedLossHigh / 1e9).toFixed(1)}B
              </p>
              <p className="text-xs text-emerald-700">
                {isAr ? `التعافي: ${outcomeConfirmation.coordinatedResponse.recoveryDays} يوم` : `Recovery: ${outcomeConfirmation.coordinatedResponse.recoveryDays} days`}
              </p>
              <p className="text-[10px] text-slate-600 mt-2">
                {isAr ? outcomeConfirmation.coordinatedResponse.descriptionAr : outcomeConfirmation.coordinatedResponse.description}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <span className="px-2 py-1 rounded bg-emerald-100 text-emerald-800 font-semibold">
              {isAr ? "تخفيض الخسائر:" : "Loss Reduction:"} {outcomeConfirmation.expectedLossReductionPercent}%
            </span>
            <span className="px-2 py-1 rounded bg-blue-100 text-blue-800 font-semibold">
              {isAr ? "تقليل أفق التعافي:" : "Recovery Shortened:"} {outcomeConfirmation.recoveryHorizonReduction} {isAr ? "يوم" : "days"}
            </span>
            <span className="px-2 py-1 rounded bg-slate-100 text-slate-700 font-semibold">
              {isAr ? "التتبع:" : "Tracking:"} {outcomeConfirmation.outcomeTrackingStatus}
            </span>
          </div>
        </div>
      )}

      {/* ── Collaboration / Executive Stage ── */}
      {collaborationStage && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900">
              {isAr ? "مرحلة التعاون التنفيذي" : "Executive Collaboration Stage"}
            </h2>
            <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold ${
              collaborationStage.approvalState === "APPROVED" ? "bg-green-100 text-green-800" :
              collaborationStage.approvalState === "UNDER_REVIEW" ? "bg-amber-100 text-amber-800" :
              collaborationStage.approvalState === "REJECTED" ? "bg-red-100 text-red-800" :
              "bg-slate-100 text-slate-700"
            }`}>
              {collaborationStage.approvalState}
            </span>
          </div>
          {/* Reviewer Status */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            {collaborationStage.reviewers.map(r => (
              <div key={r.role} className="bg-slate-50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{r.role}</p>
                <p className="text-xs font-semibold text-slate-900">{r.name}</p>
                <span className={`inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-bold ${
                  r.status === "APPROVED" ? "bg-green-100 text-green-700" :
                  r.status === "REJECTED" ? "bg-red-100 text-red-700" :
                  "bg-slate-200 text-slate-600"
                }`}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
          {/* Persona Focus Views */}
          <div className="space-y-2 mb-4">
            <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-3">
              <p className="text-[9px] text-blue-600 uppercase tracking-wider font-semibold mb-1">
                {isAr ? "منظور الرئيس التنفيذي" : "CEO View"}
              </p>
              <p className="text-xs text-slate-700">{isAr ? collaborationStage.personaViews.ceo.focusAr : collaborationStage.personaViews.ceo.focus}</p>
            </div>
            <div className="bg-amber-50/50 border border-amber-200 rounded-lg p-3">
              <p className="text-[9px] text-amber-600 uppercase tracking-wider font-semibold mb-1">
                {isAr ? "منظور إدارة المخاطر" : "Risk Officer View"}
              </p>
              <p className="text-xs text-slate-700">{isAr ? collaborationStage.personaViews.risk.focusAr : collaborationStage.personaViews.risk.focus}</p>
            </div>
            <div className="bg-purple-50/50 border border-purple-200 rounded-lg p-3">
              <p className="text-[9px] text-purple-600 uppercase tracking-wider font-semibold mb-1">
                {isAr ? "منظور الرقابة" : "Regulator View"}
              </p>
              <p className="text-xs text-slate-700">{isAr ? collaborationStage.personaViews.regulator.focusAr : collaborationStage.personaViews.regulator.focus}</p>
            </div>
          </div>
          {/* Audit Trail */}
          {collaborationStage.auditTrail.length > 0 && (
            <div className="border-t border-slate-200 pt-3">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-2">
                {isAr ? "سجل التدقيق" : "Audit Trail"}
              </p>
              <div className="space-y-1">
                {collaborationStage.auditTrail.map((e, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-[10px] text-slate-600">
                    <span className="text-slate-400 tabular-nums flex-shrink-0">{new Date(e.timestamp).toLocaleTimeString()}</span>
                    <span className="font-medium text-slate-700">{e.actor}</span>
                    <span>{e.detail}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Scenario Library ── */}
      <div>
        <h2 className="text-base font-bold text-slate-900 mb-4">
          {isAr ? "مكتبة السيناريوهات" : "Scenario Library"}
        </h2>
        <ScenarioLibrary
          onSelectScenario={onSelectScenario}
          isLoading={isRunningScenario}
          locale={locale}
        />
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COUNTRY EXPOSURE MATRIX — GCC Exposure Tab primary view
// ══════════════════════════════════════════════════════════════

function CountryExposureMatrix({ countryBake, locale }: { countryBake: CountryBakeEntry[]; locale: "en" | "ar" }) {
  const isAr = locale === "ar";
  const hasData = countryBake.some(c => c.exposureUsd > 0);

  const stressBadge = (pct: number) => {
    if (pct >= 80) return { bg: "bg-io-status-severe/15", text: "text-io-status-severe", label: isAr ? "حرج" : "SEVERE" };
    if (pct >= 65) return { bg: "bg-io-status-high/15", text: "text-io-status-high", label: isAr ? "عالي" : "HIGH" };
    if (pct >= 50) return { bg: "bg-io-status-elevated/15", text: "text-io-status-elevated", label: isAr ? "مرتفع" : "ELEVATED" };
    if (pct >= 35) return { bg: "bg-io-status-guarded/15", text: "text-io-status-guarded", label: isAr ? "حذر" : "GUARDED" };
    return { bg: "bg-io-accent/10", text: "text-io-accent", label: isAr ? "منخفض" : "LOW" };
  };

  const fmtUsd = (v: number) => {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
    return `$${(v / 1e3).toFixed(0)}K`;
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm" dir={isAr ? "rtl" : "ltr"}>
      <h2 className="text-base font-bold text-slate-900 mb-1">
        {isAr ? "مصفوفة تعرض الدول" : "Country Exposure Matrix"}
      </h2>
      <p className="text-xs text-slate-500 mb-4">
        {isAr ? "٦ دول — الإجهاد والخسارة والقطاع والمحرك والثقة والسياسة" : "6 nations — stress, estimated loss, primary sector, driver, confidence, policy lever"}
      </p>
      {!hasData ? (
        <p className="text-sm text-slate-400 text-center py-8">
          {isAr ? "اختر سيناريو لعرض بيانات التعرض" : "Select a scenario to view exposure data"}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <th className="pb-2 pr-3">{isAr ? "الدولة" : "Country"}</th>
                <th className="pb-2 pr-3 tabular-nums">{isAr ? "الضغط" : "Stress"}</th>
                <th className="pb-2 pr-3 tabular-nums">{isAr ? "الخسارة" : "Est. Loss"}</th>
                <th className="pb-2 pr-3">{isAr ? "القطاع" : "Primary Sector"}</th>
                <th className="pb-2 pr-3">{isAr ? "المحرك" : "Driver"}</th>
                <th className="pb-2 pr-3 tabular-nums">{isAr ? "الثقة" : "Confidence"}</th>
                <th className="pb-2">{isAr ? "الأداة السياسية" : "Policy Lever"}</th>
              </tr>
            </thead>
            <tbody>
              {countryBake.map(c => {
                const badge = stressBadge(c.stressPercent);
                return (
                  <tr key={c.code} className="border-b border-slate-100">
                    <td className="py-2.5 pr-3 font-medium text-slate-900">
                      {isAr ? c.nameAr : c.name}
                    </td>
                    <td className="py-2.5 pr-3">
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${badge.bg} ${badge.text}`}>
                        {c.stressPercent.toFixed(0)}% <span className="font-medium">{badge.label}</span>
                      </span>
                    </td>
                    <td className="py-2.5 pr-3 tabular-nums font-semibold text-io-status-severe">
                      {fmtUsd(c.exposureUsd)}
                    </td>
                    <td className="py-2.5 pr-3 text-slate-700">
                      {isAr ? c.primarySectorAr : c.primarySector}
                    </td>
                    <td className="py-2.5 pr-3 text-slate-600 max-w-[200px] truncate">
                      {isAr ? c.primaryDriverAr : c.primaryDriver}
                    </td>
                    <td className="py-2.5 pr-3 tabular-nums text-io-accent font-semibold">
                      {(c.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="py-2.5 text-slate-600 max-w-[180px] truncate">
                      {isAr ? c.policyLeverAr : c.policyLever}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function MetricCard(
  { label, value, color, source, formula, assumption }: {
    label: string;
    value: string;
    color: string;
    source?: string;
    formula?: string;
    assumption?: string;
  }
) {
  const [showDetail, setShowDetail] = useState(false);
  const hasProvenance = source || formula || assumption;

  return (
    <div
      className="bg-white border border-slate-200 rounded-lg p-3.5 relative group shadow-sm hover:shadow-md transition-shadow"
      onMouseEnter={() => hasProvenance && setShowDetail(true)}
      onMouseLeave={() => setShowDetail(false)}
    >
      <div className="flex items-start justify-between">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1.5">{label}</p>
        {hasProvenance && (
          <span className="text-[9px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity cursor-help">
            ⓘ
          </span>
        )}
      </div>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {showDetail && hasProvenance && (
        <div className="absolute z-20 top-full left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-[11px] text-slate-600 space-y-1.5">
          {source && <p><span className="font-semibold text-slate-700">Source:</span> {source}</p>}
          {formula && <p><span className="font-semibold text-slate-700">Formula:</span> {formula}</p>}
          {assumption && <p><span className="font-semibold text-slate-700">Assumption:</span> {assumption}</p>}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// MACRO INTELLIGENCE VIEW — Top-down flow with enterprise cards
// ══════════════════════════════════════════════════════════════

function MacroIntelligenceView(
  {
    scenario,
    headline,
    narrativeEn,
    narrativeAr,
    macroContext,
    confidence,
    causalChain,
    sectorRollups,
    decisionActions,
    trust,
    locale,
  }: {
    scenario: ReturnType<typeof useCommandCenter>["scenario"];
    headline: ReturnType<typeof useCommandCenter>["headline"];
    narrativeEn?: string;
    narrativeAr?: string;
    macroContext?: ReturnType<typeof useCommandCenter>["macroContext"];
    confidence?: number;
    causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
    sectorRollups: ReturnType<typeof useCommandCenter>["sectorRollups"];
    decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
    trust?: ReturnType<typeof useCommandCenter>["trust"];
    locale: "en" | "ar";
  }
) {
  const isAr = locale === "ar";

  const sectionLabel = (en: string, ar: string) => (isAr ? ar : en);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* 1. Macro Shock */}
      {headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              1
            </span>
            {sectionLabel("Macro Shock", "الصدمة الكلية")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label={sectionLabel("Headline Loss", "الخسارة الرئيسية")}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-io-status-severe"
            />
            <MetricCard
              label={sectionLabel("Avg Stress", "متوسط الضغط")}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-io-status-elevated"
            />
            <MetricCard
              label={sectionLabel("Propagation Depth", "عمق الانتشار")}
              value={`${headline.propagationDepth}`}
              color="text-io-accent"
            />
            <MetricCard
              label={sectionLabel("Peak Day", "يوم الذروة")}
              value={`Day ${headline.peakDay}`}
              color="text-io-status-high"
            />
          </div>
        </div>
      )}

      {/* 1b. Macro Indicators — enriched institutional panel */}
      {macroContext && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              &#9670;
            </span>
            {sectionLabel("Macro-Financial Indicators", "المؤشرات الاقتصادية والمالية الكلية")}
          </h3>
          {/* Real macro signals from the pipeline — shown when available */}
          {macroContext.macro_signals && macroContext.macro_signals.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {macroContext.macro_signals.slice(0, 8).map((sig: any) => (
                <div key={sig.id || sig.name_en} className="bg-slate-50 rounded-lg p-2.5 group relative">
                  <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-0.5">
                    {isAr ? sig.name_ar : sig.name_en}
                  </p>
                  <p className={`text-sm font-bold tabular-nums ${
                    sig.impact === "high" ? "text-io-status-severe"
                    : sig.impact === "medium" ? "text-io-status-elevated"
                    : "text-io-status-guarded"
                  }`}>
                    {sig.value}
                  </p>
                  <p className="text-[8px] text-slate-400 mt-0.5">
                    {isAr ? "من محرك المحاكاة" : "From simulation engine"}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            /* Derived indicators when no macro signals available */
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MetricCard
                label={sectionLabel("System Risk Index", "مؤشر المخاطر")}
                value={`${(macroContext.system_risk_index * 100).toFixed(0)}%`}
                color="text-io-status-high"
                source="Unified Risk Score (URS)"
                formula="Weighted avg of sector stress indices"
              />
              <MetricCard
                label={sectionLabel("Contagion Risk", "مخاطر العدوى")}
                value={`${(macroContext.system_risk_index * 100).toFixed(0)}%`}
                color="text-io-status-elevated"
                source="Graph propagation depth"
                formula="Correlated with system_risk_index"
              />
            </div>
          )}
        </div>
      )}

      {/* 2. Transmission Channels */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              2
            </span>
            {sectionLabel("Transmission Channels", "قنوات الانتقال")}
          </h3>
          <div className="space-y-2">
            {causalChain.slice(0, 5).map((link, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-slate-50 p-3 rounded-lg">
                <div className="text-xs font-semibold text-slate-500 mt-0.5">→</div>
                <div className="flex-1">
                  <p className="text-sm text-slate-700">{link.entity_label}: {link.event}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Sector Impact */}
      {sectorRollups && Object.keys(sectorRollups).length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              3
            </span>
            {sectionLabel("Sector Impact", "تأثير القطاع")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(sectorRollups).map(([sector, data]: any) => {
              const stress = data?.aggregate_stress ?? data?.stress ?? 0;
              const loss = data?.total_loss ?? data?.loss_usd ?? 0;
              const sectorLabel = sector.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase());
              return (
                <div key={sector} className="bg-slate-50 rounded-lg p-3 group relative">
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                    {sectorLabel}
                  </p>
                  <p className="text-sm font-bold text-slate-900">
                    {(stress * 100).toFixed(0)}% stress
                  </p>
                  <p className="text-xs text-slate-600">
                    {loss > 0 ? `Loss: $${(loss / 1e9).toFixed(1)}B` : ""}
                  </p>
                  <p className="text-[8px] text-slate-400 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {isAr ? "التخصيص × الإجهاد × الانتشار" : "allocation × stress × propagation weight"}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Entity Exposure */}
      {scenario && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              4
            </span>
            {sectionLabel("Entity Exposure", "تعريض الكيانات")}
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-700">
              {isAr
                ? `السيناريو: ${scenario.labelAr || scenario.label}`
                : `Scenario: ${scenario.label}`}
            </p>
            <p className="text-xs text-slate-600 mt-2">
              {isAr ? "الحساسية: " : "Sensitivity: "}
              <span className="font-semibold text-slate-700">
                {scenario.severity != null ? `${(scenario.severity * 100).toFixed(0)}%` : "—"}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* 5. Decision Actions */}
      {decisionActions && decisionActions.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              5
            </span>
            {sectionLabel("Decision Actions", "إجراءات القرار")}
          </h3>
          <div className="space-y-2">
            {decisionActions.slice(0, 5).map((action: any, idx: number) => (
              <div key={idx} className="bg-slate-50 p-3 rounded-lg">
                <p className="text-sm font-semibold text-slate-900">
                  {action.title || action.label || `Action ${idx + 1}`}
                </p>
                {action.rationale && (
                  <p className="text-xs text-slate-600 mt-1">{action.rationale}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Value / ROI */}
      {macroContext && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              6
            </span>
            {sectionLabel("Value / ROI", "القيمة / العائد")}
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-700">
              {sectionLabel("System Risk Index: ", "مؤشر مخاطر النظام: ")}
              <span className="font-semibold text-io-status-severe">
                {macroContext?.system_risk_index ? `${(macroContext.system_risk_index * 100).toFixed(0)}` : "—"}%
              </span>
            </p>
            {macroContext?.macro_signals && (
              <p className="text-xs text-slate-600 mt-2">
                {isAr ? "الإشارات: " : "Signals: "}
                {Array.isArray(macroContext.macro_signals)
                  ? macroContext.macro_signals.join(", ")
                  : String(macroContext.macro_signals)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 7. Trust / Confidence / Audit */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4">
          <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
            7
          </span>
          {sectionLabel("Trust / Confidence / Audit", "الثقة / الموثوقية / التدقيق")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Confidence", "الثقة")}
            </p>
            <p className="text-lg font-bold text-io-accent">
              {confidence != null && confidence > 0 ? `${(confidence * 100).toFixed(0)}%` : "—"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Methodology", "المنهجية")}
            </p>
            <p className="text-xs text-slate-600">
              {(trust as any)?.methodology_confidence
                ? `${((trust as any).methodology_confidence * 100).toFixed(0)}% confidence`
                : "Standard pipeline"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Data Quality", "جودة البيانات")}
            </p>
            <p className="text-xs text-slate-600">
              {(trust as any)?.data_quality_score
                ? `${((trust as any).data_quality_score * 100).toFixed(0)}% quality`
                : "Enterprise grade"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// DEMO DATA BANNER — explicit, never silent
// ══════════════════════════════════════════════════════════════

function DemoDataBanner({ locale, demoContract }: { locale: "en" | "ar"; demoContract: UnifiedScenarioRun | null }) {
  const isAr = locale === "ar";

  if (!demoContract || demoContract.mode === "live") return null;

  const isSeeded = demoContract.dataSourceType === "seeded_institutional";
  const sourceLabel = isSeeded
    ? (isAr ? "بيانات مرجعية مؤسسية محملة" : "Reference Demo Dataset Loaded")
    : (isAr ? "بيانات مرجعية محملة — الخادم غير متصل" : "Reference Dataset Loaded — No Backend Connected");

  // Blue for explicit demo, amber for implicit fallback
  const bgColor = isSeeded ? "bg-blue-50 border-blue-200" : "bg-amber-50 border-amber-200";
  const dotColor = isSeeded ? "bg-blue-500" : "bg-amber-500";
  const textColor = isSeeded ? "text-blue-800" : "text-amber-800";
  const metaColor = isSeeded ? "text-blue-600" : "text-amber-600";

  return (
    <div className={`flex items-center justify-between px-4 py-2 ${bgColor} border-b flex-shrink-0`}>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${dotColor} animate-pulse`} />
        <p className={`text-[11px] font-semibold ${textColor}`}>
          {sourceLabel}
        </p>
      </div>
      <div className={`flex items-center gap-2.5 text-[10px] font-medium ${metaColor}`}>
        <span>{isAr ? "المصدر:" : "Source:"} {demoContract.provenance.join(" → ")}</span>
        <span className="opacity-30">|</span>
        <span>{isAr ? "الثقة:" : "Confidence:"} {(demoContract.confidence * 100).toFixed(0)}%</span>
        <span className="opacity-30">|</span>
        <span className="tabular-nums">{demoContract.generatedAt ? new Date(demoContract.generatedAt).toLocaleTimeString() : ""}</span>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// INNER PAGE — reads searchParams, orchestrates tabs
// ══════════════════════════════════════════════════════════════

function CommandCenterInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const language = useAppStore((s) => s.language);
  const locale = language as "en" | "ar";

  const runId = searchParams.get("run");
  const activeTab = searchParams.get("tab") || "dashboard";
  const isDemoParam = searchParams.get("demo") === "true";
  const scenarioParam = searchParams.get("scenario");
  const [isRunningScenario, setIsRunningScenario] = useState(false);
  const [scenarioUnavailableId, setScenarioUnavailableId] = useState<string | null>(null);
  const [simulationLoadedLabel, setSimulationLoadedLabel] = useState<string | null>(null);

  // ── Data Trust Layer (read-only provenance metadata) ──
  const scenarioIdForTrust = scenarioParam || "hormuz_chokepoint_disruption";
  const dataTrustMeta = useDataTrust(scenarioIdForTrust);

  // ── Demo contract from store ──
  const demoContract = useCommandCenterStore((s) => s.demoContract);
  const setDemoContract = useCommandCenterStore((s) => s.setDemoContract);

  const {
    status,
    error,
    dataSource,
    scenario,
    headline,
    causalChain,
    sectorRollups,
    decisionActions,
    graphNodes,
    sectorImpacts,
    impacts,
    narrativeEn,
    confidence,
    trust,

    // Deep-dive data
    decisionTrust,
    decisionIntegration,
    decisionValue,
    governance,
    pilot,

    // Decision Trust Layer
    metricExplanations,
    decisionTransparencyResult,

    // Decision Reliability Layer
    reliabilityPayload,

    // Explainability Layer
    narrativeAr,
    macroContext,

    // Actions
    executeAction,
    switchToMock,
    switchToLive,
    switchScenario,

    // Phase 6: Intelligence Engine
    executiveStatus,
    countryBake,
    sectorFormulas,
    bankingSimulation,
    insuranceSimulation,
    decisionROI,
    outcomeConfirmation,
    collaborationStage,
  } = useCommandCenter(runId);

  // ── Effective demo mode: explicit ?demo=true OR implicit mock fallback ──
  // Eliminates silent fallback — any mock-data state gets an explicit banner
  const isDemoMode = isDemoParam || (dataSource === "mock" && !runId);

  // ── Initialize and maintain demo contract ──
  const resolvedConfidence = confidence && confidence > 0 ? confidence : 0.87;

  useEffect(() => {
    if (!isDemoMode) return;

    const currentContract = useCommandCenterStore.getState().demoContract;

    if (!currentContract) {
      // First init — distinguish explicit demo from implicit mock fallback
      const isExplicitDemo = isDemoParam;
      const activeTemplateId = scenario?.templateId ?? "hormuz_chokepoint_disruption";
      const hasFullPayload = !!TEMPLATE_TO_SCENARIO_KEY[activeTemplateId];
      const contract: UnifiedScenarioRun = {
        scenarioId: activeTemplateId,
        runId: "demo_seeded",
        locale,
        mode: isExplicitDemo ? "demo" : "hybrid",
        dataSourceType: isExplicitDemo ? "seeded_institutional" : "fallback_mock",
        generatedAt: new Date().toISOString(),
        confidence: resolvedConfidence,
        provenance: isExplicitDemo
          ? ["Seeded Institutional Dataset", "17-Stage Simulation Engine", "Intelligence Engine v6"]
          : ["Mock Fallback", "No Backend Connected", "17-Stage Simulation Engine"],
        fallbackStatus: isExplicitDemo ? "none" : "api_unavailable",
        errorState: isExplicitDemo ? null : "Backend not connected — using reference dataset",
        isScenarioComplete: hasFullPayload,
        missingSections: hasFullPayload ? [] : ["briefing", "macro", "transmission", "exposure", "sector", "decisions", "outcome", "audit"],
      };
      setDemoContract(contract);
      return;
    }

    // Sync changes — locale, scenario, confidence, error
    const needsUpdate =
      currentContract.locale !== locale ||
      (scenario?.templateId && currentContract.scenarioId !== scenario.templateId) ||
      Math.abs(currentContract.confidence - resolvedConfidence) > 0.01 ||
      (error && currentContract.fallbackStatus === "none");

    if (needsUpdate) {
      const updatedTemplateId = scenario?.templateId ?? currentContract.scenarioId;
      const hasPayload = !!TEMPLATE_TO_SCENARIO_KEY[updatedTemplateId];
      setDemoContract({
        ...currentContract,
        locale,
        scenarioId: updatedTemplateId,
        confidence: resolvedConfidence,
        generatedAt: new Date().toISOString(),
        isScenarioComplete: hasPayload,
        missingSections: hasPayload ? [] : currentContract.missingSections,
        ...(error ? { dataSourceType: "fallback_mock" as const, fallbackStatus: "api_unavailable" as const, errorState: error } : {}),
      });
    }
  }, [isDemoMode, isDemoParam, locale, scenario?.templateId, resolvedConfidence, error, setDemoContract]);

  // ── Auto-load scenario from URL param on mount / navigation ──
  // Ensures deep-links like ?scenario=gcc_cyber_attack load the correct dataset
  const scenarioSyncRef = React.useRef<string | null>(null);
  useEffect(() => {
    if (!scenarioParam || !isDemoMode) return;
    // Only switch if the store isn't already on this scenario
    const currentTemplateId = scenario?.templateId;
    if (currentTemplateId === scenarioParam) return;
    // Prevent re-firing for the same URL param
    if (scenarioSyncRef.current === scenarioParam) return;
    scenarioSyncRef.current = scenarioParam;

    const key = TEMPLATE_TO_SCENARIO_KEY[scenarioParam];
    if (key) {
      switchScenario(key);
    }
  }, [scenarioParam, isDemoMode, scenario?.templateId, switchScenario]);

  // ── Scenario selection ──
  // Mock mode: visible simulation transition → switch → tab switch → URL update
  // Live mode: POST /api/v1/runs → navigate to new run
  const handleScenarioSelect = useCallback(
    async (templateId: string) => {
      // In demo/mock mode, switch scenario locally — no backend needed
      if (dataSource === "mock" || isDemoMode) {
        // Resolve scenario key — only commit if full payload exists
        const key = TEMPLATE_TO_SCENARIO_KEY[templateId];
        if (!key) {
          // No full payload for this scenario — show institutional message, do NOT change active scenario
          setScenarioUnavailableId(templateId);
          setSimulationLoadedLabel(null);
          return;
        }

        // ── Phase 1: Visible "Running" state ──
        setScenarioUnavailableId(null);
        setSimulationLoadedLabel(null);
        setIsRunningScenario(true);

        // Brief delay so user sees the "Running..." state on the button
        await new Promise((resolve) => setTimeout(resolve, 600));

        // ── Phase 2: Load scenario data into store ──
        switchScenario(key);

        // ── Phase 3: Update demo contract with unique run identity ──
        const demoRunId = `demo_${templateId}_${Date.now()}`;
        if (isDemoMode) {
          const currentContract = useCommandCenterStore.getState().demoContract;
          if (currentContract) {
            useCommandCenterStore.getState().setDemoContract({
              ...currentContract,
              scenarioId: templateId,
              runId: demoRunId,
              generatedAt: new Date().toISOString(),
              isScenarioComplete: true,
              missingSections: [],
            });
          }
        }

        // ── Phase 4: Navigate to briefing tab with scenario in URL ──
        const params = new URLSearchParams();
        if (isDemoParam) params.set("demo", "true");
        params.set("scenario", templateId);
        // Tab is "dashboard" (briefing) — omit param since it's the default
        router.push(`/command-center?${params.toString()}`);

        // ── Phase 5: Scroll to top so briefing is visible ──
        window.scrollTo({ top: 0, behavior: "smooth" });

        // ── Phase 6: Show "Simulation Loaded" banner ──
        const scenarioTitle =
          SCENARIO_LABELS[templateId]?.[locale === "ar" ? "ar" : "en"] ?? templateId;
        setSimulationLoadedLabel(scenarioTitle);
        setIsRunningScenario(false);

        // Auto-dismiss the loaded banner after 6 seconds
        setTimeout(() => setSimulationLoadedLabel(null), 6000);
        return;
      }

      // Live mode: call backend API
      setIsRunningScenario(true);
      setSimulationLoadedLabel(null);
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(`${API_BASE}/api/v1/runs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ template_id: templateId, severity: 0.75 }),
        });
        if (!res.ok) {
          switchToMock();
          return;
        }
        const json = await res.json();
        const newRunId = json?.data?.run_id ?? json?.run_id;
        if (newRunId) {
          router.push(`/command-center?run=${newRunId}`);
        } else {
          switchToMock();
        }
      } catch {
        switchToMock();
      } finally {
        setIsRunningScenario(false);
      }
    },
    [dataSource, isDemoMode, isDemoParam, locale, router, switchToMock, switchScenario],
  );

  const handleSubmitForReview = useCallback(
    (actionId: string) => {
      executeAction(actionId);
    },
    [executeAction],
  );

  // ── Derive country exposures from impacts for the map ──
  // NOTE: useMemo must be called BEFORE any conditional returns (React Rules of Hooks)
  const countryExposures = useMemo(() => {
    if (!impacts?.length) return undefined;
    const exposures: Record<
      string,
      { stressLevel: number; lossUsd: number; dominantSector: string; entities: string[] }
    > = {};

    const sectorToCountry: Record<string, string[]> = {
      banking: ["SA", "AE", "BH"],
      insurance: ["SA", "AE", "QA"],
      fintech: ["AE", "SA", "BH"],
      energy: ["SA", "QA", "KW"],
      logistics: ["OM", "AE", "QA"],
    };

    for (const impact of impacts) {
      const countries = sectorToCountry[impact.sector] || ["SA"];
      for (const cc of countries) {
        if (!exposures[cc]) {
          exposures[cc] = {
            stressLevel: 0,
            lossUsd: 0,
            dominantSector: impact.sector,
            entities: [],
          };
        }
        exposures[cc].stressLevel = Math.max(exposures[cc].stressLevel, impact.stressLevel);
        exposures[cc].lossUsd += (impact.lossUsd || 0) / countries.length;
      }
    }
    return Object.keys(exposures).length > 0 ? exposures : undefined;
  }, [impacts]);

  // ── State gates ──
  if (status === "loading") return <LoadingSkeleton />;
  if (status === "error" && !scenario) {
    return (
      <ErrorState
        error={error ?? "Unknown error"}
        onRetry={runId ? () => switchToLive(runId) : undefined}
        onFallbackMock={switchToMock}
      />
    );
  }

  // ── Render active tab content ──
  const renderTabContent = () => {
    switch (activeTab) {
      case "scenarios":
        return (
          <div className="p-6 max-w-7xl mx-auto">
            <ScenarioLibrary
              onSelectScenario={handleScenarioSelect}
              isLoading={isRunningScenario}
              locale={locale}
            />
          </div>
        );

      case "macro":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-slate-500 text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من لوحة المعلومات"
                : "No scenario data — select a scenario from the Dashboard"}
            </div>
          );
        }
        return (
          <MacroIntelligenceView
            scenario={scenario}
            headline={headline}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr}
            macroContext={macroContext}
            confidence={confidence}
            causalChain={causalChain}
            sectorRollups={sectorRollups}
            decisionActions={decisionActions}
            trust={trust}
            locale={locale}
          />
        );

      case "propagation":
        return (
          <PropagationView
            locale={locale}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            totalLossUsd={headline?.totalLossUsd}
            causalChain={causalChain}
          />
        );

      case "map":
        return (
          <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Country Exposure Matrix — executive-ready table */}
            <CountryExposureMatrix countryBake={countryBake} locale={locale} />

            {/* GCC Visual Map — secondary */}
            <GCCImpactMap
              countryExposures={countryExposures}
              sectorRollups={
                sectorRollups as unknown as
                  | Record<string, { stress: number; loss_usd: number }>
                  | undefined
              }
              scenarioLabel={scenario?.label}
              locale={locale}
            />
          </div>
        );

      case "sectors":
        return (
          <div className="space-y-6">
            <SectorIntelligenceView
              locale={locale}
              scenarioLabel={scenario?.label}
              scenarioLabelAr={scenario?.labelAr ?? undefined}
              severity={scenario?.severity}
              narrativeEn={narrativeEn}
              narrativeAr={narrativeAr ?? undefined}
              systemRiskIndex={macroContext?.system_risk_index}
              macroSignals={macroContext?.macro_signals}
              causalChain={causalChain}
              decisionActions={decisionActions as any}
            />

            {/* Banking Simulation Layer */}
            {bankingSimulation && bankingSimulation.metrics.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm mx-6 max-w-7xl">
                <h2 className="text-base font-bold text-slate-900 mb-4">
                  {locale === "ar" ? "محاكاة القطاع المصرفي" : "Banking Simulation Layer"}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {bankingSimulation.metrics.map(m => (
                    <div key={m.label} className="bg-slate-50 rounded-lg p-4 group relative">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs font-semibold text-slate-900">
                          {locale === "ar" ? m.labelAr : m.label}
                        </p>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          m.level === "severe" ? "bg-io-status-severe/15 text-io-status-severe" :
                          m.level === "high" ? "bg-io-status-high/15 text-io-status-high" :
                          m.level === "elevated" ? "bg-io-status-elevated/15 text-io-status-elevated" :
                          m.level === "guarded" ? "bg-io-status-guarded/15 text-io-status-guarded" :
                          "bg-io-accent/10 text-io-accent"
                        }`}>
                          {m.level.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-lg font-bold text-slate-900 tabular-nums">{m.value}</p>
                      {/* Hover provenance */}
                      <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-[10px] text-slate-600 space-y-1 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                        <p><span className="font-semibold text-slate-700">Formula:</span> {m.formula}</p>
                        <p><span className="font-semibold text-slate-700">Source:</span> {m.source}</p>
                        <p><span className="font-semibold text-slate-700">Assumption:</span> {m.assumption}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Insurance Simulation Layer */}
            {insuranceSimulation && insuranceSimulation.metrics.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm mx-6 max-w-7xl">
                <h2 className="text-base font-bold text-slate-900 mb-4">
                  {locale === "ar" ? "محاكاة قطاع التأمين" : "Insurance Simulation Layer"}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {insuranceSimulation.metrics.map(m => (
                    <div key={m.label} className="bg-slate-50 rounded-lg p-4 group relative">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs font-semibold text-slate-900">
                          {locale === "ar" ? m.labelAr : m.label}
                        </p>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          m.level === "severe" ? "bg-io-status-severe/15 text-io-status-severe" :
                          m.level === "high" ? "bg-io-status-high/15 text-io-status-high" :
                          m.level === "elevated" ? "bg-io-status-elevated/15 text-io-status-elevated" :
                          m.level === "guarded" ? "bg-io-status-guarded/15 text-io-status-guarded" :
                          "bg-io-accent/10 text-io-accent"
                        }`}>
                          {m.level.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-lg font-bold text-slate-900 tabular-nums">{m.value}</p>
                      {/* Hover provenance */}
                      <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-[10px] text-slate-600 space-y-1 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                        <p><span className="font-semibold text-slate-700">Formula:</span> {m.formula}</p>
                        <p><span className="font-semibold text-slate-700">Source:</span> {m.source}</p>
                        <p><span className="font-semibold text-slate-700">Assumption:</span> {m.assumption}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sector Formula Breakdown */}
            {sectorFormulas.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm mx-6 max-w-7xl">
                <h2 className="text-base font-bold text-slate-900 mb-4">
                  {locale === "ar" ? "تفاصيل صيغ القطاعات" : "Sector Formula Breakdown"}
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-200">
                        <th className="pb-2 pr-3">{locale === "ar" ? "القطاع" : "Sector"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "الخسارة" : "Loss"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "التخصيص" : "Allocation"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "الحساسية" : "Sensitivity"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "الانتشار" : "Propagation"}</th>
                        <th className="pb-2 tabular-nums">{locale === "ar" ? "الثقة" : "Confidence"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sectorFormulas.map(sf => (
                        <tr key={sf.sector} className="border-b border-slate-100 group relative">
                          <td className="py-2 pr-3 font-medium text-slate-900">{sf.sectorLabel}</td>
                          <td className="py-2 pr-3 tabular-nums text-io-status-severe font-semibold">${(sf.sectorLoss / 1e9).toFixed(2)}B</td>
                          <td className="py-2 pr-3 tabular-nums text-slate-600">{(sf.allocationWeight * 100).toFixed(0)}%</td>
                          <td className="py-2 pr-3 tabular-nums text-slate-600">{(sf.scenarioSensitivity * 100).toFixed(0)}%</td>
                          <td className="py-2 pr-3 tabular-nums text-slate-600">{(sf.propagationWeight * 100).toFixed(0)}%</td>
                          <td className="py-2 tabular-nums text-io-accent">{(sf.confidence * 100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );

      case "decisions":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-slate-500 text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من لوحة المعلومات"
                : "No scenario data — select a scenario from the Dashboard"}
            </div>
          );
        }
        return (
          <div className="p-6 space-y-6">
            {/* Decision ROI Engine — above Decision Room */}
            {decisionROI.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm max-w-7xl mx-auto">
                <h2 className="text-base font-bold text-slate-900 mb-4">
                  {locale === "ar" ? "عائد الاستثمار على القرار" : "Decision ROI Analysis"}
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-200">
                        <th className="pb-2 pr-3">{locale === "ar" ? "الإجراء" : "Action"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "التكلفة" : "Cost"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "متجنبة" : "Avoided"}</th>
                        <th className="pb-2 pr-3 tabular-nums">{locale === "ar" ? "صافي" : "Net"}</th>
                        <th className="pb-2 pr-3 tabular-nums">ROI</th>
                        <th className="pb-2 pr-3">{locale === "ar" ? "الموعد" : "Deadline"}</th>
                        <th className="pb-2">{locale === "ar" ? "التصعيد" : "Escalation"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {decisionROI.map(roi => (
                        <tr key={roi.id} className="border-b border-slate-100">
                          <td className="py-2 pr-3 text-slate-900 font-medium max-w-[200px] truncate">
                            {locale === "ar" ? roi.actionAr : roi.action}
                          </td>
                          <td className="py-2 pr-3 tabular-nums text-slate-600">${(roi.costUsd / 1e6).toFixed(0)}M</td>
                          <td className="py-2 pr-3 tabular-nums text-emerald-700">${(roi.lossAvoidedUsd / 1e9).toFixed(2)}B</td>
                          <td className="py-2 pr-3 tabular-nums font-semibold text-slate-900">${(roi.netBenefit / 1e9).toFixed(2)}B</td>
                          <td className="py-2 pr-3">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              roi.roiMultiple >= 5 ? "bg-green-100 text-green-800" :
                              roi.roiMultiple >= 2 ? "bg-emerald-100 text-emerald-700" :
                              "bg-slate-200 text-slate-700"
                            }`}>{roi.roiMultiple.toFixed(1)}x</span>
                          </td>
                          <td className="py-2 pr-3 tabular-nums text-amber-700">{roi.deadlineHours > 0 ? `${roi.deadlineHours}h` : "—"}</td>
                          <td className="py-2 text-[10px] text-slate-500 max-w-[180px] truncate">
                            {locale === "ar" ? roi.escalationPathAr : roi.escalationPath}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Outcome Counterfactual — above Decision Room */}
            {outcomeConfirmation && (
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm max-w-7xl mx-auto">
                <h2 className="text-base font-bold text-slate-900 mb-4">
                  {locale === "ar" ? "تحليل المقارنة المضادة" : "Counterfactual Analysis"}
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="border border-red-200 bg-red-50/50 rounded-lg p-4">
                    <p className="text-[10px] text-red-600 uppercase tracking-wider font-semibold mb-2">
                      {locale === "ar" ? "بدون تدخل" : "Without Intervention"}
                    </p>
                    <p className="text-lg font-bold text-red-800 tabular-nums">
                      ${(outcomeConfirmation.withoutAction.projectedLossLow / 1e9).toFixed(1)}B – ${(outcomeConfirmation.withoutAction.projectedLossHigh / 1e9).toFixed(1)}B
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      {locale === "ar" ? `التعافي: ${outcomeConfirmation.withoutAction.recoveryDays} يوم` : `Recovery: ${outcomeConfirmation.withoutAction.recoveryDays} days`}
                    </p>
                  </div>
                  <div className="border border-emerald-200 bg-emerald-50/50 rounded-lg p-4">
                    <p className="text-[10px] text-emerald-600 uppercase tracking-wider font-semibold mb-2">
                      {locale === "ar" ? "استجابة منسقة" : "Coordinated Response"}
                    </p>
                    <p className="text-lg font-bold text-emerald-800 tabular-nums">
                      ${(outcomeConfirmation.coordinatedResponse.projectedLossLow / 1e9).toFixed(1)}B – ${(outcomeConfirmation.coordinatedResponse.projectedLossHigh / 1e9).toFixed(1)}B
                    </p>
                    <p className="text-xs text-emerald-700 mt-1">
                      {locale === "ar" ? `التعافي: ${outcomeConfirmation.coordinatedResponse.recoveryDays} يوم` : `Recovery: ${outcomeConfirmation.coordinatedResponse.recoveryDays} days`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 mt-3 text-xs">
                  <span className="px-2 py-1 rounded bg-emerald-100 text-emerald-800 font-semibold">
                    {locale === "ar" ? "التخفيض:" : "Reduction:"} {outcomeConfirmation.expectedLossReductionPercent}%
                  </span>
                  <span className="px-2 py-1 rounded bg-blue-100 text-blue-800 font-semibold">
                    {locale === "ar" ? "تسريع التعافي:" : "Faster Recovery:"} {outcomeConfirmation.recoveryHorizonReduction} {locale === "ar" ? "يوم" : "days"}
                  </span>
                </div>
              </div>
            )}

            <DecisionRoomV2
              runId={runId ?? undefined}
              scenarioLabel={scenario.label}
              scenarioLabelAr={scenario.labelAr ?? ""}
              severity={String(scenario.severity)}
              totalLossUsd={headline.totalLossUsd}
              averageStress={headline.averageStress}
              propagationDepth={headline.propagationDepth}
              peakDay={headline.peakDay}
              causalChain={causalChain}
              decisionActions={decisionActions}
              sectorRollups={sectorRollups}
              locale={locale}
              metricExplanations={metricExplanations}
              decisionTransparency={decisionTransparencyResult ?? undefined}
              reliability={reliabilityPayload ?? undefined}
              confidenceScore={confidence}
              narrativeEn={narrativeEn}
              narrativeAr={narrativeAr ?? ""}
              macroContext={macroContext ?? undefined}
              trustInfo={trust ?? undefined}
              onSubmitForReview={handleSubmitForReview}
            />
          </div>
        );

      case "audit":
        return (
          <RegulatoryAuditView
            locale={locale}
            runId={runId ?? undefined}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            horizonHours={scenario?.horizonHours}
            trustInfo={trust ?? undefined}
            decisionActions={decisionActions}
          />
        );

      // Dashboard (default)
      default:
        return (
          <DashboardView
            runId={runId}
            scenario={scenario}
            headline={headline}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr ?? undefined}
            macroContext={macroContext}
            confidence={confidence}
            causalChain={causalChain}
            sectorRollups={sectorRollups}
            decisionActions={decisionActions}
            locale={locale}
            onSelectScenario={handleScenarioSelect}
            isRunningScenario={isRunningScenario}
            executiveStatus={executiveStatus}
            countryBake={countryBake}
            sectorFormulas={sectorFormulas}
            decisionROI={decisionROI}
            outcomeConfirmation={outcomeConfirmation}
            collaborationStage={collaborationStage}
            demoContract={demoContract}
          />
        );
    }
  };

  return (
    <ObservatoryShell
      scenarioLabel={scenario?.label}
      scenarioLabelAr={scenario?.labelAr ?? undefined}
      dataSource={dataSource}
      activeTab={activeTab}
      isDemoMode={isDemoMode}
    >
      {/* Demo Data Banner — explicit, never silent */}
      {isDemoMode && (
        <DemoDataBanner locale={locale} demoContract={demoContract} />
      )}

      {/* Simulation Loaded Banner — visible confirmation of scenario switch */}
      {simulationLoadedLabel && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-emerald-50 border-b border-emerald-200 flex-shrink-0 animate-in slide-in-from-top-1 duration-300">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-[12px] font-semibold text-emerald-800">
              {locale === "ar"
                ? `تم تحميل المحاكاة: ${simulationLoadedLabel}`
                : `Simulation Loaded: ${simulationLoadedLabel}`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-emerald-600">
              {locale === "ar" ? "١٧ مرحلة مكتملة" : "17-stage pipeline complete"}
            </span>
            <button
              onClick={() => setSimulationLoadedLabel(null)}
              className="ml-2 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200 transition-colors"
            >
              {locale === "ar" ? "إغلاق" : "Dismiss"}
            </button>
          </div>
        </div>
      )}

      {/* Simulation Running Overlay — visible "simulation in progress" feedback */}
      {isRunningScenario && (
        <div className="flex items-center justify-center px-4 py-3 bg-blue-50 border-b border-blue-200 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-[12px] font-semibold text-blue-800">
              {locale === "ar"
                ? "جاري تشغيل المحاكاة — معالجة ١٧ مرحلة..."
                : "Running Simulation — Processing 17-stage pipeline..."}
            </p>
          </div>
        </div>
      )}

      {/* Scenario Unavailable Banner — explicit dataset incomplete message */}
      {scenarioUnavailableId && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-amber-50 border-b border-amber-200 flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <p className="text-[12px] font-semibold text-amber-800">
              {locale === "ar"
                ? `مجموعة بيانات السيناريو غير مكتملة — لا يمكن تشغيل المحاكاة.`
                : `Scenario dataset incomplete — cannot run simulation.`}
            </p>
          </div>
          <button
            onClick={() => setScenarioUnavailableId(null)}
            className="ml-3 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
          >
            {locale === "ar" ? "إغلاق" : "Dismiss"}
          </button>
        </div>
      )}

      {/* Fallback banner (API failed, showing mock — non-demo mode) */}
      {!isDemoMode && error && scenario && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-amber-50 border-b border-amber-200 flex-shrink-0">
          <p className="text-[11px] text-amber-700 truncate">{error}</p>
          {runId && (
            <button
              onClick={() => switchToLive(runId)}
              className="ml-3 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-amber-100 text-amber-800 hover:bg-amber-200 transition-colors"
            >
              Retry Live
            </button>
          )}
        </div>
      )}

      {/* Scenario quick-switcher (compact pill bar) */}
      {scenario && activeTab !== "dashboard" && (
        <div className="px-6 pt-3">
          <ScenarioSelector
            activeScenarioId={scenario.templateId}
            onSelect={handleScenarioSelect}
            isLoading={isRunningScenario}
            locale={locale}
          />
        </div>
      )}

      {/* Active tab content */}
      {renderTabContent()}

      {/* Data Trust Layer — read-only provenance & freshness display */}
      {scenario && (
        <DataTrustPanel meta={dataTrustMeta} locale={locale} />
      )}

      {/* Dev Signal Preview — only visible when NEXT_PUBLIC_ENABLE_DEV_SIGNAL_PREVIEW=true */}
      <DevSignalPreview locale={locale} />

      {/* Status Bar */}
      <StatusBar dataSource={dataSource} trust={trust} confidence={confidence} />
    </ObservatoryShell>
  );
}

// ── Page Export ──

export default function CommandCenterPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <CommandCenterInner />
    </Suspense>
  );
}
