"""add pickup recycler workflow statuses

Revision ID: e51b7d2c9a44
Revises: d41a9c5e7f3b
Create Date: 2026-08-03 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e51b7d2c9a44"
down_revision: str | None = "d41a9c5e7f3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE pickupstatus ADD VALUE IF NOT EXISTS 'RECYCLER_ASSIGNED'")
        op.execute("ALTER TYPE pickupstatus ADD VALUE IF NOT EXISTS 'PROCESSING'")
        op.execute("ALTER TYPE pickupstatus ADD VALUE IF NOT EXISTS 'PROCESSED'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be safely removed in place.
    pass
