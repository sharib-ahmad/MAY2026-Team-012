"""Audit log model and helper functions for tracking system events.

This module contains the AuditLog model for storing audit events and helper
functions for creating audit log entries. Audit logs track user actions,
ward operations, and other system activities for accountability and debugging.
"""

import logging
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base, CreatedAt, UUIDPrimaryKey
from app.models.enums import EntityType, Role, TraceEventType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AuditLog(Base, UUIDPrimaryKey, CreatedAt):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_audit_logs_actor_id_users", ondelete="SET NULL"),
        nullable=True,
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

    __table_args__ = (Index("ix_trace_events_entity_type_id", "entity_type", "entity_id"),)


def create_audit_log(
    db: Session,
    actor_id: str | None = None,
    actor_name: str | None = None,
    actor_role: str = "CITIZEN",
    action: str = "",
    entity_type: str = "",
    entity_id: str | None = None,
    module: str = "auth",
    description: str = "",
    ip_address: str | None = None,
) -> AuditLog | None:
    """Create an audit log entry using the existing SQLAlchemy session.

    Uses the existing transaction to create audit logs. Since actor_id is now
    nullable with ON DELETE SET NULL, FK constraints won't block audit log creation.
    """

    try:
        audit_log = AuditLog(
            actor_id=uuid.UUID(actor_id) if actor_id else None,
            actor_role=Role(actor_role),
            actor_name=actor_name or "System",
            action=action,
            entity_type=entity_type,
            entity_id=uuid.UUID(entity_id) if entity_id else uuid.uuid4(),
            module=module,
            description=description,
            ip_address=ip_address,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        logger.info(f"Successfully created audit log: {action} on {entity_type}")
        return audit_log

    except Exception as e:
        logger.exception(f"Audit log creation failed: {e}")
        return None
