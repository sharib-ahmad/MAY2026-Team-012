"""Full system journey test for SCRUM-194 Recycler QA.

End-to-end flow from batch creation through manager assignment,
recycler acceptance, processing, credit awarding, and notification delivery.
"""

from __future__ import annotations

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.credits.models import Credit
from app.features.notifications.models import Notification
from app.models.enums import CreditReason


@pytest.mark.api
def test_recycler_system_journey(
    db_client,
    recycler_paths,
    manager_user,
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
    """RCY-SYS | System journey: batch → assign → accept → process → credits.

    Steps:
    1. Setup: batch with a pickup (pre-created in COLLECTED status)
    2. Manager assigns batch to recycler
    3. Recycler accepts the batch
    4. Recycler processes the batch
    5. Verify credits awarded to citizen
    6. Verify notifications at each step
    7. Verify batch appears as PROCESSED in recycler's list
    8. Verify re-process attempt returns 409
    """
    # ------- Step 1: Setup batch with pickup -------
    batch = make_batch(
        collector=collector_user,
        zone=test_zone,
        category=waste_category.code,
    )
    pickup = make_pickup(
        citizen=citizen_user,
        zone=test_zone,
        category=waste_category.code,
        batch=batch,
        weight=25.0,
    )
    headers_mgr = bearer_for(manager_user)
    headers_rcy = bearer_for(recycler_user)

    # ------- Step 2: Manager assigns batch -------
    assign_url = recycler_paths.manager_assign.format(batch_id=batch.id)
    assign_resp = db_client.post(
        assign_url,
        headers=headers_mgr,
        json={"recycler_id": str(recycler_user.id)},
    )
    assert assign_resp.status_code == status.HTTP_200_OK, (
        f"Step 2 (assign) failed: {assign_resp.text}"
    )
    assert assign_resp.json()["status"] == "ASSIGNED"

    # Verify recycler received notification
    rcy_notif = db.scalar(
        select(Notification).where(
            Notification.user_id == recycler_user.id,
            Notification.title == "Batch assigned to you",
        )
    )
    assert rcy_notif is not None, "Step 2: Recycler should receive assignment notification"

    # ------- Step 3: Recycler accepts batch -------
    accept_url = recycler_paths.recycler_accept.format(batch_id=batch.id)
    accept_resp = db_client.post(accept_url, headers=headers_rcy)
    assert accept_resp.status_code == status.HTTP_200_OK, (
        f"Step 3 (accept) failed: {accept_resp.text}"
    )
    assert accept_resp.json()["status"] == "PROCESSING"

    # Verify citizen received processing notification
    cit_processing = db.scalar(
        select(Notification).where(
            Notification.user_id == citizen_user.id,
            Notification.title == "Pickup processing started",
        )
    )
    assert cit_processing is not None, "Step 3: Citizen should be notified of processing"

    # ------- Step 4: Recycler processes batch -------
    process_url = recycler_paths.recycler_process.format(batch_id=batch.id)
    process_resp = db_client.post(process_url, headers=headers_rcy)
    assert process_resp.status_code == status.HTTP_200_OK, (
        f"Step 4 (process) failed: {process_resp.text}"
    )
    assert process_resp.json()["status"] == "PROCESSED"

    # ------- Step 5: Verify credits awarded to citizen -------
    credit = db.scalar(
        select(Credit).where(
            Credit.pickup_id == pickup.id,
            Credit.reason == CreditReason.PICKUP_RECYCLING,
        )
    )
    assert credit is not None, "Step 5: Credit record should exist"
    assert credit.user_id == citizen_user.id, "Step 5: Credit should belong to citizen"
    # 25 kg × 2.5 rate = 62.5 credits
    assert float(credit.amount) == 62.5, f"Step 5: Expected 62.5 credits, got {credit.amount}"
    # 25 kg × 1.8 co2_factor = 45.0 kg CO2
    assert float(credit.co2_saved) == 45.0, (
        f"Step 5: Expected 45.0 CO2 saved, got {credit.co2_saved}"
    )

    # ------- Step 6: Verify citizen reward notification -------
    cit_reward = db.scalar(
        select(Notification).where(
            Notification.user_id == citizen_user.id,
            Notification.title == "Recycling reward credited",
        )
    )
    assert cit_reward is not None, "Step 6: Citizen should receive reward notification"

    # ------- Step 7: Verify recycler batch-processed notification -------
    rcy_processed = db.scalar(
        select(Notification).where(
            Notification.user_id == recycler_user.id,
            Notification.title == "Batch marked processed",
        )
    )
    assert rcy_processed is not None, "Step 7: Recycler should receive processed notification"

    # ------- Step 8: Verify batch appears in recycler's list -------
    list_resp = db_client.get(recycler_paths.recycler_batches, headers=headers_rcy)
    assert list_resp.status_code == status.HTTP_200_OK
    batches = list_resp.json()
    processed = [b for b in batches if b["ref_code"] == batch.ref_code]
    assert len(processed) == 1
    assert processed[0]["status"] == "PROCESSED"

    # ------- Step 9: Re-process attempt → 409 -------
    reprocess_resp = db_client.post(process_url, headers=headers_rcy)
    assert reprocess_resp.status_code == status.HTTP_409_CONFLICT, (
        "Step 9: Re-processing a PROCESSED batch should return 409"
    )
