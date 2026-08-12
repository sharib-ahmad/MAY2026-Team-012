# PR #88/#89 Focused QA Evidence

**Feature:** PR #88 (EcoBot widget + citizen account deletion, SCRUM-207) and
PR #89 (collector route optimization service, Story 7.3)
**Branch under test:** `test/pr-88-89-qa`
**Execution rule:** Expected results are fixed before execution. Actual Result and
Result are recorded only from local pytest execution against the disposable
PostgreSQL test database. This document follows the same evidence format used by
`docs/qa/scrum-88-auth-test-evidence.md`, `docs/qa/scrum-173-admin-test-evidence.md`
and `docs/qa/scrum-174-manager-test-evidence.md`.

## FINAL Retest Result

`origin/main` was merged into `test/pr-88-89-qa`. One merge conflict occurred in
`tests/unit/features/collection_ops/test_route_optimization.py` (both this branch and
`main` had independently extended the same file for issue #99/#100 regression
coverage). It was resolved by keeping every test function from both sides — nothing
from either side was deleted — and renaming the one genuine name collision
(`test_collector_route_response_reports_distance_duration_and_degraded_notice` was
duplicated with different bodies; this branch's original schema-level version was kept
under its original name, and `main`'s stronger behavioural version was kept under the
new name `test_get_collector_route_reports_actual_degraded_notice_values`).

```text
Branch: test/pr-88-89-qa
Commit tested: 4daf411 (merge of origin/main HEAD b9fdbef, PR #110)
Execution date: 2026-08-13

Focused suite (the 5 scoped files below):
24 passed, 1 failed, 25 collected, 0 errors

Full backend suite:
237 passed, 1 failed, 238 collected, 0 errors
Coverage: 82.73% (gate: >= 80%) -> PASSED

Ruff check (focused + repo-wide): All checks passed
Ruff format --check (focused + repo-wide): all files already formatted
python -m compileall app tests alembic: clean
alembic check: No new upgrade operations detected
```

Scoped files (matches the current branch diff against `origin/main`, same set as the
originally known scope):

```text
backend/tests/api/features/collection_ops/test_collector_route_api.py
backend/tests/api/features/users/test_user_api.py
backend/tests/unit/features/collection_ops/test_route_optimization.py
backend/tests/unit/features/users/test_chatbot.py
backend/tests/unit/features/users/test_delete_account.py
```

The one remaining failure is a genuine, reproduced backend defect (issue #99 — Story
7.3 AC2). It is not a test error: the backend has no "fewer than 2 mapped points"
guard anywhere in `app/features/collection_ops/router.py`, so
`get_collector_route` silently returns a partial/empty result instead of rejecting the
request with "At least 2 mapped collection points are needed" as AC2 requires. No
expected result was weakened, skipped, xfailed, or suppressed.

The corresponding issue #100 regression (route response must report total distance,
estimated duration and a degraded-routing notice — Story 7.3 AC1/AC3) is now
**resolved**: both the original schema-level test and `main`'s stronger
value-level test pass against current `main`.

**Documentation discrepancy found (reported, not silently corrected):** `user-stories.txt`
Story 7.3 AC1/AC3 describes the external routing call as "the OSRM public API". The
actual implementation (`app/features/collection_ops/ors_client.py:47`) calls
`https://api.openrouteservice.org/optimization` — OpenRouteService (ORS), not OSRM. The
test suite and code (`ORS_API_KEY`, `ORSClient`) consistently use the ORS name. This is
flagged here for the Part C API-integration documentation pass; it is not something a
test file can silently "fix" without misrepresenting what the code actually calls.

## Test cases

| Test ID | Story / AC | API being tested | Inputs / Action | Expected Output | Actual Output | Result | Pytest node |
|---|---|---|---|---|---|---|---|
| PR101-01 | SCRUM-207 | `DELETE /api/v1/user/account` | Citizen deletes own account end-to-end (register, populate data, delete, verify) | `200`; account soft-deleted, login subsequently rejected, audit row recorded | Matched expected; full workflow passed | Pass | `tests/api/features/users/test_user_api.py::test_delete_citizen_account_api_workflow` |
| PR101-02 | SCRUM-207 | `POST /api/v1/user/chatbot/message` | Citizen sends a chatbot message (Gemini call mocked) | `200`; safe canonical chatbot reply | Matched expected | Pass | `tests/api/features/users/test_user_api.py::test_chatbot_api_workflow` |
| PR101-03 | R1 | Citizen-only endpoints (`account` delete, `chatbot/message`) | No Authorization header | `401 AUTHENTICATION_REQUIRED` | Matched expected for both endpoints | Pass | `tests/api/features/users/test_user_api.py::test_citizen_only_endpoints_reject_unauthenticated` |
| PR101-04 | R1 | Citizen-only endpoints | Authenticated as a non-citizen role | `403 FORBIDDEN` | Matched expected for both endpoints | Pass | `tests/api/features/users/test_user_api.py::test_citizen_only_endpoints_reject_non_citizen_role` |
| PR101-05 | Story 7.2 AC1/AC4 | `GET` collector route/map | Two collectors on different routes in the same ward | Each worker's route only returns their own assigned stops | Matched expected | Pass | `tests/api/features/collection_ops/test_collector_route_api.py::test_collector_route_only_returns_own_assigned_stops` |
| PR101-06 | — | `decode_polyline` helper | Encoded ORS polyline string | Correctly decoded lat/lng point list | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_decode_polyline` |
| PR101-07 | Story 7.3 AC1 | `ORSClient.optimize_route` | Mocked ORS HTTP response | Parses optimized job order and geometry | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_ors_client_optimize_route` |
| PR101-08 | Story 7.3 AC3 | `get_collector_route` | No `ORS_API_KEY` configured | Falls back to Haversine nearest-neighbour, straight-line polyline | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_fallback_nearest_neighbor` |
| PR101-09 | Story 7.3 AC1 | `get_collector_route` | `ORS_API_KEY` configured, ORS call succeeds | Stops reordered by ORS `optimized_indices`; road-following polyline returned | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_ors_success_orders_by_optimized_indices` |
| PR101-10 | Story 7.3 AC2 | `get_collector_route` | Fewer than 2 geo-coded points | Rejected with "At least 2 mapped collection points are needed", no ORS call | **Not raised** — request succeeds with a partial result instead of being rejected | **Fail** | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_rejects_fewer_than_two_geocoded_points` |
| PR101-11 | Story 7.3 AC1/AC3 | `CollectorRouteResponse` schema | Field-name introspection | Response model exposes distance/duration/degraded-notice fields | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_collector_route_response_reports_distance_duration_and_degraded_notice` |
| PR101-12 | Story 7.3 AC3 | `get_collector_route` | ORS configured but `urlopen` raises `URLError` | Falls back without crashing; same nearest-neighbour/straight-line output | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_falls_back_when_ors_raises` |
| PR101-13 | Story 7.3 AC2 (main's version, kept alongside PR101-10) | `get_collector_route` | 0 stops, then 1 stop | Returns gracefully with `pickup_count` 0 or 1, no exception | Matched (backend does not raise — same underlying gap as PR101-10, viewed from the "accepts" side) | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_handles_fewer_than_two_geocoded_points` |
| PR101-14 | Story 7.3 AC1/AC3 | `get_collector_route` | 1 stop, no ORS key | `total_distance_km`, `estimated_duration_min`, `is_degraded is True`, `degraded_notice` contains "Road routing service unavailable" | Matched expected exactly | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_reports_actual_degraded_notice_values` |
| PR101-15 | SCRUM-207 | Chatbot tool registry | Inspect registered tool functions | Expected pickups/tickets/impact/reuse tools registered | Matched expected | Pass | `tests/unit/features/users/test_chatbot.py::test_chatbot_tools_registered` |
| PR101-16 | SCRUM-207 | Chatbot tools | Mocked DB queries for pickups, tickets, impact/credits, reuse items | Each tool returns the expected structured summary | Matched expected for all 4 tools | Pass | `tests/unit/features/users/test_chatbot.py::test_get_my_pickups_mocked`, `test_get_my_tickets_mocked`, `test_get_my_impact_and_credits_mocked`, `test_get_my_reuse_items_mocked` |
| PR101-17 | SCRUM-207 | Chatbot maintenance mode | `GEMINI_API_KEY` missing | Safe maintenance-mode reply, no crash | Matched expected | Pass | `tests/unit/features/users/test_chatbot.py::test_chatbot_maintenance_mode_when_api_key_missing` |
| PR101-18 | SCRUM-207 | Chatbot Gemini call | Mocked Gemini HTTP error response | Safe generic reply, no internal detail leaked | Matched expected | Pass | `tests/unit/features/users/test_chatbot.py::test_chatbot_replies_gracefully_when_gemini_returns_error` |
| PR101-19 | SCRUM-207 | Delete-account service logic | Citizen with a zone/manager present | Account soft-deleted, audit log written with actor and timestamp | Matched expected | Pass | `tests/unit/features/users/test_delete_account.py::test_delete_account_logic` |
| PR101-20 | SCRUM-207 | Delete-account service logic | Citizen whose zone has no assigned manager | Deletion still completes safely without an unhandled error | Matched expected | Pass | `tests/unit/features/users/test_delete_account.py::test_delete_account_without_zone_manager` |

`SCRUM-207` (EcoBot widget and citizen account deletion) is not one of the 8 epics in
the attached `user-stories.txt`; it is referenced here only via the story ID used in
the repository's own commit history (`25290be feat(SCRUM-207): implemented EcoBot
widget and citizen account deletion (#88)`) since the authoritative user-stories
document does not define its acceptance criteria.

## FINAL EXECUTION SUMMARY

```text
PR: #101
Branch: test/pr-88-89-qa
Commit tested: 4daf411 (main merged at HEAD b9fdbef, PR #110)
Date: 2026-08-13
Relevant user story / AC: Story 7.2 AC1/AC4, Story 7.3 AC1/AC2/AC3, SCRUM-207 (PR #88 scope)

Focused command:
python -m pytest --no-cov -q \
  tests/api/features/collection_ops/test_collector_route_api.py \
  tests/api/features/users/test_user_api.py \
  tests/unit/features/collection_ops/test_route_optimization.py \
  tests/unit/features/users/test_chatbot.py \
  tests/unit/features/users/test_delete_account.py

Focused result: 24 passed, 1 failed, 25 collected, 0 errors

Full backend command:
python -m pytest -q --junitxml=pytest-junit.xml

Full backend result: 237 passed, 1 failed, 238 collected, 0 errors
Coverage: 82.73% (gate >= 80%: PASSED)
Ruff check: All checks passed (focused + repo-wide)
Ruff format --check: all files already formatted (focused + repo-wide)
python -m compileall: clean
alembic check: No new upgrade operations detected

Remaining genuine failure: 1
- tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_rejects_fewer_than_two_geocoded_points
  Story 7.3 AC2 (minimum-point guard) is not implemented in
  app/features/collection_ops/router.py — no "At least 2 mapped collection points
  are needed" rejection exists anywhere in the module.
Associated defect: issue #99 (tracked historically alongside issue #100, which is now
resolved on main).
```

No expected result was weakened, skipped, xfailed, or suppressed to obtain this
result. PR #101 remains QA-complete for its scoped diff with one genuine, reproduced
backend gap (#99) still open.
