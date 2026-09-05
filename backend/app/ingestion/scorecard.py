"""College Scorecard ingestion - real university data from the US Dept of Education.

Fetches every currently-operating, predominantly-bachelor's institution with
500+ undergraduates and upserts them into the universities table:

- Existing rows (matched by IPEDS unitid, then by normalized name) keep their
  primary key - user applications stay intact - and keep curated fields the
  Scorecard doesn't provide (deadlines, application platforms, supplemental
  essay counts, TOEFL minimums, fees, intl-aid notes).
- Statistics (admit rate, SAT/ACT bands, costs, enrollment, intl share) are
  overwritten with Scorecard values and stamped with data_source + a real
  last_verified date.
- New rows are inserted stats-only; curated fields stay empty until edited.

API key: uses SCORECARD_API_KEY from the environment / backend/.env when set,
else the public DEMO_KEY (rate-limited to ~30 requests/hour - enough for one
full sync). Get a free key at https://api.data.gov/signup/

Known mapping approximations (documented on purpose):
- majors come from Scorecard degree-program flags; "economics" maps from the
  social_science program family and "nursing" from the health family.
- test_policy maps IPEDS admission-test codes: 1=required, 3=neither required
  nor recommended -> "blind", everything else -> "optional".
"""

from __future__ import annotations

import os
import re
import time
from datetime import date

import httpx
from sqlalchemy.orm import Session

from ..models import University

API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

FIELDS = [
    "id",
    "school.name",
    "school.city",
    "school.state",
    "school.ownership",
    "school.school_url",
    "latest.student.size",
    "latest.student.demographics.race_ethnicity.non_resident_alien",
    "latest.admissions.admission_rate.overall",
    "latest.admissions.sat_scores.25th_percentile.critical_reading",
    "latest.admissions.sat_scores.25th_percentile.math",
    "latest.admissions.sat_scores.75th_percentile.critical_reading",
    "latest.admissions.sat_scores.75th_percentile.math",
    "latest.admissions.act_scores.25th_percentile.cumulative",
    "latest.admissions.act_scores.75th_percentile.cumulative",
    "latest.admissions.test_requirements",
    "latest.cost.tuition.in_state",
    "latest.cost.tuition.out_of_state",
    "latest.cost.attendance.academic_year",
    "latest.academics.program.bachelors.computer",
    "latest.academics.program.bachelors.engineering",
    "latest.academics.program.bachelors.biological",
    "latest.academics.program.bachelors.business_marketing",
    "latest.academics.program.bachelors.psychology",
    "latest.academics.program.bachelors.mathematics",
    "latest.academics.program.bachelors.social_science",
    "latest.academics.program.bachelors.health",
]

PROGRAM_TO_MAJOR = {
    "latest.academics.program.bachelors.computer": "computer_science",
    "latest.academics.program.bachelors.engineering": "engineering",
    "latest.academics.program.bachelors.biological": "biology",
    "latest.academics.program.bachelors.business_marketing": "business",
    "latest.academics.program.bachelors.psychology": "psychology",
    "latest.academics.program.bachelors.mathematics": "mathematics",
    "latest.academics.program.bachelors.social_science": "economics",  # approximation
    "latest.academics.program.bachelors.health": "nursing",            # approximation
}

DATA_SOURCE = "College Scorecard API (US Dept of Education)"

# Scorecard names that should match our curated seed names
NAME_ALIASES = {
    "arizona state university campus immersion": "arizona state university",
    "university of washington seattle campus": "university of washington",
}

_CAMPUS_SUFFIX = re.compile(r"\s+main\s+campus$")


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/campus suffixes so seed and Scorecard names match."""
    n = name.lower().replace("-", " ").replace(",", " ").replace(".", "")
    n = re.sub(r"\s+", " ", n).strip()
    n = _CAMPUS_SUFFIX.sub("", n)
    return NAME_ALIASES.get(n, n)


def transform(row: dict) -> dict | None:
    """One flattened Scorecard record -> University column dict (stats only)."""
    name = row.get("school.name")
    if not name:
        return None

    sat_25 = sat_75 = None
    cr25, m25 = (row.get("latest.admissions.sat_scores.25th_percentile.critical_reading"),
                 row.get("latest.admissions.sat_scores.25th_percentile.math"))
    cr75, m75 = (row.get("latest.admissions.sat_scores.75th_percentile.critical_reading"),
                 row.get("latest.admissions.sat_scores.75th_percentile.math"))
    if cr25 is not None and m25 is not None:
        sat_25 = int(cr25 + m25)
    if cr75 is not None and m75 is not None:
        sat_75 = int(cr75 + m75)

    test_req = row.get("latest.admissions.test_requirements")
    test_policy = {1: "required", 3: "blind"}.get(test_req, "optional")

    majors = [major for field, major in PROGRAM_TO_MAJOR.items() if (row.get(field) or 0) >= 1]

    url = row.get("school.school_url") or ""
    if url and not url.startswith("http"):
        url = "https://" + url

    return {
        "ipeds_unitid": row.get("id"),
        "name": name,
        "city": row.get("school.city") or "",
        "state": (row.get("school.state") or "")[:2],
        "control": "public" if row.get("school.ownership") == 1 else "private",
        "undergrad_enrollment": row.get("latest.student.size"),
        "intl_student_share": row.get("latest.student.demographics.race_ethnicity.non_resident_alien"),
        "acceptance_rate": row.get("latest.admissions.admission_rate.overall"),
        "sat_25": sat_25,
        "sat_75": sat_75,
        "act_25": row.get("latest.admissions.act_scores.25th_percentile.cumulative"),
        "act_75": row.get("latest.admissions.act_scores.75th_percentile.cumulative"),
        "test_policy": test_policy,
        "tuition_in_state": row.get("latest.cost.tuition.in_state"),
        "tuition_out_state": row.get("latest.cost.tuition.out_of_state"),
        "cost_of_attendance": row.get("latest.cost.attendance.academic_year"),
        "majors": majors,
        "website": url,  # merged into links by upsert
        "data_source": DATA_SOURCE,
        "last_verified": date.today(),
    }


class RateLimited(Exception):
    """The API said 429 - progress so far is already committed."""


def sync(db: Session, api_key: str | None = None, min_size: int = 500,
         per_page: int = 100, start_page: int = 0) -> dict:
    """Fetch and upsert page by page, so a rate limit never loses progress.

    Returns counts plus `rate_limited` and `next_page` (for resuming).
    """
    key = api_key or os.environ.get("SCORECARD_API_KEY") or "DEMO_KEY"
    if not key.strip() or "PASTE" in key.upper() or " " in key.strip():
        key = "DEMO_KEY"  # placeholder or malformed key -> public fallback
    params = {
        "api_key": key,
        "fields": ",".join(FIELDS),
        "school.operating": 1,
        "school.degrees_awarded.predominant": 3,  # predominantly bachelor's
        "latest.student.size__range": f"{min_size}..",
        "per_page": per_page,
        "sort": "school.name",
    }
    totals = {"fetched": 0, "updated": 0, "inserted": 0}
    page = start_page
    rate_limited = False
    total_available = None
    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(API_URL, params={**params, "page": page})
            if resp.status_code == 429:
                rate_limited = True
                break
            if resp.status_code == 403 and params["api_key"] != "DEMO_KEY":
                print("  API key rejected (403) - falling back to DEMO_KEY")
                params["api_key"] = "DEMO_KEY"
                continue
            resp.raise_for_status()
            data = resp.json()
            rows = [t for t in (transform(r) for r in data["results"]) if t is not None]
            result = upsert(db, rows)
            for k in totals:
                totals[k] += result[k]
            total_available = data["metadata"]["total"]
            print(f"  page {page}: +{result['inserted']} new, {result['updated']} updated "
                  f"({min((page + 1) * per_page, total_available)}/{total_available})")
            page += 1
            if page * per_page >= total_available:
                break
            time.sleep(0.4)  # be polite to the shared DEMO_KEY pool
    return {
        **totals,
        "rate_limited": rate_limited,
        "next_page": page,
        "total_available": total_available,
        "used_demo_key": key == "DEMO_KEY",
    }


# fields Scorecard cannot provide - preserved on existing rows, defaulted on new ones
CURATED_FIELDS = [
    "app_platforms", "deadlines", "supplemental_essay_count", "application_fee",
    "toefl_min", "ielts_min", "offers_intl_aid", "intl_support_notes",
]

STAT_FIELDS = [
    "ipeds_unitid", "city", "state", "control", "undergrad_enrollment",
    "intl_student_share", "acceptance_rate", "sat_25", "sat_75", "act_25", "act_75",
    "test_policy", "tuition_in_state", "tuition_out_state", "cost_of_attendance",
    "data_source", "last_verified",
]


def upsert(db: Session, rows: list[dict]) -> dict:
    """Merge fetched rows into the universities table. Returns counts."""
    existing = db.query(University).all()
    by_unitid = {u.ipeds_unitid: u for u in existing if u.ipeds_unitid}
    by_name = {normalize_name(u.name): u for u in existing}

    updated = inserted = 0
    for row in rows:
        uni = by_unitid.get(row["ipeds_unitid"]) or by_name.get(normalize_name(row["name"]))
        website = row.pop("website", "")
        if uni is not None:
            for field in STAT_FIELDS:
                setattr(uni, field, row[field])
            # majors: union of curated + Scorecard-confirmed
            uni.majors = sorted(set(uni.majors or []) | set(row["majors"]))
            if website:
                uni.links = {**(uni.links or {}), "website": website}
            updated += 1
        else:
            uni = University(
                name=row["name"],
                majors=row["majors"],
                links={"website": website} if website else {},
                **{f: row[f] for f in STAT_FIELDS},
            )
            db.add(uni)
            inserted += 1
    db.commit()
    return {"updated": updated, "inserted": inserted, "fetched": len(rows)}
