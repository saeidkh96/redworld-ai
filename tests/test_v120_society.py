from redworld.domains.life.progression import LifeStage
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world


def test_v120_human_development_fields_evolve() -> None:
    world = create_world(population=30)
    engine = SimulationEngine(world)
    engine.step()
    profile = next(iter(world.life_profiles.values()))
    before = profile.experience_days
    engine.run(96)
    assert profile.experience_days >= before
    assert 0 <= profile.learning_progress <= 1
    assert 0 <= profile.career_progress <= 1
    assert 0 <= profile.burnout_risk <= 1
    assert 0 <= profile.civic_engagement <= 1
    assert profile.life_stage in LifeStage


def test_v120_society_development_indices_are_bounded() -> None:
    world = create_world(population=40)
    engine = SimulationEngine(world)
    engine.run(100)
    state = world.autonomous_society
    for value in (
        state.education_index,
        state.public_health,
        state.cultural_vitality,
        state.social_mobility,
        state.inequality_pressure,
    ):
        assert 0 <= value <= 1
    assert all(0 <= i.capacity <= 1 for i in state.institutions.values())
    assert all(0 <= g.cultural_identity <= 1 for g in state.groups.values())
