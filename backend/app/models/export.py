import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, UUIDPrimaryKey
from app.models.enums import ExportJobStatus, ExportJobType

if TYPE_CHECKING:
    from app.features.users.models import User


class ExportJob(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "export_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_export_jobs_user_id_users"),
        nullable=False,
    )
    job_type: Mapped[ExportJobType] = mapped_column(
        SQLEnum(ExportJobType, name="exportjobtype"),
        nullable=False,
    )
    status: Mapped[ExportJobStatus] = mapped_column(
        SQLEnum(ExportJobStatus, name="exportjobstatus"),
        nullable=False,
        default=ExportJobStatus.PENDING,
        server_default="PENDING",
    )
    filters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("ix_export_jobs_user_id", "user_id"),)
