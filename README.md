# 🧭 College Compass

An AI-powered personalized college admissions coach: helps domestic and international
students discover suitable US universities, understand requirements, manage the entire
application process with personalized checklists and deadlines, and (in later phases)
improve essays, estimate competitiveness, and prepare for their intended major.

Full scope: [docs/SPEC.md](docs/SPEC.md) · Build phases: Foundation → Intelligence → AI → Advanced.

## Current status — Phase 1 (Foundation) ✅

- Accounts (register/login, JWT) with per-user data isolation
- Student profile: domestic/international, first-year/transfer/graduate, GPA, tests,
  courses, activities, awards, languages, financial-aid need
- University database seeded with 24 **sample** universities (illustrative, unverified —
  every record carries `data_source` and `last_verified`)
- University Finder: filter by major, state, cost, public/private, selectivity, intl aid;
  sortable; add to your list with a chosen application round
- Application Manager: statuses (not started → decision received), deadlines per round,
  remove, notes
- **Personalized checklist**: auto-generated per student × university × round — an
  international CS first-year gets a different list from a domestic biology transfer
- Dashboard: profile completeness, per-application progress, overdue/due-soon tasks, and
  a rule-based "What should I do next?"

## Phase 2 (Intelligence) ✅

- **Competitiveness Analyzer**: subscores (academics, course rigor, activities,
  leadership, awards, major preparation) + weighted overall, and per-university
  Reach/Target/Likely with plain-language reasons. Conservative rules: sub-15%-admit
  schools are always a reach; international applicants get a strength penalty.
  Always framed as a heuristic estimate, never a probability.
- **Major Advisor**: per-major roadmap (academic prep, skills, experiences,
  application evidence) for 8 majors, personalized against the student's profile
- **Skill-Gap Analysis**: per-skill strong/developing/missing with cited evidence
  from the profile, plus a prioritized improvement plan
  (`backend/app/services/analyzer.py`, `major_advisor.py`, `backend/app/data/majors.py`)

## Phase 3 (AI) ✅ — currently in mock mode

All AI features run behind one provider interface (`backend/app/services/llm.py`):
a **deterministic mock** (active now — free, offline, labeled "demo mode" in the UI)
and a **real Claude adapter** (model `claude-opus-5`, official `anthropic` SDK, with
refusal handling and server-side fallbacks) that activates automatically when
`ANTHROPIC_API_KEY` is set in `backend/.env` (and `pip install anthropic` is run).

- **Essay Coach**: essays → versioned drafts → analysis. Seven dimension scores
  (prompt alignment, storytelling, personal voice, specificity, reflection,
  structure, grammar), paragraph-level notes, cliché/repetition detection,
  weaknesses, and coaching questions. The coach never writes essay content.
  Draft-over-draft score progression is tracked per essay.
- **AI Tutor**: persistent chat. Mock mode covers a fixed glossary of admissions
  topics (course rigor, supplements, I-20/SEVIS/F-1, FAFSA/CSS, test-optional, …)
  and says honestly when a question is out of demo scope.
- **Personalized recommendations** (`/api/recommendations`): rule-based synthesis
  across deadlines, checklist state, competitiveness subscores, essay scores, and
  list balance — surfaced on the dashboard as "Recommended next steps".

## Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2, SQLite (swap `DATABASE_URL` for Postgres)
- **Frontend**: React 18, Vite, Tailwind CSS
- **Tests**: pytest (70 tests, incl. the spec's edge cases)

## Run it

Backend (from `backend/`):

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --port 8000

Frontend (from `frontend/`):

    npm install
    npm run dev

Open http://localhost:5173 — the Vite dev server proxies `/api` to the backend.
API docs: http://localhost:8000/docs

Tests (from `backend/`):

    .venv\Scripts\python -m pytest tests/ -q

## Layout

    backend/app/            FastAPI application
      models.py             SQLAlchemy models (users, profiles, universities, applications, tasks)
      routers/              auth, profile, universities, applications, tasks, dashboard
      services/checklist.py personalized checklist generation (pure functions)
      seed.py               sample university data (UNVERIFIED — dev only)
    backend/tests/          pytest suite
    frontend/src/           React app (pages, components, api client)
    docs/SPEC.md            full product spec

## Data & safety principles

- Sample university data is illustrative; the UI labels it and shows `last_verified`.
- No admission outcomes are promised; estimates (Phase 2) are clearly framed as estimates.
- One student can never see another's data (enforced + tested).
- Real data ingestion (College Scorecard API / IPEDS) replaces the seed in a later phase.
