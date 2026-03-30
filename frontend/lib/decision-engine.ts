/**
 * ══════════════════════════════════════════════════════════════════
 * DEEVO SIM — DECISION INTELLIGENCE ENGINE
 * ══════════════════════════════════════════════════════════════════
 *
 * Mathematical Model:
 *   DPS = w1·E_sys + w2·PropDepth + w3·SectorSpread + w4·Exposure + w5·StabilityRisk
 *   APS(action) = ImpactReduction(action) · Confidence(action) / Cost(action)
 *   ME = (Loss_Before - Loss_After) / Loss_Before
 *   Urgency = f(shockClass, E_sys, corridorDependency)
 *   DC = ModelConfidence · DataReliability · ScenarioCoherence
 *
 * Contract: every scenario run must produce a DecisionResult with
 *   recommended actions, urgency, confidence, mitigation effectiveness,
 *   and full Arabic translations.
 * ══════════════════════════════════════════════════════════════════
 */

import type { PropagationResult, SectorImpact } from './propagation-engine'
import type { ScenarioEngineResult } from './scenario-engines'

/* ── Types ── */

export type UrgencyLevel = 'flash' | 'immediate' | 'short_term' | 'medium_term'
export type ActionDomain = 'logistics' | 'ports' | 'aviation' | 'utilities' | 'banking' | 'insurance' | 'food_security' | 'sovereign' | 'communication'

export interface RecommendedAction {
  id: string
  domain: ActionDomain
  domainAr: string
  action: string
  actionAr: string
  priority: number        // APS score 0–1
  urgency: UrgencyLevel
  urgencyAr: string
  timeframe: string       // e.g. "0–6h", "24–72h"
  timeframeAr: string
  expectedReduction: number  // fraction of loss this action mitigates
  cost: 'low' | 'medium' | 'high'
  costAr: string
  tradeoff: string
  tradeoffAr: string
  confidence: number      // 0–1
}

export interface DecisionResult {
  // Core scores
  decisionPressureScore: number   // DPS 0–1
  urgencyLevel: UrgencyLevel
  urgencyLevelAr: string
  decisionConfidence: number      // DC 0–1

  // Loss analysis
  expectedLossBefore: number      // $B
  expectedLossAfter: number       // $B after mitigations
  mitigationEffectiveness: number // ME 0–1

  // Narrative
  decisionSummary: string
  decisionSummaryAr: string
  whyTheseActions: string
  whyTheseActionsAr: string

  // Actions
  recommendedActions: RecommendedAction[]
  immediateActions: RecommendedAction[]    // 0–6h
  shortTermActions: RecommendedAction[]    // 24–72h

  // Sector-specific
  sectorActions: { sector: string; sectorAr: string; actions: RecommendedAction[] }[]

  // Resource priorities
  resourcePriorities: { resource: string; resourceAr: string; priority: number; reason: string; reasonAr: string }[]
}

/* ── Scientist input (passed from page.tsx) ── */
export interface ScientistState {
  energy: number
  confidence: number
  uncertainty: number
  regionalStress: number
  shockClass: 'critical' | 'severe' | 'moderate' | 'low'
  stage: 'initial' | 'cascading' | 'saturated'
  propagationDepth: number
  totalExposure: number
  dominantSector: SectorImpact | null
}

/* ── Domain labels ── */
const DOMAIN_AR: Record<ActionDomain, string> = {
  logistics: 'اللوجستيات',
  ports: 'الموانئ',
  aviation: 'الطيران',
  utilities: 'المرافق',
  banking: 'البنوك',
  insurance: 'التأمين',
  food_security: 'الأمن الغذائي',
  sovereign: 'الاستجابة السيادية',
  communication: 'الاتصالات والاستقرار',
}

const URGENCY_AR: Record<UrgencyLevel, string> = {
  flash: 'فوري عاجل',
  immediate: 'فوري',
  short_term: 'قصير المدى',
  medium_term: 'متوسط المدى',
}

const COST_AR: Record<string, string> = {
  low: 'منخفض',
  medium: 'متوسط',
  high: 'مرتفع',
}

/* ══════════════════════════════════════════
   DECISION PRESSURE SCORE (DPS)
   ══════════════════════════════════════════ */
function computeDPS(
  energy: number,
  depth: number,
  sectorSpread: number,
  exposure: number,
  stabilityRisk: number,
): number {
  // Weights calibrated for GCC risk landscape
  const w1 = 0.25  // system energy
  const w2 = 0.15  // propagation depth
  const w3 = 0.20  // sector spread
  const w4 = 0.25  // exposure
  const w5 = 0.15  // public stability risk

  const normEnergy = Math.min(energy / 15, 1)     // 15 = high-energy system
  const normDepth = Math.min(depth / 8, 1)         // 8 = deep cascade
  const normSpread = Math.min(sectorSpread / 5, 1) // 5 layers
  const normExposure = Math.min(exposure / 80, 1)  // $80B = extreme
  const normStability = Math.min(stabilityRisk, 1)

  return w1 * normEnergy + w2 * normDepth + w3 * normSpread + w4 * normExposure + w5 * normStability
}

/* ══════════════════════════════════════════
   URGENCY from system state
   ══════════════════════════════════════════ */
function computeUrgency(
  shockClass: string,
  energy: number,
  stage: string,
  dps: number,
): UrgencyLevel {
  if (shockClass === 'critical' || (energy > 10 && stage === 'saturated')) return 'flash'
  if (shockClass === 'severe' || dps > 0.65 || stage === 'cascading') return 'immediate'
  if (dps > 0.35 || shockClass === 'moderate') return 'short_term'
  return 'medium_term'
}

/* ══════════════════════════════════════════
   DECISION CONFIDENCE (DC)
   ══════════════════════════════════════════ */
function computeDecisionConfidence(
  modelConfidence: number,
  sectorSpread: number,
  depth: number,
): number {
  // Data reliability degrades with more affected sectors (more uncertainty)
  const dataReliability = Math.max(0.3, 1 - (sectorSpread * 0.08))
  // Scenario coherence: deeper propagation = more complex = lower coherence
  const scenarioCoherence = Math.max(0.4, 1 - (depth * 0.06))
  return modelConfidence * dataReliability * scenarioCoherence
}

/* ══════════════════════════════════════════
   SCENARIO-SPECIFIC ACTION CATALOG
   ══════════════════════════════════════════ */

interface ActionTemplate {
  domain: ActionDomain
  action: string
  actionAr: string
  timeframe: string
  timeframeAr: string
  expectedReduction: number
  cost: 'low' | 'medium' | 'high'
  tradeoff: string
  tradeoffAr: string
  relevantScenarios: string[]  // scenario ID patterns
  relevantSectors: string[]     // affected sector layers
}

const ACTION_CATALOG: ActionTemplate[] = [
  // ── LOGISTICS / PORTS ──
  {
    domain: 'logistics', action: 'Activate Fujairah bypass for Hormuz-dependent cargo',
    actionAr: 'تفعيل مسار الفجيرة البديل للشحن المعتمد على هرمز',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.12,
    cost: 'medium', tradeoff: 'Higher per-unit shipping cost; limited Fujairah throughput capacity',
    tradeoffAr: 'تكلفة شحن أعلى لكل وحدة؛ سعة محدودة في الفجيرة',
    relevantScenarios: ['hormuz', 'port', 'military', 'shipping'],
    relevantSectors: ['infrastructure', 'geography'],
  },
  {
    domain: 'ports', action: 'Extend port operating hours to 24/7 and activate overflow berths',
    actionAr: 'تمديد ساعات عمل الموانئ إلى ٢٤/٧ وتفعيل أرصفة الفائض',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.08,
    cost: 'medium', tradeoff: 'Increased labor costs; accelerated equipment wear',
    tradeoffAr: 'زيادة تكاليف العمالة؛ تسارع استهلاك المعدات',
    relevantScenarios: ['port', 'hormuz', 'jebel_ali', 'congestion'],
    relevantSectors: ['infrastructure'],
  },
  {
    domain: 'logistics', action: 'Pre-position 90-day strategic food reserves at GCC distribution hubs',
    actionAr: 'تخزين احتياطي غذائي استراتيجي لـ٩٠ يومًا في مراكز التوزيع الخليجية',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.10,
    cost: 'high', tradeoff: 'Capital lockup in inventory; storage infrastructure required',
    tradeoffAr: 'تجميد رأس المال في المخزون؛ يتطلب بنية تخزين',
    relevantScenarios: ['food', 'hormuz', 'port', 'shipping'],
    relevantSectors: ['economy', 'society'],
  },
  // ── AVIATION ──
  {
    domain: 'aviation', action: 'Negotiate emergency overflight rights with adjacent airspace authorities',
    actionAr: 'التفاوض على حقوق تحليق طارئة مع سلطات المجال الجوي المجاورة',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.09,
    cost: 'low', tradeoff: 'Political friction; reciprocity obligations',
    tradeoffAr: 'احتكاك سياسي؛ التزامات المعاملة بالمثل',
    relevantScenarios: ['airspace', 'flight', 'escalation', 'military'],
    relevantSectors: ['infrastructure', 'economy'],
  },
  {
    domain: 'aviation', action: 'Cap ticket prices and activate airline subsidy mechanism',
    actionAr: 'تحديد سقف أسعار التذاكر وتفعيل آلية دعم شركات الطيران',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.06,
    cost: 'high', tradeoff: 'Fiscal cost; may distort airline competition',
    tradeoffAr: 'تكلفة مالية؛ قد يشوه المنافسة بين شركات الطيران',
    relevantScenarios: ['airspace', 'flight', 'hajj'],
    relevantSectors: ['economy', 'society'],
  },
  // ── UTILITIES ──
  {
    domain: 'utilities', action: 'Activate emergency power interconnect with neighboring GCC grids',
    actionAr: 'تفعيل الربط الكهربائي الطارئ مع شبكات دول الخليج المجاورة',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.11,
    cost: 'medium', tradeoff: 'Cross-border dependency; interconnect capacity limits',
    tradeoffAr: 'اعتماد عبر الحدود؛ حدود سعة الربط',
    relevantScenarios: ['grid', 'water', 'summer', 'utility'],
    relevantSectors: ['infrastructure'],
  },
  {
    domain: 'utilities', action: 'Deploy mobile desalination units to critical population centers',
    actionAr: 'نشر وحدات تحلية متنقلة في المراكز السكانية الحيوية',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.07,
    cost: 'high', tradeoff: 'Limited output capacity; logistics of deployment',
    tradeoffAr: 'سعة إنتاج محدودة؛ تحديات النقل والتوزيع',
    relevantScenarios: ['water', 'grid', 'summer', 'utility'],
    relevantSectors: ['infrastructure', 'society'],
  },
  // ── BANKING / FINANCE ──
  {
    domain: 'banking', action: 'Central bank injects emergency liquidity via repo facility',
    actionAr: 'البنك المركزي يضخ سيولة طارئة عبر تسهيلات إعادة الشراء',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.10,
    cost: 'medium', tradeoff: 'Inflation risk; moral hazard for banks',
    tradeoffAr: 'مخاطر التضخم؛ خطر أخلاقي للبنوك',
    relevantScenarios: ['liquidity', 'fx', 'banking', 'insurance', 'repricing'],
    relevantSectors: ['finance'],
  },
  {
    domain: 'banking', action: 'Activate capital control circuit breakers on Tadawul/ADX',
    actionAr: 'تفعيل قواطع التداول الآلية في تداول/سوق أبوظبي',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.05,
    cost: 'low', tradeoff: 'Reduced market liquidity; investor confidence impact',
    tradeoffAr: 'انخفاض سيولة السوق؛ تأثير على ثقة المستثمرين',
    relevantScenarios: ['fx', 'liquidity', 'escalation'],
    relevantSectors: ['finance'],
  },
  // ── INSURANCE ──
  {
    domain: 'insurance', action: 'Issue emergency reinsurance call and activate catastrophe bonds',
    actionAr: 'إصدار نداء إعادة تأمين طارئ وتفعيل سندات الكوارث',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.08,
    cost: 'high', tradeoff: 'Premium spikes for 18+ months; capacity contraction',
    tradeoffAr: 'ارتفاع الأقساط لأكثر من ١٨ شهرًا؛ تقلص السعة',
    relevantScenarios: ['insurance', 'repricing', 'hormuz', 'grid'],
    relevantSectors: ['finance'],
  },
  // ── FOOD SECURITY ──
  {
    domain: 'food_security', action: 'Activate bilateral food supply agreements with strategic partners',
    actionAr: 'تفعيل اتفاقيات الإمداد الغذائي الثنائية مع الشركاء الاستراتيجيين',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.09,
    cost: 'medium', tradeoff: 'Geopolitical obligations; premium pricing',
    tradeoffAr: 'التزامات جيوسياسية؛ أسعار مرتفعة',
    relevantScenarios: ['food', 'hormuz', 'port'],
    relevantSectors: ['economy', 'society'],
  },
  {
    domain: 'food_security', action: 'Implement temporary price controls on essential commodities',
    actionAr: 'تطبيق ضوابط أسعار مؤقتة على السلع الأساسية',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.04,
    cost: 'low', tradeoff: 'Supply distortion; black market risk',
    tradeoffAr: 'تشوه العرض؛ مخاطر السوق السوداء',
    relevantScenarios: ['food', 'hormuz'],
    relevantSectors: ['society', 'economy'],
  },
  // ── SOVEREIGN ──
  {
    domain: 'sovereign', action: 'Convene GCC Emergency Coordination Council',
    actionAr: 'عقد مجلس التنسيق الطارئ لدول مجلس التعاون',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.06,
    cost: 'low', tradeoff: 'Political consensus delay; sovereignty concerns',
    tradeoffAr: 'تأخر التوافق السياسي؛ مخاوف السيادة',
    relevantScenarios: ['hormuz', 'escalation', 'military', 'grid'],
    relevantSectors: ['geography'],
  },
  {
    domain: 'sovereign', action: 'Activate strategic petroleum reserve drawdown',
    actionAr: 'تفعيل سحب الاحتياطي النفطي الاستراتيجي',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.11,
    cost: 'high', tradeoff: 'Depletes strategic buffer; recovery time 6–12 months',
    tradeoffAr: 'يستنفد المخزون الاستراتيجي؛ وقت التعافي ٦–١٢ شهرًا',
    relevantScenarios: ['hormuz', 'escalation', 'fx'],
    relevantSectors: ['economy', 'geography'],
  },
  // ── COMMUNICATION / PUBLIC STABILITY ──
  {
    domain: 'communication', action: 'Launch coordinated public communication campaign across GCC media',
    actionAr: 'إطلاق حملة تواصل عام منسقة عبر وسائل الإعلام الخليجية',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.05,
    cost: 'low', tradeoff: 'Message control risk; credibility if situation worsens',
    tradeoffAr: 'مخاطر السيطرة على الرسالة؛ المصداقية إذا تفاقم الوضع',
    relevantScenarios: ['hormuz', 'escalation', 'food', 'grid', 'hajj', 'military'],
    relevantSectors: ['society'],
  },
  {
    domain: 'communication', action: 'Deploy social media monitoring and counter-misinformation taskforce',
    actionAr: 'نشر فريق مراقبة وسائل التواصل ومكافحة المعلومات المضللة',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.03,
    cost: 'low', tradeoff: 'Resource diversion; free speech concerns',
    tradeoffAr: 'تحويل الموارد؛ مخاوف حرية التعبير',
    relevantScenarios: ['escalation', 'hormuz', 'food', 'hajj'],
    relevantSectors: ['society'],
  },
  // ── MEGA PROJECTS / VISION 2030 ──
  {
    domain: 'sovereign', action: 'Restructure mega-project timelines and activate force majeure clauses',
    actionAr: 'إعادة هيكلة جداول المشاريع الكبرى وتفعيل شروط القوة القاهرة',
    timeframe: '24–72h', timeframeAr: '٢٤–٧٢ ساعة', expectedReduction: 0.07,
    cost: 'medium', tradeoff: 'Contractor disputes; investor confidence; timeline slippage',
    tradeoffAr: 'نزاعات المقاولين؛ ثقة المستثمرين؛ تأخر الجداول الزمنية',
    relevantScenarios: ['vision', 'mega', 'liquidity'],
    relevantSectors: ['economy', 'finance'],
  },
  // ── HAJJ ──
  {
    domain: 'logistics', action: 'Activate Hajj contingency routing via King Fahd Causeway and land corridors',
    actionAr: 'تفعيل المسارات البديلة للحج عبر جسر الملك فهد والممرات البرية',
    timeframe: '0–6h', timeframeAr: '٠–٦ ساعات', expectedReduction: 0.08,
    cost: 'medium', tradeoff: 'Congestion on land routes; accommodation redistribution needed',
    tradeoffAr: 'ازدحام المسارات البرية؛ يتطلب إعادة توزيع الإقامة',
    relevantScenarios: ['hajj', 'airspace', 'flight'],
    relevantSectors: ['infrastructure', 'society'],
  },
]

/* ══════════════════════════════════════════
   ACTION MATCHING & SCORING
   ══════════════════════════════════════════ */
function matchActions(
  scenarioId: string,
  affectedSectors: SectorImpact[],
  dps: number,
  urgency: UrgencyLevel,
  dc: number,
): RecommendedAction[] {
  const sectorLayers = new Set(affectedSectors.map(s => s.sector))
  const scenarioLower = scenarioId.toLowerCase()

  const matched = ACTION_CATALOG.filter(t => {
    // Match by scenario keyword
    const scenarioMatch = t.relevantScenarios.some(kw => scenarioLower.includes(kw))
    // Match by affected sector
    const sectorMatch = t.relevantSectors.some(s => sectorLayers.has(s as any))
    return scenarioMatch || sectorMatch
  })

  return matched.map((t, i) => {
    // APS = ImpactReduction * Confidence / Cost
    const costMultiplier = t.cost === 'low' ? 1.0 : t.cost === 'medium' ? 0.7 : 0.4
    const reductionScore = t.expectedReduction * dc * costMultiplier
    // Boost priority for actions matching urgency timeframe
    const timeBoost = (urgency === 'flash' || urgency === 'immediate') && t.timeframe === '0–6h' ? 0.15 : 0
    const priority = Math.min(reductionScore + timeBoost, 1)

    const actionUrgency: UrgencyLevel = t.timeframe === '0–6h'
      ? (dps > 0.6 ? 'flash' : 'immediate')
      : 'short_term'

    return {
      id: `action_${i}`,
      domain: t.domain,
      domainAr: DOMAIN_AR[t.domain],
      action: t.action,
      actionAr: t.actionAr,
      priority,
      urgency: actionUrgency,
      urgencyAr: URGENCY_AR[actionUrgency],
      timeframe: t.timeframe,
      timeframeAr: t.timeframeAr,
      expectedReduction: t.expectedReduction,
      cost: t.cost,
      costAr: COST_AR[t.cost],
      tradeoff: t.tradeoff,
      tradeoffAr: t.tradeoffAr,
      confidence: dc * (t.cost === 'low' ? 1.0 : 0.85),
    }
  }).sort((a, b) => b.priority - a.priority)
}

/* ══════════════════════════════════════════
   NARRATIVE GENERATION
   ══════════════════════════════════════════ */
function generateSummary(
  scenarioId: string,
  shockClass: string,
  stage: string,
  exposure: number,
  urgency: UrgencyLevel,
  topActions: RecommendedAction[],
  dominantSector: SectorImpact | null,
): { en: string; ar: string } {
  const sectorEn = dominantSector?.sectorLabel || 'multiple sectors'
  const topActionEn = topActions[0]?.action || 'assess situation'
  const topActionAr = topActions[0]?.actionAr || 'تقييم الوضع'

  const en = `${shockClass.toUpperCase()} shock detected in ${stage} stage. System exposure: $${exposure.toFixed(1)}B across ${sectorEn}. ` +
    `Urgency: ${urgency.replace('_', ' ')}. Priority action: ${topActionEn}. ` +
    `${topActions.length} recommended actions identified across ${new Set(topActions.map(a => a.domain)).size} domains.`

  const shockAr = shockClass === 'critical' ? 'حرج' : shockClass === 'severe' ? 'شديد' : shockClass === 'moderate' ? 'متوسط' : 'منخفض'
  const stageAr = stage === 'initial' ? 'أولي' : stage === 'cascading' ? 'متسلسل' : 'مشبع'
  const urgencyAr = URGENCY_AR[urgency]

  const ar = `تم رصد صدمة ${shockAr} في مرحلة ${stageAr}. التعرض: $${exposure.toFixed(1)} مليار عبر ${dominantSector?.sectorLabel || 'قطاعات متعددة'}. ` +
    `الاستعجال: ${urgencyAr}. الإجراء ذو الأولوية: ${topActionAr}. ` +
    `تم تحديد ${topActions.length} إجراء موصى به عبر ${new Set(topActions.map(a => a.domain)).size} مجالات.`

  return { en, ar }
}

function generateWhyActions(
  dps: number,
  shockClass: string,
  topActions: RecommendedAction[],
  me: number,
): { en: string; ar: string } {
  const domains = [...new Set(topActions.slice(0, 5).map(a => a.domain))]
  const domainsEn = domains.map(d => d.replace('_', ' ')).join(', ')
  const domainsAr = domains.map(d => DOMAIN_AR[d]).join('، ')

  const en = `Decision pressure score (${(dps * 100).toFixed(0)}%) and ${shockClass} shock classification indicate ` +
    `concentrated risk requiring multi-domain response across ${domainsEn}. ` +
    `Combined mitigation effectiveness: ${(me * 100).toFixed(0)}% loss reduction achievable.`

  const ar = `درجة ضغط القرار (${(dps * 100).toFixed(0)}%) وتصنيف الصدمة ${shockClass === 'critical' ? 'الحرج' : shockClass === 'severe' ? 'الشديد' : 'المتوسط'} ` +
    `يشيران إلى مخاطر مركزة تتطلب استجابة متعددة المجالات عبر ${domainsAr}. ` +
    `فعالية التخفيف المجمعة: إمكانية تقليل الخسائر بنسبة ${(me * 100).toFixed(0)}%.`

  return { en, ar }
}

/* ══════════════════════════════════════════
   MAIN: computeDecision()
   ══════════════════════════════════════════ */
export function computeDecision(
  propagation: PropagationResult,
  engineResult: ScenarioEngineResult | null,
  scientist: ScientistState,
  scenarioId: string,
): DecisionResult {
  const {
    energy, confidence, shockClass, stage,
    propagationDepth, totalExposure, regionalStress, dominantSector,
  } = scientist

  const sectorSpread = propagation.affectedSectors.length

  // ── Core Scores ──
  const dps = computeDPS(energy, propagationDepth, sectorSpread, totalExposure, regionalStress)
  const urgency = computeUrgency(shockClass, energy, stage, dps)
  const dc = computeDecisionConfidence(confidence, sectorSpread, propagationDepth)

  // ── Match Actions ──
  const allActions = matchActions(scenarioId, propagation.affectedSectors, dps, urgency, dc)
  const immediateActions = allActions.filter(a => a.timeframe === '0–6h')
  const shortTermActions = allActions.filter(a => a.timeframe === '24–72h')

  // ── Mitigation Effectiveness ──
  const combinedReduction = allActions.reduce((sum, a) => sum + a.expectedReduction, 0)
  const me = Math.min(combinedReduction, 0.85) // cap at 85% — no plan eliminates all risk
  const expectedLossAfter = totalExposure * (1 - me)

  // ── Sector Actions ──
  const sectorMap = new Map<string, RecommendedAction[]>()
  for (const action of allActions) {
    const key = action.domain
    if (!sectorMap.has(key)) sectorMap.set(key, [])
    sectorMap.get(key)!.push(action)
  }
  const sectorActions = Array.from(sectorMap.entries()).map(([sector, actions]) => ({
    sector: sector.replace('_', ' '),
    sectorAr: DOMAIN_AR[sector as ActionDomain] || sector,
    actions,
  }))

  // ── Resource Priorities ──
  const resourcePriorities = computeResourcePriorities(allActions, shockClass, scenarioId)

  // ── Narratives ──
  const summary = generateSummary(scenarioId, shockClass, stage, totalExposure, urgency, allActions, dominantSector)
  const whyActions = generateWhyActions(dps, shockClass, allActions, me)

  return {
    decisionPressureScore: dps,
    urgencyLevel: urgency,
    urgencyLevelAr: URGENCY_AR[urgency],
    decisionConfidence: dc,
    expectedLossBefore: totalExposure,
    expectedLossAfter,
    mitigationEffectiveness: me,
    decisionSummary: summary.en,
    decisionSummaryAr: summary.ar,
    whyTheseActions: whyActions.en,
    whyTheseActionsAr: whyActions.ar,
    recommendedActions: allActions,
    immediateActions,
    shortTermActions,
    sectorActions,
    resourcePriorities,
  }
}

/* ── Resource Priority Computation ── */
function computeResourcePriorities(
  actions: RecommendedAction[],
  shockClass: string,
  scenarioId: string,
): { resource: string; resourceAr: string; priority: number; reason: string; reasonAr: string }[] {
  const priorities: { resource: string; resourceAr: string; priority: number; reason: string; reasonAr: string }[] = []

  // Count action domains to determine resource needs
  const domainCounts = new Map<string, number>()
  for (const a of actions) {
    domainCounts.set(a.domain, (domainCounts.get(a.domain) || 0) + 1)
  }

  if (domainCounts.has('logistics') || domainCounts.has('ports')) {
    priorities.push({
      resource: 'Maritime & Port Operations', resourceAr: 'العمليات البحرية والموانئ',
      priority: shockClass === 'critical' ? 0.95 : 0.75,
      reason: 'Port throughput and shipping rerouting require immediate coordination',
      reasonAr: 'إنتاجية الموانئ وإعادة توجيه الشحن تتطلب تنسيقًا فوريًا',
    })
  }
  if (domainCounts.has('aviation')) {
    priorities.push({
      resource: 'Aviation Coordination', resourceAr: 'تنسيق الطيران',
      priority: scenarioId.includes('airspace') || scenarioId.includes('flight') ? 0.90 : 0.60,
      reason: 'Airspace management and airline capacity reallocation',
      reasonAr: 'إدارة المجال الجوي وإعادة تخصيص سعة شركات الطيران',
    })
  }
  if (domainCounts.has('banking') || domainCounts.has('insurance')) {
    priorities.push({
      resource: 'Financial Stability Unit', resourceAr: 'وحدة الاستقرار المالي',
      priority: shockClass === 'critical' ? 0.90 : 0.70,
      reason: 'Central bank coordination and market circuit breakers',
      reasonAr: 'تنسيق البنك المركزي وقواطع السوق',
    })
  }
  if (domainCounts.has('utilities')) {
    priorities.push({
      resource: 'GCC Grid Operations Center', resourceAr: 'مركز عمليات الشبكة الخليجية',
      priority: 0.85,
      reason: 'Power and water continuity across interconnected grids',
      reasonAr: 'استمرارية الكهرباء والمياه عبر الشبكات المترابطة',
    })
  }
  if (domainCounts.has('communication')) {
    priorities.push({
      resource: 'Crisis Communications Team', resourceAr: 'فريق اتصالات الأزمات',
      priority: 0.80,
      reason: 'Public messaging and social media monitoring',
      reasonAr: 'الرسائل العامة ومراقبة وسائل التواصل الاجتماعي',
    })
  }
  if (domainCounts.has('food_security')) {
    priorities.push({
      resource: 'Food Security Directorate', resourceAr: 'مديرية الأمن الغذائي',
      priority: 0.85,
      reason: 'Supply chain activation and price stabilization',
      reasonAr: 'تفعيل سلسلة الإمداد واستقرار الأسعار',
    })
  }

  return priorities.sort((a, b) => b.priority - a.priority)
}
