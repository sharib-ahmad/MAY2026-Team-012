import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Double, ForeignKey, Index, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.models.enums import Availability, Role, UserStatus

if TYPE_CHECKING:
    from app.models.zone import Zone


class User(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "users"

    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("zones.id", name="fk_users_zone_id_zones"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, name="role"), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="userstatus"),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default="ACTIVE",
    )
    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    availability: Mapped[Availability | None] = mapped_column(
        SQLEnum(Availability, name="availability"),
        nullable=True,
        default=Availability.AVAILABLE,
        server_default="AVAILABLE",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    zone: Mapped["Zone | None"] = relationship(
        "Zone",
        foreign_keys=[zone_id],
        back_populates="members",
    )
    managed_zones: Mapped[list["Zone"]] = relationship(
        "Zone",
        foreign_keys="[Zone.manager_id]",
        back_populates="manager",
    )

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_zone_id", "zone_id"),
        Index("ix_users_status", "status"),
    )
