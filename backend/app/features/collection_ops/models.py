import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, Timestamps, UUIDPrimaryKey
from app.models.enums import (
    DelayReason,
    PickupStatus,
    PickupStopStatus,
    WasteSeverity,
)

if TYPE_CHECKING:
    from app.features.materials.models import Batch
    from app.features.sorting_guide.models import WasteCategory
    from app.features.users.models import User
    from app.models.zone import Zone


class Pickup(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "pickups"

    ref_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    resident_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_pickups_resident_id_users"),
        nullable=False,
    )
    collector_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_pickups_collector_id_users"),
        nullable=True,
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("zones.id", name="fk_pickups_zone_id_zones"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        ForeignKey("waste_categories.code", name="fk_pickups_category_waste_categories"),
        nullable=False,
    )
    estimated_weight: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    actual_weight: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    status: Mapped[PickupStatus] = mapped_column(
        SQLEnum(PickupStatus, name="pickupstatus"),
        nullable=False,
        default=PickupStatus.PENDING,
        server_default="PENDING",
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="NORMAL",
        server_default="NORMAL",
    )
    scheduled_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    time_slot: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_contaminated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    contamination_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    contamination_cleared_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_pickups_contamination_cleared_by_id_users"),
        nullable=True,
    )
    contamination_cleared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    credit_rate_applied: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    co2_factor_applied: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("batches.id", name="fk_pickups_batch_id_batches"),
        nullable=True,
    )
    co2_saved: Mapped[float] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=0,
        server_default="0",
    )
    credits_earned: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
        server_default="0",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    resident: Mapped["User"] = relationship(
        "User",
        foreign_keys=[resident_id],
    )
    collector: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[collector_id],
    )
    zone: Mapped["Zone"] = relationship("Zone")
    waste_category: Mapped["WasteCategory"] = relationship("WasteCategory")
    contamination_cleared_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[contamination_cleared_by_id],
    )
    batch: Mapped["Batch | None"] = relationship(
        "Batch",
        back_populates="pickups",
    )
    stops: Mapped[list["DailyPickupStop"]] = relationship(
        "DailyPickupStop",
        back_populates="pickup",
    )

    __table_args__ = (
        Index("ix_pickups_resident_id", "resident_id"),
        Index("ix_pickups_collector_id", "collector_id"),
        Index("ix_pickups_zone_id", "zone_id"),
        Index("ix_pickups_status", "status"),
    )


class DailyPickupSchedule(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "daily_pickup_schedules"

    collector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_daily_pickup_schedules_collector_id_users"),
        nullable=False,
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("zones.id", name="fk_daily_pickup_schedules_zone_id_zones"),
        nullable=False,
    )
    schedule_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    total_stops: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    completed_stops: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    collector: Mapped["User"] = relationship("User")
    zone: Mapped["Zone"] = relationship("Zone")
    stops: Mapped[list["DailyPickupStop"]] = relationship(
        "DailyPickupStop",
        back_populates="schedule",
    )
    routes: Mapped[list["RouteHistory"]] = relationship(
        "RouteHistory",
        back_populates="schedule",
    )

    __table_args__ = (
        Index("ix_daily_pickup_schedules_collector_id", "collector_id"),
        Index("ix_daily_pickup_schedules_zone_id", "zone_id"),
    )


class DailyPickupStop(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "daily_pickup_stops"

    pickup_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pickups.id", name="fk_daily_pickup_stops_pickup_id_pickups"),
        nullable=False,
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "daily_pickup_schedules.id",
            name="fk_daily_pickup_stops_schedule_id_daily_pickup_schedules",
        ),
        nullable=False,
    )
    resident_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_daily_pickup_stops_resident_id_users"),
        nullable=False,
    )
    pickup_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PickupStopStatus] = mapped_column(
        SQLEnum(PickupStopStatus, name="pickupstopstatus"),
        nullable=False,
        default=PickupStopStatus.PENDING,
        server_default="PENDING",
    )
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    pickup: Mapped["Pickup"] = relationship("Pickup", back_populates="stops")
    schedule: Mapped["DailyPickupSchedule"] = relationship(
        "DailyPickupSchedule",
        back_populates="stops",
    )
    resident: Mapped["User"] = relationship("User")
    delay_logs: Mapped[list["DelayLog"]] = relationship("DelayLog", back_populates="stop")
    mixed_waste_tags: Mapped[list["MixedWasteTag"]] = relationship(
        "MixedWasteTag",
        back_populates="stop",
    )

    __table_args__ = (
        Index("ix_daily_pickup_stops_schedule_id", "schedule_id"),
        Index("ix_daily_pickup_stops_resident_id", "resident_id"),
    )


class RouteHistory(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "route_history"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_pickup_schedules.id", name="fk_route_history_schedule_id_schedules"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    schedule: Mapped["DailyPickupSchedule"] = relationship(
        "DailyPickupSchedule",
        back_populates="routes",
    )

    __table_args__ = (Index("ix_route_history_schedule_id", "schedule_id"),)


class DelayLog(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "delay_logs"

    stop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_pickup_stops.id", name="fk_delay_logs_stop_id_daily_pickup_stops"),
        nullable=False,
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_delay_logs_worker_id_users"),
        nullable=False,
    )
    reason: Mapped[DelayReason] = mapped_column(
        SQLEnum(DelayReason, name="delayreason"),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    stop: Mapped["DailyPickupStop"] = relationship("DailyPickupStop", back_populates="delay_logs")
    worker: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_delay_logs_stop_id", "stop_id"),
        Index("ix_delay_logs_worker_id", "worker_id"),
        CheckConstraint(
            (
                "reason != 'OTHER' OR "
                "(reason = 'OTHER' "
                "AND note IS NOT NULL "
                "AND length(btrim(note)) > 0)"
            ),
            name="delay_note_mandatory_for_other",
        ),
    )


class MixedWasteTag(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "mixed_waste_tags"

    stop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "daily_pickup_stops.id",
            name="fk_mixed_waste_tags_stop_id_daily_pickup_stops",
        ),
        nullable=False,
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_mixed_waste_tags_worker_id_users"),
        nullable=False,
    )
    severity: Mapped[WasteSeverity] = mapped_column(
        SQLEnum(WasteSeverity, name="wasteseverity"),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Relationships
    stop: Mapped["DailyPickupStop"] = relationship(
        "DailyPickupStop",
        back_populates="mixed_waste_tags",
    )
    worker: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_mixed_waste_tags_stop_id", "stop_id"),
        Index("ix_mixed_waste_tags_severity", "severity"),
    )
