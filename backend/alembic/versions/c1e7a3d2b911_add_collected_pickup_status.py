"""add collected pickup status

Revision ID: c1e7a3d2b911
Revises: f7a29e1d9b30
Create Date: 2026-08-01 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c1e7a3d2b911"
down_revision: tuple[str, str] = ("f7a29e1d9b30", "c42d8f17e6a9")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE pickupstatus ADD VALUE IF NOT EXISTS 'COLLECTED'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be safely removed in place.
    pass
