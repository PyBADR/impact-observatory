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

// Enterprise scenario display names — institutional macro-financial terminology
const SHORT_NAMES: Record<string, { en: string; ar: string }> = {
  hormuz_chokepoint_disruption: { en: "Hormuz Disruption", ar: "اضطراب هرمز" },
  hormuz_full_closure: { en: "Hormuz Closure", ar: "إغلاق هرمز" },
  saudi_oil_shock: { en: "Oil Supply Shock", ar: "صدمة إمداد نفطي" },
  uae_banking_crisis: { en: "Banking Stress", ar: "ضغوط بنكية" },
  gcc_cyber_attack: { en: "Cyber Disruption", ar: "اضطراب سيبراني" },
  qatar_lng_disruption: { en: "LNG Disruption", ar: "اضطراب الغاز" },
  bahrain_sovereign_stress: { en: "Sovereign Stress", ar: "ضغوط سيادية" },
  kuwait_fiscal_shock: { en: "Fiscal Shock", ar: "صدمة مالية" },
  oman_port_closure: { en: "Port Disruption", ar: "اضطراب الموانئ" },
  red_sea_trade_corridor_instability: { en: "Red Sea Corridor", ar: "ممر البحر الأحمر" },
  energy_market_volatility_shock: { en: "Energy Volatility", ar: "تقلب الطاقة" },
  regional_liquidity_stress_event: { en: "Liquidity Stress", ar: "ضغوط سيولة" },
  critical_port_throughput_disruption: { en: "Port Throughput", ar: "طاقة الموانئ" },
  financial_infrastructure_cyber_disruption: { en: "Financial Cyber", ar: "سيبراني مالي" },
  iran_regional_escalation: { en: "Regional Escalation", ar: "تصعيد إقليمي" },
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

  // Fetch scenario catalog on mount (relative URL → Next.js rewrites → backend)
  useEffect(() => {
    let cancelled = false;

    fetch("/api/v1/scenarios")
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
                ? "bg-io-accent/15 text-io-accent border border-io-accent/30"
                : "bg-io-muted text-io-secondary border border-io-border-muted hover:text-io-primary hover:border-io-border-soft"
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
