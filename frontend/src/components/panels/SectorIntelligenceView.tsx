"use client";

/**
 * Impact Observatory | مرصد الأثر — Sector Intelligence View
 *
 * Tabbed interface displaying:
 * - Intelligence Brief: scenario narrative + risk signals + causal chain
 * - Banking Stress: full banking sector breakdown
 * - Insurance Stress: insurance lines + underwriting metrics
 * - Fintech Stress: digital platform disruption
 * - Executive Directive: top 3 decisions with urgency + cost/benefit
 */

import React, { useState } from "react";
import type { BankingStress, InsuranceStress, FintechStress, Language } from "@/types/observatory";
import BankingDetailPanel from "@/features/banking/BankingDetailPanel";
import InsuranceDetailPanel from "@/features/insurance/InsuranceDetailPanel";
import FintechDetailPanel from "@/features/fintech/FintechDetailPanel";
import { formatUSD, formatHours, safeFixed, safePercent } from "@/lib/format";

// ── Types ────────────────────────────────────────────────────────────

interface MacroSignal {
  id: string;
  name_en: string;
  name_ar: string;
  value: string;
  impact: string;
}

interface CausalStep {
  step: number;
  entity_label: string;
  event: string;
  impact_usd: number;
}

interface DecisionAction {
  id: string;
  action: string;
  action_ar?: string;
  sector: string;
  owner: string;
  priority: number;
  cost_usd: number;
  loss_avoided_usd: number;
  confidence: number;
  time_to_act_hours: number;
}

export interface SectorIntelligenceViewProps {
  locale: "en" | "ar";
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  severity?: number;
  narrativeEn?: string;
  narrativeAr?: string;
  systemRiskIndex?: number;
  macroSignals?: MacroSignal[];
  causalChain?: CausalStep[];
  bankingStress?: BankingStress;
  insuranceStress?: InsuranceStress;
  fintechStress?: FintechStress;
  decisionActions?: DecisionAction[];
}

// ── Labels ────────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    intelligence_brief: "Intelligence Brief",
    banking_stress: "Banking Stress",
    insurance_stress: "Insurance Stress",
    fintech_stress: "Fintech Stress",
    executive_directive: "Executive Directive",
    scenario_context: "Scenario Context",
    severity: "Severity",
    narrative_summary: "Narrative Summary",
    system_risk_index: "System Risk Index",
    top_signals: "Top Macro Signals",
    causal_chain: "Causal Chain",
    signal_name: "Signal",
    signal_value: "Value",
    signal_impact: "Impact",
    step: "Step",
    entity: "Entity",
    event: "Event",
    impact: "Impact (USD)",
    no_data: "No data available",
    no_banking: "No banking stress data for this scenario",
    no_insurance: "No insurance stress data for this scenario",
    no_fintech: "No fintech stress data for this scenario",
    top_decisions: "Top 3 Decisions",
    action: "Action",
    sector_alignment: "Sector Alignment",
    owner: "Owner",
    priority: "Priority",
    cost: "Cost (USD)",
    loss_avoided: "Loss Avoided (USD)",
    confidence: "Confidence",
    time_to_act: "Time to Act",
    urgency_critical: "Critical",
    urgency_high: "High",
    urgency_medium: "Medium",
    urgency_low: "Low",
  },
  ar: {
    intelligence_brief: "موجز المعلومات",
    banking_stress: "ضغط القطاع البنكي",
    insurance_stress: "ضغط قطاع التأمين",
    fintech_stress: "ضغط قطاع التكنولوجيا المالية",
    executive_directive: "التوجيه التنفيذي",
    scenario_context: "سياق السيناريو",
    severity: "الشدة",
    narrative_summary: "ملخص السرد",
    system_risk_index: "مؤشر خطر النظام",
    top_signals: "أهم الإشارات الاقتصادية الكلية",
    causal_chain: "السلسلة السببية",
    signal_name: "الإشارة",
    signal_value: "القيمة",
    signal_impact: "التأثير",
    step: "الخطوة",
    entity: "الكيان",
    event: "الحدث",
    impact: "التأثير (دولار)",
    no_data: "لا توجد بيانات متاحة",
    no_banking: "لا توجد بيانات ضغط بنكي لهذا السيناريو",
    no_insurance: "لا توجد بيانات ضغط تأمين لهذا السيناريو",
    no_fintech: "لا توجد بيانات ضغط تقني مالي لهذا السيناريو",
    top_decisions: "أفضل 3 قرارات",
    action: "الإجراء",
    sector_alignment: "المحاذاة القطاعية",
    owner: "المسؤول",
    priority: "الأولوية",
    cost: "التكلفة (دولار)",
    loss_avoided: "الخسائر المتجنبة (دولار)",
    confidence: "درجة الثقة",
    time_to_act: "الوقت المتاح للتصرف",
    urgency_critical: "حرج",
    urgency_high: "عالي",
    urgency_medium: "متوسط",
    urgency_low: "منخفض",
  },
};

// ── Risk Badge ───────────────────────────────────────────────────────

function RiskBadge({ index }: { index: number | undefined }) {
  const value = index ?? 0;
  let bgColor = "bg-io-nominal";
  let textColor = "text-white";

  if (value >= 0.8) {
    bgColor = "bg-io-critical";
  } else if (value >= 0.65) {
    bgColor = "bg-io-elevated";
  } else if (value >= 0.5) {
    bgColor = "bg-io-warning";
  } else if (value >= 0.35) {
    bgColor = "bg-io-moderate";
  }

  return (
    <div className={`inline-flex items-center px-3 py-1.5 rounded-lg ${bgColor} ${textColor} font-semibold text-sm`}>
      {safePercent(value)}
    </div>
  );
}

// ── Intelligence Brief Tab ───────────────────────────────────────────

function IntelligenceBriefTab({
  locale,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  narrative,
  systemRiskIndex,
  macroSignals,
  causalChain,
}: {
  locale: Language;
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  severity?: number;
  narrative?: string;
  systemRiskIndex?: number;
  macroSignals?: MacroSignal[];
  causalChain?: CausalStep[];
}) {
  const t = labels[locale];
  const isRTL = locale === "ar";
  const scenario = locale === "ar" ? scenarioLabelAr : scenarioLabel;

  return (
    <div className={`space-y-6 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Scenario Context */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-3">{t.scenario_context}</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-io-secondary">{t.scenario_context}:</span>
            <span className="font-semibold text-io-primary">{scenario || t.no_data}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-io-secondary">{t.severity}:</span>
            <RiskBadge index={severity} />
          </div>
        </div>
      </div>

      {/* Narrative */}
      {narrative && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-3">{t.narrative_summary}</h3>
          <p className="text-sm leading-relaxed text-io-primary">{narrative}</p>
        </div>
      )}

      {/* System Risk Index */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-3">{t.system_risk_index}</h3>
        <div className="flex items-end gap-4">
          <div>
            <p className="text-xs text-io-secondary mb-1">URS (Unified Risk Severity)</p>
            <RiskBadge index={systemRiskIndex} />
          </div>
          <div className="flex-1 h-2 bg-io-bg rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                (systemRiskIndex ?? 0) >= 0.8
                  ? "bg-io-critical"
                  : (systemRiskIndex ?? 0) >= 0.65
                    ? "bg-io-elevated"
                    : (systemRiskIndex ?? 0) >= 0.5
                      ? "bg-io-warning"
                      : "bg-io-moderate"
              }`}
              style={{ width: `${Math.min((systemRiskIndex ?? 0) * 100, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Macro Signals */}
      {macroSignals && macroSignals.length > 0 && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.top_signals}</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-io-border text-io-secondary">
                  <th className="text-left py-2 font-medium">{t.signal_name}</th>
                  <th className="text-right py-2 font-medium">{t.signal_value}</th>
                  <th className="text-right py-2 font-medium">{t.signal_impact}</th>
                </tr>
              </thead>
              <tbody>
                {macroSignals.map((signal) => (
                  <tr key={signal.id} className="border-b border-io-border/50">
                    <td className="py-2.5 font-medium text-io-primary">
                      {locale === "ar" ? signal.name_ar : signal.name_en}
                    </td>
                    <td className="py-2.5 text-right tabular-nums text-io-secondary">{signal.value}</td>
                    <td className="py-2.5 text-right">
                      <span
                        className={
                          signal.impact === "high"
                            ? "text-io-critical font-semibold"
                            : signal.impact === "medium"
                              ? "text-io-warning"
                              : "text-io-primary"
                        }
                      >
                        {signal.impact.charAt(0).toUpperCase() + signal.impact.slice(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Causal Chain */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider mb-4">{t.causal_chain}</h3>
          <div className="space-y-3">
            {causalChain.map((step, idx) => (
              <div key={idx} className="flex gap-4 border-l-2 border-io-accent pl-4 py-2">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-io-accent text-white text-xs font-bold">
                    {step.step}
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-io-primary">{step.entity_label}</p>
                  <p className="text-sm text-io-secondary mt-0.5">{step.event}</p>
                  <p className="text-xs text-io-accent font-semibold mt-1">{formatUSD(step.impact_usd)} impact</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Executive Directive Tab ──────────────────────────────────────────

function ExecutiveDirectiveTab({
  locale,
  decisionActions,
}: {
  locale: Language;
  decisionActions?: DecisionAction[];
}) {
  const t = labels[locale];
  const isRTL = locale === "ar";

  if (!decisionActions || decisionActions.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
        <p className="text-io-secondary">{t.no_data}</p>
      </div>
    );
  }

  // Sort by priority and take top 3
  const topActions = [...decisionActions].sort((a, b) => a.priority - b.priority).slice(0, 3);

  return (
    <div className={`space-y-4 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      <h3 className="text-sm font-semibold text-io-primary uppercase tracking-wider">{t.top_decisions}</h3>
      {topActions.map((action) => {
        const urgency =
          action.time_to_act_hours < 6
            ? "critical"
            : action.time_to_act_hours < 24
              ? "high"
              : action.time_to_act_hours < 72
                ? "medium"
                : "low";
        const urgencyColor =
          urgency === "critical"
            ? "bg-io-critical"
            : urgency === "high"
              ? "bg-io-elevated"
              : urgency === "medium"
                ? "bg-io-warning"
                : "bg-io-moderate";

        return (
          <div key={action.id} className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
            {/* Header with urgency */}
            <div className="flex items-start justify-between gap-3 mb-3">
              <h4 className="font-semibold text-io-primary flex-1">
                {locale === "ar" && action.action_ar ? action.action_ar : action.action}
              </h4>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${urgencyColor} text-white whitespace-nowrap`}>
                {t[`urgency_${urgency}` as keyof typeof t] || urgency}
              </span>
            </div>

            {/* Metadata grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3 pb-3 border-b border-io-border/50">
              <div>
                <p className="text-xs text-io-secondary font-medium mb-0.5">{t.sector_alignment}</p>
                <p className="text-sm font-semibold text-io-accent">{action.sector}</p>
              </div>
              <div>
                <p className="text-xs text-io-secondary font-medium mb-0.5">{t.owner}</p>
                <p className="text-sm font-semibold text-io-primary">{action.owner}</p>
              </div>
              <div>
                <p className="text-xs text-io-secondary font-medium mb-0.5">{t.priority}</p>
                <p className="text-sm font-semibold text-io-primary"># {action.priority}</p>
              </div>
            </div>

            {/* Financials */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div>
                <p className="text-xs text-io-secondary font-medium mb-0.5">{t.cost}</p>
                <p className="text-sm font-semibold tabular-nums text-io-primary">{formatUSD(action.cost_usd)}</p>
              </div>
              <div>
                <p className="text-xs text-io-secondary font-medium mb-0.5">{t.loss_avoided}</p>
                <p className="text-sm font-semibold tabular-nums text-io-success">{formatUSD(action.loss_avoided_usd)}</p>
              </div>
              <div>
                <p className="text-xs text-io-secondary font-medium mb-0.5">{t.confidence}</p>
                <p className="text-sm font-semibold tabular-nums text-io-primary">{safePercent(action.confidence)}</p>
              </div>
            </div>

            {/* Time to act */}
            <div className="mt-3 pt-3 border-t border-io-border/50">
              <p className="text-xs text-io-secondary font-medium mb-1">{t.time_to_act}</p>
              <p className="text-sm font-semibold text-io-primary">{formatHours(action.time_to_act_hours)}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────

export function SectorIntelligenceView(props: SectorIntelligenceViewProps) {
  const [activeTab, setActiveTab] = useState<"brief" | "banking" | "insurance" | "fintech" | "directive">("brief");
  const t = labels[props.locale];
  const isRTL = props.locale === "ar";

  const tabs = [
    { id: "brief", label: t.intelligence_brief },
    { id: "banking", label: t.banking_stress },
    { id: "insurance", label: t.insurance_stress },
    { id: "fintech", label: t.fintech_stress },
    { id: "directive", label: t.executive_directive },
  ] as const;

  return (
    <div className={`space-y-4 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>

      {/* ── Sector Intelligence Interpretation Context ── */}
      <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-io-accent/10 flex items-center justify-center mt-0.5">
            <span className="text-xs font-bold text-io-accent">§</span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-bold text-io-primary mb-1">
              {isRTL ? "استخبارات القطاعات" : "Sector Intelligence"}
            </h2>
            <p className="text-xs text-io-secondary leading-relaxed">
              {isRTL
                ? "يوضح هذا القسم كيفية انتقال الضغط الناجم عن الصدمة عبر القطاعات المالية الرئيسية. تعكس مؤشرات الضغط البنكي والتأميني تراكم المخاطر المالية قبل أن تتحول إلى خسائر فعلية. كل قطاع يحمل رافعة قرار محددة."
                : "This section shows how shock-driven stress propagates across key financial sectors. Banking and insurance stress indicators reflect the build-up of financial risk before it materialises into losses. Each sector carries a specific decision lever."}
            </p>
            {props.systemRiskIndex != null && (
              <div className="mt-3 flex items-center gap-3">
                <span className="text-[10px] text-io-secondary uppercase tracking-wider">
                  {isRTL ? "مؤشر مخاطر النظام" : "System Risk Index"}
                </span>
                <div className="flex-1 max-w-[120px] h-1.5 bg-io-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-io-status-elevated transition-all"
                    style={{ width: `${Math.min(props.systemRiskIndex * 100, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-io-status-elevated tabular-nums">
                  {Math.round(props.systemRiskIndex * 100)}%
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="bg-io-surface border border-io-border rounded-xl p-1 shadow-sm flex flex-wrap gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 min-w-max px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === tab.id
                ? "bg-io-accent text-white shadow-md"
                : "text-io-secondary hover:text-io-primary hover:bg-io-bg"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-io-bg rounded-xl p-6 shadow-sm">
        {activeTab === "brief" && (
          <IntelligenceBriefTab
            locale={props.locale}
            scenarioLabel={props.scenarioLabel}
            scenarioLabelAr={props.scenarioLabelAr}
            severity={props.severity}
            narrative={props.locale === "ar" ? props.narrativeAr : props.narrativeEn}
            systemRiskIndex={props.systemRiskIndex}
            macroSignals={props.macroSignals}
            causalChain={props.causalChain}
          />
        )}

        {activeTab === "banking" && (
          <div className="space-y-5">
            {/* Banking interpretation block */}
            <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-orange-700 mb-2">
                {isRTL ? "ما الذي يحدث" : "What is happening"}
              </p>
              <p className="text-sm text-orange-900 leading-relaxed mb-3">
                {isRTL
                  ? "يتعرض القطاع المصرفي لضغط على السيولة ناجم عن انكشاف تمويل التجارة وتصاعد نفقات التشغيل. ارتفاع معدلات الإقراض بين البنوك يعكس شُح التمويل قصير الأجل."
                  : "The banking sector faces liquidity pressure from trade finance exposure and rising funding costs. Elevated interbank lending rates reflect short-term funding scarcity."}
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="font-semibold text-orange-800 mb-0.5">
                    {isRTL ? "لماذا يهم" : "Why it matters"}
                  </p>
                  <p className="text-orange-700">
                    {isRTL
                      ? "ضغط السيولة المصرفية ينتقل إلى الاقتصاد الحقيقي عبر تشديد الائتمان وتجميد خطوط التمويل."
                      : "Banking liquidity stress transmits to the real economy through credit tightening and frozen financing lines."}
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-orange-800 mb-0.5">
                    {isRTL ? "رافعة القرار" : "Decision lever"}
                  </p>
                  <p className="text-orange-700">
                    {isRTL
                      ? "نافذة السيولة الطارئة للبنك المركزي تُوقف التوتر بين البنوك خلال 4–6 ساعات."
                      : "Central bank emergency liquidity window arrests interbank stress within 4–6 hours."}
                  </p>
                </div>
              </div>
            </div>
            {props.bankingStress ? (
              <BankingDetailPanel data={props.bankingStress} lang={props.locale} />
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-io-secondary">{t.no_banking}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "insurance" && (
          <div className="space-y-5">
            {/* Insurance interpretation block */}
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-red-700 mb-2">
                {isRTL ? "ما الذي يحدث" : "What is happening"}
              </p>
              <p className="text-sm text-red-900 leading-relaxed mb-3">
                {isRTL
                  ? "تتصاعد المطالبات البحرية وتدعيات البضائع بشكل حاد، في حين تقترب طاقة إعادة التأمين من حدود العقود. يُفضي تفعيل أقساط مخاطر الحرب إلى ثغرات في التغطية التأمينية."
                  : "Marine hull and cargo claims are surging while reinsurance treaty capacity approaches its limits. War-risk premium activation is creating coverage gaps across GCC maritime policies."}
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="font-semibold text-red-800 mb-0.5">
                    {isRTL ? "لماذا يهم" : "Why it matters"}
                  </p>
                  <p className="text-red-700">
                    {isRTL
                      ? "ثغرات التغطية تُبطئ الإفراج عن البضائع وتُضاعف الخسائر في سلسلة الإمداد بمرور الوقت."
                      : "Coverage gaps slow cargo release and compound supply chain losses over time."}
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-red-800 mb-0.5">
                    {isRTL ? "رافعة القرار" : "Decision lever"}
                  </p>
                  <p className="text-red-700">
                    {isRTL
                      ? "ضمان إعادة التأمين الحكومي يُثبّت الطاقة ويمنع مزيداً من ارتفاع الأقساط."
                      : "Government-backed reinsurance backstop stabilises capacity and prevents further premium escalation."}
                  </p>
                </div>
              </div>
            </div>
            {props.insuranceStress ? (
              <InsuranceDetailPanel data={props.insuranceStress} lang={props.locale} />
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-io-secondary">{t.no_insurance}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "fintech" && (
          <>
            {props.fintechStress ? (
              <FintechDetailPanel data={props.fintechStress} lang={props.locale} />
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-io-secondary">{t.no_fintech}</p>
              </div>
            )}
          </>
        )}

        {activeTab === "directive" && <ExecutiveDirectiveTab locale={props.locale} decisionActions={props.decisionActions} />}
      </div>
    </div>
  );
}
