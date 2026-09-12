from redworld.simulation.factory import create_genesis_world


def test_genesis_world_has_core_institutions() -> None:
    world = create_genesis_world("RedWorld")
    assert world.name == "RedWorld"
    assert len(world.citizens) == 4
    assert len(world.businesses) == 1
    assert len(world.banks) == 1
    assert world.government is not None
    assert world.ledger.audit_entry_count() == 1
    assert world.ledger.trial_balance_delta().is_zero()
