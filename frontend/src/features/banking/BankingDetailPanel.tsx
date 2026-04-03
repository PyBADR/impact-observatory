"use client";

/**
 * Impact Observatory | مرصد الأثر — Banking Stress Detail Panel
 *
 * Shows full banking sector stress breakdown:
 * - Aggregate stress gauge
 * - Institution-level table
 * - Liquidity / Credit / FX / Contagion breakdown
 * - Basel III metrics
 * - Time to liquidity breach countdown
 */

import React from "react";
import type { BankingStress, Classification, Language } from "@/types/observatory";
import { StressGauge } from "@/components/StressGauge";
import { safeFixed, safeNum } from "@/lib/format";

// ── Helpers ──────────────────────────────────────────────────────────

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
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${classificationColors[level]}`}>
      {level}
    </span>
  );
}

function formatUSD(value: number | null | undefined): string {
  const v = safeNum(value);
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toLocaleString()}`;
}

function formatHours(hours: number): string {
  if (!isFinite(hours)) return "N/A";
  if (hours >= 720) return `${Math.round(hours / 720)}mo`;
  if (hours >= 168) return `${Math.round(hours / 168)}w`;
  if (hours >= 24) return `${Math.round(hours / 24)}d`;
  return `${Math.round(hours)}h`;
}

function StressBar({ value, label, color }: { value: number | null | undefined; label: string; color: string }) {
  const pct = Math.min(safeNum(value) * 100, 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-io-secondary font-medium">{label}</span>
        <span className="font-semibold text-io-primary">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-io-bg rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Labels ────────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Banking Sector Stress",
    aggregate: "Aggregate Stress",
    total_exposure: "Total Exposure",
    ttl_breach: "Time to Liquidity Breach",
    car_impact: "Capital Adequacy Impact",
    liquidity: "Liquidity Stress",
    credit: "Credit Stress",
    fx: "FX Stress",
    contagion: "Interbank Contagion",
    institutions: "Affected Institutions",
    institution: "Institution",
    country: "Country",
    exposure: "Exposure",
    stress: "Stress",
    car: "Proj. CAR",
    stress_decomposition: "Stress Decomposition",
    basel_metrics: "Basel III Indicators",
    min_car: "Minimum CAR (Basel III)",
    min_car_value: "8.0%",
    lcr_label: "LCR Requirement",
    lcr_value: "100%",
  },
  ar: {
    title: "ضغط القطاع البنكي",
    aggregate: "الضغط الكلي",
    total_exposure: "إجمالي التعرض",
    ttl_breach: "الوقت إلى كسر السيولة",
    car_impact: "أثر كفاية رأس المال",
    liquidity: "ضغط السيولة",
    credit: "ضغط الائتمان",
    fx: "ضغط العملة",
    contagion: "عدوى بين البنوك",
    institutions: "المؤسسات المتأثرة",
    institution: "المؤسسة",
    country: "الدولة",
    exposure: "التعرض",
    stress: "الضغط",
    car: "CAR المتوقع",
    stress_decomposition: "تحليل الضغط",
    basel_metrics: "مؤشرات بازل III",
    min_car: "الحد الأدنى CAR (بازل III)",
    min_car_value: "8.0%",
    lcr_label: "متطلب LCR",
    lcr_value: "100%",
  },
};

// ── Main Component ───────────────────────────────────────────────────

export default function BankingDetailPanel({
  data,
  lang = "en",
}: {
  data: BankingStress;
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
          sector="banking"
          sectorLabel={t.title}
          sectorLabelAr={t.title}
          score={Math.round(data.aggregate_stress * 100)}
          classification={data.classification}
          indicators={[
            `Liquidity ${((data?.liquidity_stress ?? 0) * 100).toFixed(0)}%`,
            `Credit ${((data?.credit_stress ?? 0) * 100).toFixed(0)}%`,
          ]}
          indicatorsAr={[
            `السيولة ${((data?.liquidity_stress ?? 0) * 100).toFixed(0)}%`,
            `الائتمان ${((data?.credit_stress ?? 0) * 100).toFixed(0)}%`,
          ]}
          locale={lang}
        />
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.aggregate}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{((data?.aggregate_stress ?? 0) * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.total_exposure}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{formatUSD(data.total_exposure_usd)}</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.ttl_breach}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{formatHours(data.time_to_liquidity_breach_hours)}</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.car_impact}</p>
          <p className="text-2xl font-bold tabular-nums text-io-danger">-{(data?.capital_adequacy_impact_pct ?? 0).toFixed(2)}%</p>
        </div>
      </div>

      {/* Stress Decomposition */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.stress_decomposition}</h3>
        <div className="space-y-3">
          <StressBar value={data.liquidity_stress} label={t.liquidity} color="bg-io-accent" />
          <StressBar value={data.credit_stress} label={t.credit} color="bg-io-warning" />
          <StressBar value={data.fx_stress} label={t.fx} color="bg-io-elevated" />
          <StressBar value={data.interbank_contagion} label={t.contagion} color="bg-io-critical" />
        </div>
      </div>

      {/* Basel III Reference */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.basel_metrics}</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex justify-between text-sm border-b border-io-border/50 pb-2">
            <span className="text-io-secondary">{t.min_car}</span>
            <span className="font-semibold text-io-primary">{t.min_car_value}</span>
          </div>
          <div className="flex justify-between text-sm border-b border-io-border/50 pb-2">
            <span className="text-io-secondary">{t.lcr_label}</span>
            <span className="font-semibold text-io-primary">{t.lcr_value}</span>
          </div>
          <div className="flex justify-between text-sm border-b border-io-border/50 pb-2">
            <span className="text-io-secondary">{t.car_impact}</span>
            <span className={`font-semibold ${data.capital_adequacy_impact_pct > 2 ? "text-io-danger" : "text-io-warning"}`}>
              -{(data?.capital_adequacy_impact_pct ?? 0).toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between text-sm border-b border-io-border/50 pb-2">
            <span className="text-io-secondary">{t.contagion}</span>
            <span className={`font-semibold ${(data?.interbank_contagion ?? 0) > 0.5 ? "text-io-danger" : "text-io-primary"}`}>
              {((data?.interbank_contagion ?? 0) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Institution Table */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.institutions}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-io-border text-io-secondary">
                <th className="text-left py-2 font-medium">{t.institution}</th>
                <th className="text-left py-2 font-medium">{t.country}</th>
                <th className="text-right py-2 font-medium">{t.exposure}</th>
                <th className="text-right py-2 font-medium">{t.stress}</th>
                <th className="text-right py-2 font-medium">{t.car}</th>
              </tr>
            </thead>
            <tbody>
              {data.affected_institutions.map((inst) => (
                <tr key={inst.id} className="border-b border-io-border/50">
                  <td className="py-2.5 font-medium text-io-primary">
                    {lang === "ar" ? inst.name_ar : inst.name}
                  </td>
                  <td className="py-2.5 text-io-secondary">{inst.country}</td>
                  <td className="py-2.5 text-right tabular-nums font-medium">{formatUSD(inst.exposure_usd)}</td>
                  <td className="py-2.5 text-right tabular-nums">
                    <span className={safeNum(inst.stress) > 0.6 ? "text-io-danger font-semibold" : safeNum(inst.stress) > 0.4 ? "text-io-warning" : "text-io-primary"}>
                      {safeFixed(safeNum(inst.stress) * 100, 1)}%
                    </span>
                  </td>
                  <td className="py-2.5 text-right tabular-nums">
                    <span className={safeNum(inst.projected_car_pct) < 10 ? "text-io-danger font-semibold" : "text-io-primary"}>
                      {safeFixed(inst.projected_car_pct, 1)}%
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
