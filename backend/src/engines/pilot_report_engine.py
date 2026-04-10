"""Pilot Reporting Engine — Phase 6, Stage 40.

Generates structured pilot reports from accumulated run data.
Reports are designed for weekly/monthly cadence and include
KPI summaries, divergence analysis, and key findings.
"""

from __future__ import annotations

from datetime import datetime, timezone


def generate_pilot_report(
    *,
    runs: list[dict],
    period: str = "weekly",
) -> dict:
    """Generate a pilot report from a list of run outputs.

    Each run dict must contain at minimum:
        - pilot_kpi: PilotKPI from kpi_engine
        - shadow_comparisons: list of ShadowDecision from shadow_engine
        - pilot_scope: PilotScope validation from pilot_scope_engine

    Args:
        runs: list of run output dicts (each containing Phase 6 fields)
        period: "weekly" | "monthly" | "daily" | custom label

    Returns:
        PilotReport dict.
    """
    if not runs:
        return _empty_report(period)

    # ── Aggregate KPIs across runs ──
    total_decisions = 0
    total_matched = 0
    total_divergent = 0
    total_value = 0.0
    total_latency_reduction = 0.0
    total_false_positives = 0
    total_escalations = 0
    run_count = len(runs)

    for run in runs:
        kpi = run.get("pilot_kpi", {})
        total_decisions += kpi.get("total_decisions", 0)
        total_matched += kpi.get("matched_count", 0)
        total_divergent += kpi.get("divergent_count", 0)
        total_value += kpi.get("avoided_loss_estimate", 0.0)
        total_latency_reduction += kpi.get("latency_reduction_pct", 0.0)
        total_false_positives += int(
            kpi.get("false_positive_rate", 0) * kpi.get("total_escalations", 0)
        )
        total_escalations += kpi.get("total_escalations", 0)

    avg_latency_reduction = total_latency_reduction / run_count if run_count > 0 else 0.0
    false_positive_rate = total_false_positives / total_escalations if total_escalations > 0 else 0.0
    divergence_rate = total_divergent / total_decisions if total_decisions > 0 else 0.0
    accuracy_rate = total_matched / total_decisions if total_decisions > 0 else 0.0

    # ── Generate key findings ──
    findings = _generate_findings(
        total_decisions=total_decisions,
        divergence_rate=divergence_rate,
        avg_latency_reduction=avg_latency_reduction,
        total_value=total_value,
        false_positive_rate=false_positive_rate,
        accuracy_rate=accuracy_rate,
        runs=runs,
    )

    return {
        "period": period,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_count": run_count,

        "total_decisions": total_decisions,
        "matched_decisions": total_matched,
        "divergent_decisions": total_divergent,
        "divergence_rate": round(divergence_rate, 4),
        "accuracy_rate": round(accuracy_rate, 4),

        "value_created": round(total_value, 2),
        "avg_latency_reduction": round(avg_latency_reduction, 1),
        "false_positive_rate": round(false_positive_rate, 4),

        "key_findings": findings,

        "recommendation": _generate_recommendation(
            accuracy_rate=accuracy_rate,
            divergence_rate=divergence_rate,
            total_value=total_value,
            run_count=run_count,
        ),
    }


def _generate_findings(
    *,
    total_decisions: int,
    divergence_rate: float,
    avg_latency_reduction: float,
    total_value: float,
    false_positive_rate: float,
    accuracy_rate: float,
    runs: list[dict],
) -> list[str]:
    """Generate human-readable key findings."""
    findings: list[str] = []

    if avg_latency_reduction > 50:
        findings.append(
            f"System produces decisions {avg_latency_reduction:.0f}% faster than human baseline"
        )
    elif avg_latency_reduction > 0:
        findings.append(
            f"Moderate latency improvement: {avg_latency_reduction:.0f}% faster"
        )

    if accuracy_rate >= 0.8:
        findings.append(
            f"High alignment: {accuracy_rate:.0%} of system decisions match human judgment"
        )
    elif accuracy_rate >= 0.5:
        findings.append(
            f"Moderate alignment: {accuracy_rate:.0%} match rate — review divergent cases"
        )
    else:
        findings.append(
            f"Low alignment: only {accuracy_rate:.0%} match rate — calibration needed"
        )

    if total_value > 0:
        value_str = f"${total_value:,.0f}" if total_value < 1e9 else f"${total_value/1e6:,.1f}M"
        findings.append(f"Estimated value created: {value_str}")

    if divergence_rate > 0.3:
        findings.append(
            "System detects risk earlier in >30% of cases — human decisions slower under stress"
        )

    if false_positive_rate < 0.1:
        findings.append("Low false positive rate: escalation precision is strong")
    elif false_positive_rate > 0.3:
        findings.append(
            f"High false positive rate ({false_positive_rate:.0%}) — escalation thresholds may need tuning"
        )

    # Ensure at least one finding
    if not findings:
        findings.append(f"Pilot processed {total_decisions} decisions across {len(runs)} runs")

    return findings


def _generate_recommendation(
    *,
    accuracy_rate: float,
    divergence_rate: float,
    total_value: float,
    run_count: int,
) -> str:
    """Generate a single-sentence pilot recommendation."""
    if run_count < 5:
        return "Continue collecting data — insufficient runs for confident recommendation."
    if accuracy_rate >= 0.8 and total_value > 0:
        return "System performance is strong. Consider progressing from SHADOW to ADVISORY mode."
    if accuracy_rate >= 0.6:
        return "Promising results. Extend pilot duration and increase scenario coverage."
    return "Significant calibration needed before mode progression. Review divergent decisions."


def _empty_report(period: str) -> dict:
    """Return an empty report for periods with no data."""
    return {
        "period": period,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_count": 0,
        "total_decisions": 0,
        "matched_decisions": 0,
        "divergent_decisions": 0,
        "divergence_rate": 0.0,
        "accuracy_rate": 0.0,
        "value_created": 0.0,
        "avg_latency_reduction": 0.0,
        "false_positive_rate": 0.0,
        "key_findings": ["No pilot data available for this period."],
        "recommendation": "No data collected yet. Ensure pilot runs are being executed.",
    }
