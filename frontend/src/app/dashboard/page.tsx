"use client";

/**
 * Impact Observatory | مرصد الأثر — Executive Dashboard
 *
 * Wired to POST /api/v1/runs → renders real pipeline output using:
 *   KPICard, StressGauge, DecisionActionCard, FinancialImpactPanel
 *
 * Layout:
 *   TOP ROW:    4 KPI cards (headline loss, severity, peak day, liquidity breach)
 *   MIDDLE:     FinancialImpactPanel (60%) + 3 StressGauges (40%)
 *   BOTTOM:     3 DecisionActionCards side by side
 *   FOOTER:     pipeline_stages_completed + schema_version (muted)
 */

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import ImpactGlobe from "@/components/globe/impact-globe";
import KPICard from "@/components/KPICard";
import StressGauge from "@/components/StressGauge";
import DecisionActionCard from "@/components/DecisionActionCard";
import FinancialImpactPanel from "@/components/FinancialImpactPanel";
import type { RunResult, Language } from "@/types/observatory";
import { useRunsList } from "@/hooks/use-api";
import type { RunSummary } from "@/types/observatory";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SCENARIOS = [
  { id: "hormuz_chokepoint_disruption", label: "Strategic Maritime Chokepoint Disruption (Hormuz)", labelAr: "تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)", severity: 0.85, horizon: 336 },
  { id: "red_sea_trade_corridor_instability", label: "Red Sea Trade Corridor Instability", labelAr: "اضطراب ممر التجارة في البحر الأحمر", severity: 0.7, horizon: 336 },
  { id: "financial_infrastructure_cyber_disruption", label: "Financial Infrastructure Cyber Disruption", labelAr: "تعطّل البنية المالية نتيجة هجوم سيبراني", severity: 0.6, horizon: 168 },
  { id: "energy_market_volatility_shock", label: "Energy Market Volatility Shock", labelAr: "صدمة تقلبات أسواق الطاقة", severity: 0.8, horizon: 336 },
  { id: "regional_liquidity_stress_event", label: "Regional Liquidity Stress Event", labelAr: "أزمة سيولة مصرفية إقليمية", severity: 0.7, horizon: 336 },
  { id: "critical_port_throughput_disruption", label: "Critical Port Throughput Disruption", labelAr: "تعطّل تدفق العمليات في ميناء حيوي", severity: 0.6, horizon: 336 },
];

function formatLoss(usd: number): string {
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(1)}B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)}M`;
  return `$${Math.round(usd)}`;
}

function formatHours(h: number): string {
  if (!h || h === Infinity) return "N/A";
  if (h >= 24) return `${Math.round(h / 24)}d`;
  return `${Math.round(h)}h`;
}

function classifyStress(score: number): string {
  if (score >= 0.8) return "CRITICAL";
  if (score >= 0.6) return "ELEVATED";
  if (score >= 0.4) return "MODERATE";
  if (score >= 0.2) return "LOW";
  return "NOMINAL";
}

function stressToPercent(score: number): number {
  return Math.round(Math.min(1, Math.max(0, score)) * 100);
}

function severityFromFloat(s: number): "critical" | "severe" | "high" | "medium" | "low" {
  if (s >= 0.9) return "critical";
  if (s >= 0.75) return "severe";
  if (s >= 0.5) return "high";
  if (s >= 0.25) return "medium";
  return "low";
}

export default function DashboardPage() {
  const [data, setData] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);
  const [locale, setLocale] = useState<Language>("en");
  const [gccEntities, setGccEntities] = useState<any[]>([]);
  const { data: runsHistory } = useRunsList({ limit: 10 });

  const runScenario = useCallback(async (scenarioId: string) => {
    setLoading(true);
    setError(null);
    const scenario = SCENARIOS.find((s) => s.id === scenarioId) ?? SCENARIOS[0];
    try {
      const res = await fetch(`${API_BASE}/api/v1/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_id: scenario.id,
          severity: scenario.severity,
          horizon_hours: scenario.horizon,
        }),
        signal: AbortSignal.timeout(30000),
      });
      if (!res.ok) {
        throw new Error(`API ${res.status}: ${await res.text()}`);
      }
      const result: RunResult = await res.json();
      setData(result);
      // Fetch GCC entities for the globe
      fetch(`${API_BASE}/api/v1/graph/nodes?limit=200`, {
        headers: { "X-API-Key": "observatory-dev-key" },
      })
        .then((r) => r.json())
        .then((d) => setGccEntities(d.nodes || []))
        .catch(() => {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pipeline unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    runScenario(selectedScenario);
  }, []);

  const handleRun = () => {
    runScenario(selectedScenario);
  };

  const handleSubmitForReview = async (actionId: string) => {
    if (!data) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/runs/${data.run_id}/actions/${actionId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error(`Approval failed: ${res.status}`);
      const result = await res.json();
      alert(locale === "ar" ? `${result.message_ar}` : `${result.message}`);
      // Refresh data to reflect new status
      runScenario(selectedScenario);
    } catch (err) {
      alert(locale === "ar" ? "فشلت الموافقة — حاول مرة أخرى" : "Approval failed — please try again");
    }
  };

  // ── Loading skeleton ──
  if (loading) {
    return (
      <div className="min-h-screen bg-io-bg p-6">
        <Nav locale={locale} onLocaleToggle={() => setLocale(locale === "en" ? "ar" : "en")} />
        <div className="max-w-7xl mx-auto mt-6 space-y-6">
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-white rounded-xl border border-io-border animate-pulse" />
            ))}
          </div>
          <div className="grid grid-cols-5 gap-4">
            <div className="col-span-3 h-80 bg-white rounded-xl border border-io-border animate-pulse" />
            <div className="col-span-2 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-white rounded-xl border border-io-border animate-pulse" />
              ))}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-white rounded-xl border border-io-border animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Error state ──
  if (error || !data) {
    return (
      <div className="min-h-screen bg-io-bg p-6">
        <Nav locale={locale} onLocaleToggle={() => setLocale(locale === "en" ? "ar" : "en")} />
        <div className="max-w-lg mx-auto mt-20 text-center">
          <div className="bg-red-50 border border-red-200 rounded-xl p-8">
            <h2 className="text-lg font-semibold text-red-800 mb-2">
              {locale === "ar" ? "المعالجة غير متاحة" : "Pipeline Unavailable"}
            </h2>
            <p className="text-sm text-red-600 mb-4">{error}</p>
            <button
              onClick={handleRun}
              className="px-6 py-2 bg-io-accent text-white rounded-lg font-medium hover:bg-blue-800 transition-colors"
            >
              {locale === "ar" ? "إعادة المحاولة" : "Retry"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Extract data ──
  const headline = data.headline;
  const banking = data.banking;
  const insurance = data.insurance;
  const fintech = data.fintech;
  const decisions = data.decisions;
  const scenarioLabel = data.scenario?.label ?? "Scenario";
  const severity = data.scenario?.severity ?? 0;
  const horizonDays = Math.round((data.scenario?.horizon_hours ?? 336) / 24);

  // Build sector exposure from financial impacts
  const sectorExposure: Record<string, number> = {};
  for (const fi of data.financial) {
    sectorExposure[fi.sector] = (sectorExposure[fi.sector] ?? 0) + fi.loss_usd;
  }

  return (
    <div className="min-h-screen bg-io-bg" dir={locale === "ar" ? "rtl" : "ltr"}>
      <Nav locale={locale} onLocaleToggle={() => setLocale(locale === "en" ? "ar" : "en")} />

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Scenario selector */}
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="px-3 py-2 border border-io-border rounded-lg bg-white text-sm text-io-primary focus:outline-none focus:ring-2 focus:ring-io-accent"
          >
            {SCENARIOS.map((s) => (
              <option key={s.id} value={s.id}>
                {locale === "ar" ? s.labelAr : s.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleRun}
            disabled={loading}
            className="px-5 py-2 bg-io-accent text-white rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors disabled:opacity-50"
          >
            {locale === "ar" ? "تشغيل السيناريو" : "Run Scenario"}
          </button>
          {/* PDF Export Button */}
          <a
            href={`${API_BASE}/api/v1/runs/${data.run_id}/report/executive/pdf?lang=${locale}`}
            download={`impact-report-${data.run_id}.pdf`}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-io-primary text-white text-xs font-semibold rounded hover:bg-io-primary/90 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            ↓ {locale === "ar" ? "تصدير PDF" : "Export PDF"}
          </a>
          <span className="text-xs text-io-secondary">
            {scenarioLabel} — {horizonDays}d
          </span>
        </div>

        {/* ── TOP ROW: 4 KPI Cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            label="Headline Loss"
            labelAr="إجمالي الخسارة"
            value={formatLoss(headline.total_loss_usd)}
            severity={severityFromFloat(severity)}
            trend="up"
            locale={locale}
          />
          <KPICard
            label="Severity Code"
            labelAr="مستوى الشدة"
            value={classifyStress(severity)}
            severity={severityFromFloat(severity)}
            locale={locale}
          />
          <KPICard
            label="Peak Day"
            labelAr="يوم الذروة"
            value={`Day ${headline.peak_day} of ${horizonDays}`}
            severity="normal"
            locale={locale}
          />
          <KPICard
            label="Liquidity Breach"
            labelAr="كسر السيولة"
            value={formatHours(banking.time_to_liquidity_breach_hours)}
            severity={banking.time_to_liquidity_breach_hours < 168 ? "severe" : "medium"}
            locale={locale}
          />
        </div>

        {/* ── MIDDLE: Financial Impact (60%) + Stress Gauges (40%) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          <div className="lg:col-span-3">
            <FinancialImpactPanel
              loss_usd={headline.total_loss_usd}
              loss_baseline_usd={headline.total_loss_usd * 1.2}
              peak_loss_day={headline.peak_day}
              duration_days={horizonDays}
              liquidity_breach_hours={banking.time_to_liquidity_breach_hours}
              sector_exposure={sectorExposure}
              severity_code={classifyStress(severity)}
              locale={locale}
            />
          </div>
          <div className="lg:col-span-2 space-y-4">
            <StressGauge
              sector="banking"
              sectorLabel="Banking"
              sectorLabelAr="البنوك"
              score={stressToPercent(banking.aggregate_stress)}
              classification={banking.classification}
              indicators={[
                `Liquidity: ${(banking.liquidity_stress * 100).toFixed(0)}%`,
                `Credit: ${(banking.credit_stress * 100).toFixed(0)}%`,
              ]}
              indicatorsAr={[
                `السيولة: ${(banking.liquidity_stress * 100).toFixed(0)}%`,
                `الائتمان: ${(banking.credit_stress * 100).toFixed(0)}%`,
              ]}
              locale={locale}
            />
            <StressGauge
              sector="insurance"
              sectorLabel="Insurance"
              sectorLabelAr="التأمين"
              score={stressToPercent(insurance.aggregate_stress)}
              classification={insurance.classification}
              indicators={[
                `Claims: ${insurance.claims_surge_multiplier.toFixed(1)}x`,
                `Combined: ${(insurance.combined_ratio * 100).toFixed(0)}%`,
              ]}
              indicatorsAr={[
                `المطالبات: ${insurance.claims_surge_multiplier.toFixed(1)}x`,
                `النسبة المجمعة: ${(insurance.combined_ratio * 100).toFixed(0)}%`,
              ]}
              locale={locale}
            />
            <StressGauge
              sector="fintech"
              sectorLabel="Fintech"
              sectorLabelAr="التقنية المالية"
              score={stressToPercent(fintech.aggregate_stress)}
              classification={fintech.classification}
              indicators={[
                `Payments: -${fintech.payment_volume_impact_pct.toFixed(0)}%`,
                `Settlement: +${fintech.settlement_delay_hours.toFixed(0)}h`,
              ]}
              indicatorsAr={[
                `المدفوعات: -${fintech.payment_volume_impact_pct.toFixed(0)}%`,
                `التسوية: +${fintech.settlement_delay_hours.toFixed(0)}h`,
              ]}
              locale={locale}
            />
          </div>
        </div>

        {/* ── Geographic Impact Map ── */}
        <ImpactGlobe
          runResult={data}
          entities={gccEntities}
          lang={locale}
          className="w-full min-h-[360px]"
        />

        {/* ── BOTTOM: 3 Decision Action Cards ── */}
        <div>
          <h2 className="text-sm font-semibold text-io-secondary uppercase tracking-wide mb-3">
            {locale === "ar" ? "الإجراءات المقترحة" : "Decision Actions"}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {decisions.actions.slice(0, 3).map((action, idx) => (
              <DecisionActionCard
                key={action.id}
                rank={(idx + 1) as 1 | 2 | 3}
                actionId={action.id}
                priority_score={action.priority}
                title_en={action.action}
                title_ar={action.action_ar ?? action.action}
                urgency={action.urgency}
                value={action.value}
                time_to_act_hours={action.time_to_act_hours}
                cost_usd={action.cost_usd}
                loss_avoided_usd={action.loss_avoided_usd}
                status="PENDING_REVIEW"
                locale={locale}
                onSubmitForReview={handleSubmitForReview}
              />
            ))}
          </div>
        </div>

        {/* ── Run History ── */}
        {runsHistory && runsHistory.runs.length > 0 && (
          <section className="mt-6">
            <h2 className="text-sm font-semibold text-io-secondary mb-3">
              {locale === "ar" ? "سجل التشغيل" : "Run History"}
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-io-border text-io-secondary/60">
                    <th className="text-left py-2 pr-4 font-medium">{locale === "ar" ? "السيناريو" : "Scenario"}</th>
                    <th className="text-right py-2 pr-4 font-medium">{locale === "ar" ? "الخسارة" : "Loss"}</th>
                    <th className="text-right py-2 pr-4 font-medium">{locale === "ar" ? "ذروة الأثر" : "Peak Day"}</th>
                    <th className="text-right py-2 pr-4 font-medium">{locale === "ar" ? "الشدة" : "Severity"}</th>
                    <th className="text-right py-2 font-medium">{locale === "ar" ? "الحالة" : "Status"}</th>
                  </tr>
                </thead>
                <tbody>
                  {runsHistory.runs.map((run: RunSummary) => (
                    <tr key={run.run_id} className="border-b border-io-border/40 hover:bg-io-bg/50">
                      <td className="py-2 pr-4 font-mono text-io-primary">{run.scenario_id}</td>
                      <td className="py-2 pr-4 text-right text-io-danger font-semibold">
                        {run.headline_loss_usd >= 1e9
                          ? `$${(run.headline_loss_usd / 1e9).toFixed(1)}B`
                          : `$${(run.headline_loss_usd / 1e6).toFixed(0)}M`}
                      </td>
                      <td className="py-2 pr-4 text-right text-io-secondary">Day {run.peak_day}</td>
                      <td className="py-2 pr-4 text-right text-io-secondary">{(run.severity * 100).toFixed(0)}%</td>
                      <td className="py-2 text-right">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          run.severity_code === "CRITICAL" ? "bg-red-100 text-red-700" :
                          run.severity_code === "SEVERE" ? "bg-orange-100 text-orange-700" :
                          "bg-green-100 text-green-700"
                        }`}>
                          {run.severity_code || run.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ── Footer: pipeline metadata ── */}
        <div className="flex items-center justify-between text-xs text-io-secondary/60 pt-4 border-t border-io-border">
          <span>
            {locale === "ar" ? "مراحل المعالجة" : "Pipeline"}: {data.pipeline_stages_completed} stages
            {" · "}
            {locale === "ar" ? "الإصدار" : "Schema"}: {data.schema_version}
            {" · "}
            {data.duration_ms}ms
          </span>
          <Link href="/" className="hover:text-io-accent transition-colors">
            {locale === "ar" ? "← الرئيسية" : "← Home"}
          </Link>
        </div>
      </main>
    </div>
  );
}

// ── Nav Component ──
function Nav({ locale, onLocaleToggle }: { locale: Language; onLocaleToggle: () => void }) {
  return (
    <nav className="bg-white border-b border-io-border px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2">
            <span className="bg-io-primary text-white text-xs font-bold px-2 py-1 rounded">IO</span>
            <span className="text-sm font-semibold text-io-primary">
              {locale === "ar" ? "مرصد الأثر" : "Impact Observatory"}
            </span>
          </Link>
          <span className="text-io-border">|</span>
          <Link href="/dashboard" className="text-sm text-io-accent font-medium">
            {locale === "ar" ? "لوحة المعلومات" : "Dashboard"}
          </Link>
          <Link href="/control-room" className="text-sm text-io-secondary hover:text-io-accent transition-colors">
            {locale === "ar" ? "الهيكلية" : "Architecture"}
          </Link>
        </div>
        <button
          onClick={onLocaleToggle}
          className="px-3 py-1 border border-io-border rounded text-xs font-semibold text-io-secondary hover:bg-io-bg transition-colors"
        >
          {locale === "ar" ? "EN" : "AR"}
        </button>
      </div>
    </nav>
  );
}
