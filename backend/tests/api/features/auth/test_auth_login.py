"""Login API and persistence tests for SCRUM-88."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import status
from jose import jwt

from app.models.enums import UserStatus


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
def test_valid_login_returns_canonical_safe_response_and_updates_last_login(
    db_client,
    db,
    app_test,
    auth_paths,
    make_user,
    ward_a,
):
    """S1-5101: a provisioned active user can authenticate safely."""

    user = make_user(
        name="Jane Citizen",
        email="jane.citizen@example.com",
        password="StrongPassword123!",
        zone_id=ward_a.id,
        last_login_at=None,
    )

    before = datetime.now(UTC)
    response = db_client.post(
        auth_paths["login"],
        json={
            "email": "jane.citizen@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("X-Request-ID")

    body = response.json()
    assert set(body) == {"access_token", "token_type", "expires_in", "user"}
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == app_test.state.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert body["user"] == {
        "id": str(user.id),
        "name": "Jane Citizen",
        "email": "jane.citizen@example.com",
        "role": "CITIZEN",
        "ward_code": "W-04",
    }

    claims = jwt.decode(
        body["access_token"],
        app_test.state.settings.SECRET_KEY,
        algorithms=[app_test.state.settings.ALGORITHM],
    )
    assert claims["sub"] == str(user.id)
    assert claims["token_version"] == user.token_version
    assert claims["exp"] > int(before.timestamp())

    db.refresh(user)
    assert user.last_login_at is not None
    assert user.last_login_at >= before

    response_text = response.text.lower()
    for forbidden in ("password", "password_hash", "token_version", "deleted_at", "zone_id"):
        assert forbidden not in response_text


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "account_case",
    [
        pytest.param("wrong-password", id="wrong-password"),
        pytest.param("unknown-account", id="unknown-account"),
        pytest.param("disabled-account", id="disabled-account"),
        pytest.param("deleted-account", id="deleted-account"),
    ],
)
def test_invalid_account_states_use_one_generic_authentication_failure(
    db_client,
    db,
    auth_paths,
    make_user,
    assert_safe_error,
    account_case,
):
    """S1-G01/S1-5102: login does not disclose account existence or state."""

    submitted_password = "StrongPassword123!"
    tracked_user = None

    if account_case == "wrong-password":
        email = "known.active@example.com"
        tracked_user = make_user(
            email=email,
            password="CorrectPassword123!",
            last_login_at=None,
        )

    elif account_case == "unknown-account":
        email = "unknown.account@example.com"

    elif account_case == "disabled-account":
        email = "known.disabled@example.com"
        tracked_user = make_user(
            email=email,
            password=submitted_password,
            status=UserStatus.DISABLED,
            last_login_at=None,
        )

    elif account_case == "deleted-account":
        email = "known.deleted@example.com"
        tracked_user = make_user(
            email=email,
            password=submitted_password,
            deleted_at=datetime.now(UTC),
            last_login_at=None,
        )

    else:
        raise AssertionError(f"Unhandled account case: {account_case}")

    response = db_client.post(
        auth_paths["login"],
        json={
            "email": email,
            "password": submitted_password,
        },
    )

    body = assert_safe_error(
        response,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="AUTHENTICATION_REQUIRED",
        forbidden_values=(email, submitted_password),
    )

    assert body["error"]["message"] == "Invalid email or password."
    assert "access_token" not in response.text

    if tracked_user is not None:
        db.refresh(tracked_user)
        assert tracked_user.last_login_at is None


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.boundary
def test_login_email_is_trimmed_and_case_insensitive(
    db_client,
    auth_paths,
    make_user,
):
    """S1-5101: email normalisation is consistent at the API boundary."""

    make_user(
        email="mixed.case@example.com",
        password="StrongPassword123!",
    )

    response = db_client.post(
        auth_paths["login"],
        json={
            "email": "  Mixed.Case@Example.com  ",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"]["email"] == "mixed.case@example.com"


@pytest.mark.api
@pytest.mark.boundary
@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {"email": "not-an-email", "password": "StrongPassword123!"},
            id="invalid-email",
        ),
        pytest.param(
            {"email": "citizen@example.com", "password": ""},
            id="blank-password",
        ),
        pytest.param(
            {"password": "StrongPassword123!"},
            id="missing-email",
        ),
        pytest.param(
            {"email": "citizen@example.com"},
            id="missing-password",
        ),
        pytest.param(
            {"email": "citizen@example.com", "password": "A" * 73},
            id="password-over-bcrypt-byte-limit",
        ),
    ],
)
def test_invalid_login_payload_returns_safe_validation_error(
    db_client,
    auth_paths,
    payload,
    assert_safe_error,
):
    """S1-G03/R4: invalid input is rejected before authentication or database work."""

    response = db_client.post(auth_paths["login"], json=payload)

    body = assert_safe_error(
        response,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        forbidden_values=(str(payload.get("password", "")),),
    )
    assert body["error"].get("details")
