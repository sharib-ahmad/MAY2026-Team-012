import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
MAX_BCRYPT_PASSWORD_BYTES = 72


def validate_email_format(v: str) -> str:
    if not isinstance(v, str):
        return v
    v = v.strip()
    if not EMAIL_REGEX.match(v):
        raise ValueError("value is not a valid email address")
    return v


def validate_password_bytes(value: str) -> str:
    """Reject passwords bcrypt cannot represent without silent truncation."""
    if len(value.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return value


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return validate_password_bytes(v)


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str
    password: str = Field(..., min_length=8, max_length=128)
    phone: str = Field(..., min_length=5, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    zone_id: uuid.UUID | None = Field(default=None)
    role: str = Field(..., min_length=3, max_length=50)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)

    @field_validator("name", "email", "phone")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return validate_password_bytes(v)


class AuthenticatedUser(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    ward_code: str | None = None
    zone_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUser
