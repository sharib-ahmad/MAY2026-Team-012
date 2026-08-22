"""PostgreSQL integration test for the credit-ledger uniqueness invariant.

Verifies the database itself rejects a second Credit row for the same
(pickup_id, reason) identity, protecting against duplicate reward issuance
for the same pickup.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.collection_ops.models import Pickup
from app.features.credits.models import Credit
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import CreditReason, Role, UserStatus


@pytest.mark.integration
def test_duplicate_credit_for_same_pickup_and_reason_reports_unique_violation(db, ward_a):
    citizen = User(
        name="Credit Citizen",
        email="credit.citizen@example.com",
        password_hash="hashed_password",
        phone="+919876500001",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(citizen)

    category = WasteCategory(code="PLASTIC_CR", label="Plastic Waste")
    db.add(category)
    db.flush()

    pickup = Pickup(
        ref_code="COL-CREDIT1",
        citizen_id=citizen.id,
        zone_id=ward_a.id,
        category=category.code,
        estimated_weight=10.0,
    )
    db.add(pickup)
    db.flush()

    db.add(
        Credit(
            user_id=citizen.id,
            pickup_id=pickup.id,
            amount=25.0,
            reason=CreditReason.PICKUP_RECYCLING,
        )
    )
    db.flush()

    db.add(
        Credit(
            user_id=citizen.id,
            pickup_id=pickup.id,
            amount=25.0,
            reason=CreditReason.PICKUP_RECYCLING,
        )
    )

    with pytest.raises(IntegrityError) as captured, db.begin_nested():
        db.flush()

    original = captured.value.orig
    assert original.sqlstate == "23505"
    assert original.diag.constraint_name == "uq_credit_pickup_reason"
