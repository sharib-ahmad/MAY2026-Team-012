# tests/unit/features/collection_ops/test_route_optimization.py
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.features.collection_ops import router as collector_module
from app.features.collection_ops.ors_client import ORSClient, decode_polyline
from app.features.collection_ops.router import get_collector_route, optimize_collector_route
from app.models.enums import PickupStatus, PickupStopStatus


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values


class FakeDatabase:
    def __init__(self, scalars=(), scalar=None):
        self.scalars_values, self.scalar_value, self.added, self.commits = (
            list(scalars),
            scalar,
            [],
            0,
        )

    def scalars(self, _statement):
        return ScalarResult(self.scalars_values.pop(0))

    def scalar(self, _statement):
        return self.scalar_value

    def add(self, value):
        self.added.append(value)

    def flush(self):
        pass

    def commit(self):
        self.commits += 1

    def refresh(self, _value):
        pass


def test_decode_polyline():
    # A known polyline: "_p~iF~ps|U_ulLnnqC_mqNvxq`@" decodes to:
    # [[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]]
    polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    decoded = decode_polyline(polyline)
    assert len(decoded) == 3
    assert abs(decoded[0][0] - 38.5) < 1e-4
    assert abs(decoded[0][1] - (-120.2)) < 1e-4
    assert abs(decoded[1][0] - 40.7) < 1e-4
    assert abs(decoded[1][1] - (-120.95)) < 1e-4
    assert abs(decoded[2][0] - 43.252) < 1e-4
    assert abs(decoded[2][1] - (-126.453)) < 1e-4


@patch("urllib.request.urlopen")
def test_ors_client_optimize_route(mock_urlopen):
    # Mock ORS API response
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {
            "routes": [
                {
                    "steps": [
                        {"type": "start"},
                        {"type": "job", "id": "1"},
                        {"type": "job", "id": "0"},
                        {"type": "end"},
                    ],
                    "geometry": "_p~iF~ps|U_ulLnnqC",
                }
            ]
        }
    ).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    client = ORSClient(api_key="test-api-key")
    res = client.optimize_route(
        start_coords=(26.8, 80.9), stop_coords=[(26.9, 81.0), (26.85, 80.95)]
    )

    assert res["optimized_indices"] == [1, 0]
    assert len(res["geometry"]) > 0


def test_get_collector_route_fallback_nearest_neighbor(monkeypatch):
    # Mock _materialize_assigned_bulk_stops to do nothing
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: False)

    # Mock settings to have no ORS key
    monkeypatch.setattr(collector_module, "get_settings", lambda: SimpleNamespace(ORS_API_KEY=""))

    collector = SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.0, longitude=80.0)

    # Create two stops
    # Stop 1 is further away: lat=26.2, lon=80.2
    # Stop 2 is closer: lat=26.1, lon=80.1
    # Both stops are pending. If nearest neighbor works, Stop 2 should be visited first.
    schedule = SimpleNamespace(
        id=uuid4(),
        zone_id=uuid4(),
        zone=SimpleNamespace(code="W-04", name="Ward Four"),
        completed_stops=0,
        completed_at=None,
    )

    stop1 = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-001",
            category="DRY",
            estimated_weight=8,
            time_slot="09:00",
            status=PickupStatus.ASSIGNED,
        ),
        citizen_id=uuid4(),
        citizen=SimpleNamespace(name="Riya Citizen"),
        schedule=schedule,
        schedule_id=schedule.id,
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        latitude=26.2,
        longitude=80.2,
        notes="Far Stop",
        completed_at=None,
        mixed_waste_tags=[],
    )

    stop2 = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-002",
            category="WET",
            estimated_weight=5,
            time_slot="09:00",
            status=PickupStatus.ASSIGNED,
        ),
        citizen_id=uuid4(),
        citizen=SimpleNamespace(name="Amit Citizen"),
        schedule=schedule,
        schedule_id=schedule.id,
        pickup_order=2,
        status=PickupStopStatus.PENDING,
        latitude=26.1,
        longitude=80.1,
        notes="Near Stop",
        completed_at=None,
        mixed_waste_tags=[],
    )

    db = FakeDatabase(scalars=[[stop1, stop2]])
    response = get_collector_route(collector, db)

    # Since Stop 2 is closer to collector (26.0, 80.0), it should be first in optimized order
    assert response.ordered_pickups[0].id == stop2.id
    assert response.ordered_pickups[1].id == stop1.id

    # Geometry should start at collector, then stop2, then stop1, then return to collector
    assert response.route_geometry == [[26.0, 80.0], [26.1, 80.1], [26.2, 80.2], [26.0, 80.0]]


def test_get_collector_route_handles_fewer_than_two_geocoded_points(monkeypatch):
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: False)
    monkeypatch.setattr(collector_module, "get_settings", lambda: SimpleNamespace(ORS_API_KEY=""))
    collector = SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.0, longitude=80.0)

    # 1. Zero stops
    db_empty = FakeDatabase(scalars=[[]])
    res_empty = get_collector_route(collector, db_empty)
    assert res_empty.pickup_count == 0
    assert res_empty.ordered_pickups == []

    # 2. Only 1 stop with geocoded points
    stop1 = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-001",
            category="DRY",
            estimated_weight=8,
            time_slot="09:00",
            status=PickupStatus.ASSIGNED,
        ),
        citizen_id=uuid4(),
        citizen=SimpleNamespace(name="Riya Citizen"),
        schedule=SimpleNamespace(
            id=uuid4(),
            zone_id=uuid4(),
            zone=SimpleNamespace(code="W-04", name="Ward Four"),
            completed_stops=0,
            completed_at=None,
        ),
        schedule_id=uuid4(),
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        latitude=26.2,
        longitude=80.2,
        notes="Single Stop",
        completed_at=None,
        mixed_waste_tags=[],
    )
    db_single = FakeDatabase(scalars=[[stop1]])
    res_single = get_collector_route(collector, db_single)
    assert res_single.pickup_count == 1
    assert len(res_single.ordered_pickups) == 1
    assert res_single.ordered_pickups[0].id == stop1.id


def test_collector_route_response_reports_distance_duration_and_degraded_notice(monkeypatch):
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: False)
    monkeypatch.setattr(collector_module, "get_settings", lambda: SimpleNamespace(ORS_API_KEY=""))

    collector = SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.0, longitude=80.0)

    schedule = SimpleNamespace(
        id=uuid4(),
        zone_id=uuid4(),
        zone=SimpleNamespace(code="W-04", name="Ward Four"),
        completed_stops=0,
        completed_at=None,
    )

    stop1 = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-001",
            category="DRY",
            estimated_weight=8,
            time_slot="09:00",
            status=PickupStatus.ASSIGNED,
        ),
        citizen_id=uuid4(),
        citizen=SimpleNamespace(name="Riya Citizen"),
        schedule=schedule,
        schedule_id=schedule.id,
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        latitude=26.1,
        longitude=80.1,
        notes="Stop 1",
        completed_at=None,
        mixed_waste_tags=[],
    )

    db = FakeDatabase(scalars=[[stop1]])
    response = get_collector_route(collector, db)

    # Verify total_distance_km, estimated_duration_min, is_degraded, and degraded_notice
    # exist and match expectations
    assert hasattr(response, "total_distance_km")
    assert response.total_distance_km > 0
    assert hasattr(response, "estimated_duration_min")
    assert response.estimated_duration_min > 0
    assert hasattr(response, "is_degraded")
    assert response.is_degraded is True
    assert response.degraded_notice is not None
    assert "Road routing service unavailable" in response.degraded_notice


@patch("urllib.request.urlopen")
def test_get_collector_route_below_minimum_points_never_calls_external_provider(mock_urlopen, monkeypatch):
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: False)
    monkeypatch.setattr(collector_module, "get_settings", lambda: SimpleNamespace(ORS_API_KEY="test-api-key"))

    collector = SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.0, longitude=80.0)

    stop1 = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-001",
            category="DRY",
            estimated_weight=8,
            time_slot="09:00",
            status=PickupStatus.ASSIGNED,
        ),
        citizen_id=uuid4(),
        citizen=SimpleNamespace(name="Riya Citizen"),
        schedule=SimpleNamespace(
            id=uuid4(),
            zone_id=uuid4(),
            zone=SimpleNamespace(code="W-04", name="Ward Four"),
            completed_stops=0,
            completed_at=None,
        ),
        schedule_id=uuid4(),
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        latitude=26.1,
        longitude=80.1,
        notes="Stop 1",
        completed_at=None,
        mixed_waste_tags=[],
    )

    db = FakeDatabase(scalars=[[stop1]])
    response = get_collector_route(collector, db)

    assert response.pickup_count == 1
    assert len(response.ordered_pickups) == 1
    mock_urlopen.assert_not_called()


@patch("urllib.request.urlopen")
def test_optimize_collector_route_rejects_fewer_than_two_geocoded_points(mock_urlopen, monkeypatch):
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: False)
    monkeypatch.setattr(collector_module, "get_settings", lambda: SimpleNamespace(ORS_API_KEY="test-api-key"))

    collector = SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.0, longitude=80.0)

    stop1 = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-001",
            category="DRY",
            estimated_weight=8,
            time_slot="09:00",
            status=PickupStatus.ASSIGNED,
        ),
        citizen_id=uuid4(),
        citizen=SimpleNamespace(name="Riya Citizen"),
        schedule=SimpleNamespace(
            id=uuid4(),
            zone_id=uuid4(),
            zone=SimpleNamespace(code="W-04", name="Ward Four"),
            completed_stops=0,
            completed_at=None,
        ),
        schedule_id=uuid4(),
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        latitude=26.1,
        longitude=80.1,
        notes="Stop 1",
        completed_at=None,
        mixed_waste_tags=[],
    )

    db = FakeDatabase(scalars=[[stop1]])
    with pytest.raises(HTTPException) as exc_info:
        optimize_collector_route(collector, db)

    assert exc_info.value.status_code == 400
    assert "At least 2 mapped collection points" in exc_info.value.detail
    mock_urlopen.assert_not_called()

