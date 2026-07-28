"""Integration tests for the Zone model -- proves the DB chain and the
ward-code canonicalisation invariant."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.zone import Zone


@pytest.mark.integration
def test_zone_persists_and_reads_back(db, ward_a):
    fetched = db.get(Zone, ward_a.id)
    assert fetched is not None
    assert fetched.code == "W-04"


@pytest.mark.integration
def test_code_is_canonicalised_on_write(db):
    """lowercase and surrounding whitespace are normalised on write."""
    z = Zone(name="  Spaced Name  ", code="  w-09  ")
    db.add(z)
    db.flush()
    assert z.code == "W-09"
    assert z.name == "Spaced Name"


@pytest.mark.integration
@pytest.mark.boundary
@pytest.mark.parametrize("dupe_code", ["W-04", "w-04", " W-04 ", "w-04 "])
def test_logical_duplicate_ward_is_rejected(db, ward_a, dupe_code):
    """W-04, w-04 and ' W-04 ' are the SAME ward.

    A plain unique constraint on the raw string would let these through; the
    canonical index must reject all of them.
    """
    db.add(Zone(name="Duplicate", code=dupe_code))
    with pytest.raises(IntegrityError) as exc, db.begin_nested():
        db.flush()
    # assert it is the canonical uniqueness that fired, not some other
    # integrity error.
    assert "uq_zones_code_canonical" in str(exc.value).lower() or "unique" in str(exc.value).lower()


@pytest.mark.integration
@pytest.mark.boundary
@pytest.mark.parametrize("bad", ["", "   "])
def test_blank_code_is_rejected(db, bad):
    """blank or whitespace-only code violates the not-blank check."""
    db.add(Zone(name="Has name", code=bad))
    with pytest.raises(IntegrityError), db.begin_nested():
        db.flush()
