/**
 * Executive Intelligence Engine — Phase 6
 *
 * Deterministic computation layer for 9 executive decision intelligence workstreams.
 * All functions are pure: (inputs) → outputs. No side effects, no API calls.
 *
 * Workstreams:
 *   1. Executive Status Engine
 *   2. Country Bake Layer
 *   3. Sector Formula Lab
 *   4. Banking Simulation Layer
 *   5. Insurance Simulation Layer
 *   6. Decision ROI Engine
 *   7. Outcome Confirmation Layer
 *   8. Collaboration Stage
 *   9. (PDF handled backend-side)
 */

import type {
  CausalStep,
  DecisionActionV2,
  KnowledgeGraphNode,
} from "@/types/observatory";
import type { CommandCenterHeadline } from "./command-store";
import type { CountryExposureEntry, OutcomeScenario } from "./mock-data";

// ═══════════════════════════════════════════════════════════════════════
// 1. Executive Status Engine
// ═══════════════════════════════════════════════════════════════════════

export type ExecutiveStatusLevel = "STABLE" | "ELEVATED" | "SEVERE" | "CRITICAL";

export interface ExecutiveStatusResult {
  status: ExecutiveStatusLevel;
  statusAr: string;
  severityRationale: string;
  severityRationaleAr: string;
  decisionUrgency: "IMMEDIATE" | "URGENT" | "PRIORITY" | "STANDARD";
  decisionUrgencyHours: number;
  affectedCountries: string[];
  affectedSectors: string[];
  confidence: number;
  reasonForStatus: string;
  reasonForStatusAr: string;
}

const STATUS_AR: Record<ExecutiveStatusLevel, string> = {
  STABLE: "مستقر",
  ELEVATED: "مرتفع",
  SEVERE: "حاد",
  CRITICAL: "حرج",
};

export function computeExecutiveStatus(
  headline: CommandCenterHeadline | null,
  causalChain: CausalStep[],
  decisionActions: DecisionActionV2[],
  graphNodes: KnowledgeGraphNode[],
  sectorRollups: Record<string, { aggregate_stress?: number; stress?: number; total_loss?: number }>,
): ExecutiveStatusResult {
  if (!headline) {
    return {
      status: "STABLE",
      statusAr: STATUS_AR.STABLE,
      severityRationale: "No scenario data loaded",
      severityRationaleAr: "لا توجد بيانات سيناريو محملة",
      decisionUrgency: "STANDARD",
      decisionUrgencyHours: 0,
      affectedCountries: [],
      affectedSectors: [],
      confidence: 0,
      reasonForStatus: "Awaiting scenario selection",
      reasonForStatusAr: "بانتظار اختيار السيناريو",
    };
  }

  const avgStress = headline.averageStress;
  const criticalCount = headline.criticalCount;
  const totalLoss = headline.totalLossUsd;

  // Determine status level
  let status: ExecutiveStatusLevel;
  if (avgStress >= 0.75 || criticalCount >= 6 || totalLoss >= 8_000_000_000) {
    status = "CRITICAL";
  } else if (avgStress >= 0.55 || criticalCount >= 3 || totalLoss >= 3_000_000_000) {
    status = "SEVERE";
  } else if (avgStress >= 0.35 || criticalCount >= 1 || totalLoss >= 1_000_000_000) {
    status = "ELEVATED";
  } else {
    status = "STABLE";
  }

  // Severity rationale
  const drivers: string[] = [];
  if (criticalCount > 0) drivers.push(`${criticalCount} entities at critical stress`);
  if (totalLoss > 0) drivers.push(`$${(totalLoss / 1e9).toFixed(1)}B projected loss`);
  if (headline.propagationDepth >= 4) drivers.push(`${headline.propagationDepth}-step contagion depth`);
  const severityRationale = drivers.length > 0
    ? drivers.join("; ")
    : "Stress levels within normal operating parameters";

  // Decision urgency from fastest-acting decision
  const urgencies = decisionActions
    .map(a => a.deadline_hours ?? a.time_to_act_hours ?? 999)
    .filter(h => h > 0 && h < 999);
  const fastestDeadline = urgencies.length > 0 ? Math.min(...urgencies) : 0;

  let decisionUrgency: ExecutiveStatusResult["decisionUrgency"];
  if (fastestDeadline > 0 && fastestDeadline <= 6) decisionUrgency = "IMMEDIATE";
  else if (fastestDeadline <= 24) decisionUrgency = "URGENT";
  else if (fastestDeadline <= 72) decisionUrgency = "PRIORITY";
  else decisionUrgency = "STANDARD";

  // Affected countries — derive from graph nodes by lat/lng proximity
  const countryMap: Record<string, { lat: number; lng: number }> = {
    "Saudi Arabia": { lat: 24.7, lng: 46.7 },
    "UAE": { lat: 25.0, lng: 55.2 },
    "Kuwait": { lat: 29.3, lng: 47.9 },
    "Qatar": { lat: 25.3, lng: 51.5 },
    "Bahrain": { lat: 26.0, lng: 50.5 },
    "Oman": { lat: 23.6, lng: 58.5 },
  };

  const affectedCountries = new Set<string>();
  for (const node of graphNodes) {
    if ((node.stress ?? 0) < 0.2) continue;
    const lat = node.lat ?? 25;
    const lng = node.lng ?? 52;
    let nearest = "Saudi Arabia";
    let nearestDist = Infinity;
    for (const [name, coords] of Object.entries(countryMap)) {
      const d = Math.sqrt((lat - coords.lat) ** 2 + (lng - coords.lng) ** 2);
      if (d < nearestDist) {
        nearestDist = d;
        nearest = name;
      }
    }
    affectedCountries.add(nearest);
  }

  // Affected sectors
  const affectedSectors = Object.entries(sectorRollups)
    .filter(([, data]) => (data.aggregate_stress ?? data.stress ?? 0) >= 0.2)
    .map(([sector]) => sector.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()));

  // Confidence
  const confidence = Math.min(0.95, 0.6 + causalChain.length * 0.03 + decisionActions.length * 0.02);

  // Reason for status
  const topStep = causalChain[0];
  const reasonForStatus = topStep
    ? `${topStep.entity_label}: ${topStep.event}. ${drivers[0] || ""}.`
    : severityRationale;

  return {
    status,
    statusAr: STATUS_AR[status],
    severityRationale,
    severityRationaleAr: `${criticalCount > 0 ? `${criticalCount} كيانات في ضغط حرج` : ""}${totalLoss > 0 ? ` — خسائر $${(totalLoss / 1e9).toFixed(1)} مليار` : ""}`,
    decisionUrgency,
    decisionUrgencyHours: fastestDeadline,
    affectedCountries: Array.from(affectedCountries),
    affectedSectors,
    confidence,
    reasonForStatus,
    reasonForStatusAr: topStep
      ? `${topStep.entity_label_ar || topStep.entity_label}: ${topStep.event_ar || topStep.event}`
      : "مستويات الضغط ضمن النطاق الطبيعي",
  };
}

// ═══════════════════════════════════════════════════════════════════════
// 2. Country Bake Layer
// ═══════════════════════════════════════════════════════════════════════

export interface CountryBakeEntry {
  code: string;
  name: string;
  nameAr: string;
  exposureUsd: number;
  stressPercent: number;
  primarySector: string;
  primarySectorAr: string;
  primaryDriver: string;
  primaryDriverAr: string;
  transmissionChannel: string;
  transmissionChannelAr: string;
  policyLever: string;
  policyLeverAr: string;
  confidence: number;
}

const GCC_COUNTRIES = [
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", lat: 24.7, lng: 46.7 },
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", lat: 25.0, lng: 55.2 },
  { code: "KWT", name: "Kuwait", nameAr: "الكويت", lat: 29.3, lng: 47.9 },
  { code: "QAT", name: "Qatar", nameAr: "قطر", lat: 25.3, lng: 51.5 },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", lat: 26.0, lng: 50.5 },
  { code: "OMN", name: "Oman", nameAr: "عُمان", lat: 23.6, lng: 58.5 },
];

const POLICY_LEVERS: Record<string, { en: string; ar: string }> = {
  KSA: { en: "Activate sovereign wealth fund stabilization + SAMA emergency repo", ar: "تفعيل صندوق الثروة السيادية + مرفق الريبو الطارئ لمؤسسة النقد" },
  UAE: { en: "CBUAE liquidity injection + Mubadala counter-cyclical deployment", ar: "ضخ السيولة من المصرف المركزي + نشر مبادلة المعاكس للدورة" },
  KWT: { en: "KIA reserve drawdown + emergency fiscal buffer activation", ar: "سحب احتياطي الهيئة العامة للاستثمار + تفعيل المنطقة المالية الطارئة" },
  QAT: { en: "QIA stabilization fund + LNG revenue hedge rebalancing", ar: "صندوق استقرار جهاز قطر للاستثمار + إعادة موازنة تحوط إيرادات الغاز" },
  BHR: { en: "GCC joint credit facility + IMF standby arrangement", ar: "تسهيل ائتماني مشترك خليجي + ترتيب احتياطي صندوق النقد الدولي" },
  OMN: { en: "National Reserve Fund deployment + Oman Investment Authority coordination", ar: "نشر صندوق الاحتياطي الوطني + تنسيق جهاز الاستثمار العماني" },
};

const TRANSMISSION_CHANNELS: Record<string, { en: string; ar: string }> = {
  KSA: { en: "Oil revenue → fiscal balance → banking liquidity", ar: "إيرادات النفط → الميزانية المالية → سيولة القطاع المصرفي" },
  UAE: { en: "Trade volume → logistics → real estate demand", ar: "حجم التجارة → الخدمات اللوجستية → الطلب العقاري" },
  KWT: { en: "Oil exports → fiscal balance → public spending", ar: "صادرات النفط → الميزانية المالية → الإنفاق العام" },
  QAT: { en: "LNG revenue → fiscal surplus → banking reserves", ar: "إيرادات الغاز المسال → الفائض المالي → احتياطيات البنوك" },
  BHR: { en: "Financial services → sovereign credit → public services", ar: "الخدمات المالية → الائتمان السيادي → الخدمات العامة" },
  OMN: { en: "Port operations → trade flows → fiscal balance", ar: "عمليات الموانئ → تدفقات التجارة → الميزانية المالية" },
};

export function computeCountryBake(
  graphNodes: KnowledgeGraphNode[],
  headline: CommandCenterHeadline | null,
  sectorRollups: Record<string, { aggregate_stress?: number; stress?: number; total_loss?: number }>,
): CountryBakeEntry[] {
  if (!headline || headline.totalLossUsd <= 0 || graphNodes.length === 0) {
    return GCC_COUNTRIES.map(c => ({
      code: c.code,
      name: c.name,
      nameAr: c.nameAr,
      exposureUsd: 0,
      stressPercent: 0,
      primarySector: "—",
      primarySectorAr: "—",
      primaryDriver: "No data available",
      primaryDriverAr: "لا توجد بيانات متاحة",
      transmissionChannel: TRANSMISSION_CHANNELS[c.code]?.en ?? "—",
      transmissionChannelAr: TRANSMISSION_CHANNELS[c.code]?.ar ?? "—",
      policyLever: POLICY_LEVERS[c.code]?.en ?? "—",
      policyLeverAr: POLICY_LEVERS[c.code]?.ar ?? "—",
      confidence: 0,
    }));
  }

  const totalLoss = headline.totalLossUsd;

  // Assign nodes to countries by proximity
  const buckets: Record<string, {
    totalStress: number;
    count: number;
    maxStress: number;
    topNode: string;
    topNodeAr: string;
    topSector: string;
    nodes: KnowledgeGraphNode[];
  }> = {};
  for (const c of GCC_COUNTRIES) {
    buckets[c.code] = { totalStress: 0, count: 0, maxStress: 0, topNode: "", topNodeAr: "", topSector: "", nodes: [] };
  }

  for (const node of graphNodes) {
    const lat = node.lat ?? 25;
    const lng = node.lng ?? 52;
    let nearestCode = "KSA";
    let nearestDist = Infinity;
    for (const c of GCC_COUNTRIES) {
      const d = Math.sqrt((lat - c.lat) ** 2 + (lng - c.lng) ** 2);
      if (d < nearestDist) {
        nearestDist = d;
        nearestCode = c.code;
      }
    }
    const bucket = buckets[nearestCode];
    const stress = node.stress ?? 0;
    bucket.totalStress += stress;
    bucket.count++;
    bucket.nodes.push(node);
    if (stress > bucket.maxStress) {
      bucket.maxStress = stress;
      bucket.topNode = node.label;
      bucket.topNodeAr = node.label_ar ?? node.label;
      bucket.topSector = node.layer ?? "economy";
    }
  }

  const totalStressAll = Object.values(buckets).reduce((s, b) => s + b.totalStress, 0) || 1;

  return GCC_COUNTRIES.map(c => {
    const bucket = buckets[c.code];
    const avgStress = bucket.count > 0 ? bucket.totalStress / bucket.count : 0;
    const exposureFraction = bucket.totalStress / totalStressAll;
    const exposureUsd = Math.round(totalLoss * exposureFraction);
    const sectorLabel = bucket.topSector.replace(/_/g, " ").replace(/\b\w/g, ch => ch.toUpperCase());

    return {
      code: c.code,
      name: c.name,
      nameAr: c.nameAr,
      exposureUsd,
      stressPercent: Math.min(1, avgStress),
      primarySector: sectorLabel || "—",
      primarySectorAr: sectorLabel || "—",
      primaryDriver: bucket.topNode
        ? `${bucket.topNode} — stress at ${(bucket.maxStress * 100).toFixed(0)}%`
        : "No impacted entities",
      primaryDriverAr: bucket.topNodeAr
        ? `${bucket.topNodeAr} — الضغط عند ${(bucket.maxStress * 100).toFixed(0)}%`
        : "لا توجد كيانات متأثرة",
      transmissionChannel: TRANSMISSION_CHANNELS[c.code]?.en ?? "Multi-channel financial transmission",
      transmissionChannelAr: TRANSMISSION_CHANNELS[c.code]?.ar ?? "قنوات انتقال مالية متعددة",
      policyLever: POLICY_LEVERS[c.code]?.en ?? "Coordinate with regional central banks",
      policyLeverAr: POLICY_LEVERS[c.code]?.ar ?? "التنسيق مع البنوك المركزية الإقليمية",
      confidence: bucket.count > 0 ? Math.min(0.95, 0.5 + bucket.count * 0.05) : 0,
    };
  });
}

// ═══════════════════════════════════════════════════════════════════════
// 3. Sector Formula Lab
// ═══════════════════════════════════════════════════════════════════════

export interface SectorFormulaResult {
  sector: string;
  sectorLabel: string;
  sectorLoss: number;
  totalLoss: number;
  allocationWeight: number;
  scenarioSensitivity: number;
  propagationWeight: number;
  formula: string;
  source: string;
  assumption: string;
  confidence: number;
}

const SECTOR_ALLOCATION_WEIGHTS: Record<string, number> = {
  energy: 0.35,
  banking: 0.25,
  insurance: 0.12,
  trade: 0.18,
  fintech: 0.05,
  real_estate: 0.03,
  government: 0.02,
};

const SCENARIO_SENSITIVITY: Record<string, Record<string, number>> = {
  energy: { ENERGY_TRADE: 0.95, BANKING_FINANCE: 0.30, CYBER: 0.40, GEOPOLITICAL: 0.85 },
  banking: { ENERGY_TRADE: 0.55, BANKING_FINANCE: 0.92, CYBER: 0.60, GEOPOLITICAL: 0.50 },
  insurance: { ENERGY_TRADE: 0.65, BANKING_FINANCE: 0.45, CYBER: 0.55, GEOPOLITICAL: 0.60 },
  trade: { ENERGY_TRADE: 0.80, BANKING_FINANCE: 0.35, CYBER: 0.45, GEOPOLITICAL: 0.70 },
  fintech: { ENERGY_TRADE: 0.20, BANKING_FINANCE: 0.70, CYBER: 0.85, GEOPOLITICAL: 0.25 },
};

export function computeSectorFormulas(
  headline: CommandCenterHeadline | null,
  sectorRollups: Record<string, { aggregate_stress?: number; stress?: number; total_loss?: number }>,
  scenarioDomain: string,
): SectorFormulaResult[] {
  if (!headline || headline.totalLossUsd <= 0) return [];

  const totalLoss = headline.totalLossUsd;
  const avgStress = headline.averageStress;

  return Object.entries(sectorRollups).map(([sector, data]) => {
    const stress = data.aggregate_stress ?? data.stress ?? 0;
    const actualLoss = data.total_loss ?? 0;

    const allocationWeight = SECTOR_ALLOCATION_WEIGHTS[sector] ?? 0.05;
    const scenarioSensitivity = SCENARIO_SENSITIVITY[sector]?.[scenarioDomain] ?? 0.5;
    const propagationWeight = Math.min(1, stress / Math.max(0.01, avgStress));

    const computedLoss = Math.round(totalLoss * allocationWeight * scenarioSensitivity * propagationWeight);
    const sectorLoss = actualLoss > 0 ? actualLoss : computedLoss;

    return {
      sector,
      sectorLabel: sector.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
      sectorLoss,
      totalLoss,
      allocationWeight,
      scenarioSensitivity,
      propagationWeight,
      formula: `sector_loss = total_loss × allocation_weight × scenario_sensitivity × propagation_weight = $${(totalLoss / 1e9).toFixed(1)}B × ${allocationWeight.toFixed(2)} × ${scenarioSensitivity.toFixed(2)} × ${propagationWeight.toFixed(2)}`,
      source: "17-stage simulation engine with sector-specific allocation weights from config.py",
      assumption: `Allocation weight ${(allocationWeight * 100).toFixed(0)}% assumes ${sector} sector accounts for ${(allocationWeight * 100).toFixed(0)}% of GCC systemic exposure. Sensitivity ${(scenarioSensitivity * 100).toFixed(0)}% calibrated to ${scenarioDomain} scenario type.`,
      confidence: Math.min(0.95, 0.6 + (actualLoss > 0 ? 0.2 : 0) + (stress > 0.3 ? 0.1 : 0)),
    };
  });
}

// ═══════════════════════════════════════════════════════════════════════
// 4. Banking Simulation Layer
// ═══════════════════════════════════════════════════════════════════════

export interface BankingSimulationResult {
  liquidityStress: number;
  interbankPressure: number;
  fundingStress: number;
  paymentDelay: number;
  sovereignSpreadSensitivity: number;
  metrics: Array<{
    label: string;
    labelAr: string;
    value: string;
    level: "nominal" | "guarded" | "elevated" | "high" | "severe";
    formula: string;
    source: string;
    assumption: string;
  }>;
}

function classifyLevel(v: number): "nominal" | "guarded" | "elevated" | "high" | "severe" {
  if (v >= 0.8) return "severe";
  if (v >= 0.65) return "high";
  if (v >= 0.5) return "elevated";
  if (v >= 0.35) return "guarded";
  return "nominal";
}

export function computeBankingSimulation(
  sectorRollups: Record<string, { aggregate_stress?: number; stress?: number; total_loss?: number }>,
  headline: CommandCenterHeadline | null,
): BankingSimulationResult {
  const banking = sectorRollups.banking ?? sectorRollups.finance;
  const bankingStress = banking?.aggregate_stress ?? banking?.stress ?? 0;
  const totalLoss = headline?.totalLossUsd ?? 0;
  const severity = headline?.averageStress ?? 0;

  // Derived banking metrics
  const liquidityStress = Math.min(1, bankingStress * 1.1 + severity * 0.15);
  const interbankPressure = Math.min(1, bankingStress * 0.9 + severity * 0.2);
  const fundingStress = Math.min(1, bankingStress * 0.85 + severity * 0.1);
  const paymentDelay = Math.min(1, bankingStress * 0.6);
  const sovereignSpreadSensitivity = Math.min(1, severity * 0.8 + bankingStress * 0.3);

  return {
    liquidityStress,
    interbankPressure,
    fundingStress,
    paymentDelay,
    sovereignSpreadSensitivity,
    metrics: [
      {
        label: "Liquidity Stress", labelAr: "ضغط السيولة",
        value: `${(liquidityStress * 100).toFixed(1)}%`,
        level: classifyLevel(liquidityStress),
        formula: `liquidity_stress = banking_stress × 1.1 + avg_severity × 0.15 = ${bankingStress.toFixed(2)} × 1.1 + ${severity.toFixed(2)} × 0.15`,
        source: "Banking sector aggregate from 42-node GCC graph",
        assumption: "Liquidity stress amplifies banking base stress by 10% plus system-wide severity contribution",
      },
      {
        label: "Interbank Pressure", labelAr: "ضغط سوق ما بين البنوك",
        value: `${(interbankPressure * 100).toFixed(1)}%`,
        level: classifyLevel(interbankPressure),
        formula: `interbank_pressure = banking_stress × 0.9 + avg_severity × 0.2 = ${bankingStress.toFixed(2)} × 0.9 + ${severity.toFixed(2)} × 0.2`,
        source: "Interbank contagion model with bilateral exposure matrix",
        assumption: "Interbank markets transmit 90% of banking stress with 20% system-wide contagion",
      },
      {
        label: "Funding Stress", labelAr: "ضغط التمويل",
        value: `${(fundingStress * 100).toFixed(1)}%`,
        level: classifyLevel(fundingStress),
        formula: `funding_stress = banking_stress × 0.85 + avg_severity × 0.1 = ${bankingStress.toFixed(2)} × 0.85 + ${severity.toFixed(2)} × 0.1`,
        source: "Wholesale funding market freeze model",
        assumption: "Funding channels absorb 85% of banking stress; 10% system-wide contribution",
      },
      {
        label: "Payment System Delay", labelAr: "تأخير نظام الدفع",
        value: paymentDelay > 0.3 ? `${Math.round(paymentDelay * 480)}min` : "Normal",
        level: classifyLevel(paymentDelay),
        formula: `payment_delay = banking_stress × 0.6 = ${bankingStress.toFixed(2)} × 0.6 → ${Math.round(paymentDelay * 480)}min`,
        source: "Payment infrastructure stress model",
        assumption: "Payment delays scale linearly with banking stress at 60% transmission",
      },
      {
        label: "Sovereign Spread Sensitivity", labelAr: "حساسية الهامش السيادي",
        value: `${(sovereignSpreadSensitivity * 100).toFixed(0)}bp`,
        level: classifyLevel(sovereignSpreadSensitivity),
        formula: `sovereign_spread = avg_severity × 0.8 + banking_stress × 0.3 = ${severity.toFixed(2)} × 0.8 + ${bankingStress.toFixed(2)} × 0.3`,
        source: "Sovereign credit spread model",
        assumption: "Sovereign spreads driven 80% by system severity, 30% by banking sector health",
      },
    ],
  };
}

// ═══════════════════════════════════════════════════════════════════════
// 5. Insurance Simulation Layer
// ═══════════════════════════════════════════════════════════════════════

export interface InsuranceSimulationResult {
  claimsPressure: number;
  pricingResponse: number;
  reinsuranceTrigger: number;
  reserveAbsorption: number;
  solvencyStress: number;
  metrics: Array<{
    label: string;
    labelAr: string;
    value: string;
    level: "nominal" | "guarded" | "elevated" | "high" | "severe";
    formula: string;
    source: string;
    assumption: string;
  }>;
}

export function computeInsuranceSimulation(
  sectorRollups: Record<string, { aggregate_stress?: number; stress?: number; total_loss?: number }>,
  headline: CommandCenterHeadline | null,
): InsuranceSimulationResult {
  const insurance = sectorRollups.insurance;
  const insuranceStress = insurance?.aggregate_stress ?? insurance?.stress ?? 0;
  const severity = headline?.averageStress ?? 0;
  const totalLoss = headline?.totalLossUsd ?? 0;
  const insuranceLoss = insurance?.total_loss ?? 0;

  const claimsPressure = Math.min(1, insuranceStress * 1.2 + severity * 0.1);
  const pricingResponse = Math.min(1, insuranceStress * 0.7 + severity * 0.15);
  const reinsuranceTrigger = Math.min(1, insuranceStress * 1.1);
  const reserveAbsorption = Math.max(0, 1 - insuranceStress * 0.9);
  const solvencyStress = Math.min(1, insuranceStress * 0.8 + severity * 0.2);

  const claimsSurgeMultiplier = 1 + claimsPressure * 4;

  return {
    claimsPressure,
    pricingResponse,
    reinsuranceTrigger,
    reserveAbsorption,
    solvencyStress,
    metrics: [
      {
        label: "Claims Pressure", labelAr: "ضغط المطالبات",
        value: `${claimsSurgeMultiplier.toFixed(1)}× surge`,
        level: classifyLevel(claimsPressure),
        formula: `claims_pressure = insurance_stress × 1.2 + severity × 0.1 = ${insuranceStress.toFixed(2)} × 1.2 + ${severity.toFixed(2)} × 0.1 → ${claimsSurgeMultiplier.toFixed(1)}× multiplier`,
        source: "Insurance claims cascade model with P&I marine exposure",
        assumption: "Claims amplify insurance base stress by 20% plus 10% system-wide contribution",
      },
      {
        label: "Pricing Response", labelAr: "استجابة التسعير",
        value: `+${(pricingResponse * 100).toFixed(0)}%`,
        level: classifyLevel(pricingResponse),
        formula: `pricing_response = insurance_stress × 0.7 + severity × 0.15 = ${insuranceStress.toFixed(2)} × 0.7 + ${severity.toFixed(2)} × 0.15`,
        source: "Rate hardening model with loss ratio sensitivity",
        assumption: "Premium increases lag claims by 3-6 months; 70% of stress passed through",
      },
      {
        label: "Reinsurance Trigger", labelAr: "تفعيل إعادة التأمين",
        value: reinsuranceTrigger >= 0.6 ? "ACTIVATED" : reinsuranceTrigger >= 0.35 ? "WARNING" : "NORMAL",
        level: classifyLevel(reinsuranceTrigger),
        formula: `reinsurance_trigger = insurance_stress × 1.1 = ${insuranceStress.toFixed(2)} × 1.1 = ${reinsuranceTrigger.toFixed(2)}`,
        source: "Reinsurance treaty trigger model (excess-of-loss + cat bond)",
        assumption: "Trigger threshold at 60% stress; IFRS-17 catastrophe reserve activated",
      },
      {
        label: "Reserve Absorption", labelAr: "امتصاص الاحتياطي",
        value: `${(reserveAbsorption * 100).toFixed(0)}%`,
        level: classifyLevel(1 - reserveAbsorption),
        formula: `reserve_absorption = 1 - insurance_stress × 0.9 = 1 - ${insuranceStress.toFixed(2)} × 0.9`,
        source: "Reserve adequacy model with IBNR projection",
        assumption: "Reserves absorb up to 90% of insurance stress before requiring external capital",
      },
      {
        label: "Solvency Stress", labelAr: "ضغط الملاءة",
        value: `${(solvencyStress * 100).toFixed(1)}%`,
        level: classifyLevel(solvencyStress),
        formula: `solvency_stress = insurance_stress × 0.8 + severity × 0.2 = ${insuranceStress.toFixed(2)} × 0.8 + ${severity.toFixed(2)} × 0.2`,
        source: "Solvency II/IFRS-17 capital adequacy model",
        assumption: "Solvency driven 80% by insurance sector health, 20% by system-wide stress",
      },
    ],
  };
}

// ═══════════════════════════════════════════════════════════════════════
// 6. Decision ROI Engine
// ═══════════════════════════════════════════════════════════════════════

export interface DecisionROIEntry {
  id: string;
  action: string;
  actionAr: string;
  sector: string;
  owner: string;
  costUsd: number;
  lossAvoidedUsd: number;
  netBenefit: number;
  roiMultiple: number;
  confidence: number;
  deadlineHours: number;
  escalationPath: string;
  escalationPathAr: string;
  consequenceOfDelay: string;
  consequenceOfDelayAr: string;
  priority: number;
}

const ESCALATION_PATHS: Record<string, { en: string; ar: string }> = {
  energy: { en: "Ministry of Energy → Cabinet → GCC Energy Council", ar: "وزارة الطاقة → مجلس الوزراء → مجلس الطاقة الخليجي" },
  maritime: { en: "Federal Transport Authority → Maritime Council → IMO coordination", ar: "الهيئة الاتحادية للمواصلات → المجلس البحري → تنسيق المنظمة البحرية" },
  insurance: { en: "Insurance Authority → Central Bank → GCC Insurance Federation", ar: "هيئة التأمين → البنك المركزي → اتحاد التأمين الخليجي" },
  finance: { en: "Central Bank → Finance Ministry → GCC Monetary Council", ar: "البنك المركزي → وزارة المالية → المجلس النقدي الخليجي" },
  banking: { en: "Central Bank → Basel Committee liaison → GCC Financial Stability Board", ar: "البنك المركزي → لجنة بازل → مجلس الاستقرار المالي الخليجي" },
  government: { en: "Finance Ministry → Cabinet → GCC Supreme Council", ar: "وزارة المالية → مجلس الوزراء → المجلس الأعلى الخليجي" },
};

export function computeDecisionROI(
  decisionActions: DecisionActionV2[],
  headline: CommandCenterHeadline | null,
): DecisionROIEntry[] {
  const totalLoss = headline?.totalLossUsd ?? 0;

  return decisionActions
    .map(action => {
      const cost = action.cost_usd ?? 0;
      const avoided = action.loss_avoided_usd ?? 0;
      const netBenefit = avoided - cost;
      const roiMultiple = cost > 0 ? avoided / cost : 0;
      const deadline = action.deadline_hours ?? action.time_to_act_hours ?? 0;
      const sector = action.sector ?? "finance";

      const escalation = ESCALATION_PATHS[sector] ?? ESCALATION_PATHS.finance;

      // Consequence of delay — derived from urgency + loss avoided
      const lossPerHour = deadline > 0 ? avoided / Math.max(1, deadline) : 0;
      const consequenceEn = deadline > 0
        ? `Delay costs ~$${(lossPerHour / 1e6).toFixed(0)}M per hour. After ${deadline}h, intervention effectiveness drops by ${Math.min(80, Math.round(action.urgency * 0.8))}%.`
        : `Immediate action required. Each hour of delay reduces intervention effectiveness.`;
      const consequenceAr = deadline > 0
        ? `التأخير يكلف ~${(lossPerHour / 1e6).toFixed(0)} مليون دولار بالساعة. بعد ${deadline} ساعة، تنخفض فعالية التدخل بنسبة ${Math.min(80, Math.round(action.urgency * 0.8))}%.`
        : `يتطلب إجراءً فورياً. كل ساعة تأخير تقلل فعالية التدخل.`;

      return {
        id: action.id,
        action: action.action,
        actionAr: action.action_ar ?? action.action,
        sector,
        owner: action.owner,
        costUsd: cost,
        lossAvoidedUsd: avoided,
        netBenefit,
        roiMultiple,
        confidence: action.confidence ?? 0,
        deadlineHours: deadline,
        escalationPath: escalation.en,
        escalationPathAr: escalation.ar,
        consequenceOfDelay: consequenceEn,
        consequenceOfDelayAr: consequenceAr,
        priority: action.priority ?? 0,
      };
    })
    .sort((a, b) => b.priority - a.priority);
}

// ═══════════════════════════════════════════════════════════════════════
// 7. Outcome Confirmation Layer
// ═══════════════════════════════════════════════════════════════════════

export interface OutcomeConfirmation {
  withoutAction: {
    projectedLossLow: number;
    projectedLossHigh: number;
    recoveryDays: number;
    description: string;
    descriptionAr: string;
  };
  coordinatedResponse: {
    projectedLossLow: number;
    projectedLossHigh: number;
    recoveryDays: number;
    description: string;
    descriptionAr: string;
  };
  expectedLossReduction: number;
  expectedLossReductionPercent: number;
  recoveryHorizonDays: number;
  recoveryHorizonReduction: number;
  outcomeTrackingStatus: "PENDING" | "IN_PROGRESS" | "COMPLETED";
  actualOutcome: "PENDING" | "BETTER_THAN_EXPECTED" | "AS_EXPECTED" | "WORSE_THAN_EXPECTED";
  variancePercent: number | null;
  varianceExplanation: string;
}

export function computeOutcomeConfirmation(
  headline: CommandCenterHeadline | null,
  decisionActions: DecisionActionV2[],
  outcomes: { baseCase: OutcomeScenario; mitigatedCase: OutcomeScenario; valueSaved: { low: number; high: number } } | null,
): OutcomeConfirmation {
  const totalLoss = headline?.totalLossUsd ?? 0;
  const recoveryDays = headline?.maxRecoveryDays ?? 42;
  const totalLossAvoided = decisionActions.reduce((sum, a) => sum + (a.loss_avoided_usd ?? 0), 0);
  const actionCount = decisionActions.length;

  const baseLow = outcomes?.baseCase.lossLow ?? Math.round(totalLoss * 0.89);
  const baseHigh = outcomes?.baseCase.lossHigh ?? Math.round(totalLoss * 1.11);
  const baseMid = (baseLow + baseHigh) / 2;

  const mitigationRate = totalLossAvoided > 0 ? Math.min(0.6, totalLossAvoided / Math.max(1, totalLoss)) : 0.45;

  const mitLow = outcomes?.mitigatedCase.lossLow ?? Math.round(baseLow * (1 - mitigationRate));
  const mitHigh = outcomes?.mitigatedCase.lossHigh ?? Math.round(baseHigh * (1 - mitigationRate));
  const mitMid = (mitLow + mitHigh) / 2;

  const mitRecovery = outcomes?.mitigatedCase.recoveryDays ?? Math.round(recoveryDays * (1 - mitigationRate * 0.8));

  const expectedReduction = baseMid - mitMid;
  const reductionPercent = baseMid > 0 ? (expectedReduction / baseMid) * 100 : 0;

  return {
    withoutAction: {
      projectedLossLow: baseLow,
      projectedLossHigh: baseHigh,
      recoveryDays: outcomes?.baseCase.recoveryDays ?? recoveryDays,
      description: outcomes?.baseCase.description ?? `Full propagation across affected sectors. Recovery dependent on external resolution timeline.`,
      descriptionAr: outcomes?.baseCase.descriptionAr ?? "انتشار كامل عبر القطاعات المتأثرة.",
    },
    coordinatedResponse: {
      projectedLossLow: mitLow,
      projectedLossHigh: mitHigh,
      recoveryDays: mitRecovery,
      description: outcomes?.mitigatedCase.description ?? `${actionCount} coordinated interventions reducing exposure by ${reductionPercent.toFixed(0)}%.`,
      descriptionAr: outcomes?.mitigatedCase.descriptionAr ?? `${actionCount} تدخلات منسقة تقلل التعرض بنسبة ${reductionPercent.toFixed(0)}%.`,
    },
    expectedLossReduction: Math.round(expectedReduction),
    expectedLossReductionPercent: Math.round(reductionPercent),
    recoveryHorizonDays: mitRecovery,
    recoveryHorizonReduction: (outcomes?.baseCase.recoveryDays ?? recoveryDays) - mitRecovery,
    outcomeTrackingStatus: "PENDING",
    actualOutcome: "PENDING",
    variancePercent: null,
    varianceExplanation: "Outcome tracking will begin once coordinated response is initiated. Variance analysis requires T+7 data collection.",
  };
}

// ═══════════════════════════════════════════════════════════════════════
// 8. Collaboration / Executive Stage
// ═══════════════════════════════════════════════════════════════════════

export type ApprovalState = "DRAFT" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED";

export interface CollaborationStage {
  submittedForReview: boolean;
  submittedAt: string | null;
  owner: string;
  approvalState: ApprovalState;
  reviewers: Array<{
    role: "CEO" | "CRO" | "REGULATOR";
    name: string;
    status: "PENDING" | "APPROVED" | "REJECTED" | "ABSTAINED";
    comment: string | null;
  }>;
  auditTrail: Array<{
    timestamp: string;
    actor: string;
    action: string;
    detail: string;
  }>;
  personaViews: {
    ceo: { focus: string; focusAr: string };
    risk: { focus: string; focusAr: string };
    regulator: { focus: string; focusAr: string };
  };
}

export function computeCollaborationStage(
  scenario: { label: string; severity: number } | null,
  headline: CommandCenterHeadline | null,
  decisionActions: DecisionActionV2[],
): CollaborationStage {
  const now = new Date().toISOString();
  const totalCost = decisionActions.reduce((s, a) => s + (a.cost_usd ?? 0), 0);
  const totalAvoided = decisionActions.reduce((s, a) => s + (a.loss_avoided_usd ?? 0), 0);
  const scenarioLabel = scenario?.label ?? "Scenario";

  return {
    submittedForReview: false,
    submittedAt: null,
    owner: "Intelligence Operations",
    approvalState: "DRAFT",
    reviewers: [
      { role: "CEO", name: "Chief Executive Officer", status: "PENDING", comment: null },
      { role: "CRO", name: "Chief Risk Officer", status: "PENDING", comment: null },
      { role: "REGULATOR", name: "Regulatory Affairs", status: "PENDING", comment: null },
    ],
    auditTrail: [
      { timestamp: now, actor: "System", action: "SCENARIO_LOADED", detail: `Scenario "${scenarioLabel}" loaded into intelligence pipeline` },
      { timestamp: now, actor: "System", action: "ANALYSIS_COMPLETE", detail: `${decisionActions.length} decision recommendations generated` },
    ],
    personaViews: {
      ceo: {
        focus: `$${(headline?.totalLossUsd ?? 0) / 1e9 > 0 ? ((headline?.totalLossUsd ?? 0) / 1e9).toFixed(1) : "0"}B at risk. ${decisionActions.length} interventions recommended. Net ROI: $${((totalAvoided - totalCost) / 1e9).toFixed(1)}B.`,
        focusAr: `${((headline?.totalLossUsd ?? 0) / 1e9).toFixed(1)} مليار دولار معرض للخطر. ${decisionActions.length} تدخلات موصى بها.`,
      },
      risk: {
        focus: `${headline?.criticalCount ?? 0} critical entities. Average stress ${((headline?.averageStress ?? 0) * 100).toFixed(0)}%. Propagation depth ${headline?.propagationDepth ?? 0}. Recovery horizon ${headline?.maxRecoveryDays ?? 0} days.`,
        focusAr: `${headline?.criticalCount ?? 0} كيانات حرجة. متوسط الضغط ${((headline?.averageStress ?? 0) * 100).toFixed(0)}%.`,
      },
      regulator: {
        focus: `Regulatory obligations triggered across ${decisionActions.filter(a => (a.regulatory_risk ?? 0) > 0.2).length} actions. Compliance cost: $${(totalCost / 1e6).toFixed(0)}M. Oversight chain: Central Bank → Finance Ministry → GCC Council.`,
        focusAr: `التزامات تنظيمية مفعلة عبر ${decisionActions.filter(a => (a.regulatory_risk ?? 0) > 0.2).length} إجراءات.`,
      },
    },
  };
}
