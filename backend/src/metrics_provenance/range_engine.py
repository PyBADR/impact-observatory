"""MetricRangeEngine — replaces false-precision fixed points with honest
uncertainty bands tied to scenario severity and propagation behavior.

For each major metric, computes [min, expected, max] with reasoning.
"""

from __future__ import annotations

import math


def build_metric_ranges(run_result: dict) -> list[dict]:
    """Build uncertainty ranges for all major metrics.

    Returns list of dicts matching MetricRange model.
    """
    headline = run_result.get("headline", {})
    severity = run_result.get("severity", 0.5)
    conf = run_result.get("confidence_score", 0.85)
    total_loss = headline.get("total_loss_usd", 0.0)
    banking = run_result.get("banking_stress", run_result.get("banking", {}))
    insurance = run_result.get("insurance_stress", run_result.get("insurance", {}))
    horizon = run_result.get("horizon_hours", 336)

    # Uncertainty width: wider at extreme severity, lower confidence
    base_width = 0.15 + 0.25 * abs(severity - 0.5) + 0.10 * (1 - conf)

    ranges: list[dict] = []

    # ── total_loss_usd ───────────────────────────────────────────────────
    loss_width = base_width * 1.2  # losses have wider uncertainty
    ranges.append({
        "metric_name": "total_loss_usd",
        "metric_name_ar": "إجمالي الخسائر بالدولار",
        "min_value": round(total_loss * (1 - loss_width), 2),
        "expected_value": round(total_loss, 2),
        "max_value": round(total_loss * (1 + loss_width * 1.5), 2),
        "confidence_band": f"±{loss_width*100:.0f}% / +{loss_width*150:.0f}%",
        "unit": "USD",
        "reasoning_en": (
            f"Uncertainty driven by severity extremity ({severity:.2f}), "
            f"model confidence ({conf:.2f}), and propagation model assumptions. "
            f"Upside risk is 1.5× wider than downside because tail losses "
            f"amplify through systemic contagion channels."
        ),
        "reasoning_ar": (
            f"عدم اليقين مدفوع بتطرف الشدة ({severity:.2f})، "
            f"ثقة النموذج ({conf:.2f})، وافتراضات نموذج الانتشار."
        ),
    })

    # ── unified_risk_score ───────────────────────────────────────────────
    urs = run_result.get("unified_risk_score", 0.0)
    urs_width = base_width * 0.8  # composite scores are tighter
    ranges.append({
        "metric_name": "unified_risk_score",
        "metric_name_ar": "درجة المخاطر الموحدة",
        "min_value": round(max(0, urs - urs_width * urs), 4),
        "expected_value": round(urs, 4),
        "max_value": round(min(1, urs + urs_width * urs), 4),
        "confidence_band": f"±{urs_width*100:.0f}%",
        "unit": "score [0-1]",
        "reasoning_en": (
            f"5-factor weighted composite with deterministic weights. "
            f"Uncertainty comes from input metric ranges, not weight uncertainty. "
            f"Clamped to [0, 1]."
        ),
        "reasoning_ar": "مركب مرجح من 5 عوامل بأوزان حتمية. عدم اليقين من نطاقات المدخلات.",
    })

    # ── propagation_score ────────────────────────────────────────────────
    prop = run_result.get("propagation_score", 0.0)
    prop_width = base_width * 0.6  # propagation is deterministic on graph
    ranges.append({
        "metric_name": "propagation_score",
        "metric_name_ar": "درجة الانتشار",
        "min_value": round(max(0, prop * (1 - prop_width)), 4),
        "expected_value": round(prop, 4),
        "max_value": round(min(1, prop * (1 + prop_width)), 4),
        "confidence_band": f"±{prop_width*100:.0f}%",
        "unit": "score [0-1]",
        "reasoning_en": (
            "Propagation is deterministic on fixed adjacency graph (43 nodes, 188 edges). "
            "Uncertainty reflects graph completeness assumptions — real GCC interconnections "
            "may include unlisted bilateral agreements."
        ),
        "reasoning_ar": "الانتشار حتمي على الرسم البياني الثابت. عدم اليقين يعكس افتراضات اكتمال الشبكة.",
    })

    # ── confidence_score ─────────────────────────────────────────────────
    conf_width = 0.08  # confidence is inherently bounded
    ranges.append({
        "metric_name": "confidence_score",
        "metric_name_ar": "درجة الثقة",
        "min_value": round(max(0.3, conf - conf_width), 4),
        "expected_value": round(conf, 4),
        "max_value": round(min(0.99, conf + conf_width), 4),
        "confidence_band": f"±{conf_width*100:.0f}%",
        "unit": "score [0-1]",
        "reasoning_en": (
            "Model confidence is self-referential — it estimates its own reliability. "
            "Range is narrow because the 4-factor formula uses fixed parameters."
        ),
        "reasoning_ar": "ثقة النموذج ذاتية المرجعية — تقدر موثوقيتها الخاصة.",
    })

    # ── banking_aggregate_stress ──────────────────────────────────────────
    lsi = banking.get("aggregate_stress", 0.0)
    lsi_width = base_width * 0.9
    ranges.append({
        "metric_name": "banking_aggregate_stress",
        "metric_name_ar": "إجهاد القطاع المصرفي",
        "min_value": round(max(0, lsi * (1 - lsi_width)), 4),
        "expected_value": round(lsi, 4),
        "max_value": round(min(1, lsi * (1 + lsi_width)), 4),
        "confidence_band": f"±{lsi_width*100:.0f}%",
        "unit": "score [0-1]",
        "reasoning_en": (
            f"LSI is a 4-factor liquidity model. Uncertainty depends on withdrawal "
            f"behavior assumptions and interbank contagion dynamics. "
            f"LCR: {banking.get('lcr_ratio', 1.0):.2f}, CAR: {banking.get('car_ratio', 0.12):.3f}."
        ),
        "reasoning_ar": f"مؤشر إجهاد السيولة. نسبة تغطية السيولة: {banking.get('lcr_ratio', 1.0):.2f}.",
    })

    # ── insurance_aggregate_stress ────────────────────────────────────────
    isi = insurance.get("aggregate_stress", 0.0)
    isi_width = base_width * 0.9
    ranges.append({
        "metric_name": "insurance_aggregate_stress",
        "metric_name_ar": "إجهاد قطاع التأمين",
        "min_value": round(max(0, isi * (1 - isi_width)), 4),
        "expected_value": round(isi, 4),
        "max_value": round(min(1, isi * (1 + isi_width)), 4),
        "confidence_band": f"±{isi_width*100:.0f}%",
        "unit": "score [0-1]",
        "reasoning_en": (
            f"ISI is a 4-factor insurance stress model. Claims surge assumption "
            f"(1 + severity×2.5) is the largest uncertainty driver. "
            f"Combined ratio: {insurance.get('combined_ratio', 0.95):.2f}."
        ),
        "reasoning_ar": f"مؤشر إجهاد التأمين. النسبة المجمعة: {insurance.get('combined_ratio', 0.95):.2f}.",
    })

    # ── peak_day ─────────────────────────────────────────────────────────
    peak = headline.get("peak_day", run_result.get("peak_day", 0))
    day_horizon = max(1, horizon // 24)
    peak_min = max(1, int(peak * 0.7))
    peak_max = min(day_horizon, int(peak * 1.4) + 1)
    ranges.append({
        "metric_name": "peak_day",
        "metric_name_ar": "يوم الذروة",
        "min_value": float(peak_min),
        "expected_value": float(peak),
        "max_value": float(peak_max),
        "confidence_band": f"Day {peak_min}–{peak_max}",
        "unit": "day",
        "reasoning_en": (
            "Peak day depends on propagation speed and sector coupling strength. "
            "Faster-than-modeled contagion shifts peak earlier; "
            "slower inter-sector transmission delays it."
        ),
        "reasoning_ar": "يوم الذروة يعتمد على سرعة الانتشار وقوة ارتباط القطاعات.",
    })

    # ── event_severity ───────────────────────────────────────────────────
    es = run_result.get("event_severity", 0.0)
    es_width = 0.05  # event severity is deterministic given inputs
    ranges.append({
        "metric_name": "event_severity",
        "metric_name_ar": "شدة الحدث المحسوبة",
        "min_value": round(max(0, es - es_width), 4),
        "expected_value": round(es, 4),
        "max_value": round(min(1, es + es_width), 4),
        "confidence_band": f"±{es_width*100:.0f}%",
        "unit": "score [0-1]",
        "reasoning_en": (
            "Narrow band — event severity is deterministic from scenario parameters. "
            "Small residual reflects geopolitical amplification uncertainty."
        ),
        "reasoning_ar": "نطاق ضيق — شدة الحدث حتمية من معاملات السيناريو.",
    })

    return ranges
