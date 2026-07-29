import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.models.enums import BatchQuality, BatchStatus

if TYPE_CHECKING:
    from app.models.pickup import Pickup
    from app.models.user import User
    from app.models.waste_category import WasteCategory
    from app.models.zone import Zone


class Batch(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "batches"

    ref_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    collector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_batches_collector_id_users"),
        nullable=False,
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_batches_assigned_by_id_users"),
        nullable=False,
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("zones.id", name="fk_batches_zone_id_zones"),
        nullable=True,
    )
    status: Mapped[BatchStatus] = mapped_column(
        SQLEnum(BatchStatus, name="batchstatus"),
        nullable=False,
        default=BatchStatus.AVAILABLE,
        server_default="AVAILABLE",
    )
    waste_category: Mapped[str] = mapped_column(
        ForeignKey("waste_categories.code", name="fk_batches_waste_category_waste_categories"),
        nullable=False,
    )
    declared_weight: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    final_weight: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    quality_status: Mapped[BatchQuality] = mapped_column(
        SQLEnum(BatchQuality, name="batchquality"),
        nullable=False,
        default=BatchQuality.CLEAN,
        server_default="CLEAN",
    )
    contamination_note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quality_set_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_batches_quality_set_by_id_users"),
        nullable=True,
    )
    destination_recycler_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_batches_destination_recycler_id_users"),
        nullable=True,
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_quantity: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    collector: Mapped["User"] = relationship(
        "User",
        foreign_keys=[collector_id],
    )
    assigned_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_by_id],
    )
    zone: Mapped["Zone | None"] = relationship("Zone")
    waste_category_ref: Mapped["WasteCategory"] = relationship("WasteCategory")
    quality_set_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[quality_set_by_id],
    )
    destination_recycler: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[destination_recycler_id],
    )
    pickups: Mapped[list["Pickup"]] = relationship("Pickup", back_populates="batch")

    __table_args__ = (
        Index("ix_batches_status", "status"),
        Index("ix_batches_destination_recycler_id", "destination_recycler_id"),
        Index("ix_batches_waste_category", "waste_category"),
        CheckConstraint(
            (
                "quality != 'UNSAFE' OR "
                "(quality = 'UNSAFE' "
                "AND contamination_note IS NOT NULL "
                "AND length(btrim(contamination_note)) > 0)"
            ),
            name="contamination_note_required_for_unsafe",
        ),
    )


class Inventory(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "inventory"

    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("zones.id", name="fk_inventory_zone_id_zones"),
        nullable=False,
    )
    waste_category: Mapped[str] = mapped_column(
        ForeignKey("waste_categories.code", name="fk_inventory_waste_category_waste_categories"),
        nullable=False,
    )
    current_weight: Mapped[float] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=0.0,
        server_default="0",
    )

    # Relationships
    zone: Mapped["Zone"] = relationship("Zone")
    waste_category_ref: Mapped["WasteCategory"] = relationship("WasteCategory")

    __table_args__ = (
        UniqueConstraint("zone_id", "waste_category", name="uq_inventory_zone_category"),
    )
