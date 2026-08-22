"""Error-envelope, integrity-classification, and request-ID tests."""

import asyncio
import json
import logging
import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator
from sqlalchemy.exc import IntegrityError

from app.main import register_exception_handlers, register_middleware


class FakeDriverError(Exception):
    """Minimal Psycopg-style exception for API-handler tests."""

    def __init__(
        self,
        *,
        sqlstate: str | None,
        constraint_name: str | None,
    ) -> None:
        super().__init__("private driver message about secret_col")

        self.sqlstate = sqlstate
        self.diag = SimpleNamespace(
            sqlstate=sqlstate,
            constraint_name=constraint_name,
        )


def make_integrity_error(
    *,
    sqlstate: str | None,
    constraint_name: str | None,
) -> IntegrityError:
    return IntegrityError(
        ("INSERT INTO private_table(secret_col) VALUES (%(value)s)"),
        {"value": "private-value"},
        FakeDriverError(
            sqlstate=sqlstate,
            constraint_name=constraint_name,
        ),
    )


def get_integrity_handler():
    application = FastAPI()
    register_exception_handlers(application)

    handler = application.exception_handlers.get(IntegrityError)

    assert handler is not None
    return handler


def make_request(request_id: str):
    return SimpleNamespace(
        state=SimpleNamespace(request_id=request_id),
    )


@pytest.fixture
def handler_app():
    application = FastAPI()

    register_middleware(application)
    register_exception_handlers(application)

    class Body(BaseModel):
        name: str

        @field_validator("name")
        @classmethod
        def _no_bad(cls, value: str) -> str:
            if value == "bad":
                raise ValueError("secret internal reason")

            return value

    @application.post("/echo")
    def echo(body: Body):
        return {"ok": True}

    @application.get("/boom")
    def boom():
        raise RuntimeError("stack trace with secrets")

    @application.get("/missing")
    def missing():
        raise HTTPException(status_code=404)

    @application.get("/http-422")
    def http_422():
        raise HTTPException(status_code=422, detail="Invalid business input")

    @application.get("/auth-required")
    def auth_required():
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with TestClient(
        application,
        raise_server_exceptions=False,
    ) as client:
        yield client


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


@pytest.mark.api
def test_validator_valueerror_returns_422_not_500(handler_app):
    response = handler_app.post(
        "/echo",
        json={"name": "bad"},
    )

    assert response.status_code == 422

    error = response.json()["error"]

    assert error["code"] == "VALIDATION_ERROR"
    assert "details" in error
    assert _is_uuid(error["request_id"])
    assert "secret internal reason" not in response.text
    assert all(set(detail) <= {"loc", "type"} for detail in error["details"])
    assert any("name" in detail["loc"] for detail in error["details"])


@pytest.mark.api
def test_missing_field_uses_details_not_detail(handler_app):
    response = handler_app.post("/echo", json={})

    assert response.status_code == 422

    body = response.json()

    assert "detail" not in body
    assert "details" in body["error"]


@pytest.mark.api
def test_unexpected_exception_returns_internal_error_without_leak(
    handler_app,
):
    response = handler_app.get("/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "stack trace with secrets" not in response.text


@pytest.mark.api
@pytest.mark.parametrize(
    (
        "sqlstate",
        "constraint_name",
        "expected_status",
        "expected_code",
    ),
    [
        (
            "23505",
            "uq_zones_code_canonical",
            409,
            "DUPLICATE_RESOURCE",
        ),
        (
            "23503",
            "fk_private",
            409,
            "CONFLICT",
        ),
        (
            "23514",
            "ck_zones_code_not_blank",
            422,
            "VALIDATION_ERROR",
        ),
        (
            "23514",
            "ck_internal_only",
            500,
            "INTERNAL_ERROR",
        ),
        (
            "23502",
            "private_not_null",
            500,
            "INTERNAL_ERROR",
        ),
        (
            None,
            None,
            500,
            "INTERNAL_ERROR",
        ),
    ],
)
def test_integrity_handler_uses_safe_classification(
    sqlstate,
    constraint_name,
    expected_status,
    expected_code,
):
    request_id = "22222222-2222-2222-2222-222222222222"

    handler = get_integrity_handler()

    error = make_integrity_error(
        sqlstate=sqlstate,
        constraint_name=constraint_name,
    )

    response = asyncio.run(
        handler(
            make_request(request_id),
            error,
        )
    )

    body = json.loads(response.body)["error"]

    assert response.status_code == expected_status
    assert body["code"] == expected_code
    assert body["request_id"] == request_id
    assert response.headers["X-Request-ID"] == request_id

    response_text = response.body.decode()

    assert "private_table" not in response_text
    assert "secret_col" not in response_text
    assert "private-value" not in response_text
    assert "private driver message" not in response_text
    assert str(constraint_name) not in response_text
    assert str(sqlstate) not in response_text


@pytest.mark.api
def test_integrity_handler_logs_only_safe_metadata(caplog):
    request_id = "33333333-3333-3333-3333-333333333333"

    handler = get_integrity_handler()

    error = make_integrity_error(
        sqlstate="23505",
        constraint_name="uq_zones_code_canonical",
    )

    with caplog.at_level(
        logging.WARNING,
        logger="verdeza",
    ):
        asyncio.run(
            handler(
                make_request(request_id),
                error,
            )
        )

    assert request_id in caplog.text
    assert "FakeDriverError" in caplog.text
    assert "23505" in caplog.text
    assert "uq_zones_code_canonical" in caplog.text
    assert "DUPLICATE_RESOURCE" in caplog.text

    assert "private_table" not in caplog.text
    assert "secret_col" not in caplog.text
    assert "private-value" not in caplog.text
    assert "private driver message" not in caplog.text


@pytest.mark.api
def test_404_envelope_shape(handler_app):
    response = handler_app.get("/missing")

    assert response.status_code == 404

    error = response.json()["error"]

    assert error["code"] == "RESOURCE_NOT_FOUND"
    assert set(error) >= {
        "code",
        "message",
        "request_id",
    }


@pytest.mark.api
@pytest.mark.parametrize(
    "path",
    ["/boom", "/missing"],
)
def test_every_error_has_request_id_header_and_body(
    handler_app,
    path,
):
    response = handler_app.get(path)

    assert "X-Request-ID" in response.headers
    assert _is_uuid(response.json()["error"]["request_id"])


@pytest.mark.api
def test_valid_incoming_request_id_is_echoed(handler_app):
    request_id = str(uuid.uuid4())

    response = handler_app.get(
        "/missing",
        headers={"x-request-id": request_id},
    )

    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["error"]["request_id"] == request_id


@pytest.mark.api
def test_invalid_incoming_request_id_is_replaced(
    handler_app,
):
    response = handler_app.get(
        "/missing",
        headers={"x-request-id": "not-a-uuid"},
    )

    received = response.headers["X-Request-ID"]

    assert received != "not-a-uuid"
    assert _is_uuid(received)


@pytest.mark.api
def test_absent_request_id_is_generated(handler_app):
    response = handler_app.get("/missing")

    assert _is_uuid(response.headers["X-Request-ID"])


@pytest.mark.api
def test_http_exception_422_returns_validation_error(handler_app):
    response = handler_app.get("/http-422")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"] == "Invalid business input"


@pytest.mark.api
def test_http_exception_forwards_custom_headers(handler_app):
    response = handler_app.get("/auth-required")

    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
