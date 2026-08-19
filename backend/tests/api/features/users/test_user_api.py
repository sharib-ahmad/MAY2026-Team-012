from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.features.notifications.models import Notification
from app.features.users.models import User
from app.models.audit import AuditLog
from app.models.enums import Role, UserStatus

# R1: both endpoints are citizen-only. Requests through them without a valid
# citizen session must be rejected server-side, not merely hidden in the UI.
CITIZEN_ONLY_ENDPOINTS = [
    ("DELETE", "/api/v1/user/account", {"reason": "test"}),
    ("POST", "/api/v1/user/chatbot/message", {"message": "hi", "history": []}),
]


@pytest.mark.integration
@pytest.mark.api
def test_delete_citizen_account_api_workflow(db_client, db, ward_a):
    # Provision the citizen directly through the ORM/token fixtures used
    # elsewhere in this suite, not through POST /api/v1/auth/register: that
    # endpoint is documented (api-doc.yaml, docs/qa/endpoint-inventory.md) as
    # a known contract defect that lets an unauthenticated caller
    # self-provision any role, contradicting Story 5.1's admin-provisioned
    # identity model - test setup must not lean on it.
    citizen = User(
        name="Jane SoftDelete",
        email="jane.softdelete@example.com",
        password_hash=get_password_hash("strongpassword123"),
        phone="+919876543001",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(citizen)
    db.commit()
    db.refresh(citizen)
    user_id = citizen.id
    token = create_access_token(citizen.id, token_version=citizen.token_version)

    # Assign a manager to ward_a if not already there so a notification gets created
    manager_user = User(
        name="Ward Manager",
        email="manager@example.com",
        phone="+919876543002",
        role=Role.MUNICIPAL_OFFICER,
        status=UserStatus.ACTIVE,
        password_hash="fakehashpassword",
    )
    db.add(manager_user)
    db.commit()
    db.refresh(manager_user)

    ward_a.manager_id = manager_user.id
    db.commit()

    # 2. Call DELETE /api/v1/user/account
    headers = {"Authorization": f"Bearer {token}"}
    delete_payload = {"reason": "Moving away from ward"}
    delete_response = db_client.request(
        "DELETE", "/api/v1/user/account", json=delete_payload, headers=headers
    )
    assert delete_response.status_code == status.HTTP_200_OK

    # Refresh DB session to get updated records
    db.expire_all()

    # 3. Query the user from DB to verify soft delete and anonymization
    db_user = db.scalar(select(User).where(User.id == user_id))
    assert db_user is not None
    assert db_user.deleted_at is not None
    assert db_user.status == UserStatus.DISABLED
    assert db_user.email.startswith("jane.softdelete@example.com-deleted-")
    assert db_user.phone.startswith("del-")

    # 4. Verify notification was sent to manager
    notif = db.scalar(select(Notification).where(Notification.user_id == manager_user.id))
    assert notif is not None
    assert "jane.softdelete@example.com" in notif.body
    assert "Moving away from ward" in notif.body

    # 5. Verify audit log entry exists
    audit_entry = db.scalar(
        select(AuditLog).where(
            AuditLog.actor_name == "Jane SoftDelete", AuditLog.action == "DELETE_ACCOUNT"
        )
    )
    assert audit_entry is not None
    assert audit_entry.action == "DELETE_ACCOUNT"
    assert "Moving away from ward" in audit_entry.description

    # 6. Verify that accessing /me endpoint fails with old token (due to token_version bump)
    me_response = db_client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED

    # 7. Verify the original email/phone are free for reuse - anonymization
    # must have released the unique constraints. Checked at the ORM level
    # (the approved provisioning path here) rather than via
    # POST /api/v1/auth/register, per the note above.
    returning_citizen = User(
        name="Jane Returning",
        email="jane.softdelete@example.com",
        password_hash=get_password_hash("anotherpassword123"),
        phone="+919876543001",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(returning_citizen)
    db.commit()
    db.refresh(returning_citizen)
    assert returning_citizen.email == "jane.softdelete@example.com"
    assert returning_citizen.id != user_id


@pytest.mark.integration
@pytest.mark.api
@patch("app.features.users.router.execute_chatbot_turn", new_callable=AsyncMock)
def test_chatbot_api_workflow(mock_execute_chatbot_turn, db_client, db, ward_a):
    # Mock the return value of execute_chatbot_turn
    mock_execute_chatbot_turn.return_value = {
        "reply": "Here are your recent pickups:",
        "history": [
            {"role": "user", "text": "Show my pickups"},
            {"role": "bot", "text": "Here are your recent pickups:"},
        ],
    }

    # Provision the citizen directly via the ORM (see the provisioning-path
    # note in test_delete_citizen_account_api_workflow above) rather than
    # POST /api/v1/auth/register.
    citizen = User(
        name="Jane Chatbot",
        email="jane.chatbot@example.com",
        password_hash=get_password_hash("strongpassword123"),
        phone="+919876543003",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(citizen)
    db.commit()
    db.refresh(citizen)
    token = create_access_token(citizen.id, token_version=citizen.token_version)

    # Call POST /api/v1/user/chatbot/message
    headers = {"Authorization": f"Bearer {token}"}
    chat_payload = {"message": "Show my pickups", "history": []}
    chat_res = db_client.post("/api/v1/user/chatbot/message", json=chat_payload, headers=headers)
    assert chat_res.status_code == status.HTTP_200_OK

    data = chat_res.json()
    assert data["reply"] == "Here are your recent pickups:"
    assert len(data["history"]) == 2
    assert data["history"][0]["role"] == "user"
    assert data["history"][1]["role"] == "bot"


@pytest.mark.security
@pytest.mark.api
@pytest.mark.parametrize("method,path,json_body", CITIZEN_ONLY_ENDPOINTS)
def test_citizen_only_endpoints_reject_unauthenticated(db_client, method, path, json_body):
    response = db_client.request(method, path, json=json_body)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.security
@pytest.mark.api
@pytest.mark.parametrize("method,path,json_body", CITIZEN_ONLY_ENDPOINTS)
def test_citizen_only_endpoints_reject_non_citizen_role(
    db_client, db, ward_a, method, path, json_body
):
    worker = User(
        name="Wrong Role Worker",
        email="wrong.role.worker@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540099",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(worker)
    db.commit()

    token = create_access_token(worker.id, token_version=worker.token_version)
    headers = {"Authorization": f"Bearer {token}"}
    response = db_client.request(method, path, json=json_body, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
