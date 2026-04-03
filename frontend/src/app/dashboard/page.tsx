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
import { safeNum } from "@/lib/format";

/**
 * Normalize the raw pipeline response to ensure all numeric fields are safe numbers.
 * Prevents "Cannot read properties of undefined (reading 'toFixed')" crashes.
 */
function normalizeRunResult(raw: Record<string, unknown>): RunResult {
  // Normalize actions array — backend uses action_id/priority_score/action_en
  const rawDecisions = (raw.decisions ?? {}) as Record<string, unknown>;
  const rawActions = Array.isArray(rawDecisions.actions) ? rawDecisions.actions : [];
  const normalizedActions = rawActions.map((a: unknown) => {
    const act = (a ?? {}) as Record<string, unknown>;
    return {
      id: String(act.id ?? act.action_id ?? act.rank ?? ""),
      action: String(act.action ?? act.action_en ?? ""),
      action_ar: act.action_ar ? String(act.action_ar) : null,
      sector: String(act.sector ?? ""),
      owner: String(act.owner ?? ""),
      urgency: safeNum(act.urgency),
      value: safeNum(act.value ?? act.priority_score ?? act.priority),
      regulatory_risk: safeNum(act.regulatory_risk ?? act.reg_risk),
      priority_score: safeNum(act.priority_score ?? act.priority),
      priority: safeNum(act.priority ?? act.priority_score),
      time_to_act_hours: safeNum(act.time_to_act_hours, 24),
      time_to_failure_hours: safeNum(act.time_to_failure_hours ?? act.time_to_failure, Infinity),
      loss_avoided_usd: safeNum(act.loss_avoided_usd),
      cost_usd: safeNum(act.cost_usd),
      confidence: safeNum(act.confidence, 0.8),
    };
  });

  // Normalize headline
  const rawHeadline = (raw.headline ?? {}) as Record<string, unknown>;
  const headline = {
    total_loss_usd: safeNum(rawHeadline.total_loss_usd),
    peak_day: safeNum(rawHeadline.peak_day),
    max_recovery_days: safeNum(rawHeadline.max_recovery_days),
    average_stress: safeNum(rawHeadline.average_stress),
    affected_entities: safeNum(rawHeadline.affected_entities),
    critical_count: safeNum(rawHeadline.critical_count),
    elevated_count: safeNum(rawHeadline.elevated_count),
  };

  // Normalize banking
  const rawBanking = (raw.banking ?? raw.banking_stress ?? {}) as Record<string, unknown>;
  const banking = {
    run_id: String(rawBanking.run_id ?? raw.run_id ?? ""),
    sector: String(rawBanking.sector ?? "banking"),
    total_exposure_usd: safeNum(rawBanking.total_exposure_usd),
    liquidity_stress: safeNum(rawBanking.liquidity_stress),
    credit_stress: safeNum(rawBanking.credit_stress),
    fx_stress: safeNum(rawBanking.fx_stress),
    market_stress: safeNum(rawBanking.market_stress),
    wholesale_funding_stress: safeNum(rawBanking.wholesale_funding_stress),
    interbank_contagion: safeNum(rawBanking.interbank_contagion),
    time_to_liquidity_breach_hours: safeNum(rawBanking.time_to_liquidity_breach_hours ?? rawBanking.time_to_breach_hours, Infinity),
    capital_adequacy_impact_pct: safeNum(rawBanking.capital_adequacy_impact_pct),
    aggregate_stress: safeNum(rawBanking.aggregate_stress),
    classification: (rawBanking.classification ?? "NOMINAL") as any,
    affected_institutions: Array.isArray(rawBanking.affected_institutions)
      ? rawBanking.affected_institutions.map((inst: unknown) => {
          const i = (inst ?? {}) as Record<string, unknown>;
          return {
            id: String(i.id ?? ""),
            name: String(i.name ?? ""),
            name_ar: String(i.name_ar ?? i.name ?? ""),
            country: String(i.country ?? ""),
            exposure_usd: safeNum(i.exposure_usd),
            stress: safeNum(i.stress),
            projected_car_pct: safeNum(i.projected_car_pct),
          };
        })
      : [],
  };

  // Normalize insurance
  const rawInsurance = (raw.insurance ?? raw.insurance_stress ?? {}) as Record<string, unknown>;
  const insurance = {
    run_id: String(rawInsurance.run_id ?? raw.run_id ?? ""),
    sector: String(rawInsurance.sector ?? "insurance"),
    portfolio_exposure_usd: safeNum(rawInsurance.portfolio_exposure_usd),
    reserve_adequacy_ratio: safeNum(rawInsurance.reserve_adequacy_ratio ?? rawInsurance.reserve_adequacy, 1),
    claims_surge_multiplier: safeNum(rawInsurance.claims_surge_multiplier, 1),
    severity_index: safeNum(rawInsurance.severity_index),
    loss_ratio: safeNum(rawInsurance.loss_ratio),
    combined_ratio: safeNum(rawInsurance.combined_ratio),
    underwriting_status: String(rawInsurance.underwriting_status ?? "NORMAL"),
    time_to_insolvency_hours: safeNum(rawInsurance.time_to_insolvency_hours, Infinity),
    reinsurance_trigger: Boolean(rawInsurance.reinsurance_trigger),
    ifrs17_risk_adjustment_pct: safeNum(rawInsurance.ifrs17_risk_adjustment_pct),
    aggregate_stress: safeNum(rawInsurance.aggregate_stress),
    classification: (rawInsurance.classification ?? "NOMINAL") as any,
    affected_lines: Array.isArray(rawInsurance.affected_lines)
      ? rawInsurance.affected_lines.map((line: unknown) => {
          const l = (line ?? {}) as Record<string, unknown>;
          return {
            id: String(l.id ?? ""),
            name: String(l.name ?? ""),
            name_ar: String(l.name_ar ?? l.name ?? ""),
            exposure_usd: safeNum(l.exposure_usd),
            claims_surge: safeNum(l.claims_surge, 1),
            stress: safeNum(l.stress),
          };
        })
      : [],
  };

  // Normalize fintech
  const rawFintech = (raw.fintech ?? raw.fintech_stress ?? {}) as Record<string, unknown>;
  const fintech = {
    run_id: String(rawFintech.run_id ?? raw.run_id ?? ""),
    sector: String(rawFintech.sector ?? "fintech"),
    payment_volume_impact_pct: safeNum(rawFintech.payment_volume_impact_pct),
    settlement_delay_hours: safeNum(rawFintech.settlement_delay_hours),
    api_availability_pct: safeNum(rawFintech.api_availability_pct, 100),
    cross_border_disruption: safeNum(rawFintech.cross_border_disruption),
    digital_banking_stress: safeNum(rawFintech.digital_banking_stress),
    time_to_payment_failure_hours: safeNum(rawFintech.time_to_payment_failure_hours, Infinity),
    aggregate_stress: safeNum(rawFintech.aggregate_stress),
    classification: (rawFintech.classification ?? "NOMINAL") as any,
    affected_platforms: Array.isArray(rawFintech.affected_platforms)
      ? rawFintech.affected_platforms.map((p: unknown) => {
          const plat = (p ?? {}) as Record<string, unknown>;
          return {
            id: String(plat.id ?? ""),
            name: String(plat.name ?? ""),
            name_ar: String(plat.name_ar ?? plat.name ?? ""),
            country: String(plat.country ?? ""),
            volume_impact_pct: safeNum(plat.volume_impact_pct),
            cross_border_stress: safeNum(plat.cross_border_stress),
            stress: safeNum(plat.stress),
          };
        })
      : [],
  };

  const decisions = {
    run_id: String(rawDecisions.run_id ?? raw.run_id ?? ""),
    scenario_label: String(rawDecisions.scenario_label ?? raw.scenario_id ?? ""),
    total_loss_usd: safeNum(rawDecisions.total_loss_usd ?? rawHeadline.total_loss_usd),
    peak_day: safeNum(rawDecisions.peak_day ?? rawHeadline.peak_day),
    time_to_failure_hours: safeNum(
      (rawDecisions as any).time_to_failure_hours ??
      (rawDecisions as any).system_time_to_first_failure_hours,
      Infinity
    ),
    actions: normalizedActions,
    all_actions: normalizedActions,
    escalation_triggers: Array.isArray(rawDecisions.escalation_triggers)
      ? (rawDecisions.escalation_triggers as string[])
      : [],
    monitoring_priorities: Array.isArray(rawDecisions.monitoring_priorities)
      ? (rawDecisions.monitoring_priorities as string[])
      : [],
  };

  if (process.env.NODE_ENV === "development") {
    console.group("[Pipeline Result] normalizeRunResult");
    console.log("Raw banking:", rawBanking);
    console.log("Raw insurance:", rawInsurance);
    console.log("Raw fintech:", rawFintech);
    console.log("Raw decisions:", rawDecisions);
    console.log("Normalized decisions.actions:", normalizedActions);
    console.groupEnd();
  }

  return {
    ...(raw as unknown as RunResult),
    headline,
    banking,
    insurance,
    fintech,
    decisions,
    financial: Array.isArray(raw.financial) ? raw.financial as any : [],
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SCENARIOS = [
  { id: "hormuz_chokepoint_disruption", label: "Strategic Maritime Chokepoint Disruption (Hormuz)", labelAr: "تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)", severity: 0.85, horizon: 336 },
  { id: "red_sea_trade_corridor_instability", label: "Red Sea Trade Corridor Instability", labelAr: "اضطراب ممر التجارة في البحر الأحمر", severity: 0.7, horizon: 336 },
  { id: "financial_infrastructure_cyber_disruption", label: "Financial Infrastructure Cyber Disruption", labelAr: "تعطّل البنية المالية نتيجة هجوم سيبراني", severity: 0.6, horizon: 168 },
  { id: "energy_market_volatility_shock", label: "Energy Market Volatility Shock", labelAr: "صدمة تقلبات أسواق الطاقة", severity: 0.8, horizon: 336 },
  { id: "regional_liquidity_stress_event", label: "Regional Liquidity Stress Event", labelAr: "أزمة سيولة مصرفية إقليمية", severity: 0.7, horizon: 336 },
  { id: "critical_port_throughput_disruption", label: "Critical Port Throughput Disruption", labelAr: "تعطّل تدفق العمليات في ميناء حيوي", severity: 0.6, horizon: 336 },
];

function formatLoss(usd: number | null | undefined): string {
  if (usd === null || usd === undefined || !isFinite(usd)) return "$0";
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
      const rawResult: Record<string, unknown> = await res.json();
      const result = normalizeRunResult(rawResult);
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
  // Guard: financial must be an array — backend previously returned a dict causing
  // "f.reduce / for..of not iterable" crashes at runtime.
  const financialList = Array.isArray(data.financial) ? data.financial : [];
  const sectorExposure: Record<string, number> = {};
  for (const fi of financialList) {
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
            value={formatHours(banking?.time_to_liquidity_breach_hours ?? Infinity)}
            severity={(banking?.time_to_liquidity_breach_hours ?? Infinity) < 168 ? "severe" : "medium"}
            locale={locale}
          />
        </div>

        {/* ── MIDDLE: Financial Impact (60%) + Stress Gauges (40%) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          <div className="lg:col-span-3">
            <FinancialImpactPanel
              loss_usd={headline?.total_loss_usd ?? 0}
              loss_baseline_usd={(headline?.total_loss_usd ?? 0) * 1.2}
              peak_loss_day={headline?.peak_day ?? 0}
              duration_days={horizonDays}
              liquidity_breach_hours={banking?.time_to_liquidity_breach_hours ?? Infinity}
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
              score={stressToPercent(banking?.aggregate_stress ?? 0)}
              classification={banking?.classification ?? "NOMINAL"}
              indicators={[
                `Liquidity: ${((banking?.liquidity_stress ?? 0) * 100).toFixed(0)}%`,
                `Credit: ${((banking?.credit_stress ?? 0) * 100).toFixed(0)}%`,
              ]}
              indicatorsAr={[
                `السيولة: ${((banking?.liquidity_stress ?? 0) * 100).toFixed(0)}%`,
                `الائتمان: ${((banking?.credit_stress ?? 0) * 100).toFixed(0)}%`,
              ]}
              locale={locale}
            />
            <StressGauge
              sector="insurance"
              sectorLabel="Insurance"
              sectorLabelAr="التأمين"
              score={stressToPercent(insurance?.aggregate_stress ?? 0)}
              classification={insurance?.classification ?? "NOMINAL"}
              indicators={[
                `Claims: ${(insurance?.claims_surge_multiplier ?? 1).toFixed(1)}x`,
                `Combined: ${((insurance?.combined_ratio ?? 0) * 100).toFixed(0)}%`,
              ]}
              indicatorsAr={[
                `المطالبات: ${(insurance?.claims_surge_multiplier ?? 1).toFixed(1)}x`,
                `النسبة المجمعة: ${((insurance?.combined_ratio ?? 0) * 100).toFixed(0)}%`,
              ]}
              locale={locale}
            />
            <StressGauge
              sector="fintech"
              sectorLabel="Fintech"
              sectorLabelAr="التقنية المالية"
              score={stressToPercent(fintech?.aggregate_stress ?? 0)}
              classification={fintech?.classification ?? "NOMINAL"}
              indicators={[
                `Payments: -${(fintech?.payment_volume_impact_pct ?? 0).toFixed(0)}%`,
                `Settlement: +${(fintech?.settlement_delay_hours ?? 0).toFixed(0)}h`,
              ]}
              indicatorsAr={[
                `المدفوعات: -${(fintech?.payment_volume_impact_pct ?? 0).toFixed(0)}%`,
                `التسوية: +${(fintech?.settlement_delay_hours ?? 0).toFixed(0)}h`,
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
            {(Array.isArray(decisions?.actions) ? decisions.actions : []).slice(0, 3).map((action, idx) => (
              <DecisionActionCard
                key={action.id}
                rank={(idx + 1) as 1 | 2 | 3}
                actionId={action.id}
                priority_score={action.priority_score ?? action.priority ?? 0}
                title_en={action.action}
                title_ar={action.action_ar ?? action.action}
                urgency={action.urgency}
                value={action.value ?? 0}
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
                        {(run.headline_loss_usd ?? 0) >= 1e9
                          ? `$${((run.headline_loss_usd ?? 0) / 1e9).toFixed(1)}B`
                          : `$${((run.headline_loss_usd ?? 0) / 1e6).toFixed(0)}M`}
                      </td>
                      <td className="py-2 pr-4 text-right text-io-secondary">Day {run.peak_day ?? 0}</td>
                      <td className="py-2 pr-4 text-right text-io-secondary">{((run.severity ?? 0) * 100).toFixed(0)}%</td>
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
