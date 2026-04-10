"""
Trust Override Engine — final safety gate before decision output.

Combines all preceding engines into a single final verdict:
  - ValidationEngine   → structural pass/fail
  - TrustEngine (S70)  → trust score + trust level
  - CalibrationEngine  → calibration grade + adjustment factor
  - LearningEngine     → action adjustment recommendation
  - ScenarioEngine     → taxonomy confidence

Override rules (in priority order):
  1. REJECTED by ValidationEngine → BLOCKED
  2. BLOCK recommendation by LearningEngine → BLOCKED
  3. Category error from AuditEngine → BLOCKED
  4. Trust level LOW → HUMAN_REQUIRED
  5. Calibration grade D → HUMAN_REQUIRED
  6. Taxonomy confidence < 0.50 → HUMAN_REQUIRED
  7. Trust level MEDIUM → CONDITIONAL
  8. Cross-border coordination → CONDITIONAL (never auto-execute cross-border)
  9. Trust level HIGH + all checks pass → AUTO_EXECUTABLE

This engine is the FINAL determination. No downstream process may change it.

Consumed by: Stage 80 pipeline (last engine)
Input: all preceding engine outputs
Output: list[OverrideResult]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.decision_trust.validation_engine import ValidationResult
from src.decision_calibration.trust_engine import TrustResult
from src.decision_calibration.calibration_engine import CalibrationResult
from src.decision_trust.learning_closure_engine import LearningUpdate
from src.decision_trust.scenario_enforcement_engine import ScenarioValidation
from src.decision_calibration.authority_engine import AuthorityAssignment

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OverrideResult:
    """Final trust override determination for a decision."""
    decision_id: str
    action_id: str

    # Final status (immutable after this engine)
    final_status: str               # "BLOCKED" | "HUMAN_REQUIRED" | "CONDITIONAL" | "AUTO_EXECUTABLE"
    final_status_ar: str

    # Override reason
    override_reason_en: str
    override_reason_ar: str

    # Which rule triggered the override
    override_rule: str              # e.g., "VALIDATION_REJECTED", "LOW_TRUST", "CATEGORY_ERROR"

    # Input signals summary
    validation_status: str          # from ValidationEngine
    trust_level: str                # from TrustEngine (Stage 70)
    trust_score: float
    calibration_grade: str          # from CalibrationEngine
    learning_action: str            # from LearningClosureEngine
    taxonomy_confidence: float      # from ScenarioEnforcementEngine

    # Override chain (audit trail — which rules were evaluated)
    override_chain: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "final_status": self.final_status,
            "final_status_ar": self.final_status_ar,
            "override_reason_en": self.override_reason_en,
            "override_reason_ar": self.override_reason_ar,
            "override_rule": self.override_rule,
            "validation_status": self.validation_status,
            "trust_level": self.trust_level,
            "trust_score": round(self.trust_score, 4),
            "calibration_grade": self.calibration_grade,
            "learning_action": self.learning_action,
            "taxonomy_confidence": round(self.taxonomy_confidence, 4),
            "override_chain": self.override_chain,
        }


def apply_trust_overrides(
    decisions: list[FormattedExecutiveDecision],
    validation_results: list[ValidationResult],
    trust_results: list[TrustResult],
    calibration_results: list[CalibrationResult],
    learning_updates: list[LearningUpdate],
    scenario_validation: ScenarioValidation,
    authority_assignments: list[AuthorityAssignment],
) -> list[OverrideResult]:
    """
    Apply final trust overrides — the last safety gate.

    Args:
        decisions:              FormattedExecutiveDecision list from Stage 60.
        validation_results:     ValidationResult list from ValidationEngine.
        trust_results:          TrustResult list from Stage 70 TrustEngine.
        calibration_results:    CalibrationResult list from Stage 70 CalibrationEngine.
        learning_updates:       LearningUpdate list from LearningClosureEngine.
        scenario_validation:    ScenarioValidation from ScenarioEnforcementEngine.
        authority_assignments:  AuthorityAssignment list from Stage 70 AuthorityEngine.

    Returns:
        list[OverrideResult] — final, immutable status for each decision.
    """
    val_map = {v.action_id: v for v in validation_results}
    trust_map = {t.action_id: t for t in trust_results}
    cal_map = {c.action_id: c for c in calibration_results}
    learn_map = {l.action_id: l for l in learning_updates}
    auth_map = {a.action_id: a for a in authority_assignments}

    taxonomy_confidence = scenario_validation.classification_confidence

    results: list[OverrideResult] = []

    for dec in decisions:
        val = val_map.get(dec.action_id)
        trust = trust_map.get(dec.action_id)
        cal = cal_map.get(dec.action_id)
        learn = learn_map.get(dec.action_id)
        auth = auth_map.get(dec.action_id)

        # Extract signals
        v_status = val.validation_status if val else "VALID"
        t_level = trust.trust_level if trust else "MEDIUM"
        t_score = trust.trust_score if trust else 0.50
        c_grade = cal.calibration_grade if cal else "C"
        l_action = learn.action_adjustment if learn else "MAINTAIN"
        cross_border = auth.requires_cross_border_coordination if auth else False

        # ── Evaluate override rules in priority order ────────────────────
        chain: list[dict[str, str]] = []
        final_status = ""
        final_ar = ""
        reason_en = ""
        reason_ar = ""
        rule = ""

        # Rule 1: REJECTED by ValidationEngine
        chain.append(_eval_rule("VALIDATION_CHECK", v_status != "REJECTED",
                                "Validation passed", "Validation rejected"))
        if v_status == "REJECTED":
            final_status, final_ar = "BLOCKED", "محظور"
            reason_en = f"Action rejected by validation: {_first_rejection_reason(val)}"
            reason_ar = f"الإجراء مرفوض من التحقق: {_first_rejection_reason_ar(val)}"
            rule = "VALIDATION_REJECTED"

        # Rule 2: BLOCK from LearningEngine
        if not final_status:
            chain.append(_eval_rule("LEARNING_CHECK", l_action != "BLOCK",
                                    "Learning OK", "Learning recommends BLOCK"))
            if l_action == "BLOCK":
                final_status, final_ar = "BLOCKED", "محظور"
                reason_en = "Action blocked by learning closure — persistent category error"
                reason_ar = "الإجراء محظور من محرك التعلم — خطأ تصنيف مستمر"
                rule = "LEARNING_BLOCK"

        # Rule 3: Category error
        if not final_status:
            cat_err = val.category_error_flag if val else False
            chain.append(_eval_rule("CATEGORY_CHECK", not cat_err,
                                    "No category error", "Category error detected"))
            if cat_err:
                final_status, final_ar = "BLOCKED", "محظور"
                reason_en = "Action does not match scenario type — category error"
                reason_ar = "الإجراء لا يتطابق مع نوع السيناريو — خطأ تصنيف"
                rule = "CATEGORY_ERROR"

        # Rule 4: LOW trust
        if not final_status:
            chain.append(_eval_rule("TRUST_LEVEL_CHECK", t_level != "LOW",
                                    f"Trust level: {t_level}", "Trust level LOW"))
            if t_level == "LOW":
                final_status, final_ar = "HUMAN_REQUIRED", "يتطلب تدخل بشري"
                reason_en = f"Low trust score ({t_score:.2f}) — human validation required"
                reason_ar = f"نتيجة ثقة منخفضة ({t_score:.2f}) — يتطلب التحقق البشري"
                rule = "LOW_TRUST"

        # Rule 5: Calibration grade D
        if not final_status:
            chain.append(_eval_rule("CALIBRATION_CHECK", c_grade != "D",
                                    f"Calibration grade: {c_grade}", "Calibration grade D"))
            if c_grade == "D":
                final_status, final_ar = "HUMAN_REQUIRED", "يتطلب تدخل بشري"
                reason_en = f"Poor calibration (grade D) — human review required"
                reason_ar = f"معايرة ضعيفة (درجة D) — مراجعة بشرية مطلوبة"
                rule = "CALIBRATION_GRADE_D"

        # Rule 6: Taxonomy confidence < 0.50
        if not final_status:
            chain.append(_eval_rule("TAXONOMY_CHECK", taxonomy_confidence >= 0.50,
                                    f"Taxonomy confidence: {taxonomy_confidence:.2f}",
                                    f"Low taxonomy confidence: {taxonomy_confidence:.2f}"))
            if taxonomy_confidence < 0.50:
                final_status, final_ar = "HUMAN_REQUIRED", "يتطلب تدخل بشري"
                reason_en = f"Scenario type uncertain (confidence: {taxonomy_confidence:.0%}) — human classification required"
                reason_ar = f"نوع السيناريو غير مؤكد (ثقة: {taxonomy_confidence:.0%}) — تصنيف بشري مطلوب"
                rule = "LOW_TAXONOMY_CONFIDENCE"

        # Rule 7: MEDIUM trust
        if not final_status:
            chain.append(_eval_rule("TRUST_MEDIUM_CHECK", t_level != "MEDIUM",
                                    "Trust above MEDIUM", f"Trust level: {t_level}"))
            if t_level == "MEDIUM":
                final_status, final_ar = "CONDITIONAL", "مشروط"
                reason_en = f"Moderate trust ({t_score:.2f}) — conditional execution with monitoring"
                reason_ar = f"ثقة متوسطة ({t_score:.2f}) — تنفيذ مشروط مع مراقبة"
                rule = "MEDIUM_TRUST"

        # Rule 8: Cross-border coordination
        if not final_status:
            chain.append(_eval_rule("CROSS_BORDER_CHECK", not cross_border,
                                    "No cross-border", "Cross-border coordination required"))
            if cross_border:
                final_status, final_ar = "CONDITIONAL", "مشروط"
                reason_en = "Cross-border GCC coordination required — conditional execution"
                reason_ar = "يتطلب تنسيقاً عابراً للحدود — تنفيذ مشروط"
                rule = "CROSS_BORDER"

        # Rule 9: All pass → AUTO_EXECUTABLE
        if not final_status:
            chain.append(_eval_rule("ALL_PASS", True, "All checks passed", ""))
            final_status, final_ar = "AUTO_EXECUTABLE", "قابل للتنفيذ التلقائي"
            reason_en = f"High trust ({t_score:.2f}), grade {c_grade}, all validations passed"
            reason_ar = f"ثقة عالية ({t_score:.2f})، درجة {c_grade}، جميع التحققات ناجحة"
            rule = "ALL_PASS"

        results.append(OverrideResult(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            final_status=final_status,
            final_status_ar=final_ar,
            override_reason_en=reason_en,
            override_reason_ar=reason_ar,
            override_rule=rule,
            validation_status=v_status,
            trust_level=t_level,
            trust_score=t_score,
            calibration_grade=c_grade,
            learning_action=l_action,
            taxonomy_confidence=taxonomy_confidence,
            override_chain=chain,
        ))

    blocked = sum(1 for r in results if r.final_status == "BLOCKED")
    human = sum(1 for r in results if r.final_status == "HUMAN_REQUIRED")
    conditional = sum(1 for r in results if r.final_status == "CONDITIONAL")
    auto = sum(1 for r in results if r.final_status == "AUTO_EXECUTABLE")
    logger.info(
        "[TrustOverrideEngine] Final verdicts: %d BLOCKED, %d HUMAN_REQUIRED, %d CONDITIONAL, %d AUTO_EXECUTABLE",
        blocked, human, conditional, auto,
    )
    return results


# ── Helpers ───────────────────────────────────────────────────────────────

def _eval_rule(name: str, passed: bool, pass_msg: str, fail_msg: str) -> dict[str, str]:
    """Create override chain entry for audit trail."""
    return {
        "rule": name,
        "result": "PASS" if passed else "FAIL",
        "detail": pass_msg if passed else fail_msg,
    }


def _first_rejection_reason(val: ValidationResult | None) -> str:
    """Extract first rejection reason from validation result."""
    if not val or not val.rejection_reasons:
        return "unknown"
    return val.rejection_reasons[0].get("reason_en", "unknown")


def _first_rejection_reason_ar(val: ValidationResult | None) -> str:
    """Extract first rejection reason (Arabic)."""
    if not val or not val.rejection_reasons:
        return "غير معروف"
    return val.rejection_reasons[0].get("reason_ar", "غير معروف")
