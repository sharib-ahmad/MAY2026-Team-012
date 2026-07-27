# Requirements Traceability Matrix — Verdeza

**137 acceptance criteria across 25 stories.** Two parts: a **Master RTM** with a
lifecycle status per criterion, and a **Sprint 1 test matrix** with execution
detail. Coverage is reported as criteria-with-a-passing-test.

## Decisions recorded 

- **Vocabulary:** external API `/complaints`; internal table `tickets`.
- **Enums:** `IssueType` and `ComplaintStatus` match the authoritative DBML
  exactly — `MISSED_PICKUP, OVERFLOW, MIXED_WASTE, DELAY, OTHER` and
  `OPEN, IN_PROGRESS, RESOLVED, REOPENED, CLOSED`.
- **Story 5.1:** REMOVED from the Sprint 1 contract. Its ACs are admin user
  provisioning (create/disable/re-enable/lockout), not login. Only `/auth/login`
  ships in Sprint 1, mapped as a **platform authentication requirement**, not a
  5.1 AC. Full 5.1 is Deferred.
- **Mappings:** every Sprint 1 row is taken verbatim from the user-story
  document. Generic auth/security behaviour is labelled a platform requirement,
  never falsely attached to an unrelated AC.

## Status legend
Planned · Implemented · Tested · Deferred

---

## Part A — Master RTM (all 137 criteria)

| Story | AC | Kind (from source) | Component | Endpoint (external) | Type | Sprint | Status |
|---|---|---|---|---|---|---|---|
| 1.1 | AC1 | Happy path | C1.1 | getSchedule (GET /api/v1/schedules) | Positive | 1 | Planned |
| 1.1 | AC2 | Invalid input | C1.1 | getSchedule (GET /api/v1/schedules) | Negative | 1 | Planned |
| 1.1 | AC3 | No selection | C1.1 | getSchedule (GET /api/v1/schedules) | Negative | 1 | Planned |
| 1.1 | AC4 | Empty state | C1.1 | getSchedule (GET /api/v1/schedules) | Negative | 1 | Planned |
| 1.1 | AC5 | Input normalization | C1.1 | getSchedule (GET /api/v1/schedules) | Boundary | 1 | Planned |
| 1.2 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.2 | AC2 | No false positive | — | (later sprint) | Negative | 3–5 | Deferred |
| 1.2 | AC3 | Resolution | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.2 | AC4 | Channel scope, explicit | — | (later sprint) | Security | 3–5 | Deferred |
| 1.3 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.3 | AC2 | Lead time validation | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.3 | AC3 | Status lifecycle | — | (later sprint) | Lifecycle | 3–5 | Deferred |
| 1.3 | AC4 | Cancellation | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.3 | AC5 | Visibility for manual conflict management | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.3 | AC6 | Officer ward authorization | — | (later sprint) | Security | 3–5 | Deferred |
| 1.3 | AC7 | Stale request handling | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.4 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.4 | AC2 | Audit trail | — | (later sprint) | Audit | 3–5 | Deferred |
| 1.4 | AC3 | Correction path | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.4 | AC4 | Citizen-facing reflection | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.4 | AC5 | Empty/no-assignment state | — | (later sprint) | Negative | 3–5 | Deferred |
| 1.4 | AC6 | Authorization | — | (later sprint) | Security | 3–5 | Deferred |
| 1.5 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.5 | AC2 | Validation | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.5 | AC3 | Traceability | — | (later sprint) | Audit | 3–5 | Deferred |
| 1.5 | AC4 | "Other" enforcement | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.5 | AC5 | Own-route scope | — | (later sprint) | Security | 3–5 | Deferred |
| 1.6 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 1.6 | AC2 | Empty state | — | (later sprint) | Negative | 3–5 | Deferred |
| 1.6 | AC3 | Honest labeling | — | (later sprint) | Negative | 3–5 | Deferred |
| 2.1 | AC1 | Happy path | C1.5 | createComplaint (POST /api/v1/complaints) | Positive | 1 | Planned |
| 2.1 | AC2 | Required field validation | C1.5 | createComplaint (POST /api/v1/complaints) | Negative | 1 | Planned |
| 2.1 | AC3 | Description length validation | C1.5 | createComplaint (POST /api/v1/complaints) | Boundary | 1 | Planned |
| 2.1 | AC4 | Duplicate visibility, not auto-merge | C1.5 | createComplaint (POST /api/v1/complaints) | Negative | 1 | Planned |
| 2.1 | AC5 | Ownership and valid ward | C1.5 | createComplaint (POST /api/v1/complaints) | Security | 1 | Planned |
| 2.2 | AC1 | Happy path | C3.1 | listComplaints (GET /api/v1/complaints) | Positive | 1 | Planned |
| 2.2 | AC2 | Aging flag | C3.1 | listComplaints (GET /api/v1/complaints) | Boundary | 1 | Planned |
| 2.2 | AC3 | Empty state | C3.1 | listComplaints (GET /api/v1/complaints) | Negative | 1 | Planned |
| 2.2 | AC4 | Scale handling | C3.1 | listComplaints (GET /api/v1/complaints) | Boundary | 1 | Planned |
| 2.3 | AC1 | Happy path | C3.2 | resolveComplaint / reopenComplaint | Positive | 1 | Planned |
| 2.3 | AC2 | Reopen path | C3.2 | resolveComplaint / reopenComplaint | Lifecycle | 1 | Planned |
| 2.3 | AC3 | Ward authorization | C3.2 | resolveComplaint / reopenComplaint | Security | 1 | Planned |
| 2.3 | AC4 | Audit trail | C3.2 | resolveComplaint / reopenComplaint | Audit | 1 | Planned |
| 2.3 | AC5 | Reopen boundary and ownership | C3.2 | resolveComplaint / reopenComplaint | Boundary | 1 | Planned |
| 3.1 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.1 | AC2 | Editability | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.1 | AC3 | Performance on low-end devices | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.2 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.2 | AC2 | Severity tiering | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.2 | AC3 | Escalation | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.2 | AC4 | Default-state clarity | — | (later sprint) | Positive | 3–5 | Deferred |
| 3.2 | AC5 | Own-route scope | — | (later sprint) | Security | 3–5 | Deferred |
| 4.1 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.1 | AC2 | Concurrency | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.1 | AC3 | Honest labeling | — | (later sprint) | Negative | 3–5 | Deferred |
| 4.1 | AC4 | Empty state | — | (later sprint) | Negative | 3–5 | Deferred |
| 4.2 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.2 | AC2 | Visual distinction | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.2 | AC3 | Mandatory context for unsafe tags | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.2 | AC4 | Note rule for other statuses | — | (later sprint) | Lifecycle | 3–5 | Deferred |
| 4.3 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.3 | AC2 | Auto-release timeout | — | (later sprint) | Positive | 3–5 | Deferred |
| 4.3 | AC3 | Authorization | — | (later sprint) | Security | 3–5 | Deferred |
| 4.3 | AC4 | Transition guard | — | (later sprint) | Positive | 3–5 | Deferred |
| 5.1 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 5.1 | AC2 | Immediate effect of disabling | — | (later sprint) | Lifecycle | 3–5 | Deferred |
| 5.1 | AC3 | Duplicate prevention | — | (later sprint) | Negative | 3–5 | Deferred |
| 5.1 | AC4 | URL-bypass protection | — | (later sprint) | Security | 3–5 | Deferred |
| 5.1 | AC5 | Explicit scope flag | — | (later sprint) | Security | 3–5 | Deferred |
| 5.1 | AC6 | Role change takes effect | — | (later sprint) | Lifecycle | 3–5 | Deferred |
| 5.1 | AC7 | Re-enable | — | (later sprint) | Positive | 3–5 | Deferred |
| 5.1 | AC8 | Lockout guard | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.1 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.1 | AC2 | Photo file-type validation | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.1 | AC3 | Photo size validation | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.1 | AC4 | Required field validation | — | (later sprint) | Negative | 3–5 | Deferred |
| 6.1 | AC5 | Withdrawal before approval | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.2 | AC1 | Approve | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.2 | AC2 | Reject with note | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.2 | AC3 | Rejection without note blocked | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.2 | AC4 | Ward scoping | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.2 | AC5 | Audit trail | — | (later sprint) | Audit | 3–5 | Deferred |
| 6.2 | AC6 | Moderatable state only | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.3 | AC1 | Public browse | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.3 | AC2 | Login required to claim | — | (later sprint) | Negative | 3–5 | Deferred |
| 6.3 | AC3 | Claim | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.3 | AC4 | Cannot claim own listing | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.3 | AC5 | One pending claim per listing | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.3 | AC6 | Claimable state only | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.4 | AC1 | Approve | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.4 | AC2 | Reject with note | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.4 | AC3 | Rejection without note blocked | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.4 | AC4 | Audit trail | — | (later sprint) | Audit | 3–5 | Deferred |
| 6.4 | AC5 | Ward scoping | — | (later sprint) | Positive | 3–5 | Deferred |
| 6.4 | AC6 | Actionable state and first decision wins | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.1 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.1 | AC2 | Save confirmation | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.1 | AC3 | Update existing location | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.1 | AC4 | Location prompt | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.1 | AC5 | No location = excluded from worker map | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.1 | AC6 | Coordinate validation | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.2 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.2 | AC2 | Marker popup detail | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.2 | AC3 | Empty map state | — | (later sprint) | Negative | 3–5 | Deferred |
| 7.2 | AC4 | Own route only | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.3 | AC1 | Happy path — full pipeline | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.3 | AC2 | Minimum point guard | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.3 | AC3 | OSRM fallback | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.3 | AC4 | Loading state | — | (later sprint) | Positive | 3–5 | Deferred |
| 7.3 | AC5 | Upper-bound guard | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC1 | Happy path — deterministic formula | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC2 | Configured factors, no hardcoding | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC3 | Factor bound at completion | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC4 | CO2 travels with the credit | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC5 | Credit subject is the resident | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC6 | Idempotency — no double credit | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC7 | Actual weight required | — | (later sprint) | Negative | 3–5 | Deferred |
| 8.1 | AC8 | Non-positive weight boundary | — | (later sprint) | Boundary | 3–5 | Deferred |
| 8.1 | AC9 | Missing factor | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC10 | Contamination = held, then released once | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC11 | Reversal on un-completion | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.1 | AC12 | Re-completion restores, never duplicates | — | (later sprint) | Negative | 3–5 | Deferred |
| 8.1 | AC13 | Authoritative balance | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC1 | Happy path — deterministic trigger | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC2 | Idempotency — one badge per resident | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC3 | Milestone metric defined | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC4 | Multiple thresholds crossed at once | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC5 | Categories | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC6 | Display metadata | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC7 | No revocation | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.2 | AC8 | Thresholds are configuration | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.3 | AC1 | Happy path | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.3 | AC2 | Validation — enumerated | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.3 | AC3 | Precision and reference set | — | (later sprint) | Positive | 3–5 | Deferred |
| 8.3 | AC4 | Audit trail | — | (later sprint) | Audit | 3–5 | Deferred |
| 8.3 | AC5 | Bounded effect, consistent with holds | — | (later sprint) | Lifecycle | 3–5 | Deferred |
| 8.3 | AC6 | Concurrent edit | — | (later sprint) | Positive | 3–5 | Deferred |
---

## Part B — Sprint 1 test matrix

Sprint 1 stories: **1.1, 2.1, 2.2, 2.3** (19 criteria; Story 5.1 Deferred).
Columns follow: API, inputs, expected output, actual
output, result, pytest evidence. Actual/Result/Defect stay blank until the test
runs. Compound criteria carry multiple test IDs (A/B/C).

| Test ID | Story/AC | API (operationId) | Preconditions | Input | Expected status | Expected body | Actual status | Actual body | Result | Pytest path | Defect |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-010 | 1.1 AC1 | getSchedule | ward WARD-01 has a published schedule | ward_code=WARD-01 | 200 | published=true, windows[] with morning/evening | | | | tests/api/test_schedules.py | |
| TC-011 | 1.1 AC2 | getSchedule | no such ward | ward_code=ZZZ-99 | 404 | RESOURCE_NOT_FOUND envelope | | | | tests/api/test_schedules.py | |
| TC-012 | 1.1 AC3 | getSchedule | — | (ward_code omitted) | 422 | VALIDATION_ERROR envelope | | | | tests/api/test_schedules.py | |
| TC-013 | 1.1 AC4 | getSchedule | ward exists, no schedule published | ward_code=WARD-03 | 200 | published=false, windows=[] | | | | tests/api/test_schedules.py | |
| TC-014 | 1.1 AC5 | getSchedule | ward WARD-01 exists | ward_code=" ward-01 " | 200 | resolves to WARD-01 | | | | tests/api/test_schedules.py | |
| TC-015 | 2.1 AC1 | createComplaint | citizen authed | valid issue_type+ward_code+description | 201 | Complaint with id, ref_code, status=OPEN | | | | tests/api/test_complaints.py | |
| TC-016A | 2.1 AC2 | createComplaint | citizen authed | missing issue_type | 422 | VALIDATION_ERROR | | | | tests/api/test_complaints.py | |
| TC-016B | 2.1 AC2 | createComplaint | citizen authed | missing ward_code | 422 | VALIDATION_ERROR | | | | tests/api/test_complaints.py | |
| TC-016C | 2.1 AC2 | createComplaint | citizen authed | missing description | 422 | VALIDATION_ERROR | | | | tests/api/test_complaints.py | |
| TC-017A | 2.1 AC3 | createComplaint | citizen authed | description length 9 | 422 | below-min rejected | | | | tests/api/test_complaints.py | |
| TC-017B | 2.1 AC3 | createComplaint | citizen authed | description length 501 | 422 | above-max rejected | | | | tests/api/test_complaints.py | |
| TC-017C | 2.1 AC3 | createComplaint | citizen authed | description length 10 and 500 | 201 | exact boundaries accepted | | | | tests/api/test_complaints.py | |
| TC-018A | 2.1 AC5 | createComplaint | citizen authed | ward_code that does not exist | 422 | invalid ward rejected | | | | tests/api/test_complaints.py | |
| TC-018B | 2.1 AC5 | createComplaint | citizen authed | valid body | 201 | complaint bound to caller id | | | | tests/api/test_complaints.py | |
| TC-019 | 2.1 AC4 | listComplaints | 3 same-ward/date/type complaints exist | officer lists | 200 | all 3 present as separate rows (not merged) | | | | tests/api/test_complaints.py | |
| TC-020 | 2.2 AC1 | listComplaints | open complaints exist | officer, sort=ward_code | 200 | sorted list | | | | tests/api/test_complaints.py | |
| TC-021 | 2.2 AC2 | listComplaints | a complaint open > threshold | officer lists | 200 | that item has aging=true | | | | tests/api/test_complaints.py | |
| TC-022 | 2.2 AC3 | listComplaints | no complaints match | filter matches nothing | 200 | items=[], total=0 | | | | tests/api/test_complaints.py | |
| TC-023 | 2.2 AC4 | listComplaints | volume exceeds one page | page=2, page_size=20 | 200 | stable pagination, no dup/skip | | | | tests/api/test_complaints.py | |
| TC-024 | 2.3 AC1 | resolveComplaint | officer, own ward, OPEN complaint | resolution_notes present | 200 | status=RESOLVED, note stored | | | | tests/api/test_complaints.py | |
| TC-024N | 2.3 AC1 | resolveComplaint | officer, own ward, OPEN complaint | resolution_notes missing | 422 | mandatory note enforced | | | | tests/api/test_complaints.py | |
| TC-025 | 2.3 AC2 | reopenComplaint | RESOLVED, original complainant, within window | reopen | 200 | status returns to OPEN | | | | tests/api/test_complaints.py | |
| TC-026 | 2.3 AC3 | resolveComplaint | officer ward A, complaint ward B | resolve | 403 | FORBIDDEN (ward scope) | | | | tests/api/test_complaints.py | |
| TC-027A | 2.3 AC4 | resolveComplaint | resolution occurs | resolve | 200 | audit records actor+timestamp | | | | tests/api/test_complaints.py | |
| TC-027B | Platform auditability | reopenComplaint | reopen occurs | reopen | 200 | audit records REOPENED event (citizen actor+timestamp) | | | | tests/api/test_complaints.py | |
| TC-028A | 2.3 AC5 | reopenComplaint | window expired | reopen | 409 | REOPEN_WINDOW_EXPIRED | | | | tests/api/test_complaints.py | |
| TC-028B | 2.3 AC5 | reopenComplaint | non-complainant, within window | reopen | 403 | ownership enforced | | | | tests/api/test_complaints.py | |

### Platform requirements 

| Test ID | Requirement | operationId | Input | Expected | Pytest path |
|---|---|---|---|---|---|
| TC-P01 | Auth: valid credentials yield token+user+role | login | valid email/password | 200 + token + user.role | tests/api/test_auth.py |
| TC-P02 | Auth: wrong password rejected | login | bad password | 401 AUTHENTICATION_REQUIRED | tests/api/test_auth.py |
| TC-P03 | Liveness independent of DB | health | — | 200, no DB call | tests/test_health.py |
| TC-P04 | Readiness reflects DB availability | ready | DB up / down | 200 / 503 | tests/test_health.py |
| TC-P05 | Error envelope on unknown route | — | GET /nope | 404 envelope + request_id | tests/test_health.py |
| TC-P06 | Citizen sees only own complaints | listMyComplaints | citizen A authed | 200, only A's complaints | tests/api/test_my_complaints.py |
| TC-P07 | Another citizen's complaint never returned | listMyComplaints | A authed, B owns X | X absent from A's list | tests/api/test_my_complaints.py |
| TC-P08 | Resolved complaint appears and is reopenable | listMyComplaints + reopen | A has a RESOLVED complaint | visible, then reopen -> OPEN | tests/api/test_my_complaints.py |
| TC-P09 | My-complaints pagination | listMyComplaints | A has > page_size | stable pages | tests/api/test_my_complaints.py |
| TC-W01 | Whitespace-only description rejected | createComplaint | description = 10 spaces | 422 | tests/api/test_complaints.py |
| TC-W02 | Whitespace-only resolution note rejected | resolveComplaint | resolution_notes = spaces | 422 | tests/api/test_complaints.py |
| TC-W03 | Leading/trailing whitespace trimmed and stored | createComplaint | padded description | 201, stored trimmed | tests/api/test_complaints.py |

## Coverage report format
```
Sprint 1: 19 story criteria (approx 30 parametrised cases) + 5 platform reqs
Master:  137 criteria | Planned 19 | Deferred 118
```
