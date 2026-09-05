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

All AI features run behind one provider interface (`backend/app/services/llm.py`).
Set `LLM_PROVIDER` (or leave it on `auto`, which picks the best one configured):

| Provider | Cost | Quality | Use for |
|---|---|---|---|
| `mock` | free | pattern-matching, no reading | tests, CI, offline dev |
| `ollama` | free | good | local development (can't serve a deployed app) |
| `openai_compat` | free tier → pennies | good | **deployment on a budget** (Groq, Together, OpenRouter) |
| `anthropic` | ~6¢/analysis | best | when feedback quality matters most |

`auto` resolves anthropic → openai_compat → mock, so CI never needs a key and
production upgrades itself the moment one is set. Weaker models are handled with
brace-balanced JSON extraction, field coercion, and one automatic retry — the API
contract holds regardless of which provider answers.

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

## Phase 4 (Advanced) ✅

- **Financial-Aid & Scholarship Planner**: personalized forms (FAFSA/CSS for
  domestic; CSS/ISFAA + proof of funds for international), per-school aid picture,
  and scholarship matching by student type, GPA, and major — with one-click
  deadline tracking into the task system. 14 scholarships, 7 verified against
  the sponsor's own site with a source link, 7 labeled sample data.
- **International Student Center**: the full post-application pathway
  (application → admission → financial docs → I-20 → SEVIS → F-1 visa → housing →
  arrival) as a timeline with the current stage inferred from application state,
  plain-language term explanations, and action items per stage.
- **University Comparison**: side-by-side 2-4 schools with 16 aligned attributes
  plus per-user fit (Reach/Target/Likely) and personal deadlines.
- **Application Readiness Score**: one dashboard number across six components
  (academics, activities, essays, major prep, tasks, financial prep) with the
  highest-impact improvement — explicitly *not* an admission prediction.
- **Notifications**: idempotent deadline reminders (due-soon and overdue) with an
  unread-count bell in the header.

## Finishing set ✅

- **Calendar view** (spec #6): month grid of every task due date and application
  deadline, with priority colors, month navigation, and per-day drill-down.
- **Progress Tracking** (spec #18): essay score progression chart (per-draft, with
  hover tooltips and a table view), readiness component history, and per-school
  checklist completion.
- **Account deletion** (privacy requirement): one button in Profile → Danger zone
  removes the account and every piece of the student's data; re-registering the
  same email starts truly fresh. Other users and the shared catalog are untouched.
- **Real data sync** (`python -m app.ingestion.run --until-done`): resumable
  College Scorecard ingestion that waits out DEMO_KEY rate windows when no
  API key is configured.

## Data status

**1,520 real universities** synced from the US Dept. of Education College
Scorecard — admission rates, SAT/ACT bands, costs, enrollment, international
share, and degree programs. Each school shows its `data_source` and
`last_verified` date in the Finder. The 24 originally-curated schools kept their
hand-entered deadlines, application platforms, supplemental-essay counts, TOEFL
minimums, fees, and intl-aid notes — those fields remain unverified sample data
for every school and are labeled as such.

Re-sync any time (safe, idempotent, upserts by IPEDS unitid):

    cd backend && .venv\Scripts\python -m app.ingestion.run

Scholarship data is hand-curated: 7 entries verified against the sponsor's own
site (with `source_url` and `last_verified`), 7 still labeled sample data. Deadlines
and fees for 872 universities come from the Common App requirements grid; re-import
with `python -m app.ingestion.commonapp`.

## Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2, SQLite (swap `DATABASE_URL` for Postgres)
- **Frontend**: React 18, Vite, Tailwind CSS
- **Tests**: pytest (130 tests, incl. the spec's edge cases)

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
