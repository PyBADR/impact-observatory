"use client";

/**
 * Impact Observatory | مرصد الأثر
 *
 * Product landing page → Scenario runner → Executive dashboard
 * White/light boardroom aesthetic. Financial-first. Large typography.
 * Arabic + English bilingual.
 */

import React, { useState } from "react";
import ImpactGlobe from "@/components/globe/impact-globe";
import ExecutiveDashboard from "@/features/dashboard/ExecutiveDashboard";
import BankingDetailPanel from "@/features/banking/BankingDetailPanel";
import InsuranceDetailPanel from "@/features/insurance/InsuranceDetailPanel";
import FintechDetailPanel from "@/features/fintech/FintechDetailPanel";
import DecisionDetailPanel from "@/features/decisions/DecisionDetailPanel";
import BusinessImpactPanel from "@/features/business-impact/BusinessImpactPanel";
import RegulatoryTimelinePanel from "@/features/regulatory/RegulatoryTimelinePanel";
import TimelinePanel from "@/features/timeline/TimelinePanel";
import type { RunResult, Language, ViewMode, BusinessImpact, TimelineResult, RegulatoryState, RegulatoryBreachEvent } from "@/types/observatory";

type AppView = "landing" | "scenarios" | "results";
type DetailView = "dashboard" | "banking" | "insurance" | "fintech" | "decisions" | "business-impact" | "regulatory" | "timeline";

// ── Scenarios ────────────────────────────────────────────────────────

const SCENARIOS = [
  { id: "hormuz_chokepoint_disruption", label: "Strategic Maritime Chokepoint Disruption (Hormuz)", label_ar: "تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)", desc: "Strait of Hormuz blockade — oil transit, shipping, energy supply chain", desc_ar: "حصار مضيق هرمز — عبور النفط والشحن وسلسلة إمداد الطاقة", loss: "$3.2B", severity: 0.8, icon: "⚓" },
  { id: "red_sea_trade_corridor_instability", label: "Red Sea Trade Corridor Instability", label_ar: "اضطراب ممر التجارة في البحر الأحمر", desc: "Regional conflict escalation — Red Sea shipping, insurance claims surge", desc_ar: "تصعيد صراع إقليمي — شحن البحر الأحمر وارتفاع مطالبات التأمين", loss: "$1.8B", severity: 0.7, icon: "🔥" },
  { id: "financial_infrastructure_cyber_disruption", label: "Financial Infrastructure Cyber Disruption", label_ar: "تعطّل البنية المالية نتيجة هجوم سيبراني", desc: "Financial infrastructure cyberattack — payment systems, API disruption", desc_ar: "هجوم سيبراني على البنية المالية — أنظمة الدفع وتعطل الواجهات", loss: "$0.9B", severity: 0.6, icon: "🛡️" },
  { id: "energy_market_volatility_shock", label: "Energy Market Volatility Shock", label_ar: "صدمة تقلبات أسواق الطاقة", desc: "Sudden oil price collapse — GDP impact, banking stress, fiscal reserves", desc_ar: "انهيار مفاجئ في أسعار النفط — أثر على الناتج المحلي والاحتياطيات", loss: "$4.5B", severity: 0.8, icon: "📉" },
  { id: "regional_liquidity_stress_event", label: "Regional Liquidity Stress Event", label_ar: "أزمة سيولة مصرفية إقليمية", desc: "Regional banking contagion — liquidity crisis, CAR deterioration", desc_ar: "عدوى بنكية إقليمية — أزمة سيولة وتدهور كفاية رأس المال", loss: "$2.1B", severity: 0.7, icon: "🏦" },
  { id: "critical_port_throughput_disruption", label: "Critical Port Throughput Disruption", label_ar: "تعطّل تدفق العمليات في ميناء حيوي", desc: "Major port shutdown — trade flow, supply chain cascade, insurance", desc_ar: "توقف ميناء رئيسي — تدفق التجارة وتأثيرات سلسلة التوريد", loss: "$1.5B", severity: 0.6, icon: "🚢" },
  { id: "cross_border_sanctions_escalation", label: "Cross-Border Sanctions Escalation", label_ar: "تصاعد العقوبات العابرة للحدود", desc: "New sanctions wave — trade rerouting, compliance costs, banking exposure", desc_ar: "موجة عقوبات جديدة — إعادة توجيه التجارة وتكاليف الامتثال والتعرض البنكي", loss: "$2.4B", severity: 0.7, icon: "⚖️" },
  { id: "regional_airspace_constraint", label: "Regional Airspace Constraint Scenario", label_ar: "سيناريو قيود المجال الجوي الإقليمي", desc: "Regional airspace restrictions — aviation disruption, cargo delays, tourism impact", desc_ar: "قيود المجال الجوي الإقليمي — تعطل الطيران وتأخر الشحن وأثر السياحة", loss: "$1.1B", severity: 0.6, icon: "✈️" },
];

// ── Capability Cards ─────────────────────────────────────────────────

const CAPABILITIES = {
  en: [
    { title: "Financial Impact Modeling", desc: "Compute GDP-weighted loss propagation across 31 GCC entities with sector-specific elasticities. Real economics, not estimates.", icon: "💰" },
    { title: "Banking Stress Analysis", desc: "Basel III-aligned liquidity, credit, and FX stress testing across 6 major GCC institutions. Time-to-liquidity-breach countdown.", icon: "🏦" },
    { title: "Insurance Stress Modeling", desc: "IFRS-17 compliant claims surge modeling across 8 insurance lines. Combined ratio tracking with reinsurance trigger detection.", icon: "📋" },
    { title: "Fintech & Payment Disruption", desc: "Payment volume impact, settlement delays, API availability monitoring across 7 GCC payment platforms.", icon: "💳" },
    { title: "Decision Intelligence", desc: "Priority = 0.25×Urgency + 0.30×Value + 0.20×RegRisk + 0.15×Feasibility + 0.10×TimeEffect. Top 3 ranked actions.", icon: "🎯" },
    { title: "Bilingual Explainability", desc: "20-step causal chain explaining how events propagate through the GCC financial system. Arabic and English narratives.", icon: "🔗" },
  ],
  ar: [
    { title: "نمذجة الأثر المالي", desc: "حساب انتشار الخسائر المرجحة بالناتج المحلي عبر 31 كياناً خليجياً مع مرونات قطاعية محددة.", icon: "💰" },
    { title: "تحليل الضغط البنكي", desc: "اختبار ضغط السيولة والائتمان والعملة وفق بازل III عبر 6 مؤسسات خليجية. العد التنازلي لكسر السيولة.", icon: "🏦" },
    { title: "نمذجة ضغط التأمين", desc: "نمذجة ارتفاع المطالبات وفق IFRS-17 عبر 8 خطوط تأمين. تتبع النسبة المجمعة مع كشف تفعيل إعادة التأمين.", icon: "📋" },
    { title: "تعطل الفنتك والمدفوعات", desc: "أثر حجم المدفوعات وتأخر التسوية ومراقبة توفر واجهة API عبر 7 منصات دفع خليجية.", icon: "💳" },
    { title: "ذكاء القرار", desc: "الأولوية = القيمة + الإلحاح + المخاطر التنظيمية. أهم 3 قرارات قابلة للتنفيذ مع تحليل التكلفة والعائد.", icon: "🎯" },
    { title: "تفسير ثنائي اللغة", desc: "سلسلة سببية من 20 خطوة توضح كيف تنتشر الأحداث عبر النظام المالي الخليجي. بالعربية والإنجليزية.", icon: "🔗" },
  ],
};

// ── Main Component ───────────────────────────────────────────────────

export default function HomePage() {
  const [appView, setAppView] = useState<AppView>("landing");
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<Language>("en");
  const [viewMode, setViewMode] = useState<ViewMode>("executive");
  const [detailView, setDetailView] = useState<DetailView>("dashboard");
  const [gccEntities, setGccEntities] = useState<any[]>([]);

  const isAr = lang === "ar";

  const runScenario = async (templateId: string, severity: number) => {
    setLoading(true);
    setError(null);
    setAppView("results");
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${BASE}/api/v1/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_id: templateId,
          severity,
          horizon_hours: 336,
        }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setResult(data);
      setDetailView("dashboard");
      // Fetch GCC entities for the globe
      fetch(`${BASE}/api/v1/graph/nodes?limit=200`, {
        headers: { "X-API-Key": "observatory-dev-key" },
      })
        .then((r) => r.json())
        .then((d) => setGccEntities(d.nodes || []))
        .catch(() => {});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
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
    en: { dashboard: "Dashboard", banking: "Banking", insurance: "Insurance", fintech: "Fintech", decisions: "Decisions", "business-impact": "Business Impact", regulatory: "Regulatory", timeline: "Timeline" },
    ar: { dashboard: "لوحة المعلومات", banking: "البنوك", insurance: "التأمين", fintech: "الفنتك", decisions: "القرارات", "business-impact": "أثر الأعمال", regulatory: "التنظيمي", timeline: "الجدول الزمني" },
  };

  // ── Top Navigation (always visible) ──

  const TopNav = () => (
    <nav className="bg-io-surface border-b border-io-border px-6 lg:px-10 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <button onClick={() => { setAppView("landing"); setResult(null); }} className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-io-accent rounded-lg flex items-center justify-center text-white text-sm font-bold">IO</div>
          <span className="text-lg font-bold text-io-primary group-hover:text-io-accent transition-colors">
            {isAr ? "مرصد الأثر" : "Impact Observatory"}
          </span>
        </button>
        {appView !== "landing" && (
          <span className="text-xs text-io-secondary font-medium bg-io-bg px-2 py-0.5 rounded border border-io-border">v1.0</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        {appView === "results" && result && (
          <div className="hidden md:flex bg-io-bg rounded-lg p-0.5 border border-io-border">
            {(["executive", "analyst", "regulatory"] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-colors ${viewMode === mode ? "bg-io-accent text-white" : "text-io-secondary hover:text-io-primary"}`}
              >
                {mode}
              </button>
            ))}
          </div>
        )}
        <button
          onClick={() => setLang(isAr ? "en" : "ar")}
          className="px-3 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary transition-colors"
        >
          {isAr ? "English" : "العربية"}
        </button>
        {appView === "landing" && (
          <div className="flex items-center gap-2">
            <a
              href="/dashboard"
              className="px-4 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-accent hover:border-io-accent transition-colors"
            >
              {isAr ? "لوحة المعلومات" : "Dashboard"}
            </a>
            <button
              onClick={() => setAppView("scenarios")}
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
            >
              {isAr ? "ابدأ التحليل" : "Run Scenario"}
            </button>
          </div>
        )}
      </div>
    </nav>
  );

  // ── LANDING PAGE ──────────────────────────────────────────────────

  if (appView === "landing") {
    const caps = CAPABILITIES[lang];
    return (
      <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
        <TopNav />

        {/* Hero Section */}
        <section className="max-w-5xl mx-auto px-6 lg:px-10 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-io-accent/5 border border-io-accent/20 rounded-full text-io-accent text-xs font-medium mb-6">
            {isAr ? "منصة ذكاء القرار للأسواق المالية الخليجية" : "Decision Intelligence for GCC Financial Markets"}
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-io-primary leading-tight mb-6">
            {isAr ? "افهم الأثر المالي" : "Understand financial impact"}
            <br />
            <span className="text-io-accent">
              {isAr ? "قبل حدوثه" : "before it happens"}
            </span>
          </h1>
          <p className="text-lg md:text-xl text-io-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
            {isAr
              ? "حاكي الضغط النظامي عبر البنوك والتأمين والفنتك والبنية الحيوية — واتخذ القرار قبل الانهيار."
              : "Simulate systemic stress across banking, insurance, fintech, and critical infrastructure — then act before failure."}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => setAppView("scenarios")}
              className="px-8 py-3.5 bg-io-accent text-white text-base font-semibold rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-io-accent/20"
            >
              {isAr ? "ابدأ التحليل" : "Run Scenario"}
            </button>
            <a
              href="/dashboard"
              className="px-8 py-3.5 text-io-secondary text-base font-medium rounded-xl border border-io-border hover:border-io-accent hover:text-io-accent transition-colors"
            >
              {isAr ? "عرض الملخص التنفيذي" : "View Executive Brief"}
            </a>
          </div>
        </section>

        {/* Metrics Strip */}
        <section className="max-w-5xl mx-auto px-6 lg:px-10 pb-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { value: "31", label: isAr ? "كيان خليجي" : "GCC Entities", sub: isAr ? "طاقة · بحري · طيران · مالي" : "Energy · Maritime · Aviation · Finance" },
              { value: "15", label: isAr ? "خدمة تحليلية" : "Analysis Services", sub: isAr ? "سيناريو → قرار → أثر" : "Scenario → Decision → Impact" },
              { value: "$2.1T", label: isAr ? "ناتج محلي مغطى" : "GDP Coverage", sub: isAr ? "دول الخليج الست" : "Six GCC nations" },
              { value: "<2s", label: isAr ? "وقت التحليل" : "Analysis Time", sub: isAr ? "من الحدث إلى القرار" : "Event to decision" },
            ].map((m) => (
              <div key={m.label} className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm text-center">
                <p className="text-3xl font-bold text-io-accent tabular-nums">{m.value}</p>
                <p className="text-sm font-semibold text-io-primary mt-1">{m.label}</p>
                <p className="text-xs text-io-secondary mt-0.5">{m.sub}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What It Does */}
        <section className="bg-io-surface border-y border-io-border py-16">
          <div className="max-w-5xl mx-auto px-6 lg:px-10">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-io-primary mb-3">
                {isAr ? "كيف يعمل مرصد الأثر" : "How Impact Observatory Works"}
              </h2>
              <p className="text-io-secondary text-base max-w-2xl mx-auto">
                {isAr
                  ? "كل مخرج يربط: الحدث → الأثر المالي → ضغط القطاع → القرار"
                  : "Every output maps: Event → Financial Impact → Sector Stress → Decision"}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  step: "01",
                  title: isAr ? "حدد السيناريو" : "Define Scenario",
                  desc: isAr ? "اختر حدثاً جيوسياسياً أو اقتصادياً — إغلاق مضيق هرمز، صدمة نفطية، هجوم سيبراني" : "Select a geopolitical or economic event — Hormuz closure, oil shock, cyber attack",
                },
                {
                  step: "02",
                  title: isAr ? "حلل الأثر" : "Analyze Impact",
                  desc: isAr ? "محرك الفيزياء ينشر الصدمة عبر 31 كياناً خليجياً ويحسب الخسارة المالية والضغط القطاعي" : "Physics engine propagates the shock across 31 GCC entities, computing financial loss and sector stress",
                },
                {
                  step: "03",
                  title: isAr ? "اتخذ القرار" : "Decide & Act",
                  desc: isAr ? "أعلى 3 إجراءات ذات أولوية مع تحليل التكلفة والعائد وتعيين المسؤول" : "Top 3 prioritized actions with cost-benefit analysis and owner assignment",
                },
              ].map((s) => (
                <div key={s.step} className="bg-io-bg border border-io-border rounded-xl p-6">
                  <div className="w-10 h-10 bg-io-accent/10 rounded-lg flex items-center justify-center text-io-accent text-sm font-bold mb-4">
                    {s.step}
                  </div>
                  <h3 className="text-lg font-bold text-io-primary mb-2">{s.title}</h3>
                  <p className="text-sm text-io-secondary leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Capabilities Grid */}
        <section id="capabilities" className="max-w-5xl mx-auto px-6 lg:px-10 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-io-primary mb-3">
              {isAr ? "القدرات" : "Capabilities"}
            </h2>
            <p className="text-io-secondary text-base">
              {isAr ? "نمذجة مالية شاملة للأسواق الخليجية" : "Comprehensive financial modeling for GCC markets"}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {caps.map((cap) => (
              <div key={cap.title} className="bg-io-surface border border-io-border rounded-xl p-6 shadow-sm hover:shadow-md hover:border-io-accent/30 transition-all">
                <div className="text-2xl mb-3">{cap.icon}</div>
                <h3 className="text-base font-bold text-io-primary mb-2">{cap.title}</h3>
                <p className="text-sm text-io-secondary leading-relaxed">{cap.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="bg-io-accent py-16">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              {isAr ? "ابدأ تحليل الأثر المالي الآن" : "Start analyzing financial impact now"}
            </h2>
            <p className="text-blue-100 text-base mb-8 max-w-xl mx-auto">
              {isAr
                ? "اختر سيناريو خليجي واحصل على تحليل مالي شامل مع إجراءات قرار مُرتّبة حسب الأولوية"
                : "Choose a GCC scenario and get comprehensive financial analysis with prioritized decision actions"}
            </p>
            <button
              onClick={() => setAppView("scenarios")}
              className="px-10 py-4 bg-white text-io-accent text-base font-bold rounded-xl hover:bg-blue-50 transition-colors shadow-lg"
            >
              {isAr ? "تشغيل السيناريو" : "Run Scenario"}
            </button>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-io-surface border-t border-io-border py-8">
          <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-io-accent rounded flex items-center justify-center text-white text-[10px] font-bold">IO</div>
              <span className="text-sm font-semibold text-io-primary">Impact Observatory</span>
              <span className="text-xs text-io-secondary">| مرصد الأثر</span>
            </div>
            <p className="text-xs text-io-secondary">
              {isAr ? "منصة ذكاء القرار للأسواق المالية الخليجية" : "Decision Intelligence Platform for GCC Financial Markets"}
            </p>
          </div>
        </footer>
      </div>
    );
  }

  // ── SCENARIO SELECTOR ─────────────────────────────────────────────

  if (appView === "scenarios" && !result && !loading) {
    return (
      <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
        <TopNav />
        <div className="max-w-4xl mx-auto px-6 lg:px-10 pt-12 pb-16">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-io-primary mb-3">
              {isAr ? "اختر سيناريو" : "Select a Scenario"}
            </h2>
            <p className="text-io-secondary text-base">
              {isAr
                ? "اختر حدثاً لتحليل الأثر المالي عبر القطاعات الخليجية"
                : "Choose an event to analyze financial impact across GCC sectors"}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {SCENARIOS.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => runScenario(scenario.id, scenario.severity)}
                className="bg-io-surface border border-io-border rounded-xl p-6 text-left shadow-sm hover:shadow-lg hover:border-io-accent transition-all group"
              >
                <div className="flex items-start gap-4">
                  <div className="text-3xl flex-shrink-0 mt-0.5">{scenario.icon}</div>
                  <div className="flex-1">
                    <p className="text-lg font-bold text-io-primary group-hover:text-io-accent transition-colors">
                      {isAr ? scenario.label_ar : scenario.label}
                    </p>
                    <p className="text-sm text-io-secondary mt-1 leading-relaxed">
                      {isAr ? scenario.desc_ar : scenario.desc}
                    </p>
                    <div className="flex items-center gap-3 mt-3 text-xs">
                      <span className="px-2 py-0.5 bg-io-danger/10 text-io-danger rounded font-semibold">
                        {scenario.loss}
                      </span>
                      <span className="text-io-secondary">
                        Severity: {(scenario.severity * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="text-center mt-8">
            <button
              onClick={() => setAppView("landing")}
              className="text-sm text-io-secondary hover:text-io-accent transition-colors"
            >
              {isAr ? "← العودة للصفحة الرئيسية" : "← Back to Home"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── RESULTS VIEW (Loading / Error / Dashboard) ─────────────────────

  return (
    <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      <TopNav />

      {/* Detail Navigation Tabs */}
      {result && (
        <div className="bg-io-surface border-b border-io-border px-6 lg:px-10 py-0 flex items-center gap-1 overflow-x-auto">
          {(["dashboard", "banking", "insurance", "fintech", "decisions", "business-impact", "regulatory", "timeline"] as DetailView[]).map((view) => (
            <button
              key={view}
              onClick={() => setDetailView(view)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                detailView === view
                  ? "border-io-accent text-io-accent"
                  : "border-transparent text-io-secondary hover:text-io-primary hover:border-io-border"
              }`}
            >
              {detailLabels[lang][view]}
            </button>
          ))}
          {/* PDF Export Button */}
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/runs/${result.run_id}/report/executive/pdf?lang=${lang}`}
            download={`impact-report-${result.run_id}.pdf`}
            className="flex items-center gap-1.5 px-3 py-1.5 ml-auto bg-io-primary text-white text-xs font-semibold rounded hover:bg-io-primary/90 transition-colors whitespace-nowrap"
            target="_blank"
            rel="noopener noreferrer"
          >
            ↓ {isAr ? "تصدير PDF" : "Export PDF"}
          </a>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center mt-32">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-io-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-io-primary font-semibold text-lg mb-1">
              {isAr ? "جاري تحليل السيناريو..." : "Analyzing scenario..."}
            </p>
            <p className="text-io-secondary text-sm">
              {isAr ? "15 محرك تحليلي يعمل الآن" : "Running 15 analysis engines"}
            </p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="max-w-lg mx-auto mt-16 p-6 bg-red-50 border border-red-200 rounded-xl text-center">
          <p className="text-io-danger font-medium mb-2">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => { setError(null); setAppView("scenarios"); }}
              className="px-4 py-2 text-sm bg-io-surface border border-io-border rounded-lg hover:bg-io-bg transition-colors"
            >
              {isAr ? "اختر سيناريو آخر" : "Try Another Scenario"}
            </button>
          </div>
        </div>
      )}

      {/* Dashboard */}
      {result && detailView === "dashboard" && (
        <>
          <ExecutiveDashboard data={result} lang={lang} onNavigate={(view: string) => setDetailView(view as DetailView)} />
          {/* Geographic Impact Map */}
          <div className="max-w-6xl mx-auto px-6 pb-8">
            <ImpactGlobe
              runResult={result}
              entities={gccEntities}
              lang={lang}
              className="w-full min-h-[360px]"
            />
          </div>
        </>
      )}

      {result && detailView === "banking" && (
        <div className="max-w-6xl mx-auto p-6"><BankingDetailPanel data={result.banking} lang={lang} /></div>
      )}

      {result && detailView === "insurance" && (
        <div className="max-w-6xl mx-auto p-6"><InsuranceDetailPanel data={result.insurance} lang={lang} /></div>
      )}

      {result && detailView === "fintech" && (
        <div className="max-w-6xl mx-auto p-6"><FintechDetailPanel data={result.fintech} lang={lang} /></div>
      )}

      {result && detailView === "decisions" && (
        <div className="max-w-6xl mx-auto p-6"><DecisionDetailPanel decisions={result.decisions} explanation={result.explanation} lang={lang} /></div>
      )}

      {result && detailView === "business-impact" && (
        <div className="max-w-6xl mx-auto p-6">
          <BusinessImpactPanel data={(result as unknown as Record<string, unknown>).business_impact as BusinessImpact | undefined} lang={lang} />
        </div>
      )}

      {result && detailView === "regulatory" && (
        <div className="max-w-6xl mx-auto p-6">
          <RegulatoryTimelinePanel
            breachEvents={((result as unknown as Record<string, unknown>).business_impact as BusinessImpact | undefined)?.regulatory_breach_events || []}
            regulatoryState={(result as unknown as Record<string, unknown>).regulatory_state as RegulatoryState | undefined}
            lang={lang}
          />
        </div>
      )}

      {result && detailView === "timeline" && (
        <div className="max-w-6xl mx-auto p-6">
          <TimelinePanel data={(result as unknown as Record<string, unknown>).timeline as TimelineResult | undefined} lang={lang} />
        </div>
      )}

      {/* Back button */}
      {(result || loading) && (
        <div className="fixed bottom-6 left-6 z-50">
          <button
            onClick={handleBack}
            className="px-4 py-2 text-sm font-medium bg-io-surface border border-io-border rounded-lg shadow-md hover:shadow-lg transition-shadow"
          >
            {detailView !== "dashboard" && result
              ? (isAr ? "← لوحة المعلومات" : "← Dashboard")
              : (isAr ? "← سيناريو جديد" : "← New Scenario")
            }
          </button>
        </div>
      )}
    </div>
  );
}
