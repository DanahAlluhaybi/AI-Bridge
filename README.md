# AI Bridge

**Making Enterprise Systems AI-Ready Without Replacing Them.**

AI Bridge is a learning project that simulates an Enterprise AI Infrastructure
platform: something that sits between a company's existing systems (ERP, HR,
Finance, CRM...) and an AI model, and adds data readiness checks, risk
assessment, governance policy, and human approval in between.

This is **not** a chatbot. The chatbot-looking part (the "AI Playground",
built much later) is a thin demo on top of the real point of the project:
governance and controlled AI adoption.

> **Status: Phase 1 — Foundation.** Only the base stack is built so far:
> a React dashboard talking to a FastAPI backend talking to a SQLite
> database. No governance, risk, or AI logic yet — that comes in later
> phases, one at a time.

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
├── mock-data/         (reserved for Phase 2 — simulated enterprise systems)
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

## Checklist — Phase 1 is working when...

- [ ] `http://localhost:8000/` returns a JSON welcome message
- [ ] `http://localhost:8000/docs` shows the interactive API docs with a `/api/health` endpoint
- [ ] Calling `GET /api/health` (from `/docs`, or `curl http://localhost:8000/api/health`) returns `"status": "ok"` and `"database": "connected"`
- [ ] A file `backend/ai_bridge.db` exists after that call
- [ ] `http://localhost:5173` loads the dashboard with the AI Bridge header
- [ ] The dashboard's "Backend connection" card turns **green** and shows real numbers (status, database, health checks recorded, server time)
- [ ] Refreshing the dashboard increases "Health checks recorded" by 1 each time (proof it's live data, not hardcoded)
- [ ] Stopping the backend and refreshing the dashboard shows a **red** error card instead of a crash

If the last two both behave as described, you've proven the full chain —
frontend, backend, and database — actually works together, not just that
each piece runs in isolation.

## A note on verification

This project was scaffolded and syntax-checked in a cloud sandbox whose
network policy blocks package installs (`pip`/`npm`) for security reasons —
so I could not run the full `pip install` / `npm install` / `uvicorn` /
`npm run dev` loop end-to-end before handing it to you. The Python files
passed a syntax check, and everything follows standard, well-documented
FastAPI/Vite patterns, but please run the checklist above yourself the
first time — and tell me what you see (including any error) so we can fix
anything together before moving to Phase 2.

## Git

This repo was initialized with `git init` and has one commit ("Phase 1:
Foundation"). Going forward, a reasonable habit is one commit per phase:

```bash
git add .
git commit -m "Phase 2: Enterprise Systems"
```

## What's next (not built yet)

Phase 2 adds simulated enterprise systems (Corporate ERP, HR, Finance,
Support, Sales) so later phases have something realistic to connect to,
assess, and govern. We build it only when you're ready and have confirmed
Phase 1 works for you.
