# Verdeza Backend

FastAPI + SQLAlchemy + Alembic + PostgreSQL. Part of MAY2026-Team-012.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                 # set SECRET_KEY and DATABASE_URL
alembic upgrade head                 # create the schema
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

## Layout

```
app/
  core/        config (all business thresholds live here)
  db/          engine, session, declarative base + mixins
  models/      SQLAlchemy models  (import every new model in __init__.py)
  schemas/     Pydantic request/response models
  api/v1/      routers, one module per epic
  services/    business logic invoked by routers
  main.py      FastAPI app + router registration
alembic/       migration environment and versions/
tests/
  unit/        pure logic, no database
  integration/ exercises the database
  api/         endpoint level, through the test client
```

## The checks CI runs (run them before you push)

```bash
ruff check .            # lint
ruff format --check .   # formatting  (ruff format . to fix)
alembic upgrade head    # migrations apply to a clean DB
alembic check           # models and migrations agree
pytest                  # tests
```

## Error-handling foundation

The shared exception handlers in `main.py` are the base every feature endpoint
inherits, so they are hardened here rather than per-router:

- **Validation errors never crash to 500.** `RequestValidationError.errors()` can
  contain non-JSON objects (e.g. a `ValueError` raised inside a validator's
  `ctx`). The handler runs them through `jsonable_encoder` and drops `ctx`, so a
  bad request always returns a clean **422 `VALIDATION_ERROR`** envelope.
  Regression test: `tests/test_error_handling.py`.
- **Error codes match the API contract catalogue** (`VALIDATION_ERROR`,
  `AUTHENTICATION_REQUIRED`, `FORBIDDEN`, `RESOURCE_NOT_FOUND`, `CONFLICT`,
  `DATABASE_UNAVAILABLE`, `INTERNAL_ERROR`), with a `request_id` on every error.
- **`get_db` resolves the session factory from `request.app.state`**, so a feature
  endpoint using `Depends(get_db)` always uses the running app's engine — the one
  `create_app()` built — including in a test that injected an alternate database.
Verified end to end against real PostgreSQL 15: lint, format, migration
round-trip (upgrade → check → downgrade → upgrade), and pytest with
warnings-as-errors and the 80% coverage gate (record the exact figure from your local run).

## Scope (per the team plan)

This PR is the shared foundation only — config, db session/base, app factory,
error envelope, `/health`, `/ready`, the `Zone` reference model, and the initial
migration. **No feature logic** (no complaint, credit, reuse, material-batch,
route-optimization, or badge code). Each feature PR adds its own models, enums,
schemas, routers, and tests on top of this base.
