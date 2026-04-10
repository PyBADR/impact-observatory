/**
 * Impact Observatory | مرصد الأثر — Dashboard Mapping (v4 §18.2)
 *
 * Bilingual scenario presentation metadata and dashboard card priority order.
 * scenarioPresentationMap: 8 entries matching backend catalog IDs.
 * dashboardPriorityOrder: McKinsey pyramid — situation → complication → resolution → detail.
 */

export type DashboardCardKey =
  | "headline_loss"
  | "peak_day"
  | "time_to_first_failure"
  | "business_severity"
  | "executive_status"
  | "financial_impact"
  | "banking_stress"
  | "insurance_stress"
  | "fintech_stress"
  | "decision_actions"
  | "business_impact_timeline"
  | "regulatory_timeline";

export type ScenarioDomain = "MARITIME" | "ENERGY" | "FINANCIAL" | "CYBER" | "AVIATION" | "TRADE";

export type ScenarioPresentation = {
  scenarioId: string;
  titleAr: string;
  titleEn: string;
  subtitleAr: string;
  subtitleEn: string;
  severityLabel: string;
  headlineLossLabel: string;
  domain: ScenarioDomain;
  affectedSectors: string[];
  triggerType: string;
};

export const scenarioPresentationMap: Record<string, ScenarioPresentation> = {
  hormuz_chokepoint_disruption: {
    scenarioId: "hormuz_chokepoint_disruption",
    titleAr: "تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)",
    titleEn: "Strategic Maritime Chokepoint Disruption",
    subtitleAr:
      "أثر متوقع على التدفقات التجارية، تكاليف الطاقة، والسيولة القطاعية",
    subtitleEn:
      "Expected impact on trade flows, energy costs, and sector liquidity",
    severityLabel: "80%",
    headlineLossLabel: "$3.2B",
    domain: "MARITIME",
    affectedSectors: ["Banking", "Insurance", "Fintech", "Energy"],
    triggerType: "geopolitical",
  },
  red_sea_trade_corridor_instability: {
    scenarioId: "red_sea_trade_corridor_instability",
    titleAr: "اضطراب ممر التجارة في البحر الأحمر",
    titleEn: "Red Sea Trade Corridor Instability",
    subtitleAr:
      "إعادة توجيه الشحن، ارتفاع التكاليف، وضغط على سلاسل الإمداد",
    subtitleEn: "Shipping rerouting, rising costs, and supply chain pressure",
    severityLabel: "70%",
    headlineLossLabel: "$1.8B",
    domain: "MARITIME",
    affectedSectors: ["Banking", "Insurance", "Fintech"],
    triggerType: "geopolitical",
  },
  energy_market_volatility_shock: {
    scenarioId: "energy_market_volatility_shock",
    titleAr: "صدمة تقلبات أسواق الطاقة",
    titleEn: "Energy Market Volatility Shock",
    subtitleAr: "أثر على الخزينة، التسعير، والتحوط والسيولة",
    subtitleEn: "Impact on treasury, pricing, hedging, and liquidity",
    severityLabel: "80%",
    headlineLossLabel: "$4.5B",
    domain: "ENERGY",
    affectedSectors: ["Banking", "Insurance", "Fintech", "Energy"],
    triggerType: "market",
  },
  critical_port_operations_disruption: {
    scenarioId: "critical_port_operations_disruption",
    titleAr: "تعطّل عمليات ميناء حيوي",
    titleEn: "Critical Port Operations Disruption",
    subtitleAr: "اختناق لوجستي وتأخر تدفقات التجارة وارتفاع التكاليف",
    subtitleEn: "Logistics bottleneck, trade delays, and rising costs",
    severityLabel: "60%",
    headlineLossLabel: "$1.5B",
    domain: "MARITIME",
    affectedSectors: ["Banking", "Insurance", "Fintech"],
    triggerType: "infrastructure",
  },
  regional_airspace_disruption: {
    scenarioId: "regional_airspace_disruption",
    titleAr: "سيناريو تعطّل المجال الجوي الإقليمي",
    titleEn: "Regional Airspace Disruption Scenario",
    subtitleAr: "تأخر الشحن الجوي وتعطل السفر وأثر السياحة",
    subtitleEn: "Air cargo delays, travel disruption, and tourism impact",
    severityLabel: "60%",
    headlineLossLabel: "$1.2B",
    domain: "AVIATION",
    affectedSectors: ["Insurance", "Fintech"],
    triggerType: "infrastructure",
  },
  cross_border_sanctions_escalation: {
    scenarioId: "cross_border_sanctions_escalation",
    titleAr: "تصاعد العقوبات العابرة للحدود",
    titleEn: "Cross-Border Sanctions Escalation",
    subtitleAr:
      "تكاليف امتثال أعلى، إعادة توجيه التجارة، وتعرضات بنكية",
    subtitleEn:
      "Higher compliance costs, trade rerouting, and banking exposure",
    severityLabel: "70%",
    headlineLossLabel: "$2.8B",
    domain: "TRADE",
    affectedSectors: ["Banking", "Fintech"],
    triggerType: "regulatory",
  },
  regional_liquidity_stress_event: {
    scenarioId: "regional_liquidity_stress_event",
    titleAr: "أزمة سيولة مصرفية إقليمية",
    titleEn: "Regional Liquidity Stress",
    subtitleAr: "ضغط على السيولة، التمويل، وحدود رأس المال",
    subtitleEn: "Pressure on liquidity, funding, and capital buffers",
    severityLabel: "70%",
    headlineLossLabel: "$2.1B",
    domain: "FINANCIAL",
    affectedSectors: ["Banking", "Insurance", "Fintech"],
    triggerType: "systemic",
  },
  financial_infrastructure_cyber_disruption: {
    scenarioId: "financial_infrastructure_cyber_disruption",
    titleAr: "تعطّل البنية المالية نتيجة هجوم سيبراني",
    titleEn: "Financial Infrastructure Cyber Disruption",
    subtitleAr: "تعطل المدفوعات، مخاطر الاحتيال، وتأخر التسوية",
    subtitleEn: "Payment disruption, fraud risk, and settlement delay",
    severityLabel: "60%",
    headlineLossLabel: "$0.9B",
    domain: "CYBER",
    affectedSectors: ["Banking", "Fintech"],
    triggerType: "cyber",
  },
};

/**
 * Dashboard card rendering order — McKinsey pyramid principle:
 *   Cards 1-5:  Situation + Complication (CEO's first 5 questions)
 *   Card  6:    Financial bridge
 *   Cards 7-9:  Sector drill-down (Banking → Insurance → Fintech)
 *   Card  10:   Resolution (decision actions)
 *   Cards 11-12: Forward-looking timelines
 */
export const dashboardPriorityOrder: DashboardCardKey[] = [
  "headline_loss",
  "peak_day",
  "time_to_first_failure",
  "business_severity",
  "executive_status",
  "financial_impact",
  "banking_stress",
  "insurance_stress",
  "fintech_stress",
  "decision_actions",
  "business_impact_timeline",
  "regulatory_timeline",
];

/**
 * Helper: get scenario presentation by ID with language fallback.
 */
export function getScenarioPresentation(
  scenarioId: string,
  language: "en" | "ar" = "en"
): { title: string; subtitle: string; severity: string; loss: string } | null {
  const entry = scenarioPresentationMap[scenarioId];
  if (!entry) return null;
  return {
    title: language === "ar" ? entry.titleAr : entry.titleEn,
    subtitle: language === "ar" ? entry.subtitleAr : entry.subtitleEn,
    severity: entry.severityLabel,
    loss: entry.headlineLossLabel,
  };
}

/**
 * All catalog scenario IDs in catalog order.
 */
export const catalogScenarioIds = Object.keys(scenarioPresentationMap);
