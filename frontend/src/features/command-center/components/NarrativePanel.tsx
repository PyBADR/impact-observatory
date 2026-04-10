"use client";

/**
 * Executive Narrative Panel — transforms raw simulation data into
 * structured intelligence briefs.
 *
 * Pipeline: Signal → Propagation → Exposure → Decision → Outcome
 *
 * Five sections:
 *   1. Executive Summary — headline, what happened, why it matters
 *   2. Causal Chain Story — root cause → propagation → effects
 *   3. Sector Impact Stories — per-sector narratives with metrics
 *   4. Decision Rationale — enriched actions with ROI + consequences
 *   5. Governance & Trust — audit, certainty, methodology
 */

import React, { useState } from "react";
import {
  AlertTriangle,
  TrendingDown,
  Shield,
  Building2,
  Landmark,
  Cpu,
  Anchor,
  Zap,
  ChevronRight,
  ChevronDown,
  FileText,
  Lock,
  BarChart3,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────

export interface NarrativeData {
  executive_summary?: {
    headline_en?: string;
    headline_ar?: string;
    what_happened_en?: string;
    what_happened_ar?: string;
    why_it_matters_en?: string;
    why_it_matters_ar?: string;
    financial_exposure?: {
      total_loss_formatted?: string;
      total_loss_usd?: number;
      affected_entities?: number;
      critical_entities?: number;
    };
    urgency?: {
      level_en?: string;
      level_ar?: string;
      color?: string;
      peak_day?: number;
      risk_level?: string;
    };
    confidence?: {
      score?: number;
      percentage?: number;
      interpretation_en?: string;
      interpretation_ar?: string;
    };
  };
  causal_chain_story?: {
    root_cause?: string;
    root_cause_ar?: string;
    propagation_path?: string;
    first_order_effects?: string[];
    second_order_effects?: string[];
    tertiary_effects_count?: number;
  };
  sector_stories?: Array<{
    sector?: string;
    sector_ar?: string;
    classification?: string;
    stress_score?: number;
    why_affected?: string;
    why_affected_ar?: string;
    what_happens_next?: string;
    what_happens_next_ar?: string;
    key_metrics?: Record<string, string | number>;
  }>;
  decision_rationale?: {
    total_actions?: number;
    immediate_count?: number;
    short_term_count?: number;
    business_severity?: string;
    time_to_first_failure_hours?: number;
    summary_en?: string;
    summary_ar?: string;
    actions?: Array<{
      action?: string;
      priority?: string;
      timeline?: string;
      why_this_decision?: string;
      why_this_decision_ar?: string;
      what_it_mitigates?: string;
      if_ignored?: string;
      estimated_roi?: string;
    }>;
    five_questions?: Record<string, { description_en?: string; description_ar?: string }>;
  };
  governance?: {
    audit_trail?: {
      run_id?: string;
      model_version?: string;
      explanation_en?: string;
      explanation_ar?: string;
    };
    model_certainty?: {
      explanation_en?: string;
      explanation_ar?: string;
    };
    uncertainty?: {
      explanation_en?: string;
      explanation_ar?: string;
    };
    sensitivity_summary?: {
      explanation_en?: string;
      explanation_ar?: string;
    };
  };
  narrative_available?: boolean;
}

interface NarrativePanelProps {
  narrative: NarrativeData | null;
  language?: "en" | "ar";
}

// ── Sector icon helper ────────────────────────────────────────────────

function SectorIcon({ sector }: { sector: string }) {
  const s = (sector ?? "").toLowerCase();
  if (s.includes("bank")) return <Landmark size={13} className="text-blue-400" />;
  if (s.includes("insur")) return <Shield size={13} className="text-emerald-400" />;
  if (s.includes("fintech")) return <Cpu size={13} className="text-violet-400" />;
  if (s.includes("energy")) return <Zap size={13} className="text-amber-400" />;
  if (s.includes("marit")) return <Anchor size={13} className="text-cyan-400" />;
  return <Building2 size={13} className="text-slate-400" />;
}

// ── Urgency badge ──────────────────────────────────────────────────────

function UrgencyBadge({ urgency }: { urgency?: { level_en?: string; level_ar?: string; color?: string; risk_level?: string; peak_day?: number } }) {
  if (!urgency) return null;
  const colorMap: Record<string, string> = {
    "#DC2626": "bg-red-500/15 text-red-400 border-red-500/30",
    "#F97316": "bg-orange-500/15 text-orange-400 border-orange-500/30",
    "#EAB308": "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
    "#3B82F6": "bg-blue-500/15 text-blue-400 border-blue-500/30",
    "#10B981": "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  };
  const cls = colorMap[urgency.color ?? ""] ?? "bg-slate-500/15 text-slate-400 border-slate-500/30";

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full border ${cls}`}>
      <AlertTriangle size={10} />
      {urgency.risk_level ?? urgency.level_en ?? "UNKNOWN"}
    </span>
  );
}

// ── Stress bar ─────────────────────────────────────────────────────────

function StressBar({ score, classification }: { score: number; classification?: string }) {
  const pct = Math.round(Math.min(1, Math.max(0, score)) * 100);
  const color =
    pct >= 80 ? "bg-red-500" :
    pct >= 65 ? "bg-orange-500" :
    pct >= 50 ? "bg-yellow-500" :
    pct >= 35 ? "bg-blue-500" :
    "bg-emerald-500";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-slate-500 font-mono w-8 text-right">{pct}%</span>
      {classification && (
        <span className="text-[9px] text-slate-600 uppercase tracking-wider">{classification}</span>
      )}
    </div>
  );
}

// ── Collapsible section ────────────────────────────────────────────────

function Section({
  title,
  icon,
  children,
  defaultOpen = true,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-white/[0.04] last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-left hover:bg-white/[0.02] transition-colors"
      >
        {icon}
        <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex-1">{title}</span>
        {open ? <ChevronDown size={12} className="text-slate-600" /> : <ChevronRight size={12} className="text-slate-600" />}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────

export function NarrativePanel({ narrative, language = "en" }: NarrativePanelProps) {
  if (!narrative || narrative.narrative_available === false) {
    return (
      <div className="flex items-center justify-center h-full text-slate-600 text-xs">
        Narrative layer not available for this run.
      </div>
    );
  }

  const isAr = language === "ar";
  const dir = isAr ? "rtl" : "ltr";
  const es = narrative.executive_summary;
  const cs = narrative.causal_chain_story;
  const sectors = narrative.sector_stories ?? [];
  const decisionRationale = narrative.decision_rationale;
  const decisions = decisionRationale?.actions ?? [];
  const gov = narrative.governance;

  return (
    <div className="h-full overflow-y-auto" dir={dir}>
      {/* ── Executive Summary ─────────────────────────────────────── */}
      <Section title={isAr ? "الملخص التنفيذي" : "Executive Summary"} icon={<FileText size={13} className="text-blue-400" />}>
        {es && (
          <div className="space-y-3">
            {/* Headline + Urgency */}
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-sm font-semibold text-white leading-snug flex-1">
                {isAr ? es.headline_ar : es.headline_en}
              </h3>
              <UrgencyBadge urgency={es.urgency} />
            </div>

            {/* What happened */}
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                {isAr ? "ماذا حدث" : "What Happened"}
              </p>
              <p className="text-xs text-slate-300 leading-relaxed">
                {isAr ? es.what_happened_ar : es.what_happened_en}
              </p>
            </div>

            {/* Why it matters */}
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                {isAr ? "لماذا يهم" : "Why It Matters"}
              </p>
              <p className="text-xs text-slate-300 leading-relaxed">
                {isAr ? es.why_it_matters_ar : es.why_it_matters_en}
              </p>
            </div>

            {/* Financial exposure + confidence */}
            <div className="flex items-center gap-4 pt-1">
              {es.financial_exposure && (
                <div className="flex items-center gap-1.5">
                  <TrendingDown size={11} className="text-red-400" />
                  <span className="text-xs font-mono text-red-400">{es.financial_exposure.total_loss_formatted}</span>
                </div>
              )}
              {es.confidence && (
                <div className="flex items-center gap-1.5 text-slate-500">
                  <span className="text-[10px]">Confidence:</span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {es.confidence.percentage ?? Math.round((es.confidence.score ?? 0) * 100)}%
                  </span>
                  <span className="text-[10px] text-slate-600">
                    ({isAr ? es.confidence.interpretation_ar : es.confidence.interpretation_en})
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </Section>

      {/* ── Causal Chain Story ────────────────────────────────────── */}
      <Section title={isAr ? "سلسلة السببية" : "Causal Chain"} icon={<TrendingDown size={13} className="text-orange-400" />}>
        {cs && (
          <div className="space-y-3">
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Root Cause</p>
              <p className="text-xs text-slate-300 leading-relaxed">
                {isAr ? cs.root_cause_ar : cs.root_cause}
              </p>
            </div>

            {cs.propagation_path && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Propagation Path</p>
                <div className="bg-white/[0.03] rounded-lg px-3 py-2 overflow-x-auto">
                  <p className="text-[10px] font-mono text-blue-400 whitespace-nowrap">
                    {cs.propagation_path}
                  </p>
                </div>
              </div>
            )}

            {(cs.first_order_effects?.length ?? 0) > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">First-Order Effects</p>
                <div className="space-y-1">
                  {cs.first_order_effects?.map((e, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="w-1 h-1 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                      <span className="text-xs text-slate-300">{e}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(cs.second_order_effects?.length ?? 0) > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Second-Order Effects</p>
                <div className="space-y-1">
                  {cs.second_order_effects?.map((e, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="w-1 h-1 rounded-full bg-orange-400 mt-1.5 flex-shrink-0" />
                      <span className="text-xs text-slate-400">{e}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(cs.tertiary_effects_count ?? 0) > 0 && (
              <p className="text-[10px] text-slate-600">
                + {cs.tertiary_effects_count} tertiary cascading effects
              </p>
            )}
          </div>
        )}
      </Section>

      {/* ── Sector Impact Stories ─────────────────────────────────── */}
      <Section title={isAr ? "تأثير القطاعات" : "Sector Impact"} icon={<BarChart3 size={13} className="text-emerald-400" />} defaultOpen={false}>
        <div className="space-y-3">
          {sectors.map((s, i) => (
            <div key={i} className="bg-white/[0.02] rounded-lg p-3 border border-white/[0.04]">
              <div className="flex items-center gap-2 mb-2">
                <SectorIcon sector={s.sector ?? ""} />
                <span className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
                  {isAr ? s.sector_ar : s.sector}
                </span>
                {s.classification && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.05] text-slate-500 uppercase">
                    {s.classification}
                  </span>
                )}
              </div>

              <StressBar score={s.stress_score ?? 0} />

              <div className="mt-2 space-y-1.5">
                <div>
                  <p className="text-[9px] text-slate-600 uppercase mb-0.5">{isAr ? "لماذا تأثر" : "Why Affected"}</p>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{isAr ? s.why_affected_ar : s.why_affected}</p>
                </div>
                <div>
                  <p className="text-[9px] text-slate-600 uppercase mb-0.5">{isAr ? "ماذا بعد" : "What Happens Next"}</p>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{isAr ? s.what_happens_next_ar : s.what_happens_next}</p>
                </div>
              </div>

              {/* Key metrics */}
              {s.key_metrics && Object.keys(s.key_metrics).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(s.key_metrics).map(([k, v]) => (
                    <div key={k} className="bg-white/[0.03] rounded px-2 py-1">
                      <p className="text-[8px] text-slate-600 uppercase">{k.replace(/_/g, " ")}</p>
                      <p className="text-[10px] font-mono text-slate-300">{String(v)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* ── Decision Rationale ────────────────────────────────────── */}
      <Section title={isAr ? "مبررات القرار" : "Decision Rationale"} icon={<Shield size={13} className="text-violet-400" />} defaultOpen={false}>
        <div className="space-y-2">
          {/* Decision overview strip */}
          {decisionRationale && (
            <div className="flex items-center gap-4 mb-2 px-2 py-1.5 bg-white/[0.02] rounded-lg">
              {decisionRationale.business_severity && (
                <div className="text-[10px]">
                  <span className="text-slate-600">Severity: </span>
                  <span className="text-slate-300 font-semibold">{decisionRationale.business_severity}</span>
                </div>
              )}
              {decisionRationale.time_to_first_failure_hours != null && (
                <div className="text-[10px]">
                  <span className="text-slate-600">Time to failure: </span>
                  <span className="text-red-400 font-mono">{decisionRationale.time_to_first_failure_hours.toFixed(1)}h</span>
                </div>
              )}
              <div className="text-[10px]">
                <span className="text-slate-600">Actions: </span>
                <span className="text-slate-300">{decisionRationale.total_actions ?? decisions.length}</span>
              </div>
            </div>
          )}
          {decisions.map((d, i) => (
            <div key={i} className="bg-white/[0.02] rounded-lg p-3 border border-white/[0.04]">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-200">{d.action}</span>
                <div className="flex items-center gap-2">
                  {d.priority && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.05] text-slate-500 uppercase">
                      {d.priority}
                    </span>
                  )}
                  {d.timeline && (
                    <span className="text-[9px] text-slate-600">{d.timeline}</span>
                  )}
                </div>
              </div>

              {d.why_this_decision && (
                <p className="text-[10px] text-slate-400 mb-1">
                  <span className="text-slate-600">Why: </span>
                  {isAr ? d.why_this_decision_ar : d.why_this_decision}
                </p>
              )}
              {d.what_it_mitigates && (
                <p className="text-[10px] text-slate-400 mb-1">
                  <span className="text-slate-600">Mitigates: </span>{d.what_it_mitigates}
                </p>
              )}
              {d.if_ignored && (
                <p className="text-[10px] text-red-400/80 mb-1">
                  <span className="text-red-500/60">If ignored: </span>{d.if_ignored}
                </p>
              )}
              {d.estimated_roi && (
                <p className="text-[10px] text-emerald-400/80">
                  <span className="text-emerald-500/60">Est. ROI: </span>{d.estimated_roi}
                </p>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* ── Governance & Trust ────────────────────────────────────── */}
      <Section title={isAr ? "الحوكمة والثقة" : "Governance & Trust"} icon={<Lock size={13} className="text-slate-500" />} defaultOpen={false}>
        {gov && (
          <div className="space-y-3">
            {gov.audit_trail && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Audit Trail</p>
                {gov.audit_trail.run_id && (
                  <p className="text-[10px] text-slate-600 font-mono mb-1">Run: {gov.audit_trail.run_id} · v{gov.audit_trail.model_version}</p>
                )}
                <p className="text-xs text-slate-400 leading-relaxed">
                  {isAr ? gov.audit_trail.explanation_ar : gov.audit_trail.explanation_en}
                </p>
              </div>
            )}
            {gov.model_certainty && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Model Certainty</p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {isAr ? gov.model_certainty.explanation_ar : gov.model_certainty.explanation_en}
                </p>
              </div>
            )}
            {gov.uncertainty && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Uncertainty Bands</p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {isAr ? gov.uncertainty.explanation_ar : gov.uncertainty.explanation_en}
                </p>
              </div>
            )}
            {gov.sensitivity_summary && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Sensitivity Analysis</p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {isAr ? gov.sensitivity_summary.explanation_ar : gov.sensitivity_summary.explanation_en}
                </p>
              </div>
            )}
          </div>
        )}
      </Section>
    </div>
  );
}
