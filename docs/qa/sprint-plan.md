# Verdeza — Sprint 1 and Sprint 2 Backend Plan

**Team rule:** Milestones 3 and 4 are Sprint 1 and Sprint 2. Backend APIs are
split across the two sprints — develop, unit-test, and integrate. There are only
these two backend sprints; Milestone 5 is the final submission stage (working
prototype, presentation, complete code, final documentation), not another
backend-development sprint. All 25 user stories ship across Sprints 1 and 2.

## Summary

The backend development stage is divided across the two official course sprints:

- **Sprint 1 (Milestone 3): 11 stories, 57 acceptance criteria**
- **Sprint 2 (Milestone 4): 14 stories, 80 acceptance criteria**
- **Total: 25 stories, 137 acceptance criteria**

All 25 stories remain within project scope. Story 1.6 remains part of Epic 1 but
is scheduled for Sprint 2 because its recycling-transparency summary depends on
material-batch and dispatch data from Epic 4.

The API allocation is approximately balanced. Endpoint count and implementation
complexity are both considered; acceptance-criteria count alone is not treated as
a 50/50 measurement. Proposed endpoints per story are in `endpoint-inventory.md`.

## Status labels

`Planned — Sprint 1` · `Planned — Sprint 2` · `Implemented` · `Tested`.
`Deferred` is used only for a requirement formally excluded from both sprints.

---

## Sprint 1 — Milestone 3 (11 stories, 57 ACs)

**Epic 1 — Schedule Look-Up & Status Tracking**
- 1.1 Static Route Schedule Look-up
- 1.2 Delay Notification for Citizens
- 1.3 Bulk or Institutional Waste Pickup Scheduling
- 1.4 Manual Route Progress Update
- 1.5 Delay Log Input

**Epic 2 — Public Grievance & Issue Management**
- 2.1 Text-Based Complaint Lodging
- 2.2 Centralized Grievance Sorting Data Grid
- 2.3 Form-Driven Resolution Closure

**Epic 3 — Informational Core & Sorting Support**
- 3.1 Static Sorting Resource Repository
- 3.2 Mixed Waste Issue Tagging

**Epic 5 — Administrative Control & Identity Provisioning**
- 5.1 Role-Based User Provisioning


---

## Sprint 2 — Milestone 4 (14 stories, 80 ACs)

> **Story 1.6 (Recycling Transparency)** remains part of Epic 1 but is scheduled
> here because its summary needs material type, volume and dispatch status —
> data produced by Epic 4's material-batch workflow. It cannot function until
> Epic 4 exists.

**Epic 1 — Schedule Look-Up & Status Tracking**
- 1.6 Recycling Transparency

**Epic 4 — B2G Material Inventory Ledger**
- 4.1 Material Batch Look-up
- 4.2 Material Quality and Contamination Visibility
- 4.3 Pickup Status Update

**Epic 6 — Civic Reuse Exchange**
- 6.1 Reuse Item Listing
- 6.2 Reuse Listing Moderation (Officer)
- 6.3 Reuse Item Browse & Claim
- 6.4 Reuse Claim Transaction Approval (Officer)

**Epic 7 — Route Optimization**
- 7.1 Citizen Pickup Location Registration
- 7.2 Collection Point Map View
- 7.3 One-Click Route Optimization

**Epic 8 — Eco-Credit & Gamification**
- 8.1 Eco-Credits for Verified Segregation
- 8.2 Achievement Badges
- 8.3 Credit Factor Configuration


---

## Route optimisation (Story 7.3)

The public endpoint is `POST /api/v1/routes/me/optimize`. OpenRouteService is
called only by the backend using a server-side key; the frontend never calls it
directly, and the Verdeza response stays provider-independent.

## How this maps to PRs

Each user story or coherent feature slice becomes a focused PR containing the
related contract update, implementation, tests, integration, and RTM update —
not one PR per endpoint.
