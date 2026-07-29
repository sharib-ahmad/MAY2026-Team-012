import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: str = Field(..., min_length=5, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    zone_id: uuid.UUID | None = Field(default=None)
    role: str = Field(..., min_length=3, max_length=50)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)

    @field_validator("name", "email", "phone")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class AuthenticatedUser(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    ward_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUser
