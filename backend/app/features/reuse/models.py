import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, Timestamps, UUIDPrimaryKey
from app.models.enums import ReuseCategory, ReuseClaimStatus, ReuseCondition, ReuseStatus

if TYPE_CHECKING:
    from app.features.users.models import User
    from app.models.zone import Zone


class ReuseListing(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "reuse_listings"

    lister_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_reuse_listings_lister_id_users"),
        nullable=False,
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("zones.id", name="fk_reuse_listings_zone_id_zones"),
        nullable=True,
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_reuse_listings_reviewed_by_id_users"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[ReuseCategory] = mapped_column(
        SQLEnum(ReuseCategory, name="reusecategory"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition: Mapped[ReuseCondition] = mapped_column(
        SQLEnum(ReuseCondition, name="reusecondition"),
        nullable=False,
    )
    status: Mapped[ReuseStatus] = mapped_column(
        SQLEnum(ReuseStatus, name="reusestatus"),
        nullable=False,
        default=ReuseStatus.PENDING_APPROVAL,
        server_default="PENDING_APPROVAL",
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    manager_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    lister: Mapped["User"] = relationship(
        "User",
        foreign_keys=[lister_id],
    )
    zone: Mapped["Zone | None"] = relationship("Zone")
    reviewed_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[reviewed_by_id],
    )
    images: Mapped[list["ReuseImage"]] = relationship(
        "ReuseImage",
        back_populates="listing",
    )
    claims: Mapped[list["ReuseClaim"]] = relationship(
        "ReuseClaim",
        back_populates="listing",
    )

    __table_args__ = (
        Index("ix_reuse_listings_zone_id", "zone_id"),
        Index("ix_reuse_listings_status", "status"),
        CheckConstraint(
            (
                "status != 'REJECTED' OR "
                "(status = 'REJECTED' "
                "AND rejection_reason IS NOT NULL "
                "AND length(btrim(rejection_reason)) > 0)"
            ),
            name="rejection_reason_mandatory_for_rejected",
        ),
    )


class ReuseImage(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "reuse_images"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reuse_listings.id", name="fk_reuse_images_listing_id_reuse_listings"),
        nullable=False,
    )
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    # Relationships
    listing: Mapped["ReuseListing"] = relationship("ReuseListing", back_populates="images")

    __table_args__ = (Index("ix_reuse_images_listing_id", "listing_id"),)


class ReuseClaim(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "reuse_claims"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reuse_listings.id", name="fk_reuse_claims_listing_id_reuse_listings"),
        nullable=False,
    )
    claimant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_reuse_claims_claimant_id_users"),
        nullable=False,
    )
    status: Mapped[ReuseClaimStatus] = mapped_column(
        SQLEnum(ReuseClaimStatus, name="reuseclaimstatus"),
        nullable=False,
        default=ReuseClaimStatus.PENDING,
        server_default="PENDING",
    )
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_reuse_claims_decided_by_id_users"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    listing: Mapped["ReuseListing"] = relationship("ReuseListing", back_populates="claims")
    claimant: Mapped["User"] = relationship(
        "User",
        foreign_keys=[claimant_id],
    )
    decided_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[decided_by_id],
    )

    __table_args__ = (
        Index("ix_reuse_claims_listing_id", "listing_id"),
        Index("ix_reuse_claims_claimant_id", "claimant_id"),
        CheckConstraint(
            (
                "status != 'REJECTED' OR "
                "(status = 'REJECTED' "
                "AND note IS NOT NULL "
                "AND length(btrim(note)) > 0)"
            ),
            name="claim_note_mandatory_for_rejected",
        ),
    )
