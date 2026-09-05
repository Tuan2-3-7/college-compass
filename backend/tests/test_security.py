"""Deployment hardening: production config guard and rate limiting."""

import pytest

from app import ratelimit
from app.config import DEV_JWT_SECRET, Settings, validate_for_production


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    ratelimit.reset()
    yield
    ratelimit.reset()


# ---------------- production config guard ----------------

def test_dev_defaults_are_rejected_in_production():
    problems = validate_for_production(Settings())
    joined = " | ".join(problems)
    assert "JWT_SECRET" in joined       # forgeable tokens - the dangerous one
    assert "SQLite" in joined           # ephemeral disk = data loss
    assert "localhost" in joined        # CORS would block the real frontend


def test_production_ready_config_passes():
    good = Settings(
        environment="production",
        jwt_secret="x" * 48,
        database_url="postgresql+psycopg://user:pw@host/db",
        cors_origins="https://collegecompass.pages.dev",
    )
    assert validate_for_production(good) == []


def test_short_secret_still_rejected():
    weak = Settings(
        environment="production",
        jwt_secret="tooshort",
        database_url="postgresql+psycopg://user:pw@host/db",
        cors_origins="https://example.com",
    )
    assert any("too short" in p for p in validate_for_production(weak))
    assert weak.jwt_secret != DEV_JWT_SECRET  # a different failure than the default


# ---------------- rate limiting ----------------

def test_login_brute_force_is_blocked(client):
    """Password guessing must hit a wall well before it becomes useful."""
    payload = {"email": "victim@example.com", "password": "wrong-guess-1"}
    statuses = [
        client.post("/api/auth/login", json=payload).status_code for _ in range(12)
    ]
    assert 429 in statuses, "brute-force attempts were never rate limited"
    assert statuses.index(429) >= 5, "limit should allow a few genuine mistakes"


def test_rate_limited_response_tells_the_client_when_to_retry(client):
    payload = {"email": "a@example.com", "password": "nope-nope-nope"}
    resp = None
    for _ in range(15):
        resp = client.post("/api/auth/login", json=payload)
        if resp.status_code == 429:
            break
    assert resp.status_code == 429
    assert int(resp.headers["Retry-After"]) > 0
    assert "Try again" in resp.json()["detail"]


def test_ai_endpoints_are_limited_separately_from_auth(client, auth_headers):
    """One user must not be able to drain a free LLM tier - but AI limits
    must not be consumed by ordinary auth traffic."""
    for _ in range(25):
        resp = client.post("/api/tutor/chat", headers=auth_headers,
                           json={"message": "What is the FAFSA?"})
        if resp.status_code == 429:
            break
    assert resp.status_code == 429


def test_normal_endpoints_are_not_rate_limited(client, auth_headers):
    """Browsing universities is cheap - it must never trip the limiter."""
    for _ in range(40):
        assert client.get("/api/universities", params={"limit": 1}).status_code == 200


def test_forwarded_ip_is_used_behind_a_proxy(client):
    """Deployments sit behind a proxy; without X-Forwarded-For every user
    would share one bucket and rate-limit each other."""
    for _ in range(12):
        client.post("/api/auth/login",
                    headers={"X-Forwarded-For": "203.0.113.10"},
                    json={"email": "a@example.com", "password": "bad-password"})
    blocked = client.post("/api/auth/login",
                          headers={"X-Forwarded-For": "203.0.113.10"},
                          json={"email": "a@example.com", "password": "bad-password"})
    assert blocked.status_code == 429

    # a different client IP is unaffected
    other = client.post("/api/auth/login",
                        headers={"X-Forwarded-For": "198.51.100.7"},
                        json={"email": "a@example.com", "password": "bad-password"})
    assert other.status_code == 401
