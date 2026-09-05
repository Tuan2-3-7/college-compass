"""Competitiveness analyzer - classification rules and edge cases."""

from conftest import find_university, set_profile

STRONG_PROFILE = dict(
    gpa=3.95, sat=1550,
    intended_major="computer_science",
    courses=["AP Calculus BC", "AP Computer Science A", "AP Physics C", "AP Statistics",
             "AP English", "AP Chemistry", "AP US History", "AP Biology"],
    activities=[{"name": "Robotics club president"}, {"name": "USACO Gold"},
                {"name": "Founder of coding tutoring program"}, {"name": "Varsity tennis captain"},
                {"name": "Open-source project maintainer"}],
    awards=["ISEF finalist", "AIME qualifier", "Hackathon winner"],
)

WEAK_PROFILE = dict(
    gpa=2.7, sat=None, act=None,
    intended_major=None, courses=[], activities=[], awards=[],
)


def _fit(client, headers, name_fragment):
    uni = find_university(client, name_fragment)
    resp = client.get(f"/api/analyzer/university/{uni['id']}", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_profile_scores_shape_and_ranges(client, auth_headers):
    set_profile(client, auth_headers, **STRONG_PROFILE)
    data = client.get("/api/analyzer/profile", headers=auth_headers).json()
    assert set(data["subscores"]) == {
        "academics", "course_rigor", "activities", "leadership", "awards", "major_preparation"
    }
    for value in data["subscores"].values():
        assert value is None or 0 <= value <= 100
    assert 0 <= data["overall"] <= 100
    assert "estimate" in data["disclaimer"].lower()
    # essay is explicitly not scored yet
    assert any("essay" in n.lower() for n in data["notes"])


def test_strong_student_scores_high(client, auth_headers):
    set_profile(client, auth_headers, **STRONG_PROFILE)
    data = client.get("/api/analyzer/profile", headers=auth_headers).json()
    assert data["overall"] >= 80
    assert data["subscores"]["leadership"] >= 70
    assert data["subscores"]["major_preparation"] >= 70


def test_ultra_selective_school_is_always_reach(client, auth_headers):
    """Even a 1550/3.95 applicant sees MIT as a reach."""
    set_profile(client, auth_headers, **STRONG_PROFILE)
    fit = _fit(client, auth_headers, "Massachusetts Institute")
    assert fit["classification"] == "reach"
    assert any("reach for every applicant" in r for r in fit["reasons"])


def test_strong_student_likely_at_open_school(client, auth_headers):
    set_profile(client, auth_headers, **STRONG_PROFILE)
    fit = _fit(client, auth_headers, "Arizona State")
    assert fit["classification"] == "likely"


def test_weak_profile_reach_at_selective_school(client, auth_headers):
    set_profile(client, auth_headers, **WEAK_PROFILE)
    fit = _fit(client, auth_headers, "Carnegie Mellon")
    assert fit["classification"] == "reach"


def test_missing_gpa_and_tests_still_works(client, auth_headers):
    set_profile(client, auth_headers, **WEAK_PROFILE)
    data = client.get("/api/analyzer/profile", headers=auth_headers).json()
    assert data["subscores"]["academics"] is None or data["subscores"]["academics"] <= 100
    fit = _fit(client, auth_headers, "Ohio State")
    assert fit["classification"] in ("reach", "target", "likely")


def test_no_gpa_no_tests_gets_note(client, auth_headers):
    set_profile(client, auth_headers, gpa=None, sat=None, act=None)
    data = client.get("/api/analyzer/profile", headers=auth_headers).json()
    assert data["subscores"]["academics"] is None
    assert any("No GPA or test scores" in n for n in data["notes"])


def test_test_blind_school_ignores_sat(client, auth_headers):
    """Berkeley is test-blind in the sample data: SAT must not affect the fit."""
    set_profile(client, auth_headers, **{**STRONG_PROFILE, "sat": 1550})
    with_sat = _fit(client, auth_headers, "Berkeley")
    set_profile(client, auth_headers, **{**STRONG_PROFILE, "sat": None})
    without_sat = _fit(client, auth_headers, "Berkeley")
    assert with_sat["strength"] == without_sat["strength"]
    assert any("Test-blind" in r for r in without_sat["reasons"])


def test_international_penalty_applies(client, auth_headers):
    set_profile(client, auth_headers, **STRONG_PROFILE, student_type="domestic")
    domestic = _fit(client, auth_headers, "Purdue")
    set_profile(client, auth_headers, **STRONG_PROFILE, student_type="international")
    intl = _fit(client, auth_headers, "Purdue")
    assert intl["strength"] < domestic["strength"]
    assert any("International" in r for r in intl["reasons"])


def test_required_tests_missing_is_flagged(client, auth_headers):
    set_profile(client, auth_headers, sat=None, act=None)
    fit = _fit(client, auth_headers, "Georgia Institute")
    assert any("requires tests" in r for r in fit["reasons"])


def test_applications_list_analysis(client, auth_headers):
    set_profile(client, auth_headers, **STRONG_PROFILE)
    for name in ["Massachusetts Institute", "Arizona State"]:
        uni = find_university(client, name)
        client.post("/api/applications", headers=auth_headers, json={"university_id": uni["id"]})
    data = client.get("/api/analyzer/applications", headers=auth_headers).json()
    assert len(data) == 2
    by_name = {d["university"]: d["classification"] for d in data}
    assert by_name["Massachusetts Institute of Technology"] == "reach"
    assert by_name["Arizona State University"] == "likely"
    assert all("application_id" in d for d in data)
