# ADR-0002: Feature-First Backend Modular Monolith

- Date: 2026-07-30
- Status: Accepted
- Scope: Backend application architecture for Milestones 3 and 4

## Context

The backend contains shared platform concerns such as configuration, database
sessions, error handling, health probes, migrations, and the shared `Zone`
reference model.

Milestones 3 and 4 introduce multiple business capabilities with distinct
models, lifecycle rules, permissions, persistence queries, and API endpoints.
The structure must keep these capabilities understandable and independently
testable without introducing unnecessary distributed-system or framework
complexity.

## Decision

The backend will use a feature-first modular monolith.

New business functionality is organised under `app/features/<feature>/`.
Shared platform concerns remain under `app/core/` and `app/db/`.

The architecture follows this dependency direction:

```text
router
  → service
    → repository
      → SQLAlchemy models and database session
```

Dependencies must not point in the opposite direction:

- models do not import repositories, services, or routers;
- repositories do not import services or routers;
- services do not import routers;
- feature routers are aggregated by `app/api/v1/router.py`;
- `app/main.py` includes the versioned API router once.

## Target Structure

The structure is introduced incrementally. Feature PRs create only the files
required by the feature they implement.

```text
backend/
├── alembic/
│   ├── env.py
│   └── versions/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db_errors.py
│   │   ├── errors.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── registry.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── zone.py
│   │
│   └── features/
│       ├── __init__.py
│       ├── auth/
│       ├── users/
│       ├── wards/
│       ├── sorting_guide/
│       ├── complaints/
│       ├── bulk_pickups/
│       ├── collection_ops/
│       └── notifications/
│
├── scripts/
│   └── seed_sprint1.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── core/
│   │   └── features/
│   ├── api/
│   │   └── features/
│   ├── integration/
│   │   └── features/
│   └── system/
│
├── docs/
│   ├── adr-0001-sync-sqlalchemy.md
│   └── adr-0002-feature-first-backend.md
│
├── README.md
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

Empty feature directories are not created in advance.

## Application Composition

`app/api/v1/router.py` owns the versioned API router:

```python
api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(wards_router)
```

`app/main.py` includes it once:

```python
app.include_router(api_router, prefix="/api/v1")
```

Operational probes remain outside the versioned business API:

```text
GET /health
GET /ready
```

`main.py` remains responsible for:

- application creation;
- lifespan management;
- middleware;
- global exception handlers;
- platform state;
- health and readiness probes;
- inclusion of the aggregated API router.

Feature-specific endpoints and business rules do not belong in `main.py`.

## Core Responsibilities

### `app/core/config.py`

Owns validated application and database configuration.

### `app/core/db_errors.py`

Owns safe classification of database integrity failures.

### `app/core/security.py`

Owns shared security primitives:

- password hashing and verification;
- access-token creation;
- access-token decoding;
- token expiry validation.

It does not query users or enforce feature-specific permissions.

### `app/core/errors.py`

May define small application-level exceptions carrying:

- HTTP status;
- public error code;
- safe public message.

Services may raise these exceptions without importing FastAPI
`HTTPException`. The global application handler converts them into the
standard error envelope.

This file is introduced by the first feature that requires it.

## Database Responsibilities

### `app/db/base.py`

Owns the declarative base, naming convention, primary-key mixins, and timestamp
mixins.

### `app/db/session.py`

Owns engine and session-factory creation and the request-scoped database
dependency.

Successful feature transactions are not committed automatically by the
dependency.

When an exception escapes database work, the dependency rolls back and closes
the session.

### `app/db/registry.py`

Explicitly imports every SQLAlchemy model required by Alembic metadata
discovery.

The registry:

- imports models only;
- does not import routers or services;
- does not scan the filesystem dynamically;
- is updated whenever a feature introduces a model.

Alembic imports `Base` from this registry for `target_metadata`.

The existing `Zone` model remains in `app/models/zone.py`. It is not moved
solely to change folder layout.

## Feature Package Responsibilities

A persistence-backed feature normally contains:

```text
models.py
schemas.py
repository.py
service.py
router.py
```

Files are included only when the feature needs them.

### Models

Models own:

- tables and columns;
- foreign keys;
- indexes;
- unique constraints;
- check constraints;
- relationships.

Models do not contain HTTP behaviour or service orchestration.

### Schemas

Schemas define the public request and response vocabulary.

Internal persistence names must not leak into public schemas.

Examples:

```text
Public resource: complaint
Internal table: tickets

Public field: ward_code
Internal foreign key: zone_id
```

### Repositories

Feature-local repositories own database access:

- SQLAlchemy `select()` statements;
- filtered list queries;
- persistence lookups;
- row locking where required;
- `session.add()` and related persistence operations.

Repositories expose intention-revealing methods such as:

```text
get_by_id()
get_for_update()
get_by_email()
list_for_citizen()
list_for_worker()
list_for_ward()
add()
```

Repositories do not:

- enforce roles or lifecycle rules;
- return HTTP responses;
- call external services;
- commit or roll back transactions.

A generic base repository, generic CRUD framework, repository interface layer,
or unit-of-work framework is not introduced.

### Services

Services own:

- business rules;
- role and permission decisions;
- ownership checks;
- ward-scope enforcement;
- lifecycle transitions;
- orchestration between repositories;
- notification coordination;
- successful transaction commits.

A write use case should normally:

1. load the required records;
2. validate the actor and current state;
3. apply all related changes;
4. flush when database-generated values are required;
5. commit once;
6. refresh the response entity when required.

Repositories do not commit on behalf of services.

### Routers

Routers own HTTP concerns only:

- paths and methods;
- request schemas;
- response schemas;
- authentication dependencies;
- status codes;
- service invocation.

Routers do not contain SQLAlchemy queries, commits, lifecycle rules, or
feature orchestration.

## Sprint 1 Feature Boundaries

### Authentication

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

The optional refresh endpoint is added only when the token design requires it.

Authentication uses the user repository and does not introduce a separate
authentication repository.

`auth/dependencies.py` owns current-user and common role dependencies.

### Users

```text
POST  /api/v1/admin/users
GET   /api/v1/admin/users
PATCH /api/v1/admin/users/{user_id}
```

The users feature owns user persistence, provisioning, administrative updates,
and future saved-location data.

### Wards

```text
GET /api/v1/wards
```

The wards feature exposes the existing `Zone` reference model through public
ward terminology.

The optional administrative ward endpoint remains outside the core endpoint
count.

### Sorting Guide

```text
GET /api/v1/sorting-guide
PUT /api/v1/admin/sorting-guide
```

The feature owns sorting-guide persistence and administrative updates.

### Complaints

```text
POST  /api/v1/complaints
GET   /api/v1/me/complaints
GET   /api/v1/complaints
PATCH /api/v1/complaints/{complaint_id}/resolution
POST  /api/v1/complaints/{complaint_id}/reopen
```

The internal SQLAlchemy model may be named `Ticket` and use the `tickets`
table. Public schemas and routes use complaint terminology.

Approved complaint types are:

```text
MISSED_PICKUP
OVERFLOW
MIXED_WASTE
DELAY
OTHER
```

The Sprint 1 lifecycle does not introduce `IN_REVIEW`, `ESCALATED`, or a stored
`REOPENED` status.

Reopening performs:

```text
RESOLVED → OPEN
```

Resolution and reopen operations must protect state transitions with an
appropriate row lock or concurrency-safe guarded update.

### Bulk Pickups

```text
POST  /api/v1/bulk-pickups
GET   /api/v1/bulk-pickups
PATCH /api/v1/bulk-pickups/{bulk_pickup_id}
```

The patch operation accepts defined actions rather than arbitrary field or
status updates:

- a citizen cancels an eligible request;
- an officer approves or rejects a pending request;
- stale pending requests may expire through internal server behaviour.

State-changing operations must validate ownership, role, current state, and
concurrent decisions.

### Collection Operations

```text
GET   /api/v1/schedules
GET   /api/v1/routes/me
PATCH /api/v1/route-stops/{route_stop_id}/progress
POST  /api/v1/route-stops/{route_stop_id}/delays
POST  /api/v1/route-stops/{route_stop_id}/waste-issues
GET   /api/v1/waste-issues
```

This feature contains the tightly related collection lifecycle:

```text
Schedule
Route
RouteStop
WorkerAssignment
Delay
WasteIssue
```

Worker-scoped queries enforce assignment in the database query rather than
loading unrestricted data and filtering it only in Python.

Route-stop progress supports:

```text
status
actual_weight_kg
contaminated
```

This preserves the verified-weight prerequisite required by later credit
processing.

### Notifications

```text
GET /api/v1/notifications/me
```

Notifications are persisted in the same transaction as the state change that
creates them where atomic behaviour is required.

Calling services pass the recipient, notification type, reference, and
required display values. Notification handling does not unnecessarily reload
an entity already loaded by the calling service.

No message broker or event-bus infrastructure is introduced for the current
milestones.

## Sprint 1 Seed Data

`scripts/seed_sprint1.py` provides development and demonstration data required
for schedules and collection operations:

```text
schedules
routes
route stops
worker assignments
```

The script must be:

- idempotent;
- non-destructive;
- explicit rather than executed automatically at application startup;
- restricted to development or demonstration use;
- documented in the backend README.

## Milestone 4 Extension

The same architecture extends without changing the platform structure:

```text
features/materials/
features/reuse/
features/credits/
```

Responsibilities map as follows:

- `materials`: material batches and recycling summary;
- `reuse`: listings and claims;
- `credits`: factors, pickup verification, ledger, user credits, and badges;
- `collection_ops`: saved route operations and route optimisation;
- `collection_ops/ors_client.py`: provider-specific OpenRouteService HTTP
  integration when route optimisation is implemented.

The OpenRouteService client is added only with the route-optimisation feature.
Its public service response remains provider-independent.

## Security and Scope Enforcement

Protected feature operations enforce security on the server:

- authentication;
- role;
- ownership;
- ward scope;
- explicit patchable fields;
- valid lifecycle transitions.

Public API responses and logs must not expose:

- password hashes;
- access-token secrets;
- SQL statements or parameters;
- database constraint names;
- internal table or column names;
- third-party API keys;
- driver exception messages.

Database constraints remain the final concurrency-safe guard.

## Testing Structure

Tests remain organised by test level and then feature:

```text
tests/unit/features/<feature>/
tests/api/features/<feature>/
tests/integration/features/<feature>/
tests/system/
```

### Unit tests

Service business rules are tested without PostgreSQL using focused fakes or
stubs where appropriate.

### Integration tests

Repositories, constraints, migrations, query scoping, and PostgreSQL-specific
behaviour are tested against the disposable PostgreSQL test database.

SQLAlchemy is not mocked for repository integration tests.

### API tests

API tests use the complete FastAPI application and verify:

- public status and schema;
- authentication and authorisation;
- ownership and ward scope;
- public error code and request ID;
- persistence effects;
- absence of internal details.

### System tests

System tests verify complete journeys after their dependent features are
available.

Existing foundation tests remain in their current locations unless naturally
changed by later feature work.

## Incremental Adoption

This ADR does not require a separate restructuring of all existing backend
files.

Each feature PR:

1. creates only its required feature package;
2. updates the versioned API router;
3. updates the explicit model registry when models are added;
4. adds migrations when the schema changes;
5. adds tests at the appropriate levels;
6. updates the OpenAPI contract and RTM for its scope.

Existing stable foundation files are not moved merely to make the directory
tree visually uniform.

## Consequences

Benefits:

- feature code is easier to locate and review;
- persistence and business rules remain separate;
- transactions have a clear owner;
- feature tests can be developed independently;
- future Milestone 4 capabilities fit the same structure;
- the backend remains deployable as one application.

Trade-offs:

- substantial features contain several small files;
- repositories introduce an additional layer where meaningful persistence
  behaviour exists;
- the explicit model registry must be updated with each new model.

These trade-offs are accepted in exchange for clearer boundaries, safer
changes, and maintainable testing.
