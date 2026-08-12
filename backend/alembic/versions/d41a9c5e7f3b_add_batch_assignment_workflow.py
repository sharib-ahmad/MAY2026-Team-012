"""add batch assignment workflow columns and statuses

Revision ID: d41a9c5e7f3b
Revises: c2f4d1e6a322
Create Date: 2026-08-03 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d41a9c5e7f3b"
down_revision: str | None = "c2f4d1e6a322"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE batchstatus ADD VALUE IF NOT EXISTS 'ASSIGNED'")
        op.execute("ALTER TYPE batchstatus ADD VALUE IF NOT EXISTS 'PROCESSING'")

    op.alter_column("batches", "assigned_by_id", existing_type=sa.UUID(), nullable=True)
    op.add_column("batches", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("batches", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("batches", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("batches", "processed_at")
    op.drop_column("batches", "rejected_at")
    op.drop_column("batches", "assigned_at")
    op.alter_column("batches", "assigned_by_id", existing_type=sa.UUID(), nullable=False)
