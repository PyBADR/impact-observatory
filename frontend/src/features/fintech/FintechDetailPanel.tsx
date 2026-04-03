"use client";

/**
 * Impact Observatory | مرصد الأثر — Fintech Stress Detail Panel
 *
 * Shows full fintech/payment system stress breakdown:
 * - Aggregate stress + classification
 * - Payment volume impact
 * - Settlement delay
 * - API availability
 * - Cross-border disruption
 * - Affected platforms table
 * - Time to payment failure countdown
 */

import React from "react";
import type { FintechStress, Classification, Language } from "@/types/observatory";
import { StressGauge } from "@/components/StressGauge";

// ── Helpers ──────────────────────────────────────────────────────────

const classificationColors: Record<Classification, string> = {
  CRITICAL: "bg-io-critical text-white",
  ELEVATED: "bg-io-elevated text-white",
  MODERATE: "bg-io-moderate text-white",
  LOW: "bg-io-low text-white",
  NOMINAL: "bg-io-nominal text-white",
};

function Badge({ level }: { level: Classification }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${classificationColors[level]}`}>
      {level}
    </span>
  );
}

function formatHours(hours: number): string {
  if (!isFinite(hours)) return "N/A";
  if (hours >= 720) return `${Math.round(hours / 720)}mo`;
  if (hours >= 168) return `${Math.round(hours / 168)}w`;
  if (hours >= 24) return `${Math.round(hours / 24)}d`;
  return `${Math.round(hours)}h`;
}

function MetricRing({ value, label, unit, color }: { value: number; label: string; unit: string; color: string }) {
  const pct = Math.min(Math.abs(value), 100);
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" fill="none" strokeWidth="5" className="stroke-io-border" />
          <circle
            cx="40" cy="40" r="36" fill="none" strokeWidth="5"
            className={color}
            strokeLinecap="round"
            strokeDasharray={`${circumference}`}
            strokeDashoffset={`${offset}`}
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold tabular-nums text-io-primary">
            {value.toFixed(1)}
          </span>
          <span className="text-[10px] text-io-secondary">{unit}</span>
        </div>
      </div>
      <p className="text-xs font-medium text-io-secondary mt-2 text-center">{label}</p>
    </div>
  );
}

// ── Labels ────────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Fintech & Payment Systems Stress",
    aggregate: "Aggregate Stress",
    payment_drop: "Payment Volume Drop",
    settlement: "Settlement Delay",
    api_uptime: "API Availability",
    cross_border: "Cross-Border Disruption",
    digital_banking: "Digital Banking Stress",
    tt_failure: "Time to Payment Failure",
    system_metrics: "System Metrics",
    platforms: "Affected Platforms",
    platform: "Platform",
    country: "Country",
    volume_impact: "Volume Impact",
    cb_stress: "Cross-Border",
    stress: "Stress",
  },
  ar: {
    title: "ضغط الفنتك وأنظمة الدفع",
    aggregate: "الضغط الكلي",
    payment_drop: "انخفاض حجم المدفوعات",
    settlement: "تأخر التسوية",
    api_uptime: "توفر واجهة API",
    cross_border: "تعطل المدفوعات العابرة",
    digital_banking: "ضغط البنوك الرقمية",
    tt_failure: "الوقت إلى فشل المدفوعات",
    system_metrics: "مقاييس النظام",
    platforms: "المنصات المتأثرة",
    platform: "المنصة",
    country: "الدولة",
    volume_impact: "أثر الحجم",
    cb_stress: "العابرة للحدود",
    stress: "الضغط",
  },
};

// ── Main Component ───────────────────────────────────────────────────

export default function FintechDetailPanel({
  data,
  lang = "en",
}: {
  data: FintechStress;
  lang?: Language;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";

  return (
    <div className={`space-y-6 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-io-primary">{t.title}</h2>
        <Badge level={data.classification as Classification} />
      </div>

      {/* Stress Gauge */}
      <div className="flex justify-center">
        <StressGauge
          sector="fintech"
          sectorLabel="Fintech Stress"
          sectorLabelAr="ضغط الفنتك"
          score={Math.round(data.aggregate_stress * 100)}
          classification={data.classification}
          indicators={[
            `Payments −${data.payment_volume_impact_pct.toFixed(1)}%`,
            `API ${data.api_availability_pct.toFixed(0)}% up`,
          ]}
          indicatorsAr={[
            `المدفوعات −${data.payment_volume_impact_pct.toFixed(1)}%`,
            `الإتاحة ${data.api_availability_pct.toFixed(0)}%`,
          ]}
          locale={lang}
        />
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.aggregate}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{(data.aggregate_stress * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.tt_failure}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{formatHours(data.time_to_payment_failure_hours)}</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.digital_banking}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{(data.digital_banking_stress * 100).toFixed(1)}%</p>
        </div>
      </div>

      {/* System Metrics Rings */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-6">{t.system_metrics}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 justify-items-center">
          <MetricRing
            value={data.payment_volume_impact_pct}
            label={t.payment_drop}
            unit="%"
            color="stroke-io-danger"
          />
          <MetricRing
            value={data.settlement_delay_hours}
            label={t.settlement}
            unit="hrs"
            color="stroke-io-warning"
          />
          <MetricRing
            value={data.api_availability_pct}
            label={t.api_uptime}
            unit="%"
            color="stroke-io-accent"
          />
          <MetricRing
            value={data.cross_border_disruption * 100}
            label={t.cross_border}
            unit="%"
            color="stroke-io-elevated"
          />
        </div>
      </div>

      {/* Platforms Table */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.platforms}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-io-border text-io-secondary">
                <th className="text-left py-2 font-medium">{t.platform}</th>
                <th className="text-left py-2 font-medium">{t.country}</th>
                <th className="text-right py-2 font-medium">{t.volume_impact}</th>
                <th className="text-right py-2 font-medium">{t.cb_stress}</th>
                <th className="text-right py-2 font-medium">{t.stress}</th>
              </tr>
            </thead>
            <tbody>
              {data.affected_platforms.map((platform) => (
                <tr key={platform.id} className="border-b border-io-border/50">
                  <td className="py-2.5 font-medium text-io-primary">
                    {lang === "ar" ? platform.name_ar : platform.name}
                  </td>
                  <td className="py-2.5 text-io-secondary">{platform.country}</td>
                  <td className="py-2.5 text-right tabular-nums">
                    <span className={platform.volume_impact_pct > 30 ? "text-io-danger font-semibold" : "text-io-primary"}>
                      {platform.volume_impact_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2.5 text-right tabular-nums">
                    {(platform.cross_border_stress * 100).toFixed(1)}%
                  </td>
                  <td className="py-2.5 text-right tabular-nums">
                    <span className={platform.stress > 0.6 ? "text-io-danger font-semibold" : platform.stress > 0.4 ? "text-io-warning" : "text-io-primary"}>
                      {(platform.stress * 100).toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
