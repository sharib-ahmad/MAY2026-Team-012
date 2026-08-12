# SCRUM-194 Recycler Dashboard & Gamification QA Evidence

**Feature:** Recycler Dashboard & Gamification
**Related PR:** #86
**Branch under test:** `test/SCRUM-194-recycler-qa`
**Commit tested:** `f8aa790`
**Execution date:** 2026-08-11
**QA state:** Focused execution completed; product corrections and final retest pending

## Execution rule

Expected results were fixed before execution and were not changed to match the current implementation.
Actual Output, Database Effect, Result and Defect below are based only on the recorded pytest run against the disposable PostgreSQL test database.

## Test cases

| ID | Story / Rule | API or component | Input / action | Expected output | Expected database effect | Pytest coverage | Actual output | Database effect | Result | Defect |
|---|---|---|---|---|---|---|---|---|---|---|
| RCY-01 | Contract | Runtime route inventory | Inspect application routes | Recycler and manager batch routes exist under `/api/v1` | None | `tests/api/features/recycler/test_recycler_contract.py::test_runtime_exposes_manager_batch_routes` and `test_runtime_exposes_recycler_routes` | Passed. Runtime route inventory included all expected batch routes. | None | Pass | — |
| RCY-02 | Contract | Auth boundaries | Missing Bearer token on manager and recycler batch endpoints | `401` or `403` without processing state changes | No mutation | `tests/api/features/recycler/test_recycler_contract.py::test_missing_credentials_returns_401_or_403` | Passed. Missing credentials were rejected safely. | No state-changing handler was entered. | Pass | — |
| RCY-03 | Contract | Role enforcement | Citizen or collector hits manager/recycler routes; manager hits recycler routes | `403 FORBIDDEN` for cross-role access | None | `tests/api/features/recycler/test_recycler_contract.py::test_non_manager_cannot_access_manager_batch_endpoints` and `test_non_recycler_cannot_access_recycler_endpoints` | Passed. Role boundaries were enforced. | None | Pass | — |
| RCY-04 | Batch listing | Manager batch view | Manager lists batches in supervised ward | `200 OK` with list of collected batches | None | `tests/api/features/recycler/test_batch_lifecycle.py::test_manager_list_batches_with_data` | Passed. Manager list returns collected batches in ward. | Read-only query. | Pass | — |
| RCY-05 | Recycler listing | Active recyclers | Manager requests active recyclers | `200 OK` with active recycler users | None | `tests/api/features/recycler/test_batch_lifecycle.py::test_manager_list_recyclers` | Passed. Returns active recycler list. | Read-only query. | Pass | — |
| RCY-06 | Assignment | Batch assignment | Manager assigns collected batch to active recycler | `200 OK`; status becomes `ASSIGNED` | Batch assigned to recycler; recycler and citizen notifications created | `tests/api/features/recycler/test_batch_lifecycle.py::test_manager_assign_batch_success` | Passed. Batch assigned and notifications delivered. | Status updated to `ASSIGNED`, recycler and citizen notified. | Pass | — |
| RCY-07 | Authorization | Manager ward scoping | Unassigned manager assigns a batch | `403 Forbidden` | No batch mutation | `tests/api/features/recycler/test_batch_lifecycle.py::test_manager_without_managed_ward_cannot_assign_batch` | Failed. Response was `200 OK` instead of `403`. | Batch assigned despite officer having no managed ward. | Fail | RCY-QA-01 |
| RCY-08 | Lifecycle | Assignment status gate | Manager assigns non-COLLECTED batch | `409 Conflict` | No status change | `tests/api/features/recycler/test_batch_lifecycle.py::test_manager_assign_non_collected_batch` | Passed. Non-collected batch assignment rejected. | No mutation. | Pass | — |
| RCY-09 | Validation | Recycler validation | Manager assigns batch to disabled or nonexistent recycler | `422 Unprocessable Entity` | No assignment | `tests/api/features/recycler/test_batch_lifecycle.py::test_manager_assign_to_disabled_recycler` | Passed. Invalid recycler rejected. | No assignment persisted. | Pass | — |
| RCY-10 | Recycler listing | Recycler batch view | Recycler lists assigned batches | `200 OK` with only batches assigned to them | None | `tests/api/features/recycler/test_batch_lifecycle.py::test_recycler_list_batches` | Passed. Recycler sees only assigned batches. | Read-only query. | Pass | — |
| RCY-11 | Lifecycle | Recycler acceptance | Recycler accepts assigned batch | `200 OK`; status becomes `PROCESSING` | Batch and pickups move to `PROCESSING`; citizen notified | `tests/api/features/recycler/test_batch_lifecycle.py::test_recycler_accept_batch` | Passed. Acceptance updated status to processing. | Batch and pickup statuses updated; citizen notified. | Pass | — |
| RCY-12 | Authorization | Recycler batch boundary | Recycler accepts batch assigned to another recycler | `403 Forbidden` | No state change | `tests/api/features/recycler/test_batch_lifecycle.py::test_recycler_accept_other_batch` | Passed. Cross-recycler acceptance denied. | No mutation. | Pass | — |
| RCY-13 | Lifecycle | Recycler rejection | Recycler rejects assigned batch with note | `200 OK`; status reverts to `COLLECTED` | Batch unassigned, note saved, manager notified | `tests/api/features/recycler/test_batch_lifecycle.py::test_recycler_reject_batch` | Passed. Rejection unassigned batch and notified manager. | Status reverted to `COLLECTED`, recycler cleared, note saved. | Pass | — |
| RCY-14 | Boundary | Rejection note validation | Recycler rejects batch with whitespace-only note | `422 Unprocessable Entity` | Batch remains `ASSIGNED` | `tests/api/features/recycler/test_recycler_reject_whitespace_only_note` | Failed. Response was `200 OK` instead of `422`. | Whitespace note stored and batch unassigned. | Fail | RCY-QA-02 |
| RCY-15 | Lifecycle | Batch processing | Recycler processes processing batch | `200 OK`; status becomes `PROCESSED` | Credits awarded to citizens, CO2 saved computed, recycler notified | `tests/api/features/recycler/test_batch_lifecycle.py::test_recycler_process_batch` and `test_credits_awarded_on_process` | Passed. Processing awarded credits and completed batch. | Status set to `PROCESSED`, credits and CO2 saved recorded. | Pass | — |
| RCY-16 | Idempotency | Credit idempotency | Recycler re-processes already processed batch | `409 Conflict` | No duplicate credits created | `tests/api/features/recycler/test_gamification.py::test_credits_idempotent` | Passed. Re-processing blocked with 409 conflict. | No double-crediting. | Pass | — |
| RCY-17 | Fallback | Credit factor fallback | Process batch with category missing credit factor | `200 OK` with 0 credits and 0 CO2 | Graceful 0 credit record stored | `tests/api/features/recycler/test_gamification.py::test_missing_credit_factor_graceful_fallback` | Passed. Handled missing credit factor gracefully. | Zero credit record created without error. | Pass | — |
| RCY-18 | Integration | Batch pooling | Pickups reaching 30kg threshold auto-pool | Batch created when total weight >= 30kg | New `COLLECTED` batch created in DB | `tests/api/features/recycler/test_batch_pooling.py::test_collected_pickups_pool_at_thirty_kg` | Passed. Auto-pooling triggered at 30kg. | Batch created and pickups attached. | Pass | — |
| RCY-19 | Integration | Pooling isolation | Sub-threshold or mixed-category pickups pool | No batch created below 30kg or across categories | Pickups remain unbatched | `tests/api/features/recycler/test_batch_pooling.py::test_pooling_does_not_mix_categories_or_create_subthreshold_batch` | Passed. Category isolation and threshold enforced. | No batch created. | Pass | — |
| RCY-20 | Notifications | Recycler notifications | Recycler lists and marks notifications read | `200 OK`; notifications marked read | Notification `is_read` updated | `tests/api/features/recycler/test_recycler_notifications.py::test_list_recycler_notifications` and `test_mark_notification_read` | Passed. Notification management works. | Read status updated in DB. | Pass | — |
| RCY-21 | System journey | End-to-end recycler flow | Batch → assign → accept → process → credits | Full lifecycle completes seamlessly | Full transitive state matches expected flow | `tests/api/features/recycler/test_recycler_system.py::test_recycler_system_journey` | Passed. Full end-to-end journey succeeded. | Batch, pickup, credit, and notification state consistent. | Pass | — |

## Execution record

```text
Commit tested: f8aa790
Branch: test/SCRUM-194-recycler-qa
Base: main at f8aa790
Host: local development
Python: conda verdeza (3.12+)
PostgreSQL: 16.14
Database: Disposable PostgreSQL database ending in _test
Execution timestamp: 2026-08-11T23:42:00+00:00

Command:
cd backend
export APP_ENV=test
export DATABASE_URL=postgresql+psycopg://verdeza:verdeza@localhost:5433/verdeza_test
python -m pytest --no-cov -q tests/api/features/recycler --tb=short
```

| Metric | Count |
|---|---:|
| Collected | 84 |
| Passed | 82 |
| Failed | 2 |
| Errors | 0 |
| Skipped | 0 |
| Duration | ~41s |
| QA verdict | **Fail — 2 product defects** |

## Defect summary

| Defect | Severity | Priority | Summary | Affected test cases |
|---|---|---|---|---|
| RCY-QA-01 | High | P0 | Unassigned municipal officer can assign batches outside any ward | RCY-07 |
| RCY-QA-02 | Medium | P1 | Whitespace-only rejection notes are accepted and stored as empty after stripping | RCY-14 |

## Root cause analysis

- **RCY-QA-01:** `assign_batch` in `backend/app/features/materials/service.py` checks `if zone_ids and batch.zone_id not in zone_ids:`. When `get_managed_zone_ids` returns `[]` for an unassigned officer, the guard is bypassed (fail-open pattern).
- **RCY-QA-02:** `RejectBatchRequest` schema in `backend/app/features/materials/schemas.py` uses `Field(min_length=1)` which allows `" "`. The service trims it to `""` before saving.

## Final status

```text
SCRUM-194 Recycler Dashboard & Gamification QA: FAILED (2 product defects)
Focused suite: 82 passed, 2 failed (84 collected)
Full backend regression: Pending corrections
QA pull request: May be committed and pushed as Draft
```
