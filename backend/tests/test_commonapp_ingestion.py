"""Common App requirements grid ingestion (parser + upsert), no network."""

from datetime import date

from conftest import TestingSession

from app.ingestion.commonapp import (
    DATA_SOURCE,
    _column_for,
    _english_tests,
    _to_mmdd,
    upsert,
)
from app.models import University


def test_column_assignment_uses_x_position():
    """Which round a date belongs to is positional - order alone cannot tell
    early decision from early action."""
    assert _column_for(120.6) == "early_decision"
    assert _column_for(179.4) == "early_action"
    assert _column_for(236.7) == "restrictive_early_action"
    assert _column_for(263.2) == "regular"
    assert _column_for(299.1) == "fee_us"
    assert _column_for(331.1) == "fee_intl"
    # observed value offsets from their header still land in the right column
    assert _column_for(172.3) == "early_action"
    assert _column_for(259.0) == "regular"
    assert _column_for(25.8) == "name"


def test_date_conversion():
    assert _to_mmdd("11/1/2026") == "11-01"
    assert _to_mmdd("02/01/2027") == "02-01"
    assert _to_mmdd("Rolling") is None
    assert _to_mmdd("") is None


def test_english_test_decoding():
    """Legend p.54: C/D/I/P/T/N are the accepted-exam codes."""
    assert _english_tests(["D", "or", "I", "or", "T"]) == ["Duolingo", "IELTS", "TOEFL"]
    assert _english_tests(["N"]) == ["none required"]
    assert _english_tests(["See", "Website"]) == []
    # stray characters bleeding in from a wrapped school name are dropped
    assert _english_tests(["h", "D", "or", "T"]) == ["Duolingo", "TOEFL"]


def _record(name, **over):
    rec = {
        "name": name,
        "deadlines": {"early_action": "11-01", "regular": "01-15"},
        "fee_us": 60,
        "fee_intl": 85,
        "writing_supplement": "Y",
        "english_tests": ["Duolingo", "TOEFL"],
        "test_policy_raw": "A",
    }
    rec.update(over)
    return rec


def test_upsert_enriches_matched_university(client):
    db = TestingSession()
    try:
        before = db.query(University).filter(University.name == "Purdue University").one()
        before_id, before_rate = before.id, before.acceptance_rate

        result = upsert(db, [_record("Purdue University")])
        assert result["updated"] == 1 and result["unmatched"] == 0

        after = db.query(University).filter(University.name == "Purdue University").one()
        assert after.id == before_id                     # identity preserved
        assert after.acceptance_rate == before_rate      # statistics untouched
        assert after.deadlines == {"early_action": "11-01", "regular": "01-15"}
        assert after.application_fee == 60
        assert after.supplemental_essay_count == 1       # "Y" -> at least one
        assert after.requirements_source == DATA_SOURCE
        assert after.requirements_verified == date.today()
        assert "International application fee: $85" in after.intl_support_notes
        assert "Accepts Duolingo, TOEFL" in after.intl_support_notes
    finally:
        db.close()


def test_upsert_never_creates_universities(client):
    """The Scorecard owns which schools exist; this source only enriches."""
    db = TestingSession()
    try:
        count_before = db.query(University).count()
        result = upsert(db, [_record("Some College That Is Not In Our Database")])
        assert result == {"parsed": 1, "updated": 0, "unmatched": 1}
        assert db.query(University).count() == count_before
    finally:
        db.close()


def test_unverified_schools_are_not_stamped(client):
    """MIT is not a Common App member, so it must keep its unverified sample
    deadlines rather than being falsely marked as sourced."""
    db = TestingSession()
    try:
        upsert(db, [_record("Purdue University")])
        mit = db.query(University).filter(
            University.name == "Massachusetts Institute of Technology"
        ).one()
        assert mit.requirements_verified is None
        assert mit.requirements_source is None
    finally:
        db.close()


def test_notes_do_not_duplicate_on_reimport(client):
    """Re-running the import must refresh its own notes, not append them again."""
    db = TestingSession()
    try:
        upsert(db, [_record("Purdue University")])
        upsert(db, [_record("Purdue University", fee_intl=95)])
        uni = db.query(University).filter(University.name == "Purdue University").one()
        assert uni.intl_support_notes.count("International application fee") == 1
        assert "$95" in uni.intl_support_notes
        assert uni.intl_support_notes.count("Accepts ") == 1
        # the curated note from the original seed survives
        assert "Tuition freeze" in uni.intl_support_notes
    finally:
        db.close()


def test_blank_supplement_leaves_curated_count(client):
    """A blank Writing column means the grid says nothing about essay counts -
    it must not silently zero out a curated value."""
    db = TestingSession()
    try:
        upsert(db, [_record("Stanford University", writing_supplement="")])
        uni = db.query(University).filter(University.name == "Stanford University").one()
        assert uni.supplemental_essay_count == 3  # curated value preserved
    finally:
        db.close()
