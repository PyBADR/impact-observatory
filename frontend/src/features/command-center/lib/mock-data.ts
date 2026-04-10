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
  label: "Strait of Hormuz Partial Blockage",
  label_ar: "إغلاق جزئي لمضيق هرمز",
  severity: 0.72,
  horizon_hours: 168,
  domain: "MARITIME",
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
  { sector: "infrastructure", sectorLabel: "Infrastructure", avgImpact: 0.73, maxImpact: 0.88, nodeCount: 4, topNode: "ras_tanura", color: "#EF4444" },
  { sector: "economy", sectorLabel: "Economy", avgImpact: 0.68, maxImpact: 0.78, nodeCount: 5, topNode: "brent_crude", color: "#F59E0B" },
  { sector: "finance", sectorLabel: "Finance", avgImpact: 0.50, maxImpact: 0.58, nodeCount: 4, topNode: "gcc_insurance", color: "#3B82F6" },
  { sector: "geography", sectorLabel: "Geography", avgImpact: 0.88, maxImpact: 0.88, nodeCount: 1, topNode: "hormuz_strait", color: "#8B5CF6" },
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
  methodology: "9-layer deterministic simulation: Signal → Graph → Causal → Propagation → Physics → Math → Sectors → Decision → Explanation. 76-node GCC knowledge graph with 190 causal edges. Confidence interval: Monte Carlo 10K iterations.",
  confidence: 0.84,
  total_steps: 7,
};

// ── Sector Rollups ────────────────────────────────────────────────────

export const MOCK_SECTOR_ROLLUPS = {
  banking: { aggregate_stress: 0.52, total_loss: 890_000_000, node_count: 6, classification: "MODERATE" as const },
  insurance: { aggregate_stress: 0.58, total_loss: 410_000_000, node_count: 4, classification: "MODERATE" as const },
  fintech: { aggregate_stress: 0.35, total_loss: 120_000_000, node_count: 3, classification: "LOW" as const },
  energy: { aggregate_stress: 0.78, total_loss: 2_100_000_000, node_count: 5, classification: "ELEVATED" as const },
  trade: { aggregate_stress: 0.67, total_loss: 750_000_000, node_count: 4, classification: "ELEVATED" as const },
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
