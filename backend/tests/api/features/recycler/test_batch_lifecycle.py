"""Batch lifecycle tests for SCRUM-194 Recycler QA.

Covers: manager assign, recycler accept/reject/process, state transitions,
permission enforcement, adversarial boundary cases, and notification generation.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification
from app.models.enums import BatchStatus, PickupStatus, Role, UserStatus

# ---------------------------------------------------------------------------
# RCY-04 | Manager lists batches
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_list_batches_empty(db_client, recycler_paths, manager_user, bearer_for):
    """RCY-04a | Empty batch list returns 200 with empty array."""
    response = db_client.get(recycler_paths.manager_batches, headers=bearer_for(manager_user))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.api
def test_manager_list_batches_with_data(
    db_client,
    recycler_paths,
    manager_user,
    bearer_for,
    make_batch,
    make_pickup,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
):
    """RCY-04b | Manager sees batches in their zone with pickup data."""
    batch = make_batch(collector=collector_user, zone=test_zone, category=waste_category.code)
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    response = db_client.get(recycler_paths.manager_batches, headers=bearer_for(manager_user))
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body) >= 1
    batch_data = next((b for b in body if b["ref_code"] == batch.ref_code), None)
    assert batch_data is not None
    assert batch_data["status"] == "COLLECTED"
    assert batch_data["pickup_count"] >= 1


# ---------------------------------------------------------------------------
# RCY-05 | Manager lists recyclers
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_list_recyclers(db_client, recycler_paths, manager_user, recycler_user, bearer_for):
    """RCY-05 | Manager lists active recyclers."""
    response = db_client.get(recycler_paths.manager_recyclers, headers=bearer_for(manager_user))
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    recycler_ids = [r["id"] for r in body]
    assert str(recycler_user.id) in recycler_ids


# ---------------------------------------------------------------------------
# RCY-06 | Manager assigns batch to recycler
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_assign_batch_success(
    db_client,
    recycler_paths,
    manager_user,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-06 | Manager assigns COLLECTED batch → ASSIGNED, notifications sent."""
    batch = make_batch(collector=collector_user, zone=test_zone, category=waste_category.code)
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.manager_assign.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(manager_user),
        json={"recycler_id": str(recycler_user.id)},
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "ASSIGNED"
    assert body["destination_recycler_id"] == str(recycler_user.id)

    # Check recycler notification
    notif = db.scalar(
        select(Notification).where(
            Notification.user_id == recycler_user.id,
            Notification.title == "Batch assigned to you",
        )
    )
    assert notif is not None, "Recycler should receive assignment notification"

    # Check citizen notification for pickup assignment
    cit_notif = db.scalar(
        select(Notification).where(
            Notification.user_id == citizen_user.id,
            Notification.title == "Pickup assigned to recycler",
        )
    )
    assert cit_notif is not None, "Citizen should receive assignment notification"


# ---------------------------------------------------------------------------
# RCY-07 | Manager assigns batch outside their ward → 403
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_assign_batch_outside_ward(
    db_client,
    recycler_paths,
    manager_user,
    recycler_user,
    collector_user,
    citizen_user,
    second_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-07a | Manager cannot assign batch in a zone they don't manage."""
    batch = make_batch(collector=collector_user, zone=second_zone, category=waste_category.code)
    make_pickup(
        citizen=citizen_user,
        zone=second_zone,
        category=waste_category.code,
        batch=batch,
    )

    url = recycler_paths.manager_assign.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(manager_user),
        json={"recycler_id": str(recycler_user.id)},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.api
@pytest.mark.security
def test_manager_without_managed_ward_cannot_assign_batch(
    db_client,
    recycler_paths,
    make_user,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-07b | Manager with no ward assignment cannot assign any batch.

    KNOWN DEFECT: get_managed_zone_ids returns [] for unassigned managers,
    and assign_batch only enforces ward boundaries when the list is non-empty,
    so this test currently FAILS with 200 OK instead of 403.
    """
    unassigned_manager = make_user(role=Role.MUNICIPAL_OFFICER)
    batch = make_batch(collector=collector_user, zone=test_zone, category=waste_category.code)
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.manager_assign.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(unassigned_manager),
        json={"recycler_id": str(recycler_user.id)},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# RCY-08 | Manager assigns non-COLLECTED batch → 409
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.parametrize(
    "batch_status",
    [BatchStatus.ASSIGNED, BatchStatus.PROCESSING, BatchStatus.PROCESSED],
    ids=["assigned", "processing", "processed"],
)
def test_manager_assign_non_collected_batch(
    db_client,
    recycler_paths,
    manager_user,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    batch_status,
):
    """RCY-08 | Only COLLECTED batches can be assigned."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=batch_status,
        recycler=recycler_user if batch_status != BatchStatus.COLLECTED else None,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.manager_assign.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(manager_user),
        json={"recycler_id": str(recycler_user.id)},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# RCY-09 | Manager assigns to inactive/nonexistent recycler → 422
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_assign_to_nonexistent_recycler(
    db_client,
    recycler_paths,
    manager_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-09a | Assigning to nonexistent recycler → 422."""
    batch = make_batch(collector=collector_user, zone=test_zone, category=waste_category.code)
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.manager_assign.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(manager_user),
        json={"recycler_id": str(uuid.uuid4())},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
def test_manager_assign_to_disabled_recycler(
    db_client,
    recycler_paths,
    manager_user,
    make_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-09b | Assigning to disabled recycler → 422."""
    disabled_recycler = make_user(role=Role.RECYCLER, zone=test_zone, status=UserStatus.DISABLED)
    batch = make_batch(collector=collector_user, zone=test_zone, category=waste_category.code)
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.manager_assign.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(manager_user),
        json={"recycler_id": str(disabled_recycler.id)},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# RCY-10 | Recycler lists assigned batches
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_list_batches(
    db_client,
    recycler_paths,
    recycler_user,
    second_recycler,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-10 | Recycler sees only batches assigned to them."""
    # Batch assigned to this recycler
    my_batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=my_batch)

    # Batch assigned to other recycler (should NOT appear)
    other_batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=second_recycler,
    )
    make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=other_batch,
    )

    response = db_client.get(recycler_paths.recycler_batches, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body) >= 1
    assert all(b["destination_recycler_id"] == str(recycler_user.id) for b in body)


# ---------------------------------------------------------------------------
# RCY-11 | Recycler accepts batch → PROCESSING
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_accept_batch(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-11 | Recycler accepts ASSIGNED batch → PROCESSING, citizen notified."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=recycler_user,
    )
    pickup = make_pickup(
        citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch
    )

    url = recycler_paths.recycler_accept.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "PROCESSING"

    # Verify pickup status transitioned
    db.refresh(pickup)
    assert pickup.status == PickupStatus.PROCESSING

    # Citizen notification
    notif = db.scalar(
        select(Notification).where(
            Notification.user_id == citizen_user.id,
            Notification.title == "Pickup processing started",
        )
    )
    assert notif is not None


# ---------------------------------------------------------------------------
# RCY-12 | Recycler accepts batch not assigned to them → 403
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_accept_other_batch(
    db_client,
    recycler_paths,
    recycler_user,
    second_recycler,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-12 | Recycler cannot accept batch assigned to another recycler."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=second_recycler,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_accept.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# RCY-13 | Recycler accepts non-ASSIGNED batch → 409
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_accept_non_assigned_batch(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-13 | Can only accept ASSIGNED batches."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_accept.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# RCY-14 | Recycler rejects batch → COLLECTED, manager notified
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_reject_batch(
    db_client,
    recycler_paths,
    recycler_user,
    manager_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-14 | Recycler rejects batch → COLLECTED, reason saved, manager notified."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_reject.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(recycler_user),
        json={"note": "Contaminated material"},
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "COLLECTED"
    assert body["rejection_reason"] == "Contaminated material"
    assert body["destination_recycler_id"] is None

    # Manager notification
    notif = db.scalar(
        select(Notification).where(
            Notification.user_id == manager_user.id,
            Notification.title == "Batch rejected by recycler",
        )
    )
    assert notif is not None, "Manager should be notified of rejection"


# ---------------------------------------------------------------------------
# RCY-15 | Recycler rejects batch not assigned to them → 403
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_reject_other_batch(
    db_client,
    recycler_paths,
    recycler_user,
    second_recycler,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-15 | Recycler cannot reject batch assigned to another recycler."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=second_recycler,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_reject.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(recycler_user),
        json={"note": "Should fail"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# RCY-16 | Recycler rejects non-ASSIGNED batch → 409
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_reject_non_assigned_batch(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-16a | Can only reject ASSIGNED batches."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_reject.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(recycler_user),
        json={"note": "Should fail"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.api
@pytest.mark.boundary
def test_recycler_reject_whitespace_only_note(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-16b | Whitespace-only rejection notes must be rejected.

    KNOWN DEFECT: RejectBatchRequest uses min_length=1 which accepts " ",
    and the service stores note.strip() as empty string. Expected 422.
    """
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_reject.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(recycler_user),
        json={"note": " "},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Verify batch state unchanged on rejection failure
    db.refresh(batch)
    assert batch.status == BatchStatus.ASSIGNED


# ---------------------------------------------------------------------------
# RCY-17 | Recycler processes batch → PROCESSED, credits awarded
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_process_batch(
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
    """RCY-17 | Recycler processes batch → PROCESSED, credits + notifications."""
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
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "PROCESSED"

    # Verify pickup updated
    db.refresh(pickup)
    assert pickup.status == PickupStatus.PROCESSED

    # Verify recycler notification
    notif = db.scalar(
        select(Notification).where(
            Notification.user_id == recycler_user.id,
            Notification.title == "Batch marked processed",
        )
    )
    assert notif is not None


# ---------------------------------------------------------------------------
# RCY-18 | Recycler processes batch not assigned to them → 403
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_process_other_batch(
    db_client,
    recycler_paths,
    recycler_user,
    second_recycler,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-18 | Recycler cannot process batch assigned to another recycler."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=second_recycler,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# RCY-19 | Recycler processes non-PROCESSING batch → 409
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_recycler_process_non_processing_batch(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
):
    """RCY-19 | Can only process PROCESSING batches."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.ASSIGNED,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# RCY-20 | Batch with no pickups cannot be processed → 400
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_process_batch_with_no_pickups(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
):
    """RCY-20 | Batch with zero pickups → 400 BAD_REQUEST."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )

    url = recycler_paths.recycler_process.format(batch_id=batch.id)
    response = db_client.post(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# RCY-21 | Assign nonexistent batch → 404
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_assign_nonexistent_batch(
    db_client, recycler_paths, manager_user, recycler_user, bearer_for
):
    """RCY-21 | Assigning a nonexistent batch → 404."""
    url = recycler_paths.manager_assign.format(batch_id=uuid.uuid4())
    response = db_client.post(
        url,
        headers=bearer_for(manager_user),
        json={"recycler_id": str(recycler_user.id)},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# RCY-22 | Batch state unchanged after rejected rejection attempt
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_batch_state_unchanged_after_failed_rejection(
    db_client,
    recycler_paths,
    recycler_user,
    collector_user,
    citizen_user,
    test_zone,
    waste_category,
    bearer_for,
    make_batch,
    make_pickup,
    db: Session,
):
    """RCY-22 | Failed rejection must not alter batch state."""
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
        status=BatchStatus.PROCESSING,
        recycler=recycler_user,
    )
    make_pickup(citizen=citizen_user, zone=test_zone, category=waste_category.code, batch=batch)

    url = recycler_paths.recycler_reject.format(batch_id=batch.id)
    response = db_client.post(
        url,
        headers=bearer_for(recycler_user),
        json={"note": "Invalid state attempt"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    db.refresh(batch)
    assert batch.status == BatchStatus.PROCESSING
    assert batch.destination_recycler_id == recycler_user.id
