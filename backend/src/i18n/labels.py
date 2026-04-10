"""Impact Observatory — مرصد الأثر — Bilingual Labels (EN/AR).

All user-facing labels for the dashboard and reports.
"""

from __future__ import annotations

LABELS: dict[str, dict[str, str]] = {
    "headline_loss": {
        "en": "Headline Loss",
        "ar": "إجمالي الخسارة",
    },
    "peak_day": {
        "en": "Peak Impact Day",
        "ar": "يوم الذروة",
    },
    "banking_stress": {
        "en": "Banking Stress",
        "ar": "ضغط القطاع البنكي",
    },
    "insurance_stress": {
        "en": "Insurance Stress",
        "ar": "ضغط التأمين",
    },
    "fintech_stress": {
        "en": "Fintech Stress",
        "ar": "اضطراب الفنتك",
    },
    "financial_impact": {
        "en": "Financial Impact",
        "ar": "الأثر المالي",
    },
    "severity_code": {
        "en": "Severity Code",
        "ar": "مستوى الشدة",
    },
    "decision_actions": {
        "en": "Decision Actions",
        "ar": "الإجراءات المقترحة",
    },
    "time_to_failure": {
        "en": "Time to Failure",
        "ar": "وقت الانهيار",
    },
    "time_to_liquidity_breach": {
        "en": "Time to Liquidity Breach",
        "ar": "الوقت إلى كسر السيولة",
    },
    "time_to_insurance_failure": {
        "en": "Time to Insurance Failure",
        "ar": "الوقت إلى فشل التأمين",
    },
    "time_to_insolvency": {
        "en": "Time to Insolvency",
        "ar": "وقت الإفلاس",
    },
    "time_to_payment_failure": {
        "en": "Time to Payment Failure",
        "ar": "الوقت إلى فشل المدفوعات",
    },
    "scenario_label": {
        "en": "Event Scenario",
        "ar": "سيناريو الحدث",
    },
    "physics_label": {
        "en": "Flow Impact",
        "ar": "أثر التدفق",
    },
    "propagation_label": {
        "en": "Impact Chain",
        "ar": "سلسلة الأثر",
    },
    "financial_label": {
        "en": "Financial Impact",
        "ar": "الأثر المالي",
    },
    "banking_label": {
        "en": "Banking Risk",
        "ar": "مخاطر البنوك",
    },
    "insurance_label": {
        "en": "Insurance Risk",
        "ar": "مخاطر التأمين",
    },
    "fintech_label": {
        "en": "Fintech Risk",
        "ar": "مخاطر الفنتك",
    },
    "decision_label": {
        "en": "Decision Actions",
        "ar": "قرارات الإجراء",
    },
    "explanation_label": {
        "en": "Explanation",
        "ar": "التفسير",
    },
    "explanation": {
        "en": "Explanation",
        "ar": "التفسير",
    },
    "executive_mode": {
        "en": "Executive Mode",
        "ar": "وضع الإدارة التنفيذية",
    },
    "analyst_mode": {
        "en": "Analyst Mode",
        "ar": "وضع المحلل",
    },
    "regulatory_brief": {
        "en": "Regulatory Brief",
        "ar": "موجز تنظيمي",
    },
    "loss_avoided": {
        "en": "Loss Avoided",
        "ar": "الخسائر المتجنبة",
    },
    "cost_to_act": {
        "en": "Cost to Act",
        "ar": "تكلفة الإجراء",
    },
    "urgency": {
        "en": "Urgency",
        "ar": "الاستعجال",
    },
    "priority": {
        "en": "Priority",
        "ar": "الأولوية",
    },
    "confidence": {
        "en": "Confidence",
        "ar": "الثقة",
    },
    "recovery_days": {
        "en": "Recovery Days",
        "ar": "أيام التعافي",
    },
}


def get_label(key: str, lang: str = "en") -> str:
    """Get a label in the requested language, falling back to English."""
    entry = LABELS.get(key, {})
    return entry.get(lang, entry.get("en", key))


def get_all_labels(lang: str = "en") -> dict[str, str]:
    """Get all labels in the requested language."""
    return {k: get_label(k, lang) for k in LABELS}
