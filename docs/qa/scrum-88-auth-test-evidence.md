# SCRUM-88 Authentication QA Evidence

**Feature:** Authentication platform used by Sprint 1 protected APIs
**Source matrix:** `docs/qa/sprint1-acceptance-matrix.md`
**Execution rule:** Expected results are fixed before execution. Actual Result and
Result are recorded only from local or CI execution.

## Current Test Results

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
| AUTH-16 | R4 | Login schema | Valid trimmed email and invalid input partitions | Valid input normalised; unsafe input raises validation error | `tests/unit/features/auth/test_auth_schemas.py::test_login_request_rejects_invalid_or_unsafe_input` | Passed. Valid input was normalised and all invalid or unsafe partitions, including the over-limit password, raised validation errors. | Pass |

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

## Current-Main Corrective Retest

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
Test errors: 0
Full backend regression: Pending corrective changes
QA pull request: Draft
Corrective issue: #69 (reopen required)
```

The remaining five failing cases represent three product root causes. Expected results were not
weakened, skipped, suppressed or changed to obtain a passing result.
