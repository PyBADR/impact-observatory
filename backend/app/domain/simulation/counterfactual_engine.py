"""
Impact Observatory | مرصد الأثر — Phase 2 Counterfactual Engine
Simulates "what if we take this action?" branches against the baseline.

Design:
  1. Run the base scenario → get PropagationResult + decisions (no_action case)
  2. For each fired decision, re-run propagation with reduced severity
     proportional to the decision's value_avoided_pct
  3. Return a CounterfactualResult containing:
     - no_action: full baseline
     - branches: one per decision, each with reduced loss/stress

This is NOT a Monte Carlo simulation. Each branch is a deterministic
re-run with a single parameter perturbation. The engine answers:
  "If we execute decision X, how much does the total loss decrease?"

Architecture layer: Models (Layer 3 — Models)

No new dependencies. Reuses SimulationRunner for each branch.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.domain.simulation.runner import GenericPropagationResult, SimulationRunner
from app.domain.simulation.decision_engine import generate_decisions, DECISION_RULES
from app.domain.simulation.schemas import (
    CountryImpact,
    DecisionAction,
    RiskLevel,
    SectorImpact,
    Urgency,
)

logger = logging.getLogger("observatory.counterfactual")


# ═══════════════════════════════════════════════════════════════════════════════
# Counterfactual Output Types
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CounterfactualBranch:
    """One "what-if" branch: what happens if we execute this decision."""
    decision: DecisionAction
    total_loss_usd: float
    loss_reduction_usd: float
    loss_reduction_pct: float
    risk_level: RiskLevel
    confidence: float
    top_country: CountryImpact | None
    top_sector: SectorImpact | None
    pathway_headline: str


@dataclass
class CounterfactualResult:
    """Complete counterfactual analysis for a scenario."""
    scenario_slug: str
    severity: float
    horizon_hours: int

    # Baseline: what happens with no intervention
    no_action: NoActionBaseline

    # One branch per fired decision
    branches: list[CounterfactualBranch]

    # Summary
    best_single_action: CounterfactualBranch | None
    combined_max_avoidable_usd: float
    combined_max_avoidable_pct: float


@dataclass
class NoActionBaseline:
    """Baseline scenario with zero intervention."""
    total_loss_usd: float
    risk_level: RiskLevel
    confidence: float
    countries: list[CountryImpact]
    sectors: list[SectorImpact]
    decisions: list[DecisionAction]
    pathway_headlines: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════════════════════

class CounterfactualEngine:
    """Generates counterfactual branches from a base simulation."""

    def __init__(self) -> None:
        self._runner = SimulationRunner()

    def analyze(
        self,
        slug: str,
        severity: float | None = None,
        horizon_hours: int | None = None,
        **extra_params: Any,
    ) -> CounterfactualResult:
        """Run full counterfactual analysis.

        Steps:
          1. Run baseline (no action)
          2. Generate decisions from baseline
          3. For each decision, compute the severity reduction and re-run
          4. Package into CounterfactualResult
        """
        # ── Step 1: Baseline ─────────────────────────────────────────────
        baseline = self._runner.run(slug, severity=severity, horizon_hours=horizon_hours, **extra_params)
        actual_severity = severity if severity is not None else baseline.spec.default_severity
        actual_horizon = horizon_hours if horizon_hours is not None else baseline.spec.default_horizon_hours

        # ── Step 2: Decisions ────────────────────────────────────────────
        decisions = generate_decisions(baseline)

        no_action = NoActionBaseline(
            total_loss_usd=baseline.total_loss_usd,
            risk_level=baseline.country_impacts[0].risk_level if baseline.country_impacts else RiskLevel.NOMINAL,
            confidence=baseline.confidence,
            countries=baseline.country_impacts,
            sectors=baseline.sector_impacts,
            decisions=decisions,
            pathway_headlines=baseline.pathway_headlines,
        )

        if not decisions:
            return CounterfactualResult(
                scenario_slug=slug,
                severity=actual_severity,
                horizon_hours=actual_horizon,
                no_action=no_action,
                branches=[],
                best_single_action=None,
                combined_max_avoidable_usd=0.0,
                combined_max_avoidable_pct=0.0,
            )

        # ── Step 3: Per-decision branches ────────────────────────────────
        branches: list[CounterfactualBranch] = []

        for decision in decisions:
            # Compute how much this decision reduces severity
            # value_avoided_usd / total_loss gives the fractional impact
            if baseline.total_loss_usd > 0:
                reduction_fraction = decision.value_avoided_usd / baseline.total_loss_usd
            else:
                reduction_fraction = 0.0

            # Re-run with reduced severity
            # The decision "absorbs" a fraction of the shock
            reduced_severity = actual_severity * (1.0 - reduction_fraction)
            reduced_severity = max(reduced_severity, 0.01)  # floor

            branch_result = self._runner.run(
                slug,
                severity=reduced_severity,
                horizon_hours=actual_horizon,
                **extra_params,
            )

            loss_reduction = baseline.total_loss_usd - branch_result.total_loss_usd
            loss_reduction_pct = (
                loss_reduction / baseline.total_loss_usd
                if baseline.total_loss_usd > 0
                else 0.0
            )

            branches.append(CounterfactualBranch(
                decision=decision,
                total_loss_usd=round(branch_result.total_loss_usd, 2),
                loss_reduction_usd=round(loss_reduction, 2),
                loss_reduction_pct=round(loss_reduction_pct, 4),
                risk_level=(
                    branch_result.country_impacts[0].risk_level
                    if branch_result.country_impacts
                    else RiskLevel.NOMINAL
                ),
                confidence=branch_result.confidence,
                top_country=branch_result.country_impacts[0] if branch_result.country_impacts else None,
                top_sector=branch_result.sector_impacts[0] if branch_result.sector_impacts else None,
                pathway_headline=(
                    branch_result.pathway_headlines[0]
                    if branch_result.pathway_headlines
                    else "Pathway data unavailable"
                ),
            ))

        # ── Step 4: Summary ──────────────────────────────────────────────
        branches.sort(key=lambda b: b.loss_reduction_usd, reverse=True)
        best = branches[0] if branches else None

        # Combined max avoidable = sum of all branch reductions (capped at baseline)
        # This is an upper bound — actual combined effect would be less due to overlap
        combined = min(
            sum(b.loss_reduction_usd for b in branches),
            baseline.total_loss_usd * 0.85,  # theoretical cap: can't avoid >85%
        )
        combined_pct = combined / baseline.total_loss_usd if baseline.total_loss_usd > 0 else 0.0

        logger.info(
            "Counterfactual analysis: %s, %d branches, best saves %s (%.1f%%)",
            slug,
            len(branches),
            f"${best.loss_reduction_usd:,.0f}" if best else "$0",
            (best.loss_reduction_pct * 100) if best else 0.0,
        )

        return CounterfactualResult(
            scenario_slug=slug,
            severity=actual_severity,
            horizon_hours=actual_horizon,
            no_action=no_action,
            branches=branches,
            best_single_action=best,
            combined_max_avoidable_usd=round(combined, 2),
            combined_max_avoidable_pct=round(combined_pct, 4),
        )
