import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.features.users.service import (
    TOOL_MAP,
    execute_chatbot_turn,
    get_my_impact_and_credits,
    get_my_pickups,
    get_my_reuse_items,
    get_my_tickets,
)


def test_chatbot_tools_registered():
    assert "get_my_pickups" in TOOL_MAP
    assert "get_my_tickets" in TOOL_MAP
    assert "get_my_impact_and_credits" in TOOL_MAP
    assert "get_my_reuse_items" in TOOL_MAP
    assert "get_waste_rules_and_rates" in TOOL_MAP


def test_get_my_pickups_mocked():
    db = MagicMock()
    mock_pickup = MagicMock()
    mock_pickup.ref_code = "COL-123"
    mock_pickup.category = "WET"
    mock_pickup.status.value = "PENDING"
    mock_pickup.scheduled_date = None
    mock_pickup.estimated_weight = 10.5
    mock_pickup.actual_weight = None
    mock_pickup.credits_earned = 0.0
    mock_pickup.co2_saved = 0.0
    mock_pickup.is_contaminated = False
    mock_pickup.completed_at = None

    db.scalars.return_value.all.return_value = [mock_pickup]

    res = get_my_pickups(db, "fake-user-uuid")
    assert "pickups" in res
    assert len(res["pickups"]) == 1
    assert res["pickups"][0]["ref_code"] == "COL-123"
    assert res["pickups"][0]["category"] == "WET"


def test_get_my_tickets_mocked():
    db = MagicMock()
    mock_ticket = MagicMock()
    mock_ticket.ref_code = "TKT-123"
    mock_ticket.issue_type.value = "MISSED_PICKUP"
    mock_ticket.status.value = "OPEN"
    mock_ticket.description = "Test issue"
    mock_ticket.resolution_notes = None
    mock_ticket.created_at = None

    db.scalars.return_value.all.return_value = [mock_ticket]

    res = get_my_tickets(db, "fake-user-uuid")
    assert "tickets" in res
    assert len(res["tickets"]) == 1
    assert res["tickets"][0]["ref_code"] == "TKT-123"


def test_get_my_impact_and_credits_mocked():
    db = MagicMock()
    db.scalar.side_effect = [15.5, 12.3]  # credits sum, co2 sum

    mock_badge = MagicMock()
    mock_badge.badge.code = "CONSISTENT"
    mock_badge.badge.name = "Consistency Badge"
    mock_badge.badge.category.value = "CONSISTENCY"
    mock_badge.badge.description = "Test badge"
    mock_badge.earned_at = None

    db.scalars.return_value.all.return_value = [mock_badge]

    res = get_my_impact_and_credits(db, "fake-user-uuid")
    assert res["total_credits"] == 15.5
    assert res["total_co2_saved"] == 12.3
    assert len(res["badges_earned"]) == 1
    assert res["badges_earned"][0]["code"] == "CONSISTENT"


def test_get_my_reuse_items_mocked():
    db = MagicMock()

    mock_listing = MagicMock()
    mock_listing.title = "Old Chair"
    mock_listing.category.value = "FURNITURE"
    mock_listing.condition.value = "GOOD"
    mock_listing.status.value = "AVAILABLE"
    mock_listing.rejection_reason = None
    mock_listing.created_at = None

    mock_claim = MagicMock()
    mock_claim.listing.title = "Old Sofa"
    mock_claim.status.value = "PENDING"
    mock_claim.note = "Need it"
    mock_claim.decided_at = None
    mock_claim.created_at = None

    db.scalars.return_value.all.side_effect = [[mock_listing], [mock_claim]]

    res = get_my_reuse_items(db, "fake-user-uuid")
    assert len(res["my_listings"]) == 1
    assert len(res["my_claims"]) == 1
    assert res["my_listings"][0]["title"] == "Old Chair"
    assert res["my_claims"][0]["listing_title"] == "Old Sofa"


def test_chatbot_maintenance_mode_when_api_key_missing(monkeypatch):
    """PR-derived: with no GEMINI_API_KEY configured, EcoBot must reply with a
    maintenance message instead of crashing or attempting a network call."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db = MagicMock()
    current_user = MagicMock(id="fake-user-id")

    result = asyncio.run(
        execute_chatbot_turn(
            message="Show my pickups", history=[], current_user=current_user, db=db
        )
    )

    assert "maintenance" in result["reply"].lower()
    assert result["history"][-1].text == "Maintenance Mode: API key missing."
    db.scalars.assert_not_called()
    db.scalar.assert_not_called()


@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
def test_chatbot_replies_gracefully_when_gemini_returns_error(mock_post, monkeypatch):
    """PR-derived: a non-200 response from Gemini must degrade to a clear
    error reply rather than propagate/crash the request."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    mock_post.return_value = MagicMock(status_code=503, text="Service Unavailable")
    db = MagicMock()
    current_user = MagicMock(id="fake-user-id")

    result = asyncio.run(
        execute_chatbot_turn(
            message="Show my pickups", history=[], current_user=current_user, db=db
        )
    )

    assert result["reply"] == (
        "I encountered an error trying to process your request. Please try again."
    )
    assert result["history"][-1].text == "Error communicating with LLM."
    mock_post.assert_awaited_once()
