/* ═══════════════════════════════════════════════════════════════
   Propagation Engine — Discrete Dynamic Graph v4.0
   ═══════════════════════════════════════════════════════════════
   Computes cascading impacts through the GCC Reality Graph.

   Mathematical Model (enforced):
   1. x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t)
      + shock_i (external forcing for shock nodes)
   2. Severity scaling: x_i_eff = severity × x_i
   3. System energy: E_sys = Σ x_i(t)²
   4. Normalized intensity: I_i = x_i / max_k |x_k|
   5. Sector aggregation: S_k = avg(x_i) for nodes in sector k
   6. Confidence: C = 1 / (1 + variance)
   7. Propagation depth: D = max iteration with new affected nodes

   Validity Conditions:
   - D > 2
   - |x_i| ≤ 1 (bounded)
   - No disconnected critical nodes
   - Explanation chain = actual propagation path
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
/* GCC combined GDP ~$2.1T (2024 est.)
   Layer weights reflect real sectoral contribution:
   - Geography: 0 (spatial layer, no direct GDP)
   - Infrastructure: $210B (ports, airports, utilities, telecom — ~10% GDP)
   - Economy: $950B (oil $540B + non-oil $410B — ~45% GDP)
   - Finance: $380B (banking, insurance, capital markets — ~18% GDP)
   - Society: $160B (consumer services, tourism demand, employment — ~8% GDP) */
const SECTOR_GDP_BASE: Record<GCCLayer, number> = {
  geography: 0,
  infrastructure: 210,
  economy: 950,
  finance: 380,
  society: 160,
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
  // Formula: x_i(t+1) = clamp( s_i × Σ_j(w_ji × p_ji × x_j(t)) - d_i × x_i(t) )
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

      // x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t)
      // Pure discrete dynamical replacement (not accumulation)
      const propagated = weightedSum * node.sensitivity
      const nodeDamping = (node as any).damping_factor ?? decayRate
      const decayed = nodeDamping * currentImpact
      let newImpact = propagated - decayed

      // Clamp to [-1, 1]
      newImpact = Math.max(-1, Math.min(1, newImpact))

      // Shock nodes: add shock signal as external forcing term
      const shockEntry = shocks.find(s => s.nodeId === node.id)
      if (shockEntry) {
        // x_i(t+1) = s_i × Σ(w_ji × x_j(t)) - d_i × x_i(t) + shock_i
        newImpact = Math.max(-1, Math.min(1, newImpact + shockEntry.impact))
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

  // ── Confidence: C = 1 / (1 + variance) ──
  // Deterministic variance: spread of node impacts as uncertainty proxy
  const impactValues = Array.from(impacts.values()).map(Math.abs)
  const meanImpact = impactValues.reduce((a, b) => a + b, 0) / impactValues.length
  const impactVariance = impactValues.reduce((acc, v) => acc + (v - meanImpact) ** 2, 0) / impactValues.length
  const confidence = 1 / (1 + impactVariance)

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

/* ═══════════════════════════════════════════════════
   SECTOR FINANCIAL FORMULAS
   ═══════════════════════════════════════════════════
   Mandatory sector-specific financial metrics derived
   from propagation impacts on relevant graph nodes.

   Each formula aggregates impacts on the relevant nodes
   and applies domain-specific scaling:

   Oil + Hormuz Core Chain (mandatory):
   F_flow           = 1 - (Severity_hormuz × Dependency_hormuz)
   Oil_export       = Base_export × F_flow
   Impact_oil       = 1 - (Oil_export / Base_export)
   Cost_shipping    = Base_shipping × (1 + Impact_oil × W_oil_to_shipping)
   Risk_insurance   = Base_risk × (1 + Cost_shipping_impact × W_shipping_to_insurance)
   Cost_aviation    = Base_fuel × (1 + Risk_insurance_impact × W_insurance_to_aviation)
   Tourism          = Base_tourism × (1 - Cost_aviation_impact × W_aviation_to_tourism)
   GDP_loss         = Σ (Sector_impact × Sector_weight)

   Additional sector formulas:
   Throughput_airport = base × Π(1 - |I(inf_airport_k)|)
   Throughput_port  = base × Π(1 - |I(inf_port_k)|)
   Stress_banking   = Σ|I(fin_bank_k)| / N_banks
   Stress_food      = |I(eco_food)| × 0.5 + |I(soc_food_d)| × 0.5
   Avail_utility    = 1 - (|I(inf_desal)| + |I(inf_power)|) / 2
   ═══════════════════════════════════════════════════ */

export interface SectorFinancialMetric {
  value: number; base: number; label: string; labelAr: string; unit: string
  formula?: string  // readable formula for explanation
  direction?: 'up' | 'down'  // whether this metric rises or falls under stress
}

export interface SectorFinancials {
  oilRevenue: SectorFinancialMetric
  shippingCost: SectorFinancialMetric
  insuranceRisk: SectorFinancialMetric
  aviationCost: SectorFinancialMetric
  flightCost: SectorFinancialMetric
  travelDemand: SectorFinancialMetric
  tourismRevenue: SectorFinancialMetric
  gdpLoss: SectorFinancialMetric
  airportThroughput: SectorFinancialMetric
  portThroughput: SectorFinancialMetric
  bankingStress: SectorFinancialMetric
  foodStress: SectorFinancialMetric
  utilityAvailability: SectorFinancialMetric
}

const AIRPORT_IDS = ['inf_ruh', 'inf_dxb', 'inf_kwi', 'inf_doh', 'inf_jed', 'inf_dmm', 'inf_auh', 'inf_bah', 'inf_mct']
const PORT_IDS = ['inf_jebel', 'inf_dammam', 'inf_doha_p', 'inf_hamad', 'inf_khalifa', 'inf_shuwaikh', 'inf_sohar']
const BANK_IDS = ['fin_sama', 'fin_uae_cb', 'fin_kw_cb', 'fin_qa_cb', 'fin_om_cb', 'fin_bh_cb', 'fin_banking']

/** Base values (annual, $B or index) */
const FINANCIAL_BASES = {
  oilRevenue: 540,       // $B — GCC combined oil revenue
  tourismRevenue: 85,    // $B — GCC tourism
  airportPax: 350,       // M passengers — GCC combined
  portTEU: 45,           // M TEU — GCC combined
  shippingCost: 12,      // $B baseline shipping cost
  insurancePremium: 28,  // $B GCC insurance premiums
  aviationFuel: 42,      // $B — GCC aviation fuel cost
  baseTicket: 320,       // $ — average GCC flight ticket price
}

export function computeSectorFinancials(impacts: Map<string, number>): SectorFinancials {
  const I = (id: string) => Math.abs(impacts.get(id) ?? 0)
  const raw = (id: string) => impacts.get(id) ?? 0

  // ── Oil + Hormuz Core Chain (mandatory formulas) ──

  // F_flow = 1 - (Severity_hormuz × Dependency_hormuz)
  // Dependency = 0.95 (edge weight), Severity = propagated Hormuz impact
  const severity_hormuz = I('geo_hormuz')
  const dependency_hormuz = 0.95
  const F_flow = Math.max(0, 1 - severity_hormuz * dependency_hormuz)

  // Oil_export = Base_export × F_flow
  const oilExport = FINANCIAL_BASES.oilRevenue * F_flow

  // Impact_oil = 1 - (Oil_export / Base_export) = 1 - F_flow
  const impactOil = 1 - F_flow

  // Cost_shipping = Base_shipping × (1 + Impact_oil × W_oil_to_shipping)
  const W_oil_to_shipping = 0.85
  const shippingCost = FINANCIAL_BASES.shippingCost * (1 + impactOil * W_oil_to_shipping)
  const shippingCostImpact = (shippingCost - FINANCIAL_BASES.shippingCost) / FINANCIAL_BASES.shippingCost

  // Risk_insurance = Base_risk × (1 + Cost_shipping_impact × W_shipping_to_insurance)
  const W_shipping_to_insurance = 0.80
  const insuranceRisk = FINANCIAL_BASES.insurancePremium * (1 + shippingCostImpact * W_shipping_to_insurance)
  const insuranceRiskImpact = (insuranceRisk - FINANCIAL_BASES.insurancePremium) / FINANCIAL_BASES.insurancePremium

  // Cost_aviation = Base_fuel × (1 + Risk_insurance_impact × W_insurance_to_aviation)
  const W_insurance_to_aviation = 0.75
  const aviationCost = FINANCIAL_BASES.aviationFuel * (1 + insuranceRiskImpact * W_insurance_to_aviation)
  const aviationCostImpact = (aviationCost - FINANCIAL_BASES.aviationFuel) / FINANCIAL_BASES.aviationFuel

  // Tourism = Base_tourism × (1 - Cost_aviation_impact × W_aviation_to_tourism)
  const W_aviation_to_tourism = 0.70
  const tourismDemand = FINANCIAL_BASES.tourismRevenue * Math.max(0, 1 - aviationCostImpact * W_aviation_to_tourism)

  // GDP_loss = Σ (Sector_impact × Sector_weight)
  const gdpLoss =
    impactOil * 0.45 +                     // oil sector (45% of GCC GDP)
    shippingCostImpact * 0.10 +             // shipping (10%)
    insuranceRiskImpact * 0.05 +            // insurance (5%)
    aviationCostImpact * 0.08 +             // aviation (8%)
    (1 - tourismDemand / FINANCIAL_BASES.tourismRevenue) * 0.07  // tourism (7%)

  // ── Aviation Phase 2 Chain Formulas ──

  // Flight_cost = Base_ticket × (1 + Fuel_cost_impact × W_fuel)
  const W_fuel_to_ticket = 0.85
  const flightCost = FINANCIAL_BASES.baseTicket * (1 + aviationCostImpact * W_fuel_to_ticket)
  const flightCostImpact = (flightCost - FINANCIAL_BASES.baseTicket) / FINANCIAL_BASES.baseTicket

  // Demand = Base_demand × (1 - Flight_cost_impact × W_price)
  const W_price_to_demand = 0.80
  const travelDemand = Math.max(0, 1 - flightCostImpact * W_price_to_demand)

  // Throughput_airport = Base_passengers × Demand
  const airportThroughputFromDemand = FINANCIAL_BASES.airportPax * travelDemand

  // Tourism_revenue = Base_tourism × Demand (demand-driven)
  const tourismFromDemand = FINANCIAL_BASES.tourismRevenue * travelDemand

  // ── Additional sector formulas ──

  // Throughput_airport = base × Π(1 - |I(airport_k)|) — per-node impact product
  let airportProduct = 1
  for (const id of AIRPORT_IDS) {
    airportProduct *= (1 - I(id))
  }
  const airportThroughput = FINANCIAL_BASES.airportPax * Math.max(0, airportProduct)

  // Throughput_port = base × Π(1 - |I(port_k)|)
  let portProduct = 1
  for (const id of PORT_IDS) {
    portProduct *= (1 - I(id))
  }
  const portThroughput = FINANCIAL_BASES.portTEU * Math.max(0, portProduct)

  // Stress_banking = Σ|I(fin_bank_k)| / N_banks
  let bankSum = 0
  for (const id of BANK_IDS) { bankSum += I(id) }
  const bankingStress = bankSum / BANK_IDS.length

  // Stress_food = |I(eco_food)| × 0.5 + |I(soc_food_d)| × 0.5
  const foodStress = I('eco_food') * 0.5 + I('soc_food_d') * 0.5

  // Avail_utility = 1 - (|I(inf_desal)| + |I(inf_power)|) / 2
  const utilityAvailability = Math.max(0, 1 - (I('inf_desal') + I('inf_power')) / 2)

  return {
    oilRevenue:         { value: oilExport, base: FINANCIAL_BASES.oilRevenue, label: 'Oil Export', labelAr: 'تدفق النفط', unit: '$B', formula: `F_flow=${F_flow.toFixed(2)} → $${oilExport.toFixed(0)}B`, direction: 'down' as const },
    shippingCost:       { value: shippingCost, base: FINANCIAL_BASES.shippingCost, label: 'Shipping Cost', labelAr: 'تكلفة الشحن', unit: '$B', formula: `Base×(1+${impactOil.toFixed(2)}×0.85)`, direction: 'up' as const },
    insuranceRisk:      { value: insuranceRisk, base: FINANCIAL_BASES.insurancePremium, label: 'Insurance Risk', labelAr: 'مخاطر التأمين', unit: '$B', formula: `Base×(1+${shippingCostImpact.toFixed(2)}×0.80)`, direction: 'up' as const },
    aviationCost:       { value: aviationCost, base: FINANCIAL_BASES.aviationFuel, label: 'Aviation Fuel Cost', labelAr: 'تكلفة وقود الطيران', unit: '$B', formula: `Base×(1+${insuranceRiskImpact.toFixed(2)}×0.75)`, direction: 'up' as const },
    flightCost:         { value: flightCost, base: FINANCIAL_BASES.baseTicket, label: 'Flight Cost', labelAr: 'تكلفة الرحلات', unit: '$', formula: `$${FINANCIAL_BASES.baseTicket}×(1+${aviationCostImpact.toFixed(2)}×0.85)=$${flightCost.toFixed(0)}`, direction: 'up' as const },
    travelDemand:       { value: travelDemand, base: 1, label: 'Travel Demand', labelAr: 'الطلب على السفر', unit: '%', formula: `1-(${flightCostImpact.toFixed(2)}×0.80)=${(travelDemand*100).toFixed(0)}%`, direction: 'down' as const },
    tourismRevenue:     { value: tourismFromDemand, base: FINANCIAL_BASES.tourismRevenue, label: 'Tourism Revenue', labelAr: 'إيرادات السياحة', unit: '$B', formula: `$${FINANCIAL_BASES.tourismRevenue}B×${(travelDemand*100).toFixed(0)}%=$${tourismFromDemand.toFixed(1)}B`, direction: 'down' as const },
    gdpLoss:            { value: gdpLoss, base: 0, label: 'GDP Loss', labelAr: 'خسائر الناتج المحلي', unit: 'index', formula: `Σ(sector×weight)=${(gdpLoss*100).toFixed(1)}%`, direction: 'up' as const },
    airportThroughput:  { value: airportThroughputFromDemand, base: FINANCIAL_BASES.airportPax, label: 'Airport Throughput', labelAr: 'حركة المطارات', unit: 'M pax', formula: `${FINANCIAL_BASES.airportPax}M×${(travelDemand*100).toFixed(0)}%=${airportThroughputFromDemand.toFixed(0)}M`, direction: 'down' as const },
    portThroughput:     { value: portThroughput, base: FINANCIAL_BASES.portTEU, label: 'Port Throughput', labelAr: 'إنتاجية الموانئ', unit: 'M TEU', direction: 'down' as const },
    bankingStress:      { value: bankingStress, base: 0, label: 'Banking Stress', labelAr: 'إجهاد المصارف', unit: 'index', direction: 'up' as const },
    foodStress:         { value: foodStress, base: 0, label: 'Food Stress', labelAr: 'إجهاد الأمن الغذائي', unit: 'index', direction: 'up' as const },
    utilityAvailability:{ value: utilityAvailability, base: 1, label: 'Utility Availability', labelAr: 'توفر المرافق', unit: '%', direction: 'down' as const },
  }
}

/* ══════════════════════════════════════════════
   HORMUZ CASCADE FORMULA ENGINE
   Mandatory chain: Hormuz → Oil → Shipping → Insurance → Aviation → Tourism → GDP
   Each step computes a dollar/index value from the previous step's output.
   ══════════════════════════════════════════════ */

export interface HormuzChainStep {
  id: string
  label: string
  labelAr: string
  formula: string
  formulaAr: string
  value: number
  base: number
  unit: string
  direction: '↑' | '↓' | '—'
  impactPct: number  // % change from base
}

export interface HormuzChainResult {
  steps: HormuzChainStep[]
  gdpLoss: number
  chainNarrative: string
  chainNarrativeAr: string
}

const HORMUZ_BASES = {
  dependency: 0.85,       // GCC Hormuz dependency factor
  oilExport: 540,         // $B annual GCC oil export
  shippingCost: 12,       // $B baseline shipping
  insuranceBase: 0.02,    // 2% base risk premium
  fuelCost: 45,           // $B annual GCC aviation fuel
  tourismBase: 85,        // $B annual GCC tourism
  W_oil: 1.8,             // shipping sensitivity to oil disruption
  W_shipping: 2.5,        // insurance sensitivity to shipping cost increase
  W_insurance: 1.2,       // fuel cost sensitivity to insurance risk
  W_aviation: 0.6,        // tourism sensitivity to aviation cost increase
}

export function computeHormuzChain(
  impacts: Map<string, number>,
  severity: number = 1.0,
): HormuzChainResult {
  const I = (id: string) => impacts.get(id) ?? 0
  const absI = (id: string) => Math.abs(I(id))

  // Step 1: F_flow = 1 - (Severity_hormuz × Dependency_hormuz)
  const hormuzSeverity = absI('geo_hormuz') * severity
  const F_flow = Math.max(0, 1 - (hormuzSeverity * HORMUZ_BASES.dependency))

  // Step 2: Oil_export = Base_export × F_flow
  const oilExport = HORMUZ_BASES.oilExport * F_flow
  const impactOil = 1 - F_flow  // = 1 - (Oil_export / Base_export)

  // Step 3: Cost_shipping = Base_shipping × (1 + Impact_oil × W_oil)
  const costShipping = HORMUZ_BASES.shippingCost * (1 + impactOil * HORMUZ_BASES.W_oil)
  const shippingIncrease = (costShipping - HORMUZ_BASES.shippingCost) / HORMUZ_BASES.shippingCost

  // Step 4: Risk_insurance = Base_risk × (1 + Cost_shipping_increase × W_shipping)
  const riskInsurance = HORMUZ_BASES.insuranceBase * (1 + shippingIncrease * HORMUZ_BASES.W_shipping)

  // Step 5: Cost_aviation = Base_fuel × (1 + Risk_insurance_increase × W_insurance)
  const insuranceIncrease = (riskInsurance - HORMUZ_BASES.insuranceBase) / HORMUZ_BASES.insuranceBase
  const costAviation = HORMUZ_BASES.fuelCost * (1 + insuranceIncrease * HORMUZ_BASES.W_insurance)
  const aviationIncrease = (costAviation - HORMUZ_BASES.fuelCost) / HORMUZ_BASES.fuelCost

  // Step 6: Tourism = Base_tourism × (1 - Cost_aviation_increase × W_aviation)
  const tourismRevenue = HORMUZ_BASES.tourismBase * Math.max(0, 1 - aviationIncrease * HORMUZ_BASES.W_aviation)
  const tourismDecline = (HORMUZ_BASES.tourismBase - tourismRevenue) / HORMUZ_BASES.tourismBase

  // Step 7: GDP_loss = Σ (Sector_impact × Sector_weight)
  const gdpLoss = (impactOil * 540) + (shippingIncrease * 12) + (tourismDecline * 85)

  const steps: HormuzChainStep[] = [
    {
      id: 'hormuz', label: 'Strait of Hormuz', labelAr: 'مضيق هرمز',
      formula: `F_flow = 1 - (${(hormuzSeverity * 100).toFixed(0)}% × ${(HORMUZ_BASES.dependency * 100).toFixed(0)}%) = ${(F_flow * 100).toFixed(0)}%`,
      formulaAr: `تدفق = 1 - (${(hormuzSeverity * 100).toFixed(0)}% × ${(HORMUZ_BASES.dependency * 100).toFixed(0)}%) = ${(F_flow * 100).toFixed(0)}%`,
      value: F_flow, base: 1, unit: 'flow', direction: '↓', impactPct: (1 - F_flow) * 100,
    },
    {
      id: 'oil', label: 'Oil Export', labelAr: 'صادرات النفط',
      formula: `$${HORMUZ_BASES.oilExport}B × ${(F_flow * 100).toFixed(0)}% = $${oilExport.toFixed(1)}B`,
      formulaAr: `$${HORMUZ_BASES.oilExport} مليار × ${(F_flow * 100).toFixed(0)}% = $${oilExport.toFixed(1)} مليار`,
      value: oilExport, base: HORMUZ_BASES.oilExport, unit: '$B', direction: '↓', impactPct: impactOil * 100,
    },
    {
      id: 'shipping', label: 'Shipping Cost', labelAr: 'تكلفة الشحن',
      formula: `$${HORMUZ_BASES.shippingCost}B × (1 + ${(impactOil * 100).toFixed(0)}% × ${HORMUZ_BASES.W_oil}) = $${costShipping.toFixed(1)}B`,
      formulaAr: `$${HORMUZ_BASES.shippingCost} مليار × (1 + ${(impactOil * 100).toFixed(0)}% × ${HORMUZ_BASES.W_oil}) = $${costShipping.toFixed(1)} مليار`,
      value: costShipping, base: HORMUZ_BASES.shippingCost, unit: '$B', direction: '↑', impactPct: shippingIncrease * 100,
    },
    {
      id: 'insurance', label: 'Insurance Risk', labelAr: 'مخاطر التأمين',
      formula: `${(HORMUZ_BASES.insuranceBase * 100).toFixed(0)}% × (1 + ${(shippingIncrease * 100).toFixed(0)}% × ${HORMUZ_BASES.W_shipping}) = ${(riskInsurance * 100).toFixed(1)}%`,
      formulaAr: `${(HORMUZ_BASES.insuranceBase * 100).toFixed(0)}% × (1 + ${(shippingIncrease * 100).toFixed(0)}% × ${HORMUZ_BASES.W_shipping}) = ${(riskInsurance * 100).toFixed(1)}%`,
      value: riskInsurance, base: HORMUZ_BASES.insuranceBase, unit: 'risk', direction: '↑', impactPct: insuranceIncrease * 100,
    },
    {
      id: 'aviation', label: 'Aviation Fuel Cost', labelAr: 'تكلفة وقود الطيران',
      formula: `$${HORMUZ_BASES.fuelCost}B × (1 + ${(insuranceIncrease * 100).toFixed(0)}% × ${HORMUZ_BASES.W_insurance}) = $${costAviation.toFixed(1)}B`,
      formulaAr: `$${HORMUZ_BASES.fuelCost} مليار × (1 + ${(insuranceIncrease * 100).toFixed(0)}% × ${HORMUZ_BASES.W_insurance}) = $${costAviation.toFixed(1)} مليار`,
      value: costAviation, base: HORMUZ_BASES.fuelCost, unit: '$B', direction: '↑', impactPct: aviationIncrease * 100,
    },
    {
      id: 'tourism', label: 'Tourism Revenue', labelAr: 'إيرادات السياحة',
      formula: `$${HORMUZ_BASES.tourismBase}B × (1 - ${(aviationIncrease * 100).toFixed(0)}% × ${HORMUZ_BASES.W_aviation}) = $${tourismRevenue.toFixed(1)}B`,
      formulaAr: `$${HORMUZ_BASES.tourismBase} مليار × (1 - ${(aviationIncrease * 100).toFixed(0)}% × ${HORMUZ_BASES.W_aviation}) = $${tourismRevenue.toFixed(1)} مليار`,
      value: tourismRevenue, base: HORMUZ_BASES.tourismBase, unit: '$B', direction: '↓', impactPct: tourismDecline * 100,
    },
    {
      id: 'gdp', label: 'GDP Loss', labelAr: 'خسائر الناتج المحلي',
      formula: `Σ sectors = $${gdpLoss.toFixed(1)}B`,
      formulaAr: `مجموع القطاعات = $${gdpLoss.toFixed(1)} مليار`,
      value: gdpLoss, base: 0, unit: '$B', direction: '↓', impactPct: gdpLoss > 0 ? (gdpLoss / 2100) * 100 : 0,
    },
  ]

  const chainNarrative =
    `Hormuz blockade (${(hormuzSeverity * 100).toFixed(0)}% severity) reduces oil flow to ${(F_flow * 100).toFixed(0)}%, ` +
    `cutting exports by $${(HORMUZ_BASES.oilExport - oilExport).toFixed(0)}B. ` +
    `Shipping costs surge +${(shippingIncrease * 100).toFixed(0)}% to $${costShipping.toFixed(1)}B, ` +
    `driving insurance risk to ${(riskInsurance * 100).toFixed(1)}%. ` +
    `Aviation fuel rises +${(aviationIncrease * 100).toFixed(0)}% to $${costAviation.toFixed(1)}B, ` +
    `depressing tourism by ${(tourismDecline * 100).toFixed(0)}% (−$${(HORMUZ_BASES.tourismBase - tourismRevenue).toFixed(1)}B). ` +
    `Total GDP exposure: $${gdpLoss.toFixed(1)}B.`

  const chainNarrativeAr =
    `إغلاق هرمز (حدة ${(hormuzSeverity * 100).toFixed(0)}%) يخفض تدفق النفط إلى ${(F_flow * 100).toFixed(0)}%، ` +
    `ويقلص الصادرات بمقدار $${(HORMUZ_BASES.oilExport - oilExport).toFixed(0)} مليار. ` +
    `ترتفع تكاليف الشحن +${(shippingIncrease * 100).toFixed(0)}% إلى $${costShipping.toFixed(1)} مليار، ` +
    `مما يرفع مخاطر التأمين إلى ${(riskInsurance * 100).toFixed(1)}%. ` +
    `يرتفع وقود الطيران +${(aviationIncrease * 100).toFixed(0)}% إلى $${costAviation.toFixed(1)} مليار، ` +
    `مما يخفض السياحة ${(tourismDecline * 100).toFixed(0)}% (−$${(HORMUZ_BASES.tourismBase - tourismRevenue).toFixed(1)} مليار). ` +
    `إجمالي التعرض: $${gdpLoss.toFixed(1)} مليار.`

  return { steps, gdpLoss, chainNarrative, chainNarrativeAr }
}

/* ═══════════════════════════════════════════════════════════════
   AVIATION CHAIN — Phase 2 Financial Formula Engine
   Chain: Insurance → Fuel → Flight Cost → Demand → Throughput → Tourism → GDP
   ═══════════════════════════════════════════════════════════════ */

export interface AviationChainStep {
  id: string
  label: string
  labelAr: string
  formula: string
  formulaAr: string
  value: number
  base: number
  unit: string
  direction: '↑' | '↓'
  impactPct: number
}

export interface AviationChainResult {
  steps: AviationChainStep[]
  gdpImpact: number
  chainNarrative: string
  chainNarrativeAr: string
  airportImpacts: { id: string; label: string; labelAr: string; paxM: number; basePaxM: number; changePct: number }[]
}

const AVIATION_BASES = {
  fuelCost: 45,          // $B annual GCC aviation fuel
  baseTicket: 380,       // $ average GCC round-trip ticket
  baseDemand: 350,       // M passengers/year GCC airports
  tourismBase: 85,       // $B annual GCC tourism revenue
  W_insurance: 1.2,      // fuel sensitivity to insurance risk
  W_fuel: 0.65,          // ticket sensitivity to fuel cost increase
  W_price: 0.55,         // demand sensitivity to ticket price increase
}

const AIRPORT_PAX: Record<string, { label: string; labelAr: string; basePaxM: number }> = {
  inf_dxb: { label: 'DXB', labelAr: 'دبي', basePaxM: 87.0 },
  inf_ruh: { label: 'RUH', labelAr: 'الرياض', basePaxM: 35.0 },
  inf_jed: { label: 'JED', labelAr: 'جدة', basePaxM: 46.0 },
  inf_doh: { label: 'DOH', labelAr: 'الدوحة', basePaxM: 38.0 },
  inf_auh: { label: 'AUH', labelAr: 'أبوظبي', basePaxM: 24.0 },
  inf_dmm: { label: 'DMM', labelAr: 'الدمام', basePaxM: 12.0 },
  inf_kwi: { label: 'KWI', labelAr: 'الكويت', basePaxM: 15.0 },
  inf_bah: { label: 'BAH', labelAr: 'البحرين', basePaxM: 10.0 },
  inf_mct: { label: 'MCT', labelAr: 'مسقط', basePaxM: 18.0 },
}

export function computeAviationChain(
  impacts: Map<string, number>,
  severity: number = 1.0,
): AviationChainResult {
  const absI = (id: string) => Math.abs(impacts.get(id) ?? 0)

  // Step 1: Fuel_cost = Base_fuel × (1 + Risk_insurance × W_insurance)
  const insRisk = absI('fin_ins_risk') * severity
  const fuelCost = AVIATION_BASES.fuelCost * (1 + insRisk * AVIATION_BASES.W_insurance)
  const fuelIncrease = (fuelCost - AVIATION_BASES.fuelCost) / AVIATION_BASES.fuelCost

  // Step 2: Flight_cost = Base_ticket × (1 + Fuel_increase × W_fuel)
  const flightCost = AVIATION_BASES.baseTicket * (1 + fuelIncrease * AVIATION_BASES.W_fuel)
  const ticketIncrease = (flightCost - AVIATION_BASES.baseTicket) / AVIATION_BASES.baseTicket

  // Step 3: Demand = Base_demand × (1 - Ticket_increase × W_price)
  const demand = AVIATION_BASES.baseDemand * Math.max(0, 1 - ticketIncrease * AVIATION_BASES.W_price)
  const demandDecline = (AVIATION_BASES.baseDemand - demand) / AVIATION_BASES.baseDemand

  // Step 4: Throughput per airport = Base_pax × demand_factor
  const demandFactor = demand / AVIATION_BASES.baseDemand
  const airportImpacts = Object.entries(AIRPORT_PAX).map(([id, info]) => {
    const airportSpecific = absI(id) * severity
    const combinedFactor = Math.max(0, demandFactor * (1 - airportSpecific * 0.3))
    const paxM = info.basePaxM * combinedFactor
    return {
      id,
      label: info.label,
      labelAr: info.labelAr,
      paxM: Math.round(paxM * 10) / 10,
      basePaxM: info.basePaxM,
      changePct: ((paxM - info.basePaxM) / info.basePaxM) * 100,
    }
  })

  // Step 5: Tourism_revenue = Base_tourism × demand_factor
  const tourismRevenue = AVIATION_BASES.tourismBase * Math.max(0, demandFactor)
  const tourismDecline = (AVIATION_BASES.tourismBase - tourismRevenue) / AVIATION_BASES.tourismBase

  // Step 6: GDP_impact = fuel_increase + tourism_decline + airline_loss
  const gdpImpact = (fuelIncrease * 45) + (tourismDecline * 85) + (demandDecline * 25)

  const steps: AviationChainStep[] = [
    {
      id: 'fuel', label: 'Aviation Fuel Cost', labelAr: 'تكلفة وقود الطيران',
      formula: `$${AVIATION_BASES.fuelCost}B × (1 + ${(insRisk * 100).toFixed(0)}% × ${AVIATION_BASES.W_insurance}) = $${fuelCost.toFixed(1)}B`,
      formulaAr: `$${AVIATION_BASES.fuelCost} مليار × (1 + ${(insRisk * 100).toFixed(0)}% × ${AVIATION_BASES.W_insurance}) = $${fuelCost.toFixed(1)} مليار`,
      value: fuelCost, base: AVIATION_BASES.fuelCost, unit: '$B', direction: '↑', impactPct: fuelIncrease * 100,
    },
    {
      id: 'ticket', label: 'Flight Cost', labelAr: 'تكلفة الرحلات',
      formula: `$${AVIATION_BASES.baseTicket} × (1 + ${(fuelIncrease * 100).toFixed(0)}% × ${AVIATION_BASES.W_fuel}) = $${flightCost.toFixed(0)}`,
      formulaAr: `$${AVIATION_BASES.baseTicket} × (1 + ${(fuelIncrease * 100).toFixed(0)}% × ${AVIATION_BASES.W_fuel}) = $${flightCost.toFixed(0)}`,
      value: flightCost, base: AVIATION_BASES.baseTicket, unit: '$', direction: '↑', impactPct: ticketIncrease * 100,
    },
    {
      id: 'demand', label: 'Travel Demand', labelAr: 'الطلب على السفر',
      formula: `${AVIATION_BASES.baseDemand}M × (1 - ${(ticketIncrease * 100).toFixed(0)}% × ${AVIATION_BASES.W_price}) = ${demand.toFixed(0)}M`,
      formulaAr: `${AVIATION_BASES.baseDemand} مليون × (1 - ${(ticketIncrease * 100).toFixed(0)}% × ${AVIATION_BASES.W_price}) = ${demand.toFixed(0)} مليون`,
      value: demand, base: AVIATION_BASES.baseDemand, unit: 'M pax', direction: '↓', impactPct: demandDecline * 100,
    },
    {
      id: 'throughput', label: 'Airport Throughput', labelAr: 'حركة المطارات',
      formula: `Total: ${airportImpacts.reduce((s, a) => s + a.paxM, 0).toFixed(0)}M / ${airportImpacts.reduce((s, a) => s + a.basePaxM, 0)}M pax`,
      formulaAr: `الإجمالي: ${airportImpacts.reduce((s, a) => s + a.paxM, 0).toFixed(0)} مليون / ${airportImpacts.reduce((s, a) => s + a.basePaxM, 0)} مليون مسافر`,
      value: airportImpacts.reduce((s, a) => s + a.paxM, 0),
      base: airportImpacts.reduce((s, a) => s + a.basePaxM, 0),
      unit: 'M pax', direction: '↓',
      impactPct: demandDecline * 100,
    },
    {
      id: 'tourism', label: 'Tourism Revenue', labelAr: 'إيرادات السياحة',
      formula: `$${AVIATION_BASES.tourismBase}B × ${(demandFactor * 100).toFixed(0)}% = $${tourismRevenue.toFixed(1)}B`,
      formulaAr: `$${AVIATION_BASES.tourismBase} مليار × ${(demandFactor * 100).toFixed(0)}% = $${tourismRevenue.toFixed(1)} مليار`,
      value: tourismRevenue, base: AVIATION_BASES.tourismBase, unit: '$B', direction: '↓', impactPct: tourismDecline * 100,
    },
    {
      id: 'gdp', label: 'GDP Impact', labelAr: 'أثر الناتج المحلي',
      formula: `Σ (fuel + tourism + airlines) = $${gdpImpact.toFixed(1)}B`,
      formulaAr: `مجموع (الوقود + السياحة + الطيران) = $${gdpImpact.toFixed(1)} مليار`,
      value: gdpImpact, base: 0, unit: '$B', direction: '↓', impactPct: gdpImpact > 0 ? (gdpImpact / 2100) * 100 : 0,
    },
  ]

  const chainNarrative =
    `Insurance risk (${(insRisk * 100).toFixed(0)}%) drives aviation fuel to $${fuelCost.toFixed(1)}B (+${(fuelIncrease * 100).toFixed(0)}%). ` +
    `Flight costs surge to $${flightCost.toFixed(0)}/ticket (+${(ticketIncrease * 100).toFixed(0)}%), ` +
    `depressing travel demand to ${demand.toFixed(0)}M passengers (−${(demandDecline * 100).toFixed(0)}%). ` +
    `Airport throughput falls across all 9 GCC hubs. ` +
    `Tourism revenue drops to $${tourismRevenue.toFixed(1)}B (−${(tourismDecline * 100).toFixed(0)}%). ` +
    `Total aviation GDP impact: $${gdpImpact.toFixed(1)}B.`

  const chainNarrativeAr =
    `مخاطر التأمين (${(insRisk * 100).toFixed(0)}%) ترفع وقود الطيران إلى $${fuelCost.toFixed(1)} مليار (+${(fuelIncrease * 100).toFixed(0)}%). ` +
    `ترتفع تكلفة الرحلات إلى $${flightCost.toFixed(0)}/تذكرة (+${(ticketIncrease * 100).toFixed(0)}%)، ` +
    `مما يخفض الطلب على السفر إلى ${demand.toFixed(0)} مليون مسافر (−${(demandDecline * 100).toFixed(0)}%). ` +
    `تنخفض حركة المطارات في جميع مطارات الخليج التسعة. ` +
    `تتراجع إيرادات السياحة إلى $${tourismRevenue.toFixed(1)} مليار (−${(tourismDecline * 100).toFixed(0)}%). ` +
    `إجمالي أثر الطيران على الناتج المحلي: $${gdpImpact.toFixed(1)} مليار.`

  return { steps, gdpImpact, chainNarrative, chainNarrativeAr, airportImpacts }
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
