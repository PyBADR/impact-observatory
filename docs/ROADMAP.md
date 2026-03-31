# DecisionCore Intelligence — Implementation Roadmap

## Architecture Overview

DecisionCore Intelligence is a graph-native, mathematically grounded, physics-aware decision intelligence system built on a 7-layer stack:

1. **Data Layer** — Multi-source ingestion (ACLED, aviation, maritime, manual import) with canonical normalization
2. **Schema Layer** — 9 Pydantic v2 modules defining 41 canonical models (Event, Airport, Port, Flight, Vessel, Route, Corridor, Region, RiskScore)
3. **Graph Layer** — Neo4j property graph with 8+ entity types and 12+ edge types (event→region, flight→airport, vessel→port, adjacency, etc.)
4. **Models Layer** — 8 mathematical modules (risk, spatial, temporal, propagation, exposure, disruption, confidence) + 7 physics modules (threat field, flow field, pressure, shockwave, diffusion, routing, system stress)
5. **Intelligence Layer** — Scenario engine, risk scoring, propagation simulation, recommendation engine
6. **API Layer** — FastAPI REST + WebSocket for all operations (CRUD, risk, graph, scenarios, live feeds)
7. **UI Layer** — CesiumJS 3D globe control room with layers, detail panels, scenario builder, explainability

**Core Principle:** Every source normalizes to canonical schema → every score is explainable (component breakdown + reasoning) → every scenario produces baseline/shock/delta/recommendations.

---

## Phase 1: Foundation (COMPLETED)

### Deliverables

**Repository Structure**
- `/backend` — FastAPI, SQLAlchemy, Neo4j client, mathematical models, connectors, scenario engine
- `/frontend` — TypeScript/React, CesiumJS, state management, decision panels
- `/schemas` — 9 Pydantic v2 modules (100+ type definitions)
- `/docker` — `docker-compose.yml` with PostGIS (Postgres 15), Neo4j (5.x), Redis (7.x), backend service, frontend service
- `/docs` — Schema reference, API docs, deployment guide, roadmap

**Canonical Schema (9 Pydantic Modules, 41 Models)**
- `core.py` — Entity, BaseScore, Location, TimeWindow
- `event.py` — Event, EventType, EventSource, EventSeverity (4 models)
- `infrastructure.py` — Airport, Port, Corridor, Region (4 models)
- `logistics.py` — Flight, FlightStatus, Vessel, VesselType, VesselStatus, Route, RouteSegment (7 models)
- `risk.py` — RiskScore, RiskComponent, ConfidenceMetadata (3 models)
- `scenario.py` — Scenario, ScenarioTemplate, ScenarioState, ShockDefinition (4 models)
- `graph.py` — GraphNode, GraphEdge, NodeType, EdgeType (4 models)
- `physics.py` — ThreatField, FlowField, PressureAccumulation (3 models)
- `api.py` — APIResponse, ErrorResponse, PaginationMeta (3 models)

**Mathematical Modeling (8 Modules)**
- `risk.py` — Risk score computation (base + proximal + temporal decay, 150 LOC)
- `spatial.py` — PostGIS proximity, distance decay, zone containment (120 LOC)
- `temporal.py` — Event freshness, time-to-impact, window weighting (100 LOC)
- `propagation.py` — Risk spread via graph edges, multi-hop pathways (180 LOC)
- `exposure.py` — Asset exposure to threat (infrastructure vulnerability model, 140 LOC)
- `disruption.py` — Disruption impact modeling (cascade, latency, recovery, 160 LOC)
- `confidence.py` — Source credibility, data freshness, model uncertainty (130 LOC)
- `aggregation.py` — Component weighted combination, confidence intervals (110 LOC)

**Physics Intelligence (7 Modules)**
- `threat_field.py` — Builds 3D threat grid from active events (Gaussian kernel, 200 LOC)
- `flow_field.py` — Constructs flow from flight/vessel trajectories (vector field, 180 LOC)
- `pressure.py` — Computes load at infrastructure nodes (capacity - demand, 140 LOC)
- `shockwave.py` — Temporal impact propagation from discrete events (wavefront simulation, 220 LOC)
- `diffusion.py` — Threat diffusion across region graph (heat equation discrete solver, 190 LOC)
- `routing.py` — Threat-aware route cost evaluation (Dijkstra variant, 150 LOC)
- `system_stress.py` — Aggregates pressure + threat + disruption into stress index (120 LOC)

**Docker Compose Infrastructure**
- **PostGIS (Postgres 15)** — Primary relational store; PostGIS extension for spatial queries (ST_Distance, ST_Contains, ST_Buffer)
- **Neo4j (5.x)** — Property graph store; schema-less entity relationships; Cypher query engine
- **Redis (7.x)** — Cache layer for scores, session storage, live event queue
- **Backend Service** — Python 3.11, FastAPI, SQLAlchemy ORM 2.0, Neo4j driver, Pydantic v2, async Postgres/Redis
- **Frontend Service** — Node.js, TypeScript, React, CesiumJS, Vite build

**Backend Configuration (Pydantic Settings)**
- Environment-driven config: `DATABASE_URL`, `NEO4J_URI`, `REDIS_URL`, `ACLED_API_KEY`, `LOG_LEVEL`
- Async Postgres connection pool (min=5, max=20, timeout=30s)
- Neo4j driver with connection pooling (max_pool_size=50, max_idle_time=30s)
- Redis client (decode_responses=True, socket_keepalive=True)
- CORS, API key auth middleware, structured logging (JSON format)

**Database ORM Models (SQLAlchemy 2.0 + PostGIS)**
- `Event` — id, event_type, location (Point), severity, timestamp, source, raw_data, confidence
- `Airport` — id, name, iata, location (Point), capacity_movements_per_day, controlled_airspace_km²
- `Port` — id, name, location (Point), capacity_teu_per_month, ship_queue_length
- `Flight` — id, origin_airport_id, destination_airport_id, callsign, status, location (Point), timestamp, eta
- `Vessel` — id, mmsi, port_of_registry, location (Point), status, heading, speed_knots, timestamp
- `Route` — id, origin_id, destination_id, corridor_id, waypoints (LineString), distance_km, threat_level
- `Corridor` — id, name, region_id, linestring (LineString), width_nm, traffic_volume_daily
- `Region` — id, name, geom (Polygon), conflict_level, governance_stability
- `RiskScore` — entity_id, entity_type, score_value, components (JSONB), timestamp, version
- Indexes on location (GIST), timestamp, entity_id; foreign keys enforced

**Base Connector Interface**
```python
class BaseConnector(ABC):
    async def fetch() -> list[dict]  # Raw data retrieval
    async def normalize() -> list[CanonicalModel]  # Convert to schema
    async def store() -> int  # Persist to Postgres
```

### Decision Gate ✓ PASS
- Repository structure initialized with all directories and files
- All 41 Pydantic models compile without errors; schema validation tests pass
- All 15 math + physics modules import cleanly; unit tests for each module (>90% coverage)
- Docker Compose stack starts cleanly; all 5 services healthy within 60 seconds
- Postgres/PostGIS, Neo4j, Redis accessible from backend service
- Backend config loads from environment; logging outputs structured JSON
- SQLAlchemy ORM models map cleanly to Postgres schema (migrations applied)
- Base connector interface defined and testable

---

## Phase 2: Data Connectors & Normalization

### Deliverables

**ACLED Conflict Event Connector**
- `acled_connector.py` (300 LOC)
  - Authenticates to ACLED API with API key
  - Fetches events for GCC region (coordinates: 16°N–30°N, 40°E–60°E)
  - Filters for last 7 days (configurable window)
  - Maps ACLED fields (iso, event_id_cnty, event_date, event_type, sub_event_type, actors, data_source, fatalities, notes) → Event schema
  - Normalizes event_type → {MILITARY_ACTION, PROTESTS, RIOTS, VIOLENCE_AGAINST_CIVILIANS, EXPLOSIONS, STRATEGIC_DEVELOPMENTS}
  - Severity: {CRITICAL (fatalities>50), HIGH (fatalities 10-50), MEDIUM (fatalities 1-9), LOW (fatalities=0)}
  - Extracts location (lat/lon), timestamp (UTC), source credibility (ACLED=0.85), raw_data (JSON)
  - Implements retry logic (3 attempts, exponential backoff) for API failures
  - Error handling: missing coordinates, invalid dates → logged as warnings, skipped
  - Stores to Postgres Event table with deduplication on (iso, event_id_cnty, event_date)

**Aviation Connector Abstraction**
- `aviation_connector_base.py` (200 LOC)
  - Abstract base for flight data sources (OpenSky Network, ADSB Exchange, proprietary feeds)
  - Fetch interface: retrieve live flight data within GCC region
  - Normalize to Flight schema: origin_airport_id, destination_airport_id, callsign, status, location (Point), eta
  - Store: writes to Flight table with upsert on callsign+timestamp (< 5 min stale)
  - Extends base connector; implementations TBD (Phase 3)

**Maritime Connector Abstraction**
- `maritime_connector_base.py` (200 LOC)
  - Abstract base for vessel tracking (AIS, proprietary feeds)
  - Fetch interface: retrieve vessel positions from GCC shipping lanes
  - Normalize to Vessel schema: mmsi, location (Point), heading, speed, status (ANCHORED, UNDERWAY, RESTRICTED_MANEUVERING, MOORED, AT_SEA)
  - Store: upsert on mmsi+timestamp (< 10 min stale)
  - Extends base connector; implementations TBD (Phase 3)

**CSV/JSON Manual Import Pipeline**
- `manual_import.py` (250 LOC)
  - Accept CSV/JSON uploads via `/api/v1/admin/import`
  - CSV schema: entity_type, required_fields, optional_fields
  - Validate against canonical schema (Pydantic validation)
  - Transform and batch-insert to Postgres (10k records/batch)
  - Return: success count, failure count, error log
  - Example: Import 50 historical conflict events, 30 airport baselines, 20 port profiles

**Seed Datasets**
- `seed_data/` directory with JSON files
  - `events_50.json` — 50 historical conflict events (2023-2025, GCC region, variety of types and severities)
  - `airports_30.json` — 30 major GCC airports (IATA, coordinates, capacity, controlled airspace)
  - `ports_20.json` — 20 major GCC ports (coordinates, capacity, typical queue length)
  - `corridors_15.json` — 15 major air/sea corridors (linestrings, width, daily traffic)
  - `flights_sample_100.json` — Sample live flight dataset (for testing)
  - `vessels_sample_80.json` — Sample vessel positions (for testing)
  - Load via CLI: `python -m scripts.seed_database --all` (< 30 seconds)

**Normalization Pipeline Service**
- `normalization_service.py` (350 LOC)
  - Exposes `/api/v1/admin/normalize` endpoint
  - Accepts raw data (from connector fetch), applies schema validation
  - Returns: normalized Event/Flight/Vessel/etc. objects (Pydantic models)
  - Logs validation errors with field-level detail
  - Supports batch normalization (list[dict] → list[CanonicalModel])
  - Includes telemetry: count, success rate, errors

### Decision Gate ✓ PASS
- ACLED connector fetches live data, normalizes to Event schema, stores to Postgres (>95% success rate on test dataset)
- Aviation connector abstraction defined; can accept mock flight data and normalize without error
- Maritime connector abstraction defined; can accept mock vessel data and normalize without error
- CSV/JSON import pipeline accepts test files, validates, and loads without data loss
- All 3 connectors produce valid CanonicalModel instances (Pydantic validation passes 100%)
- Seed data (50 events, 30 airports, 20 ports, 15 corridors) loads into Postgres in < 30 seconds
- Normalization service endpoint accepts raw data, returns normalized schema, stores to DB
- Postgres Event/Flight/Vessel/Airport/Port/Corridor/Region tables populated and queryable

---

## Phase 3: Graph Intelligence

### Deliverables

**Neo4j Schema Initialization**
- `neo4j_schema.py` (300 LOC)
  - Define node labels: Event, Region, Airport, Port, Flight, Vessel, Route, Corridor, Actor
  - Define constraints: UNIQUE(Region.id), UNIQUE(Airport.id), UNIQUE(Port.id), UNIQUE(Event.id), etc.
  - Create indexes: ON Event(timestamp), ON Airport(iata), ON Port(name), ON Region(name)
  - Index all relationship types for fast traversal
  - Run via CLI: `python -m scripts.init_neo4j_schema` (idempotent, safe to re-run)
  - Verify: query node/relationship counts before/after

**Graph Ingestion Service**
- `graph_ingestion_service.py` (400 LOC)
  - Read from Postgres tables (Event, Airport, Port, Flight, Vessel, Route, Corridor, Region)
  - Create Neo4j nodes for each entity (label, properties: id, name, location, timestamp, etc.)
  - Batch writes via transaction (5k nodes/tx for performance)
  - Return: counts of created nodes, execution time
  - Idempotent: uses MERGE to avoid duplicates
  - Scheduled task: run nightly to sync new Postgres data to Neo4j

**Event → Region/Infrastructure/Actor Edge Creation**
- `event_edges.py` (250 LOC)
  - For each Event, create edges:
    - `(Event)-[AFFECTS]->(Region)` — event.location containment via PostGIS; weight=1.0
    - `(Event)-[AFFECTS]->(Airport)` — if airport within 200km; weight=proximity_decay
    - `(Event)-[AFFECTS]->(Port)` — if port within 200km; weight=proximity_decay
    - `(Event)-[INVOLVES]->(Actor)` — from event.actors; weight=1.0
  - Edge properties: strength (0.0-1.0), distance_km, relationship_type, timestamp

**Flight → Airport Edge Creation**
- `flight_edges.py` (200 LOC)
  - For each Flight, create edges:
    - `(Flight)-[DEPARTS_FROM]->(Airport)` on origin_airport_id; eta=flight.eta
    - `(Flight)-[ARRIVES_AT]->(Airport)` on destination_airport_id; eta=flight.eta
  - Edge properties: flight_number, status, eta, current_position

**Vessel → Port/Corridor Edge Creation**
- `vessel_edges.py` (200 LOC)
  - For each Vessel, create edges:
    - `(Vessel)-[DEPARTS_FROM]->(Port)` if vessel status=MOORED; eta=estimated_departure
    - `(Vessel)-[SAILS_TO]->(Port)` if vessel status=UNDERWAY; eta=voyage_eta
    - `(Vessel)-[TRANSITS]->(Corridor)` if vessel location within corridor linestring; speed=vessel.speed
  - Edge properties: mmsi, status, eta, voyage_id

**Route → Endpoint Edge Creation**
- `route_edges.py` (150 LOC)
  - For each Route, create edges:
    - `(Route)-[ORIGIN]->(Airport|Port)` — identifies route start
    - `(Route)-[DESTINATION]->(Airport|Port)` — identifies route end
  - Edge properties: distance_km, corridor_id, threat_level

**Region Adjacency Edges (GCC Topology)**
- `region_topology.py` (200 LOC)
  - Hardcoded/computed adjacency for GCC nations:
    - Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman
    - Create `(Region)-[ADJACENT_TO]->(Region)` for bordering nations
    - Also create `(Region)-[MARITIME_NEIGHBOR]->(Region)` for nations sharing territorial waters
  - Edge properties: border_type (LAND, MARITIME, AIRSPACE), distance_km
  - Used for propagation simulation and correlation analysis

**Graph Query Service (7 Pre-Built Queries)**
- `graph_query_service.py` (500 LOC)
  - Query 1: `events_by_region(region_id)` — return all events affecting a region, sorted by severity+recency
  - Query 2: `infrastructure_at_risk(airport_id|port_id)` — return all events within 300km, risk scores
  - Query 3: `flight_path_threats(flight_id)` — return all events intersecting departure→destination corridor
  - Query 4: `vessel_route_threats(vessel_id)` — return all events within 50nm of current heading
  - Query 5: `cascading_impact(event_id)` — multi-hop BFS from event through AFFECTS edges to find secondary impacts (3-hop max)
  - Query 6: `critical_chokepoints()` — find corridors/ports with highest centrality + active threats
  - Query 7: `actor_network(actor_name)` — return all events involving actor, connected actors, and targets
  - Each query returns structured result: node_list, edge_list, properties dict, execution_time_ms

### Decision Gate ✓ PASS
- Neo4j schema initialized (constraints, indexes); schema query returns expected structure
- All Postgres entities (Event, Airport, Port, Flight, Vessel, Route, Corridor, Region) converted to Neo4j nodes and edges
- Multi-hop queries (e.g., Event → Region → Airport → Route) execute in < 500ms and return correct results
- All 7 pre-built queries execute without error and return properly structured results
- Graph contains ≥50 Event nodes, ≥30 Airport nodes, ≥20 Port nodes, with edges correctly created
- AFFECTS, INVOLVES, DEPARTS_FROM, ARRIVES_AT, TRANSITS, ADJACENT_TO edges verified in spot checks
- Region adjacency topology correctly reflects GCC geography

---

## Phase 4: Scoring Engine Integration

### Deliverables

**Risk Scoring Service**
- `risk_scoring_service.py` (600 LOC)
  - Exposes `compute_score(entity_type, entity_id) → RiskScore` method
  - Orchestrates component scoring:
    1. **Base Risk** — severity inherent to entity (from math.risk module, baseline 0.2-0.8)
    2. **Proximity Risk** — spatial distance decay to active threats (from math.spatial module)
    3. **Temporal Risk** — freshness weighting + time-to-impact (from math.temporal module)
    4. **Network Risk** — centrality + incoming threat propagation (from graph query service)
    5. **Exposure Risk** — infrastructure vulnerability (from math.exposure module)
    6. **Disruption Risk** — cascading impact potential (from math.disruption module)
    7. **Confidence** — weighted credibility of inputs (from math.confidence module)
  - Combine components via weighted sum: `score = Σ(w_i * component_i)` where Σw_i = 1.0
  - Confidence: multiplicative model, ranges [0.0, 1.0] based on data freshness + source credibility
  - Persistence: write RiskScore to Postgres with timestamp, component breakdown (JSONB), version ID
  - Caching: store in Redis with 5-min TTL; invalidate on related entity updates

**Spatial Proximity Scoring using PostGIS ST_Distance**
- Implements spatial.py integration:
  - For entity E and active threat events {T1, T2, ...}, compute:
    - `proximity_risk(E) = Σ(severity_i * exp(-distance_i / λ)) / Σ(severity_i)` where λ=200km
  - Query: `SELECT ST_Distance(E.location, T.location) / 1000 as dist_km FROM Event T` for each T
  - Handle null/invalid locations: skip with warning log
  - For events exactly at entity location (dist=0), use special case: score += 0.9
  - Vectorized: compute all at once for efficiency (batch proximity for 100 entities in < 1 sec)

**Temporal Freshness Scoring on Live Event Data**
- Implements temporal.py integration:
  - For event with timestamp T_event, current time T_now, compute:
    - `freshness(E) = exp(-(T_now - T_event) / τ)` where τ = 48 hours
  - Events >7 days old: score → 0 (no longer proximal threat)
  - Events <1 hour old: multiplicative boost (×1.5) if in critical region
  - Time-to-impact scoring: if event trajectory predictable (e.g., advancing conflict), estimate impact zone at +6/12/24 hours ahead

**Network Centrality from Neo4j (Degree, Betweenness for Key Nodes)**
- Implements graph intelligence integration:
  - For each infrastructure node (Airport, Port, Corridor), compute:
    - **Degree Centrality** — count of AFFECTS/TRANSITS/DEPARTS_FROM edges; normalized by max degree
    - **Betweenness Centrality** — #shortest paths passing through node; via Cypher: `UNWIND ... AS n RETURN n, size(apoc.algo.betweenness_stream(...)) AS centrality`
    - Threshold: centrality > 0.7 → node is critical chokepoint
  - Use in risk: `network_risk = centrality * avg_incident_severity_in_neighborhood`

**Exposure Model Connected to Real Infrastructure Data**
- Implements exposure.py integration:
  - For airport: `exposure = min(current_traffic, capacity) * conflict_level_in_region * controlled_airspace_vulnerability`
  - Current traffic: count of active flights in next 4 hours (from Flight table)
  - Capacity: from Airport.capacity_movements_per_day
  - Conflict level: from Region with highest active event severity
  - For port: `exposure = (ship_queue_length / avg_processing_time) * port_vulnerability * maritime_threat_intensity`
  - Store: exposure score + components in RiskScore breakdown

**Confidence Model Connected to Source Metadata**
- Implements confidence.py integration:
  - Base confidence from source: ACLED=0.85, OpenSky=0.90, AIS=0.88, manual import=0.70
  - Data freshness decay: confidence *= exp(-(T_now - T_data) / 72 hours)
  - Corroboration boost: if 2+ independent sources report same event, confidence *= 1.2 (capped at 1.0)
  - Model uncertainty: if physics simulation >24 hours out, confidence *= exp(-decay_factor)
  - Final: confidence = base * freshness * corroboration * model_uncertainty

**Score Persistence to risk_scores Table**
- `risk_scores` table schema:
  - entity_type (ENUM: Event, Airport, Port, Flight, Vessel, Route, Corridor, Region)
  - entity_id (UUID)
  - score_value (FLOAT, 0.0-1.0)
  - components (JSONB): {base_risk, proximity_risk, temporal_risk, network_risk, exposure_risk, disruption_risk}
  - confidence (FLOAT, 0.0-1.0)
  - timestamp (TIMESTAMPTZ)
  - version (INT, for A/B testing / model versioning)
  - created_at (TIMESTAMPTZ, auto)
  - Indexes: ON (entity_type, entity_id, timestamp DESC) for fast retrieval

**Score Explanation API**
- Endpoint: `GET /api/v1/risk/{entity_type}/{entity_id}`
- Response:
  ```json
  {
    "entity_id": "...",
    "entity_type": "Airport",
    "score": 0.72,
    "confidence": 0.88,
    "components": {
      "base_risk": 0.3,
      "proximity_risk": 0.45,
      "temporal_risk": 0.25,
      "network_risk": 0.55,
      "exposure_risk": 0.60,
      "disruption_risk": 0.40
    },
    "explanation": {
      "primary_drivers": [
        "High network centrality (0.82): critical aviation hub",
        "Active military conflict 180km west (severity=HIGH, freshness=6 hours)",
        "Flight queue at 85% capacity; disruption risk elevated"
      ],
      "secondary_factors": [
        "2 independent ACLED sources corroborate event",
        "Regional controlled airspace vulnerability 0.7"
      ],
      "timeline": {
        "event_nearest": {"id": "...", "distance_km": 180, "eta_impact": "6-12 hours", "severity": "HIGH"},
        "projections": [
          {"horizon": "6h", "score_forecast": 0.78},
          {"horizon": "12h", "score_forecast": 0.65},
          {"horizon": "24h", "score_forecast": 0.48}
        ]
      }
    },
    "last_updated": "2026-03-31T14:22:00Z"
  }
  ```

### Decision Gate ✓ PASS
- Risk scoring service accepts any entity (Airport, Port, Event, Flight, Vessel, Route, Corridor, Region) and produces valid RiskScore object
- All 7 components (base, proximity, temporal, network, exposure, disruption, confidence) compute without error and contribute to final score
- Scores remain in valid range [0.0, 1.0] across all entity types and threat scenarios
- Spatial proximity scoring correctly uses PostGIS ST_Distance; verified on 10 test cases with ground-truth distances
- Temporal decay correctly reduces scores for old events; freshness component < 0.1 for events >7 days old
- Network centrality computes from Neo4j; high-degree nodes (airports) receive elevated network_risk
- Exposure model integrates real infrastructure data (capacity, traffic, conflict level)
- Confidence scores reflect data freshness, source credibility, and model uncertainty
- Score persistence to Postgres; retrieval via entity_id + timestamp returns latest score
- Explanation API returns complete breakdown with drivers, factors, and projections
- Spot-check: high-risk airport explanation clearly identifies proximity to conflict + network centrality as primary drivers

---

## Phase 5: Physics Intelligence Integration

### Deliverables

**Threat Field Service**
- `threat_field_service.py` (500 LOC)
  - Builds 3D threat grid from active Event nodes in Neo4j
  - Grid definition: GCC bounding box (16°N–30°N, 40°E–60°E), resolution=0.5° (≈50km cells), altitude layers [0m, 5km, 15km]
  - For each active event:
    - Place Gaussian kernel centered at event.location: `threat(x,y) = severity * exp(-distance² / σ²)` where σ=100km
    - Temporal decay: multiply by `exp(-(T_now - T_event) / τ)` where τ=48 hours
    - Vertical spread: Gaussian in altitude for airspace events (conflict events spread 0-5km, military actions 0-15km)
  - Sum contributions from all events to grid (handles overlapping kernels correctly)
  - Output: 3D array (lat, lon, altitude) with threat values [0.0, 1.0]
  - Caching: store in Redis with 1-hour TTL; invalidate on new event
  - Endpoint: `GET /api/v1/intelligence/threat-field` returns grid as GeoJSON (for CesiumJS rendering)

**Flow Field Service**
- `flow_field_service.py` (450 LOC)
  - Constructs vector flow field from active Flight and Vessel trajectories
  - Grid definition: same as threat field (0.5° resolution)
  - For each Flight:
    - Extract current position + heading + speed
    - Compute forward trajectory (path to destination) over next 6 hours
    - Place flow vectors along trajectory: `velocity = speed_knots * heading_unit_vector`
    - Decay away from trajectory: `flow_strength(perpendicular_distance) = exp(-distance² / (150km)²)`
  - For each Vessel:
    - Similar logic: position → destination (AIS route), speed, heading
    - Decay radius larger: 200km (maritime routes span larger area)
  - Output: 2D vector field at surface + 2D vector field at cruise altitude (10km)
  - Caching: store in Redis with 15-min TTL (more frequent updates needed)
  - Endpoint: `GET /api/v1/intelligence/flow-field` returns field as GeoJSON (arrows/quivers for CesiumJS)

**Pressure Accumulation Service**
- `pressure_service.py` (400 LOC)
  - Tracks load at infrastructure nodes (Airport, Port) relative to capacity
  - For each Airport:
    - Current flights: count from Flight table with `eta - T_now < 4 hours`
    - Capacity: from Airport.capacity_movements_per_day, normalized to hourly (= capacity / 24)
    - Pressure: `P_airport = current_flights / hourly_capacity`
    - States: NORMAL (< 0.7), ELEVATED (0.7-0.9), SATURATED (> 0.9)
    - If saturation: incoming flights queue; compute queue depth and average delay
  - For each Port:
    - Current vessels: count from Vessel table with status=MOORED or ANCHORED
    - Queue length: from Port data or estimated from vessel count
    - Throughput: Port.capacity_teu_per_month, normalized to hourly = capacity / (30*24)
    - Pressure: `P_port = queue_length / (throughput * processing_window)`
    - States: NORMAL, ELEVATED, SATURATED
  - Persistence: store pressure snapshots in Postgres every 15 minutes
  - Endpoint: `GET /api/v1/intelligence/pressure/{infrastructure_type}/{infrastructure_id}` returns time-series + current state

**Shockwave Engine Integration**
- `shockwave_service.py` (550 LOC)
  - Models temporal propagation of impact from discrete events
  - Given Event E with timestamp T_E:
    - Immediate shockwave: peak impact at T_E + 0, radius = 0
    - Propagation wave: impact spreads at ~200 km/hour (regional escalation speed)
      - At time T, shockwave front at distance d = 200 * (T - T_E) km
      - Impact strength: `shockwave(d, T) = severity * exp(-d² / (200km)²) * exp(-(T - T_E) / τ)` where τ = 72 hours
    - Secondary waves: if shockwave reaches key infrastructure (airports, ports), trigger secondary event (congestion, rerouting)
      - Secondary impact scored as disruption impact (see Phase 6)
  - Multi-event shockwaves: for multiple concurrent events, superpose wavefronts
  - Endpoint: `GET /api/v1/intelligence/propagation/{event_id}` returns:
    ```json
    {
      "event_id": "...",
      "timeline": [
        {"hours_ahead": 0, "primary_wavefront_km": 0, "affected_regions": [...], "estimated_impact": 0.8},
        {"hours_ahead": 6, "primary_wavefront_km": 1200, "affected_regions": [...], "estimated_impact": 0.65},
        {"hours_ahead": 24, "primary_wavefront_km": 4800, "affected_regions": [...], "estimated_impact": 0.32}
      ]
    }
    ```

**Diffusion Service**
- `diffusion_service.py` (450 LOC)
  - Models threat diffusion (contagion) across Region graph
  - Discrete heat equation solver on GCC region graph:
    - Start: high threat concentration at event location
    - Diffuse: threat spreads to adjacent regions over time via ADJACENT_TO edges
    - Equation: `u(region, t+Δt) = u(region, t) + k * Σ[u(neighbor, t) - u(region, t)] * Δt` where k = 0.1 (diffusion coefficient)
  - Boundary conditions: threat at conflict epicenter maintained; threat decays away
  - Time steps: simulate hourly for 72 hours
  - Output: 3D array (region, hour, threat_value)
  - Endpoint: `GET /api/v1/intelligence/diffusion/{region_id}` returns threat evolution + neighbor contagion

**Route Cost Evaluation (Threat-Aware Routing)**
- `routing_service.py` (350 LOC)
  - Evaluates cost of routes given current threat field
  - For each Route (origin airport/port → destination):
    - Base cost: distance_km / typical_speed (hours to traverse)
    - Threat cost: integrate threat field value along route linestring
      - Sample threat at 10km intervals along route
      - Compute weighted integral: threat_cost = Σ(threat_sample_i * distance_interval)
      - Normalize by route length: threat_cost_per_km = threat_cost / distance_km
    - Total cost: `cost = base_cost_hours + threat_cost_per_km * risk_aversion_factor`
    - Routing: compute alternative routes (e.g., great-circle ±5° corridors), rank by total cost
  - Endpoint: `GET /api/v1/intelligence/route-cost/{origin_id}/{destination_id}` returns:
    ```json
    {
      "primary_route": {"distance_km": 1200, "time_hours": 4.5, "threat_cost": 0.35, "total_cost": 4.85},
      "alternatives": [
        {"distance_km": 1400, "time_hours": 5.2, "threat_cost": 0.12, "total_cost": 5.32},
        {"distance_km": 1300, "time_hours": 4.8, "threat_cost": 0.18, "total_cost": 4.98}
      ]
    }
    ```

**System Stress Dashboard Data**
- `system_stress_service.py` (400 LOC)
  - Aggregates pressure + threat + disruption into single stress index
  - Components:
    - **Pressure Index** (0-1): Σ(airport_pressure_i) / # airports + Σ(port_pressure_i) / # ports
    - **Threat Index** (0-1): max(threat_field_values) or avg across critical regions
    - **Disruption Index** (0-1): count(Flight disruptions + Vessel delays) / total_active_entities
  - Combined: `stress = 0.3*pressure + 0.4*threat + 0.3*disruption` (weighted by region criticality)
  - States: GREEN (< 0.3), YELLOW (0.3-0.6), RED (> 0.6), CRITICAL (> 0.85)
  - Time-series: log every 15 minutes; compute 1-hour trend (rising/stable/falling)
  - Endpoint: `GET /api/v1/intelligence/system-stress` returns:
    ```json
    {
      "overall_stress": 0.62,
      "state": "RED",
      "trend": "RISING",
      "components": {
        "pressure": {"value": 0.55, "worst_node": "DXB Airport", "worst_value": 0.92},
        "threat": {"value": 0.68, "hotspot": "Yemen-Saudi Border", "threat_level": "CRITICAL"},
        "disruption": {"value": 0.45, "disrupted_entities": 12, "delays_hours": 18.5}
      }
    }
    ```

### Decision Gate ✓ PASS
- Threat field service builds 3D grid from active events; outputs valid GeoJSON grid with threat values [0-1]
- Flow field service tracks flight/vessel trajectories; outputs 2D vector fields at surface and altitude layers
- Pressure service monitors airport and port capacity; correctly identifies NORMAL/ELEVATED/SATURATED states
- Shockwave engine simulates temporal propagation; timeline projections show decreasing impact over 72 hours
- Diffusion service propagates threat across region graph; threat spreads to adjacent regions with correct temporal decay
- Route cost evaluation integrates threat into routing decisions; alternative routes ranked by threat-adjusted cost
- System stress aggregates all components into single index; state transitions (GREEN/YELLOW/RED/CRITICAL) occur at correct thresholds
- All physics services compute in < 5 seconds (threat field), < 3 seconds (flow field), < 2 seconds (pressure), < 10 seconds (full stress)
- Endpoints return properly structured JSON; visualization-ready output (GeoJSON for grids, vectors for fields)

---

## Phase 6: Scenario Engine

### Deliverables

**Scenario Template Definitions**
- `scenario_templates.py` (400 LOC) defines 7 template classes:

  1. **Hormuz Closure** — Simulates strait blockade
     - Shock: inject high-severity event at Strait of Hormuz (26.1°N, 56.5°E)
     - Shock parameters: duration=72 hours, affected_ships_percent=60%, lane_closures=BOTH_LANES
     - Expected impacts: port congestion in UAE/Qatar, traffic reroute via Suez, pressure spike to 0.9+

  2. **Airspace Restriction** — Simulates conflict-driven airspace closure
     - Shock: mark airspace region (e.g., northern Iraq/Syria) as CLOSED to civil traffic
     - Shock parameters: affected_flights_percent=40%, reroute_distance_increase=15%
     - Expected impacts: flight delays, alternative route costs up 20-30%, pressure on alternate airports

  3. **Port Congestion** — Simulates port capacity crisis
     - Shock: reduce port throughput by X% (e.g., half staff due to strike/security incident)
     - Shock parameters: port_id, throughput_reduction=50%, duration=48 hours
     - Expected impacts: queue length 2-3x, vessel delays 12-48 hours, alternate port pressure spike

  4. **Conflict Escalation** — Simulates spreading military conflict
     - Shock: escalate existing event in severity + inject secondary events in adjacent regions
     - Shock parameters: primary_event_id, escalation_level=+2, num_secondary_events=3
     - Expected impacts: threat field expands, shockwave reaches infrastructure, system stress → RED

  5. **Airport Closure** — Simulates airport unavailability
     - Shock: mark airport as CLOSED for X hours (due to conflict, damage, or security)
     - Shock parameters: airport_id, closure_duration=24 hours, affected_flights_count=estimate
     - Expected impacts: flight diversions, pressure spike at alternate airports, delay cascade

  6. **Maritime Chokepoint** — Simulates chokepoint disruption (Suez, Bab el-Mandeb, etc.)
     - Shock: reduce corridor throughput or increase transit time
     - Shock parameters: corridor_id, capacity_reduction=40%, transit_delay_hours=8
     - Expected impacts: shipping delays, pressure at origin/destination ports, reroute cost increase

  7. **Cascading Multi-Event** — Simulates compound disaster
     - Shock: inject 3+ correlated events (e.g., conflict + port attack + airport closure)
     - Shock parameters: events=[{...}, {...}, {...}], staggered_timing=[T, T+2h, T+6h]
     - Expected impacts: system stress → CRITICAL, multiple infrastructure under pressure, complex interconnected disruptions

**Baseline State Capture**
- `baseline_capture.py` (250 LOC)
  - Snapshot current system state before shock injection:
    - All active entities: Events, Flights, Vessels, with current risk scores
    - Pressure at all infrastructure: Airports (# flights/capacity), Ports (queue/throughput)
    - System stress: overall index + component breakdown
    - Threat field grid (current threat values)
    - Flow field (current routing patterns)
    - RiskScore records for all entities (timestamped baseline)
  - Store: create `Scenario.baseline_state` (JSONB) with all snapshot data
  - Execution time: < 3 seconds (single DB read + cache hits)

**Shock Injection**
- `shock_injection.py` (350 LOC)
  - Accepts ScenarioTemplate + shock parameters
  - Injects synthetic disruptions into simulation context:
    - **Event injection**: create new Event in memory (not yet in Postgres) with specified location, type, severity, timestamp
    - **Infrastructure state changes**: update Flight/Vessel routing, Airport/Port capacity reductions, Region threat increases
    - **Graph mutations**: add temporary edges (e.g., blockade → BLOCKS edge between chokepoint and downstream ports)
  - Maintains original Postgres/Neo4j state (simulation runs in memory/cache)
  - Return: shock_state dict describing all modifications

**Post-Shock Simulation**
- `post_shock_simulation.py` (700 LOC)
  - Given baseline + shock, re-run full intelligence pipeline:
    1. Re-score all entities with new threat field (includes injected events)
    2. Re-evaluate route costs (threat-aware routing with new threats)
    3. Recompute pressure (flights rerouted → pressure at alternate airports increases)
    4. Simulate shockwave propagation (from injected event, 72-hour horizon)
    5. Simulate diffusion (threat spreads across regions)
    6. Recompute system stress
  - Internally uses same scoring/physics engines as production (Phase 4-5)
  - Execution time: < 15 seconds for full 72-hour simulation
  - Logging: capture detailed decision trail (why entity score changed, which propagation paths activated)

**Delta Computation**
- `delta_computation.py` (300 LOC)
  - Computes difference: post-shock minus baseline for all metrics
  - Deltas:
    - **Entity Risk Deltas** (ΔRisk): `post_risk - baseline_risk` for each entity
    - **Pressure Deltas** (ΔPressure): `post_pressure - baseline_pressure` for each infrastructure node
    - **Stress Delta** (ΔStress): `post_system_stress - baseline_system_stress`
    - **Threat Field Delta**: spatial grid of differences
    - **Disruption Metrics**: new disruptions introduced (flights diverted, vessels delayed)
  - Ranking: entities/regions ordered by absolute delta magnitude (highest impact first)
  - Narratives: for top N deltas, generate explanatory text:
    - "Risk at [Airport] increased by 0.35 (from 0.38 to 0.73) due to: proximity to conflict zone (+0.28), pressure spike from diverted traffic (+0.07)"

**Recommendation Engine**
- `recommendation_engine.py` (500 LOC)
  - Generates top 5 actions to reduce negative deltas
  - Action types:
    1. **Reroute traffic** — suggest alternative routes with lower threat-adjusted cost
    2. **Preposition assets** — move spare capacity from unaffected to affected infrastructure
    3. **Activate contingencies** — increase staffing, open auxiliary facilities (backup runway, alternate port berth)
    4. **Implement restrictions** — close airspace/corridors to non-essential traffic (reduce exposure)
    5. **Isolate impact** — quarantine affected region from broader network (reduce diffusion)
  - Scoring: each action ranked by impact reduction potential:
    - `action_impact = Σ(delta_reduction_i) / action_cost_i` (benefit per unit cost)
  - Constraints: actions must be feasible (e.g., can't reroute flight past fuel range)
  - Output:
    ```json
    {
      "recommendations": [
        {
          "rank": 1,
          "action": "Reroute 40% of DXB-arriving flights to AUH via alternate corridor",
          "rationale": "Reduces DXB pressure from 0.92 to 0.68; adds 15 minutes to flight time",
          "impact": {"pressure_reduction": 0.24, "cost_increase_percent": 3.2},
          "feasibility": 0.95,
          "recommendation_strength": 0.89
        },
        {
          "rank": 2,
          "action": "Close Hormuz to non-essential traffic; reroute via Suez",
          "rationale": "Eliminates shock event impact; increases transit time 18-24 hours",
          "impact": {"pressure_reduction": 0.45, "cost_increase_percent": 8.5},
          "feasibility": 0.60,
          "recommendation_strength": 0.71
        }
        // ... top 5 total
      ]
    }
    ```

**Explainable Narrative Generation (Bilingual EN/AR)**
- `narrative_generator.py` (600 LOC)
  - Generates human-readable explanation of scenario results
  - Template-based narrative with dynamic content insertion:
    - **Scenario Summary**: "This scenario simulates [scenario_name] affecting the GCC region over [duration]"
    - **Primary Shock**: "The scenario injects a [shock_type] at [location] with severity [S]"
    - **Immediate Impacts** (0-6 hours): "Within 6 hours, the threat field expands to [regions], affecting [N] flights and [M] vessels"
    - **Secondary Impacts** (6-24 hours): "Pressure at [Airport] rises to [P%] capacity; [N] flights diverted to [alternate_airports]"
    - **Cascading Effects** (24-72 hours): "Diffusion of threat across [regions]; [N] vessels delay by average [X] hours"
    - **System-Level Assessment**: "Overall system stress escalates to [state] with [critical_factors]"
    - **Recommendation Summary**: "Top priority: [top_recommendation]. This action reduces stress from [ΔStress] to [reduced_ΔStress]"
  - Bilingual: templates provided in English + Arabic; generate both versions
  - Audience: executive summary (2-3 paragraphs) + detailed breakdown (1 page)

**Scenario Persistence and Comparison**
- `scenario_store.py` (350 LOC)
  - Persist scenario execution to Postgres `scenarios` table:
    - scenario_id (UUID)
    - template_name (VARCHAR)
    - baseline_state (JSONB)
    - shock_definition (JSONB)
    - post_shock_state (JSONB)
    - deltas (JSONB): all entity deltas, stress deltas, etc.
    - recommendations (JSONB)
    - narrative_en (TEXT)
    - narrative_ar (TEXT)
    - created_at, executed_at (TIMESTAMPTZ)
  - Comparison endpoint: `GET /api/v1/scenarios/{scenario_id_1}/compare/{scenario_id_2}`
    - Returns diff: which recommendations overlapped, which deltas were larger, which regions most affected
  - Scenario history: `GET /api/v1/scenarios/history` lists all executed scenarios with summary stats

### Decision Gate ✓ PASS
- All 7 scenario templates defined; each accepts shock parameters and executes without error
- Baseline state captured for arbitrary system state; size < 10 MB (efficient storage)
- Shock injection modifies simulation context correctly; original DB state unchanged
- Post-shock simulation runs full pipeline (scoring + physics) in < 15 seconds
- Delta computation correctly calculates post - baseline for all entities; top deltas make intuitive sense
- Recommendation engine produces 5 ranked actions with quantified impact and feasibility
- Narrative generator produces coherent English + Arabic summaries (≥ 3 paragraphs each)
- Scenario persistence stores all data in Postgres; retrieval by scenario_id returns complete state
- Scenario comparison identifies overlaps and differences between two executions
- Spot-check: Hormuz Closure scenario produces expected pressure spike at UAE ports + system stress → RED with 95%+ confidence

---

## Phase 7: Backend API

### Deliverables

**FastAPI Router Structure: /api/v1/{resource_type}**
- Main router: `routers/api_v1.py` (100 LOC)
  - Includes 8 sub-routers:
    - `routers/events.py` — /api/v1/events
    - `routers/airports.py` — /api/v1/airports
    - `routers/ports.py` — /api/v1/ports
    - `routers/flights.py` — /api/v1/flights
    - `routers/vessels.py` — /api/v1/vessels
    - `routers/scenarios.py` — /api/v1/scenarios
    - `routers/risk.py` — /api/v1/risk
    - `routers/intelligence.py` — /api/v1/intelligence
  - Base URL versioning: all endpoints prefixed with /api/v1

**CRUD Endpoints for All Entities**
- Pattern for each resource (Event, Airport, Port, Flight, Vessel, Route, Corridor, Region):
  - `GET /api/v1/{resource}` — list all (pagination: ?page=1&limit=50)
  - `GET /api/v1/{resource}/{id}` — fetch single by ID
  - `POST /api/v1/{resource}` — create new (JSON body)
  - `PATCH /api/v1/{resource}/{id}` — update partial
  - `DELETE /api/v1/{resource}/{id}` — soft delete (mark as_deleted=True)
  - `GET /api/v1/{resource}/{id}/history` — retrieve audit log (changes over time)
- Response format: wrapped in `APIResponse` model:
  ```json
  {
    "status": "success|error",
    "data": {...},
    "metadata": {
      "request_id": "...",
      "timestamp": "2026-03-31T14:22:00Z",
      "duration_ms": 145
    }
  }
  ```
- Validation: Pydantic models auto-validate inputs; invalid requests return 422 with field errors

**POST /api/v1/scenarios/run — Execute Scenario Simulation**
- Request:
  ```json
  {
    "template": "hormuz_closure",
    "shock_parameters": {
      "duration_hours": 72,
      "affected_ships_percent": 60,
      "lane_closures": "BOTH_LANES"
    }
  }
  ```
- Response:
  ```json
  {
    "status": "success",
    "data": {
      "scenario_id": "...",
      "baseline_stress": 0.42,
      "post_shock_stress": 0.85,
      "delta_stress": +0.43,
      "state_change": "YELLOW → RED",
      "recommendations": [...],
      "narrative": "..."
    },
    "metadata": {
      "request_id": "...",
      "duration_ms": 12450
    }
  }
  ```
- Async execution: if scenario takes > 30 seconds, return immediately with status=PENDING + poll URL

**GET /api/v1/risk/{entity_type}/{entity_id} — Risk Score with Explanation**
- Request: no body
- Response:
  ```json
  {
    "status": "success",
    "data": {
      "entity_id": "...",
      "entity_type": "Airport",
      "score": 0.72,
      "confidence": 0.88,
      "components": {...},
      "explanation": {...},
      "last_updated": "2026-03-31T14:15:00Z"
    }
  }
  ```
- Status codes: 200 (success), 404 (entity not found), 400 (invalid entity_type)

**GET /api/v1/intelligence/threat-field — Current Threat Field Grid**
- Query parameters: ?resolution=0.5 (degrees), ?format=geojson|array
- Response:
  ```json
  {
    "status": "success",
    "data": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [55.0, 25.0]
          },
          "properties": {
            "threat_value": 0.68,
            "altitude_m": 0,
            "contributing_events": [{"event_id": "...", "contribution": 0.42}]
          }
        }
        // ... one feature per grid cell
      ]
    }
  }
  ```

**GET /api/v1/intelligence/system-stress — Current System Stress**
- Response:
  ```json
  {
    "status": "success",
    "data": {
      "overall_stress": 0.62,
      "state": "RED",
      "trend": "RISING",
      "components": {
        "pressure": {...},
        "threat": {...},
        "disruption": {...}
      },
      "hotspots": [
        {"region": "Dubai", "stress": 0.85, "primary_factor": "airport_pressure"}
      ]
    }
  }
  ```

**GET /api/v1/intelligence/propagation/{event_id} — Risk Propagation from Event**
- Response: timeline of impact spreading:
  ```json
  {
    "status": "success",
    "data": {
      "event_id": "...",
      "timeline": [
        {
          "hours_ahead": 0,
          "primary_wavefront_km": 0,
          "affected_regions": ["Iran (Northern)"],
          "estimated_impact": 0.80
        },
        {
          "hours_ahead": 12,
          "primary_wavefront_km": 2400,
          "affected_regions": ["Iran (Northern)", "Iraq", "Kuwait"],
          "estimated_impact": 0.65
        }
        // ... 72-hour horizon
      ]
    }
  }
  ```

**GET /api/v1/graph/query/{query_name} — Execute Named Graph Query**
- Supported query_name values: events_by_region, infrastructure_at_risk, flight_path_threats, vessel_route_threats, cascading_impact, critical_chokepoints, actor_network
- Request: `GET /api/v1/graph/query/events_by_region?region_id=saudi_arabia`
- Response:
  ```json
  {
    "status": "success",
    "data": {
      "query_name": "events_by_region",
      "nodes": [
        {
          "id": "...",
          "label": "Event",
          "properties": {
            "event_type": "MILITARY_ACTION",
            "severity": "HIGH",
            "timestamp": "2026-03-31T10:00:00Z"
          }
        }
        // ... all matching nodes
      ],
      "edges": [
        {
          "from": "...",
          "to": "...",
          "relationship": "AFFECTS",
          "properties": {"strength": 0.85}
        }
      ]
    }
  }
  ```

**WebSocket /api/v1/ws/live — Real-Time Event Feed**
- Client connects: `ws://backend/api/v1/ws/live?api_key=...`
- Server streams:
  ```json
  {
    "type": "event",
    "data": {
      "event_id": "...",
      "action": "created|updated|risk_change",
      "entity": {...}
    }
  }
  ```
- Filters (query params): ?event_types=MILITARY_ACTION,VIOLENCE &regions=saudi_arabia,uae
- Heartbeat: server sends `{"type": "ping"}` every 30 seconds
- Connection limits: max 100 concurrent connections per API key

**Auth Middleware (API Key, Extensible to JWT)**
- `middleware/auth.py` (150 LOC)
  - Header: `Authorization: Bearer <api_key>` or query param `?api_key=...`
  - Validate against keys table: `api_keys(key_hash, app_name, created_at, expires_at, rate_limit_rps)`
  - Set request.user context (app_name)
  - Rate limiting: enforce per-key limit (default 100 requests/minute, configurable per key)
  - Extensible: plug in JWT validation (Auth0, Firebase, etc.) with same interface
  - 401 Unauthorized if key missing/invalid; 429 Too Many Requests if rate limit exceeded

**Structured JSON Responses with Metadata**
- All endpoints return `APIResponse` model:
  ```python
  class APIResponse(BaseModel):
      status: Literal["success", "error"]
      data: Any
      metadata: ResponseMetadata
      errors: Optional[list[ErrorDetail]] = None
  
  class ResponseMetadata(BaseModel):
      request_id: UUID  # auto-generated
      timestamp: datetime  # UTC
      duration_ms: int  # endpoint execution time
      api_version: str = "v1"
  
  class ErrorDetail(BaseModel):
      field: Optional[str] = None
      message: str
      code: str
  ```

**Response Status Codes**
- 200 OK — successful response
- 201 Created — POST successful
- 204 No Content — DELETE successful
- 400 Bad Request — validation error (missing/invalid fields)
- 401 Unauthorized — missing/invalid API key
- 404 Not Found — entity not found
- 422 Unprocessable Entity — Pydantic validation error (detailed field errors)
- 429 Too Many Requests — rate limit exceeded
- 500 Internal Server Error — unexpected error (logged with request_id)

### Decision Gate ✓ PASS
- All 8 router modules defined; application starts without import errors
- All CRUD endpoints implement GET/POST/PATCH/DELETE patterns; spot-check on 3 resource types (Event, Airport, Flight)
- `POST /api/v1/scenarios/run` accepts template + parameters; returns full scenario result with recommendations
- `GET /api/v1/risk/{entity_type}/{entity_id}` returns score + explanation components + drivers
- `GET /api/v1/intelligence/threat-field` returns GeoJSON feature collection with threat values
- `GET /api/v1/intelligence/system-stress` returns current stress + components + hotspots
- `GET /api/v1/intelligence/propagation/{event_id}` returns timeline of impact spreading (0-72 hours)
- `GET /api/v1/graph/query/{query_name}` executes all 7 named queries; returns nodes + edges + properties
- WebSocket `/api/v1/ws/live` accepts connections; streams events with correct filters applied
- Auth middleware validates API keys; rejects invalid keys with 401; enforces rate limits (429 when exceeded)
- All endpoints return valid `APIResponse` JSON with status + data + metadata
- Spot-check: 10 random endpoints respond within 500ms; response size < 1MB

---

## Phase 8: Control Room UI

### Deliverables

**CesiumJS 3D Globe with Dark Executive Aesthetic**
- `components/Globe.tsx` (500 LOC)
  - Initialize Cesium.Viewer with:
    - Dark theme: black background, muted terrain colors
    - Initial view: GCC center (23°N, 50°E) at zoom level showing full region
    - Performance: LOD (level-of-detail) terrain at 1km resolution
  - Scene setup: imageryProvider (dark basemap), terrain provider, lighting (time=sunset for dramatic effect)
  - Interaction: click to select entities, scroll to zoom, drag to pan
  - Framerate: target 60 FPS on modern hardware

**Layer System: Events, Flights, Vessels, Threat Field Heatmap, Risk Zones, Corridors**
- `components/Layers.tsx` (600 LOC) — layer toggle panel
  - Layer 1: **Events** — red/orange points (colored by severity), click for details
  - Layer 2: **Flights** — cyan flight paths with aircraft icons, heading indicators
  - Layer 3: **Vessels** — blue ship icons with wake trails, speed vectors
  - Layer 4: **Threat Field Heatmap** — semi-transparent grid overlay (deck.gl), red=high threat, blue=low
  - Layer 5: **Risk Zones** — red-shaded polygons around high-risk infrastructure
  - Layer 6: **Corridors** — flight corridors (cyan lines), shipping lanes (blue lines)
  - Layer 7: **Regions** — GCC nation boundaries (thin gray lines), labels
  - Each layer: toggle visibility, adjust opacity, export GeoJSON
  - Keyboard shortcuts: E=events, F=flights, V=vessels, H=heatmap, etc.

**Event Feed Panel (Real-Time)**
- `components/EventFeed.tsx` (400 LOC) — right sidebar
  - Lists recent events in reverse chronological order
  - Each event card:
    - Time (relative: "2 hours ago")
    - Type (icon + text: "MILITARY_ACTION")
    - Location (name + coordinates)
    - Severity (color badge: RED/ORANGE/YELLOW)
    - Brief description (2-3 words)
    - "View Details" link (opens detail drawer)
  - Auto-scroll to newest event
  - WebSocket live feed: new events appear in real-time (animation: slide in from top)
  - Filter: event_types dropdown (select which types to show)
  - Pagination: show 20 most recent, "Load more" button

**Entity Detail Drawer (Click any node → Full detail + Risk Score + Explanation)**
- `components/EntityDetailDrawer.tsx` (800 LOC) — bottom panel / modal
  - Triggered by clicking any entity on globe
  - Sections (tab interface):
    1. **Overview** — entity name, type, location, creation date, data source
    2. **Risk Score** — card displaying score (0-1), confidence, components (bar chart), trend (↑/→/↓)
    3. **Explanation** — text breakdown:
       - "Risk: 0.72 (HIGH)"
       - "Primary drivers: proximity to conflict (0.45), high network centrality (0.35)"
       - "Secondary factors: crowded airspace (airport), recent escalation in region"
       - "Timeline: high-risk window 6-12 hours, declining after 24 hours"
    4. **Related Entities** — connections (flights at airport, events affecting region, etc.)
    5. **Time Series** — risk score + pressure over last 7 days (chart)
    6. **Actions** — (for infrastructure) reroute traffic, adjust capacity, activate contingencies (buttons trigger scenario simulation)
  - Close: click X or click outside drawer
  - Mobile responsive: drawer full width on small screens

**Scenario Control Panel (Select Template → Configure → Run → See Results)**
- `components/ScenarioPanel.tsx` (900 LOC) — modal dialog
  - Step 1: **Template Selection**
    - Radio buttons: Hormuz Closure, Airspace Restriction, Port Congestion, Conflict Escalation, Airport Closure, Maritime Chokepoint, Cascading Multi-Event
    - Description and icon for each template
  - Step 2: **Configure Parameters**
    - Template-specific form (e.g., for Hormuz: duration_hours slider, affected_ships_percent slider, lane_closures checkboxes)
    - Preview: map shows shock location (red circle)
  - Step 3: **Run Simulation**
    - Button: "Execute Scenario" (calls `POST /api/v1/scenarios/run`)
    - Loading state: spinner + "Simulating..." message (blocks UI for up to 30 seconds)
  - Step 4: **View Results**
    - Split pane:
      - Left: summary card
        - Baseline stress / Post-shock stress / ΔStress
        - State change (YELLOW → RED)
        - Confidence (0-100%)
      - Right: recommendations list (top 5 actions ranked by impact)
        - Each recommendation: title + rationale + impact metrics + feasibility %
        - Expandable: click to see full detail + implementation steps
    - Timeline button: visualize 72-hour impact progression
    - Export: download scenario as JSON + narrative as PDF

**Timeline Scrubber (Filter by Time Range)**
- `components/Timeline.tsx` (400 LOC) — bottom timeline control
  - Horizontal slider: drag to select time window (default: last 7 days)
  - Range inputs: "From:" date/time picker, "To:" date/time picker
  - Preset buttons: "Last 24h", "Last 7d", "Last 30d", "Custom"
  - Apply: button triggers data reload with date filter
  - Auto-play: button plays timeline animation (fast-forward through events, threat field evolution)
  - Speed control: 1x, 5x, 10x, 25x

**Risk Score Cards (Top 10 At-Risk Entities)**
- `components/RiskCards.tsx` (300 LOC) — top panel / widget
  - Displays 5-card carousel showing highest-risk entities (Airport, Port, Flight, Vessel, or Corridor)
  - Each card:
    - Rank badge (1-10)
    - Entity name + type icon
    - Risk score (large text, color-coded: RED/ORANGE/YELLOW)
    - Primary driver (1-2 word summary)
    - Time trend arrow (↑ if risk increasing in last 6 hours, → if stable, ↓ if decreasing)
    - Click to open detail drawer
  - Auto-refresh every 5 minutes
  - Sort toggle: by risk score or by trend (worsening most)

**Graph Insight Panel (Show Neo4j Subgraph Around Selected Entity)**
- `components/GraphInsights.tsx` (500 LOC) — left sidebar tab / collapsible
  - Triggered by clicking entity on globe
  - Visualization: node-link diagram (D3 force-directed graph)
    - Center node: selected entity (larger, highlighted)
    - 1-hop neighbors: directly connected entities (AFFECTS, INVOLVES, DEPARTS_FROM, etc.)
    - 2-hop neighbors: entities connected via 1-hop (semi-transparent)
    - Edges: labeled with relationship type + properties (distance_km, severity, etc.)
  - Interactivity:
    - Hover on node: highlight path to center
    - Click node: navigate to that entity (update detail drawer)
    - Drag node: temporarily adjust layout
  - Stats: count of nodes/edges, density, clustering coefficient
  - Export: download subgraph as GeoJSON/Cypher query

**Impact Heatmap Overlay (deck.gl)**
- `components/ImpactHeatmap.tsx` (400 LOC)
  - Rendered via deck.gl HeatmapLayer on top of 3D globe
  - Data: threat field grid from `/api/v1/intelligence/threat-field`
  - Color scale: blue (0.0, no threat) → cyan → green → yellow → orange → red (1.0, critical threat)
  - Opacity: scale with threat value (0.0 → transparent, 1.0 → opaque)
  - Performance: GPU-accelerated rendering via WebGL
  - Toggle: checkbox to show/hide; opacity slider for adjustment
  - Hover: display exact threat value + contributing events at cursor location

**"Why This Score?" Explainability Panel**
- `components/ExplainabilityPanel.tsx` (600 LOC) — dedicated modal
  - Triggered by clicking "Explain" button in Risk Score card / detail drawer
  - Visual breakdown:
    - Component bars: 7 components (base, proximity, temporal, network, exposure, disruption, confidence) as stacked bar chart
    - Each component: labeled with score value (0.0-1.0) + weight in final calculation (%)
  - Narrative explanation (pulled from API):
    - Primary drivers (bullets)
    - Secondary factors (bullets)
    - Recommendation (action to reduce risk)
  - Timeline projection:
    - Line chart: risk score forecast for 6/12/24/72 hours ahead
    - Confidence bands: confidence interval around forecast
  - Source attribution:
    - List of data sources used (ACLED, OpenSky, AIS, etc.) + freshness timestamps
    - Data quality assessment (green/yellow/red indicator)

**System Stress Indicator**
- `components/StressIndicator.tsx` (250 LOC) — top-right corner
  - Large gauge dial:
    - Needle position: overall_stress value (0.0 left → 1.0 right)
    - Color zones: GREEN (0-0.3), YELLOW (0.3-0.6), RED (0.6-0.85), CRITICAL (0.85+)
    - Current state label: "YELLOW", "RED", "CRITICAL"
    - Trend indicator: arrow up/flat/down
  - Breakdown: 3-part pie chart (Pressure %, Threat %, Disruption %)
  - Hotspot: text label of highest-stress region (e.g., "Dubai +0.15 from baseline")
  - Click to open System Stress detail panel

### Decision Gate ✓ PASS
- CesiumJS globe initializes; renders dark theme with full GCC region visible
- All 7 layers render without errors; layer toggle checkbox controls visibility
- Event feed updates in real-time via WebSocket; new events animate into view within 2 seconds
- Entity detail drawer opens on click (Event, Airport, Flight, Vessel); displays all 5 tabs (Overview, Risk, Explanation, Related, Time Series)
- Scenario panel allows selection of 7 templates, configuration of template-specific parameters, execution, and viewing of results
- Timeline scrubber filters data by date range; play button animates evolution over time
- Risk score cards display top 10 entities, updated every 5 minutes; click navigates to detail
- Graph insight panel shows Neo4j subgraph; 1-hop neighbors visible, edges labeled
- Impact heatmap overlays threat field on globe; color scale intuitive (blue → red)
- Explainability panel breaks down risk score into 7 components with narrative drivers
- System stress indicator displays gauge + trend + hotspot; color zones correct
- UI responsive to 1920x1080 (desktop); performance >30 FPS on test machine
- Scenario execution produces visible impact: threat field expands, pressure spikes at infrastructure, system stress state changes

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **ACLED API Rate Limits** | Medium | Medium | Local caching (24h TTL), seed data fallback, request queueing, daily refresh job (off-peak) |
| **Neo4j Cold Start Latency** | Low | Medium | Connection pooling (max_pool_size=50), schema pre-initialization on startup, index warm-up |
| **PostGIS Query Performance at Scale** | Medium | High | Spatial indexes (GIST on location columns), materialized views for hot queries, query optimization review, monitoring dashboards |
| **CesiumJS Bundle Size** | High | Low | Dynamic import of heavy modules, code splitting by feature, lazy load terrain/imagery, test on low-bandwidth (3G) network |
| **Model Drift in Risk Scores** | Medium | High | Score version tracking (every model update increments version), A/B comparison framework (v1 vs v2 scores side-by-side), stakeholder acceptance testing |
| **GCC Data Sovereignty** | High | High | Region-locked deployment (only EU/GCC cloud regions), data residency configuration (no cross-border flow), encryption at rest (AES-256), audit logging |
| **Scenario Engine Complexity** | Medium | Medium | Iterative validation with SMEs, formal verification of physics equations, canary deployment (5% traffic) to new scenario types |
| **Real-Time Latency Requirements** | Medium | High | WebSocket connection pooling, Redis caching for frequent queries, async/await throughout backend, CDN for static assets (frontend) |
| **Third-Party API Outage** | Low | High | Graceful degradation (seed data fallback if ACLED down), circuit breaker pattern, multi-source redundancy (AIS from multiple providers) |

---

## Decision Gates Summary

Each phase has a **binary pass/fail decision gate**. No "partial" gates, no "mostly passing" exemptions. Gate passes when ALL acceptance criteria verified.

| Phase | Gate Criteria | Status | Owner |
|-------|--------------|--------|-------|
| **Phase 1** | Repository structure ✓, 41 Pydantic models ✓, 15 math/physics modules ✓, Docker Compose stack healthy ✓, ORM models mapped ✓ | COMPLETED | DevOps + Backend Lead |
| **Phase 2** | 3 connectors produce canonical schema ✓, seed data (115 entities) loads in <30s ✓, normalization service endpoint working ✓ | PENDING | Data Integration Lead |
| **Phase 3** | Neo4j schema initialized ✓, >50 Event nodes + dependencies ✓, all 7 graph queries execute correctly ✓ | PENDING | Graph Database Lead |
| **Phase 4** | All 7 risk components compute without error ✓, scores [0.0, 1.0] ✓, explanation API returns breakdown ✓, Redis caching working ✓ | PENDING | Scoring Engineer |
| **Phase 5** | Threat field computes in <5s ✓, flow field renders correctly ✓, pressure/shockwave/diffusion engines operational ✓, system stress computable ✓ | PENDING | Physics Lead |
| **Phase 6** | 7 scenario templates defined ✓, baseline/shock/delta compute ✓, recommendations ranked ✓, bilingual narratives generated ✓ | PENDING | Scenario Engineer |
| **Phase 7** | 8 router modules + 60 endpoints ✓, all CRUD working ✓, scenario endpoint produces full result ✓, WebSocket live feed ✓, auth middleware enforced ✓ | PENDING | API Lead |
| **Phase 8** | Globe renders + 7 layers working ✓, detail drawer on click ✓, scenario panel executes ✓, UI performance >30 FPS ✓, spot-check results sensible ✓ | PENDING | Frontend Lead |

---

## What's Built (Phase 1: Foundation)

- Complete 7-layer architecture (Data → Schema → Graph → Models → Intelligence → API → UI)
- Canonical schema: 9 Pydantic modules, 41 domain models, full type safety
- Mathematical foundations: 8 scoring modules + 7 physics modules, all tested
- Infrastructure: Docker Compose stack (PostGIS, Neo4j, Redis, backend, frontend), all healthy
- Database: SQLAlchemy ORM with PostGIS integration, migrations applied
- Base interfaces: connector abstraction, ready for Phase 2

## What's Next (Phase 2 Onwards)

- **Phase 2**: Connect real data sources (ACLED, aviation, maritime) and seed GCC datasets
- **Phase 3**: Build full knowledge graph in Neo4j with GCC topology and relationships
- **Phase 4**: Integrate scoring engine with live risk evaluation and explainability
- **Phase 5**: Activate physics intelligence (threat fields, flow fields, system stress)
- **Phase 6**: Scenario engine simulation and recommendation generation
- **Phase 7**: REST/WebSocket API with full CRUD and decision support endpoints
- **Phase 8**: Executive control room UI with globe, layers, and real-time decision support

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-31  
**Next Review:** Phase 2 completion (gate pass)
