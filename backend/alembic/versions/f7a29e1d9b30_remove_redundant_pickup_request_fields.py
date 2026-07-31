"""remove redundant pickup request fields

Revision ID: f7a29e1d9b30
Revises: e24b4cc7d673
Create Date: 2026-07-31 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f7a29e1d9b30"
down_revision: str | None = "e24b4cc7d673"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("pickups", "pickup_address")
    op.drop_column("bulk_pickup_requests", "pickup_address")
    op.drop_column("bulk_pickup_requests", "approx_volume")


def downgrade() -> None:
    import sqlalchemy as sa

    op.add_column("pickups", sa.Column("pickup_address", sa.String(length=500), nullable=True))
    op.add_column(
        "bulk_pickup_requests", sa.Column("pickup_address", sa.String(length=500), nullable=True)
    )
    op.add_column(
        "bulk_pickup_requests",
        sa.Column("approx_volume", sa.String(length=60), nullable=False, server_default=""),
    )
    op.alter_column("bulk_pickup_requests", "approx_volume", server_default=None)
