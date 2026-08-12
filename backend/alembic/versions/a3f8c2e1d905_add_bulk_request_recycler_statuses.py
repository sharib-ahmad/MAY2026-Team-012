"""add bulk request recycler workflow statuses

Revision ID: a3f8c2e1d905
Revises: e51b7d2c9a44
Create Date: 2026-08-03 00:00:00.000000

The bulkrequeststatus enum was missing RECYCLER_ASSIGNED, PROCESSING, and
PROCESSED values that the recycler batch workflow requires.  Without them
PostgreSQL rejects the INSERT/UPDATE when process_batch (and the earlier
accept_batch) tries to sync BulkPickupRequest status, producing a 500 error
surfaced to the recycler as "Unable to mark this batch as processed."
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a3f8c2e1d905"
down_revision: str | None = "e51b7d2c9a44"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE bulkrequeststatus ADD VALUE IF NOT EXISTS 'RECYCLER_ASSIGNED'")
        op.execute("ALTER TYPE bulkrequeststatus ADD VALUE IF NOT EXISTS 'PROCESSING'")
        op.execute("ALTER TYPE bulkrequeststatus ADD VALUE IF NOT EXISTS 'PROCESSED'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be safely removed in-place without
    # recreating the type and all columns that reference it.  This migration
    # is intentionally left as a no-op on downgrade.
    pass
