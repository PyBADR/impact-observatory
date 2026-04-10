"use client";

/**
 * Impact Observatory | مرصد الأثر — Executive Dashboard
 *
 * McKinsey Pyramid Layout:
 *   Row 1:  KPI Strip (6 headline metrics)
 *   Row 2:  Financial Impact table (2-col) | Sector Stress panels (1-col)
 *   Row 3:  Decision Actions (institutional response cards)
 *   Row 4:  Business Impact Timeline | Regulatory Timeline
 *
 * Design: institutional, boardroom-grade, no emoji in chrome.
 * Classification: uses standard Tailwind colors (io-critical etc. do not exist).
 */

import React, { useState, useCallback } from "react";
import type {
  RunResult,
  Classification,
  Language,
  DecisionAction,
} from "@/types/observatory";
import TrustBox from "@/components/TrustBox";
import PipelineViewer from "@/components/PipelineViewer";
import BusinessTimeline from "@/features/timeline/BusinessTimeline";
import RegulatoryTimeline from "@/features/timeline/RegulatoryTimeline";
import {
  ClassificationBadge,
  SectorStressPanel,
  Panel,
  SectionHeader,
  InstitutionalActionCard,
  KPICard,
  EmptyState,
} from "@/components/ui";
import { formatUSD, formatHours, safeFixed, safePercent, safeArray } from "@/lib/format";

const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

function exportErrorMessage(status: number): string {
  if (status === 404) return "Report not found. Please re-run the scenario and try again.";
  if (status === 425) return "Report is still generating. Please wait a moment and try again.";
  if (status === 403) return "Report export requires elevated permissions. Contact your administrator.";
  if (status >= 500) return "The export service is temporarily unavailable. Please try again shortly.";
  return "Report export could not be completed. Please try again.";
}

async function downloadRunPDF(runId: string, lang: string): Promise<void> {
  const res = await fetch(`/api/v1/runs/${runId}/export?lang=${lang}`, {
    headers: { "X-IO-API-Key": API_KEY },
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

// ── Bilingual label maps ───────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    // KPI strip — exact per spec: label + unit embedded in label
    headline_loss: "Projected Financial Loss",
    peak_day: "Peak Impact Day",
    tt_first_failure: "Liquidity Breach Window",
    business_severity: "Business Severity",
    executive_status: "Executive Status",
    severity: "Scenario Severity",
    // Sector cards
    banking_stress: "Banking Stress Index",
    insurance_stress: "Insurance Stress Index",
    fintech_stress: "Fintech Stress Index",
    // Financial panel
    financial_impact: "Financial Impact Summary",
    action: "Response Action",
    owner: "Owner",
    priority: "Priority",
    loss_avoided: "Estimated Mitigation Value (USD)",
    cost: "Estimated Cost (USD)",
    entity: "Entity",
    sector: "Sector",
    loss: "Projected Loss (USD)",
    stress: "Severity Index",
    classification: "Status",
    export_pdf: "Export Report",
    exporting: "Generating…",
    view_all: "View All →",
    entities_affected: "entities affected · projected",
    critical_count: "critical",
    banking_first: "Banking first",
    insurance_first: "Insurance first",
    fintech_first: "Fintech first",
    recovery: "d recovery · simulated",
    no_actions: "No response actions available",
    no_actions_desc: "Run a scenario to generate prioritized response actions.",
  },
  ar: {
    headline_loss: "الخسارة المالية المتوقعة",
    peak_day: "يوم ذروة الأثر",
    tt_first_failure: "نافذة خرق السيولة",
    business_severity: "شدة الأعمال",
    executive_status: "الحالة التنفيذية",
    severity: "شدة السيناريو",
    banking_stress: "مؤشر ضغط البنوك",
    insurance_stress: "مؤشر ضغط التأمين",
    fintech_stress: "مؤشر ضغط الفنتك",
    financial_impact: "ملخص الأثر المالي",
    action: "إجراء الاستجابة",
    owner: "المسؤول",
    priority: "الأولوية",
    loss_avoided: "قيمة التخفيف المقدّرة (دولار)",
    cost: "التكلفة التقديرية (دولار)",
    entity: "الكيان",
    sector: "القطاع",
    loss: "الخسارة المتوقعة (دولار)",
    stress: "مؤشر الشدة",
    classification: "الحالة",
    export_pdf: "تصدير التقرير",
    exporting: "جاري الإنشاء...",
    view_all: "عرض الكل ←",
    entities_affected: "كيان متأثر · متوقع",
    critical_count: "حرج",
    banking_first: "البنوك أولاً",
    insurance_first: "التأمين أولاً",
    fintech_first: "الفنتك أولاً",
    recovery: "يوم للاسترداد · محاكى",
    no_actions: "لا توجد إجراءات استجابة",
    no_actions_desc: "شغّل سيناريو لإنشاء إجراءات استجابة مُصنّفة.",
  },
};

// ── Financial Impact Table ─────────────────────────────────────────────

function FinancialImpactTable({
  financial,
  lang,
  t,
}: {
  financial: ReturnType<typeof safeArray>;
  lang: Language;
  t: Record<string, string>;
}) {
  const rows = safeArray(financial) as Array<{
    entity_id: string;
    entity_label?: string;
    sector?: string;
    loss_usd?: number;
    stress_level?: number;
    classification?: Classification;
  }>;

  return (
    <Panel
      title={t.financial_impact}
      titleAr={labels.ar.financial_impact}
      lang={lang}
      noPadding
      className="lg:col-span-2"
    >
      {rows.length === 0 ? (
        <div className="p-5">
          <EmptyState
            title="No entity data"
            description="Financial entity impact data is not available."
            compact
            lang={lang}
          />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-io-border bg-io-bg">
                <th className="text-left py-2.5 px-5 text-[10px] font-semibold text-io-secondary uppercase tracking-wider">
                  {t.entity}
                </th>
                <th className="text-left py-2.5 px-3 text-[10px] font-semibold text-io-secondary uppercase tracking-wider">
                  {t.sector}
                </th>
                <th className="text-right py-2.5 px-3 text-[10px] font-semibold text-io-secondary uppercase tracking-wider">
                  {t.loss}
                </th>
                <th className="text-right py-2.5 px-3 text-[10px] font-semibold text-io-secondary uppercase tracking-wider">
                  {t.stress}
                </th>
                <th className="text-center py-2.5 px-5 text-[10px] font-semibold text-io-secondary uppercase tracking-wider">
                  {t.classification}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 12).map((fi, idx) => (
                <tr
                  key={fi.entity_id}
                  className={`border-b border-io-border/50 last:border-0 hover:bg-io-bg/50 transition-colors ${
                    idx % 2 === 0 ? "" : "bg-io-bg/30"
                  }`}
                >
                  <td className="py-2.5 px-5 font-medium text-io-primary text-sm">
                    {fi.entity_label || fi.entity_id}
                  </td>
                  <td className="py-2.5 px-3 text-io-secondary text-xs">
                    {fi.sector ?? "—"}
                  </td>
                  <td className="py-2.5 px-3 text-right tabular-nums font-medium text-io-primary text-sm">
                    {formatUSD(fi.loss_usd)}
                  </td>
                  <td className="py-2.5 px-3 text-right tabular-nums text-io-secondary text-xs">
                    {safePercent(fi.stress_level)}
                  </td>
                  <td className="py-2.5 px-5 text-center">
                    {fi.classification ? (
                      <ClassificationBadge
                        level={fi.classification}
                        lang={lang}
                        size="xs"
                      />
                    ) : (
                      <span className="text-io-secondary">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length > 12 && (
            <div className="px-5 py-2.5 border-t border-io-border text-xs text-io-secondary">
              {rows.length - 12} {lang === "ar" ? "كيانات إضافية" : "additional entities"}
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────

export default function ExecutiveDashboard({
  data,
  lang = "en",
  onNavigate,
}: {
  data: RunResult;
  lang?: Language;
  onNavigate?: (view: string) => void;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";
  const { headline, banking, insurance, fintech, decisions, financial } = data;

  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const handleExport = useCallback(async () => {
    if (!data.run_id) return;
    setPdfLoading(true);
    setPdfError(null);
    try {
      await downloadRunPDF(data.run_id, lang);
    } catch (e) {
      setPdfError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setPdfLoading(false);
    }
  }, [data.run_id, lang]);

  // Compute time to first failure
  const tff = (() => {
    const times = [
      { label: t.banking_first, hours: banking.time_to_liquidity_breach_hours || Infinity },
      { label: t.insurance_first, hours: insurance.time_to_insolvency_hours || Infinity },
      { label: t.fintech_first, hours: fintech.time_to_payment_failure_hours || Infinity },
    ];
    const first = times.reduce((a, b) => (a.hours < b.hours ? a : b));
    return {
      value: first.hours < Infinity ? first.hours : 0,
      context: first.hours < Infinity ? first.label : undefined,
    };
  })();

  // Classification for each KPI
  const bClass = (banking.classification as Classification) || "NOMINAL";
  const iClass = (insurance.classification as Classification) || "NOMINAL";
  const fClass = (fintech.classification as Classification) || "NOMINAL";

  const actions = safeArray<DecisionAction>(decisions?.actions);

  return (
    <div
      className={`min-h-screen bg-io-bg pb-12 ${isRTL ? "font-ar" : "font-sans"}`}
      dir={isRTL ? "rtl" : "ltr"}
    >
      {/* ── Page header ────────────────────────────────────────────── */}
      <div className="bg-io-surface border-b border-io-border px-6 lg:px-10 py-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-0.5">
              {lang === "ar" ? "تقرير التحليل التنفيذي" : "Executive Analysis Report"}
            </p>
            <h1 className="text-xl font-bold text-io-primary leading-tight">
              {data.scenario.label}
            </h1>
            {data.scenario.severity !== undefined && (
              <p className="text-sm text-io-secondary mt-0.5">
                {t.severity}:{" "}
                <span className="font-medium text-io-primary">
                  {safePercent(data.scenario.severity, 0)}
                </span>
              </p>
            )}
          </div>

          {/* Export action */}
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={handleExport}
              disabled={pdfLoading || !data.run_id}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-io-border bg-io-surface text-xs font-semibold text-io-primary hover:bg-io-accent hover:text-white hover:border-io-accent disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {pdfLoading ? (
                <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
              )}
              {pdfLoading ? t.exporting : t.export_pdf}
            </button>
            {pdfError && (
              <p className="text-[10px] text-red-600 max-w-[220px] text-end leading-tight">
                {pdfError}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="px-6 lg:px-10 pt-6 space-y-6">

        {/* ── Trust / Model provenance bar ───────────────────────── */}
        <TrustBox
          modelVersion={data.model_version}
          confidence={data.global_confidence}
          assumptions={data.assumptions}
          auditHash={data.audit_hash}
          runId={data.run_id}
          lang={lang}
        />

        {/* ── KPI Strip: 6 headline metrics ──────────────────────── */}
        <section>
          <SectionHeader
            label={lang === "en" ? "Headline Metrics" : "المؤشرات الرئيسية"}
            lang={lang}
          />
          {/* Rule: every KPI shows label + value + unit + context (projected/simulated) + horizon */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {/* 1. Projected Financial Loss — USD, projected, scenario horizon */}
            <KPICard
              label={t.headline_loss}
              value={formatUSD(headline.total_loss_usd)}
              unit="USD"
              context={`${headline.affected_entities} ${t.entities_affected}`}
              classification={
                headline.total_loss_usd > 2e9
                  ? "CRITICAL"
                  : headline.total_loss_usd > 1e9
                  ? "ELEVATED"
                  : "MODERATE"
              }
              lang={lang}
            />
            {/* 2. Peak Impact Day — Day X of Y, simulated */}
            <KPICard
              label={t.peak_day}
              value={`Day ${headline.peak_day} of ${headline.max_recovery_days}`}
              context={lang === "ar" ? "محاكى" : "simulated"}
              lang={lang}
            />
            {/* 3. Liquidity Breach Window — hours, time to first sector breach */}
            <KPICard
              label={t.tt_first_failure}
              value={
                tff.value > 0
                  ? `${Math.round(tff.value)} ${lang === "ar" ? "ساعة" : "hours"}`
                  : "—"
              }
              context={tff.context ?? (lang === "ar" ? "الوقت إلى أول خرق" : "time to first breach")}
              classification={
                tff.value > 0 && tff.value < 24
                  ? "CRITICAL"
                  : tff.value < 72
                  ? "ELEVATED"
                  : "MODERATE"
              }
              lang={lang}
            />
            {/* 4. Business Severity — enterprise status label */}
            <KPICard
              label={t.business_severity}
              value={
                data.business_severity === "severe" ? (lang === "ar" ? "شديد" : "Severe")
                : data.business_severity === "high" ? (lang === "ar" ? "مرتفع" : "Elevated")
                : data.business_severity === "medium" ? (lang === "ar" ? "محدود" : "Guarded")
                : (lang === "ar" ? "مستقر" : "Stable")
              }
              context={`${headline.critical_count} ${t.critical_count}`}
              classification={
                (data.business_severity === "severe"
                  ? "CRITICAL"
                  : data.business_severity === "high"
                  ? "ELEVATED"
                  : data.business_severity === "medium"
                  ? "MODERATE"
                  : "LOW") as Classification
              }
              lang={lang}
            />
            {/* 5. Executive Status — enterprise status label */}
            <KPICard
              label={t.executive_status}
              value={
                data.executive_status === "CRITICAL" ? (lang === "ar" ? "حرج" : "Critical")
                : data.executive_status === "SEVERE" ? (lang === "ar" ? "شديد" : "Severe")
                : data.executive_status === "ELEVATED" ? (lang === "ar" ? "مرتفع" : "Elevated")
                : (lang === "ar" ? "مستقر" : "Stable")
              }
              classification={
                (data.executive_status === "CRITICAL"
                  ? "CRITICAL"
                  : data.executive_status === "SEVERE"
                  ? "ELEVATED"
                  : data.executive_status === "ELEVATED"
                  ? "MODERATE"
                  : "NOMINAL") as Classification
              }
              lang={lang}
            />
            {/* 6. Scenario Severity — %, simulated input */}
            <KPICard
              label={t.severity}
              value={safePercent(data.scenario.severity, 0)}
              unit="%"
              context={lang === "ar" ? "إدخال المحاكاة" : "simulation input"}
              lang={lang}
            />
          </div>
        </section>

        {/* ── Pipeline Viewer ─────────────────────────────────────── */}
        <PipelineViewer
          stagesCompleted={data.stages_completed}
          stageLog={data.stage_log}
          scenarioSeverity={data.scenario.severity}
          headlineLoss={headline.total_loss_usd}
          confidence={data.global_confidence}
          lang={lang}
        />

        {/* ── Financial Impact + Sector Stress ────────────────────── */}
        <section>
          <SectionHeader
            label={lang === "en" ? "Sector Analysis" : "تحليل القطاعات"}
            lang={lang}
          />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Financial Impact Table */}
            <FinancialImpactTable
              financial={financial}
              lang={lang}
              t={t}
            />

            {/* Sector Stress Panels — label: "X Stress Index", value: X / 100 */}
            <div className="space-y-4">
              <SectorStressPanel
                title={t.banking_stress}
                titleAr={labels.ar.banking_stress}
                classification={bClass}
                stressPercent={banking.aggregate_stress}
                metrics={[
                  { label: "Liquidity Stress (%)", labelAr: "ضغط السيولة (%)", value: safePercent(banking.liquidity_stress, 0) },
                  { label: "Credit Risk (%)", labelAr: "مخاطر الائتمان (%)", value: safePercent(banking.credit_stress, 0) },
                  { label: "FX Stress (%)", labelAr: "ضغط العملة (%)", value: banking.fx_stress ? safePercent(banking.fx_stress, 0) : "N/A" },
                  { label: "Interbank Contagion (%)", labelAr: "العدوى المصرفية (%)", value: safePercent(banking.interbank_contagion, 0) },
                ]}
                lang={lang}
                onClick={onNavigate ? () => onNavigate("banking") : undefined}
              />
              <SectorStressPanel
                title={t.insurance_stress}
                titleAr={labels.ar.insurance_stress}
                classification={iClass}
                stressPercent={insurance.aggregate_stress}
                metrics={[
                  { label: "Claims Surge Multiplier", labelAr: "مضاعف المطالبات", value: `${safeFixed(insurance.claims_surge_multiplier, 2)}×` },
                  { label: "Combined Ratio (%)", labelAr: "النسبة المجمعة (%)", value: safePercent(insurance.combined_ratio, 0) },
                  { label: "Underwriting Status", labelAr: "حالة الاكتتاب", value: insurance.underwriting_status },
                  { label: "Reinsurance Trigger", labelAr: "تفعيل إعادة التأمين", value: insurance.reinsurance_trigger ? (lang === "ar" ? "مُفعَّل" : "Triggered") : (lang === "ar" ? "طبيعي" : "Normal") },
                ]}
                lang={lang}
                onClick={onNavigate ? () => onNavigate("insurance") : undefined}
              />
              <SectorStressPanel
                title={t.fintech_stress}
                titleAr={labels.ar.fintech_stress}
                classification={fClass}
                stressPercent={fintech.aggregate_stress}
                metrics={[
                  { label: "Payment Volume Drop (%)", labelAr: "انخفاض حجم المدفوعات (%)", value: `${safeFixed(fintech.payment_volume_impact_pct, 1)}%` },
                  { label: "Settlement Delay (hours)", labelAr: "تأخر التسوية (ساعة)", value: `+${safeFixed(fintech.settlement_delay_hours, 1)}h` },
                  { label: "API Availability (%)", labelAr: "توفر الواجهة (%)", value: `${safeFixed(fintech.api_availability_pct, 0)}%` },
                  { label: "Cross-Border Disruption (%)", labelAr: "التعطل العابر للحدود (%)", value: fintech.cross_border_disruption ? safePercent(fintech.cross_border_disruption, 0) : "N/A" },
                ]}
                lang={lang}
                onClick={onNavigate ? () => onNavigate("fintech") : undefined}
              />
            </div>
          </div>
        </section>

        {/* ── Decision Actions ─────────────────────────────────────── */}
        <section>
          <SectionHeader
            label={lang === "en" ? "Recommended Response Actions" : "إجراءات الاستجابة الموصى بها"}
            lang={lang}
            action={
              onNavigate && actions.length > 0 ? (
                <button
                  onClick={() => onNavigate("decisions")}
                  className="text-xs font-medium text-io-accent hover:text-blue-700 transition-colors"
                >
                  {t.view_all}
                </button>
              ) : undefined
            }
          />

          {actions.length === 0 ? (
            <Panel>
              <EmptyState
                title={t.no_actions}
                description={t.no_actions_desc}
                compact
                lang={lang}
              />
            </Panel>
          ) : (
            <div className="space-y-3">
              {actions.slice(0, 4).map((action, i) => (
                <InstitutionalActionCard
                  key={action.id ?? i}
                  rank={i + 1}
                  title={lang === "ar" ? action.action_ar || action.action || "Action" : action.action || "Action"}
                  urgency={action.urgency}
                  confidence={action.confidence}
                  timeToEffectHours={action.time_to_act_hours}
                  mitigationValueUSD={action.loss_avoided_usd}
                  costUSD={action.cost_usd}
                  lang={lang}
                />
              ))}
            </div>
          )}
        </section>

        {/* ── Timelines ────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            label={lang === "en" ? "Forward-Looking Timelines" : "الجداول الزمنية المستقبلية"}
            lang={lang}
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BusinessTimeline data={data.timeline} lang={lang} />
            <RegulatoryTimeline data={data.regulatory_events} lang={lang} />
          </div>
        </section>

      </div>
    </div>
  );
}
