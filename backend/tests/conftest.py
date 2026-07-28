"""Shared pytest fixtures.

Deployed-schema testing: the pytest schema is built by running the
real Alembic migrations, not create_all.

Destructive-setup guard: refuses to run unless APP_ENV=test AND the DB
name ends in _test.

App-factory testing: app_test builds an app via create_app() with an
explicit test engine bound to the rolled-back connection, so /ready genuinely
exercises the injected database and create_app's own wiring is under test.
"""

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config
from app.core.config import Settings, settings
from app.db.session import get_db
from app.main import create_app
from app.models.zone import Zone


def _assert_safe_test_database() -> None:
    if not settings.is_test:
        raise RuntimeError(f"Refusing test DB setup: APP_ENV is {settings.APP_ENV!r}, not 'test'.")
    db_name = make_url(settings.DATABASE_URL).database or ""
    if not re.search(r"_test$", db_name):
        raise RuntimeError(f"Refusing test DB setup: database {db_name!r} does not end in '_test'.")


@pytest.fixture(scope="session")
def engine():
    _assert_safe_test_database()
    eng = create_engine(settings.DATABASE_URL, future=True)
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def app_test():
    """A real create_app() built with explicit test settings.

    We do NOT overwrite application.state.engine after construction — that would
    orphan the first engine undisposed. create_app builds the engine from the
    settings we pass, so it is the only one.
    """
    test_settings = Settings(
        APP_ENV="test",
        SECRET_KEY="",
        DATABASE_URL=settings.DATABASE_URL,
    )
    return create_app(test_settings)


@pytest.fixture
def app_client():
    """No database dependency; for liveness and pure-app behaviour."""
    application = create_app()
    with TestClient(application) as c:
        yield c


@pytest.fixture
def db_client(app_test, db):
    """get_db overridden to the rolled-back session on a real create_app instance."""
    app_test.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app_test) as c:
            yield c
    finally:
        app_test.dependency_overrides.pop(get_db, None)


@pytest.fixture
def ward_a(db):
    z = Zone(name="Ward A", code="W-04")
    db.add(z)
    db.flush()
    return z
