"""Impact Engine — converts propagation results into structured ImpactAssessment.

Consumes the full pipeline output dict and produces a validated ImpactAssessment.
All weights from config.py. Deterministic. Fail-safe (works without graph).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.config import (
    IE_W1, IE_W2, IE_W3, IE_W4,
    IE_DOMAIN_EXPOSURE_THRESHOLD,
    RISK_THRESHOLDS,
)
from src.utils import clamp
from src.impact_engine.domain_classifier import classify_domains
from src.impact_engine.entity_ranker import rank_entities
from src.impact_engine.time_horizon import compute_time_horizon

logger = logging.getLogger(__name__)


def _classify_risk(score: float) -> str:
    """Map [0,1] score to risk classification."""
    for label, (lo, hi) in RISK_THRESHOLDS.items():
        if lo <= score < hi:
            return label
    return "SEVERE" if score >= 0.80 else "NOMINAL"


def _extract_urs_score(unified_risk_score: Any) -> float:
    """Extract float score from URS which may be float or dict."""
    if isinstance(unified_risk_score, dict):
        return float(unified_risk_score.get("score", 0.0))
    return float(unified_risk_score or 0.0)


def compute_impact_assessment(
    pipeline_output: dict[str, Any],
    gcc_nodes: list[dict[str, Any]],
    scenario_catalog: dict[str, Any],
    graph_store: Optional[Any] = None,
) -> dict[str, Any]:
    """Compute structured impact assessment from pipeline output.

    DETERMINISTIC: Same input → same output.
    FAIL-SAFE: Works without graph_store.
    CONTRACT: Returns dict that passes ImpactAssessment.model_validate().
    """
    run_id = pipeline_output.get("run_id", "")
    scenario_id = pipeline_output.get("scenario_id", "")

    # ── Extract pipeline signals ──────────────────────────────────────────
    event_severity = float(pipeline_output.get("event_severity", 0.0))
    propagation_score = float(pipeline_output.get("propagation_score", 0.0))
    urs = _extract_urs_score(pipeline_output.get("unified_risk_score", 0.0))
    confidence_score = float(pipeline_output.get("confidence_score", 0.0))
    risk_level = pipeline_output.get("risk_level", "NOMINAL")
    peak_day = int(pipeline_output.get("peak_day", 0))

    financial_impact = pipeline_output.get("financial_impact", {})
    total_loss_usd = float(financial_impact.get("total_loss_usd", 0.0))
    direct_loss_usd = float(financial_impact.get("direct_loss_usd", 0.0))
    indirect_loss_usd = float(financial_impact.get("indirect_loss_usd", 0.0))
    systemic_loss_usd = float(financial_impact.get("systemic_loss_usd", 0.0))
    gdp_impact_pct = float(financial_impact.get("gdp_impact_pct", 0.0))
    financial_impacts_list = financial_impact.get("top_entities", [])

    sector_analysis = pipeline_output.get("sector_analysis", [])
    propagation_chain = pipeline_output.get("propagation_chain", [])
    recovery_trajectory = pipeline_output.get("recovery_trajectory", [])

    banking_stress = pipeline_output.get("banking_stress", {})
    insurance_stress = pipeline_output.get("insurance_stress", {})

    # Time to first failure from banking stress
    ttff = float(banking_stress.get("time_to_breach_hours",
                  banking_stress.get("time_to_liquidity_breach_hours", 9999.0)))

    horizon_days = int(pipeline_output.get("time_horizon_days", 14))

    # ── Build sector_exposure from sector_analysis ────────────────────────
    sector_exposure: dict[str, float] = {}
    for sa in sector_analysis:
        s = sa.get("sector", "")
        if s:
            sector_exposure[s] = float(sa.get("exposure", 0.0))

    # ── Resolve scenario metadata ─────────────────────────────────────────
    scenario_meta = scenario_catalog.get(scenario_id, {})
    shock_nodes: list[str] = scenario_meta.get("shock_nodes", [])
    node_sectors: dict[str, str] = scenario_meta.get("node_sectors", {})

    # ── Peak sector stress ────────────────────────────────────────────────
    lsi = float(banking_stress.get("aggregate_stress", 0.0))
    isi = float(insurance_stress.get("aggregate_stress",
                 insurance_stress.get("severity_index", 0.0)))
    peak_stress = max(lsi, isi)

    # ── Composite severity ────────────────────────────────────────────────
    # CompositeSeverity = IE_W1*URS + IE_W2*EventSev + IE_W3*PropScore + IE_W4*PeakStress
    composite_severity = clamp(
        IE_W1 * urs + IE_W2 * event_severity + IE_W3 * propagation_score + IE_W4 * peak_stress,
        0.0,
        1.0,
    )
    severity_classification = _classify_risk(composite_severity)

    # ── Domain classification ─────────────────────────────────────────────
    affected_domains = classify_domains(
        sector_analysis=sector_analysis,
        sector_exposure=sector_exposure,
        financial_impacts=financial_impacts_list,
        shock_nodes=shock_nodes,
        node_sectors=node_sectors,
        total_loss_usd=total_loss_usd,
    )

    primary_domain = affected_domains[0]["domain"] if affected_domains else ""
    domain_count = len(affected_domains)
    cross_domain = domain_count > 1

    # ── Entity ranking ────────────────────────────────────────────────────
    affected_entities = rank_entities(
        financial_impacts=financial_impacts_list,
        propagation_chain=propagation_chain,
        shock_nodes=shock_nodes,
        node_sectors=node_sectors,
    )

    entity_count = len(affected_entities)
    critical_entity_count = sum(
        1 for e in affected_entities
        if e.get("classification") in ("HIGH", "SEVERE")
    )

    # ── Time horizon ──────────────────────────────────────────────────────
    time_horizon = compute_time_horizon(
        peak_day=peak_day,
        total_loss_usd=total_loss_usd,
        recovery_trajectory=recovery_trajectory,
        time_to_first_failure_hours=ttff,
        horizon_days=horizon_days,
    )

    # ── Source stages that contributed ─────────────────────────────────────
    source_stages = [
        "event_severity", "sector_exposure", "propagation",
        "liquidity_stress", "insurance_stress", "financial_losses",
        "unified_risk_score", "confidence", "physics", "recovery",
    ]
    graph_enriched = graph_store is not None

    # ── Assemble ──────────────────────────────────────────────────────────
    assessment = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "assessment_version": "1.0.0",

        "composite_severity": round(composite_severity, 4),
        "severity_classification": severity_classification,
        "confidence": round(confidence_score, 4),

        "affected_domains": affected_domains,
        "primary_domain": primary_domain,
        "domain_count": domain_count,
        "cross_domain_propagation": cross_domain,

        "affected_entities": affected_entities,
        "entity_count": entity_count,
        "critical_entity_count": critical_entity_count,

        "total_exposure_usd": round(total_loss_usd, 2),
        "direct_exposure_usd": round(direct_loss_usd, 2),
        "indirect_exposure_usd": round(indirect_loss_usd, 2),
        "systemic_exposure_usd": round(systemic_loss_usd, 2),
        "gdp_impact_pct": round(gdp_impact_pct, 6),

        "time_horizon": time_horizon,

        "source_pipeline_stages": source_stages,
        "graph_enriched": graph_enriched,
    }

    logger.info(
        "[ImpactEngine] severity=%.4f domains=%d entities=%d loss=$%.0f",
        composite_severity, domain_count, entity_count, total_loss_usd,
    )

    return assessment
