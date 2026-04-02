# Impact Observatory — Developer Runbook

**Version:** 1.0.0 | **Updated:** 2026-03-31

## System Architecture

```
┌─────────────────────────────────────────────────┐
│          Frontend (Next.js 14 + CesiumJS)       │
│    Control Room  │  Scenario Panel  │  deck.gl   │
└────────────────────────┬────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────▼────────────────────────┐
│             FastAPI Gateway (64 routes)          │
│  /events /conflicts /incidents /scenarios /graph │
│  /insurance /scores /decision /pipeline /ingest  │
└──┬──────────┬──────────┬────────────────────────┘
   │          │          │
┌──▼──┐  ┌───▼───┐  ┌───▼──┐
│PG+  │  │ Neo4j │  │Redis │
│Post │  │ Graph │  │Cache │
│GIS  │  │  DB   │  │Queue │
└─────┘  └───────┘  └──────┘
   ▲          ▲          ▲
   └──────────┼──────────┘
              │
┌─────────────▼──────────────┐
│    Intelligence Layers     │
│ math_core │ physics │ ins. │
│ scenario  │ Mesa    │ dec. │
└────────────────────────────┘
```

## Service Dependency & Startup Order

1. **PostgreSQL + PostGIS** (port 5432) — spatial event storage
2. **Neo4j + APOC** (bolt 7687, http 7474) — graph intelligence
3. **Redis** (port 6379) — cache, pipeline status, task queue
4. **FastAPI backend** (port 8000) — API gateway, depends on all above
5. **Next.js frontend** (port 3000) — control room UI

## Quick Start

```bash
# Clone and start
git clone https://github.com/PyBADR/deevo-sim.git && cd deevo-sim
cp backend/.env.example backend/.env
make dev          # docker-compose up -d all services

# Load seed data
make seed         # 175 GCC records: 50 events, 30 airports, 20 ports, 15 corridors, etc.

# Verify
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/scenarios
```

## Monitoring Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | System health + DB connectivity |
| `GET /version` | Version and capabilities |
| `GET /api/v1/pipeline` | Pipeline execution status |
| `GET /api/v1/ingest/status` | Data ingestion status |

## Common Operations

### Run a scenario
```bash
curl -X POST http://localhost:8000/api/v1/scenarios/run \
  -H "Content-Type: application/json" \
  -H "X-DC7-API-Key: dc7_test_key" \
  -d '{"scenario_id": "hormuz_closure", "severity": 0.9}'
```

### Generate decision output
```bash
curl -X POST http://localhost:8000/api/v1/decisions/output \
  -H "Content-Type: application/json" \
  -H "X-DC7-API-Key: dc7_test_key" \
  -d '{"scenario_id": "hormuz_closure", "severity": 0.9}'
```

### Run full lifecycle pipeline
```bash
curl -X POST http://localhost:8000/api/v1/pipeline/start \
  -H "X-DC7-API-Key: dc7_test_key"
```

### CLI scenario runner
```bash
cd backend
PYTHONPATH=. python -m scripts.run_scenario --list
PYTHONPATH=. python -m scripts.run_scenario hormuz_closure
PYTHONPATH=. python -m scripts.run_scenario --all --json
```

## Database Operations

### PostgreSQL
```bash
make shell-db                          # Open psql shell
docker-compose exec postgres pg_dump -U dc7_user dc7_db > backup.sql  # Backup
```

### Neo4j
```bash
make shell-neo4j                       # Open cypher-shell
# Browser: http://localhost:7474
```

### Redis
```bash
docker-compose exec redis redis-cli    # Open redis-cli
docker-compose exec redis redis-cli FLUSHALL  # Clear cache
```

## Failure Modes

| Failure | Symptom | Recovery |
|---------|---------|----------|
| PostgreSQL down | `/health` returns `unhealthy` | `docker-compose restart postgres` |
| Neo4j down | Graph queries fail | `docker-compose restart neo4j` |
| Redis down | Pipeline tracking fails | `docker-compose restart redis` |
| OOM | Container exits | Increase Docker memory, `docker-compose restart` |
| Git lock file | `index.lock exists` | `rm -f .git/index.lock .git/HEAD.lock` |

## Environment Variables

All variables use the `DC7_` prefix. See `backend/.env.example` for full reference.

| Variable | Default | Description |
|----------|---------|-------------|
| `DC7_POSTGRES_HOST` | localhost | PostgreSQL host |
| `DC7_POSTGRES_PORT` | 5432 | PostgreSQL port |
| `DC7_NEO4J_URI` | bolt://localhost:7687 | Neo4j connection |
| `DC7_REDIS_URL` | redis://localhost:6379 | Redis URL |
| `DC7_API_KEY` | (required) | API authentication key |
| `NEXT_PUBLIC_CESIUM_ION_TOKEN` | (required) | CesiumJS access token |
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend API URL |

## Running Tests

```bash
cd backend
PYTHONPATH=. pytest tests/ -v                    # All tests
PYTHONPATH=. pytest tests/test_integration.py -v  # Integration
PYTHONPATH=. pytest tests/test_scenarios_seeded.py -v  # Scenario regression
PYTHONPATH=. pytest tests/test_insurance.py -v    # Insurance
PYTHONPATH=. pytest tests/test_physics_gcc.py -v  # Physics GCC defaults
```

## Architecture Layers

| Layer | Package | Key Files |
|-------|---------|-----------|
| Schema | `app/schema/` | 9 modules, 41 Pydantic v2 models |
| Connectors | `app/connectors/` | ACLED, aviation, maritime, CSV |
| Graph | `app/graph/` | 11 node types, 16 edge types, 8 Cypher templates |
| Math Core | `app/intelligence/math_core/` | GCC risk equations, calibration |
| Physics | `app/intelligence/physics/` | Threat, flow, friction, pressure, shockwave |
| Insurance | `app/intelligence/insurance/` | Exposure, claims surge, UW restriction |
| Scenarios | `app/scenarios/` | 15 templates, simulator, explainer |
| Simulation | `app/simulation/` | Mesa agent-based model |
| Decision | `app/decision/` | Structured output answering 5 questions |
| Services | `app/services/` | Orchestrator, scoring, physics, insurance, enrichment |
| API | `app/api/` | 64 FastAPI routes across 12 routers |
| Seeds | `seeds/` | 175 GCC records + 15 expected outputs |
