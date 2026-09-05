"""Scorecard ingestion - offline tests (no network)."""

from datetime import date

from conftest import TestingSession

from app.ingestion.scorecard import DATA_SOURCE, normalize_name, transform, upsert
from app.models import University


def _fake_row(**overrides):
    row = {
        "id": 166683,
        "school.name": "Massachusetts Institute of Technology",
        "school.city": "Cambridge",
        "school.state": "MA",
        "school.ownership": 2,
        "school.school_url": "web.mit.edu/",
        "latest.student.size": 4535,
        "latest.student.demographics.race_ethnicity.non_resident_alien": 0.1166,
        "latest.admissions.admission_rate.overall": 0.0455,
        "latest.admissions.sat_scores.25th_percentile.critical_reading": 740,
        "latest.admissions.sat_scores.25th_percentile.math": 780,
        "latest.admissions.sat_scores.75th_percentile.critical_reading": 780,
        "latest.admissions.sat_scores.75th_percentile.math": 800,
        "latest.admissions.act_scores.25th_percentile.cumulative": 34,
        "latest.admissions.act_scores.75th_percentile.cumulative": 36,
        "latest.admissions.test_requirements": 1,
        "latest.cost.tuition.in_state": 62396,
        "latest.cost.tuition.out_of_state": 62396,
        "latest.cost.attendance.academic_year": 82730,
        "latest.academics.program.bachelors.computer": 1,
        "latest.academics.program.bachelors.engineering": 1,
        "latest.academics.program.bachelors.social_science": 1,
        "latest.academics.program.bachelors.health": 0,
    }
    row.update(overrides)
    return row


def test_normalize_name_matches_scorecard_variants():
    assert normalize_name("University of California-Berkeley") == \
        normalize_name("University of California, Berkeley")
    assert normalize_name("Pennsylvania State University-Main Campus") == \
        normalize_name("Pennsylvania State University")
    assert normalize_name("Purdue University-Main Campus") == "purdue university"
    assert normalize_name("Arizona State University Campus Immersion") == \
        "arizona state university"
    assert normalize_name("University of Washington-Seattle Campus") == \
        "university of washington"


def test_transform_maps_fields():
    t = transform(_fake_row())
    assert t["ipeds_unitid"] == 166683
    assert t["sat_25"] == 1520 and t["sat_75"] == 1580
    assert t["control"] == "private"
    assert t["test_policy"] == "required"
    assert t["acceptance_rate"] == 0.0455
    assert t["intl_student_share"] == 0.1166
    assert "computer_science" in t["majors"]
    assert "economics" in t["majors"]      # social_science approximation
    assert "nursing" not in t["majors"]    # health flag was 0
    assert t["website"] == "https://web.mit.edu/"
    assert t["data_source"] == DATA_SOURCE
    assert t["last_verified"] == date.today()


def test_transform_handles_missing_data():
    t = transform(_fake_row(**{
        "latest.admissions.sat_scores.25th_percentile.math": None,
        "latest.admissions.admission_rate.overall": None,
        "latest.admissions.test_requirements": 3,
    }))
    assert t["sat_25"] is None
    assert t["acceptance_rate"] is None
    assert t["test_policy"] == "blind"
    assert transform({"school.name": None}) is None


def test_upsert_updates_curated_row_and_preserves_curated_fields(client):
    db = TestingSession()
    try:
        before = db.query(University).filter(University.name.like("%Massachusetts%")).one()
        old_id, old_deadlines = before.id, dict(before.deadlines)
        old_supp, old_toefl = before.supplemental_essay_count, before.toefl_min
        count_before = db.query(University).count()

        rows = [
            transform(_fake_row()),  # matches curated MIT by normalized name
            transform(_fake_row(**{
                "id": 999001, "school.name": "Example State University-Main Campus",
                "school.ownership": 1,
            })),
        ]
        result = upsert(db, rows)
        assert result == {"updated": 1, "inserted": 1, "fetched": 2}

        after = db.query(University).filter(University.name.like("%Massachusetts%")).one()
        # identity and curated fields preserved
        assert after.id == old_id
        assert after.deadlines == old_deadlines
        assert after.supplemental_essay_count == old_supp
        assert after.toefl_min == old_toefl
        # stats replaced with real values + provenance
        assert after.acceptance_rate == 0.0455
        assert after.sat_25 == 1520
        assert after.ipeds_unitid == 166683
        assert after.intl_student_share == 0.1166
        assert after.last_verified == date.today()
        assert "Scorecard" in after.data_source
        # curated majors survive the union
        assert "mathematics" in after.majors

        new = db.query(University).filter(University.ipeds_unitid == 999001).one()
        assert new.control == "public"
        assert new.deadlines == {} and new.app_platforms == []
        assert db.query(University).count() == count_before + 1

        # re-running is idempotent: second row now matches by unitid
        result2 = upsert(db, [transform(_fake_row(**{
            "id": 999001, "school.name": "Example State University-Main Campus",
            "school.ownership": 1,
        }))])
        assert result2["updated"] == 1 and result2["inserted"] == 0
    finally:
        db.close()
