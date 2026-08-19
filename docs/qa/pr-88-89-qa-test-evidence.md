# PR #88/#89 Focused QA Evidence

**Feature:** PR #88 (EcoBot widget + citizen account deletion, SCRUM-207) and
PR #89 (collector route optimization service, Story 7.3)
**Branch under test:** `test/pr-88-89-qa`
**Execution rule:** Expected results are fixed before execution. Actual Result and
Result are recorded only from local pytest execution against the disposable
PostgreSQL test database. This document follows the same evidence format used by
`docs/qa/scrum-88-auth-test-evidence.md`, `docs/qa/scrum-173-admin-test-evidence.md`
and `docs/qa/scrum-174-manager-test-evidence.md`.

## Refinement Pass — 2026-08-20

This pass re-reviewed the suite against a clarified requirement interpretation
and the current `main` (`api-doc.yaml`, rebuilt in PR #111) rather than the
older assumptions the 2026-08-13 retest was written under. No production code
was changed; only the 5 scoped test files below were touched (plus this
document). Net: 25 -> 23 tests (2 removed, 1 renamed/strengthened, 3
strengthened in place).

**Story 7.2 vs 7.3 are one endpoint, not two.** `GET /api/v1/collector/route`
implements Story 1.4 (checklist), 7.2 (map pins) and 7.3 (optimisation)
together in a single call — confirmed directly in `api-doc.yaml`'s operation
description, which also states plainly: *"there is no minimum-point guard
(AC2 — fewer than 2 geocoded points silently skips optimisation rather than
returning a clear message)."* This means a 400/`HTTPException` for `<2` points
would break Story 7.2 (a worker with 0 or 1 mapped points must still see
them), and is not what the contract documents for this route (only
401/403/500 are declared). Accordingly:

- **Removed** `test_get_collector_route_rejects_fewer_than_two_geocoded_points`
  — it asserted `pytest.raises(HTTPException, match="At least 2 mapped
  collection points are needed")`, a status code/message the current contract
  does not require and directly contradicted the next test below (one
  expected an exception, the other expected a normal response for the same
  input shape). Keeping both was the genuinely contradictory pair this pass
  was asked to resolve.
- **Renamed/strengthened**
  `test_get_collector_route_handles_fewer_than_two_geocoded_points` ->
  `test_get_collector_route_below_minimum_points_never_calls_external_provider`.
  It keeps the original 0-point and 1-point sub-cases (no exception, points
  still shown — Story 7.2 preserved) and now also configures an
  `ORS_API_KEY` and mocks `urllib.request.urlopen` to assert the external
  routing provider is **never** called below the 2-point threshold — the
  concrete, contract-agnostic form of "must not call the routing provider"
  that doesn't require inventing a status code.
- **Removed** `test_collector_route_response_reports_distance_duration_and_degraded_notice`
  — it only introspected `CollectorRouteResponse.model_fields` for
  substring matches (`"distance" in name`), which passes even if the field
  is broken; the value-level test below already asserts the real numbers.
  Removing it is a duplicate-consolidation, not a coverage loss.
- **Strengthened** the three scenario tests that previously only checked
  ordering/geometry — `test_get_collector_route_fallback_nearest_neighbor`
  (no key), `test_get_collector_route_ors_success_orders_by_optimized_indices`
  (ORS succeeds), `test_get_collector_route_falls_back_when_ors_raises` (ORS
  raises) — to also assert `is_degraded`, `degraded_notice`,
  `total_distance_km` and `estimated_duration_min` for their respective
  scenario. Previously only the single "1 point, no key" test
  (`test_get_collector_route_reports_actual_degraded_notice_values`) checked
  these values at all; issue #100's regression protection now covers all
  three degraded/non-degraded paths, not just one.
- **No upper-bound (max-points) guard test was added.** Story 7.3 AC5
  describes one, but neither `app/features/collection_ops/router.py` nor
  `api-doc.yaml` implements or documents any such limit — writing a test for
  it would assert behaviour that doesn't exist and isn't promised anywhere,
  which is speculative, not regression protection. Flagged here as an
  uncovered AC rather than silently invented.
- **`test_user_api.py` setup no longer depends on `POST /api/v1/auth/register`.**
  `api-doc.yaml` documents this endpoint as a known contract defect: it lets
  an unauthenticated caller self-provision *any* role, including
  `MUNICIPAL_OFFICER`/`SYSTEM_ADMIN`, directly contradicting Story 5.1's
  admin-provisioned identity model (`docs/qa/endpoint-inventory.md` records
  it as "admin provisioning only"). Both
  `test_delete_citizen_account_api_workflow` and `test_chatbot_api_workflow`
  now provision their citizen directly via the ORM + `create_access_token`,
  the same stable mechanism every other test in this file (and
  `test_collector_route_api.py`) already uses. The one behavioural check that
  depended on register — "can the original email/phone be reused after
  deletion" — is preserved, but verified by inserting a second `User` row
  with the same email/phone directly rather than by calling the flagged
  endpoint again.
- **Chatbot tests reviewed for redundant tool-dispatch/registry coverage** per
  instruction; none found. `test_chatbot_tools_registered` checks the
  dispatch table is wired (a distinct wiring risk), the four `test_get_my_*_mocked`
  tests each check a different tool's own data-mapping logic, and the
  maintenance-mode/Gemini-error tests check two distinct failure paths of
  `execute_chatbot_turn`. None are left unchanged only for volume; no tests
  were added or removed in this file.
- **`test_collector_route_api.py` and `test_delete_account.py` were reviewed
  and left unchanged** — the former already provisions users via the ORM
  (no register dependency, no contradictions with the route-optimization
  suite); the latter's two tests (manager present / manager absent) protect
  distinct branches with no overlap to trim.
- Gemini and ORS remain fully mocked throughout; no live external calls were
  made at any point in this pass.

```text
Branch: test/pr-88-89-qa
Execution date: 2026-08-20

Focused suite (the 5 scoped files below):
23 collected, 22 passed, 1 failed, 0 errors

Full backend suite:
236 collected, 235 passed, 1 failed, 0 errors
Coverage: 82.73% (gate: >= 80%) -> PASSED

Ruff check (focused + repo-wide): All checks passed
Ruff format --check (focused + repo-wide): 157 files already formatted (repo), 5/5 scoped files already formatted
python -m compileall app tests alembic: clean (exit 0)
alembic check: No new upgrade operations detected
```

Scoped files (matches the current branch diff against `origin/main`):

```text
backend/tests/api/features/collection_ops/test_collector_route_api.py
backend/tests/api/features/users/test_user_api.py
backend/tests/unit/features/collection_ops/test_route_optimization.py
backend/tests/unit/features/users/test_chatbot.py
backend/tests/unit/features/users/test_delete_account.py
```

**The one remaining failure is a genuine, confirmed backend defect —**
`test_get_collector_route_below_minimum_points_never_calls_external_provider`.
With exactly 1 geocoded pending stop and an `ORS_API_KEY` configured,
`get_collector_route` still calls `ORSClient.optimize_route` (and therefore
`urllib.request.urlopen`) even though there's nothing to optimise between a
single point. `mock_urlopen.assert_not_called()` fails: the call happens once.
No expected result was weakened, skipped, xfailed, or suppressed to obtain
this result.

**GitHub issue #99 is marked "Resolved in PR #107," but the fix is not
present on current `main` — this is a regression, not a still-open original
bug.** Commit `8d14e29` (PR #107) added exactly this guard
(`if len(pending_with_coords) < 2: raise HTTPException(...)`) to
`router.py`. Commit `b9fdbef` (PR #110, "return route details and fallback
status") was authored as a sibling diff against the *same pre-#107 parent
blob* (`3bb8d97`) rather than on top of #107's change, and when it landed on
`main` the guard from #107 was silently dropped — it is absent from
`router.py` today and from `api-doc.yaml`'s own gap list for this endpoint.
Recommend **reopening #99** rather than filing a new issue, since the root
cause (no minimum-point guard) is identical to the original report; only the
mechanism this suite now checks for it (provider-not-called, not an
`HTTPException`) has changed, per the clarified interpretation that an
`HTTPException` here would itself break Story 7.2.

Issue #100 (distance/duration/degraded-notice reporting) remains resolved:
all three degraded/non-degraded scenarios (no key, ORS raises, ORS succeeds)
now assert real `total_distance_km`, `estimated_duration_min`, `is_degraded`
and `degraded_notice` values, and all pass.

**Documentation discrepancy (still open, reported not silently corrected):**
`user-stories.txt` Story 7.3 AC1/AC3 describes the external routing call as
"the OSRM public API." The actual implementation
(`app/features/collection_ops/ors_client.py:47`) and `api-doc.yaml`'s
`x-external-integrations` both consistently name OpenRouteService (ORS), not
OSRM. The test suite intentionally protects the real, provider-independent
*behaviour* (deterministic mocked HTTP call, optimized ordering, fallback on
failure) rather than asserting on which provider is named, so this
discrepancy does not affect test correctness — it's flagged here for the
API-documentation/user-stories reconciliation, not something a test file can
fix.

## Test cases

| Test ID | Story / AC | API being tested | Inputs / Action | Expected Output | Actual Output | Result | Pytest node |
|---|---|---|---|---|---|---|---|
| PR101-01 | SCRUM-207 | `DELETE /api/v1/user/account` | Citizen deletes own account end-to-end (ORM-provisioned citizen, populate data, delete, verify, verify email/phone reusable) | `200`; account soft-deleted, login subsequently rejected, audit row recorded, original email/phone reusable | Matched expected; full workflow passed | Pass | `tests/api/features/users/test_user_api.py::test_delete_citizen_account_api_workflow` |
| PR101-02 | SCRUM-207 | `POST /api/v1/user/chatbot/message` | Citizen (ORM-provisioned) sends a chatbot message (Gemini call mocked) | `200`; safe canonical chatbot reply | Matched expected | Pass | `tests/api/features/users/test_user_api.py::test_chatbot_api_workflow` |
| PR101-03 | R1 | Citizen-only endpoints (`account` delete, `chatbot/message`) | No Authorization header | `401 AUTHENTICATION_REQUIRED` | Matched expected for both endpoints | Pass | `tests/api/features/users/test_user_api.py::test_citizen_only_endpoints_reject_unauthenticated` |
| PR101-04 | R1 | Citizen-only endpoints | Authenticated as a non-citizen role | `403 FORBIDDEN` | Matched expected for both endpoints | Pass | `tests/api/features/users/test_user_api.py::test_citizen_only_endpoints_reject_non_citizen_role` |
| PR101-05 | Story 7.2 AC1/AC4 | `GET` collector route/map | Two collectors on different routes in the same ward | Each worker's route only returns their own assigned stops | Matched expected | Pass | `tests/api/features/collection_ops/test_collector_route_api.py::test_collector_route_only_returns_own_assigned_stops` |
| PR101-06 | — | `decode_polyline` helper | Encoded ORS polyline string | Correctly decoded lat/lng point list | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_decode_polyline` |
| PR101-07 | Story 7.3 AC1 | `ORSClient.optimize_route` | Mocked ORS HTTP response | Parses optimized job order and geometry | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_ors_client_optimize_route` |
| PR101-08 | Story 7.3 AC1/AC3 | `get_collector_route` | No `ORS_API_KEY` configured, 2 points | Falls back to Haversine nearest-neighbour, straight-line polyline, `is_degraded=True` with notice, distance/duration > 0 | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_fallback_nearest_neighbor` |
| PR101-09 | Story 7.3 AC1 | `get_collector_route` | `ORS_API_KEY` configured, ORS call succeeds, 2 points | Stops reordered by ORS `optimized_indices`; road-following polyline; `is_degraded=False`, no notice, distance/duration > 0 | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_ors_success_orders_by_optimized_indices` |
| PR101-10 | Story 7.3 AC2 / issue #99 | `get_collector_route` | Fewer than 2 geo-coded points (0, then 1), `ORS_API_KEY` configured | No exception (Story 7.2 preserved for 0/1 points); external routing provider (`urlopen`) never called | Points shown correctly, but `urlopen` **was called once** for the 1-point case | **Fail — BACKEND DEFECT** | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_below_minimum_points_never_calls_external_provider` |
| PR101-11 | Story 7.3 AC3 | `get_collector_route` | ORS configured but `urlopen` raises `URLError`, 2 points | Falls back without crashing; same nearest-neighbour/straight-line output; `is_degraded=True` with notice, distance/duration > 0 | Matched expected | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_falls_back_when_ors_raises` |
| PR101-12 | Story 7.3 AC1/AC3 | `get_collector_route` | 1 stop, no ORS key | `total_distance_km`, `estimated_duration_min`, `is_degraded is True`, `degraded_notice` contains "Road routing service unavailable" | Matched expected exactly | Pass | `tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_reports_actual_degraded_notice_values` |
| PR101-13 | SCRUM-207 | Chatbot tool registry | Inspect registered tool functions | Expected pickups/tickets/impact/reuse tools registered | Matched expected | Pass | `tests/unit/features/users/test_chatbot.py::test_chatbot_tools_registered` |
| PR101-14 | SCRUM-207 | Chatbot tools | Mocked DB queries for pickups, tickets, impact/credits, reuse items | Each tool returns the expected structured summary | Matched expected for all 4 tools | Pass | `tests/unit/features/users/test_chatbot.py::test_get_my_pickups_mocked`, `test_get_my_tickets_mocked`, `test_get_my_impact_and_credits_mocked`, `test_get_my_reuse_items_mocked` |
| PR101-15 | SCRUM-207 | Chatbot maintenance mode | `GEMINI_API_KEY` missing | Safe maintenance-mode reply, no crash | Matched expected | Pass | `tests/unit/features/users/test_chatbot.py::test_chatbot_maintenance_mode_when_api_key_missing` |
| PR101-16 | SCRUM-207 | Chatbot Gemini call | Mocked Gemini HTTP error response | Safe generic reply, no internal detail leaked | Matched expected | Pass | `tests/unit/features/users/test_chatbot.py::test_chatbot_replies_gracefully_when_gemini_returns_error` |
| PR101-17 | SCRUM-207 | Delete-account service logic | Citizen with a zone/manager present | Account soft-deleted, audit log written with actor and timestamp | Matched expected | Pass | `tests/unit/features/users/test_delete_account.py::test_delete_account_logic` |
| PR101-18 | SCRUM-207 | Delete-account service logic | Citizen whose zone has no assigned manager | Deletion still completes safely without an unhandled error | Matched expected | Pass | `tests/unit/features/users/test_delete_account.py::test_delete_account_without_zone_manager` |

`SCRUM-207` (EcoBot widget and citizen account deletion) is not one of the 8 epics in
the attached `user-stories.txt`; it is referenced here only via the story ID used in
the repository's own commit history (`25290be feat(SCRUM-207): implemented EcoBot
widget and citizen account deletion (#88)`) since the authoritative user-stories
document does not define its acceptance criteria.

## FINAL EXECUTION SUMMARY

```text
PR: #101
Branch: test/pr-88-89-qa
Date: 2026-08-20
Relevant user story / AC: Story 7.2 AC1/AC4, Story 7.3 AC1/AC2/AC3, SCRUM-207 (PR #88 scope)

Focused command:
python -m pytest --no-cov -q \
  tests/api/features/collection_ops/test_collector_route_api.py \
  tests/api/features/users/test_user_api.py \
  tests/unit/features/collection_ops/test_route_optimization.py \
  tests/unit/features/users/test_chatbot.py \
  tests/unit/features/users/test_delete_account.py

Focused result: 23 collected, 22 passed, 1 failed, 0 errors

Full backend command:
python -m pytest -q

Full backend result: 236 collected, 235 passed, 1 failed, 0 errors
Coverage: 82.73% (gate >= 80%: PASSED)
Ruff check: All checks passed (focused + repo-wide)
Ruff format --check: all files already formatted (focused + repo-wide)
python -m compileall: clean
alembic check: No new upgrade operations detected

Remaining genuine failure: 1 — BACKEND DEFECT
- tests/unit/features/collection_ops/test_route_optimization.py::test_get_collector_route_below_minimum_points_never_calls_external_provider
  Story 7.3 AC2 (minimum-point guard) is not implemented in
  app/features/collection_ops/router.py: with exactly 1 geocoded point and an
  ORS_API_KEY configured, the router still calls the external routing
  provider. Regression of issue #99's fix (PR #107), lost when PR #110 was
  merged on top of the same pre-#107 parent commit. Recommend reopening #99.
```

No expected result was weakened, skipped, xfailed, or suppressed to obtain this
result. PR #101 remains QA-complete for its scoped diff, with one genuine,
confirmed backend regression (#99, recommend reopening) still open. Merge
readiness: **the test suite itself is ready to merge** — every change is
test-only, no production code was touched, and the one failing test is
correctly documenting a real backend gap rather than a test defect.
