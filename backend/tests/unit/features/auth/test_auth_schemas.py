import pytest
from pydantic import ValidationError

from app.features.auth.schemas import LoginRequest, UserRegisterRequest


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


@pytest.mark.unit
def test_login_request_trims_email_whitespace():
    request = LoginRequest(
        email="  citizen@example.com  ",
        password="StrongPassword123!",
    )

    assert request.email == "citizen@example.com"
    assert request.password == "StrongPassword123!"


@pytest.mark.unit
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
def test_login_request_rejects_invalid_or_unsafe_input(payload):
    with pytest.raises(ValidationError):
        LoginRequest(**payload)
