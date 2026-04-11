"use client";

import React, { useMemo } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { t, type Locale } from "@/i18n/dictionary";
import { Globe, ChevronRight } from "lucide-react";

interface ObservatoryShellProps {
  children: React.ReactNode;
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  dataSource?: "live" | "mock";
  activeTab?: string;
}

const TABS = [
  { id: "dashboard", labelEn: "Dashboard", labelAr: "لوحة المعلومات" },
  { id: "propagation", labelEn: "Propagation", labelAr: "الانتشار" },
  { id: "map", labelEn: "Impact Map", labelAr: "خريطة الأثر" },
  { id: "sectors", labelEn: "Sector Intel", labelAr: "القطاعات" },
  { id: "decisions", labelEn: "Decision Room", labelAr: "غرفة القرار" },
  { id: "regulatory", labelEn: "Regulatory", labelAr: "الرقابة والتدقيق" },
];

const FLOW_STAGES = [
  "Macro Shock",
  "Transmission",
  "Sector Impact",
  "Entity Exposure",
  "Decision",
  "Audit",
];

export function ObservatoryShell({
  children,
  scenarioLabel,
  scenarioLabelAr,
  dataSource = "mock",
  activeTab = "dashboard",
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
        <span className="text-xs font-medium text-slate-300">{stage}</span>
        {idx < FLOW_STAGES.length - 1 && (
          <ChevronRight className="w-3 h-3 text-slate-600" />
        )}
      </React.Fragment>
    ));
  }, []);

  const runId = searchParams.get("run");

  const handleTabClick = (tabId: string) => {
    const runSuffix = runId ? `${tabId === "dashboard" ? "?" : "&"}run=${runId}` : "";
    if (tabId === "dashboard") {
      router.push(`/command-center${runSuffix}`);
    } else {
      router.push(`/command-center?tab=${tabId}${runId ? `&run=${runId}` : ""}`);
    }
  };

  const handleLanguageToggle = () => {
    setLanguage(language === "en" ? "ar" : "en");
  };

  const scenarioDisplayLabel = isArabic ? scenarioLabelAr || scenarioLabel : scenarioLabel;

  return (
    <div
      className={`min-h-screen bg-[#060910] text-slate-300 flex flex-col ${isArabic ? "rtl" : "ltr"}`}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* Identity Header */}
      <header className="bg-gradient-to-b from-[#0f1419] to-[#060910] border-b border-slate-800 px-6 py-5">
        <div className="max-w-7xl mx-auto">
          {/* Top Row: Logo + Title + Language Toggle */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Globe className="w-5 h-5 text-blue-400" />
              </div>
              <div className={`flex flex-col gap-0.5 ${isArabic ? "text-right" : "text-left"}`}>
                <h1 className="text-lg font-semibold text-white">
                  {isArabic ? "الذكاء المالي الكلي" : "Macro Financial Intelligence"}
                </h1>
                <p className="text-xs text-slate-400">
                  {isArabic ? "دول مجلس التعاون الخليجي" : "GCC"}
                </p>
              </div>
            </div>

            {/* Language Toggle Button */}
            <button
              onClick={handleLanguageToggle}
              className="px-3 py-2 text-sm font-medium rounded-lg border border-slate-700 bg-slate-900/50 hover:bg-slate-800 transition-colors text-slate-300 hover:text-white"
              aria-label={isArabic ? "Switch to English" : "Switch to Arabic"}
            >
              {isArabic ? "EN" : "عربي"}
            </button>
          </div>

          {/* Subtitle */}
          <p className="text-xs text-slate-400 mb-3">
            {isArabic
              ? "نظام القرار لأسواق دول مجلس التعاون المالية"
              : "Decision System for GCC Financial Markets"}
          </p>

          {/* Flow Stages */}
          <div className="flex items-center gap-2 text-slate-500 overflow-x-auto pb-1">
            {flowStageDisplay}
          </div>
        </div>
      </header>

      {/* Scenario Context Bar */}
      {scenarioDisplayLabel && (
        <div className="bg-[#0f1419] border-b border-slate-800 px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className={`flex items-center gap-3 ${isArabic ? "flex-row-reverse" : ""}`}>
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <span className="text-sm text-slate-400">
                {isArabic ? "السيناريو النشط:" : "Active Scenario:"}
              </span>
              <span className="text-sm font-medium text-blue-400">{scenarioDisplayLabel}</span>
            </div>

            {/* Live/Demo Indicator */}
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  dataSource === "live" ? "bg-green-500" : "bg-yellow-500"
                } animate-pulse`}
              />
              <span className="text-xs text-slate-500">
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
      <nav className="bg-[#060910] border-b border-slate-800 px-6">
        <div className="max-w-7xl mx-auto flex gap-8">
          {TABS.map((tab) => {
            const isActive = currentTabId === tab.id;
            const tabLabel = isArabic ? tab.labelAr : tab.labelEn;
            
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.id)}
                className={`py-4 px-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? "text-blue-400 border-blue-400"
                    : "text-slate-400 border-transparent hover:text-slate-300"
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
