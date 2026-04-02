"""FastAPI Application - Phase 7

Main application entry point for Impact Observatory GCC platform.
Sets up routes, middleware, and application lifecycle management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import Settings
from app.graph.client import GraphClient
from app.api import health, scenarios, entities, graph, ingest, auth, pipeline, conflicts, incidents, insurance, decision, scores
from app.api.observatory import router as observatory_router
from app.services.pipeline_status import PipelineStatusTracker
from app.services.orchestrator import LifecycleOrchestrator
from app.services.normalization import NormalizationService
from app.services.graph_ingestion import GraphIngestionService
from app.services.graph_query import GraphQueryService
from app.services.scoring_service import ScoringService
from app.services.physics_service import PhysicsService
from app.services.insurance_service import InsuranceService
from app.services.enrichment import EnrichmentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Global service instances
graph_client: GraphClient = None
pipeline_status_tracker: PipelineStatusTracker = None
lifecycle_orchestrator: LifecycleOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Impact Observatory application...")
    
    try:
        global graph_client, pipeline_status_tracker, lifecycle_orchestrator
        
        # Initialize graph client
        graph_client = GraphClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            max_connection_pool_size=settings.neo4j_max_pool_size,
            connection_timeout=settings.neo4j_timeout
        )
        
        await graph_client.initialize()
        schema = GraphSchema()
        await graph_client.initialize_schema(schema)
        
        logger.info("Graph database initialized successfully")
        
        # Store in app state for access in routes
        app.state.graph_client = graph_client
        
        # Initialize pipeline status tracker with Redis
        pipeline_status_tracker = PipelineStatusTracker(redis_url=settings.redis_url)
        await pipeline_status_tracker.initialize()
        app.state.pipeline_status_tracker = pipeline_status_tracker
        logger.info("Pipeline status tracker initialized successfully")
        
        # Initialize all service dependencies for lifecycle orchestrator
        normalization_service = NormalizationService()
        graph_ingestion_service = GraphIngestionService(graph_client=graph_client)
        graph_query_service = GraphQueryService(graph_client=graph_client)
        scoring_service = ScoringService()
        physics_service = PhysicsService()
        insurance_service = InsuranceService()
        enrichment_service = EnrichmentService()
        
        logger.info("Initializing service dependencies for lifecycle orchestrator")
        
        # Initialize lifecycle orchestrator with all service dependencies
        lifecycle_orchestrator = LifecycleOrchestrator(
            normalization_service=normalization_service,
            graph_ingestion_service=graph_ingestion_service,
            graph_query_service=graph_query_service,
            scoring_service=scoring_service,
            physics_service=physics_service,
            insurance_service=insurance_service,
            enrichment_service=enrichment_service,
            status_tracker=pipeline_status_tracker,
        )
        await lifecycle_orchestrator.initialize()
        app.state.lifecycle_orchestrator = lifecycle_orchestrator
        logger.info("Lifecycle orchestrator initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Impact Observatory application...")
    try:
        if graph_client:
            await graph_client.close()
            logger.info("Graph database connection closed")
        
        if pipeline_status_tracker:
            await pipeline_status_tracker.close()
            logger.info("Pipeline status tracker connection closed")
        
        if lifecycle_orchestrator:
            await lifecycle_orchestrator.cleanup()
            logger.info("Lifecycle orchestrator cleaned up")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="Impact Observatory GCC Platform",
    description="Decision Intelligence Platform for GCC Financial Impact | مرصد الأثر",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, 'allowed_origins', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"]
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=getattr(settings, 'trusted_hosts', ["*"])
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(scenarios.router, prefix=settings.api_prefix, tags=["Scenarios"])
app.include_router(entities.router, prefix=settings.api_prefix, tags=["Entities"])
app.include_router(graph.router, prefix=settings.api_prefix, tags=["Graph Intelligence"])
app.include_router(ingest.router, prefix=settings.api_prefix, tags=["Data Ingestion"])
app.include_router(pipeline.router, prefix=settings.api_prefix, tags=["Lifecycle Pipeline"])
app.include_router(conflicts.router, prefix=settings.api_prefix, tags=["Conflict Intelligence"])
app.include_router(incidents.router, prefix=settings.api_prefix, tags=["Incident Intelligence"])
app.include_router(insurance.router, prefix=settings.api_prefix, tags=["Insurance Portfolio"])
app.include_router(decision.router, prefix=settings.api_prefix, tags=["Decision Generation"])
app.include_router(scores.router, prefix=settings.api_prefix, tags=["Risk Scores"])

# Impact Observatory — Core pipeline router
app.include_router(observatory_router, prefix=settings.api_prefix, tags=["Observatory"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Impact Observatory | مرصد الأثر",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "docs": "/api/docs",
            "api_prefix": settings.api_prefix
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode,
        log_level="info"
    )
