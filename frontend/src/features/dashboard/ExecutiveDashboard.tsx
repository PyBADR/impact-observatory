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
        <MetricCard
          label={t.headline_loss}
          value={formatUSD(headline.total_loss_usd)}
          sub={`${headline.affected_entities} entities`}
        />
        <MetricCard
          label={t.severity}
          value={`${(data.scenario.severity * 100).toFixed(0)}%`}
          sub={`${headline.critical_count} critical`}
        />
        <MetricCard
          label={t.peak_day}
          value={`Day ${headline.peak_day}`}
          sub={`${headline.max_recovery_days}d recovery`}
        />
        <MetricCard
          label={t.ttl_breach}
          value={formatHours(banking.time_to_liquidity_breach_hours)}
        />
        <MetricCard
          label={t.tt_insurance}
          value={formatHours(insurance.time_to_insolvency_hours)}
        />
        <MetricCard
          label={t.tt_payment}
          value={formatHours(fintech.time_to_payment_failure_hours)}
        />
      </section>

      {/* Middle + Right: Financial Impact + Sector Stress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Financial Impact Table (2 cols) */}
        <div className="lg:col-span-2 bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">
            {t.financial_impact}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-io-border text-io-secondary">
                  <th className="text-left py-2 font-medium">{t.entity}</th>
                  <th className="text-left py-2 font-medium">{t.sector}</th>
                  <th className="text-right py-2 font-medium">{t.loss}</th>
                  <th className="text-right py-2 font-medium">{t.stress}</th>
                  <th className="text-center py-2 font-medium">{t.classification}</th>
                </tr>
              </thead>
              <tbody>
                {financial.slice(0, 10).map((fi) => (
                  <tr key={fi.entity_id} className="border-b border-io-border/50">
                    <td className="py-2 font-medium text-io-primary">
                      {fi.entity_label || fi.entity_id}
                    </td>
                    <td className="py-2 text-io-secondary">{fi.sector}</td>
                    <td className="py-2 text-right tabular-nums font-medium">
                      {formatUSD(fi.loss_usd)}
                    </td>
                    <td className="py-2 text-right tabular-nums">
                      {(fi.stress_level * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 text-center">
                      <Badge level={fi.classification} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Sector Stress Cards (1 col) */}
        <div className="space-y-4">
          <div onClick={() => onNavigate?.("banking")} className={onNavigate ? "cursor-pointer" : ""}>
            <SectorStressCard
              title={t.banking_stress}
              classification={banking.classification as Classification}
              stress={banking.aggregate_stress}
              metrics={[
                { label: "Liquidity", value: `${(banking.liquidity_stress * 100).toFixed(0)}%` },
                { label: "Credit", value: `${(banking.credit_stress * 100).toFixed(0)}%` },
                { label: "FX", value: `${(banking.fx_stress * 100).toFixed(0)}%` },
                { label: "Contagion", value: `${(banking.interbank_contagion * 100).toFixed(0)}%` },
              ]}
            />
          </div>
          <div onClick={() => onNavigate?.("insurance")} className={onNavigate ? "cursor-pointer" : ""}>
            <SectorStressCard
              title={t.insurance_stress}
              classification={insurance.classification as Classification}
              stress={insurance.aggregate_stress}
              metrics={[
                { label: "Claims Surge", value: `${insurance.claims_surge_multiplier.toFixed(2)}x` },
                { label: "Combined Ratio", value: `${(insurance.combined_ratio * 100).toFixed(0)}%` },
                { label: "UW Status", value: insurance.underwriting_status },
                { label: "Reinsurance", value: insurance.reinsurance_trigger ? "TRIGGERED" : "Normal" },
              ]}
            />
          </div>
          <div onClick={() => onNavigate?.("fintech")} className={onNavigate ? "cursor-pointer" : ""}>
            <SectorStressCard
              title={t.fintech_stress}
              classification={fintech.classification as Classification}
              stress={fintech.aggregate_stress}
              metrics={[
                { label: "Payment Drop", value: `${fintech.payment_volume_impact_pct.toFixed(1)}%` },
                { label: "Delay", value: `+${fintech.settlement_delay_hours.toFixed(1)}h` },
                { label: "API Uptime", value: `${fintech.api_availability_pct.toFixed(0)}%` },
                { label: "Cross-Border", value: `${(fintech.cross_border_disruption * 100).toFixed(0)}%` },
              ]}
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
