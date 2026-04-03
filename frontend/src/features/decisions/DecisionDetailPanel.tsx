"use client";

/**
 * Impact Observatory | مرصد الأثر — Decision Actions Detail Panel
 *
 * Shows full decision plan breakdown:
 * - Headline loss + time to failure
 * - All ranked decision actions (not just top 3)
 * - Priority formula breakdown per action
 * - Urgency/Value/RegulatoryRisk decomposition
 * - Causal explanation chain (bilingual)
 */

import React from "react";
import type {
  DecisionPlan,
  ExplanationPack,
  Classification,
  Language,
} from "@/types/observatory";
import { DecisionActionCard } from "@/components/DecisionActionCard";

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

function formatUSD(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}

function formatHours(hours: number): string {
  if (!isFinite(hours)) return "N/A";
  if (hours >= 720) return `${Math.round(hours / 720)}mo`;
  if (hours >= 168) return `${Math.round(hours / 168)}w`;
  if (hours >= 24) return `${Math.round(hours / 24)}d`;
  return `${Math.round(hours)}h`;
}

function PriorityBar({ urgency, value, regulatory }: { urgency: number; value: number; regulatory: number }) {
  const total = urgency + value + regulatory;
  if (total === 0) return null;
  const uPct = (urgency / total) * 100;
  const vPct = (value / total) * 100;
  const rPct = (regulatory / total) * 100;

  return (
    <div className="space-y-1">
      <div className="flex h-2 rounded-full overflow-hidden">
        <div className="bg-io-danger" style={{ width: `${uPct}%` }} title="Urgency" />
        <div className="bg-io-accent" style={{ width: `${vPct}%` }} title="Value" />
        <div className="bg-io-warning" style={{ width: `${rPct}%` }} title="Regulatory Risk" />
      </div>
      <div className="flex gap-3 text-[10px] text-io-secondary">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-io-danger inline-block" /> Urgency {urgency.toFixed(1)}</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-io-accent inline-block" /> Value {value.toFixed(1)}</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-io-warning inline-block" /> Reg. Risk {regulatory.toFixed(1)}</span>
      </div>
    </div>
  );
}

// ── Labels ────────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Decision Actions",
    headline_loss: "Headline Loss",
    peak_day: "Peak Day",
    ttf: "Time to Failure",
    total_actions: "Total Actions",
    prioritized_actions: "Prioritized Actions",
    all_actions: "All Ranked Actions",
    action: "Action",
    sector: "Sector",
    owner: "Owner",
    priority: "Priority",
    urgency: "Urgency",
    value: "Value",
    reg_risk: "Reg. Risk",
    loss_avoided: "Loss Avoided",
    cost: "Cost",
    net_benefit: "Net Benefit",
    time_to_act: "Time to Act",
    confidence: "Confidence",
    causal_chain: "Causal Explanation Chain",
    methodology: "Methodology",
    narrative: "Narrative",
    formula: "Priority = Value + Urgency + RegulatoryRisk",
    formula_detail: "Value = Loss_avoided - Cost | Urgency = Time_to_failure / Time_to_act",
  },
  ar: {
    title: "إجراءات القرار",
    headline_loss: "إجمالي الخسارة",
    peak_day: "يوم الذروة",
    ttf: "الوقت إلى الفشل",
    total_actions: "إجمالي الإجراءات",
    prioritized_actions: "الإجراءات ذات الأولوية",
    all_actions: "جميع الإجراءات المرتبة",
    action: "الإجراء",
    sector: "القطاع",
    owner: "المسؤول",
    priority: "الأولوية",
    urgency: "الإلحاح",
    value: "القيمة",
    reg_risk: "المخاطر التنظيمية",
    loss_avoided: "الخسائر المتجنبة",
    cost: "التكلفة",
    net_benefit: "صافي المنفعة",
    time_to_act: "الوقت للتنفيذ",
    confidence: "الثقة",
    causal_chain: "سلسلة التفسير السببي",
    methodology: "المنهجية",
    narrative: "السرد",
    formula: "الأولوية = القيمة + الإلحاح + المخاطر التنظيمية",
    formula_detail: "القيمة = الخسائر المتجنبة - التكلفة | الإلحاح = الوقت إلى الفشل / الوقت للتنفيذ",
  },
};

// ── Main Component ───────────────────────────────────────────────────

export default function DecisionDetailPanel({
  decisions,
  explanation,
  lang = "en",
}: {
  decisions: DecisionPlan;
  explanation?: ExplanationPack;
  lang?: Language;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";
  const allActions = decisions.all_actions?.length > 0 ? decisions.all_actions : decisions.actions;

  return (
    <div className={`space-y-6 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-io-primary">{t.title}</h2>
        <p className="text-xs text-io-secondary mt-1 font-mono">{t.formula}</p>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.headline_loss}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{formatUSD(decisions.total_loss_usd)}</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.peak_day}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">Day {decisions.peak_day}</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.ttf}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{formatHours(decisions.time_to_failure_hours)}</p>
        </div>
        <div className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">{t.total_actions}</p>
          <p className="text-2xl font-bold tabular-nums text-io-primary">{allActions.length}</p>
        </div>
      </div>

      {/* Top 3 Prioritized Actions */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.prioritized_actions}</h3>
        <div className="space-y-4">
          {decisions.actions.slice(0, 3).map((action, i) => (
            <DecisionActionCard
              key={action.id}
              rank={(i + 1) as 1 | 2 | 3}
              actionId={action.id}
              priority_score={Math.min(action.priority / 100, 1)}
              title_en={action.action}
              title_ar={action.action_ar || action.action}
              urgency={Math.min(action.urgency / 100, 1)}
              value={Math.min(action.value / 100, 1)}
              time_to_act_hours={action.time_to_act_hours}
              cost_usd={action.cost_usd}
              loss_avoided_usd={action.loss_avoided_usd}
              status="PENDING_REVIEW"
              locale={lang}
              onSubmitForReview={() => {}}
            />
          ))}
        </div>
      </div>

      {/* All Actions Table */}
      {allActions.length > 3 && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.all_actions}</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-io-border text-io-secondary">
                  <th className="text-left py-2 font-medium">#</th>
                  <th className="text-left py-2 font-medium">{t.action}</th>
                  <th className="text-left py-2 font-medium">{t.sector}</th>
                  <th className="text-right py-2 font-medium">{t.priority}</th>
                  <th className="text-right py-2 font-medium">{t.loss_avoided}</th>
                  <th className="text-right py-2 font-medium">{t.cost}</th>
                </tr>
              </thead>
              <tbody>
                {allActions.map((action, i) => (
                  <tr key={action.id} className={`border-b border-io-border/50 ${i < 3 ? "bg-io-accent/5" : ""}`}>
                    <td className="py-2 text-io-secondary">{i + 1}</td>
                    <td className="py-2 font-medium text-io-primary">
                      {lang === "ar" ? action.action_ar || action.action : action.action}
                    </td>
                    <td className="py-2 text-io-secondary">{action.sector}</td>
                    <td className="py-2 text-right tabular-nums font-semibold">{action.priority.toFixed(1)}</td>
                    <td className="py-2 text-right tabular-nums text-io-success">{formatUSD(action.loss_avoided_usd)}</td>
                    <td className="py-2 text-right tabular-nums">{formatUSD(action.cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Causal Explanation Chain */}
      {explanation && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.causal_chain}</h3>

          {/* Narrative */}
          <div className="mb-4 p-4 bg-io-bg rounded-lg border border-io-border">
            <p className="text-xs font-medium uppercase text-io-secondary mb-1">{t.narrative}</p>
            <p className="text-sm text-io-primary leading-relaxed">
              {lang === "ar" ? explanation.narrative_ar : explanation.narrative_en}
            </p>
          </div>

          {/* Chain steps */}
          <div className="space-y-0">
            {explanation.causal_chain.slice(0, 12).map((step, i) => (
              <div key={step.step} className="flex gap-3 relative">
                {/* Connector line */}
                {i < Math.min(explanation.causal_chain.length, 12) - 1 && (
                  <div className="absolute left-[15px] top-8 bottom-0 w-0.5 bg-io-border" />
                )}
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-io-accent/10 text-io-accent flex items-center justify-center text-xs font-bold z-10">
                  {step.step}
                </div>
                <div className="flex-1 pb-4">
                  <p className="text-sm font-medium text-io-primary">
                    {lang === "ar" ? step.entity_label_ar || step.entity_label : step.entity_label}
                  </p>
                  <p className="text-xs text-io-secondary">
                    {lang === "ar" ? step.event_ar || step.event : step.event}
                  </p>
                  <div className="flex gap-3 mt-1 text-xs text-io-secondary">
                    <span>Impact: {formatUSD(step.impact_usd)}</span>
                    <span>Stress: +{(step.stress_delta * 100).toFixed(1)}%</span>
                    <span className="text-io-accent">{step.mechanism}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {explanation.causal_chain.length > 12 && (
            <p className="text-xs text-io-secondary text-center mt-2">
              +{explanation.causal_chain.length - 12} more steps
            </p>
          )}

          {/* Methodology */}
          <div className="mt-4 pt-3 border-t border-io-border">
            <p className="text-xs text-io-secondary">
              <strong>{t.methodology}:</strong> {explanation.methodology}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
