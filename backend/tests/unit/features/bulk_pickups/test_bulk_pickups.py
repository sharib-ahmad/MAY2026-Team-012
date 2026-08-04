from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.features.bulk_pickups.service import (
    build_tracking_response,
    citizen_requests,
    serialize_request,
)
from app.models.enums import BulkRequestStatus, WasteSeverity


def test_citizen_requests_query():
    user_id = uuid4()
    query = citizen_requests(user_id)
    assert str(query) is not None


def test_serialize_request():
    request = SimpleNamespace(
        id=uuid4(),
        ref_code="BPR-123",
        waste_category=SimpleNamespace(label="Plastic"),
        category="DRY",
        estimated_weight=10.5,
        requested_date=datetime.now(UTC),
        time_slot="Morning (8-11)",
        notes="Pick up plastic",
        status=BulkRequestStatus.ASSIGNED,
        zone=SimpleNamespace(code="W-04", name="Ward Four"),
        assigned_collector=SimpleNamespace(name="John Doe", phone="+919876543210"),
        is_flagged=True,
        flag_severity=WasteSeverity.HAZARDOUS,
        flag_note="Hazardous items present",
        created_at=datetime.now(UTC),
    )

    serialized = serialize_request(request)
    assert serialized.id == request.id
    assert serialized.ref_code == "BPR-123"
    assert serialized.category == "Plastic"
    assert serialized.estimated_weight == 10.5
    assert serialized.status == "ASSIGNED"
    assert serialized.zone_name == "W-04 - Ward Four"
    assert serialized.collector_name == "John Doe"
    assert serialized.collector_phone == "+919876543210"
    assert serialized.is_flagged is True
    assert serialized.flag_severity == "HAZARDOUS"
    assert serialized.flag_note == "Hazardous items present"


def test_build_tracking_response():
    request = SimpleNamespace(
        ref_code="BPR-123",
        status=BulkRequestStatus.PENDING,
        time_slot="Morning (8-11)",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    res = build_tracking_response(request)
    assert res.ref_code == "BPR-123"
    assert res.status == "PENDING"
    assert len(res.timeline) == 1
    assert res.timeline[0].stage == "PENDING"

    # Status not pending
    request.status = BulkRequestStatus.APPROVED
    res2 = build_tracking_response(request)
    assert len(res2.timeline) == 2
    assert res2.timeline[1].stage == "APPROVED"
