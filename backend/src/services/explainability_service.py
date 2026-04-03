"""Service 10: explainability_service — Explanation (التفسير).

Generates bilingual (EN/AR) causal chain explanations for a run.
Maps each propagation step to a human-readable narrative.
"""

from __future__ import annotations

import logging

from src.schemas.explanation import ExplanationPack, CausalStep
from src.schemas.financial_impact import FinancialImpact

logger = logging.getLogger(__name__)


# Causal mechanism templates
MECHANISMS: dict[str, dict[str, str]] = {
    "supply": {
        "en": "Supply chain dependency: disruption propagates through physical supply link",
        "ar": "تبعية سلسلة الإمداد: الاضطراب ينتشر عبر رابط الإمداد المادي",
    },
    "financial": {
        "en": "Financial contagion: loss transmits through financial exposure",
        "ar": "عدوى مالية: الخسارة تنتقل عبر التعرض المالي",
    },
    "route": {
        "en": "Route dependency: transport corridor disruption affects connected nodes",
        "ar": "تبعية المسار: اضطراب ممر النقل يؤثر على العقد المتصلة",
    },
    "insurance": {
        "en": "Insurance cascade: claims surge propagates through reinsurance chain",
        "ar": "سلسلة التأمين: ارتفاع المطالبات ينتشر عبر سلسلة إعادة التأمين",
    },
    "regulatory": {
        "en": "Regulatory impact: regulatory action affects supervised entities",
        "ar": "أثر تنظيمي: الإجراء التنظيمي يؤثر على الكيانات المشرف عليها",
    },
    "threat": {
        "en": "Threat propagation: geopolitical threat affects regional stability",
        "ar": "انتشار التهديد: التهديد الجيوسياسي يؤثر على الاستقرار الإقليمي",
    },
    "direct_shock": {
        "en": "Direct shock: primary event impact on this entity",
        "ar": "صدمة مباشرة: تأثير مباشر للحدث على هذا الكيان",
    },
}


def generate_explanation(
    run_id: str,
    entities: list[dict],
    edges: list[dict],
    propagation_results: list[dict],
    financial_impacts: list[FinancialImpact],
    scenario_label: str | None = None,
    severity: float = 0.5,
) -> ExplanationPack:
    """Generate bilingual causal chain explanation.

    Traces the propagation path and maps each step to a mechanism + USD impact.
    """
    entity_map = {e["id"]: e for e in entities}
    impact_map = {i.entity_id: i for i in financial_impacts}

    # Build edge type lookup
    edge_types: dict[tuple[str, str], str] = {}
    for edge in edges:
        src = edge.get("source_id") or edge.get("source", "")
        tgt = edge.get("target_id") or edge.get("target", "")
        etype = edge.get("edge_type", "financial")
        edge_types[(src, tgt)] = etype

    # Build causal steps from propagation paths
    causal_steps: list[CausalStep] = []
    step_num = 0

    for prop in propagation_results:
        eid = prop["entity_id"]
        path = prop.get("path", [eid])
        impact = prop.get("impact", 0)
        entity = entity_map.get(eid, {})
        fin = impact_map.get(eid)

        step_num += 1

        # Determine mechanism from incoming edge
        if len(path) >= 2:
            parent = path[-2]
            edge_type = edge_types.get((parent, eid), "financial")
        else:
            edge_type = "direct_shock"

        mechanism = MECHANISMS.get(edge_type, MECHANISMS["financial"])

        # Event description
        if prop.get("hop", 0) == 0:
            event_en = f"Direct shock: severity {severity:.0%} applied to {entity.get('label', eid)}"
            event_ar = f"صدمة مباشرة: شدة {severity:.0%} مطبقة على {entity.get('label_ar', eid)}"
        else:
            parent_label = entity_map.get(path[-2], {}).get("label", path[-2]) if len(path) >= 2 else "unknown"
            event_en = f"Impact propagated from {parent_label} (hop {prop.get('hop', 0)}, impact {impact:.2%})"
            event_ar = f"انتشر الأثر من {entity_map.get(path[-2], {}).get('label_ar', parent_label) if len(path) >= 2 else parent_label} (خطوة {prop.get('hop', 0)}, أثر {impact:.2%})"

        causal_steps.append(CausalStep(
            step=step_num,
            entity_id=eid,
            entity_label=entity.get("label", eid),
            entity_label_ar=entity.get("label_ar"),
            event=event_en,
            event_ar=event_ar,
            impact_usd=fin.loss_usd if fin else 0.0,
            stress_delta=round(prop.get("raw_impact", impact), 4),
            mechanism=mechanism["en"],
        ))

    # Generate narratives
    total_loss = sum(i.loss_usd for i in financial_impacts)
    n_critical = sum(1 for i in financial_impacts if i.classification == "CRITICAL")
    peak_day = max((i.peak_day for i in financial_impacts), default=0)

    # Top 3 affected
    top_3 = sorted(financial_impacts, key=lambda x: x.loss_usd, reverse=True)[:3]
    top_3_en = ", ".join(f"{i.entity_label} (${i.loss_usd/1e6:.0f}M)" for i in top_3)
    top_3_ar = ", ".join(f"{entity_map.get(i.entity_id, {}).get('label_ar', i.entity_id)} ({i.loss_usd/1e6:.0f}$ مليون)" for i in top_3)

    narrative_en = (
        f"SCENARIO: {scenario_label or 'Unknown'}\n"
        f"HEADLINE LOSS: ${total_loss/1e9:.2f}B across {len(financial_impacts)} entities\n"
        f"PEAK IMPACT: Day {peak_day}\n"
        f"CRITICAL ENTITIES: {n_critical}\n"
        f"PROPAGATION: {len(causal_steps)} causal steps traced\n"
        f"TOP AFFECTED: {top_3_en}\n"
        f"The event triggers a {len(causal_steps)}-step cascade through the GCC economic graph, "
        f"with {n_critical} entities reaching CRITICAL stress levels. "
        f"Total projected loss is ${total_loss/1e9:.2f}B with peak impact on day {peak_day}."
    )

    narrative_ar = (
        f"السيناريو: {scenario_label or 'غير محدد'}\n"
        f"إجمالي الخسارة: {total_loss/1e9:.2f} مليار دولار عبر {len(financial_impacts)} كيان\n"
        f"ذروة الأثر: اليوم {peak_day}\n"
        f"الكيانات الحرجة: {n_critical}\n"
        f"الانتشار: {len(causal_steps)} خطوة سببية\n"
        f"الأكثر تأثراً: {top_3_ar}\n"
        f"يُطلق الحدث سلسلة من {len(causal_steps)} خطوة عبر الرسم البياني الاقتصادي الخليجي، "
        f"مع وصول {n_critical} كيان إلى مستوى ضغط حرج. "
        f"إجمالي الخسائر المتوقعة {total_loss/1e9:.2f} مليار دولار مع ذروة في اليوم {peak_day}."
    )

    return ExplanationPack(
        run_id=run_id,
        scenario_label=scenario_label,
        narrative_en=narrative_en,
        narrative_ar=narrative_ar,
        causal_chain=causal_steps,
        total_steps=len(causal_steps),
        headline_loss_usd=round(total_loss, 2),
        peak_day=peak_day,
        confidence=0.75,
        methodology="deterministic_propagation",
    )
