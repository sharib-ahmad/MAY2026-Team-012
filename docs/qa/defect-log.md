# Defect Log — Verdeza

Defects are filed as GitHub Issues or tracked through the corresponding Jira
work item. This file is the milestone-facing summary and is updated before each
submission.

## Life Cycle

`New → Triaged → In Progress → Ready for Retest → Closed`

Additional transitions:

- `Triaged → Rejected`
- `Ready for Retest → Reopened`

Two rules apply:

1. **Only the tester closes a defect.** The developer moves it to
   `Ready for Retest`.
2. **Every closed defect leaves a regression test behind.** A defect that was
   possible once is possible again.

## Severity and Priority

Severity is set by the tester. Priority is set by the Scrum Master.

Keeping them separate prevents "how serious is this?" and "when should it be
fixed?" from being treated as the same question.

| Severity | Definition | Target |
|---|---|---|
| Critical | Data corruption, authorisation bypass, wrong credit or CO₂ value | Before the next merge to `main` |
| High | A core journey cannot be completed and no workaround exists | Within the sprint |
| Medium | The journey remains possible, but defined behaviour is incorrect | Within the sprint if capacity allows |
| Low | Cosmetic or minor usability issue | Backlog |

**Override:** A defect involving the credit ledger, authorisation scope, or a
lifecycle guard is Critical by default. It may be downgraded only with a written
reason. These defects can fail silently and produce incorrect data rather than
visible errors.

## Corrective Work

The following defects were identified from Sharib's review feedback on the
merged backend foundation PR #53.

All three corrections are tracked under:

- Parent work item: `SCRUM-120`
- Corrective Jira work item: `SCRUM-171`
- Jira title: `Correct backend integrity handling, readiness diagnostics, and migration settings`

PR #53 remains part of the project history and must not be reopened or
rewritten.

## Log

| ID | Title | Source | Severity | Priority | Expected Behaviour | Actual Behaviour | Corrective Jira Key | Corrective PR | Regression Tests | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| DEF-001 | Integrity errors were all reported as duplicate resources | Sharib's review of merged PR #53 | Medium | Set by Scrum Master | PostgreSQL integrity failures must be classified safely by SQLSTATE. Unique violations return `409 DUPLICATE_RESOURCE`, foreign-key violations return `409 CONFLICT`, recognised public check constraints return `422 VALIDATION_ERROR`, and unknown or internal violations return `500 INTERNAL_ERROR`. | Every SQLAlchemy `IntegrityError` was returned as `409 DUPLICATE_RESOURCE`, regardless of its SQLSTATE or constraint type. | `SCRUM-171` | TBD | `tests/unit/test_db_errors.py`<br>`tests/test_error_handling.py`<br>`tests/integration/test_zone_persistence.py` | In Progress |
| DEF-002 | Readiness logging discarded the database failure cause | Sharib's review of merged PR #53 | Medium | Set by Scrum Master | `/ready` must return a safe `503 DATABASE_UNAVAILABLE` for SQLAlchemy failures while retaining the request ID, exception type, and traceback in protected server logs. Non-SQLAlchemy programming errors must continue to the global `500 INTERNAL_ERROR` handler. | `/ready` caught every exception and logged only a generic readiness failure with the request ID. The exception type and traceback were lost, and programming errors could be misreported as database outages. | `SCRUM-171` | TBD | `tests/test_health.py` | In Progress |
| DEF-003 | Alembic unnecessarily required the application secret | Sharib's review of merged PR #53 | Medium | Set by Scrum Master | Alembic must load database-only configuration and operate with `DATABASE_URL` without requiring or validating the FastAPI application `SECRET_KEY`. FastAPI startup must remain fail-closed outside test. | Alembic imported the complete application settings, causing migration commands to fail when `SECRET_KEY` was missing or empty even though migrations did not use it. | `SCRUM-171` | TBD | `tests/unit/test_config_fails_closed.py`<br>`tests/integration/test_alembic_settings.py` | In Progress |
| DEF-004 | Public self-registration lets a caller provision itself as MUNICIPAL_OFFICER or SYSTEM_ADMIN | Found while reconciling `api-doc.yaml` against `main` for docs/sprint1-2-openapi-final (`backend/app/features/auth/router.py::register`, `backend/app/features/auth/router.py::ROLE_MAP_FRONTEND_TO_DB`) | Critical | Set by Scrum Master | Per Story 5.1, only a SYSTEM_ADMIN provisions MUNICIPAL_OFFICER/SYSTEM_ADMIN accounts, through the admin panel. `POST /api/v1/auth/register` is unauthenticated and public. | The `role` field on `POST /api/v1/auth/register` accepts `MANAGER`/`ADMIN` (or the raw `MUNICIPAL_OFFICER`/`SYSTEM_ADMIN` enum names) with no server-side restriction, letting any unauthenticated caller self-provision a staff account and receive a valid Bearer token for it immediately. | TBD | TBD | None yet | New |
| DEF-005 | Public reference-code tracking exposes citizen PII with no authentication or ownership check | Found while reconciling `api-doc.yaml` against `main` (`backend/app/api/v1/router.py::track_by_reference`) | Medium | Set by Scrum Master | Tracking a pickup/complaint/bulk-request by reference code should be scoped to the owning citizen, consistent with the authenticated equivalents (`GET /api/v1/user/pickups/{id}/tracking`). | `GET /api/v1/track/{reference}` requires no authentication and applies no ownership check; anyone who knows or guesses a reference code (a short, low-entropy string such as `TK-A1B2C3D4`) can read `citizen_name`, `zone_name`, `manager_name` and status. | TBD | TBD | None yet | New |
| DEF-006 | Reuse moderation queues return every ward's items when an officer has no assigned ward | Found while reconciling `api-doc.yaml` against `main` (`backend/app/features/reuse/service.py::list_manager_pending_donations`, `list_manager_pending_claims`, `list_manager_all_donations`) | Medium | Set by Scrum Master | Per R1, an officer's moderation queue must be scoped to their assigned ward(s) only, the same guard already applied to `assign_batch` after the #108 fix. | When `get_managed_zone_ids` returns an empty list (an officer with no ward assignment), the ward `.where(...)` filter is skipped entirely rather than yielding zero results, so the officer sees pending donations/claims from every ward. | TBD | TBD | None yet | New |

## Known Contract Gaps (not defects — never implemented)

Identified during the same reconciliation pass. These are not regressions in
working code; they are user-story scope that has no corresponding endpoint
on `main` at all, or that exists but under a materially different
lifecycle/trigger than the story describes. Recorded here so the gap is
visible without contradicting the defect life cycle above (there is nothing
to retest — there is no code path to exercise).

| Story | Gap |
|---|---|
| 1.1 | No ward-code, no-login schedule search exists. The only schedule endpoint (`GET /api/v1/user/daily-pickup-schedules`) requires citizen auth and returns only the caller's own stops. |
| 2.2 | No "Aging" flag or server-side pagination on the officer complaint grid (`GET /api/v1/manager/dashboard`), despite `COMPLAINT_AGING_THRESHOLD_DAYS` existing in configuration. |
| 3.1 | No sorting-guide endpoint exists; `sorting_guide/router.py` and `schemas.py` are empty stub files. |
| 4.2 | No endpoint sets a batch's `quality_status` or `contamination_note`. The DB check constraint requiring a note for `UNSAFE` is ready, but nothing can ever reach that state through the API. |
| 4.3 | No `Available → Claimed → Scheduled → Collected` transition guard exists; the real lifecycle is `assign → accept/reject → process`, and there is no recycler-initiated claim or auto-release timeout. |
| 7.1 | No endpoint updates a citizen's saved pickup coordinates after registration. |
| 7.3 | No minimum-point guard, upper-bound guard, or non-reentrant "Optimize" action; optimisation runs as a side effect of every `GET /api/v1/collector/route` call. |
| 8.1 | Credit award triggers on recycler batch processing, not pickup completion; `actual_weight` is never set by any endpoint, so estimated weight is always used; the factor is read at processing time, not frozen at an earlier completion; there is no reversal path on un-completion. |
| 8.2 | Badges are computed live from hardcoded thresholds on every request; the `badges`/`user_badges` tables (with a ready `(user_id, badge_id)` uniqueness constraint) are never written to. |

## Closure Requirements

A defect may move to `Ready for Retest` only when:

- the corrective implementation is complete;
- its focused regression tests pass;
- the complete backend test suite passes;
- the coverage requirement passes;
- the corrective pull request is opened and linked to `SCRUM-171`;
- the corrective pull request is linked from the relevant PR #53 review
  conversations.

The tester may move a defect to `Closed` only after verifying the corrected
behaviour from the corrective pull request or its merged commit.

## Metrics Reported per Milestone

- Defects found, grouped by severity
- Defects found per epic or platform area
- Escape rate: defects found after merge divided by total defects found
- Reopen rate: a high rate indicates that `Ready for Retest` is being used as
  "implementation complete" rather than "verified fix"
- Mean time from `New` to `Closed`, grouped by severity
