"""add bulk collection completion and flag fields

Revision ID: c2f4d1e6a322
Revises: c1e7a3d2b911
Create Date: 2026-08-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c2f4d1e6a322"
down_revision: str | None = "c1e7a3d2b911"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE bulkrequeststatus ADD VALUE IF NOT EXISTS 'COLLECTED'")
    op.add_column("bulk_pickup_requests", sa.Column("collected_at", sa.DateTime(timezone=True)))
    op.add_column(
        "bulk_pickup_requests",
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    severity_type = (
        postgresql.ENUM("ROUTINE", "HAZARDOUS", name="wasteseverity", create_type=False)
        if op.get_bind().dialect.name == "postgresql"
        else sa.String(length=20)
    )
    op.add_column("bulk_pickup_requests", sa.Column("flag_severity", severity_type))
    op.add_column("bulk_pickup_requests", sa.Column("flag_note", sa.String(length=300)))
    op.alter_column("bulk_pickup_requests", "is_flagged", server_default=None)


def downgrade() -> None:
    op.drop_column("bulk_pickup_requests", "flag_note")
    op.drop_column("bulk_pickup_requests", "flag_severity")
    op.drop_column("bulk_pickup_requests", "is_flagged")
    op.drop_column("bulk_pickup_requests", "collected_at")
