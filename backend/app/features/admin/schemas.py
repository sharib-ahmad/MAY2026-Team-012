import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserSummary(BaseModel):
    """Summary of a user for admin dashboard display."""

    id: uuid.UUID
    name: str
    email: str
    phone: str
    role: str
    zone_code: str | None = None
    zone_name: str | None = None
    zone_id: uuid.UUID | None = None
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
    actor_id: uuid.UUID
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
