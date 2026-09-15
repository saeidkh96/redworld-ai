from fastapi.testclient import TestClient

from redworld.api.dependencies import get_engine
from redworld.api.main import app
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world
from redworld.simulation.snapshot import civilization_snapshot


def test_v121_civilization_bootstraps_and_evolves_daily() -> None:
    world = create_world(population=60)
    engine = SimulationEngine(world)
    engine.step()
    assert world.civilization.initialized
    assert world.civilization.history.records

    engine.run(72)
    state = world.civilization
    for value in (
        state.development_level,
        state.stability,
        state.prosperity,
        state.resilience,
        state.careers.mobility_index,
        state.economy.demand_index,
        state.economy.supply_index,
        state.governance.approval,
        state.social.cooperation,
        state.intelligence.foresight,
    ):
        assert 0 <= value <= 1


def test_v121_monthly_systems_and_city_evolution() -> None:
    world = create_world(population=80)
    engine = SimulationEngine(world)
    engine.step()
    before = world.civilization.governance.months_to_election
    world.clock.day = 30
    world.clock.minute_of_day = 23 * 60 + 45
    engine.step()
    state = world.civilization
    assert state.governance.months_to_election < before
    assert state.economy.price_index > 0
    assert state.careers.wage_index > 0
    assert state.city.construction_projects >= 0
    assert abs(sum(state.careers.class_distribution.values()) - 1.0) < 1e-9


def test_v121_civilization_snapshot_has_all_capability_domains() -> None:
    world = create_world(population=30)
    SimulationEngine(world).step()
    payload = civilization_snapshot(world)
    assert set(
        (
            "demography",
            "careers",
            "economy",
            "governance",
            "social_dynamics",
            "city_evolution",
            "crises",
            "world_intelligence",
            "history_count",
        )
    ).issubset(payload)


def test_v121_api_exposes_civilization_and_history() -> None:
    get_engine.cache_clear()
    client = TestClient(app)
    assert client.post("/api/v1/world/step?steps=1").status_code == 200
    civilization = client.get("/api/v1/world/civilization")
    assert civilization.status_code == 200
    assert "world_intelligence" in civilization.json()
    history = client.get("/api/v1/world/history?limit=10")
    assert history.status_code == 200
    assert history.json()["total"] >= 1
    summary = client.get("/api/v1/world").json()
    assert summary["version"] == "1.4.0"
    assert "living_civilization" in summary
