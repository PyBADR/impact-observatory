# 03 — Decision Output Spec

**Status:** Foundation (spec-only).
**Depends on:** [01-architecture-lock](./01-architecture-lock.md),
[02-scenario-taxonomy](./02-scenario-taxonomy.md).
**Consumed by:** [04-outcome-learning-spec](./04-outcome-learning-spec.md),
any future backend contract, any future UI binding.

---

## 0. What this document locks

The exact shape, semantics, and invariants of a 2.0 **DecisionOutput**.
This is the customer-visible output of the system. It is also the root
anchor for audit, policy review, and outcome learning.

Build may serialize this contract as Pydantic + TypeScript + JSON schema.
The wire format can evolve; the logical contract is locked here.

---

## 1. DecisionOutput contract

```
DecisionOutput {
  # ── Identity ────────────────────────────────────────────────────────
  decision_id          : string                 # ULID, globally unique
  run_id               : string                 # provenance to the run that produced it
  scenario_id          : string                 # from 02-scenario-taxonomy
  created_at           : timestamp
  version              : int                    # monotonic; see §10

  # ── Customer-visible core ───────────────────────────────────────────
  title                : LocalizedText          # { en, ar }
  summary              : LocalizedText          # 1–2 sentence plain-language
  action_class         : ActionClassId          # from 02-scenario-taxonomy §4
  owner                : OwnerRef               # institutional owner; see §5
  timing_window        : TimingWindow           # see §6
  escalation_threshold : EscalationTrigger      # see §7
  confidence_class     : "HIGH" | "MEDIUM" | "LOW"

  # ── Economics ───────────────────────────────────────────────────────
  expected_value_usd   : number                 # expected loss avoided / value saved
  cost_usd             : number                 # fully-loaded implementation cost
  trade_offs           : TradeOff[]             # see §8
  reversibility        : "HIGH" | "MEDIUM" | "LOW"

  # ── Rationale & evidence ────────────────────────────────────────────
  rationale            : Rationale              # see §9
  without_intervention : OutcomeBand            # see §11
  with_intervention    : OutcomeBand            # see §11
  comparison_narrative : LocalizedText          # institutional-tone prose

  # ── Governance ──────────────────────────────────────────────────────
  priority_score       : number                 # 0..1, derived per §12
  urgency              : number                 # 0..1, derived per §12
  feasibility          : number                 # 0..1, derived per §12
  calibration_ref      : CalibrationRef | null  # which calibration snapshot fed this
  audit_hash           : string                 # deterministic hash of the contract
}
```

All times are UTC ISO-8601. All USD values are whole dollars, non-negative
except where explicitly signed. All 0..1 fields are clamped and never null.

---

## 2. LocalizedText

```
LocalizedText {
  en : string        # required
  ar : string        # required
}
```

Both languages are **required** in Foundation. Build may fall back at the
UI layer when a field is missing, but the contract still demands both. No
free-form HTML.

---

## 3. ActionClassId

A string ID drawn from the lockbox in
[02-scenario-taxonomy](./02-scenario-taxonomy.md) §4. Anything not in that
table fails contract validation.

---

## 4. Title wording rules

- Institutional tone. Describe the action, not the adversary.
- English and Arabic both required.
- English maximum 96 characters; Arabic maximum 96 characters.
- No trailing punctuation.
- No scenario ID in the title.
- No currency values in the title; those belong in the economics block.

Examples (good):
- `Activate emergency liquidity facility and raise overnight repo limit by 150 bps`
- `تفعيل تسهيل السيولة الطارئ ورفع حد إعادة الشراء الليلية بمقدار 150 نقطة أساس`

Examples (bad):
- `Raise cyber threat level to orange` — adversarial framing, wrong register.
- `Fix $4.3B exposure` — currency in title.
- `hormuz_action_01` — internal ID leaked.

---

## 5. OwnerRef

```
OwnerRef {
  owner_id     : string              # canonical, e.g. "central_bank_uae"
  label        : LocalizedText       # display form
  category     : OwnerCategory
  ownership_trust : number           # 0..1, from calibration (§12)
}

OwnerCategory =
  | "central_bank"
  | "finance_ministry"
  | "energy_ministry"
  | "trade_authority"
  | "insurance_supervisor"
  | "payment_authority"
  | "sector_regulator"
  | "national_oil_company"
  | "commercial_institution"
  | "inter_governmental"
```

An owner must be resolvable in the ownership matrix maintained in Build;
a DecisionOutput may not reference a free-form owner string.

---

## 6. TimingWindow

```
TimingWindow {
  hours_to_act    : number    # soft target, business hours
  hours_to_breach : number    # hard threshold; after this, escalation_threshold fires
  mode            : "IMMEDIATE" | "CONDITIONAL" | "STRATEGIC"
}
```

Rules:
- `0 < hours_to_act ≤ hours_to_breach`.
- `IMMEDIATE` implies `hours_to_breach ≤ 72`.
- `CONDITIONAL` implies `72 < hours_to_breach ≤ 168`.
- `STRATEGIC` implies `hours_to_breach > 168`.
- UI must render scale-aware labels (`4h` / `3d` / `2w`) from these values.

---

## 7. EscalationTrigger

```
EscalationTrigger {
  description_en   : string
  description_ar   : string
  breach_condition : string      # machine-parseable expression (see §15)
  escalation_to    : OwnerRef    # whom to escalate to if breach fires
  severity_step    : "ELEVATE_URGENCY" | "ELEVATE_OWNER" | "ELEVATE_BOTH"
}
```

Escalation is evaluated continuously by the decision surface; the
mechanism is Build-level, the contract is locked here.

---

## 8. TradeOff

Short institutional trade-off statement — the honest cost of the
recommended action.

```
TradeOff {
  category : "fiscal" | "regulatory" | "reputational" | "operational"
           | "geopolitical" | "market"
  magnitude : "LOW" | "MEDIUM" | "HIGH"
  description : LocalizedText
}
```

Every DecisionOutput must declare **at least one** TradeOff. A decision
with zero trade-offs is rejected by contract validation — the product
does not render recommendations that pretend to be costless.

---

## 9. Rationale

```
Rationale {
  why_this_decision : LocalizedText         # maps to the UI "Why this decision?" block
  why_now           : LocalizedText         # maps to "Why now?"
  why_trust         : LocalizedText         # maps to "Why trust this?"
  evidence_chain    : EvidenceChainEntry[]  # mandatory, minimum 1 entry
}

EvidenceChainEntry {
  layer       : "exposure" | "transmission" | "signal"
  ref_type    : "entity_exposure" | "transmission_step" | "signal_observation"
  ref_id      : string
  summary     : LocalizedText
}
```

The evidence chain is not cosmetic. Every decision must trace back to at
least one EntityExposure, through at least one TransmissionStep, down to at
least one SignalObservation. A decision that cannot produce this chain
fails contract validation.

---

## 10. Version

A monotonically increasing integer per `decision_id`. Used when Outcome
Learning publishes a re-scored version of the same decision (for example,
after calibration snapshot update) without overwriting history.

UI renders the latest version by default but must expose prior versions in
audit.

---

## 11. OutcomeBand

```
OutcomeBand {
  loss_usd_p50      : number     # median point estimate
  loss_usd_p10      : number     # favorable 10th percentile
  loss_usd_p90      : number     # adverse 90th percentile
  stress_index_p50  : number     # 0..1
  narrative         : LocalizedText
}
```

`with_intervention.loss_usd_p50 ≤ without_intervention.loss_usd_p50` is
**not** enforced at the contract level — a recommended action may, in
rare cases, have zero or negative delta when evidence is thin. When that
is the case, `confidence_class` must be `LOW` and `rationale.why_this_decision`
must state the uncertainty explicitly. Silent lying is forbidden.

---

## 12. Derived scalars

`priority_score`, `urgency`, `feasibility` are computed in the Decision
Layer from the following inputs (exact weights are Build-tunable; the
inputs are Foundation-locked):

```
urgency      = f( timing_window.hours_to_breach, exposure_severity )
feasibility  = f( owner.ownership_trust, regulatory_risk, operational_complexity )
priority_score
             = g( urgency,
                  feasibility,
                  decision_effectiveness_for_action_class,
                  expected_value_usd,
                  cost_usd )
```

Where `decision_effectiveness_for_action_class` comes from the active
CalibrationSnapshot (see [01-architecture-lock](./01-architecture-lock.md) §7).

---

## 13. UI rendering contract (binding)

The Decision Panel (v1.0.1 tab `decisions`) and its 2.0 successor must
render, at minimum:

1. `title` (localized).
2. A status/urgency chip derived from `timing_window.mode` +
   `confidence_class`.
3. `owner.label` with category badge.
4. `timing_window.hours_to_act` in scale-aware form.
5. `expected_value_usd` and `cost_usd` (scale-aware formatter; no
   `$0.0B` for sub-billion).
6. Top 2 `trade_offs` visible, remainder under a disclosure.
7. `rationale.why_this_decision`, `rationale.why_now`,
   `rationale.why_trust` as the three canonical narrative blocks.
8. `without_intervention` vs `with_intervention` comparison panel.
9. An expandable evidence chain.

Missing any of (1)–(9) is a contract breach at the UI binding, not at the
contract itself.

---

## 14. Serialization guidance (informational, not binding)

- Backend suggested: Pydantic v2 model `DecisionOutputV2`. Aliases for any
  legacy field names from v1.0.x `decision_actions` (e.g.
  `action` → `title.en`, `priority_score` already exists).
- Frontend suggested: TypeScript type `DecisionOutput` mirroring the
  contract verbatim; store adapter maps legacy `DecisionActionV2` onto it
  during migration.
- JSON schema: one canonical file under `schemas/` in Build; versioned.

Implementation details are deliberately informational. Build owns them.

---

## 15. breach_condition grammar (v0, non-final)

Foundation does not finalize the expression grammar. Build proposes and
adopts a grammar under governance review. Foundation locks only the
*slot*: `breach_condition` is a machine-parseable string produced by the
Decision Layer and consumed by a continuous evaluator.

---

## 16. Invariants enforced by contract validation

1. All required fields present.
2. `action_class` ∈ [02-scenario-taxonomy](./02-scenario-taxonomy.md) §4.
3. `owner.owner_id` resolvable in the ownership matrix.
4. `timing_window.mode` matches the `hours_to_breach` bucket (§6).
5. At least one `TradeOff`.
6. `rationale.evidence_chain.length ≥ 1`.
7. `rationale.evidence_chain` contains **at least one** entry of each of
   `signal`, `transmission`, `exposure` layers — or `confidence_class`
   must be `LOW` with an explicit evidence-gap note in
   `rationale.why_trust`.
8. `audit_hash` matches a deterministic hash of the serialized contract
   sans `audit_hash` itself.

A DecisionOutput failing any invariant is **not** rendered in the UI. The
Decision Layer logs the violation to Outcome Learning's governance hooks
as `DECISION_CONTRACT_BREACH`.

---

## 17. Exit criteria

Locked when §1 is complete, §2–§12 are unambiguous, §16 invariants are
agreed, and the UI-rendering contract in §13 is accepted by product. This
file is the source of truth for any Pydantic / TypeScript / JSON schema
produced in Build.
