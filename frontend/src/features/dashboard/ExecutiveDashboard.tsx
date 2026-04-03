"use client";

/**
 * Impact Observatory | مرصد الأثر — Executive Dashboard
 *
 * Layout:
 *   Top:    Headline Loss | Severity | Peak Day | TTL Breach | TT Insurance Failure | TT Payment Failure
 *   Middle: Financial Impact table
 *   Right:  Banking / Insurance / Fintech stress cards
 *   Bottom: Decision Actions (top 3)
 *
 * Design: white/light, boardroom aesthetic, premium cards, no neon.
 */

import React from "react";
import type {
  RunResult,
  Classification,
  Language,
} from "@/types/observatory";
import { KPICard } from "@/components/KPICard";
import { StressGauge } from "@/components/StressGauge";
import { FinancialImpactPanel } from "@/components/FinancialImpactPanel";
import { safeFixed, safeNum } from "@/lib/format";

// ── Helpers ──────────────────────────────────────────────────────────

function formatUSD(value: number | null | undefined): string {
  const v = safeNum(value);
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toLocaleString()}`;
}

function formatHours(hours: number | null | undefined): string {
  const h = safeNum(hours, Infinity);
  if (!isFinite(h)) return "N/A";
  if (h >= 720) return `${Math.round(h / 720)}mo`;
  if (h >= 24) return `${Math.round(h / 24)}d`;
  return `${Math.round(h)}h`;
}

const classificationColors: Record<Classification, string> = {
  CRITICAL: "bg-io-critical text-white",
  ELEVATED: "bg-io-elevated text-white",
  MODERATE: "bg-io-moderate text-white",
  LOW: "bg-io-low text-white",
  NOMINAL: "bg-io-nominal text-white",
  GUARDED: "bg-yellow-500 text-white",
  HIGH: "bg-orange-600 text-white",
  SEVERE: "bg-red-700 text-white",
};

function Badge({ level }: { level: Classification }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${classificationColors[level]}`}
    >
      {level}
    </span>
  );
}

// ── Labels ───────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    headline_loss: "Headline Loss",
    severity: "Severity",
    peak_day: "Peak Day",
    ttl_breach: "Time to Liquidity Breach",
    tt_insurance: "Time to Insurance Failure",
    tt_payment: "Time to Payment Failure",
    banking_stress: "Banking Stress",
    insurance_stress: "Insurance Stress",
    fintech_stress: "Fintech Stress",
    decision_actions: "Decision Actions",
    financial_impact: "Financial Impact",
    action: "Action",
    owner: "Owner",
    priority: "Priority",
    loss_avoided: "Loss Avoided",
    cost: "Cost",
    entity: "Entity",
    sector: "Sector",
    loss: "Loss",
    stress: "Stress",
    classification: "Level",
  },
  ar: {
    headline_loss: "إجمالي الخسارة",
    severity: "مستوى الشدة",
    peak_day: "يوم الذروة",
    ttl_breach: "الوقت إلى كسر السيولة",
    tt_insurance: "الوقت إلى فشل التأمين",
    tt_payment: "الوقت إلى فشل المدفوعات",
    banking_stress: "ضغط القطاع البنكي",
    insurance_stress: "ضغط التأمين",
    fintech_stress: "اضطراب الفنتك",
    decision_actions: "الإجراءات المقترحة",
    financial_impact: "الأثر المالي",
    action: "الإجراء",
    owner: "المسؤول",
    priority: "الأولوية",
    loss_avoided: "الخسائر المتجنبة",
    cost: "التكلفة",
    entity: "الكيان",
    sector: "القطاع",
    loss: "الخسارة",
    stress: "الضغط",
    classification: "المستوى",
  },
};

// ── Components ───────────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">
        {label}
      </p>
      <p className="text-3xl font-bold tabular-nums text-io-primary">{value}</p>
      {sub && <p className="text-sm text-io-secondary mt-1">{sub}</p>}
    </div>
  );
}

function SectorStressCard({
  title,
  classification,
  stress,
  metrics,
}: {
  title: string;
  classification: Classification;
  stress: number;
  metrics: { label: string; value: string }[];
}) {
  return (
    <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-io-primary">{title}</h3>
        <Badge level={classification} />
      </div>
      <p className="text-2xl font-bold tabular-nums text-io-primary mb-3">
        {safeFixed(safeNum(stress) * 100, 1)}%
      </p>
      <div className="space-y-1.5">
        {metrics.map((m, i) => (
          <div key={i} className="flex justify-between text-sm">
            <span className="text-io-secondary">{m.label}</span>
            <span className="font-medium text-io-primary">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Dashboard ───────────────────────────────────────────────────

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
  const headline = data.headline ?? {} as typeof data.headline;
  const banking = (data.banking ?? (data as any).banking_stress ?? {}) as typeof data.banking;
  const insurance = (data.insurance ?? (data as any).insurance_stress ?? {}) as typeof data.insurance;
  const fintech = (data.fintech ?? (data as any).fintech_stress ?? {}) as typeof data.fintech;
  const decisions = (data.decisions ?? {}) as typeof data.decisions;
  // Normalize: backend must return financial as FinancialImpact[] but guard
  // against the dict shape that previously caused "f.reduce is not a function"
  const financial = Array.isArray(data.financial) ? data.financial : [];

  return (
    <div className={`min-h-screen bg-io-bg p-6 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-io-primary">
          {lang === "ar" ? "مرصد الأثر" : "Impact Observatory"}
        </h1>
        <p className="text-sm text-io-secondary mt-1">
          {data.scenario?.label ?? ""}
        </p>
      </header>

      {/* Top Row: 6 headline metrics */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPICard
          label={t.headline_loss}
          labelAr={labels.ar.headline_loss}
          value={formatUSD(headline?.total_loss_usd)}
          severity={safeNum(headline?.total_loss_usd) >= 1e10 ? "critical" : safeNum(headline?.total_loss_usd) >= 1e9 ? "severe" : safeNum(headline?.total_loss_usd) >= 1e8 ? "high" : "medium"}
          sublabel={`${headline?.affected_entities ?? 0} entities`}
          locale={lang}
        />
        <KPICard
          label={t.severity}
          labelAr={labels.ar.severity}
          value={`${safeFixed(safeNum(data.scenario?.severity) * 100, 0)}%`}
          severity={safeNum(data.scenario?.severity) >= 0.8 ? "critical" : safeNum(data.scenario?.severity) >= 0.6 ? "severe" : safeNum(data.scenario?.severity) >= 0.4 ? "high" : "medium"}
          sublabel={`${headline?.critical_count ?? 0} critical`}
          locale={lang}
        />
        <KPICard
          label={t.peak_day}
          labelAr={labels.ar.peak_day}
          value={`Day ${headline?.peak_day ?? 0}`}
          sublabel={`${headline?.max_recovery_days ?? 0}d recovery`}
          locale={lang}
        />
        <KPICard
          label={t.ttl_breach}
          labelAr={labels.ar.ttl_breach}
          value={formatHours(banking?.time_to_liquidity_breach_hours)}
          severity={safeNum(banking?.time_to_liquidity_breach_hours, Infinity) < 24 ? "critical" : safeNum(banking?.time_to_liquidity_breach_hours, Infinity) < 72 ? "high" : "normal"}
          locale={lang}
        />
        <KPICard
          label={t.tt_insurance}
          labelAr={labels.ar.tt_insurance}
          value={formatHours(insurance?.time_to_insolvency_hours)}
          severity={safeNum(insurance?.time_to_insolvency_hours, Infinity) < 48 ? "critical" : safeNum(insurance?.time_to_insolvency_hours, Infinity) < 168 ? "high" : "normal"}
          locale={lang}
        />
        <KPICard
          label={t.tt_payment}
          labelAr={labels.ar.tt_payment}
          value={formatHours(fintech?.time_to_payment_failure_hours)}
          severity={safeNum(fintech?.time_to_payment_failure_hours, Infinity) < 12 ? "critical" : safeNum(fintech?.time_to_payment_failure_hours, Infinity) < 48 ? "high" : "normal"}
          locale={lang}
        />
      </section>

      {/* Middle + Right: Financial Impact + Sector Stress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Financial Impact Panel (2 cols) */}
        <div className="lg:col-span-2">
          <FinancialImpactPanel
            loss_usd={safeNum(headline?.total_loss_usd)}
            loss_baseline_usd={safeNum(headline?.total_loss_usd) * 1.5}
            peak_loss_day={safeNum(headline?.peak_day)}
            duration_days={safeNum(headline?.max_recovery_days)}
            liquidity_breach_hours={banking?.time_to_liquidity_breach_hours}
            sector_exposure={financial.reduce<Record<string, number>>((acc, fi) => {
              acc[fi.sector] = (acc[fi.sector] ?? 0) + fi.loss_usd;
              return acc;
            }, {})}
            severity_code={
              safeNum(data.scenario?.severity) >= 0.85 ? "CRITICAL"
              : safeNum(data.scenario?.severity) >= 0.7 ? "SEVERE"
              : safeNum(data.scenario?.severity) >= 0.55 ? "HIGH"
              : safeNum(data.scenario?.severity) >= 0.4 ? "ELEVATED"
              : "MODERATE"
            }
            locale={lang}
          />
        </div>

        {/* Right: Sector Stress Gauges (1 col) */}
        <div className="space-y-4">
          <div onClick={() => onNavigate?.("banking")} className={onNavigate ? "cursor-pointer" : ""}>
            <StressGauge
              sector="banking"
              sectorLabel={t.banking_stress}
              sectorLabelAr={labels.ar.banking_stress}
              score={Math.round(safeNum(banking?.aggregate_stress) * 100)}
              classification={banking?.classification ?? "NOMINAL"}
              indicators={[
                `Liquidity ${safeFixed(safeNum(banking?.liquidity_stress) * 100, 0)}%`,
                `Credit ${safeFixed(safeNum(banking?.credit_stress) * 100, 0)}%`,
              ]}
              indicatorsAr={[
                `السيولة ${safeFixed(safeNum(banking?.liquidity_stress) * 100, 0)}%`,
                `الائتمان ${safeFixed(safeNum(banking?.credit_stress) * 100, 0)}%`,
              ]}
              locale={lang}
            />
          </div>
          <div onClick={() => onNavigate?.("insurance")} className={onNavigate ? "cursor-pointer" : ""}>
            <StressGauge
              sector="insurance"
              sectorLabel={t.insurance_stress}
              sectorLabelAr={labels.ar.insurance_stress}
              score={Math.round(safeNum(insurance?.aggregate_stress) * 100)}
              classification={insurance?.classification ?? "NOMINAL"}
              indicators={[
                `Claims ${safeFixed(safeNum(insurance?.claims_surge_multiplier, 1), 2)}x`,
                `Combined ${safeFixed(safeNum(insurance?.combined_ratio) * 100, 0)}%`,
              ]}
              indicatorsAr={[
                `المطالبات ${safeFixed(safeNum(insurance?.claims_surge_multiplier, 1), 2)}x`,
                `النسبة ${safeFixed(safeNum(insurance?.combined_ratio) * 100, 0)}%`,
              ]}
              locale={lang}
            />
          </div>
          <div onClick={() => onNavigate?.("fintech")} className={onNavigate ? "cursor-pointer" : ""}>
            <StressGauge
              sector="fintech"
              sectorLabel={t.fintech_stress}
              sectorLabelAr={labels.ar.fintech_stress}
              score={Math.round(safeNum(fintech?.aggregate_stress) * 100)}
              classification={fintech?.classification ?? "NOMINAL"}
              indicators={[
                `Payments −${safeFixed(safeNum(fintech?.payment_volume_impact_pct), 1)}%`,
                `API ${safeFixed(safeNum(fintech?.api_availability_pct, 100), 0)}% up`,
              ]}
              indicatorsAr={[
                `المدفوعات −${safeFixed(safeNum(fintech?.payment_volume_impact_pct), 1)}%`,
                `الإتاحة ${safeFixed(safeNum(fintech?.api_availability_pct, 100), 0)}%`,
              ]}
              locale={lang}
            />
          </div>
        </div>
      </div>

      {/* Bottom: Decision Actions */}
      <section className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-io-primary uppercase tracking-wider">
            {t.decision_actions}
          </h2>
          {onNavigate && (
            <button
              onClick={() => onNavigate("decisions")}
              className="text-xs text-io-accent hover:text-io-accent/80 font-medium transition-colors"
            >
              {lang === "ar" ? "عرض الكل ←" : "View All →"}
            </button>
          )}
        </div>
        <div className="space-y-3">
          {(Array.isArray(decisions?.actions) ? decisions.actions : []).map((action, i) => (
            <div
              key={action.id || i}
              className="flex items-start gap-4 p-4 rounded-lg bg-io-bg border border-io-border"
            >
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-io-accent text-white flex items-center justify-center text-sm font-bold">
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-io-primary">
                  {lang === "ar" ? action.action_ar || action.action : action.action}
                </p>
                <div className="flex flex-wrap gap-4 mt-2 text-sm text-io-secondary">
                  <span>
                    <strong>{t.owner}:</strong> {action.owner}
                  </span>
                  <span>
                    <strong>{t.priority}:</strong> {safeFixed(action?.priority_score ?? action?.priority, 1)}
                  </span>
                  <span>
                    <strong>{t.loss_avoided}:</strong> {formatUSD(action.loss_avoided_usd)}
                  </span>
                  <span>
                    <strong>{t.cost}:</strong> {formatUSD(action.cost_usd)}
                  </span>
                </div>
              </div>
              <Badge
                level={
                  safeNum(action.urgency) > 50
                    ? "CRITICAL"
                    : safeNum(action.urgency) > 10
                    ? "ELEVATED"
                    : "MODERATE"
                }
              />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
