"""Macro Intelligence Layer — Impact Engine (Pack 3).

Deterministic computation of MacroImpact from PropagationResult.

Algorithm:
  1. For each PropagationHit → DomainImpact:
       exposure_weight = DOMAIN_EXPOSURE_WEIGHTS[domain]
       weighted_impact = severity_at_hit × exposure_weight

  2. overall_severity = max(severity_at_hit) across all hits

  3. total_exposure_score = mean(weighted_impact) across all hits
       → 0.0 if no hits

  4. confidence = _derive_confidence(total_domains_reached)
       → coverage-based; independent of source signal confidence

  5. impact_reasoning = composed from hit reasonings (preserves graph fragments)

Design rules:
  - Pure function: same PropagationResult → same MacroImpact
  - No external state, no ML, no LLM
  - Preserves all PropagationHit.reasoning strings (including [Graph Brain] annotations)
  - Falls back gracefully if PropagationResult has zero hits
"""

from __future__ import annotations

from src.macro.macro_enums import (
    ImpactDomain,
    SignalConfidence,
    SignalSeverity,
)
from src.macro.macro_validators import severity_from_score
from src.macro.propagation.propagation_schemas import PropagationHit, PropagationResult
from src.macro.impact.impact_models import DomainImpact, MacroImpact


# ── Domain Exposure Weights ───────────────────────────────────────────────────
# Static, deterministic GCC economic exposure weights.
# Reflect systemic importance in the GCC context.
# Source: GCC sector dependency analysis (Pack 3 deterministic constants).
# These NEVER change at runtime — they are part of the decision contract.

DOMAIN_EXPOSURE_WEIGHTS: dict[ImpactDomain, float] = {
    ImpactDomain.OIL_GAS:              0.95,  # sovereign revenue backbone
    ImpactDomain.SOVEREIGN_FISCAL:     0.90,  # government budget linkage
    ImpactDomain.BANKING:              0.85,  # financial system core
    ImpactDomain.TRADE_LOGISTICS:      0.80,  # trade dependency
    ImpactDomain.CAPITAL_MARKETS:      0.75,  # market confidence
    ImpactDomain.ENERGY_GRID:          0.75,  # infrastructure criticality
    ImpactDomain.MARITIME:             0.70,  # chokepoint exposure
    ImpactDomain.REAL_ESTATE:          0.70,  # asset price linkage
    ImpactDomain.AVIATION:             0.65,  # transport network
    ImpactDomain.INSURANCE:            0.65,  # risk transfer mechanism
    ImpactDomain.TELECOMMUNICATIONS:   0.60,  # communications backbone
    ImpactDomain.CYBER_INFRASTRUCTURE: 0.55,  # digital infrastructure
}

_DEFAULT_EXPOSURE_WEIGHT: float = 0.50  # fallback for unmapped domains


def get_exposure_weight(domain: ImpactDomain) -> float:
    """Return static exposure weight for a domain.

    Falls back to _DEFAULT_EXPOSURE_WEIGHT for any unmapped domain.
    This ensures forward compatibility as new ImpactDomain values are added.
    """
    return DOMAIN_EXPOSURE_WEIGHTS.get(domain, _DEFAULT_EXPOSURE_WEIGHT)


# ── Confidence Derivation ─────────────────────────────────────────────────────

def _derive_confidence(total_domains_reached: int) -> SignalConfidence:
    """Derive impact confidence from propagation coverage.

    More domains reached means more cross-sector corroboration,
    which increases confidence in the impact assessment.

    This is NOT the source signal's confidence — it reflects how
    widely the impact propagated (breadth = confidence).

    Thresholds:
      0 domains  → UNVERIFIED (no propagation evidence)
      1 domain   → LOW (single-domain signal, limited corroboration)
      2–3 domains → MODERATE (cross-sector propagation confirmed)
      4–6 domains → HIGH (broad propagation, strong corroboration)
      7+ domains  → VERIFIED (system-wide propagation evidence)
    """
    if total_domains_reached == 0:
        return SignalConfidence.UNVERIFIED
    elif total_domains_reached == 1:
        return SignalConfidence.LOW
    elif total_domains_reached <= 3:
        return SignalConfidence.MODERATE
    elif total_domains_reached <= 6:
        return SignalConfidence.HIGH
    else:
        return SignalConfidence.VERIFIED


# ── Hit → DomainImpact ────────────────────────────────────────────────────────

def _hit_to_domain_impact(hit: PropagationHit) -> DomainImpact:
    """Convert a PropagationHit to a DomainImpact."""
    weight = get_exposure_weight(hit.domain)
    weighted = round(hit.severity_at_hit * weight, 6)
    # Clamp to [0.0, 1.0] — product is always in range but be explicit
    weighted = min(1.0, max(0.0, weighted))
    return DomainImpact(
        domain=hit.domain,
        severity_score=hit.severity_at_hit,
        severity_level=hit.severity_level,
        exposure_weight=weight,
        weighted_impact=weighted,
        depth=hit.depth,
        path_description=hit.path_description,
        reasoning=hit.reasoning,
        is_entry_domain=(hit.depth == 0),
        regions=list(hit.regions),
    )


# ── Reasoning Composition ─────────────────────────────────────────────────────

def _compose_reasoning(
    domain_impacts: list[DomainImpact],
    overall_severity: float,
    total_domains: int,
) -> str:
    """Compose a human-readable impact reasoning summary.

    Preserves [Graph Brain] fragments from graph-enriched hits.
    Top 3 highest-severity domains are highlighted in the summary.
    """
    top = sorted(domain_impacts, key=lambda d: d.severity_score, reverse=True)[:3]
    sev_label = severity_from_score(overall_severity).value.upper()

    lines = [
        f"Impact assessment: {sev_label} severity across {total_domains} domain(s).",
        f"Overall severity score: {overall_severity:.4f}.",
    ]

    if top:
        lines.append("Top affected domains:")
        for d in top:
            lines.append(
                f"  [{d.domain.value}] severity={d.severity_score:.4f} "
                f"({d.severity_level.value}), "
                f"exposure_weight={d.exposure_weight:.2f}, "
                f"weighted_impact={d.weighted_impact:.4f}, "
                f"depth={d.depth}."
            )

    # Append full reasoning from each hit (preserves [Graph Brain] annotations)
    if domain_impacts:
        lines.append("--- Propagation reasoning by domain ---")
        for di in sorted(domain_impacts, key=lambda d: d.depth):
            lines.append(f"[{di.domain.value}] {di.reasoning}")

    return "\n".join(lines)


# ── Core Engine ───────────────────────────────────────────────────────────────

def compute_impact(result: PropagationResult) -> MacroImpact:
    """Compute MacroImpact from a PropagationResult.

    This is the primary entry point for the impact assessment layer.

    Algorithm:
      1. Convert each hit to DomainImpact (adds exposure_weight + weighted_impact)
      2. Compute overall_severity = max(hit.severity_at_hit), 0 if no hits
      3. Compute total_exposure_score = mean(weighted_impact), 0 if no hits
      4. Derive confidence from domain coverage breadth
      5. Compose reasoning (preserves graph-enriched reasoning strings)
      6. Return MacroImpact

    Args:
        result: A PropagationResult from the propagation engine.

    Returns:
        MacroImpact — always valid, never raises. Zero-hit results return
        a valid MacroImpact with NOMINAL severity and UNVERIFIED confidence.
    """
    hits = result.hits

    # ── Step 1: Convert hits → DomainImpact ──────────────────────────────────
    domain_impacts: list[DomainImpact] = [_hit_to_domain_impact(h) for h in hits]

    # ── Step 2: Overall severity ──────────────────────────────────────────────
    overall_severity: float = (
        max(di.severity_score for di in domain_impacts)
        if domain_impacts else 0.0
    )
    overall_severity_level: SignalSeverity = severity_from_score(overall_severity)

    # ── Step 3: Total exposure score ──────────────────────────────────────────
    total_exposure_score: float = (
        round(sum(di.weighted_impact for di in domain_impacts) / len(domain_impacts), 6)
        if domain_impacts else 0.0
    )

    # ── Step 4: Derived confidence ────────────────────────────────────────────
    total_domains = result.total_domains_reached
    confidence = _derive_confidence(total_domains)

    # ── Step 5: Organize domains ──────────────────────────────────────────────
    # Sort by severity descending for the affected_domains list
    sorted_impacts = sorted(domain_impacts, key=lambda d: d.severity_score, reverse=True)
    affected_domains = [d.domain for d in sorted_impacts]
    entry_domains = list(result.entry_domains)

    # ── Step 6: Reasoning composition ─────────────────────────────────────────
    impact_reasoning = _compose_reasoning(domain_impacts, overall_severity, total_domains)

    # ── Step 7: Graph enrichment flag ─────────────────────────────────────────
    graph_enriched = any("[Graph Brain]" in di.reasoning for di in domain_impacts)

    return MacroImpact(
        signal_id=result.signal_id,
        signal_title=result.signal_title,
        overall_severity=overall_severity,
        overall_severity_level=overall_severity_level,
        total_exposure_score=total_exposure_score,
        confidence=confidence,
        domain_impacts=domain_impacts,
        affected_domains=affected_domains,
        entry_domains=entry_domains,
        total_domains_reached=total_domains,
        max_depth=result.max_depth,
        impact_reasoning=impact_reasoning,
        graph_enriched=graph_enriched,
    )
