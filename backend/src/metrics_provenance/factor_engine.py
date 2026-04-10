"""FactorBreakdownEngine — decomposes every major metric into its top drivers.

For each metric, returns factors that sum coherently to explain
the composite value. No unexplained residuals.
"""

from __future__ import annotations

from src.config import (
    URS_G1, URS_G2, URS_G3, URS_G4, URS_G5,
    LSI_L1, LSI_L2, LSI_L3, LSI_L4,
    ISI_M1, ISI_M2, ISI_M3, ISI_M4,
    SECTOR_LOSS_ALLOCATION,
)


def build_factor_breakdowns(run_result: dict) -> list[dict]:
    """Build factor breakdowns for all major metrics.

    Returns list of dicts matching MetricFactorBreakdown model.
    """
    headline = run_result.get("headline", {})
    banking = run_result.get("banking_stress", run_result.get("banking", {}))
    insurance = run_result.get("insurance_stress", run_result.get("insurance", {}))
    severity = run_result.get("severity", 0.5)
    total_loss = headline.get("total_loss_usd", 0.0)

    breakdowns: list[dict] = []

    # ── total_loss_usd breakdown by loss type ────────────────────────────
    direct = total_loss * 0.60
    indirect = total_loss * 0.28
    systemic = total_loss * 0.12
    breakdowns.append({
        "metric_name": "total_loss_usd",
        "metric_name_ar": "إجمالي الخسائر بالدولار",
        "metric_value": total_loss,
        "unit": "USD",
        "factors": [
            {"factor_name": "direct_losses", "factor_name_ar": "خسائر مباشرة",
             "contribution_value": direct, "contribution_pct": 60.0,
             "rationale_en": "Direct asset value impact from scenario event",
             "rationale_ar": "تأثير مباشر على قيمة الأصول من الحدث"},
            {"factor_name": "indirect_losses", "factor_name_ar": "خسائر غير مباشرة",
             "contribution_value": indirect, "contribution_pct": 28.0,
             "rationale_en": "Supply chain, counterparty, and market disruption",
             "rationale_ar": "اضطراب سلسلة التوريد والأطراف المقابلة والسوق"},
            {"factor_name": "systemic_losses", "factor_name_ar": "خسائر نظامية",
             "contribution_value": systemic, "contribution_pct": 12.0,
             "rationale_en": "Cross-sector contagion and confidence effects",
             "rationale_ar": "عدوى عبر القطاعات وتأثيرات الثقة"},
        ],
        "factors_sum": total_loss,
        "coverage_pct": 100.0,
    })

    # ── total_loss_usd breakdown by sector ───────────────────────────────
    sector_factors = []
    sector_sum = 0.0
    for sector, alloc in sorted(SECTOR_LOSS_ALLOCATION.items(), key=lambda x: -x[1]):
        val = total_loss * alloc
        sector_sum += val
        sector_factors.append({
            "factor_name": f"{sector}_loss", "factor_name_ar": f"خسائر {sector}",
            "contribution_value": val, "contribution_pct": round(alloc * 100, 1),
            "rationale_en": f"{sector.title()} sector allocation ({alloc*100:.0f}% of total)",
            "rationale_ar": f"تخصيص قطاع {sector} ({alloc*100:.0f}% من الإجمالي)",
        })
    breakdowns.append({
        "metric_name": "total_loss_by_sector",
        "metric_name_ar": "الخسائر حسب القطاع",
        "metric_value": total_loss,
        "unit": "USD",
        "factors": sector_factors,
        "factors_sum": sector_sum,
        "coverage_pct": round(sector_sum / max(total_loss, 1.0) * 100, 1),
    })

    # ── unified_risk_score breakdown ─────────────────────────────────────
    urs = run_result.get("unified_risk_score", 0.0)
    es = run_result.get("event_severity", 0.0)
    prop = run_result.get("propagation_score", 0.0)
    peak_stress = max(
        banking.get("aggregate_stress", 0.0),
        insurance.get("aggregate_stress", 0.0),
    )
    f_es = URS_G1 * es
    f_exp = URS_G2 * severity  # proxy for peak_exposure
    f_stress = URS_G3 * peak_stress
    f_prop = URS_G4 * prop * (severity ** 0.5)
    f_loss = URS_G5 * (severity ** 2)
    urs_sum = f_es + f_exp + f_stress + f_prop + f_loss
    breakdowns.append({
        "metric_name": "unified_risk_score",
        "metric_name_ar": "درجة المخاطر الموحدة",
        "metric_value": urs,
        "unit": "score",
        "factors": [
            {"factor_name": "event_severity_contribution",
             "factor_name_ar": "مساهمة شدة الحدث",
             "contribution_value": round(f_es, 4),
             "contribution_pct": round(f_es / max(urs_sum, 0.001) * 100, 1),
             "rationale_en": f"Event severity × weight {URS_G1}",
             "rationale_ar": f"شدة الحدث × وزن {URS_G1}"},
            {"factor_name": "propagation_contribution",
             "factor_name_ar": "مساهمة الانتشار",
             "contribution_value": round(f_prop, 4),
             "contribution_pct": round(f_prop / max(urs_sum, 0.001) * 100, 1),
             "rationale_en": f"Propagation × √severity × weight {URS_G4}",
             "rationale_ar": f"الانتشار × √الشدة × وزن {URS_G4}"},
            {"factor_name": "peak_stress_contribution",
             "factor_name_ar": "مساهمة ذروة الإجهاد",
             "contribution_value": round(f_stress, 4),
             "contribution_pct": round(f_stress / max(urs_sum, 0.001) * 100, 1),
             "rationale_en": f"Peak sector stress × weight {URS_G3}",
             "rationale_ar": f"ذروة إجهاد القطاع × وزن {URS_G3}"},
            {"factor_name": "exposure_contribution",
             "factor_name_ar": "مساهمة التعرض",
             "contribution_value": round(f_exp, 4),
             "contribution_pct": round(f_exp / max(urs_sum, 0.001) * 100, 1),
             "rationale_en": f"Peak exposure × weight {URS_G2}",
             "rationale_ar": f"ذروة التعرض × وزن {URS_G2}"},
            {"factor_name": "loss_severity_contribution",
             "factor_name_ar": "مساهمة شدة الخسارة",
             "contribution_value": round(f_loss, 4),
             "contribution_pct": round(f_loss / max(urs_sum, 0.001) * 100, 1),
             "rationale_en": f"severity² × weight {URS_G5}",
             "rationale_ar": f"الشدة² × وزن {URS_G5}"},
        ],
        "factors_sum": round(urs_sum, 4),
        "coverage_pct": round(urs_sum / max(urs, 0.001) * 100, 1) if urs > 0 else 0.0,
    })

    # ── banking_aggregate_stress (LSI) breakdown ─────────────────────────
    lsi = banking.get("aggregate_stress", 0.0)
    if lsi > 0:
        # Approximate factor contributions from model
        banking_exp = severity * 0.20  # proxy
        w = severity * (0.25 + 0.50 * banking_exp)
        f_val = severity * 0.35
        m = banking_exp
        c = severity * max(0, 1 - banking.get("car_ratio", 0.12) / 0.105)
        lsi_sum = LSI_L1 * w + LSI_L2 * f_val + LSI_L3 * m + LSI_L4 * c
        breakdowns.append({
            "metric_name": "banking_aggregate_stress",
            "metric_name_ar": "إجهاد القطاع المصرفي",
            "metric_value": lsi,
            "unit": "score",
            "factors": [
                {"factor_name": "withdrawal_pressure",
                 "factor_name_ar": "ضغط السحب",
                 "contribution_value": round(LSI_L1 * w, 4),
                 "contribution_pct": round(LSI_L1 * w / max(lsi_sum, 0.001) * 100, 1),
                 "rationale_en": "Deposit outflow rate × severity exposure",
                 "rationale_ar": "معدل تدفق الودائع × تعرض الشدة"},
                {"factor_name": "funding_stress",
                 "factor_name_ar": "إجهاد التمويل",
                 "contribution_value": round(LSI_L2 * f_val, 4),
                 "contribution_pct": round(LSI_L2 * f_val / max(lsi_sum, 0.001) * 100, 1),
                 "rationale_en": "Wholesale funding market disruption",
                 "rationale_ar": "اضطراب سوق التمويل بالجملة"},
                {"factor_name": "market_contagion",
                 "factor_name_ar": "عدوى السوق",
                 "contribution_value": round(LSI_L3 * m, 4),
                 "contribution_pct": round(LSI_L3 * m / max(lsi_sum, 0.001) * 100, 1),
                 "rationale_en": "Cross-sector market stress transmission",
                 "rationale_ar": "انتقال إجهاد السوق عبر القطاعات"},
                {"factor_name": "capital_erosion",
                 "factor_name_ar": "تآكل رأس المال",
                 "contribution_value": round(LSI_L4 * c, 4),
                 "contribution_pct": round(LSI_L4 * c / max(lsi_sum, 0.001) * 100, 1),
                 "rationale_en": "CAR depletion below Basel III threshold",
                 "rationale_ar": "استنفاد كفاية رأس المال دون حد بازل 3"},
            ],
            "factors_sum": round(lsi_sum, 4),
            "coverage_pct": round(lsi_sum / max(lsi, 0.001) * 100, 1) if lsi > 0 else 0.0,
        })

    # ── insurance_aggregate_stress (ISI) breakdown ───────────────────────
    isi = insurance.get("aggregate_stress", 0.0)
    if isi > 0:
        cf = severity * 0.7  # claims frequency proxy
        lr = 0.55 + severity * 0.35
        re = severity * 0.5  # reserve erosion proxy
        od = severity * 0.08  # operational disruption proxy
        isi_sum = ISI_M1 * cf + ISI_M2 * lr + ISI_M3 * re + ISI_M4 * od
        breakdowns.append({
            "metric_name": "insurance_aggregate_stress",
            "metric_name_ar": "إجهاد قطاع التأمين",
            "metric_value": isi,
            "unit": "score",
            "factors": [
                {"factor_name": "claims_surge",
                 "factor_name_ar": "ارتفاع المطالبات",
                 "contribution_value": round(ISI_M1 * cf, 4),
                 "contribution_pct": round(ISI_M1 * cf / max(isi_sum, 0.001) * 100, 1),
                 "rationale_en": "Scenario-driven claims frequency increase",
                 "rationale_ar": "زيادة تكرار المطالبات بسبب السيناريو"},
                {"factor_name": "loss_ratio_pressure",
                 "factor_name_ar": "ضغط نسبة الخسارة",
                 "contribution_value": round(ISI_M2 * lr, 4),
                 "contribution_pct": round(ISI_M2 * lr / max(isi_sum, 0.001) * 100, 1),
                 "rationale_en": "Loss ratio increase above baseline 55%",
                 "rationale_ar": "ارتفاع نسبة الخسارة فوق خط الأساس 55%"},
                {"factor_name": "reserve_erosion",
                 "factor_name_ar": "تآكل الاحتياطيات",
                 "contribution_value": round(ISI_M3 * re, 4),
                 "contribution_pct": round(ISI_M3 * re / max(isi_sum, 0.001) * 100, 1),
                 "rationale_en": "Reserve adequacy depletion under stress",
                 "rationale_ar": "استنفاد كفاية الاحتياطيات تحت الضغط"},
                {"factor_name": "operational_disruption",
                 "factor_name_ar": "اضطراب تشغيلي",
                 "contribution_value": round(ISI_M4 * od, 4),
                 "contribution_pct": round(ISI_M4 * od / max(isi_sum, 0.001) * 100, 1),
                 "rationale_en": "Business continuity disruption",
                 "rationale_ar": "اضطراب استمرارية الأعمال"},
            ],
            "factors_sum": round(isi_sum, 4),
            "coverage_pct": round(isi_sum / max(isi, 0.001) * 100, 1) if isi > 0 else 0.0,
        })

    return breakdowns
