# Regime Layer Architecture — Impact Observatory | مرصد الأثر

**Version:** 1.0.0
**Date:** 2026-04-10
**Status:** Production-Ready — Implemented and Integrated

---

## 1. Why the Regime Layer Is Needed Now

The Impact Observatory's 17-stage simulation engine produces granular per-sector stress scores, propagation chains, and financial impact projections. However, the decision layer currently treats every scenario output identically — the same urgency formulas, the same propagation decay, the same thresholds — regardless of whether the system is calm or in active crisis.

This creates three concrete failure modes in production:

**F1 — Threshold blindness.** A node at 0.39 stress in a stable system is qualitatively different from 0.39 stress when three other sectors are already breached. Without regime awareness, the dashboard shows the same color for both.

**F2 — Propagation undercount.** During liquidity crises, interbank contagion accelerates 2–3× faster than normal. The current propagation engine uses static decay (`0.85^hop`), which underestimates cascade speed precisely when accuracy matters most.

**F3 — Decision timing drift.** Emergency liquidity actions have a 4-hour window during crisis but 24 hours during stable operations. Without regime-conditioned time windows, the decision layer either over-alerts (alert fatigue) or under-alerts (missed intervention window).

The regime layer solves all three by inserting a system-state classification between raw signals and downstream consumers. Every component — propagation, graph, decisions, thresholds — reads from the same regime classification, ensuring consistent behavior across the entire pipeline.

---

## 2. Production-Ready Regime Layer Spec

### 2.1 Five Canonical Regimes

| Regime ID | Severity Band | Label (EN) | Label (AR) | Persistence |
|---|---|---|---|---|
| `STABLE` | 0.00 – 0.20 | Stable Operations | عمليات مستقرة | 0.90 |
| `ELEVATED_STRESS` | 0.20 – 0.40 | Elevated Stress | ضغط مرتفع | 0.75 |
| `LIQUIDITY_STRESS` | 0.40 – 0.60 | Liquidity Stress | ضغط السيولة | 0.65 |
| `SYSTEMIC_STRESS` | 0.60 – 0.80 | Systemic Stress | ضغط نظامي | 0.55 |
| `CRISIS_ESCALATION` | 0.80 – 1.00 | Crisis Escalation | تصعيد أزمة | 0.80 |

### 2.2 Input Signal Schema (RegimeInputs)

Sixteen signals feed the classification engine. All have safe defaults so the engine never crashes on missing data:

| Signal | Type | Default | Source |
|---|---|---|---|
| `event_severity` | float 0–1 | 0.0 | Scenario definition |
| `system_stress` | float 0–1 | 0.0 | `unified_risk_score` |
| `scenario_type` | str | "" | MARITIME/ENERGY/LIQUIDITY/CYBER/REGULATORY |
| `banking_stress` | float 0–1 | 0.0 | Banking sector `aggregate_stress` |
| `lcr_ratio` | float | 1.20 | Liquidity Coverage Ratio |
| `car_ratio` | float | 0.12 | Capital Adequacy Ratio |
| `insurance_stress` | float 0–1 | 0.0 | Insurance sector `aggregate_stress` |
| `combined_ratio` | float | 0.95 | Insurance combined ratio |
| `fintech_stress` | float 0–1 | 0.0 | Fintech sector `aggregate_stress` |
| `payment_volume_impact_pct` | float | 0.0 | % reduction in payment throughput |
| `api_availability_pct` | float | 100.0 | Fintech API uptime |
| `propagation_depth` | int | 0 | Hops from origin |
| `nodes_affected` | int | 0 | Count of impacted nodes |
| `bottleneck_count` | int | 0 | Critical bottlenecks identified |
| `sectors_under_pressure` | int | 0 | Sectors with stress > 0.35 |

### 2.3 Composite Stress Formula

```
composite = Σ(signal_i × weight_i) × sector_pressure_bonus

Weights:
  event_severity:    0.20    system_stress:    0.20
  banking_stress:    0.18    insurance_stress: 0.10
  fintech_stress:    0.08    lcr_breach:       0.08
  car_breach:        0.06    combined_breach:  0.05
  payment_impact:    0.05

Sector pressure bonus:
  ≥3 sectors under pressure: × 1.15
  ≥4 sectors under pressure: × 1.10 (cumulative)
```

### 2.4 Output Contract (RegimeState)

| Field | Type | Description |
|---|---|---|
| `regime_id` | RegimeType | Canonical classification |
| `regime_label` / `regime_label_ar` | str | Human-readable labels |
| `confidence` | float 0–1 | Classification confidence (higher at band center) |
| `transition_risk` | float 0–1 | Probability of moving to a worse regime |
| `persistence_score` | float 0–1 | Likelihood of staying in current regime |
| `stress_level` | float 0–1 | Composite stress driving classification |
| `trigger_flags` | list[str] | Active breach/stress flags |
| `likely_next_regime` | RegimeType | Most probable next state |
| `transition_probability` | float 0–1 | Probability of that transition |
| `propagation_amplifier` | float | Shock speed multiplier |
| `delay_compression` | float | Time compression factor |
| `failure_threshold_shift` | float | Threshold tightening factor |

### 2.5 Transition Matrix

5×5 Markov transition matrix with base probabilities adjusted by proximity to regime boundaries:

```
                    STABLE  ELEVATED  LIQUIDITY  SYSTEMIC  CRISIS
STABLE              0.85    0.12      0.02       0.005     0.005
ELEVATED_STRESS     0.25    0.50      0.15       0.08      0.02
LIQUIDITY_STRESS    0.05    0.20      0.45       0.22      0.08
SYSTEMIC_STRESS     0.01    0.05      0.15       0.44      0.35
CRISIS_ESCALATION   0.00    0.02      0.08       0.25      0.65
```

---

## 3. Graph + Regime Integration Design

### 3.1 Regime Graph Adapter

The `regime_graph_adapter.py` translates RegimeState into concrete graph modifiers:

**Node Sensitivity Profiles:** Each regime defines sector-specific sensitivity multipliers. Under `CRISIS_ESCALATION`, banking nodes receive 1.80× sensitivity while healthcare stays at 1.10×. This reflects the empirical reality that financial nodes amplify crisis propagation far more than peripheral sectors.

**Edge Transfer Modifiers:** Cross-sector edges receive additional transfer coefficient boosts during stress regimes. Banking↔insurance edges get +0.12 boost at maximum, banking↔fintech +0.10. These boosts are scaled by regime severity index (0.0 for STABLE, 1.0 for CRISIS).

**Regime-Adjusted Propagation Formula:**
```
adjusted_stress = base_stress × node_sensitivity × propagation_amplifier
adjusted_transfer = base_transfer × (1 + edge_transfer_boost)
```

### 3.2 Propagation Amplifier Matrix

| Regime | Amplifier | Delay Compression | Threshold Shift |
|---|---|---|---|
| STABLE | 1.00× | 1.00 | 0.00 |
| ELEVATED_STRESS | 1.10× | 0.90 | -0.03 |
| LIQUIDITY_STRESS | 1.25× | 0.75 | -0.08 |
| SYSTEMIC_STRESS | 1.50× | 0.60 | -0.12 |
| CRISIS_ESCALATION | 2.00× | 0.40 | -0.20 |

---

## 4. Decision Trigger Layer Design

### 4.1 Trigger Architecture

The decision trigger engine evaluates 10 decision classes against condition sets built from three signal categories:

- **Regime conditions:** What system state is required?
- **Propagation conditions:** How deep/wide is the cascade?
- **Breach conditions:** Which regulatory thresholds are violated?

Each decision class has a condition set. A trigger fires when **at least one condition is met**. Urgency scales with the fraction of conditions satisfied.

### 4.2 Decision Classes

| Class | Base Urgency | Time Window | Approval Required | Sectors |
|---|---|---|---|---|
| EMERGENCY_LIQUIDITY | 0.92 | 4h | Yes | banking, fintech |
| CAPITAL_CONTROLS | 0.95 | 6h | Yes | banking, government |
| OIL_RESERVES_RELEASE | 0.90 | 8h | Yes | energy, government |
| PAYMENT_CONTINGENCY | 0.88 | 2h | Yes | fintech, banking |
| CYBER_DEFENSE | 0.85 | 1h | No | infrastructure, fintech |
| REGULATORY_FORBEARANCE | 0.80 | 12h | Yes | banking, insurance |
| PORT_REROUTING | 0.78 | 6h | No | maritime, logistics |
| CROSS_BORDER_COORDINATION | 0.75 | 24h | Yes | government, banking |
| STAGE_RESERVES | 0.50 | 24h | No | banking, insurance |
| MONITOR | 0.30 | 48h | No | all |

### 4.3 Urgency Formula

```
fraction_met = conditions_met / conditions_total
urgency = base_urgency × fraction_met + stress_level × 0.2
         + 0.1 if all conditions met

Time compression under severe regimes:
  SYSTEMIC_STRESS:    time_to_act × 0.6
  LIQUIDITY_STRESS:   time_to_act × 0.8
```

### 4.4 Trigger Provenance

Every DecisionTrigger includes full provenance: which conditions were evaluated, which were met, the signal values that triggered them, and bilingual reasoning summaries. This supports SHA-256 audit trail requirements.

---

## 5. Files Created

| File | Purpose | Lines |
|---|---|---|
| `backend/src/regime/__init__.py` | Module init, public API surface | 48 |
| `backend/src/regime/regime_types.py` | RegimeType, REGIME_DEFINITIONS, TRANSITION_MATRIX | 155 |
| `backend/src/regime/regime_engine.py` | RegimeInputs, RegimeState, classify_regime, build_regime_inputs | 367 |
| `backend/src/regime/regime_graph_adapter.py` | RegimeGraphModifiers, apply_regime_to_graph, stress/transfer helpers | ~210 |
| `backend/src/regime/decision_trigger_engine.py` | DecisionTrigger, TriggerCondition, build_decision_triggers | ~370 |

---

## 6. Files Modified

| File | Change | Risk |
|---|---|---|
| `backend/src/services/run_orchestrator.py` | Added 3 regime pipeline stages (17b/c/d), regime imports, regime fields in response dict | LOW — all additions are additive; no existing fields changed |
| `backend/src/engines/map_payload_engine.py` | Added `regime_modifiers` parameter to `build_map_payload`, `_apply_regime_stress` helper | LOW — parameter defaults to None; existing behavior unchanged |
| `backend/src/decision_layer.py` | Added `regime_urgency_boost` parameter to `build_decision_actions` | LOW — defaults to 0.0; no behavioral change for existing callers |

---

## 7. Functions Implemented

### regime_types.py
- `RegimeType` — Literal type with 5 values
- `ALL_REGIMES` — Ordered tuple for iteration
- `REGIME_DEFINITIONS` — Full definition dict per regime
- `TRANSITION_MATRIX` — 5×5 Markov matrix

### regime_engine.py
- `_compute_composite_stress(inputs) → (float, list[str])` — Weighted signal aggregation with trigger flag collection
- `_classify_from_stress(stress) → RegimeType` — Threshold-based classification
- `_compute_confidence(stress, regime) → float` — Band-center distance confidence
- `_compute_transitions(current, stress) → (RegimeType, float, float)` — Transition forecast
- `_build_reasoning(regime, stress, flags, inputs) → (str, str)` — EN/AR reasoning
- `classify_regime(inputs) → RegimeState` — **Primary API**
- `build_regime_inputs(result) → RegimeInputs` — Factory from pipeline dict
- `classify_regime_from_result(result) → RegimeState` — Convenience composition

### regime_graph_adapter.py
- `apply_regime_to_graph(regime_id, gcc_nodes, gcc_adjacency) → RegimeGraphModifiers` — **Primary API**
- `compute_regime_adjusted_stress(base_stress, node_id, modifiers) → float` — Per-node stress adjustment
- `compute_regime_adjusted_transfer(base_transfer, src, tgt, modifiers) → float` — Per-edge transfer adjustment

### decision_trigger_engine.py
- `_build_conditions(...) → dict[str, list[TriggerCondition]]` — Condition set builder for all 10 classes
- `build_decision_triggers(...) → list[DecisionTrigger]` — **Primary API**
- `build_decision_triggers_from_regime_state(regime_state, inputs) → list[DecisionTrigger]` — Convenience

---

## 8. Pipeline Wiring Order

```
Stage 1:   Validate scenario ID
Stage 2-17: SimulationEngine.run() → raw result
Stage 17b:  classify_regime_from_result(result) → RegimeState        ← NEW
Stage 17c:  apply_regime_to_graph(regime, nodes, adj) → GraphModifiers ← NEW
Stage 17d:  build_decision_triggers(regime, inputs) → triggers        ← NEW
Stage 18:   Audit
Stage 19:   Transmission Engine
Stage 20:   Counterfactual Engine
Stage 21:   Action Pathways Engine
...
Stage 41:   Failure Engine
Stage 42:   Map Payload Engine (now regime-aware)                     ← MODIFIED
Stage 43:   Validation + Sanity Guard
```

The regime stages (17b/c/d) execute immediately after the simulation engine and before all downstream consumers. This ensures every subsequent stage can optionally consume regime state without circular dependencies.

**Data flow:**
```
SimulationEngine.run()
    │
    ├──→ build_regime_inputs(result) → RegimeInputs
    │         │
    │         └──→ classify_regime(inputs) → RegimeState
    │                   │
    │                   ├──→ apply_regime_to_graph() → RegimeGraphModifiers
    │                   │         │
    │                   │         └──→ map_payload_engine (stress adjustment)
    │                   │
    │                   └──→ build_decision_triggers() → [DecisionTrigger]
    │
    └──→ [existing stages 18-41 unchanged]
```

---

## 9. Sprint-by-Sprint Execution Plan

### Sprint 1 (COMPLETE — This Delivery)
- [x] `regime_types.py` — 5 regime definitions + transition matrix
- [x] `regime_engine.py` — Classification engine with 16-signal input
- [x] `regime_graph_adapter.py` — Node/edge modifier computation
- [x] `decision_trigger_engine.py` — 10 decision classes, condition evaluation
- [x] `regime/__init__.py` — Clean public API surface
- [x] Orchestrator wiring — 3 new pipeline stages (17b/c/d)
- [x] Map payload integration — regime-adjusted stress in entity payloads
- [x] Decision layer integration — `regime_urgency_boost` parameter
- [x] Functional tests — 6 test scenarios passing
- [x] Contract tests — 113/113 passing (no regression)
- [x] End-to-end integration — Hormuz scenario produces LIQUIDITY_STRESS with 8 triggers

### Sprint 2 (Next)
- [ ] Frontend TypeScript types for `regime_state`, `decision_triggers`
- [ ] Regime badge component on Executive Dashboard
- [ ] Transition risk gauge on Impact Map overlay
- [ ] Decision trigger cards in the decision panel
- [ ] Regime-conditioned color scale for map entities

### Sprint 3 (Follow-on)
- [ ] Temporal regime tracking — store regime history per run for trend analysis
- [ ] Regime-aware recovery trajectory adjustment
- [ ] Multi-run regime comparison (compare regime paths across scenarios)
- [ ] Regime transition alerting — notify when transition_risk > 0.5

### Sprint 4 (Hardening)
- [ ] Regime hysteresis — prevent rapid oscillation between adjacent regimes
- [ ] Confidence calibration — validate confidence scores against known historical events
- [ ] Regime-specific stress test scenarios (predefined inputs that exercise each regime)
- [ ] PDPL/IFRS 17 audit logging for regime transitions

---

## 10. Risks and What Not to Build Yet

### Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **Regime oscillation** — rapid flipping between adjacent regimes when stress is near boundary | MEDIUM | Dashboard flicker, alert fatigue | Sprint 4 hysteresis buffer (±0.02 dead zone around boundaries) |
| **Confidence overstatement** — model reports 0.95 confidence without historical calibration | MEDIUM | False sense of precision | Confidence is mathematically derived from band distance; labeling it "model confidence" rather than "calibrated probability" |
| **Cross-sector boost tuning** — the 0.12/0.10/0.08 cross-sector boost values are informed estimates, not empirically calibrated | LOW | Slightly over/under-count contagion | Values are conservative; can be tuned per-deployment when historical GCC contagion data is available |
| **Decision trigger alert volume** — CRISIS_ESCALATION triggers all 10 classes simultaneously | LOW | Decision fatigue for operators | Triggers are sorted by urgency; UI should show top-3 with "show more" |

### What NOT to Build Yet

1. **ML-based regime classification.** The current rule-based engine is deterministic, auditable, and explainable. ML adds opacity without sufficient training data. Wait until ≥100 historical scenario runs are available.

2. **Real-time regime streaming.** The current engine classifies per-run. Streaming classification (sub-second regime updates from live feeds) requires a different architecture (event-driven, not request-response). Build this only when live data feeds (ACLED, AISStream, OpenSky) are in production.

3. **Regime-conditional pricing.** Using regime state to adjust insurance pricing or premium calculations requires actuarial validation and regulatory approval. The data contract is ready, but the pricing integration must go through GCC regulatory review.

4. **Cross-tenant regime correlation.** In multi-tenant SaaS, comparing regime states across tenants could leak competitive intelligence. Regime data must stay tenant-isolated until a formal data-sharing agreement is in place.

5. **Automated action execution.** Decision triggers identify WHAT should happen and WHEN. They must NOT auto-execute. Human-in-the-loop governance is mandatory — the `required_approval` field on DecisionTrigger enforces this at the data contract level.
