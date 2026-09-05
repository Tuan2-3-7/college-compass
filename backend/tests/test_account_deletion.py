"""Privacy requirement: users can delete their account and all their data."""

from datetime import date, timedelta

from conftest import find_university, set_profile


def _populate(client, headers):
    """Give the user one of everything."""
    set_profile(client, headers, financial_aid_needed=True)
    uni = find_university(client, "Purdue")
    client.post("/api/applications", headers=headers, json={"university_id": uni["id"]})
    essay = client.post(
        "/api/essays", headers=headers,
        json={"title": "PS", "prompt": "Tell us about yourself."},
    ).json()
    draft = client.post(
        f"/api/essays/{essay['id']}/drafts", headers=headers,
        json={"content": "One day I remember when I realized I learned something. " * 10},
    ).json()
    client.post(f"/api/essays/{essay['id']}/drafts/{draft['id']}/analyze", headers=headers)
    client.post("/api/tutor/chat", headers=headers, json={"message": "What is the FAFSA?"})
    client.post("/api/tasks", headers=headers, json={
        "title": "Custom thing", "due_date": (date.today() + timedelta(days=2)).isoformat(),
    })
    client.get("/api/notifications", headers=headers)  # generate notifications


def test_delete_account_removes_everything(client, auth_headers):
    _populate(client, auth_headers)

    resp = client.delete("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 204

    # token no longer works, login no longer works
    assert client.get("/api/auth/me", headers=auth_headers).status_code == 401
    assert client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "testpass123"}
    ).status_code == 401

    # re-registering the same email starts truly fresh
    token = client.post(
        "/api/auth/register", json={"email": "student@example.com", "password": "testpass123"}
    ).json()["access_token"]
    fresh = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/applications", headers=fresh).json() == []
    assert client.get("/api/essays", headers=fresh).json() == []
    assert client.get("/api/tutor/history", headers=fresh).json() == []
    assert client.get("/api/tasks", headers=fresh).json() == []
    assert client.get("/api/notifications", headers=fresh).json()["notifications"] == []
    assert client.get("/api/profile", headers=fresh).json()["full_name"] == ""


def test_delete_account_leaves_other_users_untouched(client, auth_headers):
    _populate(client, auth_headers)

    other = client.post(
        "/api/auth/register", json={"email": "keepme@example.com", "password": "secret1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    set_profile(client, other_headers)
    uni = find_university(client, "Cornell")
    client.post("/api/applications", headers=other_headers, json={"university_id": uni["id"]})

    client.delete("/api/auth/me", headers=auth_headers)

    apps = client.get("/api/applications", headers=other_headers).json()
    assert len(apps) == 1
    assert apps[0]["university"]["name"] == "Cornell University"
    # shared university catalog untouched
    assert len(client.get("/api/universities").json()) >= 20
