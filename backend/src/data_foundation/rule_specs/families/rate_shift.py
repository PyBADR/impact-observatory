"""
Rate Shift Rule Family | عائلة قواعد تحول الفائدة
=====================================================

Policy domain: Central bank rate changes that affect GCC credit conditions.

GCC context:
  - All GCC currencies except KWD are pegged to USD → GCC central banks
    largely follow Fed rate moves within days
  - KWD uses a basket peg (USD-dominant) → CBK has limited independent
    policy space but often moves within 25bps of Fed
  - A surprise CBK rate change (outside scheduled meetings) signals
    extreme monetary stress
  - Rate increases transmit directly to bank funding costs, mortgage
    rates, and corporate borrowing

Variants:
  SPEC-RATE-CBK-HIKE-SURPRISE-v1 — Unscheduled CBK discount rate increase
  SPEC-RATE-GCC-DIVERGENCE-v1    — GCC rate diverges from Fed by >100bps
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
    GCCCountry,
    RiskLevel,
    Sector,
    SignalSeverity,
)

__all__ = ["RATE_SHIFT_SPECS"]


_CBK_HIKE_SURPRISE = RuleSpec(
    spec_id="SPEC-RATE-CBK-HIKE-SURPRISE-v1",
    spec_version="1.0.0",
    family="rate-shift",
    variant="cbk-hike-surprise",

    name="Unscheduled CBK Discount Rate Increase",
    name_ar="رفع غير مجدول لسعر الخصم من البنك المركزي الكويتي",
    description=(
        "Triggers when the CBK discount rate increases by 50bps or more "
        "outside of a scheduled policy meeting. An unscheduled rate hike "
        "signals that CBK is responding to an acute threat — capital "
        "outflow pressure, currency defense, or systemic banking stress. "
        "This has never occurred in CBK history, making it a tail risk "
        "indicator of the highest severity."
    ),
    status="ACTIVE",
    effective_date=date(2025, 2, 1),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="interest_rate_signals.change_bps",
            signal_name="CBK Discount Rate Change (bps)",
            signal_name_ar="تغير سعر الخصم (نقاط أساس)",
            source_dataset="p1_interest_rate_signals",
            unit="basis_points",
            monitoring_frequency="DAILY",
            baseline_value=0,
            baseline_source="CBK scheduled policy meeting cadence",
        ),
        TriggerSignalSpec(
            signal_field="interest_rate_signals.is_scheduled_decision",
            signal_name="Is Scheduled Decision Flag",
            source_dataset="p1_interest_rate_signals",
            unit="boolean",
            monitoring_frequency="DAILY",
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="interest_rate_signals.change_bps",
            operator="gte",
            value=50,
            unit="basis_points",
            severity_at_threshold=SignalSeverity.SEVERE,
            historical_frequency=(
                "CBK has never made an unscheduled rate change. Scheduled "
                "changes are typically 25bps. A 50bps unscheduled move would "
                "be unprecedented."
            ),
            calibration_note=(
                "50bps chosen as double the normal 25bps increment. This "
                "filters out routine scheduled adjustments that might be "
                "slightly larger than usual."
            ),
        ),
        ThresholdSpec(
            field="interest_rate_signals.is_scheduled_decision",
            operator="eq",
            value=False,
            severity_at_threshold=SignalSeverity.SEVERE,
            historical_frequency="N/A — defines the 'surprise' qualifier",
            calibration_note="Separates emergency action from routine policy.",
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="CREDIT_CHANNEL",
            description=(
                "Surprise rate hike → immediate increase in bank funding costs → "
                "repricing of floating-rate loans → corporate stress for leveraged "
                "borrowers → potential NPL increase."
            ),
            description_ar=(
                "رفع مفاجئ → ارتفاع فوري في تكلفة تمويل البنوك → إعادة تسعير "
                "القروض المتغيرة → ضغط على الشركات المقترضة → ارتفاع محتمل في القروض المتعثرة"
            ),
            propagation_hops=2,
            attenuation_per_hop=0.9,
            estimated_lag_hours=48.0,
            intermediate_entities=["KW-CBK"],
            evidence_basis=(
                "Historical: When central banks make unscheduled moves (Fed in March 2020, "
                "BOE in October 2022), banking sector CDS spreads widen 20-50bps within 48 hours."
            ),
        ),
        TransmissionSpec(
            mechanism="MARKET_CONTAGION",
            description=(
                "Surprise hike signals defensive posture → market interprets as "
                "crisis signal → equity sell-off → KSE/Boursa decline → portfolio "
                "losses for banks and insurers."
            ),
            propagation_hops=1,
            attenuation_per_hop=0.8,
            estimated_lag_hours=2.0,
            evidence_basis="Signaling channel — unscheduled moves amplify uncertainty.",
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_id="KW-CBK",
            exposure_type="DIRECT",
            impact_description="CBK itself is the actor — monitoring for follow-up actions.",
            key_metrics_at_risk=["CBK_DISCOUNT_RATE", "RESERVE_ASSETS"],
        ),
        AffectedEntitySpec(
            entity_pattern="entity_type:COMMERCIAL_BANK AND country:KW",
            exposure_type="DIRECT",
            impact_description=(
                "All Kuwaiti commercial banks face immediate funding cost increase "
                "and potential repricing of their entire floating-rate book."
            ),
            key_metrics_at_risk=["nim_pct", "npl_ratio_pct", "car_pct", "lcr_pct"],
        ),
        AffectedEntitySpec(
            entity_pattern="sector:INSURANCE AND country:KW",
            exposure_type="INDIRECT",
            impact_description=(
                "Insurance companies with bond portfolios face mark-to-market "
                "losses. Investment yield improves long-term but short-term "
                "unrealized losses hit solvency ratios."
            ),
            key_metrics_at_risk=["solvency_ratio_pct", "investment_yield_pct"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.BANKING,
            impact_magnitude="CRITICAL",
            impact_channel="Cost of funding increase + floating-rate loan repricing",
            estimated_gdp_drag_pct=0.5,
        ),
        SectorImpactSpec(
            sector=Sector.INSURANCE,
            impact_magnitude="MODERATE",
            impact_channel="Bond portfolio mark-to-market losses",
        ),
        SectorImpactSpec(
            sector=Sector.REAL_ESTATE,
            impact_magnitude="HIGH",
            impact_channel="Mortgage rate increase → demand compression",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.ESCALATE,
        action_params={
            "escalate_to": "Risk Committee",
            "banking_stress_test_required": True,
            "insurance_bond_portfolio_review": True,
            "real_estate_exposure_assessment": True,
        },
        escalation_level=RiskLevel.SEVERE,
        requires_human_approval=True,
        approval_authority="CRO",
        time_to_act_hours=2.0,
        fallback_action=DecisionAction.ALERT,
        related_scenario_ids=["kuwait_fiscal_shock"],
    ),

    confidence=ConfidenceBasis(
        methodology=(
            "Expert judgment based on GCC central bank behavior patterns. "
            "No direct historical precedent for CBK surprise hike — calibrated "
            "from Fed (March 2020) and BOE (October 2022) emergency actions."
        ),
        data_sources=["cbk-statistical-bulletin", "gcc-central-banks"],
        false_positive_rate=0.001,
        false_negative_rate=0.10,
        confidence_score=0.85,
        limitations=[
            "No CBK precedent — confidence based on other central bank analogy",
            "is_scheduled_decision flag requires reliable tagging in ingestion",
        ],
        next_review_date=date(2026, 6, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "CBK raised the discount rate by {interest_rate_signals.change_bps}bps "
            "outside a scheduled meeting — signaling acute monetary stress. "
            "Escalating to Risk Committee for immediate banking sector assessment."
        ),
        summary_ar=(
            "رفع البنك المركزي الكويتي سعر الخصم بمقدار {interest_rate_signals.change_bps} "
            "نقطة أساس خارج اجتماع مجدول — إشارة ضغط نقدي حاد. التصعيد إلى "
            "لجنة المخاطر لتقييم فوري للقطاع المصرفي."
        ),
        dashboard_label="CBK SURPRISE HIKE — Risk Escalation",
        dashboard_label_ar="رفع مفاجئ CBK — تصعيد مخاطر",
    ),

    exclusions=[
        Exclusion(
            exclusion_id="EXCL-RATE-001",
            description=(
                "Do not trigger for scheduled policy meeting decisions, even if "
                "the rate change exceeds 50bps. Scheduled decisions are priced in."
            ),
            condition_field="interest_rate_signals.is_scheduled_decision",
            condition_operator="eq",
            condition_value=True,
            reason_code="SCHEDULED_DECISION",
        ),
    ],

    applicable_countries=[GCCCountry.KW],
    applicable_sectors=[Sector.BANKING, Sector.INSURANCE, Sector.REAL_ESTATE],
    applicable_scenarios=["kuwait_fiscal_shock"],
    cooldown_minutes=720,
    max_concurrent_triggers=1,

    audit=SpecAuditRecord(
        authored_by="Risk Analytics Team",
        authored_at=datetime(2025, 1, 20, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 1, 25, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        change_summary="Initial version — CBK surprise rate hike detection",
    ),

    tags=["interest-rate", "cbk", "surprise", "tier-1", "kuwait"],
    source_dataset_ids=["p1_interest_rate_signals", "p1_cbk_indicators"],
)


_GCC_FED_DIVERGENCE = RuleSpec(
    spec_id="SPEC-RATE-GCC-DIVERGENCE-v1",
    spec_version="1.0.0",
    family="rate-shift",
    variant="gcc-fed-divergence",

    name="GCC-Fed Rate Spread Exceeds 100bps",
    name_ar="فارق أسعار الفائدة بين مجلس التعاون والاحتياطي الفيدرالي يتجاوز ١٠٠ نقطة أساس",
    description=(
        "Triggers when the spread between any GCC central bank policy rate "
        "and the Fed Funds rate exceeds 100bps. GCC pegged currencies "
        "require rate alignment — divergence creates carry trade pressure, "
        "capital flow risks, and peg sustainability questions."
    ),
    status="ACTIVE",
    effective_date=date(2025, 2, 1),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="interest_rate_signals.spread_to_reference_bps",
            signal_name="Spread to Fed Funds Rate (bps)",
            source_dataset="p1_interest_rate_signals",
            unit="basis_points",
            monitoring_frequency="DAILY",
            baseline_value=25,
            baseline_source="Historical average GCC-Fed spread (2015-2024)",
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="interest_rate_signals.spread_to_reference_bps",
            operator="exceeds_threshold",
            value=100,
            unit="basis_points",
            severity_at_threshold=SignalSeverity.ELEVATED,
            historical_frequency="Rare — ~1-2 times per rate cycle",
            calibration_note=(
                "100bps divergence creates meaningful carry trade incentive. "
                "Below 100bps, spread is within normal policy calibration range."
            ),
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="CROSS_BORDER_SPILLOVER",
            description=(
                "Rate divergence → carry trade flows → foreign reserve pressure → "
                "potential peg defense intervention → liquidity tightening."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.75,
            estimated_lag_hours=168.0,
            evidence_basis=(
                "2006-2007: GCC-Fed divergence led to speculative KWD revaluation "
                "pressure. Kuwait eventually revalued by 1% in May 2007."
            ),
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="entity_type:CENTRAL_BANK",
            exposure_type="DIRECT",
            impact_description="Central banks face foreign reserve pressure from capital flows.",
            key_metrics_at_risk=["RESERVE_ASSETS", "FOREIGN_ASSETS"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.BANKING,
            impact_magnitude="MODERATE",
            impact_channel="Interest rate margin compression from divergence",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.MONITOR,
        action_params={
            "monitoring_type": "RATE_DIVERGENCE",
            "alert_if_widens_further": True,
            "escalate_at_bps": 150,
        },
        escalation_level=RiskLevel.ELEVATED,
        requires_human_approval=False,
        time_to_act_hours=48.0,
    ),

    confidence=ConfidenceBasis(
        methodology="Historical spread analysis against Fed Funds rate 2015-2025.",
        data_sources=["gcc-central-banks", "cbk-statistical-bulletin"],
        confidence_score=0.80,
        limitations=["KWD basket peg complicates direct Fed comparison"],
        next_review_date=date(2026, 6, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "GCC-Fed rate spread widened to {interest_rate_signals.spread_to_reference_bps}bps, "
            "exceeding the 100bps monitoring threshold. Capital flow risk elevated."
        ),
        summary_ar=(
            "اتسع فارق أسعار الفائدة بين مجلس التعاون والفيدرالي إلى "
            "{interest_rate_signals.spread_to_reference_bps} نقطة أساس، "
            "متجاوزاً عتبة المراقبة البالغة ١٠٠ نقطة أساس."
        ),
        dashboard_label="GCC-Fed Spread >100bps — Monitoring",
        dashboard_label_ar="فارق مجلس التعاون-الفيدرالي >١٠٠ — مراقبة",
    ),

    exclusions=[],
    applicable_countries=[
        GCCCountry.SA, GCCCountry.AE, GCCCountry.KW,
        GCCCountry.QA, GCCCountry.BH, GCCCountry.OM,
    ],
    applicable_sectors=[Sector.BANKING],
    applicable_scenarios=["regional_liquidity_stress_event"],
    cooldown_minutes=240,

    audit=SpecAuditRecord(
        authored_by="Risk Analytics Team",
        authored_at=datetime(2025, 1, 20, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 1, 28, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        change_summary="Initial version — GCC-Fed rate divergence monitoring",
    ),

    tags=["interest-rate", "fed", "divergence", "peg-risk", "tier-2"],
    source_dataset_ids=["p1_interest_rate_signals"],
)


RATE_SHIFT_SPECS = [_CBK_HIKE_SURPRISE, _GCC_FED_DIVERGENCE]
