from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password


@pytest.mark.unit
def test_password_hashing_and_verification():
    """Verify that password hashing and matching works successfully."""
    pwd = "MySuperSecretPassword123"
    hashed = get_password_hash(pwd)

    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False


@pytest.mark.unit
def test_verify_password_handles_invalid_hash():
    """Verify that junk or malformed hashes return False instead of raising exceptions."""
    assert verify_password("password", "") is False
    assert verify_password("password", "randomjunktext") is False


@pytest.mark.unit
def test_create_access_token_claims():
    """Verify that JWT creation embeds the correct claims and respects expiration config."""
    settings = get_settings()
    user_id = "12345678-1234-1234-1234-123456789abc"
    token_version = 4

    token = create_access_token(subject=user_id, token_version=token_version)
    assert token is not None

    # Decode and assert claims
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == user_id
    assert decoded["token_version"] == token_version
    assert "exp" in decoded


@pytest.mark.unit
def test_create_access_token_custom_expiry():
    """Verify that create_access_token respects custom expires_delta parameters."""
    settings = get_settings()
    user_id = "user-123"
    delta = timedelta(minutes=10)

    token = create_access_token(subject=user_id, expires_delta=delta)
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == user_id
