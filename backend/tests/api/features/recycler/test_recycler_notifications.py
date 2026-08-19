"""Recycler notification tests for SCRUM-194 Recycler QA.

Covers listing, marking read, marking all read, cross-tenant isolation,
and 404 for nonexistent notifications.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification

# ---------------------------------------------------------------------------
# RCY-N01 | List recycler notifications
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_list_recycler_notifications(
    db_client,
    recycler_paths,
    recycler_user,
    bearer_for,
    db: Session,
):
    """RCY-N01 | Recycler lists their own notifications."""
    db.add(
        Notification(
            user_id=recycler_user.id,
            title="Test notification",
            body="QA test body",
        )
    )
    db.flush()

    response = db_client.get(
        recycler_paths.recycler_notifications, headers=bearer_for(recycler_user)
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body) >= 1
    assert any(n["title"] == "Test notification" for n in body)


# ---------------------------------------------------------------------------
# RCY-N02 | Mark single notification read
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_mark_notification_read(
    db_client,
    recycler_paths,
    recycler_user,
    bearer_for,
    db: Session,
):
    """RCY-N02 | Marking a notification as read returns success."""
    notif = Notification(
        user_id=recycler_user.id,
        title="Read me",
        body="This should be marked read",
    )
    db.add(notif)
    db.flush()

    url = recycler_paths.recycler_mark_read.format(notification_id=notif.id)
    response = db_client.patch(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_200_OK

    db.refresh(notif)
    assert notif.is_read is True


# ---------------------------------------------------------------------------
# RCY-N03 | Mark all notifications read
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_mark_all_notifications_read(
    db_client,
    recycler_paths,
    recycler_user,
    bearer_for,
    db: Session,
):
    """RCY-N03 | Marking all notifications as read returns count."""
    for i in range(3):
        db.add(
            Notification(
                user_id=recycler_user.id,
                title=f"Notif {i}",
                body=f"Body {i}",
            )
        )
    db.flush()

    response = db_client.patch(
        recycler_paths.recycler_mark_all_read, headers=bearer_for(recycler_user)
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["marked_read"] >= 3


# ---------------------------------------------------------------------------
# RCY-N04 | Mark nonexistent notification → 404
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_mark_nonexistent_notification_returns_404(
    db_client,
    recycler_paths,
    recycler_user,
    bearer_for,
):
    """RCY-N04 | Nonexistent notification → 404."""
    url = recycler_paths.recycler_mark_read.format(notification_id=uuid.uuid4())
    response = db_client.patch(url, headers=bearer_for(recycler_user))
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# RCY-N05 | Cross-tenant notification isolation
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_cross_tenant_notification_isolation(
    db_client,
    recycler_paths,
    recycler_user,
    second_recycler,
    bearer_for,
    db: Session,
):
    """RCY-N05 | Recycler A cannot mark recycler B's notification as read."""
    notif = Notification(
        user_id=second_recycler.id,
        title="Secret notification",
        body="Only for recycler B",
    )
    db.add(notif)
    db.flush()

    url = recycler_paths.recycler_mark_read.format(notification_id=notif.id)
    response = db_client.patch(url, headers=bearer_for(recycler_user))
    # Should return 404 because mark_read service query filters by user_id
    assert response.status_code == status.HTTP_404_NOT_FOUND

    db.refresh(notif)
    assert notif.is_read is False, "Cross-tenant mark-read must not mutate"


# ---------------------------------------------------------------------------
# RCY-N06 | Empty notification list
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_empty_notification_list(
    db_client,
    recycler_paths,
    recycler_user,
    bearer_for,
):
    """RCY-N06 | Recycler with no notifications gets empty array."""
    response = db_client.get(
        recycler_paths.recycler_notifications, headers=bearer_for(recycler_user)
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
