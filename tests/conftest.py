import os

os.environ["DATABASE_URL"] = os.environ.get(
    'TEST_DATABASE_URL',
    "postgresql+psycopg://tracker:tracker@localhost:5432/tracker_test"
)
os.environ["ADMIN_API_KEY"] = "test-key"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

ADMIN = {"X-API-KEY": "test-key"}

@pytest.fixture(autouse=True)
def fesh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def make_listing(client):
    def _make(**overrides):
        body = {
            "sector": "pharma",
            "title": "Graduate Scientist",
            "company": "AstraZeneca",
            "location": "Cambridge",
            "url": "https://example.com/job/1",
        }
        body.update(overrides)
        response = client.post("api/listings", json=body, headers=ADMIN)
        assert response.status_code == 201, response.txt
        return response.json()
    return _make


