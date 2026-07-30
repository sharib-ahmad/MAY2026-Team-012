import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.models.enums import BulkRequestStatus

if TYPE_CHECKING:
    from app.features.sorting_guide.models import WasteCategory
    from app.features.users.models import User
    from app.models.zone import Zone


class BulkPickupRequest(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "bulk_pickup_requests"

    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_bulk_pickup_requests_requester_id_users"),
        nullable=False,
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("zones.id", name="fk_bulk_pickup_requests_zone_id_zones"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        ForeignKey(
            "waste_categories.code",
            name="fk_bulk_pickup_requests_category_waste_categories",
        ),
        nullable=False,
    )
    requested_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    approx_volume: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[BulkRequestStatus] = mapped_column(
        SQLEnum(BulkRequestStatus, name="bulkrequeststatus"),
        nullable=False,
        default=BulkRequestStatus.PENDING,
        server_default="PENDING",
    )
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_bulk_pickup_requests_decided_by_id_users"),
        nullable=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    requester: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requester_id],
    )
    zone: Mapped["Zone"] = relationship("Zone")
    waste_category: Mapped["WasteCategory"] = relationship("WasteCategory")
    decided_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[decided_by_id],
    )

    __table_args__ = (
        Index("ix_bulk_pickup_requests_requester_id", "requester_id"),
        Index("ix_bulk_pickup_requests_status", "status"),
        Index("ix_bulk_pickup_requests_zone_requested", "zone_id", "requested_date"),
    )
