"""
Logistics Disruption Rule Family | عائلة قواعد اضطراب اللوجستيات
===================================================================

Policy domain: Port/chokepoint disruptions threatening GCC trade flows.

GCC context:
  - Strait of Hormuz: ~21% of global oil transit, ~30% of GCC non-oil exports
  - Jebel Ali (Dubai): Largest port in Middle East, 15M TEU/year
  - Salalah (Oman): Key transshipment hub for Indian Ocean routes
  - Red Sea / Bab al-Mandab: 10-15% of global trade, critical for GCC-Europe
  - 2024 Houthi disruptions rerouted ~50% of Red Sea traffic around Cape of Good Hope

Variants:
  SPEC-LOGISTICS-HORMUZ-CLOSURE-v1  — Strait of Hormuz full/partial closure
  SPEC-LOGISTICS-PORT-OVERLOAD-v1   — Major GCC port utilization >95%
"""

from __future__ import annotations

from datetime import datetime, timezone, date

from src.data_foundation.rule_specs.schema import (
    RuleSpec,
    TriggerSignalSpec,
    ThresholdSpec,
    TransmissionSpec,
    AffectedEntitySpec,
    SectorImpactSpec,
    DecisionProposalSpec,
    ConfidenceBasis,
    RationaleTemplate,
    Exclusion,
    SpecAuditRecord,
)
from src.data_foundation.schemas.enums import (
    DecisionAction,
    EventCategory,
    GCCCountry,
    RiskLevel,
    Sector,
    SignalSeverity,
)

__all__ = ["LOGISTICS_DISRUPTION_SPECS"]


_HORMUZ_CLOSURE = RuleSpec(
    spec_id="SPEC-LOGISTICS-HORMUZ-CLOSURE-v1",
    spec_version="1.0.0",
    family="logistics-disruption",
    variant="hormuz-closure",

    name="Strait of Hormuz Disruption (Severity ≥ HIGH)",
    name_ar="اضطراب مضيق هرمز (شدة ≥ مرتفع)",
    description=(
        "Triggers when an event signal related to the Strait of Hormuz "
        "reaches HIGH severity (URS ≥ 0.65). Hormuz carries ~21% of "
        "global oil supply and is the sole maritime export route for "
        "Kuwait, Qatar, Bahrain, and UAE eastern ports. Any significant "
        "disruption has cascading effects on oil prices, shipping costs, "
        "insurance premiums, and GCC government revenue."
    ),
    status="ACTIVE",
    effective_date=date(2025, 3, 1),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="event_signals.severity_score",
            signal_name="Hormuz Event Severity Score",
            signal_name_ar="درجة شدة حدث هرمز",
            source_dataset="p1_event_signals",
            unit="score_0_1",
            monitoring_frequency="REAL_TIME",
            baseline_value=0.0,
            baseline_source="No disruption baseline",
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="event_signals.severity_score",
            operator="gte",
            value=0.65,
            unit="score_0_1",
            severity_at_threshold=SignalSeverity.HIGH,
            historical_frequency=(
                "Elevated severity events near Hormuz: ~4-6 per year (tanker "
                "seizures, naval exercises, drone incidents). HIGH severity "
                "(≥0.65) events that actually impede transit: ~1 per 2-3 years."
            ),
            calibration_note=(
                "0.65 aligns with the HIGH band in the URS classification "
                "(config.py). Below this, events are concerning but traffic "
                "typically flows. At 0.65+, insurance underwriters begin "
                "restricting coverage or adding war risk premiums."
            ),
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="SUPPLY_CHAIN_DISRUPTION",
            description=(
                "Hormuz disruption → oil tanker transit halted → spot price "
                "spike → container shipping rerouted → 14-21 day delay via "
                "Cape of Good Hope → inventory shortfalls in importing nations."
            ),
            description_ar=(
                "اضطراب هرمز → توقف عبور ناقلات النفط → ارتفاع حاد في السعر "
                "الفوري → إعادة توجيه الشحن عبر رأس الرجاء الصالح → تأخير "
                "١٤-٢١ يوم → نقص المخزون"
            ),
            propagation_hops=3,
            attenuation_per_hop=0.9,
            estimated_lag_hours=6.0,
            intermediate_entities=["AE-JEBEL-ALI", "OM-SOHAR", "KW-SHUAIBA"],
            evidence_basis=(
                "2019 tanker attacks: Brent spiked 15% in 24 hours. Shipping "
                "insurance premiums tripled for Hormuz transit within 48 hours. "
                "2024 Houthi Red Sea: ~50% traffic rerouted, adding $1M+ per "
                "container ship voyage."
            ),
        ),
        TransmissionSpec(
            mechanism="INSURANCE_LOSS_CASCADE",
            description=(
                "Hormuz disruption → marine war risk premium spike → "
                "hull/cargo claims on affected vessels → reinsurance "
                "retrocession activation → P&I club capital calls."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.85,
            estimated_lag_hours=24.0,
            evidence_basis=(
                "2019: Lloyd's Market Association listed Persian Gulf as "
                "Enhanced Risk Area. War risk premiums jumped from 0.025% "
                "to 0.5% of hull value within 72 hours."
            ),
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="entity_type:PORT AND chokepoint_dependency:STRAIT_OF_HORMUZ",
            exposure_type="DIRECT",
            impact_description=(
                "Ports dependent on Hormuz transit face immediate throughput "
                "collapse. Cannot reroute — Hormuz is the only exit for the "
                "Arabian Gulf."
            ),
            key_metrics_at_risk=["annual_throughput_teu", "vessel_calls_annual", "utilization_pct"],
        ),
        AffectedEntitySpec(
            entity_pattern="entity_type:LNG_TERMINAL AND country:QA",
            exposure_type="DIRECT",
            impact_description=(
                "Qatar's LNG exports (~77M tonnes/year) transit entirely "
                "through Hormuz. Full closure halts all exports."
            ),
            key_metrics_at_risk=["annual_cargo_tonnage"],
        ),
        AffectedEntitySpec(
            entity_pattern="sector:INSURANCE",
            exposure_type="INDIRECT",
            impact_description=(
                "Marine insurers face war risk claims. Reinsurers face "
                "retrocession activation. P&I clubs may issue capital calls."
            ),
            key_metrics_at_risk=["combined_ratio_pct", "net_claims_incurred"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.ENERGY,
            impact_magnitude="CRITICAL",
            impact_channel="Oil/LNG export halt — 21% of global oil supply at risk",
            estimated_gdp_drag_pct=8.0,
        ),
        SectorImpactSpec(
            sector=Sector.MARITIME,
            impact_magnitude="CRITICAL",
            impact_channel="Port throughput collapse + shipping rerouting costs",
            estimated_gdp_drag_pct=3.0,
        ),
        SectorImpactSpec(
            sector=Sector.LOGISTICS,
            impact_magnitude="HIGH",
            impact_channel="Supply chain delays — 14-21 day rerouting via Cape",
        ),
        SectorImpactSpec(
            sector=Sector.INSURANCE,
            impact_magnitude="HIGH",
            impact_channel="Marine war risk claims + premium spike",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.ACTIVATE_CONTINGENCY,
        action_params={
            "contingency_type": "HORMUZ_DISRUPTION_PROTOCOL",
            "activate_strategic_reserve_monitoring": True,
            "trigger_insurance_war_risk_assessment": True,
            "alert_port_authorities": ["AE-JEBEL-ALI", "OM-SOHAR", "KW-SHUAIBA"],
            "activate_alternative_route_planning": True,
        },
        escalation_level=RiskLevel.SEVERE,
        requires_human_approval=True,
        approval_authority="Board",
        time_to_act_hours=1.0,
        fallback_action=DecisionAction.ESCALATE,
        related_scenario_ids=["hormuz_chokepoint_disruption", "hormuz_full_closure"],
    ),

    confidence=ConfidenceBasis(
        methodology=(
            "Event severity scoring calibrated against historical Hormuz incidents "
            "(2019 tanker attacks, 2020 Iranian naval exercises, 2024 regional "
            "tensions). Transmission paths validated against 2024 Red Sea disruption "
            "as a Hormuz analogy."
        ),
        data_sources=["acled-api", "port-authority-data", "opec-momr"],
        back_test_period="2019-05 to 2024-12",
        false_positive_rate=0.05,
        false_negative_rate=0.02,
        confidence_score=0.90,
        limitations=[
            "Severity scoring depends on event signal quality and classification speed",
            "Full Hormuz closure has never occurred — impact estimates are modeled, not observed",
            "Military/geopolitical escalation paths are unpredictable",
        ],
        next_review_date=date(2026, 3, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "Hormuz-related event detected at severity {event_signals.severity_score} "
            "(HIGH threshold: 0.65). Activating Hormuz disruption contingency protocol."
        ),
        summary_ar=(
            "تم رصد حدث متعلق بهرمز بدرجة شدة {event_signals.severity_score} "
            "(عتبة مرتفع: ٠.٦٥). تفعيل بروتوكول طوارئ اضطراب هرمز."
        ),
        detail_en=(
            "SIGNAL: Event '{title}' detected at severity {event_signals.severity_score}. "
            "Category: {category}. Countries affected: {countries_affected}.\n\n"
            "CHOKEPOINT IMPACT: Strait of Hormuz carries 21% of global oil transit. "
            "A disruption at this severity level has historically triggered 10-20% "
            "oil price spikes within 24 hours.\n\n"
            "IMMEDIATE ACTIONS: Activate strategic reserve monitoring, trigger "
            "insurance war risk reassessment, alert port authorities, evaluate "
            "alternative routing via Fujairah/Oman bypass."
        ),
        dashboard_label="HORMUZ DISRUPTION — Contingency Active",
        dashboard_label_ar="اضطراب هرمز — طوارئ مفعّلة",
    ),

    exclusions=[
        Exclusion(
            exclusion_id="EXCL-HORMUZ-001",
            description=(
                "Do not trigger for pre-announced naval exercises. These are "
                "routine and disclosed through official military channels."
            ),
            condition_field="event_signals.subcategory",
            condition_operator="eq",
            condition_value="naval_exercise",
            reason_code="SCHEDULED_MAINTENANCE",
        ),
    ],

    applicable_countries=[
        GCCCountry.KW, GCCCountry.QA, GCCCountry.BH,
        GCCCountry.AE, GCCCountry.SA, GCCCountry.OM,
    ],
    applicable_sectors=[Sector.ENERGY, Sector.MARITIME, Sector.LOGISTICS, Sector.INSURANCE],
    applicable_scenarios=["hormuz_chokepoint_disruption", "hormuz_full_closure"],
    applicable_event_categories=[EventCategory.GEOPOLITICAL, EventCategory.CONFLICT],
    cooldown_minutes=360,
    max_concurrent_triggers=1,

    audit=SpecAuditRecord(
        authored_by="Geopolitical Risk Team",
        authored_at=datetime(2025, 2, 15, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 2, 20, tzinfo=timezone.utc),
        approved_by="Board",
        approved_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
        change_summary="Initial version — Hormuz disruption detection and contingency activation",
    ),

    tags=["hormuz", "chokepoint", "geopolitical", "tier-1", "maritime"],
    source_dataset_ids=["p1_event_signals", "p1_logistics_nodes", "p1_oil_energy_signals"],
)


_PORT_OVERLOAD = RuleSpec(
    spec_id="SPEC-LOGISTICS-PORT-OVERLOAD-v1",
    spec_version="1.0.0",
    family="logistics-disruption",
    variant="port-overload",

    name="Major GCC Port Utilization Exceeds 95%",
    name_ar="استخدام ميناء رئيسي في مجلس التعاون يتجاوز ٩٥٪",
    description=(
        "Triggers when any major GCC port reaches 95%+ utilization, "
        "indicating congestion risk. At this level, any minor disruption "
        "(weather, equipment failure, labor shortage) can cascade into "
        "multi-day backlogs. Particularly critical for Jebel Ali which "
        "handles ~15M TEU and serves as the primary transshipment hub "
        "for the entire GCC."
    ),
    status="ACTIVE",
    effective_date=date(2025, 3, 1),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="logistics_nodes.utilization_pct",
            signal_name="Port Utilization %",
            signal_name_ar="نسبة استخدام الميناء",
            source_dataset="p1_logistics_nodes",
            unit="percent",
            monitoring_frequency="WEEKLY",
            baseline_value=75.0,
            baseline_source="GCC major port average utilization 2020-2024",
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="logistics_nodes.utilization_pct",
            operator="gte",
            value=95.0,
            unit="percent",
            severity_at_threshold=SignalSeverity.ELEVATED,
            historical_frequency=(
                "Major GCC ports hit 90%+ utilization 2-3 times per year, "
                "typically during Q4 peak season. 95%+ is rare — ~once per "
                "2 years, usually coinciding with regional disruptions."
            ),
            calibration_note=(
                "95% is the industry-standard congestion warning threshold. "
                "Above this, vessel waiting times increase exponentially."
            ),
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="SUPPLY_CHAIN_DISRUPTION",
            description=(
                "Port congestion → vessel queue buildup → container dwell "
                "time increase → inventory shortfalls for importers → "
                "retail/manufacturing delays."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.8,
            estimated_lag_hours=72.0,
            evidence_basis=(
                "2021 global port congestion: Average dwell time at congested "
                "ports increased from 5 to 14 days. Shipping costs tripled."
            ),
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="entity_type:PORT AND transport_mode:MARITIME",
            exposure_type="DIRECT",
            impact_description="Congested port and connected downstream ports face cascade.",
            key_metrics_at_risk=["utilization_pct", "annual_throughput_teu"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.LOGISTICS,
            impact_magnitude="HIGH",
            impact_channel="Throughput bottleneck + demurrage costs",
        ),
        SectorImpactSpec(
            sector=Sector.MARITIME,
            impact_magnitude="MODERATE",
            impact_channel="Vessel waiting time increase + schedule disruption",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.ALERT,
        action_params={
            "alert_type": "PORT_CONGESTION",
            "alert_recipients": ["logistics-ops", "supply-chain-risk"],
            "recommend_diversion_assessment": True,
        },
        escalation_level=RiskLevel.ELEVATED,
        requires_human_approval=False,
        time_to_act_hours=12.0,
        related_scenario_ids=["critical_port_throughput_disruption"],
    ),

    confidence=ConfidenceBasis(
        methodology="Port utilization data from port authority reporting.",
        data_sources=["port-authority-data"],
        confidence_score=0.82,
        limitations=["Utilization data may lag 1-7 days depending on port"],
        next_review_date=date(2026, 6, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "Port utilization at {logistics_nodes.utilization_pct}%, exceeding "
            "the 95% congestion threshold. Congestion alert issued."
        ),
        summary_ar=(
            "استخدام الميناء عند {logistics_nodes.utilization_pct}٪، متجاوزاً "
            "عتبة الازدحام ٩٥٪. تم إصدار تنبيه ازدحام."
        ),
        dashboard_label="PORT >95% — Congestion Alert",
        dashboard_label_ar="ميناء >٩٥٪ — تنبيه ازدحام",
    ),

    exclusions=[
        Exclusion(
            exclusion_id="EXCL-PORT-001",
            description="Do not trigger during known scheduled maintenance windows.",
            condition_field="logistics_nodes.operational_status",
            condition_operator="eq",
            condition_value="UNDER_CONSTRUCTION",
            reason_code="SCHEDULED_MAINTENANCE",
        ),
    ],

    applicable_countries=[
        GCCCountry.AE, GCCCountry.SA, GCCCountry.OM, GCCCountry.KW, GCCCountry.QA, GCCCountry.BH,
    ],
    applicable_sectors=[Sector.LOGISTICS, Sector.MARITIME],
    applicable_scenarios=["critical_port_throughput_disruption", "oman_port_closure"],
    cooldown_minutes=120,

    audit=SpecAuditRecord(
        authored_by="Supply Chain Risk Team",
        authored_at=datetime(2025, 2, 15, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 2, 25, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
        change_summary="Initial version — port congestion detection",
    ),

    tags=["logistics", "port", "congestion", "tier-2"],
    source_dataset_ids=["p1_logistics_nodes"],
)


LOGISTICS_DISRUPTION_SPECS = [_HORMUZ_CLOSURE, _PORT_OVERLOAD]
