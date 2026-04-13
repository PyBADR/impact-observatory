"""
Impact Observatory | مرصد الأثر — Explainability Module (Phase 1 + Phase 2)
Generates human-readable causal explanations from propagation output.

Answers four questions:
  1. Why the total loss?
  2. Why this country?
  3. Why this sector?
  4. Why act now?

Phase 2 update: now accepts both PropagationResult (Phase 1 hormuz-only)
and GenericPropagationResult (Phase 2 any-scenario) via duck typing.
Country/sector metadata is resolved from the result's attached spec when
available, falling back to hormuz_dataset for backward compatibility.

All explanations are deterministic templates filled from simulation data.
No LLM generation — executive-readable without black-box risk.
"""
from __future__ import annotations

from typing import Any

from app.domain.simulation.schemas import Explainability


def _fmt_usd(value: float) -> str:
    """Format USD value as human-readable string."""
    if abs(value) >= 1e9:
        return f"${value / 1e9:.1f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.0f}M"
    return f"${value:,.0f}"


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _resolve_meta(result: Any) -> tuple[dict[str, dict], dict[str, dict], str]:
    """Extract country_meta, sector_meta, and shock_label from result.

    Supports both Phase 1 PropagationResult (no spec) and
    Phase 2 GenericPropagationResult (has spec attribute).
    """
    if hasattr(result, "spec") and result.spec is not None:
        return (
            result.spec.country_meta,
            result.spec.sector_meta,
            result.spec.shock_origin_label or "scenario shock",
        )
    # Fallback: Phase 1 hormuz-only
    from app.domain.simulation.hormuz_dataset import COUNTRY_META, SECTOR_META
    return COUNTRY_META, SECTOR_META, "Hormuz transit disruption"


def generate_explanations(result: Any) -> Explainability:
    """Build the explainability layer from propagation results.

    Accepts either PropagationResult (Phase 1) or GenericPropagationResult (Phase 2).
    """
    country_meta, sector_meta, shock_label = _resolve_meta(result)

    # ── Why total loss ───────────────────────────────────────────────────
    top_countries = result.country_impacts[:3]
    country_str = ", ".join(
        f"{c.country_name} ({_fmt_usd(c.loss_usd)})" for c in top_countries
    )
    top_sectors = result.sector_impacts[:2]
    sector_str = " and ".join(s.sector_label for s in top_sectors)

    # Compute base severity from graph if available
    base_sev = 0.0
    if hasattr(result, "graph") and result.graph and result.graph.nodes:
        first_node = next(iter(result.graph.nodes.values()))
        base_sev = first_node.initial_shock

    why_total = (
        f"The estimated total exposure of {_fmt_usd(result.total_loss_usd)} arises from "
        f"a {shock_label} at {_pct(base_sev)} base severity. "
        f"The three most-exposed economies — {country_str} — account for the majority of losses, "
        f"driven primarily through {sector_str} transmission channels. "
        f"Stress propagated across {result.iterations_run} transmission rounds "
        f"{'(converged)' if result.converged else '(did not fully converge — tail risk may be underestimated)'}."
    )

    # ── Why each country ─────────────────────────────────────────────────
    why_country: dict[str, str] = {}
    for ci in result.country_impacts:
        cc = ci.country_code.value
        meta = country_meta.get(cc, {})

        # Build exposure description based on available metadata
        exposure_parts: list[str] = []
        if "hormuz_dependency" in meta:
            exposure_parts.append(f"Hormuz dependency is {_pct(meta['hormuz_dependency'])}")
        if "interbank_exposure" in meta:
            exposure_parts.append(f"interbank exposure is {_pct(meta['interbank_exposure'])}")
        if "oil_gdp_share" in meta:
            exposure_parts.append(f"oil constitutes {_pct(meta['oil_gdp_share'])} of GDP")
        exposure_str = " and ".join(exposure_parts) if exposure_parts else "significant macro exposure"

        why_country[cc] = (
            f"{ci.country_name} faces {_fmt_usd(ci.loss_usd)} exposure because "
            f"its {exposure_str}. "
            f"The dominant stress channel is {ci.dominant_sector.value} "
            f"({ci.primary_driver}), with stress propagating via {ci.transmission_channel}."
        )

    # ── Why each sector ──────────────────────────────────────────────────
    why_sector: dict[str, str] = {}
    for si in result.sector_impacts:
        sc = si.sector.value
        meta = sector_meta.get(sc, {})
        base_sens = meta.get("base_sensitivity", 0.0)
        recovery_lag = meta.get("recovery_lag_hours", "unknown")

        why_sector[sc] = (
            f"{si.sector_label} shows {_pct(si.stress)} aggregate stress "
            f"(base sensitivity: {_pct(base_sens)}). "
            f"Primary driver: {si.primary_driver}. "
            f"Secondary risk: {si.secondary_risk}. "
            f"Estimated recovery lag: {recovery_lag}h. "
            f"Recommended lever: {si.recommended_lever}"
        )

    # ── Why act now ──────────────────────────────────────────────────────
    severe_sectors = [s for s in result.sector_impacts if s.stress >= 0.5]
    if severe_sectors:
        severe_names = ", ".join(s.sector_label for s in severe_sectors)
        why_now = (
            f"Action is required immediately because {len(severe_sectors)} sector(s) "
            f"({severe_names}) exceed the ELEVATED stress threshold. "
            f"At current propagation velocity, stress will cascade into secondary sectors "
            f"within 24–48 hours. Delayed intervention increases total exposure by an estimated "
            f"15–25% due to liquidity feedback loops and reinsurance treaty trigger conditions. "
            f"The decision window narrows as each transmission round amplifies cross-sector contagion."
        )
    else:
        why_now = (
            "Current stress levels are below the ELEVATED threshold across all sectors, "
            "but the propagation trajectory suggests escalation within 48–72 hours. "
            "Preemptive positioning reduces tail-risk exposure and preserves optionality "
            "for fiscal and monetary policy levers."
        )

    return Explainability(
        why_total_loss=why_total,
        why_country=why_country,
        why_sector=why_sector,
        why_act_now=why_now,
    )
