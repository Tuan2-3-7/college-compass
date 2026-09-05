def test_pagination_caps_results_and_reports_total(client):
    """1,500+ real schools must never ship in one response."""
    resp = client.get("/api/universities", params={"limit": 5})
    assert resp.status_code == 200
    assert len(resp.json()) == 5
    total = int(resp.headers["X-Total-Count"])
    assert total >= 20  # header reports the full match count, not the page

    page2 = client.get("/api/universities", params={"limit": 5, "offset": 5}).json()
    assert [u["id"] for u in page2] != [u["id"] for u in resp.json()]

    # limit is bounded
    assert client.get("/api/universities", params={"limit": 500}).status_code == 422


def test_name_search(client):
    unis = client.get("/api/universities", params={"q": "Purdue"}).json()
    assert unis and all("purdue" in u["name"].lower() for u in unis)


def test_search_by_abbreviation_and_nickname(client):
    """Students type what they say out loud - 'MIT', not the full name."""
    def names(q):
        return [u["name"] for u in client.get("/api/universities", params={"q": q}).json()]

    assert "Massachusetts Institute of Technology" in names("MIT")      # initials
    assert "Massachusetts Institute of Technology" in names("mit")      # case-insensitive
    assert "University of California, Los Angeles" in names("UCLA")     # initials
    assert "New York University" in names("nyu")
    assert "Carnegie Mellon University" in names("CMU")                 # nickname map
    assert "Georgia Institute of Technology" in names("Georgia Tech")   # multi-word nickname
    # a long query is never treated as an abbreviation
    assert names("zzzzzz") == []


def test_search_ranks_the_intended_school_first(client):
    """Bare substring search puts 'Johnson C Smith' above MIT, because 'Smith'
    contains 'mit'. Relevance ranking must fix that."""
    unis = client.get("/api/universities", params={"q": "MIT"}).json()
    assert unis[0]["name"] == "Massachusetts Institute of Technology"

    # exact and prefix matches outrank incidental substrings too
    purdue = client.get("/api/universities", params={"q": "Purdue University"}).json()
    assert purdue[0]["name"] == "Purdue University"


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
