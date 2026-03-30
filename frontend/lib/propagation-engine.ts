/* ═══════════════════════════════════════════════════════════════
   Propagation Engine — Causal Impact Computation v3.0
   ═══════════════════════════════════════════════════════════════
   Computes cascading impacts through the GCC Reality Graph.

   Mathematical Model:
   1. impact_i(t+1) = Σ(w_ji × polarity_ji × impact_j(t)) × sensitivity_i - damping_i × impact_i(t)
   2. Severity scaling: effective_impact = impact × severity
   3. Energy: E_total = Σ impact_i²
   4. Normalization: normalized_i = impact_i / max(all node impacts)

   Validity Conditions:
   - Propagation depth > 2
   - Impacts bounded [-1, 1]
   - No disconnected critical nodes
   - Explanation chain matches propagation path
   ═══════════════════════════════════════════════════════════════ */

import type { GCCNode, GCCEdge, GCCLayer } from './gcc-graph'

/* ── Result types ── */
export interface PropagationResult {
  nodeImpacts: Map<string, number>
  propagationChain: PropagationStep[]
  affectedSectors: SectorImpact[]
  topDrivers: Driver[]
  totalLoss: number
  confidence: number
  explanation: string
  spreadLevel: 'low' | 'medium' | 'high' | 'critical'
  spreadLevelAr: string
  systemEnergy: number
  iterationSnapshots: IterationSnapshot[]
  nodeExplanations: Map<string, NodeExplanation>
  propagationDepth: number
}

export interface IterationSnapshot {
  iteration: number
  impacts: Map<string, number>
  energy: number
  deltaEnergy: number
}

export interface NodeExplanation {
  nodeId: string
  label: string
  labelAr: string
  layer: GCCLayer
  impact: number
  normalizedImpact: number
  incomingEdges: { from: string; fromLabel: string; weight: number; polarity: number; contribution: number }[]
  outgoingEdges: { to: string; toLabel: string; weight: number; polarity: number }[]
  explanation: string
  explanationAr: string
}

export interface PropagationStep {
  from: string
  fromLabel: string
  to: string
  toLabel: string
  weight: number
  polarity: number
  impact: number
  label: string
  iteration: number
}

export interface SectorImpact {
  sector: GCCLayer
  sectorLabel: string
  avgImpact: number
  maxImpact: number
  nodeCount: number
  topNode: string
  color: string
}

export interface Driver {
  nodeId: string
  label: string
  impact: number
  layer: GCCLayer
  outDegree: number
}

/* ── Sector economic base values ($B) for loss estimation ── */
const SECTOR_GDP_BASE: Record<GCCLayer, number> = {
  geography: 0,
  infrastructure: 85,
  economy: 420,
  finance: 180,
  society: 95,
}

/* ── Layer labels ── */
const LAYER_LABELS: Record<GCCLayer, { en: string; ar: string }> = {
  geography: { en: 'Geography', ar: 'الجغرافيا' },
  infrastructure: { en: 'Infrastructure', ar: 'البنية التحتية' },
  economy: { en: 'Economy', ar: 'الاقتصاد' },
  finance: { en: 'Finance', ar: 'المالية' },
  society: { en: 'Society', ar: 'المجتمع' },
}

const LAYER_COLORS: Record<GCCLayer, string> = {
  geography: '#2DD4A0',
  infrastructure: '#F5A623',
  economy: '#5B7BF8',
  finance: '#A78BFA',
  society: '#EF5454',
}

/* ── Spread level i18n ── */
const SPREAD_LABELS: Record<string, string> = {
  low: 'منخفض',
  medium: 'متوسط',
  high: 'مرتفع',
  critical: 'حرج',
}

/* ════════════════════════════════════════════════
   MAIN PROPAGATION FUNCTION
   ════════════════════════════════════════════════ */
export function runPropagation(
  nodes: GCCNode[],
  edges: GCCEdge[],
  shocks: { nodeId: string; impact: number }[],
  maxIterations: number = 6,
  lang: 'ar' | 'en' = 'ar',
  decayRate: number = 0.05,
): PropagationResult {
  // Build adjacency: target ← [{ source, edge }] (incoming edges for each node)
  const incomingAdj = new Map<string, { source: string; edge: GCCEdge }[]>()
  const outgoingAdj = new Map<string, { target: string; edge: GCCEdge }[]>()
  for (const e of edges) {
    if (!incomingAdj.has(e.target)) incomingAdj.set(e.target, [])
    incomingAdj.get(e.target)!.push({ source: e.source, edge: e })
    if (!outgoingAdj.has(e.source)) outgoingAdj.set(e.source, [])
    outgoingAdj.get(e.source)!.push({ target: e.target, edge: e })
  }

  // Node lookup
  const nodeMap = new Map<string, GCCNode>(nodes.map(n => [n.id, n]))

  // Impact state: I(t)
  const impacts = new Map<string, number>()
  nodes.forEach(n => impacts.set(n.id, 0))

  // Apply initial shocks
  for (const shock of shocks) {
    impacts.set(shock.nodeId, Math.max(-1, Math.min(1, shock.impact)))
  }

  // Track propagation chain & iteration history
  const chain: PropagationStep[] = []
  const iterationSnapshots: IterationSnapshot[] = []
  let maxDepth = 0

  // Snapshot iteration 0 (initial shocks)
  const snap0 = new Map(impacts)
  const energy0 = computeEnergy(snap0)
  iterationSnapshots.push({ iteration: 0, impacts: snap0, energy: energy0, deltaEnergy: 0 })

  // ── CORE MATHEMATICAL LOOP ──
  // Formula: I_i(t+1) = clamp( Σ_j(w_ji × p_ji × I_j(t)) × s_i - damping_i × I_i(t) )
  for (let iter = 0; iter < maxIterations; iter++) {
    const newImpacts = new Map<string, number>()
    let anyChange = false

    for (const node of nodes) {
      const currentImpact = impacts.get(node.id) ?? 0
      const incoming = incomingAdj.get(node.id) ?? []

      // Σ(w_ji × polarity_ji × I_j(t))
      let weightedSum = 0
      for (const { source: srcId, edge } of incoming) {
        const srcImpact = impacts.get(srcId) ?? 0
        if (Math.abs(srcImpact) < 0.005) continue

        const polarity = (edge as any).polarity ?? 1
        const contribution = edge.weight * polarity * srcImpact
        weightedSum += contribution

        // Record propagation step if meaningful
        if (Math.abs(contribution * node.sensitivity) > 0.01) {
          const srcNode = nodeMap.get(srcId)!
          chain.push({
            from: srcId,
            fromLabel: lang === 'ar' ? (srcNode.labelAr || srcNode.label) : srcNode.label,
            to: node.id,
            toLabel: lang === 'ar' ? (node.labelAr || node.label) : node.label,
            weight: edge.weight,
            polarity: polarity,
            impact: contribution * node.sensitivity,
            label: lang === 'ar' ? (edge.labelAr || edge.label) : edge.label,
            iteration: iter + 1,
          })
        }
      }

      // I_i(t+1) = Σ(w_ji × p_ji × I_j(t)) × s_i - damping_i × I_i(t)
      // Uses per-node damping_factor (falls back to global decayRate if absent)
      const propagated = weightedSum * node.sensitivity
      const nodeDamping = (node as any).damping_factor ?? decayRate
      const decayed = nodeDamping * currentImpact
      let newImpact = currentImpact + propagated - decayed

      // Clamp to [-1, 1]
      newImpact = Math.max(-1, Math.min(1, newImpact))

      // Check for shocks (keep them pinned on iter 0)
      const isShockNode = shocks.some(s => s.nodeId === node.id)
      if (isShockNode && iter === 0) {
        // On first iteration, shock nodes keep their initial value + propagation
        const shockVal = shocks.find(s => s.nodeId === node.id)!.impact
        newImpact = Math.max(-1, Math.min(1, shockVal + propagated - decayed))
      }

      newImpacts.set(node.id, newImpact)

      if (Math.abs(newImpact - currentImpact) > 0.005) {
        anyChange = true
      }
    }

    // Update impacts
    for (const [id, val] of newImpacts) {
      impacts.set(id, val)
    }

    // Track depth
    const affectedCount = Array.from(impacts.values()).filter(v => Math.abs(v) > 0.01).length
    if (affectedCount > shocks.length) {
      maxDepth = iter + 1
    }

    // Snapshot this iteration
    const snapN = new Map(impacts)
    const energyN = computeEnergy(snapN)
    const prevEnergy = iterationSnapshots[iterationSnapshots.length - 1].energy
    iterationSnapshots.push({
      iteration: iter + 1,
      impacts: snapN,
      energy: energyN,
      deltaEnergy: energyN - prevEnergy,
    })

    // Early convergence: if no meaningful change, stop
    if (!anyChange && iter > 1) break
  }

  // ── Compute sector impacts ──
  const sectorGroups = new Map<GCCLayer, { impacts: number[]; nodes: string[] }>()
  for (const node of nodes) {
    const impact = Math.abs(impacts.get(node.id) ?? 0)
    if (!sectorGroups.has(node.layer)) {
      sectorGroups.set(node.layer, { impacts: [], nodes: [] })
    }
    const group = sectorGroups.get(node.layer)!
    group.impacts.push(impact)
    group.nodes.push(lang === 'ar' ? (node.labelAr || node.label) : node.label)
  }

  const affectedSectors: SectorImpact[] = []
  for (const [layer, group] of sectorGroups) {
    const avg = group.impacts.reduce((a, b) => a + b, 0) / group.impacts.length
    const max = Math.max(...group.impacts)
    const maxIdx = group.impacts.indexOf(max)
    if (avg > 0.01) {
      affectedSectors.push({
        sector: layer,
        sectorLabel: lang === 'ar' ? LAYER_LABELS[layer].ar : LAYER_LABELS[layer].en,
        avgImpact: avg,
        maxImpact: max,
        nodeCount: group.impacts.filter(i => i > 0.01).length,
        topNode: group.nodes[maxIdx],
        color: LAYER_COLORS[layer],
      })
    }
  }
  affectedSectors.sort((a, b) => b.avgImpact - a.avgImpact)

  // ── Compute top drivers ──
  const driverMap = new Map<string, number>()
  for (const step of chain) {
    driverMap.set(step.from, (driverMap.get(step.from) ?? 0) + 1)
  }
  const topDrivers: Driver[] = Array.from(driverMap.entries())
    .map(([nodeId, outDegree]) => {
      const node = nodeMap.get(nodeId)!
      return {
        nodeId,
        label: lang === 'ar' ? (node.labelAr || node.label) : node.label,
        impact: Math.abs(impacts.get(nodeId) ?? 0),
        layer: node.layer,
        outDegree,
      }
    })
    .sort((a, b) => b.impact * b.outDegree - a.impact * a.outDegree)
    .slice(0, 8)

  // ── Total economic loss ──
  let totalLoss = 0
  for (const [layer, group] of sectorGroups) {
    const avgImpact = group.impacts.reduce((a, b) => a + b, 0) / group.impacts.length
    totalLoss += SECTOR_GDP_BASE[layer] * avgImpact
  }

  // ── Spread level ──
  const avgGlobalImpact = Array.from(impacts.values())
    .reduce((a, b) => a + Math.abs(b), 0) / impacts.size
  const spreadLevel: PropagationResult['spreadLevel'] =
    avgGlobalImpact > 0.4 ? 'critical' :
    avgGlobalImpact > 0.25 ? 'high' :
    avgGlobalImpact > 0.1 ? 'medium' : 'low'
  const spreadLevelAr = SPREAD_LABELS[spreadLevel] || spreadLevel

  // ── System energy: E = Σ impact_i² ──
  const systemEnergy = computeEnergy(impacts)

  // ── Confidence ──
  const confidence = Math.min(0.95, 0.6 + chain.length * 0.005 + maxDepth * 0.05)

  // ── Per-node explanations ──
  const maxImpactVal = Math.max(...Array.from(impacts.values()).map(Math.abs), 0.001)
  const nodeExplanations = new Map<string, NodeExplanation>()
  for (const node of nodes) {
    const impact = impacts.get(node.id) ?? 0
    const normalizedImpact = impact / maxImpactVal
    const incoming = (incomingAdj.get(node.id) ?? []).map(({ source: srcId, edge }) => {
      const srcNode = nodeMap.get(srcId)!
      const srcImpact = impacts.get(srcId) ?? 0
      const polarity = (edge as any).polarity ?? 1
      return {
        from: srcId,
        fromLabel: lang === 'ar' ? (srcNode.labelAr || srcNode.label) : srcNode.label,
        weight: edge.weight,
        polarity,
        contribution: edge.weight * polarity * srcImpact * node.sensitivity,
      }
    }).filter(e => Math.abs(e.contribution) > 0.005)
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))

    const outgoing = (outgoingAdj.get(node.id) ?? []).map(({ target: tgtId, edge }) => {
      const tgtNode = nodeMap.get(tgtId)!
      const polarity = (edge as any).polarity ?? 1
      return {
        to: tgtId,
        toLabel: lang === 'ar' ? (tgtNode.labelAr || tgtNode.label) : tgtNode.label,
        weight: edge.weight,
        polarity,
      }
    })

    const topIncoming = incoming.slice(0, 3)
    const impactPct = (Math.abs(impact) * 100).toFixed(0)

    const nodeLabel = lang === 'ar' ? (node.labelAr || node.label) : node.label
    const layerLabel = lang === 'ar' ? LAYER_LABELS[node.layer].ar : LAYER_LABELS[node.layer].en

    let explanation = ''
    let explanationAr = ''

    if (Math.abs(impact) < 0.01) {
      explanation = `${node.label} is not significantly affected in this scenario.`
      explanationAr = `${node.labelAr || node.label} غير متأثر بشكل ملحوظ في هذا السيناريو.`
    } else {
      const topSrc = topIncoming[0]
      if (topSrc) {
        explanation = `${node.label} (${LAYER_LABELS[node.layer].en}) is ${impactPct}% impacted. ` +
          `Primary driver: ${topSrc.fromLabel} (contribution: ${(topSrc.contribution * 100).toFixed(0)}%). ` +
          `Sensitivity: ${(node.sensitivity * 100).toFixed(0)}%. ` +
          `Feeds into ${outgoing.length} downstream node${outgoing.length !== 1 ? 's' : ''}.`
        explanationAr = `${node.labelAr || node.label} (${LAYER_LABELS[node.layer].ar}) متأثر بنسبة ${impactPct}%. ` +
          `المحرك الرئيسي: ${topSrc.fromLabel} (مساهمة: ${(topSrc.contribution * 100).toFixed(0)}%). ` +
          `الحساسية: ${(node.sensitivity * 100).toFixed(0)}%. ` +
          `يغذي ${outgoing.length} عقد${outgoing.length > 1 ? 'ة' : ''} تالية.`
      } else {
        // Shock node
        explanation = `${node.label} is a shock origin with ${impactPct}% direct impact. ` +
          `Feeds into ${outgoing.length} downstream node${outgoing.length !== 1 ? 's' : ''}.`
        explanationAr = `${node.labelAr || node.label} نقطة صدمة أصلية بتأثير مباشر ${impactPct}%. ` +
          `يغذي ${outgoing.length} عقد${outgoing.length > 1 ? 'ة' : ''} تالية.`
      }
    }

    nodeExplanations.set(node.id, {
      nodeId: node.id,
      label: node.label,
      labelAr: node.labelAr || node.label,
      layer: node.layer,
      impact,
      normalizedImpact,
      incomingEdges: incoming,
      outgoingEdges: outgoing,
      explanation,
      explanationAr,
    })
  }

  // ── Global explanation ──
  const primaryShock = shocks[0]
  const primaryNode = nodeMap.get(primaryShock.nodeId)
  const topSector = affectedSectors[0]
  const primaryLabel = lang === 'ar' ? (primaryNode?.labelAr || primaryNode?.label || 'غير معروف') : (primaryNode?.label ?? 'Unknown')
  const globalExplanation = lang === 'ar'
    ? `الصدمة الأساسية: ${primaryLabel} (الحدة ${(primaryShock.impact * 100).toFixed(0)}%). ` +
      `انتشرت عبر ${chain.length} مسار سببي في ${affectedSectors.length} قطاعات خلال ${maxDepth} مراحل انتشار. ` +
      `الأكثر تأثراً: ${topSector?.sectorLabel ?? 'غير متاح'} (متوسط التأثير ${((topSector?.avgImpact ?? 0) * 100).toFixed(0)}%). ` +
      `طاقة النظام: ${systemEnergy.toFixed(3)}. معدل الاضمحلال: ${(decayRate * 100).toFixed(0)}%. ` +
      `التعرض الاقتصادي المقدر: $${(totalLoss).toFixed(1)} مليار.`
    : `Primary shock: ${primaryLabel} (severity ${(primaryShock.impact * 100).toFixed(0)}%). ` +
      `Propagated through ${chain.length} causal paths across ${affectedSectors.length} sectors over ${maxDepth} iterations. ` +
      `Most affected: ${topSector?.sectorLabel ?? 'N/A'} (avg impact ${((topSector?.avgImpact ?? 0) * 100).toFixed(0)}%). ` +
      `System energy: ${systemEnergy.toFixed(3)}. Decay rate: ${(decayRate * 100).toFixed(0)}%. ` +
      `Estimated economic exposure: $${(totalLoss).toFixed(1)}B.`

  return {
    nodeImpacts: impacts,
    propagationChain: chain,
    affectedSectors,
    topDrivers,
    totalLoss,
    confidence,
    explanation: globalExplanation,
    spreadLevel,
    spreadLevelAr,
    systemEnergy,
    iterationSnapshots,
    nodeExplanations,
    propagationDepth: maxDepth,
  }
}

/* ── Compute system energy: E = Σ impact_i² ── */
function computeEnergy(impacts: Map<string, number>): number {
  let energy = 0
  for (const val of impacts.values()) {
    energy += val * val
  }
  return energy
}

/* ── Utility: format propagation chain as readable strings ── */
export function formatPropagationChain(chain: PropagationStep[]): string[] {
  const seen = new Set<string>()
  return chain
    .filter(step => {
      const key = `${step.from}->${step.to}`
      if (seen.has(key)) return false
      seen.add(key)
      return Math.abs(step.impact) > 0.02
    })
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
    .slice(0, 12)
    .map(step => {
      const direction = step.impact > 0 ? '↑' : '↓'
      const pol = step.polarity < 0 ? ' ⊖' : ''
      return `${step.fromLabel} → ${step.toLabel} ${direction}${pol} (${step.label})`
    })
}
