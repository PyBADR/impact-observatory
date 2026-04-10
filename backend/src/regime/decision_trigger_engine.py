"""
Decision Trigger Engine — maps regime + propagation + breach signals to decision triggers.

This is the critical bridge between system-state intelligence (regime layer)
and actionable decisions (decision layer). It answers:

  "Given the current regime, propagation state, and breach conditions,
   which decision classes should be activated NOW?"

Input:
  - RegimeState (from regime_engine)
  - Propagation summary (depth, bottleneck count, affected nodes)
  - Breach conditions (LCR, CAR, combined ratio, payment disruption)

Output:
  - List[DecisionTrigger] — ordered by urgency, each mapping to a decision class

Pipeline position: RegimeEngine → DecisionTriggerEngine → DecisionLayer
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.regime.regime_types import RegimeType, REGIME_DEFINITIONS
from src.utils import clamp


# ── Decision classes that can be triggered ──────────────────────────────────

DECISION_CLASSES = (
    "EMERGENCY_LIQUIDITY",
    "REGULATORY_FORBEARANCE",
    "CAPITAL_CONTROLS",
    "PAYMENT_CONTINGENCY",
    "CYBER_DEFENSE",
    "PORT_REROUTING",
    "OIL_RESERVES_RELEASE",
    "CROSS_BORDER_COORDINATION",
    "MONITOR",
    "STAGE_RESERVES",
)


# ── Trigger condition types ─────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class TriggerCondition:
    """A single condition that contributes to a decision trigger."""
    condition_type: str    # "regime" | "propagation" | "breach" | "sector_pressure"
    description: str       # Human-readable
    description_ar: str    # Arabic
    met: bool              # Whether this condition is currently satisfied
    severity: float        # 0-1 how severe this condition is
    signal_value: Any = None  # The actual value that triggered/didn't trigger


@dataclass(frozen=True, slots=True)
class DecisionTrigger:
    """
    A triggered decision class with full provenance.

    Consumed by:
      - Decision Layer (action prioritization)
      - Executive Dashboard (trigger display)
      - Audit trail (why this decision was recommended)
    """
    decision_class: str              # e.g. "EMERGENCY_LIQUIDITY"
    urgency: float                   # 0-1 composite urgency
    confidence: float                # 0-1 confidence that this trigger is correct
    regime_id: RegimeType            # regime that contributed
    conditions: list[TriggerCondition] = field(default_factory=list)
    conditions_met: int = 0          # count of satisfied conditions
    conditions_total: int = 0        # total conditions evaluated
    reasoning_en: str = ""
    reasoning_ar: str = ""

    # Action guidance
    required_approval: bool = False  # Requires human-in-the-loop?
    time_to_act_hours: float = 24.0  # Suggested action window
    affected_sectors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_class": self.decision_class,
            "urgency": round(self.urgency, 4),
            "confidence": round(self.confidence, 4),
            "regime_id": self.regime_id,
            "conditions_met": self.conditions_met,
            "conditions_total": self.conditions_total,
            "reasoning_en": self.reasoning_en,
            "reasoning_ar": self.reasoning_ar,
            "required_approval": self.required_approval,
            "time_to_act_hours": round(self.time_to_act_hours, 1),
            "affected_sectors": self.affected_sectors,
            "conditions": [
                {
                    "type": c.condition_type,
                    "description": c.description,
                    "met": c.met,
                    "severity": round(c.severity, 4),
                }
                for c in self.conditions
            ],
        }


# ── Trigger rules ───────────────────────────────────────────────────────────
# Each rule: (decision_class, condition_builder_fn, urgency_base, sectors, approval_required)

def _build_conditions(
    regime_id: RegimeType,
    stress_level: float,
    trigger_flags: list[str],
    propagation_depth: int,
    bottleneck_count: int,
    nodes_affected: int,
    lcr_ratio: float,
    car_ratio: float,
    combined_ratio: float,
    payment_volume_impact_pct: float,
    sectors_under_pressure: int,
) -> dict[str, list[TriggerCondition]]:
    """
    Build condition sets for each decision class.

    Returns dict[decision_class → list[TriggerCondition]].
    """
    regime_idx = list(REGIME_DEFINITIONS.keys()).index(regime_id)
    regime_severity = stress_level

    conditions: dict[str, list[TriggerCondition]] = {}

    # ── EMERGENCY_LIQUIDITY ────────────────────────────────────────────────
    conditions["EMERGENCY_LIQUIDITY"] = [
        TriggerCondition(
            "regime", "System in liquidity stress or worse",
            "النظام في حالة ضغط سيولة أو أسوأ",
            regime_idx >= 2, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "breach", "LCR below 100% regulatory minimum",
            "نسبة تغطية السيولة أقل من 100% الحد الأدنى التنظيمي",
            lcr_ratio < 1.0, clamp(1.0 - lcr_ratio, 0, 1),
            lcr_ratio,
        ),
        TriggerCondition(
            "breach", "CAR below 10.5% Basel III minimum",
            "نسبة كفاية رأس المال أقل من 10.5% الحد الأدنى لبازل III",
            car_ratio < 0.105, clamp(0.105 - car_ratio, 0, 1) * 10,
            car_ratio,
        ),
        TriggerCondition(
            "propagation", "Banking sector under high stress",
            "القطاع المصرفي تحت ضغط عالٍ",
            "BANKING_HIGH_STRESS" in trigger_flags, 0.7 if "BANKING_HIGH_STRESS" in trigger_flags else 0.0,
        ),
    ]

    # ── REGULATORY_FORBEARANCE ─────────────────────────────────────────────
    conditions["REGULATORY_FORBEARANCE"] = [
        TriggerCondition(
            "regime", "Systemic stress or crisis escalation",
            "ضغط نظامي أو تصعيد أزمة",
            regime_idx >= 3, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "sector_pressure", "3+ sectors under simultaneous pressure",
            "3+ قطاعات تحت ضغط متزامن",
            sectors_under_pressure >= 3, clamp(sectors_under_pressure / 5.0, 0, 1),
            sectors_under_pressure,
        ),
        TriggerCondition(
            "breach", "Multiple regulatory breaches active",
            "انتهاكات تنظيمية متعددة نشطة",
            sum(1 for f in trigger_flags if "BREACH" in f) >= 2,
            0.8 if sum(1 for f in trigger_flags if "BREACH" in f) >= 2 else 0.0,
        ),
    ]

    # ── CAPITAL_CONTROLS ───────────────────────────────────────────────────
    conditions["CAPITAL_CONTROLS"] = [
        TriggerCondition(
            "regime", "Crisis escalation regime active",
            "نظام تصعيد الأزمة نشط",
            regime_idx >= 4, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "propagation", "Deep propagation (10+ hops)",
            "انتشار عميق (10+ قفزات)",
            propagation_depth >= 10, clamp(propagation_depth / 15.0, 0, 1),
            propagation_depth,
        ),
        TriggerCondition(
            "breach", "CAR severely below minimum",
            "نسبة كفاية رأس المال أقل بكثير من الحد الأدنى",
            car_ratio < 0.08, clamp(0.105 - car_ratio, 0, 1) * 10,
            car_ratio,
        ),
    ]

    # ── PAYMENT_CONTINGENCY ────────────────────────────────────────────────
    conditions["PAYMENT_CONTINGENCY"] = [
        TriggerCondition(
            "regime", "Liquidity stress or worse",
            "ضغط السيولة أو أسوأ",
            regime_idx >= 2, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "breach", "Payment volume disruption >30%",
            "اضطراب حجم المدفوعات >30%",
            payment_volume_impact_pct >= 30, clamp(payment_volume_impact_pct / 100, 0, 1),
            payment_volume_impact_pct,
        ),
        TriggerCondition(
            "propagation", "Fintech sector under high stress",
            "قطاع التكنولوجيا المالية تحت ضغط عالٍ",
            "FINTECH_HIGH_STRESS" in trigger_flags, 0.7 if "FINTECH_HIGH_STRESS" in trigger_flags else 0.0,
        ),
    ]

    # ── CYBER_DEFENSE ──────────────────────────────────────────────────────
    conditions["CYBER_DEFENSE"] = [
        TriggerCondition(
            "regime", "Elevated stress or higher",
            "ضغط مرتفع أو أعلى",
            regime_idx >= 1, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "propagation", "Multiple bottlenecks detected (3+)",
            "اكتشاف اختناقات متعددة (3+)",
            bottleneck_count >= 3, clamp(bottleneck_count / 5.0, 0, 1),
            bottleneck_count,
        ),
    ]

    # ── PORT_REROUTING ─────────────────────────────────────────────────────
    conditions["PORT_REROUTING"] = [
        TriggerCondition(
            "regime", "Elevated stress or higher",
            "ضغط مرتفع أو أعلى",
            regime_idx >= 1, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "propagation", "Nodes affected > 10",
            "العقد المتأثرة > 10",
            nodes_affected > 10, clamp(nodes_affected / 20.0, 0, 1),
            nodes_affected,
        ),
    ]

    # ── OIL_RESERVES_RELEASE ───────────────────────────────────────────────
    conditions["OIL_RESERVES_RELEASE"] = [
        TriggerCondition(
            "regime", "Systemic stress or crisis",
            "ضغط نظامي أو أزمة",
            regime_idx >= 3, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "propagation", "Deep propagation chain (8+ hops)",
            "سلسلة انتشار عميقة (8+ قفزات)",
            propagation_depth >= 8, clamp(propagation_depth / 12.0, 0, 1),
            propagation_depth,
        ),
    ]

    # ── CROSS_BORDER_COORDINATION ──────────────────────────────────────────
    conditions["CROSS_BORDER_COORDINATION"] = [
        TriggerCondition(
            "regime", "Systemic stress or crisis",
            "ضغط نظامي أو أزمة",
            regime_idx >= 3, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "sector_pressure", "4+ sectors under pressure",
            "4+ قطاعات تحت ضغط",
            sectors_under_pressure >= 4, clamp(sectors_under_pressure / 5.0, 0, 1),
            sectors_under_pressure,
        ),
        TriggerCondition(
            "propagation", "High node count affected (15+)",
            "عدد عقد مرتفع متأثر (15+)",
            nodes_affected >= 15, clamp(nodes_affected / 25.0, 0, 1),
            nodes_affected,
        ),
    ]

    # ── MONITOR ────────────────────────────────────────────────────────────
    conditions["MONITOR"] = [
        TriggerCondition(
            "regime", "Any non-stable regime",
            "أي نظام غير مستقر",
            regime_idx >= 1, regime_severity * 0.5,
            regime_id,
        ),
    ]

    # ── STAGE_RESERVES ─────────────────────────────────────────────────────
    conditions["STAGE_RESERVES"] = [
        TriggerCondition(
            "regime", "Elevated stress or higher",
            "ضغط مرتفع أو أعلى",
            regime_idx >= 1, regime_severity,
            regime_id,
        ),
        TriggerCondition(
            "propagation", "Multiple sectors under pressure",
            "قطاعات متعددة تحت ضغط",
            sectors_under_pressure >= 2, clamp(sectors_under_pressure / 4.0, 0, 1),
            sectors_under_pressure,
        ),
    ]

    return conditions


# ── Decision class metadata ─────────────────────────────────────────────────

_CLASS_META: dict[str, dict[str, Any]] = {
    "EMERGENCY_LIQUIDITY": {
        "base_urgency": 0.92,
        "time_to_act": 4.0,
        "approval_required": True,
        "sectors": ["banking", "fintech"],
    },
    "REGULATORY_FORBEARANCE": {
        "base_urgency": 0.80,
        "time_to_act": 12.0,
        "approval_required": True,
        "sectors": ["banking", "insurance", "government"],
    },
    "CAPITAL_CONTROLS": {
        "base_urgency": 0.95,
        "time_to_act": 6.0,
        "approval_required": True,
        "sectors": ["banking", "government"],
    },
    "PAYMENT_CONTINGENCY": {
        "base_urgency": 0.88,
        "time_to_act": 2.0,
        "approval_required": True,
        "sectors": ["fintech", "banking"],
    },
    "CYBER_DEFENSE": {
        "base_urgency": 0.85,
        "time_to_act": 1.0,
        "approval_required": False,
        "sectors": ["infrastructure", "fintech", "banking"],
    },
    "PORT_REROUTING": {
        "base_urgency": 0.78,
        "time_to_act": 6.0,
        "approval_required": False,
        "sectors": ["maritime", "logistics"],
    },
    "OIL_RESERVES_RELEASE": {
        "base_urgency": 0.90,
        "time_to_act": 8.0,
        "approval_required": True,
        "sectors": ["energy", "government"],
    },
    "CROSS_BORDER_COORDINATION": {
        "base_urgency": 0.75,
        "time_to_act": 24.0,
        "approval_required": True,
        "sectors": ["government", "banking"],
    },
    "MONITOR": {
        "base_urgency": 0.30,
        "time_to_act": 48.0,
        "approval_required": False,
        "sectors": [],
    },
    "STAGE_RESERVES": {
        "base_urgency": 0.50,
        "time_to_act": 24.0,
        "approval_required": False,
        "sectors": ["banking", "insurance"],
    },
}


# ── Public API ──────────────────────────────────────────────────────────────

def build_decision_triggers(
    regime_id: RegimeType,
    stress_level: float,
    trigger_flags: list[str],
    propagation_depth: int = 0,
    bottleneck_count: int = 0,
    nodes_affected: int = 0,
    lcr_ratio: float = 1.20,
    car_ratio: float = 0.12,
    combined_ratio: float = 0.95,
    payment_volume_impact_pct: float = 0.0,
    sectors_under_pressure: int = 0,
) -> list[DecisionTrigger]:
    """
    Evaluate all decision trigger rules and return activated triggers.

    Pure function. No side effects.

    Only returns triggers where at least one condition is met.
    Sorted by urgency descending.
    """
    all_conditions = _build_conditions(
        regime_id=regime_id,
        stress_level=stress_level,
        trigger_flags=trigger_flags,
        propagation_depth=propagation_depth,
        bottleneck_count=bottleneck_count,
        nodes_affected=nodes_affected,
        lcr_ratio=lcr_ratio,
        car_ratio=car_ratio,
        combined_ratio=combined_ratio,
        payment_volume_impact_pct=payment_volume_impact_pct,
        sectors_under_pressure=sectors_under_pressure,
    )

    triggers: list[DecisionTrigger] = []

    for dc in DECISION_CLASSES:
        conds = all_conditions.get(dc, [])
        if not conds:
            continue

        met_conditions = [c for c in conds if c.met]
        conditions_met = len(met_conditions)
        conditions_total = len(conds)

        # Skip if no conditions met
        if conditions_met == 0:
            continue

        meta = _CLASS_META[dc]

        # Urgency: base + boost from fraction of conditions met + stress level
        fraction_met = conditions_met / max(conditions_total, 1)
        urgency = clamp(
            meta["base_urgency"] * fraction_met
            + stress_level * 0.2
            + (0.1 if conditions_met == conditions_total else 0.0),
            0.0,
            1.0,
        )

        # Confidence: higher when more conditions are met
        confidence = clamp(
            0.5 + fraction_met * 0.4
            + (0.1 if conditions_met >= 3 else 0.0),
            0.0,
            1.0,
        )

        # Time compression under severe regimes
        regime_idx = list(REGIME_DEFINITIONS.keys()).index(regime_id)
        time_to_act = meta["time_to_act"]
        if regime_idx >= 3:
            time_to_act *= 0.6  # 40% faster action required
        elif regime_idx >= 2:
            time_to_act *= 0.8  # 20% faster

        # Reasoning
        met_descs = [c.description for c in met_conditions[:3]]
        met_descs_ar = [c.description_ar for c in met_conditions[:3]]
        reasoning_en = (
            f"Decision class {dc} triggered ({conditions_met}/{conditions_total} conditions met). "
            f"Active: {'; '.join(met_descs)}."
        )
        reasoning_ar = (
            f"فئة القرار {dc} مُفعَّلة ({conditions_met}/{conditions_total} شروط مستوفاة). "
            f"نشطة: {'; '.join(met_descs_ar)}."
        )

        # Approval required: always true for CRISIS regimes, otherwise per-class
        approval = meta["approval_required"] or regime_idx >= 4

        triggers.append(DecisionTrigger(
            decision_class=dc,
            urgency=urgency,
            confidence=confidence,
            regime_id=regime_id,
            conditions=conds,
            conditions_met=conditions_met,
            conditions_total=conditions_total,
            reasoning_en=reasoning_en,
            reasoning_ar=reasoning_ar,
            required_approval=approval,
            time_to_act_hours=round(time_to_act, 1),
            affected_sectors=meta["sectors"],
        ))

    # Sort by urgency descending
    triggers.sort(key=lambda t: -t.urgency)

    return triggers


def build_decision_triggers_from_regime_state(
    regime_state: Any,
    inputs: Any,
) -> list[DecisionTrigger]:
    """
    Convenience: build triggers directly from RegimeState + RegimeInputs.

    Extracts all required signals from the two objects.
    """
    return build_decision_triggers(
        regime_id=regime_state.regime_id,
        stress_level=regime_state.stress_level,
        trigger_flags=regime_state.trigger_flags,
        propagation_depth=inputs.propagation_depth,
        bottleneck_count=inputs.bottleneck_count,
        nodes_affected=inputs.nodes_affected,
        lcr_ratio=inputs.lcr_ratio,
        car_ratio=inputs.car_ratio,
        combined_ratio=inputs.combined_ratio,
        payment_volume_impact_pct=inputs.payment_volume_impact_pct,
        sectors_under_pressure=inputs.sectors_under_pressure,
    )
