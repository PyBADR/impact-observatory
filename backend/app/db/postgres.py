"""
PostgreSQL + PostGIS database connectivity and session management.
Uses SQLAlchemy 2.0 async engine with asyncpg driver.
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text
from contextlib import asynccontextmanager
import logging

from app.config.settings import Settings

logger = logging.getLogger(__name__)


def get_engine(settings: Settings) -> AsyncEngine:
    """
    Create and configure async SQLAlchemy engine for PostgreSQL.

    Args:
        settings: Application settings with database configuration

    Returns:
        Configured AsyncEngine instance
    """
    connect_args = {
        "server_settings": {
            "application_name": f"{settings.app_name}/{settings.app_version}",
            "jit": "off",
        },
        "timeout": settings.api_timeout,
    }

    engine = create_async_engine(
        settings.postgres_url,
        echo=settings.postgres_echo,
        future=True,
        pool_pre_ping=settings.postgres_pool_pre_ping,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
        connect_args=connect_args,
        poolclass=QueuePool if settings.environment != "development" else NullPool,
    )

    # Enable PostGIS extension on connection
    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Enable PostGIS extension and set search path."""
        try:
            with dbapi_conn.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp;")
                dbapi_conn.commit()
                logger.debug("PostGIS extensions enabled")
        except Exception as e:
            logger.warning(f"Could not enable PostGIS extensions: {e}")

    return engine


def get_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """
    Create async session factory.

    Args:
        engine: AsyncEngine instance

    Returns:
        Configured async_sessionmaker
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@asynccontextmanager
async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session(session_factory) as session:
            result = await session.execute(...)

    Args:
        session_factory: Session factory from get_session_factory

    Yields:
        AsyncSession instance
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(engine: AsyncEngine, metadata) -> None:
    """
    Initialize database schema by creating all tables.

    Args:
        engine: AsyncEngine instance
        metadata: SQLAlchemy MetaData with mapped models
    """
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        logger.info("Database schema initialized")


async def close_engine(engine: AsyncEngine) -> None:
    """
    Properly close engine connection pool.

    Args:
        engine: AsyncEngine instance to close
    """
    await engine.dispose()
    logger.info("Database engine closed")


async def health_check(session_factory: async_sessionmaker[AsyncSession]) -> bool:
    """
    Check database connectivity.

    Args:
        session_factory: Session factory for health check

    Returns:
        True if database is healthy, False otherwise
    """
    try:
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
