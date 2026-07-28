"""Database engine and session factories.

No import-time engine. The application owns exactly one engine, built by
create_app() onto app.state and disposed on shutdown. get_db resolves that
factory from request.app.state, so every request uses the running app's
configured database.
"""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str) -> Engine:
    """Build an engine for an explicit database URL."""

    return create_engine(
        url,
        pool_pre_ping=True,
        future=True,
    )


def make_session_factory(engine: Engine) -> sessionmaker:
    """Build the application's synchronous SQLAlchemy session factory."""

    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a request-scoped session and clean up its transaction safely."""

    factory: sessionmaker = request.app.state.session_factory
    db = factory()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
