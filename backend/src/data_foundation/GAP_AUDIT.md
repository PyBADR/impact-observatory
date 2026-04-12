# P1 Data Foundation — Gap Audit
**Audit Date:** 2026-04-11
**Auditor:** Impact Observatory Architecture Team
**Scope:** All P1 data foundation modules
**Test Coverage:** 87/87 passing (100%)

---

## Audit Summary

| Category | Built | Tested | Status |
|----------|-------|--------|--------|
| Schemas (14 datasets) | 16 files | 48 tests | COMPLETE |
| Seed data (14 datasets) | 14 JSON files | 26 tests | COMPLETE |
| Ingestion contracts | 10 contracts | 4 tests | COMPLETE |
| Ingestion pipeline | 3 modules | 18 tests | COMPLETE |
| Decision layer | 2 modules | 10 tests | COMPLETE |
| Validation framework | 3 modules | 8 tests | COMPLETE |
| Referential integrity | 1 module | 3 tests | COMPLETE |
| Documentation | README + GAP_AUDIT | — | COMPLETE |

---

## CRITICAL GAPS (Must fix before production)

### GAP-C1: No Postgres ORM Layer
**Why it matters:** Schemas exist as Pydantic models but there are no SQLAlchemy ORM models, Alembic migrations, or table definitions. Data currently only lives in JSON seed files and memory.
**What to build:** SQLAlchemy models mirroring each Pydantic schema, Alembic migration scripts, database seeding CLI command.
**Where it fits:** New module `data_foundation/db/` with `orm.py`, `migrations/`, and `seed_db.py`.
**Priority:** P2-immediate. Block for any API endpoint that persists data.

### GAP-C2: No Real API/HTTP Ingestion
**Why it matters:** APILoader has the interface but returns empty results for actual HTTP calls. No central bank, OPEC, or ACLED data flows in automatically.
**What to build:** httpx-based HTTP client in APILoader, rate limiting, retry with exponential backoff, response parsing for each source's specific JSON format.
**Where it fits:** `ingestion/loaders.py` APILoader.fetch(), plus per-source adapter modules.
**Priority:** P2. Required for any live data.

### GAP-C3: No Authentication/Authorization on Data Access
**Why it matters:** tenant_id field exists on all schemas but there is no enforcement. Any tenant can read any other tenant's data.
**What to build:** Row-level security middleware, tenant context injection into all queries, API key scoping per tenant.
**Where it fits:** Integrates with existing `middleware/tenant_context.py`.
**Priority:** P2. Hard requirement for multi-tenant deployment.

---

## IMPORTANT GAPS (Should fix before enterprise demo)

### GAP-I1: Limited Seed Data Coverage
**Why it matters:** Entity registry has 20 entities but production needs ~500. Only KW/SA/AE have banking profiles. QA/BH/OM are underrepresented.
**What to build:** Expand entity_registry to cover all GCC D-SIBs (~50 banks), major insurers (~30), all significant ports (~40), and all central banks (6).
**Where it fits:** `seed/entity_registry_seed.json` and corresponding sector profile seeds.
**Priority:** P2.

### GAP-I2: No Time-Series Storage Strategy
**Why it matters:** Macro indicators, interest rates, oil prices, and FX are time-series data. Current flat JSON structure doesn't support efficient temporal queries (e.g., "KW CPI for last 12 months").
**What to build:** Partitioning strategy (by period_start/observation_date), TimescaleDB extension or date-partitioned Postgres tables, time-range query helpers.
**Where it fits:** `data_foundation/db/` and query layer.
**Priority:** P2.

### GAP-I3: No Event-Driven Ingestion Trigger
**Why it matters:** Current pipeline is batch-only (call run_ingestion_pipeline with records). No way to trigger ingestion on webhook receipt or schedule.
**What to build:** Celery or APScheduler task definitions for each source, webhook receiver endpoints, schedule registry.
**Where it fits:** `ingestion/scheduler.py`, `api/v1/webhooks.py`.
**Priority:** P2.

### GAP-I4: No Knowledge Graph Writer
**Why it matters:** All schemas have KG node/edge annotations in docstrings, but no Neo4j writer exists. The graph brain module exists in the codebase but doesn't consume P1 datasets.
**What to build:** Neo4j Cypher templates for each P1 schema, graph writer that translates Pydantic instances to Cypher MERGE statements.
**Where it fits:** Bridge between `data_foundation/` and existing `graph_brain/neo4j_graph_writer.py`.
**Priority:** P2.

### GAP-I5: No Data Lineage Tracking
**Why it matters:** Provenance hash and _ingested_at fields exist per-record, but there is no cross-record lineage (which source record produced which derived record).
**What to build:** Lineage graph model, parent_record_ids field on derived records, lineage query API.
**Where it fits:** `data_foundation/metadata/lineage.py`.
**Priority:** P2.

---

## LATER IMPROVEMENTS (P3 — post-launch refinement)

### GAP-L1: No ML Feature Store Integration
**Why it matters:** Simulation engine and decision brain could benefit from pre-computed features (rolling averages, z-scores, regime indicators).
**What to build:** Feature computation pipeline, feature versioning, point-in-time feature retrieval.
**Where it fits:** New `data_foundation/features/` package.
**Priority:** P3.

### GAP-L2: No Data Quality Scoring
**Why it matters:** Current validation is binary (pass/fail). Production needs a continuous quality score per-record and per-dataset that degrades with staleness, inconsistency, or missing fields.
**What to build:** Composite DQS (Data Quality Score) computation, quality decay model based on freshness, quality trend dashboard.
**Where it fits:** `validation/quality_score.py`.
**Priority:** P3.

### GAP-L3: No Streaming/Real-Time Pipeline
**Why it matters:** Event signals and FX data need sub-minute latency. Current batch pipeline has no streaming capability.
**What to build:** Redis Streams or Kafka integration, streaming quality gates, real-time dedup.
**Where it fits:** `ingestion/streaming.py`.
**Priority:** P3.

### GAP-L4: No Arabic NLP Signal Enrichment
**Why it matters:** GCC news and government announcements are primarily in Arabic. Current event signals rely on English-language sources.
**What to build:** Arabic NLP pipeline (arabert or similar), Arabic RSS ingestion, bilingual entity resolution.
**Where it fits:** Extends existing `signals/` and `connectors/` modules.
**Priority:** P3.

### GAP-L5: No Automated Schema Migration
**Why it matters:** schema_version field exists but there's no automated migration when schemas evolve. Breaking changes require manual data transformation.
**What to build:** Schema migration registry, forward/backward migration functions, version compatibility matrix.
**Where it fits:** `data_foundation/migrations/`.
**Priority:** P3.

### GAP-L6: No Decision Outcome Feedback Loop
**Why it matters:** OutcomeRecord model exists in impact_chain.py but there's no automated outcome collection or decision quality scoring.
**What to build:** Outcome collector, decision accuracy tracker, model calibration feedback.
**Where it fits:** `decision/outcome_tracker.py`.
**Priority:** P3.

---

## File Inventory (Post-Audit)

```
data_foundation/                         # 26 files
├── __init__.py                          # Package root, version 1.0.0
├── README.md                            # Architecture docs
├── GAP_AUDIT.md                         # This file
├── schemas/                             # 16 schema files
│   ├── __init__.py
│   ├── enums.py                         # 17 enum types
│   ├── base.py                          # FoundationModel + AuditMixin + GeoCoordinate
│   ├── dataset_registry.py              # A
│   ├── source_registry.py               # B
│   ├── entity_registry.py               # C
│   ├── macro_indicators.py              # D
│   ├── interest_rate_signals.py         # E
│   ├── oil_energy_signals.py            # F
│   ├── fx_signals.py                    # G
│   ├── cbk_indicators.py               # H
│   ├── event_signals.py                 # I
│   ├── banking_sector_profiles.py       # J
│   ├── insurance_sector_profiles.py     # K
│   ├── logistics_nodes.py              # L
│   ├── decision_rules.py               # M
│   └── decision_logs.py                # N
├── seed/                                # 14 JSON seed files
│   ├── __init__.py
│   ├── dataset_registry_seed.json       # 14 datasets
│   ├── source_registry_seed.json        # 11 sources
│   ├── entity_registry_seed.json        # 20 entities (KW/SA/AE/QA/BH/OM)
│   ├── macro_indicators_seed.json       # 6 indicators
│   ├── interest_rate_signals_seed.json  # 4 rate observations
│   ├── oil_energy_signals_seed.json     # 5 energy signals
│   ├── fx_signals_seed.json             # 6 FX pairs (all GCC)
│   ├── cbk_indicators_seed.json         # 6 CBK indicators
│   ├── event_signals_seed.json          # 3 events (Hormuz, CBK, Red Sea)
│   ├── banking_profiles_seed.json       # 3 bank profiles (NBK, KFH, FAB)
│   ├── insurance_profiles_seed.json     # 2 insurer profiles (GIG, Tawuniya)
│   ├── logistics_nodes_seed.json        # 9 nodes (7 ports + 2 airports)
│   ├── decision_rules_seed.json         # 5 active rules
│   └── decision_logs_seed.json          # 3 log entries
├── ingestion/                           # 3 modules
│   ├── __init__.py
│   ├── contracts.py                     # 10 ingestion contracts
│   ├── pipeline.py                      # Runtime pipeline engine
│   └── loaders.py                       # API/CSV/Manual/Derived loaders
├── validation/                          # 3 modules
│   ├── __init__.py
│   ├── validators.py                    # Quality gate evaluator
│   ├── integrity.py                     # Referential integrity checker
│   └── entrypoint.py                    # Single-call full validation
├── decision/                            # 2 modules
│   ├── __init__.py
│   ├── impact_chain.py                  # Signal→Transmission→Exposure→Decision→Outcome
│   └── rule_engine.py                   # Deterministic rule evaluator
└── metadata/                            # 1 module
    ├── __init__.py
    └── loader.py                        # Seed data loader
```

**Total:** 26 source files, 14 seed files, 87 passing tests, 0 failures.
