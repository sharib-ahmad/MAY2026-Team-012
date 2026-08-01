"""Story 5.1 administrator user-provisioning tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy import func, select

from app.core.security import verify_password
from app.features.admin import router as admin_router
from app.features.users.models import User
from app.models.audit import AuditLog
from app.models.enums import Role, UserStatus


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.parametrize(
    "role",
    [
        Role.CITIZEN,
        Role.COLLECTION_WORKER,
        Role.MUNICIPAL_OFFICER,
        Role.RECYCLER,
    ],
)
def test_admin_can_provision_each_supported_role_with_safe_canonical_output(
    db_client,
    db,
    ward_a,
    admin_user,
    admin_paths,
    bearer_for,
    user_create_payload,
    extract_user_body,
    assert_safe_public_body,
    role,
):
    suffix = uuid.uuid4().hex
    email = f"{role.value.lower()}-{suffix}@example.com"
    phone = f"+91{uuid.uuid4().int % 10**10:010d}"
    password = "StrongPass123!"

    response = db_client.post(
        admin_paths.create_user,
        headers=bearer_for(admin_user),
        json=user_create_payload(
            admin_paths,
            name=f"{role.value} User",
            email=email,
            phone=phone,
            password=password,
            role=role,
            ward=ward_a,
        ),
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text

    persisted = db.scalar(select(User).where(User.email == email))
    assert persisted is not None
    assert persisted.role == role
    assert persisted.zone_id == ward_a.id
    assert persisted.status == UserStatus.ACTIVE
    assert persisted.last_login_at is None
    assert persisted.password_hash != password
    assert verify_password(password, persisted.password_hash)

    audit = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "User",
            AuditLog.entity_id == persisted.id,
            AuditLog.action == "ACCOUNT_CREATED",
        )
    )
    assert audit is not None
    assert audit.actor_id == admin_user.id

    body = extract_user_body(response)
    assert str(body["id"]) == str(persisted.id)
    assert body["role"] == role.value
    assert body["ward_code"] == ward_a.code
    assert_safe_public_body(response, additional_forbidden_keys={"zone_id"})


@pytest.mark.api
@pytest.mark.integration
def test_admin_dashboard_lists_users_with_safe_canonical_fields(
    db_client,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    assert_safe_public_body,
):
    alpha = make_user(name="Alpha User", email="alpha@example.com")
    bravo = make_user(name="Bravo User", email="bravo@example.com")

    response = db_client.get(
        admin_paths.dashboard,
        headers=bearer_for(admin_user),
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert {"stats", "users"} <= set(body)
    assert isinstance(body["users"], list)

    returned_ids = {str(item["id"]) for item in body["users"]}
    assert {str(alpha.id), str(bravo.id)} <= returned_ids

    for item in body["users"]:
        assert {"id", "name", "email", "phone", "role", "status"} <= set(item)
        assert item["role"] in {role.value for role in Role}

    assert_safe_public_body(response, additional_forbidden_keys={"zone_id"})


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.parametrize(
    "duplicate_case",
    ["email-exact", "email-normalised", "phone"],
)
def test_duplicate_email_and_phone_are_rejected_without_creating_a_second_user(
    db_client,
    db,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    user_create_payload,
    assert_safe_error,
    duplicate_case,
):
    existing = make_user(
        email="duplicate@example.com",
        phone="+919876543233",
    )
    before = db.scalar(select(func.count(User.id)))

    email = f"new-{uuid.uuid4().hex}@example.com"
    phone = f"+91{uuid.uuid4().int % 10**10:010d}"
    if duplicate_case == "email-exact":
        email = existing.email
    elif duplicate_case == "email-normalised":
        email = f"  {existing.email.upper()}  "
    else:
        phone = existing.phone

    response = db_client.post(
        admin_paths.create_user,
        headers=bearer_for(admin_user),
        json=user_create_payload(
            admin_paths,
            name="Duplicate Candidate",
            email=email,
            phone=phone,
            password="StrongPass123!",
            role=Role.CITIZEN,
        ),
    )

    after = db.scalar(select(func.count(User.id)))
    assert after == before
    assert_safe_error(
        response,
        status.HTTP_409_CONFLICT,
        {"CONFLICT", "DUPLICATE_RESOURCE"},
    )


@pytest.mark.api
@pytest.mark.security
@pytest.mark.boundary
@pytest.mark.parametrize(
    "case_name",
    [
        "mass-assignment",
        "blank-name",
        "password-over-72-bytes",
        "invalid-role",
        "unknown-ward",
    ],
)
def test_admin_create_rejects_unsafe_or_invalid_input_without_persistence(
    db_client,
    db,
    admin_user,
    admin_paths,
    ward_a,
    bearer_for,
    user_create_payload,
    assert_safe_error,
    case_name,
):
    suffix = uuid.uuid4().hex
    email = f"unsafe-{suffix}@example.com"
    payload = user_create_payload(
        admin_paths,
        name="Boundary User",
        email=email,
        phone=f"+91{uuid.uuid4().int % 10**10:010d}",
        password="StrongPass123!",
        role=Role.CITIZEN,
        ward=ward_a,
    )
    secret_values: set[str] = set()

    if case_name == "mass-assignment":
        payload.update(
            {
                "status": "ACTIVE",
                "token_version": 999,
                "password_hash": "injected-secret-hash",
                "deleted_at": "2026-01-01T00:00:00Z",
            }
        )
        secret_values.add("injected-secret-hash")
    elif case_name == "blank-name":
        payload["name"] = "   "
    elif case_name == "password-over-72-bytes":
        payload["password"] = "a" * 73
    elif case_name == "invalid-role":
        payload["role"] = "SUPERUSER"
    elif case_name == "unknown-ward":
        payload["zone_id"] = str(uuid.uuid4())

    response = db_client.post(
        admin_paths.create_user,
        headers=bearer_for(admin_user),
        json=payload,
    )

    assert db.scalar(select(User).where(User.email == email.strip().lower())) is None
    assert_safe_error(
        response,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        secret_values=secret_values,
    )


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_disabling_user_revokes_login_and_existing_token_atomically(
    db_client,
    db,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    status_update_payload,
    assert_safe_error,
):
    password = "StrongPass123!"
    user = make_user(
        email="disable-target@example.com",
        phone="+919876543236",
        password=password,
        role=Role.CITIZEN,
    )
    old_version = user.token_version
    old_headers = bearer_for(user)

    update = db_client.patch(
        admin_paths.update_status.format(user_id=user.id),
        headers=bearer_for(admin_user),
        json=status_update_payload(admin_paths, UserStatus.DISABLED),
    )
    login = db_client.post(
        admin_paths.login,
        json={"email": user.email, "password": password},
    )
    me = db_client.get(admin_paths.me, headers=old_headers)

    db.refresh(user)
    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "User",
            AuditLog.entity_id == user.id,
            AuditLog.action == "USER_STATUS_CHANGED",
        )
    ).all()

    assert update.status_code == status.HTTP_200_OK
    assert user.status == UserStatus.DISABLED
    assert user.token_version == old_version + 1
    assert audits
    assert audits[-1].actor_id == admin_user.id
    assert_safe_error(login, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED")
    assert_safe_error(me, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_role_change_invalidates_old_token_and_enforces_new_role(
    db_client,
    db,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    role_update_payload,
    assert_safe_error,
):
    user = make_user(
        email="role-target@example.com",
        phone="+919876543237",
        role=Role.CITIZEN,
    )
    old_version = user.token_version
    old_headers = bearer_for(user)

    update = db_client.patch(
        admin_paths.update_user.format(user_id=user.id),
        headers=bearer_for(admin_user),
        json=role_update_payload(admin_paths, Role.COLLECTION_WORKER),
    )
    stale_me = db_client.get(admin_paths.me, headers=old_headers)

    db.refresh(user)
    assert update.status_code == status.HTTP_200_OK
    assert user.role == Role.COLLECTION_WORKER
    assert user.token_version == old_version + 1
    assert_safe_error(stale_me, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED")

    fresh_me = db_client.get(admin_paths.me, headers=bearer_for(user))
    assert fresh_me.status_code == status.HTTP_200_OK
    assert fresh_me.json()["role"] == Role.COLLECTION_WORKER.value


@pytest.mark.api
@pytest.mark.integration
def test_reenable_restores_login_and_records_both_state_changes(
    db_client,
    db,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    status_update_payload,
):
    password = "StrongPass123!"
    user = make_user(
        email="reenable-target@example.com",
        phone="+919876543238",
        password=password,
    )
    headers = bearer_for(admin_user)

    disabled = db_client.patch(
        admin_paths.update_status.format(user_id=user.id),
        headers=headers,
        json=status_update_payload(admin_paths, UserStatus.DISABLED),
    )
    enabled = db_client.patch(
        admin_paths.update_status.format(user_id=user.id),
        headers=headers,
        json=status_update_payload(admin_paths, UserStatus.ACTIVE),
    )
    login = db_client.post(
        admin_paths.login,
        json={"email": user.email, "password": password},
    )

    db.refresh(user)
    status_audits = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "User",
            AuditLog.entity_id == user.id,
            AuditLog.action == "USER_STATUS_CHANGED",
        )
        .order_by(AuditLog.created_at)
    ).all()

    assert disabled.status_code == status.HTTP_200_OK
    assert enabled.status_code == status.HTTP_200_OK
    assert user.status == UserStatus.ACTIVE
    assert login.status_code == status.HTTP_200_OK
    assert len(status_audits) == 2
    assert all(audit.actor_id == admin_user.id for audit in status_audits)


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
@pytest.mark.parametrize("operation", ["disable", "demote"])
def test_last_active_administrator_cannot_be_disabled_or_demoted(
    db_client,
    db,
    admin_user,
    admin_paths,
    bearer_for,
    status_update_payload,
    role_update_payload,
    assert_safe_error,
    operation,
):
    if operation == "disable":
        response = db_client.patch(
            admin_paths.update_status.format(user_id=admin_user.id),
            headers=bearer_for(admin_user),
            json=status_update_payload(admin_paths, UserStatus.DISABLED),
        )
    else:
        response = db_client.patch(
            admin_paths.update_user.format(user_id=admin_user.id),
            headers=bearer_for(admin_user),
            json=role_update_payload(admin_paths, Role.MUNICIPAL_OFFICER),
        )

    db.refresh(admin_user)
    assert admin_user.role == Role.SYSTEM_ADMIN
    assert admin_user.status == UserStatus.ACTIVE
    assert_safe_error(response, status.HTTP_409_CONFLICT, "CONFLICT")


@pytest.mark.api
@pytest.mark.integration
def test_second_active_admin_allows_one_admin_to_be_demoted(
    db_client,
    db,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    role_update_payload,
):
    make_user(role=Role.SYSTEM_ADMIN)

    response = db_client.patch(
        admin_paths.update_user.format(user_id=admin_user.id),
        headers=bearer_for(admin_user),
        json=role_update_payload(admin_paths, Role.MUNICIPAL_OFFICER),
    )

    db.refresh(admin_user)
    remaining = db.scalar(
        select(func.count(User.id)).where(
            User.role == Role.SYSTEM_ADMIN,
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
        )
    )
    assert response.status_code == status.HTTP_200_OK
    assert admin_user.role == Role.MUNICIPAL_OFFICER
    assert remaining >= 1


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_audit_failure_rolls_back_user_creation(
    db_client,
    db,
    admin_user,
    admin_paths,
    bearer_for,
    user_create_payload,
    monkeypatch,
):
    email = "audit-failure@example.com"
    calls = {"count": 0}

    def fail_audit(*_args, **_kwargs):
        calls["count"] += 1
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr(admin_router, "create_audit_log", fail_audit)

    with pytest.raises(RuntimeError, match="simulated audit failure"):
        db_client.post(
            admin_paths.create_user,
            headers=bearer_for(admin_user),
            json=user_create_payload(
                admin_paths,
                name="Atomic User",
                email=email,
                phone="+919876543239",
                password="StrongPass123!",
                role=Role.CITIZEN,
            ),
        )

    assert calls["count"] == 1
    assert db.scalar(select(User).where(User.email == email)) is None
