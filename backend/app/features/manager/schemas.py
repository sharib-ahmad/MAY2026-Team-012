"""Request schemas for manager operations."""

from pydantic import BaseModel, Field

from app.models.enums import TicketStatus


class TicketUpdate(BaseModel):
    status: TicketStatus
    resolution_notes: str | None = Field(default=None, max_length=1000)


class BulkPickupAssignment(BaseModel):
    collector_id: str


class WorkerUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=1, max_length=20)
    status: str
