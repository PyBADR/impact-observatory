"""Alembic environment — sync driver for migrations.

Uses postgres_sync_dsn (psycopg2) since Alembic runs synchronously.
Imports all ORM models so Base.metadata reflects the full schema.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.core.config import settings
from src.db.postgres import Base

# Import ALL ORM model modules so Base.metadata knows every table
import src.models.orm  # noqa: F401
import src.models.action_tracking  # noqa: F401
import src.models.enterprise  # noqa: F401
import src.data_foundation.models.tables  # noqa: F401
import src.data_foundation.evaluation.orm_models  # noqa: F401
import src.data_foundation.governance.orm_models  # noqa: F401
import src.data_foundation.enforcement.orm_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.postgres_sync_dsn)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without connecting to the database."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
