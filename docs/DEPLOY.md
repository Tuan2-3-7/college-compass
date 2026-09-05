# Deploying College Compass (free tier)

A stack that costs **$0/month** and has no forced cold-start penalty.

| Layer | Service | Why |
|---|---|---|
| Frontend | **Cloudflare Pages** | Free, fast globally, custom domains included |
| Backend | **Google Cloud Run** | Scales to zero, ~1-3s cold start, 2M requests/month free, deploys from GitHub |
| Database | **Neon** Postgres | Free tier that does **not** expire |
| AI | **Groq** free tier | Hosted Llama, OpenAI-compatible, nothing to self-host |

Deliberately **not** Render's free tier: it sleeps after ~15 minutes and the
next visitor waits ~50 seconds. Also avoid Render's free Postgres, which is
deleted after 90 days.

---

## 1. Database (Neon)

Create a project at neon.tech, copy the connection string, and convert the
driver prefix for psycopg 3:

    postgresql://...        ->  postgresql+psycopg://...

## 2. Generate a JWT secret

    python -c "import secrets; print(secrets.token_urlsafe(48))"

Without this the app refuses to start in production - the dev default is
public in the source, so anyone could forge a login for any student.

## 3. Backend (Cloud Run) - from the browser, no local CLI

Cloud Run builds straight from GitHub, so neither gcloud nor Docker needs to
be installed locally.

1. console.cloud.google.com -> create or pick a project (billing must be
   enabled; the free tier still applies)
2. **Cloud Run** -> **Deploy container** -> **Service**
3. Choose **Continuously deploy from a repository** -> **Set up with Cloud
   Build** -> authorise GitHub -> pick the repo, branch `main`
4. Build type **Dockerfile**, source location `/backend/Dockerfile`
5. Region: **us-east5** (Columbus) to sit beside a Neon `us-east-2` database
6. Authentication: **Allow unauthenticated invocations**
7. Under **Container -> Variables & Secrets**, add:

   | Name | Value |
   |---|---|
   | `ENVIRONMENT` | `production` |
   | `DATABASE_URL` | the Neon string, prefix swapped to `postgresql+psycopg://` |
   | `JWT_SECRET` | the secret from step 2 |
   | `CORS_ORIGINS` | your Pages URL (fill in after step 4; use a placeholder first) |
   | `LLM_PROVIDER` | `openai_compat` |
   | `OPENAI_COMPAT_BASE_URL` | `https://api.groq.com/openai/v1` |
   | `OPENAI_COMPAT_API_KEY` | the Groq key |
   | `OPENAI_COMPAT_MODEL` | `llama-3.1-8b-instant` |

The container runs `alembic upgrade head` before serving, so the schema is
created on first deploy and migrated on later ones. If the service fails to
start, read the logs: the production guard refuses to boot on a dev JWT
secret, a SQLite URL, or a localhost CORS origin, and says which.

Prefer the CLI? `gcloud run deploy --source backend/` does the same thing.

To use Claude instead, swap the last four vars for:

    LLM_PROVIDER=anthropic
    ANTHROPIC_API_KEY=sk-ant-...

and uncomment `anthropic>=1.0` in `requirements.txt`.

## 4. Frontend (Cloudflare Pages)

Point Pages at the repo with:

- Build command: `npm run build`
- Output directory: `dist`
- Root directory: `frontend`
- Environment variable: `VITE_API_BASE=https://<your-cloud-run-url>`

## 5. Load the university data

The seed ships 24 sample schools. To load all ~1,520 real ones, run the sync
once against the production database:

    DATABASE_URL=<the production URL> SCORECARD_API_KEY=<key> \
      python -m app.ingestion.run

## 6. Verify

    curl https://<cloud-run-url>/api/health
    curl https://<cloud-run-url>/api/ai/status     # confirms the live provider

Then register an account through the deployed UI and confirm the essay coach
returns real feedback.

---

## Before you accept real users

Still outstanding, and **not** code:

- **Privacy policy, terms, and a signup consent checkbox.** The app stores
  GPAs, test scores, immigration status, and personal essays, and many users
  will be minors. Account deletion is implemented (Profile -> Danger zone);
  the disclosures are not.
- Consider whether you need a data-retention policy and a contact address for
  deletion requests.

## Operational notes

- Rate limiting is in-process (`app/ratelimit.py`), which is correct for a
  single instance. If you scale to multiple instances, move the counters to
  Redis - the limiter is called from one place, so the swap is small.
- Set `min-instances=1` on Cloud Run (~$5/month) to remove cold starts if the
  app gets real traffic.
- Back up Neon regularly; the free tier has limited history.
