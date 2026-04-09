"""Impact Observatory | مرصد الأثر — Application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # === Core ===
    app_env: str = Field("development", description="Environment: development|staging|production")
    debug: bool = Field(False, description="Enable debug logging")
    log_level: str = Field("info", description="Logging level: debug|info|warning|error")

    # === PostgreSQL ===
    postgres_host: str = Field("localhost", description="PostgreSQL host")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_db: str = Field("impact_observatory", description="PostgreSQL database name")
    postgres_user: str = Field("observatory_admin", description="PostgreSQL user")
    postgres_password: str = Field("changeme", description="PostgreSQL password — override in production via POSTGRES_PASSWORD env var")

    # === Neo4j ===
    neo4j_uri: str = Field("bolt://localhost:7687", description="Neo4j Bolt URI")
    neo4j_user: str = Field("neo4j", description="Neo4j user")
    neo4j_password: str = Field("changeme", description="Neo4j password — override in production via NEO4J_PASSWORD env var")

    # === Redis ===
    redis_url: str = Field("redis://localhost:6379/0", description="Redis connection URL")

    # === API Security ===
    api_key: str = Field(
        "",
        description=(
            "Master API key for X-API-Key header auth. "
            "Empty string = dev mode (all requests granted CRO access). "
            "Override in production: API_KEY=<strong-random-key>"
        ),
    )

    # === JWT ===
    jwt_secret_key: str = Field(
        "io-dev-secret-change-in-prod-2026",
        description="JWT signing secret. Override in production: JWT_SECRET_KEY=<strong-random-secret>",
    )

    # === Real-time data feeds (all optional) ===
    acled_api_key: str = Field("", description="ACLED conflict events API key (optional)")
    acled_api_email: str = Field("", description="ACLED account email (optional)")
    acled_email: str = Field("", description="ACLED email alias (optional)")
    aisstream_api_key: str = Field("", description="AISStream.io WebSocket API key for vessel tracking (optional)")
    opensky_username: str = Field("", description="OpenSky Network username for flight data (optional)")
    opensky_password: str = Field("", description="OpenSky Network password (optional)")
    feed_refresh_minutes: int = Field(15, description="How often to refresh external data feeds (minutes)")

    # === Map / visualization tokens (optional) ===
    cesium_ion_token: str = Field("", description="Cesium Ion token for 3D globe rendering (optional)")
    next_public_mapbox_token: str = Field("", description="Mapbox GL JS public token (optional)")
    next_public_cesium_token: str = Field("", description="Cesium public token (optional)")

    # === Server ===
    backend_host: str = Field("0.0.0.0", description="Uvicorn bind host")
    backend_port: int = Field(8000, description="Uvicorn bind port")

    # === CORS ===
    cors_origins: str = Field(
        "http://localhost:3000,https://deevo-sim.vercel.app",
        description="Comma-separated list of allowed CORS origins. Add your Vercel/production domain here.",
    )

    # === Cache ===
    cache_warmup_limit: int = Field(2000, description="Max records per store loaded on startup cache warmup (decisions/outcomes/values)")

    # === Simulation limits ===
    max_horizon_days: int = Field(365, description="Maximum simulation time horizon in days")
    default_horizon_hours: int = Field(336, description="Default simulation time horizon in hours (14 days)")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_sync_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
