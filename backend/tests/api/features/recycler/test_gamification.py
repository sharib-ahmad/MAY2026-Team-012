"""Gamification / credit-awarding tests for SCRUM-194 Recycler QA.

Verifies that processing a batch correctly awards green credits and CO2
savings to the citizen who scheduled the pickup, with idempotency and
graceful fallback for missing credit factors.
"""

from __future__ import annotations

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.credits.models import Credit
from app.models.enums import BatchStatus, CreditReason, PickupStatus

# ---------------------------------------------------------------------------
# RCY-G01 | Credits awarded correctly on batch process
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_credits_awarded_on_process(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    credit_factor,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-G01 | amount = weight × rate, co2_saved = weight × co2_factor."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    pickup = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=20.0,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK

    # credit_rate = 2.5, co2_factor = 1.8 (from credit_factor fixture)
    expected_credits = round(20.0 * 2.5, 2)  # 50.0
    expected_co2 = round(20.0 * 1.8, 3)  # 36.0

    credit = db.scalar(
        select(Credit).where(
            Credit.pickup_id == pickup.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    )
    assert credit is not None, "Credit record should be created"
    assert float(credit.amount) == expected_credits
    assert float(credit.co2_saved) == expected_co2
    assert credit.user_id == citizen_user.id


# ---------------------------------------------------------------------------
# RCY-G02 | Credits are idempotent — re-processing returns 409
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_credits_idempotent(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    credit_factor,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-G02 | Processing same batch again returns 409 and doesn't double-award."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    pickup = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=15.0,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)

    # First process — should succeed
    response1 = db_client.post(url, headers=bearer_for(recycler_user))
    assert response1.status_code == status.HTTP_200_OK

    # Second process — batch is now PROCESSED, should get 409
    response2 = db_client.post(url, headers=bearer_for(recycler_user))
    assert response2.status_code == status.HTTP_409_CONFLICT

    # Count credits — only one
    credits = db.scalars(
        select(Credit).where(
            Credit.pickup_id == pickup.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    ).all()
    assert len(credits) == 1, "Only one credit record should exist per pickup"


# ---------------------------------------------------------------------------
# RCY-G03 | Missing CreditFactor → 0 credits, 0 CO2
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_missing_credit_factor_graceful_fallback(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    second_waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-G03 | No CreditFactor for category → 0 credits, 0 CO2 (graceful)."""
    # Use PAPER category which has no CreditFactor fixture
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=second_waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    pickup = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=second_waste_category.code,
        batch=batch,
        weight=10.0,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK

    credit = db.scalar(
        select(Credit).where(
            Credit.pickup_id == pickup.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    )
    assert credit is not None
    assert float(credit.amount) == 0.0
    assert float(credit.co2_saved) == 0.0


# ---------------------------------------------------------------------------
# RCY-G04 | Pickup fields updated after processing
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_pickup_fields_updated_on_process(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    credit_factor,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-G04 | credit_rate_applied, co2_factor_applied, credits_earned, co2_saved."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    pickup = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=10.0,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK

    db.refresh(pickup)
    assert pickup.status == PickupStatus.PROCESSED
    assert float(pickup.credit_rate_applied) == 2.5
    assert float(pickup.co2_factor_applied) == 1.8
    assert float(pickup.credits_earned) == round(10.0 * 2.5, 2)
    assert float(pickup.co2_saved) == round(10.0 * 1.8, 3)
    assert pickup.completed_at is not None


# ---------------------------------------------------------------------------
# RCY-G05 | Credit record has correct user_id and reason
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_credit_record_correctness(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    credit_factor,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-G05 | Credit has correct user_id (citizen), pickup_id, reason."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    pickup = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=12.0,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK

    credit = db.scalar(
        select(Credit).where(
            Credit.pickup_id == pickup.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    )
    assert credit is not None
    assert credit.user_id == citizen_user.id, "Credit should be for the citizen"
    assert credit.pickup_id == pickup.id
    assert credit.reason == CreditReason.PICKUP_RECYCLING


# ---------------------------------------------------------------------------
# RCY-G06 | Multi-pickup batch: each pickup gets its own credit
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_multi_pickup_batch_credits(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    second_citizen,
    test_zone,
    waste_category,
    credit_factor,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-G06 | Each pickup in a batch gets its own credit for its citizen."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
        weight=50.0,
    )
    p1 = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=20.0,
    )
    p2 = make_pickup(
        citizen=second_citizen,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=30.0,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK

    credit1 = db.scalar(
        select(Credit).where(
            Credit.pickup_id == p1.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    )
    credit2 = db.scalar(
        select(Credit).where(
            Credit.pickup_id == p2.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    )
    assert credit1 is not None and credit2 is not None
    assert credit1.user_id == citizen_user.id
    assert credit2.user_id == second_citizen.id
    assert float(credit1.amount) == round(20.0 * 2.5, 2)
    assert float(credit2.amount) == round(30.0 * 2.5, 2)
