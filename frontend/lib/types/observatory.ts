/* ════════════════════════════════════════════════════════════════
   Impact Observatory | مرصد الأثر — TypeScript Domain Types
   Mirrors: backend/app/schemas/observatory.py (ObservatoryOutput)
   Schema Version: v1
   ════════════════════════════════════════════════════════════════ */

// ── Severity & Stress Levels ──

export type SeverityCode = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type StressLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type AlertLevel = 'NORMAL' | 'WATCH' | 'WARNING' | 'CRITICAL'
export type Sector = 'banking' | 'insurance' | 'fintech' | 'macroeconomic'
export type GCCLayer = 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society'
export type DecisionStatus = 'PENDING_REVIEW' | 'APPROVED' | 'EXECUTING'
export type Language = 'ar' | 'en'

// ── Stage 1: Scenario Input ──

export interface ScenarioInput {
  id: string
  name: string
  name_ar: string
  severity: number        // 0.0–1.0
  duration_days: number   // ≥1
  description: string
}

// ── Stage 5: Financial Impact ──

export interface FinancialImpact {
  headline_loss_usd: number   // ≥0, in billions for display
  peak_day: number            // 1-indexed
  time_to_failure_days: number
  severity_code: SeverityCode
  confidence: number          // 0.0–1.0
}

// ── Stage 6: Sector Stress ──

export interface BankingStress {
  liquidity_gap_usd: number
  capital_adequacy_ratio: number    // 0.0–2.0
  interbank_rate_spike: number      // basis points 0–1000
  time_to_liquidity_breach_days: number
  fx_reserve_drawdown_pct: number   // 0–100
  stress_level: StressLevel
  stress_score: number              // 0–100 composite gauge
}

export interface InsuranceStress {
  claims_surge_pct: number          // 0–1000
  reinsurance_trigger: boolean
  combined_ratio: number            // 0–5.0
  solvency_margin_pct: number       // -100–100
  time_to_insolvency_days: number
  premium_adequacy: number          // 0–2.0
  stress_level: StressLevel
  stress_score: number              // 0–100 composite gauge
}

export interface FintechStress {
  payment_failure_rate: number      // 0.0–1.0 fraction
  settlement_delay_hours: number    // 0–720
  gateway_downtime_pct: number      // 0–100
  digital_banking_disruption: number // 0.0–1.0 fraction
  time_to_payment_failure_days: number
  stress_level: StressLevel
  stress_score: number              // 0–100 composite gauge
}

// ── Stage 3: Graph Snapshot ──

export interface Entity {
  id: string
  name: string
  name_ar: string
  layer: GCCLayer
  sector: string
  severity: number    // 0.0–1.0
  metadata: Record<string, unknown>
}

export interface Edge {
  source: string
  target: string
  weight: number              // 0.0–1.0
  propagation_factor: number  // 0.0–1.0
  edge_type: string
}

// ── Stage 4: Propagation ──

export interface FlowState {
  timestep: number
  entity_states: Record<string, number>
  total_stress: number
  peak_entity: string
  converged: boolean
}

// ── Stage 7: Regulatory ──

export interface RegulatoryState {
  pdpl_compliant: boolean
  ifrs17_impact: number         // billions USD
  basel3_car_floor: number      // 0.0–1.0 (8% default)
  sama_alert_level: AlertLevel
  cbuae_alert_level: AlertLevel
  sanctions_exposure: number    // 0.0–1.0
  regulatory_triggers: string[]
}

// ── Stage 8: Decision ──

export interface DecisionAction {
  id: string
  rank: number                  // 1=highest, 2, 3 (0=unranked)
  title: string
  title_ar: string
  urgency: number               // 0.0–1.0
  value: number                 // 0.0–1.0
  priority: number              // 0.0–1.0 (5-factor composite)
  feasibility: number           // 0.0–1.0 (probability × resource)
  time_effect: number           // 0.0–1.0 (decay factor)
  cost_usd: number
  loss_avoided_usd: number
  regulatory_risk: number       // 0.0–1.0
  sector: Sector
  description: string
  status: DecisionStatus        // human-in-the-loop governance
}

export interface DecisionPlan {
  plan_id: string
  name: string
  name_ar: string
  actions: DecisionAction[]
  total_cost_usd: number
  total_loss_avoided_usd: number
  net_benefit_usd: number
  execution_days: number
  sectors_covered: string[]
}

// ── Stage 9: Explanation ──

export interface ExplanationPack {
  summary_en: string
  summary_ar: string
  key_findings: Array<{ en: string; ar: string }>
  causal_chain: string[]
  confidence_note: string
  data_sources: string[]
  audit_trail: Record<string, unknown>
}

// ── Stage 10: Observatory Output (canonical contract) ──

export interface ObservatoryOutput {
  // VersionedModel base
  schema_version: string          // "v1" (frozen)

  // Pipeline tracking
  pipeline_stages_completed: number  // 0–10

  // Stage 1
  scenario: ScenarioInput

  // Stage 3
  entities: Entity[]
  edges: Edge[]

  // Stage 4
  flow_states: FlowState[]

  // Stage 5
  financial_impact: FinancialImpact

  // Stage 6
  banking_stress: BankingStress
  insurance_stress: InsuranceStress
  fintech_stress: FintechStress

  // Stage 7
  regulatory: RegulatoryState

  // Stage 8
  decisions: DecisionAction[]
  decision_plan: DecisionPlan | null

  // Stage 9
  explanation: ExplanationPack | null

  // Stage 10: Output metadata
  timestamp: string               // ISO 8601
  audit_hash: string              // SHA-256
  computed_in_ms: number
  runtime_flow: string[]
  stage_timings: Record<string, number>
}

// ── Display Helpers ──

/** Stress score thresholds for gauge colors */
export const STRESS_THRESHOLDS = {
  LOW:      { max: 25,  color: '#22C55E' },  // green
  MEDIUM:   { max: 50,  color: '#F59E0B' },  // amber
  HIGH:     { max: 75,  color: '#F97316' },  // orange
  CRITICAL: { max: 100, color: '#EF4444' },  // red
} as const

/** Map stress_score (0-100) to StressLevel */
export function scoreToLevel(score: number): StressLevel {
  if (score >= 75) return 'CRITICAL'
  if (score >= 50) return 'HIGH'
  if (score >= 25) return 'MEDIUM'
  return 'LOW'
}

/** Map stress_score to gauge color */
export function scoreToColor(score: number): string {
  if (score >= 75) return STRESS_THRESHOLDS.CRITICAL.color
  if (score >= 50) return STRESS_THRESHOLDS.HIGH.color
  if (score >= 25) return STRESS_THRESHOLDS.MEDIUM.color
  return STRESS_THRESHOLDS.LOW.color
}

/** Decision status display labels (bilingual) */
export const STATUS_LABELS: Record<DecisionStatus, { en: string; ar: string }> = {
  PENDING_REVIEW: { en: 'Pending Review', ar: 'قيد المراجعة' },
  APPROVED:       { en: 'Approved',       ar: 'معتمد' },
  EXECUTING:      { en: 'Executing',      ar: 'قيد التنفيذ' },
}
