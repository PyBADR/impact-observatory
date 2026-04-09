# Macro Signal Schema — Architecture Specification v1.0.0

**مخطط إشارات الاقتصاد الكلي — مواصفات البنية**

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | Production Draft |
| **Layer** | Data → Features (Layer 1-2) |
| **Owner** | Signal Gateway / Ingestion Pipeline |
| **Consumers** | Knowledge Graph Writer, Feature Store, Event Bus, AI Agents, Simulation Engine |
| **Last Updated** | 2026-04-09 |

---

## 1. Architecture Decision

**What:** A unified, versioned signal schema that serves as the single data contract for all macro intelligence signals entering the platform — regardless of domain, source, or transport mechanism.

**Why:** The Macro Intelligence platform ingests signals from 10+ heterogeneous sources (APIs, webhooks, manual entries, satellite feeds, ML models). Without a canonical schema, each source creates its own data format, leading to N×M integration complexity, inconsistent KG node properties, and unauditable data lineage. A single schema with domain-specific payloads reduces this to N×1.

**Layer:** This schema sits at the boundary between Layer 1 (Data) and Layer 2 (Features). Raw signals enter as Layer 1 artifacts. Once validated and enriched, they become Layer 2 feature vectors ready for model consumption.

**Trade-off Analysis:**

| Decision | Alternative | Why This Choice |
|----------|-------------|-----------------|
| Discriminated union for payloads | Single flat schema with all fields | Payloads grow independently per domain; flat schema would have 200+ optional fields within 6 months |
| `extensions: Dict[str, Any]` escape hatch | Strict-only schema, no dynamic fields | New domains must be prototypable without schema releases; `extensions` provides a controlled valve |
| UUIDv7 for signal_id | UUIDv4, ULID, snowflake | UUIDv7 is time-sortable (eliminates index scatter) and standard RFC 9562 |
| Separate event_time vs ingested_at | Single timestamp | Conflating "when it happened" with "when we learned" corrupts temporal KG queries |
| SHA-256 lineage_hash | No hash | PDPL and IFRS 17 require tamper-evident audit trails for GCC enterprise clients |

---

## 2. Schema Definition — Field Reference

### 2.1 Core Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_id` | `string (UUIDv7)` | Auto-generated | Unique identifier. Immutable after creation. |
| `schema_version` | `string (SemVer)` | Yes (default: "1.0.0") | Schema version. Consumers MUST check major version. |
| `signal_type` | `string (snake_case)` | **Yes** | Machine-readable type for routing (e.g., `oil_price_shock`). |
| `title` | `string (max 256)` | **Yes** | Short human-readable title for dashboards. |
| `domain` | `enum SignalDomain` | **Yes** | Primary domain: macroeconomic, insurance, operational, etc. |
| `temporal` | `TemporalContext` | **Yes** | Must include at minimum `event_time`. |
| `source` | `SignalSource` | **Yes** | Must include `source_id` and `source_type`. |
| `payload` | `SignalPayload` | **Yes** | Domain-specific data (discriminated union on `payload_type`). |

### 2.2 Optional Metadata Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | `string (max 4096)` | `null` | Extended narrative context. |
| `severity` | `enum SignalSeverity` | `NOMINAL` | Categorical severity (aligned with URS thresholds). |
| `severity_score` | `float [0.0–1.0]` | `0.0` | Numeric severity for continuous processing. |
| `status` | `enum SignalStatus` | `RAW` | Pipeline lifecycle status. |
| `tags` | `List[string]` | `[]` | Free-form tags, auto-lowercased and deduplicated. |
| `geo` | `GeoContext` | `null` | Lat/lng, region code, affected zones. |
| `quality` | `QualityIndicators` | (defaults) | Confidence, completeness, corroboration. |
| `entity_refs` | `List[EntityReference]` | `[]` | Pre-linked KG entity references. |
| `lineage` | `SignalLineage` | (defaults) | Audit trail, tenant_id, parent signals. |
| `extensions` | `Dict[str, Any]` | `{}` | Escape hatch for dynamic/unknown fields. |

### 2.3 Validation Rules

| Rule | Scope | Constraint |
|------|-------|------------|
| `signal_type` | Required | Non-empty, auto-normalized to snake_case |
| `title` | Required | 1–256 characters |
| `severity_score` | Optional | `[0.0, 1.0]` inclusive |
| `confidence_score` | Optional | `[0.0, 1.0]` inclusive |
| `trust_score` | Optional | `[0.0, 1.0]` inclusive |
| `tags` | Optional | Auto-lowercased, deduplicated, empty strings stripped |
| `signals` (batch) | Required | 1–1000 items per request |
| `lineage_hash` | Auto-computed | SHA-256 of `signal_id|payload_json|event_time` |
| Quarantine gate | Pipeline | Signals with `confidence_score < 0.30` are quarantined |

---

## 3. Payload Structure — Domain Types

The `payload` field uses a Pydantic discriminated union on the `payload_type` field. Each domain defines its own typed model. Adding a new domain means adding a new `*Payload` class and registering it in the union — zero changes to existing consumers.

### 3.1 MacroeconomicPayload

For GDP releases, oil prices, FX rates, central bank decisions, inflation data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload_type` | `"macroeconomic"` | Yes (discriminator) | |
| `indicator_code` | `string` | **Yes** | Standardized code (e.g., `BRENT_CRUDE_USD`) |
| `value` | `float` | **Yes** | Observed value |
| `unit` | `string` | No | `USD/bbl`, `%`, `bps` |
| `previous_value` | `float` | No | Prior period for delta |
| `delta_pct` | `float` | No | % change |
| `forecast_value` | `float` | No | Consensus forecast |
| `surprise_factor` | `float` | No | (value - forecast) / forecast |
| `frequency` | `string` | No | `daily`, `weekly`, `monthly`, `quarterly` |
| `affected_sectors` | `List[string]` | No | Sectors impacted |

### 3.2 InsurancePayload

For claims surges, catastrophe events, reserve breaches, underwriting shifts.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload_type` | `"insurance"` | Yes (discriminator) | |
| `line_of_business` | `string` | **Yes** | `property`, `marine_cargo`, `motor`, `health` |
| `estimated_loss_usd` | `float` | No (default 0.0) | Estimated economic loss |
| `insured_loss_usd` | `float` | No | Insured portion |
| `claims_count` | `int` | No | Number of claims |
| `combined_ratio_impact` | `float` | No | Impact on combined ratio |
| `reinsurance_triggered` | `bool` | No (default false) | |
| `ifrs17_impact` | `string` | No | IFRS 17 classification impact |

### 3.3 OperationalPayload

For port closures, pipeline disruptions, cyber incidents, infrastructure failures.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload_type` | `"operational"` | Yes (discriminator) | |
| `system_id` | `string` | **Yes** | Affected infrastructure node ID |
| `incident_type` | `string` | No | `port_closure`, `pipeline_rupture`, `cyber_breach` |
| `severity_score` | `float [0–1]` | No | Operational severity |
| `capacity_impact_pct` | `float [0–100]` | No | % capacity lost |
| `estimated_downtime_hours` | `float` | No | Expected outage duration |
| `affected_flow_types` | `List[string]` | No | `energy`, `logistics`, `payments` |

### 3.4 GeopoliticalPayload

For armed conflicts, sanctions, diplomatic shifts, escalations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `payload_type` | `"geopolitical"` | Yes (discriminator) | |
| `event_type` | `string` | **Yes** | `armed_conflict`, `sanction`, `treaty` |
| `actors` | `List[string]` | No | State/non-state actors |
| `escalation_level` | `float [0–1]` | No | Escalation intensity |
| `acled_event_id` | `string` | No | ACLED reference |
| `affected_trade_routes` | `List[string]` | No | Trade routes impacted |

---

## 4. JSON Examples

### 4.1 Macroeconomic Signal — Oil Price Shock

```json
{
  "signal_id": "019078a2-3c4f-7d00-8000-000000000001",
  "schema_version": "1.0.0",
  "signal_type": "oil_price_shock",
  "title": "Brent Crude drops 12% on OPEC+ disagreement",
  "description": "Brent crude fell from $82.50 to $72.60 following breakdown in OPEC+ production quota negotiations. Saudi Arabia signaled willingness to increase output unilaterally.",
  "domain": "macroeconomic",
  "severity": "HIGH",
  "severity_score": 0.72,
  "status": "VALIDATED",
  "tags": ["oil", "opec", "brent", "energy", "gcc"],
  "temporal": {
    "event_time": "2026-04-09T08:30:00Z",
    "ingested_at": "2026-04-09T08:31:15Z",
    "reported_at": "2026-04-09T08:30:45Z",
    "valid_from": "2026-04-09T00:00:00Z",
    "valid_until": null,
    "ttl_hours": 168
  },
  "geo": {
    "lat": 26.0667,
    "lng": 50.5577,
    "region_code": "SA",
    "region_name": "Arabian Gulf",
    "affected_zones": ["hormuz_strait", "ras_tanura_terminal", "fujairah_hub"]
  },
  "source": {
    "source_id": "reuters-eikon-feed",
    "source_type": "FEED",
    "source_name": "Reuters Eikon Real-Time Feed",
    "source_url": "https://eikon.refinitiv.com",
    "source_version": "3.2.1",
    "trust_score": 0.92
  },
  "quality": {
    "confidence_score": 0.95,
    "confidence_method": "SOURCE_DECLARED",
    "data_freshness_hours": 0.02,
    "completeness_score": 0.98,
    "corroboration_count": 3,
    "is_corroborated": true,
    "noise_flag": false,
    "duplicate_of": null
  },
  "payload": {
    "payload_type": "macroeconomic",
    "indicator_code": "BRENT_CRUDE_USD",
    "indicator_name": "Brent Crude Oil Price",
    "value": 72.60,
    "unit": "USD/bbl",
    "previous_value": 82.50,
    "delta_pct": -12.0,
    "forecast_value": 81.00,
    "surprise_factor": -0.1037,
    "frequency": "daily",
    "affected_sectors": ["energy", "maritime", "insurance", "banking"]
  },
  "entity_refs": [
    {
      "entity_id": "ent_aramco",
      "entity_type": "Organization",
      "entity_label": "Saudi Aramco",
      "relationship_type": "AFFECTS",
      "confidence": 0.95
    },
    {
      "entity_id": "node_hormuz_strait",
      "entity_type": "Chokepoint",
      "entity_label": "Strait of Hormuz",
      "relationship_type": "MENTIONS",
      "confidence": 0.80
    }
  ],
  "lineage": {
    "parent_signal_ids": [],
    "pipeline_version": "1.0.0",
    "processing_steps": ["validate", "enrich_geo", "link_entities"],
    "lineage_hash": "a3f2b8c9d1e4f567890abcdef1234567890abcdef1234567890abcdef123456",
    "tenant_id": "deevo_gcc_prod"
  },
  "extensions": {}
}
```

### 4.2 Operational Signal — Port Closure

```json
{
  "signal_id": "019078a2-3c4f-7d00-8000-000000000002",
  "schema_version": "1.0.0",
  "signal_type": "port_closure",
  "title": "Fujairah Port partial closure due to vessel collision",
  "domain": "operational",
  "severity": "ELEVATED",
  "severity_score": 0.55,
  "status": "ENRICHED",
  "tags": ["port", "fujairah", "maritime", "uae", "logistics"],
  "temporal": {
    "event_time": "2026-04-08T14:00:00Z",
    "ingested_at": "2026-04-08T14:12:30Z",
    "valid_from": "2026-04-08T14:00:00Z",
    "valid_until": "2026-04-11T14:00:00Z",
    "ttl_hours": 72
  },
  "geo": {
    "lat": 25.1164,
    "lng": 56.3400,
    "region_code": "AE",
    "region_name": "Port of Fujairah",
    "affected_zones": ["fujairah_hub", "fujairah_anchorage"]
  },
  "source": {
    "source_id": "ais-stream-v2",
    "source_type": "AIS",
    "source_name": "AISStream Maritime Feed",
    "trust_score": 0.78
  },
  "quality": {
    "confidence_score": 0.72,
    "confidence_method": "MODEL_COMPUTED",
    "data_freshness_hours": 0.2,
    "completeness_score": 0.85,
    "corroboration_count": 1,
    "is_corroborated": false,
    "noise_flag": false
  },
  "payload": {
    "payload_type": "operational",
    "system_id": "node_fujairah_port",
    "system_name": "Port of Fujairah",
    "incident_type": "port_closure",
    "severity_score": 0.55,
    "capacity_impact_pct": 40.0,
    "estimated_downtime_hours": 72.0,
    "estimated_recovery_hours": 96.0,
    "affected_flow_types": ["energy", "logistics"],
    "upstream_dependencies": ["node_hormuz_strait"],
    "downstream_dependents": ["node_jebel_ali_port", "ent_adnoc"]
  },
  "entity_refs": [
    {
      "entity_id": "node_fujairah_port",
      "entity_type": "Port",
      "entity_label": "Port of Fujairah",
      "relationship_type": "AFFECTS",
      "confidence": 0.98
    }
  ],
  "lineage": {
    "parent_signal_ids": [],
    "pipeline_version": "1.0.0",
    "processing_steps": ["validate", "enrich_geo", "link_entities", "compute_impact"],
    "lineage_hash": "b4e3c9d0f2a1b678901cdef23456789abcdef01234567890abcdef0123456789",
    "tenant_id": "deevo_gcc_prod"
  },
  "extensions": {
    "vessel_imo": "9876543",
    "vessel_name": "MV Gulf Star",
    "berth_number": "T3-07"
  }
}
```

### 4.3 Insurance Signal — Claims Surge

```json
{
  "signal_id": "019078a2-3c4f-7d00-8000-000000000003",
  "schema_version": "1.0.0",
  "signal_type": "claims_surge",
  "title": "Marine cargo claims surge following Red Sea rerouting",
  "description": "Marine cargo insurers in GCC report 340% increase in delay/damage claims as vessels reroute around Cape of Good Hope. Average claim size up 28%.",
  "domain": "insurance",
  "severity": "ELEVATED",
  "severity_score": 0.58,
  "status": "CORRELATED",
  "tags": ["insurance", "marine_cargo", "red_sea", "claims", "reinsurance"],
  "temporal": {
    "event_time": "2026-04-07T00:00:00Z",
    "ingested_at": "2026-04-09T09:00:00Z",
    "reported_at": "2026-04-08T16:00:00Z",
    "valid_from": "2026-04-01T00:00:00Z",
    "valid_until": "2026-04-30T23:59:59Z"
  },
  "geo": {
    "region_code": "AE",
    "region_name": "UAE - DIFC Insurance Market",
    "affected_zones": ["red_sea_corridor", "suez_canal", "bab_el_mandeb"]
  },
  "source": {
    "source_id": "manual-analyst-gcc",
    "source_type": "MANUAL",
    "source_name": "GCC Insurance Desk Analyst",
    "trust_score": 0.85
  },
  "quality": {
    "confidence_score": 0.80,
    "confidence_method": "ANALYST_ASSIGNED",
    "data_freshness_hours": 24.0,
    "completeness_score": 0.90,
    "corroboration_count": 2,
    "is_corroborated": true,
    "noise_flag": false
  },
  "payload": {
    "payload_type": "insurance",
    "line_of_business": "marine_cargo",
    "event_type": "claims_surge",
    "estimated_loss_usd": 145000000.0,
    "insured_loss_usd": 87000000.0,
    "total_insured_value_usd": 2400000000.0,
    "claims_count": 1247,
    "combined_ratio_impact": 0.18,
    "reserve_adequacy_ratio": 0.72,
    "reinsurance_triggered": true,
    "ifrs17_impact": "risk_adjustment_increase",
    "affected_entities": ["ent_adnic", "ent_oman_insurance", "ent_tawuniya"]
  },
  "entity_refs": [
    {
      "entity_id": "ent_adnic",
      "entity_type": "Organization",
      "entity_label": "Abu Dhabi National Insurance Company",
      "relationship_type": "AFFECTS",
      "confidence": 0.88
    },
    {
      "entity_id": "node_red_sea_corridor",
      "entity_type": "TradeRoute",
      "entity_label": "Red Sea Trade Corridor",
      "relationship_type": "ORIGINATES_FROM",
      "confidence": 0.92
    }
  ],
  "lineage": {
    "parent_signal_ids": ["019078a2-3c4f-7d00-8000-000000000099"],
    "pipeline_version": "1.0.0",
    "processing_steps": ["validate", "enrich_geo", "link_entities", "correlate_events"],
    "lineage_hash": "c5f4d0e1a3b2c789012def34567890abcdef12345678901bcdef01234567890a",
    "tenant_id": "deevo_gcc_prod"
  },
  "extensions": {
    "avg_claim_size_usd": 69768,
    "avg_claim_size_delta_pct": 28.0,
    "rerouting_premium_increase_pct": 15.0
  }
}
```

---

## 5. Knowledge Graph Mapping Logic

This section describes how `MacroSignal` objects map to Neo4j nodes, relationships, and properties. No Cypher code — just the conceptual mapping that the KG Writer service implements.

### 5.1 Signal → Event Node

Every promoted signal (`status = PROMOTED`) becomes an `(:Event)` node in the KG.

| Signal Field | KG Node Property | Notes |
|---|---|---|
| `signal_id` | `event_id` | Stable reference back to raw signal |
| `signal_type` | `event_type` | Used as secondary label: `(:Event:OilPriceShock)` |
| `title` | `title` | |
| `domain` | `domain` | Also applied as node label: `(:Event:Macroeconomic)` |
| `severity` | `severity` | Categorical |
| `severity_score` | `severity_score` | Numeric for graph algorithms |
| `temporal.event_time` | `event_time` | Temporal index property |
| `temporal.valid_from/until` | `valid_from`, `valid_until` | For temporal graph queries |
| `geo.lat/lng` | `lat`, `lng` | Spatial index for PostGIS bridge |
| `geo.region_code` | `region_code` | Partition key |
| `quality.confidence_score` | `confidence` | Filters low-confidence events |
| `lineage.lineage_hash` | `audit_hash` | Tamper detection |
| `lineage.tenant_id` | `tenant_id` | Multi-tenant partition |
| `payload.*` | Flattened onto node | Domain-specific properties (e.g., `indicator_code`, `value`) |

**Multi-label strategy:** Events carry multiple Neo4j labels for fast filtering: `(:Event:Macroeconomic:OilPriceShock)`, `(:Event:Operational:PortClosure)`, etc.

### 5.2 Entity References → Entity Nodes + Relationships

Each `entity_ref` in the signal maps to a relationship from the Event node to an existing Entity node.

| Signal Field | KG Element | Notes |
|---|---|---|
| `entity_refs[].entity_id` | `MATCH (e:Entity {entity_id: ...})` | Lookup existing node |
| `entity_refs[].entity_type` | Node label `:Organization`, `:Port`, etc. | Create if not exists (MERGE) |
| `entity_refs[].relationship_type` | Relationship type | `(:Event)-[:AFFECTS]->(:Entity)` |
| `entity_refs[].confidence` | Relationship property `confidence` | Edge weight for graph algorithms |
| `temporal.event_time` | Relationship property `since` | Temporal edge for time-travel queries |

### 5.3 Source → Source Node + Relationship

| Signal Field | KG Element |
|---|---|
| `source.source_id` | `(:Source {source_id: ...})` node (MERGE) |
| `source.source_type` | Property on `:Source` node |
| `source.trust_score` | Property + edge weight on `[:EMITTED]` |
| — | `(:Source)-[:EMITTED]->(:Event)` relationship |

### 5.4 Lineage → Derivation Chain

| Signal Field | KG Element |
|---|---|
| `lineage.parent_signal_ids` | `(:Event)-[:DERIVED_FROM]->(:Event)` for each parent |
| `lineage.processing_steps` | Property `pipeline_steps` on the `[:DERIVED_FROM]` edge |
| `lineage.lineage_hash` | Property `audit_hash` on the Event node |

### 5.5 Tags → Tag Nodes

| Signal Field | KG Element |
|---|---|
| `tags[]` | `(:Tag {name: "oil"})` — MERGE per unique tag |
| — | `(:Event)-[:TAGGED_WITH]->(:Tag)` relationship |

### 5.6 Conceptual Graph Topology

```
(:Source)-[:EMITTED]->(:Event:Macroeconomic:OilPriceShock)
                          |
                          |-[:AFFECTS {confidence: 0.95}]->(:Organization {entity_id: "ent_aramco"})
                          |-[:MENTIONS {confidence: 0.80}]->(:Chokepoint {entity_id: "node_hormuz_strait"})
                          |-[:TAGGED_WITH]->(:Tag {name: "oil"})
                          |-[:TAGGED_WITH]->(:Tag {name: "opec"})
                          |-[:DERIVED_FROM]->(:Event {event_id: "..."})  // parent signal
```

---

## 6. Versioning Strategy

### 6.1 Schema Versioning (SemVer)

The `schema_version` field follows Semantic Versioning 2.0.0:

| Change Type | Version Bump | Example | Breaking? |
|---|---|---|---|
| New optional field on MacroSignal | MINOR | 1.0.0 → 1.1.0 | No |
| New payload domain type | MINOR | 1.1.0 → 1.2.0 | No |
| New enum value in existing enum | MINOR | 1.2.0 → 1.3.0 | No |
| Documentation/description change | PATCH | 1.3.0 → 1.3.1 | No |
| Remove a field | MAJOR | 1.3.1 → 2.0.0 | **Yes** |
| Change a field's type | MAJOR | 2.0.0 → 3.0.0 | **Yes** |
| Rename a field (without alias) | MAJOR | — | **Yes** |

### 6.2 How v1 Evolves to v2

When a MAJOR version bump is required:

1. **Parallel schemas:** Define `MacroSignalV2` alongside `MacroSignalV1`. Both schemas coexist in the codebase.
2. **Dual endpoints:** The ingestion API accepts both `/v1/signals/ingest` and `/v2/signals/ingest` simultaneously.
3. **Version router:** The Signal Gateway reads `schema_version` from the payload and routes to the correct validator.
4. **Migration window:** v1 is supported for a minimum of 90 days after v2 GA. During this window, a translation layer converts v1 signals to v2 internally.
5. **Deprecation:** After the migration window, v1 endpoint returns `410 Gone` with a migration guide URL.

### 6.3 Payload Extension Pattern

Adding a new domain (e.g., `ClimatePayload`) requires:

1. Define `ClimatePayload(BaseModel)` with `payload_type: Literal["climate"]`
2. Add it to the `SignalPayload` union
3. Add `CLIMATE = "climate"` to `SignalDomain` enum
4. Bump schema_version MINOR: `1.0.0` → `1.1.0`
5. No changes to existing consumers — they ignore unknown `payload_type` values

---

## 7. Operational Recommendations

### 7.1 Handling Unknown / Dynamic Fields

The `extensions: Dict[str, Any]` field is the controlled escape hatch. Rules:

- Keys MUST use `snake_case`
- Values MUST be JSON-serializable (no binary, no circular refs)
- Extensions are stored as a JSON blob in Neo4j (not flattened to node properties)
- If an `extensions` key appears in >50% of signals for a domain, it should be promoted to a typed payload field (tracked via observability metrics)
- Extensions are NOT indexed in Neo4j — they are for supplementary data only

### 7.2 Handling Schema Evolution

- New optional fields with defaults are always backward-compatible
- Pydantic's `model_config = ConfigDict(extra="ignore")` ensures old consumers silently drop unknown fields
- The `schema_version` field allows the pipeline to apply version-specific validation rules
- A schema registry (JSON Schema exported from Pydantic) is published on every deployment

### 7.3 Handling Noisy / Low-Confidence Signals

| Confidence Range | Action | KG Treatment |
|---|---|---|
| `≥ 0.70` | Accept immediately | Write to KG as `:Event` with full relationships |
| `0.30 – 0.69` | Accept with flag | Write to KG as `:Event:LowConfidence` (excluded from default queries) |
| `< 0.30` | Quarantine | Write to staging table only. Do NOT create KG nodes. |
| `noise_flag = true` | Hold for review | Route to analyst queue. Create KG node only after human approval. |
| `duplicate_of != null` | Merge | Increment `corroboration_count` on the original signal. No new KG node. |

Quarantined signals are retained for 30 days in the staging table, then auto-purged unless manually promoted.

### 7.4 Normalization Strategy Across Sources

| Dimension | Normalization Rule |
|---|---|
| **Timestamps** | All converted to UTC ISO 8601 on ingestion. Source-local timestamps preserved in `extensions.original_timestamp`. |
| **Currency** | All monetary values normalized to USD. Original currency preserved in `extensions.original_currency` and `extensions.original_amount`. |
| **Entity names** | Fuzzy-matched against the KG entity registry. If match confidence > 0.85, auto-linked. Otherwise, queued for manual resolution. |
| **Severity** | All sources map to the 6-level `SignalSeverity` enum. Source-specific severity scales preserved in `extensions.source_severity`. |
| **Geographic codes** | Normalized to ISO 3166-1 alpha-2. GCC sub-region codes (e.g., `SA-RI` for Riyadh) follow ISO 3166-2. |
| **Signal types** | Mapped to a controlled vocabulary maintained in `signal_type_registry.yaml`. Unknown types default to `unknown_signal` and trigger an alert. |

---

## 8. Data Flow

```
Source (API/Webhook/Manual/Feed/Sensor)
  │
  ▼
Signal Gateway (FastAPI endpoint: POST /api/v1/signals/ingest)
  │  ← Schema validation (Pydantic MacroSignal)
  │  ← Confidence gate (quarantine < 0.30)
  │  ← Deduplication check (hash-based)
  ▼
Enrichment Pipeline (LangGraph stages)
  │  ← Geo enrichment (PostGIS reverse geocode)
  │  ← Entity linking (fuzzy match against KG registry)
  │  ← Source trust scoring
  │  ← Severity classification
  ▼
Knowledge Graph Writer (Neo4j)
  │  ← MERGE :Source, :Event, :Entity, :Tag nodes
  │  ← CREATE relationships with temporal properties
  │  ← SHA-256 audit hash on every write
  ▼
Event Bus (for downstream consumers)
  │  ← Simulation Engine trigger
  │  ← Alert Engine
  │  ← Feature Store update
  ▼
Observability (logging, metrics, audit trail)
```

---

## 9. Risk Register

| # | Failure Mode | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Schema version mismatch between producer and consumer | Medium | Signals silently dropped or mis-parsed | Version router + `schema_version` validation on every request |
| R2 | High-volume duplicate signals from same source | Medium | KG node bloat, inflated corroboration counts | SHA-256 dedup on `(source_id, signal_type, event_time, payload_hash)` |
| R3 | Low-confidence signals pollute KG | High | Degraded AI reasoning quality | Quarantine gate at confidence < 0.30; `:LowConfidence` label for 0.30–0.69 |
| R4 | Entity linking false positives | Medium | Wrong relationships in KG → wrong propagation paths | Confidence threshold (0.85) + human-in-the-loop queue for borderline matches |
| R5 | Extensions field abuse (large blobs, PII) | Low | Storage bloat, PDPL compliance violation | Max 10KB per extensions field; PII scanner on ingestion |
| R6 | Tenant data leak (wrong tenant_id) | Low | Severe — GCC regulatory exposure | Tenant_id enforced at API gateway + row-level Neo4j isolation |
| R7 | Stale signals (data_freshness_hours exceeded) | Medium | Outdated KG state | TTL-based auto-archival + staleness alerts |
| R8 | Source trust score drift | Low | Trusted source becomes unreliable silently | Monthly trust recalibration based on corroboration rates |

---

## 10. Observability Hooks

| Hook | Type | Trigger | Payload |
|---|---|---|---|
| `signal.ingested` | Metric (counter) | Every signal accepted | `{domain, source_id, severity}` |
| `signal.rejected` | Metric (counter) | Validation failure | `{reason, source_id}` |
| `signal.quarantined` | Metric (counter) | Confidence < 0.30 | `{signal_id, confidence_score}` |
| `signal.promoted` | Metric (counter) | Status → PROMOTED | `{signal_id, kg_node_id}` |
| `signal.duplicate_detected` | Metric (counter) | Dedup match found | `{signal_id, duplicate_of}` |
| `signal.enrichment_latency_ms` | Metric (histogram) | Enrichment pipeline complete | `{stage, duration_ms}` |
| `signal.lineage_hash` | Log (structured) | Every mutation | `{signal_id, hash, pipeline_version}` — SHA-256 audit trail |
| `signal.entity_link_confidence` | Metric (histogram) | Entity linking complete | `{entity_id, confidence}` |
| `extensions.promotion_candidate` | Alert | Extension key appears in >50% of domain signals | `{key, domain, frequency}` |

---

## 11. Decision Gate — What Must Be True Before Proceeding

Before building the next layer (Knowledge Graph Writer + Enrichment Pipeline), these conditions must be met:

- [ ] **Schema frozen:** `MacroSignal` v1.0.0 reviewed and approved by architecture board
- [ ] **Contract tests pass:** Pydantic model validates all 3 example payloads without error
- [ ] **KG mapping confirmed:** Neo4j node labels and relationship types agreed with graph team
- [ ] **Dedup strategy tested:** SHA-256 hash-based deduplication tested with 10K synthetic signals
- [ ] **Quarantine threshold calibrated:** 0.30 confidence threshold validated against historical signal quality data
- [ ] **Tenant isolation verified:** Multi-tenant `tenant_id` enforcement tested with cross-tenant query attempts
- [ ] **Audit trail verified:** SHA-256 lineage_hash computation matches expected outputs for all example payloads
- [ ] **Extensions policy documented:** Max size, PII scanning rules, and promotion threshold communicated to all signal producers
- [ ] **Observability pipeline connected:** All 8 metric/log hooks wired to monitoring stack

---

## 12. Implementation Sequence

| Step | Component | Owner | Dependencies | Estimated Effort |
|---|---|---|---|---|
| 1 | `MacroSignal` Pydantic schema (this deliverable) | Data Platform | None | ✅ Complete |
| 2 | Contract tests (`test_macro_signal_contracts.py`) | Data Platform | Step 1 | 1 day |
| 3 | FastAPI ingestion endpoint (`POST /api/v1/signals/ingest`) | API Team | Step 1 | 2 days |
| 4 | Signal type registry (`signal_type_registry.yaml`) | Data Platform | Step 1 | 1 day |
| 5 | Deduplication service (Redis hash lookup) | Pipeline Team | Step 3 | 2 days |
| 6 | Enrichment pipeline stages (LangGraph) | AI Team | Step 3, Step 5 | 5 days |
| 7 | Knowledge Graph Writer (Neo4j MERGE logic) | Graph Team | Step 6 | 3 days |
| 8 | Observability hooks + dashboards | SRE | Step 3 | 2 days |
| 9 | Integration test suite | QA | Steps 3–8 | 3 days |
| 10 | Tenant isolation penetration test | Security | Step 7 | 1 day |

---

*Document generated for Deevo Analytics — Impact Observatory | مرصد الأثر*
*Schema source of truth: `backend/src/schemas/macro_signal_schema.py`*
