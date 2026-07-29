import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, UUIDPrimaryKey
from app.models.enums import EntityType, Role, TraceEventType

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_audit_logs_actor_id_users"),
        nullable=False,
    )
    actor_role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="role"),
        nullable=False,
    )
    actor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    module: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    actor: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("ix_audit_logs_entity_type_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_actor_id", "actor_id"),
    )


class TraceEvent(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "trace_events"

    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType, name="entitytype"),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    event_type: Mapped[TraceEventType] = mapped_column(
        SQLEnum(TraceEventType, name="traceeventtype"),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_trace_events_actor_id_users"),
        nullable=False,
    )
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    actor: Mapped["User"] = relationship("User")

    __table_args__ = (Index("ix_trace_events_entity_type_id", "entity_type", "entity_id"),)
