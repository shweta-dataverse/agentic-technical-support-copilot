"""Alembic migration environment.

Reads the database URL from application settings so migrations always target
the same database the service is configured for.
"""

from alembic import context
from sqlalchemy import engine_from_config, pool

from copilot.config import get_settings

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# populated from the ORM metadata once the v2 schema lands (step 2)
target_metadata = None


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live database connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
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
