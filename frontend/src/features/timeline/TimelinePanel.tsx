"use client";

/**
 * Timeline Panel — Temporal simulation timestep playback
 * Impact Observatory | مرصد الأثر
 */

import React from "react";
import type { TimelineResult, Language } from "@/types/observatory";

interface Props {
  data: TimelineResult | undefined;
  lang: Language;
}

const statusIcons: Record<string, string> = {
  stable: "🟢",
  degrading: "🟡",
  critical: "🔴",
  failed: "⛔",
};

export default function TimelinePanel({ data, lang }: Props) {
  const isAr = lang === "ar";

  if (!data || !data.timesteps || data.timesteps.length === 0) {
    return (
      <div className="bg-io-surface border border-io-border rounded-xl p-6 text-center text-io-secondary">
        {isAr ? "لا توجد بيانات زمنية" : "No timeline data available"}
      </div>
    );
  }

  const { timesteps, time_config } = data;
  const maxLoss = Math.max(...timesteps.map((s) => s.aggregate_loss), 1);
  const maxFlow = Math.max(...timesteps.map((s) => s.aggregate_flow), 1);

  return (
    <div className="space-y-6">
      {/* Config Info */}
      <div className="bg-io-surface border border-io-border rounded-xl p-4">
        <div className="flex flex-wrap gap-4 text-xs text-io-secondary">
          <span>{isAr ? "خطوات" : "Steps"}: <strong className="text-io-primary">{time_config.time_horizon_steps}</strong></span>
          <span>{isAr ? "الدقة" : "Granularity"}: <strong className="text-io-primary">{time_config.time_granularity_minutes}m</strong></span>
          <span>{isAr ? "تلاشي الصدمة" : "Shock Decay"}: <strong className="text-io-primary">{(time_config.shock_decay_rate * 100).toFixed(1)}%/step</strong></span>
          <span>{isAr ? "تأخير الانتشار" : "Prop. Delay"}: <strong className="text-io-primary">{time_config.propagation_delay_steps} steps</strong></span>
          <span>{isAr ? "معدل التعافي" : "Recovery"}: <strong className="text-io-primary">{(time_config.recovery_rate * 100).toFixed(1)}%/step</strong></span>
        </div>
      </div>

      {/* Timestep Table */}
      <div className="bg-io-surface border border-io-border rounded-xl p-6">
        <h3 className="text-base font-bold text-io-primary mb-4">
          {isAr ? "محاكاة زمنية خطوة بخطوة" : "Timestep Simulation"}
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-io-secondary border-b border-io-border">
                <th className="pb-2 text-left font-medium w-12">T</th>
                <th className="pb-2 text-center font-medium">{isAr ? "الحالة" : "Status"}</th>
                <th className="pb-2 text-right font-medium">{isAr ? "صدمة" : "Shock"}</th>
                <th className="pb-2 font-medium text-left pl-2">{isAr ? "الخسارة" : "Loss"}</th>
                <th className="pb-2 font-medium text-left pl-2">{isAr ? "التدفق" : "Flow"}</th>
                <th className="pb-2 text-right font-medium">{isAr ? "انتهاكات" : "Breaches"}</th>
              </tr>
            </thead>
            <tbody>
              {timesteps.map((step) => {
                const lossPct = (step.aggregate_loss / maxLoss) * 100;
                const flowPct = (step.aggregate_flow / maxFlow) * 100;
                return (
                  <tr key={step.timestep_index} className="border-b border-io-border/30 hover:bg-io-bg/50">
                    <td className="py-1.5 font-medium text-io-primary tabular-nums">+{step.timestep_index}</td>
                    <td className="py-1.5 text-center">{statusIcons[step.system_status] || "⚪"}</td>
                    <td className="py-1.5 text-right tabular-nums text-io-secondary">
                      {(step.shock_intensity_effective * 100).toFixed(1)}%
                    </td>
                    <td className="py-1.5 pl-2">
                      <div className="flex items-center gap-1">
                        <div className="w-16 h-2.5 bg-io-bg rounded-sm overflow-hidden">
                          <div className="h-full bg-red-400 rounded-sm" style={{ width: `${Math.min(lossPct, 100)}%` }} />
                        </div>
                        <span className="tabular-nums text-io-secondary">${(step.aggregate_loss / 1e9).toFixed(1)}B</span>
                      </div>
                    </td>
                    <td className="py-1.5 pl-2">
                      <div className="flex items-center gap-1">
                        <div className="w-16 h-2.5 bg-io-bg rounded-sm overflow-hidden">
                          <div className="h-full bg-blue-400 rounded-sm" style={{ width: `${Math.min(flowPct, 100)}%` }} />
                        </div>
                        <span className="tabular-nums text-io-secondary">${(step.aggregate_flow / 1e9).toFixed(1)}B</span>
                      </div>
                    </td>
                    <td className="py-1.5 text-right">
                      {step.regulatory_breach_count > 0 ? (
                        <span className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded font-bold text-[10px]">
                          {step.regulatory_breach_count}
                        </span>
                      ) : (
                        <span className="text-green-600">0</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
