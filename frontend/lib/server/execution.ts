/**
 * ══════════════════════════════════════════════════════════════
 * IMPACT OBSERVATORY — SERVER-SIDE SCENARIO EXECUTION
 * ══════════════════════════════════════════════════════════════
 * Runs the full intelligence pipeline server-side:
 *   Scenario → Propagation → Engine → Decision
 * Returns typed results with full trace provenance.
 * ══════════════════════════════════════════════════════════════
 */

import { gccNodes, gccEdges, gccScenarios } from '../gcc-graph'
import { runPropagation, type PropagationResult } from '../propagation-engine'
import { getScenarioEngine, type ScenarioEngineResult } from '../scenario-engines'
import { computeDecision, type DecisionResult, type ScientistState } from '../decision-engine'
import { generateTraceId, generateRunId } from './trace'
import { createAuditEntry } from './audit'
import { runStore, type StoredRun } from './store'
import type { AuthContext } from './auth'

export const MODEL_VERSION = '7.0.0'
export const ENGINE_VERSION = '2.0.0'
export const GRAPH_VERSION = '1.5.0'

export interface ScenarioExecutionInput {
  scenarioId: string
  severity: number
  analysisMode?: 'deterministic' | 'probabilistic'
}

export interface ScenarioExecutionResult {
  runId: string
  traceId: string
  auditId: string
  scenarioId: string
  scenarioLabel: string
  inputs: {
    severity: number
    analysisMode: string
  }
  metrics: {
    totalLoss: number
    confidence: number
    systemEnergy: number
    propagationDepth: number
    spreadLevel: string
    totalExposure: number
  }
  nodeImpacts: Record<string, number>
  sectorImpacts: Array<{
    sector: string
    sectorLabel: string
    avgImpact: number
    maxImpact: number
    nodeCount: number
    topNode: string
  }>
  explanationChain: Array<{
    from: string
    to: string
    impact: number
    iteration: number
  }>
  engineResult: {
    engineId: string
    steps: Array<{
      id: string
      label: string
      formula: string
      value: number
      impactPct: number
      direction: string
    }>
    totalExposure: number
    narrative: string
    keyMetrics: Array<{ label: string; value: string; color: string }>
  }
  decision: {
    decisionPressureScore: number
    urgencyLevel: string
    decisionConfidence: number
    mitigationEffectiveness: number
    expectedLossBefore: number
    expectedLossAfter: number
    decisionSummary: string
    whyTheseActions: string
    recommendedActions: Array<{
      domain: string
      action: string
      priority: number
      urgency: string
      timeframe: string
      expectedReduction: number
      cost: string
      tradeoff: string
      confidence: number
    }>
    resourcePriorities: Array<{
      resource: string
      priority: number
      reason: string
    }>
  }
  model: {
    modelVersion: string
    engineVersion: string
    graphVersion: string
    nodeCount: number
    edgeCount: number
    scenarioCount: number
  }
  timestamp: string
  durationMs: number
  environment: string
}

export function executeScenario(
  input: ScenarioExecutionInput,
  auth: AuthContext,
  environment: string,
): ScenarioExecutionResult {
  const startTime = Date.now()
  const traceId = generateTraceId()
  const runId = generateRunId()

  // ── Find scenario ──
  const scenario = gccScenarios.find(s => s.id === input.scenarioId)
  if (!scenario) {
    throw new Error(`Scenario not found: ${input.scenarioId}`)
  }

  // ── Severity-modified shocks (matches frontend behavior) ──
  const modShocks = scenario.shocks.map(s => ({
    ...s, impact: Math.min(1, s.impact * input.severity),
  }))

  // ── Run propagation ──
  const propagation: PropagationResult = runPropagation(
    gccNodes,
    gccEdges,
    modShocks,
    6,   // maxIterations
    'en', // lang
    0.05, // decayRate
  )

  // ── Run scenario engine ──
  const engineMeta = getScenarioEngine(scenario.engineId || scenario.id)
  const engineResult: ScenarioEngineResult = engineMeta.compute(propagation.nodeImpacts, input.severity)

  // ── Compute scientist state ──
  const sectorSpread = propagation.affectedSectors.length
  const energy = propagation.systemEnergy
  const shockClass = (energy > 8 && propagation.propagationDepth > 4 && sectorSpread >= 4) ? 'critical' as const
    : (energy > 4 || (propagation.propagationDepth > 3 && sectorSpread >= 3) || propagation.totalLoss > 30) ? 'severe' as const
    : (energy > 1.5 || sectorSpread >= 2) ? 'moderate' as const : 'low' as const

  const geoNodes = gccNodes.filter(n => n.layer === 'geography')
  const regionalStress = geoNodes.length > 0
    ? geoNodes.reduce((sum, n) => sum + Math.abs(propagation.nodeImpacts.get(n.id) || 0), 0) / geoNodes.length
    : 0

  const scientistState: ScientistState = {
    energy,
    confidence: propagation.confidence,
    uncertainty: 1 - propagation.confidence,
    regionalStress,
    shockClass,
    stage: propagation.propagationDepth <= 2 ? 'initial' : propagation.propagationDepth <= 4 ? 'cascading' : 'saturated',
    propagationDepth: propagation.propagationDepth,
    totalExposure: engineResult.totalExposure || propagation.totalLoss,
    dominantSector: propagation.affectedSectors.length > 0
      ? propagation.affectedSectors.reduce((a, b) => a.avgImpact > b.avgImpact ? a : b)
      : null,
  }

  // ── Compute decision ──
  const decision: DecisionResult = computeDecision(
    propagation,
    engineResult,
    scientistState,
    scenario.engineId || scenario.id,
  )

  const durationMs = Date.now() - startTime

  // ── Convert nodeImpacts Map to Record ──
  const nodeImpactsRecord: Record<string, number> = {}
  propagation.nodeImpacts.forEach((val, key) => {
    nodeImpactsRecord[key] = val
  })

  // ── Audit ──
  const auditEntry = createAuditEntry({
    traceId,
    runId,
    tenantId: auth.tenantId,
    userId: auth.userId,
    action: 'run_scenario',
    endpoint: '/api/run-scenario',
    method: 'POST',
    inputs: { scenarioId: input.scenarioId, severity: input.severity },
    status: 'success',
    statusCode: 200,
    durationMs,
    metadata: { environment, modelVersion: MODEL_VERSION },
  })

  // ── Persist run ──
  const storedRun: StoredRun = {
    runId,
    traceId,
    auditId: auditEntry.auditId,
    tenantId: auth.tenantId,
    userId: auth.userId,
    workspace: auth.workspace,
    scenarioId: input.scenarioId,
    scenarioLabel: scenario.title,
    severity: input.severity,
    analysisMode: input.analysisMode || 'deterministic',
    nodeImpacts: nodeImpactsRecord,
    sectorImpacts: propagation.affectedSectors.map(s => ({
      sector: s.sector,
      avgImpact: s.avgImpact,
      maxImpact: s.maxImpact,
      nodeCount: s.nodeCount,
      topNode: s.topNode,
    })),
    propagationChain: propagation.propagationChain.map(s => ({
      from: s.from,
      to: s.to,
      impact: s.impact,
      iteration: s.iteration,
    })),
    totalLoss: propagation.totalLoss,
    confidence: propagation.confidence,
    systemEnergy: propagation.systemEnergy,
    propagationDepth: propagation.propagationDepth,
    spreadLevel: propagation.spreadLevel,
    engineId: engineResult.engineId,
    engineSteps: engineResult.steps.map(s => ({
      id: s.id,
      label: s.label,
      value: s.value,
      impactPct: s.impactPct,
      direction: s.direction,
    })),
    totalExposure: engineResult.totalExposure,
    engineNarrative: engineResult.narrative,
    decisionPressureScore: decision.decisionPressureScore,
    urgencyLevel: decision.urgencyLevel,
    decisionConfidence: decision.decisionConfidence,
    mitigationEffectiveness: decision.mitigationEffectiveness,
    expectedLossBefore: decision.expectedLossBefore,
    expectedLossAfter: decision.expectedLossAfter,
    recommendedActions: decision.recommendedActions.map(a => ({
      domain: a.domain,
      action: a.action,
      priority: a.priority,
      timeframe: a.timeframe,
      expectedReduction: a.expectedReduction,
      cost: a.cost,
    })),
    decisionSummary: decision.decisionSummary,
    modelVersion: MODEL_VERSION,
    engineVersion: ENGINE_VERSION,
    graphVersion: GRAPH_VERSION,
    timestamp: new Date().toISOString(),
    durationMs,
    environment,
    status: 'success',
  }
  runStore.save(storedRun)

  // ── Build response ──
  return {
    runId,
    traceId,
    auditId: auditEntry.auditId,
    scenarioId: input.scenarioId,
    scenarioLabel: scenario.title,
    inputs: {
      severity: input.severity,
      analysisMode: input.analysisMode || 'deterministic',
    },
    metrics: {
      totalLoss: propagation.totalLoss,
      confidence: propagation.confidence,
      systemEnergy: propagation.systemEnergy,
      propagationDepth: propagation.propagationDepth,
      spreadLevel: propagation.spreadLevel,
      totalExposure: engineResult.totalExposure,
    },
    nodeImpacts: nodeImpactsRecord,
    sectorImpacts: propagation.affectedSectors.map(s => ({
      sector: s.sector,
      sectorLabel: s.sectorLabel,
      avgImpact: s.avgImpact,
      maxImpact: s.maxImpact,
      nodeCount: s.nodeCount,
      topNode: s.topNode,
    })),
    explanationChain: propagation.propagationChain.slice(0, 50).map(s => ({
      from: s.from,
      to: s.to,
      impact: s.impact,
      iteration: s.iteration,
    })),
    engineResult: {
      engineId: engineResult.engineId,
      steps: engineResult.steps.map(s => ({
        id: s.id,
        label: s.label,
        formula: s.formula,
        value: s.value,
        impactPct: s.impactPct,
        direction: s.direction,
      })),
      totalExposure: engineResult.totalExposure,
      narrative: engineResult.narrative,
      keyMetrics: engineResult.keyMetrics.map(m => ({
        label: m.label,
        value: m.value,
        color: m.color,
      })),
    },
    decision: {
      decisionPressureScore: decision.decisionPressureScore,
      urgencyLevel: decision.urgencyLevel,
      decisionConfidence: decision.decisionConfidence,
      mitigationEffectiveness: decision.mitigationEffectiveness,
      expectedLossBefore: decision.expectedLossBefore,
      expectedLossAfter: decision.expectedLossAfter,
      decisionSummary: decision.decisionSummary,
      whyTheseActions: decision.whyTheseActions,
      recommendedActions: decision.recommendedActions.map(a => ({
        domain: a.domain,
        action: a.action,
        priority: a.priority,
        urgency: a.urgency,
        timeframe: a.timeframe,
        expectedReduction: a.expectedReduction,
        cost: a.cost,
        tradeoff: a.tradeoff,
        confidence: a.confidence,
      })),
      resourcePriorities: decision.resourcePriorities.map(r => ({
        resource: r.resource,
        priority: r.priority,
        reason: r.reason,
      })),
    },
    model: {
      modelVersion: MODEL_VERSION,
      engineVersion: ENGINE_VERSION,
      graphVersion: GRAPH_VERSION,
      nodeCount: gccNodes.length,
      edgeCount: gccEdges.length,
      scenarioCount: gccScenarios.length,
    },
    timestamp: new Date().toISOString(),
    durationMs,
    environment,
  }
}
