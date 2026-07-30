"""Application-factory wiring tests."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app

PG = "postgresql+psycopg://user:pass@localhost:5432/verdeza_test"


@pytest.mark.unit
def test_create_app_builds_engine_from_given_settings():
    s = Settings(APP_ENV="test", SECRET_KEY="", DATABASE_URL=PG)
    app = create_app(s)
    assert app.state.settings is s
    assert app.state.engine is not None
    assert app.state.session_factory is not None


@pytest.mark.unit
def test_get_db_uses_app_state_factory():
    """get_db must yield from the running app's factory and close it.

    Uses a mock session so the unit test is genuinely DB-independent."""
    app = create_app(Settings(APP_ENV="test", SECRET_KEY="", DATABASE_URL=PG))
    session = MagicMock()
    app.state.session_factory = MagicMock(return_value=session)

    class DummyRequest:
        pass

    request = DummyRequest()
    request.app = app

    generator = get_db(request)
    assert next(generator) is session
    generator.close()

    app.state.session_factory.assert_called_once()
    session.close.assert_called_once()


@pytest.mark.unit
def test_lifespan_disposes_engine_on_shutdown():
    """Application shutdown must dispose the engine.

    Prove it through the TestClient lifecycle + a spy on the engine's dispose,
    not by calling dispose() manually."""
    app = create_app(Settings(APP_ENV="test", SECRET_KEY="", DATABASE_URL=PG))
    with patch.object(app.state.engine, "dispose", wraps=app.state.engine.dispose) as spy:
        # Entering and exiting the context runs startup and shutdown.
        with TestClient(app):
            pass
        spy.assert_called_once()
