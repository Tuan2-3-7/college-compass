"""Major advisor and skill-gap analysis."""

from conftest import set_profile


def test_list_majors(client):
    majors = client.get("/api/majors").json()
    assert len(majors) >= 8
    keys = {m["key"] for m in majors}
    assert "computer_science" in keys and "nursing" in keys


def test_unknown_major_404(client, auth_headers):
    resp = client.get("/api/majors/underwater_basket_weaving/advisor", headers=auth_headers)
    assert resp.status_code == 404


def test_advisor_requires_auth(client):
    assert client.get("/api/majors/computer_science/advisor").status_code == 401


def test_cs_advisor_payload_shape(client, auth_headers):
    set_profile(client, auth_headers)
    data = client.get("/api/majors/computer_science/advisor", headers=auth_headers).json()
    assert data["label"] == "Computer Science"
    assert data["academic_prep"] and data["experiences"] and data["application_evidence"]
    assert {s["status"] for s in data["skills"]} <= {"strong", "developing", "missing"}
    assert isinstance(data["improvement_plan"], list)
    assert data["preparation_score"] is None or 0 <= data["preparation_score"] <= 100


def test_gap_analysis_detects_evidence(client, auth_headers):
    """AP CS + robotics + hackathon should register as programming/team strength."""
    set_profile(
        client, auth_headers,
        courses=["AP Computer Science A", "AP Calculus BC"],
        activities=[{"name": "Robotics club president"}, {"name": "Hackathon team"}],
        awards=["USACO Silver"],
    )
    data = client.get("/api/majors/computer_science/advisor", headers=auth_headers).json()
    by_key = {s["key"]: s for s in data["skills"]}
    assert by_key["programming"]["status"] in ("strong", "developing")
    assert by_key["programming"]["evidence"]  # actual matched items shown
    assert by_key["teamwork"]["status"] == "strong"
    # research has no evidence -> missing, and it appears in the plan as high priority
    assert by_key["research"]["status"] == "missing"
    plan_skills = [(p["skill"], p["priority"]) for p in data["improvement_plan"]]
    assert ("Research / independent study", "high") in plan_skills


def test_empty_profile_all_missing(client, auth_headers):
    set_profile(client, auth_headers, courses=[], activities=[], awards=[])
    data = client.get("/api/majors/biology/advisor", headers=auth_headers).json()
    assert all(s["status"] == "missing" for s in data["skills"])
    assert data["preparation_score"] == 0
    assert len(data["improvement_plan"]) == len(data["skills"])


def test_preparation_score_reflects_matches(client, auth_headers):
    set_profile(
        client, auth_headers,
        intended_major="nursing",
        courses=["AP Biology", "AP Chemistry", "Anatomy and Physiology"],
        activities=[{"name": "Hospital volunteer"}, {"name": "Red Cross club"},
                    {"name": "Lifeguard job"}],
        awards=["HOSA regional medalist"],
    )
    data = client.get("/api/majors/nursing/advisor", headers=auth_headers).json()
    assert data["preparation_score"] >= 60
    # this should also feed the analyzer's subscore
    prof = client.get("/api/analyzer/profile", headers=auth_headers).json()
    assert prof["subscores"]["major_preparation"] == data["preparation_score"]
