/* =================================================
    Impact Observatory — Simulation Engine
    Rule-based Decision Intelligence Logic
   ================================================= */

import type {
  DecisionOutput, RiskLevel, SentimentDirection,
  RecommendedAction, ExplainabilityItem, ScenarioNarrative,
  SimulationInput
} from './types'

/* -------------------------------------------------
   Risk Score Calculator
   ------------------------------------------------- */
function calculateRiskScore(input: SimulationInput): number {
  let score = 0
  const highInfluencers = input.agents.filter(a => a.influence > 0.7)

  // Sentiment factor
  if (input.baseSentiment === 'negative') score += 3
  if (input.baseSentiment === 'mixed') score += 1

  // Influencer + Media combo (highest risk)
  if (highInfluencers.length > 0 && input.hasMediaPickup) score += 3

  // Individual factors
  if (highInfluencers.length > 0) score += 2
  if (input.hasMediaPickup) score += 1

  // Government response absence
  if (!input.hasGovernmentResponse) score += 2

  // Entity density factor
  if (input.entities.length > 6) score += 1

  return score
}

/* -------------------------------------------------
   Spread Percentage Calculator
   ------------------------------------------------- */
function calculateSpread(input: SimulationInput): number {
  let spread = 15
  const highInfluencers = input.agents.filter(a => a.influence > 0.7)

  if (highInfluencers.length > 0) spread += 25
  if (input.hasMediaPickup) spread += 20
  if (input.baseSentiment === 'negative') spread += 15
  if (input.baseSentiment === 'mixed') spread += 8
  if (!input.hasGovernmentResponse) spread += 10
  if (input.entities.length > 6) spread += 5

  return Math.min(spread, 95)
}

/* -------------------------------------------------
   Explanation Generator
   ------------------------------------------------- */
function generateExplanation(input: SimulationInput): ExplainabilityItem[] {
  const items: ExplainabilityItem[] = []
  const highInfluencers = input.agents.filter(a => a.influence > 0.7)

  if (input.baseSentiment === 'negative') {
    items.push({
      factor: 'Negative public sentiment',
      factorAr: 'مشاعر عامة سلبية',
      direction: 'amplifying',
      weight: 0.85,
      description: 'Negative events spread 2.3x faster than neutral ones in GCC social media ecosystems',
      descriptionAr: 'الأحداث السلبية تنتشر أسرع ب 2.3 مرة من المحايدة'
    })
  }

  if (highInfluencers.length > 0) {
    items.push({
      factor: 'High influencer amplification',
      factorAr: 'تضخيم المؤثرين',
      direction: 'amplifying',
      weight: 0.78,
      description: 'Influencers with >70% reach accelerate information spread across platform boundaries',
      descriptionAr: 'المؤثرون بنسبة وصول أكثر من 70% يسرعون انتشار المعلومات'
    })
  }

  if (!input.hasGovernmentResponse) {
    items.push({
      factor: 'Absence of official response',
      factorAr: 'غياب الرد الرسمي',
      direction: 'amplifying',
      weight: 0.72,
      description: 'Delayed government response increases speculation and rumor propagation by up to 40%',
      descriptionAr: 'تأخر الرد الحكومي يزيد التكهنات بنسبة 40%'
    })
  }

  if (input.hasMediaPickup) {
    items.push({
      factor: 'Media coverage within first wave',
      factorAr: 'تغطية إعلامية في الموجة الأولى',
      direction: 'amplifying',
      weight: 0.65,
      description: 'Media pickup in the first cycle legitimizes the narrative and expands audience reach 3x',
      descriptionAr: 'التغطية الإعلامية تضفي شرعية وتوسع نطاق الجمهور'
    })
  }

  if (input.hasGovernmentResponse) {
    items.push({
      factor: 'Early official response detected',
      factorAr: 'رد رسمي مبكر',
      direction: 'dampening',
      weight: 0.60,
      description: 'Official statements within the first cycle reduce speculation by up to 40%',
      descriptionAr: 'البيانات الرسمية تقلل التكهنات بنسبة 40%'
    })
  }

  return items
      }

/* -------------------------------------------------
   Action Recommender
   ------------------------------------------------- */
function generateActions(input: SimulationInput, riskScore: number): RecommendedAction[] {
  const actions: RecommendedAction[] = []
  const highInfluencers = input.agents.filter(a => a.influence > 0.7)

  if (!input.hasGovernmentResponse && riskScore >= 3) {
    actions.push({
      id: 'act-1',
      priority: 'immediate',
      action: 'Issue official statement within 2 hours',
      actionAr: 'إصدار بيان رسمي خلال ساعتين',
      rationale: 'Early official response reduces misinformation spread by 40% and stabilizes public sentiment',
      rationaleAr: 'الرد الرسمي المبكر يقلل انتشار المعلومات المضللة بنسبة 40%',
      timeframe: '0–2 hours',
      impact: 'high'
    })
  }

  if (highInfluencers.length > 0) {
    actions.push({
      id: 'act-2',
      priority: 'immediate',
      action: 'Engage top influencers with verified information',
      actionAr: 'إشراك أهم المؤثرين بمعلومات موثقة',
      rationale: 'Redirecting influencer narrative shifts public perception within 1 simulation cycle',
      rationaleAr: 'إعادة توجيه خطاب المؤثرين يغير التصور العام',
      timeframe: '0–4 hours',
      impact: 'high'
    })
  }

  if (riskScore >= 6) {
    actions.push({
      id: 'act-3',
      priority: 'short-term',
      action: 'Activate crisis communication protocol',
      actionAr: 'تفعيل بروتوكول اتصال الأزمات',
      rationale: 'High-risk scenarios require coordinated multi-channel response with unified messaging',
      rationaleAr: 'السيناريوهات عالية المخاطر تتطلب استجابة منسقة',
      timeframe: '2–6 hours',
      impact: 'high'
    })
  }

  actions.push({
    id: 'act-monitor',
    priority: 'monitoring',
    action: 'Deploy real-time sentiment monitoring across Twitter and WhatsApp',
    actionAr: 'نشر مراقبة المشاعر عبر تويتر وواتساب',
    rationale: 'Continuous monitoring enables early detection of narrative shifts and emerging risks',
    rationaleAr: 'المراقبة المستمرة تمكن من الكشف المبكر',
    timeframe: 'Ongoing',
    impact: 'medium'
  })

  return actions
        }

/* -------------------------------------------------
   Main Simulation Runner
   ------------------------------------------------- */
export function runDecisionSimulation(input: SimulationInput): DecisionOutput {
  const riskScore = calculateRiskScore(input)
  const spreadPct = calculateSpread(input)
  const highInfluencers = input.agents.filter(a => a.influence > 0.7)

  // Map score to risk level
  const riskLevel: RiskLevel =
    riskScore >= 9 ? 'CRITICAL' :
    riskScore >= 6 ? 'HIGH' :
    riskScore >= 3 ? 'MEDIUM' : 'LOW'

  // Determine primary driver
  let primaryDriver = 'Organic public discussion'
  let primaryDriverAr = 'نقاش عام عضوي'
  if (highInfluencers.length > 0 && input.hasMediaPickup) {
    primaryDriver = 'Influencer amplification combined with media coverage'
    primaryDriverAr = 'تضخيم المؤثرين مع تغطية إعلامية'
  } else if (highInfluencers.length > 0) {
    primaryDriver = 'High-influence persona amplification'
    primaryDriverAr = 'تضخيم شخصيات عالية التأثير'
  } else if (input.hasMediaPickup) {
    primaryDriver = 'Media coverage acceleration'
    primaryDriverAr = 'تسارع التغطية الإعلامية'
  }

  // Critical time window
  const criticalTimeWindow =
    riskScore >= 6 ? 'First 2 hours are critical — immediate response required' :
    riskScore >= 3 ? 'First 6 hours require active monitoring' :
    'Standard 24-hour monitoring cycle'
  const criticalTimeWindowAr =
    riskScore >= 6 ? 'أول ساعتين حرجة — يتطلب استجابة فورية' :
    riskScore >= 3 ? 'أول 6 ساعات تتطلب مراقبة نشطة' :
    'دورة مراقبة 24 ساعة'

  // Build narrative
  const narrative: ScenarioNarrative = {
    title: input.scenarioTitle + ' — Risk Simulation',
    titleAr: input.scenarioTitle + ' — محاكاة المخاطر',
    subtitle: 'Decision Intelligence Analysis',
    subtitleAr: 'تحليل ذكاء القرار',
    summary: 'This simulation models public reaction dynamics across GCC social channels. The scenario triggers a ' + riskLevel.toLowerCase() + '-risk propagation pattern driven primarily by ' + primaryDriver.toLowerCase() + '.',
    summaryAr: 'تحاكي هذه المحاكاة ديناميكيات ردود الفعل العامة عبر قنوات التواصل الخليجية.',
    riskDescription: riskScore >= 6
      ? 'This scenario presents significant reputational and operational risk requiring immediate executive attention and coordinated response.'
      : 'This scenario requires standard monitoring with escalation triggers in place.',
    riskDescriptionAr: riskScore >= 6
      ? 'يمثل هذا السيناريو مخاطر كبيرة تتطلب اهتماماً تنفيذياً فورياً.'
      : 'يتطلب هذا السيناريو مراقبة قياسية مع محفزات التصعيد.'
  }

  return {
    riskLevel,
    expectedSpread: spreadPct,
    sentiment: input.baseSentiment,
    primaryDriver,
    primaryDriverAr,
    criticalTimeWindow,
    criticalTimeWindowAr,
    recommendedActions: generateActions(input, riskScore),
    explanation: generateExplanation(input),
    narrative
  }
}

/* -------------------------------------------------
   Export to Structured JSON (Phase 6)
   ------------------------------------------------- */
export function toSimulationJSON(decision: DecisionOutput, confidence: number, entities: string[]): Record<string, unknown> {
  return {
    scenario_title: decision.narrative.title,
    risk_level: decision.riskLevel,
    expected_spread: decision.expectedSpread + '%',
    sentiment: decision.sentiment,
    primary_driver: decision.primaryDriver,
    time_window: decision.criticalTimeWindow,
    explanation: decision.explanation.map(e => e.factor + ': ' + e.description),
    recommended_actions: decision.recommendedActions.map(a => '[' + a.priority.toUpperCase() + '] ' + a.action),
    confidence: (confidence * 100).toFixed(0) + '%',
    key_entities: entities
  }
    }
