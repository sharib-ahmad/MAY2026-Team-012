# SCRUM-88 Authentication QA Evidence

**Feature:** Authentication platform used by Sprint 1 protected APIs
**Source matrix:** `docs/qa/sprint1-acceptance-matrix.md`
**Execution rule:** Expected results are fixed before execution. Actual Result and
Result are recorded only from local or CI execution.

## FINAL VERIFICATION (2026-08-23, current — supersedes every section below)

This is the closing verification for PR #81, executed against **current `main`
as merged into this branch** (`76982c1`), after the accepted DEF-004 fix
(`ca666a2`, PR #134, closing issue #133). Every section below this one is
retained as **historical evidence** and no longer describes current behaviour.

### Focused execution result

```text
Branch: test/SCRUM-88-auth-qa
Branch HEAD: 76982c1 (current main merged in)
Execution date: 2026-08-23
Database: verdeza_pytest_test (Docker container verdeza-postgres, port 5433)
Python: 3.12.3

python -m pytest \
  tests/api/features/auth \
  tests/unit/features/auth \
  tests/unit/core/test_security.py \
  -q --no-cov

43 passed in 15.12s
```

No focused test fails, is skipped, or is xfailed.

### Quality checks

```text
ruff check tests/api/features/auth tests/unit/features/auth tests/unit/core/test_security.py
-> All checks passed

ruff format --check tests/api/features/auth tests/unit/features/auth tests/unit/core/test_security.py
-> passed (already formatted)
```

### Current accepted registration contract

`POST /api/v1/auth/register` **exists and remains part of the contract**. It is
public and unauthenticated, but the `role` field is now restricted server-side
(`app/features/auth/router.py::register`):

| Role | Self-registration |
|---|---|
| `CITIZEN` | Allowed |
| `COLLECTION_WORKER` (`COLLECTOR`) | Allowed |
| `RECYCLER` | Allowed |
| `MUNICIPAL_OFFICER` (`MANAGER`) | **Blocked — `403 FORBIDDEN`** |
| `SYSTEM_ADMIN` (`ADMIN`) | **Blocked — `403 FORBIDDEN`** |

Staff accounts remain administrator-provisioned, per Story 5.1. The endpoint was
**not** removed.

### Issue #133 / PR #134 resolution

PR #81 originally asserted that `POST /api/v1/auth/register` was itself
forbidden, because it predicted **endpoint removal** as the remedy for DEF-004.
That premise became **stale** when the maintainer accepted the narrower and
correct security fix in PR #134 (`ca666a2`): retain public registration, block
staff-role self-provisioning. Issue #133 was closed on that basis.

The test suite has been reconciled to the accepted contract:

- legitimate current-`main` registration coverage was retained;
- duplicate older auth tests were not restored;
- legacy / wrong-prefix auth routes (`POST /api/v1/register`,
  `POST /api/v1/login`, `GET /api/v1/me`) remain asserted absent;
- staff-role self-registration is explicitly protected;
- public-role registration is explicitly proven to succeed.

### Previously reported auth defects — current status

| Historical defect group | Current status on `main` | Verifying test (passing) |
|---|---|---|
| Staff-role self-provisioning (DEF-004 / issue #133) | **Resolved** by `ca666a2` (PR #134): staff roles rejected with `403` | `test_auth_api.py::test_self_registration_blocks_staff_roles` (4 params), `test_auth_api.py::test_self_registration_allows_public_roles` (3 params), `test_auth_contract.py::test_public_registration_role_surface_excludes_staff_roles` |
| Public registration route treated as forbidden (AUTH-QA-02 / AUTH-01) | **Premise superseded** — the endpoint is contractual; only legacy/wrong-prefix routes are forbidden | `test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes` |
| Implicit account seeding at startup (AUTH-QA-03 / AUTH-02) | **Resolved** — startup no longer seeds accounts implicitly | `test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly` |
| `WWW-Authenticate: Bearer` dropped on 401 (AUTH-08) | **Resolved** — the challenge header now reaches the client | `test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge` (3 params) |
| AUTH-QA-01, 04, 05, 06, 07, 08 (bcrypt byte limit, canonical role value, disabled-account disclosure, inconsistent 401s, malformed JWT subject, missing `token_version`) | **Resolved** in earlier corrective work | `test_auth_login.py`, `test_auth_session.py`, `tests/unit/core/test_security.py` — all passing |

### Remaining focused failures

**None.** The current focused run proves no remaining failure in the SCRUM-88
authentication scope.

### PR #81 merge readiness

```text
QA decision: PASSED for the SCRUM-88 authentication scope
Focused result: 43 passed, 0 failed, 0 skipped, 0 xfailed
Quality gates: ruff check passed; ruff format --check passed
Merge status: READY — no authentication defect remains open against current main
```

Scope note: this verdict covers the SCRUM-88 authentication scope only. Defects
recorded in `docs/qa/defect-log.md` outside that scope (DEF-001, DEF-002,
DEF-003, DEF-005, DEF-006) are unaffected by this verification and retain their
own status there.

---
## HISTORICAL — Retest Result (2026-08-20, SUPERSEDED by the FINAL VERIFICATION above)

> **Superseded.** The 3 root-cause defects and 5 failures recorded below were
> real at the time of this run. All are resolved on current `main`; see the
> FINAL VERIFICATION section above. Retained as historical evidence only.

The suite was refined for minimality without reducing fault detection: two
schema-level unit tests in `tests/unit/features/auth/test_auth_schemas.py`
(`test_login_request_trims_email_whitespace` and
`test_login_request_rejects_invalid_or_unsafe_input`, the latter parametrized
over 5 cases) were removed. Both duplicated invariants already proven more
strongly at the API level in `tests/api/features/auth/test_auth_login.py`
(`test_login_email_is_trimmed_and_case_insensitive` proves trimming
end-to-end through a successful login; `test_invalid_login_payload_returns_safe_validation_error`
proves the identical 5 input partitions are rejected with `422` through the
full HTTP stack and the safe error envelope, which the removed schema-only
duplicate did not check). No other test was changed, weakened, skipped or
xfailed. `UserRegisterRequest` schema unit tests were kept as-is: they are the
only coverage for that schema, do not call the out-of-contract
`POST /api/v1/auth/register` endpoint, and so do not make public registration
a test dependency.

`origin/main` was re-checked (`fe4a94e`, 4 commits ahead of this branch's merge
base: a ruff dev-dependency bump, a frontend dependency bump, an unrelated
teammate QA PR (#104, recycler/gamification), and an OpenAPI-doc-only PR
(#111)). None of the four touch `app/features/auth/`, `app/core/security.py`,
`app/main.py` or `app/api/v1/router.py`, so the three root-cause defects below
are unchanged and this branch was not rebased.

```text
Branch: test/SCRUM-88-auth-qa
Branch HEAD: d7322e0
Execution date: 2026-08-20
Database: verdeza_pytest_test (Docker container verdeza-postgres, port 5433)
Python: 3.12.3

Focused suite (auth + security + auth schemas):
27 passed, 5 failed, 32 collected, 0 errors
(38 -> 32 collected: 6 fewer tests from the consolidation above)

Full backend suite:
242 passed, 5 failed, 247 collected, 0 errors
Coverage: 81.75% (gate: >= 80%) -> PASSED

pip check: No broken requirements found
Ruff check (repo-wide): All checks passed
Ruff format --check (repo-wide): 159 files already formatted
python -m compileall -q app tests alembic: clean
alembic check: No new upgrade operations detected
```

The same 5 failing test cases, reproducing the same 3 previously-documented
root-cause defect groups, are still present and were deliberately left
failing (not weakened, skipped or xfailed) because each is a valid,
requirement-backed test exposing a genuine backend defect:

1. **Public self-registration route still exposed.** `POST /api/v1/auth/register`
   still exists in `app/features/auth/router.py:38`, which the accepted
   contract (S1-5101, and `api-doc.yaml`'s auth path list) forbids — Story 5.1
   specifies System-Admin-driven user provisioning only, with no story for
   citizen self-registration. Test: `test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes`.
2. **Application startup still seeds accounts implicitly.** `app/main.py`'s
   `lifespan` calls `seed_database(...)` whenever `APP_ENV != "test"`
   (`app/main.py:328-333`), creating a known `admin@verdeza.test` /
   `password123` account outside a disposable test environment, with no
   additional guard. Test:
   `test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly`.
3. **`WWW-Authenticate: Bearer` header dropped on 401s.** `get_current_user`
   correctly raises `HTTPException(..., headers={"WWW-Authenticate": "Bearer"})`
   (`app/features/auth/dependencies.py:35`), and `api-doc.yaml`'s
   `AuthenticationRequired` response component formally documents this header
   on every protected endpoint, but the global `StarletteHTTPException`
   handler in `app/main.py` (`_http`, around line 132) rebuilds the JSON
   response via `error_response(...)` and never forwards `exc.headers`, so the
   header never reaches the client. Test:
   `test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge`
   (all 3 parametrizations).

```text
QA decision: FAILED (3 genuine backend defects remain; coverage gate passes)
Merge status: Blocked on the 3 defects above, not on coverage or test quality
Corrective issue: #69 must remain open until routes/seeding/header are fixed
```

## HISTORICAL — Retest Result (2026-08-12, superseded by the 2026-08-20 retest above)

`origin/main` was merged into `test/SCRUM-88-auth-qa` and the full authentication
suite was rerun against the disposable local PostgreSQL test database
(`verdeza_pytest_test`, Docker container `verdeza-postgres`, port 5433).

```text
Branch: test/SCRUM-88-auth-qa
Main merged at: 813133a (origin/main HEAD b9fdbef, PR #110)
Execution date: 2026-08-12

Focused suite (auth + security + auth schemas):
33 passed, 5 failed, 38 collected, 0 errors

Full backend suite:
248 passed, 5 failed, 253 collected, 0 errors
Coverage: 81.75% (gate: >= 80%) -> PASSED (previously 79.55% Failed)

Ruff check (focused + repo-wide): All checks passed
Ruff format --check (focused + repo-wide): all files already formatted
python -m compileall app tests alembic: clean
alembic check: No new upgrade operations detected
```

Two test corrections were made to `test_auth_login.py` and `test_auth_session.py`:
the exact-equality assertions on the login/`me` response body were missing the
`zone_name` field. `zone_name` was added to `AuthenticatedUser` by corrective PR
`#95` (already merged to `main`) and is a deliberate, non-sensitive enrichment
used consistently across the backend (`bulk_pickups`, `collection_ops`,
`materials` schemas all carry the same field). This was a stale test fixture,
not a backend defect, so only the expected-response dictionaries were updated.

The remaining 5 failures reproduce 3 genuine, previously-documented backend
defects that are still present on current `main` (verified directly against
`app/features/auth/router.py`, `app/features/auth/dependencies.py` and
`app/main.py`):

1. **Public self-registration route still exposed.** `POST /api/v1/auth/register`
   still exists in `app/features/auth/router.py:38`, which the accepted
   contract (S1-5101) forbids — there is no authoritative user story for
   citizen self-registration; Story 5.1 specifies System-Admin-driven user
   provisioning only. Test: `test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes`.
2. **Application startup still seeds accounts implicitly.** `app/main.py`'s
   `lifespan` calls `seed_database(...)` whenever `APP_ENV != "test"`
   (`app/main.py:328-333`), with no additional guard. Test:
   `test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly`.
3. **`WWW-Authenticate: Bearer` header dropped on 401s.** `get_current_user`
   correctly raises `HTTPException(..., headers={"WWW-Authenticate": "Bearer"})`
   (`app/features/auth/dependencies.py:35`), but the global
   `StarletteHTTPException` handler in `app/main.py` (`_http`, around line 132)
   rebuilds the JSON response via `error_response(...)` and never forwards
   `exc.headers`, so the header never reaches the client. Test:
   `test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge`
   (all 3 parametrizations).

No expected result was weakened, skipped, xfailed, or suppressed. These are the
same 3 root-cause groups documented in the historical sections below; only the
coverage gate and the two `zone_name`-related failures have changed since the
last recorded retest.

```text
QA decision: FAILED (3 genuine backend defects remain; coverage gate now passes)
Merge status: Blocked on the 3 defects above, not on coverage
Corrective issue: #69 must remain open until routes/seeding/header are fixed
```

## HISTORICAL — Test Case Results (2026-08-20 run, SUPERSEDED)

> **Superseded.** The `Fail` rows below (AUTH-01, AUTH-02, AUTH-08) reflect the
> 2026-08-20 run. All three pass on current `main` — see the FINAL VERIFICATION
> section above. AUTH-01's original expected result ("public registration is
> absent") is itself stale: public registration is contractual after PR #134.
> Retained as historical evidence only.

**Update (2026-08-20):** AUTH-16's automated test was removed as a
consolidation (see the FINAL Retest Result section above) — the same
invariant is proven more strongly at API level by AUTH-06. The row is kept
below for historical traceability rather than deleted.

| Test ID | Matrix trace | API / component | Input or action | Expected result | Automated test | Actual result | Result |
|---|---|---|---|---|---|---|---|
| AUTH-01 | S1-G01, S1-5101 | Runtime routes | Inspect registered methods and paths | Canonical `/api/v1/auth/login` and `/api/v1/auth/me` exist; public registration and legacy paths are absent | `tests/api/features/auth/test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes` | Failed. The canonical authentication routes are present, but forbidden legacy or public routes remain registered, including `GET /api/v1/me`, `POST /api/v1/login`, `POST /api/v1/register` and `POST /api/v1/auth/register`. | Fail |
| AUTH-02 | S1-5101 | Application startup | Start non-test app with the seeding function observed | Startup does not create demo or privileged accounts implicitly | `tests/api/features/auth/test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly` | Failed. `seed_database()` was called once during application startup. | Fail |
| AUTH-03 | S1-5101 | Login | Active provisioned citizen with correct credentials | 200; safe token response, canonical role and ward; last login updated | `tests/api/features/auth/test_auth_login.py::test_valid_login_returns_canonical_safe_response_and_updates_last_login` | Passed. Login returned the canonical safe response for the citizen account and updated the last-login value. | Pass |
| AUTH-04 | S1-G01, S1-5102 | Login | Wrong password, unknown, disabled and deleted accounts | All return the same generic 401 and no token; failed login does not update timestamp | `tests/api/features/auth/test_auth_login.py::test_invalid_account_states_use_one_generic_authentication_failure` | Passed. Wrong-password, unknown-account, disabled-account and deleted-account cases all returned the required generic `401 AUTHENTICATION_REQUIRED` response without a token. | Pass |
| AUTH-05 | S1-5101 | Login | Mixed-case email with surrounding spaces | 200 for the matching canonical account | `tests/api/features/auth/test_auth_login.py::test_login_email_is_trimmed_and_case_insensitive` | Passed. The submitted email was trimmed and matched case-insensitively. | Pass |
| AUTH-06 | S1-G03, R4 | Login validation | Invalid or missing fields and password over 72 UTF-8 bytes | 422 `VALIDATION_ERROR`; no submitted secret or internal detail in response | `tests/api/features/auth/test_auth_login.py::test_invalid_login_payload_returns_safe_validation_error` | Passed. Invalid email, blank password, missing fields and a password exceeding 72 UTF-8 bytes were rejected through the safe validation-error contract. | Pass |
| AUTH-07 | S1-G02, S1-5101 | Current user | Valid token for one of two users | 200; only the token owner's canonical public profile is returned | `tests/api/features/auth/test_auth_session.py::test_valid_token_returns_only_the_authenticated_users_public_profile` | Passed. The endpoint returned only the authenticated user's canonical public profile. | Pass |
| AUTH-08 | S1-G01, S1-G03 | Current user | Missing header, Basic scheme and malformed Bearer token | 401 `AUTHENTICATION_REQUIRED` with `WWW-Authenticate: Bearer` | `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge` | Failed. All three cases returned HTTP `401` with the expected safe error envelope and request ID, but every response omitted `WWW-Authenticate: Bearer`. | Fail |
| AUTH-09 | S1-G01 | Current user | Expired and wrong-signature tokens | 401; no profile or internal detail | `tests/api/features/auth/test_auth_session.py::test_expired_or_forged_token_is_rejected` | Passed. Expired and incorrectly signed tokens both returned `401 AUTHENTICATION_REQUIRED` without exposing a profile or internal details. | Pass |
| AUTH-10 | S1-G01 | Current user | Missing, malformed and unknown JWT subject | 401; malformed subject never becomes 500 | `tests/api/features/auth/test_auth_session.py::test_subject_claim_must_identify_an_existing_user` | Passed. Missing, malformed and unknown subjects all returned the controlled generic authentication failure; the malformed UUID subject did not escape as an unhandled exception. | Pass |
| AUTH-11 | S1-5102, S1-5105 | Current user | Token missing version or carrying stale version | 401; every session participates in revocation | `tests/api/features/auth/test_auth_session.py::test_token_version_is_required_and_stale_sessions_are_revoked` | Passed. Tokens with a missing or stale `token_version` were rejected through the generic authentication-failure path. | Pass |
| AUTH-12 | S1-5102 | Current user | Disable or soft-delete after token issue | Existing token returns generic 401 | `tests/api/features/auth/test_auth_session.py::test_account_state_change_revokes_an_existing_session` | Passed. Existing sessions for disabled and soft-deleted accounts were both revoked and returned the required generic `401 AUTHENTICATION_REQUIRED` response. | Pass |
| AUTH-13 | R4 | Password helper | Correct password, wrong password and malformed hashes | Salted hashes verify correctly and malformed hashes fail closed | `tests/unit/core/test_security.py::test_password_hash_is_salted_and_verification_fails_closed` | Passed. Password hashes were salted, correct passwords verified, wrong passwords were rejected and malformed hashes failed closed. | Pass |
| AUTH-14 | R4 | Password boundary | 72-byte and over-72-byte UTF-8 passwords | 72 bytes accepted; longer inputs rejected without truncation | `tests/unit/core/test_security.py::test_password_hashing_enforces_the_bcrypt_utf8_byte_limit` | Passed. The helper accepted the supported boundary and rejected a password exceeding 72 UTF-8 bytes. | Pass |
| AUTH-15 | S1-5102, S1-5105 | JWT helper | Create default and custom-expiry tokens | Subject, token version and expiry are correct | `tests/unit/core/test_security.py` | Passed. JWT helper tests for required claims and expiry completed successfully. | Pass |
| AUTH-16 | R4 | Login schema | Valid trimmed email and invalid input partitions | Valid input normalised; unsafe input raises validation error | Removed 2026-08-20; consolidated into AUTH-06, which proves the identical 5 input partitions through the full API stack plus the safe error envelope | Consolidated. Passed before removal; the invariant remains proven by AUTH-06. | Consolidated |

## Initial Execution Summary (Historical)

```text
Commit tested: Pending capture
Branch: test/SCRUM-88-auth-qa
Database: Disposable PostgreSQL database verdeza_test
Python: 3.12.3

Initial test collection:
33 tests collected before account-state parameterisation

Focused authentication test collection:
36 tests

Unit and contract result:
8 passed, 4 failed

Login API result:
8 passed, 3 failed

Login failures:
- canonical role mismatch: RESIDENT returned instead of CITIZEN
- disabled-account disclosure: 403 returned instead of generic 401
- password byte-limit validation: 401 returned instead of 422

Isolated invalid-account-state result:
3 passed, 1 failed
Failure: disabled-account returned 403 instead of 401

Session API result:
6 passed, 7 failed

Session failures:
- canonical role mismatch: RESIDENT returned instead of CITIZEN
- missing Authorization returned 403 instead of 401
- unsupported Basic scheme returned 403 instead of 401
- malformed Bearer response omitted WWW-Authenticate: Bearer
- malformed UUID subject raised an unhandled ValueError
- token without token_version was accepted with 200
- disabled account session returned distinguishable 403

Focused authentication result:
22 passed, 14 failed in 7.62s

Full backend result:
Pending execution

Coverage:
Not measured for focused runs using --no-cov

CI checks:
Pending

Initial confirmed defect groups:
8
```

## Initial Confirmed Defect Groups (Historical)

### AUTH-QA-01 — Passwords exceeding bcrypt's byte limit are accepted

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Resolved in current-main retest

#### Expected behaviour

Passwords longer than 72 UTF-8 bytes must be rejected before hashing or
authentication.

#### Actual behaviour

The password-hashing function and login request schema accepted a password
longer than 72 UTF-8 bytes. Neither raised the required validation error.

At API level, the over-limit password reached authentication and returned `401`
instead of being rejected with `422 VALIDATION_ERROR`.

#### Affected tests

```text
tests/unit/core/test_security.py::test_password_hashing_enforces_the_bcrypt_utf8_byte_limit

tests/unit/features/auth/test_auth_schemas.py::test_login_request_rejects_invalid_or_unsafe_input[password-over-bcrypt-byte-limit]

tests/api/features/auth/test_auth_login.py::test_invalid_login_payload_returns_safe_validation_error[password-over-bcrypt-byte-limit]
```

#### Risk

Silently accepting an over-limit password may cause bcrypt to ignore bytes
outside its supported boundary. Distinct submitted passwords could therefore
be treated as equivalent.

#### Required correction

Validate the UTF-8 encoded password length before hashing.

Reject values greater than 72 bytes in:

- the authentication request schema;
- the password-hashing helper.

The API must return `422 VALIDATION_ERROR` without exposing the submitted
password or internal details.

---

### AUTH-QA-02 — Runtime authentication routes do not match the approved contract

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Still failing; canonical routes now exist, but forbidden legacy/public routes remain

#### Expected behaviour

The application must expose:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

Unsupported public-registration and legacy authentication routes must not be
exposed.

#### Actual behaviour

The runtime route inventory did not contain the complete approved canonical
authentication route set.

#### Affected test

```text
tests/api/features/auth/test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes
```

#### Risk

The running backend, frontend integration, automated tests and Swagger contract
may use different paths, causing integration failures and inaccurate milestone
evidence.

#### Required correction

Register the authentication endpoints under `/api/v1/auth`.

Remove unsupported legacy or public-registration routes from the runtime API.

---

### AUTH-QA-03 — Application startup invokes account seeding automatically

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Still failing

#### Expected behaviour

Starting the FastAPI application must not automatically create or modify user
accounts.

Development or demonstration records must be created only through an explicit,
environment-guarded seed command.

#### Actual behaviour

`seed_database()` was called once when the application lifespan started through
`TestClient`.

#### Affected test

```text
tests/api/features/auth/test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly
```

#### Risk

Application startup can unexpectedly modify authentication data.

The impact becomes especially serious when predictable privileged credentials
are created outside a disposable development environment.

#### Required correction

Remove account seeding from the FastAPI application lifespan.

Provide a separate and explicit development seed command that refuses to run in
staging or production.

---

### AUTH-QA-04 — Authentication responses return a non-canonical public role value

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Resolved in current-main retest

#### Expected behaviour

Successful authentication responses for a citizen must return the canonical
backend role value:

```text
CITIZEN
```

Presentation labels may be translated in the user interface, but they must not
replace the API contract value.

#### Actual behaviour

Both the successful login response and the authenticated current-user profile
returned:

```text
RESIDENT
```

The endpoints returned HTTP `200`, but the public responses did not follow the
approved role vocabulary.

#### Affected tests

```text
tests/api/features/auth/test_auth_login.py::test_valid_login_returns_canonical_safe_response_and_updates_last_login

tests/api/features/auth/test_auth_session.py::test_valid_token_returns_only_the_authenticated_users_public_profile
```

#### Risk

Role values are used by API consumers for navigation, permissions and protected
feature access.

Different role vocabularies across the backend, frontend, OpenAPI contract and
tests can cause incorrect authorisation behaviour and integration failures.

#### Required correction

Return the canonical `Role` enum value from every authentication API response,
including login and current-user profile responses.

The frontend may map `CITIZEN` to a user-facing label, but the transport value
must remain canonical.

---

### AUTH-QA-05 — Disabled accounts expose account state during authentication

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Resolved in current-main retest

#### Expected behaviour

Wrong passwords, unknown accounts, disabled accounts and deleted accounts must
all return the same generic authentication failure:

```text
HTTP 401
AUTHENTICATION_REQUIRED
```

Login must use the generic message:

```text
Invalid email or password.
```

Existing sessions for disabled or deleted accounts must also fail with a generic
`401 AUTHENTICATION_REQUIRED` response.

#### Actual behaviour

During login, the disabled-account case returned:

```text
HTTP 403 Forbidden
```

with a suspension-specific response instead of the same generic `401` used for
wrong-password, unknown-account and deleted-account cases.

During session validation, a disabled account's existing token also returned
HTTP `403` with:

```text
This account has been suspended by an administrator.
```

The soft-deleted account's existing token was rejected with the required generic
`401`.

#### Affected tests

```text
tests/api/features/auth/test_auth_login.py::test_invalid_account_states_use_one_generic_authentication_failure[disabled-account]

tests/api/features/auth/test_auth_session.py::test_account_state_change_revokes_an_existing_session[disabled]
```

#### Risk

An attacker can compare responses and determine that an email or token belongs
to a real but disabled account.

This creates account-enumeration and account-state disclosure risk and makes
authentication failures inconsistent across login and session validation.

#### Required correction

Handle disabled accounts through the same public authentication-failure path
used for unknown, deleted and invalid-credential cases.

The public response must use the same HTTP status, public error code, generic
message and response structure. The server may record the internal reason in
protected logs, but it must not expose that reason to the client.

---

### AUTH-QA-06 — Protected endpoints use inconsistent Bearer authentication failures

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Still failing; HTTP status is corrected, but the Bearer challenge header remains absent

#### Expected behaviour

Missing credentials, unsupported authentication schemes and malformed Bearer
tokens must all return:

```text
HTTP 401
AUTHENTICATION_REQUIRED
WWW-Authenticate: Bearer
```

The response must use the standard public error envelope and expose no internal
details.

#### Actual behaviour

A request without an Authorization header returned HTTP `403`.

A request using the Basic scheme returned HTTP `403`.

A malformed Bearer token returned HTTP `401`, but the response omitted:

```text
WWW-Authenticate: Bearer
```

#### Affected test

```text
tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge
```

#### Risk

Inconsistent authentication responses break the protected-endpoint contract,
produce unreliable client behaviour and make security failures harder to
monitor and test consistently.

#### Required correction

Route missing, unsupported and malformed credentials through one authentication
failure handler.

Return `401 AUTHENTICATION_REQUIRED` with `WWW-Authenticate: Bearer` for every
Bearer authentication failure.

---

### AUTH-QA-07 — Malformed JWT subject causes an unhandled UUID conversion error

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Resolved in current-main retest

#### Expected behaviour

A token subject that is missing, malformed or does not identify an existing user
must return a generic:

```text
HTTP 401
AUTHENTICATION_REQUIRED
```

Malformed input must never escape as an unhandled server exception.

#### Actual behaviour

Missing-subject and unknown-user tokens returned the required `401`.

A validly signed token containing:

```text
sub = not-a-uuid
```

raised:

```text
ValueError: badly formed hexadecimal UUID string
```

instead of returning a controlled authentication response.

#### Affected test

```text
tests/api/features/auth/test_auth_session.py::test_subject_claim_must_identify_an_existing_user[malformed-subject]
```

#### Risk

A crafted token can trigger an unhandled exception, causing a server error,
unnecessary error logging and avoidable availability risk on a protected
endpoint.

#### Required correction

Parse the JWT subject inside the guarded authentication block.

Treat `JWTError`, `ValueError` and `TypeError` as authentication failures and
return the standard generic `401 AUTHENTICATION_REQUIRED` response.

---

### AUTH-QA-08 — Access tokens without token_version are accepted

**Severity:** High
**Initial status:** Confirmed in initial execution
**Current retest status:** Resolved in current-main retest

#### Expected behaviour

Every access token must contain a valid `token_version` claim matching the
current user's stored token version.

A token with a missing, malformed or stale version must return:

```text
HTTP 401
AUTHENTICATION_REQUIRED
```

#### Actual behaviour

A stale token version was rejected correctly.

A token without the `token_version` claim was accepted and returned HTTP `200`
with the user's profile.

#### Affected test

```text
tests/api/features/auth/test_auth_session.py::test_token_version_is_required_and_stale_sessions_are_revoked[missing-version]
```

#### Risk

A token without a version claim does not participate in the application's
session-revocation mechanism.

This can allow an otherwise valid token to remain usable when account disablement
or a role change should invalidate existing sessions.

#### Required correction

Require `token_version` during token validation and verify that it is a valid
integer equal to the user's current stored value.

Reject missing, malformed and stale versions with the same generic
`401 AUTHENTICATION_REQUIRED` response.

## Initial QA Conclusion (Historical)

The initial execution was not accepted because eight defect groups were confirmed.

```text
Initial result: Failed
Executed groups: unit, contract, login and session
Initial focused authentication result: 22 passed, 14 failed in 7.62s
Initial confirmed defect groups: 8
Initial session result: 6 passed, 7 failed
Full backend regression at that time: Pending
Retest status at that time: Pending production corrections
```

The expected results were not weakened merely to make the tests pass.

## HISTORICAL — Interim Retest (2026-08-02, superseded by FINAL Retest Result above)

The original authentication execution remains preserved above as historical evidence.

The QA branch was updated from current `main`, the stored SCRUM-88 tests were restored, and the
focused authentication suite was rerun against the disposable PostgreSQL test database.

```text
Repository HEAD before restored QA changes: 7163d4d
Branch: test/SCRUM-88-auth-qa
Execution date: 2026-08-02
Focused suite: 33 passed, 5 failed
Collected: 38
Errors: 0
Skipped: 0
Duration: 8.11 seconds
JUnit XML: SCRUM88_Auth_Retest/scrum88-auth-junit.xml
Pytest output: SCRUM88_Auth_Retest/scrum88-auth-pytest.txt
Working tree: restored SCRUM-88 QA changes were present and uncommitted during execution
```

### Current failing test cases

1. `tests/api/features/auth/test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes`
2. `tests/api/features/auth/test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly`
3. `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge[missing-authorization]`
4. `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge[unsupported-scheme]`
5. `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge[malformed-bearer-token]`

### Remaining confirmed root-cause groups

#### 1. Legacy or public authentication routes remain exposed

**Expected result:** Only the approved canonical authentication routes are exposed.

**Actual result:** The canonical routes exist, but one or more forbidden legacy or public routes
remain registered, including legacy login/profile routes and public registration routes.

**Result:** Fail

#### 2. Application startup still invokes account seeding

**Expected result:** Normal application startup must not create or seed known accounts implicitly.

**Actual result:** `seed_database` was called once during application startup.

**Result:** Fail

#### 3. Authentication failures omit the Bearer challenge header

**Expected result:** Missing, unsupported-scheme and malformed Bearer credentials return HTTP 401
with the safe authentication error envelope and `WWW-Authenticate: Bearer`.

**Actual result:** All three cases returned HTTP 401 with the expected safe error envelope and
request ID, but the `WWW-Authenticate` header was absent.

**Result:** Fail

### Current QA decision

```text
SCRUM-88 Authentication QA: FAILED
Latest focused suite: 33 passed, 5 failed
Focused-suite errors: 0
CI full-backend suite: 142 passed, 5 failed
CI test errors: 0
Coverage: 79.55%
Required coverage: 80%
Coverage gate: Failed
QA pull request: #81, Draft
Corrective issue: #69 must remain open or be reopened
Merge status: Blocked
```

The remaining five failing cases represent three product root causes. The complete CI regression
reproduced the same five failures and introduced no additional functional test failure. Expected
results were not weakened, skipped, suppressed or changed to obtain a passing result.

## HISTORICAL — CI Full-Backend Regression Result (commit `277caa7`, superseded)

GitHub Actions executed the complete backend suite against QA commit `277caa7`.

```text
Pull request: #81
Branch: test/SCRUM-88-auth-qa
Frontend check: Passed
API contract check: Passed
Backend check: Failed

Complete backend pytest result:
147 tests executed
142 passed
5 failed
0 errors
Coverage: 79.55%
Required coverage threshold: 80%
Duration: 14.83 seconds
```

The same five authentication failures reproduced in the complete GitHub Actions run:

1. `tests/api/features/auth/test_auth_contract.py::test_runtime_exposes_only_the_approved_authentication_routes`
2. `tests/api/features/auth/test_auth_contract.py::test_application_startup_does_not_seed_accounts_implicitly`
3. `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge[missing-authorization]`
4. `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge[unsupported-scheme]`
5. `tests/api/features/auth/test_auth_session.py::test_missing_or_malformed_authorization_returns_bearer_challenge[malformed-bearer-token]`

### CI failure classification

The five failing test cases still represent three confirmed root-cause groups:

1. Forbidden legacy or public authentication routes remain exposed.
2. Application startup still invokes `seed_database()`.
3. Missing, unsupported-scheme and malformed Bearer credentials omit
   `WWW-Authenticate: Bearer`.

No additional functional test failure was observed outside these already documented authentication
groups.

The coverage gate also failed because the exact measured coverage was `79.55%`, below the required
`80%`. The coverage result is recorded as a separate merge blocker and is not treated as another
authentication defect.

### CI decision

```text
Functional authentication result: Failed on five confirmed requirement tests
Coverage gate: Failed at 79.55%
Frontend check: Passed
API contract check: Passed
Backend check: Failed
QA pull request status: Draft
Corrective issue: #69 must remain open or be reopened
Merge status: Blocked
```

PR `#81` must remain Draft. It must not be merged until the three remaining authentication
root causes are corrected, the focused authentication suite passes, and the complete backend
regression and required CI checks pass.

No expected result was weakened, skipped, suppressed or changed to make CI pass.

**Update (2026-08-12):** the coverage gate referenced above (`79.55%`, Failed) is historical.
The FINAL Retest Result section at the top of this document shows current `main` now measures
`81.75%` coverage on the full backend suite, which passes the `80%` gate. Coverage is no longer
a merge blocker; the three functional authentication defects are the only remaining blockers.
