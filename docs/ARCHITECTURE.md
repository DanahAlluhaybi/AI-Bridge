# Architecture — Phase 1: Foundation

## The full vision (for context — most of this is not built yet)

AI Bridge's eventual pipeline:

```
Existing Enterprise Systems
    -> Integration / AI Adapter
    -> Data Normalization & Classification
    -> AI Readiness Assessment
    -> AI Governance Gateway
    -> Risk & Policy Engine
    -> Human Approval (when required)
    -> AI Model
    -> Audit Trail & Dashboard
```

Phase 1 builds none of the boxes above. It builds the *road* those boxes
will sit on: a working frontend, backend, and database, talking to each
other correctly. Everything after this phase is business logic layered on
top of this same skeleton.

## Phase 1 architecture

```
┌─────────────────────┐         HTTP (fetch)         ┌──────────────────────┐
│   React frontend     │  ───────────────────────────>│   FastAPI backend     │
│  (Vite, port 5173)   │<───────────────────────────  │   (port 8000)         │
└─────────────────────┘         JSON response          └───────────┬──────────┘
                                                                     │ SQLAlchemy ORM
                                                                     v
                                                          ┌──────────────────────┐
                                                          │  SQLite (ai_bridge.db)│
                                                          └──────────────────────┘
```

- The **frontend** is a static site while developing (served by Vite's dev
  server) that runs entirely in your browser. It never talks to the
  database directly — only ever to the backend, over HTTP.
- The **backend** is the only thing allowed to talk to the database. This
  matters for every later phase: it's where governance/risk/policy checks
  will live, and a frontend can't be trusted to enforce those honestly
  (a user could just edit the JavaScript). Enforcement always happens
  server-side.
- The **database** is one file (`ai_bridge.db`). No install, no server
  process, no account. Good enough for an MVP; SQLite has real limits
  (e.g. limited concurrent writers) that would matter in a production
  multi-user system — out of scope for a local learning project.

## Why FastAPI specifically

- Generates interactive API documentation automatically (`/docs`) from
  your code — you get a free testing UI without writing one.
- Uses Python type hints to validate requests/responses, which catches
  mistakes early and will make the more complex data (Enterprise Systems,
  Use Cases, Risk Assessments) much easier to get right in later phases.
- Async-capable if we ever need it, without switching frameworks.

## Why SQLAlchemy instead of raw SQL

`sqlite3` (Python's built-in library) would work for Phase 1's one tiny
table. But by Phase 7-9 we'll have several related tables (Enterprise
Systems, Use Cases, Risk Assessments, Approvals, Audit Logs) with
relationships between them. SQLAlchemy lets us describe those as Python
classes instead of hand-writing `CREATE TABLE` / `JOIN` SQL strings, which
is a much smaller surface for bugs — and it's still just SQLite
underneath, so nothing about "free and local" changes.

## Why one `HealthPing` table in Phase 1 and nothing else

The instruction for this phase was explicit: **no AI governance yet**.
Rather than build a placeholder business table that we'd throw away, we
built the smallest table that proves something real: every dashboard load
writes one row and reads a count back. If you see that number increase on
refresh, you've proven writes and reads both work — not just that the
server started.

## Request flow for `GET /api/health`

1. Browser (Dashboard.tsx) calls `getHealth()` in `src/api/client.ts`.
2. `fetch("http://localhost:8000/api/health")` sends an HTTP GET.
3. FastAPI's CORS middleware checks the request's origin
   (`http://localhost:5173`) is on the allowed list, and lets it through.
4. The request reaches `health_check()` in `backend/app/routers/health.py`.
5. FastAPI's `Depends(get_db)` opens a SQLAlchemy session against
   `ai_bridge.db`.
6. We `INSERT` one `HealthPing` row and `SELECT COUNT(*)`.
7. FastAPI serializes the returned dict to JSON automatically.
8. The frontend receives it, updates React state, and re-renders the
   dashboard card.

## Folder structure rationale

```
ai-bridge/
├── frontend/        # everything the browser runs
├── backend/          # everything the server runs
├── database/         # reserved: currently the SQLite file lives inside
│                       backend/ for simplicity; kept as a separate folder
│                       name at the repo root because later phases may
│                       add seed scripts / migrations here
├── docs/              # documents like this one
├── mock-data/         # enterprise_systems.json — Phase 2's seed data
├── tests/             # reserved — added once there's real logic to test
│                       (Phase 1/2 have no business logic worth unit-testing yet)
├── infrastructure/    # reserved for the OPTIONAL AWS phase (Phase 2 of the
│                       original roadmap) — empty until then
```

Separating `frontend/` and `backend/` (rather than one mixed folder) means
each has its own dependency file (`package.json` vs `requirements.txt`),
its own run command, and can eventually be deployed independently.

## What deliberately isn't here yet

- No authentication — Phase 6 (Governance Gateway) introduces it, because
  "who is allowed to do this" only matters once there's something worth
  protecting.
- No readiness score, no risk engine, no governance policies — Phases 4,
  5, 6.
- No AI provider abstraction (`MockAIProvider` / `CloudAIProvider`) —
  Phase 10 (AI Playground) is the first phase that actually calls one.

Building these now would mean code you haven't been walked through yet —
against the explicit "learning-first" instruction for this project.

---

# Phase 2: Enterprise Systems

## What Phase 2 adds

Phase 1 proved the pipes work. Phase 2 puts something real into them: a
database table, a set of API endpoints, and two new pages that together
form a small but complete CRUD (Create, Read, Update, Delete) module for
"enterprise systems" — the simulated ERP, HR, Finance, Customer Support,
and Sales systems that later phases will assess, score, and govern.

This phase deliberately does **not** touch AI, risk, or governance. It
only answers one question: *what systems does AI Bridge know about, and
what do we know about each one?* Everything from Phase 3 onward asks
questions like "is THIS system's data AI-ready?" — that question is
meaningless until there's a "this system" to ask it about.

## How the three layers communicate (the new part)

Phase 1 had one round trip: Dashboard → `/api/health` → SQLite → back.
Phase 2 introduces a pattern that repeats for the rest of the project —
a **layer in between** the database and the API response:

```
SQLite row (backend/app/models.py: EnterpriseSystem)
        │  SQLAlchemy reads it as a Python object
        ▼
Pydantic schema (backend/app/schemas.py: EnterpriseSystemOut)
        │  validates + shapes it into an API contract
        ▼
JSON response
        │  fetch() in the browser
        ▼
TypeScript type (frontend/src/types.ts: EnterpriseSystem)
        │  same shape, re-declared in TypeScript so the editor can
        │  catch mistakes (e.g. system.staus instead of system.status)
        ▼
React component (EnterpriseSystems.tsx / SystemDetails.tsx)
```

Three representations of "one enterprise system" exist on purpose — a
SQL row, a Pydantic schema, a TypeScript type — because each layer cares
about different things: the database cares about storage, the API layer
cares about what's a valid request/response, the frontend cares about
what TypeScript can check at compile time. Keeping them separate (rather
than one shared "god object") is what makes it safe to change one layer
(e.g. add a field to the database) without silently breaking another.

## New files, and why each exists

**Backend**
- `backend/app/schemas.py` — Pydantic request/response shapes and the
  five controlled-vocabulary Enums (SystemType, IntegrationType,
  DataClassification, SecurityLevel, SystemStatus).
- `backend/app/routers/systems.py` — the five CRUD endpoints.
- `backend/app/seed_data.py` — loads `mock-data/enterprise_systems.json`
  into the database once, if it's empty.
- `backend/app/models.py` — gained one new table, `EnterpriseSystem`.
- `backend/app/main.py` — now runs the seed step at startup and
  registers the new router.

**Frontend**
- `frontend/src/types.ts` — the TypeScript mirror of `schemas.py`.
- `frontend/src/api/systems.ts` — `listSystems`, `getSystem`,
  `createSystem`, `updateSystem`, `deleteSystem`.
- `frontend/src/components/Layout.tsx` — shared header + navigation,
  now that there's more than one page.
- `frontend/src/components/Badge.tsx` — the small colored status pill,
  reused across both new pages.
- `frontend/src/components/AddSystemModal.tsx` — the "Add System" form.
- `frontend/src/pages/EnterpriseSystems.tsx` — the list/search/filter
  page.
- `frontend/src/pages/SystemDetails.tsx` — the per-system detail page.
- `frontend/src/App.tsx`, `main.tsx` — now use `react-router-dom` to
  switch between pages instead of always rendering `<Dashboard />`.

## Why an Enum-based controlled vocabulary

`system_type`, `integration_type`, `data_classification`, `security_level`,
and `status` are all restricted to a fixed list of values (in
`schemas.py`, and mirrored as TypeScript union types). This isn't
FastAPI/Pydantic ceremony for its own sake — it's how real enterprise
data governance tools work: if "Confidential" can also be typed as
"confidential", "CONFIDENTIAL", or "Sensitive", then Phase 4's readiness
score and Phase 6's policy engine can't reliably group or count systems
by classification. Locking the vocabulary down now, while there are only
five systems, is much cheaper than discovering the inconsistency later.

## Why the mock data lives in its own JSON file

`mock-data/enterprise_systems.json` holds the five example systems as
plain data. `backend/app/seed_data.py` just reads that file and inserts
rows. Keeping "the data" and "the code that loads the data" separate
means you can open the JSON file and edit an example system's fields
without touching any Python — and it's also *why* the `mock-data/`
folder existed (empty) since Phase 1: it was reserved for exactly this.
