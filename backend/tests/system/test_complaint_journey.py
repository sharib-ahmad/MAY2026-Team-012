"""Cross-role system journey for citizen complaints.

Exercises the full ticket lifecycle through the real FastAPI application and a
disposable PostgreSQL database: a citizen raises a complaint, an authorised
municipal officer resolves it, the same citizen reads the resolved
server-written state back through their own API, reopens it, and a second
citizen is blocked from reopening a complaint they do not own.
"""

from __future__ import annotations

import pytest
from fastapi import status


@pytest.mark.system
def test_complaint_journey_flow(
    db_client,
    manager_user,
    citizen_user,
    second_citizen,
    bearer_for,
):
    headers_citizen = bearer_for(citizen_user)
    headers_manager = bearer_for(manager_user)
    headers_other_citizen = bearer_for(second_citizen)

    # ------- Step 1: Citizen creates a complaint -------
    create_resp = db_client.post(
        "/api/v1/complaints/tickets",
        headers=headers_citizen,
        json={
            "issue_type": "MISSED_PICKUP",
            "description": "Our street has not been collected for three days.",
        },
    )
    assert create_resp.status_code == status.HTTP_201_CREATED, (
        f"Step 1 (create) failed: {create_resp.text}"
    )
    created = create_resp.json()
    assert created["status"] == "OPEN"
    ticket_id = created["id"]

    # ------- Step 2: Authorised municipal officer resolves it -------
    resolve_resp = db_client.patch(
        f"/api/v1/manager/tickets/{ticket_id}",
        headers=headers_manager,
        json={"status": "RESOLVED", "resolution_notes": "Crew dispatched and street cleared."},
    )
    assert resolve_resp.status_code == status.HTTP_200_OK, (
        f"Step 2 (resolve) failed: {resolve_resp.text}"
    )
    assert resolve_resp.json()["status"] == "RESOLVED"

    # ------- Step 3: Same citizen reads the resolved server-written state -------
    list_resp = db_client.get("/api/v1/complaints/tickets", headers=headers_citizen)
    assert list_resp.status_code == status.HTTP_200_OK
    resolved_ticket = next(t for t in list_resp.json()["tickets"] if t["id"] == ticket_id)
    assert resolved_ticket["status"] == "RESOLVED"
    assert resolved_ticket["manager_note"] == "Crew dispatched and street cleared."

    # ------- Step 4: Citizen reopens it through the real API -------
    reopen_resp = db_client.post(
        f"/api/v1/complaints/{ticket_id}/reopen",
        headers=headers_citizen,
        json={"note": "The street was missed again this morning."},
    )
    assert reopen_resp.status_code == status.HTTP_200_OK, (
        f"Step 4 (reopen) failed: {reopen_resp.text}"
    )
    reopened = reopen_resp.json()
    assert reopened["status"] == "OPEN"
    assert "The street was missed again this morning." in reopened["description"]

    # ------- Step 5: Ownership boundary blocks another citizen from reopening -------
    boundary_resp = db_client.post(
        f"/api/v1/complaints/{ticket_id}/reopen",
        headers=headers_other_citizen,
        json={"note": "Trying to reopen someone else's complaint."},
    )
    assert boundary_resp.status_code == status.HTTP_404_NOT_FOUND, (
        "Step 5: A citizen must not be able to reopen another citizen's complaint"
    )

    # The ticket the owner reopened must be unaffected by the other citizen's attempt.
    final_list_resp = db_client.get("/api/v1/complaints/tickets", headers=headers_citizen)
    final_ticket = next(t for t in final_list_resp.json()["tickets"] if t["id"] == ticket_id)
    assert final_ticket["status"] == "OPEN"
