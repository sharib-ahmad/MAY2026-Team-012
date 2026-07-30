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
        "role": "RESIDENT",
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
            role="RESIDENT",
        )

    # Name too short
    with pytest.raises(ValidationError):
        UserRegisterRequest(
            name="J",
            email="jane@example.com",
            password="password123",
            phone="+919876543210",
            role="RESIDENT",
        )

    # Password too short
    with pytest.raises(ValidationError):
        UserRegisterRequest(
            name="Jane Doe",
            email="jane@example.com",
            password="short",
            phone="+919876543210",
            role="RESIDENT",
        )
