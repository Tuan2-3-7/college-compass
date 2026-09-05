def test_seed_loaded(client):
    resp = client.get("/api/universities")
    assert resp.status_code == 200
    unis = resp.json()
    assert len(unis) >= 20
    # sample data must be labeled as unverified
    assert all(u["last_verified"] is None for u in unis)
    assert all("sample" in u["data_source"] for u in unis)


def test_filter_by_major(client):
    resp = client.get("/api/universities", params={"major": "computer science"})
    unis = resp.json()
    assert unis
    assert all("computer_science" in u["majors"] for u in unis)


def test_filter_by_state_and_control(client):
    resp = client.get("/api/universities", params={"state": "ca", "control": "public"})
    unis = resp.json()
    assert unis
    assert all(u["state"] == "CA" and u["control"] == "public" for u in unis)


def test_filter_by_cost(client):
    resp = client.get("/api/universities", params={"max_cost": 55000})
    unis = resp.json()
    assert unis
    assert all(u["cost_of_attendance"] <= 55000 for u in unis)


def test_filter_competitiveness(client):
    resp = client.get("/api/universities", params={"competitiveness": "most_selective"})
    unis = resp.json()
    assert unis
    assert all(u["acceptance_rate"] < 0.10 for u in unis)


def test_filter_intl_aid(client):
    resp = client.get("/api/universities", params={"intl_aid": "true"})
    unis = resp.json()
    assert unis
    assert all(u["offers_intl_aid"] for u in unis)


def test_sort_by_cost(client):
    resp = client.get("/api/universities", params={"sort": "cost"})
    costs = [u["cost_of_attendance"] for u in resp.json() if u["cost_of_attendance"]]
    assert costs == sorted(costs)


def test_university_detail_and_404(client):
    uni = client.get("/api/universities").json()[0]
    assert client.get(f"/api/universities/{uni['id']}").status_code == 200
    assert client.get("/api/universities/999999").status_code == 404
