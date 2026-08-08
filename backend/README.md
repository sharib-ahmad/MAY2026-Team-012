# Verdeza Backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL. Part of MAY2026-Team-012.

## Setup

Run these commands from the `backend/` directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Generate a local application secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `SECRET_KEY` in `.env` and configure
`DATABASE_URL`.

Never commit `.env`, and do not reuse local secrets in staging or
production.

Apply the migrations:

```bash
alembic upgrade head
```

Alembic requires database configuration but does not require
`SECRET_KEY`. Starting the FastAPI application outside `APP_ENV=test`
still requires a valid `SECRET_KEY`.

Start the backend:

```bash
uvicorn app.main:app --reload
```

Local API documentation:

```text
http://localhost:8000/docs
```

## Running Celery and Redis

For daily collection scheduling, the application uses Celery with Redis as the message broker.

### 1. Start Redis Broker

Ensure Redis is installed and running.

- **Using WSL/Ubuntu (Native)**:
  ```bash
  sudo service redis-server start
  ```
- **Using Docker Compose**:
  If you prefer running Redis inside Docker, start the service:
  ```bash
  docker compose up -d redis
  ```

Make sure the `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` variables in your `.env` are configured correctly (defaults to `redis://localhost:6379/0`).

### 2. Start Celery Worker

Open a new terminal, activate the virtual environment, navigate to the `backend/` directory, and start the Celery worker process:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

### 3. Start Celery Beat Scheduler

Open another terminal, activate the virtual environment, navigate to the `backend/` directory, and start the Celery beat scheduler:

```bash
celery -A app.core.celery_app beat --loglevel=info
```

> [!NOTE]
> For manual local testing and verification, the beat schedule is set to run every 300 seconds. For production, configure it to daily (`crontab(hour=0, minute=0)`) in `app/core/celery_app.py`.


Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

## Current Layout

The backend follows a feature-first structure: cross-cutting concerns
live under `app/core`, `app/db`, and `app/models`, while each business
capability owns its own `router.py`, `schemas.py`, `service.py`, and
(where it has its own tables) `models.py` under `app/features/`.

```text
app/
├── main.py                         # App factory, middleware, error handlers,
│                                    # /health, /ready, dev-only DB seeding
├── api/
│   └── v1/
│       └── router.py               # Composes every feature router under /api/v1
├── core/
│   ├── config.py                   # Settings (env-driven)
│   ├── db_errors.py                # Postgres integrity-error classifier
│   └── security.py                 # Password hashing, JWT helpers
├── db/
│   ├── base.py                     # Declarative base
│   ├── session.py                  # Engine + session factory
│   └── registry.py                 # Imports every model for metadata
├── models/
│   ├── zone.py                     # Shared Zone reference model
│   ├── audit.py                    # AuditLog model
│   ├── enums.py                    # Role, UserStatus, PickupStatus, ...
│   └── export.py
└── features/
    ├── auth/                       # Signup, login, session/token issuance
    ├── users/                      # Resident profile & account endpoints
    ├── admin/                      # Admin-only account/zone management
    ├── manager/                    # Municipal officer dashboards & workflows
    ├── wards/                      # Ward/zone reference data
    ├── collection_ops/             # Resident schedules + collector ops
    │                               # (includes ors_client.py routing client)
    ├── bulk_pickups/               # Resident bulk-pickup requests +
    │                               # collector assignment
    ├── complaints/                 # Resident complaint submission/handling
    ├── notifications/              # Resident notification delivery
    ├── tracking/                   # Public, unauthenticated pickup tracking
    ├── sorting_guide/              # WasteCategory model, seeded at startup
    │                               # (router/service not yet wired up)
    ├── materials/                  # Materials ledger (router defined,
    │                               # not yet mounted on the API router)
    ├── credits/                    # Credits & gamification (router
    │                               # defined, not yet mounted)
    └── reuse/                      # Civic reuse exchange (router
                                     # defined, not yet mounted)

    # each feature above typically contains:
    #   router.py        - APIRouter with its own prefix/tags
    #   schemas.py        - Pydantic request/response models
    #   service.py        - business logic
    #   models.py         - SQLAlchemy models (only where the feature owns tables)
    #   dependencies.py   - feature-specific auth/role guards (auth, admin,
    #                       manager, users)

alembic/
├── env.py                          # Migration environment
├── script.py.mako                  # Migration template
└── versions/                       # Migration scripts

docs/                                # Architecture decision records (ADRs)

tests/
├── unit/                           # Isolated logic tests, mirrored per feature
├── integration/                    # PostgreSQL integration tests
├── api/                            # Endpoint-level API tests, per feature
└── system/                         # End-to-end user-journey tests
```

Each feature's `router.py` declares its own `APIRouter` (with its own
`prefix` and OpenAPI `tags`); `app/api/v1/router.py` is the single
place that wires those routers onto `/api/v1`, mounting most resident
endpoints under `/user`, collector endpoints under `/user/collector`,
manager endpoints under `/manager`, and admin endpoints under
`/admin`. `sorting_guide`, `materials`, `credits`, and `reuse` currently
exist as feature packages but are not yet included in that router, so
their endpoints aren't reachable through the API yet.

## Checks CI Runs

Run these before pushing:

```bash
python -m pip check

ruff check .
ruff format --check .

alembic upgrade head
alembic check

python -m pytest
```

The backend CI job also verifies migration downgrade and re-upgrade
against an isolated migration test database.

## Configuration Safety

Database-only configuration is separated from complete application
configuration.

Alembic loads only the settings required for migrations, including
`DATABASE_URL`. It does not load or validate `SECRET_KEY`.

Application startup remains fail-closed outside `APP_ENV=test` when
`SECRET_KEY` is missing, blank, a recognised placeholder, or too short.

No default application secret is committed.

## Error-Handling Foundation

The shared handlers in `main.py` provide one consistent public error
envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "request_id": "00000000-0000-0000-0000-000000000000"
  }
}
```

Every error response includes:

- a stable public error code;
- a safe public message;
- an `X-Request-ID` response header;
- the same request ID in the response body.

### Validation errors

Request-validation failures return `422 VALIDATION_ERROR`.

Internal validator messages and contexts are not exposed to API clients.

### Database integrity errors

PostgreSQL integrity failures are classified using SQLSTATE:

- unique violation: `409 DUPLICATE_RESOURCE`;
- foreign-key violation: `409 CONFLICT`;
- recognised public check constraint: `422 VALIDATION_ERROR`;
- unknown or internal integrity failure: `500 INTERNAL_ERROR`.

API clients never receive SQL statements, SQL parameters, submitted
database values, constraint names, or database-driver messages.

### Database session cleanup

`get_db` obtains the session factory from `request.app.state`.

When an exception escapes database work, the request session is rolled
back and then closed. Successful write transactions are owned by the
service or use-case layer.

## Health Endpoints

### `GET /health`

Database-independent liveness probe.

A successful response confirms that the application process is running.

### `GET /ready`

Database-backed readiness probe.

It obtains the session factory from `request.app.state` and executes:

```sql
SELECT 1
```

Behaviour:

- successful database query: `200 OK`;
- SQLAlchemy/database failure: `503 DATABASE_UNAVAILABLE`;
- unrelated programming failure: `500 INTERNAL_ERROR`.

Database failure details remain available only in protected server logs
and are not returned to API clients.

## Test Database Safety

Destructive test setup is refused unless:

```text
APP_ENV=test
```

and the database name ends in:

```text
_test
```

Examples:

```text
verdeza_pytest_test
verdeza_migration_test
```

Never run migration downgrade tests against staging or production.

## Current Scope

Shared backend foundation:

- configuration and fail-closed secret validation;
- database-only configuration for Alembic;
- SQLAlchemy engine and session management;
- Alembic migrations;
- standard public error envelopes;
- PostgreSQL integrity-error classification;
- request-ID propagation;
- `/health` and `/ready`;
- the shared `Zone` and `AuditLog` reference models;
- unit, API, integration, and system tests.

Business features implemented and mounted on `/api/v1`:

- `auth` — signup, login, and session handling;
- `users` — resident profile endpoints;
- `admin` — account, zone, and platform administration;
- `manager` — municipal officer dashboards and workflows;
- `wards` — ward/zone reference data;
- `collection_ops` — resident collection schedules and collector
  operations, including ORS-based routing;
- `bulk_pickups` — resident bulk-pickup requests and collector
  assignment;
- `complaints` — resident complaint handling;
- `notifications` — resident notifications;
- `tracking` — public pickup tracking.

Feature packages that exist in code but are not yet mounted on the
API router: `sorting_guide` (waste-category reference data, seeded at
startup), `materials`, `credits`, and `reuse`.