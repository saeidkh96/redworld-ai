from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world


def test_autonomous_society_bootstraps_and_profiles_exist() -> None:
    world = create_world(population=60)
    engine = SimulationEngine(world)
    engine.step()
    assert len(world.autonomous_society.institutions) == 4
    assert len(world.autonomous_society.groups) == 3
    assert len(world.autonomous_society.norms) == 5
    assert len(world.life_profiles) == len(world.citizens)


def test_autonomous_society_metrics_are_bounded() -> None:
    world = create_world(population=40)
    engine = SimulationEngine(world)
    engine.run(100)
    state = world.autonomous_society
    for value in (
        state.public_mood,
        state.social_cohesion,
        state.civic_participation,
        state.institutional_trust,
        state.collective_agency,
        state.polarization,
    ):
        assert 0.0 <= value <= 1.0
