# 04 — Outcome Learning Spec

**Status:** Foundation (spec-only).
**Depends on:** [01-architecture-lock](./01-architecture-lock.md),
[03-decision-output-spec](./03-decision-output-spec.md).

---

## 0. What this document locks

The **post-decision learning model**: the state machine a decision passes
through after it leaves the Decision Layer, the outcome records that feed
the model, the attribution logic that decides "did it work," the
signal-reweighting and model-memory deltas that flow back, and the
governance hooks that keep the loop honest.

This closes the gap between *recommendation* and *institutional learning*.

---

## 1. Why this layer exists

A recommendation system that never learns is a static product. Impact
Observatory 2.0 commits to:

1. Every DecisionOutput is **observed** until it reaches a terminal state.
2. Every terminal state is **attributed** to realized outcomes with an
   explicit confidence band.
3. Every attribution produces a **calibration delta** for upstream layers.
4. Every calibration delta is **governance-reviewed** before becoming
   active.
5. Governance may **override or revert** any attribution or reweighting.

Without these five properties, the loop cannot be trusted by an
institutional customer.

---

## 2. DecisionState — the state machine

A DecisionOutput exists in exactly one of these states at any moment:

| State | Entered when | Exit conditions |
|---|---|---|
| `PENDING` | Decision emitted; no human action yet | operator acts, decision expires, or new version supersedes |
| `APPROVED` | Owner explicitly approves the recommended action | execution begins |
| `DELAYED` | Owner acknowledges but defers beyond `timing_window.hours_to_act` | eventually approved, rejected, or expires |
| `REJECTED` | Owner declines to act | terminal unless a new version is published |
| `EXECUTED` | Action recorded as performed | outcome observation begins |
| `CONFIRMED` | Realized outcome is consistent with `with_intervention` band | terminal |
| `DISCONFIRMED` | Realized outcome inconsistent with model | terminal; triggers calibration delta |

State transitions:

```
PENDING ──► APPROVED ──► EXECUTED ──► CONFIRMED
   │           │                       │
   │           ▼                       ▼
   │        DELAYED               DISCONFIRMED
   │           │
   ▼           ▼
REJECTED ◄── REJECTED
```

All transitions are auditable. Each transition records:

```
StateTransition {
  decision_ref   : DecisionOutput.ref
  from_state     : DecisionState
  to_state       : DecisionState
  recorded_at    : timestamp
  recorded_by    : "operator" | "system" | "external"
  rationale      : LocalizedText | null
  evidence_ref   : string | null                # external confirmation ref
}
```

Terminal states: `REJECTED`, `CONFIRMED`, `DISCONFIRMED`.

---

## 3. RealizedOutcome observation

A RealizedOutcome is how the world reports back what actually happened,
independent of any single owner's attestation.

```
RealizedOutcome {
  outcome_id        : string                 # ULID
  decision_ref      : DecisionOutput.ref
  observed_at       : timestamp
  observation_type  : "market" | "regulatory" | "operational"
                      | "self_reported" | "third_party"
  realized_loss_usd : number | null
  realized_stress   : number | null          # 0..1
  evidence_refs     : string[]               # source IDs from the Macro Signal layer
  notes             : LocalizedText | null
}
```

RealizedOutcomes are **append-only**. Correction is via a new record, not
edit-in-place.

---

## 4. Attribution

Attribution decides whether a realized outcome confirms or disconfirms
the decision model.

### Inputs
- DecisionOutput (including `without_intervention` and `with_intervention`
  bands).
- StateTransition history.
- RealizedOutcome records.

### Attribution logic (conceptual — Build owns the numerics)

1. If terminal state is `REJECTED`, compare realized outcome to
   `without_intervention` band. Consistent → model confirmed (correct not
   to act was inconsistent — i.e. we said "don't act" and indeed nothing
   bad happened). Inconsistent → calibration delta flagged.

2. If terminal state is `EXECUTED → CONFIRMED`, compare realized outcome
   to `with_intervention` band. Within p10–p90 → confirmed. Outside →
   flagged.

3. If terminal state is `EXECUTED → DISCONFIRMED`, realized outcome is
   outside the favorable band or worse than `without_intervention`.
   Always produces a calibration delta.

4. If no terminal state within horizon + 30 days, auto-transition to
   `PENDING_EXPIRED` (non-learning state; decision is stale, not
   outcome-attributable).

### attribution_confidence

```
"HIGH"   : realized loss observed directly; evidence chain complete.
"MEDIUM" : realized loss inferred from related signals; partial chain.
"LOW"    : realized loss inferred from proxies; material gaps in chain.
```

Only `HIGH` and `MEDIUM` feed calibration deltas. `LOW` is recorded but
does not influence weights — it influences the governance queue instead
(see §8).

---

## 5. SignalReweightDelta

When attribution is complete and confidence ≥ MEDIUM, Outcome Learning
computes a delta on the signal weights that contributed to the decision's
evidence chain.

```
SignalReweightDelta {
  indicator      : string              # canonical indicator name
  delta          : number              # bounded per §7
  rationale      : LocalizedText
  source_decision: DecisionOutput.ref
  produced_at    : timestamp
}
```

Rules:

1. Deltas target *indicators*, not individual SignalObservation records.
2. Multiple deltas on the same indicator within a calibration window are
   aggregated before publishing.
3. A reweighting that would raise an indicator's absolute weight above or
   below fixed hard limits is clamped and flagged to governance.

---

## 6. ModelMemoryPatch

Decision-level learning, distinct from signal-level learning:

```
ModelMemoryPatch {
  action_class_id      : ActionClassId         # from 02-scenario-taxonomy §4
  effectiveness_delta  : number                # bounded per §7
  ownership_trust_delta: { owner_id → number }
  rationale            : LocalizedText
  source_decision      : DecisionOutput.ref
  produced_at          : timestamp
}
```

Memory patches are inputs to the next CalibrationSnapshot. They do not
mutate any running Decision-Layer state directly.

---

## 7. Bounds, windows, rollover

- Every delta is clamped to `[-0.10, +0.10]` per CalibrationSnapshot
  cycle (Foundation bound; Build may refine within governance review).
- Calibration snapshots roll over at most **once per week** under normal
  governance. Emergency rollovers are allowed but require the explicit
  `approver = "governance"` flag and a review note.
- A calibration snapshot is immutable once published
  ([01-architecture-lock](./01-architecture-lock.md) §7).
- If cumulative delta on any single indicator or action class exceeds
  `0.25` since the last manual calibration review, Outcome Learning
  raises a `CALIBRATION_DRIFT_REVIEW` governance event.

---

## 8. Governance hooks

The following events must be emitted by Outcome Learning to the governance
log; each is auditable and reviewable:

| Event | Raised when |
|---|---|
| `DECISION_CONTRACT_BREACH` | Decision Layer produced a contract-invalid DecisionOutput; see [03-decision-output-spec](./03-decision-output-spec.md) §16. |
| `ATTRIBUTION_LOW_CONFIDENCE` | An outcome attribution completed with `LOW` confidence. |
| `CALIBRATION_DRIFT_REVIEW` | Cumulative delta on an indicator or action class exceeds §7 bound. |
| `OWNERSHIP_TRUST_SWING` | `ownership_trust` for any owner moved by more than 0.15 within a calibration cycle. |
| `OVERRIDE_APPLIED` | A reviewer manually overrode an attribution, delta, or snapshot. |
| `ROLLBACK_APPLIED` | A calibration snapshot was superseded intentionally to revert prior learning. |
| `LEARNING_PAUSED` | Governance paused learning globally or for a specific action class. |
| `LEARNING_RESUMED` | Counterpart to above. |

Every governance event carries the set of DecisionOutputs it is derived
from; there is no anonymous governance activity.

---

## 9. Retention & disclosure

- StateTransition and RealizedOutcome records are retained for **at
  least 7 years** (institutional norm; Build may extend by policy).
- SignalReweightDeltas and ModelMemoryPatches are retained for **at
  least 5 years**, or until superseded + 2 years.
- CalibrationSnapshots are retained **indefinitely** — they are the
  history of the model.
- Any decision that influenced a published calibration delta is
  discoverable from the snapshot back to the decision and forward to its
  realized outcome. That reverse-lookup path is a Build requirement
  flowing from this spec.

---

## 10. What this layer does NOT do

- Does not produce recommendations. That is the Decision Layer.
- Does not recalculate EntityExposure or TransmissionChain. Those are
  their own layers.
- Does not read raw external data. It consumes only DecisionOutput,
  RealizedOutcome, and StateTransition records.
- Does not mutate live runs. All influence is via the immutable
  calibration channel described in
  [01-architecture-lock](./01-architecture-lock.md) §7.

---

## 11. UI surface — v1.0.1 Governance & Reliability tab

The v1.0.1 tab `audit` (label: **Governance & Reliability** /
**الحوكمة والموثوقية**) is the natural surface for this layer. 2.0 Build
extends that surface to expose:

1. DecisionState of the active run's decisions.
2. Attributions once present.
3. Governance events for the last N days (read-only for operators;
   write-capable only for the governance role).
4. Calibration snapshot provenance, with a diff view vs. the previous
   snapshot.

Extending the tab is Build work. The contract is here.

---

## 12. Exit criteria

Locked when the state machine in §2 is complete, the attribution logic in
§4 is agreed, the delta types in §5–§6 are acceptable as inputs to the
calibration channel, and the governance event list in §8 is accepted as
non-optional. Changes to any of those require a new revision of this file
before Build implements the loop.
