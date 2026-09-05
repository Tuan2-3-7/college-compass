def test_register_login_me(client):
    resp = client.post(
        "/api/auth/register", json={"email": "new@example.com", "password": "secret1234"}
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"

    resp = client.post(
        "/api/auth/login", json={"email": "new@example.com", "password": "secret1234"}
    )
    assert resp.status_code == 200


def test_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "secret1234"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_wrong_password_rejected(client):
    client.post("/api/auth/register", json={"email": "a@example.com", "password": "secret1234"})
    resp = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrongpass1"})
    assert resp.status_code == 401


def test_short_password_rejected(client):
    resp = client.post("/api/auth/register", json={"email": "b@example.com", "password": "short"})
    assert resp.status_code == 422


def test_protected_routes_require_auth(client):
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/applications").status_code == 401
    assert client.get("/api/dashboard").status_code == 401


def test_users_cannot_see_each_others_data(client):
    r1 = client.post("/api/auth/register", json={"email": "u1@example.com", "password": "secret1234"})
    r2 = client.post("/api/auth/register", json={"email": "u2@example.com", "password": "secret1234"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    uni = client.get("/api/universities").json()[0]
    app_resp = client.post("/api/applications", headers=h1, json={"university_id": uni["id"]})
    assert app_resp.status_code == 201
    app_id = app_resp.json()["id"]

    # user 2 cannot see or modify user 1's application
    assert client.get(f"/api/applications/{app_id}/tasks", headers=h2).status_code == 404
    assert client.patch(
        f"/api/applications/{app_id}", headers=h2, json={"status": "submitted"}
    ).status_code == 404
    assert client.get("/api/applications", headers=h2).json() == []
