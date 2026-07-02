## Summary

Briefly explain what this PR changes in 2–4 lines.

## Jira / Task Reference

Jira ticket: SCRUM-___

Related GitHub issue, if any: #___

## Type of Change

- [ ] Feature
- [ ] Bug fix
- [ ] Test
- [ ] Documentation
- [ ] Chore / setup
- [ ] Refactor

## What Changed?

List the main files, modules, screens, APIs, tests, or documentation changed.

Example:
- Added backend health endpoint
- Added pytest test for health endpoint
- Updated README setup instructions

## Why This Change Is Needed

Explain the reason for this change.

Example:
- Supports Milestone 2 setup
- Implements user story SCRUM-12
- Fixes a validation issue found during testing
- Adds required test evidence for sprint deliverables

## How Was This Tested?

Write exact commands and/or manual testing steps.

Backend examples:
```bash
cd backend
source .venv/bin/activate
pytest
ruff check .
```

Frontend examples:

```bash
cd frontend
npm install
npm run build
```

Manual test examples:

* Opened the page locally
* Submitted the form with valid data
* Checked empty/error state
* Verified API response in browser/Postman

## Expected Result

Write the expected outcome.

Examples:

* Tests should pass
* Page should render without console errors
* API should return `200 OK`
* Invalid input should return a validation error

## Actual Result

Write the actual result observed.

Examples:

* `pytest` passed locally
* `npm run build` completed successfully
* API returned the expected response
* Manual UI check completed successfully

## Screenshots / Evidence

Add screenshots, terminal output, API response, or short notes if applicable.

Examples:

```text
pytest result:
3 passed in 1.25s
```

```text
frontend build:
npm run build completed successfully
```

```text
API response:
GET /health returned 200 OK
```

## Risk Level

* [ ] Low — docs/setup only, no application behavior changed
* [ ] Medium — affects one feature/module
* [ ] High — affects shared logic, authentication, database, API contract, or deployment

## Reviewer Checklist

* [ ] PR branch is not `main`
* [ ] PR target/base branch is `main`
* [ ] Jira ticket is mentioned, or clearly marked as initial setup if not yet assigned
* [ ] Change is small enough to review
* [ ] No `.env`, `.venv`, `venv`, `node_modules`, or generated files committed
* [ ] Backend tests added/updated, if backend behavior changed
* [ ] Frontend validation/error/empty states checked, if UI changed
* [ ] API contract checked, if API changed
* [ ] Documentation updated, if setup or behavior changed
* [ ] Reviewer assigned
