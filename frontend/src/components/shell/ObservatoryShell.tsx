"use client";

/**
 * ObservatoryShell — Executive command surface shell.
 *
 * 4 primary tabs only: Briefing | Propagation | Decision | Monitoring
 * No analyst toolbox. No flow diagrams. No demo CTAs.
 * The executive sees one command flow.
 */

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAppStore } from "@/store/app-store";

interface ObservatoryShellProps {
  children: React.ReactNode;
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  dataSource?: "live" | "mock";
  activeTab?: string;
}

// Executive command flow — 4 tabs only.
const TABS = [
  { id: "", labelEn: "Briefing", labelAr: "الإحاطة" },
  { id: "propagation", labelEn: "Propagation", labelAr: "الانتشار" },
  { id: "decision", labelEn: "Decision", labelAr: "القرار" },
  { id: "monitoring", labelEn: "Monitoring", labelAr: "المراقبة" },
];

export function ObservatoryShell({
  children,
  scenarioLabel,
  scenarioLabelAr,
  dataSource = "mock",
  activeTab = "",
}: ObservatoryShellProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const language = useAppStore((s) => s.language);
  const setLanguage = useAppStore((s) => s.setLanguage);

  const isArabic = language === "ar";
  const tabParam = searchParams.get("tab") || "";
  const currentTabId = tabParam;
  const runId = searchParams.get("run");

  const scenarioDisplayLabel = isArabic
    ? scenarioLabelAr || scenarioLabel
    : scenarioLabel;

  const handleTabClick = (tabId: string) => {
    if (tabId === "") {
      router.push(`/command-center${runId ? `?run=${runId}` : ""}`);
    } else {
      router.push(`/command-center?tab=${tabId}${runId ? `&run=${runId}` : ""}`);
    }
  };

  const handleLanguageToggle = () => {
    setLanguage(language === "en" ? "ar" : "en");
  };

  return (
    <div
      className={`min-h-screen bg-[#f5f5f7] text-[#1d1d1f] flex flex-col ${isArabic ? "rtl" : "ltr"}`}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* ── Identity Header ── */}
      <header className="border-b border-[#e5e5e7] px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className={`flex items-baseline gap-3 ${isArabic ? "flex-row-reverse" : ""}`}>
            <h1 className="text-[0.9375rem] font-bold tracking-tight text-[#1d1d1f]">
              Impact Observatory
            </h1>
            <span className="text-[0.6875rem] text-[#6e6e73] font-medium tracking-wide">
              مرصد الأثر
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Active scenario indicator */}
            {scenarioDisplayLabel && (
              <div className={`flex items-center gap-2 ${isArabic ? "flex-row-reverse" : ""}`}>
                <div className="w-1.5 h-1.5 rounded-full bg-[#0071e3] animate-pulse" />
                <span className="text-[0.75rem] text-[#515154] font-medium truncate max-w-[200px]">
                  {scenarioDisplayLabel}
                </span>
              </div>
            )}

            {/* Data source */}
            <span className="text-[0.625rem] text-[#8e8e93] uppercase tracking-widest font-medium">
              {dataSource === "live" ? "Live" : "Sim"}
            </span>

            {/* Language toggle */}
            <button
              onClick={handleLanguageToggle}
              className="px-2.5 py-1 text-[0.6875rem] font-medium rounded border border-[#e5e5e7] text-[#6e6e73] hover:text-[#515154] hover:border-[#d6d6db] transition-colors"
              aria-label={isArabic ? "Switch to English" : "Switch to Arabic"}
            >
              {isArabic ? "EN" : "عربي"}
            </button>
          </div>
        </div>
      </header>

      {/* ── Executive Tab Navigation ── */}
      <nav className="border-b border-[#e5e5e7] px-6">
        <div className="max-w-6xl mx-auto flex gap-0">
          {TABS.map((tab) => {
            const isActive = currentTabId === tab.id;
            const tabLabel = isArabic ? tab.labelAr : tab.labelEn;

            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.id)}
                className={`py-3 px-5 text-[0.8125rem] font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? "text-[#1d1d1f] border-[#0071e3]"
                    : "text-[#6e6e73] border-transparent hover:text-[#515154]"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                {tabLabel}
              </button>
            );
          })}
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className="flex-1 overflow-auto">
        <div className="h-full w-full">{children}</div>
      </main>
    </div>
  );
}
