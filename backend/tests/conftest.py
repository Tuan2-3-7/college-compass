import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.scholarships import seed_scholarships
from app.database import Base, get_db
from app.main import app
from app.seed import seed_universities

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_universities(db)
    seed_scholarships(db)
    db.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def auth_headers(client):
    """Register a fresh user and return Authorization headers."""
    resp = client.post(
        "/api/auth/register", json={"email": "student@example.com", "password": "testpass123"}
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def set_profile(client, headers, **overrides):
    base = {
        "full_name": "Test Student",
        "student_type": "domestic",
        "applicant_level": "first_year",
        "gpa": 3.8,
        "sat": 1450,
        "intended_major": "computer_science",
        "financial_aid_needed": False,
    }
    base.update(overrides)
    resp = client.put("/api/profile", headers=headers, json=base)
    assert resp.status_code == 200, resp.text
    return resp.json()


def find_university(client, name_fragment):
    resp = client.get("/api/universities", params={"q": name_fragment})
    assert resp.status_code == 200
    results = resp.json()
    assert results, f"no university matching {name_fragment}"
    return results[0]
