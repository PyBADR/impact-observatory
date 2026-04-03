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

// ── Helpers ──────────────────────────────────────────────────────────

function formatUSD(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}

function formatHours(hours: number): string {
  if (!isFinite(hours)) return "N/A";
  if (hours >= 720) return `${Math.round(hours / 720)}mo`;
  if (hours >= 24) return `${Math.round(hours / 24)}d`;
  return `${Math.round(hours)}h`;
}

const classificationColors: Record<Classification, string> = {
  CRITICAL: "bg-io-critical text-white",
  ELEVATED: "bg-io-elevated text-white",
  MODERATE: "bg-io-moderate text-white",
  LOW: "bg-io-low text-white",
  NOMINAL: "bg-io-nominal text-white",
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
        {(stress * 100).toFixed(1)}%
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
  const { headline, banking, insurance, fintech, decisions, financial } = data;

  return (
    <div className={`min-h-screen bg-io-bg p-6 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-io-primary">
          {lang === "ar" ? "مرصد الأثر" : "Impact Observatory"}
        </h1>
        <p className="text-sm text-io-secondary mt-1">
          {data.scenario.label}
        </p>
      </header>

      {/* Top Row: 6 headline metrics */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <KPICard
          label={t.headline_loss}
          labelAr={labels.ar.headline_loss}
          value={formatUSD(headline.total_loss_usd)}
          severity={headline.total_loss_usd >= 1e10 ? "critical" : headline.total_loss_usd >= 1e9 ? "severe" : headline.total_loss_usd >= 1e8 ? "high" : "medium"}
          sublabel={`${headline.affected_entities} entities`}
          locale={lang}
        />
        <KPICard
          label={t.severity}
          labelAr={labels.ar.severity}
          value={`${(data.scenario.severity * 100).toFixed(0)}%`}
          severity={data.scenario.severity >= 0.8 ? "critical" : data.scenario.severity >= 0.6 ? "severe" : data.scenario.severity >= 0.4 ? "high" : "medium"}
          sublabel={`${headline.critical_count} critical`}
          locale={lang}
        />
        <KPICard
          label={t.peak_day}
          labelAr={labels.ar.peak_day}
          value={`Day ${headline.peak_day}`}
          sublabel={`${headline.max_recovery_days}d recovery`}
          locale={lang}
        />
        <KPICard
          label={t.ttl_breach}
          labelAr={labels.ar.ttl_breach}
          value={formatHours(banking.time_to_liquidity_breach_hours)}
          severity={banking.time_to_liquidity_breach_hours < 24 ? "critical" : banking.time_to_liquidity_breach_hours < 72 ? "high" : "normal"}
          locale={lang}
        />
        <KPICard
          label={t.tt_insurance}
          labelAr={labels.ar.tt_insurance}
          value={formatHours(insurance.time_to_insolvency_hours)}
          severity={insurance.time_to_insolvency_hours < 48 ? "critical" : insurance.time_to_insolvency_hours < 168 ? "high" : "normal"}
          locale={lang}
        />
        <KPICard
          label={t.tt_payment}
          labelAr={labels.ar.tt_payment}
          value={formatHours(fintech.time_to_payment_failure_hours)}
          severity={fintech.time_to_payment_failure_hours < 12 ? "critical" : fintech.time_to_payment_failure_hours < 48 ? "high" : "normal"}
          locale={lang}
        />
      </section>

      {/* Middle + Right: Financial Impact + Sector Stress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Financial Impact Panel (2 cols) */}
        <div className="lg:col-span-2">
          <FinancialImpactPanel
            loss_usd={headline.total_loss_usd}
            loss_baseline_usd={headline.total_loss_usd * 1.5}
            peak_loss_day={headline.peak_day}
            duration_days={headline.max_recovery_days}
            liquidity_breach_hours={banking.time_to_liquidity_breach_hours}
            sector_exposure={financial.reduce<Record<string, number>>((acc, fi) => {
              acc[fi.sector] = (acc[fi.sector] ?? 0) + fi.loss_usd;
              return acc;
            }, {})}
            severity_code={
              data.scenario.severity >= 0.85 ? "CRITICAL"
              : data.scenario.severity >= 0.7 ? "SEVERE"
              : data.scenario.severity >= 0.55 ? "HIGH"
              : data.scenario.severity >= 0.4 ? "ELEVATED"
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
              score={Math.round(banking.aggregate_stress * 100)}
              classification={banking.classification}
              indicators={[
                `Liquidity ${(banking.liquidity_stress * 100).toFixed(0)}%`,
                `Credit ${(banking.credit_stress * 100).toFixed(0)}%`,
              ]}
              indicatorsAr={[
                `السيولة ${(banking.liquidity_stress * 100).toFixed(0)}%`,
                `الائتمان ${(banking.credit_stress * 100).toFixed(0)}%`,
              ]}
              locale={lang}
            />
          </div>
          <div onClick={() => onNavigate?.("insurance")} className={onNavigate ? "cursor-pointer" : ""}>
            <StressGauge
              sector="insurance"
              sectorLabel={t.insurance_stress}
              sectorLabelAr={labels.ar.insurance_stress}
              score={Math.round(insurance.aggregate_stress * 100)}
              classification={insurance.classification}
              indicators={[
                `Claims ${insurance.claims_surge_multiplier.toFixed(2)}x`,
                `Combined ${(insurance.combined_ratio * 100).toFixed(0)}%`,
              ]}
              indicatorsAr={[
                `المطالبات ${insurance.claims_surge_multiplier.toFixed(2)}x`,
                `النسبة ${(insurance.combined_ratio * 100).toFixed(0)}%`,
              ]}
              locale={lang}
            />
          </div>
          <div onClick={() => onNavigate?.("fintech")} className={onNavigate ? "cursor-pointer" : ""}>
            <StressGauge
              sector="fintech"
              sectorLabel={t.fintech_stress}
              sectorLabelAr={labels.ar.fintech_stress}
              score={Math.round(fintech.aggregate_stress * 100)}
              classification={fintech.classification}
              indicators={[
                `Payments −${fintech.payment_volume_impact_pct.toFixed(1)}%`,
                `API ${fintech.api_availability_pct.toFixed(0)}% up`,
              ]}
              indicatorsAr={[
                `المدفوعات −${fintech.payment_volume_impact_pct.toFixed(1)}%`,
                `الإتاحة ${fintech.api_availability_pct.toFixed(0)}%`,
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
          {decisions.actions.map((action, i) => (
            <div
              key={action.id}
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
                    <strong>{t.priority}:</strong> {action.priority.toFixed(1)}
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
                  action.urgency > 50
                    ? "CRITICAL"
                    : action.urgency > 10
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
