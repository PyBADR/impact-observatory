"""
Scenario-Type-Keyed Action Registry.

Replaces the index-based SCENARIO_ACTION_MATRIX + flat _ACTION_TEMPLATES
that caused cross-scenario action leakage (e.g., CYBER scenarios receiving
"Declare force majeure on Hormuz contracts").

Design principles:
  1. Each action explicitly declares allowed_scenario_types
  2. Lookup is by scenario_type, not by template index
  3. Actions are semantically grouped by their operational domain
  4. No action can reach a scenario type it doesn't declare

Consumed by: decision_layer.py, action_policy.py
"""
from __future__ import annotations

from typing import TypedDict
from src.config import SCENARIO_TAXONOMY


class ActionTemplate(TypedDict):
    """Typed action template with explicit scenario-type scoping."""
    action_id: str
    sector: str
    owner: str
    owner_ar: str
    action_en: str
    action_ar: str
    base_urgency: float
    cost_usd: int
    regulatory_risk: float
    feasibility: float
    time_to_act_hours: int
    allowed_scenario_types: set[str]


# ── MARITIME Actions ────────────────────────────────────────────────────────

_MARITIME_ACTIONS: list[ActionTemplate] = [
    {
        "action_id": "MAR-001",
        "sector": "maritime",
        "owner": "Port Authority / هيئة الموانئ",
        "owner_ar": "هيئة الموانئ",
        "action_en": "Divert vessel traffic to Salalah and Ad Dammam; activate port congestion surge protocol",
        "action_ar": "تحويل حركة السفن إلى صلالة والدمام؛ تفعيل بروتوكول ازدحام الموانئ",
        "base_urgency": 0.90,
        "cost_usd": 350_000_000,
        "regulatory_risk": 0.60,
        "feasibility": 0.88,
        "time_to_act_hours": 3,
        "allowed_scenario_types": {"MARITIME"},
    },
    {
        "action_id": "MAR-002",
        "sector": "maritime",
        "owner": "Shipping Lines / خطوط الشحن",
        "owner_ar": "خطوط الشحن",
        "action_en": "Reroute 60% of tonnage via Cape of Good Hope; file surcharge notice to cargo owners",
        "action_ar": "إعادة توجيه 60% من الحمولة عبر رأس الرجاء الصالح؛ إخطار أصحاب البضائع بالرسوم الإضافية",
        "base_urgency": 0.85,
        "cost_usd": 900_000_000,
        "regulatory_risk": 0.55,
        "feasibility": 0.82,
        "time_to_act_hours": 8,
        "allowed_scenario_types": {"MARITIME"},
    },
    {
        "action_id": "MAR-003",
        "sector": "logistics",
        "owner": "Logistics Authority / هيئة اللوجستيات",
        "owner_ar": "هيئة اللوجستيات",
        "action_en": "Activate emergency warehousing capacity and redirect overland freight via Saudi rail network",
        "action_ar": "تفعيل طاقة التخزين الطارئة وإعادة توجيه الشحن البري عبر شبكة السكك الحديدية السعودية",
        "base_urgency": 0.78,
        "cost_usd": 180_000_000,
        "regulatory_risk": 0.45,
        "feasibility": 0.80,
        "time_to_act_hours": 12,
        "allowed_scenario_types": {"MARITIME"},
    },
    {
        "action_id": "MAR-004",
        "sector": "insurance",
        "owner": "Marine Insurance Desk / مكتب التأمين البحري",
        "owner_ar": "مكتب التأمين البحري",
        "action_en": "Issue hull and cargo war-risk premium adjustment; notify reinsurers of elevated loss corridor",
        "action_ar": "إصدار تعديل أقساط مخاطر الحرب للسفن والبضائع؛ إخطار معيدي التأمين بممر الخسائر المرتفع",
        "base_urgency": 0.75,
        "cost_usd": 200_000_000,
        "regulatory_risk": 0.85,
        "feasibility": 0.78,
        "time_to_act_hours": 12,
        "allowed_scenario_types": {"MARITIME"},
    },
    {
        "action_id": "MAR-005",
        "sector": "government",
        "owner": "GCC Maritime Coordination / التنسيق البحري الخليجي",
        "owner_ar": "التنسيق البحري الخليجي",
        "action_en": "Convene emergency GCC maritime coordination session; harmonize port access priorities across member states",
        "action_ar": "عقد جلسة تنسيق بحري طارئة لدول الخليج؛ تنسيق أولويات الوصول إلى الموانئ عبر الدول الأعضاء",
        "base_urgency": 0.72,
        "cost_usd": 0,
        "regulatory_risk": 0.90,
        "feasibility": 0.65,
        "time_to_act_hours": 24,
        "allowed_scenario_types": {"MARITIME"},
    },
]

# ── ENERGY Actions ──────────────────────────────────────────────────────────

_ENERGY_ACTIONS: list[ActionTemplate] = [
    {
        "action_id": "ENR-001",
        "sector": "energy",
        "owner": "National Oil Company / شركة النفط الوطنية",
        "owner_ar": "شركة النفط الوطنية",
        "action_en": "Activate strategic petroleum reserve drawdown and reroute exports via Red Sea corridor",
        "action_ar": "تفعيل سحب الاحتياطي البترولي الاستراتيجي وإعادة توجيه الصادرات عبر ممر البحر الأحمر",
        "base_urgency": 0.95,
        "cost_usd": 1_200_000_000,
        "regulatory_risk": 0.70,
        "feasibility": 0.85,
        "time_to_act_hours": 6,
        "allowed_scenario_types": {"ENERGY"},
    },
    {
        "action_id": "ENR-002",
        "sector": "energy",
        "owner": "Ministry of Energy / وزارة الطاقة",
        "owner_ar": "وزارة الطاقة",
        "action_en": "Declare force majeure on disrupted supply contracts; invoke IEA emergency sharing protocol",
        "action_ar": "الإعلان عن قوة قاهرة على عقود التوريد المتعطلة؛ تفعيل بروتوكول وكالة الطاقة الدولية للطوارئ",
        "base_urgency": 0.90,
        "cost_usd": 80_000_000,
        "regulatory_risk": 0.80,
        "feasibility": 0.80,
        "time_to_act_hours": 4,
        "allowed_scenario_types": {"ENERGY"},
    },
    {
        "action_id": "ENR-003",
        "sector": "energy",
        "owner": "OPEC+ Coordination / تنسيق أوبك+",
        "owner_ar": "تنسيق أوبك+",
        "action_en": "Request OPEC+ emergency production quota reallocation to compensate supply gap",
        "action_ar": "طلب إعادة تخصيص طارئة لحصص الإنتاج من أوبك+ لتعويض فجوة العرض",
        "base_urgency": 0.82,
        "cost_usd": 0,
        "regulatory_risk": 0.75,
        "feasibility": 0.60,
        "time_to_act_hours": 48,
        "allowed_scenario_types": {"ENERGY"},
    },
    {
        "action_id": "ENR-004",
        "sector": "banking",
        "owner": "Energy Finance Desk / مكتب تمويل الطاقة",
        "owner_ar": "مكتب تمويل الطاقة",
        "action_en": "Activate commodity hedging facilities and margin call buffer for energy-exposed bank portfolios",
        "action_ar": "تفعيل تسهيلات التحوط السلعي ومخزن طلب الهامش لمحافظ البنوك المعرضة للطاقة",
        "base_urgency": 0.80,
        "cost_usd": 500_000_000,
        "regulatory_risk": 0.65,
        "feasibility": 0.78,
        "time_to_act_hours": 6,
        "allowed_scenario_types": {"ENERGY"},
    },
    {
        "action_id": "ENR-005",
        "sector": "government",
        "owner": "Sovereign Wealth Fund / صندوق الثروة السيادي",
        "owner_ar": "صندوق الثروة السيادي",
        "action_en": "Activate counter-cyclical deployment facility; inject liquidity into energy-stressed equity segments",
        "action_ar": "تفعيل تسهيلات النشر المضادة للدورة الاقتصادية؛ ضخ السيولة في شرائح أسهم الطاقة المتعثرة",
        "base_urgency": 0.78,
        "cost_usd": 3_000_000_000,
        "regulatory_risk": 0.60,
        "feasibility": 0.75,
        "time_to_act_hours": 6,
        "allowed_scenario_types": {"ENERGY"},
    },
]

# ── LIQUIDITY Actions ───────────────────────────────────────────────────────

_LIQUIDITY_ACTIONS: list[ActionTemplate] = [
    {
        "action_id": "LIQ-001",
        "sector": "banking",
        "owner": "Central Bank / المصرف المركزي",
        "owner_ar": "المصرف المركزي",
        "action_en": "Activate emergency liquidity facility and raise overnight repo limits by 150bps",
        "action_ar": "تفعيل تسهيل السيولة الطارئ ورفع حدود إعادة الشراء الليلية بمقدار 150 نقطة أساس",
        "base_urgency": 0.92,
        "cost_usd": 500_000_000,
        "regulatory_risk": 0.85,
        "feasibility": 0.80,
        "time_to_act_hours": 4,
        "allowed_scenario_types": {"LIQUIDITY"},
    },
    {
        "action_id": "LIQ-002",
        "sector": "banking",
        "owner": "Systemically Important Banks / البنوك ذات الأهمية النظامية",
        "owner_ar": "البنوك ذات الأهمية النظامية",
        "action_en": "Invoke capital conservation buffer and suspend discretionary distributions",
        "action_ar": "تفعيل احتياطي صون رأس المال وتعليق التوزيعات التقديرية",
        "base_urgency": 0.85,
        "cost_usd": 0,
        "regulatory_risk": 0.90,
        "feasibility": 0.75,
        "time_to_act_hours": 6,
        "allowed_scenario_types": {"LIQUIDITY"},
    },
    {
        "action_id": "LIQ-003",
        "sector": "banking",
        "owner": "Banking Regulator / الجهة التنظيمية المصرفية",
        "owner_ar": "الجهة التنظيمية المصرفية",
        "action_en": "Issue liquidity stress disclosure to markets and activate BCBS crisis protocol",
        "action_ar": "إصدار إفصاح ضغط السيولة للأسواق وتفعيل بروتوكول أزمة لجنة بازل",
        "base_urgency": 0.78,
        "cost_usd": 50_000_000,
        "regulatory_risk": 0.95,
        "feasibility": 0.70,
        "time_to_act_hours": 8,
        "allowed_scenario_types": {"LIQUIDITY"},
    },
    {
        "action_id": "LIQ-004",
        "sector": "insurance",
        "owner": "Reinsurance Treaty Desk / مكتب معاهدات إعادة التأمين",
        "owner_ar": "مكتب معاهدات إعادة التأمين",
        "action_en": "File precautionary loss notification to reinsurers; reserve IFRS-17 claims uplift provisions",
        "action_ar": "تقديم إخطار خسارة احترازي لمعيدي التأمين؛ احتجاز مخصصات ارتفاع مطالبات IFRS-17",
        "base_urgency": 0.80,
        "cost_usd": 200_000_000,
        "regulatory_risk": 0.88,
        "feasibility": 0.78,
        "time_to_act_hours": 12,
        "allowed_scenario_types": {"LIQUIDITY"},
    },
    {
        "action_id": "LIQ-005",
        "sector": "government",
        "owner": "GCC Financial Stability Board / مجلس الاستقرار المالي الخليجي",
        "owner_ar": "مجلس الاستقرار المالي الخليجي",
        "action_en": "Convene emergency GCC financial stability council session and harmonise capital buffer releases",
        "action_ar": "عقد جلسة طارئة لمجلس الاستقرار المالي الخليجي وتنسيق الإفراج عن احتياطيات رأس المال",
        "base_urgency": 0.75,
        "cost_usd": 0,
        "regulatory_risk": 0.92,
        "feasibility": 0.68,
        "time_to_act_hours": 24,
        "allowed_scenario_types": {"LIQUIDITY"},
    },
]

# ── CYBER Actions ───────────────────────────────────────────────────────────

_CYBER_ACTIONS: list[ActionTemplate] = [
    {
        "action_id": "CYB-001",
        "sector": "infrastructure",
        "owner": "National Cyber Security Authority / الهيئة الوطنية للأمن السيبراني",
        "owner_ar": "الهيئة الوطنية للأمن السيبراني",
        "action_en": "Raise national cyber threat level to orange; isolate critical OT networks from public internet",
        "action_ar": "رفع مستوى التهديد السيبراني الوطني إلى البرتقالي؛ عزل شبكات التقنيات التشغيلية الحيوية",
        "base_urgency": 0.92,
        "cost_usd": 120_000_000,
        "regulatory_risk": 0.80,
        "feasibility": 0.85,
        "time_to_act_hours": 1,
        "allowed_scenario_types": {"CYBER"},
    },
    {
        "action_id": "CYB-002",
        "sector": "fintech",
        "owner": "Central Bank Payment System / نظام المدفوعات للبنك المركزي",
        "owner_ar": "نظام المدفوعات للبنك المركزي",
        "action_en": "Switch RTGS to high-priority-only mode; suspend non-critical SWIFT batch processing",
        "action_ar": "تحويل نظام التسوية الفورية إلى وضع الأولوية العالية فقط؛ تعليق معالجة SWIFT الدُفعية غير الحرجة",
        "base_urgency": 0.90,
        "cost_usd": 5_000_000,
        "regulatory_risk": 0.75,
        "feasibility": 0.90,
        "time_to_act_hours": 2,
        "allowed_scenario_types": {"CYBER"},
    },
    {
        "action_id": "CYB-003",
        "sector": "fintech",
        "owner": "Digital Finance Operators / مشغلو التمويل الرقمي",
        "owner_ar": "مشغلو التمويل الرقمي",
        "action_en": "Impose transaction velocity limits and activate fraud detection elevated-threshold regime",
        "action_ar": "فرض حدود سرعة المعاملات وتفعيل نظام العتبات المرتفعة للكشف عن الاحتيال",
        "base_urgency": 0.85,
        "cost_usd": 15_000_000,
        "regulatory_risk": 0.70,
        "feasibility": 0.88,
        "time_to_act_hours": 1,
        "allowed_scenario_types": {"CYBER"},
    },
    {
        "action_id": "CYB-004",
        "sector": "infrastructure",
        "owner": "Critical Infrastructure Operators / مشغلو البنية التحتية الحيوية",
        "owner_ar": "مشغلو البنية التحتية الحيوية",
        "action_en": "Activate business continuity plans; switch to backup power and redundant communication links",
        "action_ar": "تفعيل خطط استمرارية الأعمال؛ التحويل إلى الطاقة الاحتياطية وروابط الاتصال المتكررة",
        "base_urgency": 0.88,
        "cost_usd": 250_000_000,
        "regulatory_risk": 0.72,
        "feasibility": 0.87,
        "time_to_act_hours": 1,
        "allowed_scenario_types": {"CYBER"},
    },
    {
        "action_id": "CYB-005",
        "sector": "banking",
        "owner": "Banking CISO Council / مجلس أمن المعلومات المصرفي",
        "owner_ar": "مجلس أمن المعلومات المصرفي",
        "action_en": "Activate banking sector cyber incident response protocol; freeze external API integrations pending threat assessment",
        "action_ar": "تفعيل بروتوكول الاستجابة للحوادث السيبرانية في القطاع المصرفي؛ تجميد التكاملات الخارجية بانتظار تقييم التهديد",
        "base_urgency": 0.87,
        "cost_usd": 30_000_000,
        "regulatory_risk": 0.82,
        "feasibility": 0.80,
        "time_to_act_hours": 2,
        "allowed_scenario_types": {"CYBER"},
    },
]

# ── REGULATORY Actions ──────────────────────────────────────────────────────

_REGULATORY_ACTIONS: list[ActionTemplate] = [
    {
        "action_id": "REG-001",
        "sector": "government",
        "owner": "GCC Foreign Affairs Council / مجلس الشؤون الخارجية الخليجي",
        "owner_ar": "مجلس الشؤون الخارجية الخليجي",
        "action_en": "Activate GCC unified geopolitical risk protocol; issue cross-border travel and trade advisories",
        "action_ar": "تفعيل بروتوكول المخاطر الجيوسياسية الموحد لدول الخليج؛ إصدار إرشادات السفر والتجارة عبر الحدود",
        "base_urgency": 0.82,
        "cost_usd": 0,
        "regulatory_risk": 0.92,
        "feasibility": 0.65,
        "time_to_act_hours": 12,
        "allowed_scenario_types": {"REGULATORY"},
    },
    {
        "action_id": "REG-002",
        "sector": "government",
        "owner": "Regulatory Forbearance Committee / لجنة التسامح التنظيمي",
        "owner_ar": "لجنة التسامح التنظيمي",
        "action_en": "Issue temporary regulatory forbearance on capital and liquidity ratios for affected institutions",
        "action_ar": "إصدار تسامح تنظيمي مؤقت بشأن نسب رأس المال والسيولة للمؤسسات المتأثرة",
        "base_urgency": 0.78,
        "cost_usd": 0,
        "regulatory_risk": 0.95,
        "feasibility": 0.70,
        "time_to_act_hours": 24,
        "allowed_scenario_types": {"REGULATORY"},
    },
    {
        "action_id": "REG-003",
        "sector": "banking",
        "owner": "Central Bank / المصرف المركزي",
        "owner_ar": "المصرف المركزي",
        "action_en": "Activate cross-border capital flow monitoring and temporary limits on non-essential foreign transfers",
        "action_ar": "تفعيل مراقبة تدفقات رأس المال عبر الحدود وحدود مؤقتة على التحويلات الخارجية غير الأساسية",
        "base_urgency": 0.80,
        "cost_usd": 10_000_000,
        "regulatory_risk": 0.88,
        "feasibility": 0.72,
        "time_to_act_hours": 6,
        "allowed_scenario_types": {"REGULATORY"},
    },
    {
        "action_id": "REG-004",
        "sector": "insurance",
        "owner": "Insurance Regulator / هيئة التأمين",
        "owner_ar": "هيئة التأمين",
        "action_en": "Issue solvency watch list for insurers with >30% TIV in affected corridors; mandate stress test disclosure",
        "action_ar": "إصدار قائمة مراقبة الملاءة لشركات التأمين ذات التعرض >30% في الممرات المتأثرة؛ إلزام الإفصاح عن اختبار الإجهاد",
        "base_urgency": 0.72,
        "cost_usd": 10_000_000,
        "regulatory_risk": 0.92,
        "feasibility": 0.72,
        "time_to_act_hours": 16,
        "allowed_scenario_types": {"REGULATORY"},
    },
    {
        "action_id": "REG-005",
        "sector": "government",
        "owner": "Sovereign Wealth Fund / صندوق الثروة السيادي",
        "owner_ar": "صندوق الثروة السيادي",
        "action_en": "Activate counter-cyclical deployment facility; inject liquidity into stressed equity segments",
        "action_ar": "تفعيل تسهيلات النشر المضادة للدورة الاقتصادية؛ ضخ السيولة في شرائح الأسهم المتعثرة",
        "base_urgency": 0.75,
        "cost_usd": 3_000_000_000,
        "regulatory_risk": 0.60,
        "feasibility": 0.75,
        "time_to_act_hours": 6,
        "allowed_scenario_types": {"REGULATORY"},
    },
]

# ── CROSS-TYPE Actions (shared across 2+ types) ────────────────────────────

_CROSS_TYPE_ACTIONS: list[ActionTemplate] = [
    {
        "action_id": "XTP-001",
        "sector": "government",
        "owner": "GCC Financial Stability Board / مجلس الاستقرار المالي الخليجي",
        "owner_ar": "مجلس الاستقرار المالي الخليجي",
        "action_en": "Convene emergency GCC financial stability session; coordinate cross-border crisis response protocols",
        "action_ar": "عقد جلسة طارئة لمجلس الاستقرار المالي الخليجي؛ تنسيق بروتوكولات الاستجابة للأزمات عبر الحدود",
        "base_urgency": 0.75,
        "cost_usd": 0,
        "regulatory_risk": 0.90,
        "feasibility": 0.65,
        "time_to_act_hours": 24,
        "allowed_scenario_types": {"MARITIME", "ENERGY", "LIQUIDITY", "CYBER", "REGULATORY"},
    },
]


# ── Assembled Registry ──────────────────────────────────────────────────────

ALL_ACTIONS: list[ActionTemplate] = (
    _MARITIME_ACTIONS
    + _ENERGY_ACTIONS
    + _LIQUIDITY_ACTIONS
    + _CYBER_ACTIONS
    + _REGULATORY_ACTIONS
    + _CROSS_TYPE_ACTIONS
)

# Pre-index by scenario type for O(1) lookup
SCENARIO_ACTION_REGISTRY: dict[str, list[ActionTemplate]] = {}
for _action in ALL_ACTIONS:
    for _stype in _action["allowed_scenario_types"]:
        SCENARIO_ACTION_REGISTRY.setdefault(_stype, []).append(_action)


# ── Public API ──────────────────────────────────────────────────────────────

def get_actions_for_scenario_type(scenario_type: str) -> list[ActionTemplate]:
    """
    Return all actions allowed for the given scenario type.

    If scenario_type is unknown, returns all cross-type actions only.
    """
    if scenario_type in SCENARIO_ACTION_REGISTRY:
        return SCENARIO_ACTION_REGISTRY[scenario_type]
    # Unknown type: return only cross-type (universal) actions
    return [a for a in ALL_ACTIONS if len(a["allowed_scenario_types"]) >= 4]


def get_actions_for_scenario_id(scenario_id: str) -> list[ActionTemplate]:
    """
    Resolve scenario_id → scenario_type → actions.

    Uses SCENARIO_TAXONOMY for resolution.
    """
    scenario_type = SCENARIO_TAXONOMY.get(scenario_id, "")
    return get_actions_for_scenario_type(scenario_type)
