# ADR 0001 — Synchronous SQLAlchemy with sync routes

## Decision
The backend uses synchronous SQLAlchemy. FastAPI endpoints that touch the
database are declared with plain `def`, NOT `async def`.

## Why
FastAPI runs `def` routes in a threadpool, so a synchronous database call does
not block the event loop. This keeps the data layer simple (no async engine, no
async session, no await-everywhere).

## The rule this creates
Never write `async def` on a route that calls the synchronous `Session`. Doing
so runs the blocking call directly on the event loop and can stall the whole
server under load. If a genuinely async dependency appears later (e.g. an
external HTTP call), isolate it and keep DB access synchronous, or migrate the
whole data layer to the async stack deliberately — not per-endpoint.
