import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.auth.schemas import validate_email_format
from app.models.enums import UserStatus


class AdminRequest(BaseModel):
    """Base schema that rejects fields administrators must never set directly."""

    model_config = ConfigDict(extra="forbid")


def _required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


def _password_within_bcrypt_limit(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("must not exceed 72 UTF-8 bytes")
    return value


class UserCreate(AdminRequest):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., max_length=255)
    phone: str = Field(..., min_length=5, max_length=20)
    role: Literal["CITIZEN", "COLLECTION_WORKER", "MUNICIPAL_OFFICER", "RECYCLER", "SYSTEM_ADMIN"]
    zone_id: uuid.UUID | None = None
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("name", "phone")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        return _required_text(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return validate_email_format(value).lower()

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        return _password_within_bcrypt_limit(value)


class UserUpdate(AdminRequest):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    role: (
        Literal["CITIZEN", "COLLECTION_WORKER", "MUNICIPAL_OFFICER", "RECYCLER", "SYSTEM_ADMIN"]
        | None
    ) = None

    @field_validator("name", "phone")
    @classmethod
    def strip_optional_fields(cls, value: str | None) -> str | None:
        return _required_text(value) if value is not None else value

    @field_validator("email")
    @classmethod
    def normalize_optional_email(cls, value: str | None) -> str | None:
        return validate_email_format(value).lower() if value is not None else value


class UserStatusUpdate(AdminRequest):
    status: UserStatus


class UserSummary(BaseModel):
    """Summary of a user for admin dashboard display."""

    id: uuid.UUID
    name: str
    email: str
    phone: str
    role: str
    zone_code: str | None = None
    zone_name: str | None = None
    last_login_at: datetime | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Summary statistics for admin dashboard."""

    registered_users: int
    wards_configured: int
    errors_in_24h: int
    system_uptime_hours: int


class AdminDashboardResponse(BaseModel):
    """Complete admin dashboard response."""

    stats: DashboardStats
    users: list[UserSummary]


class WardCreate(BaseModel):
    """Request schema for creating a new ward."""

    code: str = Field(..., min_length=1, max_length=20, description="Ward code (e.g., WARD-01)")
    name: str = Field(..., min_length=2, max_length=120, description="Ward name")
    sectors: str | None = Field(None, max_length=500, description="Sectors in this ward")


class WardUpdate(BaseModel):
    """Request schema for updating a ward."""

    name: str = Field(..., min_length=2, max_length=120, description="Ward name")
    sectors: str | None = Field(None, max_length=500, description="Sectors in this ward")
    manager_id: uuid.UUID | None = Field(None, description="Manager user ID to assign")


class WardResponse(BaseModel):
    """Response schema for ward data."""

    id: uuid.UUID
    code: str
    name: str
    sectors: str | None = None
    manager_id: uuid.UUID | None = None
    manager_name: str | None = None
    workers_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WardListResponse(BaseModel):
    """Response schema for listing all wards."""

    wards: list[WardResponse]
    total: int


class LogEntry(BaseModel):
    """Schema for a single log entry."""

    id: uuid.UUID
    timestamp: datetime
    actor_id: uuid.UUID | None = None
    actor_role: str
    actor_name: str
    action: str
    entity_type: str
    entity_id: uuid.UUID
    module: str
    description: str | None = None
    ip_address: str | None = None

    model_config = ConfigDict(from_attributes=True)


class LogsResponse(BaseModel):
    """Response schema for listing logs."""

    logs: list[LogEntry]
    total: int
