"""
Decision Gate Engine — applies approval logic and escalation rules.

Statuses:
  DRAFT → PENDING_APPROVAL → APPROVED → EXECUTED
                            → REJECTED
  OBSERVATION (monitoring only, no action required)

Rules:
  - If deadline missed → escalate
  - If severity high → approval_required = true
  - If no action → auto escalation
  - Emergency decisions skip DRAFT, start at PENDING_APPROVAL
  - Low-impact operational decisions start at APPROVED (auto-approve)

Consumed by: Stage 60 pipeline
Input: list[AnchoredDecision] + triggers
Output: list[DecisionGate]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from src.decision_quality.anchoring_engine import AnchoredDecision
from src.decision_intelligence.trigger_engine import GraphDecisionTrigger

logger = logging.getLogger(__name__)

GateStatus = Literal[
    "DRAFT", "PENDING_APPROVAL", "APPROVED",
    "EXECUTED", "REJECTED", "OBSERVATION",
]

# ── Gate rules ─────────────────────────────────────────────────────────────

_HIGH_SEVERITY_THRESHOLD = 0.70      # urgency or impact ≥ this → approval required
_AUTO_APPROVE_IMPACT = 0.30          # impact < this → auto-approve (operational)
_ESCALATION_URGENCY = 0.85           # urgency ≥ this → auto-escalation
_OBSERVATION_THRESHOLD = 0.25        # impact < this → OBSERVATION only

# ── Escalation paths by decision type ──────────────────────────────────────

_ESCALATION_PATHS: dict[str, dict[str, str]] = {
    "emergency": {
        "escalation_target_en": "Executive Committee / C-Suite",
        "escalation_target_ar": "اللجنة التنفيذية",
        "escalation_reason_en": "Emergency decision requires executive authorization within time window",
        "escalation_reason_ar": "قرار طوارئ يتطلب تفويض تنفيذي ضمن الإطار الزمني",
    },
    "operational": {
        "escalation_target_en": "Department Head / Risk Committee",
        "escalation_target_ar": "رئيس القسم / لجنة المخاطر",
        "escalation_reason_en": "Operational decision exceeds local authority threshold",
        "escalation_reason_ar": "قرار تشغيلي يتجاوز حد السلطة المحلية",
    },
    "strategic": {
        "escalation_target_en": "Board Risk Committee / Regulatory Affairs",
        "escalation_target_ar": "لجنة مخاطر مجلس الإدارة / الشؤون التنظيمية",
        "escalation_reason_en": "Strategic decision requires board-level approval and regulatory review",
        "escalation_reason_ar": "قرار استراتيجي يتطلب موافقة مستوى مجلس الإدارة ومراجعة تنظيمية",
    },
}


@dataclass(frozen=True, slots=True)
class DecisionGate:
    """Approval gate for a single decision."""
    decision_id: str
    action_id: str

    # Gate status
    current_status: GateStatus
    approval_required: bool

    # Ownership
    decision_owner: str
    decision_owner_ar: str
    approver_en: str
    approver_ar: str

    # Escalation
    escalation_threshold: float      # urgency threshold for auto-escalation
    auto_escalation_trigger: str     # what triggers escalation
    auto_escalation_trigger_ar: str
    escalation_target_en: str
    escalation_target_ar: str

    # Metadata
    decision_type: str               # emergency | operational | strategic
    urgency: float
    impact: float
    time_window_hours: float

    # Gate reasoning
    gate_reason_en: str
    gate_reason_ar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "current_status": self.current_status,
            "approval_required": self.approval_required,
            "decision_owner": self.decision_owner,
            "decision_owner_ar": self.decision_owner_ar,
            "approver_en": self.approver_en,
            "approver_ar": self.approver_ar,
            "escalation_threshold": round(self.escalation_threshold, 4),
            "auto_escalation_trigger": self.auto_escalation_trigger,
            "auto_escalation_trigger_ar": self.auto_escalation_trigger_ar,
            "escalation_target_en": self.escalation_target_en,
            "escalation_target_ar": self.escalation_target_ar,
            "decision_type": self.decision_type,
            "urgency": round(self.urgency, 4),
            "impact": round(self.impact, 4),
            "time_window_hours": round(self.time_window_hours, 1),
            "gate_reason_en": self.gate_reason_en,
            "gate_reason_ar": self.gate_reason_ar,
        }


def apply_decision_gates(
    anchored_decisions: list[AnchoredDecision],
    triggers: list[GraphDecisionTrigger],
) -> list[DecisionGate]:
    """
    Apply approval gates and escalation rules to anchored decisions.

    Args:
        anchored_decisions: From anchoring_engine.
        triggers:           From trigger_engine (for escalation context).

    Returns:
        list[DecisionGate] — one per anchored decision.
    """
    gates: list[DecisionGate] = []
    trigger_by_sector: dict[str, GraphDecisionTrigger] = {}
    for t in triggers:
        trigger_by_sector.setdefault(t.sector, t)

    for ad in anchored_decisions:
        if not ad.is_valid:
            continue

        # ── Determine approval requirement ────────────────────────────────
        needs_approval = (
            ad.urgency >= _HIGH_SEVERITY_THRESHOLD
            or ad.impact >= _HIGH_SEVERITY_THRESHOLD
            or ad.decision_type == "strategic"
        )

        # ── Determine initial status ─────────────────────────────────────
        status, reason_en, reason_ar = _determine_initial_status(
            ad, needs_approval,
        )

        # ── Escalation configuration ─────────────────────────────────────
        esc = _ESCALATION_PATHS.get(ad.decision_type, _ESCALATION_PATHS["operational"])

        # Auto-escalation trigger
        trigger = trigger_by_sector.get(ad.sector)
        if trigger and ad.urgency >= _ESCALATION_URGENCY:
            auto_trigger = f"Deadline breach OR {trigger.trigger_type} escalation"
            auto_trigger_ar = f"اختراق الموعد النهائي أو تصعيد {trigger.trigger_type}"
        else:
            auto_trigger = f"Deadline missed ({ad.time_window_hours:.0f}h) with no action taken"
            auto_trigger_ar = f"تجاوز الموعد النهائي ({ad.time_window_hours:.0f} ساعة) دون اتخاذ إجراء"

        # Approver
        approver_en, approver_ar = _determine_approver(ad)

        gates.append(DecisionGate(
            decision_id=ad.decision_id,
            action_id=ad.action_id,
            current_status=status,
            approval_required=needs_approval,
            decision_owner=ad.decision_owner,
            decision_owner_ar=ad.decision_owner_ar,
            approver_en=approver_en,
            approver_ar=approver_ar,
            escalation_threshold=_ESCALATION_URGENCY,
            auto_escalation_trigger=auto_trigger,
            auto_escalation_trigger_ar=auto_trigger_ar,
            escalation_target_en=esc["escalation_target_en"],
            escalation_target_ar=esc["escalation_target_ar"],
            decision_type=ad.decision_type,
            urgency=ad.urgency,
            impact=ad.impact,
            time_window_hours=ad.time_window_hours,
            gate_reason_en=reason_en,
            gate_reason_ar=reason_ar,
        ))

    logger.info(
        "[GateEngine] Applied gates to %d decisions: %d PENDING_APPROVAL, %d APPROVED, %d OBSERVATION",
        len(gates),
        sum(1 for g in gates if g.current_status == "PENDING_APPROVAL"),
        sum(1 for g in gates if g.current_status == "APPROVED"),
        sum(1 for g in gates if g.current_status == "OBSERVATION"),
    )
    return gates


def _determine_initial_status(
    ad: AnchoredDecision,
    needs_approval: bool,
) -> tuple[GateStatus, str, str]:
    """Determine initial gate status based on decision characteristics."""
    # OBSERVATION — very low impact, monitoring only
    if ad.impact < _OBSERVATION_THRESHOLD and ad.urgency < 0.3:
        return (
            "OBSERVATION",
            f"Low impact ({ad.impact:.2f}) — monitoring only, no immediate action required",
            f"تأثير منخفض ({ad.impact:.2f}) — مراقبة فقط، لا يتطلب إجراء فوري",
        )

    # Emergency → skip DRAFT, go straight to PENDING_APPROVAL
    if ad.decision_type == "emergency":
        return (
            "PENDING_APPROVAL",
            f"Emergency decision requires immediate approval (urgency={ad.urgency:.2f})",
            f"قرار طوارئ يتطلب موافقة فورية (إلحاح={ad.urgency:.2f})",
        )

    # Low-impact operational → auto-approve
    if not needs_approval and ad.decision_type == "operational" and ad.impact < _AUTO_APPROVE_IMPACT:
        return (
            "APPROVED",
            f"Auto-approved: low-impact operational (impact={ad.impact:.2f})",
            f"معتمد تلقائياً: تشغيلي منخفض التأثير (تأثير={ad.impact:.2f})",
        )

    # Needs approval
    if needs_approval:
        return (
            "PENDING_APPROVAL",
            f"Approval required: high severity (urgency={ad.urgency:.2f}, impact={ad.impact:.2f})",
            f"يتطلب الموافقة: شدة عالية (إلحاح={ad.urgency:.2f}، تأثير={ad.impact:.2f})",
        )

    # Default: DRAFT
    return (
        "DRAFT",
        f"Decision drafted — awaiting review (impact={ad.impact:.2f})",
        f"قرار مصاغ — في انتظار المراجعة (تأثير={ad.impact:.2f})",
    )


def _determine_approver(ad: AnchoredDecision) -> tuple[str, str]:
    """Determine who must approve this decision."""
    if ad.decision_type == "emergency":
        return "Chief Risk Officer / مدير المخاطر الرئيسي", "مدير المخاطر الرئيسي"
    if ad.decision_type == "strategic":
        return "Board Risk Committee / لجنة مخاطر مجلس الإدارة", "لجنة مخاطر مجلس الإدارة"
    # operational
    return f"Head of {ad.sector.title()} / رئيس {ad.sector}", f"رئيس {ad.sector}"
