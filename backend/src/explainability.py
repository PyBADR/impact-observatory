"""
Impact Observatory | مرصد الأثر
Explainability Engine — causal chain construction, bilingual narrative generation,
sensitivity analysis, uncertainty quantification.

All output is deterministic and template-based (no LLM dependency).
"""
from __future__ import annotations

import math
from typing import Any

from src.utils import (
    clamp,
    classify_stress,
    format_loss_usd,
    severity_label,
    severity_label_ar,
    risk_label_ar,
)

# ---------------------------------------------------------------------------
# Mechanism library (bilingual)
# ---------------------------------------------------------------------------

_MECHANISMS: list[tuple[str, str]] = [
    ("Direct shock — immediate capacity constraint at shock origin node",
     "صدمة مباشرة — قيد فوري على الطاقة في عقدة نشأة الصدمة"),
    ("Counter-party credit exposure — creditor institutions absorb first-loss",
     "تعرض ائتمان الطرف المقابل — تتحمل المؤسسات الدائنة الخسارة الأولى"),
    ("Liquidity contagion — market participants hoard reserves, reducing velocity",
     "عدوى السيولة — يحتجز المشاركون في السوق الاحتياطيات، مما يقلل من السرعة"),
    ("Supply-chain disruption — upstream bottleneck propagates downstream shortfall",
     "تعطل سلسلة التوريد — يؤدي الاختناق المرحلي إلى عجز في المراحل اللاحقة"),
    ("Market sentiment spillover — price discovery impaired across correlated assets",
     "امتداد معنويات السوق — يضعف اكتشاف الأسعار عبر الأصول المترابطة"),
    ("Operational dependency failure — shared infrastructure node degradation",
     "فشل التبعية التشغيلية — تدهور عقدة البنية التحتية المشتركة"),
    ("Regulatory capital stress — pillar-2 add-on triggers asset sales",
     "ضغط رأس المال التنظيمي — يُشغّل الركيزة الثانية مبيعات الأصول"),
    ("Cross-collateral trigger — mark-to-market losses breach covenant thresholds",
     "تشغيل الضمانات المتقاطعة — خسائر القيمة العادلة تتجاوز عتبات الشروط التعاقدية"),
    ("Currency pressure amplification — USD/local peg stress escalates import costs",
     "تضخيم ضغط العملة — ضغط ربط العملة بالدولار يرفع تكاليف الاستيراد"),
    ("Network centrality amplification — high-degree node failure multiplies disruption",
     "تضخيم مركزية الشبكة — فشل عقدة ذات درجة عالية يضاعف الاضطراب"),
    ("Reinsurance cession pressure — cedants breach treaty loss thresholds",
     "ضغط تنازل إعادة التأمين — تتجاوز الشركات المتنازلة عتبات الخسارة في المعاهدة"),
    ("Sovereign spillover — rising CDS spreads tighten government funding costs",
     "الامتداد السيادي — ارتفاع فروق أسعار CDS يرفع تكاليف تمويل الحكومة"),
    ("Energy price shock — oil/gas price volatility erodes fiscal surplus buffers",
     "صدمة أسعار الطاقة — تؤدي تقلبات أسعار النفط والغاز إلى تآكل احتياطيات الفائض المالي"),
    ("Digital payment system saturation — RTGS queue builds, settlement delays mount",
     "تشبع نظام الدفع الرقمي — تتراكم قائمة RTGS وتتزايد تأخيرات التسوية"),
    ("Insurance moral hazard acceleration — claims reporting surge strains adjusters",
     "تسارع الخطر الأخلاقي في التأمين — موجة الإبلاغ عن المطالبات تُثقل المقيّمين"),
    ("Port congestion feedback — vessel queuing multiplies delay costs exponentially",
     "تأثير ازدحام الميناء — تصطف السفن وترتفع تكاليف التأخير بصورة أسية"),
    ("Trade finance freeze — letters of credit refused at stressed issuing banks",
     "تجميد تمويل التجارة — رفض خطابات الاعتماد من البنوك المُصدِرة المتعثرة"),
    ("Labour market shock — sector-specific unemployment rises, consumer demand falls",
     "صدمة سوق العمل — ترتفع البطالة القطاعية وتنخفض الطلب الاستهلاكي"),
    ("GCC fiscal coordination gap — asymmetric policy responses amplify volatility",
     "فجوة التنسيق المالي الخليجي — الاستجابات السياسية غير المتماثلة تضخّم التقلبات"),
    ("Systemic interconnectedness — central node cascade triggers multi-hop failure",
     "الترابط النظامي — تتالي العقدة المركزية يُشغّل فشل متعدد القفزات"),
]


# ---------------------------------------------------------------------------
# 1. Causal Chain Builder
# ---------------------------------------------------------------------------

def build_causal_chain(
    shock_nodes: list[str],
    propagation: list[dict],
    financial_impacts: list[dict],
    severity: float,
) -> list[dict]:
    """
    Build an ordered causal chain of up to 20 propagation steps.

    Each step enriched with:
      entity_label_ar, impact_usd, stress_delta, mechanism_en, mechanism_ar,
      sector, hop, confidence

    If the propagation list yields fewer than 20 unique hops, intermediate
    mechanism sub-steps are synthesised by expanding each high-impact hop
    into sector-specific intermediate steps until the chain reaches 20 entries.
    """
    severity = clamp(severity, 0.0, 1.0)

    # Build loss lookup by entity_id
    loss_by_entity: dict[str, float] = {
        fi["entity_id"]: fi.get("loss_usd", 0.0) for fi in financial_impacts
    }

    chain: list[dict] = []
    seen: set[str] = set()

    # First: inject shock origin nodes at step 0
    for sn in shock_nodes[:3]:
        if sn in seen:
            continue
        seen.add(sn)
        mech_en, mech_ar = _MECHANISMS[0]
        label = sn.replace("_", " ").title()
        loss = loss_by_entity.get(sn, severity * 500_000_000)
        chain.append({
            "step": 0,
            "entity_id": sn,
            "entity_label": label,
            "entity_label_ar": _to_arabic_label(sn),
            "impact_usd": round(loss, 2),
            "impact_usd_formatted": format_loss_usd(loss),
            "stress_delta": round(severity, 4),
            "mechanism_en": mech_en,
            "mechanism_ar": mech_ar,
            "sector": _infer_sector(sn),
            "hop": 0,
            "confidence": round(clamp(0.95 - len(chain) * 0.02, 0.5, 0.98), 3),
        })

    # Then: propagation chain
    for row in propagation:
        if len(chain) >= 20:
            break
        eid = row["entity_id"]
        if eid in seen:
            continue
        seen.add(eid)

        step = row.get("step", len(chain))
        impact = row.get("impact", 0.0)

        mech_idx = (step + hash(eid[:4]) % 7) % len(_MECHANISMS)
        mech_en, mech_ar = _MECHANISMS[mech_idx]

        loss = loss_by_entity.get(eid, impact * severity * 200_000_000)
        confidence = round(clamp(0.92 - step * 0.03 - (1 - severity) * 0.05, 0.45, 0.95), 3)

        chain.append({
            "step": step,
            "entity_id": eid,
            "entity_label": eid.replace("_", " ").title(),
            "entity_label_ar": _to_arabic_label(eid),
            "impact_usd": round(loss, 2),
            "impact_usd_formatted": format_loss_usd(loss),
            "stress_delta": round(impact, 4),
            "mechanism_en": mech_en,
            "mechanism_ar": mech_ar,
            "sector": _infer_sector(eid),
            "hop": step,
            "confidence": confidence,
        })

    # Sort by step then stress_delta
    chain.sort(key=lambda x: (x["step"], -x["stress_delta"]))

    # Re-sequence steps 0..n-1
    for i, item in enumerate(chain):
        item["step"] = i

    # ── Expansion phase: pad to 20 steps using intermediate mechanism steps ──
    # Sector-to-mechanism index mapping for expansions
    _SECTOR_MECH_OFFSETS: dict[str, list[int]] = {
        "energy":         [12, 4, 11],
        "maritime":       [15, 3, 9],
        "banking":        [1, 6, 7, 8],
        "insurance":      [10, 14, 7],
        "fintech":        [13, 8, 5],
        "logistics":      [3, 15, 17],
        "infrastructure": [5, 9, 18],
        "government":     [11, 18, 6],
        "healthcare":     [17, 4, 19],
    }

    if len(chain) < 20:
        # Pick the highest-impact entries from chain (source hops) to expand
        sources = sorted(chain, key=lambda x: -x["stress_delta"])
        expansion_idx = 0
        while len(chain) < 20:
            src = sources[expansion_idx % max(len(sources), 1)]
            base_hop = src["hop"]
            sector = src["sector"]
            offsets = _SECTOR_MECH_OFFSETS.get(sector, [1, 5, 9])
            mech_offset = offsets[expansion_idx % len(offsets)]
            mech_en, mech_ar = _MECHANISMS[mech_offset % len(_MECHANISMS)]

            # Attenuate stress and loss with each expansion step
            attenuation = 0.75 ** (expansion_idx // max(len(sources), 1) + 1)
            sub_impact = round(src["stress_delta"] * attenuation, 4)
            sub_loss = src["impact_usd"] * attenuation

            synthetic_id = f"{src['entity_id']}_sub{expansion_idx}"
            confidence = round(clamp(src["confidence"] * 0.92 - expansion_idx * 0.01, 0.35, 0.90), 3)

            chain.append({
                "step": len(chain),
                "entity_id": synthetic_id,
                "entity_label": f"{src['entity_label']} (Secondary Effect {expansion_idx + 1})",
                "entity_label_ar": f"{src['entity_label_ar']} (أثر ثانوي {expansion_idx + 1})",
                "impact_usd": round(sub_loss, 2),
                "impact_usd_formatted": format_loss_usd(sub_loss),
                "stress_delta": sub_impact,
                "mechanism_en": mech_en,
                "mechanism_ar": mech_ar,
                "sector": sector,
                "hop": base_hop + expansion_idx // max(len(sources), 1) + 1,
                "confidence": confidence,
            })
            expansion_idx += 1

    # Final re-sequence
    for i, item in enumerate(chain):
        item["step"] = i

    return chain[:20]


# ---------------------------------------------------------------------------
# 2. Narrative builder (bilingual, template-based)
# ---------------------------------------------------------------------------

_EN_TEMPLATES: list[str] = [
    (
        "A {severity_label} severity event has emerged across the GCC financial network "
        "under scenario '{scenario_id}'. The simulation projects a total economic impact of "
        "{loss_formatted} over a {peak_day}-day shock horizon, with system-wide risk classified "
        "as {risk_level}. The {top_sector} sector registers the highest exposure. "
        "Confidence in this projection is {confidence_pct}%."
    ),
    (
        "Scenario '{scenario_id}' has been activated at {severity_label} severity. "
        "Impact modelling identifies {affected_count} affected entities across the GCC, "
        "with an estimated financial loss of {loss_formatted}. Peak stress is expected "
        "on day {peak_day}. The unified risk score places the system at {risk_level} level. "
        "Analytical confidence is rated at {confidence_pct}%."
    ),
]

_AR_TEMPLATES: list[str] = [
    (
        "ظهر حدث بمستوى خطورة {severity_label_ar} عبر الشبكة المالية الخليجية "
        "في سيناريو '{scenario_id}'. تتوقع المحاكاة تأثيراً اقتصادياً إجمالياً قدره "
        "{loss_formatted} خلال أفق صدمة {peak_day} أيام، مع تصنيف المخاطر الشاملة بمستوى "
        "{risk_level_ar}. يُسجّل قطاع {top_sector_ar} أعلى مستوى تعرض. "
        "ثقة هذا التوقع تبلغ {confidence_pct}%."
    ),
    (
        "تم تفعيل سيناريو '{scenario_id}' بمستوى خطورة {severity_label_ar}. "
        "يُحدد نمذجة الأثر {affected_count} كياناً متأثراً عبر منطقة الخليج، "
        "مع خسارة مالية مُقدَّرة بـ {loss_formatted}. يُتوقع ذروة الضغط في اليوم {peak_day}. "
        "تضع درجة المخاطر الموحدة النظام عند مستوى {risk_level_ar}. "
        "التقييم التحليلي مُصنَّف بثقة {confidence_pct}%."
    ),
]

_SECTOR_ARABIC: dict[str, str] = {
    "energy":         "الطاقة",
    "maritime":       "الملاحة البحرية",
    "banking":        "الخدمات المصرفية",
    "insurance":      "التأمين",
    "fintech":        "التقنية المالية",
    "logistics":      "اللوجستيات",
    "infrastructure": "البنية التحتية",
    "government":     "الحكومة",
    "healthcare":     "الرعاية الصحية",
}


def build_narrative(
    scenario_id: str,
    severity: float,
    risk_level: str,
    total_loss_usd: float,
    peak_day: int,
    affected_count: int,
    top_sector: str,
    confidence_score: float,
) -> dict:
    """
    Generate bilingual executive narrative using templates (no LLM).

    Returns {narrative_en: str, narrative_ar: str}.
    """
    sev_label = severity_label(severity)
    sev_label_ar_str = severity_label_ar(severity)
    risk_ar = risk_label_ar(risk_level)
    loss_fmt = format_loss_usd(total_loss_usd)
    confidence_pct = round(confidence_score * 100, 1)
    top_sector_ar = _SECTOR_ARABIC.get(top_sector, top_sector)
    scenario_clean = scenario_id.replace("_", " ").title()

    # Choose template based on severity bucket
    tpl_idx = 0 if severity < 0.5 else 1

    narrative_en = _EN_TEMPLATES[tpl_idx].format(
        severity_label=sev_label,
        scenario_id=scenario_clean,
        loss_formatted=loss_fmt,
        peak_day=peak_day,
        risk_level=risk_level,
        affected_count=affected_count,
        top_sector=top_sector.title(),
        confidence_pct=confidence_pct,
    )

    narrative_ar = _AR_TEMPLATES[tpl_idx].format(
        severity_label_ar=sev_label_ar_str,
        scenario_id=scenario_clean,
        loss_formatted=loss_fmt,
        peak_day=peak_day,
        risk_level_ar=risk_ar,
        affected_count=affected_count,
        top_sector_ar=top_sector_ar,
        confidence_pct=confidence_pct,
    )

    return {
        "narrative_en": narrative_en.strip(),
        "narrative_ar": narrative_ar.strip(),
    }


# ---------------------------------------------------------------------------
# 3. Sensitivity Analysis
# ---------------------------------------------------------------------------

def compute_sensitivity(
    base_severity: float,
    base_loss: float,
    base_risk_score: float,
) -> dict:
    """
    Perturb severity at ±10%, ±20% and report output deltas.

    Assumes quadratic loss scaling and linear risk score scaling.
    """
    base_severity = clamp(base_severity, 0.0, 1.0)

    perturbations_pct = [-0.20, -0.10, +0.10, +0.20]
    perturbations: list[dict] = []

    for delta_pct in perturbations_pct:
        perturbed_sev = clamp(base_severity * (1 + delta_pct), 0.0, 1.0)

        # Loss scales quadratically with severity (from risk_models equation)
        ratio_sq = (perturbed_sev / max(base_severity, 0.001)) ** 2
        resulting_loss = base_loss * ratio_sq

        # Risk score scales roughly linearly (from unified_risk model)
        ratio_lin = perturbed_sev / max(base_severity, 0.001)
        resulting_risk_score = clamp(base_risk_score * ratio_lin, 0.0, 1.0)

        loss_change_pct = round((resulting_loss - base_loss) / max(base_loss, 1) * 100, 2)
        risk_change_pct = round((resulting_risk_score - base_risk_score) / max(base_risk_score, 0.001) * 100, 2)

        perturbations.append({
            "delta_severity_pct": round(delta_pct * 100, 1),
            "perturbed_severity": round(perturbed_sev, 4),
            "resulting_loss_usd": round(resulting_loss, 2),
            "resulting_risk_score": round(resulting_risk_score, 4),
            "loss_change_pct": loss_change_pct,
            "risk_change_pct": risk_change_pct,
        })

    # Linearity score: how consistently proportional are the changes?
    # Perfect linearity = 1.0; non-linear = approaches 0
    loss_changes = [abs(p["loss_change_pct"]) for p in perturbations]
    if len(loss_changes) >= 2 and max(loss_changes) > 0:
        linearity_score = round(
            1.0 - (max(loss_changes) - min(loss_changes)) / max(max(loss_changes), 1),
            4,
        )
    else:
        linearity_score = 1.0

    return {
        "perturbations": perturbations,
        "most_sensitive_parameter": "severity",
        "linearity_score": linearity_score,
        "base_severity": base_severity,
        "base_loss_usd": base_loss,
        "base_risk_score": base_risk_score,
    }


# ---------------------------------------------------------------------------
# 4. Uncertainty Bands
# ---------------------------------------------------------------------------

def compute_uncertainty_bands(base_score: float, confidence: float) -> dict:
    """
    Compute ±uncertainty bounds around a base_score.

    Band width = (1 - confidence) * 0.4
    Lower bound = max(0, base_score - band_width / 2)
    Upper bound = min(1, base_score + band_width / 2)
    """
    base_score = clamp(base_score, 0.0, 1.0)
    confidence = clamp(confidence, 0.0, 1.0)

    band_width = (1.0 - confidence) * 0.40
    lower = clamp(base_score - band_width / 2.0, 0.0, 1.0)
    upper = clamp(base_score + band_width / 2.0, 0.0, 1.0)

    if base_score < 0.35:
        interp = "Model uncertainty is low; additional data collection is recommended but not urgent."
    elif base_score < 0.65:
        interp = (
            "Moderate uncertainty band — outcome may vary between "
            f"{classify_stress(lower)} and {classify_stress(upper)} classifications. "
            "Cross-validate with sector subject matter experts."
        )
    else:
        interp = (
            f"Wide uncertainty band at high risk levels ({classify_stress(lower)}–{classify_stress(upper)}). "
            "Precautionary actions should be initiated at the lower bound; "
            "do not wait for confirmation before activating escalation protocols."
        )

    return {
        "lower_bound": round(lower, 4),
        "upper_bound": round(upper, 4),
        "band_width": round(band_width, 4),
        "interpretation": interp,
        "confidence": round(confidence, 4),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _infer_sector(entity_id: str) -> str:
    eid = entity_id.lower()
    if any(k in eid for k in ("bank", "financial", "credit", "monetary")):
        return "banking"
    if any(k in eid for k in ("oil", "gas", "lng", "energy", "petro")):
        return "energy"
    if any(k in eid for k in ("port", "ship", "maritime", "hormuz", "lane")):
        return "maritime"
    if any(k in eid for k in ("insur", "takaful")):
        return "insurance"
    if any(k in eid for k in ("fintech", "payment", "swift")):
        return "fintech"
    if any(k in eid for k in ("logistic", "cargo", "freight")):
        return "logistics"
    return "infrastructure"


def _to_arabic_label(entity_id: str) -> str:
    """Map common GCC node ids to Arabic labels."""
    _LABELS_AR: dict[str, str] = {
        "hormuz":              "مضيق هرمز",
        "dubai_port":          "ميناء دبي",
        "abu_dhabi_port":      "ميناء أبوظبي",
        "riyadh_financial":    "مركز الرياض المالي",
        "qatar_lng":           "منشآت LNG القطرية",
        "kuwait_oil":          "منشآت النفط الكويتية",
        "bahrain_banking":     "القطاع المصرفي البحريني",
        "oman_trade":          "البنية التجارية العُمانية",
        "shipping_lanes":      "ممرات الشحن",
        "uae_banking":         "القطاع المصرفي الإماراتي",
        "saudi_banking":       "القطاع المصرفي السعودي",
        "gcc_insurance":       "تأمين الخليج",
        "gcc_fintech":         "التقنية المالية الخليجية",
        "saudi_aramco":        "أرامكو السعودية",
        "adnoc":               "أدنوك",
    }
    label = _LABELS_AR.get(entity_id)
    if label:
        return label
    return entity_id.replace("_", " ")
