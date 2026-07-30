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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, Timestamps, UUIDPrimaryKey
from app.models.enums import BadgeCategory, CreditReason, CreditStatus

if TYPE_CHECKING:
    from app.features.collection_ops.models import Pickup
    from app.features.sorting_guide.models import WasteCategory
    from app.features.users.models import User


class CreditFactor(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "credit_factors"

    category: Mapped[str] = mapped_column(
        ForeignKey("waste_categories.code", name="fk_credit_factors_category_waste_categories"),
        nullable=False,
        unique=True,
    )
    credit_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    co2_factor: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    waste_category: Mapped["WasteCategory"] = relationship("WasteCategory")

    __table_args__ = (CheckConstraint("credit_rate >= 0", name="credit_rate_non_negative"),)


class Credit(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "credits"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_credits_user_id_users"),
        nullable=False,
    )
    pickup_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pickups.id", name="fk_credits_pickup_id_pickups"),
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    co2_saved: Mapped[float] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=0.0,
        server_default="0",
    )
    reason: Mapped[CreditReason] = mapped_column(
        SQLEnum(CreditReason, name="creditreason"),
        nullable=False,
    )
    status: Mapped[CreditStatus] = mapped_column(
        SQLEnum(CreditStatus, name="creditstatus"),
        nullable=False,
        default=CreditStatus.CONFIRMED,
        server_default="CONFIRMED",
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    pickup: Mapped["Pickup | None"] = relationship("Pickup")

    __table_args__ = (
        UniqueConstraint("pickup_id", "reason", name="uq_credit_pickup_reason"),
        Index("ix_credits_user_id_status", "user_id", "status"),
    )


class Badge(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "badges"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[BadgeCategory] = mapped_column(
        SQLEnum(BadgeCategory, name="badgecategory"),
        nullable=False,
    )
    icon_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criteria: Mapped[str] = mapped_column(Text, nullable=False)
    threshold: Mapped[int] = mapped_column(nullable=False)


class UserBadge(Base, UUIDPrimaryKey):
    __tablename__ = "user_badges"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_user_badges_user_id_users"),
        nullable=False,
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("badges.id", name="fk_user_badges_badge_id_badges"),
        nullable=False,
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    badge: Mapped["Badge"] = relationship("Badge")

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)
