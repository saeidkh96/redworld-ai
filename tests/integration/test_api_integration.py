from fastapi.testclient import TestClient

from redworld.api.dependencies import get_engine
from redworld.api.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0"


def test_world_endpoint_and_step() -> None:
    get_engine.cache_clear()
    client = TestClient(app)
    before = client.get("/api/v1/world")
    assert before.status_code == 200
    assert before.json()["population"] == 1500
    stepped = client.post("/api/v1/world/step?steps=1")
    assert stepped.status_code == 200
    payload = stepped.json()
    assert payload["world"]["tick"] == 1
    assert payload["stepped"] == 1
    assert payload["world"]["ledger_entries"] >= 0
