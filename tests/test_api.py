from fastapi.testclient import TestClient

from redworld.api.dependencies import get_engine
from redworld.api.main import app


def test_world_api_and_viewer() -> None:
    get_engine.cache_clear()
    client = TestClient(app)
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    world = client.get("/api/v1/world")
    assert world.status_code == 200
    assert world.json()["population"] == 1500
    map_response = client.get("/api/v1/world/map?render_sample=20")
    assert map_response.status_code == 200
    assert len(map_response.json()["agents"]) <= 20
    viewer = client.get("/viewer")
    assert viewer.status_code == 200
    assert "Genesis City" in viewer.text


def test_step_endpoint_advances_time() -> None:
    get_engine.cache_clear()
    client = TestClient(app)
    before = client.get("/api/v1/world").json()["tick"]
    response = client.post("/api/v1/world/step?steps=2")
    assert response.status_code == 200
    assert response.json()["world"]["tick"] == before + 2
