"""add pickup address

Revision ID: d8f184abac92
Revises: 5c9cfddc3b15
Create Date: 2026-07-31 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8f184abac92"
down_revision: str | None = "5c9cfddc3b15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pickups", sa.Column("pickup_address", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("pickups", "pickup_address")
