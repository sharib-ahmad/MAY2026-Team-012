"""add bulk pickup collector assignment

Revision ID: a91c7e34b2d5
Revises: f7a29e1d9b30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a91c7e34b2d5"
down_revision: str | None = "f7a29e1d9b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bulk_pickup_requests",
        sa.Column("assigned_collector_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_bulk_pickup_requests_assigned_collector_id_users",
        "bulk_pickup_requests",
        "users",
        ["assigned_collector_id"],
        ["id"],
    )
    op.create_index(
        "ix_bulk_pickup_requests_assigned_collector_id",
        "bulk_pickup_requests",
        ["assigned_collector_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_bulk_pickup_requests_assigned_collector_id", table_name="bulk_pickup_requests"
    )
    op.drop_constraint(
        "fk_bulk_pickup_requests_assigned_collector_id_users",
        "bulk_pickup_requests",
        type_="foreignkey",
    )
    op.drop_column("bulk_pickup_requests", "assigned_collector_id")
