"""Run the College Scorecard sync:  python -m app.ingestion.run [start_page]

Safe to re-run any time - it upserts page by page, so a rate limit never loses
progress; re-running continues from where it stopped (pass the printed
next_page to skip already-synced pages). Adds the two ingestion columns to an
existing SQLite database first (create_all doesn't alter existing tables).
"""

import sys

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


def main() -> None:
    load_dotenv()  # pick up SCORECARD_API_KEY from backend/.env
    start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    migrate()
    print("Syncing from College Scorecard...")
    db = SessionLocal()
    try:
        result = sync(db, start_page=start_page)
    finally:
        db.close()

    print(f"\nSynced {result['fetched']} schools "
          f"({result['inserted']} new, {result['updated']} updated).")
    if result["rate_limited"]:
        print(
            f"Stopped early: rate limited at page {result['next_page']} of "
            f"~{(result['total_available'] or 0) // 100 + 1}."
        )
        if result["used_demo_key"]:
            print(
                "You are on the shared DEMO_KEY. Get a free key at "
                "https://api.data.gov/signup/, put SCORECARD_API_KEY=<key> in backend/.env, "
                f"then re-run:  python -m app.ingestion.run {result['next_page']}"
            )
    else:
        print("Full sync complete.")


if __name__ == "__main__":
    main()
