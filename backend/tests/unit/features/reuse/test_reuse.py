from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.features.notifications.models import Notification
from app.features.reuse.service import (
    claim_donation,
    create_donation,
    map_frontend_category,
    map_frontend_condition,
    review_claim,
    review_donation,
)
from app.models.enums import ReuseCategory, ReuseClaimStatus, ReuseCondition, ReuseStatus, Role


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def unique(self):
        return self

    def all(self):
        return self.value


class FakeDatabase:
    def __init__(self, listing=None, claim=None):
        self.listing = listing
        self.claim = claim
        self.added = []
        self.commits = 0
        self.flushes = 0

    def scalar(self, statement):
        stmt_str = str(statement).lower()
        if "reuse_claims" in stmt_str:
            return self.claim
        elif "reuse_listings" in stmt_str:
            return self.listing
        elif "users" in stmt_str:
            return uuid4()
        return None

    def scalars(self, statement):
        zone_id = None
        if self.listing:
            zone_id = self.listing.zone_id
        elif self.claim and self.claim.listing:
            zone_id = self.claim.listing.zone_id
        return ScalarResult([zone_id] if zone_id else [])

    def execute(self, statement):
        pass

    def add(self, value):
        self.added.append(value)

    def add_all(self, values):
        self.added.extend(values)

    def commit(self):
        self.commits += 1

    def flush(self):
        self.flushes += 1

    def refresh(self, value):
        pass


@pytest.fixture
def citizen():
    return SimpleNamespace(
        id=uuid4(), name="Jane Citizen", role=Role.CITIZEN, zone_id=uuid4(), address="123 Street"
    )


@pytest.fixture
def manager():
    return SimpleNamespace(id=uuid4(), name="John Manager", role=Role.SYSTEM_ADMIN, zone_id=uuid4())


@pytest.fixture
def listing(citizen):
    return SimpleNamespace(
        id=uuid4(),
        lister_id=citizen.id,
        lister=citizen,
        zone_id=citizen.zone_id,
        title="Old Book",
        category=ReuseCategory.BOOKS,
        condition=ReuseCondition.GOOD,
        status=ReuseStatus.PENDING_APPROVAL,
        address="123 Street",
        images=[],
        claims=[],
    )


def test_map_frontend():
    assert map_frontend_category("clothes") == ReuseCategory.CLOTHING
    assert map_frontend_category("TOYS") == ReuseCategory.HOUSEHOLD
    assert map_frontend_condition("LIKE_NEW") == ReuseCondition.GOOD
    assert map_frontend_condition("needs_repair") == ReuseCondition.FAIR


def test_create_donation(citizen):
    db = FakeDatabase()
    payload = SimpleNamespace(
        title="Table",
        category="FURNITURE",
        description="wooden table",
        condition="GOOD",
        address="321 Lane",
        images=["url1", "url2"],
    )
    res = create_donation(db, citizen, payload)
    assert res.title == "Table"
    assert res.status == ReuseStatus.PENDING_APPROVAL
    assert db.commits == 1
    assert len(db.added) > 0


def test_review_donation_approve(manager, listing):
    db = FakeDatabase(listing=listing)
    payload = SimpleNamespace(status="AVAILABLE", rejection_reason=None)

    res = review_donation(db, manager, listing.id, payload)
    assert res.status == ReuseStatus.AVAILABLE
    assert db.commits == 1


def test_review_donation_reject(manager, listing):
    db = FakeDatabase(listing=listing)
    payload = SimpleNamespace(status="REJECTED", rejection_reason="bad photo")

    res = review_donation(db, manager, listing.id, payload)
    assert res.status == ReuseStatus.REJECTED
    assert res.rejection_reason == "bad photo"
    assert db.commits == 1


def test_review_donation_reject_missing_reason(manager, listing):
    db = FakeDatabase(listing=listing)
    payload = SimpleNamespace(status="REJECTED", rejection_reason="")

    with pytest.raises(HTTPException) as exc:
        review_donation(db, manager, listing.id, payload)
    assert exc.value.status_code == 422


def test_manager_without_ward_cannot_review_donation(listing, monkeypatch):
    unassigned_manager = SimpleNamespace(
        id=uuid4(), name="No Ward Manager", role=Role.SYSTEM_ADMIN, zone_id=None
    )
    db = FakeDatabase(listing=listing)
    payload = SimpleNamespace(status="AVAILABLE", rejection_reason=None)

    monkeypatch.setattr("app.features.reuse.service.get_managed_zone_ids", lambda *_: [])

    with pytest.raises(HTTPException) as exc:
        review_donation(db, unassigned_manager, listing.id, payload)
    assert exc.value.status_code == 403
    assert "supervised wards" in exc.value.detail


def test_claim_donation(citizen, listing):
    listing.status = ReuseStatus.AVAILABLE
    claimant = SimpleNamespace(
        id=uuid4(), name="Claimer Citizen", role=Role.CITIZEN, zone_id=listing.zone_id
    )
    db = FakeDatabase(listing=listing)

    res = claim_donation(db, claimant, listing.id)
    assert res.status == ReuseStatus.CLAIM_PENDING
    assert db.commits == 1


def test_review_claim_approve(manager, listing):
    claimant = SimpleNamespace(
        id=uuid4(), name="Claimer Citizen", role=Role.CITIZEN, zone_id=listing.zone_id
    )
    claim = SimpleNamespace(
        id=uuid4(),
        listing_id=listing.id,
        listing=listing,
        claimant_id=claimant.id,
        claimant=claimant,
        status=ReuseClaimStatus.PENDING,
        decided_by_id=None,
        decided_at=None,
        note=None,
    )
    db = FakeDatabase(claim=claim)
    payload = SimpleNamespace(status="APPROVED", note=None)

    res = review_claim(db, manager, claim.id, payload)
    assert res.status == ReuseClaimStatus.APPROVED
    assert listing.status == ReuseStatus.COMPLETED
    assert db.commits == 1


def test_manager_without_ward_cannot_review_claim(listing, monkeypatch):
    unassigned_manager = SimpleNamespace(
        id=uuid4(), name="No Ward Manager", role=Role.SYSTEM_ADMIN, zone_id=None
    )
    claimant = SimpleNamespace(
        id=uuid4(), name="Claimer Citizen", role=Role.CITIZEN, zone_id=listing.zone_id
    )
    claim = SimpleNamespace(
        id=uuid4(),
        listing_id=listing.id,
        listing=listing,
        claimant_id=claimant.id,
        claimant=claimant,
        status=ReuseClaimStatus.PENDING,
        decided_by_id=None,
        decided_at=None,
        note=None,
    )
    db = FakeDatabase(claim=claim)
    payload = SimpleNamespace(status="APPROVED", note=None)

    monkeypatch.setattr("app.features.reuse.service.get_managed_zone_ids", lambda *_: [])

    with pytest.raises(HTTPException) as exc:
        review_claim(db, unassigned_manager, claim.id, payload)
    assert exc.value.status_code == 403
    assert "supervised wards" in exc.value.detail


# ── Integration tests for Router + Endpoints ──


@pytest.mark.integration
def test_reuse_api_workflow(db_client, db, ward_a):
    # 1. Register Donor
    donor_res = db_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Donor Citizen",
            "email": "donor@verdeza.test",
            "password": "password123",
            "phone": "+919999988881",
            "address": "Donor Lane",
            "zone_id": str(ward_a.id),
            "role": "CITIZEN",
        },
    )
    assert donor_res.status_code == 200
    token_donor = donor_res.json()["access_token"]
    donor_id = donor_res.json()["user"]["id"]

    # 2. Register Claimant
    claimant_res = db_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Claimant Citizen",
            "email": "claimant@verdeza.test",
            "password": "password123",
            "phone": "+919999988882",
            "address": "Claimant Street",
            "zone_id": str(ward_a.id),
            "role": "CITIZEN",
        },
    )
    assert claimant_res.status_code == 200
    token_claimant = claimant_res.json()["access_token"]
    claimant_id = claimant_res.json()["user"]["id"]

    # 3. Register Manager
    manager_res = db_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Super Manager",
            "email": "manager_reuse@verdeza.test",
            "password": "password123",
            "phone": "+919999988883",
            "address": "Office",
            "zone_id": str(ward_a.id),
            "role": "MUNICIPAL_OFFICER",
        },
    )
    assert manager_res.status_code == 200
    token_manager = manager_res.json()["access_token"]

    # 4. Donor submits a donation listing
    headers_donor = {"Authorization": f"Bearer {token_donor}"}
    create_res = db_client.post(
        "/api/v1/reuse/donations",
        headers=headers_donor,
        json={
            "title": "Old Desk",
            "category": "FURNITURE",
            "description": "Solid oak desk",
            "condition": "GOOD",
            "address": "My Backyard",
            "images": ["http://cloudinary.com/pic1", "http://cloudinary.com/pic2"],
        },
    )
    assert create_res.status_code == 200
    listing_id = create_res.json()["id"]
    assert create_res.json()["status"] == "PENDING_APPROVAL"
    assert create_res.json()["address"] == "My Backyard"

    # Verify donor notification was created
    notifs = db.scalars(select(Notification).where(Notification.user_id == donor_id)).all()
    assert any("submitted" in n.body.lower() for n in notifs)

    # 5. Manager reviews pending donations
    headers_manager = {"Authorization": f"Bearer {token_manager}"}
    pending_res = db_client.get("/api/v1/reuse/manager/donations/pending", headers=headers_manager)
    assert pending_res.status_code == 200
    assert any(d["id"] == listing_id for d in pending_res.json())

    # Approve the donation listing
    review_res = db_client.post(
        f"/api/v1/reuse/donations/{listing_id}/review",
        headers=headers_manager,
        json={"status": "AVAILABLE"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "AVAILABLE"

    # Verify donor got approval notification
    notifs_after = db.scalars(select(Notification).where(Notification.user_id == donor_id)).all()
    assert any("approved" in n.body.lower() for n in notifs_after)

    # 6. Claimant views Community Shelf (listing should be present and NOT belong to claimant)
    headers_claimant = {"Authorization": f"Bearer {token_claimant}"}
    shelf_res = db_client.get("/api/v1/reuse/shelf", headers=headers_claimant)
    assert shelf_res.status_code == 200
    assert any(d["id"] == listing_id for d in shelf_res.json())

    # Claimant requests to claim
    claim_res = db_client.post(
        f"/api/v1/reuse/donations/{listing_id}/claim", headers=headers_claimant
    )
    assert claim_res.status_code == 200
    # status translated to CLAIM_REQUESTED for frontend compatibility
    assert claim_res.json()["status"] == "CLAIM_REQUESTED"

    # 7. Manager views pending claims
    pending_claims_res = db_client.get(
        "/api/v1/reuse/manager/claims/pending", headers=headers_manager
    )
    assert pending_claims_res.status_code == 200
    claim_id = pending_claims_res.json()[0]["id"]

    # Manager approves claim
    decide_res = db_client.post(
        f"/api/v1/reuse/claims/{claim_id}/review",
        headers=headers_manager,
        json={"status": "APPROVED", "note": "Safe to pick up."},
    )
    assert decide_res.status_code == 200
    assert decide_res.json()["status"] == "APPROVED"

    # Verify both donor and claimant got notified
    donor_notifs = db.scalars(select(Notification).where(Notification.user_id == donor_id)).all()
    claimant_notifs = db.scalars(
        select(Notification).where(Notification.user_id == claimant_id)
    ).all()
    assert any("claimed" in n.body.lower() for n in donor_notifs)
    assert any("approved" in n.body.lower() for n in claimant_notifs)

    # 8. Manager gets all donations (any status)
    all_res = db_client.get("/api/v1/reuse/manager/donations", headers=headers_manager)
    assert all_res.status_code == 200
    assert any(d["id"] == listing_id for d in all_res.json())

    # 9. Claimant gets their claims
    my_claims_res = db_client.get("/api/v1/reuse/claims/my", headers=headers_claimant)
    assert my_claims_res.status_code == 200
    my_claims = my_claims_res.json()
    assert len(my_claims) > 0
    assert my_claims[0]["id"] == str(claim_id)
    assert my_claims[0]["title"] == "Old Desk"
    assert my_claims[0]["status"] == "APPROVED"
    assert my_claims[0]["note"] == "Safe to pick up."
    assert my_claims[0]["donor_name"] == "Donor Citizen"

    # 10. Claimant marks all notifications as read
    mark_read_res = db_client.patch("/api/v1/user/notifications/read", headers=headers_claimant)
    assert mark_read_res.status_code == 200
    assert mark_read_res.json() == {"status": "ok"}

    # Verify no unread notifications remain for claimant
    unread_notifs = db.scalars(
        select(Notification).where(Notification.user_id == claimant_id, not Notification.is_read)
    ).all()
    assert len(unread_notifs) == 0


def test_empty_title_is_rejected():
    from pydantic import ValidationError

    from app.features.reuse.schemas import DonationCreate

    with pytest.raises(ValidationError):
        DonationCreate(title="", category="FURNITURE", condition="GOOD")

    with pytest.raises(ValidationError):
        DonationCreate(title="   ", category="FURNITURE", condition="GOOD")
