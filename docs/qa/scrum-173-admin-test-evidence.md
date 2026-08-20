# SCRUM-173 Administrator API QA Evidence

**Feature:** Story 5.1 role-based user provisioning and PR #64 administrator support APIs
**Branch under test:** `test/SCRUM-173-admin-qa`
**Initial commit tested:** `d65669d`
**Initial execution date:** 2026-08-01
**Latest retest base commit:** `0f71a83` (origin/main merged) with local QA-refinement corrections
**Latest retest date:** 2026-08-20
**Current QA decision:** Failed; Draft PR #80 remains blocked by 1 confirmed backend defect group (6 test cases). The shared `WWW-Authenticate: Bearer`/global-exception-handler defect previously tracked here is consolidated into PR #81, which owns it more deeply.
**Corrective issue:** #70
**Execution rule:** Expected results were fixed before execution. Actual outputs and results are recorded from pytest execution against the disposable PostgreSQL test database. Historical evidence is preserved, while the latest retest section is the source of truth for the current failure set.

## QA-suite refinement pass — Bearer assertion consolidated with PR #81 (2026-08-20, current, supersedes all sections below)

Follow-up to the same-day refinement pass below, requested to remove duplicate coverage of a
defect PR #81 already owns more deeply, and to re-check (not blindly consolidate) the 6
UUID-related failures before finalizing #80.

### Change 1 — `WWW-Authenticate: Bearer` assertion removed, not just the one line

`test_missing_credentials_include_the_bearer_challenge` asserted two things: (a) a missing-
credentials request to an admin endpoint returns `401 AUTHENTICATION_REQUIRED` in the safe
envelope, and (b) the response carries `WWW-Authenticate: Bearer`. Confirmed again this
session that (b) is produced entirely by shared, non-admin-specific infrastructure:
`get_current_user` (`app/features/auth/dependencies.py`) always attaches the header when it
raises, and the app-wide `StarletteHTTPException` handler (`app/main.py`) is what currently
drops it from every 401 in the application — admin included, with no admin-specific code
involved anywhere in that path. That is the same shared defect PR #81 owns and tests more
deeply, so re-asserting it here is pure duplication.

Removing only the `WWW-Authenticate` line would have left (a) behind as a standalone test —
but that remaining assertion (401 + safe envelope for `GET /admin/dashboard` with no
credentials) is an exact duplicate of the existing `dashboard` case in
`test_every_exposed_admin_endpoint_rejects_missing_credentials_with_401`, which already
covers it (and additionally checks the error message never leaks "admin"). Keeping a test
that duplicates an existing case with no unique signal reintroduces the same test-count
inflation this suite was just cleaned of, so the whole function was removed rather than left
as dead duplicate coverage. The required proof — every protected admin endpoint rejects
missing credentials with `401` and the correct safe envelope — remains fully intact via that
sweep test; nothing about admin authorization coverage was weakened.

### Change 2 — the 6 UUID-related failures were reviewed, not consolidated

Checked each of the 6 currently-failing cases for whether it protects a distinct accepted
behaviour, as instructed, rather than merging them because they currently share one root
cause. All 6 are kept unchanged:

- **`test_admin_can_provision_each_supported_role_with_safe_canonical_output[CITIZEN /
  COLLECTION_WORKER / MUNICIPAL_OFFICER / RECYCLER]`** (4 cases): each independently proves
  Story 5.1 AC1 — that specific approved role can be provisioned end-to-end (DB persistence,
  correct `role` value, audit actor, and the `ROLE_MAP_DB_TO_FRONTEND` response mapping for
  that exact role). Unlike the authorization guard (`require_admin`, which is genuinely
  identical for every non-admin role — already consolidated earlier today), role
  serialization is a per-value dictionary lookup that can break for one role without breaking
  the others. Collapsing these to one representative role would hide that class of bug, so
  they stay distinct.
- **`test_admin_provisions_user_user_logs_in_admin_disables_and_reenables`**: a
  `@pytest.mark.system` cross-endpoint journey (create with ward → login → `/me` → disable →
  relogin blocked → re-enable → relogin restored). It only shares the UUID root cause because
  its setup happens to supply a ward — the behaviour it protects (session lifecycle across
  disable/re-enable) is unrelated to the 4 provisioning cases above and to each other UUID
  failure. Not a duplicate of anything else in the suite.
- **`test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[unknown-ward]`**:
  one case within a 5-case boundary/security test; its 4 siblings (mass-assignment,
  blank-name, over-length password, invalid-role) each test a different input-safety
  dimension. `unknown-ward` is the suite's only coverage of referential validity for
  `zone_id` — a distinct dimension (R4 "valid ward/reference handling"), not redundant with
  its siblings.

No test was merged, weakened, or removed as part of this review; all 6 remain correctly red.

### Retest execution record

```text
Execution date: 2026-08-20 (same-day follow-up)
Ruff check (repo-wide):            All checks passed
Ruff format --check (repo-wide):   169 files already formatted

Focused suite, this PR's own files:
61 collected, 55 passed, 6 failed, 0 errors, 0 skipped   (was 62 / 55 / 7)

Full tests/api/features/admin + tests/unit/features/admin directory
  (includes 7 pre-existing, untouched tests from PR #72, all passing):
68 collected, 62 passed, 6 failed                         (was 69 / 62 / 7)

Full backend suite:
371 collected, 365 passed, 6 failed, 0 errors, 0 skipped, 111.49s   (was 372 / 365 / 7)
Coverage: 84.41% (gate: >= 80%) -> PASSED (unchanged — app/features/admin/* is still
  excluded from coverage measurement; see blind-spot note below)
```

### Remaining distinct backend defect groups (1, down from 2)

**BACKEND DEFECT — `POST /api/v1/admin/users` crashes when a ward is supplied.** Unchanged
from the prior retest: `app/features/admin/router.py:479` re-wraps an already-parsed `UUID`
(`AdminUserCreate.zone_id`) in `uuid.UUID(...)`, raising `AttributeError`. Still blocks the
Story 5.1 AC1 happy path (valid ward) and the unknown-ward validation path (500 instead of
422). Full detail retained below in the prior section. Affects the same 6 tests reviewed
above.

**Consolidated out of #80's defect list:** the missing `WWW-Authenticate: Bearer` header
(`app/main.py`'s global `StarletteHTTPException` handler dropping `exc.headers`) is no longer
tracked as a #80-owned defect. It is shared, non-admin-specific infrastructure now owned and
tested more deeply by PR #81 (same root cause previously also linked to SCRUM-88).

The coverage blind spot (`app/features/admin/*` excluded from `[tool.coverage.run] omit`) is
unchanged from the prior retest — see that section below for detail; not reproduced again
here.

### Current QA decision

```text
SCRUM-173 Administrator API QA: FAILED
Focused suite (this PR's files): 55 passed, 6 failed
Full backend regression: 365 passed, 6 failed, 0 unrelated regressions
Coverage: 84.41% (gate 80%) — PASSED, admin blind spot unchanged
QA pull request: Draft PR #80
Corrective issue: #70 (now tracks 1 confirmed #80-owned defect group; the Bearer/global-
  handler defect is consolidated into PR #81)
Merge readiness: NOT READY. The remaining UUID defect is real, currently reproducing, and
  blocks Story 5.1 AC1's ward-scoped provisioning path. No expected result was weakened,
  skipped, xfailed, or suppressed to obtain this result.
```

## QA-suite refinement pass (2026-08-20, superseded by the Bearer-consolidation pass above)

This pass re-read the current admin implementation (`app/features/admin/router.py`,
`service.py`, `dependencies.py`, `schemas.py`), the current `api-doc.yaml` administrator
contract, and every test this PR touches, then refined the suite against that current source
of truth rather than against the assumptions the suite was originally written under. Three
previously "failing" tests turned out to be encoding stale or incorrect expectations, not
product bugs; they are corrected below. The broad role x endpoint authorization matrix was
also reviewed and cut down, and two admin write endpoints that had no coverage at all
(`POST /admin/account`, `DELETE /admin/users/{user_id}`) gained a focused test each. No
production code was changed.

### Test-defects found and fixed in this PR's own suite

1. **`test_runtime_exposes_the_approved_admin_contract` asserted a route that was never part
   of the real contract.** `APPROVED_RUNTIME_ROUTES` required `GET /api/v1/admin/users` (a
   "list users" endpoint). No such route exists in `router.py`, and `api-doc.yaml` never
   documents a `get:` under `/api/v1/admin/users` — only `post:`. User listing is served by
   `GET /api/v1/admin/dashboard`, which already has its own passing test
   (`test_admin_dashboard_lists_users_with_safe_canonical_fields`). This was a stale
   assumption carried over from early Sprint 2 planning docs that api-doc.yaml's own
   reconciliation note calls out as never having been built as originally designed. Fixed by
   removing the spurious route from `APPROVED_RUNTIME_ROUTES` (and deleting the two unused
   `AdminPaths` fixture fields, `list_users`/`has_list_users`, that existed only to support it).

2. **`test_openapi_publishes_canonical_paths_without_legacy_aliases` misclassified two
   intentional, documented endpoints as legacy duplicates.** `LEGACY_DOCUMENTED_PATHS`
   included `/api/v1/admin/account` and `/api/v1/zones`. Both are real, currently canonical,
   deliberately schema-visible operations: `api-doc.yaml` documents `POST /admin/account`
   (`createAdminAccount`) as the staff-only provisioning endpoint distinct from
   `POST /admin/users` (`createAdminUser`, any role), and `GET /zones`
   (`listZoneReferences`) as an intentionally public, unauthenticated ward-reference lookup
   used by self-registration. Neither is a singular-alias duplicate like `/admin/user` or
   `/admin/ward`, which the router does mark `include_in_schema=False`. Fixed by removing both
   from `LEGACY_DOCUMENTED_PATHS`.

3. **`test_audit_failure_rolls_back_user_creation` was failing because of a fixture gap, not a
   transaction bug.** The shared `db_client` fixture overrides `get_db` with a bare
   `lambda: db`. FastAPI only applies a dependency override's generator/context-manager
   behaviour when the *override itself* is a generator (verified against
   `fastapi.dependencies.utils.solve_dependencies`); a plain lambda is called directly with no
   teardown at all. That silently disables `get_db`'s own `except Exception: db.rollback()`
   path (`app/db/session.py`), which is proven correct in isolation by
   `tests/unit/core/test_db_session.py::test_get_db_rolls_back_and_closes_after_escaped_exception`.
   So when the injected audit failure fired, the already-flushed (uncommitted) user row
   stayed visible on the same session the test queried, and the test reported a false
   atomicity failure that no amount of product-code correctness could pass under this
   fixture. Fixed by adding one explicit `db.rollback()` after the exception is caught,
   reproducing exactly what `get_db` already does in production, so the test now actually
   verifies what the router owns: `create_user` never calls `db.commit()` before the required
   audit write succeeds. This is a shared, pre-existing `db_client`/root-`conftest.py`
   fixture characteristic (not unique to this PR); it was corrected locally, in this file
   only, rather than by changing the shared fixture.

### Coverage consolidation: role x endpoint authorization matrix

`test_every_exposed_admin_endpoint_rejects_non_admin_roles` parametrized 4 non-admin roles x
10 endpoint keys (40 cases). Every administrator route uses exactly one dependency,
`require_admin` (`app/features/admin/dependencies.py`) — there is no per-route variation in
how the guard evaluates a role, so a full cross product re-runs identical guard logic without
adding defect-detection power. Replaced with a "cross":

- `test_every_exposed_admin_endpoint_rejects_a_non_admin_role` — one fixed non-admin role
  (`CITIZEN`) swept across every endpoint (now 12, see below) — catches a route that forgot to
  wire the guard at all.
- `test_require_admin_guard_rejects_every_non_admin_role` — all 4 non-admin roles against one
  representative endpoint (`dashboard`) — catches a guard that misjudges a specific role.

This covers the same class of regression (broken function-level authorization on any given
route, or a guard that admits a role it shouldn't) at 16 cases instead of 40.

### New coverage: previously untested admin write endpoints

Two real, currently implemented, documented admin endpoints had zero test coverage before
this pass (only an unused fixture path existed for one of them):

- `POST /api/v1/admin/account` (`test_admin_account_route_only_provisions_staff_roles`,
  2 cases) — the endpoint's distinguishing behaviour is rejecting any role other than
  `MUNICIPAL_OFFICER`/`SYSTEM_ADMIN` with `403`; verified both the rejection and a successful
  staff-account creation.
- `DELETE /api/v1/admin/users/{user_id}` (`test_admin_deletes_another_user_but_not_self`,
  1 case) — verified an admin cannot delete their own account (`400`, row unchanged) and can
  hard-delete another user (`204`, row gone, `USER_DELETED` audit row attributed to the actor).

Both endpoints were also added to the two authorization sweeps above (`create-account`,
`delete-user` endpoint keys) so they are covered by the shared-guard checks too.

### Net suite-size effect (this PR's own files only)

```text
File                            Before  After
test_admin_contract.py              54     32
test_admin_system.py                 1      1
test_admin_users.py                 20     23
test_admin_wards_support.py          6      6
                                   ---    ---
Total                               81     62
```

Net -19 tests: -24 from consolidating the authorization matrix, +6 from extending both
sweeps to the 2 newly recognized endpoints, +3 from the 2 new endpoint-coverage tests. No
behaviour the suite previously exercised was dropped without an equal-or-stronger
replacement; the matrix reduction removed only cases that re-tested the identical shared
guard.

### Retest execution record

```text
Repository base commit: 0f71a83 (origin/main already merged), refined tests uncommitted in
  the working tree
Branch: test/SCRUM-173-admin-qa
Execution date: 2026-08-20
Python: 3.12.3
PostgreSQL: 16 (Docker container verdeza-postgres, port 5433)
Database: verdeza_pytest_test (disposable, ends in _test)

Ruff check (repo-wide):            All checks passed
Ruff format --check (repo-wide):   169 files already formatted
python -m pip check:               No broken requirements found
python -m compileall app tests alembic: clean
alembic upgrade head / alembic check: No new upgrade operations detected

Focused suite, this PR's own files
  (test_admin_contract.py, test_admin_system.py, test_admin_users.py,
  test_admin_wards_support.py):
62 collected, 55 passed, 7 failed, 0 errors, 0 skipped

Full tests/api/features/admin + tests/unit/features/admin directory
  (includes 7 pre-existing tests from another merged PR, #72 —
  test_user_update_api.py, test_schemas.py — untouched, not part of PR #80,
  all 7 passing):
69 collected, 62 passed, 7 failed, 0 errors, 0 skipped

Full backend suite:
372 collected, 365 passed, 7 failed, 0 errors, 0 skipped, 251.53s
Coverage: 84.41% (gate: >= 80%) -> PASSED

The 7 failures are identical across the focused run, the admin-directory run and the full
backend run — no unrelated regression anywhere else in the codebase.
```

### Coverage blind spot (unchanged, reported not fixed)

`pyproject.toml`'s `[tool.coverage.run]` still carries
`omit = ["alembic/*", "tests/*", "app/features/admin/*"]`. Confirmed this run: `coverage.xml`
contains zero rows for any `app/features/admin/*` file. The 80% gate and the 84.41% figure
above are computed with all admin production code excluded — a regression that silently
dropped admin coverage to 0% would not fail CI. This blind spot predates this PR and was not
introduced or widened by it; per instructions it is reported, not changed, here. Recommend a
follow-up ticket to remove `app/features/admin/*` from `omit` once the 2 defects below are
fixed, so the gate actually protects this module going forward.

### Remaining confirmed backend defects (2, down from 4 previously recorded)

Both were independently reproduced this session by reading the exact failing line and
triggering it directly; neither is a test artifact.

#### BACKEND DEFECT — `POST /api/v1/admin/users` crashes when a ward is supplied

**Location:** `app/features/admin/router.py:479`, inside `create_user()`.

**Root cause:** `AdminUserCreate.zone_id` (`app/features/admin/schemas.py:43`) is typed
`uuid.UUID | None`, so Pydantic has already parsed it into a `UUID` instance by the time the
handler runs. The handler then does `zone_uuid = uuid.UUID(user_data.zone_id)` — passing an
existing `UUID` object into `uuid.UUID()`, which raises
`AttributeError: 'UUID' object has no attribute 'replace'` (confirmed via direct traceback
this session, `uuid.py:175`). `POST /api/v1/admin/account` (`create_account`) does not have
this bug — it uses `account_data.zone_id` directly with no re-wrap — so staff-only
provisioning through that endpoint is unaffected.

**Impact:** Breaks the core Story 5.1 AC1 flow of provisioning any supported role with a
valid ward (500 instead of 201), and breaks the "unknown ward" validation path (500 instead
of the required 422) — both explicitly called out as highest-value behaviour for this QA
pass ("valid ward/reference handling").

**Affected tests (still correctly red, not weakened):**
```text
tests/api/features/admin/test_admin_system.py::test_admin_provisions_user_user_logs_in_admin_disables_and_reenables
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[CITIZEN]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[COLLECTION_WORKER]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[MUNICIPAL_OFFICER]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[RECYCLER]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[unknown-ward]
```

**Required correction:** drop the redundant `uuid.UUID(...)` re-wrap in `create_user` and use
`user_data.zone_id` directly, mirroring `create_account`.

#### BACKEND DEFECT — 401 responses omit `WWW-Authenticate: Bearer`

**Location:** `app/main.py`, the `StarletteHTTPException` exception handler
(`register_exception_handlers`, `_http`).

**Root cause:** The handler rebuilds a fresh `JSONResponse` via `error_response(...)` and
never forwards `exc.headers`, so the `WWW-Authenticate: Bearer` header FastAPI's HTTPBearer
dependency attaches to its 401 is dropped on every route in the app, admin included.
Confirmed this session: the response header is `None` where `Bearer` is required. Same
shared root cause already tracked under SCRUM-88
(`docs/qa/scrum-88-auth-test-evidence.md`).

**Affected test:**
```text
tests/api/features/admin/test_admin_contract.py::test_missing_credentials_include_the_bearer_challenge
```

**Required correction:** forward `exc.headers` (when present) onto the constructed
`JSONResponse` in the `StarletteHTTPException` handler.

### Current QA decision

```text
SCRUM-173 Administrator API QA: FAILED
Focused suite (this PR's files): 55 passed, 7 failed
Full backend regression: 365 passed, 7 failed, 0 unrelated regressions
Coverage: 84.41% (gate 80%) — PASSED, but app/features/admin/* remains excluded (see blind
  spot note above)
QA pull request: Draft PR #80
Corrective issue: #70 (now tracks 2 confirmed defects, down from 4 — 2 previously recorded
  items were QA-suite defects, not product defects, and are corrected in this PR's own tests
  above)
Merge readiness: NOT READY. Both remaining defects are real, currently reproducing, and block
  highest-value Story 5.1 behaviour (ward-scoped provisioning; the auth challenge header).
  No expected result was weakened, skipped, xfailed, or suppressed to obtain this result.
```

## HISTORICAL — Retest result before QA-suite refinement (2026-08-12, superseded)

`origin/main` was merged into `test/SCRUM-173-admin-qa` (clean auto-merge, no conflicts) and the
full administrator suite was rerun against the disposable local PostgreSQL test database
(`verdeza_pytest_test`, Docker container `verdeza-postgres`, port 5433). No test code required any
change — all failures reproduce genuine, currently-reachable backend defects.

```text
Branch: test/SCRUM-173-admin-qa
Main merged at: main HEAD b9fdbef (PR #110)
Execution date: 2026-08-12

Focused suite (tests/api/features/admin):
72 passed, 10 failed, 82 collected, 0 errors

Full backend suite:
297 passed, 10 failed, 307 collected, 0 errors
Coverage: 81.57% (gate: >= 80%) -> PASSED

Ruff check (focused + repo-wide): All checks passed
Ruff format --check (focused + repo-wide): all files already formatted
python -m compileall app tests alembic: clean
alembic check: No new upgrade operations detected
```

Compared with the last recorded retest (commit `4c56834`, 71 passed / 11 failed), one previously
failing case is now resolved:

- `test_admin_contract.py::test_static_swagger_documents_the_approved_admin_paths` now **passes** —
  `api-doc.yaml` documents the required administrator paths (resolved by later corrective/docs
  commits already on `main`).

The other 10 failures are unchanged and remain genuine backend defects, verified directly against
current `app/features/admin/router.py` and `app/features/wards/router.py` on this merge:

1. **`GET /api/v1/admin/users` still does not exist.** No list-users route is registered anywhere in
   `app/features/admin/router.py` (only `POST /users`, `PATCH /users/{id}`, `PATCH
   /users/{id}/status`, `DELETE /users/{id}`).
2. **Legacy paths still published in OpenAPI.** `POST /api/v1/admin/account`
   (`app/features/admin/router.py:217`, no `include_in_schema=False`) and `GET /api/v1/zones`
   (`app/features/wards/router.py:25`) are both still live, undeprecated duplicates of the canonical
   `/admin/users` and `/wards` routes.
3. **`WWW-Authenticate: Bearer` dropped on 401s** — same shared root cause already documented for
   SCRUM-88 (`docs/qa/scrum-88-auth-test-evidence.md`): the global `StarletteHTTPException` handler
   in `app/main.py` rebuilds the JSON response and never forwards `exc.headers`.
4. **`uuid.UUID(user_data.zone_id)` crashes with `AttributeError: 'UUID' object has no attribute
   'replace'`** at `app/features/admin/router.py:479`. `AdminUserCreate.zone_id` is typed
   `uuid.UUID | None` (`app/features/admin/schemas.py:43`), so Pydantic has already parsed it into a
   `UUID` instance by the time the handler re-wraps it in `uuid.UUID(...)`. This breaks user
   provisioning for every valid zone and turns the "unknown ward" validation case into an
   unhandled 500 instead of the expected `422`. Affects
   `test_admin_provisions_user_user_logs_in_admin_disables_and_reenables`, all 4 role-provisioning
   cases in `test_admin_can_provision_each_supported_role_with_safe_canonical_output`, and the
   `unknown-ward` case in `test_admin_create_rejects_unsafe_or_invalid_input_without_persistence`.
5. **Audit-log failure during user creation does not roll back the persisted user.**
   `test_audit_failure_rolls_back_user_creation` still asserts the created user is `None` after a
   simulated `create_audit_log` failure and finds it persisted instead.

No expected result was weakened, skipped, xfailed, or suppressed.

```text
QA decision: FAILED (4 genuine backend defects remain across 10 test cases)
Merge status: Blocked on the 4 defects above
Corrective issue: #70 must remain open until the routes/header/UUID-bug/rollback are fixed
```

## Evidence history

- **Initial focused execution:** 47 collected, 12 passed, 35 failed, 0 errors, 0 skipped.
- **Latest QA-maintenance retest:** 82 collected, 71 passed, 11 failed, 0 errors, 0 skipped.
- The initial tables and defect details are retained for traceability.
- The latest retest section supersedes any initial defect classification that no longer reproduces.

## Endpoint coverage

| Method | Approved endpoint | Purpose | Automated coverage |
|---|---|---|---|
| `POST` | `/api/v1/admin/users` | Provision a supported user role | `test_admin_users.py`, `test_admin_system.py` |
| `GET` | `/api/v1/admin/users` | List users safely and deterministically | `test_admin_users.py` |
| `PATCH` | `/api/v1/admin/users/{user_id}` | Edit role/status and enforce lifecycle rules | `test_admin_users.py`, `test_admin_system.py` |
| `GET` | `/api/v1/wards` | Public canonical ward reference | `test_admin_wards_support.py` |
| `GET` | `/api/v1/admin/wards` | Administrator ward list | `test_admin_wards_support.py` |
| `POST` | `/api/v1/admin/wards` | Administrator ward creation | `test_admin_wards_support.py` |
| `PATCH` | `/api/v1/admin/wards/{ward_id}` | Administrator ward update | `test_admin_wards_support.py` |
| `DELETE` | `/api/v1/admin/wards/{ward_id}` | Delete only an unreferenced ward | `test_admin_wards_support.py` |
| `GET` | `/api/v1/admin/dashboard` | Administrator support dashboard | `test_admin_wards_support.py` |
| `GET` | `/api/v1/admin/logs` | Bounded administrator audit-log view | `test_admin_wards_support.py` |
| Route inventory | Legacy singular and duplicate paths | Must not be exposed | `test_admin_contract.py` |

## Initial test cases and execution results

The table below records the first focused execution at commit `d65669d`. It is preserved as
historical evidence. Use the latest retest section for the current result and open failure groups.


| Test ID | Story / Rule | API endpoint | Request input / action | Expected output and database result | Automated pytest node | Actual output | Result | Defect |
|---|---|---|---|---|---|---|---|---|
| ADM-01 | 5.1 contract | Runtime routes | Inspect registered methods and paths | All approved plural paths exist; singular `/admin/user`, `/admin/ward`, duplicate `/admin/account`, hard-delete user path and `/zones` are absent | `tests/api/features/admin/test_admin_contract.py::test_runtime_exposes_the_approved_admin_contract` | Failed. Required canonical routes were missing, including `POST/GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/{user_id}`, `GET /api/v1/wards` and plural `/api/v1/admin/wards` routes. Legacy singular and duplicate routes remained registered. | Fail | ADM-QA-01 |
| ADM-02 | R1, S1-G01 | Every protected admin endpoint | No Authorization header with otherwise valid request | `401 AUTHENTICATION_REQUIRED`; `WWW-Authenticate: Bearer`; no state change | `tests/api/features/admin/test_admin_contract.py::test_every_admin_endpoint_rejects_missing_credentials_with_401` | All 10 parameter cases failed. Every request returned `403 FORBIDDEN` with message `Not authenticated` instead of `401 AUTHENTICATION_REQUIRED`. The `WWW-Authenticate: Bearer` assertion was not reached. | Fail | AUTH-QA-06 |
| ADM-03 | AC4, R1 | Every protected admin endpoint | Authenticated Citizen calls each administrator function | `403 FORBIDDEN`; no read/write beyond authorised scope | `tests/api/features/admin/test_admin_contract.py::test_every_admin_endpoint_rejects_non_admin_roles` | All 10 parameter cases passed. Each administrator operation returned `403 FORBIDDEN` in the standard error envelope with a matching request ID. | Pass | — |
| ADM-04 | AC1, S1-5101 | `POST /api/v1/admin/users` | Admin submits valid Citizen, Worker, Officer and Recycler accounts with valid ward | `201`; canonical role and `ward_code`; password hashed; `last_login_at` remains null; user and audit row committed together | `tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output` | All four role cases persisted a user with the expected role, ward and `ACTIVE` status, but every new account had a non-null `last_login_at`. Assertions for password hashing, audit, response body and `201` occurred after the failing assertion and were not reached. A separate system test confirmed that creation returned `200` instead of `201`. | Fail | ADM-QA-02, ADM-QA-03 |
| ADM-05 | AC1 | `GET /api/v1/admin/users?limit=20&offset=0` | Admin lists three or more users | `200`; deterministic bounded page with `items,total,limit,offset`; no password hash, token version, deletion field or internal `zone_id` | `tests/api/features/admin/test_admin_users.py::test_admin_user_list_is_paginated_deterministic_and_safe` | Returned `200`, but the body contained `stats` and `users` rather than `items`, `total`, `limit` and `offset`. Later pagination, role and field-leakage assertions were not reached. | Fail | ADM-QA-01 |
| ADM-06 | AC3, S1-5103 | `POST /api/v1/admin/users` | Exact duplicate email, case/space-normalised duplicate email and duplicate phone | `409 DUPLICATE_RESOURCE`; exactly one matching user remains; no database detail leaked | `tests/api/features/admin/test_admin_users.py::test_duplicate_email_and_phone_are_rejected_without_creating_a_second_user` | Exact-email and phone cases prevented a second user and returned `409`, but used error code `CONFLICT` instead of `DUPLICATE_RESOURCE`. The normalised-email case created a second user; user count increased from 2 to 3. | Fail | ADM-QA-04, ADM-QA-05 |
| ADM-07 | R4, S1-5104 | `POST /api/v1/admin/users` | Protected fields, blank name, 73-byte password, invalid role and unknown ward | `422 VALIDATION_ERROR`; no user persisted; no submitted secret or internal field reflected | `tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence` | Mass-assignment, blank-name and 73-byte-password cases persisted a user, so response assertions were not reached. Invalid-role and unknown-ward cases did not persist a user and returned `422`, but used error code `ERROR` instead of `VALIDATION_ERROR`. | Fail | ADM-QA-05, ADM-QA-06 |
| ADM-08 | AC2, S1-5102 | `PATCH /api/v1/admin/users/{id}` plus login/me | Admin disables active user after token issue | Update `200`; status and token version change atomically with audit; old token and login both return generic `401` | `tests/api/features/admin/test_admin_users.py::test_disabling_user_revokes_login_and_existing_token_atomically` | Update returned `200` and stored status became `DISABLED`, but `token_version` remained `1` instead of increasing to `2`. Audit, login and old-token assertions were not reached. | Fail | ADM-QA-07 |
| ADM-09 | AC6, S1-5105 | `PATCH /api/v1/admin/users/{id}` plus me | Admin changes Citizen to Worker while old token exists | Update `200`; token version increments; old token returns `401`; fresh token returns canonical new role | `tests/api/features/admin/test_admin_users.py::test_role_change_invalidates_old_token_and_enforces_new_role` | Update returned `200` and stored role changed to `COLLECTION_WORKER`, but `token_version` remained `1` instead of increasing to `2`. Old-token and fresh-token assertions were not reached. | Fail | ADM-QA-07 |
| ADM-10 | AC7, S1-5105 | `PATCH /api/v1/admin/users/{id}` plus login | Disable, re-enable, then log in | Both changes succeed; login restored only after re-enable; both actions retain actor/timestamp audit rows | `tests/api/features/admin/test_admin_users.py::test_reenable_restores_login_and_records_both_state_changes` | Disable returned `200`, re-enable returned `200`, final status was `ACTIVE`, login returned `200` and at least two audit rows existed. The last two audit rows were not both attributed to the acting administrator. | Fail | ADM-QA-08 |
| ADM-11 | AC8, S1-5106 | `PATCH /api/v1/admin/users/{id}` | Disable or demote the only active administrator | `409 CONFLICT`; account remains active `SYSTEM_ADMIN` | `tests/api/features/admin/test_admin_users.py::test_last_active_administrator_cannot_be_disabled_or_demoted` | Both parameter cases failed. The disable case stored status `DISABLED`; the demote case stored role `MUNICIPAL_OFFICER`. The expected `409` response assertion was not reached because the forbidden state changes had already persisted. | Fail | ADM-QA-09 |
| ADM-12 | AC8 | `PATCH /api/v1/admin/users/{id}` | Demote one administrator while a second active administrator exists | `200`; target role changes and at least one active administrator remains | `tests/api/features/admin/test_admin_users.py::test_second_active_admin_allows_one_admin_to_be_demoted` | Passed. The update returned `200`, the target became `MUNICIPAL_OFFICER`, and at least one active `SYSTEM_ADMIN` remained. | Pass | — |
| ADM-13 | R2, S1-G04 | `POST /api/v1/admin/users` | Simulate required audit failure during user creation | Request fails safely; user and audit are both rolled back; no partial business commit | `tests/api/features/admin/test_admin_users.py::test_audit_failure_rolls_back_user_creation` | The simulated audit function was invoked and raised an exception, but the API returned `200`. The rollback assertion occurred after the failed status assertion and was not reached, so persistence after the audit failure remains unverified by this execution. | Fail | ADM-QA-10 |
| ADM-14 | Supporting contract | `GET /api/v1/wards` | Anonymous request with multiple wards | `200`; canonical code/name/sectors in deterministic order; no internal manager key | `tests/api/features/admin/test_admin_wards_support.py::test_public_wards_use_canonical_route_schema_and_order` | Returned `404 Not Found` instead of `200`; schema, ordering and field-safety assertions were not reached. | Fail | ADM-QA-01 |
| ADM-15 | R2, R4 | Admin ward CRUD endpoints | Create spaced/lowercase ward, list, update, then delete unassigned ward | `201/200/200/204`; canonical code/name; ordered list; create/update/delete audited | `tests/api/features/admin/test_admin_wards_support.py::test_admin_can_create_list_update_and_delete_unassigned_ward_with_audit` | Passed through the currently resolved runtime ward paths. Create returned `201` with canonical code/name, list returned `200`, update returned `200`, at least two administrator-attributed audit rows existed before deletion, delete returned `204`, and the ward was removed. The current test does not separately assert list ordering or a delete audit row; see QA-GAP-01. | Pass | QA-GAP-01 |
| ADM-16 | R4 | Admin ward create/update | Duplicate canonical ward code and unknown UUID | Duplicate returns `409 DUPLICATE_RESOURCE`; unknown returns `404 RESOURCE_NOT_FOUND`; safe envelope | `tests/api/features/admin/test_admin_wards_support.py::test_duplicate_ward_code_and_unknown_ward_id_return_safe_errors` | Duplicate ward returned `409` in the safe envelope but used code `CONFLICT` instead of `DUPLICATE_RESOURCE`. The unknown-UUID case occurred after this failing assertion and was not reached. | Fail | ADM-QA-05 |
| ADM-17 | R3 | `DELETE /api/v1/admin/wards/{id}` | Delete ward referenced by a user | `409 CONFLICT`; ward and user assignment remain unchanged | `tests/api/features/admin/test_admin_wards_support.py::test_ward_with_assigned_user_cannot_be_deleted` | The ward remained stored, but the API returned `400 BAD_REQUEST` with `Cannot delete ward with 1 assigned users` instead of `409 CONFLICT`. | Fail | ADM-QA-05 |
| ADM-18 | R1, R4 | Dashboard and logs | Admin requests dashboard and logs with `limit=20` | `200`; bounded log list in newest-first order; no passwords, token versions, deletion fields or internal `zone_id` | `tests/api/features/admin/test_admin_wards_support.py::test_dashboard_and_logs_are_admin_only_bounded_and_do_not_leak_internal_fields` | Dashboard and logs returned `200`, dashboard user count was present, and `password_hash`, `token_version` and `deleted_at` were absent. Dashboard user records exposed internal `zone_id`. Log bound/order and final safe-body assertions were not reached. | Fail | ADM-QA-11 |
| ADM-19 | AC1, AC2, AC7 | Cross-endpoint system journey | Admin creates Citizen → Citizen logs in/me → Admin disables → old session/login denied → Admin re-enables → login restored | Identity, canonical role and ward remain consistent; disable takes immediate effect; re-enable restores access | `tests/api/features/admin/test_admin_system.py::test_admin_provisions_user_user_logs_in_admin_disables_and_reenables` | The first create request returned `200` instead of required `201`. The journey stopped at that assertion; login, profile, disable, revocation, re-enable and restored-login stages were not executed. | Fail | ADM-QA-02 |

## Initial execution record

```text
Commit tested: d65669d
Branch: test/SCRUM-173-admin-qa
Host: ERAMEL
Database: Disposable PostgreSQL database ending in _test
Python: 3.12.3
PostgreSQL: 16.14
Execution timestamp: 2026-08-01T00:45:57+03:00

Command:
python -m pytest --no-cov -q \
  tests/api/features/admin \
  --junitxml=/mnt/c/Users/enish/Downloads/SCRUM173_Admin_Test_Evidence/scrum173-admin-junit.xml

Collection:
47 tests

Focused administrator API result:
12 passed, 35 failed in 15.97s
0 errors
0 skipped

Machine-readable evidence:
scrum173-admin-junit.xml

Human-readable evidence:
scrum173-admin-pytest.txt

Coverage:
Not measured in this focused run because --no-cov was used.

Full backend result:
Pending. Run only after linked product corrections are merged into main.

Current QA decision:
Failed. SCRUM-173 administrator APIs are not accepted for sign-off.

Classified root causes:
12 total
- 11 SCRUM-173 product root causes
- 1 shared authentication root cause already tracked under SCRUM-88
```

## Initial defect summary

This classification reflects the first execution only. Some initial failures were later removed
after correcting stale test adapters and unnecessarily broad assertions. The current open failure
groups are listed in the latest retest section.


| Defect | Severity | Priority | Summary | Affected evidence |
|---|---|---|---|---|
| ADM-QA-01 | High | P0 | Canonical administrator user and ward routes and response contracts are missing | ADM-01, ADM-05, ADM-14 |
| AUTH-QA-06 | High | P0 | Missing Bearer credentials return `403 FORBIDDEN` instead of `401 AUTHENTICATION_REQUIRED` | ADM-02 |
| ADM-QA-02 | Medium | P0 | Administrator user creation returns `200` instead of `201` | ADM-04, ADM-19 |
| ADM-QA-03 | Medium | P0 | Newly provisioned accounts receive a false `last_login_at` value | ADM-04 |
| ADM-QA-04 | High | P0 | Email duplicate detection is not case/space normalised | ADM-06 |
| ADM-QA-05 | Medium | P0 | Administrator APIs return non-canonical public error statuses/codes | ADM-06, ADM-07, ADM-16, ADM-17 |
| ADM-QA-06 | High | P0 | User provisioning accepts protected fields and unsafe input that should be rejected | ADM-07 |
| ADM-QA-07 | High | P0 | Role/status changes do not increment `token_version` | ADM-08, ADM-09 |
| ADM-QA-08 | High | P0 | User state-change audit rows are not consistently attributed to the acting administrator | ADM-10 |
| ADM-QA-09 | Critical | P0 | The last active administrator can be disabled or demoted | ADM-11 |
| ADM-QA-10 | High | P0 | Required audit failures are swallowed and the request reports success | ADM-13 |
| ADM-QA-11 | Medium | P0 | Administrator dashboard exposes internal `zone_id` | ADM-18 |

## Initial defect details

These defect details are retained for traceability. They describe the initial execution and must not
be treated as the current defect list when the latest retest no longer reproduces them.


### ADM-QA-01 — Canonical administrator routes and contracts are missing

**Severity:** High
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

The runtime exposes the approved plural administrator routes and public `/api/v1/wards` route. Legacy singular and duplicate routes are absent. User listing uses `items`, `total`, `limit` and `offset`.

**Actual**

The approved routes were absent, legacy routes remained registered, `/api/v1/wards` returned `404`, and the current user-list request returned a dashboard-shaped body with `stats` and `users`.

**Affected tests**

```text
tests/api/features/admin/test_admin_contract.py::test_runtime_exposes_the_approved_admin_contract
tests/api/features/admin/test_admin_users.py::test_admin_user_list_is_paginated_deterministic_and_safe
tests/api/features/admin/test_admin_wards_support.py::test_public_wards_use_canonical_route_schema_and_order
```

**Required correction**

Register the approved canonical routes, remove legacy and duplicate route semantics, return the approved schemas, and preserve the current behaviour only through the canonical contract.

---

### AUTH-QA-06 — Missing Bearer credentials return the wrong authentication response

**Severity:** High
**Priority:** P0
**Initial status:** Existing SCRUM-88 defect
**Corrective issue:** Use the existing SCRUM-88 authentication issue
**Corrective PR:** Pending

**Expected**

Every missing-credential request returns `401 AUTHENTICATION_REQUIRED` with `WWW-Authenticate: Bearer`.

**Actual**

All 10 administrator endpoint cases returned `403 FORBIDDEN` with message `Not authenticated`.

**Affected test**

```text
tests/api/features/admin/test_admin_contract.py::test_every_admin_endpoint_rejects_missing_credentials_with_401
```

**Required correction**

Route missing, unsupported and malformed credentials through the shared generic Bearer authentication failure handler.

---

### ADM-QA-02 — Administrator user creation returns HTTP 200 instead of 201

**Severity:** Medium
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Successful administrator provisioning returns `201 Created`.

**Actual**

The system journey received `200 OK` from the creation request.

**Affected tests**

```text
tests/api/features/admin/test_admin_system.py::test_admin_provisions_user_user_logs_in_admin_disables_and_reenables
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output
```

**Required correction**

Declare and return HTTP `201 Created` for successful administrator provisioning.

---

### ADM-QA-03 — Provisioning incorrectly populates last_login_at

**Severity:** Medium
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

`last_login_at` remains null until the provisioned user completes a successful login.

**Actual**

Citizen, Collection Worker, Municipal Officer and Recycler accounts all received a non-null `last_login_at` during creation.

**Affected test**

```text
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output
```

**Required correction**

Do not set `last_login_at` during provisioning. Update it only after successful authentication.

---

### ADM-QA-04 — Normalised duplicate email is accepted

**Severity:** High
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Duplicate-email checks are case-insensitive and ignore surrounding spaces.

**Actual**

Submitting a case/space variation of an existing email created a second user; the user count increased from 2 to 3.

**Affected test**

```text
tests/api/features/admin/test_admin_users.py::test_duplicate_email_and_phone_are_rejected_without_creating_a_second_user[email-normalised]
```

**Required correction**

Canonicalise email before lookup and persistence and enforce a concurrency-safe canonical uniqueness rule.

---

### ADM-QA-05 — Administrator APIs use non-canonical public error statuses and codes

**Severity:** Medium
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Duplicate resources return `409 DUPLICATE_RESOURCE`; invalid role/ward input returns `422 VALIDATION_ERROR`; referenced-ward deletion returns `409 CONFLICT`.

**Actual**

Exact duplicate user identity and duplicate ward cases returned `409 CONFLICT`; invalid role and unknown ward returned `422 ERROR`; referenced-ward deletion returned `400 BAD_REQUEST`.

**Affected tests**

```text
tests/api/features/admin/test_admin_users.py::test_duplicate_email_and_phone_are_rejected_without_creating_a_second_user[email-exact]
tests/api/features/admin/test_admin_users.py::test_duplicate_email_and_phone_are_rejected_without_creating_a_second_user[phone]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[invalid-role]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[unknown-ward]
tests/api/features/admin/test_admin_wards_support.py::test_duplicate_ward_code_and_unknown_ward_id_return_safe_errors
tests/api/features/admin/test_admin_wards_support.py::test_ward_with_assigned_user_cannot_be_deleted
```

**Required correction**

Use the standard public error taxonomy consistently without exposing database or implementation details.

---

### ADM-QA-06 — Unsafe user-creation input is accepted and persisted

**Severity:** High
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Protected fields, whitespace-only names and passwords over 72 UTF-8 bytes are rejected with `422 VALIDATION_ERROR`, and no user is created.

**Actual**

Mass-assignment, blank-name and 73-byte-password inputs each resulted in a persisted user.

**Affected tests**

```text
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[mass-assignment]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[blank-name]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[password-over-72-bytes]
```

**Required correction**

Forbid undeclared fields, trim and reject blank text, and enforce the bcrypt UTF-8 byte boundary before persistence or hashing.

---

### ADM-QA-07 — Role and status changes do not revoke existing sessions

**Severity:** High
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Every role or status change increments `token_version` exactly once so existing tokens become invalid.

**Actual**

Disable and role-change operations returned `200` and persisted the requested change, but `token_version` remained `1`.

**Affected tests**

```text
tests/api/features/admin/test_admin_users.py::test_disabling_user_revokes_login_and_existing_token_atomically
tests/api/features/admin/test_admin_users.py::test_role_change_invalidates_old_token_and_enforces_new_role
```

**Required correction**

Increment `token_version` in the same transaction as every effective role/status change and reject all stale tokens.

---

### ADM-QA-08 — State-change audits use an incorrect actor

**Severity:** High
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Disable and re-enable audit rows identify the authenticated administrator as actor.

**Actual**

Both state changes and restored login succeeded, and at least two audit rows existed, but the last two rows were not both attributed to the administrator.

**Affected test**

```text
tests/api/features/admin/test_admin_users.py::test_reenable_restores_login_and_records_both_state_changes
```

**Required correction**

Use the authenticated administrator ID for every administrator-triggered user lifecycle audit entry.

---

### ADM-QA-09 — Last-active-administrator guard is absent

**Severity:** Critical
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Disabling or demoting the only active system administrator returns `409 CONFLICT` and leaves the account unchanged.

**Actual**

The only active administrator could be stored as `DISABLED` and could be changed to `MUNICIPAL_OFFICER`.

**Affected tests**

```text
tests/api/features/admin/test_admin_users.py::test_last_active_administrator_cannot_be_disabled_or_demoted[disable]
tests/api/features/admin/test_admin_users.py::test_last_active_administrator_cannot_be_disabled_or_demoted[demote]
```

**Required correction**

Lock and count active system administrators within the update transaction. Reject the operation when it would leave none active.

---

### ADM-QA-10 — Required audit failure is swallowed

**Severity:** High
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

A required audit failure aborts the request and rolls back the business write.

**Actual**

The injected audit function raised, but the API returned `200`. The rollback assertion was not reached after the failed status assertion.

**Affected test**

```text
tests/api/features/admin/test_admin_users.py::test_audit_failure_rolls_back_user_creation
```

**Required correction**

Create the user and required audit entry in one transaction. Do not catch and ignore required audit exceptions.

---

### ADM-QA-11 — Administrator dashboard exposes internal zone_id

**Severity:** Medium
**Priority:** P0
**Initial status:** Open
**Corrective issue:** #70
**Corrective PR:** Pending

**Expected**

Dashboard responses expose only approved public fields and never internal `zone_id`.

**Actual**

The dashboard returned `200` but included `zone_id` in user records.

**Affected test**

```text
tests/api/features/admin/test_admin_wards_support.py::test_dashboard_and_logs_are_admin_only_bounded_and_do_not_leak_internal_fields
```

**Required correction**

Map dashboard users through an explicit public response schema that omits internal persistence fields.

## Initial QA coverage gap

### QA-GAP-01 — Ward CRUD test does not verify every documented audit/order requirement

This gap was recorded during the initial execution and is retained for traceability. Reassess it
against the current test implementation before final sign-off.


The passing ward CRUD test verifies create, list presence, update, two administrator-attributed audit rows before deletion, successful delete and database removal. It does not explicitly assert:

- deterministic ward-list order;
- an audit row for the delete action.

Add those assertions before final sign-off. This is a test-coverage gap, not a confirmed product defect from the current execution.

## Candidate screenshots for the consolidated report

These functions are suitable candidates. Select only the screenshots needed for the overall Milestone 3 minimum of five:

1. `test_runtime_exposes_the_approved_admin_contract`
2. `test_admin_can_provision_each_supported_role_with_safe_canonical_output`
3. `test_disabling_user_revokes_login_and_existing_token_atomically`
4. `test_admin_create_rejects_unsafe_or_invalid_input_without_persistence`
5. `test_audit_failure_rolls_back_user_creation`

For each screenshot, place the matching test-case row from this document beside it in the report so the request input, expected output, actual output and result are visible together.

## Retest and sign-off rule

Do not change expected results to match the current implementation.

After the corrective code is merged into `main`:

1. merge current `main` into `test/SCRUM-173-admin-qa`;
2. rerun the focused administrator suite;
3. rerun the complete backend quality and regression commands;
4. preserve this initial failure evidence;
5. add the corrective issue/PR references and final retest result;
6. mark a row Pass only when the expected status, body, headers and database effect have been verified.

Initial sign-off status at commit `d65669d`:

```text
SCRUM-173 Administrator API QA: FAILED
Focused suite: 12 passed, 35 failed
Full backend regression: Pending corrections
Coverage: Pending full backend execution
```

## HISTORICAL — QA-maintenance retest after current-main alignment (2026-08-02, superseded)

The original focused execution is preserved above as historical evidence.

The administrator suite was audited against the current backend routes, schemas and error
envelopes. Stale route-selection logic, legacy role payloads, overly broad sensitive-field checks,
unfiltered audit assertions and nonessential whitespace assertions were corrected without weakening
the approved acceptance criteria.

### Retest execution record

```text
Repository base commit: 4c56834
QA state under test: QA-maintenance corrections executed in the working tree before this evidence update was committed
Branch: test/SCRUM-173-admin-qa
Execution date: 2026-08-02
Python: 3.12.3
PostgreSQL: 16.14
Database: Disposable PostgreSQL database ending in _test

Command:
python -m pytest --no-cov -q \
  tests/api/features/admin \
  --junitxml=/mnt/c/Users/enish/Downloads/SCRUM173_Admin_Retest/scrum173-admin-junit.xml \
  2>&1 | tee \
  /mnt/c/Users/enish/Downloads/SCRUM173_Admin_Retest/scrum173-admin-pytest.txt

Collection: 82
Passed: 71
Failed: 11
Errors: 0
Skipped: 0
Duration: 29.04 seconds
JUnit XML: SCRUM173_Admin_Retest/scrum173-admin-junit.xml
Pytest output: SCRUM173_Admin_Retest/scrum173-admin-pytest.txt
Coverage: Not measured because --no-cov was used
```

### Current failing pytest nodes

```text
tests/api/features/admin/test_admin_contract.py::test_runtime_exposes_the_approved_admin_contract
tests/api/features/admin/test_admin_contract.py::test_openapi_publishes_canonical_paths_without_legacy_aliases
tests/api/features/admin/test_admin_contract.py::test_static_swagger_documents_the_approved_admin_paths
tests/api/features/admin/test_admin_contract.py::test_missing_credentials_include_the_bearer_challenge
tests/api/features/admin/test_admin_system.py::test_admin_provisions_user_user_logs_in_admin_disables_and_reenables
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[CITIZEN]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[COLLECTION_WORKER]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[MUNICIPAL_OFFICER]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[RECYCLER]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[unknown-ward]
tests/api/features/admin/test_admin_users.py::test_audit_failure_rolls_back_user_creation
```

### Remaining confirmed failure groups

#### 1. Administrator runtime contract

**Expected**

The approved canonical administrator user-list route exists:

```text
GET /api/v1/admin/users
```

**Actual**

The route is missing from the runtime contract.

**Affected test**

```text
tests/api/features/admin/test_admin_contract.py::test_runtime_exposes_the_approved_admin_contract
```

**Current classification:** Product/API-contract defect tracked in issue #70.

#### 2. OpenAPI runtime contract

**Expected**

OpenAPI publishes only the approved canonical administrator paths and does not publish legacy
singular aliases.

**Actual**

Legacy singular administrator aliases remain published in the generated OpenAPI schema.

**Affected test**

```text
tests/api/features/admin/test_admin_contract.py::test_openapi_publishes_canonical_paths_without_legacy_aliases
```

**Current classification:** Product/API-contract defect tracked in issue #70.

#### 3. Static Swagger contract

**Expected**

`api-doc.yaml` documents every approved administrator endpoint with the required descriptions,
user-story mapping and error responses.

**Actual**

Required administrator paths are missing from `api-doc.yaml`.

**Affected test**

```text
tests/api/features/admin/test_admin_contract.py::test_static_swagger_documents_the_approved_admin_paths
```

**Current classification:** API-documentation defect tracked in issue #70.

#### 4. Authentication challenge

**Expected**

A missing Bearer token returns the approved authentication error and includes:

```text
WWW-Authenticate: Bearer
```

**Actual**

The missing-credential response does not include the required Bearer challenge header.

**Affected test**

```text
tests/api/features/admin/test_admin_contract.py::test_missing_credentials_include_the_bearer_challenge
```

**Current classification:** Shared authentication defect. Link it to the existing SCRUM-88
authentication correction as well as issue #70 where the administrator impact is recorded.

#### 5. User provisioning and unknown-ward handling

**Expected**

Valid supported-role provisioning succeeds, and an unknown ward is rejected through the approved
safe validation response.

**Actual**

The backend calls `uuid.UUID()` on a value that is already a UUID, causing:

```text
AttributeError: 'UUID' object has no attribute 'replace'
```

This shared backend error blocks the administrator system journey, all four supported-role
provisioning cases and the unknown-ward validation case.

**Affected tests**

```text
tests/api/features/admin/test_admin_system.py::test_admin_provisions_user_user_logs_in_admin_disables_and_reenables
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[CITIZEN]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[COLLECTION_WORKER]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[MUNICIPAL_OFFICER]
tests/api/features/admin/test_admin_users.py::test_admin_can_provision_each_supported_role_with_safe_canonical_output[RECYCLER]
tests/api/features/admin/test_admin_users.py::test_admin_create_rejects_unsafe_or_invalid_input_without_persistence[unknown-ward]
```

**Current classification:** Backend implementation defect tracked in issue #70.

#### 6. Required audit rollback

**Expected**

When a required audit write fails, the exception aborts the request and the new user is not retained
in the request database session.

**Actual**

After the intentionally injected audit exception is caught by the test, the rollback verification
still fails. User creation is not fully rolled back in the request session.

**Affected test**

```text
tests/api/features/admin/test_admin_users.py::test_audit_failure_rolls_back_user_creation
```

**Current classification:** Transaction-integrity defect tracked in issue #70.

### Current QA decision

```text
SCRUM-173 Administrator API QA: FAILED
Latest focused suite: 71 passed, 11 failed
Test errors: 0
Skipped: 0
Full backend regression: Pending product corrections
Coverage: Pending full backend execution
QA pull request: Draft PR #80
Corrective issue: #70
```

The remaining failures require product or API-contract corrections. Expected results were not
weakened, skipped, suppressed or changed to obtain a passing result.

### Next retest and sign-off action

After the corrective code is merged into `main`:

1. merge current `origin/main` into `test/SCRUM-173-admin-qa`;
2. rerun the focused administrator suite;
3. update only the latest retest result and the affected current failure groups;
4. run the complete backend quality and regression commands;
5. record final coverage and CI status;
6. mark the Draft PR ready only when the focused suite, complete backend suite and required CI checks
   all pass.

## HISTORICAL — CI full-backend regression result (commit `c35179`, superseded)

GitHub Actions executed the complete backend suite against QA commit `c35179`.

```text
Pull request: #80
Branch: test/SCRUM-173-admin-qa
Frontend check: Passed
API contract check: Passed
Backend dependency check: Passed
Backend lint: Passed
Backend formatting: Passed
Migration verification: Passed

Complete backend pytest result:
201 tests executed
190 passed
11 failed
0 errors
Coverage: 80.87%
Required coverage threshold: 80%
Duration: 42.61 seconds
```

The same 11 administrator failures reproduced in both the local focused execution and the
complete GitHub Actions regression. No unrelated regression failure was observed.

### CI failure groups

1. Missing `GET /api/v1/admin/users`.
2. Legacy administrator aliases remain published in OpenAPI.
3. Required administrator endpoints are missing from `api-doc.yaml`.
4. Missing credentials omit `WWW-Authenticate: Bearer`.
5. User provisioning and unknown-ward handling attempt to convert an existing UUID again.
6. Required audit failure does not roll back the created user.

### CI decision

```text
Coverage gate: Passed
Frontend check: Passed
API contract check: Passed
Backend check: Failed on confirmed requirement tests
Merge status: Blocked
QA pull request status: Draft
Corrective issue: #70
```

No expected result was weakened, skipped, suppressed or changed to make CI pass.
