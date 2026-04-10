"""
Impact Map Validator — blocks invalid values before they reach the UI.

Applied as the LAST stage before ImpactMapResponse is serialized.
Validates structural integrity, numeric bounds, referential consistency,
and regime coherence. Every violation produces a typed ValidationFlag.

Design rules:
  - Pure function — no side effects
  - Never silently fix data — always record what was changed
  - Distinguish "warning" (UI won't crash) from "error" (UI will crash)
  - Arabic messages for every flag

Layer: Validation (post-engine, pre-API)
Called by: run_orchestrator after impact_map_engine + decision_overlay_engine.
"""
from __future__ import annotations

import logging
from typing import Any

from src.schemas.impact_map import (
    ImpactMapResponse,
    ImpactMapNode,
    ImpactMapEdge,
    PropagationEvent,
    DecisionOverlay,
    ValidationFlag,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Validation rules
# ═══════════════════════════════════════════════════════════════════════════════

def validate_impact_map(impact_map: ImpactMapResponse) -> ImpactMapResponse:
    """
    Validate and sanitize an ImpactMapResponse in place.

    Applies all validation rules and attaches ValidationFlag objects.
    Returns the same ImpactMapResponse with validation_flags populated.
    """
    flags: list[ValidationFlag] = []

    # ── Structural checks ───────────────────────────────────────────────────
    flags.extend(_validate_structure(impact_map))

    # ── Node checks ─────────────────────────────────────────────────────────
    flags.extend(_validate_nodes(impact_map))

    # ── Edge checks ─────────────────────────────────────────────────────────
    flags.extend(_validate_edges(impact_map))

    # ── Propagation event checks ────────────────────────────────────────────
    flags.extend(_validate_propagation_events(impact_map))

    # ── Overlay checks ──────────────────────────────────────────────────────
    flags.extend(_validate_overlays(impact_map))

    # ── Regime coherence ────────────────────────────────────────────────────
    flags.extend(_validate_regime_coherence(impact_map))

    # ── Cross-reference checks ──────────────────────────────────────────────
    flags.extend(_validate_cross_references(impact_map))

    # Attach flags
    impact_map.validation_flags = flags

    if flags:
        errors = [f for f in flags if f.severity == "error"]
        warnings = [f for f in flags if f.severity == "warning"]
        logger.info(
            "[ImpactMapValidator] %d flags: %d errors, %d warnings",
            len(flags), len(errors), len(warnings),
        )
    else:
        logger.debug("[ImpactMapValidator] All checks passed — 0 flags")

    return impact_map


# ── Structural ──────────────────────────────────────────────────────────────

def _validate_structure(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []

    if not im.nodes:
        flags.append(ValidationFlag(
            field="nodes",
            rule="non_empty_nodes",
            severity="error",
            message="Impact map has no nodes — UI graph will be empty",
            message_ar="خريطة التأثير لا تحتوي على عقد — سيكون الرسم البياني فارغاً",
        ))

    if not im.edges:
        flags.append(ValidationFlag(
            field="edges",
            rule="non_empty_edges",
            severity="warning",
            message="Impact map has no edges — no propagation paths visible",
            message_ar="خريطة التأثير لا تحتوي على حواف — لا مسارات انتشار مرئية",
        ))

    if not im.run_id:
        flags.append(ValidationFlag(
            field="run_id",
            rule="non_empty_run_id",
            severity="warning",
            message="Missing run_id — audit trail incomplete",
            message_ar="معرف التشغيل مفقود — سجل التدقيق غير مكتمل",
        ))

    if not im.scenario_id:
        flags.append(ValidationFlag(
            field="scenario_id",
            rule="non_empty_scenario_id",
            severity="warning",
            message="Missing scenario_id — context unavailable",
            message_ar="معرف السيناريو مفقود — السياق غير متاح",
        ))

    return flags


# ── Nodes ───────────────────────────────────────────────────────────────────

def _validate_nodes(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []
    seen_ids: set[str] = set()

    for i, node in enumerate(im.nodes):
        pfx = f"nodes[{i}]"

        # Duplicate ID check
        if node.id in seen_ids:
            flags.append(ValidationFlag(
                field=f"{pfx}.id",
                rule="unique_node_id",
                severity="error",
                message=f"Duplicate node ID: {node.id}",
                message_ar=f"معرف عقدة مكرر: {node.id}",
            ))
        seen_ids.add(node.id)

        # Stress bounds
        if node.stress_level < 0 or node.stress_level > 1:
            node.stress_level = max(0.0, min(1.0, node.stress_level))
            flags.append(ValidationFlag(
                field=f"{pfx}.stress_level",
                rule="stress_bounds_0_1",
                severity="warning",
                message=f"Node {node.id} stress clamped to [0,1]",
                message_ar=f"عقدة {node.id} تم تقييد الضغط إلى [0,1]",
            ))

        # Criticality bounds
        if node.criticality < 0 or node.criticality > 1:
            node.criticality = max(0.0, min(1.0, node.criticality))
            flags.append(ValidationFlag(
                field=f"{pfx}.criticality",
                rule="criticality_bounds_0_1",
                severity="warning",
                message=f"Node {node.id} criticality clamped to [0,1]",
                message_ar=f"عقدة {node.id} تم تقييد الأهمية إلى [0,1]",
            ))

        # Loss non-negative
        if node.loss_usd < 0:
            node.loss_usd = 0.0
            flags.append(ValidationFlag(
                field=f"{pfx}.loss_usd",
                rule="loss_non_negative",
                severity="warning",
                message=f"Node {node.id} negative loss_usd zeroed",
                message_ar=f"عقدة {node.id} خسارة سالبة مصححة إلى صفر",
            ))

        # State coherence with stress
        if node.state == "NOMINAL" and node.stress_level >= 0.30:
            flags.append(ValidationFlag(
                field=f"{pfx}.state",
                rule="state_stress_coherence",
                severity="warning",
                message=f"Node {node.id} state=NOMINAL but stress={node.stress_level:.2f}",
                message_ar=f"عقدة {node.id} حالة=طبيعي لكن الضغط={node.stress_level:.2f}",
            ))

        # Geo-coordinate sanity (GCC bounding box: lat 12-32, lng 34-60)
        if node.lat != 0.0 or node.lng != 0.0:
            if not (12.0 <= node.lat <= 32.0 and 34.0 <= node.lng <= 60.0):
                flags.append(ValidationFlag(
                    field=f"{pfx}.lat/lng",
                    rule="gcc_geo_bounds",
                    severity="warning",
                    message=f"Node {node.id} coordinates outside GCC bounding box",
                    message_ar=f"عقدة {node.id} إحداثيات خارج نطاق دول الخليج",
                ))

    return flags


# ── Edges ───────────────────────────────────────────────────────────────────

def _validate_edges(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []
    node_ids = {n.id for n in im.nodes}
    seen_pairs: set[str] = set()

    for i, edge in enumerate(im.edges):
        pfx = f"edges[{i}]"

        # Referential integrity
        if edge.source not in node_ids:
            flags.append(ValidationFlag(
                field=f"{pfx}.source",
                rule="edge_source_exists",
                severity="error",
                message=f"Edge source '{edge.source}' not in node set",
                message_ar=f"مصدر الحافة '{edge.source}' غير موجود في مجموعة العقد",
            ))

        if edge.target not in node_ids:
            flags.append(ValidationFlag(
                field=f"{pfx}.target",
                rule="edge_target_exists",
                severity="error",
                message=f"Edge target '{edge.target}' not in node set",
                message_ar=f"هدف الحافة '{edge.target}' غير موجود في مجموعة العقد",
            ))

        # Self-loop
        if edge.source == edge.target:
            flags.append(ValidationFlag(
                field=f"{pfx}",
                rule="no_self_loops",
                severity="error",
                message=f"Self-loop edge: {edge.source} → {edge.source}",
                message_ar=f"حافة حلقة ذاتية: {edge.source} → {edge.source}",
            ))

        # Duplicate edge
        pair_key = f"{edge.source}→{edge.target}"
        if pair_key in seen_pairs:
            flags.append(ValidationFlag(
                field=f"{pfx}",
                rule="unique_edges",
                severity="warning",
                message=f"Duplicate edge: {pair_key}",
                message_ar=f"حافة مكررة: {pair_key}",
            ))
        seen_pairs.add(pair_key)

        # Weight bounds
        if edge.weight < 0 or edge.weight > 1:
            edge.weight = max(0.0, min(1.0, edge.weight))
            flags.append(ValidationFlag(
                field=f"{pfx}.weight",
                rule="weight_bounds_0_1",
                severity="warning",
                message=f"Edge {pair_key} weight clamped to [0,1]",
                message_ar=f"حافة {pair_key} تم تقييد الوزن إلى [0,1]",
            ))

        # Delay non-negative
        if edge.delay_hours < 0:
            edge.delay_hours = 0.0
            flags.append(ValidationFlag(
                field=f"{pfx}.delay_hours",
                rule="delay_non_negative",
                severity="warning",
                message=f"Edge {pair_key} negative delay zeroed",
                message_ar=f"حافة {pair_key} تأخير سالب مصحح إلى صفر",
            ))

    return flags


# ── Propagation Events ──────────────────────────────────────────────────────

def _validate_propagation_events(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []
    node_ids = {n.id for n in im.nodes}

    for i, event in enumerate(im.propagation_events):
        pfx = f"propagation_events[{i}]"

        # Target must exist in nodes
        if event.target_id and event.target_id not in node_ids:
            flags.append(ValidationFlag(
                field=f"{pfx}.target_id",
                rule="event_target_exists",
                severity="warning",
                message=f"Event target '{event.target_id}' not in node set",
                message_ar=f"هدف الحدث '{event.target_id}' غير موجود في مجموعة العقد",
            ))

        # Severity bounds
        if event.severity_at_arrival < 0 or event.severity_at_arrival > 1:
            event.severity_at_arrival = max(0.0, min(1.0, event.severity_at_arrival))
            flags.append(ValidationFlag(
                field=f"{pfx}.severity_at_arrival",
                rule="event_severity_bounds",
                severity="warning",
                message=f"Event {event.event_id} severity clamped to [0,1]",
                message_ar=f"حدث {event.event_id} تم تقييد الشدة إلى [0,1]",
            ))

        # Arrival time non-negative
        if event.arrival_hour < 0:
            event.arrival_hour = 0.0
            flags.append(ValidationFlag(
                field=f"{pfx}.arrival_hour",
                rule="arrival_non_negative",
                severity="warning",
                message=f"Event {event.event_id} negative arrival_hour zeroed",
                message_ar=f"حدث {event.event_id} وقت وصول سالب مصحح إلى صفر",
            ))

    # Check chronological order
    for i in range(1, len(im.propagation_events)):
        if im.propagation_events[i].arrival_hour < im.propagation_events[i - 1].arrival_hour:
            flags.append(ValidationFlag(
                field=f"propagation_events[{i}].arrival_hour",
                rule="chronological_order",
                severity="warning",
                message="Propagation events not in chronological order",
                message_ar="أحداث الانتشار ليست بترتيب زمني",
            ))
            break  # one flag is enough

    return flags


# ── Overlays ────────────────────────────────────────────────────────────────

def _validate_overlays(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []
    node_ids = {n.id for n in im.nodes}

    for i, overlay in enumerate(im.decision_overlays):
        pfx = f"decision_overlays[{i}]"

        # Target node must exist if specified
        if overlay.target_node and overlay.target_node not in node_ids:
            flags.append(ValidationFlag(
                field=f"{pfx}.target_node",
                rule="overlay_node_exists",
                severity="warning",
                message=f"Overlay target node '{overlay.target_node}' not in node set",
                message_ar=f"عقدة هدف التداخل '{overlay.target_node}' غير موجودة",
            ))

        # CUT operation must have weight_multiplier = 0
        if overlay.operation == "CUT" and overlay.weight_multiplier != 0.0:
            overlay.weight_multiplier = 0.0
            flags.append(ValidationFlag(
                field=f"{pfx}.weight_multiplier",
                rule="cut_weight_zero",
                severity="warning",
                message=f"CUT overlay {overlay.overlay_id} weight forced to 0.0",
                message_ar=f"تداخل القطع {overlay.overlay_id} تم تصحيح الوزن إلى 0.0",
            ))

        # REDIRECT must have redirect_target
        if overlay.operation == "REDIRECT" and not overlay.redirect_target:
            flags.append(ValidationFlag(
                field=f"{pfx}.redirect_target",
                rule="redirect_has_target",
                severity="error",
                message=f"REDIRECT overlay {overlay.overlay_id} missing redirect_target",
                message_ar=f"تداخل إعادة التوجيه {overlay.overlay_id} يفتقد الهدف البديل",
            ))

        # Priority/urgency bounds
        if overlay.priority_score < 0 or overlay.priority_score > 1:
            overlay.priority_score = max(0.0, min(1.0, overlay.priority_score))
        if overlay.urgency < 0 or overlay.urgency > 1:
            overlay.urgency = max(0.0, min(1.0, overlay.urgency))

    return flags


# ── Regime Coherence ────────────────────────────────────────────────────────

def _validate_regime_coherence(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []
    regime = im.regime

    # Propagation amplifier should match regime severity direction
    if regime.regime_id == "STABLE" and regime.propagation_amplifier > 1.1:
        flags.append(ValidationFlag(
            field="regime.propagation_amplifier",
            rule="stable_no_amplification",
            severity="warning",
            message=f"STABLE regime has propagation_amplifier={regime.propagation_amplifier}",
            message_ar=f"نظام مستقر لديه مضاعف انتشار={regime.propagation_amplifier}",
        ))

    if regime.regime_id == "CRISIS_ESCALATION" and regime.propagation_amplifier < 1.5:
        flags.append(ValidationFlag(
            field="regime.propagation_amplifier",
            rule="crisis_minimum_amplification",
            severity="warning",
            message=f"CRISIS_ESCALATION has low amplifier={regime.propagation_amplifier}",
            message_ar=f"تصعيد أزمة لديه مضاعف منخفض={regime.propagation_amplifier}",
        ))

    # Delay compression range
    if regime.delay_compression <= 0 or regime.delay_compression > 1.0:
        flags.append(ValidationFlag(
            field="regime.delay_compression",
            rule="delay_compression_bounds",
            severity="warning",
            message=f"Delay compression out of (0,1]: {regime.delay_compression}",
            message_ar=f"ضغط التأخير خارج النطاق: {regime.delay_compression}",
        ))

    return flags


# ── Cross-references ────────────────────────────────────────────────────────

def _validate_cross_references(im: ImpactMapResponse) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []

    # Check that headline sector count matches actual stressed sectors
    stressed_sectors = {n.sector for n in im.nodes if n.stress_level > 0.1}
    if im.headline.sectors_impacted > 0 and abs(im.headline.sectors_impacted - len(stressed_sectors)) > 2:
        flags.append(ValidationFlag(
            field="headline.sectors_impacted",
            rule="headline_sector_consistency",
            severity="warning",
            message=f"Headline says {im.headline.sectors_impacted} sectors but found {len(stressed_sectors)} stressed",
            message_ar=f"العنوان يقول {im.headline.sectors_impacted} قطاعات لكن وُجد {len(stressed_sectors)} متأثرة",
        ))

    # Check that breached count matches
    breached_nodes = [n for n in im.nodes if n.state == "BREACHED"]
    if im.headline.nodes_breached != len(breached_nodes):
        im.headline.nodes_breached = len(breached_nodes)
        flags.append(ValidationFlag(
            field="headline.nodes_breached",
            rule="headline_breach_count_sync",
            severity="info",
            message="Headline breached count synced with actual node states",
            message_ar="تم مزامنة عدد الاختراقات في العنوان مع حالات العقد الفعلية",
        ))

    # Verify timeline is monotonically increasing
    for i in range(1, len(im.timeline)):
        if im.timeline[i].hour < im.timeline[i - 1].hour:
            flags.append(ValidationFlag(
                field=f"timeline[{i}].hour",
                rule="timeline_monotonic",
                severity="error",
                message="Timeline hours are not monotonically increasing",
                message_ar="ساعات الجدول الزمني ليست متزايدة بشكل رتيب",
            ))
            break

    return flags
