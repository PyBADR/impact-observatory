"use client";

/**
 * Impact Observatory | مرصد الأثر — Regulatory Timeline
 *
 * Dashboard card #12 (McKinsey pyramid).
 * Renders regulatory breach events from /runs/{id}/regulatory-timeline.
 * Vertical event list with breach level badges and mandatory actions.
 */

import React from "react";
import type { RegulatoryEvent, Language } from "@/types/observatory";

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Regulatory Timeline",
    no_events: "No regulatory events triggered.",
    mandatory: "Mandatory Actions",
    sector: "Sector",
    step: "Step",
  },
  ar: {
    title: "الجدول الزمني التنظيمي",
    no_events: "لم يتم تفعيل أي أحداث تنظيمية.",
    mandatory: "الإجراءات الإلزامية",
    sector: "القطاع",
    step: "الخطوة",
  },
};

const breachColors: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  major: "bg-orange-100 text-orange-700 border-orange-200",
  minor: "bg-amber-100 text-amber-700 border-amber-200",
  none: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

const breachLabels: Record<Language, Record<string, string>> = {
  en: { critical: "CRITICAL", major: "MAJOR", minor: "MINOR", none: "CLEAR" },
  ar: { critical: "حرج", major: "رئيسي", minor: "ثانوي", none: "سليم" },
};

export default function RegulatoryTimeline({
  data,
  lang = "en",
}: {
  data: RegulatoryEvent[];
  lang?: Language;
}) {
  const t = labels[lang];
  const bl = breachLabels[lang];
  const isRTL = lang === "ar";

  return (
    <div
      className={`bg-io-surface border border-io-border rounded-xl p-5 shadow-sm ${isRTL ? "font-ar" : "font-sans"}`}
      dir={isRTL ? "rtl" : "ltr"}
    >
      <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">
        {t.title}
      </h3>

      {(!data || data.length === 0) ? (
        <p className="text-sm text-io-secondary">{t.no_events}</p>
      ) : (
        <div className="space-y-3">
          {data.map((event, i) => (
            <div key={i} className="flex gap-3">
              {/* Timeline connector */}
              <div className="flex flex-col items-center">
                <div className={`w-3 h-3 rounded-full border-2 ${
                  event.breach_level === "critical" ? "bg-red-500 border-red-500" :
                  event.breach_level === "major" ? "bg-orange-500 border-orange-500" :
                  event.breach_level === "minor" ? "bg-amber-500 border-amber-500" :
                  "bg-emerald-500 border-emerald-500"
                }`} />
                {i < data.length - 1 && <div className="w-0.5 flex-1 bg-io-border mt-1" />}
              </div>

              {/* Event content */}
              <div className="flex-1 pb-4">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs text-io-secondary font-medium">
                    {t.step} {event.timestep}
                  </span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${breachColors[event.breach_level] ?? breachColors.none}`}>
                    {bl[event.breach_level] ?? event.breach_level}
                  </span>
                  <span className="text-[10px] text-io-secondary px-1.5 py-0.5 bg-io-bg rounded border border-io-border">
                    {event.sector}
                  </span>
                </div>

                {event.mandatory_actions.length > 0 && (
                  <div className="text-xs text-io-secondary">
                    <span className="font-medium">{t.mandatory}: </span>
                    {event.mandatory_actions.join(", ")}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
