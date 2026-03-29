/* âââââââââââââââââââââââââââââââââââââââââââââââ
   Deevo Sim â Core Type Definitions
   âââââââââââââââââââââââââââââââââââââââââââââââ */

/** Scenario seed input */
export interface Scenario {
  id: string
  title: string
  scenario: string
  raw_text: string
  language: 'ar' | 'en'
  country: string
  category: string
}

/** Extracted entity from scenario parsing */
export interface Entity {
  id: string
  name: string
  type: EntityType
  weight: number
}

export type EntityType =
  | 'Topic'
  | 'Region'
  | 'Organization'
  | 'Person'
  | 'Platform'
  | 'Event'

/** Graph node for React Flow visualization */
export interface GraphNode {
  id: string
  position: { x: number; y: number }
  data: { label: string; type: string; weight: number }
  type: string
}

/** Graph edge for React Flow visualization */
export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string
  animated?: boolean
}

/** Single simulation time-step */
export interface SimulationStep {
  step: number
  label: string
  summary: string
  sentiment_score: number
  visibility_score: number
  events: string[]
}

/** Simulation intelligence report */
export interface SimulationReport {
  prediction: string
  main_driver: string
  top_influencers: string[]
  spread_level: SpreadLevel
  confidence: number
  timeline_summary: string[]
  graph_observations: string[]
}

export type SpreadLevel = 'low' | 'medium' | 'high'

/** Chat message */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

/** GCC agent persona */
export interface Agent {
  id: string
  name: string
  archetype: AgentArchetype
  influence: number
  platform: 'Twitter' | 'WhatsApp' | 'News'
  behavior: 'Reactive' | 'Analytical' | 'Neutral'
  sentiment: 'Positive' | 'Negative' | 'Neutral'
}

export type AgentArchetype =
  | 'Saudi Citizen'
  | 'Kuwaiti Citizen'
  | 'Influencer'
  | 'Media Account'
  | 'Government Voice'
  | 'Youth User'

/* âââââââââââââââââââââââââââââââââââââââââââââââ
   GCC Reality Graph â Extended Types
   âââââââââââââââââââââââââââââââââââââââââââââââ */

/** 5-layer GCC dependency model */
export type GCCLayer = 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society'

/** Propagation chain step for explanation output */
export interface PropagationChainStep {
  from: string
  fromLabel: string
  to: string
  toLabel: string
  weight: number
  impact: number
  label: string
}

/** Sector-level impact aggregate */
export interface SectorImpactData {
  sector: GCCLayer
  sectorLabel: string
  avgImpact: number
  maxImpact: number
  nodeCount: number
  topNode: string
  color: string
}

/** Top causal driver in propagation */
export interface DriverData {
  nodeId: string
  label: string
  impact: number
  layer: GCCLayer
  outDegree: number
}

/** Full simulation result with causal reasoning */
export interface SimulationOutput {
  totalLoss: number
  affectedSectors: SectorImpactData[]
  topDrivers: DriverData[]
  propagationChain: string[]
  confidence: number
  explanation: string
  spreadLevel: 'low' | 'medium' | 'high' | 'critical'
  nodeImpacts: Record<string, number>
  scenarioId: string
  runId: string
  timestamp: string
}
