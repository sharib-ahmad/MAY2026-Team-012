"""Error-envelope and request-ID regression tests."""

import uuid

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator
from sqlalchemy.exc import IntegrityError

from app.main import register_exception_handlers, register_middleware


@pytest.fixture
def handler_app():
    app = FastAPI()
    register_middleware(app)
    register_exception_handlers(app)

    class Body(BaseModel):
        name: str

        @field_validator("name")
        @classmethod
        def _no_bad(cls, v: str) -> str:
            if v == "bad":
                raise ValueError("secret internal reason")
            return v

    @app.post("/echo")
    def echo(b: Body):
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("stack trace with secrets")

    @app.get("/missing")
    def missing():
        raise HTTPException(status_code=404)

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except (ValueError, TypeError):
        return False


@pytest.mark.api
def test_validator_valueerror_returns_422_not_500(handler_app):
    r = handler_app.post("/echo", json={"name": "bad"})
    assert r.status_code == 422
    b = r.json()["error"]
    assert b["code"] == "VALIDATION_ERROR"
    assert "details" in b  # 'details', not 'detail'
    assert _is_uuid(b["request_id"])
    # internal validator text must not leak anywhere in the response
    assert "secret internal reason" not in r.text
    # details expose which field + category only
    assert all(set(d) <= {"loc", "type"} for d in b["details"])
    assert any("name" in d["loc"] for d in b["details"])


@pytest.mark.api
def test_missing_field_uses_details_not_detail(handler_app):
    r = handler_app.post("/echo", json={})
    assert r.status_code == 422
    b = r.json()
    assert "detail" not in b  # top-level detail must not exist
    assert "details" in b["error"]


@pytest.mark.api
def test_unexpected_exception_returns_internal_error_without_leak(handler_app):
    r = handler_app.get("/boom")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "stack trace with secrets" not in r.text


@pytest.mark.api
def test_integrity_error_returns_409_without_leak():
    """Call the handler directly: a raw IntegrityError raised in a route leaves
    anyio streams unclosed under the test client, which is a test artifact, not a
    product issue. Real IntegrityErrors originate from a DB flush."""
    import asyncio

    from app.main import create_app

    app = create_app()
    # find the registered IntegrityError handler
    handler = app.exception_handlers.get(IntegrityError)
    assert handler is not None

    class Req:
        class state:
            request_id = "22222222-2222-2222-2222-222222222222"

    exc = IntegrityError("INSERT ...", {}, Exception("unique violation on secret_col"))
    resp = asyncio.run(handler(Req(), exc))
    assert resp.status_code == 409
    body = resp.body.decode()
    assert "DUPLICATE_RESOURCE" in body
    assert "secret_col" not in body
    assert resp.headers["X-Request-ID"] == "22222222-2222-2222-2222-222222222222"


@pytest.mark.api
def test_404_envelope_shape(handler_app):
    r = handler_app.get("/missing")
    assert r.status_code == 404
    b = r.json()["error"]
    assert b["code"] == "RESOURCE_NOT_FOUND"
    assert set(b) >= {"code", "message", "request_id"}


@pytest.mark.api
@pytest.mark.parametrize("path", ["/boom", "/missing"])
def test_every_error_has_request_id_header_and_body(handler_app, path):
    r = handler_app.get(path)
    assert "X-Request-ID" in r.headers
    assert _is_uuid(r.json()["error"]["request_id"])


@pytest.mark.api
def test_valid_incoming_request_id_is_echoed(handler_app):
    rid = str(uuid.uuid4())
    r = handler_app.get("/missing", headers={"x-request-id": rid})
    assert r.headers["X-Request-ID"] == rid
    assert r.json()["error"]["request_id"] == rid


@pytest.mark.api
def test_invalid_incoming_request_id_is_replaced(handler_app):
    r = handler_app.get("/missing", headers={"x-request-id": "not-a-uuid"})
    got = r.headers["X-Request-ID"]
    assert got != "not-a-uuid"
    assert _is_uuid(got)


@pytest.mark.api
def test_absent_request_id_is_generated(handler_app):
    r = handler_app.get("/missing")
    assert _is_uuid(r.headers["X-Request-ID"])
