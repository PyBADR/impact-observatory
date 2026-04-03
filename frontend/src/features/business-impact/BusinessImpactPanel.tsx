"use client";

/**
 * Business Impact Panel — Loss trajectory, time-to-failure, severity summary
 * Impact Observatory | مرصد الأثر
 */

import React from "react";
import type { BusinessImpact, Language } from "@/types/observatory";

interface Props {
  data: BusinessImpact | undefined;
  lang: Language;
}

const severityColors: Record<string, string> = {
  low: "bg-green-100 text-green-800 border-green-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  severe: "bg-red-100 text-red-800 border-red-200",
};

const statusColors: Record<string, string> = {
  monitor: "bg-green-100 text-green-800",
  intervene: "bg-yellow-100 text-yellow-800",
  escalate: "bg-orange-100 text-orange-800",
  crisis: "bg-red-100 text-red-800",
};

const statusLabels: Record<string, Record<string, string>> = {
  en: { monitor: "Monitor", intervene: "Intervene", escalate: "Escalate", crisis: "Crisis" },
  ar: { monitor: "مراقبة", intervene: "تدخل", escalate: "تصعيد", crisis: "أزمة" },
};

export default function BusinessImpactPanel({ data, lang }: Props) {
  const isAr = lang === "ar";
  if (!data || !data.summary) {
    return (
      <div className="bg-io-surface border border-io-border rounded-xl p-6 text-center text-io-secondary">
        {isAr ? "لا توجد بيانات أثر الأعمال" : "No business impact data available"}
      </div>
    );
  }

  const { summary, loss_trajectory = [], time_to_failures = [] } = data;
  const maxLoss = Math.max(...(loss_trajectory ?? []).map((p) => p.cumulative_loss), 1);

  return (
    <div className="space-y-6">
      {/* Executive Summary Strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-io-surface border border-io-border rounded-xl p-4 text-center">
          <p className="text-xs text-io-secondary font-medium">{isAr ? "ذروة الخسارة" : "Peak Loss"}</p>
          <p className="text-xl font-bold text-io-danger tabular-nums">
            ${((summary?.peak_cumulative_loss ?? 0) / 1e9).toFixed(2)}B
          </p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 text-center">
          <p className="text-xs text-io-secondary font-medium">{isAr ? "وقت الذروة" : "Peak Step"}</p>
          <p className="text-xl font-bold text-io-primary tabular-nums">
            T+{summary.peak_loss_timestep}h
          </p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 text-center">
          <p className="text-xs text-io-secondary font-medium">{isAr ? "أول فشل" : "First Failure"}</p>
          <p className="text-xl font-bold text-io-danger tabular-nums">
            {summary?.system_time_to_first_failure_hours != null && isFinite(summary.system_time_to_first_failure_hours)
              ? `${summary.system_time_to_first_failure_hours.toFixed(0)}h`
              : "—"}
          </p>
          <p className="text-[10px] text-io-secondary mt-0.5">
            {summary.first_failure_type?.replace("_", " ") || ""}
          </p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 text-center">
          <p className="text-xs text-io-secondary font-medium">{isAr ? "خطورة الأعمال" : "Severity"}</p>
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold border ${severityColors[summary.business_severity] || severityColors.low}`}>
            {summary.business_severity.toUpperCase()}
          </span>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 text-center">
          <p className="text-xs text-io-secondary font-medium">{isAr ? "حالة تنفيذية" : "Exec Status"}</p>
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${statusColors[summary.executive_status] || statusColors.monitor}`}>
            {statusLabels[lang]?.[summary.executive_status] || summary.executive_status}
          </span>
        </div>
      </div>

      {/* Loss Trajectory Chart (CSS-based) */}
      <div className="bg-io-surface border border-io-border rounded-xl p-6">
        <h3 className="text-base font-bold text-io-primary mb-4">
          {isAr ? "مسار الخسارة التراكمية" : "Cumulative Loss Trajectory"}
        </h3>
        <div className="space-y-1.5">
          {loss_trajectory.map((point) => {
            const pct = (point.cumulative_loss / maxLoss) * 100;
            const directPct = (point.direct_loss / maxLoss) * 100;
            const propPct = (point.propagated_loss / maxLoss) * 100;
            return (
              <div key={point.timestep_index} className="flex items-center gap-2">
                <span className="text-[10px] text-io-secondary w-8 text-right tabular-nums">
                  T+{point.timestep_index}
                </span>
                <div className="flex-1 h-5 bg-io-bg rounded-sm overflow-hidden relative">
                  <div
                    className="h-full bg-red-400 absolute left-0 top-0"
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                  <div
                    className="h-full bg-orange-300 absolute left-0 top-0"
                    style={{ width: `${Math.min(directPct, 100)}%` }}
                  />
                </div>
                <span className="text-[10px] text-io-secondary w-20 text-right tabular-nums">
                  ${((point?.cumulative_loss ?? 0) / 1e9).toFixed(2)}B
                </span>
                <span className={`text-[9px] w-16 text-right font-medium ${
                  point.status === "critical" ? "text-red-600" :
                  point.status === "deteriorating" ? "text-orange-600" : "text-green-600"
                }`}>
                  {point.status}
                </span>
              </div>
            );
          })}
        </div>
        <div className="flex gap-4 mt-3 text-[10px] text-io-secondary">
          <span className="flex items-center gap-1"><span className="w-3 h-2 bg-orange-300 rounded-sm" /> {isAr ? "مباشر" : "Direct"}</span>
          <span className="flex items-center gap-1"><span className="w-3 h-2 bg-red-400 rounded-sm" /> {isAr ? "منتشر" : "Propagated"}</span>
        </div>
      </div>

      {/* Time to Failure Table */}
      {time_to_failures.length > 0 && (
        <div className="bg-io-surface border border-io-border rounded-xl p-6">
          <h3 className="text-base font-bold text-io-primary mb-4">
            {isAr ? "الوقت حتى الفشل" : "Time to Failure"}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-io-secondary text-xs border-b border-io-border">
                  <th className="pb-2 text-left font-medium">{isAr ? "القطاع" : "Scope"}</th>
                  <th className="pb-2 text-left font-medium">{isAr ? "نوع الفشل" : "Failure Type"}</th>
                  <th className="pb-2 text-right font-medium">{isAr ? "الوقت" : "Hours"}</th>
                  <th className="pb-2 text-right font-medium">{isAr ? "الثقة" : "Confidence"}</th>
                  <th className="pb-2 text-center font-medium">{isAr ? "ضمن الأفق" : "Within Horizon"}</th>
                </tr>
              </thead>
              <tbody>
                {time_to_failures.map((ttf, i) => (
                  <tr key={i} className="border-b border-io-border/50">
                    <td className="py-2 font-medium text-io-primary capitalize">{ttf.scope_ref}</td>
                    <td className="py-2 text-io-secondary">{ttf.failure_type.replace(/_/g, " ")}</td>
                    <td className="py-2 text-right font-bold text-io-danger tabular-nums">
                      {ttf.time_to_failure_hours ? `${ttf.time_to_failure_hours}h` : "—"}
                    </td>
                    <td className="py-2 text-right tabular-nums">{((ttf?.confidence_score ?? 0) * 100).toFixed(0)}%</td>
                    <td className="py-2 text-center">
                      {ttf.failure_reached_within_horizon
                        ? <span className="text-red-600 font-bold">⚠</span>
                        : <span className="text-green-600">✓</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
