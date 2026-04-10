"""
Decision Confidence Engine — multi-dimensional confidence scoring.

Rules:
  - Confidence MUST NOT be a single number
  - High model dependency → flag
  - Low data quality → external validation required
  - Returns structured ConfidenceObject per decision

Dimensions:
  1. data_quality      — how complete/reliable the input data is
  2. model_reliability  — how much the decision depends on model accuracy
  3. action_feasibility — how executable the action is in practice
  4. causal_strength    — how strong the causal chain is

Consumed by: Stage 60 pipeline
Input: list[AnchoredDecision] + counterfactual + sim_results
Output: list[DecisionConfidence]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.anchoring_engine import AnchoredDecision
from src.decision_intelligence.counterfactual_engine import CounterfactualResult
from src.decision_intelligence.action_simulation_engine import ActionSimResult

logger = logging.getLogger(__name__)

# ── Thresholds ─────────────────────────────────────────────────────────────

_HIGH_MODEL_DEPENDENCY = 0.70    # model_reliability below this → high dependency flag
_LOW_DATA_QUALITY = 0.50         # data_quality below this → external validation required
_WEAK_CAUSAL_CHAIN = 0.40       # causal_strength below this → flag


@dataclass(frozen=True, slots=True)
class ConfidenceDimension:
    """A single dimension of confidence."""
    dimension: str
    score: float              # [0-1]
    label_en: str
    label_ar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 4),
            "label_en": self.label_en,
            "label_ar": self.label_ar,
        }


@dataclass(frozen=True, slots=True)
class DecisionConfidence:
    """Multi-dimensional confidence assessment for a decision."""
    decision_id: str
    action_id: str

    # Overall composite (for sorting — NOT the primary output)
    composite_score: float         # [0-1] weighted average of dimensions

    # Flags
    model_dependency: str          # "low" | "moderate" | "high"
    model_dependency_ar: str
    external_validation_required: bool
    validation_reason_en: str
    validation_reason_ar: str

    # Multi-dimensional breakdown (the primary output)
    dimensions: list[ConfidenceDimension] = field(default_factory=list)

    # Warnings
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "composite_score": round(self.composite_score, 4),
            "dimensions": [d.to_dict() for d in self.dimensions],
            "model_dependency": self.model_dependency,
            "model_dependency_ar": self.model_dependency_ar,
            "external_validation_required": self.external_validation_required,
            "validation_reason_en": self.validation_reason_en,
            "validation_reason_ar": self.validation_reason_ar,
            "warnings": self.warnings,
        }


def compute_decision_confidence(
    anchored_decisions: list[AnchoredDecision],
    counterfactual: CounterfactualResult | None,
    sim_results: list[ActionSimResult],
) -> list[DecisionConfidence]:
    """
    Compute multi-dimensional confidence for each anchored decision.

    Args:
        anchored_decisions: From anchoring_engine.
        counterfactual:     From counterfactual_engine.
        sim_results:        From action_simulation_engine.

    Returns:
        list[DecisionConfidence] — one per valid anchored decision.
    """
    sim_map: dict[str, ActionSimResult] = {s.action_id: s for s in sim_results}
    cf_confidence = counterfactual.confidence if counterfactual else 0.5
    # node_coverage is not stored on CounterfactualResult — derive from confidence
    # confidence = 0.5 + node_coverage*0.3 + event_factor → node_coverage ≈ (confidence - 0.5) / 0.3
    cf_node_coverage = max(0.0, min(1.0, (cf_confidence - 0.5) / 0.3)) if cf_confidence > 0.5 else 0.0

    confidences: list[DecisionConfidence] = []

    for ad in anchored_decisions:
        if not ad.is_valid:
            continue

        sim = sim_map.get(ad.action_id)

        # ── Dimension 1: Data Quality ──────────────────────────────────────
        # Based on: counterfactual confidence + node coverage
        data_quality = _compute_data_quality(cf_confidence, cf_node_coverage)

        # ── Dimension 2: Model Reliability ─────────────────────────────────
        # Based on: how much the sim result depends on model assumptions
        model_reliability = _compute_model_reliability(sim, ad)

        # ── Dimension 3: Action Feasibility ────────────────────────────────
        # Based on: feasibility from registry + time constraints
        action_feasibility = _compute_action_feasibility(ad)

        # ── Dimension 4: Causal Strength ───────────────────────────────────
        # Based on: propagation reduction + nodes affected
        causal_strength = _compute_causal_strength(sim, ad)

        # Build dimensions
        dimensions = [
            ConfidenceDimension(
                dimension="data_quality",
                score=data_quality,
                label_en=_quality_label(data_quality),
                label_ar=_quality_label_ar(data_quality),
            ),
            ConfidenceDimension(
                dimension="model_reliability",
                score=model_reliability,
                label_en=_quality_label(model_reliability),
                label_ar=_quality_label_ar(model_reliability),
            ),
            ConfidenceDimension(
                dimension="action_feasibility",
                score=action_feasibility,
                label_en=_quality_label(action_feasibility),
                label_ar=_quality_label_ar(action_feasibility),
            ),
            ConfidenceDimension(
                dimension="causal_strength",
                score=causal_strength,
                label_en=_quality_label(causal_strength),
                label_ar=_quality_label_ar(causal_strength),
            ),
        ]

        # Composite (weighted)
        composite = (
            0.25 * data_quality
            + 0.25 * model_reliability
            + 0.25 * action_feasibility
            + 0.25 * causal_strength
        )

        # ── Model dependency classification ────────────────────────────────
        if model_reliability < _HIGH_MODEL_DEPENDENCY:
            model_dep = "high"
            model_dep_ar = "عالي"
        elif model_reliability < 0.85:
            model_dep = "moderate"
            model_dep_ar = "معتدل"
        else:
            model_dep = "low"
            model_dep_ar = "منخفض"

        # ── External validation requirement ────────────────────────────────
        ext_val_required = data_quality < _LOW_DATA_QUALITY or causal_strength < _WEAK_CAUSAL_CHAIN
        if ext_val_required:
            val_reason_en = []
            val_reason_ar = []
            if data_quality < _LOW_DATA_QUALITY:
                val_reason_en.append(f"data quality ({data_quality:.2f}) below threshold")
                val_reason_ar.append(f"جودة البيانات ({data_quality:.2f}) أقل من العتبة")
            if causal_strength < _WEAK_CAUSAL_CHAIN:
                val_reason_en.append(f"causal chain weak ({causal_strength:.2f})")
                val_reason_ar.append(f"السلسلة السببية ضعيفة ({causal_strength:.2f})")
            val_en = "External validation required: " + "; ".join(val_reason_en)
            val_ar = "التحقق الخارجي مطلوب: " + "؛ ".join(val_reason_ar)
        else:
            val_en = "No external validation required"
            val_ar = "لا يتطلب تحقق خارجي"

        # ── Warnings ───────────────────────────────────────────────────────
        warnings: list[dict[str, str]] = []
        if model_dep == "high":
            warnings.append({
                "type": "HIGH_MODEL_DEPENDENCY",
                "message_en": f"Decision heavily depends on model accuracy (reliability={model_reliability:.2f})",
                "message_ar": f"القرار يعتمد بشكل كبير على دقة النموذج (موثوقية={model_reliability:.2f})",
            })
        if data_quality < _LOW_DATA_QUALITY:
            warnings.append({
                "type": "LOW_DATA_QUALITY",
                "message_en": f"Input data quality below threshold ({data_quality:.2f})",
                "message_ar": f"جودة بيانات المدخلات أقل من العتبة ({data_quality:.2f})",
            })
        if causal_strength < _WEAK_CAUSAL_CHAIN:
            warnings.append({
                "type": "WEAK_CAUSAL_CHAIN",
                "message_en": f"Causal link between action and outcome is weak ({causal_strength:.2f})",
                "message_ar": f"الرابط السببي بين الإجراء والنتيجة ضعيف ({causal_strength:.2f})",
            })

        confidences.append(DecisionConfidence(
            decision_id=ad.decision_id,
            action_id=ad.action_id,
            composite_score=composite,
            dimensions=dimensions,
            model_dependency=model_dep,
            model_dependency_ar=model_dep_ar,
            external_validation_required=ext_val_required,
            validation_reason_en=val_en,
            validation_reason_ar=val_ar,
            warnings=warnings,
        ))

    logger.info("[ConfidenceEngine] Computed confidence for %d decisions", len(confidences))
    return confidences


# ── Dimension computation helpers ──────────────────────────────────────────

def _compute_data_quality(cf_confidence: float, node_coverage: float) -> float:
    """Data quality = f(counterfactual confidence, node coverage)."""
    # Counterfactual confidence reflects data completeness (50% weight)
    # Node coverage reflects graph completeness (50% weight)
    return min(1.0, cf_confidence * 0.5 + min(1.0, node_coverage * 2.0) * 0.5)


def _compute_model_reliability(
    sim: ActionSimResult | None,
    ad: AnchoredDecision,
) -> float:
    """Model reliability = f(sim results quality, diversity of evidence)."""
    base = 0.6  # baseline model reliability

    if sim:
        # Higher propagation reduction → model has clear signal
        base += sim.propagation_reduction * 0.2
        # More affected nodes → more evidence
        base += min(0.1, len(sim.affected_nodes) / 50)
        # Non-zero loss delta → model producing actionable numbers
        if sim.baseline_loss_usd > 0 and sim.mitigated_loss_usd < sim.baseline_loss_usd:
            base += 0.1

    return min(1.0, base)


def _compute_action_feasibility(ad: AnchoredDecision) -> float:
    """Action feasibility = f(confidence from registry, time pressure, regulatory risk)."""
    base = ad.confidence  # comes from counterfactual.confidence originally

    # Time pressure reduces feasibility
    if ad.time_window_hours < 6:
        base *= 0.85
    elif ad.time_window_hours < 12:
        base *= 0.92

    # High downside risk reduces perceived feasibility
    base *= (1.0 - ad.downside_risk * 0.3)

    return min(1.0, max(0.0, base))


def _compute_causal_strength(
    sim: ActionSimResult | None,
    ad: AnchoredDecision,
) -> float:
    """Causal strength = f(propagation reduction, failure prevention, nodes protected)."""
    if not sim:
        return 0.3  # no simulation data → weak causal chain

    strength = 0.3  # baseline

    # Propagation reduction shows clear causal mechanism
    strength += sim.propagation_reduction * 0.4

    # Failure prevention shows clear outcome change
    if sim.failure_prevention_count > 0:
        strength += min(0.15, sim.failure_prevention_count * 0.05)

    # Nodes protected shows scope of causal effect
    if sim.nodes_protected > 0:
        strength += min(0.15, sim.nodes_protected / 30)

    return min(1.0, strength)


# ── Label helpers ──────────────────────────────────────────────────────────

def _quality_label(score: float) -> str:
    if score >= 0.80:
        return "High"
    if score >= 0.60:
        return "Moderate"
    if score >= 0.40:
        return "Low"
    return "Very Low"


def _quality_label_ar(score: float) -> str:
    if score >= 0.80:
        return "عالي"
    if score >= 0.60:
        return "معتدل"
    if score >= 0.40:
        return "منخفض"
    return "منخفض جداً"
