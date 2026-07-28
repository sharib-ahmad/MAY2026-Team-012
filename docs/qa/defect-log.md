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
