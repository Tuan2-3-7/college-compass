from conftest import find_university, set_profile


def _add(client, headers, name, round_name="regular"):
    uni = find_university(client, name)
    resp = client.post(
        "/api/applications", headers=headers, json={"university_id": uni["id"], "round": round_name}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_multiple_universities_with_different_deadlines(client, auth_headers):
    set_profile(client, auth_headers)
    a1 = _add(client, auth_headers, "Berkeley")           # UC: 11-30
    a2 = _add(client, auth_headers, "Cornell", "early_decision")  # 11-01
    a3 = _add(client, auth_headers, "Ohio State")         # 02-01
    apps = client.get("/api/applications", headers=auth_headers).json()
    assert len(apps) == 3
    deadlines = {a["university"]["name"]: a["deadline"] for a in apps}
    assert len(set(deadlines.values())) == 3  # all different


def test_duplicate_university_rejected(client, auth_headers):
    set_profile(client, auth_headers)
    uni = find_university(client, "Purdue")
    assert (
        client.post("/api/applications", headers=auth_headers, json={"university_id": uni["id"]})
        .status_code == 201
    )
    assert (
        client.post("/api/applications", headers=auth_headers, json={"university_id": uni["id"]})
        .status_code == 409
    )


def test_status_transitions(client, auth_headers):
    set_profile(client, auth_headers)
    app = _add(client, auth_headers, "Alabama")
    for status in ["in_progress", "completed", "submitted", "decision_received"]:
        resp = client.patch(
            f"/api/applications/{app['id']}", headers=auth_headers, json={"status": status}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == status
    resp = client.patch(
        f"/api/applications/{app['id']}", headers=auth_headers, json={"status": "bogus"}
    )
    assert resp.status_code == 422


def test_round_change_updates_deadline_and_regenerates_tasks(client, auth_headers):
    set_profile(client, auth_headers)
    app = _add(client, auth_headers, "Cornell", "regular")
    assert app["deadline"].endswith("-01-02")

    # mark one task done - it must survive the round change
    tasks = client.get(f"/api/applications/{app['id']}/tasks", headers=auth_headers).json()
    done_task = tasks[0]
    client.patch(f"/api/tasks/{done_task['id']}", headers=auth_headers, json={"status": "done"})

    resp = client.patch(
        f"/api/applications/{app['id']}", headers=auth_headers, json={"round": "early_decision"}
    )
    assert resp.status_code == 200
    assert resp.json()["deadline"].endswith("-11-01")

    new_tasks = client.get(f"/api/applications/{app['id']}/tasks", headers=auth_headers).json()
    kept = [t for t in new_tasks if t["id"] == done_task["id"]]
    assert kept and kept[0]["status"] == "done"


def test_custom_task_and_completion(client, auth_headers):
    set_profile(client, auth_headers)
    resp = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"title": "Ask coach for athletic recommendation", "priority": "high"},
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["auto_generated"] is False

    resp = client.patch(f"/api/tasks/{task['id']}", headers=auth_headers, json={"status": "done"})
    assert resp.json()["status"] == "done"


def test_delete_application_removes_tasks(client, auth_headers):
    set_profile(client, auth_headers)
    app = _add(client, auth_headers, "Purdue")
    assert client.delete(f"/api/applications/{app['id']}", headers=auth_headers).status_code == 204
    tasks = client.get("/api/tasks", headers=auth_headers).json()
    assert all(t["application_id"] != app["id"] for t in tasks)


def test_dashboard_shape_and_next_action(client, auth_headers):
    # empty profile -> next action is completing the profile
    dash = client.get("/api/dashboard", headers=auth_headers).json()
    assert dash["next_action"]["title"].lower().startswith("complete your student profile")

    set_profile(client, auth_headers)
    dash = client.get("/api/dashboard", headers=auth_headers).json()
    assert dash["profile_completeness"] >= 50
    assert dash["next_action"]["title"].lower().startswith("add your first university")

    _add(client, auth_headers, "Stanford")
    dash = client.get("/api/dashboard", headers=auth_headers).json()
    assert dash["applications"][0]["university"] == "Stanford University"
    assert dash["tasks_total"] > 0
    assert dash["applications"][0]["progress"] == 0
    # with an application in place, next action should point at a real task
    assert dash["next_action"] is None or "task_id" in dash["next_action"] or dash["next_action"]["title"]
