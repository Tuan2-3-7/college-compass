"""Essay coach - CRUD, versioning, analysis quality, and coach-not-writer."""

CLICHE_ESSAY = """Ever since I was young, I have always been passionate about science.

I worked hard in school and joined many clubs. I did many activities and learned
many things. My experiences changed my life and pushed me to be my best. Science
is important. I like science a lot. Science class was fun and science fair was
also fun. I want to study science because science is my passion.

In conclusion, I will follow my dreams and make a difference in the world.
I know that hard work pays off and I will succeed at the end of the day.
""" * 2  # long enough to clear the minimum-length gate

STRONG_ESSAY = """The robot died forty seconds into the match, and I remember the exact
sound: a soft click from the drivetrain, then silence in the Fresno convention hall.

I had spent 300 hours that season leading our twelve-person build team. When our
captain graduated, I inherited a codebase nobody understood and a gearbox design
that stripped under load. Looking back, I realized the challenge was never the robot -
it was that we documented nothing. So I started an engineering notebook, taught two
freshmen to write test logs, and rebuilt the drivetrain around a design we could
actually explain to each other.

At the state finals in March, the new gearbox survived all nine matches. But what
I learned by then was bigger than gears: systems outlive the people who build
them only when knowledge is shared. That lesson taught me why I want to study
computer science - not to write clever code, but to build things a team can trust.
"""


def _make_essay(client, headers, **overrides):
    payload = {
        "title": "Personal Statement",
        "prompt": "Describe a challenge you overcame and what you learned from the experience.",
        "essay_type": "personal_statement",
        "word_limit": 650,
    }
    payload.update(overrides)
    resp = client.post("/api/essays", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _analyze(client, headers, essay_id, content):
    d = client.post(f"/api/essays/{essay_id}/drafts", headers=headers, json={"content": content})
    assert d.status_code == 201, d.text
    draft = d.json()
    f = client.post(
        f"/api/essays/{essay_id}/drafts/{draft['id']}/analyze", headers=headers
    )
    assert f.status_code == 200, f.text
    return draft, f.json()


def test_essay_crud_and_draft_versioning(client, auth_headers):
    essay = _make_essay(client, auth_headers)
    for i in range(2):
        r = client.post(
            f"/api/essays/{essay['id']}/drafts", headers=auth_headers,
            json={"content": f"Draft number {i + 1}. " + STRONG_ESSAY},
        )
        assert r.status_code == 201
    detail = client.get(f"/api/essays/{essay['id']}", headers=auth_headers).json()
    assert [d["version"] for d in detail["drafts"]] == [1, 2]

    assert client.delete(f"/api/essays/{essay['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/essays/{essay['id']}", headers=auth_headers).status_code == 404


def test_analysis_shape_and_provider(client, auth_headers):
    essay = _make_essay(client, auth_headers)
    _, fb = _analyze(client, auth_headers, essay["id"], STRONG_ESSAY)
    assert fb["provider"] == "mock"
    assert 0 <= fb["overall_score"] <= 100
    assert set(fb["scores"]) == {
        "prompt_alignment", "storytelling", "personal_voice",
        "specificity", "reflection", "structure", "grammar",
    }
    assert all(0 <= v <= 100 for v in fb["scores"].values())
    # paragraph-level feedback matches paragraph count
    assert len(fb["paragraph_feedback"]) == 3
    # the coach asks questions rather than writing content
    assert len(fb["questions"]) >= 1
    assert all(q.endswith("?") for q in fb["questions"])


def test_cliche_essay_flagged_and_scores_lower(client, auth_headers):
    essay = _make_essay(client, auth_headers)
    _, weak = _analyze(client, auth_headers, essay["id"], CLICHE_ESSAY)
    assert len(weak["flags"]["cliches"]) >= 3
    assert any("clich" in w.lower() for w in weak["weaknesses"])

    essay2 = _make_essay(client, auth_headers, title="Second")
    _, strong = _analyze(client, auth_headers, essay2["id"], STRONG_ESSAY)
    assert strong["flags"]["cliches"] == []
    assert strong["overall_score"] > weak["overall_score"]
    # the strong essay reflects; the cliche one repeats "science"
    assert strong["scores"]["reflection"] > weak["scores"]["reflection"]
    assert "science" in weak["flags"]["repeated_words"]


def test_too_short_draft_handled(client, auth_headers):
    essay = _make_essay(client, auth_headers)
    _, fb = _analyze(client, auth_headers, essay["id"], "I like college. It is nice.")
    assert fb["overall_score"] <= 25
    assert any("short" in w.lower() for w in fb["weaknesses"])


def test_off_prompt_essay_scores_lower_alignment(client, auth_headers):
    prompt = "Describe a challenge you overcame and what you learned from the experience."
    on_topic = _make_essay(client, auth_headers, prompt=prompt)
    _, fb_on = _analyze(client, auth_headers, on_topic["id"], STRONG_ESSAY)
    off_topic = _make_essay(client, auth_headers, title="Off", prompt=(
        "Discuss your favorite painting, sculpture, gallery, museum, canvas, "
        "portrait, watercolor, exhibition and artistic movement."
    ))
    _, fb_off = _analyze(client, auth_headers, off_topic["id"], STRONG_ESSAY)
    assert fb_on["scores"]["prompt_alignment"] > fb_off["scores"]["prompt_alignment"]


def test_word_limit_flagged(client, auth_headers):
    essay = _make_essay(client, auth_headers, word_limit=100)
    _, fb = _analyze(client, auth_headers, essay["id"], STRONG_ESSAY)
    assert any("word limit" in w.lower() for w in fb["weaknesses"])


def test_reanalyze_replaces_feedback(client, auth_headers):
    essay = _make_essay(client, auth_headers)
    draft, _ = _analyze(client, auth_headers, essay["id"], STRONG_ESSAY)
    second = client.post(
        f"/api/essays/{essay['id']}/drafts/{draft['id']}/analyze", headers=auth_headers
    )
    assert second.status_code == 200
    detail = client.get(f"/api/essays/{essay['id']}", headers=auth_headers).json()
    assert detail["drafts"][0]["feedback"]["id"] == second.json()["id"]


def test_score_progression_visible(client, auth_headers):
    """Spec #18: essay scores over time - draft 1 vs draft 2."""
    essay = _make_essay(client, auth_headers)
    _analyze(client, auth_headers, essay["id"], CLICHE_ESSAY)
    _analyze(client, auth_headers, essay["id"], STRONG_ESSAY)
    detail = client.get(f"/api/essays/{essay['id']}", headers=auth_headers).json()
    s = [d["feedback"]["overall_score"] for d in detail["drafts"]]
    assert len(s) == 2 and s[1] > s[0]


def test_essays_are_user_isolated(client, auth_headers):
    other = client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "secret1234"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    essay = _make_essay(client, auth_headers)
    assert client.get(f"/api/essays/{essay['id']}", headers=other_headers).status_code == 404
    assert client.get("/api/essays", headers=other_headers).json() == []
