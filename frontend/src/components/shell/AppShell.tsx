"use client";

/**
 * Impact Observatory | مرصد الأثر — Unified App Shell
 *
 * Single institutional shell for all pages.
 * Institutional top bar: wordmark + nav + persona + language + export.
 * Desktop-first. RTL-safe. No emoji in chrome.
 */

import React from "react";
import Link from "next/link";
import { useAppStore } from "@/store/app-store";
import type { Persona } from "@/lib/persona-view-model";

interface AppShellProps {
  children: React.ReactNode;
  /** Active route for nav highlighting */
  activeRoute?: "dashboard" | "graph" | "map" | "decisions";
  /** Scenario context label shown in breadcrumb */
  scenarioLabel?: string;
  /** Export action rendered in top bar */
  exportAction?: React.ReactNode;
}

const NAV_ITEMS = [
  { key: "dashboard", href: "/", en: "Dashboard", ar: "لوحة المعلومات" },
  { key: "graph", href: "/graph-explorer", en: "Propagation", ar: "الانتشار" },
  { key: "map", href: "/map", en: "Impact Map", ar: "خريطة الأثر" },
  { key: "decisions", href: "/decisions", en: "Decision Panel", ar: "لوحة القرار" },
] as const;

const PERSONA_LABELS: Record<Persona, { en: string; ar: string; desc: string }> = {
  executive: { en: "Executive", ar: "تنفيذي", desc: "KPIs, sector status, top decisions" },
  analyst: { en: "Analyst", ar: "محلل", desc: "Deep mechanics, causal chain, signal detail" },
  regulator: { en: "Regulator", ar: "رقابي", desc: "Audit trail, decision lineage, accountability" },
};

const ALL_PERSONAS: Persona[] = ["executive", "analyst", "regulator"];

export default function AppShell({
  children,
  activeRoute,
  scenarioLabel,
  exportAction,
}: AppShellProps) {
  const language = useAppStore((s) => s.language);
  const setLanguage = useAppStore((s) => s.setLanguage);
  const persona = useAppStore((s) => s.persona);
  const setPersona = useAppStore((s) => s.setPersona);
  const isAr = language === "ar";

  return (
    <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Top Navigation ────────────────────────────────────────── */}
      <nav className="h-14 bg-io-surface border-b border-io-border px-6 lg:px-10 flex items-center justify-between sticky top-0 z-50 gap-4">

        {/* Left: Wordmark + version + scenario breadcrumb */}
        <div className="flex items-center gap-3 min-w-0">
          <Link href="/" className="flex items-center gap-2.5 flex-shrink-0 group">
            {/* Logo mark — text-based, no emoji */}
            <div className="w-7 h-7 bg-io-primary rounded flex items-center justify-center flex-shrink-0">
              <span className="text-white text-[10px] font-bold tracking-tight">IO</span>
            </div>
            <div className="hidden sm:block">
              <span className="text-sm font-semibold text-io-primary group-hover:text-io-accent transition-colors tracking-tight">
                {isAr ? "مرصد الأثر" : "Impact Observatory"}
              </span>
            </div>
          </Link>

          {/* Version badge */}
          <span className="hidden md:inline text-[10px] font-medium text-io-secondary bg-io-bg border border-io-border px-1.5 py-0.5 rounded">
            v4.0
          </span>

          {/* Scenario breadcrumb */}
          {scenarioLabel && (
            <>
              <span className="text-io-border hidden md:inline">/</span>
              <span className="text-xs text-io-secondary truncate max-w-[180px] hidden md:inline">
                {scenarioLabel}
              </span>
            </>
          )}
        </div>

        {/* Center: Nav links */}
        <div className="hidden md:flex items-center gap-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = activeRoute === item.key;
            return (
              <Link
                key={item.key}
                href={item.href}
                className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                  isActive
                    ? "bg-io-accent/8 text-io-accent"
                    : "text-io-secondary hover:text-io-primary hover:bg-io-bg"
                }`}
              >
                {isAr ? item.ar : item.en}
              </Link>
            );
          })}
        </div>

        {/* Right: Persona + Language + Export */}
        <div className="flex items-center gap-2 flex-shrink-0">

          {/* Persona switcher */}
          <div className="hidden lg:flex items-center bg-io-bg rounded-lg p-0.5 border border-io-border gap-0.5">
            {ALL_PERSONAS.map((p) => {
              const labels = PERSONA_LABELS[p];
              return (
                <button
                  key={p}
                  onClick={() => setPersona(p)}
                  title={labels.desc}
                  className={`px-2.5 py-1.5 text-[11px] font-medium rounded-md transition-colors ${
                    persona === p
                      ? "bg-io-surface text-io-primary shadow-sm border border-io-border"
                      : "text-io-secondary hover:text-io-primary"
                  }`}
                >
                  {isAr ? labels.ar : labels.en}
                </button>
              );
            })}
          </div>

          {/* Language toggle */}
          <button
            onClick={() => setLanguage(isAr ? "en" : "ar")}
            className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary hover:border-io-secondary/50 transition-colors"
          >
            {isAr ? "EN" : "عر"}
          </button>

          {/* Export action slot */}
          {exportAction && exportAction}
        </div>
      </nav>

      {/* ── Page content ──────────────────────────────────────────── */}
      <main>{children}</main>
    </div>
  );
}
