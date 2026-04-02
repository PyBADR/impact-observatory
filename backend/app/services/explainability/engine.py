"""Explainability Engine — Generates bilingual ExplanationPack from observatory results.

Produces human-readable summaries, causal chain descriptions, and confidence notes
for executive, analyst, and regulatory audiences. All outputs are AR/EN bilingual.
"""

from typing import List, Dict, Any

from app.schemas.observatory import (
    ScenarioInput,
    FinancialImpact,
    BankingStress,
    InsuranceStress,
    FintechStress,
    DecisionAction,
    ExplanationPack,
)


def compute_explanation(
    scenario: ScenarioInput,
    financial_impact: FinancialImpact,
    banking: BankingStress,
    insurance: InsuranceStress,
    fintech: FintechStress,
    decisions: List[DecisionAction],
) -> ExplanationPack:
    """
    Generate bilingual explanation pack from observatory results.

    Args:
        scenario: Input scenario
        financial_impact: Financial impact results
        banking: Banking stress results
        insurance: Insurance stress results
        fintech: Fintech stress results
        decisions: Top decision actions

    Returns:
        ExplanationPack with summaries, findings, causal chain, and audit trail
    """
    loss = financial_impact.headline_loss_usd
    sev = financial_impact.severity_code
    ttf = financial_impact.time_to_failure_days

    # Executive summary
    summary_en = (
        f"{scenario.name} triggers ${loss:.1f}B headline loss ({sev} severity). "
        f"Banking sector at {banking.stress_level} stress (CAR {banking.capital_adequacy_ratio:.1%}), "
        f"insurance at {insurance.stress_level} (CR {insurance.combined_ratio:.2f}), "
        f"fintech at {fintech.stress_level} ({fintech.payment_failure_rate:.1%} payment failure). "
        f"Critical failure window: {ttf} days."
    )

    summary_ar = (
        f"{scenario.name_ar} يؤدي إلى خسارة {loss:.1f} مليار دولار (شدة {sev}). "
        f"القطاع البنكي عند مستوى {banking.stress_level} "
        f"(كفاية رأس المال {banking.capital_adequacy_ratio:.1%})، "
        f"التأمين عند {insurance.stress_level} (النسبة المجمعة {insurance.combined_ratio:.2f})، "
        f"الفنتك عند {fintech.stress_level} (معدل فشل المدفوعات {fintech.payment_failure_rate:.1%}). "
        f"نافذة الانهيار: {ttf} أيام."
    )

    # Key findings
    findings: List[Dict[str, str]] = []

    findings.append({
        "en": f"Headline financial loss estimated at ${loss:.1f}B with {financial_impact.confidence:.0%} confidence.",
        "ar": f"الخسارة المالية المقدرة {loss:.1f} مليار دولار بثقة {financial_impact.confidence:.0%}.",
    })

    if banking.stress_level == "CRITICAL":
        findings.append({
            "en": f"Banking sector faces CRITICAL stress — capital adequacy at {banking.capital_adequacy_ratio:.1%}, below Basel III 10% warning threshold.",
            "ar": f"القطاع البنكي يواجه ضغطًا حرجًا — كفاية رأس المال عند {banking.capital_adequacy_ratio:.1%}، أقل من عتبة تحذير بازل 3.",
        })

    if insurance.reinsurance_trigger:
        findings.append({
            "en": f"Insurance claims surge of +{insurance.claims_surge_pct:.0f}% has triggered reinsurance treaty activation.",
            "ar": f"ارتفاع المطالبات بنسبة +{insurance.claims_surge_pct:.0f}% أدى إلى تفعيل اتفاقية إعادة التأمين.",
        })

    if fintech.payment_failure_rate > 0.10:
        findings.append({
            "en": f"Payment failure rate of {fintech.payment_failure_rate:.1%} exceeds 10% critical threshold — settlement delays at {fintech.settlement_delay_hours:.0f} hours.",
            "ar": f"معدل فشل المدفوعات {fintech.payment_failure_rate:.1%} يتجاوز عتبة 10% — تأخير التسوية {fintech.settlement_delay_hours:.0f} ساعة.",
        })

    if decisions:
        top = decisions[0]
        findings.append({
            "en": f"Top recommended action: {top.title} (priority {top.priority:.2f}, cost ${top.cost_usd/1e6:.0f}M, avoids ${top.loss_avoided_usd/1e9:.1f}B).",
            "ar": f"الإجراء الأول المقترح: {top.title_ar} (أولوية {top.priority:.2f}، تكلفة ${top.cost_usd/1e6:.0f}M، يتجنب ${top.loss_avoided_usd/1e9:.1f}B).",
        })

    # Causal chain
    causal_chain = _build_causal_chain(scenario, financial_impact, banking, insurance, fintech)

    # Confidence note
    confidence_note = (
        f"Deterministic model with {financial_impact.confidence:.0%} confidence. "
        f"Higher severity scenarios carry wider uncertainty bands. "
        f"Results should be validated against Monte Carlo simulation for production decisions."
    )

    # Audit trail
    audit_trail: Dict[str, Any] = {
        "scenario_id": scenario.id,
        "severity": scenario.severity,
        "duration_days": scenario.duration_days,
        "financial_headline_loss_usd_bn": round(loss, 2),
        "banking_stress_level": banking.stress_level,
        "insurance_stress_level": insurance.stress_level,
        "fintech_stress_level": fintech.stress_level,
        "decisions_count": len(decisions),
        "model_type": "deterministic_v1",
        "model_confidence": round(financial_impact.confidence, 3),
    }

    return ExplanationPack(
        summary_en=summary_en,
        summary_ar=summary_ar,
        key_findings=findings,
        causal_chain=causal_chain,
        confidence_note=confidence_note,
        data_sources=[
            "gcc-knowledge-graph (76 nodes, 191 edges)",
            "BASES macroeconomic constants",
            "HORMUZ_MULTIPLIERS calibration set",
        ],
        audit_trail=audit_trail,
    )


def _build_causal_chain(
    scenario: ScenarioInput,
    fi: FinancialImpact,
    bs: BankingStress,
    ins: InsuranceStress,
    ft: FintechStress,
) -> List[str]:
    """Build entity-level causal propagation chain."""
    chain = [scenario.id]

    # Always: scenario → oil/shipping → GDP
    if "hormuz" in scenario.id.lower() or "hormuz" in scenario.name.lower():
        chain.extend(["hormuz_strait", "oil_exports_gcc", "shipping_corridor"])

    chain.append("gcc_gdp")
    chain.append(f"financial_impact_${fi.headline_loss_usd:.0f}B")

    # Sector branches
    if bs.stress_level in ("HIGH", "CRITICAL"):
        chain.append(f"banking_sector_{bs.stress_level}")
    if ins.stress_level in ("HIGH", "CRITICAL"):
        chain.append(f"insurance_sector_{ins.stress_level}")
    if ft.stress_level in ("HIGH", "CRITICAL"):
        chain.append(f"fintech_sector_{ft.stress_level}")

    chain.append("decision_actions")
    return chain
