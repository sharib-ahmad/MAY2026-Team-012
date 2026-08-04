from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DonationCreate(BaseModel):
    title: str = Field(..., max_length=80)
    category: str
    description: str | None = Field(None, max_length=500)
    condition: str
    address: str | None = Field(None, max_length=200)
    images: list[str] = Field(default_factory=list)


class DonationResponse(BaseModel):
    id: UUID
    donor_id: UUID
    donor_name: str
    donor_phone: str | None = None
    donor_email: str | None = None
    title: str
    category: str
    description: str | None = None
    condition: str
    status: str
    address: str | None = None
    images: list[str] = []
    rejection_reason: str | None = None
    manager_notes: str | None = None
    claimant_id: UUID | None = None
    claimant_name: str | None = None
    claimant_phone: str | None = None
    claimant_email: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DonationReview(BaseModel):
    status: str  # 'AVAILABLE' or 'REJECTED'
    rejection_reason: str | None = None


class ClaimReview(BaseModel):
    status: str  # 'APPROVED' or 'REJECTED'
    note: str | None = None


class ClaimResponse(BaseModel):
    id: UUID
    listing_id: UUID
    title: str
    description: str | None = None
    category: str | None = None
    condition: str | None = None
    images: list[str] = []
    address: str | None = None
    claimant_id: UUID
    claimant_name: str
    status: str
    note: str | None = None
    donor_name: str | None = None
    donor_phone: str | None = None
    donor_email: str | None = None
    decided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
