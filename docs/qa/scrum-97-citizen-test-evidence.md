# SCRUM-97 Citizen / Resident API QA Evidence

**Feature:** Story 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 8.1, 8.2 citizen portal and PR #97 resident APIs  
**Branch under test:** `test/SCRUM-97-citizen-api-tests`  
**Commit tested:** `0b83911`  
**Execution date:** 2026-08-01  
**Execution rule:** Expected results were fixed before execution. Actual Output, Result and Defect below are based only on the recorded pytest execution against the disposable PostgreSQL test database.

---

## Endpoint coverage

| Method | Approved endpoint | Purpose | Automated coverage |
|---|---|---|---|
| `POST` | `/api/v1/user/pickups` | Schedule bulk pickup | `test_citizen_pickups.py` |
| `GET` | `/api/v1/user/pickups` | List resident's pickups | `test_citizen_pickups.py` |
| `PATCH` | `/api/v1/user/pickups/{pickup_id}/cancel` | Cancel eligible pickup request | `test_citizen_pickups.py` |
| `GET` | `/api/v1/user/pickups/{pickup_id}/tracking` | Track pickup progress | `test_citizen_pickups.py` |
| `GET` | `/api/v1/user/pickup-options` | List active waste categories | `test_citizen_pickups.py` |
| `POST` | `/api/v1/user/tickets` | Create citizen complaint | `test_citizen_complaints.py` |
| `GET` | `/api/v1/user/tickets` | List citizen complaints | `test_citizen_complaints.py` |
| `GET` | `/api/v1/user/notifications` | List resident notifications | `test_citizen_impact_dashboard.py` |
| `PATCH` | `/api/v1/user/notifications/{notification_id}/read` | Mark notification as read | `test_citizen_impact_dashboard.py` |
| `GET` | `/api/v1/user/dashboard` | Citizen dashboard overview | `test_citizen_impact_dashboard.py` |
| `GET` | `/api/v1/user/impact` | Sustainability impact & badges | `test_citizen_impact_dashboard.py` |
| `GET` | `/api/v1/user/daily-pickup-schedules` | Resident daily collection schedules | `test_citizen_schedules.py` |
| Route inventory | Approved canonical vs unapproved legacy paths | Access control & contract compliance | `test_citizen_contract.py` |

---

## Test cases

| Test ID | Story / Rule | API endpoint | Request input / action | Expected output and database result | Automated pytest node | Actual output | Result | Defect |
|---|---|---|---|---|---|---|---|---|
| CIT-01 | S1-1301 | `POST /api/v1/user/pickups` | Citizen submits valid category, weight, scheduled date (>24h notice), time slot | `201 CREATED`; `ref_code` starting `BPR-`; status `PENDING`; notification created | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_create_pickup_happy_path` | Returned `201 CREATED` with valid UUID and `BPR-` reference code. | Pass | — |
| CIT-02 | S1-1302 | `POST /api/v1/user/pickups` | Invalid weight, negative weight, invalid time slot, < 24h notice | `422 VALIDATION_ERROR`; request rejected without database write | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_create_pickup_less_than_24h_notice_returns_422` | All parameter boundary cases returned `422` with validation error details. | Pass | — |
| CIT-03 | S1-1301 | `GET /api/v1/user/pickups` | Citizen requests scheduled pickups list | `200 OK`; list container with `pickups` array and `total` count | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_list_pickups_returns_resident_pickups` | Returned `200 OK` with paginated pickups container schema. | Pass | — |
| CIT-04 | S1-1304 | `PATCH /api/v1/user/pickups/{id}/cancel` | Citizen cancels a pending pickup request | `200 OK`; status `CANCELLED` | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_cancel_pending_pickup_succeeds` | Status updated to `CANCELLED` and returned `200`. | Pass | — |
| CIT-05 | S1-1304 | `PATCH /api/v1/user/pickups/{id}/cancel` | Citizen cancels non-existent pickup ID | `404 NOT_FOUND`; state remains unchanged | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_cancel_nonexistent_pickup_returns_404` | Returned `404 NOT_FOUND`. | Pass | — |
| CIT-06 | S1-3101 | `GET /api/v1/user/pickup-options` | Citizen requests active waste categories | `200 OK`; returns active categories (`PLASTIC`, `PAPER`); excludes `is_active=False` | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_pickup_options_excludes_inactive_categories` | Returned `200 OK` and correctly excluded inactive waste categories. | Pass | — |
| CIT-07 | S1-2101 | `POST /api/v1/user/tickets` | Citizen submits valid complaint ticket | `201 CREATED`; `ref_code` starting `TK-`; status `OPEN`; ward details populated | `tests/api/features/citizen/test_citizen_complaints.py::TestCitizenComplaints::test_create_ticket_happy_path` | Returned `201 CREATED` with ticket ref code and ward mapping. | Pass | — |
| CIT-08 | S1-2101 | `GET /api/v1/user/tickets` | Citizen lists complaints | `200 OK`; list of tickets including `ward_code` and `ward_manager_name` | `tests/api/features/citizen/test_citizen_complaints.py::TestCitizenComplaints::test_list_tickets_returns_user_tickets_with_ward_details` | Returned `200 OK` with populated ward code and manager name. | Pass | — |
| CIT-09 | S1-1201 | `GET /api/v1/user/notifications` | Citizen checks in-app notifications | `200 OK`; returns list of notification objects with `is_read` boolean | `tests/api/features/citizen/test_citizen_impact_dashboard.py::TestCitizenImpactDashboard::test_notifications_list_and_mark_read` | Returned `200 OK` and successfully marked notification read. | Pass | — |
| CIT-10 | S1-G04 | `GET /api/v1/user/dashboard` | Citizen loads main dashboard overview | `200 OK`; returns `pickups`, `impact`, `queue`, `flow` | `tests/api/features/citizen/test_citizen_impact_dashboard.py::TestCitizenImpactDashboard::test_dashboard_empty_state` | Returned `200 OK` with valid dashboard structure. | Pass | — |
| CIT-11 | S1-1301 | `GET /api/v1/user/impact` | Citizen requests sustainability analytics | `200 OK`; returns `total_kg_diverted`, `co2_saved_kg`, category breakdown, monthly trend | `tests/api/features/citizen/test_citizen_impact_dashboard.py::TestCitizenImpactDashboard::test_impact_multiple_categories_aggregation` | Returned `200 OK` with accurate aggregated weight and CO2 savings. | Pass | — |
| CIT-12 | S1-G02 | Protected `/api/v1/user/*` endpoints | Officer access to citizen routes | `403 FORBIDDEN`; access denied for non-citizen roles | `tests/api/features/citizen/test_citizen_contract.py::test_every_citizen_endpoint_rejects_non_citizen_roles` | All 12 parameter cases returned `403 FORBIDDEN`. | Pass | — |
| CIT-13 | S1-G01 | Protected `/api/v1/user/*` endpoints | Unauthenticated user calls endpoints | `403 FORBIDDEN`; access denied | `tests/api/features/citizen/test_citizen_contract.py::test_every_citizen_endpoint_rejects_missing_credentials_with_403` | All 12 parameter cases returned `403 FORBIDDEN`. | Pass | — |
| CIT-14 | S1-1301 | `POST /api/v1/user/pickups` | Citizen without assigned ward schedules pickup | `422 VALIDATION_ERROR`; `Assign a ward before scheduling` | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_citizen_without_ward_cannot_schedule_pickup` | Returned `422` error blocking wardless citizens. | Pass | — |
| CIT-15 | S1-2101 | `POST /api/v1/user/tickets` | Citizen without assigned ward raises complaint | `422 VALIDATION_ERROR`; `Assign a ward before raising a complaint` | `tests/api/features/citizen/test_citizen_complaints.py::TestCitizenComplaints::test_citizen_without_ward_cannot_raise_ticket` | Returned `422` error blocking wardless citizens. | Pass | — |
| CIT-16 | Cross-module | `POST /api/v1/user/pickups` | Citizen schedules pickup → check manager notifications | Ward Manager receives `New bulk pickup request` notification | `tests/api/features/citizen/test_citizen_pickups.py::TestCitizenBulkPickups::test_create_pickup_triggers_manager_notification` | Manager received cross-module notification containing `BPR-` reference code. | Pass | — |
| CIT-17 | Cross-module | `POST /api/v1/user/tickets` | Citizen raises complaint → check manager notifications | Ward Manager receives `New citizen complaint` notification | `tests/api/features/citizen/test_citizen_complaints.py::TestCitizenComplaints::test_create_ticket_triggers_manager_notification` | Manager received cross-module notification containing `TK-` reference code. | Pass | — |
| CIT-18 | S1-1101 | `GET /api/v1/user/daily-pickup-schedules` | Resident collection schedules & queue tracking | `200 OK`; returns daily pickup schedule order and completed stops | `tests/api/features/citizen/test_citizen_schedules.py::TestCitizenSchedules::test_daily_pickup_schedule_queue_tracking_journey` | Returned `200 OK` with collector schedule details. | Pass | — |

---

## Execution record

```text
Commit tested: 0b83911
Branch: test/SCRUM-97-citizen-api-tests
Host: DESKTOP-ZELI5M2
Database: Disposable PostgreSQL database ending in _test
Python: 3.11.15
PostgreSQL: 15.0
Execution timestamp: 2026-08-01T13:37:00+00:00

Command:
python -m pytest --no-cov -q tests/api/features/citizen

Collection:
51 tests

Focused citizen API result:
51 passed in 15.12s
0 errors
0 skipped

Current QA decision:
PASSED. SCRUM-97 citizen APIs are accepted for sign-off.
```

---

## Retest and sign-off rule

Sign-off status:
```text
SCRUM-97 Citizen API QA: PASSED
Focused suite: 51 passed, 0 failed
Full backend regression: Passed
```
