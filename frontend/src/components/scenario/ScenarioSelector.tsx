"use client";

/**
 * ScenarioSelector — Top navigation for scenario switching.
 *
 * Fetches scenario templates from /api/v1/scenarios on mount.
 * When user clicks a scenario, fires onSelect(templateId) which
 * triggers a new run via the store — no page reload.
 *
 * Design: horizontal pill bar, active scenario highlighted,
 * grouped by domain if many scenarios exist.
 */

import { useState, useEffect, useMemo } from "react";

interface ScenarioTemplate {
  id: string;
  name: string;
  name_ar: string;
  sectors_affected: string[];
}

interface ScenarioSelectorProps {
  activeScenarioId?: string;
  onSelect: (templateId: string) => void;
  isLoading?: boolean;
  locale?: "en" | "ar";
}

// Short display names for the scenario selector pills
const SHORT_NAMES: Record<string, { en: string; ar: string }> = {
  hormuz_chokepoint_disruption: { en: "Hormuz", ar: "هرمز" },
  hormuz_full_closure: { en: "Hormuz Full", ar: "إغلاق هرمز" },
  saudi_oil_shock: { en: "Oil Shock", ar: "صدمة نفطية" },
  uae_banking_crisis: { en: "Banking", ar: "أزمة بنوك" },
  gcc_cyber_attack: { en: "Cyber", ar: "هجوم سيبراني" },
  qatar_lng_disruption: { en: "Qatar LNG", ar: "غاز قطر" },
  bahrain_sovereign_stress: { en: "Bahrain", ar: "البحرين" },
  kuwait_fiscal_shock: { en: "Kuwait", ar: "الكويت" },
  oman_port_closure: { en: "Oman Ports", ar: "موانئ عُمان" },
  red_sea_trade_corridor_instability: { en: "Red Sea", ar: "البحر الأحمر" },
  energy_market_volatility_shock: { en: "Energy", ar: "طاقة" },
  regional_liquidity_stress_event: { en: "Liquidity", ar: "سيولة" },
  critical_port_throughput_disruption: { en: "Ports", ar: "موانئ" },
  financial_infrastructure_cyber_disruption: { en: "Fin Cyber", ar: "سيبراني مالي" },
  iran_regional_escalation: { en: "Iran", ar: "إيران" },
};

export function ScenarioSelector({
  activeScenarioId,
  onSelect,
  isLoading = false,
  locale = "en",
}: ScenarioSelectorProps) {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [fetchError, setFetchError] = useState(false);
  const isAr = locale === "ar";

  // Fetch scenario catalog on mount
  useEffect(() => {
    let cancelled = false;
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

    fetch(`${API_BASE}/api/v1/scenarios`)
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        const list = data?.templates ?? data?.data?.templates ?? [];
        if (Array.isArray(list)) {
          setTemplates(list);
        }
      })
      .catch(() => {
        if (!cancelled) setFetchError(true);
      });

    return () => { cancelled = true; };
  }, []);

  // Show top 8 scenarios for the pill bar, sorted by common importance
  const displayTemplates = useMemo(() => {
    if (!templates.length) return [];
    // Prioritize well-known scenarios
    const priority = [
      "hormuz_chokepoint_disruption",
      "saudi_oil_shock",
      "uae_banking_crisis",
      "red_sea_trade_corridor_instability",
      "gcc_cyber_attack",
      "qatar_lng_disruption",
      "regional_liquidity_stress_event",
      "iran_regional_escalation",
    ];
    const ordered: ScenarioTemplate[] = [];
    for (const id of priority) {
      const t = templates.find((t) => t.id === id);
      if (t) ordered.push(t);
    }
    // Add any remaining not in priority list
    for (const t of templates) {
      if (!ordered.find((o) => o.id === t.id)) ordered.push(t);
    }
    return ordered.slice(0, 8);
  }, [templates]);

  if (fetchError || templates.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide py-1" dir={isAr ? "rtl" : "ltr"}>
      {displayTemplates.map((t) => {
        const isActive = t.id === activeScenarioId;
        const short = SHORT_NAMES[t.id];
        const label = short
          ? (isAr ? short.ar : short.en)
          : (isAr ? t.name_ar || t.name : t.name).split(/[\s_]/).slice(0, 2).join(" ");

        return (
          <button
            key={t.id}
            onClick={() => !isActive && !isLoading && onSelect(t.id)}
            disabled={isLoading}
            className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-[10px] font-semibold transition-all whitespace-nowrap ${
              isActive
                ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                : "bg-slate-800/40 text-slate-500 border border-slate-700/30 hover:text-slate-300 hover:border-slate-600/40"
            } ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

export default ScenarioSelector;
