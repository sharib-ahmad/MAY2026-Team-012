import uuid

from app.models.zone import Zone


def test_zone_code_and_name_canonicalisation():
    zone = Zone(code="  w-01  ", name="  Gomti Nagar  ")
    assert zone.code == "W-01"
    assert zone.name == "Gomti Nagar"


def test_list_zones_endpoint(db):
    z1 = Zone(code="W-02", name="Hazratganj")
    z2 = Zone(code="W-01", name="Alambagh")
    db.add_all([z1, z2])
    db.commit()

    from app.features.wards.router import list_zones

    result = list_zones(db)

    assert len(result) >= 2
    names = [r["name"] for r in result]
    assert "W-01 - Alambagh" in names
    assert "W-02 - Hazratganj" in names
    alambagh_idx = names.index("W-01 - Alambagh")
    hazratganj_idx = names.index("W-02 - Hazratganj")
    assert alambagh_idx < hazratganj_idx


def test_list_admin_wards_delegates_to_service(db, monkeypatch):
    from app.features.admin.schemas import WardListResponse
    from app.features.wards import router as wards_router

    admin_user = type("MockUser", (), {"id": uuid.uuid4(), "role": "SYSTEM_ADMIN"})()
    expected_response = WardListResponse(wards=[], total=0)

    monkeypatch.setattr(wards_router, "list_wards", lambda _db: expected_response)
    response = wards_router.list_admin_wards(current_user=admin_user, db=db)

    assert response == expected_response
