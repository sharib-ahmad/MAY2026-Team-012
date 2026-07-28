"""Alembic environment.

URL handling: the database URL is passed programmatically to
engine_from_config, NOT via config.set_main_option, because ConfigParser
performs %-interpolation and a URL-encoded password containing '%' would be
mangled. Passing it in the config dict avoids interpolation entirely.

compare_server_default=True so a change to a column default is
detected by autogenerate. compare_type=True catches type changes. Generated
migrations are still reviewed by a human before commit.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url() -> str:
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    # Inject the URL programmatically so ConfigParser never interpolates it.
    section["sqlalchemy.url"] = _url()
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
