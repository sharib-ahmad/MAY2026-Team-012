"""add assigned bulk request status

Revision ID: c42d8f17e6a9
Revises: a91c7e34b2d5
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c42d8f17e6a9"
down_revision: str | None = "a91c7e34b2d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE bulkrequeststatus ADD VALUE IF NOT EXISTS 'ASSIGNED'")


def downgrade() -> None:
    # PostgreSQL cannot safely remove an enum value in place.
    pass
