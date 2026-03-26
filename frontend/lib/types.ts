/* =================================================
   Deevo Sim v2 — Core Type Definitions
   Enterprise Decision Simulation Platform
   ================================================= */

// ── Base Enums ──────────────────────────────────

export type EntityType = 'person' | 'organization' | 'topic' | 'region' | 'platform' | 'media' | 'sector'
export type SpreadLevel = 'low' | 'medium' | 'high' | 'critical'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type SentimentDirection = 'positive' | 'negative' | 'mixed' | 'neutral'
export type AgentArchetype = 'reactive' | 'analytical' | 'neutral'
export type AgentPlatform = 'twitter' | 'whatsapp' | 'news' | 'telegram' | 'linkedin'
export type ActionPriority = 'immediate' | 'short-term' | 'monitoring'
export type FactorDirection = 'amplifying' | 'dampening' | 'neutral'

// ── v2 Enterprise Enums ─────────────────────────

export type ScenarioDomain = 'energy' | 'telecom' | 'banking' | 'insurance' | 'policy' | 'brand' | 'supply-chain' | 'security'
export type ScenarioRegion = 'gcc' | 'saudi' | 'kuwait' | 'uae' | 'qatar' | 'bahrain' | 'oman' | 'gcc-wide'
export type TriggerType = 'price-change' | 'leak' | 'announcement' | 'rumor' | 'incident' | 'regulatory' | 'cyberattack' | 'fraud' | 'regulation' | 'social-media' | 'competitor' | 'geopolitical' | 'natural-disaster' | 'cyber-attack' | 'market-shift'
export type SignalType = 'social' | 'media' | 'economic' | 'policy' | 'business' | 'news' | 'regulatory' | 'market' | 'internal' | 'geopolitical'
export type AnnouncementStrategy = 'aggressive' | 'soft' | 'delayed' | 'silent'

// ── Bilingual Content ───────────────────────────

export interface BilingualText {
  en: string
  ar: string
}

// ── Scenario (v2) ───────────────────────────────

export interface Scenario {
  id: string
  title: string
  titleAr?: string
  scenario: string
  raw_text: string
  language: 'ar' | 'en'
  country: string
  category: string
  // v2 enterprise fields
  domain: ScenarioDomain
  region: ScenarioRegion
  trigger: TriggerType
  actors: string[]
  signals: SignalType[]
  constraints?: string[]
  strategy?: AnnouncementStrategy
  riskClass?: RiskLevel
  narrative?: BilingualText
  estimatedImpact?: BusinessImpact
}

// ── Entity (v2) ─────────────────────────────────

export interface Entity {
  id: string
  name: string
  nameAr?: string
  type: EntityType
  weight: number
  description?: string
  // v2 extended
  influenceScore?: number
  trustScore?: number
  propagationScore?: number
  stance?: SentimentDirection
  channels?: AgentPlatform[]
}

// ── Signal ──────────────────────────────────────

export interface Signal {
  id: string
  type: SignalType
  label: BilingualText
  strength: number
  confidence: number
  trend: 'rising' | 'falling' | 'stable'
  volatility: 'low' | 'medium' | 'high'
  source: string
}

// ── Business Impact ─────────────────────────────

export interface BusinessImpact {
  financial: { score: number; label: string; labelAr?: string; detail: string; detailAr?: string }
  customer: { score: number; label: string; labelAr?: string; detail: string; detailAr?: string }
  regulatory: { score: number; label: string; labelAr?: string; detail: string; detailAr?: string }
  reputation: { score: number; label: string; labelAr?: string; detail: string; detailAr?: string }
}

// ── Graph ───────────────────────────────────────

export interface GraphNode {
  id: string
  label: string
  type: EntityType
  weight: number
  x?: number
  y?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string
  weight: number
}

// ── Simulation Step ─────────────────────────────

export interface SimulationStep {
  id: number
  title: string
  titleAr?: string
  description: string
  descriptionAr?: string
  timestamp: string
  sentiment: number
  visibility: number
  events: string[]
}

// ── Decision Layer ──────────────────────────────

export interface RecommendedAction {
  id: string
  priority: ActionPriority
  action: string
  actionAr?: string
  rationale: string
  rationaleAr?: string
  timeframe: string
  impact: 'high' | 'medium' | 'low'
}

export interface ExplainabilityItem {
  factor: string
  factorAr?: string
  direction: FactorDirection
  weight: number
  description: string
  descriptionAr?: string
}

export interface ScenarioNarrative {
  title: string
  titleAr?: string
  subtitle: string
  subtitleAr?: string
  summary: string
  summaryAr?: string
  riskDescription: string
  riskDescriptionAr?: string
}

export interface DecisionOutput {
  riskLevel: RiskLevel
  expectedSpread: number
  sentiment: SentimentDirection
  primaryDriver: string
  primaryDriverAr?: string
  criticalTimeWindow: string
  criticalTimeWindowAr?: string
  spreadVelocity?: string
  spreadVelocityAr?: string
  recommendedActions: RecommendedAction[]
  explanation: ExplainabilityItem[]
  narrative: ScenarioNarrative
  businessImpact?: BusinessImpact
}

// ── Intelligence Brief ──────────────────────────

export interface IntelligenceBrief {
  scenarioSummary: BilingualText
  timelineNarrative: BilingualText
  keyDrivers: BilingualText[]
  entityInfluence: { entity: string; entityAr?: string; role: string; roleAr?: string; score: number }[]
  forecast: BilingualText
  businessImpact: BilingualText
  recommendedActions: BilingualText[]
  confidence: { score: number; assumptions: BilingualText[] }
}

// ── Simulation Report ───────────────────────────

export interface SimulationReport {
  prediction: string
  predictionAr?: string
  mainDriver: string
  mainDriverAr?: string
  spreadLevel: SpreadLevel
  confidence: number
  topInfluencers: string[]
  keyObservations: string[]
  keyObservationsAr?: string[]
  decision: DecisionOutput
  brief?: IntelligenceBrief
}

// ── Chat ────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'user' | 'analyst'
  content: string
  timestamp: string
}

// ── Agent ───────────────────────────────────────

export interface Agent {
  id: string
  name: string
  nameAr?: string
  archetype: AgentArchetype
  platform: AgentPlatform
  influence: number
  region: string
  description?: string
  descriptionAr?: string
}

// ── Simulation Input ────────────────────────────

export interface SimulationInput {
  scenarioId: string
  scenarioTitle: string
  entities: Entity[]
  agents: Agent[]
  hasGovernmentResponse: boolean
  hasInfluencerAmplification: boolean
  hasMediaPickup: boolean
  baseSentiment: SentimentDirection
}

// ── Structured JSON Output ──────────────────────

export interface SimulationJSON {
  scenario_title: string
  risk_level: RiskLevel
  expected_spread: string
  sentiment: SentimentDirection
  primary_driver: string
  time_window: string
  explanation: string[]
  recommended_actions: string[]
  confidence: string
  key_entities: string[]
    }
