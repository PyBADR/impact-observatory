"""Reporting Service — Generates structured report payloads from observatory output.

Produces JSON report documents in three modes:
- Executive: headline KPIs + top decisions (1-page equivalent)
- Analyst: full sector breakdown + propagation detail
- Regulatory Brief: compliance-focused with PDPL/IFRS17/Basel III references
"""

from datetime import datetime
from typing import Dict, Any

from app.schemas.observatory import ObservatoryOutput


def generate_executive_report(output: ObservatoryOutput) -> Dict[str, Any]:
    """
    Generate executive-mode report payload.
    Top-level KPIs, severity, top 3 decisions. No detail noise.
    """
    fi = output.financial_impact
    decisions_summary = []
    for d in output.decisions[:3]:
        decisions_summary.append({
            "title": d.title,
            "title_ar": d.title_ar,
            "sector": d.sector,
            "priority": round(d.priority, 2),
            "cost_usd": d.cost_usd,
            "loss_avoided_usd": d.loss_avoided_usd,
        })

    return {
        "report_type": "executive",
        "generated_at": datetime.utcnow().isoformat(),
        "scenario": {
            "name": output.scenario.name,
            "name_ar": output.scenario.name_ar,
            "severity": output.scenario.severity,
            "duration_days": output.scenario.duration_days,
        },
        "headline": {
            "loss_usd_bn": round(fi.headline_loss_usd, 2),
            "severity_code": fi.severity_code,
            "peak_day": fi.peak_day,
            "time_to_failure_days": fi.time_to_failure_days,
            "confidence": round(fi.confidence, 3),
        },
        "sector_stress": {
            "banking": output.banking_stress.stress_level,
            "insurance": output.insurance_stress.stress_level,
            "fintech": output.fintech_stress.stress_level,
        },
        "decisions": decisions_summary,
        "audit_hash": output.audit_hash,
    }


def generate_analyst_report(output: ObservatoryOutput) -> Dict[str, Any]:
    """
    Generate analyst-mode report payload.
    Full sector breakdown with all metrics.
    """
    report = generate_executive_report(output)
    report["report_type"] = "analyst"

    # Add full sector detail
    report["banking_detail"] = {
        "liquidity_gap_usd_bn": round(output.banking_stress.liquidity_gap_usd, 2),
        "capital_adequacy_ratio": round(output.banking_stress.capital_adequacy_ratio, 4),
        "interbank_rate_spike_pp": round(output.banking_stress.interbank_rate_spike, 2),
        "time_to_liquidity_breach_days": output.banking_stress.time_to_liquidity_breach_days,
        "fx_reserve_drawdown_pct": round(output.banking_stress.fx_reserve_drawdown_pct, 2),
        "stress_level": output.banking_stress.stress_level,
    }
    report["insurance_detail"] = {
        "claims_surge_pct": round(output.insurance_stress.claims_surge_pct, 1),
        "reinsurance_trigger": output.insurance_stress.reinsurance_trigger,
        "combined_ratio": round(output.insurance_stress.combined_ratio, 3),
        "solvency_margin_pct": round(output.insurance_stress.solvency_margin_pct, 2),
        "time_to_insolvency_days": output.insurance_stress.time_to_insolvency_days,
        "premium_adequacy": round(output.insurance_stress.premium_adequacy, 3),
        "stress_level": output.insurance_stress.stress_level,
    }
    report["fintech_detail"] = {
        "payment_failure_rate": round(output.fintech_stress.payment_failure_rate, 4),
        "settlement_delay_hours": round(output.fintech_stress.settlement_delay_hours, 1),
        "gateway_downtime_pct": round(output.fintech_stress.gateway_downtime_pct, 2),
        "digital_banking_disruption": round(output.fintech_stress.digital_banking_disruption, 3),
        "time_to_payment_failure_days": output.fintech_stress.time_to_payment_failure_days,
        "stress_level": output.fintech_stress.stress_level,
    }

    # Add propagation data if available
    if output.flow_states:
        report["propagation"] = {
            "timesteps": len(output.flow_states),
            "converged": output.flow_states[-1].converged if output.flow_states else False,
            "peak_stress": max(s.total_stress for s in output.flow_states),
        }

    # Add explanation if available
    if output.explanation:
        report["explanation"] = {
            "summary_en": output.explanation.summary_en,
            "summary_ar": output.explanation.summary_ar,
            "findings_count": len(output.explanation.key_findings),
            "causal_chain": output.explanation.causal_chain,
        }

    return report


def generate_regulatory_brief(output: ObservatoryOutput) -> Dict[str, Any]:
    """
    Generate regulatory-mode report payload.
    Compliance-focused: PDPL, IFRS 17, Basel III, SAMA/CBUAE references.
    """
    report = generate_executive_report(output)
    report["report_type"] = "regulatory_brief"

    # Regulatory compliance assessment
    bs = output.banking_stress
    ins = output.insurance_stress
    reg = output.regulatory

    report["regulatory"] = {
        "pdpl_compliant": reg.pdpl_compliant,
        "ifrs17_impact_usd_bn": round(reg.ifrs17_impact, 2),
        "basel3_car_floor": reg.basel3_car_floor,
        "sama_alert_level": reg.sama_alert_level,
        "cbuae_alert_level": reg.cbuae_alert_level,
        "sanctions_exposure": round(reg.sanctions_exposure, 3),
        "regulatory_triggers": reg.regulatory_triggers,
    }

    # Basel III compliance check
    report["basel3_assessment"] = {
        "current_car": round(bs.capital_adequacy_ratio, 4),
        "minimum_car": 0.08,
        "buffer_remaining": round(max(0, bs.capital_adequacy_ratio - 0.08), 4),
        "breach": bs.capital_adequacy_ratio < 0.08,
        "warning": bs.capital_adequacy_ratio < 0.105,  # 10.5% with conservation buffer
    }

    # Insurance solvency check
    report["solvency_assessment"] = {
        "solvency_margin_pct": round(ins.solvency_margin_pct, 2),
        "minimum_margin_pct": 10.0,
        "combined_ratio": round(ins.combined_ratio, 3),
        "underwriting_loss": ins.combined_ratio > 1.0,
        "reinsurance_triggered": ins.reinsurance_trigger,
    }

    return report
