"""Impact Observatory | مرصد الأثر — FastAPI application entry point.

Decision Intelligence Platform for GCC Financial Markets.
Every output maps: Event → Financial Impact → Sector Stress → Decision
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

from src.core.config import settings
from src.services.state import init_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # Startup
    init_state()

    # Optional: connect to databases if available (with 5s timeout each)
    try:
        from src.db.neo4j import init_neo4j
        await asyncio.wait_for(init_neo4j(), timeout=5.0)
        print("✅ Neo4j connected")
    except Exception as e:
        print(f"⚠️ Neo4j skipped: {e}")

    try:
        from src.db.redis import init_redis
        await asyncio.wait_for(init_redis(), timeout=5.0)
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis skipped: {e}")

    print("🚀 Impact Observatory ready")
    yield

    # Shutdown
    try:
        from src.db.neo4j import close_neo4j
        await close_neo4j()
    except Exception:
        pass
    try:
        from src.db.redis import close_redis
        await close_redis()
    except Exception:
        pass


app = FastAPI(
    title="Impact Observatory | مرصد الأثر",
    description="Decision Intelligence Platform for GCC Financial Markets. "
    "Every output maps: Event → Financial Impact → Sector Stress → Decision",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health stays at root — no auth, no prefix
app.include_router(health_router)

# All domain routers under /api/v1 with X-API-Key auth
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

# ── Impact Observatory v1 endpoints ──
api_v1.include_router(v1_scenarios_router)
api_v1.include_router(v1_runs_router)

app.include_router(api_v1)
