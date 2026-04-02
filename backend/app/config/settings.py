"""
Configuration management for Impact Observatory | مرصد الأثر.
Decision Intelligence Platform for GCC Financial Impact.
Uses Pydantic Settings with environment variable support.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable overrides.
    Use IO_ prefix for environment variables (e.g., IO_ENVIRONMENT=production)
    """

    # Application
    app_name: str = "Impact Observatory"
    app_version: str = "1.0.0"
    environment: str = "development"  # development | pilot | production
    debug: bool = False
    log_level: str = "INFO"

    # PostgreSQL + PostGIS
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "impact_observatory"
    postgres_user: str = "io_admin"
    postgres_password: str = "io_pilot_2026"
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10
    postgres_pool_pre_ping: bool = True
    postgres_echo: bool = False

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "io_graph_2026"
    neo4j_pool_size: int = 50

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_socket_keepalive: bool = True
    redis_socket_keepalive_options: dict = {}

    # API
    api_prefix: str = "/api/v1"
    allowed_origins: str = "http://localhost:3000"
    api_timeout: int = 30

    # Ingestion
    acled_api_key: str = ""
    acled_api_email: str = ""
    acled_base_url: str = "https://api.acleddata.com"

    # Database connection URLs
    @property
    def postgres_url(self) -> str:
        """Async PostgreSQL connection URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def postgres_sync_url(self) -> str:
        """Synchronous PostgreSQL connection URL for Alembic migrations."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_prefix = "IO_"
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields for flexibility


def get_settings() -> Settings:
    """Factory function to get application settings."""
    return Settings()
