from redworld.simulation.factory import create_genesis_world


def test_genesis_world_contains_core_institutions() -> None:
    world = create_genesis_world("Test World")

    assert world.name == "Test World"
    assert len(world.citizens) == 1
    assert len(world.banks) == 1
    assert world.government is not None
    assert world.economy.currency == "RWC"
