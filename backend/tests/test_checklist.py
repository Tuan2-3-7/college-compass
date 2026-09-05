"""Checklist personalization - the edge cases from the spec."""

from conftest import find_university, set_profile


def _tasks_for(client, headers, university_name, round_name="regular"):
    uni = find_university(client, university_name)
    resp = client.post(
        "/api/applications", headers=headers, json={"university_id": uni["id"], "round": round_name}
    )
    assert resp.status_code == 201, resp.text
    app_id = resp.json()["id"]
    tasks = client.get(f"/api/applications/{app_id}/tasks", headers=headers).json()
    return resp.json(), tasks


def titles(tasks):
    return " | ".join(t["title"].lower() for t in tasks)


def test_domestic_with_scores_gets_no_toefl_task(client, auth_headers):
    set_profile(client, auth_headers, student_type="domestic", sat=1450)
    _, tasks = _tasks_for(client, auth_headers, "Purdue")
    t = titles(tasks)
    assert "toefl" not in t
    assert "sat/act" in t  # send scores (test-required school)
    assert "i-20" not in t


def test_international_no_sat_at_test_optional_school(client, auth_headers):
    """International student without SAT at a test-optional school:
    no 'send SAT' task, TOEFL registration + proof-of-funds path present."""
    set_profile(
        client, auth_headers,
        student_type="international", country="Vietnam", sat=None, act=None,
    )
    _, tasks = _tasks_for(client, auth_headers, "Northeastern")
    t = titles(tasks)
    assert "register for toefl" in t
    assert "send official sat/act" not in t
    assert "test-optional" in t
    assert "i-20" in t
    assert "credential evaluation" in t


def test_international_no_test_at_required_school_gets_register_task(client, auth_headers):
    set_profile(client, auth_headers, student_type="international", sat=None, act=None)
    _, tasks = _tasks_for(client, auth_headers, "Georgia Institute")
    t = titles(tasks)
    assert "register for the sat or act" in t


def test_transfer_student_gets_college_transcript(client, auth_headers):
    set_profile(client, auth_headers, applicant_level="transfer")
    _, tasks = _tasks_for(client, auth_headers, "Michigan", round_name="transfer")
    t = titles(tasks)
    assert "college transcript" in t
    assert "college report" in t


def test_student_without_major_still_gets_checklist(client, auth_headers):
    set_profile(client, auth_headers, intended_major=None)
    app, tasks = _tasks_for(client, auth_headers, "Ohio State")
    assert len(tasks) >= 5
    assert app["status"] == "not_started"


def test_student_without_gpa_can_still_apply(client, auth_headers):
    set_profile(client, auth_headers, gpa=None)
    app, tasks = _tasks_for(client, auth_headers, "Alabama")
    assert len(tasks) >= 5


def test_domestic_financial_aid_gets_fafsa(client, auth_headers):
    set_profile(client, auth_headers, financial_aid_needed=True)
    _, tasks = _tasks_for(client, auth_headers, "Wisconsin")
    t = titles(tasks)
    assert "fafsa" in t


def test_international_aid_at_need_blind_school(client, auth_headers):
    set_profile(client, auth_headers, student_type="international", financial_aid_needed=True)
    _, tasks = _tasks_for(client, auth_headers, "Massachusetts Institute")
    t = titles(tasks)
    assert "international financial aid" in t
    assert "fafsa" not in t  # FAFSA is for domestic students


def test_international_aid_at_school_without_intl_aid(client, auth_headers):
    set_profile(client, auth_headers, student_type="international", financial_aid_needed=True)
    _, tasks = _tasks_for(client, auth_headers, "Arizona State")
    t = titles(tasks)
    assert "external scholarships" in t


def test_supplemental_essay_count_flows_into_tasks(client, auth_headers):
    set_profile(client, auth_headers)
    _, tasks = _tasks_for(client, auth_headers, "Stanford")
    t = titles(tasks)
    assert "3 supplemental essays" in t


def test_test_blind_school_has_no_sat_tasks(client, auth_headers):
    set_profile(client, auth_headers, sat=1500)
    _, tasks = _tasks_for(client, auth_headers, "Berkeley")
    t = titles(tasks)
    assert "sat" not in t


def test_deadline_resolved_for_round(client, auth_headers):
    set_profile(client, auth_headers)
    app, tasks = _tasks_for(client, auth_headers, "Cornell", round_name="early_decision")
    assert app["deadline"] is not None
    assert app["deadline"].endswith("-11-01")
    # tasks due before the deadline
    due_dates = [t["due_date"] for t in tasks if t["due_date"]]
    assert due_dates
    assert all(d <= app["deadline"] for d in due_dates)
