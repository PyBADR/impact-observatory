"""MetricProvenanceEngine — traces every major metric back to its formula,
contributing factors, model basis, and data recency.

Metrics covered:
  total_loss_usd, peak_day, time_to_first_failure_hours,
  unified_risk_score, propagation_score, confidence_score,
  banking_aggregate_stress, insurance_aggregate_stress,
  event_severity, recovery_score, congestion_score
"""

from __future__ import annotations

from typing import Any

from src.config import (
    URS_G1, URS_G2, URS_G3, URS_G4, URS_G5,
    CONF_R1, CONF_R2, CONF_R3, CONF_R4,
    ES_W1, ES_W2, ES_W3, ES_W4,
    LSI_L1, LSI_L2, LSI_L3, LSI_L4,
    ISI_M1, ISI_M2, ISI_M3, ISI_M4,
)


def build_metric_provenance(run_result: dict) -> list[dict]:
    """Build provenance records for all major metrics in a run result.

    Returns list of dicts matching MetricProvenance model.
    """
    headline = run_result.get("headline", {})
    banking = run_result.get("banking_stress", run_result.get("banking", {}))
    insurance = run_result.get("insurance_stress", run_result.get("insurance", {}))
    severity = run_result.get("severity", 0.5)
    horizon = run_result.get("horizon_hours", 336)

    metrics: list[dict] = []

    # ── total_loss_usd ───────────────────────────────────────────────────
    total_loss = headline.get("total_loss_usd", 0.0)
    metrics.append({
        "metric_name": "total_loss_usd",
        "metric_name_ar": "إجمالي الخسائر بالدولار",
        "metric_value": total_loss,
        "unit": "USD",
        "time_horizon": f"{horizon} hours ({max(1, horizon // 24)} days)",
        "source_basis": "Deterministic propagation model with sector-weighted loss allocation",
        "model_basis": (
            "impact_factor = severity² × propagation_factor; "
            "total_loss = Σ(exposure_j × impact_factor × asset_base_j × θ_j); "
            "Split: direct 60%, indirect 28%, systemic 12%"
        ),
        "formula": "L = Σ_j(α_j × ES × V_j × connectivity × severity² × prop_factor × base_j × θ_j)",
        "contributing_factors": [
            {"factor_name": "severity", "factor_name_ar": "شدة الحدث",
             "factor_value": severity, "weight": 0.0,
             "description_en": "Scenario severity input (squared in loss formula)",
             "description_ar": "مدخل شدة السيناريو"},
            {"factor_name": "propagation_score", "factor_name_ar": "درجة الانتشار",
             "factor_value": run_result.get("propagation_score", 0.0), "weight": 0.0,
             "description_en": "Network propagation amplification factor",
             "description_ar": "عامل تضخيم الانتشار الشبكي"},
            {"factor_name": "event_severity", "factor_name_ar": "شدة الحدث المحسوبة",
             "factor_value": run_result.get("event_severity", 0.0), "weight": 0.0,
             "description_en": "Weighted event severity from 4-factor model",
             "description_ar": "شدة الحدث المرجحة"},
        ],
        "data_recency": "Simulated from scenario parameters at run time",
        "confidence_notes": f"Confidence score: {run_result.get('confidence_score', 0.0):.2f}",
    })

    # ── peak_day ─────────────────────────────────────────────────────────
    peak_day = headline.get("peak_day", run_result.get("peak_day", 0))
    metrics.append({
        "metric_name": "peak_day",
        "metric_name_ar": "يوم الذروة",
        "metric_value": float(peak_day),
        "unit": "day",
        "time_horizon": f"Within {max(1, horizon // 24)}-day scenario window",
        "source_basis": "Propagation chain timestep with maximum cumulative impact",
        "model_basis": "peak_day = argmax_t(cumulative_impact(t)) across propagation steps",
        "formula": "t* = argmax_t Σ_j stress_j(t)",
        "contributing_factors": [
            {"factor_name": "propagation_speed", "factor_name_ar": "سرعة الانتشار",
             "factor_value": run_result.get("propagation_score", 0.0), "weight": 0.0,
             "description_en": "Higher propagation → earlier peak",
             "description_ar": "انتشار أعلى → ذروة أبكر"},
        ],
        "data_recency": "Computed per simulation run",
        "confidence_notes": "Deterministic — exact within model assumptions",
    })

    # ── unified_risk_score ───────────────────────────────────────────────
    urs = run_result.get("unified_risk_score", 0.0)
    es = run_result.get("event_severity", 0.0)
    prop = run_result.get("propagation_score", 0.0)
    metrics.append({
        "metric_name": "unified_risk_score",
        "metric_name_ar": "درجة المخاطر الموحدة",
        "metric_value": urs,
        "unit": "score [0-1]",
        "time_horizon": f"{horizon}-hour scenario window",
        "source_basis": "5-factor weighted composite",
        "model_basis": (
            f"URS = {URS_G1}×ES + {URS_G2}×peak_exposure + "
            f"{URS_G3}×peak_stress + {URS_G4}×prop_score×√severity + "
            f"{URS_G5}×severity²"
        ),
        "formula": f"URS = {URS_G1}·Es + {URS_G2}·E_peak + {URS_G3}·S_peak + {URS_G4}·P·√s + {URS_G5}·s²",
        "contributing_factors": [
            {"factor_name": "event_severity", "factor_name_ar": "شدة الحدث",
             "factor_value": es, "weight": URS_G1,
             "description_en": f"Event severity (weight {URS_G1})",
             "description_ar": f"شدة الحدث (وزن {URS_G1})"},
            {"factor_name": "propagation_weighted", "factor_name_ar": "الانتشار المرجح",
             "factor_value": prop * (severity ** 0.5), "weight": URS_G4,
             "description_en": f"Propagation × √severity (weight {URS_G4})",
             "description_ar": f"الانتشار × √الشدة (وزن {URS_G4})"},
            {"factor_name": "peak_stress", "factor_name_ar": "ذروة الإجهاد",
             "factor_value": max(
                 banking.get("aggregate_stress", 0.0),
                 insurance.get("aggregate_stress", 0.0),
             ), "weight": URS_G3,
             "description_en": f"Max sector stress (weight {URS_G3})",
             "description_ar": f"أقصى إجهاد قطاعي (وزن {URS_G3})"},
            {"factor_name": "loss_normalized", "factor_name_ar": "الخسارة المعيارية",
             "factor_value": severity ** 2, "weight": URS_G5,
             "description_en": f"severity² (weight {URS_G5})",
             "description_ar": f"الشدة² (وزن {URS_G5})"},
        ],
        "data_recency": "Computed per simulation run",
        "confidence_notes": _risk_level_note(urs),
    })

    # ── confidence_score ─────────────────────────────────────────────────
    conf = run_result.get("confidence_score", 0.0)
    metrics.append({
        "metric_name": "confidence_score",
        "metric_name_ar": "درجة الثقة",
        "metric_value": conf,
        "unit": "score [0-1]",
        "time_horizon": "Applies to entire run",
        "source_basis": "4-factor weighted model confidence composite",
        "model_basis": (
            f"Conf = {CONF_R1}×data_quality + {CONF_R2}×model_coverage + "
            f"{CONF_R3}×historical_support + {CONF_R4}×scenario_typicality"
        ),
        "formula": f"C = {CONF_R1}·DQ + {CONF_R2}·MC + {CONF_R3}·HS + {CONF_R4}·ST",
        "contributing_factors": [
            {"factor_name": "data_quality", "factor_name_ar": "جودة البيانات",
             "factor_value": min(1.0, max(0.5, 1.0 - abs(severity - 0.5) * 0.40)),
             "weight": CONF_R1,
             "description_en": "Higher near mid-range severity; lower at extremes",
             "description_ar": "أعلى عند الشدة المتوسطة"},
        ],
        "data_recency": "Model parameters fixed; data quality varies per scenario",
        "confidence_notes": "Represents model's self-assessed reliability",
    })

    # ── propagation_score ────────────────────────────────────────────────
    metrics.append({
        "metric_name": "propagation_score",
        "metric_name_ar": "درجة الانتشار",
        "metric_value": prop,
        "unit": "score [0-1]",
        "time_horizon": f"{horizon}-hour propagation window",
        "source_basis": "Iterative propagation on 43-node GCC adjacency graph",
        "model_basis": "X_(t+1) = β·P·X_t + (1-β)·X_t + S_t; β=0.65, S_t = e^(-λt)·sev",
        "formula": "X_(t+1) = 0.65·P·X_t + 0.35·X_t + e^(-0.05t)·severity",
        "contributing_factors": [
            {"factor_name": "network_density", "factor_name_ar": "كثافة الشبكة",
             "factor_value": 0.0, "weight": 0.0,
             "description_en": "188 edges across 43 GCC nodes",
             "description_ar": "188 رابط عبر 43 عقدة خليجية"},
            {"factor_name": "propagation_beta", "factor_name_ar": "معامل الانتشار",
             "factor_value": 0.65, "weight": 0.0,
             "description_en": "Network influence weight (β=0.65)",
             "description_ar": "وزن تأثير الشبكة (β=0.65)"},
        ],
        "data_recency": "Adjacency graph fixed; propagation computed per run",
        "confidence_notes": "Deterministic model — confidence depends on graph completeness",
    })

    # ── banking_aggregate_stress (LSI) ───────────────────────────────────
    lsi = banking.get("aggregate_stress", 0.0)
    metrics.append({
        "metric_name": "banking_aggregate_stress",
        "metric_name_ar": "إجهاد القطاع المصرفي",
        "metric_value": lsi,
        "unit": "score [0-1]",
        "time_horizon": f"{horizon}-hour stress window",
        "source_basis": "Liquidity Stress Index (LSI) — 4-factor model",
        "model_basis": (
            f"LSI = {LSI_L1}×withdrawal_pressure + {LSI_L2}×funding_stress + "
            f"{LSI_L3}×market_contagion + {LSI_L4}×capital_erosion"
        ),
        "formula": f"LSI = {LSI_L1}·W + {LSI_L2}·F + {LSI_L3}·M + {LSI_L4}·C",
        "contributing_factors": [
            {"factor_name": "lcr_ratio", "factor_name_ar": "نسبة تغطية السيولة",
             "factor_value": banking.get("lcr_ratio", 1.0), "weight": 0.0,
             "description_en": "Liquidity Coverage Ratio (regulatory minimum: 1.0)",
             "description_ar": "نسبة تغطية السيولة (الحد الأدنى التنظيمي: 1.0)"},
            {"factor_name": "car_ratio", "factor_name_ar": "نسبة كفاية رأس المال",
             "factor_value": banking.get("car_ratio", 0.12), "weight": 0.0,
             "description_en": "Capital Adequacy Ratio (Basel III minimum: 10.5%)",
             "description_ar": "نسبة كفاية رأس المال (الحد الأدنى لبازل 3: 10.5%)"},
        ],
        "data_recency": "Simulated from scenario inputs",
        "confidence_notes": f"LCR {'breached' if banking.get('lcr_ratio', 1.0) < 1.0 else 'within limits'}",
    })

    # ── insurance_aggregate_stress (ISI) ─────────────────────────────────
    isi = insurance.get("aggregate_stress", 0.0)
    metrics.append({
        "metric_name": "insurance_aggregate_stress",
        "metric_name_ar": "إجهاد قطاع التأمين",
        "metric_value": isi,
        "unit": "score [0-1]",
        "time_horizon": f"{horizon}-hour stress window",
        "source_basis": "Insurance Stress Index (ISI) — 4-factor model",
        "model_basis": (
            f"ISI = {ISI_M1}×claims_frequency + {ISI_M2}×loss_ratio + "
            f"{ISI_M3}×reserve_erosion + {ISI_M4}×operational_disruption"
        ),
        "formula": f"ISI = {ISI_M1}·Cf + {ISI_M2}·LR + {ISI_M3}·Re + {ISI_M4}·Od",
        "contributing_factors": [
            {"factor_name": "combined_ratio", "factor_name_ar": "النسبة المجمعة",
             "factor_value": insurance.get("combined_ratio", 0.95), "weight": 0.0,
             "description_en": "Combined ratio (>1.0 = underwriting loss)",
             "description_ar": "النسبة المجمعة (>1.0 = خسارة اكتتاب)"},
        ],
        "data_recency": "Simulated from scenario inputs",
        "confidence_notes": (
            f"Combined ratio {'breached 110%' if insurance.get('combined_ratio', 0.95) > 1.10 else 'within limits'}"
        ),
    })

    # ── event_severity ───────────────────────────────────────────────────
    metrics.append({
        "metric_name": "event_severity",
        "metric_name_ar": "شدة الحدث المحسوبة",
        "metric_value": es,
        "unit": "score [0-1]",
        "time_horizon": "Point-in-time at scenario onset",
        "source_basis": "4-factor event severity model",
        "model_basis": (
            f"ES = {ES_W1}×infrastructure_impact + {ES_W2}×direct_disruption + "
            f"{ES_W3}×cross_sector_spread + {ES_W4}×geopolitical_amplification"
        ),
        "formula": f"ES = {ES_W1}·I + {ES_W2}·D + {ES_W3}·U + {ES_W4}·G",
        "contributing_factors": [
            {"factor_name": "severity_input", "factor_name_ar": "مدخل الشدة",
             "factor_value": severity, "weight": 0.0,
             "description_en": "User-provided scenario severity parameter",
             "description_ar": "معامل شدة السيناريو المدخل"},
        ],
        "data_recency": "Computed from scenario parameters",
        "confidence_notes": "Deterministic — exact given inputs",
    })

    # ── recovery_score ───────────────────────────────────────────────────
    rec = run_result.get("recovery_score", 0.0)
    metrics.append({
        "metric_name": "recovery_score",
        "metric_name_ar": "درجة التعافي",
        "metric_value": rec,
        "unit": "score [0-1]",
        "time_horizon": f"End of {max(1, horizon // 24)}-day window",
        "source_basis": "Recovery trajectory endpoint (1.0 = full recovery)",
        "model_basis": "recovery = 1 - residual_stress at t=horizon",
        "formula": "R = 1 - stress(t_final)",
        "contributing_factors": [],
        "data_recency": "Computed per run",
        "confidence_notes": "Model assumes monotonic recovery after peak — may underestimate setbacks",
    })

    # ── time_to_first_failure ────────────────────────────────────────────
    ttf = run_result.get("decision_plan", {}).get("time_to_first_failure_hours", 0)
    if ttf:
        metrics.append({
            "metric_name": "time_to_first_failure_hours",
            "metric_name_ar": "الوقت حتى أول إخفاق (ساعات)",
            "metric_value": float(ttf),
            "unit": "hours",
            "time_horizon": "From scenario onset to first regulatory breach",
            "source_basis": "Earliest timestep where any regulatory threshold is crossed",
            "model_basis": "min(t) where LCR<1.0 OR CAR<10.5% OR combined_ratio>110%",
            "formula": "t_fail = min_t{LCR(t)<1.0 ∨ CAR(t)<0.105 ∨ CR(t)>1.10}",
            "contributing_factors": [
                {"factor_name": "severity", "factor_name_ar": "الشدة",
                 "factor_value": severity, "weight": 0.0,
                 "description_en": "Higher severity → faster breach",
                 "description_ar": "شدة أعلى → اختراق أسرع"},
            ],
            "data_recency": "Computed per simulation run",
            "confidence_notes": "Regulatory thresholds are fixed (Basel III / IFRS)",
        })

    return metrics


def _risk_level_note(urs: float) -> str:
    if urs < 0.20:
        return "Risk level: NOMINAL"
    if urs < 0.35:
        return "Risk level: LOW"
    if urs < 0.50:
        return "Risk level: GUARDED"
    if urs < 0.65:
        return "Risk level: ELEVATED"
    if urs < 0.80:
        return "Risk level: HIGH"
    return "Risk level: SEVERE"
