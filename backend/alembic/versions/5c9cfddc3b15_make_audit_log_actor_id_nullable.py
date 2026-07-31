"""make_audit_log_actor_id_nullable

Revision ID: 5c9cfddc3b15
Revises: f127488ab2e4
Create Date: 2026-07-30 22:18:28.194349
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "5c9cfddc3b15"
down_revision: str | None = "850d4848124e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Make actor_id nullable and add ON DELETE SET NULL
    op.alter_column(
        "audit_logs",
        "actor_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
        existing_nullable=False,
    )
    # Drop and recreate the foreign key with ON DELETE SET NULL
    op.drop_constraint("fk_audit_logs_actor_id_users", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "fk_audit_logs_actor_id_users",
        "audit_logs",
        "users",
        ["actor_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Revert to NOT NULL without ON DELETE SET NULL
    op.drop_constraint("fk_audit_logs_actor_id_users", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "fk_audit_logs_actor_id_users", "audit_logs", "users", ["actor_id"], ["id"]
    )
    op.alter_column(
        "audit_logs",
        "actor_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
        existing_nullable=True,
    )
