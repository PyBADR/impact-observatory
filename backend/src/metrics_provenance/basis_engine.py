"""DataBasisEngine — shows what data period or evidence basis stands
behind each metric.

For each metric: historical analog window, scenario model basis,
calibration period, event source period, data freshness date.
If the metric is simulated, says so.  If calibrated from historical
events, shows the period.  If freshness is weak, flags it.
"""

from __future__ import annotations

from src.config import (
    CONF_WELL_KNOWN_SCENARIOS,
    SCENARIO_TAXONOMY,
)

# ── Historical analog periods for well-known GCC scenarios ──────────────
_HISTORICAL_ANALOGS: dict[str, dict] = {
    "hormuz_chokepoint_disruption": {
        "analog_event": "Tanker War / 2019 Strait incidents",
        "analog_period": "1984–1988 / Jun–Sep 2019",
        "analog_relevance": 0.82,
    },
    "hormuz_full_closure": {
        "analog_event": "1984 Tanker War peak + modeled escalation",
        "analog_period": "1984–1988 (extrapolated)",
        "analog_relevance": 0.65,
    },
    "saudi_oil_shock": {
        "analog_event": "Abqaiq–Khurais drone attack",
        "analog_period": "Sep 2019",
        "analog_relevance": 0.88,
    },
    "uae_banking_crisis": {
        "analog_event": "Dubai World debt crisis",
        "analog_period": "Nov 2009 – Mar 2010",
        "analog_relevance": 0.78,
    },
    "gcc_cyber_attack": {
        "analog_event": "Saudi Aramco Shamoon attack",
        "analog_period": "Aug 2012 / Jan 2017",
        "analog_relevance": 0.72,
    },
    "qatar_lng_disruption": {
        "analog_event": "GCC diplomatic blockade (Qatar)",
        "analog_period": "Jun 2017 – Jan 2021",
        "analog_relevance": 0.75,
    },
    "bahrain_sovereign_stress": {
        "analog_event": "Bahrain GCC support package",
        "analog_period": "2018 ($10B aid package)",
        "analog_relevance": 0.80,
    },
    "kuwait_fiscal_shock": {
        "analog_event": "2014–2016 oil price collapse",
        "analog_period": "Jun 2014 – Feb 2016",
        "analog_relevance": 0.74,
    },
    "oman_port_closure": {
        "analog_event": "Cyclone Shaheen port disruption",
        "analog_period": "Oct 2021",
        "analog_relevance": 0.68,
    },
    "red_sea_trade_corridor_instability": {
        "analog_event": "Houthi shipping attacks",
        "analog_period": "Nov 2023 – present",
        "analog_relevance": 0.91,
    },
    "iran_regional_escalation": {
        "analog_event": "US–Iran tensions / Soleimani",
        "analog_period": "Jan 2020",
        "analog_relevance": 0.70,
    },
}

# ── Calibration basis metadata ──────────────────────────────────────────
_CALIBRATION_BASES: dict[str, dict] = {
    "total_loss_usd": {
        "calibration_source": "GCC GDP sectoral data (IMF WEO 2024) + scenario base_loss_usd",
        "calibration_period": "2019–2024 annual data",
        "model_type": "deterministic_formula",
        "model_description": "Σ(sector_exposure × impact_factor × base_loss × θ_j)",
    },
    "unified_risk_score": {
        "calibration_source": "5-factor weighted composite, weights calibrated against 15 GCC stress events",
        "calibration_period": "2009–2024 stress events",
        "model_type": "deterministic_formula",
        "model_description": "URS = g1·ES + g2·AvgExp + g3·AvgStress + g4·PS + g5·LN",
    },
    "propagation_score": {
        "calibration_source": "43-node GCC adjacency graph (188 edges), coupling β=0.65",
        "calibration_period": "Graph structure: 2023 GCC bilateral data",
        "model_type": "network_simulation",
        "model_description": "Iterative: X_(t+1) = β·P·X_t + (1-β)·X_t + S_t",
    },
    "confidence_score": {
        "calibration_source": "4-factor self-assessment: data quality, model coverage, historical similarity, tractability",
        "calibration_period": "Model parameters fixed (not data-driven)",
        "model_type": "deterministic_formula",
        "model_description": "Conf = r1·DQ + r2·MC + r3·HS + r4·ST",
    },
    "banking_aggregate_stress": {
        "calibration_source": "Basel III thresholds (LCR, CAR) + GCC banking sector data",
        "calibration_period": "2019–2024 GCC central bank reports",
        "model_type": "deterministic_formula",
        "model_description": "LSI = l1·W + l2·F + l3·M + l4·C",
    },
    "insurance_aggregate_stress": {
        "calibration_source": "IFRS 17 thresholds + GCC insurance authority data",
        "calibration_period": "2020–2024 GCC insurance market reports",
        "model_type": "deterministic_formula",
        "model_description": "ISI = m1·Cf + m2·LR + m3·Re + m4·Od",
    },
    "event_severity": {
        "calibration_source": "4-factor event model: infrastructure, disruption, utilization, geopolitical",
        "calibration_period": "Scenario parameters (per-scenario catalog)",
        "model_type": "deterministic_formula",
        "model_description": "ES = w1·I + w2·D + w3·U + w4·G",
    },
    "peak_day": {
        "calibration_source": "Propagation convergence timing on 43-node graph",
        "calibration_period": "Graph-derived (no historical calibration)",
        "model_type": "network_simulation",
        "model_description": "Day of maximum aggregate node activation",
    },
    "recovery_score": {
        "calibration_source": "Inverse of unified risk score with regime damping",
        "calibration_period": "Derived metric (no independent calibration)",
        "model_type": "derived",
        "model_description": "recovery = 1 - URS × regime_damping",
    },
}


def build_data_bases(run_result: dict) -> list[dict]:
    """Build data-basis records for all major metrics.

    Returns list of dicts matching DataBasis model.
    """
    scenario_id = run_result.get("scenario_id", "")
    scenario_type = SCENARIO_TAXONOMY.get(scenario_id, "UNKNOWN")
    is_well_known = scenario_id in CONF_WELL_KNOWN_SCENARIOS
    severity = run_result.get("severity", 0.5)
    horizon = run_result.get("horizon_hours", 336)

    analog = _HISTORICAL_ANALOGS.get(scenario_id, {})
    has_analog = bool(analog)

    bases: list[dict] = []

    # ── Per-metric basis records ────────────────────────────────────────
    metrics_to_cover = [
        "total_loss_usd", "unified_risk_score", "propagation_score",
        "confidence_score", "banking_aggregate_stress",
        "insurance_aggregate_stress", "event_severity", "peak_day",
        "recovery_score",
    ]

    for metric_name in metrics_to_cover:
        cal = _CALIBRATION_BASES.get(metric_name, {})

        # Historical basis
        if has_analog:
            historical_basis_en = (
                f"Historical analog: {analog['analog_event']} "
                f"({analog['analog_period']}). "
                f"Relevance score: {analog['analog_relevance']:.0%}."
            )
            historical_basis_ar = (
                f"النظير التاريخي: {analog['analog_event']} "
                f"({analog['analog_period']}). "
                f"درجة الملاءمة: {analog['analog_relevance']:.0%}."
            )
        else:
            historical_basis_en = (
                "No direct historical analog available for this scenario. "
                "Model relies on parametric simulation only."
            )
            historical_basis_ar = (
                "لا يوجد نظير تاريخي مباشر لهذا السيناريو. "
                "يعتمد النموذج على المحاكاة البارامترية فقط."
            )

        # Scenario basis
        scenario_basis_en = (
            f"Scenario: {scenario_id.replace('_', ' ').title()} "
            f"(type: {scenario_type}, severity: {severity:.0%}, "
            f"horizon: {horizon}h). "
            f"{'Well-calibrated scenario with historical precedent.' if is_well_known else 'Limited calibration — treat outputs as indicative.'}"
        )
        scenario_basis_ar = (
            f"السيناريو: {scenario_id.replace('_', ' ')} "
            f"(النوع: {scenario_type}، الشدة: {severity:.0%}، "
            f"الأفق: {horizon} ساعة). "
            f"{'سيناريو معاير جيداً بسابقة تاريخية.' if is_well_known else 'معايرة محدودة — تعامل مع المخرجات كمؤشرات.'}"
        )

        # Calibration basis
        calibration_basis_en = (
            f"Source: {cal.get('calibration_source', 'N/A')}. "
            f"Period: {cal.get('calibration_period', 'N/A')}. "
            f"Model: {cal.get('model_type', 'unknown')} — "
            f"{cal.get('model_description', '')}."
        )
        calibration_basis_ar = (
            f"المصدر: {cal.get('calibration_source', 'غير متوفر')}. "
            f"الفترة: {cal.get('calibration_period', 'غير متوفر')}."
        )

        # Freshness assessment
        model_type = cal.get("model_type", "unknown")
        if model_type == "network_simulation":
            freshness_flag = "SIMULATED"
            freshness_en = (
                "Output is simulated via iterative network propagation. "
                "No real-time data feed — result depends on graph structure "
                "and scenario parameters."
            )
            freshness_ar = (
                "المخرج مُحاكى عبر انتشار شبكي تكراري. "
                "لا يوجد تغذية بيانات فورية."
            )
        elif model_type == "derived":
            freshness_flag = "DERIVED"
            freshness_en = (
                "Derived from other computed metrics. "
                "Freshness depends on upstream metric freshness."
            )
            freshness_ar = "مشتق من مقاييس محسوبة أخرى. الحداثة تعتمد على المقاييس الأصلية."
        elif is_well_known and has_analog:
            freshness_flag = "CALIBRATED"
            freshness_en = (
                f"Calibrated against historical events "
                f"({analog.get('analog_period', 'N/A')}). "
                f"Model parameters last updated: 2024-Q4. "
                f"Analog relevance: {analog.get('analog_relevance', 0):.0%}."
            )
            freshness_ar = (
                f"معاير مقابل أحداث تاريخية "
                f"({analog.get('analog_period', 'غير متوفر')}). "
                f"آخر تحديث للمعاملات: 2024-Q4."
            )
        else:
            freshness_flag = "PARAMETRIC"
            freshness_en = (
                "Based on parametric model with fixed weights. "
                "No historical calibration anchor for this scenario. "
                "Treat as indicative estimate."
            )
            freshness_ar = (
                "مبني على نموذج بارامتري بأوزان ثابتة. "
                "لا يوجد مرتكز معايرة تاريخي لهذا السيناريو."
            )

        # Freshness weakness flag
        freshness_weak = freshness_flag in ("PARAMETRIC", "DERIVED") or (
            has_analog and analog.get("analog_relevance", 0) < 0.70
        )

        bases.append({
            "metric_name": metric_name,
            "metric_name_ar": _METRIC_NAMES_AR.get(metric_name, metric_name),
            "historical_basis_en": historical_basis_en,
            "historical_basis_ar": historical_basis_ar,
            "scenario_basis_en": scenario_basis_en,
            "scenario_basis_ar": scenario_basis_ar,
            "calibration_basis_en": calibration_basis_en,
            "calibration_basis_ar": calibration_basis_ar,
            "freshness_flag": freshness_flag,
            "freshness_detail_en": freshness_en,
            "freshness_detail_ar": freshness_ar,
            "freshness_weak": freshness_weak,
            "model_type": model_type,
            "analog_event": analog.get("analog_event", ""),
            "analog_period": analog.get("analog_period", ""),
            "analog_relevance": analog.get("analog_relevance", 0.0),
        })

    return bases


# ── Arabic metric name lookup ───────────────────────────────────────────
_METRIC_NAMES_AR: dict[str, str] = {
    "total_loss_usd": "إجمالي الخسائر بالدولار",
    "unified_risk_score": "درجة المخاطر الموحدة",
    "propagation_score": "درجة الانتشار",
    "confidence_score": "درجة الثقة",
    "banking_aggregate_stress": "إجهاد القطاع المصرفي",
    "insurance_aggregate_stress": "إجهاد قطاع التأمين",
    "event_severity": "شدة الحدث",
    "peak_day": "يوم الذروة",
    "recovery_score": "درجة التعافي",
}
