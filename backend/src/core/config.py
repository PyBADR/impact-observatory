"""Impact Observatory | مرصد الأثر — Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "impact_observatory"
    postgres_user: str = "observatory_admin"
    postgres_password: str = "changeme"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API authentication
    api_key: str = ""
    acled_api_key: str = ""
    acled_api_email: str = ""

    # Real-time data feeds (optional)
    acled_email: str = ""
    aisstream_api_key: str = ""
    opensky_username: str = ""
    opensky_password: str = ""
    feed_refresh_minutes: int = 15

    # Cesium / Mapbox tokens
    cesium_ion_token: str = ""
    next_public_mapbox_token: str = ""
    next_public_cesium_token: str = ""

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "info"
    cors_origins: str = "http://localhost:3000,https://deevo-sim.vercel.app"

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
