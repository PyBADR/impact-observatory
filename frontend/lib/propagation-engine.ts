/* âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
   Propagation Engine â Causal Impact Computation
   âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
   Computes cascading impacts through the GCC Reality Graph.

   Algorithm:
   1. Apply initial shocks to seed nodes
   2. Propagate through edges using: impact(node) = Î£(edge_weight Ã source_impact) Ã sensitivity
   3. Track the full propagation chain for explanation
   4. Compute sector-level aggregates and economic estimates
   âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ */

import type { GCCNode, GCCEdge, GCCLayer } from './gcc-graph'

/* ââ Result types ââ */
export interface PropagationResult {
  nodeImpacts: Map<string, number>
  propagationChain: PropagationStep[]
  affectedSectors: SectorImpact[]
  topDrivers: Driver[]
  totalLoss: number
  confidence: number
  explanation: string
  spreadLevel: 'low' | 'medium' | 'high' | 'critical'
}

export interface PropagationStep {
  from: string
  fromLabel: string
  to: string
  toLabel: string
  weight: number
  impact: number
  label: string
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
  outDegree: number   // how many nodes this drives
}

/* ââ Sector economic base values ($B) for loss estimation ââ */
const SECTOR_GDP_BASE: Record<GCCLayer, number> = {
  geography: 0,           // no direct GDP
  infrastructure: 85,     // ports + airports combined
  economy: 420,           // oil + aviation + shipping
  finance: 180,           // banking + insurance
  society: 95,            // travel + consumer spending
}

/* ââ Layer labels for display ââ */
const LAYER_LABELS: Record<GCCLayer, string> = {
  geography: 'Geography',
  infrastructure: 'Infrastructure',
  economy: 'Economy',
  finance: 'Finance',
  society: 'Society',
}

const LAYER_COLORS: Record<GCCLayer, string> = {
  geography: '#2DD4A0',
  infrastructure: '#F5A623',
  economy: '#5B7BF8',
  finance: '#A78BFA',
  society: '#EF5454',
}

/* ââââââââââââââââââââââââââââââââââââââââââââââ
   MAIN PROPAGATION FUNCTION
   ââââââââââââââââââââââââââââââââââââââââââââââ */
export function runPropagation(
  nodes: GCCNode[],
  edges: GCCEdge[],
  shocks: { nodeId: string; impact: number }[],
  maxIterations: number = 5,
): PropagationResult {
  // Build adjacency: source â [{ target, edge }]
  const adjacency = new Map<string, { target: string; edge: GCCEdge }[]>()
  for (const e of edges) {
    if (!adjacency.has(e.source)) adjacency.set(e.source, [])
    adjacency.get(e.source)!.push({ target: e.target, edge: e })
  }

  // Node lookup
  const nodeMap = new Map<string, GCCNode>(nodes.map(n => [n.id, n]))

  // Impact state
  const impacts = new Map<string, number>()
  nodes.forEach(n => impacts.set(n.id, 0))

  // Apply initial shocks
  for (const shock of shocks) {
    impacts.set(shock.nodeId, shock.impact)
  }

  // Track propagation chain
  const chain: PropagationStep[] = []
  const visited = new Set<string>(shocks.map(s => s.nodeId))

  // BFS-style propagation with dampening
  let frontier = new Set<string>(shocks.map(s => s.nodeId))

  for (let iter = 0; iter < maxIterations && frontier.size > 0; iter++) {
    const nextFrontier = new Set<string>()

    for (const sourceId of frontier) {
      const sourceImpact = impacts.get(sourceId) ?? 0
      if (Math.abs(sourceImpact) < 0.01) continue // skip negligible

      const outEdges = adjacency.get(sourceId) ?? []
      for (const { target: targetId, edge } of outEdges) {
        const targetNode = nodeMap.get(targetId)
        if (!targetNode) continue

        // Core formula: impact = edge_weight Ã source_impact Ã target_sensitivity
        const rawImpact = edge.weight * sourceImpact * targetNode.sensitivity
        const currentImpact = impacts.get(targetId) ?? 0

        // Only propagate if this adds meaningful new impact
        if (Math.abs(rawImpact) > 0.01 && Math.abs(rawImpact) > Math.abs(currentImpact) * 0.1) {
          const newImpact = Math.max(-1, Math.min(1, currentImpact + rawImpact * (1 - Math.abs(currentImpact) * 0.3)))
          impacts.set(targetId, newImpact)

          const sourceNode = nodeMap.get(sourceId)!
          chain.push({
            from: sourceId,
            fromLabel: sourceNode.label,
            to: targetId,
            toLabel: targetNode.label,
            weight: edge.weight,
            impact: rawImpact,
            label: edge.label,
          })

          if (!visited.has(targetId)) {
            nextFrontier.add(targetId)
            visited.add(targetId)
          }
        }
      }
    }

    frontier = nextFrontier
  }

  // ââ Compute sector impacts ââ
  const sectorGroups = new Map<GCCLayer, { impacts: number[]; nodes: string[] }>()
  for (const node of nodes) {
    const impact = Math.abs(impacts.get(node.id) ?? 0)
    if (!sectorGroups.has(node.layer)) {
      sectorGroups.set(node.layer, { impacts: [], nodes: [] })
    }
    const group = sectorGroups.get(node.layer)!
    group.impacts.push(impact)
    group.nodes.push(node.label)
  }

  const affectedSectors: SectorImpact[] = []
  for (const [layer, group] of sectorGroups) {
    const avg = group.impacts.reduce((a, b) => a + b, 0) / group.impacts.length
    const max = Math.max(...group.impacts)
    const maxIdx = group.impacts.indexOf(max)
    if (avg > 0.01) {
      affectedSectors.push({
        sector: layer,
        sectorLabel: LAYER_LABELS[layer],
        avgImpact: avg,
        maxImpact: max,
        nodeCount: group.impacts.filter(i => i > 0.01).length,
        topNode: group.nodes[maxIdx],
        color: LAYER_COLORS[layer],
      })
    }
  }
  affectedSectors.sort((a, b) => b.avgImpact - a.avgImpact)

  // ââ Compute top drivers ââ
  const driverMap = new Map<string, number>()
  for (const step of chain) {
    driverMap.set(step.from, (driverMap.get(step.from) ?? 0) + 1)
  }
  const topDrivers: Driver[] = Array.from(driverMap.entries())
    .map(([nodeId, outDegree]) => {
      const node = nodeMap.get(nodeId)!
      return {
        nodeId,
        label: node.label,
        impact: Math.abs(impacts.get(nodeId) ?? 0),
        layer: node.layer,
        outDegree,
      }
    })
    .sort((a, b) => b.impact * b.outDegree - a.impact * a.outDegree)
    .slice(0, 8)

  // ââ Estimate total economic loss ââ
  let totalLoss = 0
  for (const [layer, group] of sectorGroups) {
    const avgImpact = group.impacts.reduce((a, b) => a + b, 0) / group.impacts.length
    totalLoss += SECTOR_GDP_BASE[layer] * avgImpact
  }

  // ââ Spread level ââ
  const avgGlobalImpact = Array.from(impacts.values())
    .reduce((a, b) => a + Math.abs(b), 0) / impacts.size
  const spreadLevel: PropagationResult['spreadLevel'] =
    avgGlobalImpact > 0.4 ? 'critical' :
    avgGlobalImpact > 0.25 ? 'high' :
    avgGlobalImpact > 0.1 ? 'medium' : 'low'

  // ââ Confidence (based on chain completeness) ââ
  const confidence = Math.min(0.95, 0.6 + chain.length * 0.008)

  // ââ Explanation ââ
  const primaryShock = shocks[0]
  const primaryNode = nodeMap.get(primaryShock.nodeId)
  const topSector = affectedSectors[0]
  const explanation = `Primary shock: ${primaryNode?.label ?? 'Unknown'} (severity ${(primaryShock.impact * 100).toFixed(0)}%). ` +
    `Propagated through ${chain.length} causal paths across ${affectedSectors.length} sectors. ` +
    `Most affected: ${topSector?.sectorLabel ?? 'N/A'} (avg impact ${(topSector?.avgImpact * 100).toFixed(0)}%). ` +
    `Estimated economic exposure: $${(totalLoss).toFixed(1)}B over 72h propagation window.`

  return {
    nodeImpacts: impacts,
    propagationChain: chain,
    affectedSectors,
    topDrivers,
    totalLoss,
    confidence,
    explanation,
    spreadLevel,
  }
}

/* ââ Utility: format propagation chain as readable strings ââ */
export function formatPropagationChain(chain: PropagationStep[]): string[] {
  // Deduplicate and order by impact magnitude
  const seen = new Set<string>()
  return chain
    .filter(step => {
      const key = `${step.from}->${step.to}`
      if (seen.has(key)) return false
      seen.add(key)
      return Math.abs(step.impact) > 0.03
    })
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
    .slice(0, 12)
    .map(step => {
      const direction = step.impact > 0 ? 'â' : 'â'
      return `${step.fromLabel} â ${step.toLabel} ${direction} (${step.label})`
    })
}
