/**
 * ══════════════════════════════════════════════════════════════
 * IMPACT OBSERVATORY — RUN PERSISTENCE STORE
 * ══════════════════════════════════════════════════════════════
 * Stores scenario run results with full provenance.
 * In-memory for pilot; interface designed for DB migration.
 *
 * Production migration path:
 *   - Vercel Postgres (recommended)
 *   - Supabase / PlanetScale
 *   - Replace InMemoryRunStore with PostgresRunStore
 * ══════════════════════════════════════════════════════════════
 */

export interface StoredRun {
  runId: string
  traceId: string
  auditId: string
  tenantId: string
  userId: string
  workspace: string

  // Inputs
  scenarioId: string
  scenarioLabel: string
  severity: number
  analysisMode: 'deterministic' | 'probabilistic'

  // Propagation outputs
  nodeImpacts: Record<string, number>
  sectorImpacts: Array<{
    sector: string
    avgImpact: number
    maxImpact: number
    nodeCount: number
    topNode: string
  }>
  propagationChain: Array<{
    from: string
    to: string
    impact: number
    iteration: number
  }>
  totalLoss: number
  confidence: number
  systemEnergy: number
  propagationDepth: number
  spreadLevel: string

  // Engine outputs
  engineId: string
  engineSteps: Array<{
    id: string
    label: string
    value: number
    impactPct: number
    direction: string
  }>
  totalExposure: number
  engineNarrative: string

  // Decision outputs
  decisionPressureScore: number
  urgencyLevel: string
  decisionConfidence: number
  mitigationEffectiveness: number
  expectedLossBefore: number
  expectedLossAfter: number
  recommendedActions: Array<{
    domain: string
    action: string
    priority: number
    timeframe: string
    expectedReduction: number
    cost: string
  }>
  decisionSummary: string

  // Metadata
  modelVersion: string
  engineVersion: string
  graphVersion: string
  timestamp: string
  durationMs: number
  environment: string
  status: 'success' | 'error'
  error?: string
}

/** Store interface — swap implementation for production DB */
export interface RunStore {
  save(run: StoredRun): void
  get(runId: string): StoredRun | undefined
  getByTenant(tenantId: string, limit?: number): StoredRun[]
  getByTrace(traceId: string): StoredRun | undefined
  count(): number
}

/** In-memory implementation — ephemeral across serverless cold starts */
class InMemoryRunStore implements RunStore {
  private runs = new Map<string, StoredRun>()

  save(run: StoredRun): void {
    this.runs.set(run.runId, run)
  }

  get(runId: string): StoredRun | undefined {
    return this.runs.get(runId)
  }

  getByTenant(tenantId: string, limit = 50): StoredRun[] {
    const results: StoredRun[] = []
    const allRuns = Array.from(this.runs.values())
    for (const run of allRuns) {
      if (run.tenantId === tenantId) results.push(run)
    }
    return results.slice(-limit)
  }

  getByTrace(traceId: string): StoredRun | undefined {
    const allRuns = Array.from(this.runs.values())
    for (const run of allRuns) {
      if (run.traceId === traceId) return run
    }
    return undefined
  }

  count(): number {
    return this.runs.size
  }
}

// Singleton store instance
export const runStore: RunStore = new InMemoryRunStore()
