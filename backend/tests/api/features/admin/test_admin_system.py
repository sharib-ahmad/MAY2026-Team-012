"""Story 5.1 provisioning lifecycle journey."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status

from app.models.enums import Role, UserStatus


@pytest.mark.system
@pytest.mark.integration
def test_admin_provisions_user_user_logs_in_admin_disables_and_reenables(
    db_client,
    ward_a,
    admin_user,
    admin_paths,
    bearer_for,
    user_create_payload,
    status_update_payload,
    extract_user_body,
    assert_safe_error,
):
    password = "StrongPass123!"
    email = f"journey-{uuid.uuid4().hex}@example.com"
    phone = f"+91{uuid.uuid4().int % 10**10:010d}"
    admin_headers = bearer_for(admin_user)

    created = db_client.post(
        admin_paths.create_user,
        headers=admin_headers,
        json=user_create_payload(
            admin_paths,
            name="Journey Citizen",
            email=email,
            phone=phone,
            password=password,
            role=Role.CITIZEN,
            ward=ward_a,
        ),
    )
    assert created.status_code == status.HTTP_201_CREATED
    created_user = extract_user_body(created)
    user_id = created_user["id"]

    login = db_client.post(
        admin_paths.login,
        json={"email": email, "password": password},
    )
    assert login.status_code == status.HTTP_200_OK
    old_token = login.json()["access_token"]

    me = db_client.get(
        admin_paths.me,
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert me.status_code == status.HTTP_200_OK
    assert str(me.json()["id"]) == str(user_id)
    assert me.json()["role"] == Role.CITIZEN.value
    assert me.json()["ward_code"] == ward_a.code

    disabled = db_client.patch(
        admin_paths.update_status.format(user_id=user_id),
        headers=admin_headers,
        json=status_update_payload(admin_paths, UserStatus.DISABLED),
    )
    assert disabled.status_code == status.HTTP_200_OK

    assert_safe_error(
        db_client.get(
            admin_paths.me,
            headers={"Authorization": f"Bearer {old_token}"},
        ),
        status.HTTP_401_UNAUTHORIZED,
        "AUTHENTICATION_REQUIRED",
    )
    assert_safe_error(
        db_client.post(
            admin_paths.login,
            json={"email": email, "password": password},
        ),
        status.HTTP_401_UNAUTHORIZED,
        "AUTHENTICATION_REQUIRED",
    )

    enabled = db_client.patch(
        admin_paths.update_status.format(user_id=user_id),
        headers=admin_headers,
        json=status_update_payload(admin_paths, UserStatus.ACTIVE),
    )
    assert enabled.status_code == status.HTTP_200_OK

    restored_login = db_client.post(
        admin_paths.login,
        json={"email": email, "password": password},
    )
    assert restored_login.status_code == status.HTTP_200_OK
    restored_me = db_client.get(
        admin_paths.me,
        headers={"Authorization": f"Bearer {restored_login.json()['access_token']}"},
    )
    assert restored_me.status_code == status.HTTP_200_OK
    assert restored_me.json()["role"] == Role.CITIZEN.value
