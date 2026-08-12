"""FastAPI application.

App factory (create_app) builds settings, engine and session factory onto
app.state, and a lifespan disposes the engine on shutdown.

Request IDs: middleware accepts an incoming X-Request-ID only when it
is a valid UUID, otherwise generates one; stores it on request.state.request_id;
adds it to every response header; exception handlers and logs use the stored
value.

Error envelope:
{"error": {"code","message","details?","request_id"}} with UPPER_SNAKE codes
matching api-doc.yaml. Internal details such as SQL and stack traces are never
exposed.
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
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings
from app.core.db_errors import (
    classify_integrity_error,
    extract_constraint_name,
    extract_sqlstate,
)
from app.db.session import make_engine, make_session_factory

logger = logging.getLogger("verdeza")


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details=None,
) -> JSONResponse:
    """Return the standard public API error envelope."""

    body = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }

    if details is not None:
        body["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=body,
        headers={"X-Request-ID": request_id},
    )


def _request_id(request: Request) -> str:
    """Return the middleware request ID or generate a safe fallback."""

    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def _valid_uuid(value: str | None) -> str | None:
    """Return a normalised UUID or None when the value is invalid."""

    if not value:
        return None

    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        return None


def register_middleware(app: FastAPI) -> None:
    """Register application-wide middleware."""

    @app.middleware("http")
    async def request_id_mw(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _valid_uuid(request.headers.get("x-request-id")) or str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def _validation(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        # Expose only which field failed and the error category.
        # Validator messages and contexts may contain internal details.
        safe_details = jsonable_encoder(
            [
                {
                    "loc": list(error.get("loc", [])),
                    "type": error.get("type", "value_error"),
                }
                for error in exc.errors()
            ]
        )

        return error_response(
            422,
            "VALIDATION_ERROR",
            "The request contains invalid data.",
            _request_id(request),
            details=safe_details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
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
        if isinstance(exc.detail, dict):
            code = exc.detail.get("code", code)
            message = exc.detail.get("message", message)

        return error_response(
            exc.status_code,
            code,
            message,
            _request_id(request),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity(
        request: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        request_id = _request_id(request)
        result = classify_integrity_error(exc)
        sqlstate = extract_sqlstate(exc)
        constraint_name = extract_constraint_name(exc)

        original = getattr(exc, "orig", None)
        exception_type = type(original).__name__ if original is not None else type(exc).__name__

        log_method = logger.error if result.status_code >= 500 else logger.warning

        log_method(
            "integrity_error request_id=%s exception_type=%s "
            "sqlstate=%s constraint=%s response_code=%s",
            request_id,
            exception_type,
            sqlstate,
            constraint_name,
            result.code,
        )

        return error_response(
            result.status_code,
            result.code,
            result.message,
            request_id,
        )

    @app.exception_handler(Exception)
    async def _unexpected(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = _request_id(request)

        # Keep the cause in protected server logs, never in the response.
        logger.exception(
            "unhandled_exception request_id=%s",
            request_id,
        )

        return error_response(
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            request_id,
        )


def seed_database(session_factory) -> None:
    """Seed reference data needed by local development only."""
    from sqlalchemy import select

    from app.core.security import get_password_hash
    from app.features.credits.models import CreditFactor
    from app.features.sorting_guide.models import WasteCategory
    from app.features.users.models import User
    from app.models.enums import Role, UserStatus
    from app.models.zone import Zone

    with session_factory() as db:
        # 1. Seed Waste Categories if none exist
        existing_categories = set(db.scalars(select(WasteCategory.code)).all())
        new_categories = []
        for code, label, order in [
            ("WET", "Wet Waste", 1),
            ("DRY", "Dry Waste", 2),
            ("HAZARDOUS", "Hazardous Waste", 3),
            ("Daily Waste", "Daily Waste", 4),
        ]:
            if code not in existing_categories:
                new_categories.append(
                    WasteCategory(code=code, label=label, sort_order=order, is_active=True)
                )
        if new_categories:
            db.add_all(new_categories)
            db.flush()

        # 1b. Seed credit factors per waste category
        existing_factors = set(db.scalars(select(CreditFactor.category)).all())
        new_factors = []
        for cat, rate, co2, desc in [
            ("WET", 0.5, 0.3, "Wet waste recycling rate"),
            ("DRY", 1.0, 0.8, "Dry waste recycling rate"),
            ("HAZARDOUS", 2.0, 1.5, "Hazardous waste safe disposal rate"),
            ("Daily Waste", 0.5, 0.3, "Daily household waste collection rate"),
        ]:
            if cat not in existing_factors:
                new_factors.append(
                    CreditFactor(category=cat, credit_rate=rate, co2_factor=co2, description=desc)
                )
        if new_factors:
            db.add_all(new_factors)
            db.flush()

        # 2. Seed Zones if they don't exist
        default_zones = [
            ("Gomti Nagar", "WARD-01", "Sector 1, Sector 2"),
            ("Hazratganj", "WARD-02", "Sector 3, Sector 4"),
            ("Alambagh", "WARD-03", "Sector 5"),
            ("Indira Nagar", "WARD-04", "Sector 6"),
            ("Chowk", "WARD-05", "Sector 7"),
        ]
        for name, code, sectors in default_zones:
            zone = db.scalar(select(Zone).where(Zone.code.in_([code, code.replace("WARD-", "W-")])))
            if not zone:
                new_zone = Zone(name=name, code=code, sectors=sectors)
                db.add(new_zone)
        db.flush()

        # Get WARD-01 zone for linking users
        zone_w01 = db.scalar(select(Zone).where(Zone.code.in_(["WARD-01", "W-01"])))
        zone_id = zone_w01.id if zone_w01 else None

        # 3. Seed Users if email doesn't exist
        password_hash = get_password_hash("password123")

        seeds = [
            ("Demo Admin", "admin@verdeza.test", "+919999999999", Role.SYSTEM_ADMIN, None),
            (
                "Demo Manager",
                "manager@verdeza.test",
                "+919876543213",
                Role.MUNICIPAL_OFFICER,
                zone_id,
            ),
            ("Demo Citizen", "citizen@verdeza.test", "+919876543214", Role.CITIZEN, zone_id),
            (
                "Demo Collector",
                "collector@verdeza.test",
                "+919876543215",
                Role.COLLECTION_WORKER,
                zone_id,
            ),
            ("Demo Recycler", "recycler@verdeza.test", "+919876543216", Role.RECYCLER, None),
        ]

        for name, email, phone, role, z_id in seeds:
            user = db.scalar(select(User).where((User.email == email) | (User.phone == phone)))
            if not user:
                new_user = User(
                    name=name,
                    email=email,
                    phone=phone,
                    password_hash=password_hash,
                    role=role,
                    zone_id=z_id,
                    status=UserStatus.ACTIVE,
                )
                db.add(new_user)
        db.commit()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure one FastAPI application instance."""

    current = settings or get_settings()

    # Register every SQLAlchemy model before request handlers configure their
    # relationships. Citizen pickup endpoints reference models outside the
    # authentication feature, so lazy partial registration breaks login.
    from app.db import registry as _model_registry  # noqa: F401

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if current.APP_ENV != "test":
            try:
                seed_database(app.state.session_factory)
            except Exception as exc:
                logger.exception("database_seeding_failed: %s", exc)
        yield

        # Dispose the application-owned connection pool on shutdown.
        app.state.engine.dispose()

    app = FastAPI(
        title="Verdeza API",
        version="0.1.0",
        description=("Sustainable Waste Management & Recycling Platform - MAY2026-Team-012."),
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        lifespan=lifespan,
    )

    app.state.settings = current
    app.state.engine = make_engine(current.DATABASE_URL)
    app.state.session_factory = make_session_factory(app.state.engine)

    register_middleware(app)
    register_exception_handlers(app)

    from app.api.v1.router import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """Liveness only. Never touches the database."""

        return {
            "status": "ok",
            "env": current.APP_ENV,
        }

    @app.get("/ready", tags=["system"])
    def ready(request: Request) -> JSONResponse:
        """Verify that the running application's database accepts a query."""

        request_id = _request_id(request)

        try:
            with request.app.state.session_factory() as session:
                session.execute(text("SELECT 1")).scalar_one()
        except SQLAlchemyError as exc:
            # The traceback is retained only in protected server logs.
            # The client receives no SQL, connection or driver details.
            logger.warning(
                "readiness_failed request_id=%s error_type=%s",
                request_id,
                type(exc).__name__,
                exc_info=True,
            )

            return error_response(
                503,
                "DATABASE_UNAVAILABLE",
                "The service is temporarily unavailable.",
                request_id,
            )

        return JSONResponse(
            status_code=200,
            content={"status": "ready"},
            headers={"X-Request-ID": request_id},
        )

    return app


app = create_app()
