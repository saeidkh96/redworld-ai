from redworld.domains.actions import ActionType
from redworld.simulation.engine import SimulationEngine
from redworld.simulation.factory import create_world


def test_v1_world_seeds_life_layers() -> None:
    world = create_world(population=120, seed=7)
    assert len(world.households) > 0
    assert len(world.society.relationships) >= 100
    assert len(world.employment.active_contracts()) > 0
    citizen = next(iter(world.citizens.values()))
    assert world.planning.for_citizen(citizen.id)
    assert 0.0 <= citizen.needs.hunger <= 1.0


def test_living_engine_advances_needs_and_actions() -> None:
    world = create_world(population=80, seed=9)
    before_tick = world.tick
    SimulationEngine(world).run(12)
    assert world.tick == before_tick + 12
    assert any(event.event_type == "CitizenActionStarted" for event in world.events.events)
    assert world.ledger.trial_balance_delta().amount == 0


def test_memory_is_bounded() -> None:
    world = create_world(population=10, seed=3)
    citizen = next(iter(world.citizens.values()))
    from redworld.domains.memory import MemoryRecord

    for index in range(40):
        world.memories.remember(citizen.id, MemoryRecord(index, "test", str(index)))
    assert len(world.memories.recent(citizen.id, 100)) == 24


def test_action_enum_contains_roadmap_actions() -> None:
    assert ActionType.WORK.value == "work"
    assert ActionType.SOCIALIZE.value == "socialize"
    assert ActionType.HEALTHCARE.value == "healthcare"
