# Verdeza — Endpoint Inventory (Milestones 3 & 4)

Each endpoint is finalised in its feature PR's `api-doc.yaml` update
before or with implementation. External vocabulary: `/complaints`, `ward_code`;
internal table `tickets`, key `zone_id`.

> **Reconciliation note (docs/sprint1-2-openapi-final):** this inventory is
> the pre-implementation proposal and was not updated as the backend was
> built — a number of listed paths were never implemented under these names,
> and a number of implemented paths (the collector `/api/v1/collector/*`
> operations, `/api/v1/reuse/donations` and `/api/v1/reuse/claims`, the
> manager-push `/api/v1/manager/batches` and `/api/v1/recycler/batches`
> model, and citizen `/api/v1/user/impact` / `/api/v1/user/dashboard`) do not
> appear here at all. `api-doc.yaml` on `main` is the authoritative record of
> what actually ships; see `docs/qa/rtm.md`'s "Reconciliation" section for a
> table of the concrete divergences per story, and `docs/qa/defect-log.md`
> for the authorization and scoping defects found while reconciling the two.
> The external routing dependency is OpenRouteService, called from
> `GET /api/v1/collector/route`. The `POST /api/v1/routes/me/optimize` action
> named below does not exist under that path; since PR #124 the separate
> Optimize operation ships as `POST /api/v1/collector/route/optimize`.

## Conventions

- All application endpoints use the `/api/v1` prefix; operational probes stay outside it.
- Optional endpoints are labelled and excluded from the core sprint balance.
- Internal events are not counted as HTTP endpoints.

## Balance summary

| | Core endpoints |
|---|---|
| **Sprint 1 (Milestone 3)** | 21 business/support |
| **Sprint 2 (Milestone 4)** | 20 |
| **Operational probes** | 2 (not assigned to a sprint) |

Close to a 50/50 API split by count. Complexity remains heavier in Sprint 2
(route optimisation, material lifecycle, credit calculations, idempotency, ledger
correctness). Acceptance-criteria count alone is not treated as the 50/50 measure.

---

## Platform and operational endpoints

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/health` | Application liveness | Core |
| GET | `/ready` | Database/application readiness | Core |
| POST | `/api/v1/auth/login` | Authenticate a user | Core |
| GET | `/api/v1/auth/me` | Return the authenticated user, role, ward and saved pickup location | Core |
| POST | `/api/v1/auth/refresh` | Refresh access token | Optional — only if refresh-token design is used |

Operational probes are not assigned to a user-story sprint.

---

## Sprint 1 — Milestone 3 (21 core endpoints)

### Identity and supporting reference data

| # | Method | Path | Story/Area |
|---:|---|---|---|
| 1 | POST | `/api/v1/admin/users` | Story 5.1 |
| 2 | GET | `/api/v1/admin/users` | Story 5.1 |
| 3 | PATCH | `/api/v1/admin/users/{user_id}` | Story 5.1 |
| 4 | GET | `/api/v1/wards` | Supporting reference data |
| 5 | POST | `/api/v1/admin/wards` | Optional supporting endpoint (excluded from core count) |

### Sorting guide

| # | Method | Path | Story |
|---:|---|---|---|
| 6 | GET | `/api/v1/sorting-guide` | Story 3.1 |
| 7 | PUT | `/api/v1/admin/sorting-guide` | Story 3.1 |

### Schedule, bulk pickup, route progress, delay and waste issues

| # | Method | Path | Story |
|---:|---|---|---|
| 8 | GET | `/api/v1/schedules` | Story 1.1 |
| 9 | POST | `/api/v1/bulk-pickups` | Story 1.3 |
| 10 | GET | `/api/v1/bulk-pickups` | Story 1.3 |
| 11 | PATCH | `/api/v1/bulk-pickups/{bulk_pickup_id}` | Story 1.3 |
| 12 | GET | `/api/v1/routes/me` | Stories 1.4 and 7.2 |
| 13 | PATCH | `/api/v1/route-stops/{route_stop_id}/progress` | Story 1.4 |
| 14 | POST | `/api/v1/route-stops/{route_stop_id}/delays` | Story 1.5 |
| 15 | POST | `/api/v1/route-stops/{route_stop_id}/waste-issues` | Story 3.2 |
| 16 | GET | `/api/v1/waste-issues` | Story 3.2 |
| 17 | GET | `/api/v1/notifications/me` | Story 1.2 and shared in-app notifications |

`PATCH /bulk-pickups/{bulk_pickup_id}` documents role-controlled actions: citizen
cancels an eligible request; officer approves/rejects a pending request; the
server expires a stale pending request internally. No arbitrary fields or illegal
status transitions pass through.

### Complaints

| # | Method | Path | Story |
|---:|---|---|---|
| 18 | POST | `/api/v1/complaints` | Story 2.1 |
| 19 | GET | `/api/v1/me/complaints` | Citizen self-read (Stories 2.1, 2.3) |
| 20 | GET | `/api/v1/complaints` | Story 2.2 |
| 21 | PATCH | `/api/v1/complaints/{complaint_id}/resolution` | Story 2.3 |
| 22 | POST | `/api/v1/complaints/{complaint_id}/reopen` | Story 2.3 |

Reopen returns the complaint to `OPEN` (no stored `REOPENED` status unless the
team formally changes the lifecycle).

---

## Sprint 2 — Milestone 4 (20 core endpoints)

### Story 1.6 recycling transparency

| # | Method | Path | Story |
|---:|---|---|---|
| 1 | GET | `/api/v1/recycling-summary` | Story 1.6 |

Aggregates Epic 4 material-batch and dispatch information. **Sprint: Sprint 2.
Dependency: Epic 4 material-batch and dispatch-status data.**

### Material batches

| # | Method | Path | Story |
|---:|---|---|---|
| 2 | POST | `/api/v1/admin/material-batches` | Supporting Epic 4 write-side |
| 3 | GET | `/api/v1/material-batches` | Story 4.1 |
| 4 | POST | `/api/v1/material-batches/{material_batch_id}/claim` | Story 4.1 |
| 5 | PATCH | `/api/v1/material-batches/{material_batch_id}/quality` | Story 4.2 |
| 6 | PATCH | `/api/v1/material-batches/{material_batch_id}/pickup-status` | Story 4.3 |

### Civic reuse exchange

| # | Method | Path | Story |
|---:|---|---|---|
| 7 | POST | `/api/v1/reuse-listings` | Story 6.1 |
| 8 | GET | `/api/v1/reuse-listings` | Story 6.3 |
| 9 | PATCH | `/api/v1/reuse-listings/{listing_id}` | Stories 6.1 and 6.2 |
| 10 | POST | `/api/v1/reuse-listings/{listing_id}/claims` | Story 6.3 |
| 11 | PATCH | `/api/v1/reuse-claims/{claim_id}` | Story 6.4 |

`PATCH /reuse-listings/{listing_id}`: citizen owner withdraws a pending listing;
officer approves/rejects (rejection requires a note); illegal state changes are
rejected. `PATCH /reuse-claims/{claim_id}`: officer approves/rejects, enforcing
first-decision-wins.

### Location and route optimisation

| # | Method | Path | Story |
|---:|---|---|---|
| 12 | PUT | `/api/v1/users/me/location` | Story 7.1 (save); the saved pin is read back via `GET /api/v1/auth/me`, no separate endpoint |
| 13 | POST | `/api/v1/routes/me/optimize` | Story 7.3 |

```
External dependency: OpenRouteService, called only by the backend.
The frontend calls only the Verdeza endpoint. Response is provider-independent.
API key lives only in the backend env (OPENROUTESERVICE_API_KEY); never committed,
never returned, never in React.
```

### Eco-credit and badges

| # | Method | Path | Story |
|---:|---|---|---|
| 14 | GET | `/api/v1/admin/credit-factors` | Story 8.3 |
| 15 | PUT | `/api/v1/admin/credit-factors/{category}` | Story 8.3 |
| 16 | PATCH | `/api/v1/pickups/{pickup_id}/verification` | Story 8.1 |
| 17 | GET | `/api/v1/credits/me` | Story 8.1 |
| 18 | GET | `/api/v1/admin/credits/ledger` | Story 8.1 (admin view) |
| 19 | GET | `/api/v1/badges` | Story 8.2 |
| 20 | GET | `/api/v1/badges/me` | Story 8.2 |

```
Internal event (not an endpoint): credit award/reversal/restore evaluation runs
on pickup completion, un-completion, re-completion, or contamination clearance.
```

The worker route-progress operation (Sprint 1 #13) must accept `status`,
`actual_weight_kg`, and `contaminated` so credit processing can run on completion.

---

## Two implementation prerequisites (inside feature work)

1. **Sprint 1** must seed route / schedule / route-point / worker-assignment data
   before Stories 1.1, 1.4, 1.5 and 3.2 can operate.
2. **Sprint 2** must provide actual-weight entry before Story 8.1 — the credit
   calculation needs a verified `actual_weight_kg`.

---

## Explicitly removed / non-core 

```
POST  /api/v1/auth/register                 → admin provisioning only (Story 5.1)
POST  /api/v1/notifications/subscriptions   → MVP uses in-app notifications
GET   /api/v1/track/{code}                  → citizen self-read is sufficient
GET   /api/v1/routes                        → use /routes/me (worker-scoped)
GET   /api/v1/credits/ledger                → use /admin/credits/ledger
PATCH /api/v1/material-batches/{id}         → use /quality and /pickup-status
POST  /api/v1/routes/optimize               → use /routes/me/optimize
```

A dedicated schedule-delay endpoint is not core; the first implementation uses
the schedule response and/or `GET /notifications/me`.

---

## How this feeds the RTM and PRs

Each **user story or coherent feature slice** becomes a focused PR containing the
contract update, implementation, unit tests, tester's independent cases, frontend
integration, and RTM update — not one PR per endpoint. The RTM status column
tracks each: Planned — Sprint 1 / Planned — Sprint 2 / Implemented / Tested.
