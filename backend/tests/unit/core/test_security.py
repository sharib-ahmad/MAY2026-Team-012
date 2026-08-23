"""Focused unit tests for password hashing and access-token creation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password


@pytest.mark.unit
@pytest.mark.security
def test_password_hash_is_salted_and_verification_fails_closed():
    password = "StrongPassword123!"

    first_hash = get_password_hash(password)
    second_hash = get_password_hash(password)

    assert first_hash != password
    assert second_hash != password
    assert first_hash != second_hash
    assert first_hash.startswith("$2")
    assert second_hash.startswith("$2")

    assert verify_password(password, first_hash) is True
    assert verify_password("WrongPassword123!", first_hash) is False
    assert verify_password(password, "") is False
    assert verify_password(password, "not-a-bcrypt-hash") is False


@pytest.mark.unit
@pytest.mark.security
@pytest.mark.boundary
def test_password_hashing_enforces_the_bcrypt_utf8_byte_limit():
    exactly_72_bytes = "A" * 72

    password_hash = get_password_hash(exactly_72_bytes)
    assert verify_password(exactly_72_bytes, password_hash) is True

    for over_limit in ("A" * 73, "€" * 25):
        assert len(over_limit.encode("utf-8")) > 72
        with pytest.raises(ValueError, match="72"):
            get_password_hash(over_limit)


@pytest.mark.unit
@pytest.mark.security
def test_access_token_contains_subject_version_and_configured_expiry():
    settings = get_settings()
    subject = "12345678-1234-1234-1234-123456789abc"
    before = datetime.now(UTC)

    token = create_access_token(
        subject=subject,
        token_version=7,
    )
    claims = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    expires_at = datetime.fromtimestamp(claims["exp"], tz=UTC)

    assert claims["sub"] == subject
    assert claims["token_version"] == 7
    assert expires_at > before
    assert expires_at - before <= timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        seconds=1,
    )


@pytest.mark.unit
@pytest.mark.security
def test_access_token_respects_custom_expiry():
    settings = get_settings()
    before = datetime.now(UTC)

    token = create_access_token(
        subject="12345678-1234-1234-1234-123456789abc",
        token_version=2,
        expires_delta=timedelta(minutes=10),
    )
    claims = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    expires_at = datetime.fromtimestamp(claims["exp"], tz=UTC)

    assert timedelta(minutes=9, seconds=55) <= expires_at - before
    assert expires_at - before <= timedelta(minutes=10, seconds=1)
