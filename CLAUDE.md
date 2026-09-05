# College Compass — dev notes

AI-powered college-admissions coach. Spec: docs/SPEC.md. All 4 phases built.

## Commands (run from repo root)

- Backend dev server: `cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000`
- Frontend dev server: `cd frontend && npm run dev` (port 5173, proxies /api → 8000)
- Tests: `cd backend && .venv/Scripts/python -m pytest tests/ -q`
- Real-data sync: `cd backend && .venv/Scripts/python -m app.ingestion.run [start_page] [--until-done]`

## Conventions & gotchas

- SQLite dev DB at `backend/collegecompass.db` (gitignored). `create_all` runs on
  startup but never ALTERs existing tables — new University columns go through the
  mini-migration in `app/ingestion/run.py`.
- All AI features go through `app/services/llm.py` (MockLLM active without
  ANTHROPIC_API_KEY; ClaudeLLM model claude-opus-5 when the key is in backend/.env).
  The essay coach must never write essay content for the student.
- University/scholarship rows carry `data_source` + `last_verified`; sample-seeded
  rows have `last_verified = NULL` and the UI must label them unverified. Never
  present seed numbers as real.
- Checklist, analyzer, advisor, readiness, recommendations are pure-function
  services in `app/services/` — keep them DB-free and unit-testable.
- Per-user data isolation is tested; every new user-owned route must filter by
  `user_id` and 404 on foreign rows.
- Estimates language: Reach/Target/Likely, readiness, and essay scores are always
  framed as heuristic estimates, never admission predictions.
