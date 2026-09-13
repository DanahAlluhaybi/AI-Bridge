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

---

# Phase 3: Legacy-to-AI Adapter

## What Phase 3 adds

Phase 2 answered "what systems does AI Bridge know about?" Phase 3
answers the next question: *if we actually pulled data out of one of
those systems, is it usable?* Real enterprise data is messy — missing
fields, inconsistent city names, phone numbers in five formats,
duplicate rows, unlabeled sensitive fields. Phase 3 simulates pulling
raw data from one enterprise system and runs it through a fixed
pipeline that cleans and labels it, so the mess is visible instead of
hidden.

This is the piece of AI Bridge that gives the project its name: it's
the *adapter* between a legacy system's actual data shape and something
an AI system could safely be pointed at later. It deliberately stops
short of that — no AI Readiness Score, no governance decision, no AI
call. It only prepares and describes the data.

## The pipeline

```
Source Data (CSV / JSON / REST API / SQL Database)
        │  adapter/extract.py
        ▼
Raw records (list of dicts)
        │  adapter/validate.py — checks the RAW data, before anything
        │  is fixed: missing required fields, invalid emails,
        │  duplicate records
        ▼
Validation issues + duplicate flags
        │  adapter/normalize.py — per field: city/country name
        │  aliases ("jeddah" / "JEDDAH" / "جدة" -> "Jeddah"), date
        │  formats, phone numbers (-> +966...), amounts (-> float)
        ▼
Normalized records + normalization issues
        │  adapter/classify.py — which fields are sensitive
        │  (national_id, amount, email, phone, employee_id)? that
        │  drives one label: Public / Internal / Sensitive
        ▼
Classified, AI-Ready records
        │  adapter/pipeline.py — orchestrates all of the above,
        │  saves one ProcessingJob (summary) + one ProcessingResult
        │  per record + one DetectedIssue per problem found
        ▼
ProcessingJobDetail (what the Data Adapter page renders)
```

Each stage is its own file with one job. `pipeline.py` doesn't decide
*how* to validate or normalize anything — it only decides *when* to
call each stage and what to do with what comes back. That separation is
what makes the pipeline testable piece by piece, and is also why these
four modules (`extract`, `validate`, `normalize`, `classify`) have zero
dependency on FastAPI or the database — they're plain Python functions
that take data in and return data out.

## Why the mock data has two "kinds" of source

`sales_csv_source.csv` and `support_json_source.json` are **real**
files — actually read from disk with `csv.DictReader` / `json.load`,
the same way a real CSV export or JSON API response would be. There's
no local, free, zero-setup way to stand up a real SQL server or REST
API for a learning project, so `erp_sql_source.json` and
`hr_rest_api_source.json` / `finance_sql_source.json` are **simulated**:
they're JSON files that *represent* what a SQL query result or REST API
response would look like, loaded by functions in `extract.py` whose
docstrings say plainly what a real version would do instead (run a SQL
query over a DB connection; call `httpx.get(...)` against a real
endpoint). This keeps the four source types honestly *different inputs
to the same pipeline*, without pretending a fake network call or a fake
database connection is something it isn't.

## Why classification and sensitive-field detection are one function

`classify.py`'s `classify_record()` returns both a single
Public/Internal/Sensitive label AND the specific list of sensitive
fields detected, from one pass over the record. Both answers come from
the same starting question — "which of this record's fields actually
have a value in a sensitive-ish field?" — so computing them separately
would mean scanning the same record twice for no benefit. The rule
itself (HIGH: national_id, amount; MEDIUM: email, phone, employee_id;
Sensitive if any HIGH or 2+ MEDIUM; Internal if exactly 1 MEDIUM; else
Public) is intentionally simple and spelled out in the module's
docstring — it's a demonstrable example of a classification engine, not
a production one.

## A design decision: one endpoint, not four

The Phase 3 brief describes four separate operations — process CSV,
process JSON, process REST API data, process SQL data. The backend
exposes **one** endpoint instead:
`POST /api/adapter/sources/{source_id}/process`. Each `AdapterSource`
already knows its own `source_type`; the endpoint looks that up and
lets `extract.py`'s `EXTRACTORS` dict dispatch to the right extraction
function. Everything after extraction — validation, normalization,
classification, detection — is identical regardless of source format.
Writing that same pipeline four times just because the input format
differs would be duplicated code pretending to be four features; one
endpoint with a type-driven internal branch is the more honest
implementation of the same requirement.

## A design decision: where the phone-format check lives

Early in building this, the plan was to check whether a phone number
"looks valid" in both `validate.py` (a quick digit-count check on the
raw value) and `normalize.py` (the actual parse into `+966...` format).
That would have reported the *same* broken phone number as two separate
issues. The check was kept in exactly one place — `normalize.py`, since
that's where the real parse attempt happens and it's the more
authoritative source — and removed from `validate.py` entirely. It's a
small thing, but it's the kind of duplicate-reporting bug that's easy to
miss until you run real data through a pipeline twice and see the same
problem listed twice.

## New files, and why each exists

**Backend**
- `backend/app/adapter/extract.py` — reads/simulates each of the four
  source types into a plain list of record dicts.
- `backend/app/adapter/validate.py` — checks raw records: missing
  required fields, invalid emails, duplicate records (by ID or by
  name+city+phone).
- `backend/app/adapter/normalize.py` — cleans city/country names,
  dates, phone numbers, amounts; returns the cleaned record plus any
  issues it couldn't fix.
- `backend/app/adapter/classify.py` — Public/Internal/Sensitive
  classification + sensitive-field detection.
- `backend/app/adapter/pipeline.py` — `run_adapter()`, the orchestrator
  that calls all of the above in order and saves the result.
- `backend/app/routers/adapter.py` — the six `/api/adapter/*`
  endpoints.
- `backend/app/models.py` — four new tables: `AdapterSource`,
  `ProcessingJob`, `ProcessingResult`, `DetectedIssue`.
- `backend/app/schemas.py` — the matching Pydantic schemas and four new
  Enums (SourceType, DataClassificationLevel, IssueType, IssueSeverity).
- `backend/app/seed_data.py` — `seed_adapter_sources()`, one
  `AdapterSource` per Phase 2 enterprise system.
- `mock-data/adapter_sources/` — the five raw source files described
  above.

**Frontend**
- `frontend/src/types.ts` — TypeScript mirror of the Phase 3 schemas.
- `frontend/src/api/adapter.ts` — `listAdapterSources`, `processSource`.
- `frontend/src/pages/DataAdapter.tsx` — the source-type/system
  pickers, Run Adapter button, summary cards, Before/After table, and
  Detected Issues table.
- `frontend/src/components/Badge.tsx` — gained `Sensitive`, `Info`, and
  `Warning` colors (`Public`/`Internal` already existed from Phase 2
  and mean the same thing here).
- `frontend/src/components/Layout.tsx`, `App.tsx` — new "Data Adapter"
  nav tab and `/adapter` route.

## What deliberately isn't here yet

- No real AI Readiness Score — `ai_readiness_status` is a simple
  pass/fail ("Passed Basic Checks" / "Needs Attention") based on
  whether any quality issue remains, not a calculated score with
  weighted factors. That's Phase 4.
- No governance policy, no risk engine, no AI Passport, no human
  approval, no AWS/Bedrock, no real LLM call — Phases 5 onward.
- No cascading delete from `EnterpriseSystem` to `AdapterSource` — if a
  system is deleted, its adapter source is simply skipped (seeding) or
  shown as "Unknown system" (the API), rather than the delete cascading
  or being blocked. A known simplification, not an oversight.

---

# Phase 4: AI Readiness Assessment

## What Phase 4 adds

Phase 3 answered "if we pulled this system's data out, is it usable?"
Phase 4 answers a bigger question: "is this system, as a whole, ready
to support an AI use case?" That's not just about data quality — it's
also about how the data is reached, how secure the system is, how
sensitive the data is, whether anyone formally owns AI decisions made
with it, and whether a human would review those decisions. The brief
is explicit that this must be **deterministic, rule-based, and
reproducible** — never an LLM call — because a readiness score that
could change between two runs on the same data, or that can't be
explained, is useless for the governance story this whole project is
about.

## Why not an LLM

Three concrete reasons, not just "the brief says so":

1. **Reproducibility.** The same system, assessed twice with no
   changes, must get the same score both times. An LLM's output can
   vary between calls even with the same prompt (especially at
   non-zero temperature) — that alone disqualifies it for something
   meant to be trusted and compared over time.
2. **Explainability.** A governance tool has to be able to say
   *exactly* why a score is what it is — "Privacy scored 45 because 50%
   of records were Sensitive and this system is classified
   Confidential" is a sentence a rule-based formula can produce
   directly from its own logic. An LLM's reasoning, even when it
   sounds plausible, isn't a guaranteed, checkable derivation of the
   number it outputs.
3. **Cost and dependency.** The whole project is 100% free and local.
   A real scoring engine that requires an API call (paid or not) for
   every assessment breaks that constraint and adds a network
   dependency to something that should work instantly, offline. Rule
   evaluation over data already in SQLite costs nothing and returns
   instantly.

(An LLM *could* eventually help generate a written summary of an
already-computed score — but computing the score itself never goes
through one, in this project or in a real governance tool.)

## The eight dimensions, briefly

Each is scored 0-100 by a plain function in
`backend/app/readiness/dimensions.py`, built entirely from data AI
Bridge already has (Phase 2's system profile, Phase 3's latest adapter
run) — nothing is invented or looked up externally:

- **Data Quality (15%)** — the last adapter run's issue rate (missing
  values, bad formats, duplicates). No adapter run yet → neutral 50.
- **Data Availability (10%)** — connection status + whether a data
  source is configured + whether a Phase 3 source exists at all.
- **Data Integration (15%)** — how AI-friendly the integration method
  is: REST API and SQL Database (queryable, on-demand) score higher
  than JSON and CSV (batch exports).
- **Technical Readiness (15%)** — has the pipeline actually been
  proven end-to-end (an adapter run exists), is the integration method
  queryable, is the system currently connected.
- **Security (15%)** — directly reuses Phase 2's `security_level`.
- **Privacy (10%)** — the proportion of Sensitive records the last
  adapter run found, plus Phase 2's `data_classification`.
- **Governance (10%)** — a documented proxy: ownership already exists
  in Phase 2 (every system has an owner), but no real governance
  policy or audit trail exists yet (Phase 6/11), so a higher data
  classification subtracts more, showing that gap honestly.
- **Human Oversight (10%)** — another documented proxy: no real
  approval workflow exists yet (Phase 9), so this measures the SIZE of
  the gap — more sensitive data implies more oversight will eventually
  be needed, and the score reflects that it isn't built yet.

Governance and Human Oversight are the two dimensions most worth
revisiting once Phase 6, 9, and 11 exist — their formulas are proxies
on purpose, and the docstrings in `dimensions.py` say so directly
rather than pretending otherwise.

## The scoring formula

```
overall_score = round(
    Data Quality × 0.15 + Data Availability × 0.10 +
    Data Integration × 0.15 + Technical Readiness × 0.15 +
    Security × 0.15 + Privacy × 0.10 +
    Governance × 0.10 + Human Oversight × 0.10
)
```

Weights live in `backend/app/readiness/engine.py`'s `WEIGHTS` dict —
one dictionary, checked at import time to sum to 100%, so changing how
much a dimension counts is a one-line edit. The four heaviest-weighted
dimensions (Data Quality, Data Integration, Technical Readiness,
Security) are the ones backed by the most concrete signal right now;
the four at 10% each are real but thinner signals (Data Availability
is mostly binary flags; Governance and Human Oversight are the
documented proxies above).

`overall_score` maps to a level via `READINESS_THRESHOLDS` (also in
`engine.py`, also a one-line edit to change):

```
90-100 → AI Ready
75-89  → Mostly Ready
50-74  → Needs Improvement
0-49   → Not Ready
```

Any dimension scoring below `WEAK_DIMENSION_THRESHOLD` (70) produces
one gap (from `GAP_MESSAGES`) and one recommendation (from
`RECOMMENDATION_MESSAGES`) — both plain lookup dictionaries keyed by
dimension name, so the text is easy to find and reword.

## Worked example

**Customer Support System** (JSON, Connected, Medium security,
Confidential), after a Phase 3 adapter run that found 2 quality issues
and 3 Sensitive records out of 6:

| Dimension | Score | Why |
|---|---|---|
| Data Quality | 67 | 2/6 records had an issue → 100 − 33 |
| Data Availability | 100 | Connected + data source configured + adapter source exists |
| Data Integration | 75 | JSON — structured, but a batch export |
| Technical Readiness | 85 | Adapter has run (+40), JSON isn't queryable (+15), Connected (+30) |
| Security | 65 | Medium security level |
| Privacy | 45 | 50% Sensitive (−35) + Confidential classification (−20) |
| Governance | 65 | Base 60 + Connected (+20) − Confidential penalty (−15) |
| Human Oversight | 75 | 100 − Confidential penalty (−25) |

```
0.15×67 + 0.10×100 + 0.15×75 + 0.15×85 + 0.15×65 + 0.10×45 + 0.10×65 + 0.10×75
= 10.05 + 10 + 11.25 + 12.75 + 9.75 + 4.5 + 6.5 + 7.5 = 72.3 → 72
```

**Overall: 72 / 100 → Needs Improvement**, with gaps on Data Quality,
Security, Privacy, and Governance (all below 70) and one
recommendation per gap. This was verified by actually running the
scoring functions in the cloud sandbox against this exact input (see
the Verification note below) before it ever reached your machine.

## New files, and why each exists

**Backend**
- `backend/app/readiness/dimensions.py` — the eight pure scoring
  functions. No FastAPI/SQLAlchemy dependency, same design choice as
  Phase 3's `extract`/`validate`/`normalize`/`classify`.
- `backend/app/readiness/engine.py` — weights, thresholds, gap/
  recommendation text, and `run_assessment()`, which pulls the values
  those pure functions need out of the database and saves the result.
- `backend/app/routers/readiness.py` — `POST /systems/{id}/assess`,
  `GET /systems/{id}/readiness/latest`, `GET /systems/{id}/readiness/history`,
  `GET /readiness/{id}`, `GET /readiness/summary`.
- `backend/app/models.py` — one new table, `AIReadinessAssessment`
  (a history table — assessing the same system twice adds a row, it
  doesn't overwrite the last one).
- `backend/app/schemas.py` — `AIReadinessAssessmentOut`,
  `DimensionGap`, `ReadinessSummary`, `SystemGovernanceGap`, and the
  `ReadinessLevel` Enum.

**Frontend**
- `frontend/src/types.ts` + `frontend/src/api/readiness.ts` — the
  TypeScript mirror and API client.
- `frontend/src/pages/SystemDetails.tsx` — the "AI Readiness" section
  is no longer a disabled button: it fetches the latest assessment,
  lets you run a new one, and shows the score, level, eight dimension
  bars, gaps, recommendations, and a collapsible assessment history.
- `frontend/src/pages/Dashboard.tsx` — a new "AI Readiness overview"
  card built entirely from `GET /api/readiness/summary` — average
  score, systems assessed, counts by level, and top governance gaps,
  none of it hardcoded.
- `frontend/src/components/Badge.tsx` — gained the four readiness
  level colors (AI Ready / Mostly Ready / Needs Improvement / Not
  Ready).

## Verification note (Phase 4 specific)

Same approach as Phase 3: `dimensions.py` has zero FastAPI/SQLAlchemy
dependency, so it was executed directly in the cloud sandbox — not
just syntax-checked — against several realistic inputs built from the
actual Phase 2 seed data and Phase 3 mock datasets (Customer Support
System, HR Management System, Sales Database, and a system with no
adapter run yet). The Customer Support System result matched the
hand-calculated worked example above exactly (72, Needs Improvement),
and the "no adapter run yet" case correctly defaulted Data Quality and
Privacy to the documented neutral 50 rather than guessing.

## What deliberately isn't here yet

- No risk engine — Phase 5 turns readiness + classification into a
  Low/Medium/High/Critical risk level.
- No governance gateway, no AI Passport, no human approval workflow,
  no real AI use cases, no audit logging, no AWS/Bedrock, no LLM call
  anywhere in the scoring — Phases 5 onward.
- Governance and Human Oversight scores are documented proxies (see
  above) — they'll get real signal once Phase 6, 9, and 11 exist, and
  their formulas are written to be easy to replace at that point.

# Phase 5: AI Risk Engine

## What Phase 5 adds

A deterministic, rule-based AI Risk Score per enterprise system —
same reasoning as Phase 4 (reproducible, explainable, zero-cost, no
LLM), but answering a different question: not "is this system ready?"
but "how much would it cost us if something went wrong here?" Risk and
readiness are related but distinct — a system can be reasonably ready
(decent data quality, connected, integrated) and still carry high risk
if its data is highly classified and its security is weak.

## The four risk factors

Each scored 0-100 by a plain function in `backend/app/risk/factors.py`
— higher means more risk, the opposite direction from readiness's
dimension scores:

- **Data Sensitivity (30%)** — directly from the system's
  `data_classification`: Public is low risk, Restricted is high.
- **Security Gap (25%)** — the inverse of `security_level`: Critical
  security is low risk, Low security is high.
- **Readiness Gap (25%)** — `100 − latest AI Readiness overall_score`.
  No readiness assessment yet is treated as a neutral 50, not
  automatically low or high risk.
- **Oversight Gap (20%)** — reuses `readiness/dimensions.py`'s
  `score_human_oversight()` directly (`100 − that score`) rather than
  duplicating the same classification-based table in two places.

## The scoring formula

```
risk_score = round(
    Data Sensitivity × 0.30 + Security Gap × 0.25 +
    Readiness Gap × 0.25 + Oversight Gap × 0.20
)
```

Weights live in `backend/app/risk/engine.py`'s `WEIGHTS` dict, checked
at import time to sum to 100%. `risk_score` maps to a level via
`RISK_THRESHOLDS` (also in `engine.py`):

```
75-100 → Critical
50-74  → High
25-49  → Medium
0-24   → Low
```

Any factor scoring at or above `SIGNIFICANT_FACTOR_THRESHOLD` (60) is
surfaced as a specific risk driver (from `FACTOR_MESSAGES`), the same
pattern Phase 4 uses for gaps.

## Worked example

A system with **Restricted** data classification, **Low** security,
and an AI Readiness Score of 40:

| Factor | Score | Why |
|---|---|---|
| Data Sensitivity | 90 | Restricted classification |
| Security Gap | 75 | Low security level |
| Readiness Gap | 60 | 100 − 40 |
| Oversight Gap | 40 | Restricted classification implies more oversight than exists |

```
0.30×90 + 0.25×75 + 0.25×60 + 0.20×40
= 27 + 18.75 + 15 + 8 = 68.75 → 69
```

**Overall: 69 / 100 → High**, with risk drivers on Data Sensitivity and
Security Gap (both at or above 60). Verified by running
`risk/factors.py` directly in the cloud sandbox — it has no
FastAPI/SQLAlchemy dependency, same as `readiness/dimensions.py` — and
confirming this exact result by hand.

## New files, and why each exists

**Backend**
- `backend/app/risk/factors.py` — the four pure risk-contribution
  functions. No FastAPI/SQLAlchemy dependency, same design choice as
  `readiness/dimensions.py`; imports `score_human_oversight` from
  there directly instead of duplicating its logic.
- `backend/app/risk/engine.py` — weights, thresholds, driver text, and
  `run_risk_assessment()`, which pulls what those pure functions need
  out of the database (including the system's latest readiness score,
  if any) and saves the result.
- `backend/app/routers/risk.py` — `POST /systems/{id}/risk-assess`,
  `GET /systems/{id}/risk/latest`, `GET /systems/{id}/risk/history`,
  `GET /risk/{id}`, `GET /risk/summary`.
- `backend/app/models.py` — one new table, `AIRiskAssessment` (a
  history table, same shape as `AIReadinessAssessment`).
- `backend/app/schemas.py` — `AIRiskAssessmentOut`, `RiskDriver`,
  `RiskSummary`, `SystemRiskFlag`, and the `RiskLevel` Enum.

**Frontend**
- `frontend/src/types.ts` + `frontend/src/api/risk.ts` — the
  TypeScript mirror and API client.
- `frontend/src/pages/SystemDetails.tsx` — a new "AI Risk" section:
  fetches the latest risk assessment, lets you run a new one, and
  shows the score, level, four factor bars, risk drivers, and a
  collapsible assessment history.
- `frontend/src/pages/Dashboard.tsx` — a new "AI Risk overview" card
  built entirely from `GET /api/risk/summary` — average risk score,
  systems assessed, counts by level, and the highest risk systems,
  none of it hardcoded.
- No changes needed in `Badge.tsx` — the Low/Medium/High/Critical
  labels already have colors defined there from Phase 2's security
  level field.

## What deliberately isn't here yet

- No real AI use cases yet, so risk is assessed per enterprise system
  rather than per use case — Phase 7 introduces use cases, and a
  later pass can extend risk assessment to them once they exist.
- No AI Passport, no human approval workflow, no audit logging, no
  AWS/Bedrock, no LLM call anywhere in the scoring.

# Phase 6: AI Adoption & Automation Opportunities

## What Phase 6 adds

Everything so far answers "is this system ready, and how risky is
it?" Phase 6 turns those two numbers into an actual answer to the
question that matters: **should this system adopt AI, and if so,
where should AI actually be applied first?**

That's two separate questions, answered by two separate, equally
deterministic layers:

```
Question 1: Can this system adopt AI?
  Readiness + Risk  ->  AI Adoption Decision   (adoption/decision.py)

Question 2: If yes, where should AI actually be applied?
  Recorded activities  ->  Automation Opportunities, ranked  (adoption/opportunities.py)
```

Neither layer runs its own new scoring model — the Adoption Decision
is a live read of a system's most recent Readiness and Risk
assessments (re-assessing either one changes the decision immediately,
nothing to keep in sync by hand), and Automation Opportunities score
plain recorded facts about an activity, not the system as a whole.

## The AI Adoption Decision

`backend/app/adoption/decision.py`'s `determine_adoption_decision()`
takes a Readiness Score and a Risk Level and returns one of five
outcomes. Risk is checked first — a **Critical**-risk system can never
read as ready, no matter its data quality — then a readiness floor
(`READINESS_MINIMUM = 60`) gates everything else, and only once both
checks pass does risk level decide between Good Candidate and
Conditional:

| Readiness | Risk | Decision |
|---|---|---|
| ≥ 75 | Low | **Good Candidate** |
| ≥ 75 | Medium or High | **Conditional** |
| 60–74 | Low or Medium | **Not Yet** |
| 60–74 | High | **Not Recommended** |
| < 60 | any | **Not Yet** |
| any | Critical | **Not Recommended** |
| missing readiness or risk | — | **Insufficient Information** |

## Automation Opportunities

Every recorded `SystemActivity` (`backend/app/models.py`) carries six
Low/Medium/High fields — frequency, volume, manual effort, human
judgment, data sensitivity, process standardization — plus the
activity's own description and a specific `ai_opportunity` sentence
authored for that activity (never a generic template reused across
systems; see `tests/automation/test_relevance.py`).
`adoption/opportunities.py` turns those into:

- **Automation potential** — High/Medium/Low. Repetitive, standardized,
  low-judgment work scores High; heavy human judgment caps this at Low
  no matter how repetitive the task looks on paper.
- **Business impact** — how much volume/frequency/effort this activity
  represents.
- **Automation risk** — sensitive data or heavy judgment, either one on
  its own, makes automating this risky.
- **Human oversight** — Required / Recommended / Not required, driven
  by judgment and automation risk together.
- **Priority score** — a ranking number (not shown to the user)
  combining all four, so opportunities can be sorted "best to automate
  first" rather than shown as an unordered list.

An activity missing required fields is never guessed at — it comes
back with every field `null` and a plain "insufficient information"
message instead of a confident-sounding recommendation.

## New files, and why each exists

**Backend**
- `backend/app/adoption/decision.py` — the five-outcome decision
  framework above; pure, no database access.
- `backend/app/adoption/opportunities.py` — the per-activity scoring
  functions and the priority ranking formula; pure, same design as
  `risk/factors.py`.
- `backend/app/adoption/engine.py` — the only piece that touches the
  database: looks up a system's latest Readiness/Risk results and its
  activities, and assembles the decision + ranked opportunities (or
  the full company-wide overview).
- `backend/app/routers/adoption.py` — `GET /systems/{id}/adoption`,
  `GET /adoption/summary`. No POST/"assess" endpoint — the decision is
  always live, not a separate saved run.
- `backend/app/models.py` — one new table, `SystemActivity` (a system
  can have several; not a history table like the assessments).
- `backend/app/schemas.py` — `AdoptionDecision`, `AutomationPotential`,
  `BusinessImpact`, `AutomationRisk`, `HumanOversight`,
  `AutomationOpportunityOut`, `SystemAdoptionOut`, `AdoptionOverview`.
- `backend/app/seed_data.py` — sixteen demo activities across the five
  existing systems, specific to each one's own domain.

**Frontend**
- `frontend/src/pages/AIAdoption.tsx` — the new AI Adoption Overview
  page (`/adoption`), one row per system, ranked by adoption
  suitability rather than plain readiness.
- `frontend/src/pages/SystemDetails.tsx` — a new "AI Adoption" section
  showing the decision, then the ranked, expandable opportunity list —
  Readiness + Risk → Decision → Opportunities, in that order.
- `frontend/src/components/Layout.tsx` + `Icons.tsx` — a new nav item
  and icon; no other page changed.
- `frontend/src/components/Badge.tsx` — five new label colors for the
  adoption decisions.

**Testing**
- `tests/fixtures/` — a synthetic dataset (enterprise systems,
  activities, expected outcomes) kept entirely separate from the demo
  data above — never loaded into `ai_bridge.db`.
- `tests/adoption/`, `tests/automation/` — `unittest`-based tests
  against specific scenarios and edge cases.
- `tests/evaluation/evaluation_runner.py` — runs the whole synthetic
  dataset through both engines and prints a real, computed accuracy
  report. Run it with `python tests/evaluation/evaluation_runner.py`
  from the project root.

## What deliberately isn't here yet

- No AI Use Cases, AI Passport, human approval workflow, or audit
  logging yet — those are Phases 7–11, immediately below. No
  AWS/Bedrock, no LLM call anywhere in the scoring — every label above
  comes from plain Python rules over data AI Bridge already has.

# Phase 7-12: AI Use Cases, Human Approval, AI Passport, AI Playground & Audit Log

## What this batch adds

Phase 6 answers "should this **system** adopt AI, and where first?"
That's a per-system question, answered once and re-read live. This
batch answers a narrower, per-proposal question that Phase 6
deliberately left open: **should this *specific* use of AI go ahead,
and does a human need to sign off first?** This is the "AI Governance
Gateway" the original project roadmap named — built here as a policy
layer over Phase 6's own decision, not a parallel system.

```
Use case proposed (name, purpose, owner, requested automation level)
        |
        v
Governance policy  (use_cases/policy.py)
  inputs: requested automation level + system's Risk Level + system's AI Adoption decision
  output: ALLOW | HUMAN_APPROVAL | BLOCK   -- computed ONCE, stored on the use case
        |
        +-- ALLOW / BLOCK --> use case status set immediately (Approved / Rejected)
        |
        +-- HUMAN_APPROVAL --> a Pending ApprovalRequest is created automatically
                                  |
                                  v
                     Approval Center: a human approves or rejects it
                                  |
                                  v
                  use case status updated to match the decision
                                  |
                                  v
         Approved use case can be run in the AI Playground (MockAIProvider)
                                  |
                                  v
         Every step above is written to the Audit Log
```

## Two decisions, deliberately kept separate

Phase 6's `adoption/decision.py` and this batch's `use_cases/policy.py`
look similar (both take Readiness/Risk-shaped inputs and return a
small fixed set of outcomes) but answer different questions and are
computed differently on purpose:

| | AI Adoption Decision (Phase 6) | Governance Policy (this batch) |
|---|---|---|
| Question | Should this *system* use AI at all? | Should this *specific proposed use* go ahead? |
| Inputs | Readiness Score + Risk Level | Requested automation level + Risk Level + the system's Adoption decision |
| When computed | Live, every time it's read | **Once**, at the moment the use case is proposed |
| Why | Nothing to keep in sync — re-assessing Readiness/Risk should immediately change the system-level picture | A use case's recorded decision is meant to be a stable snapshot (the AI Passport should reflect what was actually decided, not silently drift if the system is re-assessed later) |

## The governance policy

`backend/app/use_cases/policy.py`'s `determine_policy()` takes the
requested automation level (Advisory / Assisted / Full), the system's
current Risk Level, and its AI Adoption decision, and returns
`(ALLOW | HUMAN_APPROVAL | BLOCK, reason)`. Risk and the Adoption
decision are checked first — two hard stops that override every
automation level:

| Condition | Result |
|---|---|
| Risk Level missing (system never risk-assessed) | **HUMAN_APPROVAL** — a human reviews, Bridge never guesses |
| Risk Level is **Critical** | **BLOCK** |
| Adoption decision is **Not Recommended** | **BLOCK** |

Past those, the requested automation level decides how much scrutiny
is needed — more automation asked for means a cleaner picture is
required to skip a human:

| Automation level | Passes straight through (ALLOW) when | Otherwise |
|---|---|---|
| **Advisory** (AI suggests, a human always acts) | always, unless a hard stop above fired | — |
| **Assisted** (AI acts, a human reviews along the way) | Risk is Low or Medium | Risk High → HUMAN_APPROVAL |
| **Full** (AI acts on its own once approved) | Risk is Low **and** Adoption decision is Good Candidate | Risk Medium/High, or Adoption Conditional/Not Yet → HUMAN_APPROVAL |

`STATUS_FOR_POLICY` maps the outcome straight to the use case's
resulting status: ALLOW → Approved, BLOCK → Rejected, HUMAN_APPROVAL →
Proposed (until the Approval Center decides it).

## Human Approval

An `ApprovalRequest` only ever exists because a use case's policy
decision came back HUMAN_APPROVAL — there's no way to create one
directly (`backend/app/routers/use_cases.py` creates it in the same
step it creates the use case). Deciding one
(`POST /api/approvals/{id}/decide`) updates the request *and* the
linked `AIUseCase.status` together in one transaction, records who
decided it and when, and refuses a second decision on an
already-decided request.

## AI Passport

`GET /api/use-cases/{id}/passport` is a read-only, one-screen summary
built for an approver or auditor who shouldn't have to piece the story
together across three pages: what's being proposed, the system's data
classification and security level, the Readiness/Risk/Adoption picture
*as it was* when the decision was made, and the policy decision itself
with its reason. It reads the use case's stored `policy_decision` /
`policy_reason` — never recomputes them — which is exactly the
snapshot-vs-live distinction the table above describes.

## AI Playground

`backend/app/playground/mock_provider.py`'s `generate_response()` is
the free, deterministic stand-in for a real AI model this whole
project has been building toward being *ready* to eventually plug in
without redesigning anything: it hashes the prompt
(`hashlib.sha256`) to pick one of four response templates, so the same
prompt always produces the same response, at zero cost, with no API
key. `POST /api/playground/ask` refuses any use case that isn't
`Approved` — the governance chain isn't just advisory, nothing actually
*runs* until it's cleared. A later `CloudAIProvider` could implement
the same `generate_response(prompt, use_case_name)` signature against
a real model without anything calling it changing.

## Audit Log

`backend/app/audit.py` is one tiny helper (`audit.log(db, action,
summary, entity_type, entity_id)`) called from inside `routers/
use_cases.py`, `routers/approvals.py`, and `routers/playground.py`
right after each makes a change worth recording. `GET /api/audit-log`
is read-only by design — entries are never edited, only appended to,
by the routers that already have a database session open.

## New files, and why each exists

**Backend**
- `backend/app/use_cases/policy.py` — the ALLOW/HUMAN_APPROVAL/BLOCK
  framework above; pure, no database access, same design as
  `adoption/decision.py`.
- `backend/app/playground/mock_provider.py` — the deterministic mock
  AI response generator.
- `backend/app/audit.py` — the one shared audit-logging helper.
- `backend/app/routers/use_cases.py` — `GET /use-cases` (list),
  `GET /use-cases/{id}`, `POST /use-cases` (runs the policy, sets
  status, auto-creates a Pending approval if needed), `DELETE
  /use-cases/{id}`, `GET /use-cases/{id}/passport`.
- `backend/app/routers/approvals.py` — `GET /approvals` (filterable by
  status), `POST /approvals/{id}/decide`.
- `backend/app/routers/playground.py` — `POST /playground/ask`,
  `GET /playground/history`.
- `backend/app/routers/audit_log.py` — `GET /audit-log`.
- `backend/app/models.py` — four new tables: `AIUseCase`,
  `ApprovalRequest`, `PlaygroundRequest`, `AuditLogEntry`. None are
  seeded with demo data — like Readiness/Risk assessments, they only
  ever come from something a user actually does.
- `backend/app/schemas.py` — `AutomationLevel`, `UseCaseStatus`,
  `PolicyDecision`, `AIUseCaseCreate`, `AIUseCaseOut`,
  `ApprovalRequestOut`, `ApprovalDecision`, `AIPassportOut`,
  `PlaygroundRequestCreate`, `PlaygroundRequestOut`, `AuditLogEntryOut`.

**Frontend**
- `frontend/src/pages/AIUseCases.tsx` (`/use-cases`) — every proposed
  use case with its policy/status badges, and a "Propose use case"
  modal.
- `frontend/src/pages/AIPassport.tsx` (`/use-cases/:id/passport`) —
  the one-screen summary described above.
- `frontend/src/pages/Approvals.tsx` (`/approvals`) — the Approval
  Center, filterable by status, with an approve/reject flow.
- `frontend/src/pages/Playground.tsx` (`/playground`) — pick an
  Approved use case, send a prompt, see the response and history.
- `frontend/src/pages/AuditLog.tsx` (`/audit-log`) — the plain,
  newest-first trail.
- `frontend/src/pages/Dashboard.tsx` — a new "AI Governance overview"
  card (use cases proposed/Approved/Rejected, pending approvals).
- `frontend/src/components/AddUseCaseModal.tsx` — the "Propose Use
  Case" form, same controlled-form pattern as `AddSystemModal.tsx`.
- `frontend/src/components/Layout.tsx` + `Icons.tsx` — four new nav
  items and icons.
- `frontend/src/components/Badge.tsx` — new label colors for use case
  status and policy decisions.
- `frontend/src/api/use-cases.ts`, `api/approvals.ts`,
  `api/playground.ts`, `api/audit.ts` — one file per resource, same
  pattern as `api/adoption.ts`.

**Testing**
- `tests/governance/test_policy.py` — every branch of
  `determine_policy()`, including both hard stops and the fail-safe
  for missing risk data.
- `tests/governance/test_mock_provider.py` — determinism, truncation,
  and labeling checks for the mock AI provider. No synthetic-dataset
  evaluation run here, unlike Phase 6 — there's no per-activity scoring
  to measure accuracy against, just a decision table and a template
  picker to exercise every branch of.

## What deliberately isn't here yet

- No real AI model call anywhere — the AI Playground's responses are
  entirely deterministic and template-based (`MockAIProvider`). A
  `CloudAIProvider` implementing the same interface is a clearly-scoped
  future addition, not a redesign.
- No editing a use case's requested automation level after the fact —
  that would mean re-running the policy and potentially invalidating an
  existing approval decision, left for a later pass.
- No AWS/Bedrock deployment — that remains the separate, optional
  Phase 2 of the roadmap.
