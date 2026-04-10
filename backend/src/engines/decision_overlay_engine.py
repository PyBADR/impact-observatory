"""
Decision Overlay Engine — maps decision actions to graph structural modifications.

Each action from the action_registry + decision_layer is translated into one or more
DecisionOverlay objects that modify the ImpactMapResponse's graph behavior:

  CUT      — sever an edge (weight_multiplier = 0.0)
  DELAY    — increase propagation delay on an edge
  REDIRECT — reroute flow to an alternate target node
  BUFFER   — add capacity buffer to a node (e.g., emergency liquidity)
  NOTIFY   — flag a node/edge for human-in-the-loop review
  ISOLATE  — disconnect a node from all inbound edges

The mapping is deterministic and scenario-type-aware.
Each overlay links back to its source action_id for audit trail.

Layer: Engines (Decision → Graph)
Called by: run_orchestrator after decision_layer produces actions.
"""
from __future__ import annotations

import logging
from typing import Any

from src.schemas.impact_map import DecisionOverlay

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Action-ID → overlay operation mapping
# ═══════════════════════════════════════════════════════════════════════════════
# Each action_id maps to a list of overlay specs.
# Specs define: operation, target pattern (edge or node), and parameters.
#
# Target patterns:
#   "sector:maritime"      → all nodes in maritime sector
#   "node:hormuz"          → specific node
#   "edge:hormuz→dubai_port" → specific edge
#   "sector_edge:energy→banking" → all edges from energy to banking sector

_ACTION_OVERLAY_MAP: dict[str, list[dict[str, Any]]] = {
    # ── MARITIME ────────────────────────────────────────────────────────────
    "MAR-001": [
        {
            "operation": "REDIRECT",
            "target_node": "dubai_port",
            "redirect_target": "salalah_port",
            "effect_en": "Divert vessel traffic from Dubai to Salalah/Dammam",
            "effect_ar": "تحويل حركة السفن من دبي إلى صلالة/الدمام",
        },
        {
            "operation": "BUFFER",
            "target_node": "salalah_port",
            "buffer_capacity_usd": 350_000_000,
            "effect_en": "Surge protocol activated at alternate ports",
            "effect_ar": "تفعيل بروتوكول الطوارئ في الموانئ البديلة",
        },
    ],
    "MAR-002": [
        {
            "operation": "DELAY",
            "target_edge": "hormuz→shipping_lanes",
            "delay_delta_hours": 168,  # Cape of Good Hope adds ~7 days
            "effect_en": "Reroute 60% tonnage via Cape of Good Hope (+7d delay)",
            "effect_ar": "إعادة توجيه 60% من الحمولة عبر رأس الرجاء الصالح (+7 أيام)",
        },
    ],
    "MAR-003": [
        {
            "operation": "REDIRECT",
            "target_node": "shipping_lanes",
            "redirect_target": "dammam_port",
            "effect_en": "Redirect overland freight via Saudi rail network",
            "effect_ar": "إعادة توجيه الشحن البري عبر شبكة السكك الحديدية السعودية",
        },
    ],
    "MAR-004": [
        {
            "operation": "CUT",
            "target_edge": "hormuz→shipping_lanes",
            "effect_en": "Declare force majeure — sever Hormuz contractual obligations",
            "effect_ar": "إعلان القوة القاهرة — قطع الالتزامات التعاقدية لهرمز",
        },
    ],
    "MAR-005": [
        {
            "operation": "NOTIFY",
            "target_node": "hormuz",
            "effect_en": "Coordinate with GCC navies for passage security",
            "effect_ar": "التنسيق مع البحريات الخليجية لأمن الممرات",
        },
    ],

    # ── ENERGY ──────────────────────────────────────────────────────────────
    "ENR-001": [
        {
            "operation": "BUFFER",
            "target_node": "saudi_aramco",
            "buffer_capacity_usd": 2_000_000_000,
            "effect_en": "Release 15-day strategic petroleum reserve",
            "effect_ar": "إطلاق احتياطي النفط الاستراتيجي لمدة 15 يوماً",
        },
    ],
    "ENR-002": [
        {
            "operation": "CUT",
            "target_edge": "saudi_aramco→gcc_pipeline",
            "effect_en": "Emergency pipeline shutdown + safety isolation",
            "effect_ar": "إغلاق طوارئ خط الأنابيب + عزل السلامة",
        },
    ],
    "ENR-003": [
        {
            "operation": "DELAY",
            "target_edge": "saudi_aramco→dubai_port",
            "delay_delta_hours": 48,
            "effect_en": "Activate fuel rationing (+48h allocation cycles)",
            "effect_ar": "تفعيل تقنين الوقود (+48 ساعة دورات التخصيص)",
        },
    ],
    "ENR-004": [
        {
            "operation": "REDIRECT",
            "target_node": "qatar_lng",
            "redirect_target": "saudi_aramco",
            "effect_en": "Switch to alternative LNG suppliers",
            "effect_ar": "التحول إلى موردي الغاز الطبيعي المسال البديلين",
        },
    ],
    "ENR-005": [
        {
            "operation": "NOTIFY",
            "target_node": "saudi_aramco",
            "effect_en": "Invoke bilateral energy cooperation treaties",
            "effect_ar": "تفعيل اتفاقيات التعاون الطاقوي الثنائية",
        },
    ],

    # ── LIQUIDITY ───────────────────────────────────────────────────────────
    "LIQ-001": [
        {
            "operation": "BUFFER",
            "target_node": "uae_banking",
            "buffer_capacity_usd": 5_000_000_000,
            "effect_en": "Central bank emergency lending facility activated",
            "effect_ar": "تفعيل تسهيلات الإقراض الطارئ للبنك المركزي",
        },
    ],
    "LIQ-002": [
        {
            "operation": "DELAY",
            "target_edge": "uae_banking→difc",
            "delay_delta_hours": -12,  # negative = speed up (repo window expansion)
            "effect_en": "Expand repo window to 72h — ease interbank squeeze",
            "effect_ar": "توسيع نافذة الريبو إلى 72 ساعة — تخفيف ضغط بين البنوك",
        },
    ],
    "LIQ-003": [
        {
            "operation": "ISOLATE",
            "target_node": "difc",
            "effect_en": "Capital controls — restrict cross-border payment flows",
            "effect_ar": "ضوابط رأس المال — تقييد تدفقات المدفوعات عبر الحدود",
        },
    ],
    "LIQ-004": [
        {
            "operation": "BUFFER",
            "target_node": "uae_banking",
            "buffer_capacity_usd": 2_000_000_000,
            "effect_en": "Deposit insurance guarantee increase to SAR 500K",
            "effect_ar": "زيادة ضمان التأمين على الودائع إلى 500 ألف ريال",
        },
    ],
    "LIQ-005": [
        {
            "operation": "NOTIFY",
            "target_node": "uae_banking",
            "effect_en": "Coordinate GCC-wide liquidity backstop protocol",
            "effect_ar": "تنسيق بروتوكول دعم السيولة على مستوى دول مجلس التعاون",
        },
    ],

    # ── CYBER ───────────────────────────────────────────────────────────────
    "CYB-001": [
        {
            "operation": "ISOLATE",
            "target_node": "difc",
            "effect_en": "Isolate SWIFT hub — activate offline settlement fallback",
            "effect_ar": "عزل مركز سويفت — تفعيل بديل التسوية غير المتصل",
        },
    ],
    "CYB-002": [
        {
            "operation": "CUT",
            "target_edge": "difc→uae_banking",
            "effect_en": "Kill compromised payment channels",
            "effect_ar": "قطع قنوات الدفع المخترقة",
        },
    ],
    "CYB-003": [
        {
            "operation": "REDIRECT",
            "target_node": "difc",
            "redirect_target": "uae_banking",
            "effect_en": "Activate backup payment infrastructure through central bank",
            "effect_ar": "تفعيل البنية التحتية الاحتياطية للمدفوعات عبر البنك المركزي",
        },
    ],
    "CYB-004": [
        {
            "operation": "BUFFER",
            "target_node": "gcc_insurance",
            "buffer_capacity_usd": 500_000_000,
            "effect_en": "Activate cyber insurance claims pool",
            "effect_ar": "تفعيل صندوق مطالبات التأمين السيبراني",
        },
    ],
    "CYB-005": [
        {
            "operation": "NOTIFY",
            "target_node": "uae_banking",
            "effect_en": "Issue public cyber incident disclosure per PDPL",
            "effect_ar": "إصدار إفصاح عام عن الحادث السيبراني وفقاً لنظام حماية البيانات",
        },
    ],

    # ── REGULATORY ──────────────────────────────────────────────────────────
    "REG-001": [
        {
            "operation": "DELAY",
            "target_edge": "uae_banking→difc",
            "delay_delta_hours": 720,  # 30-day regulatory forbearance
            "effect_en": "90-day regulatory forbearance on capital ratios",
            "effect_ar": "تسامح تنظيمي لمدة 90 يوماً على نسب رأس المال",
        },
    ],
    "REG-002": [
        {
            "operation": "BUFFER",
            "target_node": "gcc_insurance",
            "buffer_capacity_usd": 3_000_000_000,
            "effect_en": "Emergency government-backed reinsurance facility",
            "effect_ar": "تسهيلات إعادة التأمين المدعومة حكومياً",
        },
    ],
    "REG-003": [
        {
            "operation": "NOTIFY",
            "target_node": "uae_banking",
            "effect_en": "PDPL-compliant stress test disclosure to market",
            "effect_ar": "إفصاح عن اختبار الضغط متوافق مع نظام حماية البيانات",
        },
    ],
    "REG-004": [
        {
            "operation": "CUT",
            "target_edge": "difc→uae_banking",
            "effect_en": "Temporary halt on cross-border transactions pending review",
            "effect_ar": "وقف مؤقت للمعاملات عبر الحدود في انتظار المراجعة",
        },
    ],
    "REG-005": [
        {
            "operation": "NOTIFY",
            "target_node": "uae_banking",
            "effect_en": "Activate crisis communication protocol for market confidence",
            "effect_ar": "تفعيل بروتوكول الاتصال في الأزمات لثقة السوق",
        },
    ],

    # ── CROSS-TYPE ──────────────────────────────────────────────────────────
    "XTP-001": [
        {
            "operation": "NOTIFY",
            "target_node": "uae_banking",
            "effect_en": "Activate cross-border GCC coordination mechanism",
            "effect_ar": "تفعيل آلية التنسيق عبر الحدود لدول مجلس التعاون",
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Main builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_decision_overlays(
    decision_actions: list[dict[str, Any]],
    gcc_adjacency: dict[str, list[str]] | None = None,
) -> list[DecisionOverlay]:
    """
    Build DecisionOverlay list from decision plan actions.

    Args:
        decision_actions:  List of action dicts from decision_layer (each has
                          action_id, priority_score, urgency, etc.)
        gcc_adjacency:     GCC_ADJACENCY for resolving ISOLATE operations.

    Returns:
        List of DecisionOverlay objects ready to inject into ImpactMapResponse.
    """
    overlays: list[DecisionOverlay] = []

    for action in decision_actions:
        if not isinstance(action, dict):
            continue

        action_id = action.get("action_id", "")
        specs = _ACTION_OVERLAY_MAP.get(action_id, [])

        if not specs:
            # No overlay mapping — create a NOTIFY fallback
            target_node = _infer_target_node(action)
            if target_node:
                overlays.append(DecisionOverlay(
                    overlay_id=f"OVL-{action_id}-notify",
                    operation="NOTIFY",
                    target_node=target_node,
                    action_id=action_id,
                    action_label=action.get("action", action.get("action_en", "")),
                    action_label_ar=action.get("action_ar", ""),
                    effect_description=f"Action {action_id} flagged for review",
                    effect_description_ar=f"الإجراء {action_id} مُعلَّم للمراجعة",
                    priority_score=float(action.get("priority_score", 0)),
                    urgency=float(action.get("urgency", 0)),
                ))
            continue

        for i, spec in enumerate(specs):
            operation = spec["operation"]
            overlay_id = f"OVL-{action_id}-{operation.lower()}-{i}"

            overlay = DecisionOverlay(
                overlay_id=overlay_id,
                operation=operation,
                target_edge=spec.get("target_edge"),
                target_node=spec.get("target_node"),
                action_id=action_id,
                action_label=action.get("action", action.get("action_en", "")),
                action_label_ar=action.get("action_ar", ""),
                effect_description=spec.get("effect_en", ""),
                effect_description_ar=spec.get("effect_ar", ""),
                delay_delta_hours=spec.get("delay_delta_hours", 0.0),
                weight_multiplier=0.0 if operation == "CUT" else 1.0,
                buffer_capacity_usd=spec.get("buffer_capacity_usd", 0.0),
                redirect_target=spec.get("redirect_target"),
                priority_score=float(action.get("priority_score", 0)),
                urgency=float(action.get("urgency", 0)),
            )

            # For ISOLATE operations, expand to all inbound edges
            if operation == "ISOLATE" and gcc_adjacency and spec.get("target_node"):
                iso_node = spec["target_node"]
                for src, targets in gcc_adjacency.items():
                    if iso_node in targets:
                        overlays.append(DecisionOverlay(
                            overlay_id=f"{overlay_id}-iso-{src}",
                            operation="CUT",
                            target_edge=f"{src}→{iso_node}",
                            target_node=iso_node,
                            action_id=action_id,
                            action_label=overlay.action_label,
                            action_label_ar=overlay.action_label_ar,
                            effect_description=f"Isolate: cut inbound from {src}",
                            effect_description_ar=f"عزل: قطع الوارد من {src}",
                            weight_multiplier=0.0,
                            priority_score=overlay.priority_score,
                            urgency=overlay.urgency,
                        ))

            overlays.append(overlay)

    logger.info("[DecisionOverlayEngine] Built %d overlays from %d actions",
                len(overlays), len(decision_actions))

    return overlays


def _infer_target_node(action: dict) -> str | None:
    """Best-effort target node inference from action sector."""
    _sector_default_nodes = {
        "maritime": "dubai_port",
        "energy": "saudi_aramco",
        "banking": "uae_banking",
        "insurance": "gcc_insurance",
        "fintech": "difc",
        "logistics": "dammam_port",
        "government": "uae_banking",
        "cross-sector": "uae_banking",
    }
    sector = action.get("sector", "cross-sector")
    return _sector_default_nodes.get(sector, "uae_banking")
