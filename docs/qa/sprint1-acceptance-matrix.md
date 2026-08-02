# Verdeza Sprint 1 Acceptance Matrix

**Official milestone:** Sprint 1 / Milestone 3
**Approved scope:** 11 stories, 57 acceptance criteria
**Matrix size:** 38 consolidated business scenarios + 4 reusable platform gates
**Evidence state:** Expected results are approved first. `Actual Result` remains `Pending execution` and `Result` remains `Not Run` until tested.

## 1. Test-selection strategy

Related acceptance criteria are combined only when one setup and one observable outcome genuinely prove them together. Equivalent invalid inputs use pytest parameterisation rather than copied test functions.

Techniques used: risk-based prioritisation, equivalence partitioning, boundary value analysis, decision tables, state-transition testing, contract testing, object/ward authorisation testing, real PostgreSQL integration, and a small number of cross-feature system journeys.

### Priority

| Priority | Meaning | Exit rule |
|---|---|---|
| P0 | Security, ownership/ward scope, lifecycle, transaction/data integrity, and core business path | Must pass before Sprint 1 sign-off |
| P1 | Important empty-state, presentation, lightweight-content, and explicit-scope evidence | Must be evidenced before submission; automate only where stable value exists |

## 2. Shared platform gates

| ID | Pri | Level | Trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-G01 | P0 | API/Contract | R1 | Authentication default-deny | Call every protected endpoint with no, malformed and expired token. | Public endpoints remain public; protected endpoints return 401 AUTHENTICATION_REQUIRED and perform no state change. | Pending execution | Not Run |
| S1-G02 | P0 | API/Integration | R1 | Role, ownership, route and ward matrix | Exercise allowed and denied actor-role, owner, assigned-route and assigned-ward combinations. | Only authorised combinations succeed; denied access returns 403 or scoped 404 and reveals no foreign data. | Pending execution | Not Run |
| S1-G03 | P0 | API | R4 | Error envelope and leak protection | Trigger representative 401, 403, 404, 409 and 422 responses. | Standard error envelope; X-Request-ID matches body request_id; no SQL, constraints, secrets, tokens, stack traces or driver messages. | Pending execution | Not Run |
| S1-G04 | P0 | PostgreSQL Integration | R2,R3,R4 | Atomic write, audit and database guard | Run one successful write, one mid-operation failure, and one constraint violation. | Success commits business state plus actor/timestamp audit; failure rolls back all partial state; DB constraints remain the final guard. | Pending execution | Not Run |

## 3. Story acceptance matrix

### Story 1.1 — Static Route Schedule Look-up

**Endpoints:** `GET /api/v1/schedules`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-1101 | P0 | API | AC1,AC5 | Valid lookup and normalisation | Existing ward using canonical, spaced and mixed-case codes. | 200; all variants resolve to the same ward and return labelled collection windows. | Pending execution | Not Run |
| S1-1102 | P0 | API | AC2,AC3 | Unknown, missing and blank ward | Parameterise unknown, omitted and whitespace-only ward_code. | Unknown returns 404; omitted/blank returns 422; no ambiguous empty response. | Pending execution | Not Run |
| S1-1103 | P1 | API/Integration | AC4 | Existing ward with no schedule | Valid ward with no published schedule rows. | 200 with explicit unpublished/empty representation, distinct from unknown ward. | Pending execution | Not Run |

### Story 1.2 — Delay Notification for Citizens

**Endpoints:** `GET /api/v1/notifications/me plus route delay/progress writes`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-1201 | P0 | API/Integration | AC1,AC2 | Affected citizen only | Log a delay for one route point; query as affected and unaffected citizens. | Affected citizen sees it; unaffected citizen sees no false positive or foreign notification. | Pending execution | Not Run |
| S1-1202 | P0 | System/Contract | AC3,AC4 | Completion updates in-app notification | Show delay, complete same stop, query again; review documented notification channels. | Notification reflects completion and is not stuck delayed; only in-app delivery is claimed, with SMS/push outside MVP. | Pending execution | Not Run |

### Story 1.3 — Bulk or Institutional Waste Pickup Scheduling

**Endpoints:** `POST/GET /api/v1/bulk-pickups; PATCH /api/v1/bulk-pickups/{id}`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-1301 | P0 | API/Integration | AC1,AC5 | Create and officer queue visibility | Citizen submits valid future date/type/positive volume; add another same ward/date request. | 201 PENDING with ID; both requests persist and appear together in stable ward/date order; no auto-merge. | Pending execution | Not Run |
| S1-1302 | P0 | API Boundary | AC2 | Lead-time boundary | Past, now, just below, exactly at and just above configured lead time. | Below boundary returns 422; exact and above are accepted. | Pending execution | Not Run |
| S1-1303 | P0 | API/Integration | AC3 | Approve/reject pending only | Approve and reject separate pending requests; repeat/conflict a decision. | First valid decision succeeds and citizen view updates; repeated/illegal decision returns 409 without overwrite. | Pending execution | Not Run |
| S1-1304 | P0 | API/Integration | AC4,AC7 | Cancellation and expiry | Citizen cancels eligible own request; separately advance undecided request past scheduled date. | CANCELLED/EXPIRED removed from active queue; later illegal actions rejected. | Pending execution | Not Run |
| S1-1305 | P0 | API/Integration | AC6 | Cross-ward officer denial | Ward-A officer acts on Ward-B request ID. | 403 or scoped 404; no state or audit mutation; no Ward-B data leak. | Pending execution | Not Run |

### Story 1.4 — Manual Route Progress Update

**Endpoints:** `GET /api/v1/routes/me; PATCH /api/v1/route-stops/{id}/progress`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-1401 | P0 | API/Integration | AC1,AC5 | Own route and no-assignment state | Query as workers on different routes and one with no route. | Each sees only own route; unassigned worker gets explicit empty state. | Pending execution | Not Run |
| S1-1402 | P0 | API/Integration | AC2,AC4 | Completion audit and citizen reflection | Assigned worker completes stop; query persisted row and citizen-facing status. | Worker ID/timestamp recorded; status reflected to citizen; state and audit commit together. | Pending execution | Not Run |
| S1-1403 | P0 | Unit/API Boundary | AC3 | Same-working-day correction | Correct within configured IST day, just before day end and just after boundary. | Allowed only within configured server day; later attempt returns 409; history remains append-only. | Pending execution | Not Run |
| S1-1404 | P0 | API/Integration | AC6 | Foreign stop denial | Worker A updates Worker B's stop ID. | 403 or scoped 404; no progress, weight, contamination or audit mutation. | Pending execution | Not Run |

### Story 1.5 — Delay Log Input

**Endpoints:** `POST /api/v1/route-stops/{id}/delays`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-1501 | P0 | API Decision Table | AC1 | Listed reason and OTHER happy paths | Submit listed reason and OTHER with valid 5-200 character note. | Valid submissions persist correct reason; free text is required only as defined. | Pending execution | Not Run |
| S1-1502 | P0 | API Boundary | AC2,AC4 | Explanation and enum validation | OTHER note missing, blank, length 4,5,200,201; invalid enum. | Invalid partitions return 422; lengths 5 and 200 succeed. | Pending execution | Not Run |
| S1-1503 | P0 | API/Integration | AC3,AC5 | Traceability and own-route scope | Assigned worker logs delay; another worker attempts same stop. | Success records worker/timestamp/stop/reason; foreign-route attempt creates no row. | Pending execution | Not Run |

### Story 2.1 — Text-Based Complaint Lodging

**Endpoints:** `POST /api/v1/complaints; GET /api/v1/me/complaints`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-2101 | P0 | API/Integration | AC1,AC5 | Valid complaint, ownership and ward | Citizen submits valid issue type, existing ward_code and 10-500 char description. | 201 with unique public reference; caller owns OPEN complaint; valid ward linked; self-read exposes ward_code, not zone_id. | Pending execution | Not Run |
| S1-2102 | P0 | API Boundary | AC2,AC3 | Required fields and description bounds | Missing/null/blank fields; invalid enum; description 9,10,500,501. | Invalid inputs return field-specific 422 and persist nothing; 10 and 500 accepted. | Pending execution | Not Run |
| S1-2103 | P1 | API/Integration | AC4 | Likely duplicates stay separate | Two citizens submit same issue/ward/date. | Distinct IDs remain; officer filtering groups them for review; no automatic merge. | Pending execution | Not Run |

### Story 2.2 — Centralized Grievance Sorting Data Grid

**Endpoints:** `GET /api/v1/complaints`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-2201 | P0 | API/Integration | AC1 | Controlled filtering and sorting | Seed multiple wards/dates/statuses; request documented sort/filter options. | Only matches returned in stable order; non-officer denied. | Pending execution | Not Run |
| S1-2202 | P0 | Unit/API Boundary | AC2 | Aging threshold | Unresolved cases just below, at and above configured threshold. | Flag follows exact documented boundary; resolved cases not falsely aging. | Pending execution | Not Run |
| S1-2203 | P0 | API/Integration | AC3,AC4 | Empty result and bounded pagination | No-match filter; more than one page; adjacent pages and invalid limits. | 200 empty page for no matches; stable bounded pages without duplicates; invalid pagination rejected. | Pending execution | Not Run |

### Story 2.3 — Form-Driven Resolution Closure

**Endpoints:** `PATCH /api/v1/complaints/{id}/resolution; POST /api/v1/complaints/{id}/reopen`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-2301 | P0 | API/Integration | AC1,AC4 | Resolve with mandatory note and audit | Assigned-ward officer resolves OPEN complaint with valid note. | 200 RESOLVED; note, officer and timestamp stored; audit and citizen self-read agree. | Pending execution | Not Run |
| S1-2302 | P0 | API State/Boundary | AC1 | Note and source-state guards | Blank note; resolve non-OPEN complaint; resolve twice. | Blank returns 422; illegal/repeated transition returns 409; prior resolution not overwritten. | Pending execution | Not Run |
| S1-2303 | P0 | API/Integration | AC2 | Owner reopens inside window | Original complainant reopens RESOLVED complaint just inside window. | 200; stored status returns to OPEN, not REOPENED; history preserved and action audited. | Pending execution | Not Run |
| S1-2304 | P0 | API/Integration | AC3,AC5 | Cross-ward, non-owner and expired reopen denial | Cross-ward resolution; non-owner reopen; owner just outside window. | Denied with contract-defined 403/404/409; complaint and audit unchanged. | Pending execution | Not Run |

### Story 3.1 — Static Sorting Resource Repository

**Endpoints:** `GET /api/v1/sorting-guide; PUT /api/v1/admin/sorting-guide`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-3101 | P1 | API/Frontend Review | AC1,AC3 | Public complete lightweight guide | Call anonymously; inspect page under throttled/low-end profile. | Wet/Dry/Recyclable content complete; core text does not depend on heavy images or login. | Pending execution | Not Run |
| S1-3102 | P0 | API Role Matrix | AC2 | Admin editability | Admin updates guide; every non-admin role attempts update. | Admin change persists and public GET reflects it; others get 403 with no mutation. | Pending execution | Not Run |

### Story 3.2 — Mixed Waste Issue Tagging

**Endpoints:** `POST /api/v1/route-stops/{id}/waste-issues; GET /api/v1/waste-issues`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-3201 | P0 | API/Integration | AC1,AC2 | Routine/Hazardous issue traceability | Assigned worker submits Routine and Hazardous; omit/invalid severity. | Valid rows store stop/date/worker/severity; missing/invalid severity returns 422. | Pending execution | Not Run |
| S1-3202 | P1 | API/Frontend State | AC3,AC4 | Hazardous prominence and clear default state | Create Routine, Hazardous, no-tag and explicitly checked-clean states. | Hazardous visibly prioritised; no-tag remains distinct from checked-clean. | Pending execution | Not Run |
| S1-3203 | P0 | API/Integration | AC5 | Foreign route denial | Worker A tags Worker B's stop. | 403 or scoped 404; no issue or audit row created. | Pending execution | Not Run |

### Story 5.1 — Role-Based User Provisioning

**Endpoints:** `POST/GET /api/v1/admin/users; PATCH /api/v1/admin/users/{id}; auth platform`

| Test ID | Pri | Level | AC trace | Description | Preconditions / Input | Expected Result | Actual Result | Result |
|---|---|---|---|---|---|---|---|---|
| S1-5101 | P0 | API/System Role Matrix | AC1,AC5 | Provision supported roles and approved account model | Admin creates Citizen, Worker, Officer, Recycler; each attempts one allowed/forbidden action; inspect contract. | Canonical roles and IDs returned; permissions enforced server-side; no public register/reset/recovery falsely claimed. | Pending execution | Not Run |
| S1-5102 | P0 | System/Integration | AC2 | Disable revokes login and active session | Create user/token; admin disables; retry login and old token. | Both rejected with 401; status/token version and actor/timestamp audit updated atomically. | Pending execution | Not Run |
| S1-5103 | P0 | API/PostgreSQL | AC3 | Duplicate email and phone | Exact/normalised duplicate email and duplicate phone; race where practical. | 409 public conflict; exactly one account; DB unique constraints remain final guard. | Pending execution | Not Run |
| S1-5104 | P0 | API Security | AC4 | Direct URL and protected-property bypass | Each non-admin calls admin endpoints and injects protected fields. | 403; id/hash/token_version/status/audit fields cannot be mass-assigned. | Pending execution | Not Run |
| S1-5105 | P0 | System/Integration | AC6,AC7 | Role change and re-enable | Change role with old token; disable then re-enable; authenticate again. | Old privileges/session invalidated; new role enforced; re-enabled user obtains new session; append-only audit retained. | Pending execution | Not Run |
| S1-5106 | P0 | API/Integration Invariant | AC8 | Last active admin guard | Attempt disable/demotion with one admin; repeat after adding second admin. | Last-admin action returns 409 and leaves account active; operation succeeds only when another active admin remains. | Pending execution | Not Run |

## 4. Acceptance-criteria coverage audit

| Story | AC count | Consolidated scenarios | Coverage |
|---|---:|---|---|
| 1.1 | 5 | S1-1101, S1-1102, S1-1103 | 5/5 |
| 1.2 | 4 | S1-1201, S1-1202 | 4/4 |
| 1.3 | 7 | S1-1301, S1-1302, S1-1303, S1-1304, S1-1305 | 7/7 |
| 1.4 | 6 | S1-1401, S1-1402, S1-1403, S1-1404 | 6/6 |
| 1.5 | 5 | S1-1501, S1-1502, S1-1503 | 5/5 |
| 2.1 | 5 | S1-2101, S1-2102, S1-2103 | 5/5 |
| 2.2 | 4 | S1-2201, S1-2202, S1-2203 | 4/4 |
| 2.3 | 5 | S1-2301, S1-2302, S1-2303, S1-2304 | 5/5 |
| 3.1 | 3 | S1-3101, S1-3102 | 3/3 |
| 3.2 | 5 | S1-3201, S1-3202, S1-3203 | 5/5 |
| 5.1 | 8 | S1-5101, S1-5102, S1-5103, S1-5104, S1-5105, S1-5106 | 8/8 |
| **Total** | **57** | **38 business scenarios** | **57/57** |

The four platform gates are reusable controls and are not counted as story acceptance criteria.

## 5. Practical automation shape

The 42 matrix rows should become roughly **25–32 focused Python test functions**, because parameterised variants are reported separately without duplicating logic.

| Area | Approximate focused functions |
|---|---:|
| Shared authentication, errors and authorisation helpers | 4–6 |
| Schedules and notifications | 4–5 |
| Bulk pickups | 5–7 |
| Route progress and delays | 6–8 |
| Complaints | 8–10 |
| Sorting guide and waste issues | 4–6 |
| User provisioning | 6–8 |

Test count is not a quality target. Every test must protect an acceptance criterion, security boundary, lifecycle invariant, transaction guarantee, or milestone evidence need.

## 6. System journeys

1. Admin provisions user → user logs in → allowed/denied access is correct → admin disables → old token fails → admin re-enables.
2. Worker sees assigned route → logs delay → affected citizen sees notification → worker completes stop → citizen state updates.
3. Citizen creates complaint → officer lists and resolves with note → citizen sees resolution and reopens within the window.
4. Citizen creates bulk request → officer decides it, or citizen cancels / system expires it → citizen and officer views agree.

## 7. Evidence rule

For each executed row, record exact input, status/body, database effect for writes, pytest node ID or manual evidence reference, and Pass/Fail. A mismatch is a defect; do not rewrite the expected result to match faulty implementation. Overall line coverage alone is not acceptance evidence.
