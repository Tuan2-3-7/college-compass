"""Common App Requirements Grid ingestion.

Source: https://content.commonapp.org/Files/ReqGrid.pdf - the Common
Application's own annually-published grid of first-year deadlines, fees, and
requirements for its 1,000+ member colleges. This is the authoritative free
source for exactly the fields the College Scorecard does not publish:
application deadlines by round, US and international application fees, whether
supplemental writing is required, and English-proficiency requirements.

It is a positional PDF table - which round a date belongs to is determined by
its x-coordinate, not its order - so parsing uses pdfplumber word positions
against the column map below rather than plain text extraction.

Run via:  python -m app.ingestion.commonapp [path-to-pdf]
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy.orm import Session

from ..models import University
from .scorecard import name_variants, normalize_name

PDF_URL = "https://content.commonapp.org/Files/ReqGrid.pdf"
DATA_SOURCE = "Common App Requirements Grid"

# x-position of each column header on the page (points). A word belongs to the
# column whose header it sits nearest, bounded by the midpoints of neighbours.
COLUMNS = [
    ("name", 21.0),
    ("school_type", 84.2),
    ("early_decision", 120.6),
    ("early_decision_2", 148.5),
    ("early_action", 179.4),
    ("early_action_2", 207.3),
    ("restrictive_early_action", 236.7),
    ("regular", 263.2),
    ("fee_us", 299.1),
    ("fee_intl", 331.1),
    ("fee_waiver", 360.5),
    ("personal_essay", 401.4),
    ("courses_grades", 431.5),
    ("portfolio", 461.6),
    ("writing_supplement", 496.6),
    ("test_policy", 528.6),
    ("tests_used", 559.8),
    ("english_proficiency", 601.8),
    ("rec_teacher", 647.2),
    ("rec_other", 674.0),
    ("rec_midyear", 701.1),
    ("rec_counselor", 729.0),
]

_BOUNDS: list[tuple[str, float, float]] = []
for i, (field, x) in enumerate(COLUMNS):
    lo = 0.0 if i == 0 else (COLUMNS[i - 1][1] + x) / 2
    hi = 10_000.0 if i == len(COLUMNS) - 1 else (COLUMNS[i + 1][1] + x) / 2
    _BOUNDS.append((field, lo, hi))

DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
FEE_RE = re.compile(r"^\$(\d+)$")
SCHOOL_TYPES = {"Coed", "Women", "Men"}


def _column_for(x: float) -> str:
    for field, lo, hi in _BOUNDS:
        if lo <= x < hi:
            return field
    return "name"


def _to_mmdd(value: str) -> str | None:
    """'11/01/2026' -> '11-01'. The app stores recurring MM-DD deadlines."""
    if not DATE_RE.match(value):
        return None
    month, day, _year = value.split("/")
    return f"{int(month):02d}-{int(day):02d}"


NAME_COLUMN_RIGHT = 84.0


def parse_page(page) -> list[dict]:
    """Extract one page's rows.

    A row is anchored by the line carrying the school type (Coed/Women/Men);
    the school name may wrap onto extra lines. Names are read by cropping the
    name column rather than from the word list: two wrapped lines overlap
    vertically, so sorting the band by x interleaves them character by
    character ("Abile n e C h r i").
    """
    words = [w for w in page.extract_words() if w["top"] > 100]
    if not words:
        return []

    # anchor rows, by the vertical band of the school-type cell
    anchors = [
        w for w in words
        if w["text"] in SCHOOL_TYPES and _column_for(w["x0"]) == "school_type"
    ]
    anchors.sort(key=lambda w: w["top"])

    out: list[dict] = []
    for index, anchor in enumerate(anchors):
        top, bottom = anchor["top"], anchor["bottom"]
        # the name may wrap above and below the anchor line; bound the crop by
        # the neighbouring rows so we never steal another school's text
        upper = 100.0 if index == 0 else (anchors[index - 1]["bottom"] + top) / 2
        lower = (
            page.height if index == len(anchors) - 1
            else (bottom + anchors[index + 1]["top"]) / 2
        )
        name_text = (
            page.crop((0, upper, NAME_COLUMN_RIGHT, lower)).extract_text() or ""
        )
        full_name = re.sub(r"\s+", " ", name_text.replace("\n", " ")).strip()
        if not full_name:
            continue

        cells: dict[str, list[str]] = {}
        for w in words:
            if abs(w["top"] - top) > 4 or w["x0"] < NAME_COLUMN_RIGHT:
                continue
            cells.setdefault(_column_for(w["x0"]), []).append(w["text"])

        record: dict = {"name": full_name}
        deadlines: dict[str, str] = {}
        for field in (
            "early_decision", "early_decision_2", "early_action",
            "early_action_2", "restrictive_early_action", "regular",
        ):
            value = " ".join(cells.get(field, [])).strip()
            if not value:
                continue
            if "Rolling" in value:
                deadlines["rolling"] = "rolling"
                continue
            mmdd = _to_mmdd(value)
            if mmdd:
                deadlines[field] = mmdd
        record["deadlines"] = deadlines

        for field, key in (("fee_us", "fee_us"), ("fee_intl", "fee_intl")):
            match = FEE_RE.match(" ".join(cells.get(field, [])).strip())
            record[key] = int(match.group(1)) if match else None

        record["writing_supplement"] = " ".join(cells.get("writing_supplement", [])).strip()
        record["english_tests"] = _english_tests(cells.get("english_proficiency", []))
        record["test_policy_raw"] = " ".join(cells.get("test_policy", [])).strip()[:1]
        out.append(record)

    return out


# Legend, page 54 of the grid: the English-proficiency column lists which exams
# the college accepts from applicants whose first language is not English.
ENGLISH_TEST_NAMES = {
    "C": "Cambridge English",
    "D": "Duolingo",
    "I": "IELTS",
    "P": "PTE Academic",
    "T": "TOEFL",
    "N": "none required",
}


def _english_tests(tokens: list[str]) -> list[str]:
    """['D', 'or', 'I', 'or', 'T'] -> ['Duolingo', 'IELTS', 'TOEFL'].

    Filters to the documented single-letter codes, which also drops stray
    characters that bleed in from a wrapped school name.
    """
    if any("Website" in t for t in tokens):
        return []
    seen = []
    for token in tokens:
        name = ENGLISH_TEST_NAMES.get(token.strip().upper())
        if name and name not in seen:
            seen.append(name)
    return seen


def parse_pdf(path: str) -> list[dict]:
    import pdfplumber

    records: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            records.extend(parse_page(page))
    return records


# The grid records only whether a supplement exists, never how many essays.
# Storing a fabricated count would be worse than storing none, so a required
# supplement maps to 1 ("at least one") and the UI keeps saying "verify".
SUPPLEMENT_REQUIRED = {"Y", "S", "SR", "R"}


def upsert(db: Session, records: list[dict]) -> dict:
    """Merge grid records into universities matched by name. Never creates
    rows - the Scorecard owns which schools exist; this only enriches them."""
    universities = db.query(University).all()
    index: dict[str, University] = {}
    for u in universities:
        for variant in name_variants(u.name, u.city):
            index.setdefault(variant, u)

    updated = unmatched = 0
    for rec in records:
        uni = index.get(normalize_name(rec["name"]))
        if uni is None:
            unmatched += 1
            continue

        if rec["deadlines"]:
            uni.deadlines = rec["deadlines"]
        if rec["fee_us"] is not None:
            uni.application_fee = rec["fee_us"]

        supplement = rec["writing_supplement"].upper()
        if supplement:
            uni.supplemental_essay_count = 1 if supplement in SUPPLEMENT_REQUIRED else 0

        links = dict(uni.links or {})
        links["requirements_source"] = PDF_URL
        uni.links = links

        # rebuild the international notes this source owns, keeping any others
        notes = [
            n for n in (uni.intl_support_notes or "").split(" | ")
            if n and not n.startswith(("International application fee", "Accepts "))
        ]
        if rec["fee_intl"] is not None and rec["fee_intl"] != rec["fee_us"]:
            notes.append(f"International application fee: ${rec['fee_intl']}")
        if rec["english_tests"]:
            notes.append("Accepts " + ", ".join(rec["english_tests"]))
        uni.intl_support_notes = " | ".join(notes)

        uni.requirements_source = DATA_SOURCE
        uni.requirements_verified = date.today()
        updated += 1

    db.commit()
    return {"parsed": len(records), "updated": updated, "unmatched": unmatched}


def main() -> None:
    import sys
    import urllib.request

    from ..database import SessionLocal

    path = sys.argv[1] if len(sys.argv) > 1 else "reqgrid.pdf"
    try:
        open(path, "rb").close()
    except FileNotFoundError:
        print(f"Downloading {PDF_URL} ...")
        urllib.request.urlretrieve(PDF_URL, path)

    print("Parsing the Common App requirements grid...")
    records = parse_pdf(path)
    db = SessionLocal()
    try:
        result = upsert(db, records)
    finally:
        db.close()
    print(
        f"Parsed {result['parsed']} colleges; enriched {result['updated']} "
        f"({result['unmatched']} had no matching university row)."
    )


if __name__ == "__main__":
    main()
