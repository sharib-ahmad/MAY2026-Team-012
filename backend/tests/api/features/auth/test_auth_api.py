"""Registration and zone-lookup API tests retained from main.

Login, /me, session revocation and account-state coverage now lives in
``test_auth_login.py`` and ``test_auth_session.py`` (SCRUM-88 QA); only the
registration and zone endpoints, which those files do not exercise, remain here.
"""

import pytest
from fastapi import status
from sqlalchemy import select

from app.features.users.models import User
from app.models.zone import Zone


@pytest.mark.integration
@pytest.mark.api
def test_register_returns_token_and_persists_user(db_client, db, ward_a):
    register_payload = {
        "name": "Jane Citizen",
        "email": "jane.citizen@example.com",
        "password": "strongpassword123",
        "phone": "+919876543219",
        "address": "123 Green Street",
        "zone_id": str(ward_a.id),
        "role": "CITIZEN",
    }

    response = db_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane.citizen@example.com"
    assert data["user"]["role"] == "CITIZEN"
    assert data["user"]["ward_code"] == "W-04"

    db_user = db.scalar(select(User).where(User.email == "jane.citizen@example.com"))
    assert db_user is not None

    # A freshly registered user can immediately use the issued token.
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_response = db_client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK
    assert me_response.json()["email"] == "jane.citizen@example.com"


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


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.parametrize("staff_role", ["ADMIN", "MANAGER", "SYSTEM_ADMIN", "MUNICIPAL_OFFICER"])
def test_self_registration_blocks_staff_roles(db_client, db, ward_a, staff_role):
    register_payload = {
        "name": f"Unauthorized {staff_role}",
        "email": f"unauth.{staff_role.lower()}@example.com",
        "password": "strongpassword123",
        "phone": "+919876549999",
        "address": "123 Security Street",
        "zone_id": str(ward_a.id),
        "role": staff_role,
    }
    response = db_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    res_json = response.json()
    err_msg = res_json["error"]["message"] if "error" in res_json else res_json.get("detail", "")
    assert "Self-registration is not allowed for staff roles" in err_msg


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.parametrize("public_role", ["CITIZEN", "COLLECTOR", "RECYCLER"])
def test_self_registration_allows_public_roles(db_client, db, ward_a, public_role):
    register_payload = {
        "name": f"Public {public_role}",
        "email": f"public.{public_role.lower()}@example.com",
        "password": "strongpassword123",
        "phone": f"+91987654{hash(public_role) % 10000:04d}",
        "address": "123 Public Street",
        "zone_id": str(ward_a.id),
        "role": public_role,
    }
    response = db_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
