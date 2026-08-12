"""Request schemas for manager operations."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TicketStatus


class TicketUpdate(BaseModel):
    status: TicketStatus
    resolution_notes: str | None = Field(default=None, max_length=1000)


class BulkPickupAssignment(BaseModel):
    collector_id: UUID


class WorkerUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=1, max_length=20)
    status: Literal["ACTIVE", "INACTIVE", "DISABLED"]

    @field_validator("name", "phone")
    @classmethod
    def strip_and_require(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
