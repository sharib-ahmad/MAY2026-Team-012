"""Database engine and session factories.

No import-time engine. The application owns exactly one engine, built
by create_app() onto app.state and disposed on shutdown. get_db resolves that
factory from request.app.state — there is no module-level fallback pool that
could use different settings.

Scripts that need a session outside a request build their own engine explicitly
from settings; that is intentional.
"""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str) -> Engine:
    """Build an engine for an explicit URL. The URL is required."""
    return create_engine(url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a session from the running app's session factory (app.state)."""
    factory: sessionmaker = request.app.state.session_factory
    db = factory()
    try:
        yield db
    finally:
        db.close()
