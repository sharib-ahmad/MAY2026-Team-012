"""FastAPI application.

App factory (create_app) builds settings, engine and session factory onto
app.state, and a lifespan disposes the engine on shutdown.

Request IDs: middleware accepts an incoming X-Request-ID only when it
is a valid UUID, otherwise generates one; stores it on request.state.request_id;
adds it to every response header; exception handlers and logs use the stored
value.

Error envelope: one shape everywhere —
{"error": {"code","message","details?","request_id"}} — with UPPER_SNAKE codes
matching api-doc.yaml. Internal details (SQL, stack traces) are never exposed.
"""

import logging
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings
from app.db.session import make_engine, make_session_factory

logger = logging.getLogger("verdeza")


def error_response(status_code: int, code: str, message: str, request_id: str, details=None):
    body = {"error": {"code": code, "message": message, "request_id": request_id}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers={"X-Request-ID": request_id})


def _request_id(request: Request) -> str:
    # Set by middleware; fall back to a fresh UUID if middleware was bypassed.
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def _valid_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        return None


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_mw(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = _valid_uuid(request.headers.get("x-request-id")) or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        # Expose only which field failed (loc) and the error category (type) —
        # never msg/ctx/url, which can carry a raw validator exception string
        # (no internal leak).
        safe = jsonable_encoder(
            [
                {"loc": list(e.get("loc", [])), "type": e.get("type", "value_error")}
                for e in exc.errors()
            ]
        )
        return error_response(
            422,
            "VALIDATION_ERROR",
            "The request contains invalid data.",
            _request_id(request),
            details=safe,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code_map = {
            400: "BAD_REQUEST",
            401: "AUTHENTICATION_REQUIRED",
            403: "FORBIDDEN",
            404: "RESOURCE_NOT_FOUND",
            409: "CONFLICT",
            503: "DATABASE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "ERROR")
        message = exc.detail if isinstance(exc.detail, str) else code.replace("_", " ").title()
        return error_response(exc.status_code, code, message, _request_id(request))

    @app.exception_handler(IntegrityError)
    async def _integrity(request: Request, exc: IntegrityError):
        rid = _request_id(request)
        logger.warning("integrity_error request_id=%s", rid)
        return error_response(
            409,
            "DUPLICATE_RESOURCE",
            "A resource with the same unique value already exists.",
            rid,
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        rid = _request_id(request)
        # Log the detail server-side; never send it to the client.
        logger.exception("unhandled_exception request_id=%s", rid)
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred.", rid)


def create_app(settings: Settings | None = None) -> FastAPI:
    current = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        # Dispose the engine's connection pool on shutdown.
        app.state.engine.dispose()

    app = FastAPI(
        title="Verdeza API",
        version="0.1.0",
        description="Sustainable Waste Management & Recycling Platform — MAY2026-Team-012.",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        lifespan=lifespan,
    )

    app.state.settings = current
    app.state.engine = make_engine(current.DATABASE_URL)
    app.state.session_factory = make_session_factory(app.state.engine)

    register_middleware(app)
    register_exception_handlers(app)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """Liveness only. Never touches the database."""
        return {"status": "ok", "env": current.APP_ENV}

    @app.get("/ready", tags=["system"])
    def ready(request: Request) -> JSONResponse:
        """Readiness: verifies the database answers a trivial query."""
        session = app.state.session_factory()
        try:
            session.execute(text("SELECT 1"))
        except Exception:
            logger.warning("readiness_failed request_id=%s", _request_id(request))
            return error_response(
                503, "DATABASE_UNAVAILABLE", "database unavailable", _request_id(request)
            )
        finally:
            session.close()
        return JSONResponse(
            status_code=200,
            content={"status": "ready"},
            headers={"X-Request-ID": _request_id(request)},
        )

    return app


app = create_app()
