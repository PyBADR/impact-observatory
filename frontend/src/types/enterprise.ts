/**
 * Impact Observatory | مرصد الأثر — Enterprise Intelligence Types
 * Layer: UI (L6) — Types for Enterprise Decision Intelligence views
 * 
 * These types extend the observatory types for enterprise-specific UI concerns.
 * Backend contracts remain the source of truth in observatory.ts.
 */

import type {
  DecisionAction,
  DecisionPlan,
  ExplanationPack,
  CausalStep,
  RunResult,
  Classification,
  UnifiedRiskScore,
  FinancialImpact,
  TimelineStep,
  RegulatoryEvent,
  ScenarioCatalogEntry,
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  InsuranceStress,
  BankingStress,
  FintechStress,
} from "./observatory";

// ── Decision Timeline ──
export type TimelineEventType =
  | "signal_ingested"
  | "scenario_triggered"
  | "simulation_started"
  | "simulation_completed"
  | "policy_check"
  | "risk_scored"
  | "decision_proposed"
  | "decision_reviewed"
  | "decision_approved"
  | "decision_rejected"
  | "decision_executed"
  | "outcome_observed"
  | "override_applied";

export interface DecisionTimelineEvent {
  id: string;
  timestamp: string;
  type: TimelineEventType;
  label: string;
  label_ar: string;
  description: string;
  actor?: string;
  severity?: Classification;
  metadata?: Record<string, unknown>;
}

// ── Policy Graph ──
export type PolicyNodeType = "rule" | "constraint" | "threshold" | "decision_path" | "action";

export interface PolicyNode {
  id: string;
  label: string;
  label_ar: string;
  type: PolicyNodeType;
  sector: string;
  weight: number;
  active: boolean;
  triggered: boolean;
  description?: string;
}

export interface PolicyEdge {
  source: string;
  target: string;
  label: string;
  type: "requires" | "blocks" | "enables" | "triggers";
  weight: number;
}

// ── Risk Heatmap ──
export interface RiskHeatmapCell {
  entityId: string;
  entityName: string;
  sector: string;
  dimension: string;
  value: number;
  severity: Classification;
}

export interface RiskHeatmapData {
  cells: RiskHeatmapCell[];
  entities: string[];
  dimensions: string[];
  maxValue: number;
}

// ── Scenario Simulation ──
export interface SimulationParams {
  templateId: string;
  severity: number;
  horizonHours: number;
  label?: string;
}

export interface SimulationComparison {
  before: {
    totalLoss: number;
    peakDay: number;
    affectedEntities: number;
    avgStress: number;
  } | null;
  after: {
    totalLoss: number;
    peakDay: number;
    affectedEntities: number;
    avgStress: number;
  };
  delta: {
    lossChange: number;
    lossChangePct: number;
    stressChange: number;
    entityChange: number;
  } | null;
}

// ── Explainability ──
export interface ExplainabilityFactor {
  id: string;
  label: string;
  label_ar: string;
  weight: number;
  contribution: number; // -1 to 1
  type: "risk" | "policy" | "market" | "geopolitical" | "model";
  description: string;
}

export interface DecisionExplanation {
  decisionId: string;
  runId: string;
  scenarioLabel: string;
  reasoning: string;
  reasoning_ar: string;
  factors: ExplainabilityFactor[];
  triggeredRules: string[];
  causalChain: CausalStep[];
  confidence: number;
  methodology: string;
}

// ── Enterprise Dashboard ──
export interface EnterpriseKPI {
  id: string;
  label: string;
  label_ar: string;
  value: number | string;
  unit: string;
  trend?: "up" | "down" | "stable";
  severity?: Classification;
  sparkline?: number[];
}

// ── Bilingual Labels ──
export const ENTERPRISE_LABELS = {
  en: {
    dashboard: "Enterprise Intelligence",
    decisions: "Decision Queue",
    simulation: "Scenario Simulation",
    timeline: "Decision Timeline",
    policyGraph: "Policy Graph",
    riskHeatmap: "Risk Heatmap",
    explainability: "Decision Explainability",
    metrics: "Key Metrics",
    filters: "Filters",
    runSimulation: "Run Simulation",
    comparing: "Comparing Results",
    noData: "No data available",
    loading: "Loading intelligence...",
    severity: "Severity",
    sector: "Sector",
    status: "Status",
    totalLoss: "Total Loss",
    peakDay: "Peak Impact Day",
    confidence: "Confidence",
    actions: "Recommended Actions",
    causalChain: "Causal Chain",
    beforeAfter: "Before / After",
  },
  ar: {
    dashboard: "الذكاء المؤسسي",
    decisions: "قائمة القرارات",
    simulation: "محاكاة السيناريو",
    timeline: "الجدول الزمني للقرار",
    policyGraph: "رسم السياسات",
    riskHeatmap: "خريطة المخاطر",
    explainability: "تفسير القرار",
    metrics: "المؤشرات الرئيسية",
    filters: "الفلاتر",
    runSimulation: "تشغيل المحاكاة",
    comparing: "مقارنة النتائج",
    noData: "لا توجد بيانات",
    loading: "جاري تحميل الذكاء...",
    severity: "الخطورة",
    sector: "القطاع",
    status: "الحالة",
    totalLoss: "إجمالي الخسائر",
    peakDay: "يوم الذروة",
    confidence: "الثقة",
    actions: "الإجراءات الموصى بها",
    causalChain: "سلسلة السببية",
    beforeAfter: "قبل / بعد",
  },
} as const;
