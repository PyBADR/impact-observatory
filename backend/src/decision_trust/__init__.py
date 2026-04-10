"""
Decision Trust Layer — Stage 80.

Transforms high-quality decisions into institutionally reliable,
verifiable, and explainable decisions.

6 engines:
  1. ActionValidationEngine    — structural action validation
  2. ScenarioEnforcementEngine — strict taxonomy enforcement
  3. AuthorityRealismEngine    — country-level governance realism
  4. ExplainabilityEngine      — causal explainability per decision
  5. LearningClosureEngine     — feedback loop for system adaptation
  6. TrustOverrideEngine       — final safety gate
"""
from src.decision_trust.validation_engine import ValidationResult, validate_actions
from src.decision_trust.scenario_enforcement_engine import ScenarioValidation, enforce_scenario_taxonomy
from src.decision_trust.authority_realism_engine import AuthorityProfile, refine_authority_realism
from src.decision_trust.explainability_engine import DecisionExplanation, explain_decisions
from src.decision_trust.learning_closure_engine import LearningUpdate, compute_learning_updates
from src.decision_trust.trust_override_engine import OverrideResult, apply_trust_overrides
from src.decision_trust.pipeline import run_trust_pipeline, TrustLayerResult

__all__ = [
    "ValidationResult", "validate_actions",
    "ScenarioValidation", "enforce_scenario_taxonomy",
    "AuthorityProfile", "refine_authority_realism",
    "DecisionExplanation", "explain_decisions",
    "LearningUpdate", "compute_learning_updates",
    "OverrideResult", "apply_trust_overrides",
    "run_trust_pipeline", "TrustLayerResult",
]
