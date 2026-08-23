# Verdeza

**A sustainable waste collection, complaint tracking and recycling management platform**

Verdeza is an academic civic-services platform developed by **API_Avengers** for the IITM Software Engineering Project.

- **Team code:** MAY2026-Team-012
- **Selected domain:** Civic Services Platform
- **Subdomain:** Sustainable Waste Management and Recycling
- **Delivery model:** Sprint-based development with independent QA and CI quality gates

> **Project status:** Active academic development. Implemented behaviour, known defects and release readiness must be verified through GitHub Actions, open issues and the QA evidence documents. This repository is not presented as production-ready.

## Contents

- [Overview](#overview)
- [User Roles and Capabilities](#user-roles-and-capabilities)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Local Development](#local-development)
- [API Documentation](#api-documentation)
- [Testing and Quality Gates](#testing-and-quality-gates)
- [Public API and Security Rules](#public-api-and-security-rules)
- [Sprint Scope](#sprint-scope)
- [Known Limitations](#known-limitations)
- [Contribution Workflow](#contribution-workflow)
- [Team](#team)

## Overview

Verdeza provides one controlled platform for municipal waste-service workflows. It connects residents, system administrators, municipal officers, collection workers and recyclers while keeping permissions, ward scope, lifecycle rules and auditability on the server.

The platform supports or is designed to support:

- collection-schedule visibility;
- complaint creation, tracking, resolution and eligible reopening;
- bulk-pickup requests and controlled status actions;
- administrator-managed users and ward reference data;
- collection-worker routes and route-stop progress;
- notifications and request traceability;
- future recycling, material, reuse, eco-credit and badge workflows.

## User Roles and Capabilities

### Residents

- view relevant schedule and dashboard information;
- create and review complaints;
- request and track bulk pickups;
- receive service notifications;
- view personal impact information as the feature set develops.

### System administrators

- provision users without public self-registration;
- manage supported account lifecycle operations;
- manage ward reference data;
- review administrative dashboard and audit information;
- maintain approved platform reference data.

### Municipal officers and managers

- access ward-scoped operational information;
- monitor complaints and collection work;
- update eligible complaint states;
- coordinate workers and operational notifications;
- perform actions subject to server-side role and lifecycle checks.

### Collection workers

- access assigned routes and stops;
- record route-stop progress;
- record actual collected weight and contamination information;
- report delays and waste issues.

### Recyclers

- participate in planned material-batch, claim and recycling workflows;
- support traceable material hand-off and processing in later sprint scope.

## Architecture

Verdeza follows a **feature-oriented modular monolith**.

```text
React client
    |
    | REST/JSON
    v
FastAPI routers
    |
    v
Feature services
    |
    v
SQLAlchemy models and database session
    |
    v
PostgreSQL
```

The intended backend dependency direction is:

```text
router -> service -> SQLAlchemy models/session -> PostgreSQL
```

Responsibility boundaries:

- **Routers** own HTTP paths, schemas, authentication dependencies, status codes and service invocation.
- **Services** own business rules, role checks, ward scope, lifecycle transitions, notifications and successful write transactions.
- **Database dependencies** own rollback and cleanup when an exception escapes.
- **Core security** owns password hashing, JWT creation and JWT validation.
- **Global error handling** provides stable public errors with request identifiers and no database or secret leakage.
- **`api/v1/router.py`** composes feature routers.
- **`main.py`** remains the application composition root.

Each feature normally owns its models, schemas, service and router. Shared infrastructure stays in `core/` and `db/`, while genuinely shared reference models remain in `models/`.

## Technology Stack

### Backend

- Python 3.11 or later
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Pydantic
- Celery and Redis (scheduled background jobs, `app/core/celery_app.py`)
- OpenRouteService (server-side route optimisation)
- pytest and pytest-cov
- Ruff
- Redocly CLI
- GitHub Actions

### Frontend

- React
- Vite
- JavaScript
- npm
- Playwright (end-to-end browser journeys)
- frontend formatting and linting through repository scripts

### Local infrastructure

- Docker Compose
- PostgreSQL (host port `5433`)
- Redis (host port `6379`)
- environment-based configuration

## Repository Structure

```text
MAY2026-Team-012/
├── .github/
│   └── workflows/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── features/
│   │   └── models/
│   ├── docs/
│   ├── tests/
│   │   ├── api/
│   │   ├── integration/
│   │   ├── system/
│   │   └── unit/
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── requirements-dev.txt
├── docs/
│   └── qa/
├── frontend/
├── api-doc.yaml
├── redocly.yaml
├── docker-compose.yml
├── CONTRIBUTING.md
└── README.md
```

Empty `__init__.py` files are intentional Python package markers. They do not contain business logic and should not be removed merely because they are empty.

## Local Development

### Prerequisites

Install:

- Git;
- Docker with Docker Compose;
- Python 3.11 or later;
- Node.js and npm.

### 1. Clone the repository

```bash
git clone https://github.com/sharib-ahmad/MAY2026-Team-012.git
cd MAY2026-Team-012
```

### 2. Configure the backend environment

Create a local environment file:

```bash
cp backend/.env.example backend/.env
```

Review `backend/.env` before starting the application.

Required safety rules:

- use a non-empty development `SECRET_KEY`;
- point `DATABASE_URL` to the intended local PostgreSQL database;
- use only disposable databases whose names end in `_test` for destructive or automated tests;
- keep real credentials and secrets out of Git;
- never commit `.env`.

### 3. Start local infrastructure

From the repository root:

```bash
docker compose up -d
```

Confirm container health before applying migrations.

### 4. Create the backend virtual environment

Linux, macOS or WSL:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 5. Install backend dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip check
```

### 6. Apply database migrations

```bash
alembic upgrade head
alembic check
```

Never run destructive Alembic commands against production or a database containing required data.

### 7. Start the backend

```bash
python -m uvicorn app.main:app --reload
```

Typical local endpoints:

- API root: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- health check: `http://127.0.0.1:8000/health`
- readiness check: `http://127.0.0.1:8000/ready`

### 8. Start the frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Use the scripts declared in `frontend/package.json` as the source of truth for frontend commands.

## API Documentation

The submission-ready Swagger-compatible OpenAPI description is:

```text
api-doc.yaml
```

It documents API paths, operation descriptions, user-story mapping, request and response schemas, security requirements and public error responses.

The Redocly configuration is:

```text
redocly.yaml
```

### Validate the OpenAPI document

Run from the repository root:

```bash
npx --yes @redocly/cli@latest check-config --config redocly.yaml

npx --yes @redocly/cli@latest lint   api-doc.yaml   --config redocly.yaml
```

The project keeps `operation-4xx-response` as a warning for approved public operations that have no application-level 4xx outcome. Other rules remain under the selected Redocly ruleset.

### Preview the API documentation

```bash
npx --yes @redocly/cli@latest preview-docs   api-doc.yaml   --config redocly.yaml
```

Open the local URL printed by Redocly, normally `http://127.0.0.1:8080`.

The static OpenAPI document and FastAPI runtime schema must be reviewed together. An endpoint is not considered implemented only because it appears in YAML, and an implemented route is not considered approved when it violates the accepted public contract.

## Testing and Quality Gates

### Backend quality commands

Run from `backend/` with the virtual environment active:

```bash
python -m pip check
ruff check .
ruff format --check .
python -m compileall -q app tests alembic
alembic check
python -m pytest
```

### Focused API tests

```bash
python -m pytest --no-cov -q tests/api/features/auth
python -m pytest --no-cov -q tests/api/features/admin
python -m pytest --no-cov -q tests/api/features/manager
python -m pytest --no-cov -q tests/api/features/citizen
```

### End-to-end tests

Playwright starts the backend and the Vite dev server itself against a
dedicated test database, so run it with Docker Compose already up:

```bash
cd frontend
npm ci
npx playwright install --with-deps chromium
npm run test:e2e
```

`frontend/playwright.config.js` is the source of truth; override
`E2E_DATABASE_URL` or `E2E_PYTHON` if your local setup differs.

### Test levels

- **Unit tests:** isolated logic and service behaviour.
- **Integration tests:** migrations, database constraints, persistence, rollback and concurrency using disposable PostgreSQL.
- **API tests:** the complete FastAPI application, including status codes, schemas, security, persistence, privacy and safe errors.
- **System tests:** complete cross-feature journeys after all required dependencies exist.
- **End-to-end tests:** a small number of critical Playwright browser journeys (`frontend/e2e/`) against the real frontend and backend.

The strategy is risk-based rather than count-based: unit tests, then API/application tests, then PostgreSQL-backed integration where database behaviour matters, then a small number of system and Playwright journeys for the critical paths.

### Automated gates

The project quality workflow includes:

- pytest;
- pytest-cov with branch coverage;
- an 80 percent coverage threshold;
- warnings treated as errors;
- strict pytest marker and configuration validation;
- PostgreSQL-backed CI tests;
- Alembic migration checks;
- Ruff lint and format checks;
- OpenAPI linting;
- frontend formatting, linting and production build;
- a Playwright end-to-end job (`e2e-check`);
- GitHub Actions (`.github/workflows/ci.yml`).

A failing requirement test must remain visible. Tests must not be skipped, weakened or rewritten merely to obtain a passing build.

### Pre-commit checks

Install and run the configured hooks:

```bash
python -m pre_commit install
python -m pre_commit run --all-files
```

The local frontend hooks intentionally run complete npm scripts without passing individual filenames.

## Public API and Security Rules

### Canonical authentication

Approved public authentication routes:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

Public self-registration is also part of the accepted contract:

```text
POST /api/v1/auth/register
```

It is public and unauthenticated, but its `role` field is restricted
server-side to public roles only — `CITIZEN`, `COLLECTION_WORKER`
(`COLLECTOR`) and `RECYCLER`. Requesting `MUNICIPAL_OFFICER` (`MANAGER`) or
`SYSTEM_ADMIN` (`ADMIN`) is rejected with `403`; those staff accounts remain
provisioned by a System Admin, per Story 5.1.

Historically the `role` field was **not** restricted, which allowed an
unauthenticated caller to self-provision a staff account. That was
DEF-004 in `docs/qa/defect-log.md`; it was fixed by PR #134 (commit
`ca666a2`, closing issue #133) and is closed. The endpoint itself was not
removed.

### Public vocabulary

```text
Public resource: complaints
Internal table: tickets

Public resource: wards
Internal model/table vocabulary: zones

Public field: ward_code
Internal foreign key: zone_id
```

Internal database names must not leak into public paths or response schemas.
This rule is not fully upheld on `main`: the complaints feature's public
paths are literal `/tickets` (e.g. `POST /api/v1/complaints/tickets`), not
`/complaints`. `api-doc.yaml` documents the routes as they exist rather than
as this rule intends.

### Standard error envelope

```json
{
  "error": {
    "code": "UPPER_SNAKE_CASE",
    "message": "Safe public message",
    "request_id": "uuid",
    "details": []
  }
}
```

`details` is optional. Public errors must not expose SQL, database constraints, driver messages, password hashes, JWT secrets or internal stack traces.

### Authorisation and lifecycle rules

- protected decisions are enforced on the server;
- role checks are not delegated to the frontend;
- ward-scoped actors may access only permitted ward data;
- state transitions must follow the approved lifecycle;
- audit history is append-only;
- related write operations must be transactional;
- authentication failures must use safe and consistent public responses.

## Sprint Scope

### Sprint 1: Milestone 3

Sprint 1 covers the platform foundation and main operational API workflows:

- authentication and current-user identity;
- administrator user and ward management;
- citizen complaints and bulk pickups;
- manager and municipal-officer workflows;
- collection schedules and worker route operations;
- sorting guidance;
- notifications;
- audit, validation and safe error handling;
- independent API QA and defect evidence.

### Sprint 2: Milestone 4

Planned priorities include:

- correct remaining Sprint 1 authentication, administrator and manager defects;
- align runtime routes and OpenAPI documentation;
- complete citizen and cross-feature regression coverage;
- recycling-summary and material-batch workflows;
- reuse exchange;
- route optimisation;
- eco-credit and badge processing;
- maintain meaningful backend coverage at or above the required threshold;
- retest all corrected acceptance criteria.

## Known Limitations

Recorded deliberately rather than closed. This submission does not claim that
every defect is resolved. Full detail, severity and history are in
[docs/qa/defect-log.md](docs/qa/defect-log.md).

- **Two open Medium defects.** DEF-005 — `GET /api/v1/track/{reference}` is
  unauthenticated and applies no ownership check, so a caller holding a
  reference code can read limited name and status information. DEF-006 — the
  reuse manager *read* queues fail open for an officer with no assigned ward,
  giving cross-ward read visibility; the corresponding write actions are
  correctly denied. Neither corrupts data nor bypasses authentication.
- **One stale regression test.** The accepted bulk-pickup rule is
  next-calendar-day scheduling in the pilot timezone; backend, frontend and
  `api-doc.yaml` agree. `test_create_pickup_less_than_24h_notice_returns_422`
  still encodes the superseded rolling-24h interpretation and can fail in the
  approximate 23:00–00:00 IST window. This is a test-premise issue, not a
  backend defect.
- **Unimplemented user-story scope.** Several acceptance criteria have no
  corresponding endpoint on `main` — see "Known Contract Gaps" in the defect
  log and the reconciliation table in [docs/qa/rtm.md](docs/qa/rtm.md).

## Contribution Workflow

1. Start a focused branch from the latest `main`.
2. Keep each pull request limited to one coherent concern.
3. Update tests and API documentation when behaviour or contracts change.
4. Run the relevant focused tests before the complete regression suite.
5. Record exact expected and actual results.
6. Create one defect issue per root cause.
7. Keep QA-only pull requests in Draft while confirmed product defects remain.
8. Request review from the responsible owner.
9. Merge only after required checks, review and acceptance are complete.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository workflow.

## Team

| Name | Roll number | Primary role | Secondary role |
|---|---:|---|---|
| Sharib Ahmad | 24f2001786 | Project Manager | Scrum Master |
| Nivedita Shill | 24f1001642 | Frontend Developer | Code Reviewer |
| Neeraj Kumar | 23f2002096 | Backend Developer | Code Reviewer |
| Eram Nishat | 23f2004433 | Tester | Backend Developer |
| Harsh Meshram | 22f3002098 | Scrum Master | Tester |

## Academic Use

This repository is maintained as part of the IITM Software Engineering Project. It demonstrates requirements traceability, API design, implementation, automated testing, defect reporting and sprint-based delivery.
