"use client";

import React, { useMemo } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { t, type Locale } from "@/i18n/dictionary";
import { Globe, ChevronRight, Play } from "lucide-react";
import Link from "next/link";

interface ObservatoryShellProps {
  children: React.ReactNode;
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  dataSource?: "live" | "mock";
  activeTab?: string;
  isDemoMode?: boolean;
}

const TABS = [
  { id: "dashboard", labelEn: "Briefing", labelAr: "الإحاطة التنفيذية" },
  { id: "scenarios", labelEn: "Scenarios", labelAr: "السيناريوهات" },
  { id: "macro", labelEn: "Macro Outlook", labelAr: "المشهد الكلي" },
  { id: "propagation", labelEn: "Transmission", labelAr: "مسار الانتقال" },
  { id: "map", labelEn: "GCC Exposure", labelAr: "خريطة التعرض" },
  { id: "sectors", labelEn: "Sector Risk", labelAr: "مخاطر القطاعات" },
  { id: "decisions", labelEn: "Decision Room", labelAr: "غرفة القرار" },
  { id: "audit", labelEn: "Governance", labelAr: "الحوكمة والرقابة" },
];

const FLOW_STAGES = [
  "Signal",
  "Macro",
  "Transmission",
  "Exposure",
  "Banking",
  "Insurance",
  "Sector",
  "Decision",
  "Outcome",
  "Audit",
];

export function ObservatoryShell({
  children,
  scenarioLabel,
  scenarioLabelAr,
  dataSource = "mock",
  activeTab = "dashboard",
  isDemoMode = false,
}: ObservatoryShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const language = useAppStore((s) => s.language);
  const setLanguage = useAppStore((s) => s.setLanguage);

  const isArabic = language === "ar";
  const tabParam = searchParams.get("tab") || "dashboard";
  const currentTabId = tabParam === "dashboard" ? "dashboard" : tabParam || "dashboard";
  
  const flowStageDisplay = useMemo(() => {
    return FLOW_STAGES.map((stage, idx) => (
      <React.Fragment key={stage}>
        <span className="text-xs font-medium text-io-secondary">{stage}</span>
        {idx < FLOW_STAGES.length - 1 && (
          <ChevronRight className="w-3 h-3 text-border-io-border" />
        )}
      </React.Fragment>
    ));
  }, []);

  const runId = searchParams.get("run");
  const demoParam = searchParams.get("demo");

  const scenarioParam = searchParams.get("scenario");

  const handleTabClick = (tabId: string) => {
    // Build query params preserving run, demo, and scenario state
    const params = new URLSearchParams();
    if (tabId !== "dashboard") params.set("tab", tabId);
    if (runId) params.set("run", runId);
    if (demoParam) params.set("demo", demoParam);
    if (scenarioParam) params.set("scenario", scenarioParam);
    const qs = params.toString();
    router.push(`/command-center${qs ? `?${qs}` : ""}`);
  };

  const handleLanguageToggle = () => {
    setLanguage(language === "en" ? "ar" : "en");
  };

  const scenarioDisplayLabel = isArabic ? scenarioLabelAr || scenarioLabel : scenarioLabel;

  return (
    <div
      className={`min-h-screen bg-io-bg text-io-primary flex flex-col ${isArabic ? "rtl" : "ltr"}`}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* Identity Header */}
      <header className="bg-io-surface border-b border-io-border px-6 py-5 shadow-sm">
        <div className="max-w-7xl mx-auto">
          {/* Top Row: Logo + Title + Language Toggle */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-io-accent-dim rounded-lg">
                <Globe className="w-5 h-5 text-io-accent" />
              </div>
              <div className={`flex flex-col gap-0.5 ${isArabic ? "text-right" : "text-left"}`}>
                <h1 className="text-lg font-semibold text-io-primary">
                  {isArabic ? "مرصد الأثر" : "Impact Observatory"}
                </h1>
                <p className="text-xs text-io-secondary">
                  {isArabic ? "منصة الاستخبارات الاقتصادية والمالية لدول الخليج" : "GCC Macro Financial Intelligence Platform"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Start Demo CTA */}
              <Link
                href="/command-center?demo=true"
                className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-io-primary text-white hover:bg-io-accent transition-colors shadow-sm"
              >
                <Play size={12} />
                {isArabic ? "عرض تجريبي" : "Start Demo"}
              </Link>

              {/* Language Toggle Button */}
              <button
                onClick={handleLanguageToggle}
                className="px-3 py-2 text-sm font-medium rounded-lg border border-io-border bg-io-bg hover:bg-slate-100 transition-colors text-io-primary hover:text-io-accent"
                aria-label={isArabic ? "Switch to English" : "Switch to Arabic"}
              >
                {isArabic ? "EN" : "عربي"}
              </button>
            </div>
          </div>

          {/* Subtitle — intelligence flow principle */}
          <p className="text-xs text-io-secondary mb-3">
            {isArabic
              ? "إشارة ← انتقال ← تعرض ← بنوك ← تأمين ← قطاعات ← قرار ← نتيجة ← حوكمة"
              : "Signal → Transmission → Exposure → Banking → Insurance → Sector → Decision → Outcome → Audit"}
          </p>

          {/* Flow Stages */}
          <div className="flex items-center gap-2 text-io-secondary overflow-x-auto pb-1">
            {flowStageDisplay}
          </div>
        </div>
      </header>

      {/* Scenario Context Bar */}
      {scenarioDisplayLabel && (
        <div className="bg-io-surface border-b border-io-border px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className={`flex items-center gap-3 ${isArabic ? "flex-row-reverse" : ""}`}>
              <div className="w-2 h-2 rounded-full bg-io-accent animate-pulse" />
              <span className="text-sm text-io-secondary">
                {isArabic ? "السيناريو النشط:" : "Active Scenario:"}
              </span>
              <span className="text-sm font-medium text-io-accent">{scenarioDisplayLabel}</span>
            </div>

            {/* Live/Demo Indicator */}
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  dataSource === "live" ? "bg-io-status-low" : "bg-io-status-elevated"
                } animate-pulse`}
              />
              <span className="text-xs text-io-secondary">
                {dataSource === "live"
                  ? isArabic
                    ? "بث مباشر"
                    : "Live"
                  : isArabic
                    ? "محاكاة"
                    : "Demo"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <nav className="bg-io-surface border-b border-io-border px-6">
        <div className="max-w-7xl mx-auto flex gap-8 overflow-x-auto">
          {TABS.map((tab) => {
            const isActive = currentTabId === tab.id;
            const tabLabel = isArabic ? tab.labelAr : tab.labelEn;
            
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.id)}
                className={`py-4 px-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? "text-io-accent border-io-accent"
                    : "text-io-secondary border-transparent hover:text-io-primary"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                {tabLabel}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        <div className="h-full w-full">{children}</div>
      </main>
    </div>
  );
}
