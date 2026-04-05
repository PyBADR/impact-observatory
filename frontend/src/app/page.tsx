"use client";

/**
 * Impact Observatory | مرصد الأثر
 *
 * UNIFIED FLOW ARCHITECTURE
 * Single product experience: Landing → Scenario → Analysis → Persona View
 *
 * All personas (Executive / Analyst / Regulator) see the same intelligence
 * pipeline through different lenses. No disconnected dashboards.
 *
 * Institutional boardroom aesthetic. Financial-first. Arabic + English.
 */

import React, { useState, useEffect } from "react";
import BankingDetailPanel from "@/features/banking/BankingDetailPanel";
import InsuranceDetailPanel from "@/features/insurance/InsuranceDetailPanel";
import FintechDetailPanel from "@/features/fintech/FintechDetailPanel";
import DecisionDetailPanel from "@/features/decisions/DecisionDetailPanel";
import { SignalFeed } from "@/features/signal-feed/SignalFeed";
import { PendingSeedPanel } from "@/features/signal-feed/PendingSeedPanel";
import { OperatorDecisionPanel } from "@/features/decisions/OperatorDecisionPanel";
import { PersonaFlowView } from "@/features/flow/PersonaFlowView";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { useRunState } from "@/lib/run-state";
import { useAppStore } from "@/store/app-store";
import { useFlowStore } from "@/store/flow-store";
import { useOutcomes, useDecisionValues } from "@/hooks/use-api";
import type { RunResult, Language } from "@/types/observatory";
import type { Persona } from "@/lib/persona-view-model";
import { DomainBadge } from "@/components/ui";

import {
  scenarioPresentationMap,
  catalogScenarioIds,
} from "@/lib/dashboard-mapping";

type AppView = "landing" | "scenarios" | "results";
type DetailView = "dashboard" | "banking" | "insurance" | "fintech" | "decisions";

// ── Scenario catalog ───────────────────────────────────────────────────

const SCENARIOS = catalogScenarioIds.map((id) => {
  const p = scenarioPresentationMap[id];
  return {
    id: p.scenarioId,
    label: p.titleEn,
    label_ar: p.titleAr,
    desc: p.subtitleEn,
    desc_ar: p.subtitleAr,
    loss: p.headlineLossLabel,
    severity: parseFloat(p.severityLabel) / 100,
    domain: p.domain,
    triggerType: p.triggerType,
    sectors: p.affectedSectors,
  };
});

// ── Decision modules (landing page, no emoji) ──────────────────────────

const DECISION_MODULES = {
  en: [
    {
      code: "FIM",
      title: "Financial Impact Modeling",
      desc: "GDP-weighted loss propagation across 31 GCC entities with sector-specific elasticities and Basel III–aligned stress coefficients.",
      domain: "Banking · Insurance · Fintech",
    },
    {
      code: "BSA",
      title: "Banking Stress Analysis",
      desc: "Liquidity, credit, and FX stress across 6 major GCC banking institutions. Interbank contagion modeling with capital buffer drawdown analysis.",
      domain: "Banking",
    },
    {
      code: "ISA",
      title: "Insurance Stress Analysis",
      desc: "Claims surge modeling across 8 insurance lines. Underwriting status assessment, combined ratio stress, and reinsurance trigger analysis under tail-risk scenarios.",
      domain: "Insurance",
    },
    {
      code: "FDM",
      title: "Fintech Disruption Monitoring",
      desc: "Settlement delay, API availability, and cross-border payment flow disruption across 7 GCC payment platforms. Real-time impact scoring for digital financial infrastructure.",
      domain: "Fintech",
    },
    {
      code: "DIE",
      title: "Decision Intelligence Engine",
      desc: "Priority-ranked response actions scored by mitigation value, urgency, and regulatory risk. Cost–benefit analysis with owner assignment and time-to-act windows.",
      domain: "Cross-sector",
    },
    {
      code: "BSE",
      title: "Bilingual Scenario Explainability",
      desc: "Full causal chain from trigger event to financial outcome in Arabic and English. SHA-256 audit hash, immutable event log, and regulator-ready reporting.",
      domain: "Regulatory · Governance",
    },
  ],
  ar: [
    {
      code: "FIM",
      title: "نمذجة الأثر المالي",
      desc: "انتشار الخسائر المرجحة بالناتج المحلي عبر 31 كياناً خليجياً مع مرونات قطاعية وفق بازل III.",
      domain: "البنوك · التأمين · الفنتك",
    },
    {
      code: "BSA",
      title: "تحليل ضغط البنوك",
      desc: "ضغط السيولة والائتمان والعملة عبر 6 مؤسسات بنكية خليجية، مع نمذجة العدوى المصرفية واستنزاف احتياطيات رأس المال.",
      domain: "البنوك",
    },
    {
      code: "ISA",
      title: "تحليل ضغط التأمين",
      desc: "نمذجة ارتفاع المطالبات عبر 8 خطوط تأمين، وتقييم حالة الاكتتاب، والنسبة المجمعة، وتحليل تفعيل إعادة التأمين.",
      domain: "التأمين",
    },
    {
      code: "FDM",
      title: "رصد تعطل الفنتك",
      desc: "أثر تأخر التسوية وتوفر الواجهة والتدفقات العابرة للحدود عبر 7 منصات دفع خليجية مع تقييم فوري للأثر.",
      domain: "الفنتك",
    },
    {
      code: "DIE",
      title: "محرك ذكاء القرار",
      desc: "إجراءات استجابة مُصنّفة حسب قيمة التخفيف والإلحاح والمخاطر التنظيمية مع تحليل التكلفة والعائد ونوافذ وقت التنفيذ.",
      domain: "متعدد القطاعات",
    },
    {
      code: "BSE",
      title: "قابلية التفسير ثنائية اللغة",
      desc: "سلسلة سببية كاملة من الحدث المُحفّز إلى النتيجة المالية بالعربية والإنجليزية، مع بصمة تدقيق SHA-256 وتقارير جاهزة للجهات الرقابية.",
      domain: "رقابي · حوكمة",
    },
  ],
};

// ── Trigger type display ───────────────────────────────────────────────

const TRIGGER_LABELS: Record<string, { en: string; ar: string }> = {
  geopolitical: { en: "Geopolitical", ar: "جيوسياسي" },
  market: { en: "Market", ar: "سوقي" },
  infrastructure: { en: "Infrastructure", ar: "بنية تحتية" },
  systemic: { en: "Systemic", ar: "منظومي" },
  regulatory: { en: "Regulatory", ar: "تنظيمي" },
  cyber: { en: "Cyber", ar: "سيبراني" },
};

// ── Unified nav ────────────────────────────────────────────────────────

function TopNav({
  isAr,
  lang,
  setLang,
  persona,
  setPersona,
  onLogoClick,
  onRunScenario,
  showRunButton,
}: {
  isAr: boolean;
  lang: Language;
  setLang: (l: Language) => void;
  persona: Persona;
  setPersona: (p: Persona) => void;
  onLogoClick: () => void;
  onRunScenario: () => void;
  showRunButton: boolean;
}) {
  const PERSONA_LABELS: Record<Persona, { en: string; ar: string }> = {
    executive: { en: "Executive", ar: "تنفيذي" },
    analyst: { en: "Analyst", ar: "محلل" },
    regulator: { en: "Regulator", ar: "رقابي" },
  };

  return (
    <nav className="h-14 bg-io-surface border-b border-io-border px-6 lg:px-10 flex items-center justify-between sticky top-0 z-50 gap-4">
      {/* Left: Wordmark */}
      <button
        onClick={onLogoClick}
        className="flex items-center gap-2.5 flex-shrink-0 group"
      >
        <div className="w-7 h-7 bg-io-primary rounded flex items-center justify-center">
          <span className="text-white text-[10px] font-bold tracking-tight">IO</span>
        </div>
        <span className="text-sm font-semibold text-io-primary group-hover:text-io-accent transition-colors tracking-tight hidden sm:inline">
          {isAr ? "مرصد الأثر" : "Impact Observatory"}
        </span>
        <span className="hidden md:inline text-[10px] font-medium text-io-secondary bg-io-bg border border-io-border px-1.5 py-0.5 rounded">
          v4.0
        </span>
      </button>

      {/* Center: Cross-links */}
      <div className="hidden md:flex items-center gap-0.5">
        <a
          href="/graph-explorer"
          className="px-3 py-2 text-xs font-medium rounded-lg text-io-secondary hover:text-io-primary hover:bg-io-bg transition-colors"
        >
          {isAr ? "الانتشار" : "Propagation"}
        </a>
        <a
          href="/map"
          className="px-3 py-2 text-xs font-medium rounded-lg text-io-secondary hover:text-io-primary hover:bg-io-bg transition-colors"
        >
          {isAr ? "خريطة الأثر" : "Impact Map"}
        </a>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Persona switcher */}
        <div className="hidden lg:flex items-center bg-io-bg rounded-lg p-0.5 border border-io-border gap-0.5">
          {(["executive", "analyst", "regulator"] as Persona[]).map((p) => (
            <button
              key={p}
              onClick={() => setPersona(p)}
              className={`px-2.5 py-1.5 text-[11px] font-medium rounded-md capitalize transition-colors ${
                persona === p
                  ? "bg-io-surface text-io-primary shadow-sm border border-io-border"
                  : "text-io-secondary hover:text-io-primary"
              }`}
              title={
                p === "executive"
                  ? "KPIs, sector status, top decisions"
                  : p === "analyst"
                  ? "Deep mechanics, causal chain, signal detail"
                  : "Audit view: decision lineage, pipeline accountability"
              }
            >
              {isAr ? PERSONA_LABELS[p].ar : PERSONA_LABELS[p].en}
            </button>
          ))}
        </div>

        {/* Language toggle */}
        <button
          onClick={() => setLang(isAr ? "en" : "ar")}
          className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary transition-colors"
        >
          {isAr ? "EN" : "عر"}
        </button>

        {/* Run scenario CTA */}
        {showRunButton && (
          <button
            onClick={onRunScenario}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
          >
            {isAr ? "تشغيل سيناريو" : "Run Scenario"}
          </button>
        )}
      </div>
    </nav>
  );
}

// ── Main Component ─────────────────────────────────────────────────────

export default function HomePage() {
  const [appView, setAppView] = useState<AppView>("landing");
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<Language>("en");
  const [detailView, setDetailView] = useState<DetailView>("dashboard");

  const persona = useAppStore((s) => s.persona);
  const setPersona = useAppStore((s) => s.setPersona);

  useOutcomes();
  useDecisionValues();

  const sharedResult = useRunState((s) => s.getRunResult());
  const sharedSource = useRunState((s) => s.activeSource);

  useEffect(() => {
    if (sharedResult && sharedSource === "unified" && !result) {
      setResult(sharedResult);
      setAppView("results");
    }
  }, [sharedResult, sharedSource]);

  const isAr = lang === "ar";

  const startFlow = useFlowStore((s) => s.startFlow);
  const advanceStage = useFlowStore((s) => s.advanceStage);
  const attachRunResult = useFlowStore((s) => s.attachRunResult);
  const completeFlow = useFlowStore((s) => s.completeFlow);
  const failCurrentStage = useFlowStore((s) => s.failCurrentStage);
  const attachDecisions = useFlowStore((s) => s.attachDecisions);
  const attachOutcomes = useFlowStore((s) => s.attachOutcomes);
  const attachValues = useFlowStore((s) => s.attachValues);

  const operatorDecisions = useAppStore((s) => s.operatorDecisions);
  const storeOutcomes = useAppStore((s) => s.outcomes);
  const storeValues = useAppStore((s) => s.decisionValues);
  const activeFlow = useFlowStore((s) => s.activeFlow);

  useEffect(() => {
    if (activeFlow?.isActive && operatorDecisions.length > 0) {
      attachDecisions(operatorDecisions);
    }
  }, [activeFlow?.flowId, operatorDecisions.length]);

  useEffect(() => {
    if (activeFlow?.isActive && storeOutcomes.length > 0) {
      attachOutcomes(storeOutcomes);
      if (activeFlow.currentStage === "decision") {
        advanceStage("outcome", { outcomeCount: storeOutcomes.length });
      }
    }
  }, [activeFlow?.flowId, storeOutcomes.length]);

  useEffect(() => {
    if (activeFlow?.isActive && storeValues.length > 0) {
      attachValues(storeValues);
      if (activeFlow.currentStage === "outcome") {
        advanceStage("roi", { valueCount: storeValues.length });
      }
    }
  }, [activeFlow?.flowId, storeValues.length]);

  const runScenario = async (templateId: string, severity: number) => {
    setLoading(true);
    setError(null);
    setAppView("results");

    const scenarioPresentation = SCENARIOS.find((s) => s.id === templateId);
    const scenarioLabel = scenarioPresentation?.label ?? templateId;
    const scenarioLabelAr = scenarioPresentation?.label_ar ?? templateId;

    startFlow({ scenarioId: templateId, scenarioLabel, scenarioLabelAr, severity });

    try {
      const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";
      const headers = {
        "Content-Type": "application/json",
        "X-IO-API-Key": API_KEY,
      };

      function scenarioFetchError(status: number): string {
        if (status === 422) return "The scenario configuration could not be processed. Please select a different scenario or adjust the severity.";
        if (status === 404) return "The scenario template was not found. Please refresh and try again.";
        if (status >= 500) return "The analysis service is temporarily unavailable. Please try again in a moment.";
        return "The analysis could not be completed. Please try again.";
      }

      advanceStage("reasoning", { templateId, severity });

      // Send both template_id (new backend) and scenario_id (legacy backend)
      const runRes = await fetch(`/api/v1/runs`, {
        method: "POST",
        headers,
        body: JSON.stringify({ template_id: templateId, scenario_id: templateId, severity }),
      });
      if (!runRes.ok) throw new Error(scenarioFetchError(runRes.status));
      const runData = await runRes.json();

      // Handle both v4 envelope ({ data: { run_id } }) and legacy direct response ({ run_id })
      const runMeta: Record<string, unknown> = runData?.data ?? runData ?? {};
      const runId = (runMeta.run_id as string) ?? "";
      if (!runId) throw new Error("The analysis service did not return a run identifier. Please try again.");
      if (runMeta.status === "failed") throw new Error("The analysis pipeline encountered an error. Please try a different scenario.");

      advanceStage("simulation", { runId, status: "processing" });

      // Legacy backends return the full result from POST, so GET may just return the same.
      // Always fetch to get the canonical result shape.
      const resultRes = await fetch(`/api/v1/runs/${runId}`, { headers });
      if (!resultRes.ok) throw new Error(scenarioFetchError(resultRes.status));
      const resultJson = await resultRes.json();

      // Handle both v4 envelope ({ data: UnifiedRunResult }) and legacy ({ run_id, ... } directly)
      const unifiedResult: Record<string, unknown> = resultJson?.data ?? resultJson ?? {};
      if (!unifiedResult || !unifiedResult.run_id) throw new Error("No result data returned");

      useRunState.getState().setUnifiedResult(unifiedResult as unknown as import("@/types/observatory").UnifiedRunResult);

      const adapted = useRunState.getState().getRunResult();
      if (!adapted) throw new Error("Adapter failed to convert unified result");

      advanceStage("decision", {
        totalLoss: adapted.headline?.total_loss_usd,
        decisionCount: adapted.decisions?.actions?.length ?? 0,
      });

      attachRunResult(adapted, runId);
      completeFlow();

      setResult(adapted);
      setDetailView("dashboard");
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "Unknown error";
      failCurrentStage(errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (detailView !== "dashboard") {
      setDetailView("dashboard");
    } else if (result) {
      setResult(null);
      setAppView("scenarios");
    } else {
      setAppView("landing");
    }
  };

  const detailLabels: Record<Language, Record<DetailView, string>> = {
    en: {
      dashboard: "Overview",
      banking: "Banking",
      insurance: "Insurance",
      fintech: "Fintech",
      decisions: "Decisions",
    },
    ar: {
      dashboard: "النظرة العامة",
      banking: "البنوك",
      insurance: "التأمين",
      fintech: "الفنتك",
      decisions: "القرارات",
    },
  };

  // ── LANDING PAGE ───────────────────────────────────────────────────

  if (appView === "landing") {
    const modules = DECISION_MODULES[lang];
    return (
      <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
        <TopNav
          isAr={isAr}
          lang={lang}
          setLang={setLang}
          persona={persona}
          setPersona={setPersona}
          onLogoClick={() => setAppView("landing")}
          onRunScenario={() => setAppView("scenarios")}
          showRunButton
        />

        {/* ── Product statement ─────────────────────────────────── */}
        <section className="bg-io-surface border-b border-io-border">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-16">
            <div className="max-w-3xl">
              <p className="text-[11px] font-semibold text-io-secondary uppercase tracking-widest mb-4">
                {isAr
                  ? "منصة ذكاء القرار · الأسواق المالية الخليجية"
                  : "Decision Intelligence Platform · GCC Financial Markets"}
              </p>
              <h1 className="text-4xl font-bold text-io-primary leading-tight mb-5 tracking-tight">
                {isAr
                  ? "مرصد الأثر المالي لمؤسسات منطقة الخليج"
                  : "Financial impact intelligence\nfor GCC institutions"}
              </h1>
              <p className="text-base text-io-secondary leading-relaxed mb-8 max-w-2xl">
                {isAr
                  ? "نمذجة كمية لانتشار الصدمات عبر القطاع البنكي والتأمين والفنتك الخليجي. من الحدث إلى قرارات مُرتَّبة حسب الأولوية في وقت قياسي."
                  : "Quantitative shock propagation modeling across GCC banking, insurance, and fintech sectors. From event to prioritized decision actions in seconds."}
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => setAppView("scenarios")}
                  className="px-5 py-2.5 bg-io-accent text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {isAr ? "تشغيل سيناريو" : "Run Scenario"}
                </button>
                <a
                  href="/graph-explorer"
                  className="px-5 py-2.5 border border-io-border text-io-secondary text-sm font-medium rounded-lg hover:border-io-accent hover:text-io-accent transition-colors"
                >
                  {isAr ? "استكشاف الرسم البياني" : "Explore Knowledge Graph"}
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* ── Platform metrics strip ────────────────────────────── */}
        <section className="border-b border-io-border">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                {
                  value: "31",
                  label: isAr ? "كياناً خليجياً" : "GCC Entities",
                  sub: isAr ? "طاقة · بحري · طيران · مالي" : "Energy · Maritime · Aviation · Finance",
                },
                {
                  value: "8",
                  label: isAr ? "سيناريوهات" : "Scenario Types",
                  sub: isAr ? "جيوسياسي · سوقي · سيبراني" : "Geopolitical · Market · Cyber",
                },
                {
                  value: "$2.1T",
                  label: isAr ? "ناتج محلي مغطى" : "GDP Coverage",
                  sub: isAr ? "دول الخليج الست" : "Six GCC nations",
                },
                {
                  value: "<2s",
                  label: isAr ? "وقت التحليل" : "Analysis Latency",
                  sub: isAr ? "من الحدث إلى القرار" : "Event to ranked decisions",
                },
              ].map((m) => (
                <div key={m.label} className="py-1">
                  <p className="text-2xl font-bold text-io-primary tabular-nums">{m.value}</p>
                  <p className="text-sm font-semibold text-io-primary mt-1">{m.label}</p>
                  <p className="text-xs text-io-secondary mt-0.5">{m.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Domain coverage ───────────────────────────────────── */}
        <section className="border-b border-io-border bg-io-surface">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-10">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-6">
              {isAr ? "نطاق التغطية" : "Coverage Domains"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  sector: isAr ? "القطاع البنكي" : "Banking",
                  items: isAr
                    ? ["ضغط السيولة وفق بازل III", "مخاطر الائتمان وضغط الصرف الأجنبي", "العدوى بين البنوك", "٦ مؤسسات بنكية خليجية كبرى"]
                    : ["Basel III liquidity stress", "Credit risk & FX pressure", "Interbank contagion", "6 major GCC institutions"],
                },
                {
                  sector: isAr ? "التأمين" : "Insurance",
                  items: isAr
                    ? ["نمذجة ارتفاع المطالبات وفق IFRS-17", "النسبة المجمعة وتفعيل إعادة التأمين", "٨ خطوط تأمين", "حالة الاكتتاب والإفلاس"]
                    : ["IFRS-17 claims surge modeling", "Combined ratio & reinsurance trigger", "8 insurance lines", "Underwriting & insolvency status"],
                },
                {
                  sector: isAr ? "الفنتك والمدفوعات" : "Fintech & Payments",
                  items: isAr
                    ? ["أثر حجم المدفوعات وتأخر التسوية", "توفر API والتعطل العابر للحدود", "٧ منصات دفع خليجية", "مراقبة احتياطيات العملات الرقمية"]
                    : ["Payment volume & settlement delay", "API availability & cross-border impact", "7 GCC payment platforms", "Digital currency reserve monitoring"],
                },
              ].map((col) => (
                <div key={col.sector}>
                  <p className="text-sm font-semibold text-io-primary mb-3">{col.sector}</p>
                  <ul className="space-y-2">
                    {col.items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-xs text-io-secondary">
                        <span className="w-1 h-1 rounded-full bg-io-accent mt-1.5 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── How it works ─────────────────────────────────────── */}
        <section className="border-b border-io-border">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-12">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-8">
              {isAr ? "آلية العمل" : "Analysis Flow"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  step: "01",
                  title: isAr ? "تعريف السيناريو" : "Define Scenario",
                  desc: isAr
                    ? "اختر سيناريو من 8 أنواع: جيوسياسي، سوقي، هجوم سيبراني، اضطراب بنية تحتية. حدّد شدة الصدمة."
                    : "Select from 8 scenario types: geopolitical, market, cyber attack, infrastructure disruption. Set shock severity.",
                },
                {
                  step: "02",
                  title: isAr ? "انتشار الأثر" : "Propagate Impact",
                  desc: isAr
                    ? "يُشغّل المحرك خط أنابيب من 13 مرحلة: انتشار الصدمة عبر 31 كياناً خليجياً باستخدام الرسم البياني السببي."
                    : "The engine runs a 13-stage pipeline: shock propagation across 31 GCC entities using the causal knowledge graph.",
                },
                {
                  step: "03",
                  title: isAr ? "إجراءات القرار" : "Decision Actions",
                  desc: isAr
                    ? "أعلى 3 إجراءات مُرتّبة بمعادلة: الأولوية = القيمة + الإلحاح + المخاطر التنظيمية. مع تعيين المسؤول."
                    : "Top-ranked responses scored by: Priority = Value + Urgency + Regulatory Risk. With owner assignment.",
                },
              ].map((s) => (
                <div key={s.step}>
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl font-bold text-io-border tabular-nums">{s.step}</span>
                    <span className="h-px flex-1 bg-io-border" />
                  </div>
                  <h3 className="text-sm font-semibold text-io-primary mb-2">{s.title}</h3>
                  <p className="text-xs text-io-secondary leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Decision modules ──────────────────────────────────── */}
        <section className="bg-io-surface border-b border-io-border">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-12">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-8">
              {isAr ? "وحدات التحليل" : "Analysis Modules"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {modules.map((mod) => (
                <div
                  key={mod.code}
                  className="bg-io-bg border border-io-border rounded-xl p-5 hover:border-io-accent/30 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[10px] font-bold text-io-secondary bg-io-surface border border-io-border px-2 py-0.5 rounded font-mono">
                      {mod.code}
                    </span>
                    <span className="text-[10px] text-io-secondary">{mod.domain}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-io-primary mb-2 leading-snug">
                    {mod.title}
                  </h3>
                  <p className="text-xs text-io-secondary leading-relaxed">{mod.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Model trust statement ─────────────────────────────── */}
        <section className="border-b border-io-border">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-12">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-6">
              {isAr ? "أسس الثقة بالنموذج" : "Model Trust Basis"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  label: isAr ? "محاكاة حتمية" : "Deterministic Simulation",
                  desc: isAr
                    ? "جميع المخرجات محاكاة حتمية وليست توقعات ذكاء اصطناعي. نفس المدخلات تُنتج نفس النتائج دائماً."
                    : "All outputs are deterministic simulations, not AI predictions. Same inputs always produce the same outputs.",
                },
                {
                  label: isAr ? "التوافق التنظيمي" : "Regulatory Alignment",
                  desc: isAr
                    ? "معاملات ضغط وفق بازل III. نمذجة المطالبات وفق IFRS-17. مؤشرات متوافقة مع متطلبات البنك المركزي."
                    : "Basel III–aligned stress coefficients. IFRS-17 compliant claims modeling. Indicators consistent with central bank requirements.",
                },
                {
                  label: isAr ? "سلسلة التدقيق غير القابلة للتغيير" : "Immutable Audit Chain",
                  desc: isAr
                    ? "كل قرار يحمل تتبعاً إلى بياناته المصدرية. تجزئة SHA-256 محمية بسلسلة أحداث تدقيق."
                    : "Every decision is traceable to source data. SHA-256 hash integrity protected by an immutable audit event chain.",
                },
                {
                  label: isAr ? "قابلية التفسير الكاملة" : "Full Explainability",
                  desc: isAr
                    ? "سلسلة سببية من 20 خطوة تشرح كيف انتشر الحدث إلى النتيجة المالية. بالعربية والإنجليزية."
                    : "20-step causal chain explaining how the event propagated to financial outcome. Arabic and English narratives.",
                },
              ].map((item) => (
                <div key={item.label} className="flex gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-io-accent mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-io-primary mb-1">{item.label}</p>
                    <p className="text-xs text-io-secondary leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Operator layer ────────────────────────────────────── */}
        <section className="border-b border-io-border bg-io-surface">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 py-10">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-2">
              {isAr ? "طبقة المشغّل" : "Operator Control Layer"}
            </p>
            <p className="text-sm text-io-secondary mb-6">
              {isAr
                ? "إشارات حية · موافقات يدوية · قرارات مشغّل منظّمة"
                : "Live signals · human-in-the-loop approvals · structured operator decisions"}
            </p>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
              <ErrorBoundary section="Signal Feed">
                <SignalFeed lang={lang} />
              </ErrorBoundary>
              <ErrorBoundary section="Pending Seed Panel">
                <PendingSeedPanel lang={lang} />
              </ErrorBoundary>
            </div>
            <ErrorBoundary section="Operator Decision Panel">
              <OperatorDecisionPanel lang={lang} />
            </ErrorBoundary>
          </div>
        </section>

        {/* ── Footer ────────────────────────────────────────────── */}
        <footer className="bg-io-surface border-t border-io-border py-8">
          <div className="max-w-5xl mx-auto px-6 lg:px-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-io-primary rounded flex items-center justify-center">
                <span className="text-white text-[9px] font-bold">IO</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-io-primary leading-none">Impact Observatory</p>
                <p className="text-[10px] text-io-secondary mt-0.5">مرصد الأثر</p>
              </div>
            </div>
            <div className="flex flex-col items-start md:items-end gap-1">
              <p className="text-xs text-io-secondary">
                {isAr
                  ? "منصة ذكاء القرار للأسواق المالية الخليجية"
                  : "Decision Intelligence Platform for GCC Financial Markets"}
              </p>
              <p className="text-[10px] text-io-secondary/60">
                {isAr
                  ? "محاكاة حتمية · ليس توقعات ذكاء اصطناعي"
                  : "Deterministic simulation · Not AI predictions"}
              </p>
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // ── SCENARIO SELECTOR ─────────────────────────────────────────────

  if (appView === "scenarios" && !result && !loading) {
    return (
      <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
        <TopNav
          isAr={isAr}
          lang={lang}
          setLang={setLang}
          persona={persona}
          setPersona={setPersona}
          onLogoClick={() => { setAppView("landing"); setResult(null); }}
          onRunScenario={() => {}}
          showRunButton={false}
        />

        <div className="max-w-4xl mx-auto px-6 lg:px-10 pt-10 pb-16">
          <div className="mb-8">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-1">
              {isAr ? "اختيار السيناريو" : "Scenario Selection"}
            </p>
            <h2 className="text-2xl font-bold text-io-primary mb-2">
              {isAr ? "اختر سيناريو لتحليله" : "Select a Scenario"}
            </h2>
            <p className="text-sm text-io-secondary">
              {isAr
                ? "اختر حدثاً لتحليل الأثر المالي عبر القطاعات الخليجية"
                : "Choose an event to analyze financial impact across GCC sectors"}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SCENARIOS.map((scenario) => {
              const trigger = TRIGGER_LABELS[scenario.triggerType];
              return (
                <button
                  key={scenario.id}
                  onClick={() => runScenario(scenario.id, scenario.severity)}
                  className="bg-io-surface border border-io-border rounded-xl p-5 text-left shadow-sm hover:shadow-md hover:border-io-accent/40 transition-all group"
                >
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-3">
                    <DomainBadge domain={scenario.domain} />
                    {trigger && (
                      <span className="text-[10px] text-io-secondary font-medium">
                        {isAr ? trigger.ar : trigger.en}
                      </span>
                    )}
                  </div>

                  {/* Title */}
                  <p className="text-sm font-semibold text-io-primary group-hover:text-io-accent transition-colors leading-snug mb-1.5">
                    {isAr ? scenario.label_ar : scenario.label}
                  </p>
                  <p className="text-xs text-io-secondary leading-relaxed mb-4">
                    {isAr ? scenario.desc_ar : scenario.desc}
                  </p>

                  {/* Metrics row */}
                  <div className="flex items-center gap-4 pt-3 border-t border-io-border/60">
                    <div>
                      <p className="text-[10px] font-medium uppercase tracking-wider text-io-secondary mb-0.5">
                        {isAr ? "الخسارة المتوقعة" : "Expected Loss"}
                      </p>
                      <p className="text-sm font-bold text-io-primary tabular-nums">
                        {scenario.loss}
                      </p>
                    </div>
                    <div className="h-6 w-px bg-io-border" />
                    <div>
                      <p className="text-[10px] font-medium uppercase tracking-wider text-io-secondary mb-0.5">
                        {isAr ? "الشدة" : "Default Severity"}
                      </p>
                      <p className="text-sm font-bold text-io-primary tabular-nums">
                        {Math.round((scenario.severity ?? 0) * 100)}%
                      </p>
                    </div>
                    <div className="h-6 w-px bg-io-border" />
                    <div className="flex flex-wrap gap-1">
                      {scenario.sectors.slice(0, 2).map((s) => (
                        <span
                          key={s}
                          className="text-[10px] text-io-secondary bg-io-bg border border-io-border px-1.5 py-0.5 rounded"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-6">
            <button
              onClick={() => setAppView("landing")}
              className="text-xs font-medium text-io-secondary hover:text-io-accent transition-colors"
            >
              {isAr ? "← العودة" : "← Back"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── RESULTS VIEW ──────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      <TopNav
        isAr={isAr}
        lang={lang}
        setLang={setLang}
        persona={persona}
        setPersona={setPersona}
        onLogoClick={() => { setAppView("landing"); setResult(null); }}
        onRunScenario={() => { setResult(null); setAppView("scenarios"); }}
        showRunButton={!!result}
      />

      {/* Detail tabs */}
      {result && (
        <div className="bg-io-surface border-b border-io-border px-6 lg:px-10 flex items-center gap-0 overflow-x-auto">
          {(["dashboard", "banking", "insurance", "fintech", "decisions"] as DetailView[]).map(
            (view) => (
              <button
                key={view}
                onClick={() => setDetailView(view)}
                className={`px-4 py-3 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
                  detailView === view
                    ? "border-io-accent text-io-accent"
                    : "border-transparent text-io-secondary hover:text-io-primary hover:border-io-border"
                }`}
              >
                {detailLabels[lang][view]}
              </button>
            )
          )}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center mt-32">
          <div className="text-center max-w-sm px-6">
            <div className="w-10 h-10 border border-io-border rounded-xl flex items-center justify-center mx-auto mb-5">
              <svg
                className="w-5 h-5 animate-spin text-io-accent"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-io-primary mb-1">
              {isAr ? "جاري تحليل السيناريو" : "Analyzing scenario"}
            </p>
            <p className="text-xs text-io-secondary">
              {isAr
                ? "حساب الأثر المالي عبر ٣١ كياناً خليجياً"
                : "Computing financial impact across 31 GCC entities"}
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="max-w-lg mx-auto mt-16 px-6">
          <div className="bg-io-surface border border-red-200 rounded-xl p-6">
            <p className="text-[10px] font-semibold text-red-600 uppercase tracking-widest mb-2">
              {isAr ? "خطأ في التحليل" : "Analysis Unavailable"}
            </p>
            <p className="text-sm font-medium text-io-primary mb-1">
              {isAr
                ? "تعذّر إتمام التحليل في هذه اللحظة."
                : "The analysis could not be completed at this time."}
            </p>
            <p className="text-xs text-io-secondary mb-4">
              {isAr
                ? "يُرجى اختيار سيناريو مختلف أو المحاولة مرة أخرى."
                : error}
            </p>
            <button
              onClick={() => { setError(null); setAppView("scenarios"); }}
              className="px-4 py-2 text-sm font-medium bg-io-bg border border-io-border rounded-lg hover:bg-io-accent hover:text-white hover:border-io-accent transition-colors"
            >
              {isAr ? "اختر سيناريو آخر" : "Try Another Scenario"}
            </button>
          </div>
        </div>
      )}

      {/* Dashboard / flow view */}
      {result && detailView === "dashboard" && (
        <ErrorBoundary section="Persona Flow View">
          <PersonaFlowView result={result} lang={lang} />
        </ErrorBoundary>
      )}

      {/* Sector drill-downs */}
      {result && detailView === "banking" && (
        <ErrorBoundary section="Banking Stress">
          <div className="max-w-6xl mx-auto p-6">
            <BankingDetailPanel data={result.banking} lang={lang} />
          </div>
        </ErrorBoundary>
      )}
      {result && detailView === "insurance" && (
        <ErrorBoundary section="Insurance Stress">
          <div className="max-w-6xl mx-auto p-6">
            <InsuranceDetailPanel data={result.insurance} lang={lang} />
          </div>
        </ErrorBoundary>
      )}
      {result && detailView === "fintech" && (
        <ErrorBoundary section="Fintech Stress">
          <div className="max-w-6xl mx-auto p-6">
            <FintechDetailPanel data={result.fintech} lang={lang} />
          </div>
        </ErrorBoundary>
      )}
      {result && detailView === "decisions" && (
        <ErrorBoundary section="Decision Actions">
          <div className="max-w-6xl mx-auto p-6">
            <DecisionDetailPanel
              decisions={result.decisions}
              explanation={result.explanation}
              lang={lang}
            />
          </div>
        </ErrorBoundary>
      )}

      {/* Back nav */}
      {(result || loading) && (
        <div className="fixed bottom-6 left-6 z-50">
          <button
            onClick={handleBack}
            className="px-4 py-2 text-xs font-medium bg-io-surface border border-io-border rounded-lg shadow-sm hover:shadow-md transition-shadow text-io-secondary hover:text-io-primary"
          >
            {detailView !== "dashboard" && result
              ? isAr
                ? "← النظرة العامة"
                : "← Overview"
              : isAr
              ? "← سيناريو جديد"
              : "← New Scenario"}
          </button>
        </div>
      )}
    </div>
  );
}
