# Impact Observatory 2.0 — Foundation Architecture Lock

**Status:** Foundation (spec-only). No implementation in this workstream.
**Branch:** `foundation/2.0-architecture-lock`
**Base:** `origin/main @ d0ffaa1` == tag `v1.0.1`
**Owner:** Product Architecture
**Date anchor:** 2026-04-22

---

## Purpose

Impact Observatory 1.0 was a scenario-based stress platform: select a shock
template, run the pipeline, inspect impact. 2.0 is a **GCC macro-to-decision
intelligence platform**: continuously read macro signals, transmit them
through a calibrated graph, identify exposure, produce auditable decisions,
and learn from outcomes.

This document set *locks the structural logic* of 2.0 before any code is
written. The goal is a specification base from which Build can proceed
without ambiguity — not a head-start on building.

---

## Canonical operating chain

```
Macro Signal → Transmission → Exposure → Decision → Outcome Learning
```

Every layer below exists to make that chain explicit, testable, and auditable.

---

## The five deliverables

| # | File | Purpose |
|---|---|---|
| 1 | [01-architecture-lock.md](./01-architecture-lock.md) | Five-layer architecture; layer purposes, inputs, outputs, allowed and prohibited dependencies. |
| 2 | [02-scenario-taxonomy.md](./02-scenario-taxonomy.md) | Canonical scenario families, naming rules, ID rules, lifecycle states, taxonomy governance. |
| 3 | [03-decision-output-spec.md](./03-decision-output-spec.md) | Formal shape of a 2.0 decision output, suitable for UI / policy review / audit / backend contract. |
| 4 | [04-outcome-learning-spec.md](./04-outcome-learning-spec.md) | Post-decision learning model: outcome states, attribution, signal reweighting, governance hooks. |
| 5 | [05-gcc-expansion-plan.md](./05-gcc-expansion-plan.md) | Data and entity expansion plan with Kuwait / Bahrain / Oman emphasis; essentials for Foundation vs items that belong in Build. |

Read in order. Each document stands alone but compounds with the previous.

---

## Foundation vs. Build — the boundary

Foundation **is** this set of documents. Foundation **is not** a running
system. The distinction is non-negotiable and is enforced by three rules:

| Foundation (this workstream) | Build (separate, later workstream) |
|---|---|
| Defines contracts, taxonomies, schemas, and boundaries. | Writes the code, services, UI, and database schema that realize them. |
| Can reference current v1.0.1 code as context, but must not modify it. | May modify v1.0.1 surfaces, add new ones, and evolve them. |
| Produces `.md` files, JSON schemas, diagrams. | Produces TypeScript, Python, migrations, tests, and deployable artifacts. |

No commit on `foundation/2.0-architecture-lock` may alter files outside
`docs/foundation-2.0/` except:
- allowed: `README.md` of the repo if a top-level index entry is required.
- disallowed: anything under `frontend/src/`, `backend/src/`, `backend/tests/`,
  `railway.toml`, `vercel.json`, `Dockerfile.backend`, `.github/workflows/`.

Any violation of this boundary **rebases this branch into a Build workstream**
and must trigger a naming change (Foundation → Build) and a separate review.

---

## Governance & protected refs

Under no circumstance does Foundation work touch:

| Ref | Reason |
|---|---|
| `v1.0.0` (tag obj `21d853a` → commit `7a94c80`) | Baseline. |
| `v1.0.1` (tag obj `3023561` → commit `d0ffaa1`) | Patch closure. |
| `v1.0.0-baseline-rc1` (tag obj `7b621c2` → commit `5a5ed2c`) | Recovery anchor; explicitly **not** on main's ancestry. |

The Foundation branch advances **only** through `docs/foundation-2.0/`.

---

## Relationship to 1.0

1.0 remains the running product. The Foundation does not deprecate it and
does not request changes to it. Where 2.0 reframes a 1.0 concept (for
example: 1.0's 9-stage pipeline becoming 2.0's five-layer architecture), the
mapping is described in the relevant spec, and 1.0 continues to operate
against its current contract until Build migrates it deliberately.

---

## Anti-scope

Explicitly **out of Foundation**:

- No 2.0 code of any kind.
- No UI components, routes, or hooks.
- No backend services, endpoints, or schemas executed against Pydantic /
  SQLAlchemy / Neo4j / Redis.
- No pipeline changes to the current simulation engine.
- No deployment work, no environment variable changes, no CI pipeline
  modifications.
- No broad data ingestion buildout; only the *plan* for what Build must
  ingest.
- No opportunistic cleanup of 1.0 code.
- No tag creation and no branch creation beyond this one.

---

## Completion criteria

Foundation is complete when:

1. All five documents (`01` → `05`) exist, are internally consistent, and
   reference each other where appropriate.
2. Each of the five layers has a defined purpose, inputs, outputs, allowed
   dependencies, and prohibited dependencies.
3. The decision output contract is precise enough that a backend engineer
   could derive a Pydantic model from it and a frontend engineer could
   derive a TypeScript type from it — without further consultation.
4. The outcome-learning model closes the loop from decision to institutional
   memory in explicit, testable states.
5. The GCC expansion plan distinguishes Foundation-essential entries from
   Build-phase entries and respects real data-availability constraints for
   Kuwait, Bahrain, and Oman.

When a later workstream ("Build Phase 1") begins, it must cite this document
set as its starting contract. Any deviation requires an updated Foundation
document first.
