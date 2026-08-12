from datetime import UTC, datetime

import pytest
from fastapi import status
from sqlalchemy import select

from app.core.security import get_password_hash
from app.features.users.models import User
from app.models.enums import Role, UserStatus
from app.models.zone import Zone


@pytest.mark.integration
@pytest.mark.api
def test_register_login_me_workflow(db_client, db, ward_a):
    register_payload = {
        "name": "Jane Citizen",
        "email": "jane.citizen@example.com",
        "password": "strongpassword123",
        "phone": "+919876543219",
        "address": "123 Green Street",
        "zone_id": str(ward_a.id),
        "role": "CITIZEN",
    }

    # 1. Register a new user
    response = db_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane.citizen@example.com"
    assert data["user"]["role"] == "CITIZEN"
    assert data["user"]["ward_code"] == "W-04"

    # Verify user exists in database
    db_user = db.scalar(select(User).where(User.email == "jane.citizen@example.com"))
    assert db_user is not None

    # 2. Login with valid credentials
    login_payload = {
        "email": "jane.citizen@example.com",
        "password": "strongpassword123",
    }
    response = db_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    login_data = response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    # 3. Login with invalid password
    bad_login_payload = {
        "email": "jane.citizen@example.com",
        "password": "wrongpassword",
    }
    response = db_client.post("/api/v1/auth/login", json=bad_login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 4. Access /me endpoint with authorization token
    headers = {"Authorization": f"Bearer {token}"}
    response = db_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    me_data = response.json()
    assert me_data["email"] == "jane.citizen@example.com"
    assert me_data["role"] == "CITIZEN"

    # 5. Access /me with invalid token
    bad_headers = {"Authorization": "Bearer invalidtoken"}
    response = db_client.get("/api/v1/auth/me", headers=bad_headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.api
def test_register_with_location(db_client, db, ward_a):
    register_payload = {
        "name": "Jane Citizen Map",
        "email": "jane.map@example.com",
        "password": "strongpassword123",
        "phone": "+919876543233",
        "address": "123 Map Street",
        "zone_id": str(ward_a.id),
        "role": "CITIZEN",
        "latitude": 26.8467,
        "longitude": 80.9462,
    }
    response = db_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_200_OK

    # Query database and verify coordinates
    db_user = db.scalar(select(User).where(User.email == "jane.map@example.com"))
    assert db_user is not None
    assert db_user.latitude == 26.8467
    assert db_user.longitude == 80.9462
    assert db_user.last_login_at is not None


@pytest.mark.integration
@pytest.mark.api
def test_login_updates_last_login_at(db_client, db, ward_a):
    # Register user first
    user = User(
        name="Login Test",
        email="login.test@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876543234",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(user)
    db.commit()
    assert user.last_login_at is None

    login_payload = {
        "email": "login.test@example.com",
        "password": "password123",
    }
    response = db_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK

    # Refresh model and verify last_login_at is populated
    db.refresh(user)
    assert user.last_login_at is not None


@pytest.mark.integration
@pytest.mark.api
def test_soft_deleted_user_cannot_login_or_me(db_client, db, ward_a):
    # Create soft-deleted user
    user = User(
        name="Deleted User",
        email="deleted@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876543235",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
        deleted_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()

    # Attempt login
    login_payload = {
        "email": "deleted@example.com",
        "password": "password123",
    }
    response = db_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.api
def test_zones_api_returns_all_five_zones(db_client, db):
    # Insert a test zone first
    zone = Zone(name="Test Zone", code="T-01", sectors="Sector A")
    db.add(zone)
    db.commit()

    response = db_client.get("/api/v1/zones")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "T-01 - Test Zone"
