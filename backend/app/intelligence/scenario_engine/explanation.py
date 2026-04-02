"""Bilingual AR/EN explanation generation.
Produces human-readable scenario descriptions in Arabic and English.
"""


def generate_explanation(
    propagation_result, engine_result, scientist_state: dict, scenario_id: str, lang: str = "ar"
) -> dict:
    """
    Generate bilingual explanation of scenario results.

    Args:
        propagation_result: Result from propagation engine
        engine_result: Result from scenario engine
        scientist_state: State dict with energy, depth, exposure, shockClass
        scenario_id: Scenario identifier
        lang: Language preference (ar/en)

    Returns:
        Dictionary with:
        - en: English explanation
        - ar: Arabic explanation
        - scenario_id: Input scenario ID
        - severity: Shock class (critical/severe/moderate)
    """
    energy = scientist_state.get("energy", 0)
    depth = scientist_state.get("propagationDepth", 0)
    exposure = scientist_state.get("totalExposure", 0)
    shock_class = scientist_state.get("shockClass", "moderate")

    # Base explanations
    en = (
        f"Scenario {scenario_id}: {shock_class} shock detected. "
        f"System energy: {energy:.2f}, propagation depth: {depth} layers, "
        f"total exposure: ${exposure:.1f}B."
    )
    ar = (
        f"سيناريو {scenario_id}: صدمة {shock_class} تم رصدها. "
        f"طاقة النظام: {energy:.2f}، عمق الانتشار: {depth} طبقات، "
        f"التعرض الكلي: ${exposure:.1f}B."
    )

    # Add top affected sectors
    affected_sectors = getattr(propagation_result, "affected_sectors", [])
    top_sectors_en = []
    top_sectors_ar = []

    for sector in (affected_sectors or [])[:3]:
        sector_label = getattr(sector, "sector_label", getattr(sector, "sector", "Unknown"))
        impact_pct = getattr(sector, "avg_impact", 0) * 100
        top_sectors_en.append(f"{sector_label} ({impact_pct:.0f}%)")
        top_sectors_ar.append(f"{sector_label} ({impact_pct:.0f}%)")

    if top_sectors_en:
        en += f" Most affected: {', '.join(top_sectors_en)}."
        ar += f" الأكثر تأثراً: {', '.join(top_sectors_ar)}."

    return {
        "en": en,
        "ar": ar,
        "scenario_id": scenario_id,
        "severity": shock_class,
    }
