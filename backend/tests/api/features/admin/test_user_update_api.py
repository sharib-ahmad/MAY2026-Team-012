import pytest
from fastapi import status

from app.core.security import create_access_token, get_password_hash
from app.features.users.models import User
from app.models.enums import Role, UserStatus


@pytest.mark.integration
@pytest.mark.api
def test_admin_can_update_user_details(db_client, db):
    admin = User(
        name="Admin User",
        email="admin.update@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540001",
        role=Role.SYSTEM_ADMIN,
        status=UserStatus.ACTIVE,
    )
    target = User(
        name="Before Update",
        email="target.update@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540002",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
    )
    db.add_all([admin, target])
    db.commit()
    headers = {
        "Authorization": (
            f"Bearer {create_access_token(admin.id, token_version=admin.token_version)}"
        )
    }

    response = db_client.patch(
        f"/api/v1/admin/users/{target.id}",
        headers=headers,
        json={
            "name": "Updated User",
            "email": target.email,
            "phone": target.phone,
            "role": "SYSTEM_ADMIN",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["message"] == "User updated successfully"
    db.refresh(target)
    assert target.name == "Updated User"
    assert target.role == Role.SYSTEM_ADMIN
