import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.models.enums import TicketStatus, TicketType

if TYPE_CHECKING:
    from app.features.collection_ops.models import Pickup
    from app.features.users.models import User
    from app.models.zone import Zone


class Ticket(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "tickets"

    ref_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    raised_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_tickets_raised_by_id_users"),
        nullable=False,
    )
    pickup_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pickups.id", name="fk_tickets_pickup_id_pickups"),
        nullable=True,
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("zones.id", name="fk_tickets_zone_id_zones"),
        nullable=True,
    )
    issue_type: Mapped[TicketType] = mapped_column(
        SQLEnum(TicketType, name="tickettype"),
        nullable=False,
    )
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, name="ticketstatus"),
        nullable=False,
        default=TicketStatus.OPEN,
        server_default="OPEN",
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_tickets_resolved_by_id_users"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    raised_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[raised_by_id],
    )
    pickup: Mapped["Pickup | None"] = relationship("Pickup")
    zone: Mapped["Zone | None"] = relationship("Zone")
    resolved_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[resolved_by_id],
    )

    __table_args__ = (
        Index("ix_tickets_zone_id", "zone_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_raised_by_id", "raised_by_id"),
    )
