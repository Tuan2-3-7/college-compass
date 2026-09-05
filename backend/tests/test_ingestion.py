"""Scorecard ingestion - offline tests (no network)."""

from datetime import date

from conftest import TestingSession

from app.ingestion.scorecard import (
    DATA_SOURCE,
    name_variants,
    normalize_name,
    relink_curated,
    transform,
    upsert,
)
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
    # Scorecard prefixes some flagships with "The"
    assert normalize_name("The University of Alabama") == "university of alabama"
    assert normalize_name("The University of Texas at Austin") == \
        normalize_name("University of Texas at Austin")


def test_name_variants_strips_campus_city():
    """Scorecard appends the campus city to some flagship names."""
    variants = name_variants("University of Michigan-Ann Arbor", "Ann Arbor")
    assert "university of michigan" in variants
    # no city suffix -> just the base form
    assert name_variants("Purdue University", "West Lafayette") == ["purdue university"]
    # never strip the whole name away
    assert name_variants("Boston", "Boston") == ["boston"]


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


def test_distinct_schools_sharing_a_name_are_disambiguated(client):
    """There really are two 'Anderson University' (IN and SC) - neither may
    overwrite the other, and `name` stays unique."""
    db = TestingSession()
    try:
        rows = [
            transform(_fake_row(**{
                "id": 150066, "school.name": "Anderson University",
                "school.city": "Anderson", "school.state": "IN",
                "latest.admissions.admission_rate.overall": 0.79,
            })),
            transform(_fake_row(**{
                "id": 217925, "school.name": "Anderson University",
                "school.city": "Anderson", "school.state": "SC",
                "latest.admissions.admission_rate.overall": 0.55,
            })),
        ]
        result = upsert(db, rows)
        assert result["inserted"] == 2 and result["updated"] == 0

        indiana = db.query(University).filter(University.ipeds_unitid == 150066).one()
        carolina = db.query(University).filter(University.ipeds_unitid == 217925).one()
        assert indiana.name == "Anderson University"
        assert carolina.name == "Anderson University (SC)"
        assert indiana.acceptance_rate == 0.79   # not clobbered by the SC row
        assert carolina.acceptance_rate == 0.55

        # re-running matches both by unitid - no new rows, no renames
        again = upsert(db, rows)
        assert again == {"updated": 2, "inserted": 0, "fetched": 2}
        assert db.query(University).filter(University.name.like("Anderson%")).count() == 2
    finally:
        db.close()


def _insert_raw_twin(db, **fields) -> University:
    """Insert a Scorecard row directly, bypassing upsert's name matching - i.e.
    the duplicate state an older, less careful sync left behind."""
    twin = University(**fields)
    db.add(twin)
    db.commit()
    return twin


def test_upsert_matches_campus_suffixed_name_without_duplicating(client):
    """The matcher itself handles 'University of Michigan-Ann Arbor'."""
    db = TestingSession()
    try:
        result = upsert(db, [transform(_fake_row(**{
            "id": 170976, "school.name": "University of Michigan-Ann Arbor",
            "school.city": "Ann Arbor", "school.state": "MI", "school.ownership": 1,
        }))])
        assert result["updated"] == 1 and result["inserted"] == 0
        assert db.query(University).filter(
            University.name.like("University of Michigan%")).count() == 1
    finally:
        db.close()


def test_relink_merges_campus_suffixed_twin_into_curated_row(client):
    """Repair pass: a curated 'University of Michigan' absorbs an already-inserted
    'University of Michigan-Ann Arbor' duplicate from an older sync."""
    db = TestingSession()
    try:
        curated = db.query(University).filter(University.name == "University of Michigan").one()
        curated_id, curated_deadlines = curated.id, dict(curated.deadlines)
        curated_supp = curated.supplemental_essay_count
        assert curated.ipeds_unitid is None

        _insert_raw_twin(
            db, ipeds_unitid=170976, name="University of Michigan-Ann Arbor",
            city="Ann Arbor", state="MI", control="public",
            acceptance_rate=0.177, majors=["computer_science"],
            links={"website": "https://umich.edu/"}, last_verified=date.today(),
        )
        assert db.query(University).filter(University.name.like("University of Michigan%")).count() == 2

        merged = relink_curated(db)
        assert ("University of Michigan", "University of Michigan-Ann Arbor") in merged

        rows = db.query(University).filter(University.name.like("University of Michigan%")).all()
        assert len(rows) == 1
        survivor = rows[0]
        assert survivor.id == curated_id                    # applications stay valid
        assert survivor.name == "University of Michigan"
        assert survivor.ipeds_unitid == 170976              # real stats absorbed
        assert survivor.acceptance_rate == 0.177
        assert survivor.deadlines == curated_deadlines      # curated fields kept
        assert survivor.supplemental_essay_count == curated_supp

        assert relink_curated(db) == []  # idempotent
    finally:
        db.close()


def test_relink_never_drops_a_row_with_applications(client, auth_headers):
    """If a student already applied to the Scorecard row, leave both alone."""
    db = TestingSession()
    try:
        twin = _insert_raw_twin(
            db, ipeds_unitid=170976, name="University of Michigan-Ann Arbor",
            city="Ann Arbor", state="MI", control="public", last_verified=date.today(),
        )
        twin_id = twin.id
    finally:
        db.close()

    resp = client.post("/api/applications", headers=auth_headers,
                       json={"university_id": twin_id})
    assert resp.status_code == 201

    db = TestingSession()
    try:
        assert relink_curated(db) == []
        assert db.query(University).filter(University.ipeds_unitid == 170976).count() == 1
    finally:
        db.close()
