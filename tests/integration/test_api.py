from fastapi.testclient import TestClient

from redworld.api.dependencies import get_engine
from redworld.api.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_world_endpoint_and_step() -> None:
    get_engine.cache_clear()
    client = TestClient(app)
    before = client.get("/api/v1/world")
    assert before.status_code == 200
    assert before.json()["citizens"] == 4
    stepped = client.post("/api/v1/world/step")
    assert stepped.status_code == 200
    payload = stepped.json()
    assert payload["tick"] == 1
    assert payload["stepped"] is True
    assert payload["ledger_entries"] > 1
