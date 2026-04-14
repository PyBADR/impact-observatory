"use client";

/**
 * ScenarioLibrary — Full-page scenario catalog with grid layout.
 *
 * Fetches scenario templates from /api/v1/scenarios on mount.
 * Falls back to hardcoded catalog if API fails.
 * Displays scenarios in a responsive grid with domain badges,
 * descriptions, impact sectors, and run buttons.
 *
 * Design: white enterprise institutional theme with light colors,
 * bilingual English/Arabic support throughout.
 */

import { useState, useEffect, useMemo } from "react";

interface ScenarioTemplate {
  id: string;
  label_en: string;
  label_ar: string;
  sectors_affected: string[];
  base_loss_usd?: number;
}

interface ScenarioLibraryProps {
  onSelectScenario: (templateId: string) => void;
  isLoading?: boolean;
  locale?: "en" | "ar";
}

interface ScenarioCard extends ScenarioTemplate {
  domain: "MARITIME" | "ENERGY" | "CYBER" | "LIQUIDITY" | "REGULATORY";
  description_en: string;
  description_ar: string;
  severity: "CRITICAL" | "HIGH" | "ELEVATED" | "GUARDED";
  impactedSectors: string[];
}

// Hardcoded fallback catalog with full details
const FALLBACK_CATALOG: ScenarioCard[] = [
  {
    id: "hormuz_chokepoint_disruption",
    label_en: "Strait of Hormuz Disruption",
    label_ar: "تعطل مضيق هرمز",
    domain: "MARITIME",
    severity: "HIGH",
    description_en:
      "Partial blockage of the Strait of Hormuz reduces critical oil transit capacity. 15-20% of global crude passes through this chokepoint daily.",
    description_ar:
      "إغلاق جزئي لمضيق هرمز يقلل من قدرة نقل النفط الحرجة. يمر 15-20% من الخام العالمي يومياً عبر هذه النقطة الضيقة.",
    sectors_affected: ["energy", "shipping", "finance"],
    impactedSectors: ["Energy", "Shipping", "Finance"],
    base_loss_usd: 45000000000,
  },
  {
    id: "hormuz_full_closure",
    label_en: "Full Hormuz Closure (Extreme)",
    label_ar: "إغلاق هرمز الكامل (متطرف)",
    domain: "MARITIME",
    severity: "CRITICAL",
    description_en:
      "Complete closure of the Strait of Hormuz blocks ~30% of global maritime oil trade. Most severe supply shock scenario.",
    description_ar:
      "إغلاق كامل لمضيق هرمز يحجب حوالي 30% من تجارة النفط البحرية العالمية. أشد سيناريو صدمة الإمدادات.",
    sectors_affected: ["energy", "shipping", "finance"],
    impactedSectors: ["Energy", "Shipping", "Finance"],
    base_loss_usd: 150000000000,
  },
  {
    id: "red_sea_trade_corridor_instability",
    label_en: "Red Sea Trade Corridor Instability",
    label_ar: "عدم استقرار ممر تجارة البحر الأحمر",
    domain: "MARITIME",
    severity: "ELEVATED",
    description_en:
      "Shipping disruptions in Red Sea and Suez Canal increase transit times and insurance premiums. 12% of global trade transits this route.",
    description_ar:
      "تعطل الشحن في البحر الأحمر وقناة السويس يزيد أوقات العبور وأقساط التأمين. يمر 12% من التجارة العالمية عبر هذا الطريق.",
    sectors_affected: ["shipping", "trade", "insurance"],
    impactedSectors: ["Shipping", "Trade", "Insurance"],
    base_loss_usd: 28000000000,
  },
  {
    id: "financial_infrastructure_cyber_disruption",
    label_en: "Financial Infrastructure Cyber Attack",
    label_ar: "هجوم سيبراني على البنية التحتية المالية",
    domain: "CYBER",
    severity: "CRITICAL",
    description_en:
      "Coordinated cyber attack on regional financial clearing systems causes settlement delays and liquidity stress across banking sector.",
    description_ar:
      "هجوم سيبراني منسق على أنظمة التسوية المالية الإقليمية يسبب تأخير التسوية والضغط على السيولة في القطاع المصرفي.",
    sectors_affected: ["finance", "banking", "payments"],
    impactedSectors: ["Finance", "Banking", "Payments"],
    base_loss_usd: 92000000000,
  },
  {
    id: "regional_liquidity_stress_event",
    label_en: "Regional Liquidity Stress Event",
    label_ar: "حدث ضغط السيولة الإقليمي",
    domain: "LIQUIDITY",
    severity: "HIGH",
    description_en:
      "Cross-border liquidity freeze tightens credit conditions. Funding costs spike, interbank market seizes, currency volatility surges.",
    description_ar:
      "تجميد السيولة عبر الحدود يشدد شروط الائتمان. تقفز تكاليف التمويل، توقف السوق البنكي، قفز تقلب العملات.",
    sectors_affected: ["finance", "banking", "currency"],
    impactedSectors: ["Finance", "Banking", "Currency"],
    base_loss_usd: 67000000000,
  },
  {
    id: "energy_market_volatility_shock",
    label_en: "Energy Market Volatility Shock",
    label_ar: "صدمة تقلبات سوق الطاقة",
    domain: "ENERGY",
    severity: "ELEVATED",
    description_en:
      "Geopolitical tensions cause oil and gas price spikes. Energy-dependent economies face inflation and balance-of-payment strain.",
    description_ar:
      "التوترات الجيوسياسية تسبب ارتفاع أسعار النفط والغاز. تواجه الاقتصادات المعتمدة على الطاقة التضخم وضغط ميزان المدفوعات.",
    sectors_affected: ["energy", "utilities", "transport"],
    impactedSectors: ["Energy", "Utilities", "Transport"],
    base_loss_usd: 38000000000,
  },
  {
    id: "critical_port_throughput_disruption",
    label_en: "Critical Port Throughput Disruption",
    label_ar: "تعطل إنتاجية الميناء الحرج",
    domain: "MARITIME",
    severity: "HIGH",
    description_en:
      "Multiple major port closures (Jebel Ali, King Abdulaziz) reduce container throughput by 40%. Supply chain bottlenecks ripple through region.",
    description_ar:
      "إغلاق عدة موانئ رئيسية (جبل علي، الملك عبدالعزيز) يقلل إنتاجية الحاويات بنسبة 40%. اختناقات سلسلة التوريد تنتشر في المنطقة.",
    sectors_affected: ["shipping", "logistics", "retail"],
    impactedSectors: ["Shipping", "Logistics", "Retail"],
    base_loss_usd: 55000000000,
  },
  {
    id: "saudi_oil_shock",
    label_en: "Saudi Oil Production Shock",
    label_ar: "صدمة الإنتاج النفطي السعودي",
    domain: "ENERGY",
    severity: "CRITICAL",
    description_en:
      "Major disruption to Saudi Aramco production (cyber or military) cuts 10+ million bbl/day. Global oil shock with cascading financial impact.",
    description_ar:
      "تعطل كبير لإنتاج أرامكو السعودية (سيبراني أو عسكري) يقطع 10+ مليون برميل/يوم. صدمة نفطية عالمية بأثر مالي متسلسل.",
    sectors_affected: ["energy", "finance", "transport"],
    impactedSectors: ["Energy", "Finance", "Transport"],
    base_loss_usd: 185000000000,
  },
  {
    id: "iran_regional_escalation",
    label_en: "Iran Regional Escalation",
    label_ar: "التصعيد الإقليمي الإيراني",
    domain: "REGULATORY",
    severity: "CRITICAL",
    description_en:
      "Geopolitical escalation triggers military conflict, regional instability. Oil supply threatened, sanctions tighten, FX markets stress.",
    description_ar:
      "التصعيد الجيوسياسي يشعل نزاع عسكري وعدم استقرار إقليمي. إمدادات النفط مهددة، العقوبات تشتد، أسواق الصرف تضغط.",
    sectors_affected: ["energy", "defense", "finance"],
    impactedSectors: ["Energy", "Defense", "Finance"],
    base_loss_usd: 220000000000,
  },
  {
    id: "gcc_cyber_attack",
    label_en: "GCC Cyber Attack",
    label_ar: "هجوم سيبراني على دول الخليج",
    domain: "CYBER",
    severity: "HIGH",
    description_en:
      "Coordinated cyber attack on critical infrastructure across GCC states. Power grids and communications disrupted, financial markets impacted.",
    description_ar:
      "هجوم سيبراني منسق على البنية التحتية الحيوية عبر دول الخليج. شبكات الكهرباء والاتصالات معطلة، الأسواق المالية متأثرة.",
    sectors_affected: ["cyber", "energy", "finance"],
    impactedSectors: ["Energy", "Finance", "Technology"],
    base_loss_usd: 75000000000,
  },
  {
    id: "qatar_lng_disruption",
    label_en: "Qatar LNG Export Disruption",
    label_ar: "تعطل صادرات الغاز القطري",
    domain: "ENERGY",
    severity: "HIGH",
    description_en:
      "Major disruption to Qatar LNG facilities reduces global liquefied natural gas supply. Energy prices spike, alternative suppliers strained.",
    description_ar:
      "تعطل كبير في منشآت الغاز الطبيعي المسال القطري يقلل من الإمدادات العالمية. ارتفاع أسعار الطاقة، الموردون البدليون مرهقون.",
    sectors_affected: ["energy", "shipping", "utilities"],
    impactedSectors: ["Energy", "Utilities", "Shipping"],
    base_loss_usd: 85000000000,
  },
  {
    id: "uae_banking_crisis",
    label_en: "UAE Banking Sector Crisis",
    label_ar: "أزمة القطاع المصرفي الإماراتي",
    domain: "LIQUIDITY",
    severity: "CRITICAL",
    description_en:
      "Systemic banking sector stress in UAE triggers credit freeze and deposit runs. Regional financial contagion spreads across GCC.",
    description_ar:
      "ضغط القطاع المصرفي النظامي في الإمارات يؤدي إلى تجميد الائتمان وهروب الودائع. العدوى المالية الإقليمية تنتشر عبر الخليج.",
    sectors_affected: ["banking", "finance", "currency"],
    impactedSectors: ["Finance", "Banking", "Currency"],
    base_loss_usd: 120000000000,
  },
  {
    id: "bahrain_sovereign_stress",
    label_en: "Bahrain Sovereign Fiscal Stress",
    label_ar: "ضغط مالي سيادي بحريني",
    domain: "LIQUIDITY",
    severity: "ELEVATED",
    description_en:
      "Fiscal consolidation pressures and debt servicing challenges stress Bahrain's sovereign creditworthiness. Regional confidence in small economies shaken.",
    description_ar:
      "ضغوط تقليص الإنفاق المالي والتحديات في خدمة الديون تضغط على جدارة بحرين الائتمانية. الثقة الإقليمية في الاقتصادات الصغيرة تتزعزع.",
    sectors_affected: ["finance", "currency", "banking"],
    impactedSectors: ["Finance", "Banking", "Currency"],
    base_loss_usd: 18000000000,
  },
  {
    id: "kuwait_fiscal_shock",
    label_en: "Kuwait Oil Revenue Shock",
    label_ar: "صدمة إيرادات النفط الكويتية",
    domain: "ENERGY",
    severity: "HIGH",
    description_en:
      "Unexpected production decline or demand collapse reduces Kuwait's oil revenue by 40%. Fiscal reserves depleted, budget deficits widen.",
    description_ar:
      "انخفاض الإنتاج غير المتوقع أو انهيار الطلب يقلل إيرادات النفط الكويتي بنسبة 40%. احتياطيات الموازنة نضبت، العجوزات تتسع.",
    sectors_affected: ["energy", "finance", "currency"],
    impactedSectors: ["Energy", "Finance", "Currency"],
    base_loss_usd: 42000000000,
  },
  {
    id: "oman_port_closure",
    label_en: "Oman Port Closure",
    label_ar: "إغلاق موانئ عمان",
    domain: "MARITIME",
    severity: "ELEVATED",
    description_en:
      "Closure of Salalah and Sohar ports disrupts logistics hub for Indian Ocean trade. Regional shipping routes redirected, costs increase.",
    description_ar:
      "إغلاق موانئ صلالة وصحار يعطل مركز الخدمات اللوجستية لتجارة المحيط الهندي. إعادة توجيه طرق الشحن الإقليمية، زيادة التكاليف.",
    sectors_affected: ["shipping", "logistics", "trade"],
    impactedSectors: ["Shipping", "Logistics", "Trade"],
    base_loss_usd: 22000000000,
  },
];

// Domain color mapping (light enterprise theme)
const DOMAIN_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  MARITIME: {
    bg: "bg-cyan-50",
    text: "text-cyan-700",
    border: "border-cyan-200",
  },
  ENERGY: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
  },
  CYBER: {
    bg: "bg-red-50",
    text: "text-red-700",
    border: "border-red-200",
  },
  LIQUIDITY: {
    bg: "bg-io-accent/10",
    text: "text-io-accent",
    border: "border-io-accent/20",
  },
  REGULATORY: {
    bg: "bg-purple-50",
    text: "text-purple-700",
    border: "border-purple-200",
  },
};

// Severity level styling (light enterprise theme)
const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-50 text-red-700 border-red-200",
  HIGH: "bg-orange-50 text-orange-700 border-orange-200",
  ELEVATED: "bg-amber-50 text-amber-700 border-amber-200",
  GUARDED: "bg-io-status-guarded/10 text-io-status-guarded border-io-status-guarded/20",
};

// Bilingual labels for all sectors
const SECTOR_LABELS: Record<string, { en: string; ar: string }> = {
  energy: { en: "Energy", ar: "الطاقة" },
  shipping: { en: "Shipping", ar: "الشحن" },
  finance: { en: "Finance", ar: "التمويل" },
  trade: { en: "Trade", ar: "التجارة" },
  insurance: { en: "Insurance", ar: "التأمين" },
  banking: { en: "Banking", ar: "البنوك" },
  payments: { en: "Payments", ar: "الدفع" },
  currency: { en: "Currency", ar: "العملة" },
  utilities: { en: "Utilities", ar: "المرافق" },
  transport: { en: "Transport", ar: "النقل" },
  logistics: { en: "Logistics", ar: "الخدمات اللوجستية" },
  retail: { en: "Retail", ar: "البيع بالتجزئة" },
  defense: { en: "Defense", ar: "الدفاع" },
  cyber: { en: "Technology", ar: "التكنولوجيا" },
};

export function ScenarioLibrary(
  {
  onSelectScenario,
  isLoading = false,
  locale = "en",
}: ScenarioLibraryProps
) {
  const [scenarios, setScenarios] = useState<ScenarioCard[]>([]);
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
        if (Array.isArray(list) && list.length > 0) {
          // Map API response to ScenarioCard format
          const mapped: ScenarioCard[] = list.map((t: any) => {
            const fallback = FALLBACK_CATALOG.find((f) => f.id === t.id);
            return {
              id: t.id,
              label_en: t.label_en || fallback?.label_en || t.name || "",
              label_ar: t.label_ar || fallback?.label_ar || t.name_ar || "",
              sectors_affected: t.sectors_affected || fallback?.sectors_affected || [],
              domain: fallback?.domain || "MARITIME",
              severity: fallback?.severity || "GUARDED",
              description_en: fallback?.description_en || "Scenario impact analysis",
              description_ar: fallback?.description_ar || "تحليل تأثير السيناريو",
              impactedSectors: fallback?.impactedSectors || [],
              base_loss_usd: t.base_loss_usd || fallback?.base_loss_usd,
            };
          });
          setScenarios(mapped);
        } else {
          // Fall back to hardcoded
          setScenarios(FALLBACK_CATALOG);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFetchError(true);
          setScenarios(FALLBACK_CATALOG);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const displayScenarios = useMemo(() => {
    // Sort by severity (critical first)
    const severityOrder = { CRITICAL: 0, HIGH: 1, ELEVATED: 2, GUARDED: 3 };
    return [...scenarios].sort(
      (a, b) =>
        (severityOrder[a.severity] || 999) - (severityOrder[b.severity] || 999)
    );
  }, [scenarios]);

  const formatCurrency = (value?: number) => {
    if (!value) return "—";
    const billions = value / 1e9;
    return `$${billions.toFixed(1)}B`;
  };

  if (scenarios.length === 0 && !fetchError) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-50">
        <div className="text-slate-600">
          {isAr ? "جاري التحميل..." : "Loading..."}
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen bg-slate-50 px-6 py-10 lg:px-8"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-3xl lg:text-4xl font-bold text-slate-900 mb-3">
          {isAr ? "مكتبة السيناريوهات" : "Scenario Library"}
        </h1>
        <p className="text-slate-600 text-lg max-w-2xl">
          {isAr
            ? "استكشف جميع السيناريوهات المتاحة وآثارها المالية والعملياتية على منطقة مجلس التعاون الخليجي."
            : "Explore all available scenarios and their financial and operational impact on the GCC region."}
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-max">
        {displayScenarios.map((scenario) => {
          const domainColor = DOMAIN_COLORS[scenario.domain];
          const severityColor = SEVERITY_COLORS[scenario.severity];
          const label = isAr ? scenario.label_ar : scenario.label_en;
          const description = isAr
            ? scenario.description_ar
            : scenario.description_en;

          return (
            <div
              key={scenario.id}
              className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-md transition-shadow flex flex-col gap-4 shadow-sm"
            >
              {/* Header with domain badge and severity */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-slate-900 mb-2 leading-snug">
                    {label}
                  </h2>
                  <div
                    className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-md border text-xs font-semibold ${domainColor.bg} ${domainColor.text} ${domainColor.border}`}
                  >
                    <span className="w-2 h-2 rounded-full bg-current opacity-70"></span>
                    {scenario.domain}
                  </div>
                </div>
                <div
                  className={`flex-shrink-0 px-2 py-1 rounded text-xs font-semibold border whitespace-nowrap ${severityColor}`}
                >
                  {scenario.severity}
                </div>
              </div>

              {/* Description */}
              <p className="text-slate-600 text-sm leading-relaxed">
                {description}
              </p>

              {/* Impacted Sectors Pills */}
              <div className="flex flex-wrap gap-2">
                {scenario.impactedSectors.map((sector) => {
                  const sectorLabel = isAr
                    ? SECTOR_LABELS[sector.toLowerCase()]?.ar || sector
                    : SECTOR_LABELS[sector.toLowerCase()]?.en || sector;
                  return (
                    <span
                      key={sector}
                      className="px-2.5 py-1 bg-slate-100 text-slate-600 border border-slate-200 rounded text-xs font-medium"
                    >
                      {sectorLabel}
                    </span>
                  );
                })}
              </div>

              {/* Estimated Loss */}
              <div className="pt-2 border-t border-slate-200">
                <div className="text-xs text-slate-600 mb-1">
                  {isAr ? "الخسارة المقدرة" : "Estimated Loss"}
                </div>
                <div className="text-lg font-bold text-red-600">
                  {formatCurrency(scenario.base_loss_usd)}
                </div>
              </div>

              {/* Run Button */}
              <button
                onClick={() => onSelectScenario(scenario.id)}
                disabled={isLoading}
                className="mt-auto px-4 py-2.5 bg-io-accent hover:bg-io-accent-hover text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {isLoading
                  ? isAr
                    ? "جاري التشغيل..."
                    : "Running..."
                  : isAr
                    ? "تشغيل السيناريو"
                    : "Run Scenario"}
              </button>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {displayScenarios.length === 0 && (
        <div className="flex items-center justify-center h-96 text-slate-600">
          {isAr ? "لم يتم العثور على سيناريوهات" : "No scenarios found"}
        </div>
      )}
    </div>
  );
}

export default ScenarioLibrary;
