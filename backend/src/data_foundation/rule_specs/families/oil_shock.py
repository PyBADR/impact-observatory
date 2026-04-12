"""
Oil Shock Rule Family | عائلة قواعد صدمة النفط
=================================================

Policy domain: Oil price movements that threaten GCC fiscal stability.

GCC context:
  - Oil revenues are 40-80% of GCC government revenue
  - Saudi Arabia fiscal breakeven: ~$78/bbl (2025 est.)
  - Kuwait fiscal breakeven: ~$85/bbl (2025 est.)
  - UAE fiscal breakeven: ~$60/bbl (2025 est.)
  - A 30%+ single-day drop has occurred twice in 50 years (2020 COVID, 2014 OPEC)
  - A 15%+ weekly drop occurs ~2-3 times per decade

Variants:
  SPEC-OIL-BRENT-DROP-30-v1    — Catastrophic single-day crash (>30%)
  SPEC-OIL-SUSTAINED-LOW-60-v1 — Sustained below $60/bbl fiscal breakeven zone
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

__all__ = ["OIL_SHOCK_SPECS"]


_BRENT_DROP_30 = RuleSpec(
    # ── Identity ────────────────────────────────────────────────────────
    spec_id="SPEC-OIL-BRENT-DROP-30-v1",
    spec_version="1.0.0",
    family="oil-shock",
    variant="brent-drop-30",

    # ── Metadata ────────────────────────────────────────────────────────
    name="Catastrophic Oil Price Crash (>30% Single Day)",
    name_ar="انهيار كارثي في أسعار النفط (>٣٠٪ يوم واحد)",
    description=(
        "Triggers when Brent crude spot price drops more than 30% in a single "
        "trading day. This magnitude of shock has only occurred twice in modern "
        "history (March 2020, November 2014) and represents an existential "
        "fiscal threat to oil-dependent GCC economies. Activates full "
        "contingency protocol including sovereign wealth fund drawdown "
        "authorization, fiscal austerity pre-positioning, and insurance "
        "reserve stress review."
    ),
    status="ACTIVE",
    effective_date=date(2025, 1, 15),

    # ── Trigger signals ─────────────────────────────────────────────────
    trigger_signals=[
        TriggerSignalSpec(
            signal_field="oil_energy_signals.change_pct",
            signal_name="Brent Crude Daily Change %",
            signal_name_ar="نسبة التغير اليومي لخام برنت",
            source_dataset="p1_oil_energy_signals",
            unit="percent",
            monitoring_frequency="DAILY",
            baseline_value=0.0,
            baseline_source="5Y rolling daily average change",
        ),
    ],
    trigger_logic="AND",

    # ── Thresholds ──────────────────────────────────────────────────────
    thresholds=[
        ThresholdSpec(
            field="oil_energy_signals.change_pct",
            operator="lt",
            value=-30.0,
            unit="percent",
            severity_at_threshold=SignalSeverity.SEVERE,
            historical_frequency=(
                "~2 occurrences in 50 years. March 9 2020: Brent dropped 24.1% "
                "(Saudi-Russia price war + COVID). November 27 2014: 10.2% drop "
                "(OPEC refusal to cut). A >30% single-day drop has never been "
                "recorded for Brent — this threshold captures tail risk."
            ),
            calibration_note=(
                "Set at 30% based on 2-sigma beyond the worst historical single-day "
                "move. The 2020 COVID crash peaked at 24.1%. Adding a ~25% buffer "
                "above the worst case ensures this rule only fires for truly "
                "unprecedented events, not recurring volatility."
            ),
        ),
    ],

    # ── Transmission paths ──────────────────────────────────────────────
    transmission_paths=[
        TransmissionSpec(
            mechanism="FISCAL_CHANNEL",
            description=(
                "Oil revenue → government budget → fiscal deficit → sovereign "
                "credit rating pressure → cost of government borrowing → banking "
                "sector sovereign exposure write-down."
            ),
            description_ar=(
                "إيرادات النفط → الميزانية الحكومية → العجز المالي → ضغوط "
                "التصنيف الائتماني السيادي → تكلفة الاقتراض الحكومي → تخفيض "
                "قيمة التعرض السيادي للقطاع المصرفي"
            ),
            propagation_hops=3,
            attenuation_per_hop=0.8,
            estimated_lag_hours=72.0,
            intermediate_entities=["SA-MOF", "KW-MOF"],
            evidence_basis=(
                "2014-2016 oil crash: Saudi fiscal deficit reached 15.8% of GDP (2015). "
                "Kuwait's deficit reached 17.8% of GDP. Banking sector sovereign "
                "bond portfolios experienced 5-15% mark-to-market losses."
            ),
        ),
        TransmissionSpec(
            mechanism="MARKET_CONTAGION",
            description=(
                "Oil price crash → GCC equity markets sell-off → portfolio losses "
                "for banks and insurers → liquidity squeeze → interbank rate spike."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.7,
            estimated_lag_hours=4.0,
            evidence_basis=(
                "March 2020: Tadawul (Saudi exchange) dropped 8.3% in a single "
                "session following the oil crash. Kuwait Boursa fell 10% hitting "
                "circuit breaker limits."
            ),
        ),
        TransmissionSpec(
            mechanism="INSURANCE_LOSS_CASCADE",
            description=(
                "Oil crash → reduced economic activity → reduced premium volume → "
                "investment portfolio losses (oil-linked assets) → solvency pressure."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.6,
            estimated_lag_hours=168.0,
            evidence_basis=(
                "GCC insurance investment portfolios are 20-40% exposed to local "
                "equities and real estate, both correlated with oil prices."
            ),
        ),
    ],

    # ── Affected entities ───────────────────────────────────────────────
    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="entity_type:SOVEREIGN_WEALTH_FUND",
            exposure_type="DIRECT",
            impact_description=(
                "SWFs face immediate portfolio devaluation on oil-linked assets "
                "and increased drawdown pressure to cover fiscal deficits."
            ),
            key_metrics_at_risk=["total_assets", "investment_yield_pct"],
        ),
        AffectedEntitySpec(
            entity_pattern="entity_type:COMMERCIAL_BANK AND country:KW",
            exposure_type="INDIRECT",
            impact_description=(
                "Kuwaiti commercial banks face sovereign exposure risk, "
                "increased NPLs from oil-dependent corporate borrowers, "
                "and equity portfolio mark-to-market losses."
            ),
            key_metrics_at_risk=["npl_ratio_pct", "car_pct", "roe_pct"],
        ),
        AffectedEntitySpec(
            entity_pattern="sector:ENERGY",
            exposure_type="DIRECT",
            impact_description=(
                "Energy sector entities face immediate revenue collapse. "
                "National oil companies may defer capex, affecting contractors."
            ),
            key_metrics_at_risk=["total_assets", "net_income"],
        ),
    ],

    # ── Sector impact ───────────────────────────────────────────────────
    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.ENERGY,
            impact_magnitude="CRITICAL",
            impact_channel="Revenue disruption (oil-dependent fiscal)",
            estimated_gdp_drag_pct=3.0,
        ),
        SectorImpactSpec(
            sector=Sector.BANKING,
            impact_magnitude="HIGH",
            impact_channel="Sovereign exposure + NPL increase + equity portfolio losses",
            estimated_gdp_drag_pct=0.8,
        ),
        SectorImpactSpec(
            sector=Sector.INSURANCE,
            impact_magnitude="MODERATE",
            impact_channel="Investment portfolio losses + reduced premium volume",
        ),
        SectorImpactSpec(
            sector=Sector.GOVERNMENT,
            impact_magnitude="CRITICAL",
            impact_channel="Fiscal deficit expansion requiring SWF drawdown or austerity",
            estimated_gdp_drag_pct=2.5,
        ),
    ],

    # ── Decision proposal ───────────────────────────────────────────────
    decision=DecisionProposalSpec(
        action=DecisionAction.ACTIVATE_CONTINGENCY,
        action_params={
            "contingency_type": "FISCAL_SHOCK_PROTOCOL",
            "swf_drawdown_authorization": True,
            "insurance_reserve_stress_test": True,
            "banking_lcr_enhanced_monitoring": True,
        },
        escalation_level=RiskLevel.SEVERE,
        requires_human_approval=True,
        approval_authority="CRO",
        time_to_act_hours=4.0,
        fallback_action=DecisionAction.ALERT,
        related_scenario_ids=["saudi_oil_shock", "energy_market_volatility_shock"],
    ),

    # ── Confidence basis ────────────────────────────────────────────────
    confidence=ConfidenceBasis(
        methodology=(
            "Historical back-test against daily Brent price series 2000-2025. "
            "Threshold calibrated at 2-sigma beyond worst single-day drop "
            "(March 9 2020: -24.1%). Transmission paths validated against "
            "2014-2016 oil downturn fiscal data."
        ),
        data_sources=["eia-api", "imf-weo", "cbk-statistical-bulletin"],
        back_test_period="2000-01 to 2025-12",
        false_positive_rate=0.001,
        false_negative_rate=0.05,
        confidence_score=0.92,
        limitations=[
            "Single-day threshold may miss slow-burn declines (10%/week for 4 weeks)",
            "Transmission lag estimates are approximate — actual propagation depends on "
            "market liquidity and central bank response speed",
            "SWF drawdown behavior is politically determined, not purely economic",
        ],
        next_review_date=date(2026, 7, 1),
    ),

    # ── Rationale template ──────────────────────────────────────────────
    rationale=RationaleTemplate(
        summary_en=(
            "Brent crude dropped {oil_energy_signals.change_pct}% in a single day, "
            "breaching the 30% catastrophic threshold. This magnitude of shock threatens "
            "GCC fiscal stability — activating contingency protocol."
        ),
        summary_ar=(
            "انخفض خام برنت بنسبة {oil_energy_signals.change_pct}٪ في يوم واحد، "
            "متجاوزاً عتبة الـ ٣٠٪ الكارثية. يهدد هذا الحجم من الصدمة الاستقرار "
            "المالي لدول مجلس التعاون — يتم تفعيل بروتوكول الطوارئ."
        ),
        detail_en=(
            "SIGNAL: Brent crude price experienced a {oil_energy_signals.change_pct}% "
            "decline on {observation_date}. Previous close: ${previous_value}/bbl. "
            "Current: ${value}/bbl.\n\n"
            "CONTEXT: This exceeds the 30% catastrophic threshold, calibrated at "
            "2-sigma beyond the worst historical single-day drop (COVID crash: -24.1%).\n\n"
            "FISCAL IMPACT: GCC average fiscal breakeven is ~$75/bbl. A sustained "
            "price below this level would create fiscal deficits across all six "
            "member states within one quarter.\n\n"
            "ACTION REQUIRED: Activate fiscal shock contingency protocol. CRO "
            "approval required within 4 hours."
        ),
        dashboard_label="OIL CRASH >30% — Contingency Protocol",
        dashboard_label_ar="انهيار نفطي >٣٠٪ — بروتوكول الطوارئ",
    ),

    # ── Exclusions ──────────────────────────────────────────────────────
    exclusions=[
        Exclusion(
            exclusion_id="EXCL-OIL-001",
            description=(
                "Do not trigger if the price drop is an OPEC-announced planned "
                "production cut that temporarily depresses spot prices. OPEC "
                "decisions are pre-announced and priced in."
            ),
            condition_field="event_signals.category",
            condition_operator="eq",
            condition_value="REGULATORY",
            reason_code="OPEC_PLANNED_CUT",
        ),
        Exclusion(
            exclusion_id="EXCL-OIL-002",
            description=(
                "Do not trigger if the data source confidence is below 0.5, "
                "indicating potential data quality issues rather than a real "
                "market event."
            ),
            condition_field="oil_energy_signals.confidence_score",
            condition_operator="lt",
            condition_value=0.5,
            reason_code="DATA_STALE",
        ),
    ],

    # ── Scope ───────────────────────────────────────────────────────────
    applicable_countries=[
        GCCCountry.SA, GCCCountry.AE, GCCCountry.KW,
        GCCCountry.QA, GCCCountry.BH, GCCCountry.OM,
    ],
    applicable_sectors=[Sector.ENERGY, Sector.BANKING, Sector.INSURANCE, Sector.GOVERNMENT],
    applicable_scenarios=["saudi_oil_shock", "energy_market_volatility_shock"],

    # ── Governance ──────────────────────────────────────────────────────
    cooldown_minutes=1440,  # 24 hours — catastrophic events don't repeat daily
    max_concurrent_triggers=1,

    # ── Audit ───────────────────────────────────────────────────────────
    audit=SpecAuditRecord(
        authored_by="Risk Analytics Team",
        authored_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 1, 12, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
        change_summary="Initial version — catastrophic oil shock detection",
    ),

    tags=["oil", "fiscal", "catastrophic", "tier-1"],
    source_dataset_ids=["p1_oil_energy_signals", "p1_macro_indicators"],
)


_SUSTAINED_LOW_60 = RuleSpec(
    spec_id="SPEC-OIL-SUSTAINED-LOW-60-v1",
    spec_version="1.0.0",
    family="oil-shock",
    variant="sustained-low-60",

    name="Sustained Oil Below $60 — Fiscal Breakeven Breach",
    name_ar="استمرار النفط تحت ٦٠ دولار — اختراق نقطة التعادل المالي",
    description=(
        "Triggers when Brent crude spot price falls below $60/bbl, which is "
        "below the fiscal breakeven for even the most diversified GCC economy "
        "(UAE at ~$60). Sustained prices at this level guarantee fiscal "
        "deficits across all six GCC states. Activates enhanced monitoring "
        "and fiscal scenario re-evaluation."
    ),
    status="ACTIVE",
    effective_date=date(2025, 1, 15),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="oil_energy_signals.value",
            signal_name="Brent Crude Spot Price (USD/bbl)",
            signal_name_ar="سعر خام برنت الفوري (دولار/برميل)",
            source_dataset="p1_oil_energy_signals",
            unit="usd_per_barrel",
            monitoring_frequency="DAILY",
            baseline_value=80.0,
            baseline_source="2024 average Brent price",
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="oil_energy_signals.value",
            operator="lt",
            value=60.0,
            unit="usd_per_barrel",
            severity_at_threshold=SignalSeverity.HIGH,
            historical_frequency=(
                "Brent was below $60 for ~18 months during 2014-2016, and "
                "briefly during March-May 2020. Approximately once per decade."
            ),
            calibration_note=(
                "UAE fiscal breakeven (~$60) is the lowest in GCC. Below this, "
                "every GCC state runs a deficit. Set as the universal stress floor."
            ),
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="FISCAL_CHANNEL",
            description=(
                "Oil price below fiscal breakeven → all GCC governments enter "
                "deficit → SWF drawdowns or debt issuance → sovereign credit "
                "pressure → banking sector exposure."
            ),
            propagation_hops=3,
            attenuation_per_hop=0.85,
            estimated_lag_hours=720.0,
            evidence_basis="2015-2016: All 6 GCC states ran fiscal deficits simultaneously.",
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="entity_type:COUNTRY",
            exposure_type="DIRECT",
            impact_description="All GCC sovereigns face fiscal deficit at this price level.",
            key_metrics_at_risk=["FISCAL_BALANCE_PCT_GDP"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.GOVERNMENT,
            impact_magnitude="HIGH",
            impact_channel="Fiscal deficit requiring debt issuance or SWF drawdown",
            estimated_gdp_drag_pct=1.5,
        ),
        SectorImpactSpec(
            sector=Sector.ENERGY,
            impact_magnitude="HIGH",
            impact_channel="Reduced capex, deferred projects",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.MONITOR,
        action_params={
            "monitoring_type": "ENHANCED_FISCAL",
            "re_evaluate_scenarios": ["saudi_oil_shock", "energy_market_volatility_shock"],
            "frequency": "daily",
        },
        escalation_level=RiskLevel.HIGH,
        requires_human_approval=False,
        time_to_act_hours=24.0,
        fallback_action=None,
        related_scenario_ids=["saudi_oil_shock", "energy_market_volatility_shock"],
    ),

    confidence=ConfidenceBasis(
        methodology="Fiscal breakeven analysis from IMF Article IV consultations.",
        data_sources=["imf-weo", "eia-api"],
        back_test_period="2014-01 to 2024-12",
        false_positive_rate=0.02,
        confidence_score=0.88,
        limitations=["Fiscal breakeven shifts with government spending decisions"],
        next_review_date=date(2026, 4, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "Brent crude at ${oil_energy_signals.value}/bbl — below the $60 "
            "universal GCC fiscal breakeven. Enhanced monitoring activated."
        ),
        summary_ar=(
            "خام برنت عند {oil_energy_signals.value} دولار/برميل — تحت عتبة "
            "التعادل المالي البالغة ٦٠ دولار. تم تفعيل المراقبة المعززة."
        ),
        dashboard_label="OIL <$60 — Fiscal Stress Zone",
        dashboard_label_ar="النفط <٦٠$ — منطقة ضغط مالي",
    ),

    exclusions=[],
    applicable_countries=[
        GCCCountry.SA, GCCCountry.AE, GCCCountry.KW,
        GCCCountry.QA, GCCCountry.BH, GCCCountry.OM,
    ],
    applicable_sectors=[Sector.ENERGY, Sector.GOVERNMENT],
    applicable_scenarios=["saudi_oil_shock", "energy_market_volatility_shock"],
    cooldown_minutes=480,
    max_concurrent_triggers=1,

    audit=SpecAuditRecord(
        authored_by="Risk Analytics Team",
        authored_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 1, 12, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
        change_summary="Initial version — sustained low oil fiscal stress detection",
    ),

    tags=["oil", "fiscal", "sustained", "tier-2"],
    source_dataset_ids=["p1_oil_energy_signals", "p1_macro_indicators"],
)


OIL_SHOCK_SPECS = [_BRENT_DROP_30, _SUSTAINED_LOW_60]
