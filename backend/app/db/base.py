"""Declarative base, metadata naming convention, and timestamp mixins.

Naming convention. Without this, Alembic autogenerates
anonymous PK/UNIQUE/CHECK constraints whose names are chosen by PostgreSQL.
Later ALTER/DROP migrations then depend on database-assigned names, which
differ between environments and break autogenerate diffing. Declaring the
convention once, before the schema grows, makes every constraint name
deterministic and reviewable in the migration.

Timestamp policy. `updated_at` uses SQLAlchemy's `onupdate`, which
fires for ORM-issued UPDATEs only. That is acceptable here because every write
in this project goes through the ORM; direct SQL that bypasses the ORM is
prohibited by convention. If a future requirement needs writes outside the ORM,
replace `onupdate` with a database trigger. This is documented rather than
silently assumed.

Audit-log rows are immutable and use CreatedAt (no updated_at). Credit-ledger
rows are non-deleting and auditable, but their exact lifecycle and timestamp
policy are defined in the Story 8.1 feature PR, not here. No credit model or
credit logic is added in this foundation.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Applied to every constraint and index in the schema.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )


class CreatedAt:
    """For append-only tables. No updated_at, by design."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Timestamps(CreatedAt):
    """For mutable entities. updated_at is ORM-managed (see module docstring)."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
