"""Alembic migration environment.

The database URL is passed programmatically to avoid ConfigParser percent
interpolation problems with URL-encoded passwords.

Alembic loads DatabaseSettings rather than the complete application Settings,
because migrations require DATABASE_URL but do not require SECRET_KEY.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_database_settings
from app.models import Base  # imports models for autogenerate

config = context.config

if config.config_file_name is not None:
    fileConfig(
        config.config_file_name,
        disable_existing_loggers=False,
    )

target_metadata = Base.metadata


def get_database_url() -> str:
    """Return the migration database URL without loading application secrets."""

    return get_database_settings().DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    section = config.get_section(config.config_ini_section, {})

    # Inject the URL through the configuration dictionary so ConfigParser
    # does not interpolate percent characters in URL-encoded credentials.
    section["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
