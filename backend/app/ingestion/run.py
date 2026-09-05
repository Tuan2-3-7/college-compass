"""Run the College Scorecard sync:  python -m app.ingestion.run [start_page] [--until-done]

Safe to re-run any time - it upserts page by page, so a rate limit never loses
progress; re-running continues from where it stopped (pass the printed
next_page to skip already-synced pages). With --until-done it sleeps out the
hourly DEMO_KEY rate window and keeps going until the full dataset is in -
useful when no SCORECARD_API_KEY is available. Adds the two ingestion columns
to an existing SQLite database first (create_all doesn't alter existing tables).
"""

import sys
import time

from dotenv import load_dotenv
from sqlalchemy import inspect, text

from ..database import Base, SessionLocal, engine
from .scorecard import sync

MIGRATION_COLUMNS = {
    "ipeds_unitid": "INTEGER",
    "intl_student_share": "FLOAT",
}


def migrate() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns("universities")}
    with engine.begin() as conn:
        for column, sqltype in MIGRATION_COLUMNS.items():
            if column not in existing:
                conn.execute(text(f"ALTER TABLE universities ADD COLUMN {column} {sqltype}"))
                print(f"added column universities.{column}")


RETRY_WAIT_SECONDS = 3700  # just over the hourly rate window


def main() -> None:
    load_dotenv()  # pick up SCORECARD_API_KEY from backend/.env
    args = sys.argv[1:]
    until_done = "--until-done" in args
    page_args = [a for a in args if a.isdigit()]
    start_page = int(page_args[0]) if page_args else 0

    migrate()
    db = SessionLocal()
    try:
        while True:
            print(f"Syncing from College Scorecard (from page {start_page})...", flush=True)
            result = sync(db, start_page=start_page)
            print(f"Synced {result['fetched']} schools "
                  f"({result['inserted']} new, {result['updated']} updated).", flush=True)

            if not result["rate_limited"]:
                print("Full sync complete.", flush=True)
                break

            start_page = result["next_page"]
            print(f"Rate limited at page {start_page} of "
                  f"~{(result['total_available'] or 0) // 100 + 1}.", flush=True)
            if not until_done:
                if result["used_demo_key"]:
                    print(
                        "You are on the shared DEMO_KEY. Get a free key at "
                        "https://api.data.gov/signup/, put SCORECARD_API_KEY=<key> in "
                        f"backend/.env, then re-run:  python -m app.ingestion.run {start_page}\n"
                        f"Or run with --until-done to wait out the hourly windows."
                    )
                break
            print(f"Waiting {RETRY_WAIT_SECONDS}s for the rate window to reset...", flush=True)
            time.sleep(RETRY_WAIT_SECONDS)
    finally:
        db.close()


if __name__ == "__main__":
    main()
