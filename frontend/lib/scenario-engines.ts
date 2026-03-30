/* ═══════════════════════════════════════════════════════════════
   Scenario Formula Engines — Scientific Runtime v2.0
   ═══════════════════════════════════════════════════════════════
   Each scenario engine implements the contract:

     scenarioEngines[engineId].compute(impacts, severity) → ScenarioEngineResult

   Pipeline:
     Scenario Input → Shock Variables → Core Equations → Derived Metrics
     → Sector Aggregation → Node Impacts → Explanation Chain

   All engines remain compatible with the shared propagation model:
     x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t)

   The propagation engine computes nodeImpacts first.
   Then the scenario engine reads those impacts and produces:
   - domain-specific derived metrics (chain steps)
   - scenario-specific sector aggregation
   - bilingual explanation narrative
   ═══════════════════════════════════════════════════════════════ */

/* ── Engine Result Types ── */
export interface ScenarioChainStep {
  id: string
  label: string
  labelAr: string
  formula: string
  formulaAr: string
  value: number
  base: number
  unit: string
  direction: '↑' | '↓' | '—'
  impactPct: number
}

export interface ScenarioEngineResult {
  engineId: string
  steps: ScenarioChainStep[]
  totalExposure: number          // $B total economic exposure
  narrative: string              // English explanation chain
  narrativeAr: string            // Arabic explanation chain
  keyMetrics: { label: string; labelAr: string; value: string; color: string }[]
}

export interface ScenarioEngine {
  id: string
  label: string
  labelAr: string
  chainLabel: string             // e.g. "Hormuz → Oil → Shipping → ..."
  chainLabelAr: string
  compute: (impacts: Map<string, number>, severity: number) => ScenarioEngineResult
}

/* ── Shared Financial Base Constants ($B unless noted) ── */
const BASES = {
  oilRevenue: 540,       // GCC annual oil revenue $B
  tourismRevenue: 85,    // GCC tourism $B
  airportPax: 350,       // GCC airport pax M/year
  portTEU: 45,           // GCC port throughput M TEU
  shippingCost: 12,      // GCC shipping cost base $B
  insurancePremium: 28,  // GCC insurance market $B
  aviationFuel: 42,      // GCC aviation fuel cost $B
  baseTicket: 320,       // Average GCC ticket price $
  bankingAssets: 2800,   // GCC commercial banking assets $B
  cbReserves: 780,       // GCC central bank reserves $B
  swfAssets: 3500,       // GCC SWF total $B
  gccGDP: 2100,          // GCC combined GDP $B
  powerCapacity: 180,    // GCC power capacity GW
  desalCapacity: 22,     // GCC desal capacity B liters/day
  foodImports: 48,       // GCC food imports $B/year
  hajjRevenue: 12,       // Saudi Hajj/Umrah revenue $B
  fdiInflows: 35,        // GCC FDI annual $B
  vision2030Budget: 1300,// Vision 2030 total committed $B
}

/* ── Helper: get impact or default ── */
function imp(impacts: Map<string, number>, nodeId: string, fallback = 0): number {
  return Math.abs(impacts.get(nodeId) ?? fallback)
}

/* ── Helper: clamp ── */
function clamp(v: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, v))
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 1: HORMUZ CLOSURE
   Hormuz → Oil Revenue → Shipping Cost → Insurance → Aviation → Tourism → GDP
   ════════════════════════════════════════════════════════════════ */
function computeHormuzEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const h = imp(impacts, 'geo_hormuz', severity)
  const oilDrop = clamp(h * 100 * 0.85)
  const oilLoss = BASES.oilRevenue * (oilDrop / 100)
  const shipSpike = clamp(h * 100 * 1.2)
  const shipCost = BASES.shippingCost * (shipSpike / 100)
  const insSpike = clamp(h * 100 * 1.5)
  const insCost = BASES.insurancePremium * (insSpike / 100)
  const avFuel = clamp(h * 100 * 0.6)
  const avCost = BASES.aviationFuel * (avFuel / 100)
  const tourDrop = clamp(h * 100 * 0.45)
  const tourLoss = BASES.tourismRevenue * (tourDrop / 100)
  const gdpLoss = (oilLoss + shipCost + insCost + avCost + tourLoss) * 0.65

  return {
    engineId: 'hormuz_closure',
    steps: [
      { id: 'oil', label: 'Oil Revenue Loss', labelAr: 'خسارة إيرادات النفط', formula: `OilLoss = $${BASES.oilRevenue}B × ${oilDrop.toFixed(0)}%`, formulaAr: `خسارة النفط = $${BASES.oilRevenue}B × ${oilDrop.toFixed(0)}%`, value: oilLoss, base: BASES.oilRevenue, unit: '$B', direction: '↓', impactPct: oilDrop },
      { id: 'ship', label: 'Shipping Cost Spike', labelAr: 'ارتفاع تكلفة الشحن', formula: `ShipCost = $${BASES.shippingCost}B × ${shipSpike.toFixed(0)}%`, formulaAr: `تكلفة الشحن = $${BASES.shippingCost}B × ${shipSpike.toFixed(0)}%`, value: shipCost, base: BASES.shippingCost, unit: '$B', direction: '↑', impactPct: shipSpike },
      { id: 'ins', label: 'Insurance Repricing', labelAr: 'إعادة تسعير التأمين', formula: `InsCost = $${BASES.insurancePremium}B × ${insSpike.toFixed(0)}%`, formulaAr: `تكلفة التأمين = $${BASES.insurancePremium}B × ${insSpike.toFixed(0)}%`, value: insCost, base: BASES.insurancePremium, unit: '$B', direction: '↑', impactPct: insSpike },
      { id: 'av', label: 'Aviation Fuel Surge', labelAr: 'ارتفاع وقود الطيران', formula: `AvFuel = $${BASES.aviationFuel}B × ${avFuel.toFixed(0)}%`, formulaAr: `وقود الطيران = $${BASES.aviationFuel}B × ${avFuel.toFixed(0)}%`, value: avCost, base: BASES.aviationFuel, unit: '$B', direction: '↑', impactPct: avFuel },
      { id: 'tour', label: 'Tourism Revenue Loss', labelAr: 'خسارة إيرادات السياحة', formula: `TourLoss = $${BASES.tourismRevenue}B × ${tourDrop.toFixed(0)}%`, formulaAr: `خسارة السياحة = $${BASES.tourismRevenue}B × ${tourDrop.toFixed(0)}%`, value: tourLoss, base: BASES.tourismRevenue, unit: '$B', direction: '↓', impactPct: tourDrop },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = ΣLosses × 0.65 = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = مجموع الخسائر × 0.65 = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Hormuz blockade at ${(h * 100).toFixed(0)}% severity cuts oil flow by ${oilDrop.toFixed(0)}%, spikes shipping costs by ${shipSpike.toFixed(0)}%, reprices insurance by ${insSpike.toFixed(0)}%, and cascades through aviation and tourism. Total GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `إغلاق هرمز بشدة ${(h * 100).toFixed(0)}% يقطع تدفق النفط بنسبة ${oilDrop.toFixed(0)}%، يرفع تكاليف الشحن ${shipSpike.toFixed(0)}%، يعيد تسعير التأمين ${insSpike.toFixed(0)}%، ويتسلسل عبر الطيران والسياحة. إجمالي التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Oil Revenue Loss', labelAr: 'خسارة النفط', value: `$${oilLoss.toFixed(1)}B`, color: '#ef4444' },
      { label: 'Shipping Spike', labelAr: 'ارتفاع الشحن', value: `+${shipSpike.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Insurance Spike', labelAr: 'ارتفاع التأمين', value: `+${insSpike.toFixed(0)}%`, color: '#a78bfa' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 2: US–IRAN ESCALATION
   ════════════════════════════════════════════════════════════════ */
function computeEscalationEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const h = imp(impacts, 'geo_hormuz', severity * 0.6)
  const ins = imp(impacts, 'fin_insurers', severity * 0.7)
  const ship = imp(impacts, 'eco_shipping', severity * 0.5)

  const riskBps = clamp(severity * 400, 50, 600)
  const capitalFlight = clamp(severity * 100 * 0.35)
  const shipSpike = clamp(ship * 100 * 0.8 + riskBps * 0.05)
  const insSpike = clamp(ins * 100 * 1.2)
  const marketDrop = clamp(severity * 100 * 0.25)
  const gdpLoss = (BASES.oilRevenue * capitalFlight / 100 * 0.3) + (BASES.shippingCost * shipSpike / 100) + (BASES.insurancePremium * insSpike / 100) + (BASES.gccGDP * marketDrop / 100 * 0.1)

  return {
    engineId: 'us_iran_escalation',
    steps: [
      { id: 'risk', label: 'Risk Premium', labelAr: 'علاوة المخاطر', formula: `ΔBps = severity × 400 = +${riskBps.toFixed(0)} bps`, formulaAr: `نقاط الأساس = الشدة × 400 = +${riskBps.toFixed(0)}`, value: riskBps, base: 0, unit: 'bps', direction: '↑', impactPct: riskBps / 4 },
      { id: 'capital', label: 'Capital Flight', labelAr: 'هروب رؤوس الأموال', formula: `Flight = ${capitalFlight.toFixed(0)}% of flows`, formulaAr: `الهروب = ${capitalFlight.toFixed(0)}% من التدفقات`, value: capitalFlight, base: 100, unit: '%', direction: '↓', impactPct: capitalFlight },
      { id: 'ship', label: 'Shipping Disruption', labelAr: 'تعطل الشحن', formula: `ShipΔ = +${shipSpike.toFixed(0)}%`, formulaAr: `تغير الشحن = +${shipSpike.toFixed(0)}%`, value: shipSpike, base: 100, unit: '%', direction: '↑', impactPct: shipSpike },
      { id: 'ins', label: 'Insurance Repricing', labelAr: 'إعادة تسعير التأمين', formula: `InsΔ = +${insSpike.toFixed(0)}%`, formulaAr: `تغير التأمين = +${insSpike.toFixed(0)}%`, value: insSpike, base: 100, unit: '%', direction: '↑', impactPct: insSpike },
      { id: 'market', label: 'Market Drop', labelAr: 'انخفاض الأسواق', formula: `Tadawul Δ = −${marketDrop.toFixed(0)}%`, formulaAr: `تداول = −${marketDrop.toFixed(0)}%`, value: marketDrop, base: 100, unit: '%', direction: '↓', impactPct: marketDrop },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Limited escalation raises risk premium by ${riskBps.toFixed(0)} bps, triggers ${capitalFlight.toFixed(0)}% capital flight, and reprices insurance +${insSpike.toFixed(0)}%. Markets drop ${marketDrop.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `تصعيد محدود يرفع علاوة المخاطر ${riskBps.toFixed(0)} نقطة أساس، يُطلق ${capitalFlight.toFixed(0)}% هروب رؤوس الأموال، ويعيد تسعير التأمين +${insSpike.toFixed(0)}%. الأسواق تنخفض ${marketDrop.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Risk Premium', labelAr: 'علاوة المخاطر', value: `+${riskBps.toFixed(0)} bps`, color: '#f59e0b' },
      { label: 'Capital Flight', labelAr: 'هروب الأموال', value: `${capitalFlight.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Market Drop', labelAr: 'انخفاض السوق', value: `−${marketDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 3: AIRSPACE RESTRICTION
   ════════════════════════════════════════════════════════════════ */
function computeAirspaceEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const av = imp(impacts, 'eco_aviation', severity * 0.7)
  const fuelSpike = clamp(av * 100 * 0.8)
  const ticketSpike = clamp(fuelSpike * 0.6 + 10)
  const demandDrop = clamp(ticketSpike * 0.7)
  const airlineStress = clamp(av * 100 * 0.9)
  const tourDrop = clamp(demandDrop * 0.65)
  const tourLoss = BASES.tourismRevenue * (tourDrop / 100)
  const avLoss = BASES.aviationFuel * (fuelSpike / 100)
  const gdpLoss = (tourLoss + avLoss) * 0.7

  return {
    engineId: 'airspace_restriction',
    steps: [
      { id: 'fuel', label: 'Fuel Burn Increase', labelAr: 'زيادة استهلاك الوقود', formula: `Fuel Δ = +${fuelSpike.toFixed(0)}%`, formulaAr: `تغير الوقود = +${fuelSpike.toFixed(0)}%`, value: fuelSpike, base: 100, unit: '%', direction: '↑', impactPct: fuelSpike },
      { id: 'ticket', label: 'Ticket Price Surge', labelAr: 'ارتفاع أسعار التذاكر', formula: `Ticket Δ = +${ticketSpike.toFixed(0)}%`, formulaAr: `تغير التذاكر = +${ticketSpike.toFixed(0)}%`, value: ticketSpike, base: BASES.baseTicket, unit: '$', direction: '↑', impactPct: ticketSpike },
      { id: 'demand', label: 'Travel Demand Drop', labelAr: 'انخفاض الطلب على السفر', formula: `Demand Δ = −${demandDrop.toFixed(0)}%`, formulaAr: `تغير الطلب = −${demandDrop.toFixed(0)}%`, value: demandDrop, base: 100, unit: '%', direction: '↓', impactPct: demandDrop },
      { id: 'airline', label: 'Airline Stress', labelAr: 'ضغط شركات الطيران', formula: `Stress = ${airlineStress.toFixed(0)}%`, formulaAr: `الضغط = ${airlineStress.toFixed(0)}%`, value: airlineStress, base: 100, unit: '%', direction: '↑', impactPct: airlineStress },
      { id: 'tour', label: 'Tourism Loss', labelAr: 'خسارة السياحة', formula: `TourLoss = $${BASES.tourismRevenue}B × ${tourDrop.toFixed(0)}%`, formulaAr: `خسارة السياحة = $${BASES.tourismRevenue}B × ${tourDrop.toFixed(0)}%`, value: tourLoss, base: BASES.tourismRevenue, unit: '$B', direction: '↓', impactPct: tourDrop },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Airspace restriction spikes fuel costs +${fuelSpike.toFixed(0)}%, raises ticket prices +${ticketSpike.toFixed(0)}%, drops travel demand ${demandDrop.toFixed(0)}%, and hits tourism by $${tourLoss.toFixed(1)}B. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `تقييد المجال الجوي يرفع تكاليف الوقود +${fuelSpike.toFixed(0)}%، أسعار التذاكر +${ticketSpike.toFixed(0)}%، ينخفض الطلب ${demandDrop.toFixed(0)}%، ويضرب السياحة بـ $${tourLoss.toFixed(1)}B. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Fuel Spike', labelAr: 'ارتفاع الوقود', value: `+${fuelSpike.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Demand Drop', labelAr: 'انخفاض الطلب', value: `−${demandDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Airline Stress', labelAr: 'ضغط الطيران', value: `${airlineStress.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 4: HAJJ DISRUPTION
   ════════════════════════════════════════════════════════════════ */
function computeHajjEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const hajj = imp(impacts, 'soc_hajj', severity * 0.85)
  const jed = imp(impacts, 'inf_jed', severity * 0.7)
  const pilgrimDrop = clamp(hajj * 100 * 0.9)
  const pilgrimsLost = 2.0 * (pilgrimDrop / 100)
  const jedDrop = clamp(jed * 100 * 0.8)
  const hajjLoss = BASES.hajjRevenue * (pilgrimDrop / 100)
  const tourLoss = BASES.tourismRevenue * (pilgrimDrop / 100) * 0.15
  const gdpLoss = hajjLoss + tourLoss

  return {
    engineId: 'hajj_disruption',
    steps: [
      { id: 'pilgrim', label: 'Pilgrim Volume Drop', labelAr: 'انخفاض أعداد الحجاج', formula: `Pilgrims Δ = −${pilgrimDrop.toFixed(0)}% (${pilgrimsLost.toFixed(1)}M lost)`, formulaAr: `تغير الحجاج = −${pilgrimDrop.toFixed(0)}% (${pilgrimsLost.toFixed(1)}M)`, value: pilgrimDrop, base: 100, unit: '%', direction: '↓', impactPct: pilgrimDrop },
      { id: 'jed', label: 'JED Airport Impact', labelAr: 'تأثير مطار جدة', formula: `JED Δ = −${jedDrop.toFixed(0)}%`, formulaAr: `مطار جدة = −${jedDrop.toFixed(0)}%`, value: jedDrop, base: 100, unit: '%', direction: '↓', impactPct: jedDrop },
      { id: 'hajj_rev', label: 'Hajj Revenue Loss', labelAr: 'خسارة إيرادات الحج', formula: `HajjLoss = $${BASES.hajjRevenue}B × ${pilgrimDrop.toFixed(0)}%`, formulaAr: `خسارة الحج = $${BASES.hajjRevenue}B × ${pilgrimDrop.toFixed(0)}%`, value: hajjLoss, base: BASES.hajjRevenue, unit: '$B', direction: '↓', impactPct: pilgrimDrop },
      { id: 'tour', label: 'Tourism Spillover', labelAr: 'تأثير السياحة', formula: `TourLoss = $${tourLoss.toFixed(1)}B`, formulaAr: `خسارة السياحة = $${tourLoss.toFixed(1)}B`, value: tourLoss, base: BASES.tourismRevenue, unit: '$B', direction: '↓', impactPct: (tourLoss / BASES.tourismRevenue) * 100 },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Hajj disruption drops pilgrim volume by ${pilgrimDrop.toFixed(0)}% (${pilgrimsLost.toFixed(1)}M pilgrims lost), JED airport capacity drops ${jedDrop.toFixed(0)}%. Hajj revenue loss: $${hajjLoss.toFixed(1)}B. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `تعطل الحج يخفض أعداد الحجاج ${pilgrimDrop.toFixed(0)}% (${pilgrimsLost.toFixed(1)}M حاج)، طاقة مطار جدة تنخفض ${jedDrop.toFixed(0)}%. خسارة إيرادات الحج: $${hajjLoss.toFixed(1)}B. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Pilgrims Lost', labelAr: 'حجاج مفقودون', value: `${pilgrimsLost.toFixed(1)}M`, color: '#ef4444' },
      { label: 'Hajj Revenue', labelAr: 'إيرادات الحج', value: `−$${hajjLoss.toFixed(1)}B`, color: '#ef4444' },
      { label: 'JED Impact', labelAr: 'تأثير جدة', value: `−${jedDrop.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 5: JEBEL ALI PORT DISRUPTION
   ════════════════════════════════════════════════════════════════ */
function computeJebelAliEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const jebel = imp(impacts, 'inf_jebel', severity * 0.8)
  const ship = imp(impacts, 'eco_shipping', severity * 0.6)
  const teuDrop = clamp(jebel * 100 * 0.85)
  const teuLost = BASES.portTEU * (teuDrop / 100)
  const tradeDelay = clamp(jebel * 100 * 0.7)
  const tradeLoss = teuLost * 0.09
  const insSpike = clamp(ship * 100 * 0.8)
  const logCost = BASES.shippingCost * (insSpike / 100) * 0.5
  const gdpLoss = tradeLoss + logCost

  return {
    engineId: 'jebel_ali_disruption',
    steps: [
      { id: 'teu', label: 'Container Volume Drop', labelAr: 'انخفاض حجم الحاويات', formula: `TEU Δ = −${teuDrop.toFixed(0)}% (${teuLost.toFixed(1)}M TEU)`, formulaAr: `حاويات = −${teuDrop.toFixed(0)}% (${teuLost.toFixed(1)}M)`, value: teuDrop, base: 100, unit: '%', direction: '↓', impactPct: teuDrop },
      { id: 'delay', label: 'Trade Delay', labelAr: 'تأخير التجارة', formula: `Delay = ${tradeDelay.toFixed(0)}% of throughput`, formulaAr: `التأخير = ${tradeDelay.toFixed(0)}% من الطاقة`, value: tradeDelay, base: 100, unit: '%', direction: '↑', impactPct: tradeDelay },
      { id: 'trade', label: 'Trade Loss', labelAr: 'خسارة التجارة', formula: `TradeLoss = $${tradeLoss.toFixed(1)}B`, formulaAr: `خسارة التجارة = $${tradeLoss.toFixed(1)}B`, value: tradeLoss, base: BASES.portTEU, unit: '$B', direction: '↓', impactPct: teuDrop },
      { id: 'ins', label: 'Insurance Spike', labelAr: 'ارتفاع التأمين', formula: `Ins Δ = +${insSpike.toFixed(0)}%`, formulaAr: `تغير التأمين = +${insSpike.toFixed(0)}%`, value: insSpike, base: 100, unit: '%', direction: '↑', impactPct: insSpike },
      { id: 'log', label: 'Logistics Cost', labelAr: 'تكلفة الخدمات اللوجستية', formula: `LogCost = $${logCost.toFixed(1)}B`, formulaAr: `تكلفة اللوجستية = $${logCost.toFixed(1)}B`, value: logCost, base: BASES.shippingCost, unit: '$B', direction: '↑', impactPct: (logCost / BASES.shippingCost) * 100 },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Jebel Ali disruption drops container throughput by ${teuDrop.toFixed(0)}% (${teuLost.toFixed(1)}M TEU lost), trade delays reach ${tradeDelay.toFixed(0)}%, insurance spikes ${insSpike.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `تعطل جبل علي يخفض حجم الحاويات ${teuDrop.toFixed(0)}% (${teuLost.toFixed(1)}M حاوية)، التأخيرات ${tradeDelay.toFixed(0)}%، التأمين يرتفع ${insSpike.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'TEU Lost', labelAr: 'حاويات مفقودة', value: `${teuLost.toFixed(1)}M`, color: '#ef4444' },
      { label: 'Trade Loss', labelAr: 'خسارة التجارة', value: `$${tradeLoss.toFixed(1)}B`, color: '#ef4444' },
      { label: 'Insurance', labelAr: 'التأمين', value: `+${insSpike.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 6: FOOD SECURITY SHOCK
   ════════════════════════════════════════════════════════════════ */
function computeFoodEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const food = imp(impacts, 'eco_food', severity * 0.85)
  const importDrop = clamp(food * 100 * 0.85)
  const bufferDays = Math.max(0, 90 - 90 * (importDrop / 100))
  const priceSpike = clamp(importDrop * 1.2)
  const colIncrease = clamp(priceSpike * 0.6)
  const socialStress = clamp(colIncrease * 0.8)
  const foodCost = BASES.foodImports * (importDrop / 100)
  const gdpLoss = foodCost * 0.4 + BASES.gccGDP * (socialStress / 100) * 0.02

  return {
    engineId: 'food_security_shock',
    steps: [
      { id: 'import', label: 'Food Import Drop', labelAr: 'انخفاض استيراد الغذاء', formula: `Import Δ = −${importDrop.toFixed(0)}%`, formulaAr: `تغير الاستيراد = −${importDrop.toFixed(0)}%`, value: importDrop, base: 100, unit: '%', direction: '↓', impactPct: importDrop },
      { id: 'buffer', label: 'Buffer Remaining', labelAr: 'المخزون المتبقي', formula: `Buffer = ${bufferDays.toFixed(0)} days`, formulaAr: `المخزون = ${bufferDays.toFixed(0)} يوم`, value: bufferDays, base: 90, unit: 'days', direction: '↓', impactPct: (1 - bufferDays / 90) * 100 },
      { id: 'price', label: 'Food Price Spike', labelAr: 'ارتفاع أسعار الغذاء', formula: `Price Δ = +${priceSpike.toFixed(0)}%`, formulaAr: `تغير الأسعار = +${priceSpike.toFixed(0)}%`, value: priceSpike, base: 100, unit: '%', direction: '↑', impactPct: priceSpike },
      { id: 'col', label: 'Cost of Living', labelAr: 'تكلفة المعيشة', formula: `COL Δ = +${colIncrease.toFixed(0)}%`, formulaAr: `تكلفة المعيشة = +${colIncrease.toFixed(0)}%`, value: colIncrease, base: 100, unit: '%', direction: '↑', impactPct: colIncrease },
      { id: 'social', label: 'Social Stress', labelAr: 'الضغط الاجتماعي', formula: `Stress = ${socialStress.toFixed(0)}%`, formulaAr: `الضغط = ${socialStress.toFixed(0)}%`, value: socialStress, base: 100, unit: '%', direction: '↑', impactPct: socialStress },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Food imports drop ${importDrop.toFixed(0)}%, buffer falls to ${bufferDays.toFixed(0)} days. Prices spike ${priceSpike.toFixed(0)}%, cost of living rises ${colIncrease.toFixed(0)}%, social stress at ${socialStress.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `واردات الغذاء تنخفض ${importDrop.toFixed(0)}%، المخزون ينخفض لـ ${bufferDays.toFixed(0)} يوم. الأسعار ترتفع ${priceSpike.toFixed(0)}%، تكلفة المعيشة +${colIncrease.toFixed(0)}%، الضغط الاجتماعي ${socialStress.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Buffer Days', labelAr: 'أيام المخزون', value: `${bufferDays.toFixed(0)}d`, color: bufferDays < 30 ? '#ef4444' : '#f59e0b' },
      { label: 'Price Spike', labelAr: 'ارتفاع الأسعار', value: `+${priceSpike.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Social Stress', labelAr: 'ضغط اجتماعي', value: `${socialStress.toFixed(0)}%`, color: socialStress > 50 ? '#ef4444' : '#f59e0b' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 7: LIQUIDITY STRESS
   ════════════════════════════════════════════════════════════════ */
function computeLiquidityEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const bank = imp(impacts, 'fin_banking', severity * 0.8)
  const withdrawal = clamp(bank * 100 * 0.7)
  const lcrDrop = clamp(withdrawal * 0.9)
  const lendingFreeze = clamp(lcrDrop * 0.75)
  const creditCrunch = clamp(lendingFreeze * 0.8)
  const employDrop = clamp(creditCrunch * 0.4)
  const bankLoss = BASES.bankingAssets * (withdrawal / 100) * 0.05
  const gdpLoss = bankLoss + BASES.gccGDP * (employDrop / 100) * 0.08

  return {
    engineId: 'liquidity_stress',
    steps: [
      { id: 'withdraw', label: 'Deposit Withdrawal', labelAr: 'سحب الودائع', formula: `Withdrawal = ${withdrawal.toFixed(0)}%`, formulaAr: `السحب = ${withdrawal.toFixed(0)}%`, value: withdrawal, base: 100, unit: '%', direction: '↓', impactPct: withdrawal },
      { id: 'lcr', label: 'LCR Drop', labelAr: 'انخفاض نسبة تغطية السيولة', formula: `LCR Δ = −${lcrDrop.toFixed(0)}%`, formulaAr: `نسبة التغطية = −${lcrDrop.toFixed(0)}%`, value: lcrDrop, base: 100, unit: '%', direction: '↓', impactPct: lcrDrop },
      { id: 'lending', label: 'Lending Freeze', labelAr: 'تجميد الإقراض', formula: `Lending Δ = −${lendingFreeze.toFixed(0)}%`, formulaAr: `الإقراض = −${lendingFreeze.toFixed(0)}%`, value: lendingFreeze, base: 100, unit: '%', direction: '↓', impactPct: lendingFreeze },
      { id: 'credit', label: 'Credit Crunch', labelAr: 'أزمة ائتمان', formula: `Credit Δ = −${creditCrunch.toFixed(0)}%`, formulaAr: `الائتمان = −${creditCrunch.toFixed(0)}%`, value: creditCrunch, base: 100, unit: '%', direction: '↓', impactPct: creditCrunch },
      { id: 'employ', label: 'Employment Impact', labelAr: 'تأثير التوظيف', formula: `Employ Δ = −${employDrop.toFixed(0)}%`, formulaAr: `التوظيف = −${employDrop.toFixed(0)}%`, value: employDrop, base: 100, unit: '%', direction: '↓', impactPct: employDrop },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Sovereign deposits withdrawn ${withdrawal.toFixed(0)}%, LCR drops ${lcrDrop.toFixed(0)}%, lending freezes ${lendingFreeze.toFixed(0)}%. Credit crunch hits employment by ${employDrop.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `سحب الودائع السيادية ${withdrawal.toFixed(0)}%، نسبة التغطية تنخفض ${lcrDrop.toFixed(0)}%، الإقراض يتجمد ${lendingFreeze.toFixed(0)}%. أزمة الائتمان تضرب التوظيف ${employDrop.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Withdrawal', labelAr: 'السحب', value: `${withdrawal.toFixed(0)}%`, color: '#ef4444' },
      { label: 'LCR Drop', labelAr: 'انخفاض التغطية', value: `−${lcrDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Credit Crunch', labelAr: 'أزمة ائتمان', value: `−${creditCrunch.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 8: FX / GOLD / CRYPTO SHOCK
   ════════════════════════════════════════════════════════════════ */
function computeFxEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const sama = imp(impacts, 'fin_sama', severity * 0.5)
  const tadawul = imp(impacts, 'fin_tadawul', severity * 0.6)
  const cbStress = clamp(sama * 100 * 0.8)
  const pegDefense = clamp(cbStress * 0.6)
  const reservesDrain = BASES.cbReserves * (pegDefense / 100) * 0.15
  const marketDrop = clamp(tadawul * 100 * 0.9)
  const swfRebal = clamp(marketDrop * 0.5)
  const swfCost = BASES.swfAssets * (swfRebal / 100) * 0.01
  const gdpLoss = reservesDrain + swfCost + BASES.gccGDP * (marketDrop / 100) * 0.05

  return {
    engineId: 'fx_gold_crypto_shock',
    steps: [
      { id: 'cb', label: 'Central Bank Stress', labelAr: 'ضغط البنك المركزي', formula: `CB Stress = ${cbStress.toFixed(0)}%`, formulaAr: `ضغط المركزي = ${cbStress.toFixed(0)}%`, value: cbStress, base: 100, unit: '%', direction: '↑', impactPct: cbStress },
      { id: 'peg', label: 'Peg Defense Cost', labelAr: 'تكلفة الدفاع عن الربط', formula: `Reserves Drain = $${reservesDrain.toFixed(1)}B`, formulaAr: `استنزاف الاحتياطي = $${reservesDrain.toFixed(1)}B`, value: reservesDrain, base: BASES.cbReserves, unit: '$B', direction: '↓', impactPct: pegDefense },
      { id: 'market', label: 'Market Drop', labelAr: 'انخفاض الأسواق', formula: `Tadawul Δ = −${marketDrop.toFixed(0)}%`, formulaAr: `تداول = −${marketDrop.toFixed(0)}%`, value: marketDrop, base: 100, unit: '%', direction: '↓', impactPct: marketDrop },
      { id: 'swf', label: 'SWF Rebalancing', labelAr: 'إعادة توازن الصندوق السيادي', formula: `SWF Cost = $${swfCost.toFixed(1)}B`, formulaAr: `تكلفة الصندوق = $${swfCost.toFixed(1)}B`, value: swfCost, base: BASES.swfAssets, unit: '$B', direction: '↓', impactPct: swfRebal },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `FX/Markets shock creates ${cbStress.toFixed(0)}% central bank stress, drains $${reservesDrain.toFixed(1)}B in reserves for peg defense. Markets drop ${marketDrop.toFixed(0)}%, SWF rebalancing costs $${swfCost.toFixed(1)}B. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `صدمة العملات/الأسواق تخلق ${cbStress.toFixed(0)}% ضغط على المركزي، تستنزف $${reservesDrain.toFixed(1)}B للدفاع عن الربط. الأسواق تنخفض ${marketDrop.toFixed(0)}%، إعادة التوازن تكلف $${swfCost.toFixed(1)}B. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'CB Stress', labelAr: 'ضغط المركزي', value: `${cbStress.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Reserves Drain', labelAr: 'استنزاف الاحتياطي', value: `$${reservesDrain.toFixed(1)}B`, color: '#ef4444' },
      { label: 'Market Drop', labelAr: 'انخفاض السوق', value: `−${marketDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 9: INSURANCE REPRICING
   ════════════════════════════════════════════════════════════════ */
function computeInsuranceEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const reins = imp(impacts, 'fin_reinsure', severity * 0.8)
  const reinsDrop = clamp(reins * 100 * 0.85)
  const premSpike = clamp(reinsDrop * 1.1)
  const shipCostUp = clamp(premSpike * 0.5)
  const avCostUp = clamp(premSpike * 0.4)
  const selfInsure = clamp(reinsDrop * 0.6)
  const totalCost = BASES.insurancePremium * (premSpike / 100) + BASES.shippingCost * (shipCostUp / 100) * 0.3 + BASES.aviationFuel * (avCostUp / 100) * 0.2
  const gdpLoss = totalCost * 0.7

  return {
    engineId: 'insurance_repricing',
    steps: [
      { id: 'reins', label: 'Reinsurer Withdrawal', labelAr: 'انسحاب إعادة التأمين', formula: `Capacity Δ = −${reinsDrop.toFixed(0)}%`, formulaAr: `الطاقة = −${reinsDrop.toFixed(0)}%`, value: reinsDrop, base: 100, unit: '%', direction: '↓', impactPct: reinsDrop },
      { id: 'prem', label: 'Premium Spike', labelAr: 'ارتفاع الأقساط', formula: `Premium Δ = +${premSpike.toFixed(0)}%`, formulaAr: `الأقساط = +${premSpike.toFixed(0)}%`, value: premSpike, base: 100, unit: '%', direction: '↑', impactPct: premSpike },
      { id: 'ship', label: 'Shipping Cost Impact', labelAr: 'تأثير تكلفة الشحن', formula: `Ship Δ = +${shipCostUp.toFixed(0)}%`, formulaAr: `الشحن = +${shipCostUp.toFixed(0)}%`, value: shipCostUp, base: 100, unit: '%', direction: '↑', impactPct: shipCostUp },
      { id: 'av', label: 'Aviation Cost Impact', labelAr: 'تأثير تكلفة الطيران', formula: `Av Δ = +${avCostUp.toFixed(0)}%`, formulaAr: `الطيران = +${avCostUp.toFixed(0)}%`, value: avCostUp, base: 100, unit: '%', direction: '↑', impactPct: avCostUp },
      { id: 'self', label: 'Self-Insurance Rate', labelAr: 'معدل التأمين الذاتي', formula: `Self-Ins = ${selfInsure.toFixed(0)}%`, formulaAr: `التأمين الذاتي = ${selfInsure.toFixed(0)}%`, value: selfInsure, base: 100, unit: '%', direction: '↑', impactPct: selfInsure },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Reinsurers withdraw ${reinsDrop.toFixed(0)}% of GCC capacity. Premiums spike ${premSpike.toFixed(0)}%, shipping costs +${shipCostUp.toFixed(0)}%, aviation costs +${avCostUp.toFixed(0)}%. Self-insurance rate: ${selfInsure.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `شركات إعادة التأمين تسحب ${reinsDrop.toFixed(0)}% من طاقة الخليج. الأقساط ترتفع ${premSpike.toFixed(0)}%، الشحن +${shipCostUp.toFixed(0)}%، الطيران +${avCostUp.toFixed(0)}%. التأمين الذاتي: ${selfInsure.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Capacity Loss', labelAr: 'فقدان الطاقة', value: `−${reinsDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Premium Spike', labelAr: 'ارتفاع الأقساط', value: `+${premSpike.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Self-Insurance', labelAr: 'تأمين ذاتي', value: `${selfInsure.toFixed(0)}%`, color: '#a78bfa' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 10: GCC GRID FAILURE
   ════════════════════════════════════════════════════════════════ */
function computeGridEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const power = imp(impacts, 'inf_power', severity * 0.85)
  const desal = imp(impacts, 'inf_desal', severity * 0.75)
  const telco = imp(impacts, 'inf_telecom', severity * 0.6)
  const gridDrop = clamp(power * 100 * 0.9)
  const desalDrop = clamp(desal * 100 * 0.85)
  const waterCrisis = clamp(desalDrop * 0.95)
  const telcoDrop = clamp(telco * 100 * 0.7)
  const bizDisrupt = clamp((gridDrop + telcoDrop) * 0.4)
  const gdpLoss = BASES.gccGDP * ((gridDrop + desalDrop + telcoDrop + bizDisrupt) / 400) * 0.08

  return {
    engineId: 'gcc_grid_failure',
    steps: [
      { id: 'grid', label: 'Grid Capacity Drop', labelAr: 'انخفاض طاقة الشبكة', formula: `Grid Δ = −${gridDrop.toFixed(0)}%`, formulaAr: `الشبكة = −${gridDrop.toFixed(0)}%`, value: gridDrop, base: 100, unit: '%', direction: '↓', impactPct: gridDrop },
      { id: 'desal', label: 'Desalination Failure', labelAr: 'فشل التحلية', formula: `Desal Δ = −${desalDrop.toFixed(0)}%`, formulaAr: `التحلية = −${desalDrop.toFixed(0)}%`, value: desalDrop, base: 100, unit: '%', direction: '↓', impactPct: desalDrop },
      { id: 'water', label: 'Water Crisis', labelAr: 'أزمة المياه', formula: `Water = ${waterCrisis.toFixed(0)}% severity`, formulaAr: `المياه = ${waterCrisis.toFixed(0)}% شدة`, value: waterCrisis, base: 100, unit: '%', direction: '↑', impactPct: waterCrisis },
      { id: 'telco', label: 'Telecom Disruption', labelAr: 'تعطل الاتصالات', formula: `Telco Δ = −${telcoDrop.toFixed(0)}%`, formulaAr: `الاتصالات = −${telcoDrop.toFixed(0)}%`, value: telcoDrop, base: 100, unit: '%', direction: '↓', impactPct: telcoDrop },
      { id: 'biz', label: 'Business Disruption', labelAr: 'تعطل الأعمال', formula: `Biz Δ = −${bizDisrupt.toFixed(0)}%`, formulaAr: `الأعمال = −${bizDisrupt.toFixed(0)}%`, value: bizDisrupt, base: 100, unit: '%', direction: '↓', impactPct: bizDisrupt },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Power grid drops ${gridDrop.toFixed(0)}%, desalination fails ${desalDrop.toFixed(0)}%, creating water crisis at ${waterCrisis.toFixed(0)}% severity. Telecom drops ${telcoDrop.toFixed(0)}%, business disruption ${bizDisrupt.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `شبكة الكهرباء تنخفض ${gridDrop.toFixed(0)}%، التحلية تفشل ${desalDrop.toFixed(0)}%، أزمة مياه بشدة ${waterCrisis.toFixed(0)}%. الاتصالات تنخفض ${telcoDrop.toFixed(0)}%، تعطل الأعمال ${bizDisrupt.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Grid Drop', labelAr: 'انخفاض الشبكة', value: `−${gridDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Water Crisis', labelAr: 'أزمة المياه', value: `${waterCrisis.toFixed(0)}%`, color: waterCrisis > 50 ? '#ef4444' : '#f59e0b' },
      { label: 'Telecom', labelAr: 'الاتصالات', value: `−${telcoDrop.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 11: WATER & ELECTRICITY DISRUPTION
   ════════════════════════════════════════════════════════════════ */
function computeWaterEngine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const power = imp(impacts, 'inf_power', severity * 0.8)
  const desal = imp(impacts, 'inf_desal', severity * 0.8)
  const powerDrop = clamp(power * 100 * 0.85)
  const waterDrop = clamp(desal * 100 * 0.9)
  const healthRisk = clamp(waterDrop * 0.8)
  const socialStress = clamp((powerDrop + waterDrop + healthRisk) / 3 * 0.85)
  const stability = clamp(socialStress * 0.7)
  const gdpLoss = BASES.gccGDP * ((powerDrop + waterDrop) / 200) * 0.06

  return {
    engineId: 'water_electricity_disruption',
    steps: [
      { id: 'power', label: 'Power Generation Drop', labelAr: 'انخفاض توليد الطاقة', formula: `Power Δ = −${powerDrop.toFixed(0)}%`, formulaAr: `الطاقة = −${powerDrop.toFixed(0)}%`, value: powerDrop, base: 100, unit: '%', direction: '↓', impactPct: powerDrop },
      { id: 'water', label: 'Water Supply Drop', labelAr: 'انخفاض إمدادات المياه', formula: `Water Δ = −${waterDrop.toFixed(0)}%`, formulaAr: `المياه = −${waterDrop.toFixed(0)}%`, value: waterDrop, base: 100, unit: '%', direction: '↓', impactPct: waterDrop },
      { id: 'health', label: 'Public Health Risk', labelAr: 'مخاطر الصحة العامة', formula: `Health Risk = ${healthRisk.toFixed(0)}%`, formulaAr: `المخاطر الصحية = ${healthRisk.toFixed(0)}%`, value: healthRisk, base: 100, unit: '%', direction: '↑', impactPct: healthRisk },
      { id: 'social', label: 'Social Stress', labelAr: 'الضغط الاجتماعي', formula: `Stress = ${socialStress.toFixed(0)}%`, formulaAr: `الضغط = ${socialStress.toFixed(0)}%`, value: socialStress, base: 100, unit: '%', direction: '↑', impactPct: socialStress },
      { id: 'stability', label: 'Stability Risk', labelAr: 'مخاطر الاستقرار', formula: `Risk = ${stability.toFixed(0)}%`, formulaAr: `المخاطر = ${stability.toFixed(0)}%`, value: stability, base: 100, unit: '%', direction: '↑', impactPct: stability },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `Power drops ${powerDrop.toFixed(0)}%, water supply drops ${waterDrop.toFixed(0)}%. Health risk at ${healthRisk.toFixed(0)}%, social stress ${socialStress.toFixed(0)}%, stability risk ${stability.toFixed(0)}%. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `الطاقة تنخفض ${powerDrop.toFixed(0)}%، إمدادات المياه تنخفض ${waterDrop.toFixed(0)}%. مخاطر صحية ${healthRisk.toFixed(0)}%، ضغط اجتماعي ${socialStress.toFixed(0)}%، مخاطر استقرار ${stability.toFixed(0)}%. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Power Drop', labelAr: 'انخفاض الطاقة', value: `−${powerDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Water Drop', labelAr: 'انخفاض المياه', value: `−${waterDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'Health Risk', labelAr: 'مخاطر صحية', value: `${healthRisk.toFixed(0)}%`, color: healthRisk > 50 ? '#ef4444' : '#f59e0b' },
      { label: 'Stability', labelAr: 'الاستقرار', value: `${stability.toFixed(0)}%`, color: stability > 40 ? '#ef4444' : '#f59e0b' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE 12: VISION 2030 STRESS
   ════════════════════════════════════════════════════════════════ */
function computeVision2030Engine(impacts: Map<string, number>, severity: number): ScenarioEngineResult {
  const tour = imp(impacts, 'eco_tourism', severity * 0.6)
  const employ = imp(impacts, 'soc_employment', severity * 0.5)
  const fdiDrop = clamp(severity * 100 * 0.45)
  const fdiLoss = BASES.fdiInflows * (fdiDrop / 100)
  const projectDelay = clamp(fdiDrop * 0.7)
  const employDrop = clamp(employ * 100 * 0.6 + projectDelay * 0.3)
  const tourDrop = clamp(tour * 100 * 0.5)
  const tourLoss = BASES.tourismRevenue * (tourDrop / 100)
  const gdpLoss = fdiLoss + tourLoss + BASES.gccGDP * (employDrop / 100) * 0.04

  return {
    engineId: 'vision2030_stress',
    steps: [
      { id: 'fdi', label: 'FDI Inflow Drop', labelAr: 'انخفاض الاستثمار الأجنبي', formula: `FDI Δ = −${fdiDrop.toFixed(0)}% ($${fdiLoss.toFixed(1)}B)`, formulaAr: `الاستثمار = −${fdiDrop.toFixed(0)}% ($${fdiLoss.toFixed(1)}B)`, value: fdiDrop, base: 100, unit: '%', direction: '↓', impactPct: fdiDrop },
      { id: 'project', label: 'Project Delays', labelAr: 'تأخيرات المشاريع', formula: `Delay = ${projectDelay.toFixed(0)}% of pipeline`, formulaAr: `التأخير = ${projectDelay.toFixed(0)}% من المشاريع`, value: projectDelay, base: 100, unit: '%', direction: '↑', impactPct: projectDelay },
      { id: 'employ', label: 'Employment Impact', labelAr: 'تأثير التوظيف', formula: `Employ Δ = −${employDrop.toFixed(0)}%`, formulaAr: `التوظيف = −${employDrop.toFixed(0)}%`, value: employDrop, base: 100, unit: '%', direction: '↓', impactPct: employDrop },
      { id: 'tour', label: 'Tourism Corridor Loss', labelAr: 'خسارة ممرات السياحة', formula: `Tour Δ = −${tourDrop.toFixed(0)}% ($${tourLoss.toFixed(1)}B)`, formulaAr: `السياحة = −${tourDrop.toFixed(0)}% ($${tourLoss.toFixed(1)}B)`, value: tourDrop, base: 100, unit: '%', direction: '↓', impactPct: tourDrop },
      { id: 'gdp', label: 'GDP Exposure', labelAr: 'التعرض للناتج المحلي', formula: `GDP = $${gdpLoss.toFixed(1)}B`, formulaAr: `الناتج = $${gdpLoss.toFixed(1)}B`, value: gdpLoss, base: BASES.gccGDP, unit: '$B', direction: '↓', impactPct: (gdpLoss / BASES.gccGDP) * 100 },
    ],
    totalExposure: gdpLoss,
    narrative: `FDI drops ${fdiDrop.toFixed(0)}% ($${fdiLoss.toFixed(1)}B lost), project delays at ${projectDelay.toFixed(0)}%, employment drops ${employDrop.toFixed(0)}%, tourism corridors lose $${tourLoss.toFixed(1)}B. GDP exposure: $${gdpLoss.toFixed(1)}B.`,
    narrativeAr: `الاستثمار الأجنبي ينخفض ${fdiDrop.toFixed(0)}% ($${fdiLoss.toFixed(1)}B)، تأخيرات المشاريع ${projectDelay.toFixed(0)}%، التوظيف ينخفض ${employDrop.toFixed(0)}%، ممرات السياحة تخسر $${tourLoss.toFixed(1)}B. التعرض: $${gdpLoss.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'FDI Loss', labelAr: 'خسارة الاستثمار', value: `$${fdiLoss.toFixed(1)}B`, color: '#ef4444' },
      { label: 'Project Delay', labelAr: 'تأخير المشاريع', value: `${projectDelay.toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Employment', labelAr: 'التوظيف', value: `−${employDrop.toFixed(0)}%`, color: '#ef4444' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${gdpLoss.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   GENERIC FALLBACK ENGINE
   ════════════════════════════════════════════════════════════════ */
function computeGenericEngine(impacts: Map<string, number>, severity: number, engineId: string): ScenarioEngineResult {
  const sorted = [...impacts.entries()]
    .map(([k, v]) => ({ id: k, val: Math.abs(v) }))
    .sort((a, b) => b.val - a.val)
    .slice(0, 6)

  const steps: ScenarioChainStep[] = sorted.map((entry) => {
    const pct = clamp(entry.val * 100)
    return {
      id: entry.id,
      label: entry.id.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
      labelAr: entry.id,
      formula: `Impact = ${pct.toFixed(0)}%`,
      formulaAr: `التأثير = ${pct.toFixed(0)}%`,
      value: pct,
      base: 100,
      unit: '%',
      direction: (entry.val > 0 ? '↑' : '↓') as '↑' | '↓',
      impactPct: pct,
    }
  })

  const avgImpact = sorted.reduce((s, e) => s + e.val, 0) / Math.max(sorted.length, 1)
  const totalExposure = BASES.gccGDP * avgImpact * severity * 0.15

  return {
    engineId,
    steps,
    totalExposure,
    narrative: `Propagation analysis across ${sorted.length} affected nodes. Average impact intensity: ${(avgImpact * 100).toFixed(0)}%. Estimated GDP exposure: $${totalExposure.toFixed(1)}B.`,
    narrativeAr: `تحليل الانتشار عبر ${sorted.length} عقد متأثرة. متوسط شدة التأثير: ${(avgImpact * 100).toFixed(0)}%. التعرض المقدر: $${totalExposure.toFixed(1)}B.`,
    keyMetrics: [
      { label: 'Nodes Affected', labelAr: 'عقد متأثرة', value: `${sorted.length}`, color: '#3b82f6' },
      { label: 'Avg Impact', labelAr: 'متوسط التأثير', value: `${(avgImpact * 100).toFixed(0)}%`, color: '#f59e0b' },
      { label: 'Severity', labelAr: 'الشدة', value: `${(severity * 100).toFixed(0)}%`, color: '#a78bfa' },
      { label: 'GDP Exposure', labelAr: 'تعرض الناتج', value: `$${totalExposure.toFixed(1)}B`, color: '#ef4444' },
    ],
  }
}

/* ════════════════════════════════════════════════════════════════
   ENGINE REGISTRY
   ════════════════════════════════════════════════════════════════ */
export const scenarioEngines: Record<string, ScenarioEngine> = {
  hormuz_closure: {
    id: 'hormuz_closure', label: 'Hormuz Cascade Engine', labelAr: 'محرك سلسلة هرمز',
    chainLabel: 'Hormuz → Oil → Shipping → Insurance → Aviation → Tourism → GDP',
    chainLabelAr: 'هرمز → النفط → الشحن → التأمين → الطيران → السياحة → الناتج',
    compute: computeHormuzEngine,
  },
  us_iran_escalation: {
    id: 'us_iran_escalation', label: 'Escalation Risk Engine', labelAr: 'محرك مخاطر التصعيد',
    chainLabel: 'Risk Premium → Capital Flight → Shipping → Insurance → Markets → GDP',
    chainLabelAr: 'علاوة المخاطر → هروب الأموال → الشحن → التأمين → الأسواق → الناتج',
    compute: computeEscalationEngine,
  },
  airspace_restriction: {
    id: 'airspace_restriction', label: 'Airspace Restriction Engine', labelAr: 'محرك تقييد المجال الجوي',
    chainLabel: 'Airspace → Fuel → Tickets → Demand → Airlines → Tourism → GDP',
    chainLabelAr: 'المجال الجوي → الوقود → التذاكر → الطلب → الطيران → السياحة → الناتج',
    compute: computeAirspaceEngine,
  },
  hajj_disruption: {
    id: 'hajj_disruption', label: 'Hajj Disruption Engine', labelAr: 'محرك تعطل الحج',
    chainLabel: 'Hajj → Pilgrims → JED Airport → Revenue → Tourism → GDP',
    chainLabelAr: 'الحج → الحجاج → مطار جدة → الإيرادات → السياحة → الناتج',
    compute: computeHajjEngine,
  },
  jebel_ali_disruption: {
    id: 'jebel_ali_disruption', label: 'Jebel Ali Port Engine', labelAr: 'محرك ميناء جبل علي',
    chainLabel: 'Port → Containers → Trade Delay → Insurance → Logistics → GDP',
    chainLabelAr: 'الميناء → الحاويات → تأخير التجارة → التأمين → اللوجستية → الناتج',
    compute: computeJebelAliEngine,
  },
  food_security_shock: {
    id: 'food_security_shock', label: 'Food Security Engine', labelAr: 'محرك الأمن الغذائي',
    chainLabel: 'Import → Buffer → Prices → Cost of Living → Social Stress → Stability',
    chainLabelAr: 'الاستيراد → المخزون → الأسعار → تكلفة المعيشة → الضغط الاجتماعي → الاستقرار',
    compute: computeFoodEngine,
  },
  liquidity_stress: {
    id: 'liquidity_stress', label: 'Liquidity Stress Engine', labelAr: 'محرك ضغط السيولة',
    chainLabel: 'Withdrawal → LCR → Lending → Credit → Employment → GDP',
    chainLabelAr: 'السحب → نسبة التغطية → الإقراض → الائتمان → التوظيف → الناتج',
    compute: computeLiquidityEngine,
  },
  fx_gold_crypto_shock: {
    id: 'fx_gold_crypto_shock', label: 'FX/Markets Engine', labelAr: 'محرك العملات والأسواق',
    chainLabel: 'CB Stress → Peg Defense → Market Drop → SWF Rebalancing → GDP',
    chainLabelAr: 'ضغط المركزي → الدفاع عن الربط → انخفاض الأسواق → إعادة التوازن → الناتج',
    compute: computeFxEngine,
  },
  insurance_repricing: {
    id: 'insurance_repricing', label: 'Insurance Repricing Engine', labelAr: 'محرك إعادة تسعير التأمين',
    chainLabel: 'Reinsurer → Premiums → Shipping → Aviation → Self-Insurance → GDP',
    chainLabelAr: 'إعادة التأمين → الأقساط → الشحن → الطيران → التأمين الذاتي → الناتج',
    compute: computeInsuranceEngine,
  },
  gcc_grid_failure: {
    id: 'gcc_grid_failure', label: 'Grid Failure Engine', labelAr: 'محرك انهيار الشبكة',
    chainLabel: 'Grid → Desalination → Water → Telecom → Business → GDP',
    chainLabelAr: 'الشبكة → التحلية → المياه → الاتصالات → الأعمال → الناتج',
    compute: computeGridEngine,
  },
  water_electricity_disruption: {
    id: 'water_electricity_disruption', label: 'Power-Water Engine', labelAr: 'محرك الكهرباء والمياه',
    chainLabel: 'Power → Water → Health → Social Stress → Stability',
    chainLabelAr: 'الكهرباء → المياه → الصحة → الضغط الاجتماعي → الاستقرار',
    compute: computeWaterEngine,
  },
  vision2030_stress: {
    id: 'vision2030_stress', label: 'Vision 2030 Engine', labelAr: 'محرك رؤية 2030',
    chainLabel: 'FDI → Projects → Employment → Tourism → GDP',
    chainLabelAr: 'الاستثمار الأجنبي → المشاريع → التوظيف → السياحة → الناتج',
    compute: computeVision2030Engine,
  },
}

/* ═══ Helper: get engine with fallback ═══ */
export function getScenarioEngine(engineId: string): ScenarioEngine {
  if (scenarioEngines[engineId]) return scenarioEngines[engineId]
  return {
    id: engineId,
    label: 'Generic Engine', labelAr: 'محرك عام',
    chainLabel: 'Impact Propagation Chain',
    chainLabelAr: 'سلسلة انتشار التأثير',
    compute: (impacts, severity) => computeGenericEngine(impacts, severity, engineId),
  }
}
