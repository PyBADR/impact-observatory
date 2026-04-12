"""
Liquidity Stress Rule Family | عائلة قواعد ضغط السيولة
=========================================================

Policy domain: Banking sector liquidity deterioration and interbank
funding market stress across GCC jurisdictions.

GCC context:
  - CBK mandates Liquidity Coverage Ratio (LCR) ≥ 100% for all
    Kuwaiti banks — aligned with Basel III but enforced with a
    15-day CBK reporting cycle
  - Net Stable Funding Ratio (NSFR) ≥ 100% — measures structural
    funding resilience over a 1-year horizon
  - GCC interbank markets are thin; a spike in KIBOR (Kuwait),
    EIBOR (UAE), or SAIBOR (Saudi) propagates quickly because
    GCC banks rely on wholesale funding for 25-40% of liabilities
  - During the 2008/2009 crisis, GCC interbank rates spiked 200-400bps
    above policy rates — governments had to inject capital and
    guarantee deposits to prevent bank runs
  - Liquidity stress is the fastest transmission channel in GCC:
    interbank freeze → deposit flight → central bank emergency
    lending → sovereign contingent liability

Variants:
  SPEC-LIQUIDITY-KW-LCR-BREACH-v1       — Kuwaiti bank LCR drops below 100%
  SPEC-LIQUIDITY-INTERBANK-SPIKE-v1     — GCC interbank rate spikes >150bps above policy rate
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

__all__ = ["LIQUIDITY_STRESS_SPECS"]


# ═══════════════════════════════════════════════════════════════════════════════
# Variant 1: Kuwaiti Bank LCR Breach
# ═══════════════════════════════════════════════════════════════════════════════

_KW_LCR_BREACH = RuleSpec(
    spec_id="SPEC-LIQUIDITY-KW-LCR-BREACH-v1",
    spec_version="1.0.0",
    family="liquidity-stress",
    variant="kw-lcr-breach",

    name="Kuwaiti Bank LCR Below Regulatory Minimum",
    name_ar="نسبة تغطية السيولة لبنك كويتي دون الحد التنظيمي",
    description=(
        "Triggers when any Kuwaiti D-SIB (Domestic Systemically Important Bank) "
        "reports a Liquidity Coverage Ratio below the CBK-mandated 100% minimum. "
        "An LCR breach signals that the bank cannot cover 30-day net cash outflows "
        "with High-Quality Liquid Assets (HQLA). This is a regulatory breach with "
        "automatic CBK supervisory intervention. For D-SIBs, a single-bank LCR "
        "breach can trigger depositor anxiety across the sector due to contagion "
        "effects — Kuwait's banking sector is concentrated (top 3 banks hold ~60% "
        "of total assets)."
    ),
    status="ACTIVE",
    effective_date=date(2025, 2, 1),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="banking_sector_profiles.lcr_pct",
            signal_name="Liquidity Coverage Ratio (%)",
            signal_name_ar="نسبة تغطية السيولة (%)",
            source_dataset="p1_banking_sector_profiles",
            unit="percent",
            monitoring_frequency="DAILY",
            baseline_value=160.0,
            baseline_source=(
                "Kuwaiti banking sector average LCR 2019-2024 (CBK Financial "
                "Stability Report 2024). Range: 140-180%."
            ),
        ),
        TriggerSignalSpec(
            signal_field="banking_sector_profiles.is_dsib",
            signal_name="D-SIB Classification Flag",
            source_dataset="p1_banking_sector_profiles",
            unit="boolean",
            monitoring_frequency="MONTHLY",
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="banking_sector_profiles.lcr_pct",
            operator="lt",
            value=100,
            unit="percent",
            severity_at_threshold=SignalSeverity.SEVERE,
            historical_frequency=(
                "No Kuwaiti D-SIB has reported LCR <100% since Basel III "
                "implementation in 2015. This would be unprecedented and "
                "constitutes a regulatory breach."
            ),
            calibration_note=(
                "100% is the CBK regulatory minimum — not a model threshold. "
                "This is a hard regulatory floor. A breach triggers automatic "
                "supervisory action under CBK Instruction 2/RB/344/2014."
            ),
        ),
        ThresholdSpec(
            field="banking_sector_profiles.is_dsib",
            operator="eq",
            value=True,
            severity_at_threshold=SignalSeverity.SEVERE,
            historical_frequency="N/A — static classification qualifier",
            calibration_note=(
                "Restricts to D-SIBs only. Non-systemic banks breaching LCR "
                "are handled by standard CBK supervisory process without "
                "triggering system-wide alert."
            ),
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="LIQUIDITY_SQUEEZE",
            description=(
                "D-SIB LCR breach → CBK supervisory intervention → bank "
                "forced asset sales or emergency borrowing → interbank rate "
                "spike → contagion to other banks' funding costs → sector-wide "
                "liquidity tightening."
            ),
            description_ar=(
                "خرق نسبة السيولة → تدخل رقابي من البنك المركزي → بيع أصول "
                "اضطراري أو اقتراض طارئ → ارتفاع أسعار الفائدة بين البنوك → "
                "عدوى إلى تكاليف تمويل البنوك الأخرى → تشديد سيولة على مستوى القطاع"
            ),
            propagation_hops=3,
            attenuation_per_hop=0.85,
            estimated_lag_hours=24.0,
            intermediate_entities=["KW-CBK"],
            evidence_basis=(
                "2008-2009: Gulf Bank derivatives loss triggered CBK emergency "
                "lending facility activation. NBK and other D-SIBs saw 50-80bps "
                "funding cost increase within 48 hours despite being unaffected. "
                "CBK ultimately had to guarantee all bank deposits (Oct 2008)."
            ),
        ),
        TransmissionSpec(
            mechanism="MARKET_CONTAGION",
            description=(
                "D-SIB LCR breach becomes public → Boursa Kuwait bank index "
                "sell-off → CDS spreads widen → foreign correspondent banks "
                "review GCC exposure → potential credit line reductions."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.75,
            estimated_lag_hours=4.0,
            evidence_basis=(
                "Signaling channel: regulatory breaches are material disclosures. "
                "Gulf Bank 2008 event caused 30% decline in Kuwait banking index "
                "within one week."
            ),
        ),
        TransmissionSpec(
            mechanism="CROSS_BORDER_SPILLOVER",
            description=(
                "Kuwaiti D-SIB stress → GCC cross-border interbank exposures "
                "repriced → UAE/Saudi banks tighten lending to Kuwaiti "
                "counterparties → trade finance disruption."
            ),
            propagation_hops=2,
            attenuation_per_hop=0.65,
            estimated_lag_hours=72.0,
            evidence_basis=(
                "GCC interbank market is bilateral — no central clearing. "
                "Cross-border exposures estimated at $15-20bn (IMF Article IV "
                "consultations). Counterparty risk repricing is immediate."
            ),
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="is_dsib:True AND country:KW",
            exposure_type="DIRECT",
            impact_description=(
                "The breaching D-SIB faces CBK supervisory intervention, "
                "potential restrictions on dividend distribution, and "
                "mandatory remediation plan within 30 days."
            ),
            key_metrics_at_risk=["lcr_pct", "nsfr_pct", "car_pct", "roe_pct"],
        ),
        AffectedEntitySpec(
            entity_pattern="entity_type:COMMERCIAL_BANK AND country:KW",
            exposure_type="INDIRECT",
            impact_description=(
                "All Kuwaiti banks face interbank rate increases, potential "
                "depositor anxiety (rational or not), and tighter CBK "
                "supervisory scrutiny of liquidity positions."
            ),
            key_metrics_at_risk=["lcr_pct", "cost_of_funds_pct", "deposit_growth_pct"],
        ),
        AffectedEntitySpec(
            entity_id="KW-CBK",
            exposure_type="DIRECT",
            impact_description=(
                "CBK must assess systemic risk, potentially activate emergency "
                "lending facility (discount window), and consider whether to "
                "extend deposit guarantee."
            ),
            key_metrics_at_risk=["RESERVE_ASSETS", "EMERGENCY_LENDING_OUTSTANDING"],
        ),
        AffectedEntitySpec(
            entity_pattern="sector:INSURANCE AND country:KW",
            exposure_type="INDIRECT",
            impact_description=(
                "Insurance companies with deposits or sukuk in the affected "
                "bank face counterparty risk. Investment portfolio mark-to-market "
                "losses if bank bonds/sukuk reprice."
            ),
            key_metrics_at_risk=["solvency_ratio_pct", "investment_yield_pct"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.BANKING,
            impact_magnitude="CRITICAL",
            impact_channel="Direct regulatory breach + interbank contagion",
            estimated_gdp_drag_pct=0.3,
        ),
        SectorImpactSpec(
            sector=Sector.INSURANCE,
            impact_magnitude="MODERATE",
            impact_channel="Counterparty exposure + investment portfolio losses",
        ),
        SectorImpactSpec(
            sector=Sector.REAL_ESTATE,
            impact_magnitude="HIGH",
            impact_channel="Credit tightening → mortgage/development loan freeze",
            estimated_gdp_drag_pct=0.2,
        ),
        SectorImpactSpec(
            sector=Sector.GOVERNMENT,
            impact_magnitude="MODERATE",
            impact_channel="Sovereign contingent liability if deposit guarantee activated",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.ESCALATE,
        action_params={
            "escalate_to": "Risk Committee",
            "cbk_emergency_assessment": True,
            "counterparty_exposure_review": True,
            "deposit_concentration_check": True,
            "stress_test_scenario": "bank_lcr_cascade",
        },
        escalation_level=RiskLevel.SEVERE,
        requires_human_approval=True,
        approval_authority="CRO",
        time_to_act_hours=4.0,
        fallback_action=DecisionAction.ALERT,
        related_scenario_ids=[
            "uae_banking_crisis",
            "regional_liquidity_stress_event",
        ],
    ),

    confidence=ConfidenceBasis(
        methodology=(
            "Basel III LCR regulatory framework — threshold is not model-derived "
            "but regulatory. Transmission path calibrated from Kuwait 2008 banking "
            "crisis and GCC-wide stress events."
        ),
        data_sources=[
            "cbk-statistical-bulletin",
            "cbk-financial-stability-report",
            "imf-article-iv-kuwait",
        ],
        back_test_period="2008-10 to 2009-06 (Gulf Bank crisis)",
        false_positive_rate=0.005,
        false_negative_rate=0.02,
        confidence_score=0.92,
        limitations=[
            "LCR reporting is T+15 days — breach may have already been remediated by CBK",
            "D-SIB classification list must be current (updated annually by CBK)",
            "Intraday liquidity stress not captured by end-of-day LCR reports",
        ],
        next_review_date=date(2026, 6, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "A Kuwaiti D-SIB reported LCR of {banking_sector_profiles.lcr_pct}%, "
            "breaching the CBK-mandated 100% minimum. This signals insufficient "
            "HQLA to cover 30-day net cash outflows. Escalating to Risk Committee "
            "for counterparty exposure review and systemic risk assessment."
        ),
        summary_ar=(
            "أبلغ بنك كويتي ذو أهمية نظامية عن نسبة تغطية سيولة بلغت "
            "{banking_sector_profiles.lcr_pct}%، متجاوزاً الحد الأدنى المفروض "
            "من البنك المركزي البالغ ١٠٠%. التصعيد إلى لجنة المخاطر لمراجعة "
            "التعرضات وتقييم المخاطر النظامية."
        ),
        dashboard_label="D-SIB LCR BREACH — Risk Escalation",
        dashboard_label_ar="خرق نسبة السيولة لبنك ذو أهمية نظامية — تصعيد",
    ),

    exclusions=[
        Exclusion(
            exclusion_id="EXCL-LIQ-001",
            description=(
                "Do not trigger during CBK-approved transitional periods where "
                "a bank is operating under an approved LCR remediation plan. "
                "CBK may grant temporary waivers during systemic stress events."
            ),
            condition_field="banking_sector_profiles.cbk_remediation_active",
            condition_operator="eq",
            condition_value=True,
            reason_code="CBK_REMEDIATION_ACTIVE",
        ),
        Exclusion(
            exclusion_id="EXCL-LIQ-002",
            description=(
                "Do not trigger if the LCR data is stale (older than 30 days). "
                "Stale data may reflect a resolved condition."
            ),
            condition_field="banking_sector_profiles.data_age_days",
            condition_operator="gt",
            condition_value=30,
            reason_code="DATA_STALE",
        ),
    ],

    applicable_countries=[GCCCountry.KW],
    applicable_sectors=[
        Sector.BANKING,
        Sector.INSURANCE,
        Sector.REAL_ESTATE,
        Sector.GOVERNMENT,
    ],
    applicable_scenarios=[
        "uae_banking_crisis",
        "regional_liquidity_stress_event",
        "kuwait_fiscal_shock",
    ],
    cooldown_minutes=480,
    max_concurrent_triggers=1,

    audit=SpecAuditRecord(
        authored_by="Risk Analytics Team",
        authored_at=datetime(2025, 1, 22, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 1, 27, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        change_summary="Initial version — Kuwaiti D-SIB LCR breach detection",
    ),

    tags=["liquidity", "lcr", "d-sib", "regulatory-breach", "tier-1", "kuwait"],
    source_dataset_ids=["p1_banking_sector_profiles", "p1_cbk_indicators"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Variant 2: GCC Interbank Rate Spike
# ═══════════════════════════════════════════════════════════════════════════════

_INTERBANK_SPIKE = RuleSpec(
    spec_id="SPEC-LIQUIDITY-INTERBANK-SPIKE-v1",
    spec_version="1.0.0",
    family="liquidity-stress",
    variant="interbank-spike",

    name="GCC Interbank Rate Spike Above Policy Rate",
    name_ar="ارتفاع حاد في أسعار الفائدة بين البنوك فوق سعر السياسة",
    description=(
        "Triggers when any GCC interbank offered rate (KIBOR, EIBOR, SAIBOR, "
        "QIBOR) spikes more than 150 basis points above the corresponding "
        "central bank policy rate. This spread signals acute funding stress — "
        "banks are unwilling to lend to each other at policy-adjacent rates, "
        "which means counterparty risk perception has spiked. In GCC markets "
        "where interbank lending is bilateral (no central clearing), this is "
        "the earliest market-observable indicator of systemic liquidity "
        "deterioration."
    ),
    status="ACTIVE",
    effective_date=date(2025, 2, 1),

    trigger_signals=[
        TriggerSignalSpec(
            signal_field="interest_rate_signals.interbank_spread_bps",
            signal_name="Interbank Rate Spread to Policy Rate (bps)",
            signal_name_ar="فارق سعر الفائدة بين البنوك وسعر السياسة (نقاط أساس)",
            source_dataset="p1_interest_rate_signals",
            unit="basis_points",
            monitoring_frequency="DAILY",
            baseline_value=25,
            baseline_source=(
                "Historical average KIBOR-CBK discount rate spread 2015-2024. "
                "Normal range: 10-40bps."
            ),
        ),
    ],
    trigger_logic="AND",

    thresholds=[
        ThresholdSpec(
            field="interest_rate_signals.interbank_spread_bps",
            operator="gte",
            value=150,
            unit="basis_points",
            severity_at_threshold=SignalSeverity.HIGH,
            historical_frequency=(
                "GCC interbank spreads exceeded 150bps only during the 2008-2009 "
                "global financial crisis (EIBOR peaked at ~350bps over CBUAE "
                "repo rate in Oct 2008) and briefly during Q1 2020 COVID panic. "
                "Occurrence: ~2-3 times per decade during systemic events."
            ),
            calibration_note=(
                "150bps chosen as 6x the normal 25bps spread. Below 100bps, "
                "spreads can widen during routine quarter-end or Ramadan liquidity "
                "management — these are seasonal, not systemic. 150bps filters "
                "out seasonal noise and captures genuine stress."
            ),
        ),
    ],

    transmission_paths=[
        TransmissionSpec(
            mechanism="LIQUIDITY_SQUEEZE",
            description=(
                "Interbank rate spike → banks hoard liquidity → credit "
                "rationing to corporate borrowers → trade finance disruption → "
                "real economy stress. SME sector hit first (no direct central "
                "bank access)."
            ),
            description_ar=(
                "ارتفاع أسعار بين البنوك → اكتناز السيولة → تقنين الائتمان "
                "للمقترضين → تعطل تمويل التجارة → ضغط على الاقتصاد الحقيقي"
            ),
            propagation_hops=2,
            attenuation_per_hop=0.80,
            estimated_lag_hours=48.0,
            evidence_basis=(
                "2008-2009: EIBOR-repo spread reached 350bps. UAE corporate "
                "loan growth turned negative for 6 quarters. SME NPL ratio "
                "doubled from 4% to 8% within 12 months (CBK data)."
            ),
        ),
        TransmissionSpec(
            mechanism="CROSS_BORDER_SPILLOVER",
            description=(
                "GCC interbank stress in one jurisdiction → correspondent "
                "banking lines repriced across GCC → contagion to other GCC "
                "interbank markets. GCC interbank network is highly "
                "interconnected — top 10 GCC banks have bilateral exposure "
                "to all 6 jurisdictions."
            ),
            propagation_hops=1,
            attenuation_per_hop=0.70,
            estimated_lag_hours=24.0,
            intermediate_entities=["KW-CBK", "AE-CBUAE", "SA-SAMA"],
            evidence_basis=(
                "2008: Dubai World restructuring announcement caused SAIBOR "
                "and KIBOR to spike sympathetically within 48 hours, even "
                "though the stress originated in UAE."
            ),
        ),
    ],

    affected_entities=[
        AffectedEntitySpec(
            entity_pattern="entity_type:COMMERCIAL_BANK",
            exposure_type="DIRECT",
            impact_description=(
                "All GCC commercial banks face elevated wholesale funding "
                "costs. Banks with higher loan-to-deposit ratios and greater "
                "reliance on interbank borrowing are most exposed."
            ),
            key_metrics_at_risk=[
                "nim_pct", "cost_of_funds_pct", "lcr_pct", "nsfr_pct",
            ],
        ),
        AffectedEntitySpec(
            entity_pattern="entity_type:CENTRAL_BANK",
            exposure_type="DIRECT",
            impact_description=(
                "Central banks must assess whether to inject liquidity via "
                "repo operations, emergency lending facility, or FX swap lines."
            ),
            key_metrics_at_risk=["RESERVE_ASSETS", "EMERGENCY_LENDING_OUTSTANDING"],
        ),
        AffectedEntitySpec(
            entity_pattern="sector:INSURANCE",
            exposure_type="INDIRECT",
            impact_description=(
                "Insurers with bank deposits and money market fund holdings "
                "face reinvestment risk at elevated rates but also counterparty "
                "risk if bank stress materializes into defaults."
            ),
            key_metrics_at_risk=["solvency_ratio_pct", "investment_yield_pct"],
        ),
    ],

    sector_impacts=[
        SectorImpactSpec(
            sector=Sector.BANKING,
            impact_magnitude="HIGH",
            impact_channel="Wholesale funding cost spike + credit rationing",
            estimated_gdp_drag_pct=0.4,
        ),
        SectorImpactSpec(
            sector=Sector.INSURANCE,
            impact_magnitude="LOW",
            impact_channel="Counterparty risk on bank deposits + mark-to-market",
        ),
        SectorImpactSpec(
            sector=Sector.LOGISTICS,
            impact_magnitude="MODERATE",
            impact_channel="Trade finance disruption → port throughput decline",
        ),
        SectorImpactSpec(
            sector=Sector.REAL_ESTATE,
            impact_magnitude="MODERATE",
            impact_channel="Development financing freeze at elevated rates",
        ),
    ],

    decision=DecisionProposalSpec(
        action=DecisionAction.MONITOR,
        action_params={
            "monitoring_type": "INTERBANK_STRESS",
            "alert_if_widens_further": True,
            "escalate_at_bps": 250,
            "check_central_bank_response": True,
            "cross_gcc_contagion_check": True,
        },
        escalation_level=RiskLevel.HIGH,
        requires_human_approval=False,
        time_to_act_hours=12.0,
        fallback_action=DecisionAction.ALERT,
        related_scenario_ids=[
            "regional_liquidity_stress_event",
            "uae_banking_crisis",
            "financial_infrastructure_cyber_disruption",
        ],
    ),

    confidence=ConfidenceBasis(
        methodology=(
            "Historical spread analysis of KIBOR, EIBOR, SAIBOR vs policy "
            "rates 2006-2024. Threshold calibrated against 2008-2009 GFC, "
            "2015 oil shock, and 2020 COVID stress episodes."
        ),
        data_sources=[
            "cbk-statistical-bulletin",
            "cbuae-statistical-bulletin",
            "sama-monthly-statistical-bulletin",
            "bloomberg-gcc-interbank",
        ],
        back_test_period="2006-01 to 2024-12",
        false_positive_rate=0.03,
        false_negative_rate=0.08,
        confidence_score=0.82,
        limitations=[
            "KIBOR fixings are contributor-based, not transaction-based — possible manipulation",
            "Some GCC central banks do not publish daily interbank rates (Oman, Bahrain)",
            "Quarter-end and Ramadan window-dressing can cause transient 80-120bps spikes",
            "Overnight vs 3-month tenor spread not differentiated in current signal spec",
        ],
        next_review_date=date(2026, 6, 1),
    ),

    rationale=RationaleTemplate(
        summary_en=(
            "GCC interbank rate spread widened to "
            "{interest_rate_signals.interbank_spread_bps}bps above the "
            "policy rate, exceeding the 150bps stress threshold. This "
            "signals acute funding stress in the interbank market. "
            "Monitoring for cross-GCC contagion and central bank response."
        ),
        summary_ar=(
            "اتسع فارق أسعار الفائدة بين البنوك إلى "
            "{interest_rate_signals.interbank_spread_bps} نقطة أساس "
            "فوق سعر السياسة، متجاوزاً عتبة الضغط البالغة ١٥٠ نقطة أساس. "
            "مراقبة العدوى عبر دول المجلس واستجابة البنوك المركزية."
        ),
        dashboard_label="GCC Interbank Spread >150bps — Monitoring",
        dashboard_label_ar="فارق بين البنوك >١٥٠ نقطة — مراقبة",
    ),

    exclusions=[
        Exclusion(
            exclusion_id="EXCL-LIQ-101",
            description=(
                "Do not trigger during known seasonal liquidity windows — "
                "quarter-end (last 3 business days of Q1-Q4) and the first "
                "week of Ramadan — when transient spread widening is expected "
                "and does not indicate systemic stress."
            ),
            condition_field="interest_rate_signals.is_seasonal_window",
            condition_operator="eq",
            condition_value=True,
            reason_code="SEASONAL_LIQUIDITY_WINDOW",
        ),
        Exclusion(
            exclusion_id="EXCL-LIQ-102",
            description=(
                "Do not trigger if the spread spike is confined to overnight "
                "tenor only and 3-month tenor remains below 100bps spread. "
                "Overnight-only spikes are typically technical (settlement "
                "timing) rather than systemic."
            ),
            condition_field="interest_rate_signals.is_overnight_only_spike",
            condition_operator="eq",
            condition_value=True,
            reason_code="OVERNIGHT_TECHNICAL_SPIKE",
        ),
    ],

    applicable_countries=[
        GCCCountry.SA, GCCCountry.AE, GCCCountry.KW,
        GCCCountry.QA, GCCCountry.BH, GCCCountry.OM,
    ],
    applicable_sectors=[
        Sector.BANKING,
        Sector.INSURANCE,
        Sector.LOGISTICS,
        Sector.REAL_ESTATE,
    ],
    applicable_scenarios=[
        "regional_liquidity_stress_event",
        "uae_banking_crisis",
        "financial_infrastructure_cyber_disruption",
    ],
    cooldown_minutes=360,
    max_concurrent_triggers=1,

    audit=SpecAuditRecord(
        authored_by="Risk Analytics Team",
        authored_at=datetime(2025, 1, 22, tzinfo=timezone.utc),
        reviewed_by="GCC Risk Committee",
        reviewed_at=datetime(2025, 1, 28, tzinfo=timezone.utc),
        approved_by="CRO",
        approved_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        change_summary="Initial version — GCC interbank rate stress detection",
    ),

    tags=["liquidity", "interbank", "kibor", "eibor", "saibor", "tier-2", "gcc-wide"],
    source_dataset_ids=["p1_interest_rate_signals"],
)


LIQUIDITY_STRESS_SPECS = [_KW_LCR_BREACH, _INTERBANK_SPIKE]
