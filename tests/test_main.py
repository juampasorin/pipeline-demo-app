import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_add_success(client):
    resp = client.post("/add", json={"a": 2, "b": 3})
    assert resp.status_code == 200
    assert resp.get_json() == {"result": 5}


def test_add_missing_field(client):
    resp = client.post("/add", json={"a": 2})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_add_invalid_type(client):
    resp = client.post("/add", json={"a": "not-a-number", "b": 2})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_add_negative_numbers(client):
    resp = client.post("/add", json={"a": -5, "b": 3})
    assert resp.status_code == 200
    assert resp.get_json() == {"result": -2}
