'use client'

import { useState, useEffect, useMemo, useCallback, useRef, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play, RotateCcw, Globe as GlobeIcon, ArrowLeft, Loader2, CheckCircle2, Circle,
  Activity, Radio, Shield, Zap, BarChart3, List, FileText, Languages,
  X, ChevronLeft, ChevronRight, TrendingUp, Target, Info, Layers,
  Anchor, Plane, AlertTriangle, Network, Users,
} from 'lucide-react'
import dynamic from 'next/dynamic'
import GraphPanel from '@/components/graph/GraphPanel'
import { gccNodes, gccEdges, gccScenarios, layerMeta, SCENARIO_GROUPS, type ScenarioGroup } from '@/lib/gcc-graph'
import { runPropagation, formatPropagationChain, computeSectorFinancials, type PropagationResult, type NodeExplanation, type SectorFinancials } from '@/lib/propagation-engine'
import { getScenarioEngine, type ScenarioEngineResult, type ScenarioEngine } from '@/lib/scenario-engines'
import { setLanguage, getLanguage, type Language } from '@/lib/i18n'
import { shippingRoutes, aviationRoutes, nodeCoordinates } from '@/lib/gcc-coordinates'

const GlobeGL = dynamic(() => import('react-globe.gl'), { ssr: false })

/* ── Layer visual config ── */
const LAYER_COLORS: Record<string, string> = {
  geography: '#22d3ee',
  infrastructure: '#f59e0b',
  economy: '#3b82f6',
  finance: '#a78bfa',
  society: '#ef4444',
}

/* ── Bilingual labels ── */
const UI: Record<string, { en: string; ar: string }> = {
  title: { en: 'Deevo Sim', ar: 'ديفو سيم' },
  controlRoom: { en: 'Regional Command Center', ar: 'مركز القيادة الإقليمي' },
  selectScenario: { en: 'Select Scenario', ar: 'اختر السيناريو' },
  runSim: { en: 'Run Simulation', ar: 'تشغيل المحاكاة' },
  processing: { en: 'Processing...', ar: 'جارٍ المعالجة...' },
  graphView: { en: 'Graph View', ar: 'عرض الرسم البياني' },
  globeView: { en: 'Globe View', ar: 'عرض الكرة الأرضية' },
  impactChain: { en: 'Impact Chain', ar: 'سلسلة التأثير' },
  topDrivers: { en: 'Top Drivers', ar: 'أهم المحركات' },
  sectorImpact: { en: 'Sector Impact', ar: 'التأثير القطاعي' },
  explanation: { en: 'Explanation', ar: 'التفسير' },
  severity: { en: 'Severity', ar: 'الحدة' },
  confidence: { en: 'Confidence', ar: 'الثقة' },
  systemEnergy: { en: 'System Energy', ar: 'طاقة النظام' },
  nodesAffected: { en: 'Nodes Affected', ar: 'العقد المتأثرة' },
  totalLoss: { en: 'Est. Exposure', ar: 'التعرض المقدر' },
  awaitingInput: { en: 'AWAITING INPUT', ar: 'في انتظار الإدخال' },
  running: { en: 'PROCESSING', ar: 'المعالجة جارية' },
  complete: { en: 'COMPLETE', ar: 'مكتمل' },
  ready: { en: 'READY', ar: 'جاهز' },
  runToSee: { en: 'Run a simulation to see results', ar: 'قم بتشغيل محاكاة لعرض النتائج' },
  shockNodes: { en: 'Shock Nodes', ar: 'عقد الصدمة' },
  presets: { en: 'Scenario Presets', ar: 'السيناريوهات المعدة' },
  pipeline: { en: 'Pipeline', ar: 'خط المعالجة' },
  spread: { en: 'Spread Level', ar: 'مستوى الانتشار' },
  desktop: { en: 'Desktop Required', ar: 'مطلوب سطح المكتب' },
  desktopMsg: { en: 'Command Center requires desktop viewport.', ar: 'مركز القيادة يتطلب شاشة سطح المكتب.' },
  rerun: { en: 'Rerun', ar: 'إعادة' },
  reset: { en: 'Reset', ar: 'إعادة تعيين' },
  back: { en: 'Back', ar: 'العودة' },
  buildingGraph: { en: 'Building entity graph...', ar: 'جارٍ بناء الرسم البياني...' },
  nodeDetail: { en: 'Node Detail', ar: 'تفاصيل العقدة' },
  impact: { en: 'Impact', ar: 'التأثير' },
  sensitivityLabel: { en: 'Sensitivity', ar: 'الحساسية' },
  layer: { en: 'Layer', ar: 'الطبقة' },
  incomingDrivers: { en: 'Incoming Drivers', ar: 'المحركات الواردة' },
  outgoingTargets: { en: 'Outgoing Targets', ar: 'الأهداف الصادرة' },
  timeline: { en: 'Timeline', ar: 'الجدول الزمني' },
  iteration: { en: 'Iteration', ar: 'التكرار' },
  energy: { en: 'Energy', ar: 'الطاقة' },
  decay: { en: 'Decay', ar: 'الاضمحلال' },
  depth: { en: 'Depth', ar: 'العمق' },
  probabilistic: { en: 'Risk Envelope', ar: 'نطاق المخاطر' },
  monteCarlo: { en: 'Monte Carlo', ar: 'مونتي كارلو' },
  p10: { en: 'P10 (Best)', ar: 'P10 (أفضل)' },
  p50: { en: 'P50 (Base)', ar: 'P50 (أساسي)' },
  p90: { en: 'P90 (Worst)', ar: 'P90 (أسوأ)' },
  runs: { en: 'runs', ar: 'تشغيل' },
  mean: { en: 'Mean', ar: 'المتوسط' },
  variance: { en: 'Variance', ar: 'التباين' },
  deterministic: { en: 'Deterministic', ar: 'حتمي' },
  probabilisticMode: { en: 'Probabilistic', ar: 'احتمالي' },
  mode: { en: 'Mode', ar: 'الوضع' },
  scenarioMeta: { en: 'Scenario Details', ar: 'تفاصيل السيناريو' },
  systemState: { en: 'System State', ar: 'حالة النظام' },
  nodes: { en: 'Nodes', ar: 'عقدة' },
  edges: { en: 'Edges', ar: 'رابط' },
  scenarios: { en: 'Scenarios', ar: 'سيناريوهات' },
  uncertaintyDrivers: { en: 'Uncertainty Drivers', ar: 'محركات عدم اليقين' },
  shippingLanes: { en: 'Shipping Lanes', ar: 'الممرات البحرية' },
  airCorridors: { en: 'Air Corridors', ar: 'الممرات الجوية' },
  hormuzLabel: { en: 'Strait of Hormuz', ar: 'مضيق هرمز' },
  live: { en: 'LIVE', ar: 'مباشر' },
  delta: { en: 'Change', ar: 'التغيير' },
  version: { en: 'v6.0', ar: 'v6.0' },
  causalBrief: { en: 'Causal Brief', ar: 'الموجز السببي' },
  lossExposure: { en: 'Loss Exposure', ar: 'التعرض للخسائر' },
  layerLegend: { en: 'Layer Legend', ar: 'دليل الطبقات' },
  confidenceMC: { en: 'Confidence (MC)', ar: 'الثقة (MC)' },
  bestCase: { en: 'Best Case', ar: 'أفضل حالة' },
  worstCase: { en: 'Worst Case', ar: 'أسوأ حالة' },
  sectorFinancials: { en: 'Sector Financial Formulas', ar: 'المعادلات المالية القطاعية' },
  gccRegion: { en: 'GCC REGION', ar: 'المنطقة' },
  corridors: { en: 'CORRIDORS', ar: 'الممرات' },
  hormuzStrait: { en: 'Hormuz Strait', ar: 'مضيق هرمز' },
  shippingCorr: { en: 'Shipping Lanes', ar: 'الممرات البحرية' },
  airCorr: { en: 'Air Corridors', ar: 'الممرات الجوية' },
  resetView: { en: 'Reset View', ar: 'إعادة العرض' },
  hormuzEngine: { en: 'Hormuz Cascade Engine', ar: 'محرك سلسلة هرمز' },
  hormuzChain: { en: 'Hormuz → Oil → Shipping → Insurance → Aviation → Tourism → GDP', ar: 'هرمز ← النفط ← الشحن ← التأمين ← الطيران ← السياحة ← الناتج المحلي' },
  chainFormula: { en: 'Formula', ar: 'المعادلة' },
  chainNarrative: { en: 'Chain Narrative', ar: 'السرد السببي' },
  gdpExposure: { en: 'GDP Exposure', ar: 'التعرض للناتج المحلي' },
  aviationEngine: { en: 'Aviation Cascade Engine', ar: 'محرك سلسلة الطيران' },
  aviationChain: { en: 'Insurance → Fuel → Flight Cost → Demand → Airports → Tourism → GDP', ar: 'التأمين ← الوقود ← تكلفة الرحلات ← الطلب ← المطارات ← السياحة ← الناتج المحلي' },
  airportImpact: { en: 'Airport Throughput', ar: 'حركة المطارات' },
  scenarioEngine: { en: 'Scenario Formula Engine', ar: 'محرك المعادلات' },
  engineExposure: { en: 'Total Exposure', ar: 'إجمالي التعرض' },
  engineNarrative: { en: 'Causal Narrative', ar: 'السرد السببي' },
  engineMetrics: { en: 'Key Metrics', ar: 'المقاييس الرئيسية' },
}

const LAYER_LABELS: Record<string, { en: string; ar: string }> = {
  geography: { en: 'Geography', ar: 'الجغرافيا' },
  infrastructure: { en: 'Infrastructure', ar: 'البنية التحتية' },
  economy: { en: 'Economy', ar: 'الاقتصاد' },
  finance: { en: 'Finance', ar: 'المالية' },
  society: { en: 'Society', ar: 'المجتمع' },
}

/* ── Scientific Globe Modes ── */
const GLOBE_MODES: { id: string; label: string; labelAr: string; icon: string; filter: string }[] = [
  { id: 'normal',   label: 'Normal',   labelAr: 'عادي',           icon: '🌍', filter: 'none' },
  { id: 'crt',      label: 'CRT',      labelAr: 'شاشة CRT',      icon: '📺', filter: 'contrast(1.3) saturate(0.3) sepia(0.15) brightness(0.85)' },
  { id: 'eo',       label: 'EO',       labelAr: 'رصد كهروبصري',   icon: '🛰️', filter: 'contrast(1.5) saturate(0) brightness(1.2)' },
  { id: 'flir',     label: 'FLIR',     labelAr: 'حراري FLIR',    icon: '🔥', filter: 'contrast(1.4) saturate(0.2) hue-rotate(180deg) brightness(0.9)' },
  { id: 'nvg',      label: 'NVG',      labelAr: 'رؤية ليلية',     icon: '🌙', filter: 'contrast(1.2) saturate(0.5) hue-rotate(90deg) brightness(0.7)' },
  { id: 'weather',  label: 'Weather',  labelAr: 'طقس',            icon: '🌦️', filter: 'contrast(0.9) saturate(1.4) brightness(1.1)' },
  { id: 'shipping', label: 'Shipping', labelAr: 'ممرات بحرية',    icon: '🚢', filter: 'contrast(1.1) saturate(0.6) brightness(0.9) hue-rotate(200deg)' },
  { id: 'flights',  label: 'Flights',  labelAr: 'مسارات جوية',    icon: '✈️', filter: 'contrast(1.1) saturate(0.4) brightness(0.95) hue-rotate(270deg)' },
  { id: 'satellite',label: 'Satellite',labelAr: 'قمر صناعي',      icon: '🛰️', filter: 'contrast(1.6) saturate(0.1) brightness(1.3) grayscale(0.3)' },
]

const PIPELINE = [
  { en: 'Parsing scenario input', ar: 'تحليل مدخلات السيناريو' },
  { en: 'Extracting entities', ar: 'استخراج الكيانات' },
  { en: 'Building relationship graph', ar: 'بناء رسم العلاقات' },
  { en: 'Running propagation engine', ar: 'تشغيل محرك الانتشار' },
  { en: 'Computing sector impacts', ar: 'حساب التأثيرات القطاعية' },
  { en: 'Running Monte Carlo inference', ar: 'تشغيل استدلال مونتي كارلو' },
  { en: 'Generating intelligence brief', ar: 'إنشاء الموجز الاستخباراتي' },
]

function ui(key: string, lang: Language): string {
  const entry = UI[key]
  return entry ? (lang === 'ar' ? entry.ar : entry.en) : key
}

function layerLabel(layer: string, lang: Language): string {
  const entry = LAYER_LABELS[layer]
  return entry ? (lang === 'ar' ? entry.ar : entry.en) : layer
}

/* ══════════════════════════════════════════════
   MONTE CARLO SIMULATION
   ══════════════════════════════════════════════ */
interface MonteCarloResult {
  meanLoss: number
  medianLoss: number
  p10Loss: number
  p50Loss: number
  p90Loss: number
  variance: number
  confidenceBand: [number, number]
  runs: number
  distribution: number[]
  confidenceMC: number        // C = 1 / (1 + variance)
  bestCase: number
  worstCase: number
}

function runMonteCarlo(
  nodes: typeof gccNodes,
  edges: typeof gccEdges,
  shocks: { nodeId: string; impact: number }[],
  severityMod: number,
  runs: number = 500,
  lang: 'ar' | 'en' = 'ar',
): MonteCarloResult {
  const losses: number[] = []

  for (let r = 0; r < runs; r++) {
    const sampledSeverity = severityMod * (0.8 + Math.random() * 0.4)
    const sampledShocks = shocks.map(s => ({
      ...s,
      impact: Math.max(-1, Math.min(1, s.impact * sampledSeverity * (0.85 + Math.random() * 0.3))),
    }))
    const sampledEdges = edges.map(e => ({
      ...e,
      weight: e.weight * (0.9 + Math.random() * 0.2),
    }))
    const result = runPropagation(nodes, sampledEdges, sampledShocks, 6, lang, 0.05)
    losses.push(result.totalLoss)
  }

  losses.sort((a: number, b: number) => a - b)
  const mean = losses.reduce((a, b) => a + b, 0) / losses.length
  const median = losses[Math.floor(losses.length / 2)]
  const p10 = losses[Math.floor(losses.length * 0.1)]
  const p50 = losses[Math.floor(losses.length * 0.5)]
  const p90 = losses[Math.floor(losses.length * 0.9)]
  const variance = losses.reduce((acc, v) => acc + (v - mean) ** 2, 0) / losses.length

  // C = 1 / (1 + variance) — normalized variance for confidence
  const normalizedVariance = variance / (mean * mean + 1)
  const confidenceMC = 1 / (1 + normalizedVariance)

  return {
    meanLoss: mean,
    medianLoss: median,
    p10Loss: p10,
    p50Loss: p50,
    p90Loss: p90,
    variance,
    confidenceBand: [p10, p90],
    runs,
    distribution: losses,
    confidenceMC,
    bestCase: losses[0],
    worstCase: losses[losses.length - 1],
  }
}

/* ══════════════════════════════════════════════
   GLOBE VIEW — Operational Geospatial Intelligence
   ══════════════════════════════════════════════ */
const SHIPPING_SCENARIOS = new Set(['hormuz_closure', 'jebel_ali_disruption', 'gcc_port_congestion', 'military_repositioning', 'insurance_repricing', 'food_security_shock'])
const AVIATION_SCENARIOS = new Set(['airspace_restriction', 'flight_rerouting', 'hajj_disruption'])

const COUNTRY_NODES: Record<string, { name: string; nameAr: string; nodeIds: string[] }> = {
  SA: { name: 'Saudi Arabia', nameAr: 'السعودية', nodeIds: ['geo_sa', 'inf_ruh', 'inf_jed', 'inf_dmm', 'inf_dammam', 'eco_oil', 'eco_aramco', 'soc_hajj', 'fin_tadawul', 'fin_sama', 'fin_banking', 'fin_insurers', 'inf_power', 'inf_desal', 'soc_citizens', 'soc_housing', 'soc_employment', 'soc_sentiment', 'soc_stability', 'eco_saudia', 'gov_transport', 'gov_water', 'gov_energy', 'gov_tourism', 'gov_finance'] },
  AE: { name: 'UAE', nameAr: 'الإمارات', nodeIds: ['geo_uae', 'inf_dxb', 'inf_auh', 'inf_jebel', 'inf_khalifa', 'eco_tourism', 'eco_aviation', 'eco_adnoc', 'eco_shipping', 'eco_logistics', 'eco_emirates', 'eco_av_stress', 'fin_uae_cb', 'fin_reinsure', 'fin_ins_risk', 'soc_travelers', 'soc_business', 'soc_media', 'soc_expats', 'soc_travel_d', 'soc_ticket', 'inf_airport_throughput'] },
  QA: { name: 'Qatar', nameAr: 'قطر', nodeIds: ['geo_qa', 'inf_doh', 'inf_doha_p', 'inf_hamad', 'eco_qatar_aw', 'fin_qa_cb', 'soc_food_d'] },
  KW: { name: 'Kuwait', nameAr: 'الكويت', nodeIds: ['geo_kw', 'inf_kwi', 'inf_shuwaikh', 'eco_kpc', 'eco_kw_airways', 'fin_kw_cb'] },
  BH: { name: 'Bahrain', nameAr: 'البحرين', nodeIds: ['geo_bh', 'inf_bah', 'eco_gulf_air', 'fin_bh_cb'] },
  OM: { name: 'Oman', nameAr: 'عُمان', nodeIds: ['geo_om', 'inf_mct', 'inf_sohar', 'eco_oman_air', 'fin_om_cb'] },
}

const SHIPPING_NODE_IDS = ['eco_shipping', 'eco_logistics', 'inf_jebel', 'inf_dammam', 'inf_doha_p', 'inf_hamad', 'inf_khalifa', 'inf_shuwaikh', 'inf_sohar']
const AVIATION_NODE_IDS = ['eco_aviation', 'eco_av_stress', 'eco_saudia', 'eco_emirates', 'eco_qatar_aw', 'eco_kw_airways', 'eco_gulf_air', 'eco_oman_air', 'inf_airport_throughput']

function GlobeView({
  propagation, selectedNode, onSelectNode, lang, timelineIteration, globeMode = 'normal',
  scientist, scenarioId,
}: {
  propagation: PropagationResult | null
  selectedNode: string | null
  onSelectNode: (id: string | null) => void
  lang: Language
  timelineIteration: number
  globeMode?: string
  scientist?: { energy: number; confidence: number; shockClass: string; shockClassAr: string; stage: string; stageAr: string } | null
  scenarioId?: string
}) {
  const globeRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dims, setDims] = useState({ w: 800, h: 600 })

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setDims({ w: Math.round(width), h: Math.round(height) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const activeImpacts = useMemo(() => {
    if (!propagation) return new Map<string, number>()
    if (propagation.iterationSnapshots && propagation.iterationSnapshots[timelineIteration]) {
      return propagation.iterationSnapshots[timelineIteration].impacts
    }
    return propagation.nodeImpacts
  }, [propagation, timelineIteration])

  // Normalized intensity: I_i = x_i / max_k |x_k|
  const maxImpact = useMemo(() => {
    let max = 0.001
    for (const val of activeImpacts.values()) {
      const abs = Math.abs(val)
      if (abs > max) max = abs
    }
    return max
  }, [activeImpacts])

  // Country-level aggregate impacts
  const countryImpacts = useMemo(() => {
    return Object.entries(COUNTRY_NODES).map(([code, country]) => {
      const impacts = country.nodeIds.map(id => Math.abs(activeImpacts.get(id) || 0))
      const active = impacts.filter(v => v > 0)
      const avg = active.length > 0 ? active.reduce((a, b) => a + b, 0) / active.length : 0
      return { code, name: country.name, nameAr: country.nameAr, avgImpact: avg, nodeCount: active.length }
    }).sort((a, b) => b.avgImpact - a.avgImpact)
  }, [activeImpacts])

  // Corridor impact computations
  const corridorImpacts = useMemo(() => {
    const hormuz = Math.abs(activeImpacts.get('geo_hormuz') || 0)
    const shippingVals = SHIPPING_NODE_IDS.map(id => Math.abs(activeImpacts.get(id) || 0)).filter(v => v > 0)
    const shippingAvg = shippingVals.length > 0 ? shippingVals.reduce((a, b) => a + b, 0) / shippingVals.length : 0
    const aviationVals = AVIATION_NODE_IDS.map(id => Math.abs(activeImpacts.get(id) || 0)).filter(v => v > 0)
    const aviationAvg = aviationVals.length > 0 ? aviationVals.reduce((a, b) => a + b, 0) / aviationVals.length : 0
    return { hormuz, shippingAvg, aviationAvg }
  }, [activeImpacts])

  const pointsData = useMemo(() => {
    return gccNodes.map(node => {
      const rawImpact = Math.abs(activeImpacts.get(node.id) || 0)
      const normalizedI = rawImpact / maxImpact  // I_i = x_i / max_k |x_k|
      const isPort = node.type === 'port' || node.id.includes('jebel') || node.id.includes('dammam') || node.id.includes('doha_p') || node.id.includes('hamad') || node.id.includes('khalifa') || node.id.includes('shuwaikh') || node.id.includes('sohar')
      const isAirport = node.type === 'airport' || node.id.includes('ruh') || node.id.includes('dxb') || node.id.includes('kwi') || node.id.includes('jed') || node.id.includes('auh') || node.id.includes('bah') || node.id.includes('mct') || (node.id.includes('doh') && !node.id.includes('doha_p'))
      const isChokepoint = node.id === 'geo_hormuz'
      return {
        id: node.id, lat: node.lat, lng: node.lng,
        label: lang === 'ar' ? (node.labelAr || node.label) : node.label,
        layer: node.layer,
        impact: rawImpact,
        normalizedI,
        color: isChokepoint ? '#ef4444' : (LAYER_COLORS[node.layer] || '#64748b'),
        size: isChokepoint ? 0.8 : (isPort || isAirport ? 0.5 + normalizedI * 1.2 : 0.3 + normalizedI * 1.5),
      }
    }).filter(Boolean)
  }, [activeImpacts, maxImpact, lang])

  const propagationArcs = useMemo(() => {
    if (!propagation) return []
    const arcs: any[] = []
    const filteredChain = propagation.propagationChain.filter(s => s.iteration <= timelineIteration)
    for (const step of filteredChain) {
      const fromNode = gccNodes.find(n => n.id === step.from)
      const toNode = gccNodes.find(n => n.id === step.to)
      if (!fromNode || !toNode) continue
      const isNegative = step.polarity < 0
      const flowStrength = Math.abs(step.impact) / maxImpact  // normalized propagation strength
      arcs.push({
        startLat: fromNode.lat, startLng: fromNode.lng,
        endLat: toNode.lat, endLng: toNode.lng,
        color: isNegative ? '#ef4444' : (LAYER_COLORS[fromNode?.layer || 'geography'] || '#22d3ee'),
        stroke: 0.5 + flowStrength * 2.5,
      })
    }
    return arcs
  }, [propagation, timelineIteration])

  const shippingArcs = useMemo(() => {
    return shippingRoutes.map(route => ({
      startLat: route.from.lat, startLng: route.from.lng,
      endLat: route.to.lat, endLng: route.to.lng,
      color: '#0ea5e9',
      stroke: 0.4,
    }))
  }, [])

  const aviationArcs = useMemo(() => {
    return aviationRoutes.map(route => ({
      startLat: route.from.lat, startLng: route.from.lng,
      endLat: route.to.lat, endLng: route.to.lng,
      color: '#a78bfa',
      stroke: 0.3,
    }))
  }, [])

  const allArcs = useMemo(() => {
    // Manual mode overrides
    if (globeMode === 'shipping') {
      const boostedShipping = shippingArcs.map(a => ({ ...a, stroke: a.stroke * 3, color: '#0ea5e9' }))
      return [...boostedShipping, ...propagationArcs]
    }
    if (globeMode === 'flights') {
      const boostedAviation = aviationArcs.map(a => ({ ...a, stroke: a.stroke * 3, color: '#a78bfa' }))
      return [...boostedAviation, ...propagationArcs]
    }
    // Auto-emphasis from scenario sector context (when in normal mode)
    if (globeMode === 'normal' && scenarioId) {
      if (SHIPPING_SCENARIOS.has(scenarioId)) {
        const autoShipping = shippingArcs.map(a => ({ ...a, stroke: a.stroke * 2.5, color: '#0ea5e9' }))
        return [...autoShipping, ...aviationArcs, ...propagationArcs]
      }
      if (AVIATION_SCENARIOS.has(scenarioId)) {
        const autoAviation = aviationArcs.map(a => ({ ...a, stroke: a.stroke * 2.5, color: '#a78bfa' }))
        return [...shippingArcs, ...autoAviation, ...propagationArcs]
      }
    }
    return [...shippingArcs, ...aviationArcs, ...propagationArcs]
  }, [shippingArcs, aviationArcs, propagationArcs, globeMode, scenarioId])

  // Heat rings: all nodes with impact > 15% get pulsing rings (heat layer)
  const ringsData = useMemo(() => {
    const rings: any[] = []
    for (const node of gccNodes) {
      const coord = nodeCoordinates[node.id]
      if (!coord) continue
      const impact = Math.abs(activeImpacts.get(node.id) || 0)
      const nI = impact / maxImpact
      if (nI < 0.15) continue
      const r = Math.min(255, Math.round(180 + nI * 75))
      const g = Math.max(0, Math.round(200 - nI * 180))
      const b = Math.round(30 - nI * 30)
      const a = Math.min(0.6, 0.15 + nI * 0.45)
      rings.push({
        lat: coord.lat, lng: coord.lng,
        maxR: 2 + nI * 6,
        propagationSpeed: 1 + nI * 3,
        repeatPeriod: 800 + (1 - nI) * 600,
        color: () => `rgba(${r},${g},${b},${a})`,
      })
    }
    return rings
  }, [activeImpacts, maxImpact])

  const pointLabelFn = useCallback((d: any) => {
    const impactPct = (d.impact * 100).toFixed(0)
    const layerName = layerLabel(d.layer, lang)
    return `<div style="color:${d.color};font-family:system-ui;font-size:12px;font-weight:600;direction:${lang === 'ar' ? 'rtl' : 'ltr'}">${d.label}<br/><span style="color:#94a3b8;font-size:10px">${layerName} · ${impactPct}%</span></div>`
  }, [lang])

  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.pointOfView({ lat: 25, lng: 51, altitude: 2.5 }, 1000)
    }
  }, [])

  const activeFilter = GLOBE_MODES.find(m => m.id === globeMode)?.filter || 'none'

  return (
    <div ref={containerRef} className="w-full h-full bg-[#06060a] rounded-xl overflow-hidden relative" style={{ filter: activeFilter }}>
      <GlobeGL
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-dark.jpg"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={pointsData}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointAltitude={(d: any) => d.impact * 0.05}
        pointRadius={(d: any) => d.size}
        pointLabel={pointLabelFn}
        onPointClick={(point: any) => {
          onSelectNode(point.id)
          if (globeRef.current) {
            globeRef.current.pointOfView({ lat: point.lat, lng: point.lng, altitude: 1.5 }, 800)
          }
        }}
        arcsData={allArcs}
        arcStartLat="startLat"
        arcStartLng="startLng"
        arcEndLat="endLat"
        arcEndLng="endLng"
        arcColor="color"
        arcStroke="stroke"
        arcDashLength={0.5}
        arcDashGap={0.3}
        arcDashAnimateTime={2000}
        ringsData={ringsData}
        ringLat="lat"
        ringLng="lng"
        ringMaxRadius="maxR"
        ringPropagationSpeed="propagationSpeed"
        ringRepeatPeriod="repeatPeriod"
        ringColor="color"
        atmosphereColor="#22d3ee"
        atmosphereAltitude={0.15}
        width={dims.w}
        height={dims.h}
        animateIn={true}
      />
      <div className="absolute bottom-3 start-3 bg-ds-surface/80 backdrop-blur-sm rounded-lg px-3 py-2 border border-ds-border text-[9px] font-mono space-y-1">
        <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-sky-500 inline-block rounded" /> {ui('shippingLanes', lang)}</div>
        <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-purple-400 inline-block rounded" /> {ui('airCorridors', lang)}</div>
        <div className="flex items-center gap-2"><span className="w-2 h-2 bg-red-500 rounded-full inline-block" /> {ui('hormuzLabel', lang)}</div>
      </div>
      {/* Scientist overlay on globe */}
      {scientist && (
        <div className="absolute top-3 end-3 bg-ds-surface/85 backdrop-blur-sm rounded-lg px-3 py-2 border border-ds-border text-[9px] font-mono space-y-1" style={{ direction: lang === 'ar' ? 'rtl' : 'ltr' }}>
          <div className="flex items-center gap-2">
            <span style={{ color: scientist.energy > 5 ? '#ef4444' : scientist.energy > 2 ? '#f59e0b' : '#22c55e' }} className="font-bold">E = {scientist.energy.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: scientist.confidence > 0.7 ? '#22c55e' : scientist.confidence > 0.4 ? '#f59e0b' : '#ef4444' }} className="font-bold">C = {(scientist.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: scientist.shockClass === 'critical' ? '#ef4444' : scientist.shockClass === 'severe' ? '#f59e0b' : '#22c55e' }} className="font-bold">
              {lang === 'ar' ? scientist.shockClassAr : scientist.shockClass}
            </span>
          </div>
          <div className="text-ds-text-dim text-[8px]">{lang === 'ar' ? scientist.stageAr : scientist.stage}</div>
        </div>
      )}
      {/* GCC Region Intelligence */}
      <div className="absolute top-3 start-3 bg-ds-surface/85 backdrop-blur-sm rounded-lg px-3 py-2 border border-ds-border text-[8px] font-mono space-y-0.5" style={{ direction: lang === 'ar' ? 'rtl' : 'ltr' }}>
        <div className="text-[9px] font-bold text-cyan-400 mb-1">{ui('gccRegion', lang)}</div>
        {countryImpacts.map(c => {
          const pct = (c.avgImpact * 100).toFixed(0)
          const pctNum = c.avgImpact * 100
          const color = pctNum > 30 ? '#ef4444' : pctNum > 15 ? '#f59e0b' : pctNum > 0 ? '#22c55e' : '#64748b'
          return (
            <div key={c.code} className="flex items-center justify-between gap-3">
              <span className="text-ds-text-dim">{lang === 'ar' ? c.nameAr : c.name}</span>
              <span style={{ color }} className="font-bold">{pctNum > 0 ? `${pct}%` : '—'}</span>
            </div>
          )
        })}
        <div className="border-t border-ds-border mt-1 pt-1">
          <div className="text-[9px] font-bold text-cyan-400 mb-1">{ui('corridors', lang)}</div>
          {(() => {
            const hPct = (corridorImpacts.hormuz * 100).toFixed(0)
            const hColor = corridorImpacts.hormuz * 100 > 30 ? '#ef4444' : corridorImpacts.hormuz * 100 > 15 ? '#f59e0b' : corridorImpacts.hormuz * 100 > 0 ? '#22c55e' : '#64748b'
            const sPct = (corridorImpacts.shippingAvg * 100).toFixed(0)
            const sColor = corridorImpacts.shippingAvg * 100 > 30 ? '#ef4444' : corridorImpacts.shippingAvg * 100 > 15 ? '#f59e0b' : corridorImpacts.shippingAvg * 100 > 0 ? '#22c55e' : '#64748b'
            const aPct = (corridorImpacts.aviationAvg * 100).toFixed(0)
            const aColor = corridorImpacts.aviationAvg * 100 > 30 ? '#ef4444' : corridorImpacts.aviationAvg * 100 > 15 ? '#f59e0b' : corridorImpacts.aviationAvg * 100 > 0 ? '#22c55e' : '#64748b'
            return (
              <>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-ds-text-dim">{ui('hormuzStrait', lang)}</span>
                  <span style={{ color: hColor }} className="font-bold">{corridorImpacts.hormuz > 0 ? `${hPct}%` : '—'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-ds-text-dim">{ui('shippingCorr', lang)}</span>
                  <span style={{ color: sColor }} className="font-bold">{corridorImpacts.shippingAvg > 0 ? `${sPct}%` : '—'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-ds-text-dim">{ui('airCorr', lang)}</span>
                  <span style={{ color: aColor }} className="font-bold">{corridorImpacts.aviationAvg > 0 ? `${aPct}%` : '—'}</span>
                </div>
              </>
            )
          })()}
        </div>
      </div>
      {/* Reset View button */}
      <button
        onClick={() => {
          if (globeRef.current) {
            globeRef.current.pointOfView({ lat: 25, lng: 51, altitude: 2.5 }, 800)
          }
        }}
        className="absolute bottom-3 end-3 bg-ds-surface/80 backdrop-blur-sm rounded-lg px-3 py-1.5 border border-ds-border text-[9px] font-mono text-ds-text-dim hover:text-cyan-400 hover:border-cyan-400/50 transition-colors cursor-pointer"
      >
        {ui('resetView', lang)}
      </button>
    </div>
  )
}

/* ══════════════════════════════════════════════
   SECTOR IMPACT BAR
   ══════════════════════════════════════════════ */
function SectorBar({ sector, avgImpact, color, lang }: { sector: string; avgImpact: number; color: string; lang: Language }) {
  const pct = Math.min(100, avgImpact * 100)
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-[11px] w-20 text-ds-text-muted truncate">{layerLabel(sector, lang)}</span>
      <div className="flex-1 h-3 bg-ds-bg-alt rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6 }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
      <span className="text-[11px] font-mono w-10 text-end" style={{ color }}>{pct.toFixed(0)}%</span>
    </div>
  )
}

/* ══════════════════════════════════════════════
   NODE DETAIL PANEL (click → explanation)
   ══════════════════════════════════════════════ */
function NodeDetailPanel({
  nodeExpl, lang, onClose,
}: {
  nodeExpl: NodeExplanation
  lang: Language
  onClose: () => void
}) {
  const impactPct = (Math.abs(nodeExpl.impact) * 100).toFixed(0)
  const layerColor = LAYER_COLORS[nodeExpl.layer] || '#64748b'
  const nodeLabel = lang === 'ar' ? nodeExpl.labelAr : nodeExpl.label
  const explanation = lang === 'ar' ? nodeExpl.explanationAr : nodeExpl.explanation

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="absolute top-2 end-2 w-72 bg-ds-surface/95 backdrop-blur-xl border border-ds-border rounded-xl p-3 z-50 shadow-2xl"
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-[11px] uppercase tracking-[0.15em] font-bold" style={{ color: layerColor }}>
          <Info size={10} className="inline me-1" />
          {ui('nodeDetail', lang)}
        </h4>
        <button onClick={onClose} className="text-ds-text-dim hover:text-ds-text transition-colors">
          <X size={14} />
        </button>
      </div>

      <div className="mb-2">
        <div className="text-[13px] font-bold text-ds-text">{nodeLabel}</div>
        <div className="text-[10px] text-ds-text-dim font-mono">
          {layerLabel(nodeExpl.layer, lang)} · {ui('impact', lang)}: <span style={{ color: layerColor }}>{impactPct}%</span> · {ui('sensitivityLabel', lang)}: {(gccNodes.find(n => n.id === nodeExpl.nodeId)?.sensitivity ?? 0) * 100}%
        </div>
      </div>

      <p className="text-[11px] text-ds-text-muted leading-relaxed mb-2 border-b border-ds-border pb-2">
        {explanation}
      </p>

      {nodeExpl.incomingEdges.length > 0 && (
        <div className="mb-2">
          <div className="text-[9px] uppercase tracking-wider text-ds-text-dim font-semibold mb-1">{ui('incomingDrivers', lang)}</div>
          {nodeExpl.incomingEdges.slice(0, 4).map((e, i) => (
            <div key={i} className="flex items-center justify-between text-[10px] px-1 py-0.5 bg-ds-bg-alt rounded mb-0.5">
              <span className="text-ds-text-muted truncate flex-1">{e.fromLabel}</span>
              <span className={`font-mono ms-2 ${e.polarity < 0 ? 'text-red-400' : 'text-cyan-400'}`}>
                {e.polarity < 0 ? '⊖' : '⊕'} {(e.contribution * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}

      {nodeExpl.outgoingEdges.length > 0 && (
        <div>
          <div className="text-[9px] uppercase tracking-wider text-ds-text-dim font-semibold mb-1">{ui('outgoingTargets', lang)}</div>
          {nodeExpl.outgoingEdges.slice(0, 4).map((e, i) => (
            <div key={i} className="flex items-center justify-between text-[10px] px-1 py-0.5 bg-ds-bg-alt rounded mb-0.5">
              <span className="text-ds-text-muted truncate flex-1">{e.toLabel}</span>
              <span className={`font-mono ms-2 ${e.polarity < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {e.polarity < 0 ? '⊖' : '⊕'} w={e.weight.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  )
}

/* ══════════════════════════════════════════════
   TIMELINE NAVIGATION — Bottom Bar
   ══════════════════════════════════════════════ */
function TimelineBar({
  propagation, currentIteration, onIterationChange, lang,
}: {
  propagation: PropagationResult
  currentIteration: number
  onIterationChange: (iter: number) => void
  lang: Language
}) {
  const maxIter = propagation.iterationSnapshots.length - 1
  const snap = propagation.iterationSnapshots[currentIteration]

  return (
    <div className="flex items-center gap-2 px-4 py-1.5 bg-ds-surface/80 border-t border-ds-border">
      <button
        onClick={() => onIterationChange(Math.max(0, currentIteration - 1))}
        disabled={currentIteration === 0}
        className="text-ds-text-dim hover:text-ds-text disabled:opacity-30 transition-colors"
      >
        <ChevronLeft size={14} />
      </button>

      <div className="flex-1 flex items-center gap-1">
        {propagation.iterationSnapshots.map((s, i) => (
          <button
            key={i}
            onClick={() => onIterationChange(i)}
            className={`flex-1 h-2 rounded-full transition-all ${
              i <= currentIteration ? 'bg-cyan-500' : 'bg-ds-bg-alt'
            } ${i === currentIteration ? 'ring-1 ring-cyan-400 ring-offset-1 ring-offset-ds-bg' : ''}`}
            title={`${ui('iteration', lang)} ${i}`}
          />
        ))}
      </div>

      <button
        onClick={() => onIterationChange(Math.min(maxIter, currentIteration + 1))}
        disabled={currentIteration === maxIter}
        className="text-ds-text-dim hover:text-ds-text disabled:opacity-30 transition-colors"
      >
        <ChevronRight size={14} />
      </button>

      <div className="flex items-center gap-3 ms-2 text-[10px] font-mono text-ds-text-dim">
        <span>{ui('iteration', lang)}: <span className="text-cyan-400">{currentIteration}/{maxIter}</span></span>
        <span>{ui('energy', lang)}: <span className="text-amber-400">{snap?.energy.toFixed(3)}</span></span>
        <span>{ui('delta', lang)}: <span className={snap?.deltaEnergy >= 0 ? 'text-red-400' : 'text-emerald-400'}>{snap?.deltaEnergy >= 0 ? '+' : ''}{snap?.deltaEnergy.toFixed(4)}</span></span>
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════
   SYNTHETIC SOCIETY PANEL
   ══════════════════════════════════════════════ */
const SOCIETY_CLUSTERS = [
  { key: 'population', nodes: ['soc_citizens', 'soc_expats', 'soc_travelers', 'soc_hajj'], en: 'Population Stress', ar: 'ضغط السكان' },
  { key: 'business', nodes: ['soc_business', 'soc_employment', 'soc_housing'], en: 'Business Climate', ar: 'مناخ الأعمال' },
  { key: 'media', nodes: ['soc_media', 'soc_social', 'soc_sentiment'], en: 'Media Amplification', ar: 'تضخيم إعلامي' },
  { key: 'consumer', nodes: ['soc_travel_d', 'soc_food_d', 'soc_ticket'], en: 'Consumer Demand', ar: 'طلب المستهلك' },
  { key: 'stability', nodes: ['soc_stability'], en: 'Public Stability', ar: 'الاستقرار العام' },
] as const

function SyntheticSocietyPanel({ impacts, lang }: { impacts: Map<string, number>; lang: Language }) {
  const clusters = SOCIETY_CLUSTERS.map(c => {
    const values = c.nodes.map(id => Math.abs(impacts.get(id) || 0))
    const avg = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0
    return { ...c, impact: avg }
  })

  // Weighted average: stability gets 2x weight (5 clusters, stability doubled = 6 total weight)
  const totalWeight = clusters.length + 1
  const riskIndex = clusters.reduce((sum, c) => sum + c.impact * (c.key === 'stability' ? 2 : 1), 0) / totalWeight

  const severityColor = (v: number) => v > 0.6 ? '#ef4444' : v > 0.3 ? '#f59e0b' : '#22c55e'
  const severityBg = (v: number) => v > 0.6 ? 'bg-red-500' : v > 0.3 ? 'bg-amber-500' : 'bg-emerald-500'

  const hasAnyImpact = clusters.some(c => c.impact > 0)
  if (!hasAnyImpact) return null

  return (
    <div className="bg-ds-surface rounded-xl border border-ds-border p-3">
      <div className="flex items-center gap-2 mb-2">
        <Users size={12} className="text-rose-400" />
        <span className="text-[10px] uppercase tracking-[0.15em] font-bold text-ds-text">{lang === 'ar' ? 'الطبقة الاجتماعية' : 'Synthetic Society'}</span>
      </div>

      {/* Society Risk Index */}
      <div className="bg-ds-bg-alt rounded px-2 py-1.5 mb-2">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-ds-text-dim">{lang === 'ar' ? 'مؤشر المخاطر الاجتماعية' : 'Society Risk Index'}</span>
          <span className="font-mono font-bold" style={{ color: severityColor(riskIndex) }}>
            {(riskIndex * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-ds-bg rounded-full h-1.5 mt-1">
          <div className={`h-1.5 rounded-full ${severityBg(riskIndex)} transition-all`} style={{ width: `${Math.min(riskIndex * 100, 100)}%` }} />
        </div>
      </div>

      {/* Cluster rows */}
      <div className="space-y-1.5">
        {clusters.map(c => (
          <div key={c.key} className="bg-ds-bg-alt rounded px-2 py-1">
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-ds-text-dim">{lang === 'ar' ? c.ar : c.en}</span>
              <div className="flex items-center gap-1">
                <span className="text-[8px]">{c.impact > 0 ? '↑' : '↓'}</span>
                <span className="font-mono font-bold" style={{ color: severityColor(c.impact) }}>
                  {(c.impact * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="w-full bg-ds-bg rounded-full h-1 mt-0.5">
              <div className={`h-1 rounded-full ${severityBg(c.impact)} transition-all`} style={{ width: `${Math.min(c.impact * 100, 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════
   MAIN COMMAND CENTER PAGE
   ══════════════════════════════════════════════ */
function DemoPageContent() {
  const [lang, setLang] = useState<Language>('ar')
  const searchParams = useSearchParams()
  const router = useRouter()
  const [scenarioId, setScenarioId] = useState<string>(searchParams.get('scenario') || '')
  const [isRunning, setIsRunning] = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [propagation, setPropagation] = useState<PropagationResult | null>(null)
  const [monteCarlo, setMonteCarlo] = useState<MonteCarloResult | null>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'graph' | 'globe'>('graph')
  const [severityMod, setSeverityMod] = useState(1.0)
  const [isMobile, setIsMobile] = useState(false)
  const [timelineIteration, setTimelineIteration] = useState(0)
  const [analysisMode, setAnalysisMode] = useState<'deterministic' | 'probabilistic'>('deterministic')
  const [globeMode, setGlobeMode] = useState<string>('normal')

  useEffect(() => {
    setLanguage(lang)
    if (typeof document !== 'undefined') {
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
      document.documentElement.lang = lang
    }
  }, [lang])

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 1024)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const scenario = useMemo(() => gccScenarios.find(s => s.id === scenarioId), [scenarioId])

  useEffect(() => {
    if (!isRunning) return
    const interval = setInterval(() => {
      setProcessingStep(prev => (prev < PIPELINE.length - 1 ? prev + 1 : prev))
    }, 400)
    return () => clearInterval(interval)
  }, [isRunning])

  useEffect(() => {
    if (processingStep === PIPELINE.length - 1 && isRunning) {
      const timeout = setTimeout(() => {
        if (scenario) {
          const modShocks = scenario.shocks.map(s => ({
            ...s, impact: Math.min(1, s.impact * severityMod),
          }))
          const result = runPropagation(gccNodes, gccEdges, modShocks, 6, lang, 0.05)
          setPropagation(result)
          setTimelineIteration(result.iterationSnapshots.length - 1)
          const mc = runMonteCarlo(gccNodes, gccEdges, modShocks, severityMod, 500, lang)
          setMonteCarlo(mc)
        }
        setIsRunning(false)
      }, 400)
      return () => clearTimeout(timeout)
    }
  }, [processingStep, isRunning, scenario, severityMod, lang])

  // Auto-set severity slider and analysis mode from scenario defaults
  useEffect(() => {
    if (scenario?.severityDefault !== undefined) {
      setSeverityMod(scenario.severityDefault)
    }
    if (scenario?.simulationType) {
      setAnalysisMode(scenario.simulationType === 'probabilistic' || scenario.simulationType === 'hybrid' ? 'probabilistic' : 'deterministic')
    }
  }, [scenario])

  const handleRun = useCallback(() => {
    if (!scenario) return
    setIsRunning(true)
    setProcessingStep(0)
    setPropagation(null)
    setMonteCarlo(null)
    setSelectedNode(null)
    setTimelineIteration(0)
  }, [scenario])

  const handleReset = useCallback(() => {
    setPropagation(null)
    setMonteCarlo(null)
    setIsRunning(false)
    setProcessingStep(0)
    setSelectedNode(null)
    setTimelineIteration(0)
  }, [])

  const activeImpacts = useMemo(() => {
    if (!propagation) return new Map<string, number>()
    if (propagation.iterationSnapshots && propagation.iterationSnapshots[timelineIteration]) {
      return propagation.iterationSnapshots[timelineIteration].impacts
    }
    return propagation.nodeImpacts
  }, [propagation, timelineIteration])

  // Pre-compute layer-stratified positions: nodes grouped by layer band, spread horizontally
  // Sub-row logic: layers with >10 nodes split into 2 staggered rows (±20px y offset)
  const layerNodePositions = useMemo(() => {
    const layerIndices = new Map<string, number>()
    const layerCounts = new Map<string, number>()
    for (const n of gccNodes) {
      const count = layerCounts.get(n.layer) || 0
      layerIndices.set(n.id, count)
      layerCounts.set(n.layer, count + 1)
    }
    const positions = new Map<string, { x: number; y: number }>()
    const canvasW = 850
    for (const n of gccNodes) {
      const meta = layerMeta[n.layer]
      const total = layerCounts.get(n.layer) || 1
      const idx = layerIndices.get(n.id) || 0

      if (total > 10) {
        // Split into 2 sub-rows: even indices on row 0 (up), odd on row 1 (down)
        const subRow = idx % 2
        const subIdx = Math.floor(idx / 2)
        const subTotal = Math.ceil(total / 2)
        const spacing = canvasW / (subTotal + 1)
        const yOffset = subRow === 0 ? -20 : 20
        positions.set(n.id, { x: spacing * (subIdx + 1), y: meta.yBase + yOffset })
      } else {
        const spacing = canvasW / (total + 1)
        positions.set(n.id, { x: spacing * (idx + 1), y: meta.yBase })
      }
    }
    return positions
  }, [])

  // Normalized intensity for graph: I_i = |x_i| / max_k |x_k|
  const maxGraphImpact = useMemo(() => {
    let max = 0.001
    for (const val of activeImpacts.values()) {
      const abs = Math.abs(val)
      if (abs > max) max = abs
    }
    return max
  }, [activeImpacts])

  // ═══ DOMINANT CHAIN DETECTION ═══
  // Identify the strongest propagation path: nodes + edges on the primary cascade
  // Filtered by timelineIteration for temporal accuracy
  const dominantChainSet = useMemo(() => {
    const nodeSet = new Set<string>()
    const edgeSet = new Set<string>()
    const edgeKeySet = new Set<string>()
    if (!propagation || propagation.propagationChain.length === 0) return { nodeSet, edgeSet, edgeKeySet, rootId: '' }
    // Filter chain by current timeline position
    const filteredChain = propagation.propagationChain.filter(s => s.iteration <= timelineIteration)
    if (filteredChain.length === 0) return { nodeSet, edgeSet, edgeKeySet, rootId: '' }
    // Root = the `from` of the first step in the filtered chain (initial shock node)
    const rootId = filteredChain[0].from
    nodeSet.add(rootId)
    // Walk the propagation chain: pick edges with strongest cumulative impact
    const chainSteps = filteredChain
      .filter(s => Math.abs(s.impact) / maxGraphImpact > 0.1)
      .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
    for (const step of chainSteps.slice(0, 12)) {
      nodeSet.add(step.from)
      nodeSet.add(step.to)
      edgeKeySet.add(`${step.from}->${step.to}`)
      // Find matching edge
      const edge = gccEdges.find(e => e.source === step.from && e.target === step.to)
      if (edge) edgeSet.add(edge.id)
    }
    return { nodeSet, edgeSet, edgeKeySet, rootId }
  }, [propagation, maxGraphImpact, timelineIteration])

  const graphNodes = useMemo(() => {
    return gccNodes.map(n => {
      const rawImpact = Math.abs(activeImpacts.get(n.id) || 0)
      const normalizedI = rawImpact / maxGraphImpact
      const nodeLabel = lang === 'ar' ? (n.labelAr || n.label) : n.label
      const pos = layerNodePositions.get(n.id) || { x: 400, y: 300 }
      const isOnDominantChain = dominantChainSet.nodeSet.has(n.id)
      const isRoot = n.id === dominantChainSet.rootId
      const layerColor = LAYER_COLORS[n.layer] || '#64748b'

      // Visual hierarchy: root cause > chain nodes > off-chain impacted > off-chain dim
      let effectiveOpacity: number
      let border: string
      let boxShadow: string
      let weightBoost = 0

      if (isRoot) {
        // Root cause node: extra large glow, white+gold border, weight boosted
        effectiveOpacity = 1
        border = '2px solid #fbbf24'
        boxShadow = `0 0 20px ${layerColor}90, 0 0 40px ${layerColor}40, 0 0 8px #fbbf2460`
        weightBoost = 0.3
      } else if (isOnDominantChain) {
        // Chain nodes: brighter border at full opacity, slightly larger weight
        effectiveOpacity = 1
        border = `2px solid ${selectedNode === n.id ? '#fff' : layerColor}`
        boxShadow = `0 0 ${Math.max(normalizedI * 30, 10)}px ${layerColor}60`
        weightBoost = 0.15
      } else if (normalizedI > 0.05) {
        // Non-chain with impact > 0.05: keep styling but reduce opacity
        effectiveOpacity = 0.5
        border = `2px solid ${selectedNode === n.id ? '#fff' : layerColor + '80'}`
        boxShadow = normalizedI > 0.2 ? `0 0 ${normalizedI * 15}px ${layerColor}25` : 'none'
      } else {
        // Non-chain with impact <= 0.05: dim, gray border, minimal glow
        effectiveOpacity = 0.25
        border = `2px solid ${selectedNode === n.id ? '#fff' : '#334155'}`
        boxShadow = 'none'
      }

      return {
        id: n.id, type: 'default',
        position: { x: pos.x, y: pos.y },
        data: { label: nodeLabel, type: n.layer, weight: Math.min(normalizedI + weightBoost, 1) },
        style: {
          background: (isOnDominantChain || isRoot || normalizedI > 0.05) ? layerColor : '#1e293b',
          color: '#e2e8f0',
          border,
          borderRadius: isRoot ? '12px' : '8px',
          padding: isRoot ? '8px 12px' : '6px 10px',
          fontSize: isRoot ? '12px' : '11px',
          fontWeight: (isOnDominantChain || isRoot || normalizedI > 0.15) ? '700' : '400',
          opacity: effectiveOpacity,
          boxShadow,
          cursor: 'pointer',
        },
      }
    })
  }, [activeImpacts, maxGraphImpact, selectedNode, lang, dominantChainSet])

  const graphEdges = useMemo(() => {
    return gccEdges.map(e => {
      const sourceImpact = Math.abs(activeImpacts.get(e.source) || 0)
      const normalizedSrc = sourceImpact / maxGraphImpact
      const strength = e.weight * normalizedSrc
      const edgeKey = `${e.source}->${e.target}`
      const isChainEdge = dominantChainSet.edgeKeySet.has(edgeKey)
      const edgeLabel = (strength > 0.05 || isChainEdge) ? (lang === 'ar' ? (e.labelAr || e.label) : e.label) : undefined
      const isNegativePolarity = e.polarity < 0

      if (isChainEdge) {
        // Chain edges: boosted stroke, full opacity, bright color, animated dash
        return {
          id: e.id, source: e.source, target: e.target,
          label: edgeLabel,
          animated: true,
          style: {
            stroke: isNegativePolarity ? '#ef4444' : '#22d3ee',
            strokeWidth: 2 + strength * 6,
            opacity: 1,
            strokeDasharray: '8 4',
          },
        }
      } else if (strength > 0.1) {
        // Non-chain with strength > 0.1: keep but reduce opacity, no animation
        return {
          id: e.id, source: e.source, target: e.target,
          label: edgeLabel,
          animated: false,
          style: {
            stroke: isNegativePolarity ? '#ef444480' : '#22d3ee60',
            strokeWidth: 1 + strength * 3,
            opacity: 0.3,
            strokeDasharray: 'none',
          },
        }
      } else {
        // Non-chain with strength <= 0.1: very dim, no animation
        return {
          id: e.id, source: e.source, target: e.target,
          label: undefined,
          animated: false,
          style: {
            stroke: '#1e293b',
            strokeWidth: 0.5 + strength * 2,
            opacity: 0.1,
            strokeDasharray: 'none',
          },
        }
      }
    })
  }, [activeImpacts, maxGraphImpact, lang, dominantChainSet])

  const selectedNodeExpl = useMemo(() => {
    if (!selectedNode || !propagation) return null
    return propagation.nodeExplanations.get(selectedNode) || null
  }, [selectedNode, propagation])

  const simStatus = isRunning ? 'running' : propagation ? 'complete' : scenario ? 'ready' : 'awaiting'
  const statusColor = { awaiting: '#f59e0b', running: '#3b82f6', complete: '#10b981', ready: '#64748b' }[simStatus]
  const statusText = ui(simStatus === 'awaiting' ? 'awaitingInput' : simStatus, lang)

  const chains = useMemo(() => {
    if (!propagation) return []
    return formatPropagationChain(propagation.propagationChain)
  }, [propagation])

  const sectorFinancials = useMemo(() => {
    if (!propagation) return null
    return computeSectorFinancials(propagation.nodeImpacts)
  }, [propagation])

  // ═══ UNIFIED ENGINE RUNTIME ═══
  // Engine reads propagation nodeImpacts + severity → produces ScenarioEngineResult
  // This single output drives: engine panel, formula chain, key metrics, narrative
  const engineMeta = useMemo<ScenarioEngine | null>(() => {
    if (!scenario) return null
    const eid = scenario.engineId || scenario.id
    return getScenarioEngine(eid)
  }, [scenario])

  const engineResult = useMemo<ScenarioEngineResult | null>(() => {
    if (!propagation || !engineMeta) return null
    return engineMeta.compute(propagation.nodeImpacts, severityMod)
  }, [propagation, engineMeta, severityMod])

  // ═══ SCIENTIST LAYER ═══
  // Computed from unified propagation state — drives scientist overlay
  const scientist = useMemo(() => {
    if (!propagation) return null
    const energy = propagation.systemEnergy
    const confidence = propagation.confidence
    const uncertainty = 1 - confidence
    const dominantSector = propagation.affectedSectors.length > 0
      ? propagation.affectedSectors.reduce((a, b) => a.avgImpact > b.avgImpact ? a : b)
      : null
    const geoNodes = gccNodes.filter(n => n.layer === 'geography')
    const regionalStress = geoNodes.length > 0
      ? geoNodes.reduce((sum, n) => sum + Math.abs(propagation.nodeImpacts.get(n.id) || 0), 0) / geoNodes.length
      : 0
    const stage = propagation.propagationDepth <= 2 ? 'initial' : propagation.propagationDepth <= 4 ? 'cascading' : 'saturated'
    const shockClass = severityMod >= 0.8 ? 'critical' : severityMod >= 0.5 ? 'severe' : severityMod >= 0.3 ? 'moderate' : 'low'
    return {
      energy, confidence, uncertainty,
      dominantSector,
      regionalStress,
      stage: stage as 'initial' | 'cascading' | 'saturated',
      stageAr: stage === 'initial' ? 'أولي' : stage === 'cascading' ? 'متسلسل' : 'مشبع',
      timeHorizon: scenario?.timeHorizon || '—',
      timeHorizonAr: scenario?.timeHorizonAr || '—',
      shockClass: shockClass as 'critical' | 'severe' | 'moderate' | 'low',
      shockClassAr: shockClass === 'critical' ? 'حرج' : shockClass === 'severe' ? 'شديد' : shockClass === 'moderate' ? 'متوسط' : 'منخفض',
      propagationDepth: propagation.propagationDepth,
      totalExposure: engineResult?.totalExposure ?? propagation.totalLoss,
    }
  }, [propagation, scenario, severityMod, engineResult])

  if (isMobile) {
    return (
      <div className="h-screen w-full bg-ds-bg flex items-center justify-center p-6" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
        <div className="ds-card p-10 text-center max-w-md">
          <GlobeIcon className="w-10 h-10 text-ds-text-muted mx-auto mb-4" />
          <h2 className="text-lg font-bold mb-2">{ui('desktop', lang)}</h2>
          <p className="text-sm text-ds-text-muted mb-6">{ui('desktopMsg', lang)}</p>
          <Link href="/" className="ds-btn-primary"><ArrowLeft className="w-4 h-4" /> {ui('back', lang)}</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen w-full bg-ds-bg flex flex-col overflow-hidden" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      {/* ═══ TOP BAR — Command Center Header ═══ */}
      <div className="h-11 border-b border-ds-border bg-ds-surface/80 backdrop-blur-xl flex-shrink-0 flex items-center justify-between px-5">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-ds-text-muted hover:text-ds-text transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
          </Link>
          <div className="w-px h-5 bg-ds-border" />
          <span className="text-[11px] font-semibold text-ds-text tracking-tight">{ui('title', lang)}</span>
          <span className="text-[11px] text-ds-text-dim font-mono">/</span>
          <span className="text-[11px] text-ds-text-muted font-mono">{ui('controlRoom', lang)}</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: statusColor }} />
            <span className="text-[10px] font-mono uppercase tracking-[0.15em]" style={{ color: statusColor }}>{statusText}</span>
          </div>
          {propagation && (
            <>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('systemEnergy', lang)}: <span className="text-amber-400">{propagation.systemEnergy.toFixed(3)}</span></span>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('confidence', lang)}: <span className="text-emerald-400">{((analysisMode === 'probabilistic' && monteCarlo ? (1 / (1 + monteCarlo.variance)) : propagation.confidence) * 100).toFixed(0)}%</span></span>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('spread', lang)}: <span className="text-cyan-400">{lang === 'ar' ? propagation.spreadLevelAr : propagation.spreadLevel}</span></span>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('depth', lang)}: <span className="text-purple-400">{propagation.propagationDepth}</span></span>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('totalLoss', lang)}: <span className="text-red-400">${propagation.totalLoss.toFixed(1)}B</span></span>
              {monteCarlo && (
                <>
                  <span className="text-[10px] text-ds-text-dim">|</span>
                  <span className="text-[10px] font-mono text-amber-400">[P10: ${monteCarlo.p10Loss.toFixed(1)}B — P90: ${monteCarlo.p90Loss.toFixed(1)}B]</span>
                </>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-md border border-ds-border overflow-hidden">
            <button
              onClick={() => setAnalysisMode('deterministic')}
              className={`px-2 py-1 text-[10px] font-semibold transition-colors ${analysisMode === 'deterministic' ? 'bg-cyan-500 text-ds-bg' : 'bg-ds-card text-ds-text-dim hover:text-ds-text'}`}
            >
              {ui('deterministic', lang)}
            </button>
            <button
              onClick={() => setAnalysisMode('probabilistic')}
              className={`px-2 py-1 text-[10px] font-semibold transition-colors ${analysisMode === 'probabilistic' ? 'bg-rose-500 text-white' : 'bg-ds-card text-ds-text-dim hover:text-ds-text'}`}
            >
              {ui('probabilisticMode', lang)}
            </button>
          </div>
          <button
            onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-ds-card border border-ds-border hover:border-ds-border-hover transition-colors text-[11px] font-semibold text-ds-text"
          >
            <Languages className="w-3 h-3" />
            {lang === 'ar' ? 'EN' : 'عربي'}
          </button>
        </div>
      </div>

      {/* ═══ MAIN 3-COLUMN LAYOUT ═══ */}
      <div className="flex-1 flex overflow-hidden">

        {/* ═══ LEFT RAIL — Intelligence ═══ */}
        <div className="w-[310px] bg-ds-surface border-e border-ds-border overflow-y-auto flex-shrink-0">
          <div className="p-3 space-y-3">

            {/* Causal Brief — HERO */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-cyan-400 font-bold mb-2 flex items-center gap-2">
                <FileText size={12} /> {ui('causalBrief', lang)}
              </h3>
              {propagation ? (
                <p className="text-[12px] text-ds-text-muted leading-relaxed">{propagation.explanation}</p>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
              )}
            </div>

            {/* ═══ SCENARIO FORMULA ENGINE — UNIVERSAL (replaced by Engine Intelligence Panel below) ═══ */}

            {/* Loss Exposure — Deterministic + Probabilistic */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-red-400 font-bold mb-2 flex items-center gap-2">
                <TrendingUp size={12} /> {ui('lossExposure', lang)}
              </h3>
              {propagation ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-ds-text-dim">{ui('deterministic', lang)}</span>
                    <span className="font-mono text-red-400 font-semibold">${propagation.totalLoss.toFixed(1)}B</span>
                  </div>
                  {monteCarlo && (
                    <>
                      <div className="border-t border-ds-border pt-1">
                        <div className="text-[10px] text-ds-text-dim font-mono mb-1">{ui('monteCarlo', lang)}: {monteCarlo.runs} {ui('runs', lang)}</div>
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-emerald-400">{ui('p10', lang)}</span>
                        <span className="font-mono text-ds-text">${monteCarlo.p10Loss.toFixed(1)}B</span>
                      </div>
                      <div className="relative h-3 bg-ds-bg-alt rounded-full overflow-hidden">
                        <div className="absolute h-full bg-emerald-500/30 rounded-full" style={{ left: `${(monteCarlo.p10Loss / monteCarlo.p90Loss) * 100 * 0.5}%`, right: `${100 - (monteCarlo.p90Loss / monteCarlo.p90Loss) * 100 * 0.9}%` }} />
                        <div className="absolute h-full w-0.5 bg-amber-400" style={{ left: `${(monteCarlo.p50Loss / monteCarlo.p90Loss) * 90}%` }} />
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-amber-400">{ui('p50', lang)}</span>
                        <span className="font-mono text-ds-text">${monteCarlo.p50Loss.toFixed(1)}B</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-red-400">{ui('p90', lang)}</span>
                        <span className="font-mono text-ds-text">${monteCarlo.p90Loss.toFixed(1)}B</span>
                      </div>
                      <div className="border-t border-ds-border pt-1 mt-1">
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-ds-text-dim">{ui('mean', lang)}</span>
                          <span className="font-mono text-ds-text-muted">${monteCarlo.meanLoss.toFixed(2)}B</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-ds-text-dim">{ui('variance', lang)}</span>
                          <span className="font-mono text-ds-text-muted">{monteCarlo.variance.toFixed(3)}</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-ds-text-dim">{ui('confidenceMC', lang)}</span>
                          <span className="font-mono text-emerald-400">{(monteCarlo.confidenceMC * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-ds-text-dim">{ui('bestCase', lang)}</span>
                          <span className="font-mono text-emerald-400">${monteCarlo.bestCase.toFixed(1)}B</span>
                        </div>
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-ds-text-dim">{ui('worstCase', lang)}</span>
                          <span className="font-mono text-red-400">${monteCarlo.worstCase.toFixed(1)}B</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
              )}
            </div>

            {/* Top Drivers */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-amber-400 font-bold mb-2 flex items-center gap-2">
                <BarChart3 size={12} /> {ui('topDrivers', lang)}
              </h3>
              {propagation ? (
                <div className="space-y-2">
                  {propagation.topDrivers.slice(0, 8).map((driver, i) => (
                    <div key={driver.nodeId} className="flex items-center gap-2 cursor-pointer hover:bg-ds-bg-alt rounded px-1 py-0.5 transition-colors" onClick={() => setSelectedNode(driver.nodeId)}>
                      <span className="text-[10px] text-ds-text-dim w-4 text-center">{i + 1}</span>
                      <div className="flex-1">
                        <div className="text-[11px] text-ds-text font-medium">{driver.label}</div>
                        <div className="h-2 bg-ds-bg-alt rounded-full mt-0.5">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${driver.impact * 100}%`, backgroundColor: LAYER_COLORS[driver.layer] }} />
                        </div>
                      </div>
                      <span className="text-[10px] font-mono font-semibold" style={{ color: LAYER_COLORS[driver.layer] }}>{(driver.impact * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
              )}
            </div>

            {/* Impact Chain */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-cyan-400 font-bold mb-2 flex items-center gap-2">
                <List size={12} /> {ui('impactChain', lang)}
              </h3>
              {propagation && chains.length > 0 ? (
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {chains.slice(0, 10).map((chain, i) => (
                    <div key={i} className="text-[11px] font-mono text-ds-text-muted px-2 py-1 bg-ds-bg-alt rounded">{chain}</div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
              )}
            </div>

            {/* Sector Impact */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-emerald-400 font-bold mb-2 flex items-center gap-2">
                <Activity size={12} /> {ui('sectorImpact', lang)}
              </h3>
              {propagation ? (
                <div>{propagation.affectedSectors.map(s => <SectorBar key={s.sector} sector={s.sector} avgImpact={s.avgImpact} color={s.color} lang={lang} />)}</div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
              )}
            </div>

            {/* Sector Financial Formulas — Oil + Hormuz Core Chain */}
            {propagation && sectorFinancials && (
              <div className="ds-card rounded-xl p-3">
                <h3 className="text-[10px] uppercase tracking-[0.15em] text-blue-400 font-bold mb-2 flex items-center gap-2">
                  <TrendingUp size={12} /> {ui('sectorFinancials', lang)}
                </h3>
                <div className="space-y-1 text-[11px]">
                  {Object.values(sectorFinancials).map((metric) => {
                    const label = lang === 'ar' ? metric.labelAr : metric.label
                    const isIndex = metric.unit === 'index'
                    const isPct = metric.unit === '%'
                    const isUp = metric.direction === 'up'
                    let barPct: number
                    let barColor: string
                    if (isIndex) {
                      barPct = Math.min(100, metric.value * 100)
                      barColor = metric.value > 0.3 ? '#ef4444' : metric.value > 0.1 ? '#f59e0b' : '#22c55e'
                    } else if (isPct) {
                      barPct = metric.value * 100
                      barColor = metric.value < 0.7 ? '#ef4444' : metric.value < 0.9 ? '#f59e0b' : '#22c55e'
                    } else if (isUp && metric.base > 0) {
                      const increase = (metric.value - metric.base) / metric.base
                      barPct = Math.min(100, increase * 100 + 50)
                      barColor = increase > 0.3 ? '#ef4444' : increase > 0.1 ? '#f59e0b' : '#22c55e'
                    } else if (metric.base > 0) {
                      const remaining = metric.value / metric.base
                      barPct = remaining * 100
                      barColor = remaining < 0.5 ? '#ef4444' : remaining < 0.8 ? '#f59e0b' : '#22c55e'
                    } else {
                      barPct = 50
                      barColor = '#64748b'
                    }
                    const arrow = isUp ? '↑' : '↓'
                    const displayVal = isIndex
                      ? (metric.value * 100).toFixed(0) + '%'
                      : isPct
                        ? (metric.value * 100).toFixed(0) + '%'
                        : metric.value.toFixed(1) + ' ' + metric.unit
                    return (
                      <div key={metric.label}>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px]" style={{ color: barColor }}>{arrow}</span>
                          <span className="w-28 text-ds-text-muted truncate text-[10px]">{label}</span>
                          <div className="flex-1 h-1.5 bg-ds-bg-alt rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all duration-500" style={{ width: `${barPct}%`, backgroundColor: barColor }} />
                          </div>
                          <span className="font-mono w-14 text-end text-[10px]" style={{ color: barColor }}>{displayVal}</span>
                        </div>
                        {metric.formula && <div className="text-[9px] font-mono text-ds-text-dim ps-4 -mt-0.5">{metric.formula}</div>}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* ═══ SCENARIO FORMULA ENGINE — UNIFIED ═══ */}
            {propagation && engineResult && engineMeta && (
              <div className="ds-card rounded-xl p-3 border border-cyan-500/20">
                <h3 className="text-[10px] uppercase tracking-[0.15em] text-cyan-400 font-bold mb-2 flex items-center gap-2">
                  <Zap size={12} /> {lang === 'ar' ? engineMeta.labelAr : engineMeta.label}
                </h3>
                <div className="text-[9px] font-mono text-ds-text-dim mb-2 leading-relaxed">
                  {lang === 'ar' ? engineMeta.chainLabelAr : engineMeta.chainLabel}
                </div>
                {/* Chain Steps — formula cascade */}
                <div className="space-y-1.5">
                  {engineResult.steps.map((step, i) => {
                    const dirColor = step.direction === '↑' ? '#ef4444' : step.direction === '↓' ? '#f59e0b' : '#64748b'
                    const label = lang === 'ar' ? step.labelAr : step.label
                    const formula = lang === 'ar' ? step.formulaAr : step.formula
                    return (
                      <div key={step.id} className="bg-ds-bg-alt rounded-lg px-2 py-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-bold" style={{ color: dirColor }}>{step.direction}</span>
                            <span className="text-[11px] text-ds-text font-medium">{label}</span>
                          </div>
                          <span className="text-[10px] font-mono font-bold" style={{ color: dirColor }}>
                            {step.impactPct > 0 ? (step.direction === '↑' ? '+' : '−') : ''}{Math.abs(step.impactPct).toFixed(0)}%
                          </span>
                        </div>
                        <div className="text-[9px] font-mono text-ds-text-dim mt-0.5">{formula}</div>
                        {i < engineResult.steps.length - 1 && (
                          <div className="text-center text-[8px] text-ds-text-dim mt-0.5">│</div>
                        )}
                      </div>
                    )
                  })}
                </div>
                {/* Key Metrics */}
                {engineResult.keyMetrics.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-ds-border">
                    <h4 className="text-[9px] text-cyan-400 font-bold mb-1.5">{ui('engineMetrics', lang)}</h4>
                    <div className="grid grid-cols-2 gap-1.5">
                      {engineResult.keyMetrics.map((m, i) => (
                        <div key={i} className="bg-ds-bg-alt rounded px-2 py-1">
                          <span className="text-[8px] text-ds-text-dim block">{lang === 'ar' ? m.labelAr : m.label}</span>
                          <span className="text-[11px] font-mono font-bold" style={{ color: m.color }}>{m.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* Total Exposure */}
                <div className="mt-2 pt-2 border-t border-ds-border">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-ds-text-dim font-semibold">{ui('engineExposure', lang)}</span>
                    <span className="font-mono text-red-400 font-bold">${engineResult.totalExposure.toFixed(1)}B</span>
                  </div>
                </div>
                {/* Bilingual Narrative */}
                <div className="mt-2 pt-2 border-t border-ds-border">
                  <p className="text-[10px] text-ds-text-muted leading-relaxed">
                    {lang === 'ar' ? engineResult.narrativeAr : engineResult.narrative}
                  </p>
                </div>
              </div>
            )}

            {/* ═══ SCIENTIST LAYER ═══ */}
            {scientist && (
              <div className="ds-card rounded-xl p-3 border border-emerald-500/20">
                <h3 className="text-[10px] uppercase tracking-[0.15em] text-emerald-400 font-bold mb-2 flex items-center gap-2">
                  <Target size={12} /> {lang === 'ar' ? 'الطبقة العلمية' : 'Scientist Layer'}
                </h3>
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  {/* System Energy */}
                  <div className="bg-ds-bg-alt rounded px-2 py-1.5">
                    <div className="text-[8px] text-ds-text-dim">{lang === 'ar' ? 'طاقة النظام' : 'System Energy'}</div>
                    <div className="text-[12px] font-mono font-bold text-amber-400">E = {scientist.energy.toFixed(3)}</div>
                    <div className="text-[8px] font-mono text-ds-text-dim">E_sys = Σx²</div>
                  </div>
                  {/* Confidence */}
                  <div className="bg-ds-bg-alt rounded px-2 py-1.5">
                    <div className="text-[8px] text-ds-text-dim">{lang === 'ar' ? 'الثقة' : 'Confidence'}</div>
                    <div className="text-[12px] font-mono font-bold" style={{ color: scientist.confidence > 0.7 ? '#22c55e' : scientist.confidence > 0.4 ? '#f59e0b' : '#ef4444' }}>C = {(scientist.confidence * 100).toFixed(0)}%</div>
                    <div className="text-[8px] font-mono text-ds-text-dim">C = 1/(1+σ²)</div>
                  </div>
                  {/* Uncertainty */}
                  <div className="bg-ds-bg-alt rounded px-2 py-1.5">
                    <div className="text-[8px] text-ds-text-dim">{lang === 'ar' ? 'عدم اليقين' : 'Uncertainty'}</div>
                    <div className="text-[12px] font-mono font-bold text-rose-400">U = {(scientist.uncertainty * 100).toFixed(0)}%</div>
                    <div className="text-[8px] font-mono text-ds-text-dim">U = 1 − C</div>
                  </div>
                  {/* Propagation Depth */}
                  <div className="bg-ds-bg-alt rounded px-2 py-1.5">
                    <div className="text-[8px] text-ds-text-dim">{lang === 'ar' ? 'عمق الانتشار' : 'Prop. Depth'}</div>
                    <div className="text-[12px] font-mono font-bold text-cyan-400">D = {scientist.propagationDepth}</div>
                    <div className="text-[8px] font-mono text-ds-text-dim">{lang === 'ar' ? scientist.stageAr : scientist.stage}</div>
                  </div>
                </div>
                {/* Dominant Sector Stress */}
                {scientist.dominantSector && (
                  <div className="mt-2 pt-2 border-t border-ds-border">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-ds-text-dim">{lang === 'ar' ? 'القطاع المهيمن' : 'Dominant Sector'}</span>
                      <span className="font-mono font-bold" style={{ color: scientist.dominantSector.color }}>{layerLabel(scientist.dominantSector.sector, lang)} · {(scientist.dominantSector.avgImpact * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                )}
                {/* Regional Stress + Shock + Horizon */}
                <div className="mt-2 pt-2 border-t border-ds-border space-y-1">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-ds-text-dim">{lang === 'ar' ? 'الضغط الإقليمي' : 'Regional Stress'}</span>
                    <span className="font-mono text-amber-400">{(scientist.regionalStress * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-ds-text-dim">{lang === 'ar' ? 'تصنيف الصدمة' : 'Shock Class'}</span>
                    <span className="font-mono" style={{ color: scientist.shockClass === 'critical' ? '#ef4444' : scientist.shockClass === 'severe' ? '#f59e0b' : '#22c55e' }}>{lang === 'ar' ? scientist.shockClassAr : scientist.shockClass}</span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-ds-text-dim">{lang === 'ar' ? 'الأفق الزمني' : 'Time Horizon'}</span>
                    <span className="font-mono text-ds-text-muted">{lang === 'ar' ? scientist.timeHorizonAr : scientist.timeHorizon}</span>
                  </div>
                  <div className="flex justify-between text-[10px]">
                    <span className="text-ds-text-dim">{lang === 'ar' ? 'إجمالي التعرض' : 'Total Exposure'}</span>
                    <span className="font-mono text-red-400 font-bold">${scientist.totalExposure.toFixed(1)}B</span>
                  </div>
                </div>
              </div>
            )}

            {/* ═══ SYNTHETIC SOCIETY LAYER ═══ */}
            <SyntheticSocietyPanel impacts={activeImpacts} lang={lang} />

            {/* Uncertainty Drivers — visible in probabilistic mode */}
            {analysisMode === 'probabilistic' && (
              <div className="ds-card rounded-xl p-3">
                <h3 className="text-[10px] uppercase tracking-[0.15em] text-rose-400 font-bold mb-2 flex items-center gap-2">
                  <AlertTriangle size={12} /> {ui('uncertaintyDrivers', lang)}
                </h3>
                {monteCarlo ? (
                  <div className="space-y-2 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-ds-text-dim">{ui('severity', lang)}</span>
                      <span className="font-mono text-amber-400">±20%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-ds-text-dim">{ui('shockNodes', lang)}</span>
                      <span className="font-mono text-amber-400">±15%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-ds-text-dim">{ui('edges', lang)}</span>
                      <span className="font-mono text-amber-400">±10%</span>
                    </div>
                    <div className="border-t border-ds-border pt-1">
                      <div className="flex justify-between">
                        <span className="text-ds-text-dim">{ui('variance', lang)}</span>
                        <span className="font-mono text-rose-400">{monteCarlo.variance.toFixed(4)}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
                )}
              </div>
            )}

            {/* Layer Legend */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-bold mb-2 flex items-center gap-2">
                <Target size={12} /> {ui('layerLegend', lang)}
              </h3>
              <div className="space-y-1">
                {Object.entries(LAYER_COLORS).map(([layer, color]) => (
                  <div key={layer} className="flex items-center gap-2 text-[11px]">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-ds-text-muted">{lang === 'ar' ? (LAYER_LABELS[layer]?.ar || layer) : (LAYER_LABELS[layer]?.en || layer)}</span>
                    <span className="ms-auto text-[10px] font-mono text-ds-text-dim">{gccNodes.filter(n => n.layer === layer).length}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ═══ CENTER — Graph / Globe Canvas ═══ */}
        <div className="flex-1 bg-ds-bg flex flex-col overflow-hidden">
          <div className="flex items-center gap-0 px-4 py-2 border-b border-ds-border bg-ds-surface/50">
            <button onClick={() => setViewMode('graph')} className={`px-4 py-1.5 text-[12px] font-semibold rounded-s-md border border-ds-border transition-colors ${viewMode === 'graph' ? 'bg-cyan-500 text-ds-bg border-cyan-500' : 'bg-ds-card text-ds-text-muted'}`}>
              <Network className="w-3 h-3 inline me-1" />{ui('graphView', lang)}
            </button>
            <button onClick={() => setViewMode('globe')} className={`px-4 py-1.5 text-[12px] font-semibold rounded-e-md border border-ds-border transition-colors ${viewMode === 'globe' ? 'bg-cyan-500 text-ds-bg border-cyan-500' : 'bg-ds-card text-ds-text-muted'}`}>
              <GlobeIcon className="w-3 h-3 inline me-1" />{ui('globeView', lang)}
            </button>
            {viewMode === 'globe' && (
              <div className="ms-3 flex items-center gap-1">
                {GLOBE_MODES.map(m => (
                  <button
                    key={m.id}
                    onClick={() => setGlobeMode(m.id as any)}
                    title={lang === 'ar' ? m.labelAr : m.label}
                    className={`px-2 py-1 text-[10px] rounded border transition-all ${
                      globeMode === m.id
                        ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-400'
                        : 'bg-ds-bg-alt border-ds-border text-ds-text-dim hover:border-ds-border-hover'
                    }`}
                  >
                    <span className="me-0.5">{m.icon}</span>
                    <span className="font-mono">{m.id === 'normal' ? (lang === 'ar' ? m.labelAr : m.label) : m.id.toUpperCase()}</span>
                  </button>
                ))}
              </div>
            )}
            {propagation && (
              <div className="ms-auto flex items-center gap-3 text-[10px] font-mono text-ds-text-dim">
                <span>{ui('totalLoss', lang)}: <span className="text-red-400 font-semibold">${propagation.totalLoss.toFixed(1)}B</span></span>
                {monteCarlo && analysisMode === 'probabilistic' && (
                  <span className="text-amber-400">[{ui('p10', lang)}: ${monteCarlo.p10Loss.toFixed(1)}B — {ui('p90', lang)}: ${monteCarlo.p90Loss.toFixed(1)}B]</span>
                )}
                <span>{ui('nodesAffected', lang)}: <span className="text-cyan-400">{propagation.propagationChain.length}</span></span>
              </div>
            )}
          </div>

          <div className="flex-1 relative">
            {!propagation && !isRunning && (
              <div className="h-full ds-card m-4 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <Network className="w-10 h-10 text-ds-text-dim mx-auto mb-3" />
                  <p className="text-sm text-ds-text-dim">{ui('runToSee', lang)}</p>
                  <p className="text-[10px] text-ds-text-dim font-mono mt-1">{gccNodes.length} {ui('nodes', lang)} · {gccEdges.length} {ui('edges', lang)} · {gccScenarios.length} {ui('scenarios', lang)}</p>
                </div>
              </div>
            )}
            {isRunning && (
              <div className="h-full ds-card m-4 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-3" />
                  <p className="text-sm text-ds-text-muted">{ui('buildingGraph', lang)}</p>
                </div>
              </div>
            )}
            {propagation && !isRunning && viewMode === 'graph' && (
              <div className="h-full p-2 relative">
                <GraphPanel initialNodes={graphNodes} initialEdges={graphEdges} onNodeClick={setSelectedNode} />
                <AnimatePresence>
                  {selectedNodeExpl && (
                    <NodeDetailPanel nodeExpl={selectedNodeExpl} lang={lang} onClose={() => setSelectedNode(null)} />
                  )}
                </AnimatePresence>
              </div>
            )}
            {propagation && !isRunning && viewMode === 'globe' && (
              <div className="h-full p-2 relative">
                <GlobeView propagation={propagation} selectedNode={selectedNode} onSelectNode={setSelectedNode} lang={lang} timelineIteration={timelineIteration} globeMode={globeMode} scientist={scientist} scenarioId={scenarioId} />
                <AnimatePresence>
                  {selectedNodeExpl && (
                    <NodeDetailPanel nodeExpl={selectedNodeExpl} lang={lang} onClose={() => setSelectedNode(null)} />
                  )}
                </AnimatePresence>
              </div>
            )}
          </div>

          {propagation && !isRunning && (
            <TimelineBar
              propagation={propagation}
              currentIteration={timelineIteration}
              onIterationChange={setTimelineIteration}
              lang={lang}
            />
          )}
        </div>

        {/* ═══ RIGHT RAIL — Controls & System State ═══ */}
        <div className="w-[280px] bg-ds-surface border-s border-ds-border overflow-y-auto flex-shrink-0">
          <div className="p-3 space-y-3">

            <div>
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-2 flex items-center gap-2">
                <Radio size={10} /> {ui('selectScenario', lang)}
              </h3>
              <select
                value={scenarioId}
                onChange={(e) => { setScenarioId(e.target.value); handleReset() }}
                className="ds-select text-[12px] w-full"
                dir={lang === 'ar' ? 'rtl' : 'ltr'}
              >
                <option value="">{ui('selectScenario', lang)}</option>
                {(Object.keys(SCENARIO_GROUPS) as ScenarioGroup[]).map(groupKey => {
                  const group = SCENARIO_GROUPS[groupKey]
                  const groupScenarios = gccScenarios.filter(s => s.group === groupKey)
                  if (groupScenarios.length === 0) return null
                  return (
                    <optgroup key={groupKey} label={`${group.icon} ${lang === 'ar' ? group.labelAr : group.label}`}>
                      {groupScenarios.map(s => (
                        <option key={s.id} value={s.id}>{lang === 'ar' ? s.titleAr : s.title}</option>
                      ))}
                    </optgroup>
                  )
                })}
              </select>
            </div>

            {scenario && (
              <div className="space-y-3">
                <div className="ds-card rounded-xl p-3">
                  <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-2 flex items-center gap-2">
                    <Info size={10} /> {ui('scenarioMeta', lang)}
                  </h3>
                  {scenario.group && (
                    <div className="text-[10px] text-cyan-400 font-semibold mb-1.5 flex items-center gap-1">
                      <span>{SCENARIO_GROUPS[scenario.group]?.icon}</span>
                      <span>{lang === 'ar' ? SCENARIO_GROUPS[scenario.group]?.labelAr : SCENARIO_GROUPS[scenario.group]?.label}</span>
                    </div>
                  )}
                  <p className="text-[12px] text-ds-text-muted leading-relaxed mb-2">
                    {lang === 'ar' ? scenario.descriptionAr : scenario.description}
                  </p>
                  {scenario.thesis && (
                    <div className="text-[11px] text-amber-400/80 italic leading-relaxed mb-2 border-s-2 border-amber-500/30 ps-2">
                      {lang === 'ar' ? scenario.thesisAr : scenario.thesis}
                    </div>
                  )}
                  <div className="text-[10px] text-ds-text-dim font-mono mb-1.5">
                    {(lang === 'ar' && scenario.countryAr) ? scenario.countryAr : scenario.country} · {(lang === 'ar' && scenario.categoryAr) ? scenario.categoryAr : scenario.category}
                  </div>
                  {scenario.sectors && scenario.sectors.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {(lang === 'ar' && scenario.sectorsAr ? scenario.sectorsAr : scenario.sectors).map((sec: string, i: number) => (
                        <span key={i} className="text-[9px] px-1.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">{sec}</span>
                      ))}
                    </div>
                  )}
                  {scenario.timeHorizon && (
                    <div className="flex items-center gap-1.5 mt-2 text-[10px] text-ds-text-dim">
                      <span className="text-purple-400">⏱</span>
                      <span className="font-mono">{lang === 'ar' ? scenario.timeHorizonAr : scenario.timeHorizon}</span>
                    </div>
                  )}
                  {scenario.simulationType && (
                    <div className="flex items-center gap-1.5 mt-1 text-[10px] text-ds-text-dim">
                      <span className="text-emerald-400">◉</span>
                      <span className="font-mono">{scenario.simulationType}</span>
                    </div>
                  )}
                  {scenario.formulaTags && scenario.formulaTags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {scenario.formulaTags.map((tag: string, i: number) => (
                        <span key={i} className="text-[8px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400/80 border border-amber-500/15 font-mono">{tag}</span>
                      ))}
                    </div>
                  )}
                  {scenario.mapModes && scenario.mapModes.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {scenario.mapModes.map((mode: string, i: number) => (
                        <span key={i} className="text-[8px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400/80 border border-purple-500/15 font-mono">{mode}</span>
                      ))}
                    </div>
                  )}
                  {scenario.chokePoints && scenario.chokePoints.length > 0 && (
                    <div className="flex items-center gap-1.5 mt-2 text-[10px] text-red-400/80">
                      <span>⚠</span>
                      <span className="font-mono">{lang === 'ar' ? 'نقاط الاختناق' : 'Choke Points'}: {scenario.chokePoints.join(', ')}</span>
                    </div>
                  )}
                  {scenario.severityDefault !== undefined && (
                    <div className="flex items-center gap-1.5 mt-1 text-[10px] text-ds-text-dim">
                      <span className="text-red-400">●</span>
                      <span className="font-mono">{lang === 'ar' ? 'الحدة الأساسية' : 'Base Severity'}: {(scenario.severityDefault * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>

                <div>
                  <span className="text-[10px] text-ds-text-dim font-semibold uppercase tracking-wider">{ui('shockNodes', lang)}</span>
                  {scenario.shocks.map(s => {
                    const node = gccNodes.find(n => n.id === s.nodeId)
                    return (
                      <div key={s.nodeId} className="flex items-center justify-between mt-1 px-2 py-1.5 bg-ds-bg-alt rounded-md text-[11px]">
                        <span style={{ color: LAYER_COLORS[node?.layer || 'geography'] }}>{lang === 'ar' ? (node?.labelAr || node?.label) : node?.label}</span>
                        <span className="text-red-400 font-mono font-semibold">{(s.impact * severityMod * 100).toFixed(0)}%</span>
                      </div>
                    )
                  })}
                </div>

                <div>
                  <div className="flex justify-between text-[10px] text-ds-text-dim mb-1">
                    <span>{ui('severity', lang)}</span>
                    <span className="font-mono">{(severityMod * 100).toFixed(0)}%</span>
                  </div>
                  <input type="range" min="0.1" max="1.5" step="0.05" value={severityMod} onChange={(e) => setSeverityMod(parseFloat(e.target.value))} className="w-full accent-cyan-500" />
                </div>

                <button onClick={handleRun} disabled={isRunning} className="w-full ds-btn-primary disabled:opacity-40 disabled:cursor-not-allowed">
                  {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> {ui('processing', lang)}</> : <><Zap className="w-4 h-4" /> {ui('runSim', lang)}</>}
                </button>

                {propagation && (
                  <div className="flex gap-2">
                    <button onClick={handleRun} className="flex-1 ds-btn-primary text-[12px]"><Play className="w-3 h-3" /> {ui('rerun', lang)}</button>
                    <button onClick={handleReset} className="flex-1 ds-btn-secondary text-[12px]"><RotateCcw className="w-3 h-3" /> {ui('reset', lang)}</button>
                  </div>
                )}
              </div>
            )}

            <AnimatePresence>
              {isRunning && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                  <div className="pt-3 border-t border-ds-border space-y-2">
                    <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold flex items-center gap-2">
                      <Activity size={10} className="text-cyan-400" /> {ui('pipeline', lang)}
                    </h3>
                    {PIPELINE.map((step, idx) => (
                      <motion.div key={idx} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }} className="flex items-center gap-2">
                        {idx < processingStep ? <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0" /> :
                         idx === processingStep ? <Loader2 className="w-3 h-3 text-cyan-400 animate-spin flex-shrink-0" /> :
                         <Circle className="w-3 h-3 text-ds-text-dim flex-shrink-0" />}
                        <span className={`text-[11px] font-mono ${idx < processingStep ? 'text-ds-text-muted line-through' : idx === processingStep ? 'text-cyan-400' : 'text-ds-text-dim'}`}>
                          {lang === 'ar' ? step.ar : step.en}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Monte Carlo / Probability Summary */}
            {(analysisMode === 'probabilistic' || monteCarlo) && (
              <div className="ds-card rounded-xl p-3">
                <h3 className="text-[10px] uppercase tracking-[0.15em] text-rose-400 font-bold mb-2 flex items-center gap-2">
                  <TrendingUp size={12} /> {ui('probabilistic', lang)}
                </h3>
                {monteCarlo ? (
                  <div className="space-y-2">
                    <div className="text-[10px] text-ds-text-dim font-mono mb-1">{ui('monteCarlo', lang)}: {monteCarlo.runs} {ui('runs', lang)}</div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-emerald-400">{ui('p10', lang)}</span>
                      <span className="font-mono text-ds-text">${monteCarlo.p10Loss.toFixed(1)}B</span>
                    </div>
                    <div className="relative h-3 bg-ds-bg-alt rounded-full overflow-hidden">
                      <div className="absolute h-full bg-gradient-to-r from-emerald-500/30 via-amber-500/30 to-red-500/30 rounded-full" style={{ left: '5%', right: '5%' }} />
                      <div className="absolute h-full w-0.5 bg-amber-400" style={{ left: `${monteCarlo.p90Loss > 0 ? (monteCarlo.p50Loss / monteCarlo.p90Loss) * 90 : 50}%` }} />
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-amber-400">{ui('p50', lang)}</span>
                      <span className="font-mono text-ds-text">${monteCarlo.p50Loss.toFixed(1)}B</span>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-red-400">{ui('p90', lang)}</span>
                      <span className="font-mono text-ds-text">${monteCarlo.p90Loss.toFixed(1)}B</span>
                    </div>
                    <div className="border-t border-ds-border pt-1 mt-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-ds-text-dim">{ui('mean', lang)}</span>
                        <span className="font-mono text-ds-text-muted">${monteCarlo.meanLoss.toFixed(2)}B</span>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-ds-text-dim">{ui('variance', lang)}</span>
                        <span className="font-mono text-ds-text-muted">{monteCarlo.variance.toFixed(3)}</span>
                      </div>
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-ds-text-dim">{ui('confidenceMC', lang)}</span>
                        <span className="font-mono text-emerald-400">{(monteCarlo.confidenceMC * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] text-ds-text-dim">{ui('runToSee', lang)}</p>
                )}
              </div>
            )}

            {/* System State */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-bold mb-2 flex items-center gap-2">
                <Layers size={12} /> {ui('systemState', lang)}
              </h3>
              <div className="space-y-1.5 text-[10px] font-mono">
                <div className="flex justify-between"><span className="text-ds-text-dim">{ui('nodes', lang)}</span><span className="text-cyan-400">{gccNodes.length}</span></div>
                <div className="flex justify-between"><span className="text-ds-text-dim">{ui('edges', lang)}</span><span className="text-cyan-400">{gccEdges.length}</span></div>
                <div className="flex justify-between"><span className="text-ds-text-dim">{ui('scenarios', lang)}</span><span className="text-cyan-400">{gccScenarios.length}</span></div>
                <div className="flex justify-between"><span className="text-ds-text-dim">{ui('mode', lang)}</span><span className={analysisMode === 'probabilistic' ? 'text-rose-400' : 'text-cyan-400'}>{ui(analysisMode === 'probabilistic' ? 'probabilisticMode' : 'deterministic', lang)}</span></div>
                {propagation && (
                  <>
                    <div className="border-t border-ds-border pt-1 mt-1" />
                    <div className="flex justify-between"><span className="text-ds-text-dim">{ui('systemEnergy', lang)}</span><span className="text-amber-400">{propagation.systemEnergy.toFixed(4)}</span></div>
                    <div className="flex justify-between"><span className="text-ds-text-dim">{ui('depth', lang)}</span><span className="text-purple-400">{propagation.propagationDepth}</span></div>
                    <div className="flex justify-between"><span className="text-ds-text-dim">{ui('totalLoss', lang)}</span><span className="text-red-400">${propagation.totalLoss.toFixed(2)}B</span></div>
                  </>
                )}
              </div>
            </div>

            {/* Scenario Presets — Grouped */}
            <div>
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-2 flex items-center gap-2">
                <Shield size={10} /> {ui('presets', lang)}
              </h3>
              <div className="space-y-3">
                {(Object.keys(SCENARIO_GROUPS) as ScenarioGroup[]).map(groupKey => {
                  const group = SCENARIO_GROUPS[groupKey]
                  const groupScenarios = gccScenarios.filter(s => s.group === groupKey)
                  if (groupScenarios.length === 0) return null
                  return (
                    <div key={groupKey}>
                      <div className="text-[9px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-1 flex items-center gap-1.5 px-1">
                        <span>{group.icon}</span>
                        <span>{lang === 'ar' ? group.labelAr : group.label}</span>
                        <span className="text-ds-text-dim/50">({groupScenarios.length})</span>
                      </div>
                      <div className="space-y-1">
                        {groupScenarios.map(s => (
                          <button
                            key={s.id}
                            onClick={() => { setScenarioId(s.id); handleReset() }}
                            className={`w-full text-start px-3 py-2 rounded-lg border transition-all text-[11px] ${
                              scenarioId === s.id ? 'bg-cyan-500/10 border-cyan-500/25' : 'bg-ds-bg-alt border-ds-border hover:border-ds-border-hover'
                            }`}
                          >
                            <div className="font-medium text-ds-text">{lang === 'ar' ? s.titleAr : s.title}</div>
                            <div className="text-[10px] text-ds-text-dim mt-0.5 font-mono">{lang === 'ar' ? s.countryAr : s.country} · {lang === 'ar' ? s.categoryAr : s.category}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══ STATUS BAR ═══ */}
      <div className="h-8 border-t border-ds-border bg-ds-surface/80 backdrop-blur-xl flex items-center justify-between px-5 text-[10px] font-mono flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
            <span style={{ color: statusColor }} className="uppercase tracking-wider">{statusText}</span>
          </div>
          {propagation && (
            <>
              <span className="text-ds-text-dim">|</span>
              <span className="text-ds-text-dim">{ui('energy', lang)}: <span className="text-cyan-400">{propagation.systemEnergy.toFixed(3)}</span></span>
              <span className="text-ds-text-dim">|</span>
              <span className="text-ds-text-dim">{ui('mode', lang)}: <span className={analysisMode === 'probabilistic' ? 'text-rose-400' : 'text-cyan-400'}>{ui(analysisMode === 'probabilistic' ? 'probabilisticMode' : 'deterministic', lang)}</span></span>
              <span className="text-ds-text-dim">|</span>
              <span className="text-ds-text-dim">{gccNodes.length} {ui('nodes', lang)} · {gccEdges.length} {ui('edges', lang)}</span>
            </>
          )}
        </div>
        <span className="text-ds-text-dim">{ui('title', lang)} {ui('version', lang)} · GCC Regional Command Center</span>
      </div>
    </div>
  )
}

export default function DemoPage() {
  return (
    <Suspense fallback={<div className="h-screen w-full bg-ds-bg flex items-center justify-center"><Loader2 className="w-8 h-8 text-cyan-400 animate-spin" /></div>}>
      <DemoPageContent />
    </Suspense>
  )
}
