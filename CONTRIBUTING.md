# Contributing to Verdeza

This repository contains the Verdeza software engineering project for Team API_Avengers.

The GitHub repository name is `MAY2026-Team-012`, but the application/project name is `Verdeza`.

---

## Branch Policy

Use:

* `main` for stable reviewed code
* `feature/*` for new features
* `test/*` for test-related work
* `fix/*` for bug fixes
* `docs/*` for documentation
* `chore/*` for setup/configuration work

Do not push directly to `main`.

Every change must go through a separate branch and Pull Request.

---

## Starting New Work

Always start from the latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/SCRUM-12-short-description
```

Use the correct branch prefix:

```text
feature/SCRUM-12-complaint-form
test/SCRUM-13-complaint-api-tests
fix/SCRUM-14-invalid-ward-error
docs/SCRUM-15-update-readme
chore/SCRUM-16-update-ci
```

The Jira ticket number should come from the Jira board.

Example:

```text
SCRUM-29 Login Page
```

Branch name:

```text
feature/SCRUM-29-login-page
```

---

## Commit Message Format

Use this format:

```text
type(scope): short message
```

Examples:

```text
feat(SCRUM-29): add login page
test(SCRUM-13): add complaint API tests
fix(SCRUM-14): correct invalid ward error
docs(SCRUM-15): update setup instructions
chore(SCRUM-16): add GitHub templates
```

Allowed commit types:

* `feat`
* `fix`
* `test`
* `docs`
* `chore`
* `refactor`

Keep commit messages short, clear, and meaningful.

---

## Pull Request Rules

Every change must go through a Pull Request.

PR target/base branch must be:

```text
main
```

Do not open PRs into:

```text
develop
dev
backup
final
latest
main-copy
```

Every PR must include:

* Jira ticket, or a clear note if the Jira ticket has not been assigned yet
* clear summary
* what changed
* why it changed
* how it was tested
* reviewer

If a Jira task is added after the PR is created, add a PR comment:

```text
Jira ticket added retroactively for traceability: SCRUM-XX
```

---

## Review Rules

Backend PRs should be reviewed for:

* test coverage
* validation
* error handling
* API behavior
* security-sensitive logic
* database impact, if applicable

Frontend PRs should be reviewed for:

* correct API usage
* form validation
* loading state
* empty state
* error state
* responsive layout, if applicable

Testing PRs should be reviewed for:

* acceptance-criteria coverage
* happy path tests
* negative/error tests
* edge cases
* clear test names

Documentation PRs should be reviewed for:

* correctness
* clarity
* milestone alignment
* consistency with the project plan

---

## Files Never to Commit

Never commit:

```text
.env
.env.*
.venv/
venv/
env/
node_modules/
dist/
build/
__pycache__/
.pytest_cache/
.coverage
htmlcov/
.ruff_cache/
```

Use `.env.example` for safe environment documentation.

Examples of safe environment documentation:

```text
DATABASE_URL=postgresql://user:password@localhost:5432/verdeza
SECRET_KEY=replace-this-with-local-secret
```

Do not put real passwords, tokens, API keys, or personal credentials in GitHub.

---

## Frontend Quality Checks

Before opening a frontend Pull Request, run these checks from the repository root:

```bash
cd frontend
npm install
npm run format:check
npm run lint
npm run build
```

If formatting fails, run:

```bash
npm run format
```

Then check again:

```bash
npm run format:check
npm run lint
npm run build
```

Before committing, `pre-commit` should also be installed locally:

```bash
cd ..
pip install pre-commit
pre-commit install
```

Run all pre-commit checks manually when needed:

```bash
pre-commit run --all-files
```

---

## Backend Development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
# Set a 32+ character SECRET_KEY.
# Use APP_ENV=local for normal local development.
# Before running tests, use APP_ENV=test and a DATABASE_URL whose
# database name ends in _test.
ruff check .
ruff format --check .
alembic upgrade head
alembic check
pytest                               # coverage gate (80%) runs automatically
```

A single `pytest` enforces the coverage gate — no extra flags needed. The test
suite refuses to run unless `APP_ENV=test` and the database name ends in `_test`
(a safety guard against pointing it at a real database).

Pre-commit runs Ruff against backend Python files. If the repo's
`.pre-commit-config.yaml` does not already cover `backend/`, add the Ruff hook
there rather than duplicating it.

---

## Before Opening a Pull Request

Always run:

```bash
git status
git diff
```

Read the output before committing. Do not commit blindly.

For backend changes, run:

```bash
cd backend
source .venv/bin/activate
ruff check .
ruff format --check .
alembic check
pytest
```

For frontend changes, run:

```bash
cd frontend
npm install
npm run build
```

If a command fails, fix the issue before opening or updating the PR.

---

## Frontend Dependency Rule

Frontend dependencies are installed locally using npm.

Use:

```bash
cd frontend
npm install
```

Do not commit `node_modules/`.

---

## Merge Policy

Use **Squash and merge** only.

After the PR is merged, delete the temporary branch.

Delete branches like:

```text
feature/SCRUM-29-login-page
test/SCRUM-13-complaint-api-tests
chore/SCRUM-16-update-ci
```

Do not delete:

```text
main
```

---

## After a PR Is Merged

Each team member should update their local repo:

```bash
git checkout main
git pull origin main
```

Then start new work from the latest `main`.

---

## Issue Tracking Policy

Jira is used for:

* sprint planning
* task ownership
* priority tracking
* milestone progress
* team management

GitHub Issues are used mainly for:

* bugs found during testing
* missing test coverage
* technical defects
* code-level problems that need traceability

Do not create duplicate Jira and GitHub items unless there is a clear reason.

If a GitHub Issue is created for a bug, link it in the related PR.

---

## Basic Team Workflow

Use this flow for every task:

```text
Jira task → branch → commit → Pull Request → review → merge → delete branch
```

Example:

```text
SCRUM-29 Login Page
→ feature/SCRUM-29-login-page
→ commits
→ Pull Request into main
→ review
→ squash merge
→ delete feature branch
```

This keeps the project traceable and easier to explain during milestone submission and final evaluation.
