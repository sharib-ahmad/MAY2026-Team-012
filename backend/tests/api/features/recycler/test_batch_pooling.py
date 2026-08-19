"""Automatic batch-pooling tests for SCRUM-194 Recycler QA.

Directly tests the pool_and_maybe_create_batches service to verify:
- 30 kg threshold triggers batch creation
- Categories are not mixed
- Sub-threshold pickups remain unbatched
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.materials.models import Batch
from app.features.materials.service import pool_and_maybe_create_batches

# ---------------------------------------------------------------------------
# RCY-P01 | Collected pickups create a batch at 30 kg threshold
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_collected_pickups_pool_at_thirty_kg(
    db: Session,
    citizen_user,
    collector_user,
    test_zone,
    waste_category,
    make_pickup,
):
    """RCY-P01 | Collected pickups create a batch when total ≥ 30 kg."""
    first = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        collector=collector_user,
        category=waste_category.code,
        weight=10.0,
    )
    second = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        collector=collector_user,
        category=waste_category.code,
        weight=20.0,
    )

    batches = pool_and_maybe_create_batches(db, test_zone.id)

    assert len(batches) == 1
    assert float(batches[0].declared_weight) == 30.0
    db.refresh(first)
    db.refresh(second)
    assert first.batch_id == batches[0].id
    assert second.batch_id == batches[0].id


# ---------------------------------------------------------------------------
# RCY-P02 | Pooling does not mix categories or create sub-threshold batches
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_pooling_does_not_mix_categories_or_create_subthreshold_batch(
    db: Session,
    citizen_user,
    collector_user,
    test_zone,
    waste_category,
    second_waste_category,
    make_pickup,
):
    """RCY-P02 | Pooling keeps categories separate below the threshold."""
    plastic = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        collector=collector_user,
        category=waste_category.code,
        weight=20.0,
    )
    paper = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        collector=collector_user,
        category=second_waste_category.code,
        weight=20.0,
    )

    batches = pool_and_maybe_create_batches(db, test_zone.id)

    assert batches == []
    assert db.scalars(select(Batch)).all() == []
    db.refresh(plastic)
    db.refresh(paper)
    assert plastic.batch_id is None
    assert paper.batch_id is None


# ---------------------------------------------------------------------------
# RCY-P03 | Sub-threshold single category stays unbatched
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_subthreshold_single_category_stays_unbatched(
    db: Session,
    citizen_user,
    collector_user,
    test_zone,
    waste_category,
    make_pickup,
):
    """RCY-P03 | 29 kg of a single category does not create a batch."""
    p = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        collector=collector_user,
        category=waste_category.code,
        weight=29.0,
    )

    batches = pool_and_maybe_create_batches(db, test_zone.id)

    assert batches == []
    db.refresh(p)
    assert p.batch_id is None


# ---------------------------------------------------------------------------
# RCY-P04 | Multiple batches from many pickups
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_multiple_batches_created_from_many_pickups(
    db: Session,
    citizen_user,
    collector_user,
    test_zone,
    waste_category,
    make_pickup,
):
    """RCY-P04 | 90 kg of pickups → at least 2 batches."""
    for _ in range(3):
        make_pickup(
            citizen=citizen_user,
            zone=test_zone,
            collector=collector_user,
            category=waste_category.code,
            weight=30.0,
        )

    batches = pool_and_maybe_create_batches(db, test_zone.id)

    assert len(batches) >= 2, f"Expected ≥ 2 batches from 90 kg, got {len(batches)}"
