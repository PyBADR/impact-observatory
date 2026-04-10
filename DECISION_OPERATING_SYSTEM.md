# Decision Operating System — Architecture Brief
## Impact Observatory | مرصد الأثر

**Version:** 1.0.0
**Date:** 2026-04-10
**Architect:** Decision Intelligence Engineering Team
**Status:** Sprint 1 Implementation In Progress

---

## 1. Product Diagnosis

The Impact Observatory has achieved something non-trivial: a deterministic 41-stage pipeline that transforms a scenario ID and severity into a ranked action plan, propagation chain, and multi-sector stress assessment across 43 GCC infrastructure nodes. The propagation chain is the platform's strongest output. The authority console lifecycle (PENDING_OBSERVATION → approval → outcome) is structurally correct. The Intelligence Brief's five-questions framework is the right signal-to-impact layer.

But the platform is not yet a decision system. It is an analytical engine with a decision-shaped output layer bolted on top. The distinction matters: a decision system's outputs must be **trustworthy enough that an executive acts on them without second-guessing the model.** Three product failures block that threshold:

**PF-1: Action-Scenario Misalignment Is a Category Error.**
The SCENARIO_ACTION_MATRIX maps 16 action indices to scenario types, but _ACTION_TEMPLATES only has 15 entries (indices 0–14). Index 15 maps to `{CYBER}` but references a non-existent template. Worse, the index alignment between the matrix and the templates is broken at the semantic level: a CYBER scenario receives action index 4, which is "Declare force majeure on Hormuz-dependent contracts" — a pure maritime/energy action. A MARITIME scenario receives index 11, which is "Raise national cyber threat level to orange" — a cyber defense action. This is not a calibration problem. It is a structural mapping error where the action matrix indices were written assuming a different template order than what exists.

**PF-2: Propagation Is the Best Output but Buried in the Response.**
The propagation chain explains *how* shock spreads through the GCC financial system — the single most valuable insight for an executive. But in the API response, it lives at `response.propagation` as a flat array, while `response.headline` (the executive-facing block) contains only aggregate numbers (total_loss_usd, affected_entities, peak_day). The headline never surfaces the propagation narrative. An executive sees "$3.2B loss across 12 entities" but never sees "Hormuz blockade → shipping lane closure → Dubai Port congestion → banking liquidity freeze within 72 hours." The causal story — which is what drives decisions — is missing from the executive surface.

**PF-3: Regime Layer Is an Annotation, Not a Controller.**
The regime layer classifies system state (STABLE → CRISIS_ESCALATION) and produces graph modifiers and decision triggers. But the classification happens *after* the simulation engine runs, meaning the simulation itself is regime-unaware. The propagation formula uses static `0.85^hop` decay regardless of whether the system is in STABLE or CRISIS_ESCALATION. The regime layer annotates the output; it does not shape the computation. This is architecturally backwards. The target flow is: regime → simulation conditions → propagation → decisions. The current flow is: simulation → regime annotation → decisions.

---

## 2. System Diagnosis

**SD-1: SCENARIO_ACTION_MATRIX Index Misalignment (CRITICAL)**
The 16-entry action matrix (indices 0–15) was built against a template list that has since been rewritten to 15 entries (indices 0–14). The mapping semantics are wrong: matrix index 0 maps to "Activate emergency liquidity facility" (a banking/liquidity action), but the current template at index 0 is the same, so *some* mappings are coincidentally correct. However, index 4 in the matrix maps to `{CYBER, LIQUIDITY}` (intended: "Payment system contingency"), but template index 4 is "Declare force majeure on Hormuz-dependent contracts" (an energy action). This creates silent category errors that no test catches because the policy layer allows unknown actions through with warnings rather than rejecting them.

**SD-2: Validation Runs After ROI Computation**
In `run_orchestrator.py`, `validate_metrics()` runs at line 772 — after all 41 stages have completed, including ROI, portfolio value, effectiveness calculations, and pilot reports. If a value is invalid (e.g., loss_avoided_usd = $500 trillion from a computation error), the entire decision trust, evidence, and ROI chain has already consumed it. The validation firewall must run *before* downstream consumers, not after.

**SD-3: ROI Event Store Is Not Run-Scoped**
`compute_roi_from_events()` in `event_store.py` filters by `run_id`, which is correct. But the `EventStore` singleton persists across requests in the same process. If two concurrent runs complete before either's ROI is computed, the event store contains interleaved events. The `get_by_run()` filter handles this, but there is no TTL or eviction — memory grows unbounded in long-running deployments.

**SD-4: Sanity Guard Silently Mutates Without Logging**
`sanitize_run_result()` clamps values in-place (e.g., capping loss at $500B, replacing NaN with 0) but does not log *which* values were clamped or *what* the original values were. When a dashboard shows $500B loss, there is no way to distinguish "the model computed exactly $500B" from "the model computed $2 trillion and sanity_guard silently capped it." This is an audit trail gap.

**SD-5: Propagation Headline Not in Executive Block**
`response.headline` contains `total_loss_usd`, `affected_entities`, `peak_day`, `propagation_depth`, `total_nodes_impacted` — all numeric aggregates. The propagation narrative (from `explainability.narrative_en`) lives in a separate block. The five_questions framework in the decision layer generates a rich narrative, but it's nested inside `decision_plan.five_questions.what_happened` — three levels deep from the top-level response. No executive will find it there.

**SD-6: Regime Layer Runs Post-Simulation**
Stages 17b/c/d run after the simulation engine output. The regime classification is accurate (the signals come from the simulation result), but it cannot influence the simulation itself. The propagation amplifier (e.g., 2.0× for CRISIS_ESCALATION) is only applied to the map_payload stress values — not to the actual propagation chain computation inside the simulation engine. This means the graph_payload and map_payload show regime-adjusted stress, but the propagation_chain itself was computed without regime awareness.

---

## 3. Strategic Architecture

The target architecture has four layers, each with a clear input-output contract:

```
┌─────────────────────────────────────────────────────┐
│ Layer 4: OUTCOME TRUTH                              │
│ Event Store → ROI → Institutional Memory            │
├─────────────────────────────────────────────────────┤
│ Layer 3: DECISION TRIGGERS                          │
│ Regime + Propagation + Breach → Decision Classes    │
├─────────────────────────────────────────────────────┤
│ Layer 2: IMPACT INTELLIGENCE                        │
│ Graph Core → Propagation Engine → Causal Surface    │
├─────────────────────────────────────────────────────┤
│ Layer 1: REGIME-CONTROLLED FLOW                     │
│ Signals → Regime → Simulation Conditions → Output   │
└─────────────────────────────────────────────────────┘
```

**Layer 1 (Regime-Controlled Flow)** classifies system state and produces propagation parameters *before* the simulation runs. The simulation engine reads regime-conditioned parameters (amplifier, delay compression, failure threshold shift) instead of hard-coded constants.

**Layer 2 (Impact Intelligence)** uses the graph core (43 nodes, 188 edges) with regime-adjusted transfer coefficients to produce a causal propagation chain that explains *how* and *when* impact spreads. The propagation narrative becomes the executive headline.

**Layer 3 (Decision Triggers)** evaluates regime state + propagation depth + breach conditions to determine which decision classes must be activated. Each trigger maps to specific actions from a scenario-type-scoped action library.

**Layer 4 (Outcome Truth)** captures every decision event with SHA-256 hashing, computes ROI strictly within run_id scope, and provides reproducible value calculations for audit.

The critical architectural change: **the action library must be restructured from an index-based flat list to a scenario-type-keyed dictionary.** This eliminates the index alignment problem permanently.

---

## 4. What Must Be Fixed Immediately

These are blocking issues that erode institutional trust if left unfixed:

1. **Rebuild SCENARIO_ACTION_MATRIX alignment.** The current index-based mapping is fundamentally broken. Replace with a sector+scenario_type keyed action registry. Every action must declare which scenario types it serves. No action should be deliverable to a scenario type it doesn't belong to.

2. **Move validation before downstream consumers.** `validate_metrics()` must run immediately after the simulation engine output (after stage 17), before transmission engine, counterfactual, trust, and all subsequent stages. Invalid values must be caught before they propagate through 24 more pipeline stages.

3. **Surface propagation narrative in the headline block.** Add `headline.propagation_headline` — a single sentence summarizing the causal chain. This is the executive's first read.

4. **Add sanity guard mutation logging.** Every value that `sanitize_run_result()` clamps must be logged with original_value, clamped_value, and field_path. This closes the audit trail gap.

5. **Scope event store with TTL.** Add a max_events or max_age parameter to EventStore to prevent unbounded memory growth. Events older than 24h or exceeding 10,000 entries should be evicted.

---

## 5. What Must Be Preserved

These are working and correct — do not refactor:

1. **The 17-stage simulation engine.** The `SimulationEngine.run()` method is the source of truth. Do not split it, rewrite it, or add regime conditioning inside it in this phase. Regime modifiers should be applied *to the output*, not by rewriting the engine internals.

2. **PolicyContext as immutable shared state.** The frozen dataclass pattern works. All policy layers read the same context. Do not add mutation.

3. **The event store append-only model.** SHA-256 hashing, frozen events, thread-safe appends — this is correct. Add eviction, not restructuring.

4. **The validation contract layer (V1–V7 rules).** The rules are sound. The issue is *when* they run, not *what* they check.

5. **The regime classification engine.** The 16-signal input, 5-regime output, and transition matrix are production-ready. The confidence calculation (band-center distance) is the right approach.

6. **The transmission chain with breakable points.** This is the strongest analytical output. Preserve the 3-phase build (entity → sector → minimum enforcement) and the breakable_point detection.

7. **PENDING_OBSERVATION as the default approved-action state.** This is structurally correct for human-in-the-loop governance.

---

## 6. Phase-by-Phase Build Strategy

### Sprint 1 — Decision Credibility Lock

**Goal:** Eliminate the action-scenario misalignment, surface propagation as headline, harden validation ordering.

**Deliverables:**

- **S1-A: Rebuild action registry as scenario-type-keyed.** Replace the index-based `SCENARIO_ACTION_MATRIX` + flat `_ACTION_TEMPLATES` with a `SCENARIO_ACTION_REGISTRY: dict[str, list[ActionTemplate]]` keyed by scenario type. Each `ActionTemplate` is a typed dict with sector, owner, action_en, action_ar, base_urgency, cost_usd, regulatory_risk, feasibility, time_to_act_hours, and `allowed_scenario_types: set[str]`. The decision layer queries `SCENARIO_ACTION_REGISTRY[scenario_type]` directly — no index mapping.

- **S1-B: Propagation headline injection.** Add `headline.propagation_headline_en` and `headline.propagation_headline_ar` to the orchestrator output, built from the first 3 hops of the propagation chain. Format: "{Origin} → {Hop1} → {Hop2}: {mechanism}, estimated {delay}h to breach."

- **S1-C: Validation firewall repositioning.** Move `validate_metrics()` call from line 772 (post-pipeline) to immediately after stage 17 (post-simulation, pre-downstream). Add a second validation pass at the current location to catch issues introduced by downstream stages.

- **S1-D: Sanity guard audit logging.** Add a `_mutations: list[dict]` collector to `sanitize_run_result()` that records every mutation. Attach as `response.sanity_mutations` for audit trail.

- **S1-E: Event store TTL.** Add `max_events=10000` parameter and FIFO eviction to EventStore.

**Decision Gate:** All 15 scenarios must produce actions that are semantically correct for their scenario type. No CYBER scenario should receive maritime actions. No MARITIME scenario should receive cyber-only actions. 113 contract tests must still pass.

### Sprint 2 — Impact Intelligence Layer

**Goal:** Transform the impact map from a geo-pin display to a causal reasoning surface.

**Deliverables:**

- **S2-A: Unified ImpactMapResponse contract.** Define a Pydantic model: `ImpactMapResponse(run_id, scenario, nodes: list[ImpactNode], edges: list[ImpactEdge], propagation_events: list[PropagationEvent], decision_overlays: list[DecisionOverlay], headline: ImpactHeadline, validation_flags)`. This replaces the current separate map_payload/graph_payload/propagation_steps trio.

- **S2-B: Graph core node types.** Extend GCC_NODES with typed node categories: BANK, FINTECH, PAYMENT_RAIL, PORT, SHIPPING_LANE, ENERGY_ASSET, REGULATOR, INSURER, MARKET_INFRA. Map from sector field to node type.

- **S2-C: Graph core edge types.** Extend GCC_ADJACENCY edges with typed relationships: LIQUIDITY_DEPENDENCY, PAYMENT_DEPENDENCY, TRADE_FLOW, ENERGY_SUPPLY, INSURANCE_CLAIMS_LINK, REGULATORY_CONTROL, CORRESPONDENT_BANKING, SETTLEMENT_ROUTE. Infer from sector pairs.

- **S2-D: Propagation event timeline.** Add timestamped propagation events: `PropagationEvent(t_hours, source, target, mechanism, severity_transfer, cumulative_impact)`. This replaces the flat propagation_chain with a time-indexed event stream.

**Decision Gate:** The unified ImpactMapResponse must contain typed nodes, typed edges, and timestamped propagation events for all 15 scenarios. Frontend TypeScript types must match.

### Sprint 3 — Regime-Controlled Flow

**Goal:** Make the regime layer a system-state controller, not just an annotation.

**Deliverables:**

- **S3-A: Pre-simulation regime estimation.** Add a lightweight `estimate_regime()` function that takes only scenario_id + severity (available before simulation runs) and returns a preliminary RegimeType. This feeds into the simulation as a parameter.

- **S3-B: Regime-conditioned propagation parameters.** Pass regime amplifier, delay compression, and failure threshold shift into the propagation computation. The simulation engine reads these from a `RegimeConditions` object instead of hard-coded `0.85^hop` decay.

- **S3-C: Post-simulation regime refinement.** After simulation completes, run full `classify_regime()` with all 16 signals. If the refined regime differs from the pre-simulation estimate, log the delta and re-score critical outputs.

- **S3-D: Regime-conditioned thresholds.** All threshold-based decisions (risk_level classification, escalation triggers, executive status) must read from regime-adjusted thresholds, not static constants.

**Decision Gate:** Running the same scenario at the same severity must produce different propagation depths under different regime conditions. CRISIS_ESCALATION must propagate deeper and faster than STABLE.

### Sprint 4 — Decision Trigger + Outcome Truth

**Goal:** Complete the decision trigger pipeline and harden outcome traceability.

**Deliverables:**

- **S4-A: Decision overlay operations.** Define 6 overlay operations that modify graph behavior: CUT (sever edge), DELAY (increase edge delay), REDIRECT (reroute flow), BUFFER (add capacity), NOTIFY (flag for monitoring), ISOLATE (disconnect node). Each decision trigger can specify which overlays it activates.

- **S4-B: Outcome truth layer.** Extend event store with DECISION_EXECUTED, OUTCOME_MEASURED event types. Link decision → outcome → ROI with explicit foreign keys (decision_trigger_id → outcome_id → roi_computation_id).

- **S4-C: ROI reproducibility.** `compute_roi_from_events()` must produce identical results when replayed. Add a `replay_roi(run_id)` function that reconstructs ROI from the event stream and compares against the stored computation.

- **S4-D: Export integrity.** Add `export_run(run_id)` that produces a self-contained JSON with all events, regime state, decision triggers, outcomes, and ROI — suitable for regulatory submission.

**Decision Gate:** Every decision trigger must link to at least one overlay operation. ROI replay must match original computation within ±0.01%.

### Sprint 5 — Integration + Hardening

**Goal:** End-to-end integration testing, performance validation, frontend wiring.

**Deliverables:**

- **S5-A: Comprehensive scenario test suite.** Run all 15 scenarios at severity 0.3, 0.6, 0.9. Validate: action-scenario alignment, regime classification, decision trigger firing, propagation headline accuracy, validation flag correctness.

- **S5-B: Frontend TypeScript contracts.** Update `frontend/src/types/observatory.ts` with RegimeState, DecisionTrigger, ImpactMapResponse, SanityMutation types. Ensure `use-api.ts` hooks consume new fields.

- **S5-C: Performance baseline.** Measure end-to-end pipeline latency per scenario. Target: <500ms for 41-stage pipeline + regime layer. Identify and optimize any stage exceeding 50ms.

- **S5-D: Regression test suite.** Add contract tests for: action-scenario type alignment (15 scenarios × 5 types), regime classification boundaries (5 regimes × boundary cases), decision trigger condition evaluation (10 classes × condition permutations).

**Decision Gate:** All 15 scenarios pass all validation gates from Sprints 1–4. Pipeline latency < 500ms. Zero validation flags of severity "error" in any scenario run.

---

## 7. Files to Create

| File | Layer | Purpose |
|---|---|---|
| `backend/src/actions/action_registry.py` | Decision | Scenario-type-keyed action library replacing flat templates + index matrix |
| `backend/src/actions/__init__.py` | Decision | Module init |
| `backend/src/schemas/impact_map.py` | Impact | Pydantic models for ImpactMapResponse, ImpactNode, ImpactEdge, PropagationEvent |
| `backend/src/engines/propagation_headline_engine.py` | Impact | Build single-sentence propagation headline from chain |
| `backend/tests/test_action_scenario_alignment.py` | Testing | Validates every scenario type gets only semantically correct actions |
| `backend/tests/test_regime_classification.py` | Testing | Tests regime boundaries, transitions, graph modifiers |
| `backend/tests/test_decision_triggers.py` | Testing | Tests trigger conditions, urgency computation, time compression |

---

## 8. Files to Modify

| File | Change | Sprint |
|---|---|---|
| `backend/src/decision_layer.py` | Replace `_ACTION_TEMPLATES` + `SCENARIO_ACTION_MATRIX` lookup with `action_registry` queries | S1 |
| `backend/src/config.py` | Deprecate `SCENARIO_ACTION_MATRIX`; keep `SCENARIO_TAXONOMY` | S1 |
| `backend/src/policies/action_policy.py` | Update `evaluate_action_policy()` to use new registry | S1 |
| `backend/src/services/run_orchestrator.py` | Move validation call; add propagation headline; add sanity mutations | S1 |
| `backend/src/engines/sanity_guard.py` | Add mutation logging collector | S1 |
| `backend/src/events/event_store.py` | Add TTL / max_events eviction | S1 |
| `backend/src/engines/map_payload_engine.py` | Consume unified ImpactMapResponse | S2 |
| `backend/src/simulation_schemas.py` | Add RegimeState, DecisionTrigger Pydantic models | S2 |
| `frontend/src/types/observatory.ts` | Add TypeScript types for regime, triggers, impact map | S5 |

---

## 9. Functions to Implement

### Sprint 1

| Function | File | Signature |
|---|---|---|
| `get_actions_for_scenario_type` | `action_registry.py` | `(scenario_type: str) → list[ActionTemplate]` |
| `get_actions_for_scenario_id` | `action_registry.py` | `(scenario_id: str) → list[ActionTemplate]` |
| `build_propagation_headline` | `propagation_headline_engine.py` | `(chain: list[dict], gcc_nodes: list[dict]) → dict[str, str]` |
| `sanitize_run_result` (v2) | `sanity_guard.py` | Add `mutations: list[dict]` return tracking |
| `validate_metrics` (repositioned) | `run_orchestrator.py` | Called at stage 17.5, not stage 42 |
| `EventStore._evict` | `event_store.py` | `() → int` (returns evicted count) |

### Sprint 2

| Function | File | Signature |
|---|---|---|
| `build_impact_map_response` | `map_payload_engine.py` | `(result, nodes, adj, regime) → ImpactMapResponse` |
| `classify_node_type` | `map_payload_engine.py` | `(node: dict) → NodeType` |
| `classify_edge_type` | `map_payload_engine.py` | `(src_sector, tgt_sector) → EdgeType` |
| `build_propagation_events` | `map_payload_engine.py` | `(chain, nodes) → list[PropagationEvent]` |

### Sprint 3

| Function | File | Signature |
|---|---|---|
| `estimate_regime` | `regime_engine.py` | `(scenario_id: str, severity: float) → RegimeType` |
| `build_regime_conditions` | `regime_engine.py` | `(regime: RegimeType) → RegimeConditions` |

### Sprint 4

| Function | File | Signature |
|---|---|---|
| `build_decision_overlays` | `decision_trigger_engine.py` | `(triggers: list[DecisionTrigger]) → list[DecisionOverlay]` |
| `replay_roi` | `event_store.py` | `(run_id: str) → dict` |
| `export_run` | `event_store.py` | `(run_id: str) → dict` |

---

## 10. Wiring Order

Sprint 1 execution sequence (order matters):

```
Step 1: Create backend/src/actions/action_registry.py
        - Define ActionTemplate typed dict
        - Build SCENARIO_ACTION_REGISTRY keyed by scenario type
        - Implement get_actions_for_scenario_type()
        - Implement get_actions_for_scenario_id()

Step 2: Update backend/src/decision_layer.py
        - Replace _ACTION_TEMPLATES with action_registry import
        - Replace SCENARIO_ACTION_MATRIX lookup with registry query
        - Update build_decision_actions() to iterate registry results

Step 3: Update backend/src/policies/action_policy.py
        - Remove SCENARIO_ACTION_MATRIX dependency
        - Action filtering now happens in the registry, not the policy
        - Policy focuses on urgency escalation only

Step 4: Create backend/src/engines/propagation_headline_engine.py
        - Build headline from first 3 propagation hops
        - Produce EN and AR summaries

Step 5: Update backend/src/services/run_orchestrator.py
        - Add early validation call after stage 17
        - Add propagation headline to response.headline
        - Add sanity_mutations to response
        - Keep late validation call as secondary check

Step 6: Update backend/src/engines/sanity_guard.py
        - Add mutation collector
        - Return mutations list alongside mutated result

Step 7: Update backend/src/events/event_store.py
        - Add max_events parameter
        - Implement FIFO eviction in append()

Step 8: Run all tests
        - 113 contract tests
        - New action-scenario alignment tests
        - End-to-end orchestrator integration
```

---

## 11. Risks / Anti-Patterns

| Risk | Description | Mitigation |
|---|---|---|
| **Action library explosion** | Each scenario type could accumulate 20+ actions, making the decision panel overwhelming | Cap at 5 actions per scenario type in the registry. Additional actions are "reserve" class. |
| **Regime-simulation coupling** | Sprint 3's pre-simulation regime estimation creates a chicken-and-egg: regime depends on simulation output, but simulation needs regime input | Use scenario_id + severity as lightweight estimator. Full classification runs post-simulation. Log any estimate-vs-actual divergence. |
| **Validation false positives** | Moving validation earlier may flag values that downstream stages would have corrected | Use "warning" severity for early validation, "error" for late validation. Early flags don't block pipeline. |
| **Event store memory pressure** | 10,000 event cap may be too low for high-throughput deployments | Make max_events configurable via environment variable. Default 10,000 is for Mac M4 Max local dev. |
| **Frontend type drift** | Backend schema changes without frontend type updates create silent failures | Add a CI check that compares Pydantic model field names against TypeScript interface fields. |
| **Over-engineering the graph core** | Adding typed nodes and edges in Sprint 2 may not justify the complexity if the frontend doesn't consume the types | Start with string-based type fields on existing node/edge dicts. Promote to Pydantic models only when the frontend actively renders by type. |

---

## 12. What Not to Build Yet

1. **Real-time regime streaming.** The platform processes scenarios in request-response mode. Streaming regime classification from live data feeds (ACLED, AISStream, OpenSky) is a different architecture (event-driven, WebSocket). Build this only after the batch pipeline is fully hardened.

2. **ML-based action recommendation.** The rule-based action registry is deterministic, auditable, and explainable. ML-based action selection adds opacity without training data. Wait for ≥200 completed outcome cycles (decision → outcome → ROI) before considering supervised learning.

3. **Multi-tenant regime comparison.** Comparing regime states across tenants could leak competitive intelligence. Regime data must stay tenant-isolated. Cross-tenant analytics require a formal data-sharing agreement and PDPL compliance review.

4. **Automated trade execution.** Decision triggers identify WHAT should happen. They must NOT auto-execute financial operations. The `required_approval` field on DecisionTrigger enforces human-in-the-loop governance at the data contract level.

5. **Regime-conditional insurance pricing.** Using regime state to adjust premiums or reserves requires actuarial validation and GCC regulatory approval. The data contract is ready, but the pricing integration must go through IFRS 17 compliance review.

6. **Graph database migration.** The current in-memory graph (dict-based adjacency list) handles 43 nodes and 188 edges in <1ms. Neo4j or similar adds operational complexity without performance benefit at this scale. Reconsider at 500+ nodes.

7. **Quant dashboard for the regime layer.** The regime layer is a system-state controller, not a trading signal. Do not build candlestick charts, volatility surfaces, or time-series regime plots. The regime output is: classification + confidence + transition risk + trigger flags. That's the interface. Keep it operational, not analytical.

8. **Custom scenario builder UI.** Users should not be able to create arbitrary scenarios in this phase. The 15 scenarios in SCENARIO_CATALOG are curated and validated. A custom builder requires validation infrastructure (What constitutes a valid shock_nodes set? What's the minimum/maximum base_loss_usd?) that doesn't exist yet.
