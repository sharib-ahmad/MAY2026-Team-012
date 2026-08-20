import pytest
from pydantic import ValidationError

from app.features.auth.schemas import UserRegisterRequest


@pytest.mark.unit
def test_user_register_request_whitespace_stripping():
    """Verify that name, email, and phone are stripped of leading/trailing whitespace."""
    payload = {
        "name": "  John Doe  ",
        "email": "   john@example.com   ",
        "password": "password123",
        "phone": "  +919876543210  ",
        "address": "Some address",
        "zone_id": None,
        "role": "CITIZEN",
    }
    req = UserRegisterRequest(**payload)
    assert req.name == "John Doe"
    assert req.email == "john@example.com"
    assert req.phone == "+919876543210"


@pytest.mark.unit
def test_user_register_request_validation_errors():
    """Verify that invalid emails, short names, or short passwords raise validation errors."""
    # Invalid email
    with pytest.raises(ValidationError):
        UserRegisterRequest(
            name="Jane",
            email="not-an-email",
            password="password123",
            phone="+919876543210",
            role="CITIZEN",
        )

    # Name too short
    with pytest.raises(ValidationError):
        UserRegisterRequest(
            name="J",
            email="jane@example.com",
            password="password123",
            phone="+919876543210",
            role="CITIZEN",
        )

    # Password too short
    with pytest.raises(ValidationError):
        UserRegisterRequest(
            name="Jane Doe",
            email="jane@example.com",
            password="short",
            phone="+919876543210",
            role="CITIZEN",
        )


# LoginRequest trimming and invalid-input rejection are proven end-to-end, more
# strongly, by tests/api/features/auth/test_auth_login.py
# (test_login_email_is_trimmed_and_case_insensitive,
# test_invalid_login_payload_returns_safe_validation_error); the schema-only
# duplicates were removed here rather than kept as redundant coverage.
