import { apiRequest } from './client'

export interface ScenarioAnchor {
    id: string
    label: string
    scenarioType: string
    estimatedImpactUSD: number
    primarySectors: string[]
}

export interface PortfolioArchetype {
    id: string
    label: string
    entityType: string
}

export interface ScenarioResult {
    scenarioType: string
    archetypeId: string
    totalLoss: number
    costCredibility: string
    calibrationScore: number
    calibrationSupport: string
    deploymentSuitability: string
    overallTrustLevel: string
    lossBySector: Record<string, number>
    drivers: string[]
    narrative: string
}

export interface TrustStatus {
    costCredibility: string
    calibrationScore: number
    supportedFields: number
    weakFields: number
    unsupportedFields: number
    fileReferences: number
    totalReferences: number
}

export async function fetchScenarios(): Promise<ScenarioAnchor[]> {
    const res = await apiRequest<{ scenarios: ScenarioAnchor[] }>('/demo/scenarios')
    return res.scenarios
}

export async function fetchArchetypes(): Promise<PortfolioArchetype[]> {
    const res = await apiRequest<{ archetypes: PortfolioArchetype[] }>('/demo/archetypes')
    return res.archetypes
}

export async function runScenario(
    scenarioType: string,
    archetypeId: string,
    severity = 0.8,
    durationHours = 72
  ): Promise<ScenarioResult> {
    return apiRequest<ScenarioResult>('/demo/run-scenario', {
          method: 'POST',
          body: JSON.stringify({ scenarioType, archetypeId, severity, durationHours }),
    })
}

export async function fetchTrustStatus(): Promise<TrustStatus> {
    return apiRequest<TrustStatus>('/demo/trust-status')
}

export async function checkBackendHealth(): Promise<boolean> {
    try {
          const res = await apiRequest<{ status: string }>('/health', undefined, 5000)
          return res.status === 'ok'
    } catch {
          return false
    }
}
