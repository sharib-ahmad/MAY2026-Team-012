"""
SCRUM-97 — Regression tests: /dashboard badges must match /impact badges.

The bug: GET /user/dashboard was reading from the unpopulated `user_badges`
DB table, always returning an empty badges list, while GET /user/impact
calculates badges dynamically from completed pickups.

Fix verified: both endpoints now use the same dynamic calculation so their
badge arrays are always identical for the same user data.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.features.users.router import get_dashboard, get_impact
from app.models.enums import CreditStatus, PickupStatus

# ── Minimal DB fake shared by both endpoint functions ────────────────────────


class ScalarResult:
    def __init__(self, items):
        self._items = items

    def unique(self):
        return self

    def all(self):
        return self._items


class FakeDashboardDB:
    """
    Mimics the sequence of DB queries made by get_dashboard:
      1. BulkPickupRequest  (requests)
      2. Credit             (credits)
      3. Pickup             (completed_pickups)
      4. DailyPickupStop    (today_stops)
    """

    def __init__(self, pickups, credits):
        self._pickups = pickups
        self._credits = credits
        self._call = 0

    def scalars(self, _stmt):
        self._call += 1
        if self._call == 1:
            return ScalarResult([])  # bulk pickup requests
        if self._call == 2:
            return ScalarResult(self._credits)
        if self._call == 3:
            return ScalarResult(self._pickups)
        return ScalarResult([])  # today_stops (no daily schedule needed)


class FakeImpactDB:
    """Mimics the two DB queries made by get_impact."""

    def __init__(self, pickups, credits):
        self._pickups = pickups
        self._credits = credits
        self._call = 0

    def scalars(self, _stmt):
        self._call += 1
        if self._call == 1:
            return ScalarResult(self._pickups)
        return ScalarResult(self._credits)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_pickup(weight: float, user_id):
    return SimpleNamespace(
        citizen_id=user_id,
        status=PickupStatus.PROCESSED,
        actual_weight=weight,
        estimated_weight=weight,
        co2_saved=weight * 1.8,
        credits_earned=weight * 2.5,
        waste_category=SimpleNamespace(label="Paper"),
        category="DRY",
        completed_at=datetime(2026, 8, 1, 12, tzinfo=UTC),
        created_at=datetime(2026, 8, 1, 12, tzinfo=UTC),
    )


def _make_credit(amount: float):
    return SimpleNamespace(
        amount=amount,
        status=CreditStatus.CONFIRMED,
        co2_saved=amount * 0.5,
    )


def _make_user(user_id=None, zone_id=None):
    return SimpleNamespace(
        id=user_id or uuid4(),
        zone_id=zone_id or uuid4(),
    )


# ── Tests ────────────────────────────────────────────────────────────────────


class TestCitizenImpactDashboard:
    """SCRUM-97: dashboard badges must match impact badges."""

    def test_dashboard_vs_impact_badges_no_pickups(self):
        """With zero pickups both endpoints must return 4 badges all earned=False."""
        user = _make_user()

        impact = get_impact(user, FakeImpactDB([], []))
        dashboard = get_dashboard(user, FakeDashboardDB([], []))

        imp_badges = {b["code"]: b["earned"] for b in impact["badges"]}
        dash_badges = {b["code"]: b["earned"] for b in dashboard["impact"]["badges"]}

        assert imp_badges == dash_badges, (
            f"Badges mismatch (no pickups):\n  impact={imp_badges}\n  dashboard={dash_badges}"
        )
        assert all(not v for v in dash_badges.values()), "All badges should be unearned"

    def test_dashboard_vs_impact_badges_first_pickup(self):
        """After 1 pickup FIRST_PICKUP badge must be earned=True in both endpoints."""
        user = _make_user()
        pickups = [_make_pickup(5.0, user.id)]
        credits = [_make_credit(12.5)]

        impact = get_impact(user, FakeImpactDB(pickups, credits))
        dashboard = get_dashboard(user, FakeDashboardDB(pickups, credits))

        imp_badges = {b["code"]: b["earned"] for b in impact["badges"]}
        dash_badges = {b["code"]: b["earned"] for b in dashboard["impact"]["badges"]}

        # Core assertion from the Jira ticket
        assert len(dash_badges) == len(imp_badges) == 4
        assert imp_badges == dash_badges, (
            f"Badges mismatch (1 pickup):\n  impact={imp_badges}\n  dashboard={dash_badges}"
        )
        assert dash_badges["FIRST_PICKUP"] is True
        assert dash_badges["FIVE_PICKUPS"] is False

    def test_dashboard_vs_impact_badges_five_pickups_fifty_kg(self):
        """5 pickups × 12 kg each → FIRST, FIVE, FIFTY_KG all earned in both."""
        user = _make_user()
        pickups = [_make_pickup(12.0, user.id) for _ in range(5)]
        credits = [_make_credit(150.0)]

        impact = get_impact(user, FakeImpactDB(pickups, credits))
        dashboard = get_dashboard(user, FakeDashboardDB(pickups, credits))

        imp_badges = {b["code"]: b["earned"] for b in impact["badges"]}
        dash_badges = {b["code"]: b["earned"] for b in dashboard["impact"]["badges"]}

        assert imp_badges == dash_badges, (
            f"Badges mismatch (5 pickups, 60 kg):\n  impact={imp_badges}\n  dashboard={dash_badges}"
        )
        assert dash_badges["FIRST_PICKUP"] is True
        assert dash_badges["FIVE_PICKUPS"] is True
        assert dash_badges["TEN_PICKUPS"] is False
        assert dash_badges["FIFTY_KG"] is True

    def test_dashboard_total_pickups_matches_impact(self):
        """total_pickups in dashboard.impact must equal the value from /impact."""
        user = _make_user()
        pickups = [_make_pickup(3.0, user.id) for _ in range(3)]
        credits = [_make_credit(22.5)]

        impact = get_impact(user, FakeImpactDB(pickups, credits))
        dashboard = get_dashboard(user, FakeDashboardDB(pickups, credits))

        assert dashboard["impact"]["total_pickups"] == impact["total_pickups"] == 3
