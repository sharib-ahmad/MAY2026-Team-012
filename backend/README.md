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

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

## Current Layout

```text
app/
  core/        configuration and shared error-handling helpers
  db/          engine, session, declarative base, and mixins
  models/      shared SQLAlchemy models
  schemas/     shared Pydantic request and response models
  api/v1/      versioned API composition
  services/    shared business services
  main.py      application factory, middleware, and platform handlers

alembic/       migration environment and migration versions

tests/
  unit/        isolated logic tests
  integration/ PostgreSQL integration tests
  api/         endpoint-level API tests
```

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

The shared backend foundation contains:

- configuration and fail-closed secret validation;
- database-only configuration for Alembic;
- SQLAlchemy engine and session management;
- Alembic migrations;
- standard public error envelopes;
- PostgreSQL integrity-error classification;
- request-ID propagation;
- `/health` and `/ready`;
- the shared `Zone` reference model;
- unit, API, and PostgreSQL integration tests.

Business features are implemented through separate feature pull
requests.
