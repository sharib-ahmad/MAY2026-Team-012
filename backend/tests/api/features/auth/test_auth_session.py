"""Session validation, revocation and profile-security tests for SCRUM-88."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status

from app.models.enums import UserStatus


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
def test_valid_token_returns_only_the_authenticated_users_public_profile(
    db_client,
    auth_paths,
    make_user,
    bearer_for,
    ward_a,
):
    """S1-G02/S1-5101: a token returns only its own canonical public identity."""

    user = make_user(
        name="Current Citizen",
        email="current.citizen@example.com",
        zone_id=ward_a.id,
    )
    make_user(
        name="Other Citizen",
        email="other.citizen@example.com",
    )

    response = db_client.get(auth_paths["me"], headers=bearer_for(user))

    assert response.status_code == status.HTTP_200_OK, (
        f"Expected 200 for a valid token, got {response.status_code}: {response.text}"
    )
    assert response.json() == {
        "id": str(user.id),
        "name": "Current Citizen",
        "email": "current.citizen@example.com",
        "role": "CITIZEN",
        "ward_code": "W-04",
        "zone_name": "Ward A",
    }

    response_text = response.text.lower()
    for forbidden in (
        "other.citizen@example.com",
        "password",
        "password_hash",
        "token_version",
        "deleted_at",
        "zone_id",
    ):
        assert forbidden not in response_text


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="missing-authorization"),
        pytest.param(
            {"Authorization": "Basic dXNlcjpwYXNz"},
            id="unsupported-scheme",
        ),
        pytest.param(
            {"Authorization": "Bearer not.a.jwt"},
            id="malformed-bearer-token",
        ),
    ],
)
def test_missing_or_malformed_authorization_returns_bearer_challenge(
    db_client,
    auth_paths,
    headers,
    assert_safe_error,
):
    """S1-G01/S1-G03: protected endpoints fail closed with RFC Bearer semantics."""

    response = db_client.get(auth_paths["me"], headers=headers)

    assert_safe_error(
        response,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="AUTHENTICATION_REQUIRED",
        require_bearer_challenge=True,
    )


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "case",
    ["expired", "wrong-signature"],
)
def test_expired_or_forged_token_is_rejected(
    db_client,
    auth_paths,
    make_user,
    signed_token,
    assert_safe_error,
    case,
):
    """S1-G01: expired and forged access tokens never authenticate."""

    user = make_user(email=f"{case}@example.com")

    if case == "expired":
        token = signed_token(
            subject=str(user.id),
            token_version=user.token_version,
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    else:
        token = signed_token(
            subject=str(user.id),
            token_version=user.token_version,
            secret="different-signing-key-with-at-least-thirty-two-characters",
        )

    response = db_client.get(
        auth_paths["me"],
        headers={"Authorization": f"Bearer {token}"},
    )

    assert_safe_error(
        response,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="AUTHENTICATION_REQUIRED",
    )


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "case",
    ["missing-subject", "malformed-subject", "unknown-user"],
)
def test_subject_claim_must_identify_an_existing_user(
    db_client,
    auth_paths,
    signed_token,
    assert_safe_error,
    case,
):
    """S1-G01: invalid token subjects are authentication failures, never server errors."""

    if case == "missing-subject":
        token = signed_token(
            token_version=1,
            include_subject=False,
        )
    elif case == "malformed-subject":
        token = signed_token(
            subject="not-a-uuid",
            token_version=1,
        )
    else:
        token = signed_token(
            subject=str(uuid.uuid4()),
            token_version=1,
        )

    response = db_client.get(
        auth_paths["me"],
        headers={"Authorization": f"Bearer {token}"},
    )

    assert_safe_error(
        response,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="AUTHENTICATION_REQUIRED",
    )


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "case",
    ["missing-version", "stale-version"],
)
def test_token_version_is_required_and_stale_sessions_are_revoked(
    db_client,
    auth_paths,
    make_user,
    bearer_for,
    assert_safe_error,
    case,
):
    """S1-5102/S1-5105: every session participates in token-version revocation."""

    user = make_user(
        email=f"{case}@example.com",
        token_version=4,
    )

    if case == "missing-version":
        headers = bearer_for(user, include_token_version=False)
    else:
        headers = bearer_for(user, token_version=3)

    response = db_client.get(auth_paths["me"], headers=headers)

    assert_safe_error(
        response,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="AUTHENTICATION_REQUIRED",
    )


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "state",
    ["disabled", "deleted"],
)
def test_account_state_change_revokes_an_existing_session(
    db_client,
    db,
    auth_paths,
    make_user,
    bearer_for,
    assert_safe_error,
    state,
):
    """S1-5102: disabled or deleted accounts cannot keep using an old token."""

    user = make_user(email=f"session.{state}@example.com")
    headers = bearer_for(user)

    if state == "disabled":
        user.status = UserStatus.DISABLED
    else:
        user.deleted_at = datetime.now(UTC)

    db.flush()

    response = db_client.get(auth_paths["me"], headers=headers)

    assert_safe_error(
        response,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="AUTHENTICATION_REQUIRED",
    )
