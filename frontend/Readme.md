# Verdeza — Frontend

Verdeza is a waste-management platform that connects residents, collectors, recyclers, managers, and admins around scheduled pickups, tracking, recycling, donations, and reporting. This repository contains the React (Vite) single-page frontend.

## Tech Stack

- **React 18** with **React Router v6**
- **Vite 6** — dev server & build tooling
- **Tailwind CSS 3** — utility-first styling with custom design tokens
- **Axios** — API client with JWT auth interceptors
- **React Leaflet / Leaflet** — maps
- **Recharts** — charts/dashboards
- **Lucide React** — icons
- **date-fns** — date formatting
- ESLint + Prettier for linting/formatting

## Prerequisites

- Node.js 20+
- npm

## Getting Started

```bash
# Install dependencies
npm install

# Start the dev server (http://localhost:5173)
npm run dev
```

The dev server proxies `/api` and `/uploads` requests to `http://localhost:8000` (see `vite.config.js`), so it expects a backend running locally on port 8000. If you don't have a backend yet, the app still works end-to-end via the mock data layer described below.

## Environment Variables

Copy `.env.example` to `.env` if you need to override defaults:

```bash
cp .env.example .env
```

| Variable            | Default | Description                                                             |
| ------------------- | ------- | ----------------------------------------------------------------------- |
| `VITE_API_BASE_URL` | `/api`  | Base URL for API requests. Only needed if not using the Vite dev proxy. |

## Available Scripts

| Command                | Description                                      |
| ---------------------- | ------------------------------------------------ |
| `npm run dev`          | Start the Vite dev server with hot reload        |
| `npm run build`        | Type-check and build for production into `dist/` |
| `npm run preview`      | Preview the production build locally             |
| `npm run lint`         | Run ESLint                                       |
| `npm run format`       | Format the codebase with Prettier                |
| `npm run format:check` | Check formatting without writing changes         |

## Project Structure

```
src/
├── App.jsx                        # Route definitions
├── main.jsx                       # App entry point
├── index.css / styles/            # Global styles
├── assets/                        # Banner & facility imagery
├── components/
│   ├── Footer.jsx
│   ├── ProtectedRoute.jsx         # Role-based route guard
│   ├── PublicLayout.jsx           # Layout wrapper for public pages
│   ├── ScrollToTop.jsx
│   ├── AddressField.jsx
│   ├── DonationImages.jsx
│   ├── ImageLightBox.jsx
│   └── UI.jsx                      # Shared UI primitives
├── context/
│   ├── AuthContext.jsx            # Auth state, login/register/logout
│   └── roles.jsx                  # Role → dashboard route mapping
├── hooks/
│   ├── usePolling.js
│   └── useRefreshOnFocus.js
├── lib/
│   ├── api.js                     # Axios instance with JWT + refresh interceptors
│   ├── mockAuth.js                # Local, in-browser mock auth (no backend yet)
│   ├── ecobot.js                  # Rule-based assistant used on the resident portal
│   ├── mockResidentData.js        # Pickups, tickets, donations/Community Shelf, impact stats
│   ├── mockRecyclerData.js        # Shared batch inventory / Community Shelf for recyclers
│   ├── mockCollectorData.js
│   ├── mockOfficerData.js
│   ├── mockSchedules.js
│   ├── mockSortingGuide.js
│   ├── mockUserStatus.js
│   └── mockZones.js
├── data/
│   ├── admin_portal_data.json
│   └── municipal_officer_data.json
└── pages/
    ├── Landing.jsx
    ├── Login.jsx
    ├── Register.jsx
    ├── Track.jsx
    ├── Flows.jsx
    ├── SortingGuidePublic.jsx
    └── dashboards/
        ├── ResidentDashboard.jsx
        ├── CollectorDashboard.jsx
        ├── RecyclerDashoard.jsx
        ├── ManagerDashboard.jsx
        ├── AdminDashboard.jsx
        ├── resident/              # Home, Community Shelf, MyClaims, MyDonations, MyPickups,
        │                          # CreateDonation, CollectionFlow, SchedulePickup, ScheduleLookup,
        │                          # SortingGuide, RecyclingTransparency, Impact, Tickets, EcoBotChat
        ├── recycler/              # Home, Community Shelf, MyClaims, Reports, QualityBadge
        ├── manager/                # Overview, Crews, Complaints, RouteTracking, shared, format
        ├── admin/                 # Accounts, CreateAccount, Wards, Logs, SortingGuideEditor, shared, format
        └── collector/             # Routes
```

## Authentication & Roles

The app supports five roles, each with its own dashboard route:

| Role      | Route                  | Status      |
| --------- | ---------------------- | ----------- |
| Resident  | `/resident/dashboard`  | Fully built |
| Recycler  | `/recycler/dashboard`  | Fully built |
| Manager   | `/manager/dashboard`   | Fully built |
| Admin     | `/admin/dashboard`     | Fully built |
| Collector | `/collector/dashboard` | In progress |

Dashboard routes are guarded by `ProtectedRoute`, which checks the authenticated user's role before rendering. Each dashboard is a self-contained shell (top bar + side nav) that composes the feature pages under its own `pages/dashboards/<role>/` folder.

**Note:** There is no live `/api/auth/*` backend yet. `src/lib/mockAuth.js` simulates registration, login, hashed password storage, and JWT-shaped session tokens entirely in `localStorage` via the Web Crypto API. `AuthContext.jsx` is the single integration point — swap its calls for real `axios` requests to `/api/auth/*` once a backend exists, and the rest of the app should not need to change.

Once a real backend is available, `src/lib/api.js` already handles:

- Attaching the JWT `Authorization` header to every request
- Automatically refreshing expired tokens on `401` responses and retrying the original request

## Mock Data Layer

Beyond auth, most feature data (pickups, tickets, donations, recycler batches, schedules, zones, sorting guide content, user status) is also backend-free for now: each `lib/mock*Data.js` module reads/writes its own `localStorage`-backed collections and is seeded with realistic demo records the first time a given user opens their dashboard. Every one of these modules is written to mirror the shape of the eventual REST API, so pages import from `lib/mock*Data.js` rather than calling `axios` directly — swapping a module's internals for real API calls should not require changes to the pages that use it.

Notable feature areas:

- **Resident portal** — scheduling pickups, live tracking, tickets/complaints, the sorting guide, recycling transparency stats, impact/credits, an EcoBot assistant chat, and the **Community Shelf** (a peer-to-peer donation marketplace where residents list and claim reusable items).
- **Recycler portal** — a shared batch inventory (**Community Shelf**) recyclers can browse and claim, claim tracking, and collection reports.
- **Manager portal** — crew and route oversight, complaints handling, and an operations overview.
- **Admin portal** — account management, ward configuration, sorting-guide editing, and activity logs.

## Styling / Design Tokens

Tailwind is extended with role-specific accent colors and design tokens (see `tailwind.config.js`):

| Token                         | Value     | Usage         |
| ----------------------------- | --------- | ------------- |
| `primary`                     | `#1B5E20` | Resident      |
| `accent`                      | `#0277BD` | Collector     |
| `manager`                     | `#B8860B` | Manager       |
| `recycler`                    | `#6A1B9A` | Recycler      |
| `admin`                       | `#37474F` | Admin         |
| `success` / `warn` / `danger` | —         | Status colors |

Fonts: `Inter` (sans) and `JetBrains Mono` (mono).

## Building for Production

```bash
npm run build
```

Output is generated in `dist/`.

## Docker

A multi-stage `Dockerfile` is included, building the app with Node and serving the static output with Nginx.

```bash
docker build -t verdeza-frontend .
docker run -p 80:80 verdeza-frontend
```

`nginx.conf` serves the SPA with client-side routing fallback and proxies `/api/` and `/uploads/` to a `backend` service on port `8000` (expects a Docker network / `docker-compose` setup where the backend container is reachable at host `backend`).

## Linting & Formatting

This project uses ESLint (with React Hooks and React Refresh plugins) and Prettier. Run before committing:

```bash
npm run lint
npm run format
```
