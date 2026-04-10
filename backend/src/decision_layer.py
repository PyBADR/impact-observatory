"""
Impact Observatory | مرصد الأثر
Decision Layer — ranked action plan, five-questions framework, escalation triggers.

Priority formula:
  Priority = DL_P_W1*urgency + DL_P_W2*loss_avoided_norm + DL_P_W3*reg_risk
           + DL_P_W4*feasibility + DL_P_W5*time_effect

All weights imported from src.config — do not hardcode here.
"""
from __future__ import annotations

import math
from typing import Any

from src.utils import clamp, classify_stress, format_loss_usd
from src.config import DL_P_W1, DL_P_W2, DL_P_W3, DL_P_W4, DL_P_W5
from src.policies.scenario_policy import build_policy_context
from src.policies.action_policy import evaluate_action_policy
from src.actions.action_registry import get_actions_for_scenario_id

# ---------------------------------------------------------------------------
# Action templates (sector × risk_level)
# ---------------------------------------------------------------------------

# Each template: (sector, owner, action_en, action_ar, base_urgency, cost_usd,
#                 regulatory_risk, feasibility, time_to_act_hours)
_ACTION_TEMPLATES: list[tuple] = [
    # Banking
    ("banking", "Central Bank / المصرف المركزي",
     "Activate emergency liquidity facility and raise overnight repo limits by 150bps",
     "تفعيل تسهيل السيولة الطارئ ورفع حدود إعادة الشراء الليلية بمقدار 150 نقطة أساس",
     0.90, 500_000_000, 0.85, 0.80, 4),
    ("banking", "Systemically Important Banks / البنوك ذات الأهمية النظامية",
     "Invoke capital conservation buffer and suspend discretionary distributions",
     "تفعيل احتياطي صون رأس المال وتعليق التوزيعات التقديرية",
     0.80, 0, 0.90, 0.75, 6),
    ("banking", "Banking Regulator / الجهة التنظيمية المصرفية",
     "Issue liquidity stress disclosure to markets and activate BCBS crisis protocol",
     "إصدار إفصاح ضغط السيولة للأسواق وتفعيل بروتوكول أزمة لجنة بازل",
     0.75, 50_000_000, 0.95, 0.70, 8),

    # Energy
    ("energy", "National Oil Company / شركة النفط الوطنية",
     "Activate strategic petroleum reserve drawdown and reroute exports via Red Sea corridor",
     "تفعيل سحب الاحتياطي البترولي الاستراتيجي وإعادة توجيه الصادرات عبر ممر البحر الأحمر",
     0.95, 1_200_000_000, 0.70, 0.85, 6),
    ("energy", "Ministry of Energy / وزارة الطاقة",
     "Declare force majeure on Hormuz-dependent contracts; invoke IEA emergency sharing protocol",
     "الإعلان عن قوة قاهرة على العقود المعتمدة على مضيق هرمز؛ تفعيل بروتوكول وكالة الطاقة الدولية للطوارئ",
     0.90, 80_000_000, 0.80, 0.80, 4),

    # Maritime
    ("maritime", "Port Authority / هيئة الموانئ",
     "Divert vessel traffic to Salalah and Ad Dammam; activate port congestion surge protocol",
     "تحويل حركة السفن إلى صلالة والدمام؛ تفعيل بروتوكول ازدحام الموانئ",
     0.88, 350_000_000, 0.60, 0.88, 3),
    ("maritime", "Shipping Lines / خطوط الشحن",
     "Reroute 60% of tonnage via Cape of Good Hope; file surcharge notice to cargo owners",
     "إعادة توجيه 60% من الحمولة عبر رأس الرجاء الصالح؛ إخطار أصحاب البضائع بالرسوم الإضافية",
     0.85, 900_000_000, 0.55, 0.82, 8),

    # Insurance
    ("insurance", "Reinsurance Treaty Desk / مكتب معاهدات إعادة التأمين",
     "File precautionary loss notification to reinsurers; reserve IFRS-17 claims uplift provisions",
     "تقديم إخطار خسارة احترازي لمعيدي التأمين؛ احتجاز مخصصات ارتفاع مطالبات IFRS-17",
     0.80, 200_000_000, 0.88, 0.78, 12),
    ("insurance", "Insurance Regulator / هيئة التأمين",
     "Issue solvency watch list for insurers with >30% TIV in affected corridors",
     "إصدار قائمة مراقبة الملاءة لشركات التأمين ذات التعرض >30% في الممرات المتأثرة",
     0.75, 10_000_000, 0.92, 0.72, 16),

    # Fintech / Payments
    ("fintech", "Central Bank Payment System / نظام المدفوعات للبنك المركزي",
     "Switch RTGS to high-priority-only mode; suspend non-critical SWIFT batch processing",
     "تحويل نظام التسوية الفورية إلى وضع الأولوية العالية فقط؛ تعليق معالجة SWIFT الدُفعية غير الحرجة",
     0.85, 5_000_000, 0.75, 0.90, 2),
    ("fintech", "Digital Finance Operators / مشغلو التمويل الرقمي",
     "Impose transaction velocity limits and activate fraud detection elevated-threshold regime",
     "فرض حدود سرعة المعاملات وتفعيل نظام العتبات المرتفعة للكشف عن الاحتيال",
     0.78, 15_000_000, 0.70, 0.85, 1),

    # Infrastructure / Cyber
    ("infrastructure", "National Cyber Security Authority / الهيئة الوطنية للأمن السيبراني",
     "Raise national cyber threat level to orange; isolate critical OT networks from public internet",
     "رفع مستوى التهديد السيبراني الوطني إلى البرتقالي؛ عزل شبكات التقنيات التشغيلية الحيوية",
     0.85, 120_000_000, 0.80, 0.82, 2),
    ("infrastructure", "Critical Infrastructure Operators / مشغلو البنية التحتية الحيوية",
     "Activate business continuity plans; switch to backup power and redundant communication links",
     "تفعيل خطط استمرارية الأعمال؛ التحويل إلى الطاقة الاحتياطية وروابط الاتصال المتكررة",
     0.88, 250_000_000, 0.72, 0.87, 1),

    # Government / Regulatory
    ("government", "GCC Financial Stability Board / مجلس الاستقرار المالي الخليجي",
     "Convene emergency GCC financial stability council session and harmonise capital buffer releases",
     "عقد جلسة طارئة لمجلس الاستقرار المالي الخليجي وتنسيق الإفراج عن احتياطيات رأس المال",
     0.82, 0, 0.92, 0.68, 24),
    ("government", "Sovereign Wealth Fund Manager / مدير صندوق الثروة السيادي",
     "Activate counter-cyclical deployment facility; inject liquidity into stressed equity segments",
     "تفعيل تسهيلات النشر المضادة للدورة الاقتصادية؛ ضخ السيولة في شرائح الأسهم المتعثرة",
     0.78, 3_000_000_000, 0.60, 0.75, 6),
]

# Escalation trigger conditions
_ESCALATION_CONDITIONS: list[tuple[str, str, str]] = [
    # (condition_key, threshold_description, trigger_text)
    ("lcr_ratio",       "<1.00",   "LCR below 100% — activate emergency liquidity facility immediately"),
    ("car_ratio",       "<0.105",  "CAR below 10.5% minimum — notify Basel III supervisory authority"),
    ("combined_ratio",  ">1.10",   "Combined ratio >110% — declare insurance market stress event"),
    ("reserve_adequacy","<0.80",   "Reserve adequacy <80% — trigger reinsurance treaty loss notification"),
    ("congestion_score",">0.75",   "System congestion >75% — invoke port and logistics diversion protocol"),
    ("recovery_score",  "<0.30",   "Recovery score <30% after 72h — escalate to ministerial crisis cell"),
]


# ---------------------------------------------------------------------------
# Priority computation
# ---------------------------------------------------------------------------

def _compute_priority(
    urgency: float,
    loss_avoided_usd: float,
    max_loss_usd: float,
    regulatory_risk: float,
    feasibility: float,
    time_to_act_hours: int,
) -> float:
    """
    Priority = 0.25*urgency + 0.30*loss_avoided_norm
             + 0.20*reg_risk + 0.15*feasibility + 0.10*time_effect

    time_effect: actions executable within 6h get 1.0, 48h get 0.5, >96h get 0.1
    """
    loss_norm = clamp(loss_avoided_usd / max(max_loss_usd, 1.0), 0.0, 1.0)

    if time_to_act_hours <= 6:
        time_effect = 1.0
    elif time_to_act_hours <= 24:
        time_effect = 0.75
    elif time_to_act_hours <= 48:
        time_effect = 0.50
    else:
        time_effect = 0.25

    priority = (
        DL_P_W1 * urgency
        + DL_P_W2 * loss_norm
        + DL_P_W3 * regulatory_risk
        + DL_P_W4 * feasibility
        + DL_P_W5 * time_effect
    )
    return round(clamp(priority, 0.0, 1.0), 4)


# ---------------------------------------------------------------------------
# Sector relevance resolver
# ---------------------------------------------------------------------------

def _relevant_sectors(sector_analysis: list[dict]) -> list[str]:
    """Return sectors sorted by exposure score, top 5."""
    sorted_s = sorted(sector_analysis, key=lambda x: -x.get("exposure", 0))
    return [s["sector"] for s in sorted_s[:5]]


# ---------------------------------------------------------------------------
# Main decision builder
# ---------------------------------------------------------------------------

def build_decision_actions(
    risk_level: str,
    sector_analysis: list[dict],
    liquidity_stress: dict,
    insurance_stress: dict,
    unified_risk: dict,
    total_loss_usd: float,
    scenario_id: str = "",
    regime_urgency_boost: float = 0.0,
) -> list[dict]:
    """
    Build top-5 ranked decision actions from scenario-type-keyed registry.

    Uses the action registry for scenario-type-scoped action lookup,
    eliminating index-based cross-scenario leakage.

    Returns list of action dicts sorted by priority_score descending.
    """
    # Build policy context for urgency escalation
    policy_ctx = build_policy_context(scenario_id) if scenario_id else None

    relevant = set(_relevant_sectors(sector_analysis))
    risk_score = unified_risk.get("score", 0.5)

    # Get scenario-type-scoped actions from the registry
    registry_actions = get_actions_for_scenario_id(scenario_id) if scenario_id else _LEGACY_ACTIONS

    candidate_actions: list[dict] = []
    for idx, tpl in enumerate(registry_actions):
        sector = tpl["sector"]
        owner = tpl["owner"]
        action_en = tpl["action_en"]
        action_ar = tpl["action_ar"]
        base_urgency = tpl["base_urgency"]
        cost_usd = tpl["cost_usd"]
        reg_risk = tpl["regulatory_risk"]
        feasibility = tpl["feasibility"]
        time_hours = tpl["time_to_act_hours"]
        action_id = tpl.get("action_id", f"ACT-{idx + 1:03d}")

        # Policy-based urgency escalation (no longer does action filtering —
        # the registry already ensures scenario-type scoping)
        policy_urgency_boost = 0.0
        if policy_ctx is not None:
            action_policy = evaluate_action_policy(
                context=policy_ctx,
                action_index=idx,
                base_urgency=base_urgency,
                time_to_act_hours=time_hours,
            )
            policy_urgency_boost = action_policy.urgency_boost

        # Urgency boost if sector is directly affected
        sector_boost = 0.15 if sector in relevant else 0.0

        # Composite urgency
        urgency = clamp(
            base_urgency + sector_boost + policy_urgency_boost + regime_urgency_boost + risk_score * 0.10,
            0.0, 1.0,
        )

        # Loss avoided = fraction of total loss this action prevents
        sector_weight = {
            "energy": 0.30, "maritime": 0.20, "banking": 0.18,
            "insurance": 0.10, "logistics": 0.08, "fintech": 0.06,
            "infrastructure": 0.05, "government": 0.02,
        }.get(sector, 0.03)
        loss_avoided_usd = total_loss_usd * sector_weight * feasibility

        priority = _compute_priority(
            urgency=urgency,
            loss_avoided_usd=loss_avoided_usd,
            max_loss_usd=total_loss_usd,
            regulatory_risk=reg_risk,
            feasibility=feasibility,
            time_to_act_hours=time_hours,
        )

        # Determine escalation trigger for this action
        if time_hours <= 4:
            status = "IMMEDIATE"
        elif time_hours <= 12:
            status = "URGENT"
        elif time_hours <= 24:
            status = "MONITOR"
        else:
            status = "WATCH"

        candidate_actions.append({
            "action_id": action_id,
            "sector": sector,
            "owner": owner,
            "action": action_en,
            "action_ar": action_ar,
            "priority_score": priority,
            "urgency": round(urgency, 4),
            "loss_avoided_usd": round(loss_avoided_usd, 2),
            "loss_avoided_formatted": format_loss_usd(loss_avoided_usd),
            "cost_usd": cost_usd,
            "cost_formatted": format_loss_usd(cost_usd) if cost_usd > 0 else "$0",
            "regulatory_risk": reg_risk,
            "feasibility": feasibility,
            "time_to_act_hours": time_hours,
            "status": status,
            "escalation_trigger": f"Activate if {risk_level} risk persists >12h",
        })

    # Sort by priority descending
    candidate_actions.sort(key=lambda x: -x["priority_score"])

    # Rank and return top 5
    for rank, action in enumerate(candidate_actions[:5], start=1):
        action["rank"] = rank

    return candidate_actions[:5]


# Legacy fallback: used only when scenario_id is empty (should never happen in production)
_LEGACY_ACTIONS = [
    {"action_id": f"LEG-{i+1:03d}", "sector": t[0], "owner": t[1],
     "action_en": t[2], "action_ar": t[3], "base_urgency": t[4],
     "cost_usd": t[5], "regulatory_risk": t[6], "feasibility": t[7],
     "time_to_act_hours": t[8], "allowed_scenario_types": set()}
    for i, t in enumerate(_ACTION_TEMPLATES)
]


# ---------------------------------------------------------------------------
# Five-Questions Framework
# ---------------------------------------------------------------------------

def build_five_questions(
    scenario_id: str,
    shock_nodes: list[str],
    severity: float,
    risk_level: str,
    total_loss_usd: float,
    affected_count: int,
    sector_analysis: list[dict],
    unified_risk: dict,
    actions: list[dict],
) -> dict:
    """
    Build the Five-Questions decision-support framework.

    Returns structured dict with keys:
      what_happened, what_is_the_impact, what_is_affected,
      how_big_is_the_risk, recommended_actions
    """
    from src.utils import severity_label, severity_label_ar, risk_label_ar

    sev_label = severity_label(severity)
    sev_label_ar = severity_label_ar(severity)
    risk_label = risk_level
    risk_ar = risk_label_ar(risk_level)
    top_sector = max(sector_analysis, key=lambda x: x.get("exposure", 0), default={}).get("sector", "banking")
    critical_count = sum(1 for s in sector_analysis if s.get("stress", 0) >= 0.65)

    # 1. What happened?
    shock_label = ", ".join(s.replace("_", " ").title() for s in shock_nodes[:3])
    what_happened = {
        "description_en": (
            f"A {sev_label.lower()} severity disruption event (scenario: {scenario_id.replace('_', ' ').title()}) "
            f"has been triggered at {shock_label}. "
            f"The event is propagating across {len(sector_analysis)} GCC sectors."
        ),
        "description_ar": (
            f"حدث اضطراب بمستوى خطورة {sev_label_ar} (سيناريو: {scenario_id.replace('_', ' ')}) "
            f"تم تشغيله في {shock_label}. "
            f"يتفاقم الحدث عبر {len(sector_analysis)} قطاعات خليجية."
        ),
        "shock_nodes": shock_nodes,
        "severity_label": sev_label,
        "scenario_id": scenario_id,
    }

    # 2. What is the impact?
    system_stress = round(unified_risk.get("score", 0.0), 4)
    what_is_the_impact = {
        "total_loss_usd": total_loss_usd,
        "total_loss_formatted": format_loss_usd(total_loss_usd),
        "system_stress": system_stress,
        "disrupted_nodes": affected_count,
        "sector_impacts": [
            {
                "sector": s.get("sector"),
                "exposure": s.get("exposure", 0),
                "classification": s.get("classification", "NOMINAL"),
            }
            for s in sorted(sector_analysis, key=lambda x: -x.get("exposure", 0))[:5]
        ],
    }

    # 3. What is affected?
    entities = [
        {
            "sector": s.get("sector"),
            "classification": s.get("classification", "NOMINAL"),
            "stress": s.get("stress", 0),
        }
        for s in sector_analysis
    ]
    what_is_affected = {
        "entities": entities,
        "count": affected_count,
        "critical_count": critical_count,
        "sectors": [s["sector"] for s in sector_analysis],
        "most_exposed_sector": top_sector,
    }

    # 4. How big is the risk?
    components = unified_risk.get("components", {})
    risk_factors = [
        {"factor": "Geopolitical", "score": components.get("G", 0), "weight": "20%"},
        {"factor": "Propagation",  "score": components.get("P", 0), "weight": "25%"},
        {"factor": "Network",      "score": components.get("N", 0), "weight": "15%"},
        {"factor": "Liquidity",    "score": components.get("L", 0), "weight": "20%"},
        {"factor": "Threat Field", "score": components.get("T", 0), "weight": "10%"},
        {"factor": "Utilization",  "score": components.get("U", 0), "weight": "10%"},
    ]
    how_big = {
        "score": unified_risk.get("score", 0.0),
        "max_risk": 1.0,
        "system_classification": risk_label,
        "system_classification_ar": risk_ar,
        "risk_factors": risk_factors,
    }

    # 5. Recommended actions
    top_3 = actions[:3] if len(actions) >= 3 else actions
    escalation = compute_escalation_triggers(risk_level, {}, {})
    recommended_actions = {
        "top_3": [
            {
                "rank": a["rank"],
                "action": a["action"],
                "action_ar": a["action_ar"],
                "owner": a["owner"],
                "priority_score": a["priority_score"],
                "time_to_act_hours": a["time_to_act_hours"],
                "loss_avoided_formatted": a["loss_avoided_formatted"],
            }
            for a in top_3
        ],
        "monitoring_priorities": compute_monitoring_priorities(sector_analysis, []),
        "escalation_triggers": escalation,
    }

    return {
        "what_happened": what_happened,
        "what_is_the_impact": what_is_the_impact,
        "what_is_affected": what_is_affected,
        "how_big_is_the_risk": how_big,
        "recommended_actions": recommended_actions,
    }


# ---------------------------------------------------------------------------
# Escalation triggers
# ---------------------------------------------------------------------------

def compute_escalation_triggers(
    risk_level: str,
    liquidity: dict,
    insurance: dict,
) -> list[str]:
    """Return list of active escalation trigger descriptions."""
    triggers: list[str] = []

    lcr = liquidity.get("lcr_ratio", 1.0)
    car = liquidity.get("car_ratio", 0.12)
    combined = insurance.get("combined_ratio", 0.90)
    reserve = insurance.get("reserve_adequacy", 1.0)

    if lcr < 1.00:
        triggers.append("LCR below 100% — activate emergency liquidity facility immediately")
    if car < 0.105:
        triggers.append("CAR below 10.5% minimum — notify Basel III supervisory authority")
    if combined > 1.10:
        triggers.append("Combined ratio >110% — declare insurance market stress event")
    if reserve < 0.80:
        triggers.append("Reserve adequacy <80% — trigger reinsurance treaty loss notification")
    if risk_level in ("HIGH", "SEVERE"):
        triggers.append(f"Risk level {risk_level} — convene emergency financial stability board session")
    if risk_level == "SEVERE":
        triggers.append("SEVERE classification — activate sovereign wealth fund counter-cyclical deployment")

    if not triggers:
        triggers.append("No immediate escalation required — maintain elevated monitoring posture")

    return triggers


# ---------------------------------------------------------------------------
# Monitoring priorities
# ---------------------------------------------------------------------------

def compute_monitoring_priorities(
    sector_analysis: list[dict],
    bottlenecks: list[dict],
) -> list[str]:
    """Return ordered list of monitoring priority strings."""
    priorities: list[str] = []

    # Top-3 stressed sectors
    top_sectors = sorted(sector_analysis, key=lambda x: -x.get("stress", 0))[:3]
    for s in top_sectors:
        sector = s.get("sector", "unknown").replace("_", " ").title()
        classification = s.get("classification", "NOMINAL")
        priorities.append(f"Monitor {sector} sector — current classification: {classification}")

    # Critical bottlenecks
    critical_bn = [b for b in bottlenecks if b.get("is_critical_bottleneck")]
    if critical_bn:
        bn_labels = ", ".join(b.get("label", b.get("node_id", "")) for b in critical_bn[:3])
        priorities.append(f"Critical bottleneck nodes requiring continuous monitoring: {bn_labels}")

    # Standing monitoring items
    priorities.extend([
        "Track interbank overnight rate vs. 30-day average — flag >75bps deviation",
        "Monitor oil futures basis spread — alert on >$4/bbl intraday move",
        "Review daily SWIFT message volume for anomalous drop >15%",
    ])

    return priorities[:8]
