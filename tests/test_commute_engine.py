from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world


def test_spatial_engine_starts_and_completes_morning_commutes() -> None:
    world = create_world(population=30, seed=19)
    engine = SimulationEngine(world)
    employed = [
        citizen
        for citizen in world.citizens.values()
        if citizen.employed and citizen.work_location_id is not None
    ]
    assert employed

    engine.run(16)  # Day 1, 10:00.

    assert any(citizen.current_location_id == citizen.work_location_id for citizen in employed)
    assert any(event.event_type == "CitizenMoved" for event in world.events.events)


def test_spatial_engine_returns_commuters_home_in_evening() -> None:
    world = create_world(population=30, seed=23)
    engine = SimulationEngine(world)
    employed = [
        citizen
        for citizen in world.citizens.values()
        if citizen.employed and citizen.work_location_id is not None
    ]
    assert employed

    engine.run(52)  # Day 1, 19:00.

    assert all(citizen.current_location_id == citizen.home_location_id for citizen in employed)
