"""
═══════════════════════════════════════════════════════════════════════════════
IMPACT OBSERVATORY — DECISION INTELLIGENCE ENGINE (Python Implementation)
═══════════════════════════════════════════════════════════════════════════════

Mathematical Model:
   DPS = w1·E_sys + w2·PropDepth + w3·SectorSpread + w4·Exposure + w5·StabilityRisk
   APS(action) = ImpactReduction(action) · Confidence(action) / Cost(action)
   ME = (Loss_Before - Loss_After) / Loss_Before
   Urgency = f(shockClass, E_sys, corridorDependency)
   DC = ModelConfidence · DataReliability · ScenarioCoherence

Contract: every scenario run must produce a DecisionResult with
   recommended actions, urgency, confidence, mitigation effectiveness,
   and full Arabic translations.
═══════════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Literal
import math

from .gcc_constants import DPS_WEIGHTS, DPS_NORMALIZATION, APS_COST_MULTIPLIER, DECISION_LIMITS
from .propagation_engine import PropagationResult, SectorImpact


# ── Type Definitions ──

UrgencyLevel = Literal['flash', 'immediate', 'short_term', 'medium_term']
ActionDomain = Literal['logistics', 'ports', 'aviation', 'utilities', 'banking', 'insurance', 'food_security', 'sovereign', 'communication']
CostLevel = Literal['low', 'medium', 'high']
ShockClass = Literal['critical', 'severe', 'moderate', 'low']
Stage = Literal['initial', 'cascading', 'saturated']


# ── Domain Labels ──

DOMAIN_AR: Dict[ActionDomain, str] = {
    'logistics': 'اللوجستيات',
    'ports': 'الموانئ',
    'aviation': 'الطيران',
    'utilities': 'المرافق',
    'banking': 'البنوك',
    'insurance': 'التأمين',
    'food_security': 'الأمن الغذائي',
    'sovereign': 'الاستجابة السيادية',
    'communication': 'الاتصالات والاستقرار',
}

URGENCY_AR: Dict[UrgencyLevel, str] = {
    'flash': 'فوري عاجل',
    'immediate': 'فوري',
    'short_term': 'قصير المدى',
    'medium_term': 'متوسط المدى',
}

COST_AR: Dict[CostLevel, str] = {
    'low': 'منخفض',
    'medium': 'متوسط',
    'high': 'مرتفع',
}


# ── Data Classes ──

@dataclass
class RecommendedAction:
    """Individual recommended action with priority and urgency."""
    id: str
    domain: ActionDomain
    domainAr: str
    action: str
    actionAr: str
    priority: float        # APS score 0–1
    urgency: UrgencyLevel
    urgencyAr: str
    timeframe: str         # e.g. "0–6h", "24–72h"
    timeframeAr: str
    expectedReduction: float  # fraction of loss this action mitigates
    cost: CostLevel
    costAr: str
    tradeoff: str
    tradeoffAr: str
    confidence: float      # 0–1


@dataclass
class ResourcePriority:
    """Resource allocation priority."""
    resource: str
    resourceAr: str
    priority: float
    reason: str
    reasonAr: str


@dataclass
class SectorActionGroup:
    """Actions grouped by domain/sector."""
    sector: str
    sectorAr: str
    actions: List[RecommendedAction]


@dataclass
class DecisionResult:
    """Complete decision intelligence result."""
    # Core scores
    decisionPressureScore: float   # DPS 0–1
    urgencyLevel: UrgencyLevel
    urgencyLevelAr: str
    decisionConfidence: float      # DC 0–1

    # Loss analysis
    expectedLossBefore: float      # $B
    expectedLossAfter: float       # $B after mitigations
    mitigationEffectiveness: float # ME 0–1

    # Narrative
    decisionSummary: str
    decisionSummaryAr: str
    whyTheseActions: str
    whyTheseActionsAr: str

    # Actions
    recommendedActions: List[RecommendedAction]
    immediateActions: List[RecommendedAction]    # 0–6h
    shortTermActions: List[RecommendedAction]    # 24–72h

    # Sector-specific
    sectorActions: List[SectorActionGroup]

    # Resource priorities
    resourcePriorities: List[ResourcePriority]


@dataclass
class ScientistState:
    """Scientist input passed from UI."""
    energy: float
    confidence: float
    uncertainty: float
    regionalStress: float
    shockClass: ShockClass
    stage: Stage
    propagationDepth: float
    totalExposure: float
    dominantSector: Optional[SectorImpact] = None


@dataclass
class ActionTemplate:
    """Template for a response action."""
    domain: ActionDomain
    action: str
    actionAr: str
    timeframe: str
    timeframeAr: str
    expectedReduction: float
    cost: CostLevel
    tradeoff: str
    tradeoffAr: str
    relevantScenarios: List[str]
    relevantSectors: List[str]


# ══════════════════════════════════════════════════════════════════════════════
# ACTION CATALOG (20 TEMPLATES EXACT FROM TYPESCRIPT)
# ══════════════════════════════════════════════════════════════════════════════

ACTION_CATALOG: List[ActionTemplate] = [
    # ── LOGISTICS / PORTS ──
    ActionTemplate(
        domain='logistics',
        action='Activate Fujairah bypass for Hormuz-dependent cargo',
        actionAr='تفعيل مسار الفجيرة البديل للشحن المعتمد على هرمز',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.12,
        cost='medium',
        tradeoff='Higher per-unit shipping cost; limited Fujairah throughput capacity',
        tradeoffAr='تكلفة شحن أعلى لكل وحدة؛ سعة محدودة في الفجيرة',
        relevantScenarios=['hormuz', 'port', 'military', 'shipping'],
        relevantSectors=['infrastructure', 'geography'],
    ),
    ActionTemplate(
        domain='ports',
        action='Extend port operating hours to 24/7 and activate overflow berths',
        actionAr='تمديد ساعات عمل الموانئ إلى ٢٤/٧ وتفعيل أرصفة الفائض',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.08,
        cost='medium',
        tradeoff='Increased labor costs; accelerated equipment wear',
        tradeoffAr='زيادة تكاليف العمالة؛ تسارع استهلاك المعدات',
        relevantScenarios=['port', 'hormuz', 'jebel_ali', 'congestion'],
        relevantSectors=['infrastructure'],
    ),
    ActionTemplate(
        domain='logistics',
        action='Pre-position 90-day strategic food reserves at GCC distribution hubs',
        actionAr='تخزين احتياطي غذائي استراتيجي لـ٩٠ يومًا في مراكز التوزيع الخليجية',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.10,
        cost='high',
        tradeoff='Capital lockup in inventory; storage infrastructure required',
        tradeoffAr='تجميد رأس المال في المخزون؛ يتطلب بنية تخزين',
        relevantScenarios=['food', 'hormuz', 'port', 'shipping'],
        relevantSectors=['economy', 'society'],
    ),
    # ── AVIATION ──
    ActionTemplate(
        domain='aviation',
        action='Negotiate emergency overflight rights with adjacent airspace authorities',
        actionAr='التفاوض على حقوق تحليق طارئة مع سلطات المجال الجوي المجاورة',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.09,
        cost='low',
        tradeoff='Political friction; reciprocity obligations',
        tradeoffAr='احتكاك سياسي؛ التزامات المعاملة بالمثل',
        relevantScenarios=['airspace', 'flight', 'escalation', 'military'],
        relevantSectors=['infrastructure', 'economy'],
    ),
    ActionTemplate(
        domain='aviation',
        action='Cap ticket prices and activate airline subsidy mechanism',
        actionAr='تحديد سقف أسعار التذاكر وتفعيل آلية دعم شركات الطيران',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.06,
        cost='high',
        tradeoff='Fiscal cost; may distort airline competition',
        tradeoffAr='تكلفة مالية؛ قد يشوه المنافسة بين شركات الطيران',
        relevantScenarios=['airspace', 'flight', 'hajj'],
        relevantSectors=['economy', 'society'],
    ),
    # ── UTILITIES ──
    ActionTemplate(
        domain='utilities',
        action='Activate emergency power interconnect with neighboring GCC grids',
        actionAr='تفعيل الربط الكهربائي الطارئ مع شبكات دول الخليج المجاورة',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.11,
        cost='medium',
        tradeoff='Cross-border dependency; interconnect capacity limits',
        tradeoffAr='اعتماد عبر الحدود؛ حدود سعة الربط',
        relevantScenarios=['grid', 'water', 'summer', 'utility'],
        relevantSectors=['infrastructure'],
    ),
    ActionTemplate(
        domain='utilities',
        action='Deploy mobile desalination units to critical population centers',
        actionAr='نشر وحدات تحلية متنقلة في المراكز السكانية الحيوية',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.07,
        cost='high',
        tradeoff='Limited output capacity; logistics of deployment',
        tradeoffAr='سعة إنتاج محدودة؛ تحديات النقل والتوزيع',
        relevantScenarios=['water', 'grid', 'summer', 'utility'],
        relevantSectors=['infrastructure', 'society'],
    ),
    # ── BANKING / FINANCE ──
    ActionTemplate(
        domain='banking',
        action='Central bank injects emergency liquidity via repo facility',
        actionAr='البنك المركزي يضخ سيولة طارئة عبر تسهيلات إعادة الشراء',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.10,
        cost='medium',
        tradeoff='Inflation risk; moral hazard for banks',
        tradeoffAr='مخاطر التضخم؛ خطر أخلاقي للبنوك',
        relevantScenarios=['liquidity', 'fx', 'banking', 'insurance', 'repricing'],
        relevantSectors=['finance'],
    ),
    ActionTemplate(
        domain='banking',
        action='Activate capital control circuit breakers on Tadawul/ADX',
        actionAr='تفعيل قواطع التداول الآلية في تداول/سوق أبوظبي',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.05,
        cost='low',
        tradeoff='Reduced market liquidity; investor confidence impact',
        tradeoffAr='انخفاض سيولة السوق؛ تأثير على ثقة المستثمرين',
        relevantScenarios=['fx', 'liquidity', 'escalation'],
        relevantSectors=['finance'],
    ),
    # ── INSURANCE ──
    ActionTemplate(
        domain='insurance',
        action='Issue emergency reinsurance call and activate catastrophe bonds',
        actionAr='إصدار نداء إعادة تأمين طارئ وتفعيل سندات الكوارث',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.08,
        cost='high',
        tradeoff='Premium spikes for 18+ months; capacity contraction',
        tradeoffAr='ارتفاع الأقساط لأكثر من ١٨ شهرًا؛ تقلص السعة',
        relevantScenarios=['insurance', 'repricing', 'hormuz', 'grid'],
        relevantSectors=['finance'],
    ),
    # ── FOOD SECURITY ──
    ActionTemplate(
        domain='food_security',
        action='Activate bilateral food supply agreements with strategic partners',
        actionAr='تفعيل اتفاقيات الإمداد الغذائي الثنائية مع الشركاء الاستراتيجيين',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.09,
        cost='medium',
        tradeoff='Geopolitical obligations; premium pricing',
        tradeoffAr='التزامات جيوسياسية؛ أسعار مرتفعة',
        relevantScenarios=['food', 'hormuz', 'port'],
        relevantSectors=['economy', 'society'],
    ),
    ActionTemplate(
        domain='food_security',
        action='Implement temporary price controls on essential commodities',
        actionAr='تطبيق ضوابط أسعار مؤقتة على السلع الأساسية',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.04,
        cost='low',
        tradeoff='Supply distortion; black market risk',
        tradeoffAr='تشوه العرض؛ مخاطر السوق السوداء',
        relevantScenarios=['food', 'hormuz'],
        relevantSectors=['society', 'economy'],
    ),
    # ── SOVEREIGN ──
    ActionTemplate(
        domain='sovereign',
        action='Convene GCC Emergency Coordination Council',
        actionAr='عقد مجلس التنسيق الطارئ لدول مجلس التعاون',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.06,
        cost='low',
        tradeoff='Political consensus delay; sovereignty concerns',
        tradeoffAr='تأخر التوافق السياسي؛ مخاوف السيادة',
        relevantScenarios=['hormuz', 'escalation', 'military', 'grid'],
        relevantSectors=['geography'],
    ),
    ActionTemplate(
        domain='sovereign',
        action='Activate strategic petroleum reserve drawdown',
        actionAr='تفعيل سحب الاحتياطي النفطي الاستراتيجي',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.11,
        cost='high',
        tradeoff='Depletes strategic buffer; recovery time 6–12 months',
        tradeoffAr='يستنفد المخزون الاستراتيجي؛ وقت التعافي ٦–١٢ شهرًا',
        relevantScenarios=['hormuz', 'escalation', 'fx'],
        relevantSectors=['economy', 'geography'],
    ),
    ActionTemplate(
        domain='sovereign',
        action='Restructure mega-project timelines and activate force majeure clauses',
        actionAr='إعادة هيكلة جداول المشاريع الكبرى وتفعيل شروط القوة القاهرة',
        timeframe='24–72h',
        timeframeAr='٢٤–٧٢ ساعة',
        expectedReduction=0.07,
        cost='medium',
        tradeoff='Contractor disputes; investor confidence; timeline slippage',
        tradeoffAr='نزاعات المقاولين؛ ثقة المستثمرين؛ تأخر الجداول الزمنية',
        relevantScenarios=['vision', 'mega', 'liquidity'],
        relevantSectors=['economy', 'finance'],
    ),
    # ── COMMUNICATION / PUBLIC STABILITY ──
    ActionTemplate(
        domain='communication',
        action='Launch coordinated public communication campaign across GCC media',
        actionAr='إطلاق حملة تواصل عام منسقة عبر وسائل الإعلام الخليجية',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.05,
        cost='low',
        tradeoff='Message control risk; credibility if situation worsens',
        tradeoffAr='مخاطر السيطرة على الرسالة؛ المصداقية إذا تفاقم الوضع',
        relevantScenarios=['hormuz', 'escalation', 'food', 'grid', 'hajj', 'military'],
        relevantSectors=['society'],
    ),
    ActionTemplate(
        domain='communication',
        action='Deploy social media monitoring and counter-misinformation taskforce',
        actionAr='نشر فريق مراقبة وسائل التواصل ومكافحة المعلومات المضللة',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.03,
        cost='low',
        tradeoff='Resource diversion; free speech concerns',
        tradeoffAr='تحويل الموارد؛ مخاوف حرية التعبير',
        relevantScenarios=['escalation', 'hormuz', 'food', 'hajj'],
        relevantSectors=['society'],
    ),
    # ── HAJJ ──
    ActionTemplate(
        domain='logistics',
        action='Activate Hajj contingency routing via King Fahd Causeway and land corridors',
        actionAr='تفعيل المسارات البديلة للحج عبر جسر الملك فهد والممرات البرية',
        timeframe='0–6h',
        timeframeAr='٠–٦ ساعات',
        expectedReduction=0.08,
        cost='medium',
        tradeoff='Congestion on land routes; accommodation redistribution needed',
        tradeoffAr='ازدحام المسارات البرية؛ يتطلب إعادة توزيع الإقامة',
        relevantScenarios=['hajj', 'airspace', 'flight'],
        relevantSectors=['infrastructure', 'society'],
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# CORE COMPUTATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def compute_dps(
    energy: float,
    depth: float,
    sector_spread: float,
    exposure: float,
    stability_risk: float,
) -> float:
    """
    Compute Decision Pressure Score (DPS) using weighted formula.

    DPS = w1·E_sys + w2·PropDepth + w3·SectorSpread + w4·Exposure + w5·StabilityRisk

    Weights calibrated for GCC risk landscape:
      w1 = 0.25  # system energy
      w2 = 0.15  # propagation depth
      w3 = 0.20  # sector spread
      w4 = 0.25  # exposure
      w5 = 0.15  # public stability risk

    Normalization:
      Energy:    15 (high-energy system)
      Depth:     8  (deep cascade)
      Spread:    5  (layers)
      Exposure:  80 ($B extreme)
      Stability: 1  (bounded)
    """
    w1 = 0.25
    w2 = 0.15
    w3 = 0.20
    w4 = 0.25
    w5 = 0.15

    norm_energy = min(energy / 15, 1)
    norm_depth = min(depth / 8, 1)
    norm_spread = min(sector_spread / 5, 1)
    norm_exposure = min(exposure / 80, 1)
    norm_stability = min(stability_risk, 1)

    return (
        w1 * norm_energy
        + w2 * norm_depth
        + w3 * norm_spread
        + w4 * norm_exposure
        + w5 * norm_stability
    )


def compute_urgency(
    shock_class: ShockClass,
    energy: float,
    stage: Stage,
    dps: float,
) -> UrgencyLevel:
    """
    Determine urgency level from system state.

    Priority hierarchy:
      1. flash:       shockClass == 'critical' OR (energy > 10 AND stage == 'saturated')
      2. immediate:   shockClass == 'severe' OR dps > 0.65 OR stage == 'cascading'
      3. short_term:  dps > 0.35 OR shockClass == 'moderate'
      4. medium_term: otherwise
    """
    if shock_class == 'critical' or (energy > 10 and stage == 'saturated'):
        return 'flash'
    if shock_class == 'severe' or dps > 0.65 or stage == 'cascading':
        return 'immediate'
    if dps > 0.35 or shock_class == 'moderate':
        return 'short_term'
    return 'medium_term'


def compute_decision_confidence(
    model_confidence: float,
    sector_spread: float,
    depth: float,
) -> float:
    """
    Compute Decision Confidence (DC).

    DC = ModelConfidence · DataReliability · ScenarioCoherence

    Data reliability degrades with more affected sectors (more uncertainty):
      DataReliability = max(0.3, 1 - sectorSpread * 0.08)

    Scenario coherence: deeper propagation = more complex = lower coherence:
      ScenarioCoherence = max(0.4, 1 - depth * 0.06)
    """
    data_reliability = max(0.3, 1 - (sector_spread * 0.08))
    scenario_coherence = max(0.4, 1 - (depth * 0.06))
    return model_confidence * data_reliability * scenario_coherence


def match_actions(
    scenario_id: str,
    affected_sectors: List[SectorImpact],
    dps: float,
    urgency: UrgencyLevel,
    dc: float,
) -> List[RecommendedAction]:
    """
    Match and score actions based on scenario and sector context.

    Scoring (APS):
      costMultiplier = 1.0 (low) | 0.7 (medium) | 0.4 (high)
      reductionScore = expectedReduction * dc * costMultiplier
      timeBoost = 0.15 if (urgency flash|immediate) AND timeframe == '0–6h' else 0
      priority = min(reductionScore + timeBoost, 1)
    """
    sector_layers = set(s.sector for s in affected_sectors)
    scenario_lower = scenario_id.lower()

    # Filter actions by scenario keyword or affected sector
    matched = [
        t for t in ACTION_CATALOG
        if any(kw in scenario_lower for kw in t.relevantScenarios)
        or any(s in sector_layers for s in t.relevantSectors)
    ]

    recommended_actions = []
    for i, template in enumerate(matched):
        # APS = ImpactReduction * Confidence / Cost
        cost_multiplier = APS_COST_MULTIPLIER.get(template.cost, 0.7)
        reduction_score = template.expectedReduction * dc * cost_multiplier

        # Boost priority for urgent timeframe matches
        time_boost = 0.15 if (urgency in ['flash', 'immediate']) and template.timeframe == '0–6h' else 0
        priority = min(reduction_score + time_boost, 1)

        # Determine action-level urgency
        action_urgency: UrgencyLevel = (
            ('flash' if dps > 0.6 else 'immediate')
            if template.timeframe == '0–6h'
            else 'short_term'
        )

        # Confidence adjusted for cost
        action_confidence = dc * (1.0 if template.cost == 'low' else 0.85)

        recommended_actions.append(
            RecommendedAction(
                id=f'action_{i}',
                domain=template.domain,
                domainAr=DOMAIN_AR[template.domain],
                action=template.action,
                actionAr=template.actionAr,
                priority=priority,
                urgency=action_urgency,
                urgencyAr=URGENCY_AR[action_urgency],
                timeframe=template.timeframe,
                timeframeAr=template.timeframeAr,
                expectedReduction=template.expectedReduction,
                cost=template.cost,
                costAr=COST_AR[template.cost],
                tradeoff=template.tradeoff,
                tradeoffAr=template.tradeoffAr,
                confidence=action_confidence,
            )
        )

    # Sort by priority descending
    recommended_actions.sort(key=lambda a: a.priority, reverse=True)
    return recommended_actions


def generate_summary(
    scenario_id: str,
    shock_class: ShockClass,
    stage: Stage,
    exposure: float,
    urgency: UrgencyLevel,
    top_actions: List[RecommendedAction],
    dominant_sector: Optional[SectorImpact],
) -> dict:
    """Generate bilingual decision summary narrative."""
    sector_en = dominant_sector.sector_label if dominant_sector else 'multiple sectors'
    top_action_en = top_actions[0].action if top_actions else 'assess situation'
    top_action_ar = top_actions[0].actionAr if top_actions else 'تقييم الوضع'

    # English
    urgency_str = urgency.replace('_', ' ')
    domains_count = len(set(a.domain for a in top_actions))
    en = (
        f'{shock_class.upper()} shock detected in {stage} stage. '
        f'System exposure: ${exposure:.1f}B across {sector_en}. '
        f'Urgency: {urgency_str}. '
        f'Priority action: {top_action_en}. '
        f'{len(top_actions)} recommended actions identified across {domains_count} domains.'
    )

    # Arabic
    shock_ar = {
        'critical': 'حرج',
        'severe': 'شديد',
        'moderate': 'متوسط',
        'low': 'منخفض',
    }.get(shock_class, shock_class)

    stage_ar = {
        'initial': 'أولي',
        'cascading': 'متسلسل',
        'saturated': 'مشبع',
    }.get(stage, stage)

    urgency_ar = URGENCY_AR[urgency]
    sector_label_ar = dominant_sector.sector_label if dominant_sector else 'قطاعات متعددة'

    ar = (
        f'تم رصد صدمة {shock_ar} في مرحلة {stage_ar}. '
        f'التعرض: ${exposure:.1f} مليار عبر {sector_label_ar}. '
        f'الاستعجال: {urgency_ar}. '
        f'الإجراء ذو الأولوية: {top_action_ar}. '
        f'تم تحديد {len(top_actions)} إجراء موصى به عبر {domains_count} مجالات.'
    )

    return {'en': en, 'ar': ar}


def generate_why_actions(
    dps: float,
    shock_class: ShockClass,
    top_actions: List[RecommendedAction],
    me: float,
) -> dict:
    """Generate bilingual explanation of why these actions were chosen."""
    # Get top 5 unique domains
    domains: List[ActionDomain] = list(dict.fromkeys(a.domain for a in top_actions[:5]))
    domains_en = ', '.join(d.replace('_', ' ') for d in domains)
    domains_ar = '، '.join(DOMAIN_AR.get(d, d) for d in domains)

    # English
    en = (
        f'Decision pressure score ({dps * 100:.0f}%) and {shock_class} shock classification indicate '
        f'concentrated risk requiring multi-domain response across {domains_en}. '
        f'Combined mitigation effectiveness: {me * 100:.0f}% loss reduction achievable.'
    )

    # Arabic
    shock_ar = {
        'critical': 'الحرج',
        'severe': 'الشديد',
        'moderate': 'المتوسط',
        'low': 'المنخفض',
    }.get(shock_class, shock_class)

    ar = (
        f'درجة ضغط القرار ({dps * 100:.0f}%) وتصنيف الصدمة {shock_ar} '
        f'يشيران إلى مخاطر مركزة تتطلب استجابة متعددة المجالات عبر {domains_ar}. '
        f'فعالية التخفيف المجمعة: إمكانية تقليل الخسائر بنسبة {me * 100:.0f}%.'
    )

    return {'en': en, 'ar': ar}


def compute_resource_priorities(
    actions: List[RecommendedAction],
    shock_class: ShockClass,
    scenario_id: str,
) -> List[ResourcePriority]:
    """Compute resource allocation priorities based on recommended actions."""
    priorities: List[ResourcePriority] = []

    # Count actions by domain
    domain_counts: Dict[ActionDomain, int] = {}
    for action in actions:
        domain_counts[action.domain] = domain_counts.get(action.domain, 0) + 1

    # Maritime & ports
    if 'logistics' in domain_counts or 'ports' in domain_counts:
        priorities.append(
            ResourcePriority(
                resource='Maritime & Port Operations',
                resourceAr='العمليات البحرية والموانئ',
                priority=0.95 if shock_class == 'critical' else 0.75,
                reason='Port throughput and shipping rerouting require immediate coordination',
                reasonAr='إنتاجية الموانئ وإعادة توجيه الشحن تتطلب تنسيقًا فوريًا',
            )
        )

    # Aviation
    if 'aviation' in domain_counts:
        priorities.append(
            ResourcePriority(
                resource='Aviation Coordination',
                resourceAr='تنسيق الطيران',
                priority=0.90 if ('airspace' in scenario_id or 'flight' in scenario_id) else 0.60,
                reason='Airspace management and airline capacity reallocation',
                reasonAr='إدارة المجال الجوي وإعادة تخصيص سعة شركات الطيران',
            )
        )

    # Finance
    if 'banking' in domain_counts or 'insurance' in domain_counts:
        priorities.append(
            ResourcePriority(
                resource='Financial Stability Unit',
                resourceAr='وحدة الاستقرار المالي',
                priority=0.90 if shock_class == 'critical' else 0.70,
                reason='Central bank coordination and market circuit breakers',
                reasonAr='تنسيق البنك المركزي وقواطع السوق',
            )
        )

    # Utilities
    if 'utilities' in domain_counts:
        priorities.append(
            ResourcePriority(
                resource='GCC Grid Operations Center',
                resourceAr='مركز عمليات الشبكة الخليجية',
                priority=0.85,
                reason='Power and water continuity across interconnected grids',
                reasonAr='استمرارية الكهرباء والمياه عبر الشبكات المترابطة',
            )
        )

    # Communication
    if 'communication' in domain_counts:
        priorities.append(
            ResourcePriority(
                resource='Crisis Communications Team',
                resourceAr='فريق اتصالات الأزمات',
                priority=0.80,
                reason='Public messaging and social media monitoring',
                reasonAr='الرسائل العامة ومراقبة وسائل التواصل الاجتماعي',
            )
        )

    # Food security
    if 'food_security' in domain_counts:
        priorities.append(
            ResourcePriority(
                resource='Food Security Directorate',
                resourceAr='مديرية الأمن الغذائي',
                priority=0.85,
                reason='Supply chain activation and price stabilization',
                reasonAr='تفعيل سلسلة الإمداد واستقرار الأسعار',
            )
        )

    # Sort by priority descending
    priorities.sort(key=lambda x: x.priority, reverse=True)
    return priorities


# ══════════════════════════════════════════════════════════════════════════════
# MAIN DECISION COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def compute_decision(
    propagation: PropagationResult,
    engineer_result: Optional[Any],
    scientist: ScientistState,
    scenario_id: str,
) -> DecisionResult:
    """
    Main orchestrator: compute complete decision intelligence result.

    Steps:
      1. Compute DPS from scientist state
      2. Determine urgency level
      3. Calculate decision confidence
      4. Match and score actions
      5. Compute mitigation effectiveness (ME)
      6. Group actions by domain and timeframe
      7. Compute resource priorities
      8. Generate bilingual narratives
      9. Return complete DecisionResult
    """
    # Extract state
    energy = scientist.energy
    confidence = scientist.confidence
    shock_class = scientist.shockClass
    stage = scientist.stage
    propagation_depth = scientist.propagationDepth
    total_exposure = scientist.totalExposure
    regional_stress = scientist.regionalStress
    dominant_sector = scientist.dominantSector

    sector_spread = len(propagation.affected_sectors)

    # ── Core Scores ──
    dps = compute_dps(energy, propagation_depth, sector_spread, total_exposure, regional_stress)
    urgency = compute_urgency(shock_class, energy, stage, dps)
    dc = compute_decision_confidence(confidence, sector_spread, propagation_depth)

    # ── Match Actions ──
    all_actions = match_actions(scenario_id, propagation.affected_sectors, dps, urgency, dc)
    immediate_actions = [a for a in all_actions if a.timeframe == '0–6h']
    short_term_actions = [a for a in all_actions if a.timeframe == '24–72h']

    # ── Mitigation Effectiveness ──
    combined_reduction = sum(a.expectedReduction for a in all_actions)
    me = min(combined_reduction, DECISION_LIMITS.get('maxMarginalEffectiveness', 0.85))
    expected_loss_after = total_exposure * (1 - me)

    # ── Sector Actions (grouped by domain) ──
    sector_map: Dict[ActionDomain, List[RecommendedAction]] = {}
    for action in all_actions:
        if action.domain not in sector_map:
            sector_map[action.domain] = []
        sector_map[action.domain].append(action)

    sector_actions = [
        SectorActionGroup(
            sector=domain.replace('_', ' '),
            sectorAr=DOMAIN_AR.get(domain, domain),
            actions=actions,
        )
        for domain, actions in sector_map.items()
    ]

    # ── Resource Priorities ──
    resource_priorities = compute_resource_priorities(all_actions, shock_class, scenario_id)

    # ── Narratives ──
    summary = generate_summary(scenario_id, shock_class, stage, total_exposure, urgency, all_actions, dominant_sector)
    why_actions = generate_why_actions(dps, shock_class, all_actions, me)

    return DecisionResult(
        decisionPressureScore=dps,
        urgencyLevel=urgency,
        urgencyLevelAr=URGENCY_AR[urgency],
        decisionConfidence=dc,
        expectedLossBefore=total_exposure,
        expectedLossAfter=expected_loss_after,
        mitigationEffectiveness=me,
        decisionSummary=summary['en'],
        decisionSummaryAr=summary['ar'],
        whyTheseActions=why_actions['en'],
        whyTheseActionsAr=why_actions['ar'],
        recommendedActions=all_actions,
        immediateActions=immediate_actions,
        shortTermActions=short_term_actions,
        sectorActions=sector_actions,
        resourcePriorities=resource_priorities,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SERIALIZATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def result_to_dict(result: DecisionResult) -> Dict[str, Any]:
    """Convert DecisionResult to JSON-serializable dictionary."""
    return {
        'decisionPressureScore': result.decisionPressureScore,
        'urgencyLevel': result.urgencyLevel,
        'urgencyLevelAr': result.urgencyLevelAr,
        'decisionConfidence': result.decisionConfidence,
        'expectedLossBefore': result.expectedLossBefore,
        'expectedLossAfter': result.expectedLossAfter,
        'mitigationEffectiveness': result.mitigationEffectiveness,
        'decisionSummary': result.decisionSummary,
        'decisionSummaryAr': result.decisionSummaryAr,
        'whyTheseActions': result.whyTheseActions,
        'whyTheseActionsAr': result.whyTheseActionsAr,
        'recommendedActions': [asdict(a) for a in result.recommendedActions],
        'immediateActions': [asdict(a) for a in result.immediateActions],
        'shortTermActions': [asdict(a) for a in result.shortTermActions],
        'sectorActions': [
            {
                'sector': sa.sector,
                'sectorAr': sa.sectorAr,
                'actions': [asdict(a) for a in sa.actions],
            }
            for sa in result.sectorActions
        ],
        'resourcePriorities': [asdict(rp) for rp in result.resourcePriorities],
    }
