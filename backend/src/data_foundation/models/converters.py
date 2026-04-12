"""P2 Data Foundation — Pydantic ↔ ORM Converters.

Bidirectional conversion between P1 Pydantic schemas and P2 ORM models.
Handles:
  - GeoCoordinate ↔ geo_lat/geo_lng flattening
  - List/Dict ↔ JSONB serialization
  - metadata ↔ metadata_json column rename
  - RuleCondition ↔ JSONB conditions
  - TriggerContext ↔ JSONB trigger_context
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TypeVar

from src.data_foundation.schemas.entity_registry import EntityRegistryEntry
from src.data_foundation.schemas.event_signals import EventSignal
from src.data_foundation.schemas.macro_indicators import MacroIndicatorRecord
from src.data_foundation.schemas.interest_rate_signals import InterestRateSignal
from src.data_foundation.schemas.oil_energy_signals import OilEnergySignal
from src.data_foundation.schemas.fx_signals import FXSignal
from src.data_foundation.schemas.cbk_indicators import CBKIndicatorRecord
from src.data_foundation.schemas.banking_sector_profiles import BankingSectorProfile
from src.data_foundation.schemas.insurance_sector_profiles import InsuranceSectorProfile
from src.data_foundation.schemas.logistics_nodes import LogisticsNode
from src.data_foundation.schemas.decision_rules import DecisionRule
from src.data_foundation.schemas.decision_logs import DecisionLogEntry

from src.data_foundation.models.tables import (
    EntityRegistryORM,
    EventSignalORM,
    MacroIndicatorORM,
    InterestRateSignalORM,
    OilEnergySignalORM,
    FXSignalORM,
    CBKIndicatorORM,
    BankingProfileORM,
    InsuranceProfileORM,
    LogisticsNodeORM,
    DecisionRuleORM,
    DecisionLogORM,
)

T = TypeVar("T")


def _geo_to_flat(obj: Any) -> Dict[str, Optional[float]]:
    """Extract geo_lat/geo_lng from a Pydantic model's .geo field."""
    geo = getattr(obj, "geo", None)
    if geo is not None:
        return {"geo_lat": geo.latitude, "geo_lng": geo.longitude}
    return {"geo_lat": None, "geo_lng": None}


def _flat_to_geo(row: Any) -> Optional[Dict[str, float]]:
    """Reconstruct geo dict from row's geo_lat/geo_lng."""
    lat = getattr(row, "geo_lat", None)
    lng = getattr(row, "geo_lng", None)
    if lat is not None and lng is not None:
        return {"latitude": lat, "longitude": lng}
    return None


def _enum_val(v: Any) -> Any:
    """Extract .value from enum, passthrough otherwise."""
    return v.value if hasattr(v, "value") else v


def _list_enum_vals(lst: List) -> List[str]:
    return [_enum_val(x) for x in lst]


# ═══════════════════════════════════════════════════════════════════════════════
# Foundation base fields (shared by all conversions)
# ═══════════════════════════════════════════════════════════════════════════════

def _base_fields(obj: Any) -> Dict[str, Any]:
    return {
        "schema_version": obj.schema_version,
        "tenant_id": obj.tenant_id,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "provenance_hash": obj.provenance_hash,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Registry
# ═══════════════════════════════════════════════════════════════════════════════

def entity_to_orm(e: EntityRegistryEntry) -> EntityRegistryORM:
    return EntityRegistryORM(
        **_base_fields(e),
        entity_id=e.entity_id,
        entity_name=e.entity_name,
        entity_name_ar=e.entity_name_ar,
        entity_type=_enum_val(e.entity_type),
        country=_enum_val(e.country),
        sector=_enum_val(e.sector),
        parent_entity_id=e.parent_entity_id,
        **_geo_to_flat(e),
        gdp_weight=e.gdp_weight,
        criticality_score=e.criticality_score,
        systemic_importance=e.systemic_importance,
        regulatory_id=e.regulatory_id,
        swift_code=e.swift_code,
        lei_code=e.lei_code,
        website=e.website,
        is_active=e.is_active,
        related_entity_ids=e.related_entity_ids or [],
        tags=e.tags or [],
        metadata_json=e.metadata,
    )


def entity_from_orm(row: EntityRegistryORM) -> EntityRegistryEntry:
    return EntityRegistryEntry(
        entity_id=row.entity_id,
        entity_name=row.entity_name,
        entity_name_ar=row.entity_name_ar,
        entity_type=row.entity_type,
        country=row.country,
        sector=row.sector,
        parent_entity_id=row.parent_entity_id,
        geo=_flat_to_geo(row),
        gdp_weight=row.gdp_weight,
        criticality_score=row.criticality_score,
        systemic_importance=row.systemic_importance,
        regulatory_id=row.regulatory_id,
        swift_code=row.swift_code,
        lei_code=row.lei_code,
        website=row.website,
        is_active=row.is_active,
        related_entity_ids=row.related_entity_ids or [],
        tags=row.tags or [],
        metadata=row.metadata_json,
        schema_version=row.schema_version,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        provenance_hash=row.provenance_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Event Signals
# ═══════════════════════════════════════════════════════════════════════════════

def event_to_orm(e: EventSignal) -> EventSignalORM:
    return EventSignalORM(
        **_base_fields(e),
        event_id=e.event_id,
        title=e.title,
        title_ar=e.title_ar,
        description=e.description,
        category=_enum_val(e.category),
        subcategory=e.subcategory,
        severity=_enum_val(e.severity),
        severity_score=e.severity_score,
        event_time=e.event_time,
        detected_at=e.detected_at,
        countries_affected=_list_enum_vals(e.countries_affected),
        sectors_affected=_list_enum_vals(e.sectors_affected),
        entity_ids_affected=e.entity_ids_affected,
        scenario_ids=e.scenario_ids,
        **_geo_to_flat(e),
        source_id=e.source_id,
        source_url=e.source_url,
        confidence_score=e.confidence_score,
        confidence_method=_enum_val(e.confidence_method),
        corroborating_source_count=e.corroborating_source_count,
        is_ongoing=e.is_ongoing,
        parent_event_id=e.parent_event_id,
        tags=e.tags or [],
        raw_payload=e.raw_payload,
    )


def event_from_orm(row: EventSignalORM) -> EventSignal:
    return EventSignal(
        event_id=row.event_id,
        title=row.title,
        title_ar=row.title_ar,
        description=row.description,
        category=row.category,
        subcategory=row.subcategory,
        severity=row.severity,
        severity_score=row.severity_score,
        event_time=row.event_time,
        detected_at=row.detected_at,
        countries_affected=row.countries_affected or [],
        sectors_affected=row.sectors_affected or [],
        entity_ids_affected=row.entity_ids_affected or [],
        scenario_ids=row.scenario_ids or [],
        geo=_flat_to_geo(row),
        source_id=row.source_id,
        source_url=row.source_url,
        confidence_score=row.confidence_score,
        confidence_method=row.confidence_method,
        corroborating_source_count=row.corroborating_source_count,
        is_ongoing=row.is_ongoing,
        parent_event_id=row.parent_event_id,
        tags=row.tags or [],
        raw_payload=row.raw_payload,
        schema_version=row.schema_version,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        provenance_hash=row.provenance_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Macro Indicators
# ═══════════════════════════════════════════════════════════════════════════════

def macro_to_orm(m: MacroIndicatorRecord) -> MacroIndicatorORM:
    return MacroIndicatorORM(
        **_base_fields(m),
        indicator_id=m.indicator_id,
        country=_enum_val(m.country),
        indicator_code=m.indicator_code,
        indicator_name=m.indicator_name,
        value=m.value,
        unit=m.unit,
        currency=_enum_val(m.currency) if m.currency else None,
        period_start=m.period_start,
        period_end=m.period_end,
        frequency=m.frequency,
        source_id=m.source_id,
        source_reliability=_enum_val(m.source_reliability),
        confidence_score=m.confidence_score,
        confidence_method=_enum_val(m.confidence_method),
        is_provisional=m.is_provisional,
        revision_number=m.revision_number,
        previous_value=m.previous_value,
        yoy_change_pct=m.yoy_change_pct,
    )


def macro_from_orm(row: MacroIndicatorORM) -> MacroIndicatorRecord:
    return MacroIndicatorRecord(
        indicator_id=row.indicator_id,
        country=row.country,
        indicator_code=row.indicator_code,
        indicator_name=row.indicator_name,
        value=row.value,
        unit=row.unit,
        currency=row.currency,
        period_start=row.period_start,
        period_end=row.period_end,
        frequency=row.frequency,
        source_id=row.source_id,
        source_reliability=row.source_reliability,
        confidence_score=row.confidence_score,
        confidence_method=row.confidence_method,
        is_provisional=row.is_provisional,
        revision_number=row.revision_number,
        previous_value=row.previous_value,
        yoy_change_pct=row.yoy_change_pct,
        schema_version=row.schema_version,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        provenance_hash=row.provenance_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Rules
# ═══════════════════════════════════════════════════════════════════════════════

def rule_to_orm(r: DecisionRule) -> DecisionRuleORM:
    return DecisionRuleORM(
        **_base_fields(r),
        rule_id=r.rule_id,
        rule_name=r.rule_name,
        rule_name_ar=r.rule_name_ar,
        description=r.description,
        version=r.version,
        is_active=r.is_active,
        conditions=[c.model_dump(mode="json") for c in r.conditions],
        condition_logic=r.condition_logic,
        action=_enum_val(r.action),
        action_params=r.action_params,
        escalation_level=_enum_val(r.escalation_level),
        applicable_countries=_list_enum_vals(r.applicable_countries),
        applicable_sectors=_list_enum_vals(r.applicable_sectors),
        applicable_scenarios=r.applicable_scenarios,
        requires_human_approval=r.requires_human_approval,
        cooldown_minutes=r.cooldown_minutes,
        expiry_date=r.expiry_date,
        source_dataset_ids=r.source_dataset_ids,
        tags=r.tags or [],
        created_by=r.created_by,
        approved_by=r.approved_by,
        audit_notes=r.audit_notes,
    )


def rule_from_orm(row: DecisionRuleORM) -> DecisionRule:
    return DecisionRule(
        rule_id=row.rule_id,
        rule_name=row.rule_name,
        rule_name_ar=row.rule_name_ar,
        description=row.description,
        version=row.version,
        is_active=row.is_active,
        conditions=row.conditions,
        condition_logic=row.condition_logic,
        action=row.action,
        action_params=row.action_params,
        escalation_level=row.escalation_level,
        applicable_countries=row.applicable_countries or [],
        applicable_sectors=row.applicable_sectors or [],
        applicable_scenarios=row.applicable_scenarios or [],
        requires_human_approval=row.requires_human_approval,
        cooldown_minutes=row.cooldown_minutes,
        expiry_date=row.expiry_date,
        source_dataset_ids=row.source_dataset_ids or [],
        tags=row.tags or [],
        created_by=row.created_by,
        approved_by=row.approved_by,
        audit_notes=row.audit_notes,
        schema_version=row.schema_version,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        provenance_hash=row.provenance_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Logs
# ═══════════════════════════════════════════════════════════════════════════════

def dlog_to_orm(d: DecisionLogEntry) -> DecisionLogORM:
    return DecisionLogORM(
        **_base_fields(d),
        log_id=d.log_id,
        rule_id=d.rule_id,
        rule_version=d.rule_version,
        triggered_at=d.triggered_at,
        action=_enum_val(d.action),
        status=_enum_val(d.status),
        trigger_context=d.trigger_context.model_dump(mode="json"),
        country=_enum_val(d.country) if d.country else None,
        entity_ids=d.entity_ids,
        requires_approval=d.requires_approval,
        reviewed_by=d.reviewed_by,
        reviewed_at=d.reviewed_at,
        review_notes=d.review_notes,
        executed_at=d.executed_at,
        execution_result=d.execution_result,
        superseded_by=d.superseded_by,
        audit_hash=d.audit_hash,
        previous_log_hash=d.previous_log_hash,
    )


def dlog_from_orm(row: DecisionLogORM) -> DecisionLogEntry:
    return DecisionLogEntry(
        log_id=row.log_id,
        rule_id=row.rule_id,
        rule_version=row.rule_version,
        triggered_at=row.triggered_at,
        action=row.action,
        status=row.status,
        trigger_context=row.trigger_context,
        country=row.country,
        entity_ids=row.entity_ids or [],
        requires_approval=row.requires_approval,
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        review_notes=row.review_notes,
        executed_at=row.executed_at,
        execution_result=row.execution_result,
        superseded_by=row.superseded_by,
        audit_hash=row.audit_hash,
        previous_log_hash=row.previous_log_hash,
        schema_version=row.schema_version,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        provenance_hash=row.provenance_hash,
    )
