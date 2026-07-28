"""PostgreSQL integration tests for the shared Zone reference model.

These tests verify persistence, ward-code canonicalisation, and the exact
PostgreSQL SQLSTATE and constraint metadata used by the public integrity-error
classifier.
"""

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
    """Lowercase values and surrounding whitespace are normalised."""

    zone = Zone(
        name="  Spaced Name  ",
        code="  w-09  ",
    )

    db.add(zone)
    db.flush()

    assert zone.code == "W-09"
    assert zone.name == "Spaced Name"


@pytest.mark.integration
@pytest.mark.boundary
@pytest.mark.parametrize(
    "duplicate_code",
    [
        "W-04",
        "w-04",
        " W-04 ",
        "w-04 ",
    ],
)
def test_duplicate_canonical_ward_reports_unique_violation(
    db,
    ward_a,
    duplicate_code,
):
    """Equivalent ward codes must trigger the canonical unique index."""

    db.add(
        Zone(
            name="Duplicate",
            code=duplicate_code,
        )
    )

    with pytest.raises(IntegrityError) as captured, db.begin_nested():
        db.flush()

    original = captured.value.orig

    assert original.sqlstate == "23505"
    assert original.diag.constraint_name == "uq_zones_code_canonical"


@pytest.mark.integration
@pytest.mark.boundary
@pytest.mark.parametrize(
    "blank_code",
    [
        "",
        "   ",
    ],
)
def test_blank_code_reports_named_check_violation(
    db,
    blank_code,
):
    """Blank ward codes must trigger the public not-blank constraint."""

    db.add(
        Zone(
            name="Has name",
            code=blank_code,
        )
    )

    with pytest.raises(IntegrityError) as captured, db.begin_nested():
        db.flush()

    original = captured.value.orig

    assert original.sqlstate == "23514"
    assert original.diag.constraint_name == "ck_zones_code_not_blank"
