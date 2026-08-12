from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.features.users.router import get_impact
from app.models.enums import CreditStatus, PickupStatus


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def unique(self):
        return self

    def all(self):
        return self.value


class FakeDatabase:
    def __init__(self, pickups, credits):
        self.pickups = pickups
        self.credits = credits
        self.calls = 0

    def scalars(self, _statement):
        self.calls += 1
        if self.calls == 1:
            return ScalarResult(self.pickups)
        return ScalarResult(self.credits)


def test_get_impact_gamification():
    user_id = uuid4()
    current_user = SimpleNamespace(id=user_id)

    # 1 pickup of 12.5 kg, 22.5 co2, 31.25 credits
    pickup = SimpleNamespace(
        citizen_id=user_id,
        status=PickupStatus.PROCESSED,
        actual_weight=12.5,
        estimated_weight=10.0,
        co2_saved=22.5,
        credits_earned=31.25,
        waste_category=SimpleNamespace(label="Paper"),
        category="DRY",
        completed_at=datetime(2026, 8, 1, 12, tzinfo=UTC),
        created_at=datetime(2026, 8, 1, 12, tzinfo=UTC),
    )

    credit = SimpleNamespace(
        amount=31.25,
        status=CreditStatus.CONFIRMED,
    )

    db = FakeDatabase(pickups=[pickup], credits=[credit])

    res = get_impact(current_user, db)

    # Verify calculated impact metrics
    assert res["total_pickups"] == 1
    assert res["total_kg_diverted"] == 12.5
    assert res["co2_saved_kg"] == 22.5
    assert res["credits_balance"] == 31.25

    # Verify categories and monthly trend aggregation
    assert len(res["by_category"]) == 1
    assert res["by_category"][0]["category"] == "Paper"
    assert res["by_category"][0]["weight_kg"] == 12.5

    # Verify badges logic
    badges = {b["code"]: b["earned"] for b in res["badges"]}
    assert badges["FIRST_PICKUP"] is True
    assert badges["FIVE_PICKUPS"] is False
    assert badges["TEN_PICKUPS"] is False
    assert badges["FIFTY_KG"] is False


def test_get_impact_gamification_multiple_pickups_for_fifty_kg():
    user_id = uuid4()
    current_user = SimpleNamespace(id=user_id)

    # 5 pickups, total weight 60 kg
    pickups = [
        SimpleNamespace(
            citizen_id=user_id,
            status=PickupStatus.PROCESSED,
            actual_weight=12.0,
            estimated_weight=10.0,
            co2_saved=18.0,
            credits_earned=30.0,
            waste_category=SimpleNamespace(label="Paper"),
            category="DRY",
            completed_at=datetime(2026, 8, 1, 12, tzinfo=UTC),
            created_at=datetime(2026, 8, 1, 12, tzinfo=UTC),
        )
        for _ in range(5)
    ]

    credits = [
        SimpleNamespace(
            amount=150.0,
            status=CreditStatus.CONFIRMED,
        )
    ]

    db = FakeDatabase(pickups=pickups, credits=credits)

    res = get_impact(current_user, db)

    assert res["total_pickups"] == 5
    assert res["total_kg_diverted"] == 60.0

    # Verify badges logic - should have FIRST, FIVE, and FIFTY_KG badges
    badges = {b["code"]: b["earned"] for b in res["badges"]}
    assert badges["FIRST_PICKUP"] is True
    assert badges["FIVE_PICKUPS"] is True
    assert badges["TEN_PICKUPS"] is False
    assert badges["FIFTY_KG"] is True
