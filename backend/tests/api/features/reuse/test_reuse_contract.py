"""Contract, authentication, and role-boundary tests for SCRUM-178 Reuse QA."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status

# ---------------------------------------------------------------------------
# Endpoint categorization
# ---------------------------------------------------------------------------

CITIZEN_ENDPOINTS = [
    "my-donations",
    "my-claims",
    "shelf",
    "create-donation",
    "claim",
    "withdraw",
]
MANAGER_ENDPOINTS = [
    "pending-donations",
    "all-donations",
    "pending-claims",
    "review-donation",
    "review-claim",
]

ALL_ENDPOINTS = CITIZEN_ENDPOINTS + MANAGER_ENDPOINTS


def _request_endpoint(client, paths, endpoint, headers=None):
    """Fire a request against the named endpoint."""
    fake_id = uuid.uuid4()
    dispatch = {
        "my-donations": lambda: client.get(paths.my_donations, headers=headers),
        "my-claims": lambda: client.get(paths.my_claims, headers=headers),
        "shelf": lambda: client.get(paths.shelf, headers=headers),
        "create-donation": lambda: client.post(
            paths.donations,
            headers=headers,
            json={"title": "QA", "category": "BOOKS", "condition": "GOOD"},
        ),
        "claim": lambda: client.post(paths.claim.format(listing_id=fake_id), headers=headers),
        "withdraw": lambda: client.post(paths.withdraw.format(listing_id=fake_id), headers=headers),
        "pending-donations": lambda: client.get(paths.pending_donations, headers=headers),
        "all-donations": lambda: client.get(paths.all_donations, headers=headers),
        "pending-claims": lambda: client.get(paths.pending_claims, headers=headers),
        "review-donation": lambda: client.post(
            paths.review_donation.format(listing_id=fake_id),
            headers=headers,
            json={"status": "AVAILABLE"},
        ),
        "review-claim": lambda: client.post(
            paths.review_claim.format(claim_id=fake_id),
            headers=headers,
            json={"status": "APPROVED"},
        ),
    }
    return dispatch[endpoint]()


# ---------------------------------------------------------------------------
# REU-01 | Route contract — all reuse routes are registered
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_runtime_exposes_reuse_routes(app_test):
    """REU-01 | Reuse routes exist at runtime."""
    registered = {route.path for route in app_test.routes}
    expected = {
        "/api/v1/reuse/donations",
        "/api/v1/reuse/donations/my",
        "/api/v1/reuse/claims/my",
        "/api/v1/reuse/shelf",
        "/api/v1/reuse/donations/{listing_id}/claim",
        "/api/v1/reuse/donations/{listing_id}/withdraw",
        "/api/v1/reuse/manager/donations/pending",
        "/api/v1/reuse/manager/donations",
        "/api/v1/reuse/manager/claims/pending",
        "/api/v1/reuse/donations/{listing_id}/review",
        "/api/v1/reuse/claims/{claim_id}/review",
    }
    missing = expected - registered
    assert not missing, f"Missing reuse routes: {missing}"


# ---------------------------------------------------------------------------
# REU-02 | 401/403 on missing credentials
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
def test_missing_credentials_returns_401_or_403(db_client, reuse_paths, endpoint):
    """REU-02 | Missing credentials → 401 or 403."""
    response = _request_endpoint(db_client, reuse_paths, endpoint)
    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }


# ---------------------------------------------------------------------------
# REU-03 | Role enforcement — citizens on manager routes
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint", MANAGER_ENDPOINTS)
def test_citizen_cannot_access_manager_reuse_endpoints(
    db_client, reuse_paths, claimant, bearer_for, endpoint
):
    """REU-03a | Citizens rejected from manager reuse routes."""
    response = _request_endpoint(db_client, reuse_paths, endpoint, bearer_for(claimant))
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# REU-04 | Role enforcement — non-citizens on citizen routes
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint", CITIZEN_ENDPOINTS)
def test_non_citizen_cannot_access_citizen_reuse_endpoints(
    db_client, reuse_paths, recycler, bearer_for, endpoint
):
    """REU-04 | Non-citizen roles rejected from citizen reuse routes."""
    response = _request_endpoint(db_client, reuse_paths, endpoint, bearer_for(recycler))
    assert response.status_code == status.HTTP_403_FORBIDDEN
