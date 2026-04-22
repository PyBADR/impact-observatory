# 02 — Scenario Taxonomy Spec

**Status:** Foundation (spec-only).
**Depends on:** [01-architecture-lock](./01-architecture-lock.md).
**Consumed by:** [03-decision-output-spec](./03-decision-output-spec.md).

---

## 0. What this document locks

The canonical **scenario families** Impact Observatory 2.0 recognizes, the
**naming and ID rules** for scenarios within them, the **lifecycle states**
a scenario passes through, and the **taxonomy governance** that decides
when a new family or scenario is added.

This is not a catalog of scenarios. It is the structural contract that any
specific scenario (existing or future) must conform to.

---

## 1. Canonical scenario families

Five families in Foundation. Additional families require a taxonomy
governance review (§6).

### 1.1 Maritime

- **Intent:** Disruption to GCC seaborne trade and hydrocarbon logistics.
- **Typical triggers:** Strait-of-Hormuz transit constraints; Red Sea
  corridor instability; Jebel Ali / Ras Tanura / Sohar throughput drops;
  naval escalation; shipping insurance premium spikes.
- **Transmission channels:** physical (port / vessel); financial (bunker
  fuel, re-insurance, marine P&I); regulatory (state-of-emergency trade
  permits).
- **Likely exposed sectors:** energy, logistics, trade, insurance, fintech
  (via SWIFT/RTGS bottlenecks on trade settlement).
- **Likely decision classes:** reroute / force-majeure-declaration /
  reinsurance-activation / reserve-release-coordination.

### 1.2 Energy

- **Intent:** Hydrocarbon supply, demand, or price shocks affecting
  GCC sovereign budgets and refinery throughput.
- **Typical triggers:** OPEC+ quota breach; Saudi Aramco production halt;
  Qatar LNG export disruption; regional refinery incident; global price
  spike or collapse (≥20% move in ≤5 trading days).
- **Transmission channels:** financial (sovereign revenue); physical
  (downstream fuel supply); regulatory (subsidy policy changes).
- **Likely exposed sectors:** energy, sovereign fiscal, banking,
  shipping, petrochemicals.
- **Likely decision classes:** production-adjustment / reserve-drawdown /
  subsidy-review / fiscal-consolidation-signal.

### 1.3 Liquidity

- **Intent:** Cross-border liquidity, interbank, or FX stress across
  GCC banking and clearing infrastructure.
- **Typical triggers:** Interbank rate spike (+150 bps in ≤48h);
  deposit-flight signal; FX parity deviation beyond policy corridor;
  sudden narrowing of swap-line availability; dollar funding squeeze.
- **Transmission channels:** financial (interbank, clearing); regulatory
  (central-bank intervention); informational (confidence contagion).
- **Likely exposed sectors:** banking, fintech, sovereign fiscal,
  insurance (short-duration liabilities).
- **Likely decision classes:** emergency-liquidity-facility /
  policy-rate-action / fx-swap-line-coordination / capital-controls-review.

### 1.4 Cyber

- **Intent:** Disruption of financial infrastructure, payment rails, or
  critical operational technology via cyber-origin events, regardless of
  attribution.
- **Typical triggers:** Payment-rail availability below SLA; SWIFT /
  RTGS latency breach; sustained DDoS against a critical financial
  institution; ransomware event affecting a GCC systemic node.
- **Transmission channels:** informational (trust contagion); financial
  (settlement freeze); physical (OT-dependent infrastructure).
- **Likely exposed sectors:** banking, fintech, infrastructure,
  government.
- **Likely decision classes:** operational-readiness-escalation /
  systems-isolation / transaction-controls / public-communication.
- **Customer-facing wording rule:** the scenario title must describe
  *impact* (e.g. *Critical Financial Infrastructure Disruption*), not
  attribution; attribution lives in the rationale body, not the title.

### 1.5 Regulatory

- **Intent:** Policy, sanction, or supervisory changes with
  macro-to-decision impact across GCC institutions.
- **Typical triggers:** Sanctions regime expansion affecting GCC
  counterparties; Basel / IFRS threshold changes; new macroprudential
  rules; cross-border data / residency rulings; rating-agency outlook
  moves.
- **Transmission channels:** regulatory (direct); financial (capital
  requirements, provisioning); informational (compliance signaling).
- **Likely exposed sectors:** banking, insurance, sovereign fiscal,
  fintech, trade.
- **Likely decision classes:** compliance-uplift / capital-plan-revision
  / counterparty-review / portfolio-rebalance.

---

## 2. Family-level contract (every family must provide)

For a scenario family to be recognized in Foundation it must specify all
six of:

1. `intent` — one-sentence purpose.
2. `typical_triggers` — 3–6 canonical triggers (measurable).
3. `transmission_channels` — subset of `physical | financial | regulatory | informational`.
4. `likely_exposed_sectors` — subset of the canonical sector list
   maintained in the entity registry (see
   [05-gcc-expansion-plan](./05-gcc-expansion-plan.md)).
5. `likely_decision_classes` — subset of the Decision Catalog (§4).
6. `family_id` — kebab-case short form, matches the rule in §3.

A family without all six may not register scenarios.

---

## 3. Naming rules

### 3.1 Scenario ID

- Lowercase snake_case.
- Maximum 48 characters.
- Must start with the family key when the scenario is intra-family:
  - `maritime_hormuz_chokepoint`
  - `energy_opec_quota_breach`
  - `liquidity_interbank_spike`
  - `cyber_payment_rail_disruption`
  - `regulatory_sanctions_expansion`
- Cross-family scenarios use a compound prefix joined by `_x_`:
  - `maritime_x_energy_hormuz_full_closure`
  - `liquidity_x_cyber_rtgs_latency_breach`
- Reserved IDs (1.x lineage): the existing v1.0.1 IDs (e.g.
  `hormuz_chokepoint_disruption`, `qatar_lng_disruption`,
  `uae_banking_crisis`, `gcc_cyber_attack`,
  `financial_infrastructure_cyber_disruption`) remain valid as **legacy
  aliases**. New 2.0 scenarios follow the rules above; legacy IDs are
  preserved for backward compatibility at the API layer but display labels
  are governed by the UI layer (v1.0.1 already demonstrates this
  separation).

### 3.2 Display label

- **Title case.** Institutional tone. No military / spy framing.
- **Describes impact, not attribution.**
- Arabic label required for every scenario; must be reviewed for tone,
  not machine-translated.
- Display labels may differ from the scenario ID; they are the customer
  surface and may be refined without changing the ID.

### 3.3 Family key

- Exactly one of: `maritime`, `energy`, `liquidity`, `cyber`, `regulatory`.
- New family keys require taxonomy governance review (§6).

---

## 4. Decision classes (the 2.0 lockbox)

A scenario's `likely_decision_classes` must be drawn from this set. Build
may extend this list only through taxonomy governance.

| Class | Intent | Typical owner category |
|---|---|---|
| `reroute` | Divert physical flows around a blockage | Trade / Logistics authority |
| `force_majeure_declaration` | Legal relief on affected contracts | Ministry / commercial |
| `reinsurance_activation` | Trigger catastrophe layers | Insurance supervisor / carrier |
| `reserve_release_coordination` | Strategic reserve drawdown coordination | Energy ministry / national oil co |
| `production_adjustment` | Change production posture | National oil co |
| `subsidy_review` | Open fiscal posture on subsidized goods | Finance ministry |
| `fiscal_consolidation_signal` | Pre-announce consolidation intent | Finance ministry |
| `emergency_liquidity_facility` | Provide short-term funding | Central bank |
| `policy_rate_action` | Change corridor / reserve requirement | Central bank / MPC |
| `fx_swap_line_coordination` | Activate GCC or global swap lines | Central banks |
| `capital_controls_review` | Review cross-border flow limits | Central bank / ministry |
| `operational_readiness_escalation` | Raise digital / operational posture | Sector regulator |
| `systems_isolation` | Isolate critical OT / payment rails | Operator + supervisor |
| `transaction_controls` | Apply temporary transaction limits | Payment authority |
| `public_communication` | Coordinated public / investor messaging | Regulator + comms |
| `compliance_uplift` | Uplift compliance posture to new rules | Compliance officer |
| `capital_plan_revision` | Revise regulatory capital plan | Bank CFO + supervisor |
| `counterparty_review` | Escalate counterparty-risk posture | Credit risk |
| `portfolio_rebalance` | Rebalance exposure | Investment committee |

Labels in this table are internal IDs. Display wording follows the rules in
[03-decision-output-spec](./03-decision-output-spec.md) §4.

---

## 5. Lifecycle states

Every scenario has exactly one of these states at a time:

| State | Meaning |
|---|---|
| `draft` | Registered in taxonomy but not yet executable. No runs allowed. |
| `candidate` | Proposed; under governance review. No runs allowed. |
| `active` | Approved; users may select and run. |
| `deprecated` | No new runs; historical runs remain visible and reproducible. |
| `retired` | No new runs; hidden from UI; historical runs remain addressable by ID only. |

Transitions:

```
draft ──▶ candidate ──▶ active ──▶ deprecated ──▶ retired
                │
                └──▶ draft (if governance rejects)
```

Only `active` scenarios appear in the Scenario Library UI. Deprecated and
retired scenarios may appear in audit views.

---

## 6. Taxonomy governance

Foundation fixes the five families; any sixth requires governance review
with these artifacts:

1. A written rationale: why the new family is structurally distinct from
   the five (it cannot be a sub-case of any existing family).
2. A filled family-level contract (§2 — all six fields).
3. Explicit listing of which sectors and decision classes the new family
   will reuse vs. introduce.
4. Impact assessment on existing calibration snapshots (see
   [01-architecture-lock](./01-architecture-lock.md) §7).

New scenarios inside an existing family require:

1. Unique scenario ID per §3.1.
2. Bilingual display label per §3.2.
3. Explicit assignment of `likely_decision_classes` from §4.
4. Default severity and horizon ranges (documented, not enforced as hard
   limits at API boundary beyond the existing 0–1 / 1–8760h envelope).
5. Lifecycle state set to `draft` on creation.

Governance maintains a taxonomy ledger (separate artifact, produced in
Build) recording every state transition and every catalog change.

---

## 7. Anti-patterns (explicitly disallowed)

- Creating a scenario family for a single client or regulatory regime.
  Regulatory regime changes are scenarios *inside* the Regulatory family.
- Using attribution or geopolitical framing in a display label. Say
  *Critical Financial Infrastructure Disruption*, not *State-Sponsored Cyber
  Attack*.
- Using scenario IDs as user-visible text. IDs are internal; labels are
  customer-facing.
- Mixing free-form action strings into `likely_decision_classes`. The
  field accepts only IDs from §4.
- Renaming a scenario ID in place. IDs are immutable; deprecate + re-add
  if conceptually changed.
- Introducing a "cross-family" family (e.g. "compound-risk"). Cross-family
  scenarios are expressed via the compound-ID rule in §3.1, not by
  creating a new family.

---

## 8. Exit criteria

This document is locked when all five families are defined per §2, the
naming rules in §3 are unambiguous, the decision-class lockbox in §4 is
agreed, and the lifecycle state machine in §5 is accepted. Changes to any
of those require a new revision of this file before Build implements the
registry.
