import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TicketCreate(BaseModel):
    issue_type: Literal["MISSED_PICKUP", "OVERFLOW", "MIXED_WASTE", "DELAY", "OTHER"]
    description: str = Field(..., min_length=1, max_length=500)

    @field_validator("description")
    @classmethod
    def description_must_have_content(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("Description must contain at least 10 non-whitespace characters.")
        return stripped  # already stripped — router no longer needs .strip()


class TicketReopenRequest(BaseModel):
    note: str = Field(..., min_length=1, max_length=1000)

    @field_validator("note")
    @classmethod
    def strip_and_require_note(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Note must not be blank.")
        return stripped


class TicketResponse(BaseModel):
    id: uuid.UUID
    ref_code: str
    issue_type: str
    status: str
    description: str
    manager_note: str | None = None
    ward_code: str | None = None
    ward_name: str | None = None
    ward_sectors: str | None = None
    ward_manager_name: str | None = None
    created_at: datetime


class TicketsResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
