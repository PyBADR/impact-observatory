"use client";

/**
 * Regulatory Timeline Panel — Breach events, compliance state, mandatory actions
 * Impact Observatory | مرصد الأثر
 */

import React from "react";
import type { RegulatoryBreachEvent, RegulatoryState, Language } from "@/types/observatory";

interface Props {
  breachEvents: RegulatoryBreachEvent[];
  regulatoryState: RegulatoryState | undefined;
  lang: Language;
}

const breachColors: Record<string, string> = {
  minor: "bg-yellow-100 text-yellow-800 border-yellow-300",
  major: "bg-orange-100 text-orange-800 border-orange-300",
  critical: "bg-red-100 text-red-800 border-red-300",
};

const breachLevelColors: Record<string, string> = {
  none: "bg-green-100 text-green-800",
  minor: "bg-yellow-100 text-yellow-800",
  major: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export default function RegulatoryTimelinePanel({ breachEvents, regulatoryState, lang }: Props) {
  const isAr = lang === "ar";

  return (
    <div className="space-y-6">
      {/* Regulatory State Summary */}
      {regulatoryState && (
        <div className="bg-io-surface border border-io-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-io-primary">
              {isAr ? "الحالة التنظيمية" : "Regulatory State"}
            </h3>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${breachLevelColors[regulatoryState.breach_level] || breachLevelColors.none}`}>
              {regulatoryState.breach_level.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-io-bg rounded-lg p-3 text-center">
              <p className="text-[10px] text-io-secondary">LCR</p>
              <p className={`text-lg font-bold tabular-nums ${regulatoryState.aggregate_lcr < 1.0 ? "text-red-600" : "text-green-600"}`}>
                {(regulatoryState.aggregate_lcr * 100).toFixed(1)}%
              </p>
              <p className="text-[9px] text-io-secondary">min: 100%</p>
            </div>
            <div className="bg-io-bg rounded-lg p-3 text-center">
              <p className="text-[10px] text-io-secondary">NSFR</p>
              <p className={`text-lg font-bold tabular-nums ${regulatoryState.aggregate_nsfr < 1.0 ? "text-red-600" : "text-green-600"}`}>
                {(regulatoryState.aggregate_nsfr * 100).toFixed(1)}%
              </p>
              <p className="text-[9px] text-io-secondary">min: 100%</p>
            </div>
            <div className="bg-io-bg rounded-lg p-3 text-center">
              <p className="text-[10px] text-io-secondary">{isAr ? "الملاءة" : "Solvency"}</p>
              <p className={`text-lg font-bold tabular-nums ${regulatoryState.aggregate_solvency_ratio < 1.0 ? "text-red-600" : "text-green-600"}`}>
                {(regulatoryState.aggregate_solvency_ratio * 100).toFixed(1)}%
              </p>
              <p className="text-[9px] text-io-secondary">min: 100%</p>
            </div>
            <div className="bg-io-bg rounded-lg p-3 text-center">
              <p className="text-[10px] text-io-secondary">CAR</p>
              <p className={`text-lg font-bold tabular-nums ${regulatoryState.aggregate_capital_adequacy_ratio < 0.13 ? "text-red-600" : "text-green-600"}`}>
                {(regulatoryState.aggregate_capital_adequacy_ratio * 100).toFixed(2)}%
              </p>
              <p className="text-[9px] text-io-secondary">min: 13%</p>
            </div>
          </div>

          {/* Jurisdiction & Reporting */}
          <div className="flex items-center justify-between text-xs text-io-secondary border-t border-io-border pt-3">
            <span>{isAr ? "السلطة القضائية" : "Jurisdiction"}: <strong className="text-io-primary">{regulatoryState.jurisdiction}</strong></span>
            <span>v{regulatoryState.regulatory_version}</span>
            {regulatoryState.reporting_required && (
              <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded font-bold">
                {isAr ? "تقرير مطلوب" : "REPORTING REQUIRED"}
              </span>
            )}
          </div>

          {/* Mandatory Actions */}
          {regulatoryState.mandatory_actions.length > 0 && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-xs font-bold text-red-800 mb-2">
                {isAr ? "إجراءات إلزامية" : "Mandatory Actions"}
              </p>
              <ul className="space-y-1">
                {regulatoryState.mandatory_actions.map((action, i) => (
                  <li key={i} className="text-xs text-red-700 flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-red-400 flex-shrink-0" />
                    {action.replace(/_/g, " ")}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Breach Events Timeline */}
      <div className="bg-io-surface border border-io-border rounded-xl p-6">
        <h3 className="text-base font-bold text-io-primary mb-4">
          {isAr ? "أحداث الانتهاك التنظيمي" : "Regulatory Breach Events"}
        </h3>

        {breachEvents.length === 0 ? (
          <p className="text-sm text-io-secondary text-center py-4">
            {isAr ? "لا توجد أحداث انتهاك" : "No breach events detected"}
          </p>
        ) : (
          <div className="space-y-3">
            {breachEvents.map((event, i) => (
              <div
                key={i}
                className={`border rounded-lg p-4 ${breachColors[event.breach_level] || breachColors.minor}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase">
                    {event.breach_level} {isAr ? "انتهاك" : "BREACH"}
                  </span>
                  <span className="text-[10px]">T+{event.timestep_index}h</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-opacity-70">{isAr ? "المقياس" : "Metric"}: </span>
                    <strong>{event.metric_name.toUpperCase()}</strong>
                  </div>
                  <div>
                    <span className="text-opacity-70">{isAr ? "القطاع" : "Scope"}: </span>
                    <strong className="capitalize">{event.scope_ref}</strong>
                  </div>
                  <div>
                    <span className="text-opacity-70">{isAr ? "القيمة" : "Value"}: </span>
                    <strong className="tabular-nums">{(event.metric_value * 100).toFixed(1)}%</strong>
                  </div>
                  <div>
                    <span className="text-opacity-70">{isAr ? "الحد" : "Threshold"}: </span>
                    <strong className="tabular-nums">{(event.threshold_value * 100).toFixed(1)}%</strong>
                  </div>
                </div>
                <div className="flex gap-2 mt-2">
                  {event.first_breach && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/50 font-medium">
                      {isAr ? "أول انتهاك" : "FIRST BREACH"}
                    </span>
                  )}
                  {event.reportable && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/50 font-medium">
                      {isAr ? "يتطلب تقرير" : "REPORTABLE"}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
