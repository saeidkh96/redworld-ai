from fastapi.testclient import TestClient

from redworld.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.0.1"


def test_world_endpoint() -> None:
    response = client.get("/api/v1/world")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"]
    assert payload["tick"] >= 0
    assert payload["citizens"] == 1
    assert payload["banks"] == 1
    assert payload["has_government"] is True


def test_step_endpoint_advances_world() -> None:
    before = client.get("/api/v1/world").json()["tick"]
    response = client.post("/api/v1/world/step")

    assert response.status_code == 200
    payload = response.json()
    assert payload["stepped"] is True
    assert payload["tick"] == before + 1
