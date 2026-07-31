"""add bulk pickup tracking fields

Revision ID: e24b4cc7d673
Revises: d8f184abac92
Create Date: 2026-07-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e24b4cc7d673"
down_revision: str | None = "d8f184abac92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bulk_pickup_requests", sa.Column("ref_code", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "bulk_pickup_requests", sa.Column("estimated_weight", sa.Numeric(10, 3), nullable=True)
    )
    op.add_column(
        "bulk_pickup_requests", sa.Column("time_slot", sa.String(length=30), nullable=True)
    )
    op.add_column(
        "bulk_pickup_requests", sa.Column("pickup_address", sa.String(length=500), nullable=True)
    )
    op.add_column("bulk_pickup_requests", sa.Column("notes", sa.String(length=500), nullable=True))
    op.execute(
        "UPDATE bulk_pickup_requests "
        "SET ref_code = 'BPR-' || upper(substr(replace(id::text, '-', ''), 1, 8)) "
        "WHERE ref_code IS NULL"
    )
    op.alter_column("bulk_pickup_requests", "ref_code", nullable=False)
    op.create_unique_constraint(
        "uq_bulk_pickup_requests_ref_code", "bulk_pickup_requests", ["ref_code"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_bulk_pickup_requests_ref_code", "bulk_pickup_requests", type_="unique")
    op.drop_column("bulk_pickup_requests", "notes")
    op.drop_column("bulk_pickup_requests", "pickup_address")
    op.drop_column("bulk_pickup_requests", "time_slot")
    op.drop_column("bulk_pickup_requests", "estimated_weight")
    op.drop_column("bulk_pickup_requests", "ref_code")
