# SCRUM-174 Manager API QA Evidence

**Feature:** Manager dashboard and manager operational actions
**Related PR:** #68
**Branch under test:** `test/SCRUM-174-manager-qa`
**Commit tested (initial):** `d9eff28`
**Execution date (initial):** 2026-08-01
**Commit tested (final retest):** `f4f074c` (merge of `origin/main` HEAD `b9fdbef`, PR #110)
**Execution date (final retest):** 2026-08-12
**QA state:** Final retest complete against current `main`; genuine backend defects remain (see "Final retest" section)

## Execution rule

Expected results were fixed before execution and were not changed to match the current implementation.
Actual Output, Database Effect, Result and Defect below are based only on the recorded pytest run
against the disposable PostgreSQL test database.

## Test cases

| ID | Story / Rule | API or component | Input / action | Expected output | Expected database effect | Pytest coverage | Actual output | Database effect | Result | Defect |
|---|---|---|---|---|---|---|---|---|---|---|
| MGR-01 | Contract | Runtime route inventory | Inspect application routes | Approved complaints, bulk-pickup and notification resource routes exist; duplicate manager write routes are absent | None | `tests/api/features/manager/test_manager_contract.py::test_runtime_uses_the_approved_resource_contract` | Failed. Five approved canonical routes were absent: `GET /api/v1/complaints`, `PATCH /api/v1/complaints/{complaint_id}/resolution`, `GET /api/v1/bulk-pickups`, `PATCH /api/v1/bulk-pickups/{bulk_pickup_id}`, and `GET /api/v1/notifications/me`. The duplicate-route assertion was not reached. | None | Fail | MGR-QA-01 |
| MGR-02 | Instructor Swagger requirement | `api-doc.yaml` | Compare every exposed `/manager/*` route with YAML | Every exposed operation is documented with method, path, story and errors | None | `tests/api/features/manager/test_manager_contract.py::test_every_exposed_manager_route_is_documented_in_swagger` | Failed. Five exposed manager routes were not found in `api-doc.yaml`; the first reported path was `/api/v1/manager/bulk-pickups/{request_id}/assign`. | None | Fail | MGR-QA-02 |
| MGR-03 | S1-G01 | Every manager endpoint | Missing Bearer token | `401 AUTHENTICATION_REQUIRED`, `WWW-Authenticate: Bearer`, safe envelope | No state change | `tests/api/features/manager/test_manager_contract.py::test_every_manager_endpoint_rejects_missing_credentials_with_bearer_challenge` | All six cases returned `401 AUTHENTICATION_REQUIRED` in the safe error envelope, but none included `WWW-Authenticate: Bearer`. | No state-changing handler was entered. | Fail | AUTH-QA-06 / follow-up to #69 |
| MGR-04 | R1 | Manager dashboard | Citizen, Worker, Recycler and Admin tokens | `403 FORBIDDEN` for every non-manager role | None | `tests/api/features/manager/test_manager_contract.py::test_non_manager_roles_cannot_open_manager_dashboard` | All four role cases returned `403 FORBIDDEN` in the safe error envelope. | None | Pass | — |
| MGR-05 | R1, S1-G02 | Ticket and pickup writes | Officer with no assigned wards | `403` or scoped `404` | No ticket or pickup mutation | `tests/api/features/manager/test_manager_authorization.py::test_manager_without_assigned_wards_is_denied_state_changes` | Both cases failed before the response assertion. The ticket changed from `OPEN` to `RESOLVED`, and the pickup changed from `PENDING` to `ASSIGNED`. | Both foreign-ward objects were mutated by a manager with no ward assignment. | Fail | MGR-QA-03 |
| MGR-06 | R1, S1-G02 | Ticket, pickup and worker writes | Ward-A officer targets Ward-B object | `403` or scoped `404` without foreign details | No foreign object mutation | `tests/api/features/manager/test_manager_authorization.py::test_manager_cannot_read_or_mutate_objects_from_another_ward` | All four cases passed: ticket update, pickup assignment, worker update and worker deletion were denied with `403 FORBIDDEN`. | Ticket, pickup and worker records remained unchanged. | Pass | — |
| MGR-07 | Story 2.2 AC1 | Manager dashboard | Own and foreign ward data | `200`; only assigned-ward records and aggregates | None | `tests/api/features/manager/test_manager_dashboard.py::test_dashboard_contains_only_the_managers_assigned_wards` | Dashboard returned `200`, but the response included foreign ward code `W-22`. Later complaint, pickup and worker-scoping assertions were not reached. | Read-only test | Fail | MGR-QA-04 |
| MGR-08 | Story 2.2 AC3 | Manager dashboard | Officer with zero assigned wards | `200` explicit empty scoped dashboard | None | `tests/api/features/manager/test_manager_dashboard.py::test_manager_without_wards_gets_an_empty_scoped_dashboard` | Dashboard returned `200`, but `wards` was not empty and contained Ward `W-22`. Later empty-list and zero-stat assertions were not reached. | Read-only test | Fail | MGR-QA-04 |
| MGR-09 | Story 2.2 AC4 | Dashboard complaints | More than 20 complaints | Bounded list/page with stable newest-first ordering | None | `tests/api/features/manager/test_manager_dashboard.py::test_dashboard_complaints_are_bounded_and_stably_ordered` | Dashboard returned `200` and all 25 complaints instead of at most 20. The ordering assertion was not reached. | Read-only test | Fail | MGR-QA-05 |
| MGR-10 | Story 2.2 AC2 | Dashboard complaints | Just below, at and above aging threshold | Exact `is_aging` boundary; resolved complaint not aging | None | `tests/api/features/manager/test_manager_dashboard.py::test_dashboard_marks_complaints_at_the_aging_threshold` | Dashboard returned `200`, but complaint rows did not contain the required `is_aging` field. Boundary values were therefore not verifiable. | Read-only test | Fail | MGR-QA-06 |
| MGR-11 | R1, R4 | Dashboard notifications | 12 own plus one foreign notification | At most 10 own notifications; no internal fields | None | `tests/api/features/manager/test_manager_dashboard.py::test_dashboard_limits_own_notifications_and_hides_internal_fields` | Passed. Dashboard returned `200`, exactly 10 manager-owned notifications, no foreign notification and no prohibited internal fields. | Read-only test | Pass | — |
| MGR-12 | Story 2.3 AC1, AC4 | Complaint resolution | OPEN complaint plus valid note | `200 RESOLVED`; safe body | Note, resolver, timestamp, audit and citizen notification commit together | `tests/api/features/manager/test_manager_actions.py::test_manager_resolves_open_complaint_with_audit_and_citizen_notification` | Response was `200`; status, note, resolver and resolution timestamp were correct. No matching audit row existed. The citizen-notification assertion occurred after the audit assertion and was not reached. | Complaint resolution persisted, but required audit evidence was absent. | Fail | MGR-QA-07 |
| MGR-13 | Story 2.3 AC1 | Complaint resolution | Empty and whitespace-only note | `422 VALIDATION_ERROR` | Complaint remains OPEN | `tests/api/features/manager/test_manager_actions.py::test_resolution_requires_a_nonblank_note_without_mutation` | Both cases returned `422`, and the complaint remained `OPEN` with no resolution note. The public error code was `ERROR` instead of `VALIDATION_ERROR`. | No complaint mutation | Fail | MGR-QA-08 |
| MGR-14 | Story 2.3 lifecycle | Complaint resolution | `IN_PROGRESS`, `RESOLVED` or `CLOSED` source state | `409 CONFLICT` | Existing state and resolution remain unchanged | `tests/api/features/manager/test_manager_actions.py::test_only_open_complaints_can_be_resolved` | All three cases failed. `IN_PROGRESS` and `CLOSED` complaints were changed to `RESOLVED`. An already `RESOLVED` complaint returned `200` instead of `409`. | Illegal complaint transitions were accepted and persisted. | Fail | MGR-QA-09 |
| MGR-15 | Story 1.3 AC3 | Pickup assignment | `PENDING` request and active same-ward worker | `200 ASSIGNED` | Assignment, decision data, two notifications and audit commit together | `tests/api/features/manager/test_manager_actions.py::test_manager_assigns_pending_pickup_with_notifications_and_audit` | Response was `200`; assignment, collector, decision actor/time and both recipient notifications were correct. No matching audit row existed. | Assignment and notifications persisted, but required audit evidence was absent. | Fail | MGR-QA-07 |
| MGR-16 | R1, R4 | Pickup assignment | Wrong role, disabled worker or wrong ward | `422 VALIDATION_ERROR` | Request remains `PENDING` and unassigned | `tests/api/features/manager/test_manager_actions.py::test_assignment_rejects_an_ineligible_collector_without_mutation` | All three cases returned `422`; each request remained `PENDING` and unassigned. The public error code was `ERROR` instead of `VALIDATION_ERROR`. | No pickup mutation | Fail | MGR-QA-08 |
| MGR-17 | Story 1.3 lifecycle | Pickup assignment | `ASSIGNED`, `REJECTED` or `CANCELLED` request | `409 CONFLICT` | Existing decision is not overwritten | `tests/api/features/manager/test_manager_actions.py::test_only_pending_pickups_can_be_assigned` | All three cases failed. Existing `REJECTED` and `CANCELLED` requests were changed to `ASSIGNED`. An already `ASSIGNED` request returned `200` instead of `409`. | Illegal pickup transitions were accepted and persisted. | Fail | MGR-QA-10 |
| MGR-18 | R3 idempotency | Pickup assignment | Assign twice with different workers | Second request returns `409` | First assignment remains authoritative | `tests/api/features/manager/test_manager_actions.py::test_repeated_assignment_does_not_overwrite_the_first_collector` | The first assignment returned `200`, but the second assignment replaced the first collector. The expected `409` assertion was not reached. | Second request overwrote the authoritative collector. | Fail | MGR-QA-10 |
| MGR-19 | Manager crew support | Worker update | Valid name and phone | `200`; canonical safe response | Contact fields and actor-attributed audit commit together | `tests/api/features/manager/test_manager_actions.py::test_worker_contact_update_is_audited_with_the_manager_as_actor` | Passed. Response was `200`; name and phone were updated; exactly one `CREW_MEMBER_UPDATED` audit row identified the manager as actor. | Worker and audit changes committed together. | Pass | — |
| MGR-20 | R4 | Worker update | Whitespace-only name or phone | `422 VALIDATION_ERROR` | Worker remains unchanged | `tests/api/features/manager/test_manager_actions.py::test_worker_update_rejects_blank_text_without_persistence` | Both cases failed. The blank-name case persisted an empty name. In the blank-phone case, the submitted replacement name `Valid Worker` was persisted before the first unchanged-state assertion failed. Later phone and response assertions were not reached. | Invalid requests mutated the worker record. | Fail | MGR-QA-11 |
| MGR-21 | Canonical status | Worker update | Status `DISABLED` | `200`; public status uses approved vocabulary | Worker becomes `DISABLED` | `tests/api/features/manager/test_manager_actions.py::test_worker_update_uses_the_canonical_disabled_status` | Returned `422` instead of `200`; the approved `DISABLED` vocabulary was rejected. | Expected status change did not occur. | Fail | MGR-QA-12 |
| MGR-22 | R1, R3 | Worker disable | Existing worker token, then disable | `200`; old session returns generic `401` | Status and token version update atomically with audit | `tests/api/features/manager/test_manager_actions.py::test_disabling_worker_increments_token_version_and_revokes_old_session` | Update returned `200` and stored status became `DISABLED`, but `token_version` remained `1` instead of increasing to `2`. The old-session assertion was not reached. | Worker was disabled without the required session-version increment. | Fail | MGR-QA-13 |
| MGR-23 | R3 | Worker delete | Worker has active pickup assignment | `409 CONFLICT` | Worker stays active and undeleted | `tests/api/features/manager/test_manager_actions.py::test_worker_with_active_pickup_assignment_cannot_be_deleted` | The worker received a non-null `deleted_at` despite an active pickup assignment. Status and response assertions were not reached. | Worker was deleted while referenced by an active assignment. | Fail | MGR-QA-14 |
| MGR-24 | R2, R3 | Worker delete | Unassigned worker | `204` | Soft delete, disable, token-version increment and audit commit together | `tests/api/features/manager/test_manager_actions.py::test_unassigned_worker_delete_is_soft_audited_and_revokes_sessions` | Response was `204`; `deleted_at` was set and status became `DISABLED`. `token_version` remained `1` instead of increasing to `2`. Audit assertions were not reached. | Soft deletion persisted without the required session-version increment. | Fail | MGR-QA-13 |
| MGR-25 | S1-G04 | Worker update | Inject required audit failure | Safe server failure | Worker update rolls back completely | `tests/api/features/manager/test_manager_actions.py::test_worker_update_rolls_back_when_required_audit_fails` | The injected audit failure produced a server error, but the submitted name `Must Roll Back` remained persisted. The phone rollback assertion was not reached. | Business data was committed despite required audit failure. | Fail | MGR-QA-15 |
| MGR-26 | Notification isolation | Mark manager notifications read | Three own and one foreign; repeat request | First marks 3, second marks 0 | Only own rows change | `tests/api/features/manager/test_manager_actions.py::test_mark_all_notifications_read_is_recipient_scoped_and_repeat_safe` | Passed. First response was `{"marked_read": 3}`, second was `{"marked_read": 0}`; only the manager's notifications changed. | Own notifications marked read; foreign notification unchanged. | Pass | — |
| MGR-27 | System journey | Manager operations | Dashboard → resolve → assign → cross-ward denial | All same-ward actions succeed; foreign action denied | Ticket, pickup, audits and notifications agree | `tests/api/features/manager/test_manager_system.py::test_manager_dashboard_resolution_and_assignment_journey` | Dashboard, same-ward resolution, pickup assignment and cross-ward denial all passed. The manager's audit-action set was empty, so `COMPLAINT_RESOLVED` was absent; notification verification was not reached. | Ticket and pickup changes persisted, but required manager audit actions were absent. | Fail | MGR-QA-07 |

## Initial execution record

```text
Commit tested: d9eff28
Branch: test/SCRUM-174-manager-qa
Host: ERAMEL
Python: 3.12.3
PostgreSQL: 16.14
Database: Disposable PostgreSQL database ending in _test
Execution timestamp: 2026-08-01T23:17:43+03:00

Command:
python -m pytest --no-cov -q \
  tests/api/features/manager \
  --junitxml="$HOME/qa-evidence/SCRUM174/scrum174-manager-junit.xml" \
  > "$HOME/qa-evidence/SCRUM174/scrum174-manager-pytest.txt" 2>&1

Collected: 47
Passed: 11
Failed: 36
Errors: 0
Skipped: 0
Duration: 50.54 seconds
Pytest exit code: 1

JUnit XML:
$HOME/qa-evidence/SCRUM174/scrum174-manager-junit.xml

Human-readable output:
$HOME/qa-evidence/SCRUM174/scrum174-manager-pytest.txt

Coverage:
Not measured in this focused run because --no-cov was used.

Focused QA decision:
Failed. SCRUM-174 is not accepted for sign-off.

Full backend regression:
Pending product corrections.
```

## Defect summary

| Defect | Severity | Priority | Summary | Affected test cases |
|---|---|---|---|---|
| MGR-QA-01 | High | P0 | Approved canonical resource routes are missing; duplicate manager routes remain unresolved | MGR-01 |
| MGR-QA-02 | High | P0 | Exposed manager API routes are missing from Swagger YAML | MGR-02 |
| AUTH-QA-06 | High | P0 | `401` responses omit the required Bearer challenge header | MGR-03 |
| MGR-QA-03 | Critical | P0 | A manager with no assigned wards can mutate complaints and pickup requests | MGR-05 |
| MGR-QA-04 | High | P0 | Manager dashboard exposes data outside assigned wards and zero-ward scope | MGR-07, MGR-08 |
| MGR-QA-05 | Medium | P0 | Dashboard complaint collection is unbounded | MGR-09 |
| MGR-QA-06 | Medium | P0 | Dashboard complaint rows omit the required aging indicator | MGR-10 |
| MGR-QA-07 | High | P0 | Complaint resolution and pickup assignment do not create required audit records | MGR-12, MGR-15, MGR-27 |
| MGR-QA-08 | Medium | P0 | Validation failures use public code `ERROR` instead of `VALIDATION_ERROR` | MGR-13, MGR-16 |
| MGR-QA-09 | High | P0 | Complaint resolution accepts illegal non-OPEN lifecycle transitions | MGR-14 |
| MGR-QA-10 | High | P0 | Pickup assignment accepts illegal states and allows reassignment overwrite | MGR-17, MGR-18 |
| MGR-QA-11 | High | P0 | Blank worker fields are accepted and persisted | MGR-20 |
| MGR-QA-12 | Medium | P0 | Approved worker status `DISABLED` is rejected | MGR-21 |
| MGR-QA-13 | High | P0 | Worker disable/delete does not increment `token_version` | MGR-22, MGR-24 |
| MGR-QA-14 | High | P0 | Worker with an active pickup assignment can be deleted | MGR-23 |
| MGR-QA-15 | High | P0 | Required audit failure does not roll back worker changes | MGR-25 |

## Passing coverage retained

The following behaviour passed and must remain protected during corrections:

- Non-manager roles cannot open the manager dashboard.
- A manager cannot mutate another ward's complaint, pickup or worker.
- Dashboard notification output is recipient-scoped, bounded and free of prohibited internal fields.
- Valid worker contact updates create an actor-attributed audit row.
- Mark-all-read is recipient-scoped and repeat-safe.

## Defect handling

Create one consolidated SCRUM-174 corrective issue with a separate section for each distinct
`MGR-QA-*` root cause, or link the rows to existing focused defects when the team already tracks
them separately.

For `AUTH-QA-06`, link or reopen GitHub issue #69 when the closed issue claimed to fix the Bearer
challenge requirement. A closed issue is not sufficient evidence when the current focused retest still
fails.

Do not create one issue per failed parameter case. Do not weaken the expected results, add blanket
`xfail`, suppress warnings or skip requirement tests to obtain a green result.

## Final retest (current, supersedes the "Pending" status below)

The initial failure evidence above is preserved as historical.

`origin/main` was merged into `test/SCRUM-174-manager-qa` (clean auto-merge, no conflicts) and the
full manager suite was rerun against the disposable local PostgreSQL test database
(`verdeza_pytest_test`, Docker container `verdeza-postgres`, port 5433). No test code required any
change — every failure reproduces a genuine, currently-reachable backend defect already catalogued
in the "Defect summary" table above.

```text
Branch: test/SCRUM-174-manager-qa
Commit tested: f4f074c (main merged at HEAD b9fdbef, PR #110)
Execution date: 2026-08-12

Focused suite (tests/api/features/manager):
20 passed, 27 failed, 47 collected, 0 errors

Full backend suite:
246 passed, 27 failed, 273 collected, 0 errors
Coverage: 83.78% (gate: >= 80%) -> PASSED

Ruff check (focused + repo-wide): All checks passed
Ruff format --check (focused + repo-wide): all files already formatted
python -m compileall app tests alembic: clean
alembic check: No new upgrade operations detected
```

Compared with the initial execution (11 passed, 36 failed), **9 previously failing cases are now
resolved** by corrective PRs already merged to `main`:

- `MGR-QA-11` — blank worker name/phone is now rejected (`test_worker_update_rejects_blank_text_without_persistence`).
- `MGR-QA-12` — the canonical `DISABLED` worker status is now accepted (`test_worker_update_uses_the_canonical_disabled_status`).
- `MGR-QA-13` — `token_version` now increments on worker disable and on worker delete, revoking old sessions (`test_disabling_worker_increments_token_version_and_revokes_old_session`, `test_unassigned_worker_delete_is_soft_audited_and_revokes_sessions`).
- `MGR-QA-14` — a worker with an active pickup assignment can no longer be deleted (`test_worker_with_active_pickup_assignment_cannot_be_deleted`).
- `MGR-QA-15` — a required audit failure now rolls back the worker update (`test_worker_update_rolls_back_when_required_audit_fails`).
- `MGR-QA-07` (partially) — direct complaint resolution and pickup assignment now write an audit row (`test_manager_resolves_open_complaint_with_audit_and_citizen_notification`, `test_manager_assigns_pending_pickup_with_notifications_and_audit` both now pass).

**10 defect groups remain genuine and unresolved** (verified directly against current
`app/features/manager/router.py`, `app/features/complaints/router.py`,
`app/features/bulk_pickups/router.py`, `app/features/notifications/router.py` and `app/main.py` on
this merge):

- `MGR-QA-01` — the approved resource-oriented routes (`GET /api/v1/complaints`, `PATCH
  /api/v1/complaints/{complaint_id}/resolution`, `GET /api/v1/bulk-pickups`, `PATCH
  /api/v1/bulk-pickups/{bulk_pickup_id}`, `GET /api/v1/notifications/me`) still do not exist; the
  implementation instead exposes role-prefixed action routes
  (`/api/v1/manager/tickets/{id}`, `/api/v1/manager/bulk-pickups/{id}/assign`,
  `/api/v1/user/notifications`).
- `MGR-QA-02` — `api-doc.yaml` is still missing manager routes (e.g.
  `/api/v1/manager/bulk-pickups/{request_id}/assign`); out of scope to fix from this QA branch
  (Part C/D documentation pass handles `api-doc.yaml`).
- Bearer challenge — `WWW-Authenticate: Bearer` is still dropped on every manager-endpoint 401, the
  same shared root cause documented for SCRUM-88 and SCRUM-173 (`app/main.py`'s global
  `StarletteHTTPException` handler does not forward `exc.headers`).
- `MGR-QA-03` — a manager with no assigned wards can still mutate a foreign-ward ticket or pickup
  (`test_manager_without_assigned_wards_is_denied_state_changes`); confirmed live: the ticket status
  changed `OPEN` -> `RESOLVED` and the pickup changed `PENDING` -> `ASSIGNED` for a manager not
  assigned to that ward.
- `MGR-QA-04` — the manager dashboard still returns data outside the manager's assigned wards.
- `MGR-QA-05` — dashboard complaints are still unbounded.
- `MGR-QA-06` — dashboard complaint rows still omit the `is_aging` field.
- `MGR-QA-07` (residual) — the system-journey test still fails: resolving a complaint now writes an
  audit row, but with `action = "COMPLAINT_STATUS_CHANGED"` rather than the more specific
  `"COMPLAINT_RESOLVED"` the test expects, so audit-action granularity for resolution vs. other
  status changes is still missing.
- `MGR-QA-08` — validation failures on resolution notes and ineligible-collector assignment still
  return public code `ERROR` instead of `VALIDATION_ERROR`.
- `MGR-QA-09` — complaint resolution still accepts illegal non-`OPEN` source states (confirmed live:
  `IN_PROGRESS`/`CLOSED` -> `RESOLVED` and an already-`RESOLVED` complaint returns `200` instead of
  `409`).
- `MGR-QA-10` — pickup assignment still accepts illegal source states and a second assignment still
  overwrites the first collector instead of returning `409`.

No expected result was weakened, skipped, xfailed, or suppressed to obtain this result.

```text
SCRUM-174 Manager API QA: FAILED
Focused suite: 20 passed, 27 failed (was 11 passed, 36 failed)
Full backend regression: 246 passed, 27 failed
Coverage: 83.78% (gate passed)
Resolved since initial execution: 5 full defect groups + 1 partial (9 test cases)
Remaining genuine defects: 10 groups across 27 test cases
QA pull request: #79, Draft — must remain Draft until the remaining 10 defect groups are corrected
```
