"use client";

/**
 * Impact Observatory | مرصد الأثر — Business Impact Timeline
 *
 * Dashboard card #11 (McKinsey pyramid).
 * Renders the 14-timestep loss trajectory from /runs/{id}/timeline.
 * Uses Recharts AreaChart. Marks peak day. Shows stress bands.
 */

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { formatUSD } from "@/lib/format";
import type { TimelineStep, Language } from "@/types/observatory";

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Business Impact Timeline",
    loss: "Cumulative Loss",
    stress: "System Stress",
    step: "Step",
    peak: "Peak",
  },
  ar: {
    title: "الجدول الزمني لأثر الأعمال",
    loss: "الخسارة التراكمية",
    stress: "ضغط النظام",
    step: "الخطوة",
    peak: "الذروة",
  },
};

function formatShortUSD(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${Math.round(value)}`;
}

export default function BusinessTimeline({
  data,
  lang = "en",
}: {
  data: TimelineStep[];
  lang?: Language;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";

  if (!data || data.length === 0) {
    return (
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.title}</h3>
        <p className="text-sm text-io-secondary">No timeline data available.</p>
      </div>
    );
  }

  // Find peak day
  const peakStep = data.reduce(
    (max, s) => (s.cumulative_loss > max.cumulative_loss ? s : max),
    data[0]
  );

  const chartData = data.map((s) => ({
    name: `${s.timestep}`,
    loss: s.cumulative_loss,
    stress: s.aggregate_stress * 100,
  }));

  return (
    <div
      className={`bg-io-surface border border-io-border rounded-xl p-5 shadow-sm ${isRTL ? "font-ar" : "font-sans"}`}
      dir={isRTL ? "rtl" : "ltr"}
    >
      <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">
        {t.title}
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <defs>
              <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#6b7280" }}
              label={{ value: t.step, position: "insideBottom", offset: -2, fontSize: 11, fill: "#9ca3af" }}
            />
            <YAxis
              tickFormatter={formatShortUSD}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              width={60}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                name === "loss" ? formatUSD(value) : `${value.toFixed(1)}%`,
                name === "loss" ? t.loss : t.stress,
              ]}
              labelFormatter={(label) => `${t.step} ${label}`}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
            />
            <Area
              type="monotone"
              dataKey="loss"
              stroke="#ef4444"
              strokeWidth={2}
              fill="url(#lossGradient)"
            />
            {peakStep && (
              <ReferenceLine
                x={`${peakStep.timestep}`}
                stroke="#dc2626"
                strokeDasharray="4 4"
                label={{ value: t.peak, position: "top", fontSize: 10, fill: "#dc2626" }}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
