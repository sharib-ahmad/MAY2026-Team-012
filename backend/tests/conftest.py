"""Shared pytest fixtures.

The pytest schema is created through the real Alembic migrations rather than
SQLAlchemy create_all.

Destructive setup is refused unless APP_ENV=test and the configured database
name ends in _test.

Application tests use create_app() with explicit Settings so each application
owns its engine and session factory.
"""

import re

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.core.config import (
    DatabaseSettings,
    Settings,
    get_database_settings,
)
from app.db.session import get_db
from app.main import create_app
from app.models.zone import Zone


def _assert_safe_test_database(
    database_settings: DatabaseSettings,
) -> None:
    """Prevent destructive test setup against a non-test database."""

    if not database_settings.is_test:
        raise RuntimeError(
            f"Refusing test DB setup: APP_ENV is {database_settings.APP_ENV!r}, not 'test'."
        )

    database_name = make_url(database_settings.DATABASE_URL).database or ""

    if not re.search(r"_test$", database_name):
        raise RuntimeError(
            f"Refusing test DB setup: database {database_name!r} does not end in '_test'."
        )


@pytest.fixture(scope="session")
def engine():
    """Create the test engine after applying the real Alembic migrations."""

    database_settings = get_database_settings()
    _assert_safe_test_database(database_settings)

    test_engine = create_engine(
        database_settings.DATABASE_URL,
        future=True,
    )

    alembic_config = Config("alembic.ini")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")

    yield test_engine

    test_engine.dispose()


@pytest.fixture
def db(engine):
    """Provide a transaction-isolated database session for each test."""

    connection = engine.connect()
    transaction = connection.begin()

    session = sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def app_test():
    """Build an application with explicit test configuration."""

    database_settings = get_database_settings()

    test_settings = Settings(
        APP_ENV="test",
        SECRET_KEY="",
        DATABASE_URL=database_settings.DATABASE_URL,
    )

    return create_app(test_settings)


@pytest.fixture
def app_client():
    """Provide an application client for database-independent behaviour."""

    application = create_app()

    with TestClient(application) as client:
        yield client


@pytest.fixture
def db_client(app_test, db):
    """Override get_db with the transaction-isolated test session."""

    app_test.dependency_overrides[get_db] = lambda: db

    try:
        with TestClient(app_test) as client:
            yield client
    finally:
        app_test.dependency_overrides.pop(get_db, None)


@pytest.fixture
def ward_a(db):
    """Create a standard Zone fixture."""

    zone = Zone(name="Ward A", code="W-04")
    db.add(zone)
    db.flush()

    return zone
