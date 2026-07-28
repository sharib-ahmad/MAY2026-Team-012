# Requirements Traceability Matrix — Verdeza

**137 acceptance criteria across 25 stories.** Two parts: a **Master RTM** with a
lifecycle status per criterion, and a **Sprint 1 test matrix** with execution
detail for the first contract slice.

## Sprint terminology

The backend stage has exactly two sprints: **Sprint 1 = Milestone 3** and
**Sprint 2 = Milestone 4**. Milestone 5 is the final submission stage, not a
backend sprint. No requirement is deferred out of the project; every story is
committed to Sprint 1 or Sprint 2.

## Allocation

- Stories 1.1–1.5, all of Epic 2, all of Epic 3, Story 5.1 → **Sprint 1**.
- Story 1.6, all of Epics 4, 6, 7, 8 → **Sprint 2**.
- Story 1.6 stays in Epic 1 but is Sprint 2: it depends on Epic 4 material-batch
  and dispatch data.
- Totals: Sprint 1 = 11 stories / 57 ACs; Sprint 2 = 14 stories / 80 ACs.

## Decisions carried from PR 1 and team review

External API `/complaints` + `ward_code`; internal table `tickets`, key
`zone_id`. Enums match the DBML. Reopen returns to `OPEN`. Endpoints below use the
canonical inventory (`endpoint-inventory.md`). Route optimisation is
`POST /api/v1/routes/me/optimize` (OpenRouteService is backend-only).

## Status legend

`Planned — Sprint 1` · `Planned — Sprint 2` · `Implemented` · `Tested`.

---

## Part A — Master RTM (all 137 criteria)

| Story | AC | Kind (from source) | Endpoint (canonical) | Type | Sprint | Status |
|---|---|---|---|---|---|---|
| 1.1 | AC1 | Happy path | GET /api/v1/schedules | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.1 | AC2 | Invalid input | GET /api/v1/schedules | Negative | Sprint 1 | Planned — Sprint 1 |
| 1.1 | AC3 | No selection | GET /api/v1/schedules | Negative | Sprint 1 | Planned — Sprint 1 |
| 1.1 | AC4 | Empty state | GET /api/v1/schedules | Negative | Sprint 1 | Planned — Sprint 1 |
| 1.1 | AC5 | Input normalization | GET /api/v1/schedules | Boundary | Sprint 1 | Planned — Sprint 1 |
| 1.2 | AC1 | Happy path | GET /api/v1/notifications/me | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.2 | AC2 | No false positive | GET /api/v1/notifications/me | Negative | Sprint 1 | Planned — Sprint 1 |
| 1.2 | AC3 | Resolution | GET /api/v1/notifications/me | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.2 | AC4 | Channel scope, explicit | GET /api/v1/notifications/me | Security | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC1 | Happy path | POST /api/v1/bulk-pickups | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC2 | Lead time validation | POST /api/v1/bulk-pickups | Boundary | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC3 | Status lifecycle | PATCH /api/v1/bulk-pickups/{id} | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC4 | Cancellation | PATCH /api/v1/bulk-pickups/{id} | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC5 | Visibility for manual conflict management | GET /api/v1/bulk-pickups | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC6 | Officer ward authorization | PATCH /api/v1/bulk-pickups/{id} | Security | Sprint 1 | Planned — Sprint 1 |
| 1.3 | AC7 | Stale request handling | Internal expiry; GET /api/v1/bulk-pickups | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.4 | AC1 | Happy path | GET /api/v1/routes/me | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.4 | AC2 | Audit trail | PATCH /api/v1/route-stops/{id}/progress | Audit | Sprint 1 | Planned — Sprint 1 |
| 1.4 | AC3 | Correction path | PATCH /api/v1/route-stops/{id}/progress | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.4 | AC4 | Citizen-facing reflection | PATCH /api/v1/route-stops/{id}/progress; GET /api/v1/schedules | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.4 | AC5 | Empty/no-assignment state | GET /api/v1/routes/me | Negative | Sprint 1 | Planned — Sprint 1 |
| 1.4 | AC6 | Authorization | PATCH /api/v1/route-stops/{id}/progress | Security | Sprint 1 | Planned — Sprint 1 |
| 1.5 | AC1 | Happy path | POST /api/v1/route-stops/{id}/delays | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.5 | AC2 | Validation | POST /api/v1/route-stops/{id}/delays | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.5 | AC3 | Traceability | POST /api/v1/route-stops/{id}/delays | Audit | Sprint 1 | Planned — Sprint 1 |
| 1.5 | AC4 | "Other" enforcement | POST /api/v1/route-stops/{id}/delays | Positive | Sprint 1 | Planned — Sprint 1 |
| 1.5 | AC5 | Own-route scope | POST /api/v1/route-stops/{id}/delays | Security | Sprint 1 | Planned — Sprint 1 |
| 1.6 | AC1 | Happy path | GET /api/v1/recycling-summary | Positive | Sprint 2 | Planned — Sprint 2 (dep: Epic 4) |
| 1.6 | AC2 | Empty state | GET /api/v1/recycling-summary | Negative | Sprint 2 | Planned — Sprint 2 (dep: Epic 4) |
| 1.6 | AC3 | Honest labeling | GET /api/v1/recycling-summary | Negative | Sprint 2 | Planned — Sprint 2 (dep: Epic 4) |
| 2.1 | AC1 | Happy path | POST /api/v1/complaints | Positive | Sprint 1 | Planned — Sprint 1 |
| 2.1 | AC2 | Required field validation | POST /api/v1/complaints | Negative | Sprint 1 | Planned — Sprint 1 |
| 2.1 | AC3 | Description length validation | POST /api/v1/complaints | Boundary | Sprint 1 | Planned — Sprint 1 |
| 2.1 | AC4 | Duplicate visibility, not auto-merge | POST /api/v1/complaints | Negative | Sprint 1 | Planned — Sprint 1 |
| 2.1 | AC5 | Ownership and valid ward | POST /api/v1/complaints | Security | Sprint 1 | Planned — Sprint 1 |
| 2.2 | AC1 | Happy path | GET /api/v1/complaints | Positive | Sprint 1 | Planned — Sprint 1 |
| 2.2 | AC2 | Aging flag | GET /api/v1/complaints | Boundary | Sprint 1 | Planned — Sprint 1 |
| 2.2 | AC3 | Empty state | GET /api/v1/complaints | Negative | Sprint 1 | Planned — Sprint 1 |
| 2.2 | AC4 | Scale handling | GET /api/v1/complaints | Boundary | Sprint 1 | Planned — Sprint 1 |
| 2.3 | AC1 | Happy path | PATCH /api/v1/complaints/{id}/resolution | Positive | Sprint 1 | Planned — Sprint 1 |
| 2.3 | AC2 | Reopen path | POST /api/v1/complaints/{id}/reopen | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 2.3 | AC3 | Ward authorization | PATCH /api/v1/complaints/{id}/resolution | Security | Sprint 1 | Planned — Sprint 1 |
| 2.3 | AC4 | Audit trail | PATCH /api/v1/complaints/{id}/resolution | Audit | Sprint 1 | Planned — Sprint 1 |
| 2.3 | AC5 | Reopen boundary and ownership | POST /api/v1/complaints/{id}/reopen | Boundary | Sprint 1 | Planned — Sprint 1 |
| 3.1 | AC1 | Happy path | GET /api/v1/sorting-guide | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.1 | AC2 | Editability | PUT /api/v1/admin/sorting-guide | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.1 | AC3 | Performance on low-end devices | GET /api/v1/sorting-guide | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.2 | AC1 | Happy path | POST /api/v1/route-stops/{id}/waste-issues | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.2 | AC2 | Severity tiering | POST /api/v1/route-stops/{id}/waste-issues | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.2 | AC3 | Escalation | POST /api/v1/route-stops/{id}/waste-issues; GET /api/v1/waste-issues | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.2 | AC4 | Default-state clarity | GET /api/v1/waste-issues | Positive | Sprint 1 | Planned — Sprint 1 |
| 3.2 | AC5 | Own-route scope | POST /api/v1/route-stops/{id}/waste-issues | Security | Sprint 1 | Planned — Sprint 1 |
| 4.1 | AC1 | Happy path | GET /api/v1/material-batches | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.1 | AC2 | Concurrency | POST /api/v1/material-batches/{id}/claim | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.1 | AC3 | Honest labeling | GET /api/v1/material-batches | Negative | Sprint 2 | Planned — Sprint 2 |
| 4.1 | AC4 | Empty state | GET /api/v1/material-batches | Negative | Sprint 2 | Planned — Sprint 2 |
| 4.2 | AC1 | Happy path | PATCH /api/v1/material-batches/{id}/quality | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.2 | AC2 | Visual distinction | PATCH /api/v1/material-batches/{id}/quality | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.2 | AC3 | Mandatory context for unsafe tags | PATCH /api/v1/material-batches/{id}/quality | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.2 | AC4 | Note rule for other statuses | PATCH /api/v1/material-batches/{id}/quality | Lifecycle | Sprint 2 | Planned — Sprint 2 |
| 4.3 | AC1 | Happy path | PATCH /api/v1/material-batches/{id}/pickup-status | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.3 | AC2 | Auto-release timeout | PATCH /api/v1/material-batches/{id}/pickup-status | Positive | Sprint 2 | Planned — Sprint 2 |
| 4.3 | AC3 | Authorization | PATCH /api/v1/material-batches/{id}/pickup-status | Security | Sprint 2 | Planned — Sprint 2 |
| 4.3 | AC4 | Transition guard | PATCH /api/v1/material-batches/{id}/pickup-status | Positive | Sprint 2 | Planned — Sprint 2 |
| 5.1 | AC1 | Happy path | POST /api/v1/admin/users | Positive | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC2 | Immediate effect of disabling | PATCH /api/v1/admin/users/{id} | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC3 | Duplicate prevention | POST /api/v1/admin/users | Negative | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC4 | URL-bypass protection | POST /api/v1/admin/users | Security | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC5 | Explicit scope flag | Documentation / MVP scope declaration | Security | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC6 | Role change takes effect | PATCH /api/v1/admin/users/{id} | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC7 | Re-enable | PATCH /api/v1/admin/users/{id} | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 5.1 | AC8 | Lockout guard | PATCH /api/v1/admin/users/{id} | Lifecycle | Sprint 1 | Planned — Sprint 1 |
| 6.1 | AC1 | Happy path | POST /api/v1/reuse-listings | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.1 | AC2 | Photo file-type validation | POST /api/v1/reuse-listings | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.1 | AC3 | Photo size validation | POST /api/v1/reuse-listings | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.1 | AC4 | Required field validation | POST /api/v1/reuse-listings | Negative | Sprint 2 | Planned — Sprint 2 |
| 6.1 | AC5 | Withdrawal before approval | PATCH /api/v1/reuse-listings/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.2 | AC1 | Approve | PATCH /api/v1/reuse-listings/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.2 | AC2 | Reject with note | PATCH /api/v1/reuse-listings/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.2 | AC3 | Rejection without note blocked | PATCH /api/v1/reuse-listings/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.2 | AC4 | Ward scoping | PATCH /api/v1/reuse-listings/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.2 | AC5 | Audit trail | PATCH /api/v1/reuse-listings/{id} | Audit | Sprint 2 | Planned — Sprint 2 |
| 6.2 | AC6 | Moderatable state only | PATCH /api/v1/reuse-listings/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.3 | AC1 | Public browse | GET /api/v1/reuse-listings | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.3 | AC2 | Login required to claim | POST /api/v1/reuse-listings/{id}/claims | Negative | Sprint 2 | Planned — Sprint 2 |
| 6.3 | AC3 | Claim | POST /api/v1/reuse-listings/{id}/claims | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.3 | AC4 | Cannot claim own listing | POST /api/v1/reuse-listings/{id}/claims | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.3 | AC5 | One pending claim per listing | POST /api/v1/reuse-listings/{id}/claims | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.3 | AC6 | Claimable state only | POST /api/v1/reuse-listings/{id}/claims | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.4 | AC1 | Approve | PATCH /api/v1/reuse-claims/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.4 | AC2 | Reject with note | PATCH /api/v1/reuse-claims/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.4 | AC3 | Rejection without note blocked | PATCH /api/v1/reuse-claims/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.4 | AC4 | Audit trail | PATCH /api/v1/reuse-claims/{id} | Audit | Sprint 2 | Planned — Sprint 2 |
| 6.4 | AC5 | Ward scoping | PATCH /api/v1/reuse-claims/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 6.4 | AC6 | Actionable state and first decision wins | PATCH /api/v1/reuse-claims/{id} | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.1 | AC1 | Happy path | PUT /api/v1/users/me/location | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.1 | AC2 | Save confirmation | PUT /api/v1/users/me/location | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.1 | AC3 | Update existing location | PUT /api/v1/users/me/location | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.1 | AC4 | Location prompt | PUT /api/v1/users/me/location | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.1 | AC5 | No location = excluded from worker map | PUT /api/v1/users/me/location | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.1 | AC6 | Coordinate validation | PUT /api/v1/users/me/location | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.2 | AC1 | Happy path | GET /api/v1/routes/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.2 | AC2 | Marker popup detail | GET /api/v1/routes/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.2 | AC3 | Empty map state | GET /api/v1/routes/me | Negative | Sprint 2 | Planned — Sprint 2 |
| 7.2 | AC4 | Own route only | GET /api/v1/routes/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.3 | AC1 | Happy path — full pipeline | POST /api/v1/routes/me/optimize | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.3 | AC2 | Minimum point guard | POST /api/v1/routes/me/optimize | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.3 | AC3 | OSRM fallback | POST /api/v1/routes/me/optimize | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.3 | AC4 | Loading state | POST /api/v1/routes/me/optimize | Positive | Sprint 2 | Planned — Sprint 2 |
| 7.3 | AC5 | Upper-bound guard | POST /api/v1/routes/me/optimize | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC1 | Happy path — deterministic formula | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC2 | Configured factors, no hardcoding | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC3 | Factor bound at completion | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC4 | CO2 travels with the credit | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC5 | Credit subject is the resident | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC6 | Idempotency — no double credit | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC7 | Actual weight required | Internal pickup-completion credit event; GET /api/v1/credits/me | Negative | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC8 | Non-positive weight boundary | Internal pickup-completion credit event; GET /api/v1/credits/me | Boundary | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC9 | Missing factor | Internal pickup-completion credit event; GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC10 | Contamination = held, then released once | PATCH /api/v1/pickups/{id}/verification; internal event | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC11 | Reversal on un-completion | PATCH /api/v1/route-stops/{id}/progress; internal event | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC12 | Re-completion restores, never duplicates | PATCH /api/v1/route-stops/{id}/progress; internal event | Negative | Sprint 2 | Planned — Sprint 2 |
| 8.1 | AC13 | Authoritative balance | GET /api/v1/credits/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC1 | Happy path — deterministic trigger | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC2 | Idempotency — one badge per resident | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC3 | Milestone metric defined | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC4 | Multiple thresholds crossed at once | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC5 | Categories | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC6 | Display metadata | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC7 | No revocation | Internal badge evaluation; GET /api/v1/badges/me | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.2 | AC8 | Thresholds are configuration | Stored badge config; GET /api/v1/badges | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.3 | AC1 | Happy path | GET + PUT /api/v1/admin/credit-factors/{category} | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.3 | AC2 | Validation — enumerated | PUT /api/v1/admin/credit-factors/{category} | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.3 | AC3 | Precision and reference set | PUT /api/v1/admin/credit-factors/{category} | Positive | Sprint 2 | Planned — Sprint 2 |
| 8.3 | AC4 | Audit trail | PUT /api/v1/admin/credit-factors/{category} | Audit | Sprint 2 | Planned — Sprint 2 |
| 8.3 | AC5 | Bounded effect, consistent with holds | PUT /api/v1/admin/credit-factors/{category} | Lifecycle | Sprint 2 | Planned — Sprint 2 |
| 8.3 | AC6 | Concurrent edit | PUT /api/v1/admin/credit-factors/{category} | Positive | Sprint 2 | Planned — Sprint 2 |
---

## Part B — Initial Sprint 1 contract test matrix

This initial execution matrix covers the stories and endpoints included in the
first API-contract PR (schedule, grievance, auth). The remaining Sprint 1 stories
are planned for Sprint 1 and receive detailed executable test rows through their
feature PRs. **Story 5.1 is not deferred** — it is Planned — Sprint 1. Story 1.6
is Planned — Sprint 2 because it depends on Epic 4 material-batch and dispatch
data.

Cells for actual status, actual output, result, and defect stay blank until the
API is implemented and actually tested — no results are entered in advance.

| Test ID | Story/AC | Requirement (from source) | operationId | Expected | Type | Test path | Result |
|---|---|---|---|---|---|---|---|
| TC-010 | 1.1 AC1 | Happy path: Given a citizen has a valid ward code, when they… | getSchedule | per AC | Positive | tests/api/ |  |
| TC-011 | 1.1 AC2 | Invalid input: Given a citizen enters a ward code that does… | getSchedule | per AC | Negative | tests/api/ |  |
| TC-012 | 1.1 AC3 | No selection: Given a citizen has not entered a ward code,… | getSchedule | per AC | Negative | tests/api/ |  |
| TC-013 | 1.1 AC4 | Empty state: Given a valid ward code has no schedule data… | getSchedule | per AC | Negative | tests/api/ |  |
| TC-014 | 1.1 AC5 | Input normalization: Given a ward code entered with… | getSchedule | per AC | Boundary | tests/api/ |  |
| TC-015 | 2.1 AC1 | Happy path: Given a citizen completes the form with issue… | createComplaint | per AC | Positive | tests/api/ |  |
| TC-016 | 2.1 AC2 | Required field validation: Given any of issue type, ward, or… | createComplaint | per AC | Negative | tests/api/ |  |
| TC-017 | 2.1 AC3 | Description length validation: Given the description is… | createComplaint | per AC | Boundary | tests/api/ |  |
| TC-018 | 2.1 AC4 | Duplicate visibility, not auto-merge: Given multiple… | createComplaint | per AC | Negative | tests/api/ |  |
| TC-019 | 2.1 AC5 | Ownership and valid ward: Given a complaint is submitted,… | createComplaint | per AC | Security | tests/api/ |  |
| TC-020 | 2.2 AC1 | Happy path: Given open complaints exist, when an officer… | listComplaints | per AC | Positive | tests/api/ |  |
| TC-021 | 2.2 AC2 | Aging flag: Given a complaint is unresolved past a threshold… | listComplaints | per AC | Boundary | tests/api/ |  |
| TC-022 | 2.2 AC3 | Empty state: Given no complaints match the filter, when… | listComplaints | per AC | Negative | tests/api/ |  |
| TC-023 | 2.2 AC4 | Scale handling: Given complaint volume exceeds a single… | listComplaints | per AC | Boundary | tests/api/ |  |
| TC-024 | 2.3 AC1 | Happy path: Given an officer updates a complaint to… | resolveComplaint | per AC | Positive | tests/api/ |  |
| TC-025 | 2.3 AC2 | Reopen path: Given a complaint is "Resolved", when the… | reopenComplaint | per AC | Lifecycle | tests/api/ |  |
| TC-026 | 2.3 AC3 | Ward authorization: Given an officer attempts to close a… | resolveComplaint | per AC | Security | tests/api/ |  |
| TC-027 | 2.3 AC4 | Audit trail: Given any status change occurs, when it… | resolveComplaint | per AC | Audit | tests/api/ |  |
| TC-028 | 2.3 AC5 | Reopen boundary and ownership: Given the reopen window has… | reopenComplaint | per AC | Boundary | tests/api/ |  |
### Platform requirements (not story ACs)

These are platform/non-functional requirements and do not map to individual
story acceptance criteria. Rows marked ✓ PR 2 are implemented and tested in the
backend skeleton PR; auth rows arrive with the Sprint 1 auth feature. Results
for unexecuted rows are recorded only after the tests run.

| Test ID | Requirement | operationId | Expected | Test path |
|---|---|---|---|---|
| TC-P01 | Authentication: valid credentials yield a token | login | 200 + token | tests/api/test_auth.py (Sprint 1 feature) |
| TC-P02 | Authentication: wrong password rejected | login | 401 envelope | tests/api/test_auth.py (Sprint 1 feature) |
| TC-P03 | Liveness independent of DB | health | 200, no DB call | tests/test_health.py ✓ |
| TC-P04 | Readiness OK when DB available | ready | 200 ready | tests/test_health.py ✓ |
| TC-P05 | Readiness 503 when DB unavailable | ready | 503 DATABASE_UNAVAILABLE | tests/test_health.py ✓ |
| TC-P06 | Validation error envelope | — | 422 VALIDATION_ERROR, details[] | tests/test_error_handling.py ✓ |
| TC-P07 | Unknown route envelope | — | 404 RESOURCE_NOT_FOUND | tests/test_error_handling.py ✓ |
| TC-P08 | Integrity conflict envelope | — | 409 DUPLICATE_RESOURCE, no SQL leak | tests/test_error_handling.py ✓ |
| TC-P09 | Unexpected error envelope | — | 500 INTERNAL_ERROR, no stack leak | tests/test_error_handling.py ✓ |
| TC-P10 | Request-ID: absent → generated UUID | — | X-Request-ID header + body | tests/test_error_handling.py ✓ |
| TC-P11 | Request-ID: valid incoming echoed | — | same UUID in header + body | tests/test_error_handling.py ✓ |
| TC-P12 | Request-ID: invalid incoming replaced | — | new UUID, not the bad value | tests/test_error_handling.py ✓ |

## Coverage report format
```
Initial story matrix: 19 story criteria (detailed contract slice)
Platform matrix: 12 requirements
  - Platform requirements: 10 (TC-P03..TC-P12) — implemented and tested in the backend skeleton PR
  - Authentication feature requirements: 2 (TC-P01, TC-P02) — arrive with the Sprint 1 auth feature
Record the final test count and coverage from your own local PostgreSQL run.
Master: 137 criteria | Planned — Sprint 1: 57 | Planned — Sprint 2: 80
```
