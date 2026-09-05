"""Phase 4: financial aid, international pathway, comparison, readiness, notifications."""

from datetime import date, timedelta

from conftest import find_university, set_profile


# ---------------- scholarships & financial aid ----------------

def test_scholarships_seeded_and_labeled(client):
    scholarships = client.get("/api/scholarships").json()
    assert len(scholarships) >= 10
    assert all("sample" in s["data_source"] for s in scholarships)
    assert all(s["last_verified"] is None for s in scholarships)


def test_scholarship_eligibility_filter(client):
    intl = client.get("/api/scholarships", params={"eligibility": "international"}).json()
    assert intl
    assert all(s["eligibility"] in ("international", "both") for s in intl)
    domestic = client.get("/api/scholarships", params={"eligibility": "domestic"}).json()
    assert all(s["eligibility"] in ("domestic", "both") for s in domestic)


def test_scholarship_major_filter(client):
    cs = client.get("/api/scholarships", params={"major": "computer science"}).json()
    assert cs
    assert all(not s["majors"] or "computer_science" in s["majors"] for s in cs)


def test_domestic_aid_plan_has_fafsa(client, auth_headers):
    set_profile(client, auth_headers, student_type="domestic", financial_aid_needed=True)
    plan = client.get("/api/financial-aid/plan", headers=auth_headers).json()
    assert plan["needs_aid"] is True
    form_names = " | ".join(f["name"] for f in plan["forms"])
    assert "FAFSA" in form_names and "CSS" in form_names
    # domestic student must not be offered international-only scholarships
    assert all(s["eligibility"] in ("domestic", "both") for s in plan["scholarships"])


def test_international_aid_plan(client, auth_headers):
    set_profile(
        client, auth_headers,
        student_type="international", financial_aid_needed=True, gpa=3.9,
    )
    uni = find_university(client, "Massachusetts Institute")
    client.post("/api/applications", headers=auth_headers, json={"university_id": uni["id"]})
    plan = client.get("/api/financial-aid/plan", headers=auth_headers).json()
    form_names = " | ".join(f["name"] for f in plan["forms"])
    assert "Proof of funds" in form_names
    assert "FAFSA" not in form_names
    assert plan["schools"][0]["offers_intl_aid"] is True
    assert all(s["eligibility"] in ("international", "both") for s in plan["scholarships"])
    # aid tasks from the checklist surface here
    assert any("financial aid" in t["title"].lower() for t in plan["aid_tasks"])


def test_min_gpa_filters_scholarship_matches(client, auth_headers):
    set_profile(client, auth_headers, student_type="domestic", financial_aid_needed=True, gpa=2.5)
    plan = client.get("/api/financial-aid/plan", headers=auth_headers).json()
    names = [s["name"] for s in plan["scholarships"]]
    assert "Jack Kent Cooke College Scholarship" not in names  # needs 3.5
    assert "Dell Scholars Program" in names  # needs 2.4


# ---------------- international pathway ----------------

def test_pathway_for_international_student(client, auth_headers):
    set_profile(client, auth_headers, student_type="international")
    data = client.get("/api/international/pathway", headers=auth_headers).json()
    assert data["applicable"] is True
    keys = [s["key"] for s in data["stages"]]
    assert keys == [
        "application", "admission", "financial_documentation",
        "i20", "sevis", "visa", "housing", "arrival",
    ]
    assert data["current_stage"] == "application"
    # every stage explains its unfamiliar terms
    assert all(s["explains"] for s in data["stages"])
    assert "official" in data["disclaimer"]


def test_pathway_stage_advances_with_acceptance(client, auth_headers):
    set_profile(client, auth_headers, student_type="international")
    uni = find_university(client, "Arizona State")
    app = client.post(
        "/api/applications", headers=auth_headers, json={"university_id": uni["id"]}
    ).json()
    client.patch(
        f"/api/applications/{app['id']}", headers=auth_headers,
        json={"status": "decision_received", "decision": "accepted"},
    )
    data = client.get("/api/international/pathway", headers=auth_headers).json()
    assert data["current_stage"] == "financial_documentation"
    statuses = {s["key"]: s["status"] for s in data["stages"]}
    assert statuses["application"] == "done"
    assert statuses["financial_documentation"] == "current"
    assert statuses["visa"] == "upcoming"


def test_pathway_notes_domestic_students(client, auth_headers):
    set_profile(client, auth_headers, student_type="domestic")
    data = client.get("/api/international/pathway", headers=auth_headers).json()
    assert data["applicable"] is False
    assert data["note"]


# ---------------- comparison ----------------

def test_compare_universities(client, auth_headers):
    set_profile(client, auth_headers)
    mit = find_university(client, "Massachusetts Institute")
    asu = find_university(client, "Arizona State")
    client.post("/api/applications", headers=auth_headers, json={"university_id": mit["id"]})
    data = client.get(
        "/api/compare", headers=auth_headers, params={"ids": f"{mit['id']},{asu['id']}"}
    ).json()
    assert len(data["universities"]) == 2
    by_name = {u["name"]: u for u in data["universities"]}
    mit_col = by_name["Massachusetts Institute of Technology"]
    assert mit_col["classification"] == "reach"
    assert mit_col["on_list"] is True
    assert by_name["Arizona State University"]["on_list"] is False
    assert "estimate" in data["disclaimer"]


def test_compare_validates_input(client, auth_headers):
    set_profile(client, auth_headers)
    uni = find_university(client, "Purdue")
    assert client.get("/api/compare", headers=auth_headers,
                      params={"ids": str(uni["id"])}).status_code == 422
    assert client.get("/api/compare", headers=auth_headers,
                      params={"ids": "1,2,3,4,5"}).status_code == 422
    assert client.get("/api/compare", headers=auth_headers,
                      params={"ids": f"{uni['id']},999999"}).status_code == 404
    assert client.get("/api/compare", params={"ids": "1,2"}).status_code == 401


# ---------------- readiness ----------------

def test_readiness_shape_and_ranges(client, auth_headers):
    set_profile(client, auth_headers)
    data = client.get("/api/readiness", headers=auth_headers).json()
    assert set(data["components"]) == {
        "academics", "activities", "essays", "major_preparation",
        "application_tasks", "financial_preparation",
    }
    assert all(0 <= v <= 100 for v in data["components"].values())
    assert 0 <= data["overall"] <= 100
    assert data["highest_impact"]["action"]
    assert "not an admission prediction" in data["disclaimer"]


def test_readiness_financial_complete_when_no_aid_needed(client, auth_headers):
    set_profile(client, auth_headers, financial_aid_needed=False)
    data = client.get("/api/readiness", headers=auth_headers).json()
    assert data["components"]["financial_preparation"] == 100


def test_readiness_reflects_essay_scores_and_tasks(client, auth_headers):
    set_profile(client, auth_headers)
    before = client.get("/api/readiness", headers=auth_headers).json()
    assert before["components"]["essays"] == 0

    essay = client.post(
        "/api/essays", headers=auth_headers,
        json={"title": "PS", "prompt": "Describe a challenge you overcame."},
    ).json()
    draft = client.post(
        f"/api/essays/{essay['id']}/drafts", headers=auth_headers,
        json={"content": "One day I remember the moment when I realized I learned from the "
                         "challenge of building our robot. " * 10},
    ).json()
    client.post(f"/api/essays/{essay['id']}/drafts/{draft['id']}/analyze", headers=auth_headers)
    after = client.get("/api/readiness", headers=auth_headers).json()
    assert after["components"]["essays"] > 0


# ---------------- notifications ----------------

def test_notifications_generated_and_idempotent(client, auth_headers):
    set_profile(client, auth_headers)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    client.post("/api/tasks", headers=auth_headers,
                json={"title": "Send scores", "due_date": tomorrow})
    first = client.get("/api/notifications", headers=auth_headers).json()
    assert first["unread"] == 1
    assert "Due soon" in first["notifications"][0]["title"]
    # calling again must not duplicate
    second = client.get("/api/notifications", headers=auth_headers).json()
    assert len(second["notifications"]) == 1


def test_overdue_notification_and_mark_read(client, auth_headers):
    set_profile(client, auth_headers)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post("/api/tasks", headers=auth_headers,
                json={"title": "Late thing", "due_date": yesterday})
    data = client.get("/api/notifications", headers=auth_headers).json()
    overdue = [n for n in data["notifications"] if n["category"] == "overdue"]
    assert overdue and "Overdue" in overdue[0]["title"]

    client.post(f"/api/notifications/{overdue[0]['id']}/read", headers=auth_headers)
    data = client.get("/api/notifications", headers=auth_headers).json()
    assert data["unread"] == 0


def test_notifications_are_user_isolated(client, auth_headers):
    set_profile(client, auth_headers)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    client.post("/api/tasks", headers=auth_headers,
                json={"title": "Mine only", "due_date": tomorrow})
    client.get("/api/notifications", headers=auth_headers)

    other = client.post(
        "/api/auth/register", json={"email": "other4@example.com", "password": "secret1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    data = client.get("/api/notifications", headers=other_headers).json()
    assert data["notifications"] == []
