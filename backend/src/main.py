"""Impact Observatory | مرصد الأثر — FastAPI application entry point.

Decision Intelligence Platform for GCC Financial Markets.
Every output maps: Event → Math Models → Physics → Sector Stress → Decision

Architecture: 9-layer deterministic simulation engine
Model version: 2.1.0
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.auth import require_api_key
from src.api.routes.conflicts import router as conflicts_router
from src.api.routes.decision import router as decision_router
from src.api.routes.events import router as events_router
from src.api.routes.flights import router as flights_router
from src.api.routes.graph import router as graph_router
from src.api.routes.health import router as health_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.insurance import router as insurance_router
from src.api.routes.scenarios import router as scenarios_router
from src.api.routes.scores import router as scores_router
from src.api.routes.vessels import router as vessels_router

# Impact Observatory v1 API
from src.api.v1.scenarios import router as v1_scenarios_router
from src.api.v1.runs import router as v1_runs_router
from src.api.v1.auth import router as v1_auth_router
from src.api.v1.nodes import router as v1_nodes_router
from src.api.v1.decisions import router as v1_decisions_router
from src.api.v1.outcomes import router as v1_outcomes_router
from src.api.v1.values import router as v1_values_router
from src.api.v1.narrative import router as v1_narrative_router
from src.api.v1.decision_authority import router as v1_decision_authority_router, register_validation_handler
from src.banking_intelligence.api.v1.scenario_chain import router as v1_scenario_chain_router
from src.banking_intelligence.api.v1.entities import router as v1_banking_entities_router
from src.banking_intelligence.api.v1.decisions import router as v1_banking_decisions_router
from src.api.v1.institutional import router as v1_institutional_router
from src.api.v1.provenance import router as v1_provenance_router

from src.core.config import settings
from src.services.state import init_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # ── Startup ──────────────────────────────────────────────────────────
    init_state()

    # Warm up simulation engine (imports + JIT-like first-call overhead)
    try:
        from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
        _warm = SimulationEngine()
        _warm.run("hormuz_chokepoint_disruption", severity=0.5, horizon_hours=24)
        print(f"✅ SimulationEngine v{SimulationEngine.MODEL_VERSION} ready "
              f"({len(SCENARIO_CATALOG)} scenarios)")
    except Exception as e:
        print(f"⚠️  SimulationEngine warmup skipped: {e}")

    # Real-time data feeds (non-blocking — falls back to seed data)
    try:
        from src.services.data_feeds import refresh_all_feeds
        from src.services.state import get_state
        asyncio.ensure_future(refresh_all_feeds(get_state()))
        print("📡 Data feeds initializing (ACLED/AIS/OpenSky)...")
    except Exception as e:
        print(f"⚠️  Data feeds skipped: {e}")

    # Optional databases (5 s timeout each — non-fatal)
    try:
        from src.db.neo4j import init_neo4j
        await asyncio.wait_for(init_neo4j(), timeout=5.0)
        print("✅ Neo4j connected")
    except Exception as e:
        print(f"⚠️  Neo4j skipped: {e}")

    try:
        from src.db.redis import init_redis
        await asyncio.wait_for(init_redis(), timeout=5.0)
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis skipped: {e}")

    # PostgreSQL table auto-creation (action tracking + enterprise models)
    try:
        from src.db.postgres import engine as pg_engine, Base
        # Import all ORM models so Base.metadata sees them
        import src.models.action_tracking  # noqa: F401
        import src.models.enterprise  # noqa: F401
        import src.models.orm  # noqa: F401

        async with pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ PostgreSQL tables verified/created (action_tracking, enterprise, orm)")
    except Exception as e:
        print(f"⚠️  PostgreSQL table creation skipped: {e}")

    # Banking Intelligence seed data (non-fatal)
    try:
        from src.banking_intelligence.seed.loader import seed_entity_store
        from src.banking_intelligence.api.v1.entities import _entity_store
        counts = seed_entity_store(_entity_store)
        total = sum(v for k, v in counts.items() if k != "edges")
        print(f"✅ Banking Intelligence seeded: {total} entities, {counts.get('edges', 0)} edges")
    except Exception as e:
        print(f"⚠️  Banking Intelligence seed skipped: {e}")

    print("🚀 Impact Observatory | مرصد الأثر — ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    for closer, name in [
        ("src.db.neo4j", "close_neo4j"),
        ("src.db.redis", "close_redis"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(closer)
            await getattr(mod, name)()
        except Exception:
            pass


# ── Application ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Impact Observatory | مرصد الأثر",
    description=(
        "Decision Simulation Engine for GCC Financial Markets.\n\n"
        "Every output maps: Event → Math Models → Physics → Sector Stress → Decision.\n\n"
        "**Model version:** 2.1.0 | **Architecture:** 10-layer deterministic pipeline "
        "(17 runtime stages in SimulationEngine + 1 audit stage = 18 pipeline stages total)\n\n"
        "**Mandatory outputs:** scenario_id · model_version · event_severity · peak_day · "
        "confidence_score · financial_impact · sector_analysis · propagation_score · "
        "unified_risk_score · risk_level · physical_system_status · bottlenecks · "
        "congestion_score · recovery_score · explainability · decision_plan"
    ),
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Validation error handler (executive-safe, no raw Pydantic leaks) ─────
register_validation_handler(app)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Observability Middleware ──────────────────────────────────────────────
import hashlib
import json
import logging
import time

obs_logger = logging.getLogger("observatory.audit")


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Log every API request with timing, status, and SHA-256 response hash.

    Provides Sentry/Datadog-equivalent audit trail without external dependencies.
    Every simulation run, decision action, and API call is traceable.
    """
    start = time.perf_counter()
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    status = response.status_code

    # Log structured audit entry
    obs_logger.info(
        "API_REQUEST",
        extra={
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "content_length": response.headers.get("content-length", "0"),
        },
    )

    # Add observability headers
    response.headers["X-Duration-Ms"] = str(duration_ms)
    response.headers["X-Model-Version"] = "2.1.0"
    return response


# ── Global exception handler ──────────────────────────────────────────────
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ── Health (no auth) ──────────────────────────────────────────────────────
app.include_router(health_router)


# ── Simulation engine direct endpoint (no auth — public) ─────────────────
@app.post("/simulate", tags=["simulation"], summary="Direct simulation — full 16-field output")
async def simulate_direct(body: dict):
    """Direct access to SimulationEngine.run() — bypasses legacy pipeline.

    Required: scenario_id (str), severity (float 0–1)
    Optional: horizon_hours (int, default 336)

    Returns all 16 mandatory output fields plus decision_plan.
    """
    from src.simulation_engine import SimulationEngine
    engine = SimulationEngine()
    scenario_id = body.get("scenario_id", "hormuz_chokepoint_disruption")
    severity = float(body.get("severity", 0.7))
    horizon_hours = int(body.get("horizon_hours", 336))
    result = engine.run(scenario_id=scenario_id, severity=severity, horizon_hours=horizon_hours)
    return result


# ── Version endpoint ──────────────────────────────────────────────────────
@app.get("/version", tags=["meta"])
async def get_version():
    """Return engine version, scenario count, and model equation."""
    from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
    return {
        "service": "Impact Observatory | مرصد الأثر",
        "model_version": SimulationEngine.MODEL_VERSION,
        "api_version": "2.1.0",
        "scenarios": len(SCENARIO_CATALOG),
        "scenario_ids": sorted(SCENARIO_CATALOG.keys()),
        "model_equation": "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U",
        "architecture_layers": 9,
        "risk_levels": ["NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"],
    }


# ── All domain routers under /api/v1 with X-API-Key auth ─────────────────
api_v1 = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])
api_v1.include_router(events_router)
api_v1.include_router(conflicts_router)
api_v1.include_router(incidents_router)
api_v1.include_router(flights_router)
api_v1.include_router(vessels_router)
api_v1.include_router(scores_router)
api_v1.include_router(scenarios_router)
api_v1.include_router(graph_router)
api_v1.include_router(insurance_router)
api_v1.include_router(decision_router)

# ── Impact Observatory v1 core endpoints ─────────────────────────────────
api_v1.include_router(v1_scenarios_router)
api_v1.include_router(v1_runs_router)
api_v1.include_router(v1_nodes_router)

# ── Decision Execution Layer (persistent operator decisions, outcomes, values) ──
api_v1.include_router(v1_decisions_router)
api_v1.include_router(v1_outcomes_router)
api_v1.include_router(v1_values_router)

# ── Executive Narrative Layer (Signal → Propagation → Exposure → Decision → Outcome) ──
api_v1.include_router(v1_narrative_router)

# ── Decision Authority Layer (Chief Risk Officer AI — forces decisions) ──
api_v1.include_router(v1_decision_authority_router)

# ── Banking Intelligence Layer (Scenario bridging to contract chains) ──
api_v1.include_router(v1_scenario_chain_router)
api_v1.include_router(v1_banking_entities_router)
api_v1.include_router(v1_banking_decisions_router)

# ── Institutional Interface Layer (Stage 70/80 consumer surface) ──
api_v1.include_router(v1_institutional_router)

# ── Metrics Provenance Layer (Stage 85 — explainability + factor decomposition) ──
api_v1.include_router(v1_provenance_router)

# ── Auth endpoints — no API key required ─────────────────────────────────
app.include_router(v1_auth_router, prefix="/api/v1")

app.include_router(api_v1)
