# Impact Observatory — Release: Data Foundation + Governance Layer

**Release Date:** 2026-04-12  
**Version:** 2.0.0-rc1  
**Classification:** Enterprise Release Candidate — Internal Validation

---

## Architecture Summary

This release introduces the **Data Foundation Layer** (82 modules, 13 packages) and the **Governance Layer** (8 modules) — completing the deterministic decision intelligence pipeline from raw signals through governed, auditable outcomes.

### 7-Layer Intelligence Stack Coverage

| Layer | Status | Module Count |
|-------|--------|-------------|
| **Data** — Schemas, ingestion, validation | Complete | 18 schemas, 5 loaders |
| **Features** — Entity registry, signals, indicators | Complete | 12 modules |
| **Models** — ORM tables, converters, repositories | Complete | 19 tables, 14 repos |
| **Agents** — Rule engine, spec compiler, families | Complete | 11 modules, 4 families |
| **APIs** — REST endpoints, connectors | Complete | 7 routers |
| **Evaluation** — Scoring, replay, performance | Complete | 8 modules |
| **Governance** — Lifecycle, validation, calibration, audit | Complete | 8 modules |

---

## What's New

### 1. Data Foundation Core (P2)

- **18 Pydantic domain schemas** covering entity registry, event signals, oil/energy/FX/rate signals, macro indicators, CBK regulatory data, banking/insurance/logistics profiles, and decision rules
- **19 ORM tables** (prefixed `df_*`, `df_eval_*`, `df_gov_*`) with `_FoundationMixin` for tenant isolation, schema versioning, and SHA-256 provenance hashing
- **14 async repositories** extending `BaseRepository[M]` with typed CRUD + domain-specific query methods
- **7 REST API routers** for entities, events, macro indicators, decision rules, decision logs, decision engine, and oil/energy connector
- **Ingestion pipeline** with typed data contracts and pluggable loaders

### 2. Decision Intelligence Engine

- **Rule engine** with `DataState` evaluation, 10 comparison operators, cooldown enforcement, and deterministic rule-firing
- **RuleSpec schema** — 11-component policy-grade specification (trigger signals, thresholds, transmission paths, exclusions, confidence basis, rationale templates)
- **Spec compiler** — Pure function `compile_spec()` that compiles RuleSpec to executable DecisionRule
- **4 rule families** — Oil Shock (3 specs), Rate Shift (2 specs), Logistics Disruption (2 specs), Liquidity Stress (2 specs) — all with GCC-specific calibration, Arabic translations, and historical evidence
- **Spec validator** — 4-level validation (structural, referential, semantic, policy)
- **Spec registry** — Singleton with `load_families()`, `compile_all_active()`, `validate_all()`

### 3. Outcome Tracking + Decision Evaluation + Replay

- **6-dimensional scoring** — severity alignment (ordinal distance), entity alignment (Jaccard), sector alignment (Jaccard), timing alignment (deviation ratio), correctness score (weighted composite: 0.35/0.30/0.20/0.15), confidence gap
- **Replay engine** — Deterministic replay of frozen DataState through current rule set, divergence detection against original decisions
- **Rule performance aggregator** — Periodic snapshots of rule quality (counts + averages + analyst verdicts)
- **Evaluation service** — Orchestrates expected outcome creation, actual observation recording, and evaluation pair scoring

### 4. Governance Layer

- **Rule lifecycle state machine** — DRAFT → REVIEW → APPROVED → ACTIVE → RETIRED|SUPERSEDED with 6 enforced guard functions (trigger signals, separate reviewer, approved_by, validation errors, reason, supersedes_spec_id)
- **Truth validation engine** — Source priority ranking, freshness checks, completeness thresholds, multi-source corroboration with deviation %, field-level validation (range, not_null, regex, enum_member)
- **Calibration trigger engine** — Deterministic threshold evaluation of RulePerformanceSnapshot metrics (confidence drift, false positive spikes, correctness degradation)
- **Unified audit chain** — SHA-256 hash-chained audit trail across all governance events with tamper detection and chain verification

### 5. Test Suite

- **368 tests passing** across 11 test files
- 113 pipeline contract tests (pre-existing)
- 43 rule spec tests
- 24 evaluation schema tests
- 36 evaluation scoring tests
- 13 replay engine tests
- 7 rule performance tests
- 25 governance schema tests
- 28 rule lifecycle tests
- 33 truth validation tests
- 24 calibration trigger tests
- 22 governance audit tests

---

## Design Principles

1. **Deterministic** — Every scoring formula, every rule evaluation, every replay is a pure function. No randomness, no ML, no side effects.
2. **Governance-first** — No rule activates without lifecycle transition. No data accepted without truth validation policy. No drift ignored without calibration triggers.
3. **Audit-complete** — SHA-256 hash chains on decision logs, evaluations, lifecycle events, and governance audit entries. Tamper detection built-in.
4. **GCC-native** — Arabic translations, PDPL-aware tenant isolation, CBK/CMA/SAMA regulatory awareness, Hijri date support readiness.
5. **Schema-driven** — Backend Pydantic models are the source of truth. TypeScript types align. No frontend-invented data structures.

---

## Deployment

- **Frontend** → Vercel (auto-deploys on push to `main`)
- **Backend** → Railway (auto-deploys on push to `main`, Dockerfile.backend)
- **Health** → `GET /health` returns `{"status":"ok","service":"Impact Observatory"}`

---

## Known Limitations

- Data Foundation API endpoints require PostgreSQL connection (graceful degradation when unavailable)
- No UI for governance layer (by design — governance is API/engine-only in this phase)
- Alembic migrations included but not yet wired to auto-run on deploy
