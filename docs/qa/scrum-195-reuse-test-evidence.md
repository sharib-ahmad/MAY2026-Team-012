# SCRUM-195 Civic Reuse Exchange QA Evidence

**Feature:** Civic Reuse Exchange
**Related PR:** #87
**Branch under test:** `test/SCRUM-195-reuse-qa`
**Commit tested:** `f8aa790`
**Execution date:** 2026-08-11
**QA state:** Focused execution completed; product corrections and final retest pending

## Execution rule

Expected results were fixed before execution and were not changed to match the current implementation.
Actual Output, Database Effect, Result and Defect below are based only on the recorded pytest run against the disposable PostgreSQL test database.

## Test cases

| ID | Story / Rule | API or component | Input / action | Expected output | Expected database effect | Pytest coverage | Actual output | Database effect | Result | Defect |
|---|---|---|---|---|---|---|---|---|---|---|
| REU-01 | Contract | Runtime route inventory | Inspect application routes | Reuse routes exist and are mounted under `/api/v1/reuse` | None | `tests/api/features/reuse/test_reuse_contract.py::test_runtime_exposes_reuse_routes` | Passed. Runtime route inventory included all expected reuse endpoints. | None | Pass | — |
| REU-02 | Contract | Auth boundaries | Missing Bearer token on citizen and manager endpoints | `401` or `403` without processing state changes | No mutation | `tests/api/features/reuse/test_reuse_contract.py::test_missing_credentials_returns_401_or_403` | Passed. Missing credentials were rejected with the expected safe envelope. | No state-changing handler was entered. | Pass | — |
| REU-03 | Contract | Role enforcement | Citizen hits manager routes; non-citizen hits citizen routes | `403 FORBIDDEN` for cross-role access | None | `tests/api/features/reuse/test_reuse_contract.py::test_citizen_cannot_access_manager_reuse_endpoints` and `test_non_citizen_cannot_access_citizen_reuse_endpoints` | Passed. Cross-role access checks were enforced. | None | Pass | — |
| REU-04 | Donation flow | Donation creation | Create a valid donation with address and image URLs | `200 OK`; donation stored as `PENDING_APPROVAL` | Listing persisted and donor + manager notifications created | `tests/api/features/reuse/test_reuse_donations.py::test_create_donation_persists_pending_listing` | Passed. Donation creation produced a pending listing and notifications. | Listing persisted with pending approval; notifications created for donor and manager. | Pass | — |
| REU-05 | Boundary | Donation validation | Empty title | `422 Unprocessable Entity` | Listing is not created | `tests/api/features/reuse/test_reuse_donations.py::test_empty_title_is_rejected` | Failed. Response was `200 OK` instead of `422`. | A request with an empty title was accepted and persisted. | Fail | REU-QA-01 |
| REU-06 | Boundary | Donation validation | Whitespace-only title | `422 Unprocessable Entity` | Listing is not created | `tests/api/features/reuse/test_reuse_donations.py::test_whitespace_only_title_is_rejected` | Failed. Response was `200 OK` instead of `422`. | A whitespace-only title was accepted and stored after stripping. | Fail | REU-QA-02 |
| REU-07 | Boundary | Donation validation | Over-length title | `422 Unprocessable Entity` | Listing is not created | `tests/api/features/reuse/test_reuse_donations.py::test_overlength_title_is_rejected` | Passed. Excess length was rejected. | No listing created. | Pass | — |
| REU-08 | Donation listing | Own-list filtering | Donor requests `my_donations` | Only current donor's listings are returned | None | `tests/api/features/reuse/test_reuse_donations.py::test_donor_lists_only_own_donations` | Passed. Own-list filtering behaved correctly. | Read-only query; only donor-owned rows returned. | Pass | — |
| REU-09 | Donation lifecycle | Withdrawal | Donor withdraws a pending donation | `200 OK`; listing becomes `WITHDRAWN` | Donation status updates | `tests/api/features/reuse/test_reuse_donations.py::test_pending_donation_can_be_withdrawn` | Passed. Donation was withdrawn successfully. | Listing status updated to `WITHDRAWN`. | Pass | — |
| REU-10 | Authorization | Donation withdrawal | Claimant tries to withdraw another donor's listing | `403 FORBIDDEN` | No mutation | `tests/api/features/reuse/test_reuse_donations.py::test_donor_cannot_withdraw_another_donors_listing` | Passed. Cross-user withdrawal was denied. | No mutation to foreign donation. | Pass | — |
| REU-11 | Manager moderation | Donation approval/rejection | Officer reviews a pending donation | `200 OK`; valid approval or rejection updates status and notes | Listing status and rejection reason persist correctly | `tests/api/features/reuse/test_reuse_manager.py::test_manager_approves_donation` and `test_manager_rejects_donation_with_reason` | Passed. Manager review actions succeeded. | Donation status and reason persisted as expected. | Pass | — |
| REU-12 | Authorization | Manager ward scoping | Unassigned officer reviews a donation | `403 Forbidden` | No listing mutation | `tests/api/features/reuse/test_reuse_manager.py::test_manager_without_ward_cannot_review_donation` | Failed. Response was `200 OK` instead of `403`. | Listing was mutated despite no assigned ward. | Fail | REU-QA-03 |
| REU-13 | Authorization | Manager ward scoping | Officer reviews donation in another ward | `403 Forbidden` | No foreign object mutation | `tests/api/features/reuse/test_reuse_manager.py::test_manager_cannot_review_donation_outside_ward` | Passed. Cross-ward review was denied. | No mutation to foreign-ward listing. | Pass | — |
| REU-14 | Shelf browsing | Public shelf | Browse available listings with search and category filters | Shelf excludes own listings and respects filters | None | `tests/api/features/reuse/test_reuse_shelf_claims.py::test_shelf_excludes_own_listings`, `test_shelf_search_and_category_filter`, and `test_shelf_only_shows_available_listings` | Passed. Shelf returned only eligible listings and respected filters. | Read-only query; shelf data stayed within scope. | Pass | — |
| REU-15 | Claim lifecycle | Claim creation | Citizen claims an available listing | `200 OK`; listing moves to `CLAIM_PENDING` and claim is created | Listing status and claim persist | `tests/api/features/reuse/test_reuse_shelf_claims.py::test_claim_available_item` | Passed. Claim path succeeded and persisted claim data. | Listing advanced to claim pending and claim record was created. | Pass | — |
| REU-16 | Claim lifecycle | Duplicate and self-claim prevention | Duplicate claim or self-claim | `409 Conflict` | No duplicate claim or self-claim record is created | `tests/api/features/reuse/test_reuse_shelf_claims.py::test_cannot_claim_own_listing` and `test_cannot_claim_item_twice` | Passed. Self-claim and duplicate claim attempts were blocked. | No duplicate or self-claim persisted. | Pass | — |
| REU-17 | Claim lifecycle | Non-claimable states | Claiming rejected, pending, or completed listings | `409 Conflict` | No claim created | `tests/api/features/reuse/test_reuse_shelf_claims.py::test_cannot_claim_rejected_listing`, `test_cannot_claim_pending_listing`, and `test_cannot_claim_completed_listing` | Passed. Non-claimable states were rejected. | No claim record created for invalid states. | Pass | — |
| REU-18 | My-claims filtering | Personal claim listing | Filter `my_claims` by status | Only matching claim records are returned | None | `tests/api/features/reuse/test_reuse_shelf_claims.py::test_my_claims_filter_by_status` and `test_my_claims_filter_claim_requested` | Passed. Claim filtering works as expected. | Read-only query only returned matching claims. | Pass | — |
| REU-19 | Isolation | Cross-user claim visibility | User A lists claims for user B | `[]` for foreign claims | None | `tests/api/features/reuse/test_reuse_shelf_claims.py::test_my_claims_cross_user_isolation` | Passed. Foreign claim visibility was blocked. | No foreign claim data leaked. | Pass | — |
| REU-20 | Manager moderation | Claim review | Manager approves or rejects a claim | `200 OK`; status transitions and note persistence work | Claim decision and listing update persist | `tests/api/features/reuse/test_reuse_manager.py::test_manager_approves_claim_completes_listing`, `test_approving_one_claim_rejects_other_pending_claims`, and `test_manager_rejects_claim_and_reopens_listing` | Passed. Manager claim review behaved correctly. | Claim decisions persisted and affected listing state as expected. | Pass | — |
| REU-21 | System journey | End-to-end lifecycle | Donate → approve → claim → approve claim | Full lifecycle completes and notifications deliver | Full transitive state matches expected flow | `tests/api/features/reuse/test_reuse_system.py::test_reuse_system_journey` | Passed. End-to-end donation to completed claim flow completed successfully. | Donation, claim, listing, and notification state were consistent. | Pass | — |

## Initial execution record

```text
Commit tested: f8aa790
Branch: test/SCRUM-195-reuse-qa
Base: main at f8aa790
Host: local development
Python: conda verdeza (3.12+)
PostgreSQL: 16.14
Database: Disposable PostgreSQL database ending in _test
Execution timestamp: 2026-08-11T19:06:00+00:00

Command:
cd backend
export APP_ENV=test
export DATABASE_URL=postgresql+psycopg://verdeza:verdeza@localhost:5433/verdeza_test
python -m pytest --no-cov -q tests/api/features/reuse --tb=line
```

| Metric | Count |
|---|---:|
| Collected | 72 |
| Passed | 69 |
| Failed | 3 |
| Errors | 0 |
| Skipped | 0 |
| Duration | ~17s |
| QA verdict | **Fail — 3 product defects** |

## Defect summary

| Defect | Severity | Priority | Summary | Affected test cases |
|---|---|---|---|---|
| REU-QA-01 | Medium | P1 | Empty donation titles are accepted and persisted despite a required title field | REU-05 |
| REU-QA-02 | Medium | P1 | Whitespace-only donation titles are accepted and stored as empty after stripping | REU-06 |
| REU-QA-03 | High | P0 | Unassigned municipal officer can review donations outside any ward | REU-12 |

## Root cause analysis

- `DonationCreate.title` in `backend/app/features/reuse/schemas.py` only enforces `max_length=80` and does not enforce a minimum length or post-strip non-empty validation, so empty or whitespace-only values pass request validation.
- Manager review logic does not guard when the manager has no managed zones. The current condition checks the list only when it is non-empty, which creates a fail-open path for unassigned officers.

## Passing behavior retained

The following behavior passed and should remain protected during corrective work:

- Reuse route registration and auth boundaries are enforced.
- Donation creation persists valid pending listings and notifications.
- Own-list filtering, search/category filtering, and available-state filtering work as expected.
- Duplicate claim attempts and self-claim attempts are rejected.
- Managers approve and reject donations and claims correctly within scope.
- The end-to-end reuse journey completes successfully for valid workflows.

## Defect handling

Keep this evidence as the initial failure record for PR #87. After the correction reaches `main`:

1. merge current `origin/main` into `test/SCRUM-195-reuse-qa`;
2. rerun the focused reuse suite;
3. update only the Actual Output, Database Effect, Result, and Defect fields;
4. preserve the prior failing evidence for traceability;
5. mark a row as Pass only when status, response body, database effect, and audit/notification state all match the expected result.

## Final status

```text
SCRUM-195 Civic Reuse Exchange QA: FAILED
Focused suite: 69 passed, 3 failed
Full backend regression: Pending corrections
Coverage: Pending full backend execution
QA pull request: May be committed and pushed as Draft
```