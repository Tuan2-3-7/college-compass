from datetime import date, timedelta

from conftest import find_university, set_profile


# ---------------- tutor ----------------

def test_tutor_explains_known_topic(client, auth_headers):
    resp = client.post(
        "/api/tutor/chat", headers=auth_headers,
        json={"message": "I don't understand what course rigor means."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mock"
    assert "rigor" in data["reply"].lower()
    assert "AP" in data["reply"]  # gives a concrete example


def test_tutor_international_topics(client, auth_headers):
    resp = client.post(
        "/api/tutor/chat", headers=auth_headers, json={"message": "What is an I-20?"}
    )
    assert "sevis" in resp.json()["reply"].lower()


def test_tutor_unknown_topic_is_honest(client, auth_headers):
    resp = client.post(
        "/api/tutor/chat", headers=auth_headers, json={"message": "Teach me quantum field theory"}
    )
    reply = resp.json()["reply"]
    assert "demo mode" in reply.lower()


def test_tutor_history_persists_and_clears(client, auth_headers):
    client.post("/api/tutor/chat", headers=auth_headers, json={"message": "What is the FAFSA?"})
    history = client.get("/api/tutor/history", headers=auth_headers).json()
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert client.delete("/api/tutor/history", headers=auth_headers).status_code == 204
    assert client.get("/api/tutor/history", headers=auth_headers).json() == []


def test_ai_status_reports_mock(client):
    data = client.get("/api/ai/status").json()
    assert data["provider"] == "mock"
    assert data["model"] is None


# ---------------- recommendations ----------------

def test_recommendations_empty_profile_suggests_basics(client, auth_headers):
    recs = client.get("/api/recommendations", headers=auth_headers).json()
    titles = " | ".join(r["title"].lower() for r in recs)
    assert "gpa" in titles or "university" in titles


def test_overdue_task_is_top_recommendation(client, auth_headers):
    set_profile(client, auth_headers)
    uni = find_university(client, "Purdue")
    client.post("/api/applications", headers=auth_headers, json={"university_id": uni["id"]})
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(
        "/api/tasks", headers=auth_headers,
        json={"title": "Send transcript to Purdue", "due_date": yesterday},
    )
    recs = client.get("/api/recommendations", headers=auth_headers).json()
    assert recs[0]["category"] == "deadline"
    assert "Overdue" in recs[0]["reason"]


def test_all_reach_list_triggers_balance_warning(client, auth_headers):
    set_profile(client, auth_headers)  # decent but not stellar profile
    for name in ["Massachusetts Institute", "Stanford"]:
        uni = find_university(client, name)
        client.post("/api/applications", headers=auth_headers, json={"university_id": uni["id"]})
    recs = client.get("/api/recommendations", headers=auth_headers).json()
    assert any(r["category"] == "list_balance" for r in recs)


def test_low_scoring_essay_recommended_for_revision(client, auth_headers):
    set_profile(client, auth_headers)
    essay = client.post(
        "/api/essays", headers=auth_headers,
        json={"title": "Why Us", "prompt": "Why do you want to attend?", "essay_type": "supplemental"},
    ).json()
    draft = client.post(
        f"/api/essays/{essay['id']}/drafts", headers=auth_headers,
        json={"content": "I want to go to college. " * 20},
    ).json()
    client.post(f"/api/essays/{essay['id']}/drafts/{draft['id']}/analyze", headers=auth_headers)
    recs = client.get("/api/recommendations", headers=auth_headers).json()
    essay_recs = [r for r in recs if r["category"] == "essays"]
    assert essay_recs and "Why Us" in essay_recs[0]["title"]


def test_unanalyzed_draft_recommended(client, auth_headers):
    set_profile(client, auth_headers)
    essay = client.post(
        "/api/essays", headers=auth_headers,
        json={"title": "Main Essay", "prompt": "Tell us about yourself."},
    ).json()
    client.post(
        f"/api/essays/{essay['id']}/drafts", headers=auth_headers,
        json={"content": "A full draft exists but nobody has analyzed it yet."},
    )
    recs = client.get("/api/recommendations", headers=auth_headers).json()
    assert any("Analyze" in r["title"] for r in recs)
