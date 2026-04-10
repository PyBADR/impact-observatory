# Decision Trust Layer — Architecture Document

**Version**: 1.0.0
**Stage**: 80 (Pipeline Integration)
**Date**: 2026-04-10
**Status**: Deployed — 44/44 tests passing, 285/285 total suite passing

---

## 1. Trust Layer Architecture

The Decision Trust Layer (Stage 80) transforms high-quality, calibrated decisions from Stages 60+70 into institutionally reliable, verifiable, and explainable decisions. It addresses 6 critical risks that remain after calibration: category errors, generic authority mapping, weak explainability, partial learning loops, imperfect trust inputs, and unclassified scenario types.

**Transformation:**

Stage 70 output: `audited + ranked + authority-assigned + calibrated + trust-scored`

Stage 80 output: `validated + taxonomy-enforced + authority-refined + explained + learning-closed + override-gated`

**Layer Position in the Intelligence Stack:**

Data (1-17) → Features (18-25) → Models (26-35) → Agents (36-41) → Impact Intelligence (42) → Decision Intelligence (50) → Decision Quality (60) → Decision Calibration (70) → **Decision Trust (80)** → API Response

**6-Engine Pipeline:**

ScenarioEnforcement (FIRST) → ActionValidation → AuthorityRealism → Explainability → LearningClosure → TrustOverride (LAST)

The ScenarioEnforcementEngine runs first because all other engines depend on a resolved scenario type. The TrustOverrideEngine runs last because it is the final safety gate — no downstream process may change its verdict. Every engine is pure-functional, stateless, deterministic, and bilingual (EN/AR). The entire pipeline completes in <1ms.

---

## 2. Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/src/decision_trust/__init__.py` | 32 | Package exports — all 6 engine types + pipeline entry |
| `backend/src/decision_trust/validation_engine.py` | ~210 | Structural action validation — scenario, sector, node coverage, feasibility |
| `backend/src/decision_trust/scenario_enforcement_engine.py` | ~230 | Strict taxonomy enforcement — 5-level resolution with fallback |
| `backend/src/decision_trust/authority_realism_engine.py` | ~310 | Country-level GCC authority — named institutions per country × sector |
| `backend/src/decision_trust/explainability_engine.py` | ~300 | Causal explanation — trigger, propagation, regime, ranking, narrative |
| `backend/src/decision_trust/learning_closure_engine.py` | ~220 | Feedback loop — action/ranking/confidence adjustments + learning velocity |
| `backend/src/decision_trust/trust_override_engine.py` | ~240 | Final safety gate — 9-rule priority chain with audit trail |
| `backend/src/decision_trust/pipeline.py` | ~140 | Pipeline orchestrator — chains all 6 engines with timing |
| `backend/tests/test_decision_trust.py` | ~440 | 44 contract tests across all engines + cross-scenario |

**Files Modified:**

| File | Change |
|------|--------|
| `backend/src/services/run_orchestrator.py` | Added Stage 80 block, imports, trust_result to response dict, pipeline_stages 70→80 |

---

## 3. Core Classes

### ValidationResult (validation_engine.py)
Frozen dataclass. Validates each action against 4 structural dimensions: `scenario_valid` (action's allowed_scenario_types includes current type), `sector_valid` (action sector in valid sectors for scenario type), `node_coverage_valid` (action's sector has stressed nodes in impact map), `operational_feasibility` (feasibility ≥ 0.30, time_to_act ≤ 168h). Final verdict: VALID (all pass), CONDITIONALLY_VALID (partial), REJECTED (category error or infeasible). Category errors detected when scenario_type is known but not in action's allowed types. Each result includes `rejection_reasons` with bilingual codes, messages, and severity levels, plus `coverage_ratio` tracking what fraction of stressed nodes the action covers.

### ScenarioValidation (scenario_enforcement_engine.py)
Frozen dataclass. Resolves scenario type via 5-level fallback: (1) Direct SCENARIO_TAXONOMY lookup → confidence 1.0, (2) Explicit fallback map for 6 known unmapped scenarios → 0.85, (3) Keyword inference from scenario_id → 0.65, (4) Sector-majority from SCENARIO_CATALOG sectors_affected → 0.45, (5) Default REGULATORY → 0.20. `taxonomy_valid` is true only for level 1. `fallback_method` records which resolution was used. The 6 explicitly mapped fallbacks: gcc_power_grid_failure→CYBER, difc_financial_contagion→LIQUIDITY, gcc_insurance_reserve_shortfall→LIQUIDITY, gcc_fintech_payment_outage→CYBER, saudi_vision_mega_project_halt→ENERGY, gcc_sovereign_debt_crisis→LIQUIDITY.

### AuthorityProfile (authority_realism_engine.py)
Frozen dataclass. Country-level authority refinement. Maps 21 scenarios to primary countries (UAE, SAUDI, QATAR, BAHRAIN, KUWAIT, OMAN). Each country has 8 named institutions (central_bank, energy_ministry, port_authority, cyber_authority, financial_regulator, insurance_regulator, supreme_council, fintech_regulator) with full EN/AR names. `primary_owner` from sector → institution key. `regulator` from scenario_type → regulatory key. `escalation_chain` is a 4-level list: operational → regulatory → ministerial/governor → supreme council. `cross_border_entities` populated from scenario_type when Stage 70 detected cross-border needs, including international bodies (IMO, OPEC, BIS, IMF, FIRST).

### DecisionExplanation (explainability_engine.py)
Frozen dataclass. Complete causal explanation with 7 dimensions: `trigger_reason` (node breach/high stress/severity → decision type context), `causal_path` (list of CausalSteps: scenario onset → propagation events → sector accumulation → decision trigger), `propagation_summary` (stressed/breached node counts, sector-specific), `regime_context` (regime state + amplifier value), `ranking_reason` (top 3 factors with weighted scores, rank delta), `rejection_reason` (if REJECTED), `narrative` (human-readable paragraph combining all dimensions). Every field bilingual. Causal path references actual propagation events from ImpactMapResponse.

### LearningUpdate (learning_closure_engine.py)
Frozen dataclass. Feedback signals for system adaptation. `action_adjustment`: MAINTAIN (normal), UPGRADE (low error ≤ 0.15), DOWNGRADE (high error ≥ 0.40), BLOCK (category error). `ranking_adjustment` ([-0.20, +0.20]): reduces for instability (rank delta ≥ 2) and high error. `confidence_adjustment` ([-0.30, +0.10]): -0.50 for category error, -0.15 for high error, +0.05 for low error, -0.05 for high model dependency. `learning_velocity`: FAST (category error or high error), MODERATE (moderate error + instability), SLOW (well-calibrated).

### OverrideResult (trust_override_engine.py)
Frozen dataclass. Final immutable determination. 9-rule priority chain: (1) REJECTED→BLOCKED, (2) BLOCK learning→BLOCKED, (3) category error→BLOCKED, (4) LOW trust→HUMAN_REQUIRED, (5) calibration grade D→HUMAN_REQUIRED, (6) taxonomy confidence <0.50→HUMAN_REQUIRED, (7) MEDIUM trust→CONDITIONAL, (8) cross-border→CONDITIONAL, (9) all pass→AUTO_EXECUTABLE. `override_chain` stores every rule evaluation (PASS/FAIL + detail) for audit trail. Includes input signals summary: validation_status, trust_level, trust_score, calibration_grade, learning_action, taxonomy_confidence.

### TrustLayerResult (pipeline.py)
Mutable dataclass aggregating all 6 engine outputs plus per-engine timing and comprehensive counts: validated, valid, conditionally_valid, rejected, authorities_refined, explanations_generated, learning_updates, blocked, human_required, conditional, auto_executable, taxonomy_valid, taxonomy_confidence.

---

## 4. Function Signatures

```python
# Scenario Enforcement Engine
def enforce_scenario_taxonomy(
    scenario_id: str,
    scenario_catalog_entry: dict[str, Any] | None = None,
) -> ScenarioValidation

# Action Validation Engine
def validate_actions(
    decisions: list[FormattedExecutiveDecision],
    impact_map: ImpactMapResponse,
    scenario_id: str,
    action_registry_lookup: dict[str, dict[str, Any]],
) -> list[ValidationResult]

# Authority Realism Engine
def refine_authority_realism(
    decisions: list[FormattedExecutiveDecision],
    authority_assignments: list[AuthorityAssignment],
    scenario_id: str,
    scenario_type: str,
) -> list[AuthorityProfile]

# Explainability Engine
def explain_decisions(
    decisions: list[FormattedExecutiveDecision],
    impact_map: ImpactMapResponse,
    validation_results: list[ValidationResult],
    ranked_decisions: list[RankedDecision],
    scenario_validation: ScenarioValidation,
) -> list[DecisionExplanation]

# Learning Closure Engine
def compute_learning_updates(
    decisions: list[FormattedExecutiveDecision],
    calibration_results: list[CalibrationResult],
    audit_results: list[ActionAuditResult],
    ranked_decisions: list[RankedDecision],
) -> list[LearningUpdate]

# Trust Override Engine
def apply_trust_overrides(
    decisions: list[FormattedExecutiveDecision],
    validation_results: list[ValidationResult],
    trust_results: list[TrustResult],
    calibration_results: list[CalibrationResult],
    learning_updates: list[LearningUpdate],
    scenario_validation: ScenarioValidation,
    authority_assignments: list[AuthorityAssignment],
) -> list[OverrideResult]

# Pipeline Entry Point
def run_trust_pipeline(
    dq_result: DecisionQualityResult,
    cal_result: CalibrationLayerResult,
    impact_map: ImpactMapResponse,
    scenario_id: str,
    action_registry_lookup: dict[str, dict[str, Any]],
    scenario_catalog_entry: dict[str, Any] | None = None,
) -> TrustLayerResult
```

---

## 5. Validation Rules

### ActionValidationEngine — 4 Structural Checks

| Check | Pass Condition | Fail Action |
|---|---|---|
| scenario_valid | action's allowed_scenario_types includes resolved scenario_type | category_error_flag = true → REJECTED |
| sector_valid | action sector ∈ SCENARIO_VALID_SECTORS[scenario_type] | CONDITIONALLY_VALID |
| node_coverage_valid | at least 1 stressed node (>0.10) in action's sector | CONDITIONALLY_VALID |
| operational_feasibility | feasibility ≥ 0.30 AND time_to_act ≤ 168h | REJECTED |

**Verdict logic:**
- category_error → REJECTED
- !operational_feasibility → REJECTED
- all 4 pass → VALID
- partial pass → CONDITIONALLY_VALID

### ScenarioEnforcementEngine — 5-Level Resolution

| Level | Method | Confidence | Example |
|---|---|---|---|
| 1 | SCENARIO_TAXONOMY direct lookup | 1.00 | hormuz_chokepoint_disruption → MARITIME |
| 2 | EXPLICIT_FALLBACKS map | 0.85 | gcc_power_grid_failure → CYBER |
| 3 | Keyword inference from ID | 0.65 | *_banking_* → LIQUIDITY |
| 4 | Sector-majority from catalog | 0.45 | sectors=[banking,fintech] → LIQUIDITY |
| 5 | Default fallback | 0.20 | unknown → REGULATORY |

---

## 6. Explainability Logic

Every decision gets a `DecisionExplanation` with 7 dimensions:

1. **trigger_reason** — What triggered this decision? Constructed from: breached nodes (if any) → stressed nodes (if any) → scenario severity. Includes decision_type classification context (emergency/operational/strategic) and loss at risk.

2. **causal_path** — Ordered list of `CausalStep` objects tracing the shock from scenario onset through propagation events to sector accumulation to decision trigger. Each step includes mechanism type and severity contribution. Uses actual `PropagationEvent` objects from ImpactMapResponse.

3. **propagation_summary** — Quantified summary: X/Y nodes stressed, Z breached, N sector nodes affected. Includes regime amplifier value.

4. **regime_context** — Current regime state (STABLE/VOLATILE/CRISIS/RECOVERY) with propagation amplifier. Human-readable description of how regime modifies propagation dynamics.

5. **ranking_reason** — Top 3 ranking factors with weighted scores. Rank position and delta from Stage 60.

6. **rejection_reason** — If REJECTED by ValidationEngine, the specific rejection codes and reasons.

7. **narrative** — Human-readable paragraph combining all dimensions into a coherent explanation. Bilingual. Includes fallback warnings if taxonomy was resolved via inference.

---

## 7. Learning Update Logic

```
For each decision:

  calibration_error = expected_calibration_error (from Stage 70 CalibrationEngine)

  ACTION ADJUSTMENT:
    category_error           → BLOCK (never use this action for this scenario type)
    cal_error ≥ 0.40        → DOWNGRADE (reduce future confidence)
    cal_error ≤ 0.15        → UPGRADE (increase future confidence)
    else                    → MAINTAIN

  RANKING ADJUSTMENT: [-0.20, +0.20]
    rank_delta ≥ 2          → -0.05 (stabilize volatile ranking)
    cal_error ≥ 0.40        → -0.10
    cal_error ≤ 0.15        → +0.05

  CONFIDENCE ADJUSTMENT: [-0.30, +0.10]
    category_error           → -0.50 (hard penalty)
    cal_error ≥ 0.40        → -0.15
    cal_error ≤ 0.15        → +0.05
    model_dependency = high  → -0.05

  LEARNING VELOCITY:
    category_error OR cal_error ≥ 0.40  → FAST (immediate system adaptation)
    cal_error ≥ 0.15 + rank instability → MODERATE
    else                                → SLOW (system is well-calibrated)
```

---

## 8. Override Logic

9-rule priority chain evaluated in order. First matching rule determines `final_status`:

```
Rule 1: VALIDATION_REJECTED      → BLOCKED
         (action structurally invalid for scenario)

Rule 2: LEARNING_BLOCK           → BLOCKED
         (learning engine recommends blocking — persistent category error)

Rule 3: CATEGORY_ERROR           → BLOCKED
         (action's allowed_scenario_types doesn't include current type)

Rule 4: LOW_TRUST                → HUMAN_REQUIRED
         (trust_level = LOW, trust_score < 0.40)

Rule 5: CALIBRATION_GRADE_D      → HUMAN_REQUIRED
         (calibration grade D — prediction quality too low)

Rule 6: LOW_TAXONOMY_CONFIDENCE  → HUMAN_REQUIRED
         (scenario_type resolved via inference with confidence < 0.50)

Rule 7: MEDIUM_TRUST             → CONDITIONAL
         (trust_level = MEDIUM, 0.40 ≤ trust_score < 0.70)

Rule 8: CROSS_BORDER             → CONDITIONAL
         (cross-border GCC coordination required — never auto-execute)

Rule 9: ALL_PASS                 → AUTO_EXECUTABLE
         (high trust, all validations passed, well-calibrated)
```

Every rule evaluation is recorded in `override_chain` as PASS/FAIL + detail for complete audit trail. The chain is immutable — no downstream process may alter the verdict.

---

## 9. Execution Flow

```
run_orchestrator.py (Stage 80)
│
└─ run_trust_pipeline(dq_result, cal_result, impact_map, scenario_id, registry, catalog)
   │
   ├─ Step 1: enforce_scenario_taxonomy(scenario_id, catalog_entry)
   │   └─ 5-level resolution: taxonomy → explicit → keyword → sector → default
   │   └─ Returns resolved scenario_type + confidence + fallback_method
   │   → ScenarioValidation (used by ALL subsequent engines)
   │
   ├─ Step 2: validate_actions(decisions, impact_map, scenario_id, registry)
   │   └─ 4 structural checks per decision: scenario, sector, nodes, feasibility
   │   └─ Returns VALID / CONDITIONALLY_VALID / REJECTED per decision
   │   → list[ValidationResult]
   │
   ├─ Step 3: refine_authority_realism(decisions, auth_assignments, scenario_id, type)
   │   └─ Resolve country from scenario_id → country registry
   │   └─ Map sector → named institution, type → named regulator
   │   └─ Build 4-level escalation chain + cross-border entities
   │   → list[AuthorityProfile]
   │
   ├─ Step 4: explain_decisions(decisions, impact_map, validations, rankings, sv)
   │   └─ Build trigger_reason from breached/stressed nodes
   │   └─ Build causal_path from propagation events
   │   └─ Add regime context, ranking reason, rejection reason
   │   └─ Compose narrative paragraph (bilingual)
   │   → list[DecisionExplanation]
   │
   ├─ Step 5: compute_learning_updates(decisions, calibrations, audits, rankings)
   │   └─ Compute action_adjustment: MAINTAIN/UPGRADE/DOWNGRADE/BLOCK
   │   └─ Compute ranking_adjustment [-0.20, +0.20]
   │   └─ Compute confidence_adjustment [-0.30, +0.10]
   │   └─ Classify learning_velocity: FAST/MODERATE/SLOW
   │   → list[LearningUpdate]
   │
   └─ Step 6: apply_trust_overrides(decisions, validations, trusts, calibrations,
   │                                  learning_updates, sv, authorities)
       └─ Evaluate 9-rule priority chain per decision
       └─ Record every rule evaluation in override_chain
       └─ Return final immutable status: BLOCKED/HUMAN_REQUIRED/CONDITIONAL/AUTO_EXECUTABLE
       → list[OverrideResult]
```

---

## 10. Test Strategy

44 tests across 8 test classes, all deterministic, no mocking, no external dependencies.

**TestScenarioEnforcementEngine (6 tests):** known_scenario (MARITIME, confidence 1.0, taxonomy_valid), unknown_scenario (fallback, <1.0), completely_unknown (defaults, non-empty), type_never_empty (all catalog + fake), all_catalog_resolved (20 scenarios), to_dict_keys.

**TestValidationEngine (5 tests):** returns_list, status_enum (VALID/CONDITIONALLY_VALID/REJECTED), scenario_valid_for_maritime, coverage_ratio_bounded [0-1], rejection_has_reasons.

**TestAuthorityRealismEngine (5 tests):** returns_list, country_is_uae_for_hormuz, named_institutions (checks for CBUAE/SAMA/ADNOC/Port/etc.), escalation_chain_4_levels, bilingual_authorities.

**TestExplainabilityEngine (5 tests):** returns_list, trigger_reason (EN+AR), causal_path (≥2 steps), narrative_non_empty (EN+AR), regime_context ("amplifier" present).

**TestLearningClosureEngine (5 tests):** returns_list, action_adjustment_enum (MAINTAIN/UPGRADE/DOWNGRADE/BLOCK), velocity_enum (FAST/MODERATE/SLOW), adjustments_bounded (ranking [-0.20,0.20], confidence [-0.30,0.10]), error_bounded [0-1].

**TestTrustOverrideEngine (5 tests):** returns_list, final_status_enum (4 statuses), override_chain_present (≥1 entry), bilingual_reasons, override_rule_present.

**TestPipeline (7 tests):** returns_result, has_all_outputs (non-empty), stage_timings (6 stages), to_dict_serializable (JSON), to_dict_counts, performance (<50ms), empty_dq_result.

**TestCrossScenarioCoverage (6 tests):** All 20 scenarios: results produced, scenario_validation present + non-empty type, override_results present, statuses valid, under 50ms, JSON-serializable.

---

## 11. Failure Modes

| Failure Mode | Probability | Detection | Mitigation |
|---|---|---|---|
| No decisions from Stage 60 | Medium | dq_result.executive_decisions empty | Pipeline returns empty TrustLayerResult |
| Scenario not in SCENARIO_TAXONOMY | Medium (6 of 20) | ScenarioEnforcementEngine fallback_applied=true | 5-level resolution: explicit map (0.85) → keyword (0.65) → sector (0.45) → default (0.20) |
| Completely unknown scenario | Very Low | fallback_method="default", confidence=0.20 | Default to REGULATORY + HUMAN_REQUIRED via Rule 6 |
| All actions rejected (wrong scenario type) | Low | All validation_status=REJECTED | All decisions BLOCKED — correct behavior, human must intervene |
| Stage 70 CalibrationLayerResult empty | Low | cal_result with empty lists | Engines use safe defaults (trust 0.50, grade C, etc.) |
| Impact map has zero stressed nodes | Very Low | stressed_sectors empty, coverage_ratio=0 | node_coverage_valid=false → CONDITIONALLY_VALID |
| Authority mapping for unknown country | Very Low | Country not in _SCENARIO_COUNTRY | Falls back to UAE institutions |
| Propagation events empty in impact map | Low | causal_path has only onset + sector + trigger steps | Explanation still valid, just shorter causal chain |
| Override chain produces conflicting signals | None | Priority order is deterministic | First matching rule wins, all evaluations recorded |
| Trust pipeline exception in any engine | Low | try/except in orchestrator | Stage 80 returns empty TrustLayerResult |

---

## 12. Decision Gate — What Must Be True Before Next Phase

Before building the next layer (frontend consumption, persistent audit trail, or IFRS 17 compliance tagging):

1. **All 285 tests pass** — 113 pipeline + 42 DI + 46 DQ + 40 calibration + 44 trust. **Verified.**

2. **Cross-scenario coverage** — All 20 scenarios produce valid TrustLayerResult with: scenario_validation resolved (never empty), validation_results, authority_profiles, explanations, learning_updates, override_results. **Verified.**

3. **Stage 80 integrated** — Pipeline stages updated from 70 to 80. `decision_trust` key present in API response. **Verified.**

4. **Scenario taxonomy enforced** — All 20 SCENARIO_CATALOG entries resolved to a non-empty type. 15 via taxonomy (1.0), 5 via explicit fallback (0.85), 0 via keyword/default. **Verified.**

5. **Override chain deterministic** — 9-rule priority chain produces consistent results. Every evaluation recorded in audit trail. First matching rule wins. **Verified.**

6. **Authority realism country-specific** — All 6 GCC countries mapped with 8 named institutions each. Hormuz→UAE, Saudi Oil→SAUDI, Qatar LNG→QATAR, etc. **Verified.**

7. **Every decision explainable** — Every decision has non-empty trigger_reason, causal_path (≥2 steps), regime_context, narrative. All bilingual. **Verified.**

8. **Performance budget** — Full Stage 80 pipeline under 50ms. Measured at <1ms across all scenarios. **Verified.**

**Next phases (not started):**

- Frontend TypeScript types for TrustLayerResult
- API endpoint `/api/v1/runs/{run_id}/trust` exposing override verdicts
- SHA-256 audit trail for override_chain persistence
- IFRS 17 compliance tagging on loss calibration baselines
- Post-execution outcome tracking → LearningClosureEngine feedback loop activation
- Decision event store for cross-run learning history
- PDPL (Saudi) / DPL (UAE) data sovereignty compliance checks on authority_profiles
