from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.router import track_by_reference


class FakeDatabase:
    def __init__(self, scalars=None, scalar=None):
        self.scalars_values = scalars or []
        self.scalar_value = scalar
        self.added = []
        self.committed = 0

    def scalars(self, statement):
        return FakeScalars(self.scalars_values)

    def scalar(self, statement):
        return self.scalar_value

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed += 1


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values

    def where(self, _):
        return self

    def options(self, _):
        return self


def test_track_by_reference_not_found():
    db = FakeDatabase(scalar=None)

    with pytest.raises(HTTPException, match="Reference code not found"):
        track_by_reference("INVALID-REF", db)


def test_track_by_reference_ticket():
    ticket = SimpleNamespace(
        id=uuid4(),
        ref_code="TCK-001",
        status=SimpleNamespace(value="OPEN"),
        issue_type=SimpleNamespace(value="MISSED_PICKUP"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        raised_by=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        resolved_by=None,
    )
    db = FakeDatabase(scalar=ticket)

    result = track_by_reference("TCK-001", db)

    assert result.ref_code == "TCK-001"
    assert result.entity_type == "TICKET"
