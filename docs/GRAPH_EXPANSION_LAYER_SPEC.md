# Graph Expansion Layer — Architecture Specification

**طبقة التوسع البياني — مواصفات البنية**

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Layer** | Features → Models (Layer 2-3) |
| **Owner** | Graph Expansion Pipeline |
| **Files** | `graph_mapper.py`, `neo4j_graph_writer.py`, `graph_expansion_service.py`, `graph_expansion.py` (API) |
| **Date** | 2026-04-09 |

---

## 1. Architecture Decision

The Graph Expansion Layer sits between the MacroSignal ingestion endpoint and the Knowledge Graph persistence layer. It transforms each incoming signal into a rich, deterministic set of GraphNodes and GraphEdges — then writes them to both the in-memory GraphStore and Neo4j via idempotent MERGE operations.

The layer was designed as a pure-function mapper with a separate writer, rather than embedding transformation logic inside the existing `GraphBrainService.ingest()`. This separation allows dry-run previews, batch processing, unit testing of mapping logic without a graph store, and future AI-driven mapping augmentation.

---

## 2. Data Flow

```
MacroSignal (dict)
  │
  ▼
map_signal_to_graph()          ← Pure function, no side effects
  │  Returns MappingResult:
  │    nodes: List[GraphNode]
  │    edges: List[GraphEdge]
  │    decisions: List[MappingDecision]
  ▼
InMemoryGraphWriter            ← Persists to in-memory GraphStore
  │  Returns WriteResult:
  │    nodes_merged, edges_merged, errors
  ▼
Neo4jGraphWriter (optional)    ← Persists to Neo4j via MERGE
  │
  ▼
GraphExpansionResult           ← Combined output for API response
```

---

## 3. Mapping Logic — Signal → KG Structure

### 3.1 Core Mapping (every signal)

Every MacroSignal produces at minimum:

| Element | Node ID Pattern | Type | Relationship |
|---------|----------------|------|--------------|
| Signal node | `signal:{signal_id}` | `:Signal` | — |
| Event node | `event:{signal_id}` | `:Event` | `(:Signal)-[:TRIGGERED_BY]->(:Event)` |
| Source node | `source:{source_id}` | `:Organization` | `(:Source)-[:LINKED_TO]->(:Signal)` |
| Region node | `region:{code}` | `:Country` | `(:Event)-[:LOCATED_IN]->(:Region)` |
| Tag nodes | `tag:{name}` | `:RiskFactor` | `(:Event)-[:LINKED_TO]->(:Tag)` |
| Entity refs | `org:{id}`, `chokepoint:{id}`, etc. | varies | `(:Event)-[:AFFECTS\|MENTIONS]->(:Entity)` |
| Affected zones | `infra:{zone}` | `:Infrastructure` | `(:Event)-[:AFFECTS]->(:Infrastructure)` |
| Lineage | `signal:{parent_id}` | reference only | `(:Signal)-[:DERIVED_FROM]->(:Signal)` |

### 3.2 Macroeconomic Payload Mapping

| Element | Node ID | Relationship |
|---------|---------|--------------|
| Indicator | `indicator:{code}` | `(:Event)-[:AFFECTS]->(:Indicator)` |
| Sectors | `sector:{name}` | `(:Indicator)-[:AFFECTS]->(:Sector)` |

### 3.3 Insurance Payload Mapping

| Element | Node ID | Relationship |
|---------|---------|--------------|
| Line of Business | `lob:{lob}` | `(:Event)-[:AFFECTS]->(:LOB)` |
| Affected Orgs | `org:{ent_id}` | `(:Event)-[:AFFECTS]->(:Organization)` |
| Reinsurance Trigger | `risk_factor:reinsurance_trigger` | `(:Event)-[:TRIGGERED_BY]->(:RiskFactor)` |

### 3.4 Operational Payload Mapping

| Element | Node ID | Relationship |
|---------|---------|--------------|
| Infrastructure | `infra:{system_id}` | `(:Event)-[:AFFECTS]->(:Infrastructure)` |
| Upstream deps | `infra:{up_id}` | `(:Infrastructure)-[:DEPENDS_ON]->(:Infrastructure)` |
| Downstream | `infra:{down_id}` | `(:Infrastructure)-[:PROPAGATES_TO]->(:Infrastructure\|Organization)` |
| Flow types | `sector:{flow}` | `(:Infrastructure)-[:AFFECTS]->(:Sector)` |

### 3.5 Geopolitical Payload Mapping

| Element | Node ID | Relationship |
|---------|---------|--------------|
| Actors | `actor:{name}` | `(:Event)-[:INFLUENCES]->(:Actor)` |
| Trade Routes | `chokepoint:{route}` | `(:Event)-[:AFFECTS]->(:Chokepoint)` |

### 3.6 Cross-Entity Inference

The mapper generates inferred edges between sectors and regions when both are present: `(:Sector)-[:OPERATES_IN]->(:Country)`.

---

## 4. Example Neo4j Graph Output

For the Oil Price Shock signal (Example 1 from the schema spec):

```
(:Source {id:"source:reuters-eikon-feed", label:"Reuters Eikon"})
  -[:LINKED_TO {weight:0.92}]->
(:Signal {id:"signal:abc", signal_type:"oil_price_shock", severity_score:0.72})
  -[:TRIGGERED_BY {weight:1.0}]->
(:Event {id:"event:abc", event_type:"oil_price_shock", severity_score:0.72})
  -[:LOCATED_IN {weight:1.0}]->     (:Region {id:"region:SA"})
  -[:AFFECTS {weight:0.72}]->       (:Infrastructure {id:"infra:hormuz_strait"})
  -[:AFFECTS {weight:0.72}]->       (:Infrastructure {id:"infra:ras_tanura_terminal"})
  -[:AFFECTS {weight:0.72}]->       (:Indicator {id:"indicator:brent_crude_usd", value:72.6})
  -[:AFFECTS {weight:0.95}]->       (:Organization {id:"org:ent_aramco"})
  -[:LINKED_TO {weight:0.80}]->     (:Corridor {id:"chokepoint:node_hormuz_strait"})

(:Indicator {id:"indicator:brent_crude_usd"})
  -[:AFFECTS {weight:0.612}]->      (:Sector {id:"sector:energy"})
  -[:AFFECTS {weight:0.612}]->      (:Sector {id:"sector:maritime"})
  -[:AFFECTS {weight:0.612}]->      (:Sector {id:"sector:insurance"})
  -[:AFFECTS {weight:0.612}]->      (:Sector {id:"sector:banking"})

(:Sector {id:"sector:energy"})
  -[:OPERATES_IN {weight:0.6}]->    (:Region {id:"region:SA"})
```

**Validated counts:** 18 nodes, 21 edges, 20 mapping decisions.

---

## 5. Neo4j Cypher Patterns

All writes use MERGE for idempotency:

```cypher
-- Node MERGE (label from entity_type mapping)
MERGE (n:Event {id: $id})
SET n += $properties
RETURN n.id, CASE WHEN n.created_at IS NULL THEN 'created' ELSE 'updated' END

-- Relationship MERGE (type from relation_type mapping)  
MATCH (a {id: $source_id}), (b {id: $target_id})
MERGE (a)-[r:AFFECTS]->(b)
SET r += $properties
```

Entity type → Neo4j label mapping: Signal→Signal, Event→Event, Country→Region, Sector→Sector, Organization→Organization, Infrastructure→Infrastructure, Chokepoint→Corridor, Indicator→Indicator, RiskFactor→RiskFactor.

---

## 6. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/graph/expand` | Expand signal → KG (with persistence) |
| POST | `/api/v1/graph/expand/batch` | Batch expand (up to 100) |
| POST | `/api/v1/graph/expand/preview` | Dry-run mapping (no persistence) |
| GET | `/api/v1/graph/expand/stats` | Pipeline statistics |

All endpoints return `MappingDecision` logs in the response for full observability.

---

## 7. Extensibility

To add a new domain (e.g., `ClimatePayload`):

1. Implement `_map_climate_payload()` following the existing signature
2. Register in `PAYLOAD_MAPPERS["climate"] = _map_climate_payload`
3. No changes to core mapping, writer, or API routes

For future AI-driven mapping: the `MappingResult` can be post-processed by an LLM agent to suggest additional entity links, resolve fuzzy entity matches, or propose new relationship types — all without modifying the deterministic base mapper.

---

## 8. Files Delivered

| File | Purpose |
|------|---------|
| `backend/src/graph_brain/graph_mapper.py` | Pure mapping: MacroSignal → GraphNode/GraphEdge |
| `backend/src/graph_brain/neo4j_graph_writer.py` | Neo4j MERGE writer + InMemoryGraphWriter |
| `backend/src/graph_brain/graph_expansion_service.py` | Orchestration: mapper + writer + stats |
| `backend/src/api/v1/graph_expansion.py` | FastAPI routes for expand/preview/batch/stats |

---

*Document generated for Deevo Analytics — Impact Observatory | مرصد الأثر*
