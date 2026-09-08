# AI Bridge

**Making Enterprise Systems AI-Ready Without Replacing Them.**

AI Bridge is a learning project that simulates an Enterprise AI Infrastructure
platform: something that sits between a company's existing systems (ERP, HR,
Finance, CRM...) and an AI model, and adds data readiness checks, risk
assessment, governance policy, and human approval in between.

This is **not** a chatbot. The chatbot-looking part (the "AI Playground",
built much later) is a thin demo on top of the real point of the project:
governance and controlled AI adoption.

> **Status: Phase 2 — Enterprise Systems.** The Phase 1 foundation (React
> dashboard ↔ FastAPI ↔ SQLite) plus a full Enterprise Systems module:
> five simulated systems (ERP, HR, Finance, Customer Support, Sales) you
> can list, search, filter, view in detail, add, and remove. No
> readiness scoring, risk engine, or governance logic yet — that starts
> in Phase 4 onward.

## Why this stack (zero cost, by design)

| Layer      | Choice                        | Why |
|------------|--------------------------------|-----|
| Frontend   | React + TypeScript + Vite + Tailwind | Free, runs entirely on your machine, huge learning resources, fast dev server |
| Backend    | Python + FastAPI               | Free, you likely already know Python, automatic interactive API docs at `/docs` |
| Database   | SQLite                         | Free, zero setup — it's a single file, no server/account needed |
| AI         | `MockAIProvider` (from Phase 10 onward) | Free — simulates AI responses so you never need a paid API key for the MVP |

No paid APIs, no paid hosting, no AWS required. AWS is an **optional**
phase 2, added only after the local version works and you understand it.

## Project structure

```
ai-bridge/
├── frontend/          React + TypeScript + Vite + Tailwind UI
├── backend/           Python + FastAPI API
├── database/          (reserved — SQLite file currently lives in backend/)
├── docs/               Architecture and design notes
├── mock-data/         enterprise_systems.json — the 5 seed enterprise systems
├── tests/              (reserved — automated tests, added as logic appears)
├── infrastructure/     (reserved — optional AWS deployment, Phase 2 of the roadmap)
├── .gitignore
└── README.md            <- you are here
```

Folders marked "reserved" exist now so the structure is visible from day
one, but are intentionally empty until the phase that needs them.

## Prerequisites

Install these once, on your own machine (all free):

- **Python 3.10+** — check with `python3 --version`
- **Node.js 18+** — check with `node --version`
- **Git** — check with `git --version`

## Running it locally

### 1. Backend (FastAPI + SQLite)

```bash
cd backend
python3 -m venv .venv

# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

You should see Uvicorn say it's running on `http://127.0.0.1:8000`.
A file `ai_bridge.db` (SQLite) will appear in `backend/` the first time
you hit an endpoint that touches the database — that's expected, it's
created automatically.

Open **http://localhost:8000/docs** in a browser — that's a free,
auto-generated interactive explorer for every endpoint. Try the
`GET /api/health` endpoint from there.

### 2. Frontend (React + Vite)

Open a **second terminal** (leave the backend running in the first one):

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — you should see the AI Bridge dashboard.
If `npm install` complains about `react-router-dom` missing, that's new
in Phase 2 — `npm install` in a folder with an updated `package.json`
always picks up new dependencies automatically, no extra step needed.

## Checklist — Phase 1 (Foundation) is working when...

- [ ] `http://localhost:8000/` returns a JSON welcome message
- [ ] `http://localhost:8000/docs` shows the interactive API docs
- [ ] Calling `GET /api/health` returns `"status": "ok"` and `"database": "connected"`
- [ ] The Dashboard's "Backend connection" card turns **green** with real numbers
- [ ] Refreshing the dashboard increases "Health checks recorded" by 1 each time
- [ ] Stopping the backend and refreshing shows a **red** error card instead of a crash

## Checklist — Phase 2 (Enterprise Systems) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/systems` endpoints (GET list, GET one, POST, PUT, DELETE)
- [ ] The nav bar at the top now shows **Dashboard** and **Enterprise Systems**
- [ ] `http://localhost:5173/systems` shows a table with **5 systems already filled in**: Corporate ERP, HR Management System, Finance Database, Customer Support System, Sales Database
- [ ] Typing in the search box narrows the table live (try "Finance")
- [ ] The status filter and integration-type filter both narrow the table
- [ ] Clicking **View Details →** on any row opens that system's detail page with four sections: Overview, Integration, Data, AI Readiness
- [ ] The AI Readiness section says "Not assessed yet" and its button is greyed out / unclickable
- [ ] Clicking **+ Add System**, filling the form, and submitting adds a new row to the table without a page reload
- [ ] Clicking **Remove this system** on a details page asks for confirmation, then returns you to the list with that system gone
- [ ] Restarting the backend does **not** re-add the 5 example systems if you've already changed them (seeding only happens once, on an empty database)

## A note on verification

This project is built and syntax-checked in a cloud sandbox whose network
policy blocks package installs (`pip`/`npm`) for security reasons, so
I can't run the full install/run loop end-to-end before handing each
phase to you. Python files are syntax-checked every time; everything
follows standard, well-documented FastAPI/React patterns. Please run the
checklist yourself and tell me what you see (including any error) — that's
how we catch anything together before moving to the next phase.

## Git

One commit per phase is a reasonable habit:

```bash
git add .
git commit -m "Phase 2: Enterprise Systems"
git push
```

## What's next (not built yet)

Phase 3 (Legacy-to-AI Adapter) takes one enterprise system's raw data and
runs it through extraction → validation → normalization → classification
→ sensitive-data detection, showing a before/after in the UI. It builds
directly on the enterprise systems created in this phase. We build it
only when you're ready and have confirmed Phase 2 works for you.
