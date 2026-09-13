# AI Bridge

**Making Enterprise Systems AI-Ready Without Replacing Them.**

AI Bridge is a learning project that simulates an Enterprise AI Infrastructure
platform: something that sits between a company's existing systems (ERP, HR,
Finance, CRM...) and an AI model, and adds data readiness checks, risk
assessment, governance policy, and human approval in between.

This is **not** a chatbot. The chatbot-looking part (the "AI Playground",
built much later) is a thin demo on top of the real point of the project:
governance and controlled AI adoption.

> **Status: Phase 12 — AI Use Cases, Human Approval, AI Passport, AI
> Playground & Audit Log.** Everything through Phase 6 answered "should
> this *system* adopt AI, and where first?" This batch answers the
> narrower, per-proposal question: "should this *specific* use of AI go
> ahead?" A use case (name, purpose, owner, requested automation level)
> is checked against a governance policy — built from the system's Risk
> Level and AI Adoption decision — that comes back ALLOW, BLOCK, or
> HUMAN_APPROVAL. HUMAN_APPROVAL creates a Pending approval automatically;
> a human decides it in the Approval Center. Every use case has an AI
> Passport — a one-screen, read-only summary of what was decided and why.
> Once Approved, a use case can be tried out in the AI Playground against
> a free, deterministic mock AI model (no paid API, ever). Every step
> along the way is written to an Audit Log. Still fully rule-based, still
> no real LLM anywhere.

## Design system

The frontend was rebuilt around one consistent, light, enterprise-SaaS
visual language (Inter typeface, a neutral slate/indigo palette,
`rounded-xl`/`shadow-card` surfaces, a fixed sidebar) instead of each
page styling itself independently. Shared building blocks live in
`frontend/src/components/`: `Card`, `Button`, `Badge`, `PageHeader`,
`MetricCard`, `EmptyState`, and `Icons` (hand-drawn line icons, no
external icon package). Every page composes these rather than
one-off `<div className="...">` styling, and the app now opens on a
proper Home page (`/`) instead of the data-dense Dashboard, which
moved to `/dashboard`.

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
│                       adapter_sources/ — the 5 raw source files the Data
│                       Adapter reads from (CSV/JSON, real; REST API/SQL,
│                       simulated as JSON — see docs/ARCHITECTURE.md)
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

## Checklist — Phase 3 (Legacy-to-AI Adapter) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/adapter` endpoints (sources, process, jobs, results, issues)
- [ ] The nav bar now shows **Dashboard**, **Enterprise Systems**, and **Data Adapter**
- [ ] `http://localhost:5173/adapter` shows a "Source type" dropdown, an "Enterprise system" dropdown, and a **Run Adapter** button
- [ ] Picking a source type (e.g. "CSV") narrows the system dropdown to only the system(s) that use it
- [ ] Clicking **Run Adapter** (with a system selected) shows four summary numbers, an AI Readiness Status pill, a Before/After table, and a Detected Issues table — all within a second or two
- [ ] The Before/After table shows visibly different values in the "before" vs "after" columns for city, phone, and date (e.g. "jeddah" → "Jeddah")
- [ ] Rows for duplicate records show a ⚠ next to the row number and a light amber background
- [ ] The Classification column shows Public/Internal/Sensitive badges, and running the **HR Management System** source shows mostly (or entirely) "Sensitive" — it carries national IDs and salaries
- [ ] The Detected Issues table lists at least one "Missing Value", one "Duplicate Record", and one "Sensitive Field" issue across the five sources
- [ ] The AI Readiness Status pill says "Needs Attention" whenever any quality issue exists, and is explicitly labeled as *not* the real AI Readiness Score
- [ ] Running the adapter again on the same system creates a new job (check `GET /api/adapter/jobs` in `/docs` — the list grows) rather than overwriting the old one

## Checklist — Phase 4 (AI Readiness Assessment) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/systems/{id}/assess`, `/api/systems/{id}/readiness/latest`, `/api/systems/{id}/readiness/history`, `/api/readiness/{id}`, and `/api/readiness/summary`
- [ ] On any system's details page, the "AI Readiness" section says "Not assessed yet" and has a clickable (not greyed out) **Assess AI Readiness** button
- [ ] Clicking it shows a score out of 100, a readiness level badge (AI Ready / Mostly Ready / Needs Improvement / Not Ready), and eight dimension bars with numbers
- [ ] A system you've already run the Legacy-to-AI Adapter on (Phase 3) scores differently on Data Quality/Privacy than one you haven't — try **Customer Support System** (run the adapter on it first, then assess) vs. a system you haven't run the adapter on yet
- [ ] Below the bars, a **Gaps** list and a **Recommendations** list appear whenever any dimension scores below 70 — for a system with no run adapter yet, Data Quality and Privacy should show as gaps (score 50, "we don't know yet")
- [ ] Clicking **Re-assess AI Readiness** again creates a new assessment — click **View past assessments** to see more than one entry with different timestamps
- [ ] The Dashboard page now shows an "AI Readiness overview" card with real numbers (average score, systems assessed, AI Ready/Needs Improvement/Not Ready counts) that change as you assess more systems — not hardcoded, and 0/5 assessed before you assess anything
- [ ] The Dashboard's "Top governance gaps" list is empty until at least one assessed system scores below 70 on Governance

## Checklist — Phase 5 (AI Risk Engine) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/systems/{id}/risk-assess`, `/api/systems/{id}/risk/latest`, `/api/systems/{id}/risk/history`, `/api/risk/{id}`, and `/api/risk/summary`
- [ ] On any system's details page, a new "AI Risk" section says "Not risk-assessed yet" and has a clickable **Assess AI Risk** button
- [ ] Clicking it shows a risk score out of 100, a risk level badge (Low/Medium/High/Critical), and four risk factor bars with numbers
- [ ] A system with **Restricted** data classification and **Low** security scores much higher risk than a **Public**/**Critical**-security system — try comparing two systems with different profiles
- [ ] Below the bars, a **Risk drivers** list appears whenever any factor scores 60 or higher, explaining which factor is pushing the score up
- [ ] Clicking **Re-assess AI Risk** again creates a new assessment — click **View past assessments** to see more than one entry with different timestamps
- [ ] The Dashboard page now shows an "AI Risk overview" card with real numbers (average risk score, systems assessed, Low/High/Critical counts, highest risk systems) — not hardcoded, and 0/5 assessed before you assess anything

## Checklist — Phase 6 (AI Adoption & Automation Opportunities) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/systems/{id}/adoption` and `/api/adoption/summary`
- [ ] The nav bar now shows **AI Adoption**, and `http://localhost:5173/adoption` shows a table of every system with its Readiness, Risk, Adoption decision, and top opportunity
- [ ] On any system's details page, a new "AI Adoption" section shows a decision badge (Good Candidate / Conditional / Not Yet / Not Recommended / Insufficient Information) with a one-line reason
- [ ] A system with no Readiness or Risk assessment yet shows **Insufficient Information** rather than a guess
- [ ] Below the decision, a ranked list of Automation Opportunities appears — click one to expand it into automation potential, business impact, risk, human oversight, and a recommendation
- [ ] Re-assessing AI Readiness or AI Risk on a system immediately updates its Adoption decision, without a page reload
- [ ] Two different systems (e.g. HR Management System vs. Sales Database) show clearly different activities and AI opportunities — never the same list

## Checklist — Phase 7 (AI Use Cases) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/use-cases` (GET list, GET one, POST, DELETE)
- [ ] The nav bar now shows **AI Use Cases**, and `http://localhost:5173/use-cases` shows a table (empty at first, with an explanation)
- [ ] Clicking **Propose use case**, picking a system, filling in name/purpose/owner/automation level, and submitting adds a row immediately with a Policy badge (ALLOW / HUMAN_APPROVAL / BLOCK) and a Status badge (Approved / Proposed / Rejected)
- [ ] Proposing the same use case with **Advisory** automation on a low-risk system comes back ALLOW/Approved immediately; the same use case with **Full** automation on the same system comes back HUMAN_APPROVAL/Proposed instead
- [ ] A system that hasn't been risk-assessed yet always comes back HUMAN_APPROVAL, never a guess
- [ ] **Remove** deletes a use case from the table without a page reload

## Checklist — Phase 8 (AI Passport) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/use-cases/{id}/passport`
- [ ] Clicking **AI Passport** on any use case row opens a one-screen summary: the use case itself, the system's data classification/security level, the Readiness score/Risk level/Adoption decision behind the policy call, and the policy decision + reason
- [ ] The Passport never recomputes the policy decision live — it always shows what was actually decided when the use case was proposed, even if the system is re-assessed afterward

## Checklist — Phase 9 (Human Approval) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/approvals` and `/api/approvals/{id}/decide`
- [ ] The nav bar now shows **Approval Center**, and `http://localhost:5173/approvals` defaults to showing only **Pending** requests
- [ ] Proposing a use case that comes back HUMAN_APPROVAL immediately creates a Pending entry here — the reason shown matches the AI Passport's policy reason
- [ ] Entering your name, optionally a note, and clicking **Approve** or **Reject** updates both the approval and the use case's status together (check the use case's row on `/use-cases` — its Status badge changes without you touching that page)
- [ ] Switching the filter to **Approved** / **Rejected** / **All** shows past decisions with who decided them and when
- [ ] Trying to decide an already-decided approval a second time is refused

## Checklist — Phase 10 (AI Playground) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/playground/ask` and `/api/playground/history`
- [ ] The nav bar now shows **AI Playground**; with no Approved use cases yet, `/playground` explains that instead of showing an empty form
- [ ] Once a use case is Approved (directly, or through the Approval Center), it appears in the Playground's dropdown
- [ ] Typing a prompt and clicking **Run prompt** shows a response labeled `MockAIProvider — Development Mode`, and running the exact same prompt again produces the exact same response
- [ ] The prompt/response pair appears in the History list below, newest first
- [ ] Trying to hit `/api/playground/ask` (via `/docs`) for a use case that is **not** Approved is refused with a clear message

## Checklist — Phase 11 (Audit Log) is working when...

- [ ] `http://localhost:8000/docs` now also shows `/api/audit-log`
- [ ] The nav bar now shows **Audit Log**, and `http://localhost:5173/audit-log` lists entries newest first
- [ ] Proposing a use case, deciding an approval, and running a Playground prompt each add exactly one new entry here, in plain language (not raw JSON)

## Checklist — Phase 12 (Governance overview on the Dashboard) is working when...

- [ ] The Dashboard (`/dashboard`) now shows an **AI Governance overview** card: use cases proposed, Approved, Rejected, and how many approvals are currently Pending
- [ ] The card lists up to 5 approvals waiting on a decision, with a link straight to the Approval Center
- [ ] The counts update the moment you propose a use case or decide an approval elsewhere in the app, on the next Dashboard visit — nothing here is hardcoded

## Testing & Evaluation

Phases 7–11's decision logic (`use_cases/policy.py`) and mock AI provider
(`playground/mock_provider.py`) are both pure, dependency-free functions,
covered the same way `adoption/decision.py` was in Phase 6 — hand-written
`unittest` cases under `tests/governance/`, not a full synthetic-dataset
evaluation run (there's no per-activity scoring here to measure accuracy
against, just a decision table to exercise every branch of):

```bash
python -m unittest discover -s tests -p "test_*.py"
```

runs everything — Phase 6's evaluation-backed tests and Phase 7–11's
governance tests together (52 tests total). `tests/governance/test_policy.py`
walks every automation-level/risk/adoption-decision combination the policy
distinguishes, including the fail-safe (missing risk → always
HUMAN_APPROVAL) and the two hard stops (Critical risk, Not Recommended
adoption) that override every automation level. `tests/governance/
test_mock_provider.py` checks the one thing that actually matters for a
mock model: same input always gives the same output, long prompts get
truncated instead of blowing up the response, and short ones don't.

Phase 6 ships with a small, dependency-free test suite under `tests/`,
using a synthetic dataset that's kept completely separate from the
demo data seeded into `ai_bridge.db` — see `tests/fixtures/`.

```bash
python tests/evaluation/evaluation_runner.py
```

run from the project root, loads the synthetic dataset, runs both the
Adoption Decision framework and the Automation Opportunity scoring
against a hand-defined set of expected outcomes, and prints a real,
computed accuracy report (not hardcoded numbers) — see that file's
docstring for what each metric means. The individual `unittest` files
under `tests/adoption/` and `tests/automation/` can also be run on
their own, e.g. `python -m unittest tests.adoption.test_adoption_decision`.

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
git commit -m "Phases 7-12: AI Use Cases, Human Approval, AI Passport, AI Playground, Audit Log"
git push
```

## What's next (not built yet)

Every phase in the original roadmap is now built. The only thing left
is the optional Phase 2 of the project — a real AWS deployment (the
local, zero-cost stack above is otherwise the complete product). That
phase is deliberately kept separate and untouched until you're ready
for it, so nothing above depends on it.
