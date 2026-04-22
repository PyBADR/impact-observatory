# 01 — Architecture Lock

**Status:** Foundation (spec-only).
**Depends on:** [00-README](./00-README.md).
**Consumed by:** [02-scenario-taxonomy](./02-scenario-taxonomy.md),
[03-decision-output-spec](./03-decision-output-spec.md),
[04-outcome-learning-spec](./04-outcome-learning-spec.md),
[05-gcc-expansion-plan](./05-gcc-expansion-plan.md).

---

## 0. What this document locks

Five layers. Fixed boundaries. Explicit dependencies. This is the spine
along which every 2.0 deliverable must align. Disagreement with this
document is a Foundation-level decision, not a Build-level one.

```
┌──────────────────────────────────────────────────────────────────────┐
│  Macro Signal Layer                                                  │
│  reads the world → produces SignalObservations                       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Transmission Layer                                                  │
│  reads SignalObservations → produces TransmissionChain               │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Exposure Layer                                                      │
│  reads TransmissionChain → produces EntityExposure / SectorRollup    │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Decision Layer                                                      │
│  reads Exposure → produces DecisionOutput                            │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Outcome Learning Layer                                              │
│  reads DecisionOutput + RealizedOutcome → produces LearningUpdate    │
│  writes back: signal reweighting, decision-model memory              │
└──────────────────────────────────────────────────────────────────────┘
```

Flow is **strictly downstream** layer-by-layer. The only upstream write path
is from Outcome Learning into calibration state consumed by the upper
layers (see Layer 5 and §7).

---

## 1. Macro Signal Layer

### Purpose

Convert observations of the world into a typed, timestamped, provenance-rich
stream of **SignalObservations** that the rest of the system can reason
about without inspecting raw sources.

### Inputs

- GCC public indicators: sovereign yield curves, sovereign risk spreads
  (2.0 wording; corresponds to what 1.0 displayed raw as "CDS spread"), FX
  parity deviations, policy-rate corridors, reserve levels, export volumes,
  refinery throughput, port throughput, LNG vessel counts, shipping lane
  utilization, regulatory filings.
- Conditioning feeds for cross-sector stress: interbank rate prints,
  cross-border clearing latency, payment-rail availability percentages.
- Human-curated macro annotations (analyst notes) tagged with source and
  confidence band.

### Outputs

`SignalObservation` — a structurally fixed record:

```
SignalObservation {
  observation_id          : string                         # ULID
  indicator               : string                         # canonical name
  value                   : number | null
  unit                    : string                         # "bps" | "bbl/d" | …
  observed_at             : timestamp
  source_id               : string                         # provenance
  source_tier             : "public" | "licensed" | "institutional" | "synthetic"
  confidence_band         : "HIGH" | "MEDIUM" | "LOW"
  deviation_from_baseline : number | null                  # optional
  tags                    : string[]                       # ["sovereign","qatar","fx"]
}
```

### What belongs here

- Normalization of heterogeneous sources to canonical indicators.
- Provenance stamping (source, tier, collection time).
- Confidence-band assignment per observation.
- Deduplication, late-arrival handling, freshness classification.

### What does NOT belong here

- No transmission logic.
- No exposure calculation.
- No decision hints.
- No entity-level damage model.
- No UI-specific formatting.

### Allowed dependencies

- External data sources (ACLED, AIS-Stream, OpenSky, Bloomberg/SAMA open
  data, licensed feeds, curated analyst input).
- A provenance registry (internal).

### Prohibited dependencies

- Cannot depend on Transmission Layer.
- Cannot depend on Exposure Layer.
- Cannot depend on Decision Layer.
- Cannot depend on Outcome Learning Layer directly; only on calibration
  state derived by Outcome Learning and published back through a versioned
  calibration channel (see §7).

---

## 2. Transmission Layer

### Purpose

Propagate a coherent set of SignalObservations through the entity graph
and produce a **TransmissionChain** — the ordered, typed path by which a
shock moves from its origin through the economy.

### Inputs

- A set of SignalObservations that clear a trigger threshold (configurable
  per scenario family — see [02-scenario-taxonomy](./02-scenario-taxonomy.md)).
- Entity graph (nodes + edges), versioned.
- Transmission coefficient matrix (versioned, calibrated).

### Outputs

`TransmissionChain` — a directed ordered graph slice:

```
TransmissionChain {
  chain_id     : string
  run_id       : string
  origin_nodes : EntityRef[]
  steps        : TransmissionStep[]
  peak_step    : int          # 1-based index into steps
  horizon_hours: int
}

TransmissionStep {
  step_index      : int
  source_entity   : EntityRef
  target_entity   : EntityRef
  mechanism       : "physical" | "financial" | "regulatory" | "informational"
  latency_hours   : number
  transmission_wt : number    # 0..1, from coefficient matrix
  stress_delta    : number    # -1..1
  loss_usd        : number
  evidence_refs   : ObservationRef[]
}
```

### What belongs here

- Graph traversal and mechanism classification.
- Latency and magnitude computation.
- Coherence checks (no self-cycles, no negative horizons, etc.).
- Emitting evidence references back to the SignalObservations that
  justified the trigger and each step.

### What does NOT belong here

- Signal normalization (belongs in Macro Signal).
- Entity-level KPI translation (belongs in Exposure).
- Action proposal (belongs in Decision).

### Allowed dependencies

- Macro Signal Layer (via SignalObservation stream).
- Entity graph registry.
- Transmission coefficient matrix (calibration artifact).

### Prohibited dependencies

- Cannot depend on Exposure Layer.
- Cannot depend on Decision Layer.
- Cannot depend on Outcome Learning Layer (except via the calibration
  channel in §7).

---

## 3. Exposure Layer

### Purpose

Translate a TransmissionChain into **EntityExposure** records (per-entity
stress, loss, classification) and **SectorRollup** records (aggregate
stress, loss, entity count, classification).

### Inputs

- TransmissionChain for the active run.
- Entity master data (sector membership, country, business model,
  institutional identifiers).
- Entity-level stress translation rules (sector-specific: banking LCR/CAR,
  insurance combined ratio / solvency, fintech availability, etc.).

### Outputs

```
EntityExposure {
  entity_ref         : EntityRef
  stress_score       : number   # 0..1
  loss_usd           : number
  classification     : "NOMINAL"|"LOW"|"GUARDED"|"ELEVATED"|"HIGH"|"SEVERE"
  time_to_breach_hrs : number | null      # sector-conditional
  breach_metric      : string | null      # e.g. "lcr", "combined_ratio"
  contributing_steps : TransmissionStep.ref[]
}

SectorRollup {
  sector_key        : string    # canonical, lowercase
  aggregate_stress  : number    # 0..1
  total_loss_usd    : number
  entity_count      : int
  classification    : StressTier
}
```

### What belongs here

- Per-entity translation from transmission stress to sector-specific KPIs.
- Aggregation into sector rollups.
- Classification thresholds (fixed in Foundation; tunable per sector in
  Build; never tunable at runtime by users).

### What does NOT belong here

- Action proposal (Decision).
- Confidence modeling beyond what is derivable from inputs (Macro Signal
  owns confidence bands; Exposure does not invent them).
- UI presentation logic.

### Allowed dependencies

- Transmission Layer output.
- Entity master data.
- Sector translation rule set.

### Prohibited dependencies

- Cannot depend on Decision Layer.
- Cannot depend on Outcome Learning Layer (except via calibrated sector
  thresholds published through §7).

---

## 4. Decision Layer

### Purpose

Produce ranked, auditable **DecisionOutput** records that articulate what
institutional action is proposed, by whom, in what window, at what
expected value, with what confidence and what trade-off. This is the
customer-visible output of the system.

### Inputs

- EntityExposure and SectorRollup records.
- TransmissionChain (for rationale / evidence).
- Decision catalog (2.0 lockbox of allowed action classes — see
  [02-scenario-taxonomy](./02-scenario-taxonomy.md) §4).
- Ownership matrix (action class → institutional owner).
- Calibration state from Outcome Learning (historical effectiveness,
  feasibility priors — §7).

### Outputs

`DecisionOutput` — the formal contract defined in
[03-decision-output-spec](./03-decision-output-spec.md).

### What belongs here

- Candidate action generation from the decision catalog.
- Ranking by priority_score = f(exposure, urgency, feasibility,
  calibrated effectiveness).
- Owner assignment, timing window, escalation trigger.
- With-intervention vs without-intervention comparison.
- Evidence chain linking each recommended action back to specific
  TransmissionSteps and SignalObservations.

### What does NOT belong here

- Signal collection.
- Transmission graph traversal.
- Stress translation.
- Realized-outcome capture (belongs in Outcome Learning).

### Allowed dependencies

- Exposure Layer output.
- Transmission Layer output (read-only, for evidence chaining).
- Decision catalog + ownership matrix.
- Calibration state from Outcome Learning (§7).

### Prohibited dependencies

- Cannot read Macro Signal Layer directly; all macro evidence must be
  chained through Transmission + Exposure.
- Cannot mutate any upstream layer.

---

## 5. Outcome Learning Layer

### Purpose

Close the institutional loop: for every DecisionOutput, capture the
realized outcome, attribute value, and update the calibration state that
influences future signal weights, decision scoring, and ownership trust.

### Inputs

- DecisionOutput records.
- RealizedOutcome observations (user-recorded, auto-recorded, or
  policy-recorded).
- External confirmation signals (did the predicted shock materialize; did
  the recommended action get executed).

### Outputs

```
LearningUpdate {
  decision_ref         : DecisionOutput.ref
  outcome_state        : "PENDING"|"APPROVED"|"DELAYED"|"REJECTED"|"EXECUTED"
                         |"CONFIRMED"|"DISCONFIRMED"
  realized_value_usd   : number | null
  missed_value_usd     : number | null
  attribution_conf     : "HIGH" | "MEDIUM" | "LOW"
  signal_reweighting   : SignalReweightDelta[]   # see 04-outcome-learning-spec
  model_memory_patch   : ModelMemoryPatch        # see 04-outcome-learning-spec
  recorded_at          : timestamp
  recorded_by          : "operator" | "system" | "external"
  governance_flags     : string[]                # audit / override / review
}
```

### What belongs here

- Outcome state machine (see [04-outcome-learning-spec](./04-outcome-learning-spec.md) §2).
- Value attribution (realized vs missed).
- Generation of signal-reweighting deltas and model-memory patches.
- Emission of governance events (override, review, breach).

### What does NOT belong here

- Primary decision making (belongs in Decision Layer).
- Entity stress recalculation from scratch (belongs in Exposure).
- Signal collection (belongs in Macro Signal).

### Allowed dependencies

- Decision Layer output.
- Realized-outcome record store.
- A calibration publishing channel (see §7).

### Prohibited dependencies

- Cannot directly mutate Macro Signal / Transmission / Exposure / Decision.
  Influence is exclusively through published calibration state (§7) that
  those layers subscribe to.

---

## 6. Key boundary decisions

1. **Flow is one-way downstream for live runs.** Macro Signal never reads
   from Transmission; Transmission never reads from Exposure; etc. This is
   enforced at the module-import level in Build.

2. **Outcome Learning is the only layer allowed to influence upstream —
   and only through the calibration channel.** Never through direct imports
   or live-run side effects.

3. **Decision Layer never touches Macro Signal directly.** All macro
   rationale flows through Transmission + Exposure. This avoids two
   competing narratives in the customer-visible output.

4. **Classification thresholds live in one place per layer.** Foundation
   fixes the slot; Build fixes the numbers; users cannot change them at
   runtime.

5. **Evidence chaining is mandatory.** Every DecisionOutput cites the
   EntityExposure records that grounded it; every EntityExposure cites the
   TransmissionSteps; every TransmissionStep cites the SignalObservations.
   Unverified references fail Decision-Layer validation.

6. **Layers are units of deployment in 2.0.** Build may collapse two layers
   into one service if justified, but must preserve the contracts. Build
   may not expand a layer across multiple services unless the extra
   services do not introduce new contracts.

---

## 7. Calibration channel (the one allowed upstream path)

Outcome Learning produces `CalibrationSnapshot` records. Upstream layers
read a frozen, versioned snapshot on run start — they never subscribe to a
live stream.

```
CalibrationSnapshot {
  snapshot_id              : string
  produced_at              : timestamp
  signal_weight_deltas     : SignalReweightDelta[]
  transmission_coefficient_deltas : CoefficientDelta[]
  decision_effectiveness   : { action_class_id → float }
  ownership_trust          : { owner_id → float }
  valid_from               : timestamp
  valid_to                 : timestamp
  version                  : int
  approver                 : "governance" | "auto"
}
```

Rules:
- Macro Signal Layer may consume `signal_weight_deltas`.
- Transmission Layer may consume `transmission_coefficient_deltas`.
- Decision Layer may consume `decision_effectiveness` and
  `ownership_trust`.
- No layer may consume raw LearningUpdate records directly.
- A snapshot is immutable once published; superseding it requires a new
  version and explicit activation.

This is the only mechanism by which learning changes the live system.

---

## 8. Mapping from 1.0 to 2.0

Informational — not prescriptive. Helps reviewers see that Foundation does
not break 1.0.

| 1.0 concept | 2.0 layer |
|---|---|
| `simulation_engine.py` 9-stage pipeline | Macro Signal + Transmission + Exposure condensed into one process (still allowed in Build if contracts hold) |
| `backend/src/schemas/scenario.py` `ScenarioCreate` | input to Macro Signal (configured trigger) and Transmission (which graph to traverse) |
| `sector_analysis` list from `/api/v1/runs` | Exposure.SectorRollup (after normalization per §3 in Foundation) |
| `decision_actions` list | Decision.DecisionOutput (after promotion to the new contract) |
| `confidence_score`, `trace_id`, `pipeline_stages_completed` | Cross-cutting provenance, preserved at every layer's output |
| v1.0.1 UI tab "Governance & Reliability" | Outcome Learning surface in 2.0 |

No 1.0 field is deleted by Foundation. Rename is at UI level only and is
already in v1.0.1.

---

## 9. Exit criteria for this document

Locked when every layer above has all six sections filled: purpose,
inputs, outputs, what-belongs, what-does-not-belong, allowed +
prohibited dependencies. This document satisfies that. Changes to any
layer's purpose, inputs, or outputs require a new revision of this file
and a governance review before Build proceeds.
