/**
 * Decision Command Center — Mock Intelligence Data
 *
 * Deterministic mock payloads matching UnifiedRunResult + PropagationResult
 * contracts from observatory.ts. Replaced by live API once wired.
 */

import type {
  UnifiedRunResult,
  PropagationStep,
  SectorImpact,
  CausalStep,
  DecisionActionV2,
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  ImpactedEntity,
} from "@/types/observatory";

// ── Scenario Headline ─────────────────────────────────────────────────

export const MOCK_SCENARIO = {
  template_id: "hormuz_chokepoint_disruption",
  label: "Energy & Trade Flow Disruption — Strait of Hormuz",
  label_ar: "اضطراب تدفق الطاقة والتجارة — مضيق هرمز",
  severity: 0.72,
  horizon_hours: 168,
  domain: "ENERGY_TRADE",
  trigger_time: "2026-04-08T06:14:00Z",
};

export const MOCK_HEADLINE = {
  total_loss_usd: 4_270_000_000,
  total_nodes_impacted: 31,
  propagation_depth: 5,
  peak_day: 3,
  max_recovery_days: 42,
  average_stress: 0.61,
  affected_entities: 31,
  critical_count: 7,
  elevated_count: 12,
};

// ── Graph Nodes (subset for command center) ───────────────────────────

export const MOCK_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "hormuz_strait", label: "Strait of Hormuz", label_ar: "مضيق هرمز", layer: "geography", type: "chokepoint", weight: 0.95, lat: 26.56, lng: 56.25, sensitivity: 0.92, stress: 0.88, classification: "CRITICAL" },
  { id: "ras_tanura", label: "Ras Tanura Terminal", label_ar: "محطة رأس تنورة", layer: "infrastructure", type: "port", weight: 0.88, lat: 26.63, lng: 50.16, sensitivity: 0.85, stress: 0.74, classification: "ELEVATED" },
  { id: "jebel_ali", label: "Jebel Ali Port", label_ar: "ميناء جبل علي", layer: "infrastructure", type: "port", weight: 0.91, lat: 25.02, lng: 55.06, sensitivity: 0.80, stress: 0.71, classification: "ELEVATED" },
  { id: "aramco", label: "Saudi Aramco", label_ar: "أرامكو السعودية", layer: "economy", type: "corporation", weight: 0.96, lat: 26.39, lng: 50.10, sensitivity: 0.78, stress: 0.65, classification: "MODERATE" },
  { id: "adnoc", label: "ADNOC", label_ar: "أدنوك", layer: "economy", type: "corporation", weight: 0.85, lat: 24.45, lng: 54.65, sensitivity: 0.75, stress: 0.62, classification: "MODERATE" },
  { id: "sama", label: "SAMA", label_ar: "مؤسسة النقد", layer: "finance", type: "central_bank", weight: 0.90, lat: 24.69, lng: 46.69, sensitivity: 0.70, stress: 0.48, classification: "MODERATE" },
  { id: "cbuae", label: "CBUAE", label_ar: "مصرف الإمارات المركزي", layer: "finance", type: "central_bank", weight: 0.87, lat: 24.49, lng: 54.37, sensitivity: 0.68, stress: 0.45, classification: "LOW" },
  { id: "brent_crude", label: "Brent Crude", label_ar: "خام برنت", layer: "economy", type: "commodity", weight: 0.82, lat: 25.30, lng: 51.52, sensitivity: 0.90, stress: 0.78, classification: "ELEVATED" },
  { id: "gcc_insurance", label: "GCC Insurance Sector", label_ar: "قطاع التأمين الخليجي", layer: "finance", type: "sector", weight: 0.74, lat: 25.20, lng: 55.27, sensitivity: 0.72, stress: 0.58, classification: "MODERATE" },
  { id: "gcc_trade", label: "GCC Trade Volume", label_ar: "حجم التجارة الخليجية", layer: "economy", type: "indicator", weight: 0.79, lat: 24.71, lng: 46.67, sensitivity: 0.82, stress: 0.67, classification: "ELEVATED" },
  // Kuwait
  { id: "kpc", label: "Kuwait Petroleum Corp", label_ar: "مؤسسة البترول الكويتية", layer: "economy", type: "corporation", weight: 0.84, lat: 29.38, lng: 47.99, sensitivity: 0.76, stress: 0.59, classification: "MODERATE" },
  { id: "cbk", label: "Central Bank of Kuwait", label_ar: "بنك الكويت المركزي", layer: "finance", type: "central_bank", weight: 0.82, lat: 29.37, lng: 47.98, sensitivity: 0.65, stress: 0.42, classification: "LOW" },
  // Qatar
  { id: "qatar_energy", label: "QatarEnergy", label_ar: "قطر للطاقة", layer: "economy", type: "corporation", weight: 0.88, lat: 25.35, lng: 51.18, sensitivity: 0.80, stress: 0.56, classification: "MODERATE" },
  { id: "qcb", label: "Qatar Central Bank", label_ar: "مصرف قطر المركزي", layer: "finance", type: "central_bank", weight: 0.80, lat: 25.29, lng: 51.53, sensitivity: 0.62, stress: 0.38, classification: "LOW" },
  // Bahrain
  { id: "cbb", label: "Central Bank of Bahrain", label_ar: "مصرف البحرين المركزي", layer: "finance", type: "central_bank", weight: 0.78, lat: 26.07, lng: 50.56, sensitivity: 0.70, stress: 0.51, classification: "MODERATE" },
  { id: "bapco", label: "BAPCO", label_ar: "بابكو", layer: "economy", type: "corporation", weight: 0.72, lat: 26.15, lng: 50.55, sensitivity: 0.68, stress: 0.47, classification: "MODERATE" },
  // Oman
  { id: "salalah_port", label: "Port of Salalah", label_ar: "ميناء صلالة", layer: "infrastructure", type: "port", weight: 0.76, lat: 16.95, lng: 54.01, sensitivity: 0.74, stress: 0.54, classification: "MODERATE" },
  { id: "cbo", label: "Central Bank of Oman", label_ar: "البنك المركزي العماني", layer: "finance", type: "central_bank", weight: 0.75, lat: 23.59, lng: 58.38, sensitivity: 0.60, stress: 0.36, classification: "LOW" },
];

export const MOCK_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "e1", source: "hormuz_strait", target: "ras_tanura", weight: 0.92, polarity: 1, label: "blocks export flow", label_ar: "يعطل تدفق الصادرات", transmission: 0.88 },
  { id: "e2", source: "hormuz_strait", target: "jebel_ali", weight: 0.87, polarity: 1, label: "disrupts container throughput", label_ar: "يعطل إنتاجية الحاويات", transmission: 0.82 },
  { id: "e3", source: "ras_tanura", target: "aramco", weight: 0.85, polarity: 1, label: "reduces export capacity", label_ar: "يقلل طاقة التصدير", transmission: 0.78 },
  { id: "e4", source: "jebel_ali", target: "gcc_trade", weight: 0.80, polarity: 1, label: "constrains trade volume", label_ar: "يقيد حجم التجارة", transmission: 0.74 },
  { id: "e5", source: "hormuz_strait", target: "brent_crude", weight: 0.90, polarity: 1, label: "spikes crude prices", label_ar: "يرفع أسعار النفط", transmission: 0.86 },
  { id: "e6", source: "brent_crude", target: "gcc_insurance", weight: 0.65, polarity: 1, label: "increases marine P&I claims", label_ar: "يزيد مطالبات التأمين البحري", transmission: 0.58 },
  { id: "e7", source: "aramco", target: "sama", weight: 0.70, polarity: 1, label: "reduces fiscal inflow", label_ar: "يقلل التدفق المالي", transmission: 0.62 },
  { id: "e8", source: "adnoc", target: "cbuae", weight: 0.68, polarity: 1, label: "reduces fiscal inflow", label_ar: "يقلل التدفق المالي", transmission: 0.60 },
  { id: "e9", source: "hormuz_strait", target: "adnoc", weight: 0.84, polarity: 1, label: "disrupts operations", label_ar: "يعطل العمليات", transmission: 0.79 },
  { id: "e10", source: "gcc_trade", target: "sama", weight: 0.55, polarity: 1, label: "strains FX reserves", label_ar: "يضغط على الاحتياطي", transmission: 0.48 },
];

// ── Impacted Entities (map overlay) ───────────────────────────────────

export const MOCK_IMPACTED_ENTITIES: ImpactedEntity[] = MOCK_GRAPH_NODES.map((n) => ({
  node_id: n.id,
  label: n.label,
  label_ar: n.label_ar,
  lat: n.lat,
  lng: n.lng,
  stress: n.stress ?? 0,
  loss_usd: Math.round((n.stress ?? 0) * 600_000_000),
  classification: n.classification ?? "NOMINAL",
  layer: n.layer,
}));

// ── Propagation Chain ─────────────────────────────────────────────────

export const MOCK_PROPAGATION_STEPS: PropagationStep[] = [
  { from: "hormuz_strait", fromLabel: "Strait of Hormuz", to: "ras_tanura", toLabel: "Ras Tanura Terminal", weight: 0.92, polarity: 1, impact: 0.88, label: "Oil export blockage", iteration: 1 },
  { from: "hormuz_strait", fromLabel: "Strait of Hormuz", to: "jebel_ali", toLabel: "Jebel Ali Port", weight: 0.87, polarity: 1, impact: 0.82, label: "Container throughput drop", iteration: 1 },
  { from: "hormuz_strait", fromLabel: "Strait of Hormuz", to: "brent_crude", toLabel: "Brent Crude", weight: 0.90, polarity: 1, impact: 0.86, label: "Crude price spike", iteration: 1 },
  { from: "ras_tanura", fromLabel: "Ras Tanura Terminal", to: "aramco", toLabel: "Saudi Aramco", weight: 0.85, polarity: 1, impact: 0.65, label: "Export capacity reduction", iteration: 2 },
  { from: "jebel_ali", fromLabel: "Jebel Ali Port", to: "gcc_trade", toLabel: "GCC Trade Volume", weight: 0.80, polarity: 1, impact: 0.67, label: "Trade volume constraint", iteration: 2 },
  { from: "brent_crude", fromLabel: "Brent Crude", to: "gcc_insurance", toLabel: "GCC Insurance Sector", weight: 0.65, polarity: 1, impact: 0.58, label: "Marine P&I claims surge", iteration: 2 },
  { from: "aramco", fromLabel: "Saudi Aramco", to: "sama", toLabel: "SAMA", weight: 0.70, polarity: 1, impact: 0.48, label: "Fiscal revenue reduction", iteration: 3 },
  { from: "adnoc", fromLabel: "ADNOC", to: "cbuae", toLabel: "CBUAE", weight: 0.68, polarity: 1, impact: 0.45, label: "Fiscal revenue reduction", iteration: 3 },
];

export const MOCK_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "infrastructure", sectorLabel: "Energy Infrastructure", avgImpact: 0.73, maxImpact: 0.88, nodeCount: 4, topNode: "ras_tanura", color: "#8C2318" },
  { sector: "economy", sectorLabel: "Trade & Commodities", avgImpact: 0.68, maxImpact: 0.78, nodeCount: 5, topNode: "brent_crude", color: "#8B6914" },
  { sector: "finance", sectorLabel: "Banking & Insurance", avgImpact: 0.50, maxImpact: 0.58, nodeCount: 4, topNode: "gcc_insurance", color: "#0C6B58" },
  { sector: "geography", sectorLabel: "Maritime Corridors", avgImpact: 0.88, maxImpact: 0.88, nodeCount: 1, topNode: "hormuz_strait", color: "#A0522D" },
];

// ── Causal Chain ──────────────────────────────────────────────────────

export const MOCK_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "hormuz_strait", entity_label: "Strait of Hormuz", entity_label_ar: "مضيق هرمز", event: "Partial maritime blockage detected — vessel transit down 60%", event_ar: "اكتشاف إغلاق بحري جزئي — انخفاض حركة السفن 60%", impact_usd: 0, stress_delta: 0.88, mechanism: "direct_shock" },
  { step: 2, entity_id: "brent_crude", entity_label: "Brent Crude", entity_label_ar: "خام برنت", event: "Crude prices spike +$18/bbl on supply disruption fears", event_ar: "ارتفاع أسعار النفط +18$/برميل بسبب مخاوف انقطاع الإمداد", impact_usd: 1_200_000_000, stress_delta: 0.78, mechanism: "price_transmission" },
  { step: 3, entity_id: "ras_tanura", entity_label: "Ras Tanura Terminal", entity_label_ar: "محطة رأس تنورة", event: "Export terminal throughput reduced to 40% capacity", event_ar: "انخفاض طاقة محطة التصدير إلى 40%", impact_usd: 890_000_000, stress_delta: 0.74, mechanism: "physical_constraint" },
  { step: 4, entity_id: "jebel_ali", entity_label: "Jebel Ali Port", entity_label_ar: "ميناء جبل علي", event: "Container backlog exceeds 72h — rerouting to Salalah/Sohar", event_ar: "تراكم الحاويات يتجاوز 72 ساعة — إعادة توجيه إلى صلالة/صحار", impact_usd: 670_000_000, stress_delta: 0.71, mechanism: "capacity_overflow" },
  { step: 5, entity_id: "aramco", entity_label: "Saudi Aramco", entity_label_ar: "أرامكو السعودية", event: "Daily export volumes cut by 3.2M bbl — force majeure declared", event_ar: "تقليص حجم الصادرات اليومية 3.2 مليون برميل — إعلان القوة القاهرة", impact_usd: 820_000_000, stress_delta: 0.65, mechanism: "supply_chain" },
  { step: 6, entity_id: "gcc_insurance", entity_label: "GCC Insurance Sector", entity_label_ar: "قطاع التأمين الخليجي", event: "Marine P&I claims surge 4.2x — reinsurance triggers activated", event_ar: "ارتفاع مطالبات التأمين البحري 4.2 ضعف — تفعيل إعادة التأمين", impact_usd: 410_000_000, stress_delta: 0.58, mechanism: "claims_cascade" },
  { step: 7, entity_id: "sama", entity_label: "SAMA", entity_label_ar: "مؤسسة النقد", event: "FX reserves drawdown accelerates — interbank liquidity tightens", event_ar: "تسارع سحب احتياطي العملات — تشديد السيولة بين البنوك", impact_usd: 280_000_000, stress_delta: 0.48, mechanism: "monetary_transmission" },
];

// ── Decision Actions ──────────────────────────────────────────────────

export const MOCK_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "da_1", action: "Activate Strategic Petroleum Reserve release (SAMA coordination)", action_ar: "تفعيل إطلاق الاحتياطي البترولي الاستراتيجي (بالتنسيق مع مؤسسة النقد)",
    sector: "energy", owner: "Ministry of Energy", urgency: 92, value: 88,
    regulatory_risk: 0.15, priority: 95, target_node_id: "ras_tanura",
    target_lat: 26.63, target_lng: 50.16, loss_avoided_usd: 1_800_000_000,
    cost_usd: 120_000_000, confidence: 0.87,
  },
  {
    id: "da_2", action: "Deploy emergency vessel rerouting through Bab el-Mandeb corridor", action_ar: "نشر خطة إعادة توجيه السفن الطارئة عبر ممر باب المندب",
    sector: "maritime", owner: "Federal Transport Authority", urgency: 88, value: 75,
    regulatory_risk: 0.22, priority: 82, target_node_id: "jebel_ali",
    target_lat: 25.02, target_lng: 55.06, loss_avoided_usd: 920_000_000,
    cost_usd: 85_000_000, confidence: 0.79,
  },
  {
    id: "da_3", action: "Trigger IFRS 17 catastrophe reserve allocation for marine P&I", action_ar: "تفعيل تخصيص احتياطي الكوارث وفق المعيار الدولي IFRS 17 للتأمين البحري",
    sector: "insurance", owner: "Insurance Authority", urgency: 78, value: 70,
    regulatory_risk: 0.30, priority: 74, target_node_id: "gcc_insurance",
    target_lat: 25.20, target_lng: 55.27, loss_avoided_usd: 410_000_000,
    cost_usd: 45_000_000, confidence: 0.82,
  },
  {
    id: "da_4", action: "Coordinate GCC central bank FX swap lines to stabilize interbank rates", action_ar: "تنسيق خطوط مبادلة العملات بين البنوك المركزية الخليجية لتثبيت أسعار الفائدة",
    sector: "finance", owner: "SAMA + CBUAE", urgency: 72, value: 82,
    regulatory_risk: 0.18, priority: 77, target_node_id: "sama",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 650_000_000,
    cost_usd: 30_000_000, confidence: 0.85,
  },
];

// ── Explanation Pack ──────────────────────────────────────────────────

export const MOCK_EXPLANATION = {
  narrative_en:
    "A partial blockage of the Strait of Hormuz — reducing vessel transit by approximately 60% — triggers a multi-sector cascade across GCC financial infrastructure. The shock propagates through three primary channels: (1) physical constraint on oil export terminals, reducing Ras Tanura throughput to 40% and Jebel Ali container processing to 55%; (2) commodity price transmission, with Brent crude spiking +$18/bbl within 48 hours; and (3) insurance claims cascade, activating reinsurance triggers across marine P&I lines. Total estimated loss reaches $4.27B over the 7-day horizon, with peak stress on Day 3. Recovery is projected at 42 days assuming diplomatic resolution within 10 days.",
  narrative_ar:
    "يؤدي الإغلاق الجزئي لمضيق هرمز — مع تقليص حركة السفن بنسبة 60% تقريباً — إلى سلسلة تأثيرات متعددة القطاعات عبر البنية التحتية المالية الخليجية.",
  methodology: "Institutional macro-financial intelligence: Macro → Banking → Insurance → Sector Transmission → Entity Exposure → Decision → Counterfactual → Governance. 76-node GCC knowledge graph with 190 causal edges. Confidence: Monte Carlo 10K iterations.",
  confidence: 0.84,
  total_steps: 7,
};

// ── Sector Rollups ────────────────────────────────────────────────────

export const MOCK_SECTOR_ROLLUPS = {
  energy: { aggregate_stress: 0.78, total_loss: 2_100_000_000, node_count: 5, classification: "ELEVATED" as const },
  banking: { aggregate_stress: 0.52, total_loss: 890_000_000, node_count: 6, classification: "GUARDED" as const },
  insurance: { aggregate_stress: 0.58, total_loss: 410_000_000, node_count: 4, classification: "GUARDED" as const },
  trade: { aggregate_stress: 0.67, total_loss: 750_000_000, node_count: 4, classification: "ELEVATED" as const },
  fintech: { aggregate_stress: 0.35, total_loss: 120_000_000, node_count: 3, classification: "LOW" as const },
};

// ── Trust Metadata ────────────────────────────────────────────────────

export const MOCK_TRUST = {
  trace_id: "trc_20260408_061400_hormuz",
  audit_id: "aud_cc_001",
  audit_hash: "sha256:a4f2c8d91e3b7f06e5d2a1c4b8f7e3d2a1c4b8f7e3d2a1c4b8f7e3d2a1c4b8f7",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.84,
  data_sources: ["ACLED", "AIS-Stream", "OpenSky", "Bloomberg Terminal", "SAMA Open Data"],
  stages_completed: ["signal_ingest", "graph_activation", "causal_trace", "propagation", "physics", "math", "sector_stress", "decision_gen", "explanation"],
  warnings: ["AIS data latency: +12min", "Brent crude price feed: delayed 5min"],
};

// ── Briefing-Layer Types ─────────────────────────────────────────────

export interface CountryExposureEntry {
  code: string;
  name: string;
  nameAr: string;
  exposureUsd: number;
  stressLevel: number;
  primaryDriver: string;
  primaryDriverAr: string;
  transmissionChannel: string;
  transmissionChannelAr: string;
}

export interface OutcomeScenario {
  label: string;
  labelAr: string;
  lossLow: number;
  lossHigh: number;
  recoveryDays: number;
  description: string;
  descriptionAr: string;
}

// ── Briefing-Layer Mock Data (Hormuz) ────────────────────────────────

export const MOCK_LOSS_RANGE = {
  low: 3_800_000_000,
  mid: 4_270_000_000,
  high: 4_740_000_000,
  confidence_pct: 90,
};

export const MOCK_DECISION_DEADLINE = new Date(Date.now() + 48 * 3_600_000).toISOString();

export const MOCK_ASSUMPTIONS: string[] = [
  "Strait closure is partial (60% throughput reduction), not full blockage",
  "Diplomatic resolution timeline estimated at 7–14 days",
  "Alternative routing via Bab el-Mandeb adds 4–6 days to transit",
  "GCC sovereign reserves sufficient for 90-day fiscal buffer",
  "No simultaneous cyber-attack on financial infrastructure",
];

export const MOCK_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", exposureUsd: 1_890_000_000, stressLevel: 0.72, primaryDriver: "Saudi Aramco — stress at 65%", primaryDriverAr: "أرامكو السعودية — الضغط عند 65%", transmissionChannel: "Oil revenue → fiscal balance → banking liquidity", transmissionChannelAr: "إيرادات النفط → الميزانية المالية → سيولة القطاع المصرفي" },
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", exposureUsd: 1_240_000_000, stressLevel: 0.67, primaryDriver: "Jebel Ali Port — stress at 71%", primaryDriverAr: "ميناء جبل علي — الضغط عند 71%", transmissionChannel: "Trade volume → logistics → real estate demand", transmissionChannelAr: "حجم التجارة → قطاع الخدمات اللوجستية → الطلب العقاري" },
  { code: "KWT", name: "Kuwait", nameAr: "الكويت", exposureUsd: 520_000_000, stressLevel: 0.51, primaryDriver: "Kuwait Petroleum Corp — stress at 59%", primaryDriverAr: "مؤسسة البترول الكويتية — الضغط عند 59%", transmissionChannel: "Oil exports → fiscal balance → public spending", transmissionChannelAr: "صادرات النفط → الميزانية المالية → الإنفاق العام" },
  { code: "QAT", name: "Qatar", nameAr: "قطر", exposureUsd: 380_000_000, stressLevel: 0.47, primaryDriver: "QatarEnergy — stress at 56%", primaryDriverAr: "قطر للطاقة — الضغط عند 56%", transmissionChannel: "LNG revenue → fiscal surplus → banking reserves", transmissionChannelAr: "إيرادات الغاز المسال → الفائض المالي → احتياطيات البنوك" },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", exposureUsd: 140_000_000, stressLevel: 0.42, primaryDriver: "Central Bank of Bahrain — stress at 51%", primaryDriverAr: "مصرف البحرين المركزي — الضغط عند 51%", transmissionChannel: "Financial services → sovereign credit → public services", transmissionChannelAr: "الخدمات المالية → الائتمان السيادي → الخدمات العامة" },
  { code: "OMN", name: "Oman", nameAr: "عُمان", exposureUsd: 100_000_000, stressLevel: 0.38, primaryDriver: "Port of Salalah — stress at 54%", primaryDriverAr: "ميناء صلالة — الضغط عند 54%", transmissionChannel: "Port operations → trade flows → fiscal balance", transmissionChannelAr: "عمليات الموانئ → تدفقات التجارة → الميزانية المالية" },
];

export const MOCK_OUTCOMES = {
  baseCase: {
    label: "Base Case (No Intervention)",
    labelAr: "السيناريو الأساسي (بدون تدخل)",
    lossLow: 3_800_000_000,
    lossHigh: 4_740_000_000,
    recoveryDays: 42,
    description: "Full propagation across affected sectors. Recovery dependent on external resolution timeline.",
    descriptionAr: "انتشار كامل عبر القطاعات المتأثرة. التعافي يعتمد على الجدول الزمني للحل الخارجي.",
  } as OutcomeScenario,
  mitigatedCase: {
    label: "Mitigated Case (Coordinated Response)",
    labelAr: "السيناريو المخفف (استجابة منسقة)",
    lossLow: 1_520_000_000,
    lossHigh: 2_370_000_000,
    recoveryDays: 24,
    description: "4 coordinated interventions reducing exposure by 50%. Recovery timeline shortened.",
    descriptionAr: "4 تدخلات منسقة تقلل التعرض بنسبة 50%. تقليص فترة التعافي.",
  } as OutcomeScenario,
  valueSaved: {
    low: 1_430_000_000,
    high: 3_220_000_000,
    description: "Estimated value preserved through coordinated intervention across 4 recommended actions.",
    descriptionAr: "القيمة المقدرة المحفوظة من خلال التدخل المنسق عبر 4 إجراءات موصى بها.",
  },
};

export const MOCK_SECTOR_DEPTH: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }> = {
  energy: { topDriver: "Crude prices spike +$18/bbl on supply disruption fears", secondOrderRisk: "1 recommended intervention — Activate Strategic Petroleum Reserve release", confidenceLow: 0.70, confidenceHigh: 0.86 },
  banking: { topDriver: "FX reserves drawdown accelerates — interbank liquidity tightens", secondOrderRisk: "1 recommended intervention — Coordinate GCC central bank FX swap lines", confidenceLow: 0.44, confidenceHigh: 0.60 },
  insurance: { topDriver: "Marine P&I claims surge 4.2x — reinsurance triggers activated", secondOrderRisk: "1 recommended intervention — Trigger IFRS 17 catastrophe reserve allocation", confidenceLow: 0.50, confidenceHigh: 0.66 },
  trade: { topDriver: "Container backlog exceeds 72h — rerouting to Salalah/Sohar", secondOrderRisk: "1 recommended intervention — Deploy emergency vessel rerouting", confidenceLow: 0.59, confidenceHigh: 0.75 },
};

// ══════════════════════════════════════════════════════════════════════
// Liquidity Stress Scenario — Full Mock Dataset
// ══════════════════════════════════════════════════════════════════════

export const MOCK_LIQUIDITY_SCENARIO = {
  template_id: "regional_liquidity_stress_event",
  label: "Regional Liquidity Stress Event — Cross-Border Banking",
  label_ar: "حدث ضغط سيولة إقليمي — القطاع المصرفي العابر للحدود",
  severity: 0.65,
  horizon_hours: 120,
  domain: "BANKING_FINANCE",
  trigger_time: "2026-04-10T09:30:00Z",
};

export const MOCK_LIQUIDITY_HEADLINE = {
  total_loss_usd: 2_310_000_000,
  total_nodes_impacted: 24,
  propagation_depth: 4,
  peak_day: 2,
  max_recovery_days: 28,
  average_stress: 0.54,
  affected_entities: 24,
  critical_count: 4,
  elevated_count: 8,
};

export const MOCK_LIQUIDITY_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "sama", label: "SAMA", label_ar: "مؤسسة النقد", layer: "finance", type: "central_bank", weight: 0.90, lat: 24.69, lng: 46.69, sensitivity: 0.78, stress: 0.72, classification: "ELEVATED" },
  { id: "cbuae", label: "CBUAE", label_ar: "مصرف الإمارات المركزي", layer: "finance", type: "central_bank", weight: 0.87, lat: 24.49, lng: 54.37, sensitivity: 0.74, stress: 0.68, classification: "ELEVATED" },
  { id: "cbk", label: "Central Bank of Kuwait", label_ar: "بنك الكويت المركزي", layer: "finance", type: "central_bank", weight: 0.82, lat: 29.37, lng: 47.98, sensitivity: 0.65, stress: 0.55, classification: "GUARDED" },
  { id: "qcb", label: "Qatar Central Bank", label_ar: "مصرف قطر المركزي", layer: "finance", type: "central_bank", weight: 0.80, lat: 25.29, lng: 51.53, sensitivity: 0.62, stress: 0.48, classification: "GUARDED" },
  { id: "cbb", label: "Central Bank of Bahrain", label_ar: "مصرف البحرين المركزي", layer: "finance", type: "central_bank", weight: 0.78, lat: 26.07, lng: 50.56, sensitivity: 0.70, stress: 0.61, classification: "ELEVATED" },
  { id: "cbo", label: "Central Bank of Oman", label_ar: "البنك المركزي العماني", layer: "finance", type: "central_bank", weight: 0.75, lat: 23.59, lng: 58.38, sensitivity: 0.60, stress: 0.44, classification: "GUARDED" },
  { id: "interbank_gcc", label: "GCC Interbank Market", label_ar: "سوق ما بين البنوك الخليجية", layer: "finance", type: "market", weight: 0.88, lat: 25.20, lng: 55.27, sensitivity: 0.85, stress: 0.78, classification: "HIGH" },
  { id: "fx_markets", label: "GCC FX Markets", label_ar: "أسواق العملات الخليجية", layer: "finance", type: "market", weight: 0.84, lat: 25.30, lng: 51.52, sensitivity: 0.80, stress: 0.65, classification: "ELEVATED" },
];

export const MOCK_LIQUIDITY_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "le1", source: "interbank_gcc", target: "sama", weight: 0.88, polarity: 1, label: "liquidity channel stress", label_ar: "ضغط قناة السيولة", transmission: 0.82 },
  { id: "le2", source: "interbank_gcc", target: "cbuae", weight: 0.85, polarity: 1, label: "interbank rate contagion", label_ar: "عدوى أسعار الفائدة بين البنوك", transmission: 0.78 },
  { id: "le3", source: "sama", target: "fx_markets", weight: 0.72, polarity: 1, label: "FX reserve pressure", label_ar: "ضغط احتياطي العملات", transmission: 0.65 },
  { id: "le4", source: "cbuae", target: "fx_markets", weight: 0.70, polarity: 1, label: "dirham peg defense", label_ar: "الدفاع عن ربط الدرهم", transmission: 0.62 },
  { id: "le5", source: "interbank_gcc", target: "cbk", weight: 0.75, polarity: 1, label: "cross-border funding stress", label_ar: "ضغط التمويل العابر للحدود", transmission: 0.68 },
  { id: "le6", source: "interbank_gcc", target: "cbb", weight: 0.78, polarity: 1, label: "wholesale funding freeze", label_ar: "تجميد التمويل بالجملة", transmission: 0.72 },
];

export const MOCK_LIQUIDITY_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "interbank_gcc", entity_label: "GCC Interbank Market", entity_label_ar: "سوق ما بين البنوك الخليجية", event: "Overnight lending rates spike 280bp — counterparty risk repricing", event_ar: "ارتفاع أسعار الإقراض لليلة واحدة 280 نقطة أساس — إعادة تسعير مخاطر الأطراف المقابلة", impact_usd: 0, stress_delta: 0.78, mechanism: "liquidity_stress" },
  { step: 2, entity_id: "sama", entity_label: "SAMA", entity_label_ar: "مؤسسة النقد", event: "Emergency repo facility activated — SAR 45B injected to stabilize interbank rates", event_ar: "تفعيل مرفق الريبو الطارئ — ضخ 45 مليار ريال لتثبيت الأسعار", impact_usd: 680_000_000, stress_delta: 0.72, mechanism: "monetary_transmission" },
  { step: 3, entity_id: "cbuae", entity_label: "CBUAE", entity_label_ar: "مصرف الإمارات المركزي", event: "AED liquidity buffer drawdown accelerates — 12% decline in 48h", event_ar: "تسارع سحب احتياطي السيولة — انخفاض 12% في 48 ساعة", impact_usd: 520_000_000, stress_delta: 0.68, mechanism: "credit_channel" },
  { step: 4, entity_id: "cbb", entity_label: "Central Bank of Bahrain", entity_label_ar: "مصرف البحرين المركزي", event: "Wholesale funding market frozen — sovereign credit spread widens 180bp", event_ar: "تجميد سوق التمويل بالجملة — اتساع هامش الائتمان السيادي 180 نقطة أساس", impact_usd: 410_000_000, stress_delta: 0.61, mechanism: "sovereign_exposure" },
  { step: 5, entity_id: "fx_markets", entity_label: "GCC FX Markets", entity_label_ar: "أسواق العملات الخليجية", event: "Forward point inversion signals peg pressure — NDF spreads widen", event_ar: "انعكاس النقاط الآجلة يشير إلى ضغط الربط — اتساع فروق العقود الآجلة", impact_usd: 700_000_000, stress_delta: 0.65, mechanism: "fx_pressure" },
];

export const MOCK_LIQUIDITY_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "finance", sectorLabel: "Banking & Central Banks", avgImpact: 0.65, maxImpact: 0.78, nodeCount: 8, topNode: "interbank_gcc", color: "#0C6B58" },
  { sector: "economy", sectorLabel: "FX & Capital Markets", avgImpact: 0.55, maxImpact: 0.65, nodeCount: 4, topNode: "fx_markets", color: "#8B6914" },
];

export const MOCK_LIQUIDITY_SECTOR_ROLLUPS = {
  banking: { aggregate_stress: 0.68, total_loss: 1_200_000_000, node_count: 6, classification: "ELEVATED" as const },
  insurance: { aggregate_stress: 0.42, total_loss: 210_000_000, node_count: 3, classification: "GUARDED" as const },
  trade: { aggregate_stress: 0.38, total_loss: 180_000_000, node_count: 3, classification: "LOW" as const },
  fintech: { aggregate_stress: 0.48, total_loss: 280_000_000, node_count: 3, classification: "GUARDED" as const },
  government: { aggregate_stress: 0.55, total_loss: 320_000_000, node_count: 4, classification: "GUARDED" as const },
};

export const MOCK_LIQUIDITY_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "lda_1", action: "Activate emergency bilateral FX swap lines between GCC central banks", action_ar: "تفعيل خطوط مبادلة العملات الثنائية الطارئة بين البنوك المركزية الخليجية",
    sector: "banking", owner: "SAMA + CBUAE", urgency: 95, value: 90,
    regulatory_risk: 0.12, priority: 94, target_node_id: "sama",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 850_000_000,
    cost_usd: 15_000_000, confidence: 0.91,
  },
  {
    id: "lda_2", action: "Deploy emergency repo facility with expanded collateral acceptance", action_ar: "نشر مرفق الريبو الطارئ مع توسيع قبول الضمانات",
    sector: "banking", owner: "SAMA", urgency: 90, value: 85,
    regulatory_risk: 0.15, priority: 88, target_node_id: "interbank_gcc",
    target_lat: 25.20, target_lng: 55.27, loss_avoided_usd: 620_000_000,
    cost_usd: 8_000_000, confidence: 0.88,
  },
  {
    id: "lda_3", action: "Coordinate sovereign wealth fund capital injection to stabilize wholesale funding", action_ar: "تنسيق ضخ رأس المال من صناديق الثروة السيادية لتثبيت التمويل بالجملة",
    sector: "government", owner: "Ministry of Finance", urgency: 82, value: 78,
    regulatory_risk: 0.25, priority: 79, target_node_id: "cbb",
    target_lat: 26.07, target_lng: 50.56, loss_avoided_usd: 410_000_000,
    cost_usd: 45_000_000, confidence: 0.82,
  },
];

export const MOCK_LIQUIDITY_EXPLANATION = {
  narrative_en: "A regional liquidity stress event originating in the GCC interbank market triggers cross-border contagion through three primary channels: (1) overnight lending rate spikes of 280bp forcing emergency central bank intervention, (2) FX reserve drawdowns accelerating across UAE and Saudi Arabia as peg defense mechanisms activate, and (3) wholesale funding market freezes impacting Bahrain's financial services hub. Total estimated loss reaches $2.31B over the 5-day horizon.",
  narrative_ar: "يؤدي حدث ضغط السيولة الإقليمي الناشئ من سوق ما بين البنوك الخليجية إلى عدوى عابرة للحدود عبر ثلاث قنوات رئيسية.",
  methodology: "Institutional macro-financial intelligence: Interbank contagion model with bilateral exposure matrix. 24-node GCC banking knowledge graph with 48 causal edges. Confidence: Monte Carlo 10K iterations.",
  confidence: 0.87,
  total_steps: 5,
};

export const MOCK_LIQUIDITY_TRUST = {
  trace_id: "trc_20260410_093000_liquidity",
  audit_id: "aud_cc_002",
  audit_hash: "sha256:b5e3d9e02f4c8a17f6e3b2d5c9f8e4d3b2a5c8f7e4d3b2a5c8f7e4d3b2a5c8f7",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.87,
  data_sources: ["SAMA Open Data", "CBUAE Reporting", "Bloomberg Terminal", "Reuters Eikon", "BIS Statistics"],
  stages_completed: ["signal_ingest", "graph_activation", "causal_trace", "propagation", "physics", "math", "sector_stress", "decision_gen", "explanation"],
  warnings: ["Interbank rate data: +5min delay", "Bahrain wholesale funding: estimated from proxy"],
};

export const MOCK_LIQUIDITY_LOSS_RANGE = {
  low: 2_060_000_000,
  mid: 2_310_000_000,
  high: 2_560_000_000,
  confidence_pct: 90,
};

export const MOCK_LIQUIDITY_DECISION_DEADLINE = new Date(Date.now() + 24 * 3_600_000).toISOString();

export const MOCK_LIQUIDITY_ASSUMPTIONS: string[] = [
  "Liquidity stress is contained to GCC interbank market (no global contagion)",
  "Central bank reserves sufficient for 60-day intervention window",
  "GCC currency pegs maintained through coordinated defense",
  "No concurrent sovereign default event in smaller GCC states",
];

export const MOCK_LIQUIDITY_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", exposureUsd: 680_000_000, stressLevel: 0.72, primaryDriver: "SAMA — stress at 72%", primaryDriverAr: "مؤسسة النقد — الضغط عند 72%", transmissionChannel: "Interbank liquidity → credit markets → real economy", transmissionChannelAr: "سيولة بين البنوك → أسواق الائتمان → الاقتصاد الحقيقي" },
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", exposureUsd: 520_000_000, stressLevel: 0.68, primaryDriver: "CBUAE — stress at 68%", primaryDriverAr: "مصرف الإمارات المركزي — الضغط عند 68%", transmissionChannel: "AED liquidity buffer → banking sector → trade finance", transmissionChannelAr: "احتياطي السيولة → القطاع المصرفي → تمويل التجارة" },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", exposureUsd: 410_000_000, stressLevel: 0.61, primaryDriver: "Central Bank of Bahrain — stress at 61%", primaryDriverAr: "مصرف البحرين المركزي — الضغط عند 61%", transmissionChannel: "Wholesale funding → sovereign credit → financial services", transmissionChannelAr: "التمويل بالجملة → الائتمان السيادي → الخدمات المالية" },
];

export const MOCK_LIQUIDITY_OUTCOMES = {
  baseCase: {
    label: "Base Case (No Intervention)",
    labelAr: "السيناريو الأساسي (بدون تدخل)",
    lossLow: 2_060_000_000,
    lossHigh: 2_560_000_000,
    recoveryDays: 28,
    description: "Full interbank contagion across GCC banking sector. Recovery dependent on market confidence restoration.",
    descriptionAr: "عدوى كاملة في سوق ما بين البنوك عبر القطاع المصرفي الخليجي.",
  } as OutcomeScenario,
  mitigatedCase: {
    label: "Mitigated Case (Coordinated Response)",
    labelAr: "السيناريو المخفف (استجابة منسقة)",
    lossLow: 720_000_000,
    lossHigh: 1_180_000_000,
    recoveryDays: 14,
    description: "3 coordinated interventions reducing exposure by 55%. Recovery timeline shortened through central bank coordination.",
    descriptionAr: "3 تدخلات منسقة تقلل التعرض بنسبة 55%. تقليص فترة التعافي عبر تنسيق البنوك المركزية.",
  } as OutcomeScenario,
  valueSaved: {
    low: 880_000_000,
    high: 1_840_000_000,
    description: "Estimated value preserved through coordinated central bank intervention across 3 recommended actions.",
    descriptionAr: "القيمة المقدرة المحفوظة من خلال التدخل المنسق للبنوك المركزية عبر 3 إجراءات موصى بها.",
  },
};

export const MOCK_LIQUIDITY_SECTOR_DEPTH: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }> = {
  banking: { topDriver: "Overnight lending rates spike 280bp — counterparty risk repricing", secondOrderRisk: "2 recommended interventions — Activate bilateral FX swap lines + Deploy emergency repo facility", confidenceLow: 0.60, confidenceHigh: 0.76 },
  government: { topDriver: "Sovereign credit spread widens as wholesale funding freezes", secondOrderRisk: "1 recommended intervention — Coordinate sovereign wealth fund capital injection", confidenceLow: 0.47, confidenceHigh: 0.63 },
  insurance: { topDriver: "Credit insurance claims rise on interbank exposure", secondOrderRisk: "Monitoring for secondary transmission effects", confidenceLow: 0.34, confidenceHigh: 0.50 },
};

// ══════════════════════════════════════════════════════════════════════
// Scenario Presets
// ══════════════════════════════════════════════════════════════════════

export type ScenarioKey = "hormuz" | "liquidity";

export const SCENARIO_PRESETS: Array<{ key: ScenarioKey; label: string; labelAr: string; domain: string }> = [
  { key: "hormuz", label: "Hormuz Chokepoint Disruption", labelAr: "اضطراب مضيق هرمز", domain: "ENERGY_TRADE" },
  { key: "liquidity", label: "Regional Liquidity Stress", labelAr: "ضغط السيولة الإقليمي", domain: "BANKING_FINANCE" },
];
